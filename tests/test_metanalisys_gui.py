from pathlib import Path

import pytest

from metanalisys_core import FileAccessError
from metanalisysGUI import FOLDER_SUMMARY_TABLE_COLUMNS
from metanalisysGUI import FOLDER_FILE_DETAIL_NOTICE
from metanalisysGUI import PRUDENT_RISK_NOTICE
from metanalisysGUI import SIDEBAR_SECTIONS
from metanalisysGUI import START_VIEW_NOTICE
from metanalisysGUI import build_destination_report_paths
from metanalisysGUI import build_folder_dashboard_cards
from metanalisysGUI import build_folder_file_detail_rows
from metanalisysGUI import build_folder_file_sidebar_items
from metanalisysGUI import build_folder_file_sidebar_label
from metanalisysGUI import build_selected_file_sidebar_items
from metanalisysGUI import build_folder_file_sidebar_tree
from metanalisysGUI import build_folder_summary_table_rows
from metanalisysGUI import build_hash_view_rows
from metanalisysGUI import build_indicator_rows
from metanalisysGUI import build_metadata_view_rows
from metanalisysGUI import build_risk_score_rows
from metanalisysGUI import build_single_file_dashboard_rows
from metanalisysGUI import find_folder_report_entry
from metanalisysGUI import format_sidebar_filename_label
from metanalisysGUI import get_about_text
from metanalisysGUI import get_folder_summary_counts
from metanalisysGUI import has_folder_sidebar_files
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


def test_sidebar_sections_include_required_labels_with_icons() -> None:
    labels = [label for section in SIDEBAR_SECTIONS for _, label in section["items"]]

    assert labels == [
        "🏠 Nuova analisi",
        "📄 Apri file",
        "📂 Apri cartella",
        "▶️ Avvia analisi",
        "💾 Salva report",
        "📊 Dashboard",
        "🧾 Report tecnico",
        "❓ Informazioni",
    ]
    assert [section["title"] for section in SIDEBAR_SECTIONS] == [
        "AZIONI",
        "ANALISI CORRENTE",
        "AIUTO",
    ]


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


def test_build_single_file_dashboard_rows_prepares_expected_values() -> None:
    results = {
        "file_info": {
            "filename": "sample.docx",
            "path": r"C:\cases\sample.docx",
        },
        "format": {
            "family": "Word",
            "extension": ".docx",
            "metadata_support": "full",
        },
        "metadata": {
            "author": None,
            "last_modified_by": "Reviewer B",
            "created": "",
            "modified": "2026-06-09T10:30:00Z",
        },
        "analysis_warnings": ["docProps/app.xml non disponibile"],
        "risk_score": 15,
    }

    assert build_single_file_dashboard_rows(results) == [
        ("Nome file", "sample.docx"),
        ("Percorso", r"C:\cases\sample.docx"),
        ("Famiglia Office", "Word"),
        ("Estensione/formato", ".docx"),
        ("Creatore", "N/D"),
        ("Ultima modifica di", "Reviewer B"),
        ("Data creazione", "N/D"),
        ("Data ultima modifica", "2026-06-09T10:30:00Z"),
        ("Risk score", "15"),
        ("Livello", "BASSO"),
        ("Stato/supporto", "OK / supporto completo"),
        ("Warning", "docProps/app.xml non disponibile"),
    ]


def test_build_folder_dashboard_cards_uses_counts_and_total_files() -> None:
    folder_results = {
        "total_files": 4,
        "rows": [
            {"status": "OK"},
            {"status": "LIMITED"},
            {"status": "ERROR"},
            {"status": "OK"},
        ],
    }

    assert build_folder_dashboard_cards(folder_results) == [
        ("Totale file", "4", "#203244"),
        ("OK", "2", "#1f4f3d"),
        ("LIMITED", "1", "#5b4721"),
        ("ERROR", "1", "#5a2f35"),
    ]


def test_build_folder_dashboard_cards_handles_empty_folder_results() -> None:
    folder_results = {"total_files": 0, "rows": []}

    assert build_folder_dashboard_cards(folder_results) == [
        ("Totale file", "0", "#203244"),
        ("OK", "0", "#1f4f3d"),
        ("LIMITED", "0", "#5b4721"),
        ("ERROR", "0", "#5a2f35"),
    ]


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
            "path": "N/D",
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


