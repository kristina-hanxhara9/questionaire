from __future__ import annotations

from datetime import datetime, timezone

import pytest

from mcp_market_research.errors import LocaleNotSupportedError
from mcp_market_research.tools.locale import (
    SUPPORTED_LANGUAGES,
    format_date,
    get_country_locale_info,
    list_supported_languages_tool,
)


def test_lists_supported_languages_includes_common_codes() -> None:
    locales = list_supported_languages_tool()
    codes = {loc.language for loc in locales}
    assert {"en", "fr", "de", "es", "ar", "zh"} <= codes
    assert codes == set(SUPPORTED_LANGUAGES)


def test_get_country_locale_for_france() -> None:
    info = get_country_locale_info("FR", "fr")
    assert info.country_code == "FR"
    assert info.language == "fr"
    assert info.country_name


def test_arabic_is_marked_rtl() -> None:
    info = get_country_locale_info("SA", "ar")
    assert info.rtl is True


def test_unknown_country_raises() -> None:
    with pytest.raises(LocaleNotSupportedError):
        get_country_locale_info("ZZ", "en")


def test_format_date_in_french() -> None:
    info = get_country_locale_info("FR", "fr")
    when = datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc)
    formatted = format_date(when, info)
    assert "29" in formatted
    assert "2026" in formatted
