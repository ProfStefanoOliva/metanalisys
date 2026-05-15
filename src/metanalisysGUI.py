# ============================================================
# OFFICE FORENSIC ANALYZER GUI
# Copyright © Stefano Oliva
# ============================================================

import os

import customtkinter as ctk

from tkinter import filedialog
from tkinter import messagebox

from metanalisys_core import GUI_FILE_FILTERS
from metanalisys_core import FileAccessError
from metanalisys_core import InvalidOfficeFileError
from metanalisys_core import UnsupportedFormatError
from metanalisys_core import analyze_office_file
from metanalisys_core import format_text_report
from metanalisys_core import save_text_report

# ============================================================
# CONFIGURAZIONE GUI
# ============================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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
        self.report_results = None

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
            filetypes=GUI_FILE_FILTERS
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
        selected_file = self.path_entry.get().strip()

        if not selected_file:

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
            self.selected_file = selected_file
            self.report_results = analyze_office_file(self.selected_file)
            self.report_text = format_text_report(self.report_results)

            self.textbox.delete(
                "1.0",
                "end"
            )

            self.textbox.insert(
                "1.0",
                self.report_text
            )

            self.status.configure(
                text="Analisi completata."
            )

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
