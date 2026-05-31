from __future__ import annotations

from pathlib import Path

import pytest

from emf_macro.datasets import DatasetRegistry, build_dataset_mapping_spec, dataset_id_for


def test_dataset_registry_adds_csv_with_schema(tmp_path: Path) -> None:
    source = tmp_path / "sample macro.csv"
    source.write_text("date,value,country\n2020-01,1.2,US\n", encoding="utf-8")

    registry = DatasetRegistry(tmp_path)
    record = registry.add_file(source, name="Sample Macro", tags=["test"])

    assert record["dataset_id"].startswith("sample-macro-")
    assert record["format"] == "csv"
    assert record["schema"]["columns"] == ["date", "value", "country"]
    assert record["tags"] == ["test"]
    assert (tmp_path / record["stored_path"]).exists()
    assert registry.list()[0]["sha256"] == record["sha256"]


def test_dataset_id_is_stable_for_name_and_hash() -> None:
    assert dataset_id_for("My Dataset!", "abcdef1234567890").startswith("my-dataset-abcdef123456")


def test_build_dataset_mapping_spec_validates_columns(tmp_path: Path) -> None:
    source = tmp_path / "panel.csv"
    source.write_text("date,policy_rate,cpi,country\n2020-01,1.0,100,IN\n", encoding="utf-8")
    record = DatasetRegistry(tmp_path).add_file(source, name="Panel")

    spec = build_dataset_mapping_spec(
        record,
        date_column="date",
        value_columns=["policy_rate", "cpi"],
        frequency="M",
        country="IN",
        indicators={"policy_rate": "policy_rate", "cpi": "price_index"},
        units={"policy_rate": "percent", "cpi": "index"},
    )

    assert spec["schema_version"] == "marco.dataset_mapping.v1"
    assert spec["dataset_id"] == record["dataset_id"]
    assert spec["mapping_id"].startswith("map-")
    assert spec["vintage_policy"] == "latest_revised_snapshot"


def test_build_dataset_mapping_spec_rejects_missing_columns(tmp_path: Path) -> None:
    source = tmp_path / "panel.csv"
    source.write_text("date,policy_rate\n2020-01,1.0\n", encoding="utf-8")
    record = DatasetRegistry(tmp_path).add_file(source, name="Panel")

    with pytest.raises(ValueError, match="missing columns"):
        build_dataset_mapping_spec(
            record,
            date_column="date",
            value_columns=["missing_cpi"],
            frequency="M",
        )
