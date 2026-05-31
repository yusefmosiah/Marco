from __future__ import annotations

from pathlib import Path

from emf_macro.datasets import DatasetRegistry, dataset_id_for


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
