"""Left vertical icon-only sidebar (40px buttons, 56px rail)."""

from __future__ import annotations

from typing import Callable, List, Optional, Tuple

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QSpacerItem, QSizePolicy, QVBoxLayout, QWidget

from parrotsub.theme import Palette
from parrotsub.widgets.icon_button import IconButton


class Sidebar(QFrame):
    """Vertical icon nav rail (56px wide).

    Emits ``page_requested(int)`` with the index of the page button that was
    clicked, and ``theme_toggled()`` when the sun/moon button is clicked.
    """

    page_requested = pyqtSignal(int)
    theme_toggled = pyqtSignal()
    github_requested = pyqtSignal()

    def __init__(
        self,
        nav_items: List[Tuple[str, str]],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(56)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Brand cell (top, with bottom border via the Sidebar QSS).
        brand_box = QHBoxLayout()
        brand_box.setContentsMargins(8, 8, 8, 8)
        self.brand = IconButton("captions", "ParrotSub", variant="brand")
        brand_box.addWidget(self.brand)
        outer.addLayout(brand_box)

        # Top separator (1px line) is drawn by the QSS border.
        # Nav buttons.
        nav_box = QVBoxLayout()
        nav_box.setContentsMargins(8, 8, 8, 8)
        nav_box.setSpacing(4)

        self._nav_buttons: List[IconButton] = []
        for index, (icon_name, tooltip) in enumerate(nav_items):
            btn = IconButton(icon_name, tooltip, variant="nav")
            btn.clicked.connect(lambda _checked=False, i=index: self._on_nav_clicked(i))
            self._nav_buttons.append(btn)
            nav_box.addWidget(btn)

        outer.addLayout(nav_box)
        outer.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Bottom: theme toggle + GitHub
        bottom_box = QVBoxLayout()
        bottom_box.setContentsMargins(8, 8, 8, 8)
        bottom_box.setSpacing(4)

        self.theme_button = IconButton("moon", "Toggle theme", variant="nav")
        self.theme_button.clicked.connect(self.theme_toggled.emit)
        bottom_box.addWidget(self.theme_button)

        self.github_button = IconButton("github", "GitHub", variant="nav")
        self.github_button.clicked.connect(self.github_requested.emit)
        bottom_box.addWidget(self.github_button)

        outer.addLayout(bottom_box)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def set_active(self, index: int) -> None:
        for i, btn in enumerate(self._nav_buttons):
            btn.set_active(i == index)

    def apply_palette(self, p: Palette, current_theme: str) -> None:
        # Switch the toggle icon depending on the current theme.
        self.theme_button._icon_name = "sun" if current_theme == "dark" else "moon"
        # Re-render every icon so the color follows the theme.
        for btn in [self.brand, self.theme_button, self.github_button, *self._nav_buttons]:
            btn.apply_palette(p)

    # ------------------------------------------------------------------
    def _on_nav_clicked(self, index: int) -> None:
        self.page_requested.emit(index)
