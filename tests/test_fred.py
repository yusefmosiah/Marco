from __future__ import annotations

from pathlib import Path

from emf_macro.catalog import SeriesSpec
from emf_macro.fred import parse_fred_series
from emf_macro.io import SourceRecord


def test_parse_fred_series_resamples_to_month_end(tmp_path: Path) -> None:
    path = tmp_path / "series.csv"
    path.write_text(
        "observation_date,TEST\n"
        "2020-01-01,1\n"
        "2020-01-31,2\n"
        "2020-02-03,\n"
        "2020-02-28,4\n",
        encoding="utf-8",
    )
    record = SourceRecord("test", "file://test", "abc", 1, "now", str(path))
    frame = parse_fred_series(record, SeriesSpec("TEST", "test", "US", "level"))
    assert list(frame.index.strftime("%Y-%m-%d")) == ["2020-01-31", "2020-02-29"]
    assert frame.loc["2020-01-31", "TEST"] == 2
    assert frame.loc["2020-02-29", "TEST"] == 4
