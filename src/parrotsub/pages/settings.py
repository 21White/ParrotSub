"""Settings page – AppConfig surfaced as grouped, translatable cards."""

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

from parrotsub.i18n import t, translator
from parrotsub.icons import make_icon
from parrotsub.languages import (
    is_english_only_model,
    label as language_label,
    source_language_options,
    target_language_options,
)
from parrotsub.models import (
    ModelDownloadWorker,
    active_hf_endpoint,
    cleanup_incomplete_downloads,
    is_model_installed,
    model_size_label,
)
from parrotsub.theme import Palette
from parrotsub.widgets.card import Card
from parrotsub.widgets.switch import Switch


# (title_key, desc_key, [field_names])
_FIELD_GROUPS: List[Tuple[str, str, List[str]]] = [
    (
        "settings.group.audio.title",
        "settings.group.audio.desc",
        ["InputDevice"],
    ),
    (
        "settings.group.model.title",
        "settings.group.model.desc",
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
        "settings.group.translation.title",
        "settings.group.translation.desc",
        [
            "EnableTranslation",
            "TranslateFrom",
            "TranslateTo",
            "TranslationPresantDelay",
        ],
    ),
    (
        "settings.group.subtitle.title",
        "settings.group.subtitle.desc",
        [
            "SubtitleLength",
            "SubtitleHight",
            "TranslationSubtitleLength",
            "TranslationSubtitleHight",
        ],
    ),
    (
        "settings.group.floating.title",
        "settings.group.floating.desc",
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
        "settings.group.speaker.title",
        "settings.group.speaker.desc",
        ["EnableSpeakerRecognition", "DbscanEps", "SavePath"],
    ),
]

_HIDDEN_FIELDS = {
    "AllModelName",
    # Online translation is parked until a future release; keep the
    # backend field but never expose it in the UI and force-write False
    # on every save so the offline argos pipeline always wins.
    "OnlineTranslation",
}


