from __future__ import annotations

import json
from pathlib import Path

from emf_macro.global_panel import build_global_macro_panel, load_global_macro_summary
from emf_macro.world_bank import fetch_world_bank_indicator


def test_build_global_macro_panel_from_world_bank_fixture(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    config_dir.mkdir()
    (config_dir / "source_hauls.json").write_text(
        json.dumps(
            {
                "schema": "marco.source_hauls.v1",
                "hauls": [
                    {
                        "id": "test_haul",
                        "name": "Test haul",
                        "vintage_policy": "latest_revised_snapshot",
                        "countries": ["IND", "BRA", "MEX", "ZAF"],
                        "world_bank": {
                            "start_year": 2023,
                            "end_year": 2023,
                            "indicators": [
                                {
                                    "id": "NY.GDP.MKTP.CD",
                                    "label": "GDP",
                                    "feature_name": "gdp_current_usd",
                                }
                            ],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    raw = Path("tests/fixtures/world_bank_gdp_sample.json").read_bytes()
    fetch_world_bank_indicator(
        tmp_path,
        ["IND", "BRA", "MEX", "ZAF"],
        "NY.GDP.MKTP.CD",
        downloader=lambda _url: raw,
    )

    summary = build_global_macro_panel(tmp_path, haul_id="test_haul")

    assert summary["schema_version"] == "marco.global_macro_panel.v1"
    assert summary["panel_rows"] == 4
    assert summary["countries"] == ["BRA", "IND", "MEX", "ZAF"]
    assert summary["features"] == ["gdp_current_usd"]
    assert (tmp_path / "data" / "derived" / "global_macro_panel" / "panel_annual.csv").exists()
    assert load_global_macro_summary(tmp_path, haul_id="test_haul")["panel_rows"] == 4
