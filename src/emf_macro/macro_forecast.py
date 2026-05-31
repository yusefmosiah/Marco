from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


MACRO_FORECAST_SCHEMA = "marco.macro_forecast_lab.v1"
TARGET_COLUMNS = ["interest_rate", "inflation_yoy", "growth_proxy_yoy"]
TARGET_SOURCE_COLUMNS = {
    "interest_rate": "FEDFUNDS",
    "inflation_yoy": "CPIAUCSL",
    "growth_proxy_yoy": "INDPRO",
}


@dataclass(frozen=True)
class MacroForecastConfig:
    root: Path
    fred_md_path: Path | None = None
    output_dir: Path | None = None
    evaluation_start: str = "2006-01"
    horizon_months: int = 6
    train_min_months: int = 120
    var_lags: int = 6
    include_chronos2: bool = False


def run_macro_forecast_lab(config: MacroForecastConfig) -> dict[str, Any]:
    fred_md_path = config.fred_md_path or default_fred_md_path(config.root)
    output_dir = config.output_dir or config.root / "data" / "backtests" / "macro-forecast-lab"
    output_dir.mkdir(parents=True, exist_ok=True)

    raw = load_fred_md(fred_md_path)
    panel = build_macro_target_panel(raw)
    predictions = walk_forward_var_comparison(
        panel,
        horizon_months=config.horizon_months,
        evaluation_start=config.evaluation_start,
        train_min_months=config.train_min_months,
        var_lags=config.var_lags,
    )
    factor_predictions = walk_forward_top_factor_models(
        raw,
        panel,
        horizon_months=config.horizon_months,
        evaluation_start=config.evaluation_start,
        train_min_months=config.train_min_months,
        top_k=5,
    )
    if not factor_predictions.empty:
        predictions = pd.concat([predictions, factor_predictions], ignore_index=True)
    metrics = metric_rows(predictions)
    chronos2 = chronos2_zero_shot_latest_forecast(panel, config.horizon_months) if config.include_chronos2 else {
        "status": "not_requested",
        "model_id": "chronos2_zero_shot",
    }

    panel.to_csv(output_dir / "macro_targets_monthly.csv", index_label="period")
    predictions.to_json(output_dir / "predictions.jsonl", orient="records", lines=True)
    plot_paths = write_forecast_plots(predictions, output_dir)
    write_json(output_dir / "metrics.json", {"schema_version": "marco.macro_forecast_metrics.v1", "metrics": metrics})
    write_json(output_dir / "chronos2_zero_shot.json", chronos2)
    summary = {
        "schema_version": MACRO_FORECAST_SCHEMA,
        "fred_md_path": str(fred_md_path),
        "output_dir": str(output_dir),
        "vintage_policy": "latest_revised_snapshot",
        "lookahead_status": "not_real_time_vintage_safe",
        "targets": {
            "interest_rate": "FEDFUNDS level",
            "inflation_yoy": "100 * log(CPIAUCSL / CPIAUCSL[t-12])",
            "growth_proxy_yoy": "100 * log(INDPRO / INDPRO[t-12]); monthly proxy, not quarterly GDP",
        },
        "horizon_months": config.horizon_months,
        "evaluation_start": config.evaluation_start,
        "train_min_months": config.train_min_months,
        "var_lags": config.var_lags,
        "prediction_rows": int(len(predictions)),
        "models": sorted(predictions["model_id"].unique().tolist()),
        "chronos2_zero_shot": chronos2,
        "plots": plot_paths,
        "metrics": metrics,
    }
    write_json(output_dir / "summary.json", summary)
    (output_dir / "report.md").write_text(render_report(summary), encoding="utf-8")
    return summary


