from __future__ import annotations

from pathlib import Path

import pytest

from mcp_market_research.config import (
    DEFAULT_DOCX_TEMPLATE,
    DEFAULT_EXCEL_GUIDE,
    DEFAULT_PDF_TEMPLATE,
    Settings,
    get_settings,
)


def test_api_keys_split() -> None:
    settings = Settings(mcp_api_keys=" key-a , key-b ,  ")
    assert settings.api_keys == ("key-a", "key-b")


def test_missing_path_falls_back_to_sample(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXCEL_GUIDE_PATH", "/totally/missing/file.xlsx")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.excel_guide_path == DEFAULT_EXCEL_GUIDE
    assert settings.using_sample_excel is True


def test_real_path_used_when_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real = tmp_path / "channel_guide.xlsx"
    real.write_bytes(b"placeholder")
    monkeypatch.setenv("EXCEL_GUIDE_PATH", str(real))
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.excel_guide_path == real.resolve()
    assert settings.using_sample_excel is False


def test_pdf_and_docx_default_to_samples(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PDF_TEMPLATE_PATH", raising=False)
    monkeypatch.delenv("DOCX_TEMPLATE_PATH", raising=False)
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.pdf_template_path == DEFAULT_PDF_TEMPLATE
    assert settings.docx_template_path == DEFAULT_DOCX_TEMPLATE
