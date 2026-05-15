import os
import sys
import json
import zipfile
import shutil
import re
import tempfile

from datetime import datetime
from xml.etree import ElementTree as ET

from PIL import Image
from PIL.ExifTags import TAGS

# ============================================================
# ESTENSIONI SUPPORTATE
# ============================================================

SUPPORTED_EXTENSIONS = {
    ".docx",
    ".xlsx",
    ".pptx",
    ".vsdx",
    ".docm",
    ".xlsm",
    ".pptm",
    ".dotx",
    ".xltx",
    ".potx"
}

# ============================================================
# ANALIZZATORE FORENSE OFFICE
# ============================================================

class OfficeForensicAnalyzer:

    def __init__(self, filepath, output_mode):

        self.filepath = filepath
        self.output_mode = output_mode

        self.filename = os.path.basename(filepath)

        self.results = {
            "file_info": {},
            "metadata": {},
            "extended_metadata": {},
            "relationships": [],
            "embedded_files": [],
            "images": [],
            "software_detected": [],
            "user_paths": [],
            "authors_detected": [],
            "suspicious_indicators": [],
            "risk_score": 0
        }

    # ========================================================
    # AGGIUNTA INDICATORI
    # ========================================================

    def add_indicator(self, text, score):

        self.results["suspicious_indicators"].append({
            "indicator": text,
            "score": score
        })

        self.results["risk_score"] += score

    # ========================================================
    # INFO FILE
    # ========================================================

    def analyze_file_info(self):

        stat = os.stat(self.filepath)

        self.results["file_info"] = {
            "filename": self.filename,
            "extension": os.path.splitext(self.filename)[1],
            "size_bytes": stat.st_size,
            "created": str(datetime.fromtimestamp(stat.st_ctime)),
            "modified": str(datetime.fromtimestamp(stat.st_mtime)),
            "accessed": str(datetime.fromtimestamp(stat.st_atime))
        }

    # ========================================================
    # LETTURA XML
    # ========================================================

    def read_xml_from_zip(self, zip_ref, path):

        try:
            return zip_ref.read(path).decode(errors="ignore")

        except:
            return None

    # ========================================================
    # ANALISI CORE METADATA
    # ========================================================

    def analyze_core_metadata(self):

        with zipfile.ZipFile(self.filepath, 'r') as z:

            core_xml = self.read_xml_from_zip(
                z,
                "docProps/core.xml"
            )

            if not core_xml:
                return

            root = ET.fromstring(core_xml)

            ns = {
                'dc': 'http://purl.org/dc/elements/1.1/',
                'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
                'dcterms': 'http://purl.org/dc/terms/'
            }

            metadata = {}

            fields = {
                "author": ".//dc:creator",
                "last_modified_by": ".//cp:lastModifiedBy",
                "created": ".//dcterms:created",
                "modified": ".//dcterms:modified",
                "title": ".//dc:title",
                "subject": ".//dc:subject",
                "description": ".//dc:description",
                "keywords": ".//cp:keywords",
                "revision": ".//cp:revision"
            }

            for key, xpath in fields.items():

                try:

                    node = root.find(xpath, ns)

                    metadata[key] = (
                        node.text if node is not None else None
                    )

                except:
                    metadata[key] = None

            self.results["metadata"] = metadata

            authors = set()

            if metadata.get("author"):
                authors.add(metadata["author"])

            if metadata.get("last_modified_by"):
                authors.add(metadata["last_modified_by"])

            self.results["authors_detected"] = list(authors)

            if len(authors) > 1:

                self.add_indicator(
                    f"Autori multipli rilevati: {list(authors)}",
                    30
                )

    # ========================================================
    # ANALISI APP XML
    # ========================================================

    def analyze_extended_metadata(self):

        with zipfile.ZipFile(self.filepath, 'r') as z:

            app_xml = self.read_xml_from_zip(
                z,
                "docProps/app.xml"
            )

            if not app_xml:
                return

            root = ET.fromstring(app_xml)

            metadata = {}

            for child in root:

                tag = child.tag.split("}")[-1]

                metadata[tag] = child.text

            self.results["extended_metadata"] = metadata

            application = metadata.get("Application")

            if application:

                self.results["software_detected"].append(
                    application
                )

    # ========================================================
    # ANALISI RELATIONSHIPS
    # ========================================================

    def analyze_relationships(self):

        with zipfile.ZipFile(self.filepath, 'r') as z:

            rel_files = [
                f for f in z.namelist()
                if ".rels" in f
            ]

            paths = set()

            for rel in rel_files:

                data = self.read_xml_from_zip(z, rel)

                if not data:
                    continue

                self.results["relationships"].append(rel)

                found_paths = re.findall(
                    r"[A-Z]:\\\\[^<>:\"|?*\n\r]+",
                    data
                )

                for p in found_paths:
                    paths.add(p)

            self.results["user_paths"] = list(paths)

            if len(paths) > 1:

                self.add_indicator(
                    f"Percorsi utente multipli rilevati: "
                    f"{len(paths)}",
                    25
                )

    # ========================================================
    # ANALISI XML
    # ========================================================

    def analyze_all_xml(self):

        software_found = set()

        with zipfile.ZipFile(self.filepath, 'r') as z:

            xml_files = [
                f for f in z.namelist()
                if f.endswith(".xml")
            ]

            patterns = [
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
                "Keynote"
            ]

            for xml_file in xml_files:

                data = self.read_xml_from_zip(
                    z,
                    xml_file
                )

                if not data:
                    continue

                for pattern in patterns:

                    if re.search(
                        pattern,
                        data,
                        re.IGNORECASE
                    ):

                        software_found.add(pattern)

            self.results["software_detected"].extend(
                list(software_found)
            )

            unique_software = set(
                self.results["software_detected"]
            )

            if len(unique_software) > 1:

                self.add_indicator(
                    f"Software multipli rilevati: "
                    f"{list(unique_software)}",
                    35
                )

    # ========================================================
    # ANALISI FILE INCORPORATI
    # ========================================================

    def analyze_embedded_files(self):

        with zipfile.ZipFile(self.filepath, 'r') as z:

            embedded = [
                f for f in z.namelist()
                if "embeddings/" in f.lower()
            ]

            self.results["embedded_files"] = embedded

            if embedded:

                self.add_indicator(
                    f"File incorporati rilevati: "
                    f"{len(embedded)}",
                    10
                )

    # ========================================================
    # ANALISI IMMAGINI
    # ========================================================

    def analyze_images(self):

        software_list = set()

        with tempfile.TemporaryDirectory() as temp_dir:

            with zipfile.ZipFile(self.filepath, 'r') as z:

                media_files = [
                    f for f in z.namelist()
                    if "media/" in f.lower()
                ]

                for media in media_files:

                    try:

                        extracted = z.extract(
                            media,
                            temp_dir
                        )

                        image_info = {
                            "file": media
                        }

                        with Image.open(extracted) as img:

                            image_info["format"] = img.format

                            exif_data = img.getexif()

                            if exif_data:

                                exif = {}

                                for tag_id, value in exif_data.items():

                                    tag = TAGS.get(tag_id, tag_id)

                                    exif[tag] = str(value)

                                image_info["exif"] = exif

                                if "Software" in exif:

                                    software_list.add(
                                        exif["Software"]
                                    )

                        self.results["images"].append(
                            image_info
                        )

                    except Exception as e:

                        self.results["images"].append({
                            "file": media,
                            "error": str(e)
                        })

        if len(software_list) > 1:

            self.add_indicator(
                f"Immagini modificate con software differenti: "
                f"{list(software_list)}",
                20
            )

    # ========================================================
    # ANALISI MACRO
    # ========================================================

    def analyze_macros(self):

        with zipfile.ZipFile(self.filepath, 'r') as z:

            macros = [
                f for f in z.namelist()
                if "vba" in f.lower()
            ]

            if macros:

                self.add_indicator(
                    f"Macro VBA rilevate: {len(macros)}",
                    15
                )

    # ========================================================
    # GENERAZIONE REPORT
    # ========================================================

    def generate_report(self):

        lines = []

        lines.append("=" * 70)
        lines.append("OFFICE FORENSIC ANALYSIS REPORT")
        lines.append("=" * 70)

        lines.append("\n[FILE INFO]\n")

        for k, v in self.results["file_info"].items():
            lines.append(f"{k}: {v}")

        lines.append("\n[METADATA]\n")

        for k, v in self.results["metadata"].items():
            lines.append(f"{k}: {v}")

        lines.append("\n[EXTENDED METADATA]\n")

        for k, v in self.results["extended_metadata"].items():
            lines.append(f"{k}: {v}")

        lines.append("\n[SOFTWARE DETECTED]\n")

        for s in set(self.results["software_detected"]):
            lines.append(f"- {s}")

        lines.append("\n[AUTHORS DETECTED]\n")

        for a in self.results["authors_detected"]:
            lines.append(f"- {a}")

        lines.append("\n[USER PATHS]\n")

        for p in self.results["user_paths"]:
            lines.append(f"- {p}")

        lines.append("\n[EMBEDDED FILES]\n")

        if self.results["embedded_files"]:

            for emb in self.results["embedded_files"]:
                lines.append(f"- {emb}")

        else:
            lines.append("Nessun file incorporato.")

        lines.append("\n[IMAGES]\n")

        if self.results["images"]:

            for img in self.results["images"]:

                lines.append(f"- File: {img.get('file')}")

                if "format" in img:
                    lines.append(f"  Formato: {img['format']}")

                if "error" in img:
                    lines.append(f"  Errore: {img['error']}")

        else:
            lines.append("Nessuna immagine trovata.")

        lines.append("\n[SUSPICIOUS INDICATORS]\n")

        if not self.results["suspicious_indicators"]:

            lines.append("Nessun indicatore rilevato.")

        else:

            for item in self.results["suspicious_indicators"]:

                lines.append(
                    f"- {item['indicator']} "
                    f"(+{item['score']})"
                )

        lines.append("\n[RISK SCORE]\n")

        risk = self.results["risk_score"]

        lines.append(f"Punteggio: {risk}")

        if risk < 20:
            lines.append("Livello: BASSO")

        elif risk < 50:
            lines.append("Livello: MEDIO")

        else:
            lines.append("Livello: ALTO")

        report_text = "\n".join(lines)

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        if self.output_mode == "1":

            print("\n")
            print(report_text)

        elif self.output_mode == "2":

            txt_report_name = (
                os.path.splitext(self.filename)[0]
                + "_forensic_report.txt"
            )

            with open(
                txt_report_name,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(report_text)

            print(
                f"\nReport TXT salvato in: "
                f"{txt_report_name}"
            )

        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        json_report_name = (
            os.path.splitext(self.filename)[0]
            + "_forensic_report.json"
        )

        with open(
            json_report_name,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.results,
                f,
                indent=4,
                ensure_ascii=False
            )

        print(
            f"Report JSON salvato in: "
            f"{json_report_name}"
        )

    # ========================================================
    # RUN
    # ========================================================

    def run(self):

        self.analyze_file_info()

        self.analyze_core_metadata()

        self.analyze_extended_metadata()

        self.analyze_relationships()

        self.analyze_all_xml()

        self.analyze_embedded_files()

        self.analyze_images()

        self.analyze_macros()

        self.generate_report()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\nOFFICE FORENSIC ANALYZER\n")

    # --------------------------------------------------------
    # SCELTA OUTPUT
    # --------------------------------------------------------

    print("Seleziona modalità output:\n")
    print("1 - Stampa su schermo")
    print("2 - Salvataggio su file TXT\n")

    output_mode = input("Scelta: ").strip()

    if output_mode not in ["1", "2"]:

        print("\n[ERRORE]")
        print("Modalità non valida.")

        sys.exit(1)

    # --------------------------------------------------------
    # INPUT FILE
    # --------------------------------------------------------

    if len(sys.argv) > 1:

        office_file = sys.argv[1]

    else:

        office_file = input(
            "\nInserisci il percorso completo del file Office:\n> "
        ).strip('"')

    # --------------------------------------------------------
    # VALIDAZIONE FILE
    # --------------------------------------------------------

    if not os.path.exists(office_file):

        print("\n[ERRORE]")
        print("Il file specificato non esiste.")

        sys.exit(1)

    ext = os.path.splitext(office_file)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:

        print("\n[ERRORE]")
        print(f"Formato non supportato: {ext}")

        print("\nFormati supportati:")

        for e in sorted(SUPPORTED_EXTENSIONS):
            print(f"- {e}")

        sys.exit(1)

    # --------------------------------------------------------
    # AVVIO ANALISI
    # --------------------------------------------------------

    try:

        analyzer = OfficeForensicAnalyzer(
            office_file,
            output_mode
        )

        analyzer.run()

    except zipfile.BadZipFile:

        print("\n[ERRORE]")
        print(
            "Il file non è un documento Office "
            "OOXML valido oppure è corrotto."
        )

    except Exception as e:

        print("\n[ERRORE DURANTE L'ANALISI]")
        print(type(e).__name__)
        print(str(e))