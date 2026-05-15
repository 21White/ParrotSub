"""Language tables for the Settings page dropdowns.

Two facts inform the dropdown contents:

1. **Whisper** can transcribe ~99 languages. The full code → name table
   matches OpenAI's reference list. Whisper model names that contain
   ``.en`` (e.g. ``whisper-tiny.en-mlx``) are *English-only* variants
   and only produce useful results for English audio.
2. **argos-translate** ships translation packages for a smaller subset.
   The intersection of these two is what we expose for the
   ``TranslateFrom`` dropdown so that, after Whisper recognises the
   speech, we can actually translate it offline.

For ``TranslateTo`` we list every language argos can translate *into*
(via English pivot when no direct package exists).

We intentionally show each language as ``"Endonym (code)"`` (e.g.
``中文 (zh)``) so the picker is locale-independent.
"""

from __future__ import annotations

from typing import Iterable, List, Tuple


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
# Whisper recognises ~99 languages. Source: OpenAI whisper/tokenizer.py
# ---------------------------------------------------------------------------
WHISPER_LANGUAGE_CODES: tuple[str, ...] = (
    "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl",
    "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk",
    "el", "ms", "cs", "ro", "da", "hu", "ta", "no", "th", "ur", "hr",
    "bg", "lt", "la", "mi", "ml", "cy", "sk", "te", "fa", "lv", "bn",
    "sr", "az", "sl", "kn", "et", "mk", "br", "eu", "is", "hy", "ne",
    "mn", "bs", "kk", "sq", "sw", "gl", "mr", "pa", "si", "km", "sn",
    "yo", "so", "af", "oc", "ka", "be", "tg", "sd", "gu", "am", "yi",
    "lo", "uz", "fo", "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my",
    "bo", "tl", "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw", "su",
)

# ---------------------------------------------------------------------------
# argos-translate has shipped translation packages for these languages
# (either as a direct pair or via the English pivot). Kept conservative
# so every option is downloadable when the user picks it.
# ---------------------------------------------------------------------------
ARGOS_LANGUAGE_CODES: tuple[str, ...] = (
    "ar", "az", "bg", "bn", "ca", "cs", "da", "de", "el", "en", "eo",
    "es", "et", "fa", "fi", "fr", "ga", "he", "hi", "hu", "id", "it",
    "ja", "ko", "lt", "lv", "ms", "nb", "nl", "pl", "pt", "ro", "ru",
    "sk", "sl", "sq", "sv", "sw", "ta", "th", "tl", "tr", "uk", "ur",
    "vi", "zh", "zt",
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


def _ordered_intersect(a: Iterable[str], b: Iterable[str]) -> List[str]:
    seen = set(b)
    keep = [c for c in a if c in seen]
    return sorted(set(keep), key=lambda x: label(x).casefold())


def source_language_options(model_name: str = "") -> List[Tuple[str, str]]:
    """``[(code, label), ...]`` for the **Translate From** dropdown.

    Filters Whisper's full language list down to those argos can also
    translate from. If the active Whisper model is an English-only
    variant (``.en`` in the name), only English is offered.
    """
    if is_english_only_model(model_name):
        codes = ["en"]
    else:
        codes = _ordered_intersect(WHISPER_LANGUAGE_CODES, ARGOS_LANGUAGE_CODES)
    return [(c, label(c)) for c in codes]


def target_language_options() -> List[Tuple[str, str]]:
    """``[(code, label), ...]`` for the **Translate To** dropdown."""
    codes = sorted(set(ARGOS_LANGUAGE_CODES), key=lambda x: label(x).casefold())
    return [(c, label(c)) for c in codes]