def test_build_hash_view_rows_uses_nd_for_missing_hashes() -> None:
    assert build_hash_view_rows({"hashes": {"sha256": "abc"}}) == [
        ("SHA-256", "abc"),
        ("SHA-512", "N/D"),
    ]


def test_build_metadata_view_rows_normalize_missing_values() -> None:
    rows = build_metadata_view_rows(
        {
            "metadata": {"author": None, "last_modified_by": "Reviewer B"},
            "extended_metadata": {"Application": "Word"},
        }
    )

    assert rows[0] == ("Creatore dichiarato", "N/D")
    assert rows[1] == ("Ultima modifica dichiarata da", "Reviewer B")
    assert rows[7] == ("Applicazione dichiarata", "Word")


def test_build_indicator_rows_preserves_structured_indicators_only() -> None:
    assert build_indicator_rows(
        {
            "suspicious_indicators": [
                {"indicator": "Autori multipli rilevati", "score": 10},
                "unexpected",
            ]
        }
    ) == [("Autori multipli rilevati", "10")]


def test_build_folder_file_sidebar_label_uses_icon_and_filename() -> None:
    assert build_folder_file_sidebar_label("sample.docx") == "📄 sample.docx"
    assert build_folder_file_sidebar_label(None, r"C:\cases\fallback.xlsx") == "📄 fallback.xlsx"


def test_format_sidebar_filename_label_keeps_short_filename_readable() -> None:
    assert format_sidebar_filename_label("sample.docx", max_chars=28) == "📄 sample.docx"


def test_format_sidebar_filename_label_truncates_only_at_end() -> None:
    label = format_sidebar_filename_label("nome_file_molto_lungo_versione_finale.docx", max_chars=18)

    assert label.startswith("📄 nome_file_molt")
    assert label.endswith("...")


def test_format_sidebar_filename_label_normalizes_missing_value() -> None:
    assert format_sidebar_filename_label(None, max_chars=18) == "📄 N/D"
    assert format_sidebar_filename_label("", max_chars=18) == "📄 N/D"


def test_build_folder_file_sidebar_items_prepare_clickable_entries() -> None:
    folder_results = {
        "reports": [
            {
                "filename": "sample.docx",
                "path": r"C:\cases\sample.docx",
                "status": "OK",
            },
            {
                "filename": "broken.pptx",
                "path": r"C:\cases\broken.pptx",
                "status": "ERROR",
            },
        ]
    }

    assert build_folder_file_sidebar_items(folder_results) == [
        {
            "path": r"C:\cases\sample.docx",
            "filename": "sample.docx",
            "label": "📄 sample.docx",
            "full_label": "📄 sample.docx",
            "status": "OK",
        },
        {
            "path": r"C:\cases\broken.pptx",
            "filename": "broken.pptx",
            "label": "📄 broken.pptx",
            "full_label": "📄 broken.pptx",
            "status": "ERROR",
        },
    ]


def test_has_folder_sidebar_files_false_when_folder_has_no_supported_results() -> None:
    assert has_folder_sidebar_files({"reports": []}) is False


def test_has_folder_sidebar_files_true_when_reports_exist() -> None:
    assert has_folder_sidebar_files(
        {"reports": [{"filename": "sample.docx", "path": r"C:\cases\sample.docx", "status": "OK"}]}
    ) is True


def test_build_folder_file_sidebar_items_keep_full_name_for_hover_data() -> None:
    long_name = "nome_file_molto_lungo_versione_finale.docx"
    folder_results = {
        "reports": [
            {
                "filename": long_name,
                "path": rf"C:\cases\{long_name}",
                "status": "OK",
            }
        ]
    }

    item = build_folder_file_sidebar_items(folder_results)[0]

    assert item["label"].startswith("📄 ")
    assert item["label"].endswith("...")
    assert item["full_label"] == f"📄 {long_name}"
    assert item["path"] == rf"C:\cases\{long_name}"


