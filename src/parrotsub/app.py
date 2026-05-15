"""Main application shell: sidebar + header + page stack."""

from __future__ import annotations

import sys
import webbrowser
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from realtime_subtitle import app_config
from realtime_subtitle.subtitle import RealtimeSubtitle

from parrotsub import __version__
from parrotsub.pages.exports import ExportsPage
from parrotsub.pages.home import HomePage
from parrotsub.pages.settings import SettingsPage
from parrotsub.theme import DARK, LIGHT, Palette, stylesheet
from parrotsub.widgets.header import Header
from parrotsub.widgets.sidebar import Sidebar


_NAV_ITEMS = [
    ("mic", "Tasks"),
    ("settings", "Settings"),
    ("download", "Exports"),
]

_GITHUB_URL = "https://github.com/21White/ParrotSub"


class MainWindow(QMainWindow):
    def __init__(
        self,
        rs: RealtimeSubtitle,
        cfg: app_config.AppConfig,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._rs = rs
        self._cfg = cfg
        self._theme: str = "light"
        self._palette: Palette = LIGHT

        self.setWindowTitle("ParrotSub")
        self.resize(1240, 760)
        self.setMinimumSize(960, 600)

        # Root: horizontal layout with sidebar | (header on top, stack below)
        root = QWidget(self)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar(_NAV_ITEMS)
        self.sidebar.page_requested.connect(self._switch_page)
        self.sidebar.theme_toggled.connect(self._toggle_theme)
        self.sidebar.github_requested.connect(lambda: webbrowser.open(_GITHUB_URL))
        root_layout.addWidget(self.sidebar)

        right_col = QWidget(self)
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.header = Header(
            title="ParrotSub",
            version=f"v{__version__}",
        )
        right_layout.addWidget(self.header)

        self.stack = QStackedWidget()
        self.home_page = HomePage(rs=rs, cfg=cfg)
        self.settings_page = SettingsPage(
            rs=rs, cfg=cfg, on_saved=self._on_settings_saved
        )
        self.exports_page = ExportsPage(cfg=cfg)
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.exports_page)
        right_layout.addWidget(self.stack, stretch=1)

        root_layout.addWidget(right_col, stretch=1)
        self.setCentralWidget(root)

        # Plumb home page status changes into the header pill.
        self.home_page.status_changed.connect(self.header.status.set_state)

        # Default selection
        self.sidebar.set_active(0)
        self.stack.setCurrentIndex(0)

        self._apply_theme(self._theme)

    # ------------------------------------------------------------------
    def _switch_page(self, index: int) -> None:
        self.sidebar.set_active(index)
        self.stack.setCurrentIndex(index)
        if index == 2:
            self.exports_page.refresh()

    def _toggle_theme(self) -> None:
        self._apply_theme("dark" if self._theme == "light" else "light")

    def _apply_theme(self, theme: str) -> None:
        self._theme = theme
        self._palette = DARK if theme == "dark" else LIGHT
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet(self._palette))
        # Refresh icons on widgets that need theme-aware repaint.
        self.sidebar.apply_palette(self._palette, self._theme)
        self.home_page.apply_palette(self._palette)
        self.settings_page.apply_palette(self._palette)
        self.exports_page.apply_palette(self._palette)

    def _on_settings_saved(self) -> None:
        self._cfg = app_config.get()
        self.home_page._cfg = self._cfg  # noqa: SLF001 – simple wiring
        self.home_page.refresh_from_config()
        self.exports_page._cfg = self._cfg  # noqa: SLF001
        self.exports_page.refresh()
        self.header.status.set_state("active", "Settings saved")

    # ------------------------------------------------------------------
    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt signature
        self.home_page.close_floating_windows()
        try:
            if self._rs.running:
                self._rs.stop()
        except Exception:
            pass
        event.accept()


def launch() -> int:
    """Boot a QApplication, build the backend & main window, and run the loop."""
    cfg = app_config.get()

    # The backend constructor downloads / loads heavy models; do it before the
    # event loop starts so the UI doesn't appear unresponsive.
    print("[parrotsub] Loading whisper / translation / speaker models...", flush=True)
    rs = RealtimeSubtitle()
    print("[parrotsub] Models ready, starting UI.", flush=True)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("ParrotSub")
    app.setApplicationDisplayName("ParrotSub")
    app.setOrganizationName("parrotsub")

    window = MainWindow(rs=rs, cfg=cfg)
    window.show()
    return app.exec()
