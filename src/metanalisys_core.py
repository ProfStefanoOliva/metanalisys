import hashlib
import json
import os
import re
import textwrap
import zipfile
import csv
import html

from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from io import BytesIO
from typing import Any
from typing import Iterable
from xml.etree import ElementTree as ET

from PIL import Image
from PIL.ExifTags import TAGS


HASH_ALGORITHMS = ("sha256", "sha512")
HASH_CHUNK_SIZE = 1024 * 1024

SOFTWARE_PATTERNS = (
    "Microsoft Office",
    "PowerPoint",
    "Excel",
    "Word",
    "LibreOffice",
    "OpenOffice",
    "Google Docs",
    "Google Sheets",
    "Google Slides",
    "WPS Office",
    "Visio",
    "Keynote",
)

CORE_XML_FIELDS = {
    "author": ".//dc:creator",
    "last_modified_by": ".//cp:lastModifiedBy",
    "created": ".//dcterms:created",
    "modified": ".//dcterms:modified",
    "title": ".//dc:title",
    "subject": ".//dc:subject",
    "description": ".//dc:description",
    "keywords": ".//cp:keywords",
    "revision": ".//cp:revision",
}

CORE_XML_NAMESPACES = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dcterms": "http://purl.org/dc/terms/",
}

RISK_WEIGHTS = {
    "multiple_authors": 10,
    "multiple_user_paths": 15,
    "multiple_software": 15,
    "embedded_files": 15,
    "multiple_image_software": 15,
    "macro_enabled_vba": 15,
    "non_macro_enabled_vba": 60,
    "ooxml_modified_before_created": 40,
    "filesystem_ooxml_modified_delta": 20,
}

MACRO_ENABLED_EXTENSIONS = {
    ".docm",
    ".dotm",
    ".xlsm",
    ".xltm",
    ".xlam",
    ".pptm",
    ".potm",
    ".ppsm",
    ".vsdm",
    ".vstm",
}

NON_MACRO_ENABLED_EXTENSIONS = {
    ".docx",
    ".dotx",
    ".xlsx",
    ".xltx",
    ".pptx",
    ".potx",
    ".ppsx",
    ".vsdx",
    ".vstx",
}

FILESYSTEM_OOXML_MODIFIED_DELTA_DAYS = 365
FOLDER_SUMMARY_CSV_FIELDS = [
    "filename",
    "path",
    "office_family",
    "format_extension",
    "creator",
    "created",
    "last_modified_by",
    "modified",
    "risk_score",
    "risk_level",
    "status",
    "error",
]


@dataclass(frozen=True)
class OfficeFormatSpec:
    """Describe a recognized Office extension and its current analysis scope.

    Fields identify file family, container type and declared support level.
    The structure documents technical coverage only and does not imply
    forensic completeness or evidentiary validity.
    """

    extension: str
    family: str
    label: str
    container: str
    metadata_support: str
    notes: str


OFFICE_FORMATS = {
    ".docx": OfficeFormatSpec(".docx", "Word", "Word Document", "ooxml", "full", "Open XML metadata extraction is supported."),
    ".docm": OfficeFormatSpec(".docm", "Word", "Word Macro-Enabled Document", "ooxml", "full", "Open XML metadata extraction is supported; macro presence is reported."),
    ".dotx": OfficeFormatSpec(".dotx", "Word", "Word Template", "ooxml", "full", "Open XML metadata extraction is supported."),
    ".dotm": OfficeFormatSpec(".dotm", "Word", "Word Macro-Enabled Template", "ooxml", "full", "Open XML metadata extraction is supported; macro presence is reported."),
    ".xlsx": OfficeFormatSpec(".xlsx", "Excel", "Excel Workbook", "ooxml", "full", "Open XML metadata extraction is supported."),
    ".xlsm": OfficeFormatSpec(".xlsm", "Excel", "Excel Macro-Enabled Workbook", "ooxml", "full", "Open XML metadata extraction is supported; macro presence is reported."),
    ".xltx": OfficeFormatSpec(".xltx", "Excel", "Excel Template", "ooxml", "full", "Open XML metadata extraction is supported."),
    ".xltm": OfficeFormatSpec(".xltm", "Excel", "Excel Macro-Enabled Template", "ooxml", "full", "Open XML metadata extraction is supported; macro presence is reported."),
    ".xlam": OfficeFormatSpec(".xlam", "Excel", "Excel Add-In", "ooxml", "full", "Open XML metadata extraction is supported; macro presence is reported."),
    ".pptx": OfficeFormatSpec(".pptx", "PowerPoint", "PowerPoint Presentation", "ooxml", "full", "Open XML metadata extraction is supported."),
    ".pptm": OfficeFormatSpec(".pptm", "PowerPoint", "PowerPoint Macro-Enabled Presentation", "ooxml", "full", "Open XML metadata extraction is supported; macro presence is reported."),
    ".potx": OfficeFormatSpec(".potx", "PowerPoint", "PowerPoint Template", "ooxml", "full", "Open XML metadata extraction is supported."),
    ".potm": OfficeFormatSpec(".potm", "PowerPoint", "PowerPoint Macro-Enabled Template", "ooxml", "full", "Open XML metadata extraction is supported; macro presence is reported."),
    ".ppsx": OfficeFormatSpec(".ppsx", "PowerPoint", "PowerPoint Slide Show", "ooxml", "full", "Open XML metadata extraction is supported."),
    ".ppsm": OfficeFormatSpec(".ppsm", "PowerPoint", "PowerPoint Macro-Enabled Slide Show", "ooxml", "full", "Open XML metadata extraction is supported; macro presence is reported."),
    ".vsdx": OfficeFormatSpec(".vsdx", "Visio", "Visio Drawing", "ooxml", "full", "Open XML metadata extraction is supported."),
    ".vsdm": OfficeFormatSpec(".vsdm", "Visio", "Visio Macro-Enabled Drawing", "ooxml", "full", "Open XML metadata extraction is supported; macro presence is reported."),
    ".vstx": OfficeFormatSpec(".vstx", "Visio", "Visio Template", "ooxml", "full", "Open XML metadata extraction is supported."),
    ".vstm": OfficeFormatSpec(".vstm", "Visio", "Visio Macro-Enabled Template", "ooxml", "full", "Open XML metadata extraction is supported; macro presence is reported."),
    ".doc": OfficeFormatSpec(".doc", "Word", "Word Legacy Document", "ole", "limited", "Legacy OLE metadata parsing is not implemented; only file-level analysis is available."),
    ".dot": OfficeFormatSpec(".dot", "Word", "Word Legacy Template", "ole", "limited", "Legacy OLE metadata parsing is not implemented; only file-level analysis is available."),
    ".xls": OfficeFormatSpec(".xls", "Excel", "Excel Legacy Workbook", "ole", "limited", "Legacy OLE metadata parsing is not implemented; only file-level analysis is available."),
    ".xlt": OfficeFormatSpec(".xlt", "Excel", "Excel Legacy Template", "ole", "limited", "Legacy OLE metadata parsing is not implemented; only file-level analysis is available."),
    ".ppt": OfficeFormatSpec(".ppt", "PowerPoint", "PowerPoint Legacy Presentation", "ole", "limited", "Legacy OLE metadata parsing is not implemented; only file-level analysis is available."),
    ".pot": OfficeFormatSpec(".pot", "PowerPoint", "PowerPoint Legacy Template", "ole", "limited", "Legacy OLE metadata parsing is not implemented; only file-level analysis is available."),
    ".pps": OfficeFormatSpec(".pps", "PowerPoint", "PowerPoint Legacy Slide Show", "ole", "limited", "Legacy OLE metadata parsing is not implemented; only file-level analysis is available."),
}

