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

from parrotsub.i18n import t, translator
from parrotsub.icons import make_icon
from parrotsub.languages import LANGUAGE_NAMES
from parrotsub.theme import Palette
from parrotsub.widgets.card import Card
from parrotsub.widgets.floating import FloatingWindow
from parrotsub.widgets.subtitle_view import SubtitleView
from parrotsub.widgets.switch import Switch


_MODEL_ADD_THRESHOLD = 80
_MODEL_SUB_THRESHOLD = 3


class HomePage(QWidget):
    """The main, "Tasks" style page."""

    # Emits ``(state, key, kwargs_json_or_text)``.  Pages translate the
    # status text themselves so MainWindow can connect a generic slot.
    status_changed = pyqtSignal(str, str)

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

        self._actions_card = self._build_actions_card()
        outer.addWidget(self._actions_card)

        grid_host = QWidget(self)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(16)

        self._original_view = SubtitleView(placeholder=t("home.original.placeholder"))
        self._original_card = Card(
            title=t("home.original.title"),
            description=t("home.original.desc"),
        )
        self._original_card.body_layout.addWidget(self._original_view)

        self._translation_view = SubtitleView(
            placeholder=t("home.translation.placeholder")
        )
        self._translation_card = Card(
            title=t("home.translation.title"),
            description=self._translation_desc_text(),
        )
        self._translation_card.body_layout.addWidget(self._translation_view)

        grid.addWidget(self._original_card, 0, 0)
        grid.addWidget(self._translation_card, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 1)
        outer.addWidget(grid_host, stretch=1)

        self._floating_card = self._build_floating_card()
        outer.addWidget(self._floating_card)

        self.status_changed.connect(lambda *_: None)
        self._rs.set_update_hook(self._on_backend_update)

        translator().locale_changed.connect(self._retranslate)

    # ------------------------------------------------------------------
    # UI assembly
    # ------------------------------------------------------------------
    def _build_actions_card(self) -> Card:
        card = Card(
            title=t("home.tasks.title"),
            description=t("home.tasks.desc"),
        )

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        self._start_btn = QPushButton(t("home.action.start"))
        self._start_btn.setProperty("variant", "")  # primary
        self._start_btn.setMinimumHeight(36)
        self._start_btn.setIcon(make_icon("play", color="#ffffff", size=18))
        self._start_btn.clicked.connect(self._on_start_stop_clicked)
        row.addWidget(self._start_btn)

        self._export_btn = QPushButton(t("home.action.export"))
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
            title=t("home.floating.title"),
            description=t("home.floating.desc"),
        )

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(20)

        self._float_original_switch = Switch(t("home.floating.original"))
        self._float_original_switch.toggled.connect(self._toggle_original_floating)
        row.addWidget(self._float_original_switch)

        self._float_translation_switch = Switch(t("home.floating.translation"))
        self._float_translation_switch.toggled.connect(self._toggle_translation_floating)
        row.addWidget(self._float_translation_switch)

        row.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self._floating_hint = QLabel(t("home.floating.tip"))
        self._floating_hint.setObjectName("FieldHint")
        row.addWidget(self._floating_hint)

        card.body_layout.addLayout(row)
        return card

    # ------------------------------------------------------------------
    # i18n
    # ------------------------------------------------------------------
    def _translation_desc_text(self) -> str:
        src_code = self._cfg.TranslateFrom
        tgt_code = self._cfg.TranslateTo
        return t(
            "home.translation.desc",
            src=LANGUAGE_NAMES.get(src_code, src_code),
            tgt=LANGUAGE_NAMES.get(tgt_code, tgt_code),
        )

    def _device_label_text(self) -> str:
        device = self._cfg.InputDevice or "default"
        model = self._cfg.ModelName.split("/")[-1]
        return t("home.device_label", device=device, model=model)

    def _retranslate(self, _locale: str) -> None:
        # Action card
        self._actions_card.title_label.setText(t("home.tasks.title"))
        self._actions_card.description_label.setText(t("home.tasks.desc"))
        self._device_label.setText(self._device_label_text())
        self._start_btn.setText(
            t("home.action.stop") if self._rs.running else t("home.action.start")
        )
        self._export_btn.setText(t("home.action.export"))

        # Subtitle cards
        self._original_card.title_label.setText(t("home.original.title"))
        self._original_card.description_label.setText(t("home.original.desc"))
        self._original_view.setPlaceholderText(t("home.original.placeholder"))

        self._translation_card.title_label.setText(t("home.translation.title"))
        self._translation_card.description_label.setText(self._translation_desc_text())
        self._translation_view.setPlaceholderText(t("home.translation.placeholder"))

        # Floating card
        self._floating_card.title_label.setText(t("home.floating.title"))
        self._floating_card.description_label.setText(t("home.floating.desc"))
        self._float_original_switch.setText(t("home.floating.original"))
        self._float_translation_switch.setText(t("home.floating.translation"))
        self._floating_hint.setText(t("home.floating.tip"))

    # ------------------------------------------------------------------
    def refresh_from_config(self) -> None:
        """Re-read the cached config (call after Settings page saves)."""
        from realtime_subtitle import app_config as _ac

        self._cfg = _ac.get()
        self._device_label.setText(self._device_label_text())
        self._translation_card.description_label.setText(self._translation_desc_text())

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
            self._start_btn.setText(t("home.action.start"))
            self.status_changed.emit("idle", t("status.idle"))
        else:
            self._rs.start()
            self._start_btn.setText(t("home.action.stop"))
            self.status_changed.emit("active", t("status.recording"))
        self._refresh_action_icons()

    def _on_export_clicked(self) -> None:
        if self._rs.running:
            self._rs.stop()
            self._start_btn.setText(t("home.action.start"))
            self._refresh_action_icons()
        self.status_changed.emit("warn", t("status.exporting"))
        try:
            self._rs.export()
            self.status_changed.emit("active", t("status.exported"))
        except Exception as exc:  # surfaced in the status pill
            self.status_changed.emit("warn", t("status.export_failed", error=str(exc)))

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

        self._dispatch_update(all_text, all_translation)

    def _dispatch_update(self, original: str, translation: str) -> None:
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
