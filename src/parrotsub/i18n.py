"""Lightweight English/Chinese i18n layer for the ParrotSub UI.

The module exposes a single ``Translator`` instance (see ``translator``)
that emits ``locale_changed`` whenever the active locale flips, plus a
short ``t(key, **kwargs)`` helper that looks the key up in the current
locale, falls back to English, and finally returns the key itself if no
translation exists.
"""

from __future__ import annotations

import locale as _stdlocale
from typing import Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal


SUPPORTED_LOCALES = ("en", "zh")
LOCALE_LABELS = {"en": "English", "zh": "中文"}


# ---------------------------------------------------------------------------
# Message catalogue
# ---------------------------------------------------------------------------
_MESSAGES: Dict[str, Dict[str, str]] = {
    "en": {
        # Navigation / sidebar
        "nav.tasks": "Tasks",
        "nav.settings": "Settings",
        "nav.exports": "Exports",
        "nav.theme.toggle": "Toggle theme",
        "nav.language.toggle": "Switch language (中文 / English)",
        "nav.github": "Open ParrotSub on GitHub",
        "brand.tooltip": "ParrotSub",

        # Header / status pill
        "status.idle": "Idle",
        "status.recording": "Recording",
        "status.exporting": "Exporting…",
        "status.exported": "Exported",
        "status.export_failed": "Export failed: {error}",
        "status.settings_saved": "Settings saved",
        "status.language_set": "Language: {label}",
        "status.theme_set": "Theme: {label}",
        "status.cleared": "History cleared",
        "status.model_fallback": "Using {fallback}",
        "status.no_model": "No whisper model downloaded",

        # Home page
        "home.tasks.title": "Tasks",
        "home.tasks.desc": "Start the realtime pipeline, or export the current session.",
        "home.original.title": "Original",
        "home.original.desc": "Live whisper transcription from your selected input device.",
        "home.original.placeholder": "Speak into your microphone, recognised text will appear here.",
        "home.translation.title": "Translation",
        "home.translation.desc": "{src} → {tgt} · offline (argos-translate)",
        "home.translation.placeholder": "Translated text will stream here when translation is enabled.",
        "home.action.start": " Start recording",
        "home.action.stop": " Stop recording",
        "home.action.export": " Export session",
        "home.action.clear": " Clear history",
        "home.action.clear.tooltip": (
            "Stop the current pipeline (if running) and wipe the in-memory "
            "audio buffer + every recognised subtitle so far."
        ),
        "home.device_label": "Input: {device}    ·    Model: {model}",
        "home.floating.title": "Floating windows",
        "home.floating.desc": "Project the live subtitles on top of every other app.",
        "home.floating.original": "Original subtitles overlay",
        "home.floating.translation": "Translation overlay",
        "home.floating.tip": "Tip: drag the overlay window with your mouse to reposition.",

        # Settings page
        "settings.title": "Settings",
        "settings.subtitle": (
            "Tweak the realtime pipeline. Changes are persisted to "
            "~/.config/glimmer/realtime-subtitle.config."
        ),
        "settings.action.save": " Save changes",
        "settings.action.reset": " Reset to defaults",
        "settings.group.audio.title": "Audio input",
        "settings.group.audio.desc": "Choose the microphone realtime-subtitle will sample.",
        "settings.group.model.title": "Whisper model",
        "settings.group.model.desc": "Pick the speech-recognition model and tuning thresholds.",
        "settings.model.download": " Download",
        "settings.model.downloading": " Downloading…",
        "settings.model.installed": " Installed",
        "settings.model.download.tooltip": (
            "Download the currently selected Whisper model from HuggingFace. "
            "Uses the HF_ENDPOINT env var, defaulting to the China mirror "
            "(hf-mirror.com)."
        ),
        "settings.model.endpoint": "Mirror: {endpoint}",
        "settings.model.downloading_status": "Downloading {model}…",
        "settings.model.downloading_via": "Downloading {model} via {endpoint}…",
        "settings.model.download_progress": "Downloading {model}: {pct}% ({done:.0f}/{total:.0f} MB · {speed} · ETA {eta})",
        "settings.model.download_ok": "Model downloaded: {model}",
        "settings.model.download_failed": "Model download failed: {error}",
        "settings.model.already_installed": "Already installed: {model}",
        "settings.group.translation.title": "Translation",
        "settings.group.translation.desc": (
            "Translate the live transcript fully offline with "
            "argos-translate. Pick the spoken (source) language and "
            "the language to translate into. Online translation is "
            "planned for a future release."
        ),
        "settings.group.subtitle.title": "Subtitle layout",
        "settings.group.subtitle.desc": "Wrap & line-count for both transcript and translation panes.",
        "settings.group.floating.title": "Floating window",
        "settings.group.floating.desc": "On-top, frameless overlay that mirrors the live subtitle stream.",
        "settings.group.speaker.title": "Speaker recognition & storage",
        "settings.group.speaker.desc": "Optional speaker clustering plus where exports are written.",

        # Field labels (Settings page)
        "field.InputDevice": "Input device",
        "field.ModelName": "Whisper model",
        "field.Latency": "Process latency (s)",
        "field.NoSpeechThreshold": "No-speech threshold",
        "field.LogprobThreshold": "Log-prob threshold",
        "field.TolerationOfLies": "Hallucination tolerance (s)",
        "field.ModelRefuseThreshold": "Model refuse threshold",
        "field.EnableTranslation": "Enable translation",
        "field.OnlineTranslation": "Use online translation",
        "field.TranslateFrom": "Source language code",
        "field.TranslateTo": "Target language code",
        "field.TranslationPresantDelay": "Translation present delay",
        "field.SubtitleLength": "Subtitle line length",
        "field.SubtitleHight": "Subtitle line count",
        "field.TranslationSubtitleLength": "Translation line length",
        "field.TranslationSubtitleHight": "Translation line count",
        "field.FloatingWindowFontSize": "Floating font size (px)",
        "field.FloatingWindowTextColor": "Text colour",
        "field.FloatingWindowTextEdgeColor": "Text edge colour",
        "field.FloatingWindowBackgroundColor": "Background colour",
        "field.FloatingWindowX": "Width (% of screen)",
        "field.FloatingWindowY": "Height (% of screen)",
        "field.FloatingWindowXOffset": "X offset (% of screen)",
        "field.FloatingWindowYOffset": "Y offset (% of screen)",
        "field.TranslationFloatingWindowXOffset": "Translation X offset",
        "field.TranslationFloatingWindowYOffset": "Translation Y offset",
        "field.EnableSpeakerRecognition": "Enable speaker clustering",
        "field.DbscanEps": "DBSCAN epsilon",
        "field.SavePath": "Save path",

        # Exports page
        "exports.title": "Exports",
        "exports.subtitle": "Sessions saved by Export are listed below. Storage root: {root}",
        "exports.action.open_folder": " Open folder",
        "exports.action.refresh": " Refresh",
        "exports.action.open_finder": " Open in Finder",
        "exports.action.open_html": " Open transcription.html",
        "exports.sessions.title": "Sessions",
        "exports.sessions.desc": "Double-click a session to open its folder in Finder.",
        "exports.empty.no_dir": "No exports yet — your first 'Export session' will appear here.",
        "exports.empty.empty_dir": "Storage folder exists but is empty.",
    },
    "zh": {
        # Navigation / sidebar
        "nav.tasks": "任务",
        "nav.settings": "设置",
        "nav.exports": "导出",
        "nav.theme.toggle": "切换主题",
        "nav.language.toggle": "切换语言（中文 / English）",
        "nav.github": "在 GitHub 上查看 ParrotSub",
        "brand.tooltip": "ParrotSub",

        # Header / status pill
        "status.idle": "待机",
        "status.recording": "录音中",
        "status.exporting": "导出中…",
        "status.exported": "已导出",
        "status.export_failed": "导出失败：{error}",
        "status.settings_saved": "设置已保存",
        "status.language_set": "语言：{label}",
        "status.theme_set": "主题：{label}",
        "status.cleared": "历史已清空",
        "status.model_fallback": "正在使用 {fallback}",
        "status.no_model": "未下载任何 Whisper 模型",

        # Home page
        "home.tasks.title": "任务",
        "home.tasks.desc": "启动实时识别，或导出当前会话。",
        "home.original.title": "原文",
        "home.original.desc": "来自所选输入设备的实时 Whisper 识别结果。",
        "home.original.placeholder": "对着麦克风说话，识别结果会出现在这里。",
        "home.translation.title": "译文",
        "home.translation.desc": "{src} → {tgt} · 离线翻译（argos-translate）",
        "home.translation.placeholder": "启用翻译后，译文会在这里实时显示。",
        "home.action.start": "  开始录音",
        "home.action.stop": "  停止录音",
        "home.action.export": "  导出会话",
        "home.action.clear": "  清空历史",
        "home.action.clear.tooltip": (
            "停止当前实时识别（如正在运行），并清空内存里的音频缓冲与所有"
            "已识别的字幕。"
        ),
        "home.device_label": "输入：{device}    ·    模型：{model}",
        "home.floating.title": "悬浮字幕窗",
        "home.floating.desc": "将实时字幕悬浮在其他所有应用之上。",
        "home.floating.original": "原文悬浮窗",
        "home.floating.translation": "译文悬浮窗",
        "home.floating.tip": "小贴士：用鼠标拖拽悬浮窗即可调整位置。",

        # Settings page
        "settings.title": "设置",
        "settings.subtitle": (
            "调整实时识别的参数。修改会保存到 "
            "~/.config/glimmer/realtime-subtitle.config。"
        ),
        "settings.action.save": "  保存修改",
        "settings.action.reset": "  恢复默认",
        "settings.group.audio.title": "音频输入",
        "settings.group.audio.desc": "选择实时识别使用的麦克风。",
        "settings.group.model.title": "Whisper 模型",
        "settings.group.model.desc": "选择语音识别模型，以及解码相关的阈值。",
        "settings.model.download": "  下载",
        "settings.model.downloading": "  下载中…",
        "settings.model.installed": "  已安装",
        "settings.model.download.tooltip": (
            "从 HuggingFace 下载当前选中的 Whisper 模型。默认走环境变量 "
            "HF_ENDPOINT，未设置时默认使用国内镜像 hf-mirror.com。"
        ),
        "settings.model.endpoint": "镜像：{endpoint}",
        "settings.model.downloading_status": "正在下载 {model}…",
        "settings.model.downloading_via": "正在从 {endpoint} 下载 {model}…",
        "settings.model.download_progress": "正在下载 {model}：{pct}%（{done:.0f}/{total:.0f} MB · {speed} · 剩余 {eta}）",
        "settings.model.download_ok": "模型下载完成：{model}",
        "settings.model.download_failed": "模型下载失败：{error}",
        "settings.model.already_installed": "已安装：{model}",
        "settings.group.translation.title": "翻译",
        "settings.group.translation.desc": (
            "使用 argos-translate 完全离线地翻译实时字幕。从下拉框中"
            "选择语音的源语言和要翻译成的目标语言。在线翻译已规划在"
            "后续版本中加入。"
        ),
        "settings.group.subtitle.title": "字幕排版",
        "settings.group.subtitle.desc": "原文与译文窗格的换行长度和保留行数。",
        "settings.group.floating.title": "悬浮窗",
        "settings.group.floating.desc": "无边框、置顶、跟随实时字幕的悬浮窗外观。",
        "settings.group.speaker.title": "声纹识别与存储",
        "settings.group.speaker.desc": "可选的声纹聚类，以及导出文件的保存位置。",

        # Field labels (Settings page)
        "field.InputDevice": "输入设备",
        "field.ModelName": "Whisper 模型",
        "field.Latency": "处理延迟（秒）",
        "field.NoSpeechThreshold": "无语音阈值",
        "field.LogprobThreshold": "对数概率阈值",
        "field.TolerationOfLies": "幻听容忍度（秒）",
        "field.ModelRefuseThreshold": "模型拒绝阈值",
        "field.EnableTranslation": "启用翻译",
        "field.OnlineTranslation": "使用在线翻译",
        "field.TranslateFrom": "源语言代码",
        "field.TranslateTo": "目标语言代码",
        "field.TranslationPresantDelay": "译文显示延迟",
        "field.SubtitleLength": "字幕单行字数",
        "field.SubtitleHight": "字幕行数",
        "field.TranslationSubtitleLength": "译文单行字数",
        "field.TranslationSubtitleHight": "译文行数",
        "field.FloatingWindowFontSize": "悬浮窗字号（px）",
        "field.FloatingWindowTextColor": "文字颜色",
        "field.FloatingWindowTextEdgeColor": "文字描边颜色",
        "field.FloatingWindowBackgroundColor": "背景颜色",
        "field.FloatingWindowX": "宽度（屏幕占比）",
        "field.FloatingWindowY": "高度（屏幕占比）",
        "field.FloatingWindowXOffset": "X 偏移（屏幕占比）",
        "field.FloatingWindowYOffset": "Y 偏移（屏幕占比）",
        "field.TranslationFloatingWindowXOffset": "译文窗 X 偏移",
        "field.TranslationFloatingWindowYOffset": "译文窗 Y 偏移",
        "field.EnableSpeakerRecognition": "启用声纹聚类",
        "field.DbscanEps": "DBSCAN epsilon",
        "field.SavePath": "导出保存路径",

        # Exports page
        "exports.title": "导出",
        "exports.subtitle": "下方列出已导出的会话。存储根目录：{root}",
        "exports.action.open_folder": "  打开目录",
        "exports.action.refresh": "  刷新",
        "exports.action.open_finder": "  在 Finder 中打开",
        "exports.action.open_html": "  打开 transcription.html",
        "exports.sessions.title": "历史会话",
        "exports.sessions.desc": "双击任意会话即可在 Finder 中打开它的目录。",
        "exports.empty.no_dir": "还没有导出记录——你第一次「导出会话」之后会出现在这里。",
        "exports.empty.empty_dir": "存储目录存在，但还没有任何会话。",
    },
}