GUI_FILE_FILTERS = [
    ("Office Files", " ".join(f"*{ext}" for ext in OFFICE_FORMATS)),
    ("Word", "*.doc *.dot *.docx *.docm *.dotx *.dotm"),
    ("Excel", "*.xls *.xlt *.xlsx *.xlsm *.xltx *.xltm *.xlam"),
    ("PowerPoint", "*.ppt *.pot *.pps *.pptx *.pptm *.potx *.potm *.ppsx *.ppsm"),
    ("Visio", "*.vsdx *.vsdm *.vstx *.vstm"),
]


class MetanalisysError(Exception):
    """Base exception for analysis errors."""


class FileAccessError(MetanalisysError):
    """Raised when a file cannot be read safely."""


class UnsupportedFormatError(MetanalisysError):
    """Raised when the provided extension is not recognized."""


class InvalidOfficeFileError(MetanalisysError):
    """Raised when a recognized OOXML file is not a valid ZIP package."""


def get_format_spec(filepath: str) -> OfficeFormatSpec:
    """Return the registered Office format specification for a file path.

    Args:
        filepath: Path whose extension is used for format lookup.
    Returns:
        The matching OfficeFormatSpec entry.
    Raises:
        UnsupportedFormatError: If the extension is not recognized.
    Limits:
        Recognition is extension-based and is not a forensic validation of
        actual file content.
    """

    extension = os.path.splitext(filepath)[1].lower()
    spec = OFFICE_FORMATS.get(extension)
    if spec is None:
        raise UnsupportedFormatError(extension)
    return spec


def ensure_readable_file(filepath: str) -> str:
    """Validate that a target path exists and can be opened in read-only mode.

    Args:
        filepath: User-supplied path to inspect.
    Returns:
        Absolute normalized path for later analysis.
    Raises:
        FileAccessError: If the path is invalid, missing or unreadable.
    Limits:
        This check reduces access errors but does not prevent operating system
        metadata such as access time from changing during later reads.
    """

    if not filepath or not isinstance(filepath, str):
        raise FileAccessError("Percorso file non valido.")
    normalized_path = os.path.abspath(filepath)
    if not os.path.exists(normalized_path):
        raise FileAccessError("Il file specificato non esiste.")
    if not os.path.isfile(normalized_path):
        raise FileAccessError("Il percorso specificato non Ã¨ un file.")
    try:
        with open(normalized_path, "rb"):
            pass
    except FileNotFoundError as exc:
        raise FileAccessError("Il file specificato non esiste.") from exc
    except PermissionError as exc:
        raise FileAccessError("Permessi insufficienti per leggere il file.") from exc
    except OSError as exc:
        raise FileAccessError(f"Impossibile accedere al file: {exc}") from exc
    return normalized_path


def ensure_existing_folder(folder_path: str) -> str:
    """Validate that a target path exists and is an accessible directory."""

    if not folder_path or not isinstance(folder_path, str):
        raise FileAccessError("Percorso cartella non valido.")
    normalized_path = os.path.abspath(folder_path)
    if not os.path.exists(normalized_path):
        raise FileAccessError("La cartella specificata non esiste.")
    if not os.path.isdir(normalized_path):
        raise FileAccessError("Il percorso specificato non è una cartella.")
    try:
        os.listdir(normalized_path)
    except PermissionError as exc:
        raise FileAccessError("Permessi insufficienti per leggere la cartella.") from exc
    except OSError as exc:
        raise FileAccessError(f"Impossibile accedere alla cartella: {exc}") from exc
    return normalized_path


def compute_file_hashes(filepath: str, algorithms: Iterable[str] = HASH_ALGORITHMS) -> dict[str, str]:
    """Compute streaming file hashes without loading the whole file in memory.

    Args:
        filepath: Path to the file to hash.
        algorithms: Iterable of hashlib algorithm names to apply.
    Returns:
        Mapping of algorithm name to hexadecimal digest.
    Raises:
        FileAccessError: If the file cannot be read safely.
    Limits:
        Hashes identify the bytes read at analysis time but do not, by
        themselves, establish chain of custody or evidentiary provenance.
    """

    hashers = {name: hashlib.new(name) for name in algorithms}
    try:
        with open(filepath, "rb") as file_handle:
            while chunk := file_handle.read(HASH_CHUNK_SIZE):
                for hasher in hashers.values():
                    hasher.update(chunk)
    except FileNotFoundError as exc:
        raise FileAccessError("Il file specificato non esiste.") from exc
    except PermissionError as exc:
        raise FileAccessError("Permessi insufficienti per leggere il file.") from exc
    except OSError as exc:
        raise FileAccessError(f"Errore durante il calcolo dell'hash: {exc}") from exc
    return {name: hasher.hexdigest() for name, hasher in hashers.items()}


