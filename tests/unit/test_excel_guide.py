from __future__ import annotations

from pathlib import Path

import pytest
from openpyxl import Workbook

from mcp_market_research.errors import ChannelNotFoundError, ExcelGuideValidationError
from mcp_market_research.models import QuestionType
from mcp_market_research.parsers.excel_guide import (
    clear_cache,
    get_channel_guide,
    list_channel_names,
    load_channel_guides,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_cache()


def test_loads_three_channels_from_sample(sample_excel_path: Path) -> None:
    guides = load_channel_guides(sample_excel_path)
    assert {"social_media", "email", "in_store"} <= set(guides.keys())
    assert "_meta" not in guides


def test_list_channel_names_skips_underscored_sheets(sample_excel_path: Path) -> None:
    names = list_channel_names(sample_excel_path)
    assert all(not n.startswith("_") for n in names)


def test_get_channel_guide_returns_sections(sample_excel_path: Path) -> None:
    guide = get_channel_guide(sample_excel_path, "social_media")
    assert guide.name == "social_media"
    assert guide.sections, "expected at least one section"
    first = guide.sections[0]
    assert first.heading
    assert first.rows
    assert isinstance(first.rows[0].question_type, QuestionType)


def test_unknown_channel_raises(sample_excel_path: Path) -> None:
    with pytest.raises(ChannelNotFoundError) as exc_info:
        get_channel_guide(sample_excel_path, "tiktok-livestream")
    assert "social_media" in exc_info.value.available


def test_case_insensitive_channel_lookup(sample_excel_path: Path) -> None:
    guide = get_channel_guide(sample_excel_path, "Social_Media")
    assert guide.name == "social_media"


def test_required_columns_missing(tmp_path: Path) -> None:
    bad = tmp_path / "bad.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "channel_x"
    ws.append(["section", "guidance"])  # missing question_type
    ws.append(["Awareness", "Some guidance"])
    wb.save(bad)

    with pytest.raises(ExcelGuideValidationError) as exc:
        load_channel_guides(bad)
    assert any("question_type" in msg for msg in exc.value.errors)


def test_unknown_question_type(tmp_path: Path) -> None:
    bad = tmp_path / "bad.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "channel_y"
    ws.append(["section", "question_type", "guidance"])
    ws.append(["Awareness", "telekinesis", "Use mind powers"])
    wb.save(bad)

    with pytest.raises(ExcelGuideValidationError) as exc:
        load_channel_guides(bad)
    assert any("telekinesis" in msg for msg in exc.value.errors)