class SettingsPage(QWidget):
    """Configuration page – emits ``saved`` so other pages can refresh.

    Also emits ``status_changed(state, text)`` so the host MainWindow can
    surface model-download progress / completion in the header pill.
    """

    saved = pyqtSignal()
    status_changed = pyqtSignal(str, str)  # state, text – mirrors HomePage

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
        self._field_labels: Dict[str, QLabel] = {}
        self._group_cards: List[Tuple[Card, str, str]] = []  # (card, title_key, desc_key)
        # Model download state
        self._model_download_btn: Optional[QPushButton] = None
        self._model_endpoint_label: Optional[QLabel] = None
        self._model_download_thread: Optional[ModelDownloadWorker] = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)

        # Top action bar
        action_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self._title_label = QLabel(t("settings.title"))
        self._title_label.setObjectName("CardTitle")
        self._title_label.setStyleSheet("font-size: 18px;")
        self._subtitle_label = QLabel(t("settings.subtitle"))
        self._subtitle_label.setObjectName("CardDescription")
        self._subtitle_label.setWordWrap(True)
        title_col.addWidget(self._title_label)
        title_col.addWidget(self._subtitle_label)
        action_row.addLayout(title_col, stretch=1)

        self._reset_btn = QPushButton(t("settings.action.reset"))
        self._reset_btn.setProperty("variant", "outline")
        self._reset_btn.clicked.connect(self._reset_to_defaults)
        action_row.addWidget(self._reset_btn)

        self._save_btn = QPushButton(t("settings.action.save"))
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

        for title_key, desc_key, field_names in _FIELD_GROUPS:
            card = self._build_group_card(title_key, desc_key, field_names)
            host_layout.addWidget(card)

        host_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        scroll.setWidget(host)
        outer.addWidget(scroll, stretch=1)

        translator().locale_changed.connect(self._retranslate)

    # ------------------------------------------------------------------
    def apply_palette(self, p: Palette) -> None:
        self._save_btn.setIcon(make_icon("save", color=p.primary_foreground, size=16))
        self._reset_btn.setIcon(make_icon("refresh-cw", color=p.foreground, size=16))
        if self._model_download_btn is not None:
            self._model_download_btn.setIcon(
                make_icon("cloud-download", color=p.foreground, size=16)
            )

    # ------------------------------------------------------------------
    def _build_group_card(self, title_key: str, desc_key: str, field_names: List[str]) -> Card:
        card = Card(title=t(title_key), description=t(desc_key))
        self._group_cards.append((card, title_key, desc_key))

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
            label = QLabel(self._field_label_text(name))
            label.setObjectName("FieldLabel")
            self._field_labels[name] = label
            form.addRow(label, self._wrap_field_widget(name, widget))

        card.body_layout.addLayout(form)
        return card

    def _wrap_field_widget(self, name: str, widget: QWidget) -> QWidget:
        """Optionally wrap ``widget`` in a horizontal container.

        Used by the ModelName row so the combo box gets an inline
        Download button (and a small endpoint hint label below).
        """
        if name == "ModelName" and isinstance(widget, QComboBox):
            return self._build_model_row(widget)
        return widget

    def _build_field_widget(self, name: str, type_: type) -> QWidget:
        defaults = self._cfg.__dict__
        value = defaults[name]

        if name == "ModelName":
            combo = QComboBox()
            combo.setObjectName("ModelCombo")
            self._populate_model_combo(combo, self._cfg.ModelName)
            # Cascade: when the user picks a different whisper model,
            # refresh the TranslateFrom dropdown (English-only models
            # lock it to "en") AND refresh the Download button state.
            combo.currentIndexChanged.connect(self._on_model_combo_index_changed)
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

        if name == "TranslateFrom":
            combo = QComboBox()
            self._populate_language_combo(
                combo,
                source_language_options(self._cfg.ModelName),
                str(value),
            )
            return combo

        if name == "TranslateTo":
            combo = QComboBox()
            self._populate_language_combo(combo, target_language_options(), str(value))
            return combo

        if isinstance(value, bool) or type_ is bool:
            sw = Switch()
            sw.setChecked(bool(value))
            return sw

        line = QLineEdit(str(value))
        line.setProperty("field-type", type_.__name__ if isinstance(type_, type) else "str")
        return line

    # ------------------------------------------------------------------
    # Language combo helpers
    # ------------------------------------------------------------------
    def _populate_language_combo(
        self,
        combo: "QComboBox",
        options: List[Tuple[str, str]],
        current_code: str,
    ) -> None:
        """Fill ``combo`` with ``(code, label)`` items, selecting ``current_code``.

        Always preserves the currently saved code even if it is not in
        ``options`` (so legacy/manual values stay visible to the user).
        """
        codes_in_options = {code for code, _ in options}
        items: List[Tuple[str, str]] = list(options)
        if current_code and current_code not in codes_in_options:
            items.insert(0, (current_code, language_label(current_code)))

        combo.blockSignals(True)
        combo.clear()
        for code, lbl in items:
            combo.addItem(lbl, userData=code)
        # Select the row whose userData matches the saved code.
        for i in range(combo.count()):
            if combo.itemData(i) == current_code:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)

    def _on_model_changed(self, new_model: str) -> None:
        """Re-build the TranslateFrom combo when the whisper model changes."""
        combo = self._field_widgets.get("TranslateFrom")
        if combo is None or not isinstance(combo, QComboBox):
            return
        current_code = combo.currentData() or ""
        new_options = source_language_options(new_model)
        # If the active source no longer fits (e.g. switching to a .en model
        # while "zh" is selected), default to "en".
        if is_english_only_model(new_model):
            current_code = "en"
        self._populate_language_combo(combo, new_options, current_code)

    # ------------------------------------------------------------------
    # Model picker helpers
    # ------------------------------------------------------------------
    def _populate_model_combo(self, combo: "QComboBox", current_repo: str) -> None:
        """Fill the model combo with status-prefixed labels.

        Each item shows ``"✓ name (size)"`` if the model is already in the
        HuggingFace cache, or ``"⬇ name (size)"`` if it still needs to be
        downloaded. The raw ``repo_id`` is stored in ``userData`` so
        ``save()`` and ``_on_model_changed`` can recover it unchanged.
        """
        repos = list(dict.fromkeys([current_repo, *self._cfg.AllModelName]))
        combo.blockSignals(True)
        combo.clear()
        for repo in repos:
            installed = is_model_installed(repo)
            badge = "✓" if installed else "⬇"
            size = model_size_label(repo)
            suffix = f"  ({size})" if size else ""
            combo.addItem(f"{badge}  {repo}{suffix}", userData=repo)
        # Re-select the saved repo (by userData).
        for i in range(combo.count()):
            if combo.itemData(i) == current_repo:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)

    def _build_model_row(self, combo: "QComboBox") -> QWidget:
        """Return a horizontal container: ``[combo] [Download]`` + endpoint hint."""
        container = QWidget()
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(combo, stretch=1)

        download_btn = QPushButton(t("settings.model.download"))
        download_btn.setProperty("variant", "outline")
        download_btn.setToolTip(t("settings.model.download.tooltip"))
        download_btn.clicked.connect(self._on_download_model_clicked)
        self._model_download_btn = download_btn
        row.addWidget(download_btn)
        outer.addLayout(row)

        hint = QLabel(t("settings.model.endpoint", endpoint=active_hf_endpoint()))
        hint.setObjectName("FieldHint")
        hint.setWordWrap(True)
        self._model_endpoint_label = hint
        outer.addWidget(hint)

        self._update_download_btn_state()
        return container

    def _current_model_repo(self) -> str:
        combo = self._field_widgets.get("ModelName")
        if isinstance(combo, QComboBox):
            data = combo.currentData()
            if data:
                return str(data)
        return self._cfg.ModelName

    def _update_download_btn_state(self) -> None:
        btn = self._model_download_btn
        if btn is None:
            return
        # Disabled while a download is in flight.
        if self._model_download_thread is not None and self._model_download_thread.isRunning():
            btn.setEnabled(False)
            btn.setText(t("settings.model.downloading"))
            return
        repo = self._current_model_repo()
        if is_model_installed(repo):
            btn.setEnabled(False)
            btn.setText(t("settings.model.installed"))
        else:
            btn.setEnabled(True)
            btn.setText(t("settings.model.download"))

    def _on_model_combo_index_changed(self, _index: int) -> None:
        """Currently-selected model changed. Update dependent UI."""
        # Read the raw repo id (not the prefixed label) and fan out.
        repo = self._current_model_repo()
        self._on_model_changed(repo)
        self._update_download_btn_state()

    # ------------------------------------------------------------------
    # Download flow
    # ------------------------------------------------------------------
    def _on_download_model_clicked(self) -> None:
        if self._model_download_thread is not None and self._model_download_thread.isRunning():
            return  # already downloading
        repo = self._current_model_repo()
        if is_model_installed(repo):
            self.status_changed.emit("active", t("settings.model.already_installed", model=repo))
            self._update_download_btn_state()
            return

        # Wipe any half-finished blobs from previous attempts so the
        # next download starts clean. (Without this, a stalled prior
        # transfer can confuse resume logic.)
        cleanup_incomplete_downloads(repo)

        worker = ModelDownloadWorker(repo, parent=self)
        worker.attempting.connect(self._on_model_download_attempting)
        worker.progress.connect(self._on_model_download_progress)
        worker.downloaded.connect(self._on_model_downloaded)
        # When the thread itself finishes, drop our reference so the GC
        # can clean up; also re-evaluate the button state.
        worker.finished.connect(self._on_download_thread_finished)
        self._model_download_thread = worker
        worker.start()
        self.status_changed.emit("warn", t("settings.model.downloading_status", model=repo))
        self._update_download_btn_state()

    def _on_model_download_attempting(self, repo_id: str, endpoint: str) -> None:
        """Show which mirror is currently being tried in the status pill."""
        from urllib.parse import urlparse
        host = urlparse(endpoint).netloc or endpoint
        self.status_changed.emit(
            "warn",
            t("settings.model.downloading_via", model=repo_id, endpoint=host),
        )

    def _on_model_download_progress(self, repo_id: str, done: int, total: int) -> None:
        """Live percentage in the header status pill, throttled by the worker."""
        if total <= 0:
            return
        pct = max(0, min(100, int(done * 100 / total)))
        done_mb = done / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        self.status_changed.emit(
            "warn",
            t(
                "settings.model.download_progress",
                model=repo_id.split("/")[-1],
                pct=pct,
                done=done_mb,
                total=total_mb,
            ),
        )

    def _on_model_downloaded(self, repo_id: str, success: bool, message: str) -> None:
        if success:
            self.status_changed.emit("active", t("settings.model.download_ok", model=repo_id))
        else:
            self.status_changed.emit("warn", t("settings.model.download_failed", error=message))
        # Refresh the combo so the badge flips from ⬇ to ✓.
        combo = self._field_widgets.get("ModelName")
        if isinstance(combo, QComboBox):
            self._populate_model_combo(combo, self._current_model_repo())

    def _on_download_thread_finished(self) -> None:
        self._model_download_thread = None
        self._update_download_btn_state()

    # ------------------------------------------------------------------
    def _field_label_text(self, name: str) -> str:
        key = f"field.{name}"
        translated = t(key)
        if translated == key:  # no translation found, fall back to humanised name
            return _humanize(name)
        return translated

    def _retranslate(self, _locale: str) -> None:
        self._title_label.setText(t("settings.title"))
        self._subtitle_label.setText(t("settings.subtitle"))
        self._save_btn.setText(t("settings.action.save"))
        self._reset_btn.setText(t("settings.action.reset"))
        for card, title_key, desc_key in self._group_cards:
            card.title_label.setText(t(title_key))
            card.description_label.setText(t(desc_key))
        for name, label in self._field_labels.items():
            label.setText(self._field_label_text(name))
        # Model picker bits
        if self._model_download_btn is not None:
            self._update_download_btn_state()
            self._model_download_btn.setToolTip(t("settings.model.download.tooltip"))
        if self._model_endpoint_label is not None:
            self._model_endpoint_label.setText(
                t("settings.model.endpoint", endpoint=active_hf_endpoint())
            )

    # ------------------------------------------------------------------
    def _save(self) -> None:
        defaults = self._cfg.__dict__
        for name, widget in self._field_widgets.items():
            current_value = defaults.get(name)
            if isinstance(widget, QComboBox):
                # For our language pickers we stored the code in userData;
                # for the model / device combos there is no userData so
                # fall back to the visible text.
                data = widget.currentData()
                new_value = data if data is not None else widget.currentText()
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

        # Online translation is parked for a future release. Force it off
        # on every save so toggling it via direct config edits doesn't
        # silently re-enable it from the UI's perspective.
        defaults["OnlineTranslation"] = False

        app_config.save(self._cfg)
        self.saved.emit()

    def _reset_to_defaults(self) -> None:
        fresh = app_config.AppConfig()
        for name, widget in self._field_widgets.items():
            value = fresh.__dict__.get(name)
            if name == "TranslateFrom" and isinstance(widget, QComboBox):
                self._populate_language_combo(
                    widget,
                    source_language_options(self._cfg.ModelName),
                    str(value),
                )
            elif name == "TranslateTo" and isinstance(widget, QComboBox):
                self._populate_language_combo(widget, target_language_options(), str(value))
            elif isinstance(widget, QComboBox):
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