# ---------------------------------------------------------------------------
# Translator singleton
# ---------------------------------------------------------------------------
class Translator(QObject):
    """Holds the active locale and notifies subscribers when it changes."""

    locale_changed = pyqtSignal(str)

    def __init__(self, locale: str = "en") -> None:
        super().__init__()
        self._locale = locale if locale in SUPPORTED_LOCALES else "en"

    @property
    def locale(self) -> str:
        return self._locale

    def set_locale(self, locale: str) -> None:
        if locale not in SUPPORTED_LOCALES or locale == self._locale:
            return
        self._locale = locale
        self.locale_changed.emit(locale)

    def toggle(self) -> None:
        self.set_locale("zh" if self._locale == "en" else "en")

    def t(self, key: str, **kwargs: object) -> str:
        text = _MESSAGES.get(self._locale, {}).get(key)
        if text is None:
            text = _MESSAGES["en"].get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError, ValueError):
                return text
        return text


# Module-level singleton; instantiated lazily so importing the module
# does not require a QCoreApplication.
_translator: Optional[Translator] = None


def translator() -> Translator:
    global _translator
    if _translator is None:
        _translator = Translator(locale=detect_default_locale())
    return _translator


def t(key: str, **kwargs: object) -> str:
    """Module-level convenience wrapper so call-sites don't import the singleton."""
    return translator().t(key, **kwargs)


def detect_default_locale() -> str:
    """Pick a sensible default locale from the OS."""
    try:
        lang, _enc = _stdlocale.getlocale()
        if lang and lang.lower().startswith("zh"):
            return "zh"
    except Exception:
        pass
    try:
        lang, _enc = _stdlocale.getdefaultlocale()
        if lang and lang.lower().startswith("zh"):
            return "zh"
    except Exception:
        pass
    return "en"
