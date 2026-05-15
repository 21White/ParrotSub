"""Home page – live transcription with original / translation cards."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QMetaObject, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from realtime_subtitle import app_config
from realtime_subtitle.subtitle import RealtimeSubtitle

from parrotsub.icons import make_icon
from parrotsub.theme import Palette
from parrotsub.widgets.card import Card
from parrotsub.widgets.floating import FloatingWindow
from parrotsub.widgets.subtitle_view import SubtitleView
from parrotsub.widgets.switch import Switch


_MODEL_ADD_THRESHOLD = 80
_MODEL_SUB_THRESHOLD = 3


class HomePage(QWidget):
    """The main, "Tasks" style page."""

    status_changed = pyqtSignal(str, str)  # state, text

    def __init__(
        self,
        rs: RealtimeSubtitle,
        cfg: app_config.AppConfig,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._rs = rs
        self._cfg = cfg
        self._last_all_text_length = 0
        self._model_thrashing_count = 0

        self._floating_original: Optional[FloatingWindow] = None
        self._floating_translation: Optional[FloatingWindow] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)

        outer.addWidget(self._build_actions_card())

        grid_host = QWidget(self)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(16)

        self._original_view = SubtitleView(
            placeholder="Speak into your microphone, recognised text will appear here."
        )
        original_card = Card(
            title="Original",
            description="Live whisper transcription from your selected input device.",
        )
        original_card.body_layout.addWidget(self._original_view)

        self._translation_view = SubtitleView(
            placeholder="Translated text will stream here when translation is enabled."
        )
        translation_card = Card(
            title="Translation",
            description=f"{cfg.TranslateFrom} → {cfg.TranslateTo} (offline argos / online).",
        )
        translation_card.body_layout.addWidget(self._translation_view)

        grid.addWidget(original_card, 0, 0)
        grid.addWidget(translation_card, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 1)
        outer.addWidget(grid_host, stretch=1)

        outer.addWidget(self._build_floating_card())

        # Hook the backend update callback into the Qt event loop via a signal.
        self.status_changed.connect(lambda *_: None)
        self._rs.set_update_hook(self._on_backend_update)

    # ------------------------------------------------------------------
    # UI assembly
    # ------------------------------------------------------------------
    def _build_actions_card(self) -> Card:
        card = Card(
            title="Tasks",
            description="Start the realtime pipeline, or export the current session.",
        )

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        self._start_btn = QPushButton(" Start recording")
        self._start_btn.setProperty("variant", "")  # primary
        self._start_btn.setMinimumHeight(36)
        # Initial icon — re-coloured by ``apply_palette``.
        self._start_btn.setIcon(make_icon("play", color="#ffffff", size=18))
        self._start_btn.clicked.connect(self._on_start_stop_clicked)
        row.addWidget(self._start_btn)

        self._export_btn = QPushButton(" Export session")
        self._export_btn.setProperty("variant", "secondary")
        self._export_btn.setMinimumHeight(36)
        self._export_btn.clicked.connect(self._on_export_clicked)
        row.addWidget(self._export_btn)

        row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self._device_label = QLabel(self._device_label_text())
        self._device_label.setObjectName("FieldHint")
        row.addWidget(self._device_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        card.body_layout.addLayout(row)
        return card

    def _build_floating_card(self) -> Card:
        card = Card(
            title="Floating windows",
            description="Project the live subtitles on top of every other app.",
        )

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(20)

        self._float_original_switch = Switch("Original subtitles overlay")
        self._float_original_switch.toggled.connect(self._toggle_original_floating)
        row.addWidget(self._float_original_switch)

        self._float_translation_switch = Switch("Translation overlay")
        self._float_translation_switch.toggled.connect(self._toggle_translation_floating)
        row.addWidget(self._float_translation_switch)

        row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        hint = QLabel("Tip: drag the overlay window with your mouse to reposition.")
        hint.setObjectName("FieldHint")
        row.addWidget(hint)

        card.body_layout.addLayout(row)
        return card

    # ------------------------------------------------------------------
    # Behaviour
    # ------------------------------------------------------------------
    def _device_label_text(self) -> str:
        device = self._cfg.InputDevice or "default"
        model = self._cfg.ModelName.split("/")[-1]
        return f"Input: {device}    ·    Model: {model}"

    def refresh_from_config(self) -> None:
        """Re-read the cached config (call after Settings page saves)."""
        from realtime_subtitle import app_config as _ac

        self._cfg = _ac.get()
        self._device_label.setText(self._device_label_text())

    def apply_palette(self, p: Palette) -> None:
        self._palette = p
        self._refresh_action_icons()

    def _refresh_action_icons(self) -> None:
        p = getattr(self, "_palette", None)
        if p is None:
            return
        running = self._rs.running
        self._start_btn.setIcon(
            make_icon("square" if running else "play", color=p.primary_foreground, size=18)
        )
        self._export_btn.setIcon(make_icon("save", color=p.foreground, size=18))

    # ------------------------------------------------------------------
    def _on_start_stop_clicked(self) -> None:
        if self._rs.running:
            self._rs.stop()
            self._start_btn.setText(" Start recording")
            self.status_changed.emit("idle", "Idle")
        else:
            self._rs.start()
            self._start_btn.setText(" Stop recording")
            self.status_changed.emit("active", "Recording")
        self._refresh_action_icons()

    def _on_export_clicked(self) -> None:
        if self._rs.running:
            self._rs.stop()
            self._start_btn.setText(" Start recording")
            self._refresh_action_icons()
        self.status_changed.emit("warn", "Exporting…")
        try:
            self._rs.export()
            self.status_changed.emit("active", "Exported")
        except Exception as exc:  # surfaced in the status pill
            self.status_changed.emit("warn", f"Export failed: {exc}")

    # ------------------------------------------------------------------
    def _toggle_original_floating(self, checked: bool) -> None:
        if checked:
            self._floating_original = FloatingWindow(self._cfg, "original")
            self._floating_original.show()
        elif self._floating_original is not None:
            self._floating_original.close()
            self._floating_original = None

    def _toggle_translation_floating(self, checked: bool) -> None:
        if checked:
            self._floating_translation = FloatingWindow(self._cfg, "translation")
            self._floating_translation.show()
        elif self._floating_translation is not None:
            self._floating_translation.close()
            self._floating_translation = None

    def close_floating_windows(self) -> None:
        for win_attr in ("_floating_original", "_floating_translation"):
            win = getattr(self, win_attr)
            if win is not None:
                win.close()
                setattr(self, win_attr, None)

    # ------------------------------------------------------------------
    def _on_backend_update(self) -> None:
        """Backend thread callback. Re-emit through the event loop."""
        try:
            archived_text = "".join(d.text for d in self._rs.archived_data)
            temp_text = "".join(d.text for d in self._rs.temp_data)
            archived_translation = "".join(d.translated_text for d in self._rs.archived_data)
            delay = self._cfg.TranslationPresantDelay
            temp_slice = self._rs.temp_data[: max(0, len(self._rs.temp_data) - delay)]
            temp_translation = "".join(d.translated_text for d in temp_slice)

            all_text = archived_text + temp_text
            all_translation = archived_translation + temp_translation

            if (
                len(all_text) > self._last_all_text_length + _MODEL_ADD_THRESHOLD
                or len(all_text) < self._last_all_text_length - _MODEL_SUB_THRESHOLD
            ):
                self._model_thrashing_count += 1
                if self._model_thrashing_count < self._cfg.ModelRefuseThreshold:
                    return
                self._model_thrashing_count = 0

            self._last_all_text_length = len(all_text)
        except Exception as exc:
            print(f"[home] update hook error: {exc}")
            return

        # Hop to the GUI thread by way of a Qt-safe signal.
        self._dispatch_update(all_text, all_translation)

    def _dispatch_update(self, original: str, translation: str) -> None:
        # The hook may be called from a backend worker thread; defer to the GUI thread.
        self._pending_original = original
        self._pending_translation = translation
        QMetaObject.invokeMethod(
            self, "_apply_update", Qt.ConnectionType.QueuedConnection
        )

    @pyqtSlot()
    def _apply_update(self) -> None:
        original = getattr(self, "_pending_original", "")
        translation = getattr(self, "_pending_translation", "")
        self._original_view.set_text(original)
        self._translation_view.set_text(translation)

        if self._floating_original is not None:
            self._floating_original.update_content(
                original, self._cfg.SubtitleLength, self._cfg.SubtitleHight
            )
        if self._floating_translation is not None:
            self._floating_translation.update_content(
                translation,
                self._cfg.TranslationSubtitleLength,
                self._cfg.TranslationSubtitleHight,
            )
