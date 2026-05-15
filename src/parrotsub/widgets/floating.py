"""Modern, frameless, translucent floating subtitle window.

Implementation notes for the "always on top" behaviour
======================================================

- We deliberately *do not* use ``Qt.WindowType.Tool``: on macOS that
  flag turns the window into a utility palette which gets demoted as
  soon as ParrotSub itself loses focus, so the overlay is no longer
  on top of e.g. a Safari window the user just clicked into.
- ``Qt.WidgetAttribute.WA_ShowWithoutActivating`` keeps the focus on
  whatever the user is doing in another app when the overlay first
  appears.
- On macOS we additionally try to bump the underlying ``NSWindow``
  level to ``NSStatusWindowLevel`` (25) via the ``pyobjc`` bindings.
  This is best-effort: if pyobjc is not installed the overlay still
  works thanks to ``Qt.WindowType.WindowStaysOnTopHint`` – it just
  won't sit on top of full-screen apps.
"""

from __future__ import annotations

import sys
from typing import Optional

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QMouseEvent, QShowEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QMainWindow,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from realtime_subtitle import app_config


class FloatingWindow(QMainWindow):
    """Frameless, transparent, always-on-top subtitle window.

    ``kind`` is either ``"original"`` or ``"translation"`` and decides which
    geometry from ``AppConfig`` we honour.
    """

    def __init__(
        self,
        cfg: app_config.AppConfig,
        kind: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._cfg = cfg
        self._kind = kind
        self._drag_offset: Optional[QPoint] = None

        screen = QApplication.primaryScreen().geometry()
        sw, sh = screen.width(), screen.height()

        if kind == "original":
            self.setWindowTitle("Original Floating Window")
            x_off = cfg.FloatingWindowXOffset
            y_off = cfg.FloatingWindowYOffset
        else:
            self.setWindowTitle("Translation Floating Window")
            x_off = cfg.TranslationFloatingWindowXOffset
            y_off = cfg.TranslationFloatingWindowYOffset

        self.setGeometry(
            int(x_off * sw),
            int(y_off * sh),
            int(cfg.FloatingWindowX * sw),
            int(cfg.FloatingWindowY * sh),
        )

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Do not steal focus from whatever the user is currently doing
        # in another app when the overlay appears.
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Container frame so we can apply rounded corners + subtle border.
        self._root = QFrame()
        self._root.setObjectName("FloatingRoot")
        layout = QVBoxLayout(self._root)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(0)

        self._text = QTextEdit(self._root)
        self._text.setReadOnly(True)
        self._text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._text.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._text.setFrameShape(QFrame.Shape.NoFrame)
        self._text.setStyleSheet(
            "QTextEdit {"
            "  background: transparent;"
            "  border: none;"
            f"  color: {cfg.FloatingWindowTextColor};"
            f"  font-size: {cfg.FloatingWindowFontSize}px;"
            "}"
        )
        layout.addWidget(self._text)

        self.setCentralWidget(self._root)

    # ------------------------------------------------------------------
    # Always-on-top guarantee
    # ------------------------------------------------------------------
    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802 - Qt signature
        super().showEvent(event)
        # Bring to front of the regular window stack first.
        self.raise_()
        # Then, on macOS, lift the underlying NSWindow above the menu bar
        # so it stays on top even when other apps take focus.
        self._bump_macos_window_level()

    def _bump_macos_window_level(self) -> None:
        """Best-effort: raise the NSWindow level on macOS via pyobjc.

        Skipped silently when:
        - we're not on macOS, or
        - the active Qt platform plugin isn't ``cocoa`` (e.g. ``offscreen``
          / ``minimal`` used by headless test runners – ``winId()`` would
          point at fake memory and AppKit calls would segfault), or
        - pyobjc is not installed.
        """
        if sys.platform != "darwin":
            return
        app = QApplication.instance()
        if app is None or app.platformName().lower() != "cocoa":
            return
        try:
            import objc  # type: ignore  # noqa: F401
            import AppKit  # type: ignore  # noqa: F401
        except Exception:
            return
        try:
            view_id = int(self.winId())
            if view_id == 0:
                return
            view = objc.objc_object(c_void_p=view_id)
            ns_window = view.window()
            if ns_window is None:
                return
            # NSStatusWindowLevel = 25 (above normal windows + menu bar).
            # Use the integer literal because the symbolic constant
            # location moved across pyobjc releases.
            ns_window.setLevel_(25)
        except Exception as exc:
            print(f"[parrotsub] could not bump NSWindow level: {exc}")

    # ------------------------------------------------------------------
    # Drag-to-move support (the window is frameless).
    # ------------------------------------------------------------------
    def mousePressEvent(self, ev: QMouseEvent) -> None:  # noqa: N802 - Qt signature
        if ev.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()
            ev.accept()

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:  # noqa: N802 - Qt signature
        if self._drag_offset is not None and ev.buttons() & Qt.MouseButton.LeftButton:
            self.move(ev.globalPosition().toPoint() - self._drag_offset)
            ev.accept()

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:  # noqa: N802 - Qt signature
        self._drag_offset = None
        ev.accept()

    # ------------------------------------------------------------------
    def update_content(self, text: str, line_length: int, line_count: int) -> None:
        if not text:
            self._text.clear()
            return

        cfg = self._cfg
        # Mirror the original wrapping logic: keep the last ``line_count`` lines.
        show_length = len(text) % line_length + (line_count - 1) * line_length
        show_text = text[-show_length:] if show_length > 0 else text
        wrapped = "<br>".join(
            show_text[i : i + line_length] for i in range(0, len(show_text), line_length)
        )

        edge = cfg.FloatingWindowTextEdgeColor
        html = (
            f'<div style="'
            f'color:{cfg.FloatingWindowTextColor};'
            f'font-size:{cfg.FloatingWindowFontSize}px;'
            f'text-shadow:'
            f' -2px -2px 0 {edge},'
            f'  2px -2px 0 {edge},'
            f' -2px  2px 0 {edge},'
            f'  2px  2px 0 {edge};'
            f'">{wrapped}</div>'
        )
        self._text.setHtml(html)
