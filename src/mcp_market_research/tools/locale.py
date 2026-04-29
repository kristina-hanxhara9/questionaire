from __future__ import annotations

from datetime import datetime

from babel import Locale, UnknownLocaleError
from babel.dates import format_date as babel_format_date

from ..errors import LocaleNotSupportedError
from ..logging_setup import traced_tool
from ..models import LocaleInfo

# Languages where deep-translator's GoogleTranslator backend supports translation.
# A non-exhaustive but practical set; extend freely.
SUPPORTED_LANGUAGES: tuple[str, ...] = (
    "af", "am", "ar", "az", "be", "bg", "bn", "bs", "ca", "cs", "cy", "da", "de",
    "el", "en", "eo", "es", "et", "eu", "fa", "fi", "fr", "ga", "gl", "gu", "ha",
    "he", "hi", "hr", "hu", "hy", "id", "ig", "is", "it", "ja", "jv", "ka", "kk",
    "km", "kn", "ko", "ku", "ky", "lo", "lt", "lv", "mk", "ml", "mn", "mr", "ms",
    "mt", "my", "ne", "nl", "no", "pa", "pl", "ps", "pt", "ro", "ru", "si", "sk",
    "sl", "so", "sq", "sr", "sv", "sw", "ta", "te", "tg", "th", "tk", "tl", "tr",
    "uk", "ur", "uz", "vi", "xh", "yi", "yo", "zh", "zu",
)

RTL_LANGUAGES = frozenset({"ar", "fa", "he", "ps", "ur", "yi"})


def list_supported_languages_tool() -> list[LocaleInfo]:
    @traced_tool("list_supported_languages")
    def _impl() -> list[LocaleInfo]:
        result: list[LocaleInfo] = []
        for code in SUPPORTED_LANGUAGES:
            try:
                native = Locale(code).get_display_name(code) or code
            except (UnknownLocaleError, ValueError):
                native = code
            result.append(
                LocaleInfo(
                    language=code,
                    language_native=native,
                    rtl=code in RTL_LANGUAGES,
                )
            )
        return result

    return _impl()


def get_country_locale_tool(country_code: str, language: str | None = None) -> LocaleInfo:
    @traced_tool("get_country_locale")
    def _impl() -> LocaleInfo:
        return get_country_locale_info(country_code, language)

    return _impl()


def get_country_locale_info(country_code: str | None, language: str | None) -> LocaleInfo:
    lang = (language or "en").strip().lower()
    if country_code is None:
        return _build_from_language(lang)

    country_norm = country_code.strip().upper()
    try:
        locale = Locale.parse(f"{lang}_{country_norm}")
    except (UnknownLocaleError, ValueError):
        try:
            locale = Locale.parse(f"en_{country_norm}")
            lang = "en"
        except (UnknownLocaleError, ValueError) as err:
            raise LocaleNotSupportedError(country_norm) from err

    return _to_locale_info(locale, lang, country_norm)


def _build_from_language(lang: str) -> LocaleInfo:
    try:
        locale = Locale.parse(lang)
    except (UnknownLocaleError, ValueError) as err:
        raise LocaleNotSupportedError(lang) from err
    return _to_locale_info(locale, lang, None)


def _to_locale_info(locale: Locale, lang: str, country: str | None) -> LocaleInfo:
    native_name = locale.get_display_name(locale) or lang
    country_name: str | None = None
    if country and locale.territory:
        try:
            country_name = locale.get_display_name().split(" (")[0]
            country_name = locale.territories.get(locale.territory, country_name)
        except Exception:  # noqa: BLE001
            country_name = None

    decimal = locale.number_symbols.get("latn", {}).get("decimal", ".") if hasattr(
        locale, "number_symbols"
    ) else "."

    first_day = getattr(locale, "first_week_day", 0) or 0

    return LocaleInfo(
        language=lang,
        language_native=native_name,
        country_code=country,
        country_name=country_name,
        date_format="d MMMM y",
        decimal_separator=decimal,
        first_day_of_week=int(first_day),
        rtl=lang in RTL_LANGUAGES,
    )


def format_date(value: datetime, locale: LocaleInfo) -> str:
    babel_locale_str = (
        f"{locale.language}_{locale.country_code}" if locale.country_code else locale.language
    )
    try:
        babel_locale = Locale.parse(babel_locale_str)
    except (UnknownLocaleError, ValueError):
        babel_locale = Locale.parse(locale.language) if locale.language else Locale("en")
    return babel_format_date(value.date(), format=locale.date_format, locale=babel_locale)
