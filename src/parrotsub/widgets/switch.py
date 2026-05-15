"""Toggle switch (looks like a shadcn Switch, behaves like QCheckBox)."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import QCheckBox, QWidget


class Switch(QCheckBox):
    def __init__(self, label: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(label, parent)
        self.setObjectName("Switch")
