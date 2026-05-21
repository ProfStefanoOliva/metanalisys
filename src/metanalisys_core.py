import hashlib
import json
import os
import re
import textwrap
import zipfile

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


def build_report_paths(filepath: str) -> dict[str, str]:
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    return {
        "txt": f"{base_name}_forensic_report.txt",
        "json": f"{base_name}_forensic_report.json",
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
