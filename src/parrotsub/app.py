"""Main application shell: sidebar + header + page stack."""

from __future__ import annotations

import sys
import webbrowser
from typing import Optional, Tuple

from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from realtime_subtitle import app_config
from realtime_subtitle.subtitle import RealtimeSubtitle

from parrotsub import __version__, ui_config
from parrotsub.i18n import LOCALE_LABELS, detect_default_locale, t, translator
from parrotsub.languages import migrate_legacy_code
from parrotsub.models import (
    active_hf_endpoint,
    ensure_default_hf_endpoint,
    find_installed_model,
    is_model_installed,
)
from parrotsub.pages.exports import ExportsPage
from parrotsub.pages.home import HomePage
from parrotsub.pages.settings import SettingsPage
from parrotsub.theme import DARK, LIGHT, Palette, stylesheet
from parrotsub.widgets.header import Header
from parrotsub.widgets.sidebar import Sidebar


_NAV_ITEMS = [
    ("mic", "nav.tasks"),
    ("settings", "nav.settings"),
    ("download", "nav.exports"),
]

_GITHUB_URL = "https://github.com/21White/ParrotSub"


class MainWindow(QMainWindow):
    def __init__(
        self,
        rs: RealtimeSubtitle,
        cfg: app_config.AppConfig,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._rs = rs
        self._cfg = cfg

        # Load persisted UI prefs (theme + locale).  ``locale == ""`` means
        # "auto-detect" – we never persist the auto-detected value back unless
        # the user explicitly toggles, so that flipping the OS language later
        # still picks up the new default.
        self._ui = ui_config.get()
        if self._ui.locale and self._ui.locale in ("en", "zh"):
            translator().set_locale(self._ui.locale)
        else:
            translator().set_locale(detect_default_locale())

        self._theme: str = self._ui.theme if self._ui.theme in ("light", "dark") else "light"
        self._palette: Palette = LIGHT

        self.setWindowTitle("ParrotSub")
        self.resize(1240, 760)
        self.setMinimumSize(960, 600)

        # Root: horizontal layout with sidebar | (header on top, stack below)
        root = QWidget(self)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar(_NAV_ITEMS)
        self.sidebar.page_requested.connect(self._switch_page)
        self.sidebar.theme_toggled.connect(self._toggle_theme)
        self.sidebar.language_toggled.connect(self._toggle_language)
        self.sidebar.github_requested.connect(lambda: webbrowser.open(_GITHUB_URL))
        root_layout.addWidget(self.sidebar)

        right_col = QWidget(self)
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.header = Header(
            title="ParrotSub",
            version=f"v{__version__}",
        )
        right_layout.addWidget(self.header)

        self.stack = QStackedWidget()
        self.home_page = HomePage(rs=rs, cfg=cfg)
        self.settings_page = SettingsPage(
            rs=rs, cfg=cfg, on_saved=self._on_settings_saved
        )
        self.exports_page = ExportsPage(cfg=cfg)
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.exports_page)
        right_layout.addWidget(self.stack, stretch=1)

        root_layout.addWidget(right_col, stretch=1)
        self.setCentralWidget(root)

        # Plumb status changes from Home + Settings into the header pill.
        self.home_page.status_changed.connect(self.header.status.set_state)
        self.settings_page.status_changed.connect(self.header.status.set_state)

        # React to locale changes for header status text.
        translator().locale_changed.connect(self._on_locale_changed_header)

        # Default selection
        self.sidebar.set_active(0)
        self.stack.setCurrentIndex(0)

        self._apply_theme(self._theme)
        # Push the initial localised "Idle" text into the header pill.
        self.header.status.set_state("idle", t("status.idle"))

    # ------------------------------------------------------------------
    def _switch_page(self, index: int) -> None:
        self.sidebar.set_active(index)
        self.stack.setCurrentIndex(index)
        if index == 2:
            self.exports_page.refresh()

    def _toggle_theme(self) -> None:
        self._apply_theme("dark" if self._theme == "light" else "light")
        # Persist user choice.
        self._ui.theme = self._theme
        ui_config.save(self._ui)
        # Acknowledge in the status pill.
        label = "🌙 Dark" if self._theme == "dark" else "☀ Light"
        self.header.status.set_state("active", t("status.theme_set", label=label))

    def _toggle_language(self) -> None:
        translator().toggle()
        new_locale = translator().locale
        self._ui.locale = new_locale
        ui_config.save(self._ui)
        # The status pill text is updated by ``_on_locale_changed_header``.

    def _on_locale_changed_header(self, locale: str) -> None:
        label = LOCALE_LABELS.get(locale, locale)
        self.header.status.set_state("active", t("status.language_set", label=label))

    def _apply_theme(self, theme: str) -> None:
        self._theme = theme
        self._palette = DARK if theme == "dark" else LIGHT
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet(self._palette))
        # Refresh icons on widgets that need theme-aware repaint.
        self.sidebar.apply_palette(self._palette, self._theme)
        self.home_page.apply_palette(self._palette)
        self.settings_page.apply_palette(self._palette)
        self.exports_page.apply_palette(self._palette)

    def _on_settings_saved(self) -> None:
        self._cfg = app_config.get()
        self.home_page._cfg = self._cfg  # noqa: SLF001 – simple wiring
        self.home_page.refresh_from_config()
        self.exports_page._cfg = self._cfg  # noqa: SLF001
        self.exports_page.refresh()
        self.header.status.set_state("active", t("status.settings_saved"))

    # ------------------------------------------------------------------
    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt signature
        self.home_page.close_floating_windows()
        try:
            if self._rs.running:
                self._rs.stop()
        except Exception:
            pass
        event.accept()