def test_build_selected_file_sidebar_items_generated_after_selection() -> None:
    assert build_selected_file_sidebar_items("sample.docx") == [
        ("selected_file_overview", "📄 sample.docx"),
        ("metadata", "🧬 Metadati"),
        ("hashes", "🔐 Hash"),
        ("risk_score", "⚠️ Risk score"),
        ("indicators", "📋 Indicatori"),
        ("file_report", "🧾 Report file"),
    ]


def test_build_selected_file_sidebar_items_empty_when_no_file_selected() -> None:
    assert build_selected_file_sidebar_items(None) == []
    assert build_selected_file_sidebar_items("") == []


def test_build_folder_file_sidebar_tree_places_detail_items_under_selected_file() -> None:
    folder_results = {
        "reports": [
            {"filename": "file1.xlsx", "path": r"C:\cases\file1.xlsx", "status": "OK"},
            {"filename": "file2.docx", "path": r"C:\cases\file2.docx", "status": "OK"},
        ]
    }

    assert build_folder_file_sidebar_tree(folder_results, r"C:\cases\file1.xlsx") == [
        {
            "kind": "file",
            "path": r"C:\cases\file1.xlsx",
            "key": "selected_file_overview",
            "label": "📄 file1.xlsx",
            "full_label": "📄 file1.xlsx",
            "filename": "file1.xlsx",
            "depth": 0,
        },
        {
            "kind": "child",
            "path": r"C:\cases\file1.xlsx",
            "key": "metadata",
            "label": "🧬 Metadati",
            "full_label": "🧬 Metadati",
            "filename": "file1.xlsx",
            "depth": 1,
        },
        {
            "kind": "child",
            "path": r"C:\cases\file1.xlsx",
            "key": "hashes",
            "label": "🔐 Hash",
            "full_label": "🔐 Hash",
            "filename": "file1.xlsx",
            "depth": 1,
        },
        {
            "kind": "child",
            "path": r"C:\cases\file1.xlsx",
            "key": "risk_score",
            "label": "⚠️ Risk score",
            "full_label": "⚠️ Risk score",
            "filename": "file1.xlsx",
            "depth": 1,
        },
        {
            "kind": "child",
            "path": r"C:\cases\file1.xlsx",
            "key": "indicators",
            "label": "📋 Indicatori",
            "full_label": "📋 Indicatori",
            "filename": "file1.xlsx",
            "depth": 1,
        },
        {
            "kind": "child",
            "path": r"C:\cases\file1.xlsx",
            "key": "file_report",
            "label": "🧾 Report file",
            "full_label": "🧾 Report file",
            "filename": "file1.xlsx",
            "depth": 1,
        },
        {
            "kind": "file",
            "path": r"C:\cases\file2.docx",
            "key": "selected_file_overview",
            "label": "📄 file2.docx",
            "full_label": "📄 file2.docx",
            "filename": "file2.docx",
            "depth": 0,
        },
    ]


def test_build_folder_file_sidebar_tree_without_selection_does_not_duplicate_file_name() -> None:
    folder_results = {
        "reports": [
            {"filename": "file1.xlsx", "path": r"C:\cases\file1.xlsx", "status": "OK"},
        ]
    }

    assert build_folder_file_sidebar_tree(folder_results, None) == [
        {
            "kind": "file",
            "path": r"C:\cases\file1.xlsx",
            "key": "selected_file_overview",
            "label": "📄 file1.xlsx",
            "full_label": "📄 file1.xlsx",
            "filename": "file1.xlsx",
            "depth": 0,
        }
    ]


def test_current_report_and_selected_file_report_are_distinct_sidebar_entries() -> None:
    current_analysis_items = dict(SIDEBAR_SECTIONS[1]["items"])
    selected_file_items = dict(build_selected_file_sidebar_items("sample.docx"))

    assert current_analysis_items["technical_report"] == "🧾 Report tecnico"
    assert selected_file_items["file_report"] == "🧾 Report file"


