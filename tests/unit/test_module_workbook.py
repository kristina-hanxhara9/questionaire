from __future__ import annotations

from pathlib import Path

import pytest

from mcp_market_research.errors import IndustryNotFoundError, ModuleNotFoundError
from mcp_market_research.models import ModuleKind
from mcp_market_research.parsers.module_workbook import (
    assemble_module_set,
    clear_cache,
    get_core_module,
    get_industry_module,
    get_unique_module,
    is_module_workbook,
    list_channels_for_industry,
    list_industries,
)


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    clear_cache()


def test_is_module_workbook_detects_modules(sample_modules_path: Path) -> None:
    assert is_module_workbook(sample_modules_path) is True


def test_legacy_workbook_is_not_module(sample_excel_path: Path) -> None:
    assert is_module_workbook(sample_excel_path) is False


def test_list_industries(sample_modules_path: Path) -> None:
    assert list_industries(sample_modules_path) == ["opticians"]


def test_list_channels_for_industry(sample_modules_path: Path) -> None:
    channels = list_channels_for_industry(sample_modules_path, "opticians")
    assert "social_media" in channels
    assert "email" in channels
    assert "in_store" in channels


def test_unknown_industry_raises(sample_modules_path: Path) -> None:
    with pytest.raises(IndustryNotFoundError):
        list_channels_for_industry(sample_modules_path, "dentists")


def test_get_core_module(sample_modules_path: Path) -> None:
    module = get_core_module(sample_modules_path)
    assert module.kind == ModuleKind.CORE
    assert module.count >= 10
    ids = {q.id for q in module.questions}
    assert "core_001" in ids
    assert all(q.id.startswith("core_") for q in module.questions)


def test_get_industry_module(sample_modules_path: Path) -> None:
    module = get_industry_module(sample_modules_path, "opticians")
    assert module.kind == ModuleKind.INDUSTRY
    assert module.industry == "opticians"
    assert module.count >= 5
    assert all(q.id.startswith("opt_std_") for q in module.questions)


def test_get_unique_module(sample_modules_path: Path) -> None:
    module = get_unique_module(sample_modules_path, "opticians", "social_media")
    assert module.kind == ModuleKind.UNIQUE
    assert module.industry == "opticians"
    assert module.channel == "social_media"
    assert module.count >= 1
    assert all(q.id.startswith("opt_sm_") for q in module.questions)


def test_unknown_unique_raises(sample_modules_path: Path) -> None:
    with pytest.raises(ModuleNotFoundError):
        get_unique_module(sample_modules_path, "opticians", "nonexistent_channel")


def test_assemble_module_set(sample_modules_path: Path) -> None:
    bundle = assemble_module_set(sample_modules_path, "opticians", "email")
    assert bundle.industry == "opticians"
    assert bundle.channel == "email"
    assert bundle.total_questions == bundle.core.count + bundle.industry_standard.count + bundle.unique.count


def test_question_options_are_split(sample_modules_path: Path) -> None:
    module = get_core_module(sample_modules_path)
    awareness = next(q for q in module.questions if q.id == "core_001")
    assert awareness.options is not None
    assert "Search engine" in awareness.options


def test_tags_are_split(sample_modules_path: Path) -> None:
    module = get_core_module(sample_modules_path)
    awareness = next(q for q in module.questions if q.id == "core_001")
    assert "awareness" in awareness.tags
