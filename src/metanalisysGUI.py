# ============================================================
# OFFICE FORENSIC ANALYZER GUI
# Copyright © Stefano Oliva
# ============================================================

from __future__ import annotations

import os
from pathlib import Path

import customtkinter as ctk

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
from metanalisys_gui_helpers import FOLDER_SUMMARY_TABLE_COLUMNS
from metanalisys_gui_helpers import FOLDER_FILE_DETAIL_NOTICE
from metanalisys_gui_helpers import NO_ANALYSIS_MESSAGE
from metanalisys_gui_helpers import NO_INDICATORS_MESSAGE
from metanalisys_gui_helpers import PRUDENT_RISK_NOTICE
from metanalisys_gui_helpers import SIDEBAR_SECTIONS
from metanalisys_gui_helpers import START_VIEW_MESSAGE
from metanalisys_gui_helpers import START_VIEW_NOTICE
from metanalisys_gui_helpers import TRIAGE_SUPPORT_TEXT
from metanalisys_gui_helpers import build_selected_file_sidebar_items
from metanalisys_gui_helpers import build_folder_dashboard_cards
from metanalisys_gui_helpers import build_folder_file_detail_rows
from metanalisys_gui_helpers import build_folder_file_sidebar_items
from metanalisys_gui_helpers import build_folder_file_sidebar_tree
from metanalisys_gui_helpers import build_folder_file_sidebar_label
from metanalisys_gui_helpers import build_folder_summary_table_rows
from metanalisys_gui_helpers import build_hash_view_rows
from metanalisys_gui_helpers import build_indicator_rows
from metanalisys_gui_helpers import build_metadata_view_rows
from metanalisys_gui_helpers import build_risk_score_rows
from metanalisys_gui_helpers import build_single_file_dashboard_rows
from metanalisys_gui_helpers import find_folder_report_entry
from metanalisys_gui_helpers import format_sidebar_filename_label
from metanalisys_gui_helpers import get_about_text
from metanalisys_gui_helpers import get_folder_summary_counts
from metanalisys_gui_helpers import has_folder_sidebar_files
from metanalisys_gui_helpers import normalize_folder_display_value

# ============================================================
# CONFIGURAZIONE GUI
# ============================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ICON_PATH = Path(__file__).resolve().parent / "assets" / "icons" / "metanalisys_icon.ico"


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


