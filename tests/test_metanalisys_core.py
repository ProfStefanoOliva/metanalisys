import hashlib
import json
import os
import zipfile

from pathlib import Path

import pytest

from metanalisys_core import FileAccessError
from metanalisys_core import UnsupportedFormatError
from metanalisys_core import analyze_office_file
from metanalisys_core import compute_file_hashes
from metanalisys_core import ensure_readable_file
from metanalisys_core import format_risk_level
from metanalisys_core import format_text_report
from metanalisys_core import get_format_spec
from metanalisys_core import save_json_report


CORE_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dcterms="http://purl.org/dc/terms/">
    {creator_block}
    {last_modified_by_block}
    {created_block}
    {modified_block}
    <dc:title>{title}</dc:title>
</cp:coreProperties>
"""

APP_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
    <Application>{application}</Application>
</Properties>
"""


def build_core_xml(
    *,
    author: str | None = None,
    last_modified_by: str | None = None,
    created: str | None = None,
    modified: str | None = None,
    title: str = "Synthetic",
) -> str:
    return CORE_XML_TEMPLATE.format(
        creator_block=f"<dc:creator>{author}</dc:creator>" if author else "",
        last_modified_by_block=f"<cp:lastModifiedBy>{last_modified_by}</cp:lastModifiedBy>" if last_modified_by else "",
        created_block=f"<dcterms:created>{created}</dcterms:created>" if created else "",
        modified_block=f"<dcterms:modified>{modified}</dcterms:modified>" if modified else "",
        title=title,
    )


def build_synthetic_ooxml_package(
    output_path: Path,
    *,
    document_xml_path: str = "word/document.xml",
    document_xml_body: str = "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'/>",
    core_xml: str | None = None,
    application: str | None = None,
    extra_entries: dict[str, bytes | str] | None = None,
) -> Path:
    with zipfile.ZipFile(output_path, "w") as archive:
        archive.writestr("docProps/core.xml", core_xml or build_core_xml())
        if application:
            archive.writestr("docProps/app.xml", APP_XML_TEMPLATE.format(application=application))
        archive.writestr("[Content_Types].xml", "<Types></Types>")
        archive.writestr("_rels/.rels", "<Relationships></Relationships>")
        archive.writestr(document_xml_path, document_xml_body)
        for entry_path, entry_content in (extra_entries or {}).items():
            archive.writestr(entry_path, entry_content)
    return output_path


def test_compute_file_hashes_known_content_and_no_modification(tmp_path: Path) -> None:
    sample_path = tmp_path / "sample.bin"
    content = b"metanalisys-test-content\nwith-known-bytes"
    sample_path.write_bytes(content)

    stat_before = sample_path.stat()
    hashes = compute_file_hashes(str(sample_path))
    stat_after = sample_path.stat()

    assert hashes["sha256"] == hashlib.sha256(content).hexdigest()
    assert hashes["sha512"] == hashlib.sha512(content).hexdigest()
    assert sample_path.read_bytes() == content
    assert stat_after.st_size == stat_before.st_size
    assert stat_after.st_mtime_ns == stat_before.st_mtime_ns


@pytest.mark.parametrize(
    ("filename", "expected_family", "expected_support"),
    [
        ("document.docx", "Word", "full"),
        ("sheet.xlsx", "Excel", "full"),
        ("slides.pptx", "PowerPoint", "full"),
        ("diagram.vsdx", "Visio", "full"),
        ("legacy.doc", "Word", "limited"),
    ],
)
def test_get_format_spec_supported_extensions(
    filename: str,
    expected_family: str,
    expected_support: str,
) -> None:
    spec = get_format_spec(filename)

    assert spec.family == expected_family
    assert spec.metadata_support == expected_support


def test_get_format_spec_unsupported_extension() -> None:
    with pytest.raises(UnsupportedFormatError):
        get_format_spec("notes.txt")


