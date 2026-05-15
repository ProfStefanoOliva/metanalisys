# ============================================================
# OFFICE FORENSIC ANALYZER GUI
# Copyright © Stefano Oliva
# ============================================================

import os
import re
import zipfile
import tempfile

from datetime import datetime
from xml.etree import ElementTree as ET

from PIL import Image
from PIL.ExifTags import TAGS

import customtkinter as ctk

from tkinter import filedialog
from tkinter import messagebox

# ============================================================
# CONFIGURAZIONE GUI
# ============================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SUPPORTED_EXTENSIONS = [
    ("Office Files", "*.docx *.xlsx *.pptx *.xlsm *.docm *.pptm *.vsdx"),
    ("Word", "*.docx *.docm"),
    ("Excel", "*.xlsx *.xlsm"),
    ("PowerPoint", "*.pptx *.pptm"),
    ("Visio", "*.vsdx"),
]

# ============================================================
# ANALIZZATORE
# ============================================================

class OfficeForensicAnalyzer:

    def __init__(self, filepath):

        self.filepath = filepath
        self.filename = os.path.basename(filepath)

        self.results = {
            "file_info": {},
            "metadata": {},
            "extended_metadata": {},
            "embedded_files": [],
            "images": [],
            "software_detected": [],
            "user_paths": [],
            "suspicious_indicators": [],
            "risk_score": 0
        }

    # ========================================================
    # INDICATORI
    # ========================================================

    def add_indicator(self, text, score):

        self.results["suspicious_indicators"].append({
            "indicator": text,
            "score": score
        })

        self.results["risk_score"] += score

    # ========================================================
    # FILE INFO
    # ========================================================

    def analyze_file_info(self):

        stat = os.stat(self.filepath)

        self.results["file_info"] = {
            "filename": self.filename,
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
    # CORE METADATA
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

    # ========================================================
    # METADATI ESTESI
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

    # ========================================================
    # RELATIONSHIPS
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

                found_paths = re.findall(
                    r"[A-Z]:\\\\[^<>:\"|?*\n\r]+",
                    data
                )

                for p in found_paths:
                    paths.add(p)

            self.results["user_paths"] = list(paths)

    # ========================================================
    # XML GENERALI
    # ========================================================

    def analyze_all_xml(self):

        software_found = set()

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

        with zipfile.ZipFile(self.filepath, 'r') as z:

            xml_files = [
                f for f in z.namelist()
                if f.endswith(".xml")
            ]

            for xml_file in xml_files:

                data = self.read_xml_from_zip(z, xml_file)

                if not data:
                    continue

                for pattern in patterns:

                    if re.search(
                        pattern,
                        data,
                        re.IGNORECASE
                    ):
                        software_found.add(pattern)

        self.results["software_detected"] = list(software_found)

    # ========================================================
    # FILE INCORPORATI
    # ========================================================

    def analyze_embedded_files(self):

        with zipfile.ZipFile(self.filepath, 'r') as z:

            embedded = [
                f for f in z.namelist()
                if "embeddings/" in f.lower()
            ]

            self.results["embedded_files"] = embedded

    # ========================================================
    # IMMAGINI
    # ========================================================

    def analyze_images(self):

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

                        self.results["images"].append(
                            image_info
                        )

                    except Exception as e:

                        self.results["images"].append({
                            "file": media,
                            "error": str(e)
                        })

    # ========================================================
    # MACRO
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
    # REPORT
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

        for s in self.results["software_detected"]:
            lines.append(f"- {s}")

        lines.append("\n[USER PATHS]\n")

        for p in self.results["user_paths"]:
            lines.append(f"- {p}")

        lines.append("\n[EMBEDDED FILES]\n")

        if self.results["embedded_files"]:

            for emb in self.results["embedded_files"]:
                lines.append(f"- {emb}")

        else:
            lines.append("Nessun file incorporato.")

        lines.append("\n[IMMAGINI]\n")

        if self.results["images"]:

            for img in self.results["images"]:

                lines.append(f"- File: {img.get('file')}")

                if "format" in img:
                    lines.append(f"  Formato: {img['format']}")

                if "error" in img:
                    lines.append(f"  Errore: {img['error']}")

        else:
            lines.append("Nessuna immagine trovata.")

        lines.append("\n[INDICATORI SOSPETTI]\n")

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

        return "\n".join(lines)

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

        return self.generate_report()

# ============================================================
# GUI
# ============================================================

class App(ctk.CTk):

    def __init__(self):

        super().__init__()

        # ====================================================
        # FINESTRA
        # ====================================================

        self.title("Office Forensic Analyzer")
        self.geometry("1400x850")
        self.minsize(1200, 700)

        self.selected_file = None
        self.report_text = ""

        # ====================================================
        # TOP FRAME
        # ====================================================

        top_frame = ctk.CTkFrame(
            self,
            height=70
        )

        top_frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        top_frame.pack_propagate(False)

        # ====================================================
        # PATH ENTRY
        # ====================================================

        self.path_entry = ctk.CTkEntry(
            top_frame,
            height=40,
            font=("Segoe UI", 14)
        )

        self.path_entry.pack(
            side="left",
            padx=(10, 5),
            pady=10,
            fill="x",
            expand=True
        )

        # ====================================================
        # APRI FILE
        # ====================================================

        open_button = ctk.CTkButton(
            top_frame,
            text="Apri File",
            width=140,
            height=40,
            font=("Segoe UI", 14, "bold"),
            command=self.open_file
        )

        open_button.pack(
            side="left",
            padx=5,
            pady=10
        )

        # ====================================================
        # AVVIA ANALISI
        # ====================================================

        analyze_button = ctk.CTkButton(
            top_frame,
            text="Avvia Analisi",
            width=160,
            height=40,
            font=("Segoe UI", 14, "bold"),
            command=self.analyze
        )

        analyze_button.pack(
            side="left",
            padx=5,
            pady=10
        )

        # ====================================================
        # SALVA REPORT
        # ====================================================

        save_button = ctk.CTkButton(
            top_frame,
            text="SALVA REPORT",
            width=180,
            height=40,
            font=("Segoe UI", 14, "bold"),
            fg_color="#1f6aa5",
            hover_color="#144870",
            command=self.save_report
        )

        save_button.pack(
            side="left",
            padx=5,
            pady=10
        )

        # ====================================================
        # HELP BUTTON
        # ====================================================

        help_button = ctk.CTkButton(
            top_frame,
            text="?",
            width=45,
            height=40,
            font=("Arial", 18, "bold"),
            command=self.show_about
        )

        help_button.pack(
            side="left",
            padx=(5, 10),
            pady=10
        )

        # ====================================================
        # TEXTBOX
        # ====================================================

        self.textbox = ctk.CTkTextbox(
            self,
            font=("Consolas", 14)
        )

        self.textbox.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # ====================================================
        # STATUS BAR
        # ====================================================

        self.status = ctk.CTkLabel(
            self,
            text="Pronto"
        )

        self.status.pack(
            fill="x",
            padx=10,
            pady=(0, 10)
        )

    # ========================================================
    # OPEN FILE
    # ========================================================

    def open_file(self):

        file = filedialog.askopenfilename(
            title="Seleziona file Office",
            filetypes=SUPPORTED_EXTENSIONS
        )

        if not file:
            return

        self.selected_file = file

        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, file)

        self.status.configure(
            text="File selezionato."
        )

    # ========================================================
    # ANALYZE
    # ========================================================

    def analyze(self):

        if not self.selected_file:

            messagebox.showerror(
                "Errore",
                "Selezionare un file."
            )

            return

        try:

            self.status.configure(
                text="Analisi in corso..."
            )

            self.update()

            analyzer = OfficeForensicAnalyzer(
                self.selected_file
            )

            report = analyzer.run()

            self.report_text = report

            self.textbox.delete(
                "1.0",
                "end"
            )

            self.textbox.insert(
                "1.0",
                report
            )

            self.status.configure(
                text="Analisi completata."
            )

        except Exception as e:

            messagebox.showerror(
                "Errore",
                str(e)
            )

            self.status.configure(
                text="Errore durante analisi."
            )

    # ========================================================
    # SAVE REPORT
    # ========================================================

    def save_report(self):

        if not self.report_text:

            messagebox.showwarning(
                "Attenzione",
                "Nessun report disponibile."
            )

            return

        original = os.path.splitext(
            os.path.basename(self.selected_file)
        )[0]

        default_name = (
            original
            + "_forensic_report.txt"
        )

        path = filedialog.asksaveasfilename(
            title="Salva Report",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Text Files", "*.txt")]
        )

        if not path:
            return

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(self.report_text)

        self.status.configure(
            text="Report salvato."
        )

        messagebox.showinfo(
            "Completato",
            "Report salvato correttamente."
        )

    # ========================================================
    # ABOUT
    # ========================================================

    def show_about(self):

        messagebox.showinfo(
            "Informazioni Software",
            (
                "OFFICE FORENSIC ANALYZER\n\n"
                "Software di analisi forense documenti Office\n\n"
                "Copyright © 2026 Stefano Oliva\n"
                "Tutti i diritti riservati."
            )
        )

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app = App()

    app.mainloop()