"""Exports browser – lists every saved session under cfg.SavePath."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from realtime_subtitle import app_config

from parrotsub.icons import make_icon
from parrotsub.theme import Palette
from parrotsub.widgets.card import Card


class ExportsPage(QWidget):
    """Browse the directory the original exporter writes into."""

    def __init__(self, cfg: app_config.AppConfig, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._cfg = cfg

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)

        # Header row
        title_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Exports")
        title.setObjectName("CardTitle")
        title.setStyleSheet("font-size: 18px;")
        subtitle = QLabel(
            f"Sessions saved by Export are listed below. Storage root: {cfg.SavePath}"
        )
        subtitle.setObjectName("CardDescription")
        subtitle.setWordWrap(True)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        title_row.addLayout(title_col, stretch=1)

        self._open_root_btn = QPushButton(" Open folder")
        self._open_root_btn.setProperty("variant", "outline")
        self._open_root_btn.clicked.connect(self._open_root)
        title_row.addWidget(self._open_root_btn)

        self._refresh_btn = QPushButton(" Refresh")
        self._refresh_btn.setProperty("variant", "secondary")
        self._refresh_btn.clicked.connect(self.refresh)
        title_row.addWidget(self._refresh_btn)

        outer.addLayout(title_row)

        # List card
        list_card = Card(
            title="Sessions",
            description="Double-click a session to open its folder in Finder.",
        )
        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._open_selected)
        list_card.body_layout.addWidget(self._list)

        actions_row = QHBoxLayout()
        self._open_btn = QPushButton(" Open in Finder")
        self._open_btn.setProperty("variant", "outline")
        self._open_btn.clicked.connect(self._open_selected)
        actions_row.addWidget(self._open_btn)

        self._open_html_btn = QPushButton(" Open transcription.html")
        self._open_html_btn.setProperty("variant", "outline")
        self._open_html_btn.clicked.connect(self._open_html)
        actions_row.addWidget(self._open_html_btn)

        actions_row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        list_card.body_layout.addLayout(actions_row)

        outer.addWidget(list_card, stretch=1)

        self.refresh()

    # ------------------------------------------------------------------
    def apply_palette(self, p: Palette) -> None:
        for btn, name in [
            (self._refresh_btn, "refresh-cw"),
            (self._open_root_btn, "folder"),
            (self._open_btn, "folder"),
            (self._open_html_btn, "languages"),
        ]:
            btn.setIcon(make_icon(name, color=p.foreground, size=16))

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        self._list.clear()
        root = os.path.expanduser(self._cfg.SavePath)
        if not os.path.isdir(root):
            placeholder = QListWidgetItem(
                "No exports yet — your first 'Export session' will appear here."
            )
            placeholder.setFlags(placeholder.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._list.addItem(placeholder)
            return

        entries = []
        for name in os.listdir(root):
            full = os.path.join(root, name)
            if os.path.isdir(full):
                entries.append((name, full, os.path.getmtime(full)))
        entries.sort(key=lambda x: x[2], reverse=True)

        if not entries:
            placeholder = QListWidgetItem(
                "Storage folder exists but is empty."
            )
            placeholder.setFlags(placeholder.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._list.addItem(placeholder)
            return

        for name, full, _ in entries:
            artefacts = []
            for fname in ("audio.wav", "subtitles.srt", "subtitles.lrc", "transcription.html"):
                if os.path.exists(os.path.join(full, fname)):
                    artefacts.append(fname.split(".")[-1].upper())
            label = f"{name}    ·    {' / '.join(artefacts) or 'empty'}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, full)
            self._list.addItem(item)

    # ------------------------------------------------------------------
    def _open_root(self) -> None:
        root = os.path.expanduser(self._cfg.SavePath)
        os.makedirs(root, exist_ok=True)
        _open_path(root)

    def _open_selected(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            _open_path(path)

    def _open_html(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        folder = item.data(Qt.ItemDataRole.UserRole)
        if not folder:
            return
        html = os.path.join(folder, "transcription.html")
        if os.path.exists(html):
            _open_path(html)


def _open_path(path: str) -> None:
    if sys.platform == "darwin":
        subprocess.Popen(["open", path])
    elif sys.platform.startswith("linux"):
        subprocess.Popen(["xdg-open", path])
    elif sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
