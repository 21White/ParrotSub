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

from parrotsub.i18n import t, translator
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
        self._title_label = QLabel(t("exports.title"))
        self._title_label.setObjectName("CardTitle")
        self._title_label.setStyleSheet("font-size: 18px;")
        self._subtitle_label = QLabel(self._subtitle_text())
        self._subtitle_label.setObjectName("CardDescription")
        self._subtitle_label.setWordWrap(True)
        title_col.addWidget(self._title_label)
        title_col.addWidget(self._subtitle_label)
        title_row.addLayout(title_col, stretch=1)

        self._open_root_btn = QPushButton(t("exports.action.open_folder"))
        self._open_root_btn.setProperty("variant", "outline")
        self._open_root_btn.clicked.connect(self._open_root)
        title_row.addWidget(self._open_root_btn)

        self._refresh_btn = QPushButton(t("exports.action.refresh"))
        self._refresh_btn.setProperty("variant", "secondary")
        self._refresh_btn.clicked.connect(self.refresh)
        title_row.addWidget(self._refresh_btn)

        outer.addLayout(title_row)

        # List card
        self._sessions_card = Card(
            title=t("exports.sessions.title"),
            description=t("exports.sessions.desc"),
        )
        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._open_selected)
        self._sessions_card.body_layout.addWidget(self._list)

        actions_row = QHBoxLayout()
        self._open_btn = QPushButton(t("exports.action.open_finder"))
        self._open_btn.setProperty("variant", "outline")
        self._open_btn.clicked.connect(self._open_selected)
        actions_row.addWidget(self._open_btn)

        self._open_html_btn = QPushButton(t("exports.action.open_html"))
        self._open_html_btn.setProperty("variant", "outline")
        self._open_html_btn.clicked.connect(self._open_html)
        actions_row.addWidget(self._open_html_btn)

        actions_row.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        self._sessions_card.body_layout.addLayout(actions_row)

        outer.addWidget(self._sessions_card, stretch=1)

        translator().locale_changed.connect(self._retranslate)

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
    def _subtitle_text(self) -> str:
        return t("exports.subtitle", root=self._cfg.SavePath)

    def _retranslate(self, _locale: str) -> None:
        self._title_label.setText(t("exports.title"))
        self._subtitle_label.setText(self._subtitle_text())
        self._open_root_btn.setText(t("exports.action.open_folder"))
        self._refresh_btn.setText(t("exports.action.refresh"))
        self._open_btn.setText(t("exports.action.open_finder"))
        self._open_html_btn.setText(t("exports.action.open_html"))
        self._sessions_card.title_label.setText(t("exports.sessions.title"))
        self._sessions_card.description_label.setText(t("exports.sessions.desc"))
        # Rebuild the list so any "empty" placeholder text picks up the new locale.
        self.refresh()

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        self._list.clear()
        root = os.path.expanduser(self._cfg.SavePath)
        if not os.path.isdir(root):
            placeholder = QListWidgetItem(t("exports.empty.no_dir"))
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
            placeholder = QListWidgetItem(t("exports.empty.empty_dir"))
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