def build_base_results(filepath: str, spec: OfficeFormatSpec, hashes: dict[str, str]) -> dict[str, Any]:
    return {
        "file_info": {},
        "hashes": hashes,
        "format": {
            "extension": spec.extension,
            "family": spec.family,
            "label": spec.label,
            "container": spec.container,
            "metadata_support": spec.metadata_support,
            "notes": spec.notes,
        },
        "metadata": {},
        "extended_metadata": {},
        "relationships": [],
        "embedded_files": [],
        "images": [],
        "software_detected": [],
        "authors_detected": [],
        "user_paths": [],
        "suspicious_indicators": [],
        "analysis_warnings": [],
        "risk_score": 0,
    }


def _normalize_datetime_for_comparison(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _parse_metadata_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return _normalize_datetime_for_comparison(value)
    if not isinstance(value, str):
        return None

    normalized = value.strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"

    try:
        return _normalize_datetime_for_comparison(datetime.fromisoformat(normalized))
    except ValueError:
        return None


class OfficeForensicAnalyzer:
    def __init__(self, filepath: str):
        self.filepath = ensure_readable_file(filepath)
        self.spec = get_format_spec(self.filepath)
        self.results = build_base_results(
            filepath=self.filepath,
            spec=self.spec,
            hashes=compute_file_hashes(self.filepath),
        )
        self.filename = os.path.basename(self.filepath)

    def add_indicator(self, text: str, score: int) -> None:
        self.results["suspicious_indicators"].append(
            {
                "indicator": text,
                "score": score,
            }
        )
        self.results["risk_score"] += score

    def add_warning(self, text: str) -> None:
        if text not in self.results["analysis_warnings"]:
            self.results["analysis_warnings"].append(text)

    def analyze_file_info(self) -> None:
        stat = os.stat(self.filepath)
        self.results["file_info"] = {
            "filename": self.filename,
            "path": self.filepath,
            "extension": self.spec.extension,
            "size_bytes": stat.st_size,
            "created": str(datetime.fromtimestamp(stat.st_ctime)),
            "modified": str(datetime.fromtimestamp(stat.st_mtime)),
            "accessed": str(datetime.fromtimestamp(stat.st_atime)),
        }

    def read_xml_from_zip(self, zip_ref: zipfile.ZipFile, path: str) -> str | None:
        try:
            return zip_ref.read(path).decode(errors="ignore")
        except KeyError:
            return None
        except UnicodeDecodeError:
            return None

    def analyze_core_metadata(self, zip_ref: zipfile.ZipFile) -> None:
        core_xml = self.read_xml_from_zip(zip_ref, "docProps/core.xml")
        if not core_xml:
            return
        try:
            root = ET.fromstring(core_xml)
        except ET.ParseError:
            self.add_warning("Il file docProps/core.xml non Ã¨ stato interpretato correttamente.")
            return
        metadata = {}
        for key, xpath in CORE_XML_FIELDS.items():
            node = root.find(xpath, CORE_XML_NAMESPACES)
            metadata[key] = node.text if node is not None else None
        self.results["metadata"] = metadata
        authors = []
        for key in ("author", "last_modified_by"):
            value = metadata.get(key)
            if value and value not in authors:
                authors.append(value)
        self.results["authors_detected"] = authors
        if len(authors) > 1:
            self.add_indicator(
                f"Autori multipli rilevati: {authors}",
                RISK_WEIGHTS["multiple_authors"],
            )

    def analyze_extended_metadata(self, zip_ref: zipfile.ZipFile) -> None:
        app_xml = self.read_xml_from_zip(zip_ref, "docProps/app.xml")
        if not app_xml:
            return
        try:
            root = ET.fromstring(app_xml)
        except ET.ParseError:
            self.add_warning("Il file docProps/app.xml non Ã¨ stato interpretato correttamente.")
            return
        metadata = {}
        for child in root:
            tag = child.tag.split("}")[-1]
            metadata[tag] = child.text
        self.results["extended_metadata"] = metadata
        application = metadata.get("Application")
        if application:
            self.results["software_detected"].append(application)

    def analyze_relationships(self, zip_ref: zipfile.ZipFile) -> None:
        rel_files = [name for name in zip_ref.namelist() if name.endswith(".rels")]
        paths = set()
        for rel_file in rel_files:
            data = self.read_xml_from_zip(zip_ref, rel_file)
            if not data:
                continue
            self.results["relationships"].append(rel_file)
            found_paths = re.findall(r"[A-Z]:\\\\[^<>:\"|?*\n\r]+", data)
            paths.update(found_paths)
        self.results["user_paths"] = sorted(paths)
        if len(paths) > 1:
            self.add_indicator(
                f"Percorsi utente multipli rilevati: {len(paths)}",
                RISK_WEIGHTS["multiple_user_paths"],
            )

    def analyze_all_xml(self, zip_ref: zipfile.ZipFile) -> None:
        software_found = set(self.results["software_detected"])
        xml_files = [name for name in zip_ref.namelist() if name.endswith(".xml")]
        for xml_file in xml_files:
            data = self.read_xml_from_zip(zip_ref, xml_file)
            if not data:
                continue
            for pattern in SOFTWARE_PATTERNS:
                if re.search(pattern, data, re.IGNORECASE):
                    software_found.add(pattern)
        self.results["software_detected"] = sorted(software_found)
        if len(software_found) > 1:
            self.add_indicator(
                f"Software multipli rilevati: {sorted(software_found)}",
                RISK_WEIGHTS["multiple_software"],
            )

    def analyze_embedded_files(self, zip_ref: zipfile.ZipFile) -> None:
        embedded = [name for name in zip_ref.namelist() if "embeddings/" in name.lower()]
        self.results["embedded_files"] = embedded
        if embedded:
            self.add_indicator(
                f"File incorporati rilevati: {len(embedded)}",
                RISK_WEIGHTS["embedded_files"],
            )

    def analyze_images(self, zip_ref: zipfile.ZipFile) -> None:
        software_list = set()
        media_files = [name for name in zip_ref.namelist() if "media/" in name.lower()]
        for media in media_files:
            try:
                data = zip_ref.read(media)
                image_info = {"file": media}
                with Image.open(BytesIO(data)) as image:
                    image_info["format"] = image.format
                    exif_data = image.getexif()
                    if exif_data:
                        exif = {}
                        for tag_id, value in exif_data.items():
                            tag = TAGS.get(tag_id, tag_id)
                            exif[str(tag)] = str(value)
                        image_info["exif"] = exif
                        if "Software" in exif:
                            software_list.add(exif["Software"])
                self.results["images"].append(image_info)
            except Exception as exc:
                self.results["images"].append({"file": media, "error": str(exc)})
        if len(software_list) > 1:
            self.add_indicator(
                f"Immagini modificate con software differenti: {sorted(software_list)}",
                RISK_WEIGHTS["multiple_image_software"],
            )

    def analyze_macros(self, zip_ref: zipfile.ZipFile) -> None:
        macros = [name for name in zip_ref.namelist() if "vba" in name.lower()]
        if macros:
            if self.spec.extension in MACRO_ENABLED_EXTENSIONS:
                self.add_indicator(
                    f"Macro VBA rilevate in formato macro-enabled: {len(macros)}",
                    RISK_WEIGHTS["macro_enabled_vba"],
                )
            elif self.spec.extension in NON_MACRO_ENABLED_EXTENSIONS:
                self.add_indicator(
                    f"Macro VBA rilevate in formato non macro-enabled: {len(macros)}",
                    RISK_WEIGHTS["non_macro_enabled_vba"],
                )
            else:
                self.add_indicator(
                    f"Macro VBA rilevate: {len(macros)}",
                    RISK_WEIGHTS["macro_enabled_vba"],
                )

    def analyze_temporal_indicators(self) -> None:
        metadata = self.results.get("metadata", {})
        file_info = self.results.get("file_info", {})

        created_dt = _parse_metadata_datetime(metadata.get("created"))
        modified_dt = _parse_metadata_datetime(metadata.get("modified"))
        filesystem_modified_dt = _parse_metadata_datetime(file_info.get("modified"))

        if created_dt is not None and modified_dt is not None and modified_dt < created_dt:
            self.add_indicator(
                "Incongruenza cronologica OOXML: data modifica precedente alla data creazione",
                RISK_WEIGHTS["ooxml_modified_before_created"],
            )

        if modified_dt is None or filesystem_modified_dt is None:
            return

        delta = abs(filesystem_modified_dt - modified_dt)
        if delta.days > FILESYSTEM_OOXML_MODIFIED_DELTA_DAYS:
            self.add_indicator(
                "Scostamento significativo tra data modifica OOXML e data modifica filesystem",
                RISK_WEIGHTS["filesystem_ooxml_modified_delta"],
            )

    def analyze_ooxml_package(self) -> None:
        try:
            with zipfile.ZipFile(self.filepath, "r") as zip_ref:
                self.analyze_core_metadata(zip_ref)
                self.analyze_extended_metadata(zip_ref)
                self.analyze_relationships(zip_ref)
                self.analyze_all_xml(zip_ref)
                self.analyze_embedded_files(zip_ref)
                self.analyze_images(zip_ref)
                self.analyze_macros(zip_ref)
        except zipfile.BadZipFile as exc:
            raise InvalidOfficeFileError(
                "Il file Ã¨ riconosciuto come Office Open XML ma non Ã¨ un pacchetto ZIP valido o Ã¨ corrotto."
            ) from exc

    def analyze_limited_format(self) -> None:
        self.add_warning(self.spec.notes)

    def run(self) -> dict[str, Any]:
        self.analyze_file_info()
        if self.spec.container == "ooxml":
            self.analyze_ooxml_package()
            self.analyze_temporal_indicators()
        else:
            self.analyze_limited_format()
        return self.results


def analyze_office_file(filepath: str) -> dict[str, Any]:
    """Run the shared Office analysis pipeline and return structured results.

    Args:
        filepath: Path to a recognized Office file.
    Returns:
        Dictionary containing hashes, file information and extracted findings.
    Raises:
        MetanalisysError subclasses for access, format or package errors.
    Limits:
        Output is intended as technical support for preliminary analysis and
        must be interpreted within an authorized procedure.
    """

    analyzer = OfficeForensicAnalyzer(filepath)
    return analyzer.run()


def format_risk_level(score: int) -> str:
    if score < 25:
        return "BASSO"
    if score < 60:
        return "MEDIO"
    if score < 100:
        return "ALTO"
    return "CRITICO"


def _folder_status_from_results(results: dict[str, Any]) -> str:
    metadata_support = results.get("format", {}).get("metadata_support")
    if metadata_support == "limited":
        return "LIMITED"
    return "OK"


def _safe_summary_value(value: Any) -> Any:
    if value in (None, ""):
        return "N/D"
    return value


def _build_folder_summary_row(filepath: str, results: dict[str, Any]) -> dict[str, Any]:
    metadata = results.get("metadata", {})
    score = results.get("risk_score")
    return {
        "filename": os.path.basename(filepath),
        "path": filepath,
        "office_family": _safe_summary_value(results.get("format", {}).get("family")),
        "format_extension": _safe_summary_value(results.get("format", {}).get("extension")),
        "creator": _safe_summary_value(metadata.get("author")),
        "created": _safe_summary_value(metadata.get("created")),
        "last_modified_by": _safe_summary_value(metadata.get("last_modified_by")),
        "modified": _safe_summary_value(metadata.get("modified")),
        "risk_score": score,
        "risk_level": format_risk_level(score) if isinstance(score, int) else "N/D",
        "status": _folder_status_from_results(results),
        "error": "",
    }


def _build_folder_error_row(filepath: str, error_message: str) -> dict[str, Any]:
    extension = os.path.splitext(filepath)[1].lower() or "N/D"
    return {
        "filename": os.path.basename(filepath),
        "path": filepath,
        "office_family": "N/D",
        "format_extension": extension,
        "creator": "N/D",
        "created": "N/D",
        "last_modified_by": "N/D",
        "modified": "N/D",
        "risk_score": None,
        "risk_level": "N/D",
        "status": "ERROR",
        "error": error_message,
    }


def _build_folder_status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"OK": 0, "LIMITED": 0, "ERROR": 0}
    for row in rows:
        status = row.get("status")
        if status in counts:
            counts[status] += 1
    return counts


