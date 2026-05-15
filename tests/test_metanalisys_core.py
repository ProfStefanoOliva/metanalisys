import hashlib
import json
import zipfile

from pathlib import Path

import pytest

from metanalisys_core import FileAccessError
from metanalisys_core import UnsupportedFormatError
from metanalisys_core import analyze_office_file
from metanalisys_core import compute_file_hashes
from metanalisys_core import ensure_readable_file
from metanalisys_core import format_text_report
from metanalisys_core import get_format_spec
from metanalisys_core import save_json_report


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
    assert "[FORENSIC NOTICE]" in report


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
    sample_path = tmp_path / "synthetic.docx"
    core_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dcterms="http://purl.org/dc/terms/">
    <dc:creator>Synthetic Tester</dc:creator>
    <dcterms:created>2026-05-15T10:00:00Z</dcterms:created>
</cp:coreProperties>
"""
    app_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
    <Application>Microsoft Word</Application>
</Properties>
"""

    with zipfile.ZipFile(sample_path, "w") as archive:
        archive.writestr("docProps/core.xml", core_xml)
        archive.writestr("docProps/app.xml", app_xml)
        archive.writestr("[Content_Types].xml", "<Types></Types>")
        archive.writestr("_rels/.rels", "<Relationships></Relationships>")

    results = analyze_office_file(str(sample_path))
    report = format_text_report(results)

    assert "sha256" in results["hashes"]
    assert "sha512" in results["hashes"]
    assert results["format"]["metadata_support"] == "full"
    assert results["metadata"]["author"] == "Synthetic Tester"
    assert results["metadata"]["created"] == "2026-05-15T10:00:00Z"
    assert "OFFICE FORENSIC ANALYSIS REPORT" in report