def safe_clear_frame(frame) -> None:
    if frame is None:
        return
    for child in list(frame.winfo_children()):
        if child.winfo_exists():
            child.destroy()


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Office Forensic Analyzer")
        self.geometry("1440x900")
        self.minsize(1220, 760)
        self._set_window_icon()

        self.selected_file: str | None = None
        self.selected_path: str | None = None
        self.current_analysis_type: str | None = None
        self.report_text = ""
        self.report_html = ""
        self.report_results: dict[str, object] | None = None
        self.folder_summary_window = None
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.default_button_fg_color = ("#1f6aa5", "#1f6aa5")
        self.active_button_fg_color = ("#2f80c2", "#2f80c2")
        self.content_scrollable_frame: ctk.CTkScrollableFrame | None = None
        self.content_surface: ctk.CTkFrame | ctk.CTkScrollableFrame | None = None
        self.sidebar_shell: ctk.CTkFrame | None = None
        self.sidebar_scrollable: ctk.CTkScrollableFrame | None = None
        self.default_status_text = "Pronto"
        self.folder_tree_item_paths: dict[str, str] = {}
        self.folder_file_cache: dict[str, dict[str, object]] = {}
        self.folder_file_buttons: dict[str, ctk.CTkButton] = {}
        self.selected_file_section_buttons: dict[str, ctk.CTkButton] = {}
        self.selected_folder_file_path: str | None = None
        self.selected_folder_file_report_text = ""
        self.active_selected_file_view = "selected_file_overview"
        self.sidebar_refresh_job = None
        self.sidebar_reset_scroll_on_refresh = False
        self.is_closing = False

        self.protocol("WM_DELETE_WINDOW", self._on_app_close)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()
        self._update_navigation_state()
        self.show_start_view()

    def _build_sidebar(self) -> None:
        sidebar_shell = ctk.CTkFrame(
            self,
            width=252,
            corner_radius=18,
            fg_color="#101923",
            border_width=1,
            border_color="#1a2b3b",
        )
        sidebar_shell.grid(row=0, column=0, sticky="ns", padx=(12, 6), pady=12)
        sidebar_shell.grid_propagate(False)
        sidebar_shell.grid_rowconfigure(0, weight=1)
        sidebar_shell.grid_columnconfigure(0, weight=1)

        sidebar = ctk.CTkScrollableFrame(
            sidebar_shell,
            width=228,
            corner_radius=18,
            fg_color="transparent",
        )
        sidebar.grid(row=0, column=0, sticky="nsew", padx=4, pady=6)
        sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar_shell = sidebar_shell
        self.sidebar_scrollable = sidebar
        self._request_sidebar_refresh(reset_scroll=True)

    def _on_app_close(self) -> None:
        self.is_closing = True
        if self.sidebar_refresh_job is not None:
            try:
                self.after_cancel(self.sidebar_refresh_job)
            except Exception:
                pass
            self.sidebar_refresh_job = None
        self._close_folder_summary_window()
        self.destroy()

    def _request_sidebar_refresh(self, *, reset_scroll: bool = False) -> None:
        if self.is_closing or self.sidebar_scrollable is None:
            return
        self.sidebar_reset_scroll_on_refresh = self.sidebar_reset_scroll_on_refresh or reset_scroll
        if self.sidebar_refresh_job is not None:
            return
        self.sidebar_refresh_job = self.after_idle(self._execute_sidebar_refresh)

    def _execute_sidebar_refresh(self) -> None:
        self.sidebar_refresh_job = None
        if self.is_closing or self.sidebar_scrollable is None or not self.sidebar_scrollable.winfo_exists():
            return
        self._render_sidebar_content()
        if self.sidebar_reset_scroll_on_refresh:
            self.after_idle(self._scroll_sidebar_to_top)
        self.sidebar_reset_scroll_on_refresh = False

    def _render_sidebar_content(self) -> None:
        if self.sidebar_scrollable is None or self.is_closing:
            return

        safe_clear_frame(self.sidebar_scrollable)

        self.nav_buttons = {}
        self.folder_file_buttons = {}
        self.selected_file_section_buttons = {}

        brand = ctk.CTkLabel(
            self.sidebar_scrollable,
            text="metanalisys",
            font=("Segoe UI", 24, "bold"),
        )
        brand.grid(row=0, column=0, sticky="w", padx=14, pady=(18, 4))

        brand_subtitle = ctk.CTkLabel(
            self.sidebar_scrollable,
            text="Dashboard prudente per analisi preliminare dei metadati Office.",
            font=("Segoe UI", 12),
            justify="left",
            wraplength=220,
            anchor="w",
        )
        brand_subtitle.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 18))

        command_map = {
            "new_analysis": self.start_new_analysis,
            "open_file": self.open_file,
            "open_folder": self.open_folder,
            "run_analysis": self.analyze,
            "save_report": self.save_report,
            "dashboard": self.show_dashboard_view,
            "technical_report": self.show_technical_report_view,
            "information": self.show_info_view,
        }

        current_row = 2
        for section in SIDEBAR_SECTIONS:
            section_label = ctk.CTkLabel(
                self.sidebar_scrollable,
                text=section["title"],
                font=("Segoe UI", 11, "bold"),
                text_color="#8fa7bd",
                anchor="w",
            )
            section_label.grid(row=current_row, column=0, sticky="ew", padx=14, pady=(0, 8))
            current_row += 1

            for button_key, button_label in section["items"]:
                button = ctk.CTkButton(
                    self.sidebar_scrollable,
                    text=button_label,
                    anchor="w",
                    height=38,
                    font=("Segoe UI", 13, "bold"),
                    fg_color=self.default_button_fg_color,
                    hover_color="#173b59",
                    command=command_map[button_key],
                )
                button.grid(row=current_row, column=0, sticky="ew", padx=10, pady=4)
                self.nav_buttons[button_key] = button
                current_row += 1

            if section["title"] == "ANALISI CORRENTE":
                file_items = self._get_sidebar_file_items()
                if file_items:
                    current_row = self._render_sidebar_file_section(file_items, current_row)
                selected_items = self._get_selected_file_sidebar_items()
                if selected_items and self.current_analysis_type == "file":
                    current_row = self._render_selected_file_section(selected_items, current_row)

            current_row += 1

        self._refresh_sidebar_visual_state()

    def _get_sidebar_file_items(self) -> list[dict[str, str]]:
        if self.current_analysis_type != "folder" or not self.report_results:
            return []
        return build_folder_file_sidebar_items(self.report_results)

    def _get_selected_file_sidebar_items(self) -> list[tuple[str, str]]:
        if self.current_analysis_type == "file" and self.report_results:
            filename = self.report_results.get("file_info", {}).get("filename")
            return build_selected_file_sidebar_items(filename)
        if self.current_analysis_type == "folder" and self.selected_folder_file_path:
            detail_entry = self._extract_folder_file_cache_entry(self.selected_folder_file_path)
            report_entry = detail_entry.get("report_entry", {})
            results = detail_entry.get("results")
            filename = None
            if isinstance(results, dict):
                filename = results.get("file_info", {}).get("filename")
            if not filename and isinstance(report_entry, dict):
                filename = report_entry.get("filename")
            return build_selected_file_sidebar_items(filename)
        return []

    def _render_sidebar_file_section(self, file_items: list[dict[str, str]], current_row: int) -> int:
        section_label = ctk.CTkLabel(
            self.sidebar_scrollable,
            text="FILE ANALIZZATI",
            font=("Segoe UI", 11, "bold"),
            text_color="#8fa7bd",
            anchor="w",
        )
        section_label.grid(row=current_row, column=0, sticky="ew", padx=14, pady=(0, 8))
        current_row += 1

        command_map = {
            "selected_file_overview": self.show_selected_file_overview_view,
            "metadata": self.show_metadata_view,
            "hashes": self.show_hash_view,
            "risk_score": self.show_risk_score_view,
            "indicators": self.show_indicators_view,
            "file_report": self.show_selected_file_report_view,
        }

        for item in build_folder_file_sidebar_tree(self.report_results or {}, self.selected_folder_file_path):
            path = str(item["path"])
            is_child = item["kind"] == "child"
            button = ctk.CTkButton(
                self.sidebar_scrollable,
                text=str(item["label"]),
                anchor="w",
                height=34 if is_child else 36,
                font=("Segoe UI", 11, "bold") if is_child else ("Segoe UI", 12, "bold"),
                fg_color=self._get_sidebar_tree_button_color(item),
                hover_color="#1f4d70" if is_child else "#173b59",
                command=(
                    (lambda target_path=path: self.open_folder_file_detail(target_path))
                    if not is_child
                    else (lambda action_key=str(item["key"]): command_map[action_key]())
                ),
            )
            button.grid(
                row=current_row,
                column=0,
                sticky="ew",
                padx=(20, 10) if is_child else (10, 10),
                pady=2 if is_child else 3,
            )
            if not is_child:
                button.bind(
                    "<Enter>",
                    lambda _event, file_item=item: self._show_sidebar_file_hover_info(file_item),
                )
                button.bind("<Leave>", lambda _event: self._restore_status_text())
                self.folder_file_buttons[path] = button
            else:
                self.selected_file_section_buttons[str(item["key"])] = button
            current_row += 1

        return current_row

    def _get_sidebar_tree_button_color(self, item: dict[str, str | int]) -> str:
        if item["kind"] == "file":
            return self.active_button_fg_color if str(item["path"]) == self.selected_folder_file_path else "#173041"
        return self.active_button_fg_color if str(item["key"]) == self._get_active_selected_file_sidebar_key() else "#132232"

    def _render_selected_file_section(
        self,
        selected_items: list[tuple[str, str]],
        current_row: int,
    ) -> int:
        section_label = ctk.CTkLabel(
            self.sidebar_scrollable,
            text="FILE SELEZIONATO",
            font=("Segoe UI", 11, "bold"),
            text_color="#8fa7bd",
            anchor="w",
        )
        section_label.grid(row=current_row, column=0, sticky="ew", padx=14, pady=(0, 8))
        current_row += 1

        command_map = {
            "selected_file_overview": self.show_selected_file_overview_view,
            "metadata": self.show_metadata_view,
            "hashes": self.show_hash_view,
            "risk_score": self.show_risk_score_view,
            "indicators": self.show_indicators_view,
            "file_report": self.show_selected_file_report_view,
        }

        active_key = self._get_active_selected_file_sidebar_key()
        for key, label in selected_items:
            button = ctk.CTkButton(
                self.sidebar_scrollable,
                text=label,
                anchor="w",
                height=36,
                font=("Segoe UI", 12, "bold"),
                fg_color=self.active_button_fg_color if key == active_key else "#173041",
                hover_color="#1f4d70",
                command=command_map[key],
            )
            button.grid(row=current_row, column=0, sticky="ew", padx=10, pady=3)
            self.selected_file_section_buttons[key] = button
            current_row += 1

        return current_row

    def _get_active_selected_file_sidebar_key(self) -> str:
        return getattr(self, "active_selected_file_view", "selected_file_overview")

    def _show_sidebar_file_hover_info(self, file_item: dict[str, str]) -> None:
        if self.is_closing or not self.status.winfo_exists():
            return
        full_name = normalize_folder_display_value(file_item.get("filename"))
        full_path = normalize_folder_display_value(file_item.get("path"))
        hover_text = f"File: {full_name}"
        if full_path != "N/D":
            hover_text += f" | Percorso: {full_path}"
        self.status.configure(text=hover_text)

    def _restore_status_text(self) -> None:
        if self.is_closing or not self.status.winfo_exists():
            return
        self.status.configure(text=self.default_status_text)

    def _set_status_text(self, text: str) -> None:
        self.default_status_text = text
        self.status.configure(text=text)

    def _scroll_sidebar_to_top(self) -> None:
        if self.sidebar_scrollable is None:
            return
        try:
            self.sidebar_scrollable._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def _build_main_area(self) -> None:
        main_frame = ctk.CTkFrame(self, fg_color="#101923")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        path_frame = ctk.CTkFrame(main_frame, fg_color="#132232")
        path_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 10))
        path_frame.grid_columnconfigure(0, weight=1)

        path_label = ctk.CTkLabel(
            path_frame,
            text="Percorso target",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        path_label.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        self.path_entry = ctk.CTkEntry(
            path_frame,
            height=42,
            font=("Segoe UI", 14),
            placeholder_text="Seleziona un file Office o una cartella da analizzare",
        )
        self.path_entry.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 6))

        path_hint = ctk.CTkLabel(
            path_frame,
            text="Le azioni principali sono disponibili nella sidebar laterale.",
            font=("Segoe UI", 11),
            text_color="#9cb3c6",
            anchor="w",
        )
        path_hint.grid(row=2, column=0, sticky="w", padx=14, pady=(0, 12))

        self.view_header_frame = ctk.CTkFrame(main_frame, fg_color="#162738")
        self.view_header_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        self.view_header_frame.grid_columnconfigure(0, weight=1)

        self.view_title_label = ctk.CTkLabel(
            self.view_header_frame,
            text="",
            font=("Segoe UI", 24, "bold"),
            anchor="w",
        )
        self.view_title_label.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))

        self.view_description_label = ctk.CTkLabel(
            self.view_header_frame,
            text="",
            font=("Segoe UI", 12),
            justify="left",
            anchor="w",
            wraplength=980,
        )
        self.view_description_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))

        self.content_frame = ctk.CTkFrame(main_frame, fg_color="#0f1a24")
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self._create_scrollable_content_surface()

        self.status = ctk.CTkLabel(
            self,
            text="Pronto",
            anchor="w",
            font=("Segoe UI", 12),
        )
        self.status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))

    def _set_window_icon(self) -> None:
        if not ICON_PATH.is_file():
            return
        try:
            self.iconbitmap(default=str(ICON_PATH))
        except Exception:
            pass

    def _clear_content(self) -> None:
        for child in self.content_frame.winfo_children():
            child.destroy()
        self.content_scrollable_frame = None
        self.content_surface = None

    def _create_scrollable_content_surface(self) -> None:
        self.content_scrollable_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color="transparent",
            corner_radius=0,
        )
        self.content_scrollable_frame.grid(row=0, column=0, sticky="nsew")
        self.content_scrollable_frame.grid_columnconfigure(0, weight=1)
        self.content_surface = self.content_scrollable_frame
        self.after_idle(self._scroll_content_to_top)

    def _scroll_content_to_top(self) -> None:
        if self.content_scrollable_frame is None:
            return
        try:
            self.content_scrollable_frame._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def _get_scrollable_content_surface(self) -> ctk.CTkScrollableFrame:
        if self.content_scrollable_frame is None:
            self._create_scrollable_content_surface()
        return self.content_scrollable_frame

    def _create_static_content_surface(self) -> ctk.CTkFrame:
        static_surface = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        static_surface.grid(row=0, column=0, sticky="nsew")
        static_surface.grid_columnconfigure(0, weight=1)
        static_surface.grid_rowconfigure(1, weight=1)
        self.content_surface = static_surface
        return static_surface

    def _set_view_header(self, title: str, description: str) -> None:
        self.view_title_label.configure(text=title)
        self.view_description_label.configure(text=description)

    def _set_active_button(self, active_key: str) -> None:
        for key, button in self.nav_buttons.items():
            if button.winfo_exists():
                fg_color = self.active_button_fg_color if key == active_key else self.default_button_fg_color
                button.configure(fg_color=fg_color)

    def _update_navigation_state(self) -> None:
        has_report = bool(self.report_text and self.report_results)
        has_selected_detail = self._has_selected_detail_file()

        if "save_report" in self.nav_buttons:
            if self.nav_buttons["save_report"].winfo_exists():
                self.nav_buttons["save_report"].configure(state="normal" if has_report else "disabled")
        if "technical_report" in self.nav_buttons:
            if self.nav_buttons["technical_report"].winfo_exists():
                self.nav_buttons["technical_report"].configure(state="normal" if has_report else "disabled")

        for button in self.selected_file_section_buttons.values():
            if button.winfo_exists():
                button.configure(state="normal" if has_selected_detail else "disabled")

    def _refresh_sidebar_visual_state(self) -> None:
        for path, button in self.folder_file_buttons.items():
            if button.winfo_exists():
                button.configure(
                    fg_color=self.active_button_fg_color if path == self.selected_folder_file_path else "#173041"
                )
        active_selected_key = self._get_active_selected_file_sidebar_key()
        for key, button in self.selected_file_section_buttons.items():
            if button.winfo_exists():
                button.configure(
                    fg_color=self.active_button_fg_color if key == active_selected_key else "#173041"
                )
        self._update_navigation_state()

    def _set_path_value(self, value: str) -> None:
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, value)

    def _reset_analysis_outputs(self) -> None:
        self.selected_file = None
        self.current_analysis_type = None
        self.report_text = ""
        self.report_html = ""
        self.report_results = None
        self.folder_tree_item_paths = {}
        self.folder_file_cache = {}
        self.selected_folder_file_path = None
        self.selected_folder_file_report_text = ""
        self.active_selected_file_view = "selected_file_overview"
        self._request_sidebar_refresh(reset_scroll=True)

    def _has_selected_detail_file(self) -> bool:
        if self.current_analysis_type == "file":
            return bool(self.report_results)
        if self.current_analysis_type == "folder":
            return bool(self.selected_folder_file_path)
        return False

    def _get_active_detail_results(self) -> dict[str, object] | None:
        if self.current_analysis_type == "file":
            return self.report_results if isinstance(self.report_results, dict) else None
        if self.current_analysis_type == "folder" and self.selected_folder_file_path:
            entry = self._extract_folder_file_cache_entry(self.selected_folder_file_path)
            results = entry.get("results")
            if isinstance(results, dict):
                return results
        return None

    def _get_active_detail_report_text(self) -> str:
        if self.current_analysis_type == "file":
            return self.report_text
        if self.current_analysis_type == "folder" and self.selected_folder_file_path:
            entry = self._extract_folder_file_cache_entry(self.selected_folder_file_path)
            return str(entry.get("report_text", ""))
        return ""

    def _get_active_detail_filename(self) -> str:
        results = self._get_active_detail_results()
        if results:
            return normalize_folder_display_value(results.get("file_info", {}).get("filename"))
        if self.current_analysis_type == "folder" and self.selected_folder_file_path:
            entry = self._extract_folder_file_cache_entry(self.selected_folder_file_path)
            report_entry = entry.get("report_entry", {})
            if isinstance(report_entry, dict):
                return normalize_folder_display_value(report_entry.get("filename"))
        return "N/D"

    def _extract_folder_file_cache_entry(self, target_path: str) -> dict[str, object]:
        if target_path in self.folder_file_cache:
            return self.folder_file_cache[target_path]

        report_entry = {}
        if self.report_results:
            report_entry = find_folder_report_entry(self.report_results, target_path) or {}

        cached_entry: dict[str, object] = {
            "path": target_path,
            "report_entry": report_entry,
            "results": None,
            "report_text": "",
            "error": "",
            "status": normalize_folder_display_value(report_entry.get("status")),
        }

        if report_entry.get("status") == "ERROR":
            cached_entry["error"] = normalize_folder_display_value(report_entry.get("error"))
            self.folder_file_cache[target_path] = cached_entry
            return cached_entry

        if isinstance(report_entry.get("results"), dict):
            results = report_entry["results"]
            cached_entry["results"] = results
            cached_entry["report_text"] = format_text_report(results)
            self.folder_file_cache[target_path] = cached_entry
            return cached_entry

        try:
            results = analyze_office_file(target_path)
            cached_entry["results"] = results
            cached_entry["report_text"] = format_text_report(results)
            cached_entry["status"] = "OK"
            if not report_entry:
                cached_entry["report_entry"] = {
                    "path": target_path,
                    "filename": os.path.basename(target_path),
                    "status": "OK",
                    "error": "",
                }
        except Exception as exc:
            cached_entry["error"] = str(exc).strip() or type(exc).__name__

        self.folder_file_cache[target_path] = cached_entry
        return cached_entry

    def _create_notice_box(self, parent, text: str, fg_color: str = "#173041"):
        box = ctk.CTkFrame(parent, fg_color=fg_color)
        box.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkLabel(
            box,
            text=text,
            font=("Segoe UI", 12),
            justify="left",
            wraplength=980,
            anchor="w",
        ).pack(fill="x", padx=14, pady=14)
        return box

    def _create_kv_table(self, parent, rows: list[tuple[str, str]]) -> None:
        table = ctk.CTkFrame(parent, fg_color="transparent")
        table.pack(fill="x", padx=18, pady=(0, 18))
        table.grid_columnconfigure(1, weight=1)

        for index, (label, value) in enumerate(rows):
            row_frame = ctk.CTkFrame(table, fg_color="#152535")
            row_frame.grid(row=index, column=0, columnspan=2, sticky="ew", pady=4)
            row_frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row_frame,
                text=label,
                font=("Segoe UI", 12, "bold"),
                width=220,
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=(14, 12), pady=10)

            ctk.CTkLabel(
                row_frame,
                text=value,
                font=("Segoe UI", 12),
                justify="left",
                wraplength=700,
                anchor="w",
            ).grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=10)

    def _create_center_message(self, title: str, body: str) -> None:
        content_parent = self._get_scrollable_content_surface()
        panel = ctk.CTkFrame(content_parent, fg_color="#132232")
        panel.pack(fill="x", padx=18, pady=18)
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text=title,
            font=("Segoe UI", 24, "bold"),
            justify="center",
        ).grid(row=0, column=0, padx=24, pady=(70, 12))

        ctk.CTkLabel(
            panel,
            text=body,
            font=("Segoe UI", 13),
            justify="center",
            wraplength=760,
        ).grid(row=1, column=0, padx=24, pady=(0, 12))

    def _create_folder_treeview(
        self,
        parent,
        rows: list[dict[str, str]],
        *,
        height: int = 360,
        on_item_open=None,
    ) -> None:
        table_frame = ctk.CTkFrame(parent, height=height)
        table_frame.pack(fill="x", padx=18, pady=(0, 18))
        table_frame.pack_propagate(False)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.folder_tree_item_paths = {}

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "FolderDashboard.Treeview",
            background="#13202c",
            fieldbackground="#13202c",
            foreground="#f0f4f8",
            rowheight=28,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "FolderDashboard.Treeview.Heading",
            background="#1f6aa5",
            foreground="#ffffff",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "FolderDashboard.Treeview",
            background=[("selected", "#2f5d7f")],
            foreground=[("selected", "#ffffff")],
        )

        column_ids = [column_id for column_id, _, _ in FOLDER_SUMMARY_TABLE_COLUMNS]
        tree = ttk.Treeview(
            table_frame,
            columns=column_ids,
            show="headings",
            style="FolderDashboard.Treeview",
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

        for row in rows:
            item_id = tree.insert(
                "",
                "end",
                values=[row[column_id] for column_id, _, _ in FOLDER_SUMMARY_TABLE_COLUMNS],
                tags=(row["status"],),
            )
            self.folder_tree_item_paths[item_id] = row.get("path", "")

        if on_item_open is not None:
            def _handle_double_click(_event) -> None:
                selection = tree.selection()
                if not selection:
                    return
                target_path = self.folder_tree_item_paths.get(selection[0], "")
                if target_path and target_path != "N/D":
                    on_item_open(target_path)

            tree.bind("<Double-1>", _handle_double_click)

    def start_new_analysis(self) -> None:
        self.selected_path = None
        self._reset_analysis_outputs()
        self.path_entry.delete(0, "end")
        self._set_status_text("Nuova analisi pronta.")
        self.show_start_view()

    def show_start_view(self) -> None:
        self.active_selected_file_view = "selected_file_overview"
        self._clear_content()
        self._set_active_button("new_analysis")
        self._set_view_header(
            "🏠 Nuova analisi",
            "Punto di partenza per il triage documentale preliminare.",
        )
        self._create_center_message(START_VIEW_MESSAGE, START_VIEW_NOTICE)

    def show_dashboard_view(self) -> None:
        self.active_selected_file_view = "selected_file_overview"
        self._clear_content()
        self._set_active_button("dashboard")
        self._refresh_sidebar_visual_state()
        self._set_view_header(
            "📊 Dashboard",
            "Vista sintetica dell'analisi attiva con guida prudente alla lettura dei risultati.",
        )

        if not self.report_results:
            self._create_center_message(
                NO_ANALYSIS_MESSAGE,
                "Seleziona un file Office o una cartella e avvia l'analisi per visualizzare la dashboard.",
            )
            return

        if self.current_analysis_type == "folder":
            content_parent = self._get_scrollable_content_surface()
            folder_path = normalize_folder_display_value(self.report_results.get("folder_path"))
            self._create_notice_box(
                content_parent,
                (
                    f"Cartella analizzata: {folder_path}\n"
                    f"{TRIAGE_SUPPORT_TEXT} Il risk score resta un indice tecnico di anomalia documentale "
                    "e non una prova automatica di manomissione."
                ),
            )

            cards_frame = ctk.CTkFrame(content_parent, fg_color="transparent")
            cards_frame.pack(fill="x", padx=18, pady=(0, 14))
            cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

            for index, (label, value, color) in enumerate(build_folder_dashboard_cards(self.report_results)):
                card = ctk.CTkFrame(cards_frame, fg_color=color)
                card.grid(row=0, column=index, padx=6, pady=0, sticky="nsew")
                ctk.CTkLabel(
                    card,
                    text=label,
                    font=("Segoe UI", 12, "bold"),
                ).pack(anchor="w", padx=14, pady=(10, 2))
                ctk.CTkLabel(
                    card,
                    text=value,
                    font=("Segoe UI", 24, "bold"),
                ).pack(anchor="w", padx=14, pady=(0, 10))

            self._create_folder_treeview(
                content_parent,
                build_folder_summary_table_rows(self.report_results),
                on_item_open=self.open_folder_file_detail,
            )
            return

        content_parent = self._get_scrollable_content_surface()
        self._create_notice_box(
            content_parent,
            (
                "Dashboard del file analizzato. I metadati mostrati sono metadati dichiarati dal file "
                "o estratti dal contenitore supportato; consulta il report tecnico per il dettaglio completo."
            ),
        )
        self._create_kv_table(
            content_parent,
            build_single_file_dashboard_rows(self.report_results),
        )

    def show_technical_report_view(self) -> None:
        self.active_selected_file_view = "selected_file_overview"
        self._clear_content()
        self._set_active_button("technical_report")
        self._refresh_sidebar_visual_state()
        self._set_view_header(
            "🧾 Report tecnico",
            "Report testuale completo, utile per audit tecnico e conservazione del dettaglio analitico.",
        )

        if not self.report_text:
            self._create_center_message(NO_ANALYSIS_MESSAGE, "Nessun report tecnico disponibile.")
            return

        report_surface = self._create_static_content_surface()
        self._create_notice_box(
            report_surface,
            (
                "Questa vista mantiene il report tecnico completo senza modificare il contenuto prodotto "
                "dal core di analisi."
            ),
        )

        if self.current_analysis_type == "folder":
            file_items = self._get_sidebar_file_items()
            if file_items:
                quick_nav_frame = ctk.CTkFrame(report_surface, fg_color="#132232")
                quick_nav_frame.pack(fill="x", padx=18, pady=(0, 12))
                ctk.CTkLabel(
                    quick_nav_frame,
                    text="File analizzati",
                    font=("Segoe UI", 12, "bold"),
                    anchor="w",
                ).pack(fill="x", padx=14, pady=(12, 6))

                buttons_frame = ctk.CTkFrame(quick_nav_frame, fg_color="transparent")
                buttons_frame.pack(fill="x", padx=10, pady=(0, 10))
                buttons_frame.grid_columnconfigure((0, 1), weight=1)

                for index, item in enumerate(file_items):
                    button = ctk.CTkButton(
                        buttons_frame,
                        text=item["label"],
                        anchor="w",
                        height=34,
                        font=("Segoe UI", 11, "bold"),
                        fg_color="#173041",
                        hover_color="#1f4d70",
                        command=lambda target_path=item["path"]: self.open_folder_file_detail(target_path),
                    )
                    button.grid(
                        row=index // 2,
                        column=index % 2,
                        sticky="ew",
                        padx=4,
                        pady=4,
                    )

        report_container = ctk.CTkFrame(report_surface)
        report_container.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        report_container.grid_rowconfigure(0, weight=1)
        report_container.grid_columnconfigure(0, weight=1)

        textbox = ctk.CTkTextbox(report_container, font=("Consolas", 13))
        textbox.grid(row=0, column=0, sticky="nsew")
        textbox.insert("1.0", self.report_text)
        textbox.configure(state="disabled")

    def show_metadata_view(self) -> None:
        self.active_selected_file_view = "metadata"
        self._clear_content()
        self._refresh_sidebar_visual_state()
        self._set_active_button("dashboard")
        self._set_view_header(
            "🧬 Metadati",
            "Principali metadati dichiarati del file selezionato, presentati in forma leggibile senza sostituire il report tecnico.",
        )

        active_results = self._get_active_detail_results()
        if not active_results:
            self._create_center_message(
                NO_ANALYSIS_MESSAGE,
                "Seleziona un file analizzato per visualizzare i dettagli.",
            )
            return

        content_parent = self._get_scrollable_content_surface()
        self._create_notice_box(
            content_parent,
            "Questi valori sono metadati dichiarati dal file. Devono essere letti con prudenza e contestualizzati.",
        )
        self._create_kv_table(content_parent, build_metadata_view_rows(active_results))

    def show_hash_view(self) -> None:
        self.active_selected_file_view = "hashes"
        self._clear_content()
        self._refresh_sidebar_visual_state()
        self._set_active_button("dashboard")
        self._set_view_header(
            "🔐 Hash",
            "Hash crittografici utili per identificazione tecnica e confronto del file selezionato.",
        )

        active_results = self._get_active_detail_results()
        if not active_results:
            self._create_center_message(
                NO_ANALYSIS_MESSAGE,
                "Seleziona un file analizzato per visualizzare i dettagli.",
            )
            return

        content_parent = self._get_scrollable_content_surface()
        self._create_notice_box(
            content_parent,
            "Se un hash non è disponibile viene mostrato come N/D.",
        )
        self._create_kv_table(content_parent, build_hash_view_rows(active_results))

    def show_risk_score_view(self) -> None:
        self.active_selected_file_view = "risk_score"
        self._clear_content()
        self._refresh_sidebar_visual_state()
        self._set_active_button("dashboard")
        self._set_view_header(
            "⚠️ Risk score",
            "Lettura prudente del punteggio di anomalia documentale del file selezionato.",
        )

        active_results = self._get_active_detail_results()
        if not active_results:
            self._create_center_message(
                NO_ANALYSIS_MESSAGE,
                "Seleziona un file analizzato per visualizzare i dettagli.",
            )
            return

        content_parent = self._get_scrollable_content_surface()
        self._create_notice_box(
            content_parent,
            f"{TRIAGE_SUPPORT_TEXT} {PRUDENT_RISK_NOTICE}",
        )
        self._create_kv_table(content_parent, build_risk_score_rows(active_results))

    def show_indicators_view(self) -> None:
        self.active_selected_file_view = "indicators"
        self._clear_content()
        self._refresh_sidebar_visual_state()
        self._set_active_button("dashboard")
        self._set_view_header(
            "📋 Indicatori",
            "Dettaglio degli indicatori strutturati che contribuiscono al risk score del file selezionato, se disponibili.",
        )

        active_results = self._get_active_detail_results()
        if not active_results:
            self._create_center_message(
                NO_ANALYSIS_MESSAGE,
                "Seleziona un file analizzato per visualizzare i dettagli.",
            )
            return

        content_parent = self._get_scrollable_content_surface()
        self._create_notice_box(
            content_parent,
            "Gli indicatori mostrati derivano solo dai dati strutturati disponibili; nulla viene inventato fuori dal report tecnico.",
        )

        indicator_rows = build_indicator_rows(active_results)
        if not indicator_rows:
            self._create_center_message("📋 Indicatori", NO_INDICATORS_MESSAGE)
            return

        formatted_rows = [(f"Indicatore {index}", f"{label} (+{score})") for index, (label, score) in enumerate(indicator_rows, start=1)]
        self._create_kv_table(content_parent, formatted_rows)

    def show_selected_file_overview_view(self) -> None:
        if self.current_analysis_type == "file":
            self.show_dashboard_view()
            return
        if self.current_analysis_type == "folder" and self.selected_folder_file_path:
            self.open_folder_file_detail(self.selected_folder_file_path)
            return
        self._clear_content()
        self.active_selected_file_view = "selected_file_overview"
        self._refresh_sidebar_visual_state()
        self._set_active_button("dashboard")
        self._set_view_header(
            "📄 File selezionato",
            "Seleziona un file analizzato per visualizzare i dettagli contestuali.",
        )
        self._create_center_message(NO_ANALYSIS_MESSAGE, "Seleziona un file analizzato per visualizzare i dettagli.")

    def show_selected_file_report_view(self) -> None:
        self.active_selected_file_view = "file_report"
        self._clear_content()
        self._refresh_sidebar_visual_state()
        self._set_active_button("dashboard")

        report_text = self._get_active_detail_report_text()
        filename = self._get_active_detail_filename()
        self._set_view_header(
            f"🧾 Report file: {filename}",
            "Report tecnico del file attualmente selezionato.",
        )

        if not report_text:
            self._create_center_message(
                NO_ANALYSIS_MESSAGE,
                "Seleziona un file analizzato per visualizzare il report tecnico del file.",
            )
            return

        report_surface = self._create_static_content_surface()
        self._create_notice_box(
            report_surface,
            "Questa vista mostra il report tecnico del file selezionato, distinto dal report cumulativo dell'analisi corrente.",
        )
        report_container = ctk.CTkFrame(report_surface)
        report_container.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        report_container.grid_rowconfigure(0, weight=1)
        report_container.grid_columnconfigure(0, weight=1)

        textbox = ctk.CTkTextbox(report_container, font=("Consolas", 13))
        textbox.grid(row=0, column=0, sticky="nsew")
        textbox.insert("1.0", report_text)
        textbox.configure(state="disabled")

    def show_info_view(self) -> None:
        self._clear_content()
        self._set_active_button("information")
        self._set_view_header(
            "❓ Informazioni",
            "Contesto sintetico sul tool e sul perimetro prudente di utilizzo.",
        )
        content_parent = self._get_scrollable_content_surface()
        self._create_notice_box(content_parent, START_VIEW_NOTICE, fg_color="#21384a")
        self._create_kv_table(
            content_parent,
            [
                ("Applicazione", "metanalisys"),
                ("Descrizione", "Analisi preliminare dei metadati Office."),
                ("Uso previsto", TRIAGE_SUPPORT_TEXT),
                ("Nota prudenziale", PRUDENT_RISK_NOTICE),
                ("Dettaglio", get_about_text().replace("\n", " | ")),
            ],
        )

    def open_folder_file_detail(self, target_path: str) -> None:
        self.selected_folder_file_path = target_path
        self.active_selected_file_view = "selected_file_overview"
        self._request_sidebar_refresh()
        self.show_folder_file_detail_view(target_path)

    def show_folder_file_detail_view(self, target_path: str) -> None:
        detail_entry = self._extract_folder_file_cache_entry(target_path)
        report_entry = detail_entry.get("report_entry", {})
        report_results = detail_entry.get("results")
        report_text = str(detail_entry.get("report_text", ""))
        filename = normalize_folder_display_value(
            report_entry.get("filename") if isinstance(report_entry, dict) else os.path.basename(target_path)
        )

        self.selected_folder_file_report_text = report_text
        self._clear_content()
        detail_surface = self._create_static_content_surface()
        self._set_active_button("dashboard")
        self._refresh_sidebar_visual_state()
        self._set_view_header(
            f"📄 Dettaglio file: {filename}",
            "Vista dedicata al file selezionato dall'analisi cartella con dati principali e report tecnico.",
        )

        self._create_notice_box(detail_surface, FOLDER_FILE_DETAIL_NOTICE)

        actions_frame = ctk.CTkFrame(detail_surface, fg_color="transparent")
        actions_frame.pack(fill="x", padx=18, pady=(0, 12))

        ctk.CTkButton(
            actions_frame,
            text="📊 Torna alla dashboard cartella",
            width=210,
            command=self.show_dashboard_view,
        ).pack(side="left", padx=(0, 8))

        save_button = ctk.CTkButton(
            actions_frame,
            text="💾 Salva report file",
            width=170,
            command=self.save_selected_folder_file_report,
            state="normal" if report_text else "disabled",
        )
        save_button.pack(side="left")

        self._create_kv_table(
            detail_surface,
            build_folder_file_detail_rows(
                report_entry if isinstance(report_entry, dict) else {},
                report_results if isinstance(report_results, dict) else None,
            ),
        )

        report_label = ctk.CTkLabel(
            detail_surface,
            text="Report tecnico del file",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        report_label.pack(fill="x", padx=18, pady=(0, 8))

        report_container = ctk.CTkFrame(detail_surface)
        report_container.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        report_container.grid_rowconfigure(0, weight=1)
        report_container.grid_columnconfigure(0, weight=1)

        textbox = ctk.CTkTextbox(report_container, font=("Consolas", 13))
        textbox.grid(row=0, column=0, sticky="nsew")
        if report_text:
            textbox.insert("1.0", report_text)
        else:
            error_text = normalize_folder_display_value(detail_entry.get("error"))
            if error_text == "N/D":
                error_text = "Dettaglio tecnico del file non disponibile."
            textbox.insert("1.0", f"Dettaglio non disponibile.\n\n{error_text}")
        textbox.configure(state="disabled")

    def show_about(self) -> None:
        messagebox.showinfo("Informazioni Software", get_about_text())

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

        ctk.CTkLabel(
            header_frame,
            text="Riepilogo analisi cartella",
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            header_frame,
            text=f"Cartella analizzata: {folder_path}",
            font=("Segoe UI", 13),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 4))

        ctk.CTkLabel(
            header_frame,
            text=(
                "Supporto tecnico di triage documentale: il risk score è un indice tecnico "
                "di anomalia documentale, non una prova automatica di manomissione."
            ),
            font=("Segoe UI", 12),
            justify="left",
            anchor="w",
            wraplength=1120,
        ).pack(fill="x", padx=14, pady=(0, 12))

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

        self._create_folder_treeview(container, build_folder_summary_table_rows(folder_results))

    def open_file(self) -> None:
        file = filedialog.askopenfilename(
            title="Seleziona file Office",
            filetypes=GUI_FILE_FILTERS,
        )

        if not file:
            return

        self.selected_file = file
        self.selected_path = file
        self._reset_analysis_outputs()
        self._set_path_value(file)
        self._set_status_text("File selezionato.")
        self.show_start_view()

    def open_folder(self) -> None:
        folder = filedialog.askdirectory(
            title="Seleziona cartella contenente file Office",
        )

        if not folder:
            return

        self.selected_path = folder
        self.selected_file = None
        self._reset_analysis_outputs()
        self._set_path_value(folder)
        self._set_status_text("Cartella selezionata.")
        self.show_start_view()

    def analyze(self) -> None:
        selected_path = self.path_entry.get().strip()

        try:
            target_type = resolve_analysis_target(selected_path)

            self._set_status_text("Analisi in corso...")
            self.update()

            self.selected_path = selected_path
            self.current_analysis_type = target_type
            self.report_html = ""
            self.folder_file_cache = {}
            self.selected_folder_file_path = None
            self.selected_folder_file_report_text = ""

            if target_type == "file":
                self.selected_file = selected_path
                self.report_results = analyze_office_file(selected_path)
                self.report_text = format_text_report(self.report_results)
                self._set_status_text("Analisi completata.")
            else:
                self.selected_file = None
                self.report_results = analyze_office_folder(selected_path)
                self.report_text = format_folder_text_report(self.report_results)
                self.report_html = format_folder_html_report(self.report_results)
                self._set_status_text("Analisi cartella completata.")

            self._request_sidebar_refresh(reset_scroll=True)
            self.show_dashboard_view()

        except UnsupportedFormatError:
            messagebox.showerror(
                "Formato non supportato",
                "L'estensione selezionata non è tra i formati Office riconosciuti.",
            )
            self._set_status_text("Formato non supportato.")

        except (FileAccessError, InvalidOfficeFileError) as exc:
            messagebox.showerror("Errore", str(exc))
            self._set_status_text("Errore durante analisi.")

        except Exception as exc:
            messagebox.showerror(
                "Errore",
                f"Errore inatteso durante l'analisi:\n{exc}",
            )
            self._set_status_text("Errore durante analisi.")

    def save_report(self) -> None:
        if not self.report_text:
            messagebox.showwarning(
                "Attenzione",
                "Nessun report disponibile.",
            )
            return

        if self.current_analysis_type == "folder":
            destination_dir = filedialog.askdirectory(
                title="Seleziona cartella di destinazione per i report",
            )

            if not destination_dir:
                return

            report_paths = build_destination_report_paths(self.selected_path, destination_dir)
            save_folder_text_report(self.report_results, report_paths["txt"])
            save_folder_csv_report(self.report_results, report_paths["csv"])
            save_folder_json_report(self.report_results, report_paths["json"])
            save_folder_html_report(self.report_html, report_paths["html"])

            self._set_status_text("Report cartella salvati.")
            messagebox.showinfo(
                "Completato",
                (
                    "Report dell'analisi riepilogativa di cartella salvati correttamente:\n"
                    f"- {os.path.basename(report_paths['txt'])}\n"
                    f"- {os.path.basename(report_paths['csv'])}\n"
                    f"- {os.path.basename(report_paths['json'])}\n"
                    f"- {os.path.basename(report_paths['html'])}"
                ),
            )
            return

        original = os.path.splitext(os.path.basename(self.selected_file))[0]
        default_name = original + "_forensic_report.txt"

        path = filedialog.asksaveasfilename(
            title="Salva Report",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Text Files", "*.txt")],
        )

        if not path:
            return

        save_text_report(self.report_text, path)
        self._set_status_text("Report salvato.")
        messagebox.showinfo("Completato", "Report salvato correttamente.")

    def save_selected_folder_file_report(self) -> None:
        if not self.selected_folder_file_path or not self.selected_folder_file_report_text:
            messagebox.showwarning(
                "Attenzione",
                "Nessun report singolo disponibile per il file selezionato.",
            )
            return

        default_name = os.path.splitext(os.path.basename(self.selected_folder_file_path))[0] + "_forensic_report.txt"
        path = filedialog.asksaveasfilename(
            title="Salva Report File",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Text Files", "*.txt")],
        )

        if not path:
            return

        save_text_report(self.selected_folder_file_report_text, path)
        self._set_status_text("Report file salvato.")
        messagebox.showinfo("Completato", "Report del file salvato correttamente.")


if __name__ == "__main__":
    app = App()
    app.mainloop()