def _iter_supported_folder_files(folder_path: str) -> list[str]:
    supported_files: list[str] = []
    for entry in os.listdir(folder_path):
        candidate_path = os.path.join(folder_path, entry)
        if not os.path.isfile(candidate_path):
            continue
        extension = os.path.splitext(entry)[1].lower()
        if extension in OFFICE_FORMATS:
            supported_files.append(os.path.abspath(candidate_path))
    return sorted(supported_files, key=lambda path: os.path.basename(path).lower())


def analyze_office_folder(folder_path: str) -> dict[str, Any]:
    """Analyze supported Office files in a folder without recursing subfolders."""

    normalized_folder = ensure_existing_folder(folder_path)
    office_files = _iter_supported_folder_files(normalized_folder)
    rows: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []

    for filepath in office_files:
        try:
            results = analyze_office_file(filepath)
        except Exception as exc:
            error_message = str(exc).strip() or type(exc).__name__
            rows.append(_build_folder_error_row(filepath, error_message))
            reports.append(
                {
                    "filename": os.path.basename(filepath),
                    "path": filepath,
                    "status": "ERROR",
                    "error": error_message,
                }
            )
            continue

        row = _build_folder_summary_row(filepath, results)
        rows.append(row)
        reports.append(
            {
                "filename": os.path.basename(filepath),
                "path": filepath,
                "status": row["status"],
                "error": "",
                "results": results,
            }
        )

    return {
        "folder_path": normalized_folder,
        "generated_at": datetime.now(UTC).isoformat(),
        "total_files": len(office_files),
        "status_counts": _build_folder_status_counts(rows),
        "rows": rows,
        "reports": reports,
    }


