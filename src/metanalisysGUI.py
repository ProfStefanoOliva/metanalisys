# ============================================================
# OFFICE FORENSIC ANALYZER GUI
# Copyright © Stefano Oliva
# ============================================================

import os
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk

from metanalisys_core import GUI_FILE_FILTERS
from metanalisys_core import FileAccessError
from metanalisys_core import InvalidOfficeFileError
from metanalisys_core import UnsupportedFormatError
from metanalisys_core import analyze_office_file
from metanalisys_core import analyze_office_folder
from metanalisys_core import build_folder_report_paths
from metanalisys_core import format_folder_html_report
from metanalisys_core import format_folder_text_report
from metanalisys_core import format_text_report
from metanalisys_core import save_folder_csv_report
from metanalisys_core import save_folder_html_report
from metanalisys_core import save_folder_json_report
from metanalisys_core import save_folder_text_report
from metanalisys_core import save_text_report

# ============================================================
# CONFIGURAZIONE GUI
# ============================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ICON_PATH = Path(__file__).resolve().parent / "assets" / "icons" / "metanalisys_icon.ico"
WATERMARK_PATH = Path(__file__).resolve().parent / "assets" / "icons" / "metanalisys_icon.png"
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


def resolve_analysis_target(path_text: str) -> str:
    normalized = path_text.strip()
    if not normalized:
        raise FileAccessError("Selezionare un file o una cartella.")
    if not os.path.exists(normalized):
        raise FileAccessError("Il percorso specificato non esiste.")
    if os.path.isfile(normalized):
        return "file"
    if os.path.isdir(normalized):
        return "folder"
    raise FileAccessError("Il percorso specificato non è né un file né una cartella.")


def build_destination_report_paths(source_folder_path: str, destination_dir: str) -> dict[str, str]:
    report_paths = build_folder_report_paths(source_folder_path)
    return {
        key: os.path.join(destination_dir, os.path.basename(path))
        for key, path in report_paths.items()
    }


