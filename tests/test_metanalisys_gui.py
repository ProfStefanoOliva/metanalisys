from pathlib import Path

import pytest

from metanalisys_core import FileAccessError
from metanalisysGUI import build_destination_report_paths
from metanalisysGUI import get_about_text
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
