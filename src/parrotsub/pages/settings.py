"""Settings page – AppConfig surfaced as grouped cards."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
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
from parrotsub.widgets.switch import Switch


# Grouping of AppConfig fields into shadcn-style cards.
_FIELD_GROUPS: List[Tuple[str, str, List[str]]] = [
    (
        "Audio input",
        "Choose the microphone realtime-subtitle will sample.",
        ["InputDevice"],
    ),
    (
        "Whisper model",
        "Pick the speech-recognition model and tuning thresholds.",
        [
            "ModelName",
            "Latency",
            "NoSpeechThreshold",
            "LogprobThreshold",
            "TolerationOfLies",
            "ModelRefuseThreshold",
        ],
    ),
    (
        "Translation",
        "Translate the live transcript online or fully offline (argos).",
        [
            "EnableTranslation",
            "OnlineTranslation",
            "TranslateFrom",
            "TranslateTo",
            "TranslationPresantDelay",
        ],
    ),
    (
        "Subtitle layout",
        "Wrap & line-count for both transcript and translation panes.",
        [
            "SubtitleLength",
            "SubtitleHight",
            "TranslationSubtitleLength",
            "TranslationSubtitleHight",
        ],
    ),
    (
        "Floating window",
        "On-top, frameless overlay that mirrors the live subtitle stream.",
        [
            "FloatingWindowFontSize",
            "FloatingWindowTextColor",
            "FloatingWindowTextEdgeColor",
            "FloatingWindowBackgroundColor",
            "FloatingWindowX",
            "FloatingWindowY",
            "FloatingWindowXOffset",
            "FloatingWindowYOffset",
            "TranslationFloatingWindowXOffset",
            "TranslationFloatingWindowYOffset",
        ],
    ),
    (
        "Speaker recognition & storage",
        "Optional speaker clustering plus where exports are written.",
        ["EnableSpeakerRecognition", "DbscanEps", "SavePath"],
    ),
]

_HIDDEN_FIELDS = {"AllModelName"}


class SettingsPage(QWidget):
    """Configuration page – emits ``saved`` so other pages can refresh."""

    saved = pyqtSignal()

    def __init__(
        self,
        rs: RealtimeSubtitle,
        cfg: app_config.AppConfig,
        on_saved: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._rs = rs
        self._cfg = cfg
        if on_saved is not None:
            self.saved.connect(on_saved)

        self._field_widgets: Dict[str, QWidget] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)

        # Top action bar
        action_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_label = QLabel("Settings")
        title_label.setObjectName("CardTitle")
        title_label.setStyleSheet("font-size: 18px;")
        subtitle_label = QLabel(
            "Tweak the realtime pipeline. Changes are persisted to "
            "~/.config/glimmer/realtime-subtitle.config."
        )
        subtitle_label.setObjectName("CardDescription")
        subtitle_label.setWordWrap(True)
        title_col.addWidget(title_label)
        title_col.addWidget(subtitle_label)
        action_row.addLayout(title_col, stretch=1)

        self._reset_btn = QPushButton(" Reset to defaults")
        self._reset_btn.setProperty("variant", "outline")
        self._reset_btn.clicked.connect(self._reset_to_defaults)
        action_row.addWidget(self._reset_btn)

        self._save_btn = QPushButton(" Save changes")
        self._save_btn.clicked.connect(self._save)
        action_row.addWidget(self._save_btn)
        outer.addLayout(action_row)

        # Scrollable card column
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        host = QWidget()
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 4, 0)
        host_layout.setSpacing(16)

        for group_title, group_desc, field_names in _FIELD_GROUPS:
            host_layout.addWidget(
                self._build_group_card(group_title, group_desc, field_names)
            )

        host_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        scroll.setWidget(host)
        outer.addWidget(scroll, stretch=1)

    # ------------------------------------------------------------------
    def apply_palette(self, p: Palette) -> None:
        self._save_btn.setIcon(make_icon("save", color=p.primary_foreground, size=16))
        self._reset_btn.setIcon(make_icon("refresh-cw", color=p.foreground, size=16))

    # ------------------------------------------------------------------
    def _build_group_card(self, title: str, description: str, field_names: List[str]) -> Card:
        card = Card(title=title, description=description)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        annotations = self._cfg.__class__.__annotations__
        defaults = self._cfg.__dict__

        for name in field_names:
            if name in _HIDDEN_FIELDS or name not in defaults:
                continue
            widget = self._build_field_widget(name, annotations.get(name, type(defaults[name])))
            self._field_widgets[name] = widget
            label = QLabel(_humanize(name))
            label.setObjectName("FieldLabel")
            form.addRow(label, widget)

        card.body_layout.addLayout(form)
        return card

    def _build_field_widget(self, name: str, type_: type) -> QWidget:
        defaults = self._cfg.__dict__
        value = defaults[name]

        if name == "ModelName":
            combo = QComboBox()
            options = list(dict.fromkeys([self._cfg.ModelName, *self._cfg.AllModelName]))
            combo.addItems(options)
            combo.setCurrentText(self._cfg.ModelName)
            return combo

        if name == "InputDevice":
            combo = QComboBox()
            try:
                devices = self._rs.get_input_devices()
            except Exception:
                devices = []
            options = list(dict.fromkeys([str(self._cfg.InputDevice), "default", *devices]))
            combo.addItems(options)
            combo.setCurrentText(str(self._cfg.InputDevice))
            return combo

        if isinstance(value, bool) or type_ is bool:
            sw = Switch()
            sw.setChecked(bool(value))
            return sw

        line = QLineEdit(str(value))
        line.setProperty("field-type", type_.__name__ if isinstance(type_, type) else "str")
        return line

    # ------------------------------------------------------------------
    def _save(self) -> None:
        defaults = self._cfg.__dict__
        for name, widget in self._field_widgets.items():
            current_value = defaults.get(name)
            if isinstance(widget, QComboBox):
                new_value = widget.currentText()
            elif isinstance(widget, Switch):
                new_value = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                raw = widget.text()
                if isinstance(current_value, bool):
                    new_value = raw.strip().lower() in ("1", "true", "yes", "on")
                elif isinstance(current_value, int) and not isinstance(current_value, bool):
                    try:
                        new_value = int(raw)
                    except ValueError:
                        continue
                elif isinstance(current_value, float):
                    try:
                        new_value = float(raw)
                    except ValueError:
                        continue
                else:
                    new_value = raw
            else:
                continue
            defaults[name] = new_value

        app_config.save(self._cfg)
        self.saved.emit()

    def _reset_to_defaults(self) -> None:
        fresh = app_config.AppConfig()
        for name, widget in self._field_widgets.items():
            value = fresh.__dict__.get(name)
            if isinstance(widget, QComboBox):
                widget.setCurrentText(str(value))
            elif isinstance(widget, Switch):
                widget.setChecked(bool(value))
            elif isinstance(widget, QLineEdit):
                widget.setText(str(value))


def _humanize(name: str) -> str:
    """``EnableSpeakerRecognition`` -> ``Enable Speaker Recognition``."""
    out: List[str] = []
    for ch in name:
        if ch.isupper() and out:
            out.append(" ")
        out.append(ch)
    return "".join(out)
