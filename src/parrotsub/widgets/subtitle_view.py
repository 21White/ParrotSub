"""A read-only QTextEdit styled for subtitle display."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QTextEdit, QWidget


class SubtitleView(QTextEdit):
    def __init__(self, placeholder: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("SubtitleView")
        self.setReadOnly(True)
        self.setPlaceholderText(placeholder)
        self.setAcceptRichText(False)

    def set_text(self, text: str) -> None:
        # Avoid noisy cursor jumps; preserve the user's scroll if they scrolled up.
        bar = self.verticalScrollBar()
        at_bottom = bar.value() >= bar.maximum() - 4
        self.setPlainText(text)
        if at_bottom:
            self.moveCursor(QTextCursor.MoveOperation.End)
            bar.setValue(bar.maximum())
