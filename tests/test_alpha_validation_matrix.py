import zipfile

from pathlib import Path

import pytest

from metanalisys_core import analyze_office_file
from metanalisys_core import format_text_report


CORE_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dcterms="http://purl.org/dc/terms/">
    <dc:creator>{author}</dc:creator>
    <dcterms:created>{created}</dcterms:created>
    <dc:title>{title}</dc:title>
</cp:coreProperties>
"""

APP_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
    <Application>{application}</Application>
</Properties>
"""


def build_synthetic_ooxml_package(
    output_path: Path,
    *,
    document_xml_path: str,
    document_xml_body: str,
    author: str,
    created: str,
    title: str,
    application: str,
    extra_entries: dict[str, bytes | str] | None = None,
) -> Path:
    core_xml = CORE_XML_TEMPLATE.format(
        author=author,
        created=created,
        title=title,
    )
    app_xml = APP_XML_TEMPLATE.format(application=application)

    with zipfile.ZipFile(output_path, "w") as archive:
        archive.writestr("docProps/core.xml", core_xml)
        archive.writestr("docProps/app.xml", app_xml)
        archive.writestr("[Content_Types].xml", "<Types></Types>")
        archive.writestr("_rels/.rels", "<Relationships></Relationships>")
        archive.writestr(document_xml_path, document_xml_body)
        for entry_path, entry_content in (extra_entries or {}).items():
            archive.writestr(entry_path, entry_content)

    return output_path


@pytest.mark.parametrize(
    (
        "case_id",
        "filename",
        "document_xml_path",
        "document_xml_body",
        "expected_family",
        "expected_application",
        "expected_author",
        "expected_created",
    ),
    [
        (
            "VAL-001",
            "val_001.docx",
            "word/document.xml",
            "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'/>",
            "Word",
            "Microsoft Word",
            "Synthetic DOCX Author",
            "2026-05-15T08:00:00Z",
        ),
        (
            "VAL-002",
            "val_002.xlsx",
            "xl/workbook.xml",
            "<workbook xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'/>",
            "Excel",
            "Microsoft Excel",
            "Synthetic XLSX Author",
            "2026-05-15T09:00:00Z",
        ),
        (
            "VAL-003",
            "val_003.pptx",
            "ppt/presentation.xml",
            "<p:presentation xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'/>",
            "PowerPoint",
            "Microsoft PowerPoint",
            "Synthetic PPTX Author",
            "2026-05-15T10:00:00Z",
        ),
    ],
)
def test_alpha_validation_matrix_synthetic_ooxml_cases(
    tmp_path: Path,
    case_id: str,
    filename: str,
    document_xml_path: str,
    document_xml_body: str,
    expected_family: str,
    expected_application: str,
    expected_author: str,
    expected_created: str,
) -> None:
    sample_path = build_synthetic_ooxml_package(
        tmp_path / filename,
        document_xml_path=document_xml_path,
        document_xml_body=document_xml_body,
        author=expected_author,
        created=expected_created,
        title=case_id,
        application=expected_application,
    )

    results = analyze_office_file(str(sample_path))
    report = format_text_report(results)

    assert "hashes" in results, f"{case_id}: missing hashes section"
    assert "sha256" in results["hashes"], f"{case_id}: missing sha256"
    assert "sha512" in results["hashes"], f"{case_id}: missing sha512"

    assert results["format"]["metadata_support"] == "full"
    assert results["format"]["family"] == expected_family
    assert results["file_info"]["filename"] == sample_path.name
    assert results["file_info"]["extension"] == sample_path.suffix
    assert results["metadata"]["author"] == expected_author
    assert results["metadata"]["created"] == expected_created

    assert "OFFICE FORENSIC ANALYSIS REPORT" in report
    assert "[FILE HASH]" in report
    assert "[FORMAT SUPPORT]" in report
    assert expected_author in report


@pytest.mark.parametrize(
    (
        "case_id",
        "filename",
        "document_xml_path",
        "document_xml_body",
        "vba_entry_path",
        "expected_family",
        "expected_application",
        "expected_author",
        "expected_created",
    ),
    [
        (
            "VAL-004-DOCM",
            "val_004.docm",
            "word/document.xml",
            "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'/>",
            "word/vbaProject.bin",
            "Word",
            "Microsoft Word",
            "Synthetic DOCM Author",
            "2026-05-16T08:00:00Z",
        ),
        (
            "VAL-004-XLSM",
            "val_004.xlsm",
            "xl/workbook.xml",
            "<workbook xmlns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'/>",
            "xl/vbaProject.bin",
            "Excel",
            "Microsoft Excel",
            "Synthetic XLSM Author",
            "2026-05-16T09:00:00Z",
        ),
        (
            "VAL-004-PPTM",
            "val_004.pptm",
            "ppt/presentation.xml",
            "<p:presentation xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'/>",
            "ppt/vbaProject.bin",
            "PowerPoint",
            "Microsoft PowerPoint",
            "Synthetic PPTM Author",
            "2026-05-16T10:00:00Z",
        ),
    ],
)
def test_alpha_validation_matrix_macro_enabled_placeholder_cases(
    tmp_path: Path,
    case_id: str,
    filename: str,
    document_xml_path: str,
    document_xml_body: str,
    vba_entry_path: str,
    expected_family: str,
    expected_application: str,
    expected_author: str,
    expected_created: str,
) -> None:
    sample_path = build_synthetic_ooxml_package(
        tmp_path / filename,
        document_xml_path=document_xml_path,
        document_xml_body=document_xml_body,
        author=expected_author,
        created=expected_created,
        title=case_id,
        application=expected_application,
        extra_entries={
            vba_entry_path: b"SYNTHETIC-VBA-PLACEHOLDER-NON-EXECUTABLE",
        },
    )

    results = analyze_office_file(str(sample_path))
    report = format_text_report(results)

    assert "hashes" in results, f"{case_id}: missing hashes section"
    assert "sha256" in results["hashes"], f"{case_id}: missing sha256"
    assert "sha512" in results["hashes"], f"{case_id}: missing sha512"

    assert results["format"]["metadata_support"] == "full"
    assert results["format"]["family"] == expected_family
    assert results["file_info"]["filename"] == sample_path.name
    assert results["file_info"]["extension"] == sample_path.suffix

    indicators = results.get("suspicious_indicators", [])
    assert any("Macro VBA rilevate" in item.get("indicator", "") for item in indicators), (
        f"{case_id}: macro indicator not found in suspicious_indicators"
    )

    assert "OFFICE FORENSIC ANALYSIS REPORT" in report
    assert "[SUSPICIOUS INDICATORS]" in report
    assert "Macro VBA rilevate" in report