def _append_key_values(lines: list[str], section_name: str, values: dict[str, Any]) -> None:
    lines.append(f"\n[{section_name}]\n")
    if not values:
        lines.append("Nessun dato disponibile.")
        return
    for key, value in values.items():
        lines.append(f"{key}: {value}")


def _append_list(lines: list[str], section_name: str, values: list[Any], empty_message: str) -> None:
    lines.append(f"\n[{section_name}]\n")
    if not values:
        lines.append(empty_message)
        return
    for value in values:
        lines.append(f"- {value}")


def _format_risk_score_breakdown(results: dict[str, Any]) -> list[str]:
    indicators = results.get("suspicious_indicators", [])
    lines = ["\n[DETTAGLIO ASSEGNAZIONE PUNTEGGIO]\n"]

    if not indicators:
        lines.append("Nessun punteggio assegnato: non sono stati rilevati indicatori sospetti.")
        return lines

    index_width = len("N.")
    indicator_width = 54
    score_width = len("Punteggio")
    running_width = len("Progressivo")

    lines.append(
        f"{'N.':<{index_width}} | "
        f"{'Indicatore':<{indicator_width}} | "
        f"{'Punteggio':>{score_width}} | "
        f"{'Progressivo':>{running_width}}"
    )
    lines.append(
        f"{'-' * index_width}-+-"
        f"{'-' * indicator_width}-+-"
        f"{'-' * score_width}-+-"
        f"{'-' * running_width}"
    )

    running_total = 0
    for index, item in enumerate(indicators, start=1):
        indicator_text = str(item.get("indicator", ""))
        score = int(item.get("score", 0))
        running_total += score
        wrapped_indicator = textwrap.wrap(
            indicator_text,
            width=indicator_width,
            break_long_words=False,
            break_on_hyphens=False,
        ) or [""]

        lines.append(
            f"{index:<{index_width}} | "
            f"{wrapped_indicator[0]:<{indicator_width}} | "
            f"{score:+>{score_width}} | "
            f"{running_total:>{running_width}}"
        )

        for extra_line in wrapped_indicator[1:]:
            lines.append(
                f"{'':<{index_width}} | "
                f"{extra_line:<{indicator_width}} | "
                f"{'':>{score_width}} | "
                f"{'':>{running_width}}"
            )

    return lines


def format_text_report(results: dict[str, Any]) -> str:
    """Render a human-readable text report from structured analysis results.

    Args:
        results: Analysis dictionary returned by the shared core.
    Returns:
        Plain-text report suitable for CLI output or TXT export.
    Limits:
        The rendered report summarizes technical observations and is not a
        substitute for professional forensic conclusions.
    """

    lines: list[str] = []
    lines.append("=" * 70)
    lines.append("OFFICE FORENSIC ANALYSIS REPORT")
    lines.append("=" * 70)

    _append_key_values(lines, "FILE HASH", results.get("hashes", {}))
    _append_key_values(lines, "FILE INFO", results.get("file_info", {}))
    _append_key_values(lines, "FORMAT SUPPORT", results.get("format", {}))
    _append_key_values(lines, "METADATA", results.get("metadata", {}))
    _append_key_values(lines, "EXTENDED METADATA", results.get("extended_metadata", {}))
    _append_list(lines, "SOFTWARE DETECTED", results.get("software_detected", []), "Nessun software rilevato.")
    _append_list(lines, "AUTHORS DETECTED", results.get("authors_detected", []), "Nessun autore rilevato.")
    _append_list(lines, "USER PATHS", results.get("user_paths", []), "Nessun percorso utente rilevato.")
    _append_list(lines, "RELATIONSHIPS", results.get("relationships", []), "Nessuna relationship rilevata.")
    _append_list(lines, "EMBEDDED FILES", results.get("embedded_files", []), "Nessun file incorporato.")

    lines.append("\n[IMAGES]\n")
    if results.get("images"):
        for image in results["images"]:
            lines.append(f"- File: {image.get('file')}")
            if "format" in image:
                lines.append(f"  Formato: {image['format']}")
            if "error" in image:
                lines.append(f"  Errore: {image['error']}")
    else:
        lines.append("Nessuna immagine trovata.")

    _append_list(
        lines,
        "ANALYSIS WARNINGS",
        results.get("analysis_warnings", []),
        "Nessuna limitazione o anomalia segnalata.",
    )

    lines.append("\n[SUSPICIOUS INDICATORS]\n")
    indicators = results.get("suspicious_indicators", [])
    if not indicators:
        lines.append("Nessun indicatore rilevato.")
    else:
        for item in indicators:
            lines.append(f"- {item['indicator']} (+{item['score']})")

    lines.append("\n[RISK SCORE]\n")
    score = results.get("risk_score", 0)
    lines.append(f"Punteggio: {score}")
    lines.append(f"Livello: {format_risk_level(score)}")
    lines.append(
        "Interpretazione: indice tecnico di anomalia documentale, "
        "non prova automatica di manomissione."
    )
    lines.extend(_format_risk_score_breakdown(results))

    lines.append("\n[FORENSIC NOTICE]\n")
    lines.append(
        "Il report è un supporto tecnico all'analisi dei metadati. "
        "Le conclusioni forensi richiedono procedura autorizzata, "
        "catena di custodia e valutazione professionale."
    )
    return "\n".join(lines)


