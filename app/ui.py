"""PySide6 user interface for the dashboard."""

from __future__ import annotations

from pathlib import Path
import platform

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app import config
from app.data_loader import DataValidationError, dataframe_to_school_records, load_schools_excel
from app.sync import SyncResult, check_for_updates
from app.updater import SoftwareUpdateResult, check_for_software_update, download_installer, install_downloaded_update
from app.utils import is_probable_email, load_json_file, normalise_url, readable_label, resource_path


class SyncWorker(QThread):
    completed = Signal(object)

    def __init__(self, cache_dir: Path):
        super().__init__()
        self.cache_dir = cache_dir

    def run(self) -> None:
        self.completed.emit(check_for_updates(self.cache_dir))


class SoftwareUpdateWorker(QThread):
    completed = Signal(object)

    def __init__(self, current_version: str, platform_name: str):
        super().__init__()
        self.current_version = current_version
        self.platform_name = platform_name

    def run(self) -> None:
        self.completed.emit(check_for_software_update(self.current_version, self.platform_name))


class MainWindow(QMainWindow):
    def __init__(self, cache_dir: Path, theme: dict[str, str]):
        super().__init__()
        self.cache_dir = cache_dir
        self.theme = {**config.DEFAULT_THEME, **theme}
        self.records: list[dict[str, str]] = []
        self.filtered_records: list[dict[str, str]] = []
        self.sync_worker: SyncWorker | None = None
        self.software_worker: SoftwareUpdateWorker | None = None
        self.platform_name = platform.system()
        self.installer_path: Path | None = None

        self.setWindowTitle(self.theme["app_title"])
        icon_path = resource_path("assets", "app_icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1000, 720)

        self._build_ui()
        self.reload_data(show_success=False)
        if config.AUTO_CHECK_SOFTWARE_UPDATES:
            self.check_software_updates()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 18, 24, 18)
        header_layout.setSpacing(16)

        logo = QLabel()
        logo_path = resource_path("assets", "logo.png")
        pixmap = QPixmap(str(logo_path)) if logo_path.exists() else QPixmap()
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(58, 58, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo.setText(self.theme["company_name"])
            logo.setObjectName("logoFallback")
        header_layout.addWidget(logo)

        title_block = QVBoxLayout()
        company = QLabel(self.theme["company_name"])
        company.setObjectName("company")
        title = QLabel(self.theme["app_title"])
        title.setObjectName("title")
        title_block.addWidget(company)
        title_block.addWidget(title)
        header_layout.addLayout(title_block, 1)

        self.version_label = QLabel("Data version: Loading")
        self.updated_label = QLabel("Last updated: Loading")
        self.cache_label = QLabel(f"Offline cache: {self.cache_dir}")
        meta = QVBoxLayout()
        for widget in (self.version_label, self.updated_label, self.cache_label):
            widget.setObjectName("meta")
            widget.setAlignment(Qt.AlignRight)
            meta.addWidget(widget)
        header_layout.addLayout(meta)
        layout.addWidget(header)

        content = QVBoxLayout()
        content.setContentsMargins(24, 20, 24, 24)
        content.setSpacing(14)
        layout.addLayout(content)

        self.status_banner = QLabel("Loading cached school data...")
        self.status_banner.setObjectName("statusBanner")
        self.status_banner.setWordWrap(True)
        content.addWidget(self.status_banner)

        controls = QGridLayout()
        controls.setHorizontalSpacing(12)
        controls.setVerticalSpacing(8)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by school name or displayed information")
        self.search_box.textChanged.connect(self._apply_filter)
        self.school_combo = QComboBox()
        self.school_combo.currentIndexChanged.connect(self._display_selected_school)
        self.update_button = QPushButton("Check data updates")
        self.update_button.clicked.connect(self.check_updates)
        self.software_check_button = QPushButton("Check software updates")
        self.software_check_button.clicked.connect(self.check_software_updates)
        self.install_update_button = QPushButton("Install update")
        self.install_update_button.setEnabled(False)
        self.install_update_button.clicked.connect(self.install_update)
        self.reload_button = QPushButton("Reload data")
        self.reload_button.clicked.connect(lambda: self.reload_data(show_success=True))
        controls.addWidget(QLabel("Search"), 0, 0)
        controls.addWidget(self.search_box, 0, 1)
        controls.addWidget(QLabel("School"), 1, 0)
        controls.addWidget(self.school_combo, 1, 1)
        controls.addWidget(self.update_button, 0, 2)
        controls.addWidget(self.software_check_button, 0, 3)
        controls.addWidget(self.reload_button, 1, 2)
        controls.addWidget(self.install_update_button, 1, 3)
        controls.setColumnStretch(1, 1)
        content.addLayout(controls)

        self.school_title = QLabel("Select a school")
        self.school_title.setObjectName("schoolTitle")
        content.addWidget(self.school_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch(1)
        scroll.setWidget(self.cards_container)
        content.addWidget(scroll, 1)

        self.setStyleSheet(self._stylesheet())

    def reload_data(self, show_success: bool) -> None:
        try:
            df = load_schools_excel(self.cache_dir / config.EXCEL_FILENAME)
            self.records = dataframe_to_school_records(df)
            self._load_version_metadata()
            self._apply_filter()
            if show_success:
                self._set_status("Cached data reloaded successfully.", "success")
            else:
                self._set_status("Showing cached school data. Internet is not required.", "success")
        except DataValidationError as exc:
            self.records = []
            self._apply_filter()
            self._set_status(str(exc), "error")

    def check_updates(self) -> None:
        if self.sync_worker and self.sync_worker.isRunning():
            return
        self.update_button.setEnabled(False)
        self._set_status("Checking GitHub for updated school data...", "info")
        self.sync_worker = SyncWorker(self.cache_dir)
        self.sync_worker.completed.connect(self._sync_finished)
        self.sync_worker.start()

    def _sync_finished(self, result: SyncResult) -> None:
        self.update_button.setEnabled(True)
        self._set_status(result.message, "success" if result.updated else "info")
        if result.updated:
            self.reload_data(show_success=False)
        if config.AUTO_CHECK_SOFTWARE_UPDATES:
            self.check_software_updates()

    def check_software_updates(self) -> None:
        if self.software_worker and self.software_worker.isRunning():
            return
        self.software_check_button.setEnabled(False)
        self._set_status("Checking for software updates from GitHub Releases...", "info")
        self.software_worker = SoftwareUpdateWorker(config.APP_VERSION, self.platform_name)
        self.software_worker.completed.connect(self._software_update_finished)
        self.software_worker.start()

    def _software_update_finished(self, result: SoftwareUpdateResult) -> None:
        self.software_check_button.setEnabled(True)
        if result.update_available and result.installer_url and result.installer_name:
            destination = self.cache_dir / result.installer_name
            try:
                self.installer_path = download_installer(result.installer_url, destination)
                self.install_update_button.setEnabled(True)
                self._set_status(
                    f"{result.message} Downloaded to {self.installer_path}. Click Install update when ready.",
                    "success",
                )
            except Exception as exc:
                self.installer_path = None
                self.install_update_button.setEnabled(False)
                self._set_status(f"Update found but download failed. Continuing normally. Details: {exc}", "info")
            return

        self.installer_path = None
        self.install_update_button.setEnabled(False)
        self._set_status(result.message, "info")

    def install_update(self) -> None:
        if not self.installer_path or not self.installer_path.exists():
            self._set_status("No downloaded installer is available yet.", "info")
            return
        try:
            message = install_downloaded_update(self.platform_name, self.installer_path)
            self._set_status(message, "success")
            if self.platform_name == "Windows":
                QApplication.instance().quit()
        except Exception as exc:
            self._set_status(f"Could not start installer. Continuing normally. Details: {exc}", "error")

    def _load_version_metadata(self) -> None:
        version = load_json_file(self.cache_dir / config.VERSION_FILENAME)
        self.version_label.setText(f"Data version: {version.get('data_version', 'Unknown')}")
        self.updated_label.setText(f"Last updated: {version.get('updated_at', 'Unknown')}")
        self.cache_label.setText(f"Offline cache: {self.cache_dir}")

    def _apply_filter(self) -> None:
        query = self.search_box.text().strip().lower() if hasattr(self, "search_box") else ""
        if query:
            self.filtered_records = [r for r in self.records if query in " ".join(r.values()).lower()]
        else:
            self.filtered_records = list(self.records)
        self.school_combo.blockSignals(True)
        self.school_combo.clear()
        for record in self.filtered_records:
            self.school_combo.addItem(record.get("school_name", "Unnamed school"), record)
        self.school_combo.blockSignals(False)
        self._display_selected_school()

    def _display_selected_school(self) -> None:
        record = self.school_combo.currentData()
        self._clear_cards()
        if not record:
            self.school_title.setText("No matching school found")
            self.cards_layout.insertWidget(0, QLabel("Try a different search term or reload the cached data."))
            return
        self.school_title.setText(record.get("school_name", "Selected school"))
        for column, value in record.items():
            if column == "school_id":
                continue
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, self._make_card(column, value))

    def _make_card(self, column: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout = QVBoxLayout(card)
        label = QLabel(readable_label(column))
        label.setObjectName("cardLabel")
        body = QLabel(value or config.NOT_PROVIDED)
        body.setObjectName("cardBody")
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextBrowserInteraction)
        body.setOpenExternalLinks(True)
        if value != config.NOT_PROVIDED and (column.lower() == "website" or value.startswith(("http://", "https://", "www."))):
            url = normalise_url(value)
            body.setText(f'<a href="{url}">{value}</a>')
        elif value != config.NOT_PROVIDED and (column.lower() == "email" or is_probable_email(value)):
            body.setText(f'<a href="mailto:{value}">{value}</a>')
        layout.addWidget(label)
        layout.addWidget(body)
        return card

    def _clear_cards(self) -> None:
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _set_status(self, message: str, level: str) -> None:
        self.status_banner.setText(message)
        self.status_banner.setProperty("level", level)
        self.status_banner.style().unpolish(self.status_banner)
        self.status_banner.style().polish(self.status_banner)

    def _stylesheet(self) -> str:
        primary = self.theme["primary_colour"]
        secondary = self.theme["secondary_colour"]
        accent = self.theme["accent_colour"]
        text = self.theme["text_colour"]
        return f"""
        QMainWindow, QWidget {{ background: {secondary}; color: {text}; font-family: Arial, Helvetica, sans-serif; font-size: 14px; }}
        #header {{ background: {primary}; color: white; }}
        #company {{ color: #DCE7FF; font-size: 14px; font-weight: 600; }}
        #title {{ color: white; font-size: 26px; font-weight: 700; }}
        #meta {{ color: white; font-size: 12px; }}
        #logoFallback {{ color: white; font-weight: 700; border: 1px solid white; padding: 10px; border-radius: 8px; }}
        QLineEdit, QComboBox {{ background: white; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px; }}
        QPushButton {{ background: {accent}; color: white; border: 0; border-radius: 6px; padding: 9px 14px; font-weight: 600; }}
        QPushButton:disabled {{ background: #94A3B8; }}
        #statusBanner {{ background: #E0F2FE; color: #075985; border-radius: 8px; padding: 10px 12px; }}
        #statusBanner[level="error"] {{ background: #FEE2E2; color: #991B1B; }}
        #statusBanner[level="success"] {{ background: #DCFCE7; color: #166534; }}
        #schoolTitle {{ font-size: 22px; font-weight: 700; margin-top: 8px; }}
        #card {{ background: white; border: 1px solid #E5E7EB; border-radius: 10px; padding: 10px; }}
        #cardLabel {{ color: {primary}; font-weight: 700; font-size: 13px; }}
        #cardBody {{ color: {text}; font-size: 14px; }}
        """


def run_app(cache_dir: Path, theme: dict[str, str]) -> int:
    app = QApplication([])
    window = MainWindow(cache_dir, theme)
    window.show()
    return app.exec()
