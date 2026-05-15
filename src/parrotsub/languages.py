"""Language tables for the Settings page dropdowns.

ParrotSub deliberately exposes a small, hand-picked set of nine
languages – Simplified & Traditional Chinese, English, French, German,
Japanese, Korean, Spanish and Russian – instead of the full ~99 that
whisper recognises or the ~47 that argos-translate could in theory
ship. The shorter list keeps the picker scannable, every entry is
known to be installable from the argos package index, and every entry
is also a language whisper can transcribe.

We intentionally show each language as ``"Endonym (code)"`` (e.g.
``中文 (zh)``) so the picker is locale-independent.

When a Whisper model name contains ``.en`` (e.g.
``whisper-tiny.en-mlx``) it is an English-only variant and the
*Translate From* dropdown collapses to English only.
"""

from __future__ import annotations

from typing import List, Tuple


# ---------------------------------------------------------------------------
# Display names – endonyms (the language's name in itself).
# Codes that don't get a localised name fall back to their code.
# ---------------------------------------------------------------------------
LANGUAGE_NAMES: dict[str, str] = {
    # Major Asian
    "zh": "中文",
    "ja": "日本語",
    "ko": "한국어",
    "vi": "Tiếng Việt",
    "th": "ไทย",
    "id": "Bahasa Indonesia",
    "ms": "Bahasa Melayu",
    "tl": "Tagalog",
    "hi": "हिन्दी",
    "bn": "বাংলা",
    "ta": "தமிழ்",
    "ur": "اردو",
    "fa": "فارسی",
    "he": "עברית",
    "ar": "العربية",
    # Western European
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "pt": "Português",
    "nl": "Nederlands",
    "ca": "Català",
    "ga": "Gaeilge",
    "eo": "Esperanto",
    # Northern European
    "sv": "Svenska",
    "da": "Dansk",
    "nb": "Norsk Bokmål",
    "no": "Norsk",
    "nn": "Nynorsk",
    "fi": "Suomi",
    "is": "Íslenska",
    "et": "Eesti",
    "lv": "Latviešu",
    "lt": "Lietuvių",
    # Eastern European
    "ru": "Русский",
    "uk": "Українська",
    "be": "Беларуская",
    "pl": "Polski",
    "cs": "Čeština",
    "sk": "Slovenčina",
    "sl": "Slovenščina",
    "hu": "Magyar",
    "ro": "Română",
    "bg": "Български",
    "sr": "Српски",
    "hr": "Hrvatski",
    "bs": "Bosanski",
    "sq": "Shqip",
    "el": "Ελληνικά",
    "mk": "Македонски",
    "tr": "Türkçe",
    "az": "Azərbaycan",
    "kk": "Қазақша",
    "uz": "O‘zbek",
    # Africa
    "sw": "Kiswahili",
    "af": "Afrikaans",
    "am": "አማርኛ",
    "yo": "Yorùbá",
    "ha": "Hausa",
    "so": "Soomaali",
    # Misc
    "zt": "繁體中文",
    "cy": "Cymraeg",
    "mt": "Malti",
    "lb": "Lëtzebuergesch",
    "yi": "ייִדיש",
    "mn": "Монгол",
    "ka": "ქართული",
    "hy": "Հայերեն",
    "ne": "नेपाली",
    "si": "සිංහල",
    "km": "ខ្មែរ",
    "lo": "ລາວ",
    "my": "မြန်မာ",
    "mr": "मराठी",
    "te": "తెలుగు",
    "kn": "ಕನ್ನಡ",
    "ml": "മലയാളം",
    "pa": "ਪੰਜਾਬੀ",
    "gu": "ગુજરાતી",
    "as": "অসমীয়া",
    "haw": "ʻŌlelo Hawaiʻi",
    "mi": "Māori",
    "su": "Basa Sunda",
    "jw": "Basa Jawa",
    "tt": "Татар теле",
    "ba": "Башҡорт",
    "tg": "Тоҷикӣ",
    "tk": "Türkmen",
    "fo": "Føroyskt",
    "br": "Brezhoneg",
    "oc": "Occitan",
    "eu": "Euskara",
    "gl": "Galego",
    "la": "Latina",
    "sn": "ChiShona",
    "mg": "Malagasy",
    "sa": "संस्कृतम्",
    "ln": "Lingála",
    "ps": "پښتو",
    "sd": "سنڌي",
    "bo": "བོད་སྐད",
    "ht": "Kreyòl Ayisyen",
}

# ---------------------------------------------------------------------------
# Curated language set – the *only* languages exposed in the Settings
# dropdowns. Order is intentional (most-relevant first, no alphabetical
# sort) so the picker stays predictable for the typical user. Every
# entry is supported by both whisper and argos-translate.
# ---------------------------------------------------------------------------
CURATED_LANGUAGE_CODES: tuple[str, ...] = (
    "zh",   # 简体中文
    "zt",   # 繁體中文
    "en",   # English
    "fr",   # Français
    "de",   # Deutsch
    "ja",   # 日本語
    "ko",   # 한국어
    "es",   # Español
    "ru",   # Русский
)


def is_english_only_model(model_name: str) -> bool:
    """``mlx-community/whisper-tiny.en-mlx`` and friends are EN-only."""
    return ".en" in (model_name or "").lower()


# Codes that show up in legacy free-text configs but are not valid
# ISO-639-1 / argos identifiers. Mapped to their canonical equivalents.
LEGACY_CODE_FIXES: dict[str, str] = {
    "cn": "zh",   # "China" / Mandarin – proper code is zh
    "tw": "zt",   # Traditional Chinese (argos uses zt)
    "jp": "ja",   # Japan – proper code is ja
    "kr": "ko",   # Korea – proper code is ko
    "uk": "uk",   # Ukrainian – kept as-is (uk is valid; do NOT remap to en)
    "us": "en",   # User likely meant English
    "gb": "en",
}


def migrate_legacy_code(code: str) -> str:
    """Return the canonical language code for a legacy/typo input.

    Returns ``code`` unchanged when no migration is needed.
    """
    if not code:
        return code
    return LEGACY_CODE_FIXES.get(code.lower(), code)


def label(code: str) -> str:
    """Return a friendly label for a language code, e.g. ``中文 (zh)``."""
    name = LANGUAGE_NAMES.get(code, code)
    if name == code:
        return code
    return f"{name} ({code})"


def source_language_options(model_name: str = "") -> List[Tuple[str, str]]:
    """``[(code, label), ...]`` for the **Translate From** dropdown.

    The list is the curated 9-language set (zh, zt, en, fr, de, ja, ko,
    es, ru). When the active Whisper model is English-only (``.en`` in
    the name), only English is offered.
    """
    if is_english_only_model(model_name):
        codes: List[str] = ["en"]
    else:
        codes = list(CURATED_LANGUAGE_CODES)
    return [(c, label(c)) for c in codes]


def target_language_options() -> List[Tuple[str, str]]:
    """``[(code, label), ...]`` for the **Translate To** dropdown."""
    return [(c, label(c)) for c in CURATED_LANGUAGE_CODES]
