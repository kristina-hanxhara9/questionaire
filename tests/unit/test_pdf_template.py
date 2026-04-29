from __future__ import annotations

from pathlib import Path

from mcp_market_research.parsers.pdf_template import (
    clear_cache,
    extract_template_structure,
)


def test_extracts_placeholders(sample_pdf_path: Path) -> None:
    clear_cache()
    structure = extract_template_structure(sample_pdf_path)
    keys = {p.key for p in structure.placeholders}
    assert {"COMPANY_NAME", "QUESTIONNAIRE_TITLE", "LANGUAGE", "COUNTRY", "GENERATED_DATE"} <= keys


def test_marks_reserved_placeholders(sample_pdf_path: Path) -> None:
    clear_cache()
    structure = extract_template_structure(sample_pdf_path)
    company = next(p for p in structure.placeholders if p.key == "COMPANY_NAME")
    assert company.reserved is True
    assert company.hint is not None


def test_caches_by_mtime(sample_pdf_path: Path) -> None:
    clear_cache()
    a = extract_template_structure(sample_pdf_path)
    b = extract_template_structure(sample_pdf_path)
    assert a is b