def launch() -> int:
    """Boot a QApplication, build the backend & main window, and run the loop."""
    # Make sure model downloads default to the China mirror unless the
    # user has already exported HF_ENDPOINT (overrides win).
    endpoint = ensure_default_hf_endpoint()
    print(f"[parrotsub] HF_ENDPOINT = {endpoint}", flush=True)

    cfg = app_config.get()

    # Auto-migrate legacy / invalid language codes that may have been typed
    # into the old free-text inputs (e.g. ``cn`` -> ``zh``). Without this
    # the upstream backend used to crash with ``StopIteration`` because no
    # argos package matches an invalid code.
    migrated = []
    for attr in ("TranslateFrom", "TranslateTo"):
        old = getattr(cfg, attr, "")
        new = migrate_legacy_code(old)
        if new != old:
            setattr(cfg, attr, new)
            migrated.append(f"{attr}: {old!r} -> {new!r}")
    if migrated:
        print(
            "[parrotsub] migrated legacy language codes: "
            + ", ".join(migrated),
            flush=True,
        )
        try:
            app_config.save(cfg)
        except Exception as exc:
            print(f"[parrotsub] could not persist migrated config: {exc}", flush=True)

    # Pre-flight: if the configured Whisper model isn't downloaded yet
    # we MUST NOT let the backend's __init__ silently fall through to
    # huggingface_hub (which is what made v0.6.0 crash on launch for
    # users whose saved ModelName pointed at a model they hadn't pulled
    # yet). Instead, swap in any already-installed model just for this
    # process so the warm-up loads instantly from cache. The saved
    # config is left untouched so the Settings page still shows the
    # user's actual preference (with the ⬇ badge).
    selected_model = cfg.ModelName
    fallback_status: Optional[Tuple[str, str]] = None
    if not is_model_installed(selected_model):
        fallback = find_installed_model(cfg)
        if fallback and fallback != selected_model:
            print(
                f"[parrotsub] {selected_model!r} not downloaded yet; using "
                f"{fallback!r} for this session (your saved preference is "
                "preserved).",
                flush=True,
            )
            # Class attribute override – RealtimeSubtitle reads
            # ``self.model_name`` which defaults to this class attr.
            RealtimeSubtitle.model_name = fallback
            fallback_status = (
                "warn",
                t(
                    "status.model_fallback",
                    fallback=fallback.split("/")[-1],
                    selected=selected_model.split("/")[-1],
                ),
            )
        else:
            print(
                "[parrotsub] WARNING: no whisper model is downloaded yet. "
                "The UI will boot but transcription will fail until you open "
                "Settings → Whisper Model and click Download.",
                flush=True,
            )
            fallback_status = ("warn", t("status.no_model"))

    # The backend constructor downloads / loads heavy models; do it before the
    # event loop starts so the UI doesn't appear unresponsive. Wrapped so a
    # network hiccup or missing model can never take the whole app down –
    # the patched subtitle.py also tolerates a failed warm-up internally.
    print("[parrotsub] Loading whisper / translation / speaker models...", flush=True)
    rs = RealtimeSubtitle()
    print("[parrotsub] Models ready, starting UI.", flush=True)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("ParrotSub")
    app.setApplicationDisplayName("ParrotSub")
    app.setOrganizationName("parrotsub")

    window = MainWindow(rs=rs, cfg=cfg)
    window.show()
    if fallback_status is not None:
        window.header.status.set_state(*fallback_status)
    return app.exec()
