from __future__ import annotations

from pathlib import Path
from typing import Any

from metanalisys_core import format_risk_level

PRUDENT_RISK_NOTICE = (
    "Indice tecnico di anomalia documentale, non prova automatica di manomissione."
)
TRIAGE_SUPPORT_TEXT = "Supporto tecnico di triage documentale."
START_VIEW_MESSAGE = (
    "Seleziona un file Office o una cartella per avviare un'analisi preliminare dei metadati."
)
START_VIEW_NOTICE = (
    "metanalisys è un supporto tecnico di triage documentale. Il risk score è un indice "
    "tecnico di anomalia documentale, non una prova automatica di manomissione."
)
NO_ANALYSIS_MESSAGE = "Nessuna analisi disponibile."
NO_INDICATORS_MESSAGE = (
    "Nessun indicatore strutturato disponibile. Consulta il report tecnico completo per il "
    "dettaglio prudente dell'analisi."
)
FOLDER_FILE_DETAIL_NOTICE = (
    "I metadati mostrati sono quelli dichiarati dal file o estratti dal contenitore supportato. "
    "Il risk score è un indice tecnico di anomalia documentale, non una prova automatica di manomissione."
)

FOLDER_SUMMARY_TABLE_COLUMNS = [
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
FOLDER_STATUS_ORDER = ("OK", "LIMITED", "ERROR")
SIDEBAR_SECTIONS = [
    {
        "title": "AZIONI",
        "items": [
            ("new_analysis", "🏠 Nuova analisi"),
            ("open_file", "📄 Apri file"),
            ("open_folder", "📂 Apri cartella"),
            ("run_analysis", "▶️ Avvia analisi"),
            ("save_report", "💾 Salva report"),
        ],
    },
    {
        "title": "ANALISI CORRENTE",
        "items": [
            ("dashboard", "📊 Dashboard"),
            ("technical_report", "🧾 Report tecnico"),
        ],
    },
    {
        "title": "AIUTO",
        "items": [
            ("information", "❓ Informazioni"),
        ],
    },
]
SELECTED_FILE_DETAIL_ITEMS = [
    ("selected_file_overview", "📄 {filename}"),
    ("metadata", "🧬 Metadati"),
    ("hashes", "🔐 Hash"),
    ("risk_score", "⚠️ Risk score"),
    ("indicators", "📋 Indicatori"),
    ("file_report", "🧾 Report file"),
]
SELECTED_FILE_DETAIL_CHILD_ITEMS = [
    ("metadata", "🧬 Metadati"),
    ("hashes", "🔐 Hash"),
    ("risk_score", "⚠️ Risk score"),
    ("indicators", "📋 Indicatori"),
    ("file_report", "🧾 Report file"),
]


def get_about_text() -> str:
    return (
        "metanalisys\n\n"
        "Analisi preliminare dei metadati Office.\n"
        "Supporto tecnico di triage documentale.\n"
        "Supporto analisi cartella con report TXT/CSV/JSON/HTML.\n\n"
        "Copyright © 2026 Stefano Oliva\n"
        "Licenza: GNU General Public License v3.0"
    )


def normalize_folder_display_value(value: object) -> str:
    if value in (None, ""):
        return "N/D"
    return str(value)


def get_folder_summary_counts(folder_results: dict[str, object]) -> dict[str, int]:
    rows = folder_results.get("rows", [])
    if isinstance(rows, list):
        counts = {status: 0 for status in FOLDER_STATUS_ORDER}
        for row in rows:
            if isinstance(row, dict):
                status = str(row.get("status", "")).upper()
                if status in counts:
                    counts[status] += 1
        return counts
    return {status: 0 for status in FOLDER_STATUS_ORDER}


def build_folder_summary_table_rows(folder_results: dict[str, object]) -> list[dict[str, str]]:
    prepared_rows: list[dict[str, str]] = []
    for row in folder_results.get("rows", []):
        if not isinstance(row, dict):
            continue
        prepared_rows.append(
            {
                "path": normalize_folder_display_value(row.get("path")),
                "filename": normalize_folder_display_value(row.get("filename")),
                "office_family": normalize_folder_display_value(row.get("office_family")),
                "creator": normalize_folder_display_value(row.get("creator")),
                "last_modified_by": normalize_folder_display_value(row.get("last_modified_by")),
                "created": normalize_folder_display_value(row.get("created")),
                "modified": normalize_folder_display_value(row.get("modified")),
                "risk_score": normalize_folder_display_value(row.get("risk_score")),
                "risk_level": normalize_folder_display_value(row.get("risk_level")),
                "status": normalize_folder_display_value(row.get("status")),
            }
        )
    return prepared_rows


def build_single_file_status_support(results: dict[str, Any]) -> str:
    metadata_support = normalize_folder_display_value(
        results.get("format", {}).get("metadata_support")
    ).lower()
    if metadata_support == "full":
        return "OK / supporto completo"
    if metadata_support == "limited":
        return "LIMITED / supporto limitato"
    return "N/D"


def build_single_file_dashboard_rows(results: dict[str, Any]) -> list[tuple[str, str]]:
    file_info = results.get("file_info", {})
    metadata = results.get("metadata", {})
    format_info = results.get("format", {})
    warnings = results.get("analysis_warnings", [])
    score = results.get("risk_score", 0)

    return [
        ("Nome file", normalize_folder_display_value(file_info.get("filename"))),
        ("Percorso", normalize_folder_display_value(file_info.get("path"))),
        ("Famiglia Office", normalize_folder_display_value(format_info.get("family"))),
        ("Estensione/formato", normalize_folder_display_value(format_info.get("extension"))),
        ("Creatore", normalize_folder_display_value(metadata.get("author"))),
        (
            "Ultima modifica di",
            normalize_folder_display_value(metadata.get("last_modified_by")),
        ),
        ("Data creazione", normalize_folder_display_value(metadata.get("created"))),
        ("Data ultima modifica", normalize_folder_display_value(metadata.get("modified"))),
        ("Risk score", normalize_folder_display_value(score)),
        ("Livello", normalize_folder_display_value(format_risk_level(score))),
        ("Stato/supporto", build_single_file_status_support(results)),
        (
            "Warning",
            normalize_folder_display_value(" | ".join(str(item) for item in warnings) if warnings else None),
        ),
    ]


def format_sidebar_filename_label(filename: object, max_chars: int = 28) -> str:
    normalized = normalize_folder_display_value(filename)
    if normalized == "N/D":
        return "📄 N/D"
    if max_chars <= 0:
        return "📄 ..."
    if len(normalized) <= max_chars:
        return f"📄 {normalized}"
    if max_chars <= 3:
        return "📄 ..."
    return f"📄 {normalized[:max_chars - 3]}..."


def build_folder_file_sidebar_label(
    filename: object,
    path: object | None = None,
    *,
    max_chars: int = 28,
) -> str:
    if filename not in (None, ""):
        return format_sidebar_filename_label(filename, max_chars=max_chars)
    if path not in (None, ""):
        return format_sidebar_filename_label(Path(str(path)).name, max_chars=max_chars)
    return format_sidebar_filename_label(None, max_chars=max_chars)


def build_folder_file_sidebar_items(folder_results: dict[str, Any]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for report in folder_results.get("reports", []):
        if not isinstance(report, dict):
            continue
        path = normalize_folder_display_value(report.get("path"))
        filename = normalize_folder_display_value(report.get("filename"))
        items.append(
            {
                "path": path,
                "filename": filename,
                "label": build_folder_file_sidebar_label(report.get("filename"), report.get("path")),
                "full_label": build_folder_file_sidebar_label(
                    report.get("filename"),
                    report.get("path"),
                    max_chars=10_000,
                ),
                "status": normalize_folder_display_value(report.get("status")),
            }
        )
    return items


def has_folder_sidebar_files(folder_results: dict[str, Any]) -> bool:
    return bool(build_folder_file_sidebar_items(folder_results))


def find_folder_report_entry(folder_results: dict[str, Any], target_path: str) -> dict[str, Any] | None:
    normalized_target = str(target_path).strip()
    for report in folder_results.get("reports", []):
        if not isinstance(report, dict):
            continue
        if str(report.get("path", "")).strip() == normalized_target:
            return report
    return None


def build_folder_file_detail_rows(
    report_entry: dict[str, Any],
    results: dict[str, Any] | None = None,
) -> list[tuple[str, str]]:
    results = results or {}
    file_info = results.get("file_info", {})
    metadata = results.get("metadata", {})
    format_info = results.get("format", {})
    warnings = results.get("analysis_warnings", [])
    path_value = file_info.get("path") or report_entry.get("path")
    filename_value = file_info.get("filename") or report_entry.get("filename")
    score = results.get("risk_score")
    level = format_risk_level(score) if isinstance(score, int) else report_entry.get("risk_level")
    warning_text = " | ".join(str(item) for item in warnings) if warnings else None
    error_text = report_entry.get("error") or warning_text

    return [
        ("Nome file", normalize_folder_display_value(filename_value)),
        ("Percorso", normalize_folder_display_value(path_value)),
        ("Famiglia Office", normalize_folder_display_value(format_info.get("family") or report_entry.get("office_family"))),
        ("Estensione/formato", normalize_folder_display_value(format_info.get("extension") or report_entry.get("format_extension"))),
        ("Creatore", normalize_folder_display_value(metadata.get("author") or report_entry.get("creator"))),
        (
            "Ultima modifica di",
            normalize_folder_display_value(metadata.get("last_modified_by") or report_entry.get("last_modified_by")),
        ),
        ("Data creazione", normalize_folder_display_value(metadata.get("created") or report_entry.get("created"))),
        (
            "Data ultima modifica",
            normalize_folder_display_value(metadata.get("modified") or report_entry.get("modified")),
        ),
        ("Risk score", normalize_folder_display_value(score if score is not None else report_entry.get("risk_score"))),
        ("Livello", normalize_folder_display_value(level)),
        ("Stato", normalize_folder_display_value(report_entry.get("status"))),
        ("Errore o warning", normalize_folder_display_value(error_text)),
    ]


def build_metadata_view_rows(results: dict[str, Any]) -> list[tuple[str, str]]:
    metadata = results.get("metadata", {})
    extended_metadata = results.get("extended_metadata", {})
    rows = [
        ("Creatore dichiarato", normalize_folder_display_value(metadata.get("author"))),
        (
            "Ultima modifica dichiarata da",
            normalize_folder_display_value(metadata.get("last_modified_by")),
        ),
        ("Data creazione dichiarata", normalize_folder_display_value(metadata.get("created"))),
        (
            "Data ultima modifica dichiarata",
            normalize_folder_display_value(metadata.get("modified")),
        ),
        ("Titolo dichiarato", normalize_folder_display_value(metadata.get("title"))),
        ("Oggetto dichiarato", normalize_folder_display_value(metadata.get("subject"))),
        ("Descrizione dichiarata", normalize_folder_display_value(metadata.get("description"))),
        ("Applicazione dichiarata", normalize_folder_display_value(extended_metadata.get("Application"))),
        ("Società dichiarata", normalize_folder_display_value(extended_metadata.get("Company"))),
        (
            "Numero pagine/slides dichiarato",
            normalize_folder_display_value(
                extended_metadata.get("Pages") or extended_metadata.get("Slides")
            ),
        ),
    ]
    return rows


def build_hash_view_rows(results: dict[str, Any]) -> list[tuple[str, str]]:
    hashes = results.get("hashes", {})
    return [
        ("SHA-256", normalize_folder_display_value(hashes.get("sha256"))),
        ("SHA-512", normalize_folder_display_value(hashes.get("sha512"))),
    ]


def build_risk_score_rows(results: dict[str, Any]) -> list[tuple[str, str]]:
    score = results.get("risk_score", 0)
    return [
        ("Punteggio", normalize_folder_display_value(score)),
        ("Livello", normalize_folder_display_value(format_risk_level(score))),
        ("Interpretazione prudente", PRUDENT_RISK_NOTICE),
        ("Nota obbligatoria", PRUDENT_RISK_NOTICE),
    ]


def build_indicator_rows(results: dict[str, Any]) -> list[tuple[str, str]]:
    indicators = results.get("suspicious_indicators", [])
    prepared_rows: list[tuple[str, str]] = []
    for item in indicators:
        if not isinstance(item, dict):
            continue
        prepared_rows.append(
            (
                normalize_folder_display_value(item.get("indicator")),
                normalize_folder_display_value(item.get("score")),
            )
        )
    return prepared_rows


def build_folder_dashboard_cards(folder_results: dict[str, Any]) -> list[tuple[str, str, str]]:
    counts = get_folder_summary_counts(folder_results)
    total_files = normalize_folder_display_value(folder_results.get("total_files"))
    return [
        ("Totale file", total_files, "#203244"),
        ("OK", str(counts["OK"]), "#1f4f3d"),
        ("LIMITED", str(counts["LIMITED"]), "#5b4721"),
        ("ERROR", str(counts["ERROR"]), "#5a2f35"),
    ]


def build_selected_file_sidebar_items(selected_filename: object | None) -> list[tuple[str, str]]:
    normalized_filename = normalize_folder_display_value(selected_filename)
    if normalized_filename == "N/D":
        return []
    return [
        (key, label.format(filename=normalized_filename))
        for key, label in SELECTED_FILE_DETAIL_ITEMS
    ]


def build_selected_file_detail_child_items() -> list[tuple[str, str]]:
    return list(SELECTED_FILE_DETAIL_CHILD_ITEMS)


def build_folder_file_sidebar_tree(
    folder_results: dict[str, Any],
    selected_path: str | None,
) -> list[dict[str, str | int]]:
    tree_entries: list[dict[str, str | int]] = []
    for item in build_folder_file_sidebar_items(folder_results):
        path = item["path"]
        tree_entries.append(
            {
                "kind": "file",
                "path": path,
                "key": "selected_file_overview",
                "label": item["label"],
                "full_label": item["full_label"],
                "filename": item["filename"],
                "depth": 0,
            }
        )
        if selected_path and path == selected_path:
            for key, label in build_selected_file_detail_child_items():
                tree_entries.append(
                    {
                        "kind": "child",
                        "path": path,
                        "key": key,
                        "label": label,
                        "full_label": label,
                        "filename": item["filename"],
                        "depth": 1,
                    }
                )
    return tree_entries
