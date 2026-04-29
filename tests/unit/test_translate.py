from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from mcp_market_research.errors import TranslationError
from mcp_market_research.tools.translate import translate_text_blocks_tool


class _FakeTranslator:
    def __init__(self, *, source: str = "en", target: str = "fr", fail_count: int = 0) -> None:
        self.source = source
        self.target = target
        self.fail_count = fail_count
        self.calls = 0

    def translate(self, text: str) -> str:
        self.calls += 1
        if self.calls <= self.fail_count:
            raise RuntimeError("temporary failure")
        return f"[{self.target}] {text}"


def test_passthrough_when_languages_match(settings: Any) -> None:
    out = translate_text_blocks_tool(
        settings, blocks=["hello", "world"], target_language="en", source_language="en"
    )
    assert out == ["hello", "world"]


def test_translates_each_block(settings: Any) -> None:
    fake = _FakeTranslator(target="fr")
    with patch("mcp_market_research.tools.translate._get_translator", return_value=fake):
        out = translate_text_blocks_tool(
            settings, blocks=["hello", "world"], target_language="fr"
        )
    assert out == ["[fr] hello", "[fr] world"]


def test_empty_input_returns_empty(settings: Any) -> None:
    out = translate_text_blocks_tool(settings, blocks=[], target_language="fr")
    assert out == []


def test_retries_then_succeeds(settings: Any) -> None:
    fake = _FakeTranslator(target="de", fail_count=2)
    with patch("mcp_market_research.tools.translate._get_translator", return_value=fake):
        out = translate_text_blocks_tool(settings, blocks=["one"], target_language="de")
    assert out == ["[de] one"]
    assert fake.calls == 3


def test_failure_after_retries(settings: Any) -> None:
    fake = _FakeTranslator(target="de", fail_count=10)
    with patch("mcp_market_research.tools.translate._get_translator", return_value=fake):
        with pytest.raises(TranslationError):
            translate_text_blocks_tool(settings, blocks=["one"], target_language="de")