def default_fred_md_path(root: Path) -> Path:
    manifest_path = root / "data" / "fred-fx-rate-lab" / "source_manifest.json"
    raw_dir = root / "data" / "fred-fx-rate-lab" / "raw"
    if manifest_path.exists():
        rows = json.loads(manifest_path.read_text(encoding="utf-8"))
        for row in rows:
            if row.get("logical_name") == "fred_md_current":
                candidate = raw_dir / f"{row['sha256']}.csv"
                if candidate.exists():
                    return candidate
    candidates = sorted(raw_dir.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError(f"no FRED-MD raw CSV found under {raw_dir}")
    return max(candidates, key=lambda path: path.stat().st_size)


def load_fred_md(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    if raw.empty or raw.iloc[0, 0] != "Transform:":
        raise ValueError(f"{path} does not look like a FRED-MD CSV with a Transform row")
    data = raw.iloc[1:].copy()
    data["sasdate"] = pd.to_datetime(data["sasdate"], errors="coerce")
    data = data.dropna(subset=["sasdate"]).set_index("sasdate").sort_index()
    data = data.apply(pd.to_numeric, errors="coerce")
    data.index = data.index.to_period("M").to_timestamp("M")
    return data


def build_macro_target_panel(fred_md: pd.DataFrame) -> pd.DataFrame:
    required = ["FEDFUNDS", "CPIAUCSL", "INDPRO"]
    missing = [column for column in required if column not in fred_md.columns]
    if missing:
        raise ValueError(f"FRED-MD panel is missing required columns: {missing}")
    panel = pd.DataFrame(index=fred_md.index)
    panel["interest_rate"] = fred_md["FEDFUNDS"]
    panel["inflation_yoy"] = 100.0 * np.log(fred_md["CPIAUCSL"] / fred_md["CPIAUCSL"].shift(12))
    panel["growth_proxy_yoy"] = 100.0 * np.log(fred_md["INDPRO"] / fred_md["INDPRO"].shift(12))
    return panel.dropna()


def walk_forward_var_comparison(
    panel: pd.DataFrame,
    *,
    horizon_months: int,
    evaluation_start: str,
    train_min_months: int,
    var_lags: int,
) -> pd.DataFrame:
    df = panel[TARGET_COLUMNS].dropna().sort_index()
    eval_start = pd.Timestamp(evaluation_start)
    rows: list[dict[str, Any]] = []
    for origin_idx, origin in enumerate(df.index):
        target_idx = origin_idx + horizon_months
        if origin < eval_start or origin_idx < train_min_months or target_idx >= len(df):
            continue
        train = df.iloc[: origin_idx + 1]
        current = df.iloc[origin_idx]
        actual = df.iloc[target_idx]
        target_period = df.index[target_idx]

        predictions = {
            "no_change": current,
            "rolling_mean_12": train.tail(12).mean(),
            "var": forecast_var(train, horizon_months=horizon_months, lags=var_lags),
        }
        for model_id, predicted in predictions.items():
            for target in TARGET_COLUMNS:
                rows.append(
                    {
                        "forecast_origin": origin.strftime("%Y-%m"),
                        "target_period": target_period.strftime("%Y-%m"),
                        "target": target,
                        "horizon_months": horizon_months,
                        "model_id": model_id,
                        "current": float(current[target]),
                        "actual": float(actual[target]),
                        "prediction": float(predicted[target]),
                        "error": float(predicted[target] - actual[target]),
                        "actual_change": float(actual[target] - current[target]),
                        "predicted_change": float(predicted[target] - current[target]),
                        "vintage_policy": "latest_revised_snapshot",
                        "lookahead_status": "not_real_time_vintage_safe",
                    }
                )
    return pd.DataFrame(rows)


def walk_forward_top_factor_models(
    fred_md: pd.DataFrame,
    panel: pd.DataFrame,
    *,
    horizon_months: int,
    evaluation_start: str,
    train_min_months: int,
    top_k: int = 5,
) -> pd.DataFrame:
    candidate_features = build_candidate_feature_panel(fred_md)
    model_frame = panel[TARGET_COLUMNS].join(candidate_features, how="inner").dropna(subset=TARGET_COLUMNS)
    eval_start = pd.Timestamp(evaluation_start)
    rows: list[dict[str, Any]] = []
    xgboost = load_xgboost()

    for target in TARGET_COLUMNS:
        feature_columns = [column for column in candidate_features.columns if column != TARGET_SOURCE_COLUMNS[target]]
        target_frame = model_frame[[target, *feature_columns]].dropna()
        for origin_idx, origin in enumerate(target_frame.index):
            target_idx = origin_idx + horizon_months
            if origin < eval_start or origin_idx < train_min_months or target_idx >= len(target_frame):
                continue
            train = target_frame.iloc[: origin_idx + 1]
            current_features = target_frame.iloc[[origin_idx]]
            actual_row = target_frame.iloc[target_idx]
            current_value = float(target_frame.iloc[origin_idx][target])
            actual = float(actual_row[target])
            target_period = target_frame.index[target_idx]

            y_train = train[target].shift(-horizon_months).dropna()
            x_train = train.loc[y_train.index, feature_columns]
            selected = select_top_linear_factors(x_train, y_train, top_k=top_k)
            if len(selected) < top_k:
                continue

            x_train_selected = x_train[selected]
            x_now_selected = current_features[selected]
            linear_pred = fit_predict_linear(x_train_selected, y_train, x_now_selected)
            rows.append(factor_prediction_row(origin, target_period, target, horizon_months, "linear_top5", actual, linear_pred, current_value, selected))

            if xgboost is not None:
                xgb_pred = fit_predict_xgboost(xgboost, x_train_selected, y_train, x_now_selected)
                rows.append(
                    factor_prediction_row(origin, target_period, target, horizon_months, "xgboost_top5", actual, xgb_pred, current_value, selected)
                )

    return pd.DataFrame(rows)


def build_candidate_feature_panel(fred_md: pd.DataFrame) -> pd.DataFrame:
    numeric = fred_md.apply(pd.to_numeric, errors="coerce")
    coverage = numeric.notna().mean()
    columns = [column for column in numeric.columns if coverage[column] >= 0.8]
    features = numeric[columns].copy()
    # First differences make nonstationary level series more usable while keeping
    # the original source column names easy to trace.
    differenced = features.diff().add_suffix("_diff1")
    return pd.concat([features, differenced], axis=1).replace([np.inf, -np.inf], np.nan)


def select_top_linear_factors(x_train: pd.DataFrame, y_train: pd.Series, *, top_k: int) -> list[str]:
    scores = []
    y = y_train.to_numpy(dtype=float)
    for column in x_train.columns:
        x = x_train[column]
        valid = x.notna() & y_train.notna()
        if int(valid.sum()) < 30 or x[valid].nunique() < 2:
            continue
        xv = x[valid].to_numpy(dtype=float)
        yv = y[valid.to_numpy()]
        design = np.column_stack([np.ones(len(xv)), xv])
        beta, *_ = np.linalg.lstsq(design, yv, rcond=None)
        pred = design @ beta
        scores.append((r_squared(yv, pred), column))
    return [column for _, column in sorted(scores, key=lambda item: (-item[0], item[1]))[:top_k]]


def fit_predict_linear(x_train: pd.DataFrame, y_train: pd.Series, x_now: pd.DataFrame) -> float:
    train = x_train.copy()
    train["__target__"] = y_train
    train = train.dropna()
    x = train.drop(columns=["__target__"]).to_numpy(dtype=float)
    y = train["__target__"].to_numpy(dtype=float)
    design = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    x_now_values = x_now.to_numpy(dtype=float)
    now_design = np.column_stack([np.ones(len(x_now_values)), x_now_values])
    return float((now_design @ beta)[0])


def fit_predict_xgboost(xgboost: Any, x_train: pd.DataFrame, y_train: pd.Series, x_now: pd.DataFrame) -> float:
    train = x_train.copy()
    train["__target__"] = y_train
    train = train.dropna()
    model = xgboost.XGBRegressor(
        n_estimators=80,
        max_depth=2,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=123,
        n_jobs=1,
    )
    model.fit(train.drop(columns=["__target__"]), train["__target__"], verbose=False)
    return float(model.predict(x_now)[0])


def load_xgboost() -> Any | None:
    try:
        import xgboost  # type: ignore
    except Exception:
        return None
    return xgboost


def factor_prediction_row(
    origin: pd.Timestamp,
    target_period: pd.Timestamp,
    target: str,
    horizon_months: int,
    model_id: str,
    actual: float,
    prediction: float,
    current: float,
    selected_factors: list[str],
) -> dict[str, Any]:
    return {
        "forecast_origin": origin.strftime("%Y-%m"),
        "target_period": target_period.strftime("%Y-%m"),
        "target": target,
        "horizon_months": horizon_months,
        "model_id": model_id,
        "current": current,
        "actual": actual,
        "prediction": prediction,
        "error": prediction - actual,
        "actual_change": actual - current,
        "predicted_change": prediction - current,
        "selected_factors": selected_factors,
        "vintage_policy": "latest_revised_snapshot",
        "lookahead_status": "not_real_time_vintage_safe",
    }


def forecast_var(train: pd.DataFrame, *, horizon_months: int, lags: int) -> pd.Series:
    y = train[TARGET_COLUMNS].dropna().to_numpy(dtype=float)
    if len(y) <= lags + 1:
        raise ValueError("not enough training rows for VAR")
    x_rows = []
    y_rows = []
    for idx in range(lags, len(y)):
        lagged = [1.0]
        for lag in range(1, lags + 1):
            lagged.extend(y[idx - lag].tolist())
        x_rows.append(lagged)
        y_rows.append(y[idx])
    beta, *_ = np.linalg.lstsq(np.asarray(x_rows), np.asarray(y_rows), rcond=None)
    history = [row.copy() for row in y[-lags:]]
    for _ in range(horizon_months):
        row = [1.0]
        for lag in range(1, lags + 1):
            row.extend(history[-lag].tolist())
        next_value = np.asarray(row) @ beta
        history.append(next_value)
    return pd.Series(history[-1], index=TARGET_COLUMNS)


def metric_rows(predictions: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for (target, model_id), group in predictions.groupby(["target", "model_id"]):
        err = group["error"].to_numpy(dtype=float)
        actual_change = group["actual_change"].to_numpy(dtype=float)
        predicted_change = group["predicted_change"].to_numpy(dtype=float)
        nonzero = actual_change != 0
        rows.append(
            {
                "target": target,
                "model_id": model_id,
                "n": int(len(group)),
                "mae": float(np.mean(np.abs(err))) if len(err) else math.nan,
                "rmse": float(np.sqrt(np.mean(err * err))) if len(err) else math.nan,
                "r_squared": r_squared(group["actual"].to_numpy(dtype=float), group["prediction"].to_numpy(dtype=float)),
                "directional_accuracy": float(np.mean(np.sign(actual_change[nonzero]) == np.sign(predicted_change[nonzero])))
                if np.any(nonzero)
                else math.nan,
            }
        )
    return sorted(rows, key=lambda row: (row["target"], row["model_id"]))


def r_squared(actual: np.ndarray, predicted: np.ndarray) -> float:
    if len(actual) == 0:
        return math.nan
    residual = actual - predicted
    centered = actual - np.mean(actual)
    ss_total = float(np.sum(centered * centered))
    if ss_total == 0:
        return math.nan
    return float(1.0 - np.sum(residual * residual) / ss_total)


def write_forecast_plots(predictions: pd.DataFrame, output_dir: Path, max_points: int = 120) -> dict[str, str]:
    plot_dir = output_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for target in TARGET_COLUMNS:
        target_predictions = predictions[predictions["target"] == target].copy()
        if target_predictions.empty:
            continue
        target_predictions["target_period_dt"] = pd.to_datetime(target_predictions["target_period"])
        actual = (
            target_predictions[["target_period_dt", "actual"]]
            .drop_duplicates("target_period_dt")
            .sort_values("target_period_dt")
            .tail(max_points)
        )
        series = {"actual": actual}
        for model_id in ["no_change", "rolling_mean_12", "var", "linear_top5", "xgboost_top5"]:
            model = target_predictions[target_predictions["model_id"] == model_id]
            model = model[["target_period_dt", "prediction"]].sort_values("target_period_dt").tail(max_points)
            series[model_id] = model.rename(columns={"prediction": model_id})
        svg = render_svg_forecast_plot(target, series)
        path = plot_dir / f"{target}.svg"
        path.write_text(svg, encoding="utf-8")
        paths[target] = str(path)
    return paths


def render_svg_forecast_plot(target: str, series: dict[str, pd.DataFrame]) -> str:
    width = 960
    height = 420
    margin = {"left": 62, "right": 26, "top": 44, "bottom": 54}
    colors = {
        "actual": "#111827",
        "no_change": "#64748b",
        "rolling_mean_12": "#d97706",
        "var": "#2563eb",
        "linear_top5": "#059669",
        "xgboost_top5": "#dc2626",
    }
    labels = {
        "actual": "Actual",
        "no_change": "No change",
        "rolling_mean_12": "Rolling mean",
        "var": "VAR",
        "linear_top5": "Linear top 5",
        "xgboost_top5": "XGBoost top 5",
    }
    all_points: list[tuple[pd.Timestamp, float]] = []
    for name, frame in series.items():
        value_column = "actual" if name == "actual" else name
        for _, row in frame.iterrows():
            if pd.notna(row[value_column]):
                all_points.append((row["target_period_dt"], float(row[value_column])))
    if not all_points:
        return empty_svg(width, height, f"{target}: no plot data")

    xs = [point[0] for point in all_points]
    ys = [point[1] for point in all_points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if y_min == y_max:
        y_min -= 1.0
        y_max += 1.0
    y_pad = (y_max - y_min) * 0.08
    y_min -= y_pad
    y_max += y_pad

    def x_scale(value: pd.Timestamp) -> float:
        denom = max((x_max - x_min).days, 1)
        return margin["left"] + ((value - x_min).days / denom) * (width - margin["left"] - margin["right"])

    def y_scale(value: float) -> float:
        return height - margin["bottom"] - ((value - y_min) / (y_max - y_min)) * (height - margin["top"] - margin["bottom"])

    def polyline(name: str, frame: pd.DataFrame) -> str:
        value_column = "actual" if name == "actual" else name
        points = [
            f"{x_scale(row['target_period_dt']):.1f},{y_scale(float(row[value_column])):.1f}"
            for _, row in frame.iterrows()
            if pd.notna(row[value_column])
        ]
        dash = " stroke-dasharray=\"6 5\"" if name in {"no_change", "rolling_mean_12"} else ""
        return f"<polyline fill=\"none\" stroke=\"{colors[name]}\" stroke-width=\"2.2\"{dash} points=\"{' '.join(points)}\" />"

    y_ticks = [y_min + idx * (y_max - y_min) / 4 for idx in range(5)]
    x_ticks = pd.date_range(x_min, x_max, periods=5)
    lines = [
        f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\" viewBox=\"0 0 {width} {height}\">",
        "<style>text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:12px;fill:#334155}.title{font-size:18px;font-weight:700;fill:#0f172a}.axis{stroke:#94a3b8;stroke-width:1}.grid{stroke:#e2e8f0;stroke-width:1}.legend{font-size:12px}</style>",
        "<rect width=\"100%\" height=\"100%\" fill=\"#ffffff\"/>",
        f"<text class=\"title\" x=\"{margin['left']}\" y=\"26\">{escape_xml(plot_title(target))}</text>",
    ]
    for tick in y_ticks:
        y = y_scale(tick)
        lines.append(f"<line class=\"grid\" x1=\"{margin['left']}\" x2=\"{width - margin['right']}\" y1=\"{y:.1f}\" y2=\"{y:.1f}\"/>")
        lines.append(f"<text x=\"10\" y=\"{y + 4:.1f}\">{tick:.2f}</text>")
    for tick in x_ticks:
        x = x_scale(pd.Timestamp(tick))
        lines.append(f"<line class=\"grid\" x1=\"{x:.1f}\" x2=\"{x:.1f}\" y1=\"{margin['top']}\" y2=\"{height - margin['bottom']}\"/>")
        lines.append(f"<text x=\"{x - 22:.1f}\" y=\"{height - 22}\">{pd.Timestamp(tick).strftime('%Y-%m')}</text>")
    lines.append(f"<line class=\"axis\" x1=\"{margin['left']}\" x2=\"{width - margin['right']}\" y1=\"{height - margin['bottom']}\" y2=\"{height - margin['bottom']}\"/>")
    lines.append(f"<line class=\"axis\" x1=\"{margin['left']}\" x2=\"{margin['left']}\" y1=\"{margin['top']}\" y2=\"{height - margin['bottom']}\"/>")
    model_order = ["actual", "no_change", "rolling_mean_12", "var", "linear_top5", "xgboost_top5"]
    for name in model_order:
        if name in series and not series[name].empty:
            lines.append(polyline(name, series[name]))
    legend_x = margin["left"]
    visible_names = [name for name in model_order if name in series and not series[name].empty]
    for idx, name in enumerate(visible_names):
        x = legend_x + (idx % 3) * 190
        y = height - 22 + (idx // 3) * 15
        dash = " stroke-dasharray=\"6 5\"" if name in {"no_change", "rolling_mean_12"} else ""
        lines.append(f"<line x1=\"{x}\" x2=\"{x + 28}\" y1=\"{y - 4}\" y2=\"{y - 4}\" stroke=\"{colors[name]}\" stroke-width=\"2.2\"{dash}/>")
        lines.append(f"<text class=\"legend\" x=\"{x + 34}\" y=\"{y}\">{labels[name]}</text>")
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def plot_title(target: str) -> str:
    if target == "interest_rate":
        return "Interest Rate Forecast: FEDFUNDS"
    if target == "inflation_yoy":
        return "Inflation Forecast: CPI YoY"
    if target == "growth_proxy_yoy":
        return "Growth Proxy Forecast: Industrial Production YoY"
    return target


def empty_svg(width: int, height: int, message: str) -> str:
    return (
        f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\">"
        f"<rect width=\"100%\" height=\"100%\" fill=\"#fff\"/><text x=\"24\" y=\"42\">{escape_xml(message)}</text></svg>\n"
    )


def escape_xml(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def chronos2_zero_shot_latest_forecast(panel: pd.DataFrame, horizon_months: int) -> dict[str, Any]:
    try:
        from autogluon.timeseries import TimeSeriesDataFrame, TimeSeriesPredictor  # type: ignore
    except Exception as exc:
        return {
            "status": "skipped",
            "model_id": "chronos2_zero_shot",
            "reason": "AutoGluon TimeSeries is not installed",
            "error": str(exc),
        }

    long_rows = []
    for target in TARGET_COLUMNS:
        for period, value in panel[target].dropna().items():
            long_rows.append({"item_id": target, "timestamp": period, "target": float(value)})
    data = TimeSeriesDataFrame.from_data_frame(pd.DataFrame(long_rows), id_column="item_id", timestamp_column="timestamp")
    predictor = TimeSeriesPredictor(prediction_length=horizon_months, target="target").fit(data, presets="chronos2")
    forecast = predictor.predict(data).reset_index()
    records = forecast.to_dict(orient="records")
    return {
        "status": "completed",
        "model_id": "chronos2_zero_shot",
        "presets": "chronos2",
        "fine_tuned": False,
        "forecast_rows": records,
    }


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Macro Forecast Lab",
        "",
        f"FRED-MD path: `{summary['fred_md_path']}`",
        "",
        f"Horizon: `{summary['horizon_months']}M`",
        "",
        "Targets:",
        "",
        "- `interest_rate`: FEDFUNDS level",
        "- `inflation_yoy`: CPIAUCSL year-over-year log inflation",
        "- `growth_proxy_yoy`: INDPRO year-over-year growth proxy, not true quarterly GDP",
        "",
        "## Metrics",
        "",
        "| Target | Model | N | MAE | RMSE | R-squared | Directional Accuracy |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["metrics"]:
        lines.append(
            f"| {row['target']} | {row['model_id']} | {row['n']} | {row['mae']:.6f} | {row['rmse']:.6f} | "
            f"{row['r_squared']:.3f} | {row['directional_accuracy']:.3f} |"
        )
    lines.extend(["", "## Forecast Plots", ""])
    for target, path in summary.get("plots", {}).items():
        lines.append(f"- `{target}`: `{path}`")
    lines.extend(
        [
            "",
            "## Chronos-2 Zero-Shot",
            "",
            "```json",
            json.dumps(summary["chronos2_zero_shot"], indent=2, sort_keys=True),
            "```",
            "",
            "This run uses latest-revised FRED-MD data, not real-time vintage-safe data.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
