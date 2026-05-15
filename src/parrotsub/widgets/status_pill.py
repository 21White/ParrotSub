"""Pill-shaped status indicator (coloured dot + label)."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget


class StatusPill(QFrame):
    """Rounded pill with a coloured dot + label.

    States: ``"idle"``, ``"active"``, ``"warn"``.
    Switching state re-polishes the widget so QSS picks the new selector.
    """

    def __init__(self, text: str = "Idle", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusPill")
        self.setProperty("state", "idle")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 12, 4)
        layout.setSpacing(8)

        self._dot = QFrame(self)
        self._dot.setObjectName("StatusDot")
        layout.addWidget(self._dot, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._label = QLabel(text, self)
        self._label.setObjectName("StatusPillText")
        layout.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignVCenter)

    def set_state(self, state: str, text: Optional[str] = None) -> None:
        self.setProperty("state", state)
        if text is not None:
            self._label.setText(text)
        # Force re-polish to apply the new state's stylesheet.
        for w in (self, self._dot, self._label):
            w.style().unpolish(w)
            w.style().polish(w)
