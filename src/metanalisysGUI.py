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
                self.status.configure(
                    text="Analisi completata."
                )
            else:
                self.selected_file = None
                self.report_results = analyze_office_folder(selected_path)
                self.report_text = format_folder_text_report(self.report_results)
                self.report_html = format_folder_html_report(self.report_results)
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
