"""Icon-only buttons used by the sidebar / header (with theme-aware repaint)."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QPushButton, QWidget

from parrotsub.icons import make_icon
from parrotsub.theme import Palette


class IconButton(QPushButton):
    """A 40x40 icon button (variant: ``nav`` for sidebar, ``brand`` for logo)."""

    def __init__(
        self,
        icon_name: str,
        tooltip: str,
        *,
        variant: str = "nav",
        size_px: int = 40,
        icon_px: int = 20,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._icon_name = icon_name
        self._icon_px = icon_px

        self.setObjectName("SidebarBrand" if variant == "brand" else "NavButton")
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(size_px, size_px)
        self.setIconSize(QSize(icon_px, icon_px))
        self.setFlat(True)
        self._active = False

    def set_active(self, active: bool) -> None:
        self._active = active
        self.setProperty("active", "true" if active else "false")
        # Force a re-polish so the QSS [active="true"] selector applies.
        self.style().unpolish(self)
        self.style().polish(self)

    def is_active(self) -> bool:
        return self._active

    def apply_palette(self, p: Palette) -> None:
        # Re-render the SVG icon with the colour appropriate to its variant/state.
        if self.objectName() == "SidebarBrand":
            color = p.brand_foreground
        elif self._active:
            color = p.brand
        else:
            color = p.muted_foreground
        self.setIcon(make_icon(self._icon_name, color=color, size=self._icon_px))