def get_about_text() -> str:
    return (
        "metanalisys\n\n"
        "Analisi preliminare dei metadati Office.\n"
        "Software alpha di supporto tecnico.\n"
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
        self._set_window_icon()

        self.selected_file = None
        self.selected_path = None
        self.current_analysis_type = None
        self.report_text = ""
        self.report_html = ""
        self.report_results = None
        self.folder_summary_window = None
        self.watermark_label = None
        self.watermark_image = None

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
        # APRI CARTELLA
        # ====================================================

        open_folder_button = ctk.CTkButton(
            top_frame,
            text="Apri Cartella",
            width=150,
            height=40,
            font=("Segoe UI", 14, "bold"),
            command=self.open_folder
        )

        open_folder_button.pack(
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

        self.report_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        self.report_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.textbox = ctk.CTkTextbox(
            self.report_frame,
            font=("Consolas", 14)
        )

        self.textbox.pack(
            fill="both",
            expand=True,
            padx=0,
            pady=0
        )
        self.textbox.bind("<<Modified>>", self._on_textbox_modified)

        self._setup_report_watermark()
        self._update_report_watermark()

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

    def _set_window_icon(self) -> None:
        # If the icon is missing or not supported by the current platform,
        # keep the GUI usable and continue startup without raising.
        if not ICON_PATH.is_file():
            return

        try:
            self.iconbitmap(default=str(ICON_PATH))
        except Exception:
            pass

    def _setup_report_watermark(self) -> None:
        if not WATERMARK_PATH.is_file():
            return

        try:
            watermark = Image.open(WATERMARK_PATH).convert("RGBA")
            watermark.thumbnail((320, 320))

            alpha_channel = watermark.getchannel("A")
            alpha_channel = alpha_channel.point(lambda value: int(value * 0.2))
            watermark.putalpha(alpha_channel)

            self.watermark_image = ctk.CTkImage(
                light_image=watermark,
                dark_image=watermark,
                size=watermark.size,
            )

            self.watermark_label = ctk.CTkLabel(
                self.report_frame,
                text="",
                image=self.watermark_image,
                fg_color="transparent",
            )

            self.watermark_label.place(
                relx=0.5,
                rely=0.5,
                anchor="center",
            )
        except Exception:
            self.watermark_image = None
            self.watermark_label = None

    def _update_report_watermark(self) -> None:
        if self.watermark_label is None:
            return

        current_text = self.textbox.get("1.0", "end").strip()

        if current_text:
            self.watermark_label.place_forget()
        else:
            self.watermark_label.place(
                relx=0.5,
                rely=0.5,
                anchor="center",
            )

    def _on_textbox_modified(self, _event=None) -> None:
        self._update_report_watermark()
        self.textbox.edit_modified(False)

    def _close_folder_summary_window(self) -> None:
        if self.folder_summary_window is None:
            return
        try:
            if self.folder_summary_window.winfo_exists():
                self.folder_summary_window.destroy()
        except Exception:
            pass
        self.folder_summary_window = None

    def show_folder_summary_window(self, folder_results: dict[str, object]) -> None:
        self._close_folder_summary_window()

        window = ctk.CTkToplevel(self)
        window.title("Riepilogo analisi cartella")
        window.geometry("1220x680")
        window.minsize(980, 540)
        self.folder_summary_window = window

        try:
            window.transient(self)
        except Exception:
            pass

        window.protocol("WM_DELETE_WINDOW", self._close_folder_summary_window)

        container = ctk.CTkFrame(window)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        header_frame = ctk.CTkFrame(container)
        header_frame.pack(fill="x", padx=10, pady=(10, 8))

        folder_path = normalize_folder_display_value(folder_results.get("folder_path"))
        counts = get_folder_summary_counts(folder_results)
        total_files = normalize_folder_display_value(folder_results.get("total_files"))

        header_title = ctk.CTkLabel(
            header_frame,
            text="Riepilogo analisi cartella",
            font=("Segoe UI", 20, "bold"),
        )
        header_title.pack(anchor="w", padx=14, pady=(12, 4))

        header_path = ctk.CTkLabel(
            header_frame,
            text=f"Cartella analizzata: {folder_path}",
            font=("Segoe UI", 13),
            justify="left",
            anchor="w",
        )
        header_path.pack(fill="x", padx=14, pady=(0, 4))

        header_notice = ctk.CTkLabel(
            header_frame,
            text=(
                "Supporto tecnico di triage documentale: il risk score è un indice tecnico "
                "di anomalia documentale, non una prova automatica di manomissione."
            ),
            font=("Segoe UI", 12),
            justify="left",
            anchor="w",
            wraplength=1120,
        )
        header_notice.pack(fill="x", padx=14, pady=(0, 12))

        summary_frame = ctk.CTkFrame(container, fg_color="transparent")
        summary_frame.pack(fill="x", padx=10, pady=(0, 10))
        summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        summary_specs = [
            ("Totale file", total_files, "#203244"),
            ("OK", counts["OK"], "#1f4f3d"),
            ("LIMITED", counts["LIMITED"], "#5b4721"),
            ("ERROR", counts["ERROR"], "#5a2f35"),
        ]

        for index, (label, value, color) in enumerate(summary_specs):
            box = ctk.CTkFrame(summary_frame, fg_color=color)
            box.grid(row=0, column=index, padx=6, pady=0, sticky="nsew")
            ctk.CTkLabel(
                box,
                text=label,
                font=("Segoe UI", 12, "bold"),
            ).pack(anchor="w", padx=14, pady=(10, 2))
            ctk.CTkLabel(
                box,
                text=str(value),
                font=("Segoe UI", 24, "bold"),
            ).pack(anchor="w", padx=14, pady=(0, 10))

        table_frame = ctk.CTkFrame(container)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style(window)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "FolderSummary.Treeview",
            background="#13202c",
            fieldbackground="#13202c",
            foreground="#f0f4f8",
            rowheight=28,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "FolderSummary.Treeview.Heading",
            background="#1f6aa5",
            foreground="#ffffff",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "FolderSummary.Treeview",
            background=[("selected", "#2f5d7f")],
            foreground=[("selected", "#ffffff")],
        )

        column_ids = [column_id for column_id, _, _ in FOLDER_SUMMARY_TABLE_COLUMNS]
        tree = ttk.Treeview(
            table_frame,
            columns=column_ids,
            show="headings",
            style="FolderSummary.Treeview",
        )
        tree.grid(row=0, column=0, sticky="nsew")

        vertical_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        horizontal_scroll.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set)

        for column_id, label, width in FOLDER_SUMMARY_TABLE_COLUMNS:
            tree.heading(column_id, text=label)
            tree.column(column_id, width=width, minwidth=90, stretch=True, anchor="w")

        tree.tag_configure("OK", background="#183629")
        tree.tag_configure("LIMITED", background="#46361b")
        tree.tag_configure("ERROR", background="#472128")

        for row in build_folder_summary_table_rows(folder_results):
            tree.insert(
                "",
                "end",
                values=[row[column_id] for column_id, _, _ in FOLDER_SUMMARY_TABLE_COLUMNS],
                tags=(row["status"],),
            )

        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(0, 4))

        close_button = ctk.CTkButton(
            button_frame,
            text="Chiudi",
            width=120,
            command=self._close_folder_summary_window,
        )
        close_button.pack(side="right")

    # ========================================================
    # OPEN FILE
    # ========================================================

    def open_file(self):

        file = filedialog.askopenfilename(
            title="Seleziona file Office",
            filetypes=GUI_FILE_FILTERS
        )

        if not file:
            return

        self.selected_file = file
        self.selected_path = file
        self.current_analysis_type = None

        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, file)

        self.status.configure(
            text="File selezionato."
        )

    def open_folder(self):

        folder = filedialog.askdirectory(
            title="Seleziona cartella contenente file Office"
        )

        if not folder:
            return

        self.selected_path = folder
        self.selected_file = None
        self.current_analysis_type = None

        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, folder)

        self.status.configure(
            text="Cartella selezionata."
        )

    # ========================================================
    # ANALYZE
    # ========================================================

    def analyze(self):
        selected_path = self.path_entry.get().strip()

        try:
            target_type = resolve_analysis_target(selected_path)

            self.status.configure(
                text="Analisi in corso..."
            )

            self.update()
            self.selected_path = selected_path
            self.current_analysis_type = target_type
            self.report_html = ""

            if target_type == "file":
                self.selected_file = selected_path
                self.report_results = analyze_office_file(selected_path)
                self.report_text = format_text_report(self.report_results)
                self._close_folder_summary_window()
                self.status.configure(
                    text="Analisi completata."
                )
            else:
                self.selected_file = None
                self.report_results = analyze_office_folder(selected_path)
                self.report_text = format_folder_text_report(self.report_results)
                self.report_html = format_folder_html_report(self.report_results)
                self.show_folder_summary_window(self.report_results)
                self.status.configure(
                    text="Analisi cartella completata."
                )

            self.textbox.delete(
                "1.0",
                "end"
            )

            self.textbox.insert(
                "1.0",
                self.report_text
            )
            self._update_report_watermark()

        except UnsupportedFormatError:

            messagebox.showerror(
                "Formato non supportato",
                "L'estensione selezionata non è tra i formati Office riconosciuti."
            )

            self.status.configure(
                text="Formato non supportato."
            )

        except (FileAccessError, InvalidOfficeFileError) as exc:

            messagebox.showerror(
                "Errore",
                str(exc)
            )

            self.status.configure(
                text="Errore durante analisi."
            )

        except Exception as exc:

            messagebox.showerror(
                "Errore",
                f"Errore inatteso durante l'analisi:\n{exc}"
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
        if self.current_analysis_type == "folder":
            destination_dir = filedialog.askdirectory(
                title="Seleziona cartella di destinazione per i report"
            )

            if not destination_dir:
                return

            report_paths = build_destination_report_paths(self.selected_path, destination_dir)
            save_folder_text_report(self.report_results, report_paths["txt"])
            save_folder_csv_report(self.report_results, report_paths["csv"])
            save_folder_json_report(self.report_results, report_paths["json"])
            save_folder_html_report(self.report_html, report_paths["html"])

            self.status.configure(
                text="Report cartella salvati."
            )

            messagebox.showinfo(
                "Completato",
                (
                    "Report dell'analisi riepilogativa di cartella salvati correttamente:\n"
                    f"- {os.path.basename(report_paths['txt'])}\n"
                    f"- {os.path.basename(report_paths['csv'])}\n"
                    f"- {os.path.basename(report_paths['json'])}\n"
                    f"- {os.path.basename(report_paths['html'])}"
                )
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

        save_text_report(self.report_text, path)

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
            get_about_text()
        )

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app = App()

    app.mainloop()
