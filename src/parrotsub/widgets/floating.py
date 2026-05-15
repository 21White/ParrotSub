"""Modern, frameless, translucent floating subtitle window."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QMouseEvent
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
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

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