def _format_folder_summary_table(rows: list[dict[str, Any]]) -> list[str]:
    columns = [
        ("Nome file", "filename", 24),
        ("Famiglia Office", "office_family", 16),
        ("Creatore", "creator", 20),
        ("Data creazione", "created", 20),
        ("Ultimo modificatore", "last_modified_by", 20),
        ("Data ultima modifica", "modified", 20),
        ("Risk score", "risk_score", 10),
        ("Livello", "risk_level", 8),
        ("Status", "status", 8),
    ]
    header = " | ".join(f"{title:<{width}}" for title, _, width in columns)
    separator = "-+-".join("-" * width for _, _, width in columns)
    lines = [header, separator]
    for row in rows:
        values = []
        for _, key, width in columns:
            value = row.get(key)
            if value is None:
                value = "N/D"
            values.append(f"{str(value):<{width}}")
        lines.append(" | ".join(values))
    return lines


def _html_escape(value: Any) -> str:
    if value is None:
        return "N/D"
    return html.escape(str(value))


def _html_badge_class(prefix: str, value: str) -> str:
    normalized = str(value).strip().lower().replace(" ", "-").replace("/", "-")
    return f"{prefix}-{normalized}"


def format_folder_text_report(folder_results: dict[str, Any]) -> str:
    """Render a cumulative plain-text report for a folder analysis."""

    rows = folder_results.get("rows", [])
    status_counts = folder_results.get("status_counts", {})
    reports = folder_results.get("reports", [])
    lines = [
        "=" * 70,
        "OFFICE FOLDER FORENSIC SUMMARY",
        "=" * 70,
        f"Cartella analizzata: {folder_results.get('folder_path', 'N/D')}",
        f"File Office trovati: {folder_results.get('total_files', 0)}",
        f"File con status OK: {status_counts.get('OK', 0)}",
        f"File con status LIMITED: {status_counts.get('LIMITED', 0)}",
        f"File con status ERROR: {status_counts.get('ERROR', 0)}",
        "",
        "[TABELLA RIEPILOGATIVA]",
        "",
    ]

    if rows:
        lines.extend(_format_folder_summary_table(rows))
    else:
        lines.append("Nessun file Office supportato trovato nella cartella indicata.")

    error_reports = [report for report in reports if report.get("status") == "ERROR"]
    if error_reports:
        lines.extend(["", "[ERRORI DI ANALISI]", ""])
        for report in error_reports:
            lines.append(f"- {report.get('filename', 'N/D')}: {report.get('error', 'N/D')}")

    lines.extend(["", "[DETTAGLIO REPORT PER SINGOLO FILE]", ""])
    if not reports:
        lines.append("Nessun file Office supportato da dettagliare.")
    else:
        for report in reports:
            lines.append("-" * 70)
            if report.get("status") == "ERROR":
                lines.append(f"Nome file: {report.get('filename', 'N/D')}")
                lines.append(f"Percorso: {report.get('path', 'N/D')}")
                lines.append(f"Status: {report.get('status', 'N/D')}")
                lines.append(f"Errore: {report.get('error', 'N/D')}")
            else:
                lines.append(format_text_report(report.get("results", {})))

    lines.extend(
        [
            "",
            "[FORENSIC NOTICE]",
            "",
            "Il report di cartella è un supporto tecnico di triage documentale e non costituisce valutazione probatoria.",
        ]
    )
    return "\n".join(lines)


