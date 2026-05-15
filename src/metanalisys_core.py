import hashlib
import json
import os
import re
import zipfile

from dataclasses import dataclass
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


@dataclass(frozen=True)
class OfficeFormatSpec:
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
    extension = os.path.splitext(filepath)[1].lower()
    spec = OFFICE_FORMATS.get(extension)
    if spec is None:
        raise UnsupportedFormatError(extension)
    return spec


def ensure_readable_file(filepath: str) -> str:
    if not filepath or not isinstance(filepath, str):
        raise FileAccessError("Percorso file non valido.")
    normalized_path = os.path.abspath(filepath)
    if not os.path.exists(normalized_path):
        raise FileAccessError("Il file specificato non esiste.")
    if not os.path.isfile(normalized_path):
        raise FileAccessError("Il percorso specificato non è un file.")
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
            self.add_warning("Il file docProps/core.xml non è stato interpretato correttamente.")
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
            self.add_indicator(f"Autori multipli rilevati: {authors}", 30)

    def analyze_extended_metadata(self, zip_ref: zipfile.ZipFile) -> None:
        app_xml = self.read_xml_from_zip(zip_ref, "docProps/app.xml")
        if not app_xml:
            return
        try:
            root = ET.fromstring(app_xml)
        except ET.ParseError:
            self.add_warning("Il file docProps/app.xml non è stato interpretato correttamente.")
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
            self.add_indicator(f"Percorsi utente multipli rilevati: {len(paths)}", 25)

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
            self.add_indicator(f"Software multipli rilevati: {sorted(software_found)}", 35)

    def analyze_embedded_files(self, zip_ref: zipfile.ZipFile) -> None:
        embedded = [name for name in zip_ref.namelist() if "embeddings/" in name.lower()]
        self.results["embedded_files"] = embedded
        if embedded:
            self.add_indicator(f"File incorporati rilevati: {len(embedded)}", 10)

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
            self.add_indicator(f"Immagini modificate con software differenti: {sorted(software_list)}", 20)

    def analyze_macros(self, zip_ref: zipfile.ZipFile) -> None:
        macros = [name for name in zip_ref.namelist() if "vba" in name.lower()]
        if macros:
            self.add_indicator(f"Macro VBA rilevate: {len(macros)}", 15)

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
                "Il file è riconosciuto come Office Open XML ma non è un pacchetto ZIP valido o è corrotto."
            ) from exc

    def analyze_limited_format(self) -> None:
        self.add_warning(self.spec.notes)

    def run(self) -> dict[str, Any]:
        self.analyze_file_info()
        if self.spec.container == "ooxml":
            self.analyze_ooxml_package()
        else:
            self.analyze_limited_format()
        return self.results


def analyze_office_file(filepath: str) -> dict[str, Any]:
    analyzer = OfficeForensicAnalyzer(filepath)
    return analyzer.run()


def format_risk_level(score: int) -> str:
    if score < 20:
        return "BASSO"
    if score < 50:
        return "MEDIO"
    return "ALTO"


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


def format_text_report(results: dict[str, Any]) -> str:
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
    return "\n".join(lines)


def build_report_paths(filepath: str) -> dict[str, str]:
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    return {
        "txt": f"{base_name}_forensic_report.txt",
        "json": f"{base_name}_forensic_report.json",
    }


def save_text_report(report_text: str, destination: str) -> None:
    with open(destination, "w", encoding="utf-8") as file_handle:
        file_handle.write(report_text)


def save_json_report(results: dict[str, Any], destination: str) -> None:
    with open(destination, "w", encoding="utf-8") as file_handle:
        json.dump(results, file_handle, indent=4, ensure_ascii=False)

