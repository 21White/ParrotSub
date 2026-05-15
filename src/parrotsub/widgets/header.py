"""Top header bar with title, version and a status pill."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QSpacerItem, QWidget

from parrotsub.widgets.status_pill import StatusPill


class Header(QFrame):
    def __init__(
        self,
        title: str = "ParrotSub",
        version: str = "v0.1.0",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Header")
        self.setFixedHeight(57)

        row = QHBoxLayout(self)
        row.setContentsMargins(20, 0, 20, 0)
        row.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("HeaderTitle")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        row.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.version_label = QLabel(version)
        self.version_label.setObjectName("HeaderVersion")
        row.addWidget(self.version_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.status = StatusPill("Idle")
        row.addWidget(self.status, alignment=Qt.AlignmentFlag.AlignVCenter)
