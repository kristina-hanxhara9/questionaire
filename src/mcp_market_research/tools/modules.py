from __future__ import annotations

from difflib import SequenceMatcher

from ..config import Settings
from ..logging_setup import traced_tool
from ..models import DuplicateCandidate, Module, ModuleQuestion, ModuleSet
from ..parsers import (
    assemble_module_set,
    get_core_module,
    get_industry_module,
    get_unique_module,
    list_channels_for_industry,
    list_industries,
)


def list_industries_tool(settings: Settings) -> list[str]:
    @traced_tool("list_industries")
    def _impl() -> list[str]:
        return list_industries(settings.excel_guide_path)

    return _impl()


def list_channels_for_industry_tool(settings: Settings, industry: str) -> list[str]:
    @traced_tool("list_channels_for_industry")
    def _impl() -> list[str]:
        return list_channels_for_industry(settings.excel_guide_path, industry)

    return _impl()


def get_core_module_tool(settings: Settings) -> Module:
    @traced_tool("get_core_module")
    def _impl() -> Module:
        return get_core_module(settings.excel_guide_path)

    return _impl()


def get_industry_module_tool(settings: Settings, industry: str) -> Module:
    @traced_tool("get_industry_module")
    def _impl() -> Module:
        return get_industry_module(settings.excel_guide_path, industry)

    return _impl()


def get_unique_module_tool(settings: Settings, industry: str, channel: str) -> Module:
    @traced_tool("get_unique_module")
    def _impl() -> Module:
        return get_unique_module(settings.excel_guide_path, industry, channel)

    return _impl()


def assemble_modules_tool(settings: Settings, industry: str, channel: str) -> ModuleSet:
    @traced_tool("assemble_modules")
    def _impl() -> ModuleSet:
        return assemble_module_set(settings.excel_guide_path, industry, channel)

    return _impl()


def find_duplicate_candidates_tool(
    questions: list[ModuleQuestion],
    similarity_threshold: float = 0.78,
) -> list[DuplicateCandidate]:
    """Surface candidate duplicate pairs by tag overlap + normalized text similarity.

    The reviewer/composer agent decides which to merge. We deliberately don't
    auto-drop questions — semantic intent matters more than literal text overlap."""

    @traced_tool("find_duplicate_candidates")
    def _impl() -> list[DuplicateCandidate]:
        candidates: list[DuplicateCandidate] = []
        normalized = [(q, _normalize(q.text)) for q in questions]

        for i in range(len(normalized)):
            q1, t1 = normalized[i]
            tags1 = set(q1.tags)
            for j in range(i + 1, len(normalized)):
                q2, t2 = normalized[j]
                tags2 = set(q2.tags)
                tag_overlap = sorted(tags1 & tags2)

                similarity = SequenceMatcher(None, t1, t2).ratio()
                if similarity < similarity_threshold and not tag_overlap:
                    continue
                if similarity < 0.55 and len(tag_overlap) < 2:
                    continue

                candidates.append(
                    DuplicateCandidate(
                        primary_id=q1.id,
                        duplicate_id=q2.id,
                        overlap_tags=tag_overlap,
                        similarity=round(similarity, 3),
                        primary_text=q1.text,
                        duplicate_text=q2.text,
                    )
                )

        candidates.sort(key=lambda c: c.similarity, reverse=True)
        return candidates

    return _impl()


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())