def format_folder_html_report(folder_results: dict[str, Any]) -> str:
    """Render a standalone HTML report for a folder analysis."""

    rows = folder_results.get("rows", [])
    reports = folder_results.get("reports", [])
    status_counts = folder_results.get("status_counts", {})
    error_reports = [report for report in reports if report.get("status") == "ERROR"]

    summary_cards = [
        ("Totale file", folder_results.get("total_files", 0), "summary-card"),
        ("OK", status_counts.get("OK", 0), "summary-card summary-ok"),
        ("LIMITED", status_counts.get("LIMITED", 0), "summary-card summary-limited"),
        ("ERROR", status_counts.get("ERROR", 0), "summary-card summary-error"),
    ]
    summary_cards_html = "\n".join(
        [
            (
                f"<section class=\"{card_class}\">"
                f"<div class=\"summary-label\">{_html_escape(label)}</div>"
                f"<div class=\"summary-value\">{_html_escape(value)}</div>"
                f"</section>"
            )
            for label, value, card_class in summary_cards
        ]
    )

    table_rows_html = ""
    for row in rows:
        risk_level = _safe_summary_value(row.get("risk_level"))
        status = _safe_summary_value(row.get("status"))
        risk_score = row.get("risk_score")
        table_rows_html += (
            "<tr>"
            f"<td>{_html_escape(_safe_summary_value(row.get('filename')))}</td>"
            f"<td>{_html_escape(_safe_summary_value(row.get('office_family')))}</td>"
            f"<td>{_html_escape(_safe_summary_value(row.get('creator')))}</td>"
            f"<td>{_html_escape(_safe_summary_value(row.get('created')))}</td>"
            f"<td>{_html_escape(_safe_summary_value(row.get('last_modified_by')))}</td>"
            f"<td>{_html_escape(_safe_summary_value(row.get('modified')))}</td>"
            f"<td>{_html_escape(risk_score if risk_score is not None else 'N/D')}</td>"
            f"<td><span class=\"badge risk-badge {_html_badge_class('risk', str(risk_level))}\">{_html_escape(risk_level)}</span></td>"
            f"<td><span class=\"badge status-badge {_html_badge_class('status', str(status))}\">{_html_escape(status)}</span></td>"
            "</tr>\n"
        )

    if not table_rows_html:
        table_rows_html = (
            "<tr><td colspan=\"9\" class=\"empty-row\">"
            "Nessun file Office supportato trovato nella cartella indicata."
            "</td></tr>"
        )

    error_section_html = ""
    if error_reports:
        error_rows = "\n".join(
            [
                (
                    "<tr>"
                    f"<td>{_html_escape(report.get('filename', 'N/D'))}</td>"
                    f"<td>{_html_escape(report.get('error', 'N/D'))}</td>"
                    "</tr>"
                )
                for report in error_reports
            ]
        )
        error_section_html = f"""
        <section class="panel">
          <h2>ERRORI DI ANALISI</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Nome file</th>
                  <th>Messaggio errore</th>
                </tr>
              </thead>
              <tbody>
                {error_rows}
              </tbody>
            </table>
          </div>
        </section>
        """

    detail_items_html = ""
    if reports:
        for report in reports:
            filename = _html_escape(report.get("filename", "N/D"))
            status = _safe_summary_value(report.get("status"))
            risk_level = "N/D"
            detail_body = ""
            if report.get("status") == "ERROR":
                detail_body = (
                    "<div class=\"error-card\">"
                    f"<p><strong>Nome file:</strong> {filename}</p>"
                    f"<p><strong>Percorso:</strong> {_html_escape(report.get('path', 'N/D'))}</p>"
                    f"<p><strong>Errore:</strong> {_html_escape(report.get('error', 'N/D'))}</p>"
                    "</div>"
                )
            else:
                results = report.get("results", {})
                risk_level = format_risk_level(results.get("risk_score", 0))
                detail_body = (
                    "<pre class=\"report-pre\">"
                    f"{html.escape(format_text_report(results))}"
                    "</pre>"
                )
            detail_items_html += f"""
            <details class="detail-item">
              <summary>
                <span class="detail-name">{filename}</span>
                <span class="detail-badges">
                  <span class="badge risk-badge {_html_badge_class('risk', str(risk_level))}">{_html_escape(risk_level)}</span>
                  <span class="badge status-badge {_html_badge_class('status', str(status))}">{_html_escape(status)}</span>
                </span>
              </summary>
              <div class="detail-content">
                {detail_body}
              </div>
            </details>
            """
    else:
        detail_items_html = "<p class=\"empty-row\">Nessun file Office supportato da dettagliare.</p>"

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OFFICE FOLDER FORENSIC SUMMARY</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0f1720;
      --panel: #182331;
      --border: #2c4158;
      --text: #e6edf4;
      --muted: #aebdcb;
      --accent: #1f6aa5;
      --shadow: 0 18px 40px rgba(0, 0, 0, 0.24);
      --radius: 16px;
      --radius-sm: 10px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Tahoma, sans-serif;
      background:
        radial-gradient(circle at top left, rgba(31, 106, 165, 0.18), transparent 30%),
        linear-gradient(180deg, #0b1219 0%, var(--bg) 100%);
      color: var(--text);
      line-height: 1.5;
    }}
    .container {{
      max-width: 1400px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .hero, .panel {{
      background: linear-gradient(180deg, rgba(31, 45, 61, 0.95), rgba(24, 35, 49, 0.98));
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }}
    .hero {{
      padding: 28px;
      margin-bottom: 24px;
    }}
    h1, h2 {{
      margin: 0 0 14px;
      letter-spacing: 0.02em;
    }}
    h1 {{ font-size: 1.95rem; }}
    h2 {{ font-size: 1.15rem; }}
    .meta {{
      color: var(--muted);
      margin: 8px 0;
    }}
    .notice {{
      margin-top: 18px;
      padding: 14px 16px;
      border-left: 4px solid var(--accent);
      background: rgba(31, 106, 165, 0.12);
      border-radius: var(--radius-sm);
    }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin: 24px 0;
    }}
    .summary-card {{
      padding: 18px;
      background: rgba(11, 18, 25, 0.45);
      border: 1px solid var(--border);
      border-radius: 14px;
    }}
    .summary-ok {{ border-color: rgba(31, 138, 91, 0.45); }}
    .summary-limited {{ border-color: rgba(183, 138, 31, 0.45); }}
    .summary-error {{ border-color: rgba(183, 74, 74, 0.45); }}
    .summary-label {{
      color: var(--muted);
      font-size: 0.92rem;
      margin-bottom: 6px;
    }}
    .summary-value {{
      font-size: 1.9rem;
      font-weight: 700;
    }}
    .panel {{
      padding: 22px;
      margin-bottom: 24px;
    }}
    .table-wrap {{
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 980px;
    }}
    th, td {{
      text-align: left;
      padding: 12px 14px;
      border-bottom: 1px solid rgba(44, 65, 88, 0.7);
      vertical-align: top;
    }}
    th {{
      color: #dbe8f4;
      background: rgba(31, 106, 165, 0.14);
      font-weight: 600;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.82rem;
      font-weight: 700;
      border: 1px solid transparent;
      white-space: nowrap;
    }}
    .risk-nd, .status-n-d {{
      background: rgba(174, 189, 203, 0.12);
      color: var(--muted);
      border-color: rgba(174, 189, 203, 0.25);
    }}
    .risk-basso {{
      background: rgba(47, 143, 107, 0.18);
      color: #b9f0d7;
      border-color: rgba(47, 143, 107, 0.45);
    }}
    .risk-medio {{
      background: rgba(155, 124, 47, 0.18);
      color: #f0ddb0;
      border-color: rgba(155, 124, 47, 0.45);
    }}
    .risk-alto {{
      background: rgba(179, 93, 47, 0.18);
      color: #f3cfb8;
      border-color: rgba(179, 93, 47, 0.45);
    }}
    .risk-critico {{
      background: rgba(177, 61, 75, 0.18);
      color: #f4bcc4;
      border-color: rgba(177, 61, 75, 0.45);
    }}
    .status-ok {{
      background: rgba(31, 138, 91, 0.18);
      color: #b9f0d7;
      border-color: rgba(31, 138, 91, 0.45);
    }}
    .status-limited {{
      background: rgba(183, 138, 31, 0.18);
      color: #f0ddb0;
      border-color: rgba(183, 138, 31, 0.45);
    }}
    .status-error {{
      background: rgba(183, 74, 74, 0.18);
      color: #f4bcc4;
      border-color: rgba(183, 74, 74, 0.45);
    }}
    details {{
      border: 1px solid var(--border);
      border-radius: 14px;
      background: rgba(11, 18, 25, 0.4);
      margin-bottom: 14px;
      overflow: hidden;
    }}
    summary {{
      cursor: pointer;
      list-style: none;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 16px 18px;
    }}
    summary::-webkit-details-marker {{
      display: none;
    }}
    .detail-name {{
      font-weight: 600;
      word-break: break-word;
    }}
    .detail-badges {{
      display: inline-flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}
    .detail-content {{
      padding: 0 18px 18px;
    }}
    .report-pre {{
      margin: 0;
      padding: 16px;
      background: rgba(8, 13, 19, 0.72);
      border: 1px solid rgba(44, 65, 88, 0.65);
      border-radius: 12px;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-word;
      color: #dce8f4;
      font-family: Consolas, "Courier New", monospace;
      font-size: 0.9rem;
    }}
    .error-card {{
      padding: 16px;
      border-radius: 12px;
      background: rgba(183, 74, 74, 0.09);
      border: 1px solid rgba(183, 74, 74, 0.28);
    }}
    .empty-row {{
      color: var(--muted);
    }}
    @media (max-width: 800px) {{
      .container {{ padding: 20px 14px 32px; }}
      .hero, .panel {{ padding: 18px; }}
      summary {{
        flex-direction: column;
        align-items: flex-start;
      }}
      .detail-badges {{
        justify-content: flex-start;
      }}
    }}
  </style>
</head>
<body>
  <main class="container">
    <section class="hero">
      <h1>OFFICE FOLDER FORENSIC SUMMARY</h1>
      <p class="meta"><strong>Cartella analizzata:</strong> {_html_escape(folder_results.get('folder_path', 'N/D'))}</p>
      <p class="meta"><strong>Data/ora generazione:</strong> {_html_escape(folder_results.get('generated_at', 'N/D'))}</p>
      <div class="summary-grid">
        {summary_cards_html}
      </div>
      <div class="notice">
        Il report è un supporto tecnico di triage documentale. Il risk score è un indice tecnico di anomalia documentale e non costituisce prova automatica di manomissione.
      </div>
    </section>

    <section class="panel">
      <h2>TABELLA RIEPILOGATIVA</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Nome file</th>
              <th>Famiglia Office</th>
              <th>Creatore</th>
              <th>Data creazione</th>
              <th>Ultimo modificatore</th>
              <th>Data ultima modifica</th>
              <th>Risk score</th>
              <th>Livello</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {table_rows_html}
          </tbody>
        </table>
      </div>
    </section>

    {error_section_html}

    <section class="panel">
      <h2>DETTAGLIO REPORT PER SINGOLO FILE</h2>
      {detail_items_html}
    </section>
  </main>
</body>
</html>
"""


def build_report_paths(filepath: str) -> dict[str, str]:
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    return {
        "txt": f"{base_name}_forensic_report.txt",
        "json": f"{base_name}_forensic_report.json",
    }


def build_folder_report_paths(folder_path: str) -> dict[str, str]:
    folder_name = os.path.basename(os.path.normpath(folder_path))
    return {
        "txt": f"{folder_name}_folder_summary.txt",
        "csv": f"{folder_name}_folder_summary.csv",
        "json": f"{folder_name}_folder_summary.json",
        "html": f"{folder_name}_folder_summary.html",
    }


def save_text_report(report_text: str, destination: str) -> None:
    """Persist a rendered text report to disk using UTF-8 encoding.

    Args:
        report_text: Plain-text report content to save.
        destination: Output path for the TXT report.
    Returns:
        None.
    Limits:
        Saving a report preserves output content only; storage controls and
        retention requirements remain the operator's responsibility.
    """

    with open(destination, "w", encoding="utf-8") as file_handle:
        file_handle.write(report_text)


def save_json_report(results: dict[str, Any], destination: str) -> None:
    """Serialize structured analysis results to a JSON report on disk.

    Args:
        results: Analysis dictionary to serialize.
        destination: Output path for the JSON file.
    Returns:
        None.
    Limits:
        JSON export reflects the collected technical data and does not add any
        forensic certification or legal status to the report.
    """

    with open(destination, "w", encoding="utf-8") as file_handle:
        json.dump(results, file_handle, indent=4, ensure_ascii=False)


def save_folder_text_report(folder_results: dict[str, Any], destination: str) -> None:
    save_text_report(format_folder_text_report(folder_results), destination)


def save_folder_csv_report(folder_results: dict[str, Any], destination: str) -> None:
    with open(destination, "w", encoding="utf-8-sig", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=FOLDER_SUMMARY_CSV_FIELDS)
        writer.writeheader()
        for row in folder_results.get("rows", []):
            writer.writerow({field: row.get(field) for field in FOLDER_SUMMARY_CSV_FIELDS})


def save_folder_json_report(folder_results: dict[str, Any], destination: str) -> None:
    json_payload = {
        "folder_path": folder_results.get("folder_path"),
        "generated_at": folder_results.get("generated_at"),
        "total_files": folder_results.get("total_files", 0),
        "status_counts": folder_results.get("status_counts", {}),
        "rows": folder_results.get("rows", []),
        "reports": [],
    }

    for report in folder_results.get("reports", []):
        if report.get("status") == "ERROR":
            json_payload["reports"].append(
                {
                    "filename": report.get("filename"),
                    "path": report.get("path"),
                    "status": report.get("status"),
                    "error": report.get("error"),
                }
            )
        else:
            json_payload["reports"].append(report.get("results", {}))

    with open(destination, "w", encoding="utf-8") as file_handle:
        json.dump(json_payload, file_handle, indent=4, ensure_ascii=False)


def save_folder_html_report(html_text: str, destination: str) -> None:
    save_text_report(html_text, destination)