def test_find_folder_report_entry_matches_by_path() -> None:
    folder_results = {
        "reports": [
            {"filename": "sample.docx", "path": r"C:\cases\sample.docx", "status": "OK"},
        ]
    }

    assert find_folder_report_entry(folder_results, r"C:\cases\sample.docx") == {
        "filename": "sample.docx",
        "path": r"C:\cases\sample.docx",
        "status": "OK",
    }
    assert find_folder_report_entry(folder_results, r"C:\cases\missing.docx") is None


def test_build_folder_file_detail_rows_prepare_selected_file_view() -> None:
    report_entry = {
        "filename": "sample.docx",
        "path": r"C:\cases\sample.docx",
        "status": "OK",
        "error": "",
        "office_family": "Word",
        "format_extension": ".docx",
        "creator": "Author A",
        "last_modified_by": "Reviewer B",
        "created": "2026-06-01T08:00:00Z",
        "modified": "2026-06-02T09:30:00Z",
        "risk_score": 12,
        "risk_level": "BASSO",
    }
    results = {
        "file_info": {
            "filename": "sample.docx",
            "path": r"C:\cases\sample.docx",
        },
        "format": {
            "family": "Word",
            "extension": ".docx",
        },
        "metadata": {
            "author": "Author A",
            "last_modified_by": "Reviewer B",
            "created": "2026-06-01T08:00:00Z",
            "modified": "2026-06-02T09:30:00Z",
        },
        "analysis_warnings": ["warning tecnico"],
        "risk_score": 12,
    }

    assert build_folder_file_detail_rows(report_entry, results) == [
        ("Nome file", "sample.docx"),
        ("Percorso", r"C:\cases\sample.docx"),
        ("Famiglia Office", "Word"),
        ("Estensione/formato", ".docx"),
        ("Creatore", "Author A"),
        ("Ultima modifica di", "Reviewer B"),
        ("Data creazione", "2026-06-01T08:00:00Z"),
        ("Data ultima modifica", "2026-06-02T09:30:00Z"),
        ("Risk score", "12"),
        ("Livello", "BASSO"),
        ("Stato", "OK"),
        ("Errore o warning", "warning tecnico"),
    ]


def test_build_folder_file_detail_rows_handle_missing_values_and_errors() -> None:
    report_entry = {
        "filename": "broken.pptx",
        "path": r"C:\cases\broken.pptx",
        "status": "ERROR",
        "error": "Pacchetto non valido",
    }

    rows = build_folder_file_detail_rows(report_entry, None)

    assert rows[0] == ("Nome file", "broken.pptx")
    assert rows[2] == ("Famiglia Office", "N/D")
    assert rows[10] == ("Stato", "ERROR")
    assert rows[11] == ("Errore o warning", "Pacchetto non valido")


def test_build_folder_file_detail_rows_keep_limited_status_context() -> None:
    report_entry = {
        "filename": "legacy.doc",
        "path": r"C:\cases\legacy.doc",
        "status": "LIMITED",
        "office_family": "Word",
        "format_extension": ".doc",
        "creator": "N/D",
        "last_modified_by": "N/D",
        "created": "N/D",
        "modified": "N/D",
        "risk_score": 0,
        "risk_level": "BASSO",
        "error": "",
    }

    rows = build_folder_file_detail_rows(report_entry, None)

    assert rows[2] == ("Famiglia Office", "Word")
    assert rows[3] == ("Estensione/formato", ".doc")
    assert rows[10] == ("Stato", "LIMITED")
    assert rows[11] == ("Errore o warning", "N/D")


def test_prudential_texts_are_present_in_risk_rows() -> None:
    risk_rows = build_risk_score_rows({"risk_score": 0})

    assert PRUDENT_RISK_NOTICE == "Indice tecnico di anomalia documentale, non prova automatica di manomissione."
    assert FOLDER_FILE_DETAIL_NOTICE.startswith("I metadati mostrati sono quelli dichiarati dal file")
    assert START_VIEW_NOTICE.startswith("metanalisys è un supporto tecnico di triage documentale.")
    assert ("Interpretazione prudente", PRUDENT_RISK_NOTICE) in risk_rows
    assert ("Nota obbligatoria", PRUDENT_RISK_NOTICE) in risk_rows
