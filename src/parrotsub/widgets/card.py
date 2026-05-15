"""shadcn-style Card with optional title/description and slot for content."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class Card(QFrame):
    """Rounded, bordered container with optional header.

    Usage:
        card = Card(title="Translation", description="Translate text live")
        card.body_layout.addWidget(...)
    """

    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        parent: Optional[QWidget] = None,
        header_right: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Card")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(12)

        if title or description or header_right:
            header = QHBoxLayout()
            header.setContentsMargins(0, 0, 0, 0)
            header.setSpacing(8)

            text_col = QVBoxLayout()
            text_col.setContentsMargins(0, 0, 0, 0)
            text_col.setSpacing(2)

            if title:
                self.title_label = QLabel(title)
                self.title_label.setObjectName("CardTitle")
                text_col.addWidget(self.title_label)
            if description:
                self.description_label = QLabel(description)
                self.description_label.setObjectName("CardDescription")
                self.description_label.setWordWrap(True)
                text_col.addWidget(self.description_label)

            header.addLayout(text_col, stretch=1)
            if header_right is not None:
                header.addWidget(header_right, alignment=header.spacing() and 0)

            outer.addLayout(header)

            sep = QFrame()
            sep.setObjectName("CardSeparator")
            outer.addWidget(sep)

        self.body = QWidget(self)
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(10)
        outer.addWidget(self.body)
