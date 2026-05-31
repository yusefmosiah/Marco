from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    family: str
    complexity_tier: int
    status: str
    executable_now: bool
    description: str
    guardrail: str


MODEL_SPECS = [
    ModelSpec(
        "random_walk",
        "baseline",
        0,
        "active",
        True,
        "Predicts zero FX return; equivalent to no expected change in log spot.",
        "Must remain a comparison baseline for all FX return experiments.",
    ),
    ModelSpec(
        "no_change",
        "baseline",
        0,
        "active",
        True,
        "Explicit no-change baseline; currently identical to random_walk for FX returns.",
        "Do not report model wins without comparing against this baseline.",
    ),
    ModelSpec(
        "rolling_mean_36m",
        "baseline",
        1,
        "active",
        True,
        "Uses the trailing 36-month average target return.",
        "Use only with walk-forward windows; never include current target in training.",
    ),
    ModelSpec(
        "carry_diff",
        "economic_rule",
        1,
        "active",
        True,
        "Interest-rate carry rule based on nominal short-rate differentials.",
        "Respect quote convention sign for each FX pair.",
    ),
    ModelSpec(
        "real_rate_diff",
        "economic_rule",
        1,
        "active",
        True,
        "Real-rate rule using nominal rate differentials adjusted for inflation differentials.",
        "Treat as latest-revised until vintage-safe CPI/rate releases are added.",
    ),
    ModelSpec(
        "ridge",
        "regularized_linear",
        2,
        "active",
        True,
        "Standardized Ridge regression over macro/rate/FX lag features.",
        "Use walk-forward fitting only; report small deltas conservatively.",
    ),
    ModelSpec(
        "elastic_net",
        "regularized_linear",
        3,
        "planned",
        False,
        "Sparse regularized linear model for wider feature panels.",
        "Needs stable feature registry and coefficient reporting before activation.",
    ),
    ModelSpec(
        "gradient_boosted_trees",
        "tree_ensemble",
        4,
        "planned",
        False,
        "Nonlinear tabular model for richer macro panels and regimes.",
        "Needs nested walk-forward tuning to avoid overfitting.",
    ),
    ModelSpec(
        "temporal_foundation_model",
        "sequence_model",
        5,
        "research",
        False,
        "Placeholder for pretrained or custom-trained time-series models.",
        "Requires broader datasets, strict vintage splits, and artifacted training runs.",
    ),
]


def list_model_specs(include_planned: bool = True) -> list[dict]:
    rows = [asdict(spec) for spec in MODEL_SPECS]
    if not include_planned:
        rows = [row for row in rows if row["executable_now"]]
    return rows