def test_ensure_readable_file_existing_path(tmp_path: Path) -> None:
    sample_path = tmp_path / "existing.docx"
    sample_path.write_bytes(b"content")

    normalized = ensure_readable_file(str(sample_path))

    assert Path(normalized) == sample_path.resolve()


def test_ensure_readable_file_missing_path(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.docx"

    with pytest.raises(FileAccessError) as exc_info:
        ensure_readable_file(str(missing_path))

    assert "non esiste" in str(exc_info.value)


@pytest.mark.parametrize("invalid_value", ["", None])
def test_ensure_readable_file_invalid_path(invalid_value) -> None:
    with pytest.raises(FileAccessError) as exc_info:
        ensure_readable_file(invalid_value)  # type: ignore[arg-type]

    assert "Percorso file non valido" in str(exc_info.value)


@pytest.mark.parametrize(
    ("score", "expected_level"),
    [
        (0, "BASSO"),
        (24, "BASSO"),
        (25, "MEDIO"),
        (59, "MEDIO"),
        (60, "ALTO"),
        (99, "ALTO"),
        (100, "CRITICO"),
    ],
)
def test_format_risk_level_thresholds(score: int, expected_level: str) -> None:
    assert format_risk_level(score) == expected_level


def test_format_text_report_contains_required_sections() -> None:
    results = {
        "hashes": {"sha256": "abc", "sha512": "def"},
        "file_info": {"filename": "sample.docx", "extension": ".docx"},
        "format": {
            "extension": ".docx",
            "family": "Word",
            "label": "Word Document",
            "container": "ooxml",
            "metadata_support": "full",
            "notes": "Open XML metadata extraction is supported.",
        },
        "metadata": {},
        "extended_metadata": {},
        "software_detected": [],
        "authors_detected": [],
        "user_paths": [],
        "relationships": [],
        "embedded_files": [],
        "images": [],
        "analysis_warnings": [],
        "suspicious_indicators": [],
        "risk_score": 0,
    }

    report = format_text_report(results)

    assert "[FILE HASH]" in report
    assert "[FILE INFO]" in report
    assert "[FORMAT SUPPORT]" in report
    assert "[RISK SCORE]" in report
    assert "[DETTAGLIO ASSEGNAZIONE PUNTEGGIO]" in report
    assert "[FORENSIC NOTICE]" in report
    assert (
        "Interpretazione: indice tecnico di anomalia documentale, "
        "non prova automatica di manomissione."
    ) in report


def test_format_text_report_without_suspicious_indicators_shows_empty_breakdown() -> None:
    results = {
        "hashes": {"sha256": "abc", "sha512": "def"},
        "file_info": {"filename": "sample.docx", "extension": ".docx"},
        "format": {
            "extension": ".docx",
            "family": "Word",
            "label": "Word Document",
            "container": "ooxml",
            "metadata_support": "full",
            "notes": "Open XML metadata extraction is supported.",
        },
        "metadata": {},
        "extended_metadata": {},
        "software_detected": [],
        "authors_detected": [],
        "user_paths": [],
        "relationships": [],
        "embedded_files": [],
        "images": [],
        "analysis_warnings": [],
        "suspicious_indicators": [],
        "risk_score": 0,
    }

    report = format_text_report(results)

    assert "[RISK SCORE]" in report
    assert "[DETTAGLIO ASSEGNAZIONE PUNTEGGIO]" in report
    assert "Nessun punteggio assegnato: non sono stati rilevati indicatori sospetti." in report


def test_format_text_report_single_indicator_shows_score_breakdown() -> None:
    results = {
        "hashes": {"sha256": "abc", "sha512": "def"},
        "file_info": {"filename": "sample.docx", "extension": ".docx"},
        "format": {
            "extension": ".docx",
            "family": "Word",
            "label": "Word Document",
            "container": "ooxml",
            "metadata_support": "full",
            "notes": "Open XML metadata extraction is supported.",
        },
        "metadata": {},
        "extended_metadata": {},
        "software_detected": [],
        "authors_detected": [],
        "user_paths": [],
        "relationships": [],
        "embedded_files": [],
        "images": [],
        "analysis_warnings": [],
        "suspicious_indicators": [
            {"indicator": "Macro VBA rilevate in formato macro-enabled: 1", "score": 15},
        ],
        "risk_score": 15,
    }

    report = format_text_report(results)

    assert "[DETTAGLIO ASSEGNAZIONE PUNTEGGIO]" in report
    assert "Macro VBA rilevate in formato macro-enabled: 1" in report
    assert "+15" in report
    assert "Progressivo" in report


def test_format_text_report_multiple_indicators_show_correct_progressive() -> None:
    results = {
        "hashes": {"sha256": "abc", "sha512": "def"},
        "file_info": {"filename": "sample.docx", "extension": ".docx"},
        "format": {
            "extension": ".docx",
            "family": "Word",
            "label": "Word Document",
            "container": "ooxml",
            "metadata_support": "full",
            "notes": "Open XML metadata extraction is supported.",
        },
        "metadata": {},
        "extended_metadata": {},
        "software_detected": [],
        "authors_detected": [],
        "user_paths": [],
        "relationships": [],
        "embedded_files": [],
        "images": [],
        "analysis_warnings": [],
        "suspicious_indicators": [
            {"indicator": "Autori multipli rilevati: ['A', 'B']", "score": 10},
            {"indicator": "Macro VBA rilevate in formato macro-enabled: 1", "score": 15},
            {
                "indicator": (
                    "Indicatore molto lungo creato per verificare il wrapping del testo "
                    "nella tabella dettagliata del punteggio senza perdere informazioni."
                ),
                "score": 10,
            },
        ],
        "risk_score": 35,
    }

    report = format_text_report(results)

    assert "[RISK SCORE]" in report
    assert "Punteggio: 35" in report
    assert "Livello: MEDIO" in report
    assert "[DETTAGLIO ASSEGNAZIONE PUNTEGGIO]" in report
    assert "Autori multipli rilevati: ['A', 'B']" in report
    assert "Macro VBA rilevate in formato macro-enabled: 1" in report
    assert "Indicatore molto lungo creato per verificare il wrapping" in report
    assert "del punteggio senza perdere informazioni." in report


def test_save_json_report_writes_hashes_key(tmp_path: Path) -> None:
    results = {
        "hashes": {"sha256": "abc", "sha512": "def"},
        "file_info": {"filename": "sample.docx"},
    }
    output_path = tmp_path / "report.json"

    save_json_report(results, str(output_path))

    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert "hashes" in loaded
    assert loaded["hashes"]["sha256"] == "abc"


def test_analyze_office_file_with_synthetic_ooxml_package(tmp_path: Path) -> None:
    sample_path = build_synthetic_ooxml_package(
        tmp_path / "synthetic.docx",
        core_xml=build_core_xml(
            author="Synthetic Tester",
            created="2026-05-15T10:00:00Z",
        ),
        application="Microsoft Word",
    )

    results = analyze_office_file(str(sample_path))
    report = format_text_report(results)

    assert "sha256" in results["hashes"]
    assert "sha512" in results["hashes"]
    assert results["format"]["metadata_support"] == "full"
    assert results["metadata"]["author"] == "Synthetic Tester"
    assert results["metadata"]["created"] == "2026-05-15T10:00:00Z"
    assert "OFFICE FORENSIC ANALYSIS REPORT" in report


def test_multiple_authors_indicator_uses_prudent_score(tmp_path: Path) -> None:
    sample_path = build_synthetic_ooxml_package(
        tmp_path / "authors.docx",
        core_xml=build_core_xml(
            author="Author A",
            last_modified_by="Author B",
        ),
    )

    results = analyze_office_file(str(sample_path))

    assert results["risk_score"] == 10
    assert results["suspicious_indicators"][0]["score"] == 10
    assert "Autori multipli rilevati" in results["suspicious_indicators"][0]["indicator"]


def test_multiple_software_indicator_uses_prudent_score(tmp_path: Path) -> None:
    sample_path = build_synthetic_ooxml_package(
        tmp_path / "software.docx",
        document_xml_body=(
            "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
            "LibreOffice export"
            "</w:document>"
        ),
        application="Acme Writer",
    )

    results = analyze_office_file(str(sample_path))

    assert results["risk_score"] == 15
    assert results["suspicious_indicators"][0]["score"] == 15
    assert "Software multipli rilevati" in results["suspicious_indicators"][0]["indicator"]


def test_macro_enabled_format_uses_low_weight(tmp_path: Path) -> None:
    sample_path = build_synthetic_ooxml_package(
        tmp_path / "macro_enabled.docm",
        extra_entries={"word/vbaProject.bin": b"SYNTHETIC-NON-EXECUTABLE"},
    )

    results = analyze_office_file(str(sample_path))

    assert results["risk_score"] == 15
    assert results["suspicious_indicators"][0]["score"] == 15
    assert "macro-enabled" in results["suspicious_indicators"][0]["indicator"]


def test_macro_in_non_macro_enabled_format_uses_high_weight(tmp_path: Path) -> None:
    sample_path = build_synthetic_ooxml_package(
        tmp_path / "macro_mismatch.docx",
        extra_entries={"word/vbaProject.bin": b"SYNTHETIC-NON-EXECUTABLE"},
    )

    results = analyze_office_file(str(sample_path))

    assert results["risk_score"] == 60
    assert results["suspicious_indicators"][0]["score"] == 60
    assert "non macro-enabled" in results["suspicious_indicators"][0]["indicator"]


def test_temporal_inconsistency_modified_before_created_uses_expected_score(tmp_path: Path) -> None:
    sample_path = build_synthetic_ooxml_package(
        tmp_path / "temporal.docx",
        core_xml=build_core_xml(
            created="2026-05-20T10:00:00Z",
            modified="2026-05-19T10:00:00Z",
        ),
    )

    results = analyze_office_file(str(sample_path))

    assert results["risk_score"] == 40
    assert results["suspicious_indicators"][0]["score"] == 40
    assert "Incongruenza cronologica OOXML" in results["suspicious_indicators"][0]["indicator"]


def test_filesystem_and_ooxml_modified_delta_uses_expected_score(tmp_path: Path) -> None:
    sample_path = build_synthetic_ooxml_package(
        tmp_path / "filesystem_delta.docx",
        core_xml=build_core_xml(
            modified="2020-01-01T00:00:00Z",
        ),
    )
    os.utime(sample_path, (sample_path.stat().st_atime, 1767225600))

    results = analyze_office_file(str(sample_path))

    assert results["risk_score"] == 20
    assert results["suspicious_indicators"][0]["score"] == 20
    assert (
        "Scostamento significativo tra data modifica OOXML e data modifica filesystem"
        in results["suspicious_indicators"][0]["indicator"]
    )


@pytest.mark.parametrize("modified_value", [None, "", "not-a-date", "2026/05/20 10:00:00"])
def test_temporal_checks_ignore_unparseable_metadata_values(tmp_path: Path, modified_value: str | None) -> None:
    sample_path = build_synthetic_ooxml_package(
        tmp_path / "unparseable.docx",
        core_xml=build_core_xml(
            created="2026-05-20T10:00:00Z",
            modified=modified_value,
        ),
    )

    results = analyze_office_file(str(sample_path))

    assert not any(
        "Incongruenza cronologica OOXML" in item["indicator"]
        or "Scostamento significativo tra data modifica OOXML e data modifica filesystem" in item["indicator"]
        for item in results["suspicious_indicators"]
    )
