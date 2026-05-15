"""Left vertical icon-only sidebar (40px buttons, 56px rail)."""

from __future__ import annotations

from typing import List, Optional, Tuple

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QSpacerItem, QSizePolicy, QVBoxLayout, QWidget

from parrotsub.i18n import t, translator
from parrotsub.theme import Palette
from parrotsub.widgets.icon_button import IconButton


class Sidebar(QFrame):
    """Vertical icon nav rail (56px wide).

    ``nav_items`` is a list of ``(icon_name, i18n_key)`` tuples where
    ``i18n_key`` is looked up in :mod:`parrotsub.i18n` so the tooltip
    follows the active locale.
    """

    page_requested = pyqtSignal(int)
    theme_toggled = pyqtSignal()
    language_toggled = pyqtSignal()
    github_requested = pyqtSignal()

    def __init__(
        self,
        nav_items: List[Tuple[str, str]],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(56)
        self._nav_keys: List[str] = [key for _, key in nav_items]

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Brand cell (top, with bottom border via the Sidebar QSS).
        brand_box = QHBoxLayout()
        brand_box.setContentsMargins(8, 8, 8, 8)
        self.brand = IconButton("captions", t("brand.tooltip"), variant="brand")
        brand_box.addWidget(self.brand)
        outer.addLayout(brand_box)

        # Nav buttons.
        nav_box = QVBoxLayout()
        nav_box.setContentsMargins(8, 8, 8, 8)
        nav_box.setSpacing(4)

        self._nav_buttons: List[IconButton] = []
        for index, (icon_name, key) in enumerate(nav_items):
            btn = IconButton(icon_name, t(key), variant="nav")
            btn.clicked.connect(lambda _checked=False, i=index: self._on_nav_clicked(i))
            self._nav_buttons.append(btn)
            nav_box.addWidget(btn)

        outer.addLayout(nav_box)
        outer.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Bottom: language toggle + theme toggle + GitHub
        bottom_box = QVBoxLayout()
        bottom_box.setContentsMargins(8, 8, 8, 8)
        bottom_box.setSpacing(4)

        self.language_button = IconButton("languages", t("nav.language.toggle"), variant="nav")
        self.language_button.clicked.connect(self.language_toggled.emit)
        bottom_box.addWidget(self.language_button)

        self.theme_button = IconButton("moon", t("nav.theme.toggle"), variant="nav")
        self.theme_button.clicked.connect(self.theme_toggled.emit)
        bottom_box.addWidget(self.theme_button)

        self.github_button = IconButton("github", t("nav.github"), variant="nav")
        self.github_button.clicked.connect(self.github_requested.emit)
        bottom_box.addWidget(self.github_button)

        outer.addLayout(bottom_box)

        # React to locale changes: refresh all tooltips.
        translator().locale_changed.connect(self._retranslate)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def set_active(self, index: int) -> None:
        for i, btn in enumerate(self._nav_buttons):
            btn.set_active(i == index)

    def apply_palette(self, p: Palette, current_theme: str) -> None:
        # Switch the toggle icon depending on the current theme.
        self.theme_button._icon_name = "sun" if current_theme == "dark" else "moon"
        for btn in [
            self.brand,
            self.language_button,
            self.theme_button,
            self.github_button,
            *self._nav_buttons,
        ]:
            btn.apply_palette(p)

    # ------------------------------------------------------------------
    def _retranslate(self, _locale: str) -> None:
        self.brand.setToolTip(t("brand.tooltip"))
        self.language_button.setToolTip(t("nav.language.toggle"))
        self.theme_button.setToolTip(t("nav.theme.toggle"))
        self.github_button.setToolTip(t("nav.github"))
        for key, btn in zip(self._nav_keys, self._nav_buttons):
            btn.setToolTip(t(key))

    def _on_nav_clicked(self, index: int) -> None:
        self.page_requested.emit(index)
