"""PySide6 user interface for the dashboard."""
from __future__ import annotations

import platform
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QScrollArea, QSizePolicy, QTabWidget, QVBoxLayout, QWidget

from app import config
from app.data_loader import DataValidationError, dataframe_to_school_records, load_schools_excel
from app.sync import SyncResult, check_for_updates
from app.ui_tokens import UITokens, build_tokens
from app.updater import SoftwareUpdateResult, check_for_software_update, download_installer, install_downloaded_update
from app.user_settings import load_user_settings, save_user_settings
from app.utils import is_probable_email, load_json_file, normalise_url, readable_label, resource_path




class SyncWorker(QThread):
    completed = Signal(object)
    def __init__(self, cache_dir: Path):
        super().__init__(); self.cache_dir = cache_dir
    def run(self) -> None: self.completed.emit(check_for_updates(self.cache_dir))


class SoftwareUpdateWorker(QThread):
    completed = Signal(object)
    def __init__(self, current_version: str, platform_name: str):
        super().__init__(); self.current_version = current_version; self.platform_name = platform_name
    def run(self) -> None: self.completed.emit(check_for_software_update(self.current_version, self.platform_name))


class MainWindow(QMainWindow):
    CATEGORY_ORDER = ("Times", "Dates", "Contact", "General")

    def __init__(self, cache_dir: Path, theme: dict[str, str]):
        super().__init__()
        self.cache_dir = cache_dir
        self.theme = {**config.DEFAULT_THEME, **theme}
        self.settings_path = self.cache_dir / "user_settings.json"
        self.user_settings = self._load_user_settings()
        self.tokens: UITokens = build_tokens(theme, self.user_settings["dark_mode"])
        self.records: list[dict[str, str]] = []
        self.filtered_records: list[dict[str, str]] = []
        self.sync_worker: SyncWorker | None = None
        self.software_worker: SoftwareUpdateWorker | None = None
        self.platform_name = platform.system()
        self.installer_path: Path | None = None
        self.latest_version_text = "Unknown"

        self.setWindowTitle(f"{self.theme['app_title']} - Version {config.APP_VERSION}")
        icon_path = resource_path("assets", "app_icon.ico")
        if icon_path.exists(): self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1080, 760)
        self._build_ui(); self.reload_data(show_success=False)
        if config.AUTO_CHECK_SOFTWARE_UPDATES: self.check_software_updates()

    def _load_user_settings(self) -> dict[str, bool]:
        return load_user_settings(self.settings_path)

    def _save_user_settings(self) -> None:
        save_user_settings(self.settings_path, self.user_settings)

    def _build_ui(self) -> None:
        root = QWidget(); self.setCentralWidget(root)
        layout = QVBoxLayout(root); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        header = QFrame(); header.setObjectName("header"); header.setMinimumHeight(120)
        header_layout = QHBoxLayout(header); header_layout.setContentsMargins(24, 16, 24, 16)
        logo = QLabel(); logo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        logo.setMinimumSize(220, 64); logo.setMaximumSize(320, 88)
        pixmap = QPixmap(str(resource_path("assets", "logo.png")))
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(320, 88, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo.setText("Logo")
            logo.setObjectName("logoFallback")
            logo.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            logo.setMinimumSize(220, 64)
            logo.setMaximumSize(320, 88)
        header_layout.addWidget(logo); header_layout.addStretch(1); layout.addWidget(header)

        self.tabs = QTabWidget(); self.tabs.setObjectName("mainTabs")
        layout.addWidget(self.tabs, 1)
        self.tabs.addTab(self._build_dashboard_tab(), "Dashboard")
        self.tabs.addTab(self._build_settings_tab(), "Settings")
        self.tabs.setCurrentIndex(0)
        self.apply_theme()

    def _build_dashboard_tab(self) -> QWidget:
        page = QWidget(); container_layout = QVBoxLayout(page); container_layout.setContentsMargins(24, 20, 24, 24); container_layout.setSpacing(16)
        self.status_banner = QLabel("Loading cached school data..."); self.status_banner.setObjectName("statusBanner"); self.status_banner.setWordWrap(True); container_layout.addWidget(self.status_banner)
        self.selector_toolbar = QFrame(); self.selector_toolbar.setObjectName("toolbar"); controls = QGridLayout(self.selector_toolbar); controls.setContentsMargins(16, 14, 16, 14); controls.setHorizontalSpacing(12)
        self.search_box = QLineEdit(); self.search_box.setPlaceholderText("Search by school name or displayed information"); self.search_box.textChanged.connect(self._apply_filter)
        self.school_combo = QComboBox(); self.school_combo.currentIndexChanged.connect(self._display_selected_school)
        controls.addWidget(QLabel("Search"), 0, 0); controls.addWidget(self.search_box, 0, 1); controls.addWidget(QLabel("School"), 1, 0); controls.addWidget(self.school_combo, 1, 1); controls.setColumnStretch(1, 1)
        container_layout.addWidget(self.selector_toolbar)

        self.collapsed_selector_bar = QFrame(); self.collapsed_selector_bar.setObjectName("collapsedSelectorBar")
        collapsed_layout = QHBoxLayout(self.collapsed_selector_bar); collapsed_layout.setContentsMargins(12, 8, 12, 8); collapsed_layout.setSpacing(10)
        summary = QVBoxLayout(); summary.setSpacing(1)
        self.collapsed_school_name = QLabel("No school selected"); self.collapsed_school_name.setObjectName("collapsedSchoolName")
        self.collapsed_meta = QLabel("Data version: Loading | Last updated: Loading"); self.collapsed_meta.setObjectName("statusMeta")
        summary.addWidget(self.collapsed_school_name); summary.addWidget(self.collapsed_meta)
        self.change_school_button = QPushButton("Change school"); self.change_school_button.setObjectName("changeSchoolButton"); self.change_school_button.clicked.connect(self._on_change_school_clicked)
        collapsed_layout.addLayout(summary, 1); collapsed_layout.addWidget(self.change_school_button, 0, Qt.AlignVCenter)
        self.collapsed_selector_bar.hide(); container_layout.addWidget(self.collapsed_selector_bar)
        self.status_meta = QLabel("Data version: Loading | Last updated: Loading"); self.status_meta.setObjectName("statusMeta"); container_layout.addWidget(self.status_meta)
        self.school_title = QLabel("Select a school"); self.school_title.setObjectName("schoolTitle"); container_layout.addWidget(self.school_title)
        self.dashboard_scroll_area = QScrollArea(); self.dashboard_scroll_area.setWidgetResizable(True); self.dashboard_scroll_area.setFrameShape(QFrame.NoFrame)
        self.cards_container = QWidget(); self.cards_layout = QGridLayout(self.cards_container); self.cards_layout.setHorizontalSpacing(16); self.cards_layout.setVerticalSpacing(16)
        self.dashboard_scroll_area.setWidget(self.cards_container); container_layout.addWidget(self.dashboard_scroll_area, 1)
        self.dashboard_scrollbar = self.dashboard_scroll_area.verticalScrollBar()
        self.dashboard_scrollbar.valueChanged.connect(self._on_dashboard_scroll)
        self.selector_collapsed = False
        return page

    def _build_settings_tab(self) -> QWidget:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(24, 20, 24, 24); layout.setSpacing(16)
        self.application_card = self._create_settings_card("Application")
        self.application_card.layout().addWidget(QLabel(f"App name: {config.APP_NAME}"))
        self.application_card.layout().addWidget(QLabel(f"Company: {config.COMPANY_NAME}"))
        self.application_card.layout().addWidget(QLabel(f"Current version: {config.APP_VERSION}"))
        self.application_card.layout().addWidget(QLabel(f"Platform: {self.platform_name}"))

        self.update_card = self._create_settings_card("Software Updates")
        self.update_status = QLabel("Status: Waiting to check updates")
        self.update_latest = QLabel("Latest version: Unknown")
        self.update_source = QLabel(f"Source: {config.GITHUB_RELEASES_API_URL}"); self.update_source.setObjectName("statusMeta")
        self.check_updates_button = QPushButton("Check for updates"); self.check_updates_button.clicked.connect(self.check_software_updates)
        self.install_update_button = QPushButton("Install update"); self.install_update_button.setEnabled(False); self.install_update_button.clicked.connect(self.install_update)
        self.update_card.layout().addWidget(QLabel(f"Current app version: {config.APP_VERSION}"))
        self.update_card.layout().addWidget(self.update_latest); self.update_card.layout().addWidget(self.update_status)
        btns = QHBoxLayout(); btns.addWidget(self.check_updates_button); btns.addWidget(self.install_update_button); btns.addStretch(1)
        self.update_card.layout().addLayout(btns); self.update_card.layout().addWidget(self.update_source)

        self.appearance_card = self._create_settings_card("Appearance")
        self.dark_mode_toggle = QCheckBox("Dark mode"); self.dark_mode_toggle.setChecked(self.user_settings["dark_mode"]); self.dark_mode_toggle.toggled.connect(self._toggle_dark_mode)
        self.appearance_card.layout().addWidget(self.dark_mode_toggle)

        self.cache_card = self._create_settings_card("Cache / Data")
        self.cache_meta = QLabel(f"Cache location: {self.cache_dir}")
        self.cache_card.layout().addWidget(self.cache_meta)

        for card in (self.application_card, self.update_card, self.appearance_card, self.cache_card): layout.addWidget(card)
        layout.addStretch(1); return page

    def _create_settings_card(self, title: str) -> QFrame:
        card = QFrame(); card.setObjectName("categoryCard"); lay = QVBoxLayout(card); lay.setContentsMargins(16, 16, 16, 16); lay.setSpacing(8)
        lab = QLabel(title); lab.setObjectName("categoryTitle"); lay.addWidget(lab); return card

    def apply_theme(self) -> None:
        self.tokens = build_tokens(self.theme, self.user_settings["dark_mode"])
        self.setStyleSheet(self._stylesheet())

    def _toggle_dark_mode(self, enabled: bool) -> None:
        self.user_settings["dark_mode"] = enabled
        self._save_user_settings()
        self.apply_theme()

    def reload_data(self, show_success: bool) -> None:
        try:
            df = load_schools_excel(self.cache_dir / config.EXCEL_FILENAME); self.records = dataframe_to_school_records(df); self._load_version_metadata(); self._apply_filter()
            self._set_status("Cached data reloaded successfully." if show_success else "Showing cached school data. Internet is not required.", "success")
        except DataValidationError as exc:
            self.records = []; self._apply_filter(); self._set_status(str(exc), "error")

    def check_software_updates(self) -> None:
        if self.software_worker and self.software_worker.isRunning(): return
        self.update_status.setText("Status: Checking for software updates...")
        self.software_worker = SoftwareUpdateWorker(config.APP_VERSION, self.platform_name)
        self.software_worker.completed.connect(self._software_update_finished); self.software_worker.start()

    def _software_update_finished(self, result: SoftwareUpdateResult) -> None:
        self.latest_version_text = result.latest_version or "Unknown"
        self.update_latest.setText(f"Latest version: {self.latest_version_text}")
        if result.update_available and result.installer_url and result.installer_name:
            try:
                self.installer_path = download_installer(result.installer_url, self.cache_dir / result.installer_name)
                self.install_update_button.setEnabled(True)
                self.update_status.setText(f"Status: Update available ({result.latest_version}). Installer downloaded.")
            except Exception as exc:
                self.installer_path = None; self.install_update_button.setEnabled(False); self.update_status.setText(f"Status: Update found but download failed: {exc}")
            return
        self.installer_path = None; self.install_update_button.setEnabled(False); self.update_status.setText(f"Status: {result.message}")

    def install_update(self) -> None:
        if not self.installer_path or not self.installer_path.exists(): self.update_status.setText("Status: No downloaded installer is available yet."); return
        try:
            message = install_downloaded_update(self.platform_name, self.installer_path); self.update_status.setText(f"Status: {message}")
            if self.platform_name == "Windows": QApplication.instance().quit()
        except Exception as exc: self.update_status.setText(f"Status: Could not start installer. Details: {exc}")

    def _load_version_metadata(self) -> None:
        version = load_json_file(self.cache_dir / config.VERSION_FILENAME); dv = version.get("data_version", "Unknown"); lu = version.get("updated_at", "Unknown")
        self.status_meta.setText(f"Data version: {dv} | Last updated: {lu}")
        if hasattr(self, "collapsed_meta"):
            self.collapsed_meta.setText(f"Data version: {dv} | Last updated: {lu}")
        self.cache_meta.setText(f"Data version: {dv} | Last updated: {lu}\nCache location: {self.cache_dir}")

    def _set_status(self, message: str, level: str) -> None:
        self.status_banner.setText(message); self.status_banner.setProperty("level", level); self.status_banner.style().unpolish(self.status_banner); self.status_banner.style().polish(self.status_banner)

    def _apply_filter(self) -> None:
        q = self.search_box.text().strip().lower() if hasattr(self, "search_box") else ""
        self.filtered_records = [r for r in self.records if q in " ".join(r.values()).lower()] if q else list(self.records)
        self.school_combo.blockSignals(True); self.school_combo.clear()
        for r in self.filtered_records: self.school_combo.addItem(r.get("school_name", "Unnamed school"), r)
        self.school_combo.blockSignals(False); self._display_selected_school()

    def _display_selected_school(self) -> None:
        record = self.school_combo.currentData(); self._clear_cards()
        if not record:
            self.school_title.setText("No matching school found"); self.collapsed_school_name.setText("No school selected")
            self.cards_layout.addWidget(QLabel("Try a different search term or reload the cached data."), 0, 0); self._set_selector_collapsed(False); return
        school_name = record.get("school_name", "Selected school")
        self.school_title.setText(school_name); self.collapsed_school_name.setText(school_name)
        grouped = self._group_fields(record)
        for idx, category in enumerate(self.CATEGORY_ORDER): self.cards_layout.addWidget(self._make_category_card(category, grouped[category]), *divmod(idx, 2))
        self._on_dashboard_scroll(self.dashboard_scrollbar.value() if hasattr(self, "dashboard_scrollbar") else 0)


    def _selected_school_exists(self) -> bool:
        return bool(self.school_combo.currentData()) if hasattr(self, "school_combo") else False

    def _should_collapse_selector(self, scroll_value: int) -> bool:
        return self._selected_school_exists() and scroll_value > 40

    def _set_selector_collapsed(self, collapsed: bool) -> None:
        self.selector_collapsed = collapsed
        self.selector_toolbar.setVisible(not collapsed)
        self.collapsed_selector_bar.setVisible(collapsed)

    def _on_dashboard_scroll(self, value: int) -> None:
        self._set_selector_collapsed(self._should_collapse_selector(value))

    def _on_change_school_clicked(self) -> None:
        self._set_selector_collapsed(False)
        self.search_box.setFocus()

    def _group_fields(self, record: dict[str, str]) -> dict[str, list[tuple[str, str]]]:
        grouped = {name: [] for name in self.CATEGORY_ORDER}
        for c, v in record.items():
            if c != "school_id": grouped[self._resolve_category(c)].append((c, v))
        return grouped

    def _resolve_category(self, column: str) -> str:
        key = column.lower()
        if any(t in key for t in ("time", "timetable", "session", "opening", "closing", "pool")): return "Times"
        if any(t in key for t in ("date", "term", "half", "inset", "holiday", "deadline")): return "Dates"
        if any(t in key for t in ("manager", "email", "phone", "website", "address", "contact")): return "Contact"
        return "General"

    def _make_category_card(self, category: str, fields: list[tuple[str, str]]) -> QFrame:
        card = QFrame(); card.setObjectName("categoryCard"); card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout = QVBoxLayout(card); layout.setContentsMargins(16, 16, 16, 16); layout.setSpacing(8)
        t = QLabel(category); t.setObjectName("categoryTitle"); layout.addWidget(t)
        if not fields:
            empty = QLabel(config.NOT_PROVIDED); empty.setObjectName("cardBody"); layout.addWidget(empty); return card
        for column, value in fields:
            field = QFrame(); field.setObjectName("fieldRow"); fl = QVBoxLayout(field); fl.setContentsMargins(0, 0, 0, 6); fl.setSpacing(4)
            label = QLabel(readable_label(column)); label.setObjectName("cardLabel"); body = QLabel(value or config.NOT_PROVIDED); body.setObjectName("cardBody"); body.setWordWrap(True); body.setTextInteractionFlags(Qt.TextBrowserInteraction); body.setOpenExternalLinks(True)
            if value != config.NOT_PROVIDED and (column.lower() == "website" or value.startswith(("http://", "https://", "www."))): body.setText(f'<a href="{normalise_url(value)}">{value}</a>')
            elif value != config.NOT_PROVIDED and (column.lower() == "email" or is_probable_email(value)): body.setText(f'<a href="mailto:{value}">{value}</a>')
            fl.addWidget(label); fl.addWidget(body); layout.addWidget(field)
        layout.addStretch(1); return card

    def _clear_cards(self) -> None:
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0); widget = item.widget()
            if widget: widget.deleteLater()

    def _stylesheet(self) -> str:
        t = self.tokens
        return f"""
        QMainWindow, QWidget {{ background: {t.canvas_surface}; color: {t.text_primary}; font-family: {t.font_family}; font-size: 14px; }}
        QLabel {{ background: transparent; border: none; }}
        QFrame {{ background-color: transparent; }}
        #header {{ background: {self.theme['primary_colour']}; border-bottom: 1px solid {t.action_brand_pressed}; min-height: 120px; }}
        #logoFallback {{ color: {t.text_inverse}; border: 1px solid {t.text_inverse}; border-radius: {t.radius_md}px; padding: 6px 10px; font-weight: 600; }}
        #mainTabs::pane {{ border: none; }}
        QTabBar::tab {{ background: {t.surface_raised}; border: 1px solid {t.border_subtle}; padding: 8px 14px; margin-right: 4px; border-top-left-radius: {t.radius_md}px; border-top-right-radius: {t.radius_md}px; }}
        QTabBar::tab:selected {{ background: {t.surface_default}; border-color: {t.border_default}; }}
        #statusMeta {{ color: {t.text_tertiary}; font-size: 12px; }}
        #toolbar, #categoryCard {{ background: {t.surface_default}; border: 1px solid {t.border_subtle}; border-radius: {t.radius_lg}px; }}
        QLineEdit, QComboBox {{ background: {t.surface_input}; border: 1px solid {t.border_default}; border-radius: {t.radius_md}px; padding: 9px 10px; }}
        QPushButton {{ background: {t.action_brand}; color: {t.text_inverse}; border-radius: {t.radius_md}px; padding: 9px 14px; font-weight: 600; }}
        QPushButton:disabled {{ background: {t.border_default}; color: {t.text_tertiary}; }}
        #statusBanner {{ background: {t.status_info_bg}; color: {t.status_info_fg}; border: 1px solid {t.border_subtle}; border-radius: {t.radius_md}px; padding: 8px 10px; }}
        #statusBanner[level="error"] {{ background: {t.status_danger_bg}; color: {t.status_danger_fg}; }}
        #statusBanner[level="success"] {{ background: {t.status_success_bg}; color: {t.status_success_fg}; }}
        #statusBanner[level="warning"] {{ background: {t.status_warning_bg}; color: {t.status_warning_fg}; }}
        #schoolTitle {{ font-size: 28px; font-weight: 600; }} #categoryTitle {{ color: {self.theme['primary_colour']}; font-size: 16px; font-weight: 600; }}
        #collapsedSelectorBar {{ background: {t.surface_default}; border: 1px solid {t.border_subtle}; border-radius: {t.radius_md}px; min-height: 48px; max-height: 56px; }}
        #collapsedSchoolName {{ font-size: 15px; font-weight: 600; color: {t.text_primary}; }}
        #changeSchoolButton {{ padding: 7px 12px; }}
        #cardLabel {{ color: {t.text_tertiary}; font-size: 12px; font-weight: 600; }} #fieldRow {{ border-bottom: 1px solid {t.border_subtle}; }}
        """


def run_app(cache_dir: Path, theme: dict[str, str]) -> int:
    app = QApplication([]); window = MainWindow(cache_dir, theme); window.show(); return app.exec()
