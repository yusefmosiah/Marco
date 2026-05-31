from __future__ import annotations

import pytest
from pathlib import Path

from emf_macro.sources import MacroSourceCatalog


def test_macro_source_catalog_lists_and_filters_repo_catalog() -> None:
    catalog = MacroSourceCatalog(Path("."))

    p0_sources = catalog.list(priority="p0")
    ids = {source["id"] for source in p0_sources}

    assert "fred" in ids
    assert "ecb_sdmx" in ids
    assert "rbi_dbie" in ids
    assert all(source["priority"] == "p0" for source in p0_sources)


def test_macro_source_catalog_inspects_one_source() -> None:
    catalog = MacroSourceCatalog(Path("."))

    source = catalog.inspect("imf_data_sdmx")

    assert source["operator"] == "International Monetary Fund"
    assert source["access_pattern"] == "sdmx_2_1_or_3_0"


def test_macro_source_catalog_rejects_unknown_source() -> None:
    catalog = MacroSourceCatalog(Path("."))

    with pytest.raises(KeyError):
        catalog.inspect("missing-source")
