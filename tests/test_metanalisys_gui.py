from pathlib import Path

import pytest

from metanalisys_core import FileAccessError
from metanalisysGUI import FOLDER_SUMMARY_TABLE_COLUMNS
from metanalisysGUI import build_destination_report_paths
from metanalisysGUI import build_folder_summary_table_rows
from metanalisysGUI import get_about_text
from metanalisysGUI import get_folder_summary_counts
from metanalisysGUI import normalize_folder_display_value
from metanalisysGUI import resolve_analysis_target


def test_resolve_analysis_target_detects_file(tmp_path: Path) -> None:
    sample_file = tmp_path / "sample.docx"
    sample_file.write_bytes(b"synthetic")

    assert resolve_analysis_target(str(sample_file)) == "file"


def test_resolve_analysis_target_detects_folder(tmp_path: Path) -> None:
    assert resolve_analysis_target(str(tmp_path)) == "folder"


@pytest.mark.parametrize("invalid_value", ["", "   "])
def test_resolve_analysis_target_rejects_empty_values(invalid_value: str) -> None:
    with pytest.raises(FileAccessError) as exc_info:
        resolve_analysis_target(invalid_value)

    assert "Selezionare un file o una cartella" in str(exc_info.value)


def test_resolve_analysis_target_rejects_missing_path(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.docx"

    with pytest.raises(FileAccessError) as exc_info:
        resolve_analysis_target(str(missing_path))

    assert "non esiste" in str(exc_info.value)


def test_build_destination_report_paths_uses_selected_destination(tmp_path: Path) -> None:
    source_folder = tmp_path / "source_folder"
    source_folder.mkdir()
    destination_folder = tmp_path / "exports"
    destination_folder.mkdir()

    report_paths = build_destination_report_paths(
        str(source_folder),
        str(destination_folder),
    )

    assert report_paths == {
        "txt": str(destination_folder / "source_folder_folder_summary.txt"),
        "csv": str(destination_folder / "source_folder_folder_summary.csv"),
        "json": str(destination_folder / "source_folder_folder_summary.json"),
        "html": str(destination_folder / "source_folder_folder_summary.html"),
    }


def test_get_about_text_mentions_folder_support() -> None:
    about_text = get_about_text()

    assert "metanalisys" in about_text
    assert "Supporto analisi cartella con report TXT/CSV/JSON/HTML." in about_text


def test_normalize_folder_display_value_uses_nd_for_missing_values() -> None:
    assert normalize_folder_display_value(None) == "N/D"
    assert normalize_folder_display_value("") == "N/D"
    assert normalize_folder_display_value("Author") == "Author"
    assert normalize_folder_display_value(12) == "12"


def test_get_folder_summary_counts_counts_known_statuses() -> None:
    folder_results = {
        "rows": [
            {"status": "OK"},
            {"status": "LIMITED"},
            {"status": "ERROR"},
            {"status": "OK"},
            {"status": "IGNORED"},
        ]
    }

    assert get_folder_summary_counts(folder_results) == {
        "OK": 2,
        "LIMITED": 1,
        "ERROR": 1,
    }


def test_build_folder_summary_table_rows_prepares_expected_display_values() -> None:
    folder_results = {
        "rows": [
            {
                "filename": "sample.docx",
                "office_family": "Word",
                "creator": None,
                "last_modified_by": "Reviewer B",
                "created": "",
                "modified": "2026-06-09T10:30:00Z",
                "risk_score": 15,
                "risk_level": "BASSO",
                "status": "OK",
            }
        ]
    }

    assert build_folder_summary_table_rows(folder_results) == [
        {
            "filename": "sample.docx",
            "office_family": "Word",
            "creator": "N/D",
            "last_modified_by": "Reviewer B",
            "created": "N/D",
            "modified": "2026-06-09T10:30:00Z",
            "risk_score": "15",
            "risk_level": "BASSO",
            "status": "OK",
        }
    ]


def test_folder_summary_table_columns_match_expected_labels() -> None:
    assert FOLDER_SUMMARY_TABLE_COLUMNS == [
        ("filename", "File", 280),
        ("office_family", "Famiglia Office", 130),
        ("creator", "Creatore", 170),
        ("last_modified_by", "Ultima modifica di", 170),
        ("created", "Creato", 170),
        ("modified", "Ultima modifica", 170),
        ("risk_score", "Risk score", 90),
        ("risk_level", "Livello", 100),
        ("status", "Stato", 100),
    ]


def test_build_folder_summary_table_rows_normalizes_missing_last_modified_by() -> None:
    folder_results = {
        "rows": [
            {
                "filename": "sample.docx",
                "office_family": "Word",
                "creator": "Author A",
                "last_modified_by": None,
                "created": "2026-06-08T09:00:00Z",
                "modified": "2026-06-09T10:30:00Z",
                "risk_score": 0,
                "risk_level": "BASSO",
                "status": "OK",
            }
        ]
    }

    assert build_folder_summary_table_rows(folder_results)[0]["last_modified_by"] == "N/D"
