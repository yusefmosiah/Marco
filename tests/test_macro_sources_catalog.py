import json
from pathlib import Path


def test_macro_sources_catalog_is_valid_and_unique():
    catalog_path = Path("configs/macro_sources.json")
    catalog = json.loads(catalog_path.read_text())

    assert catalog["schema"] == "marco.macro_sources.v1"
    sources = catalog["sources"]
    assert sources

    ids = [source["id"] for source in sources]
    assert len(ids) == len(set(ids))

    for source in sources:
        assert source["name"]
        assert source["operator"]
        assert source["priority"] in {"p0", "p1", "p2"}
        assert source["status"] in {"active", "planned", "candidate"}
        assert source["access_pattern"] in {
            "download_endpoint",
            "download_pages",
            "rest_api",
            "rest_json_csv",
            "sdmx",
            "sdmx_2_1",
            "sdmx_2_1_or_3_0",
            "structured_database",
        }
        assert source["official_url"].startswith("https://")
        assert source["docs_url"].startswith("https://")


def test_macro_sources_catalog_has_global_and_em_coverage():
    catalog = json.loads(Path("configs/macro_sources.json").read_text())
    sources = catalog["sources"]
    ids = {source["id"] for source in sources}

    assert {"fred", "alfred", "imf_data_sdmx", "world_bank_indicators"} <= ids
    assert {"rbi_dbie", "bcb_sgs", "banxico_sie", "bank_indonesia_seki"} <= ids
    assert any("global" in source["regions"] for source in sources)
    assert any("IN" in source["regions"] for source in sources)
