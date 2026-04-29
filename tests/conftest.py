from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

SAMPLES = SRC / "mcp_market_research" / "samples"
EXCEL_PATH = SAMPLES / "sample_channel_guide.xlsx"
MODULES_PATH = SAMPLES / "sample_modules.xlsx"
PDF_PATH = SAMPLES / "sample_template.pdf"
DOCX_PATH = SAMPLES / "sample_template.docx"


@pytest.fixture(scope="session", autouse=True)
def ensure_samples() -> None:
    """Generate sample assets if they aren't present."""
    if all(p.exists() for p in (EXCEL_PATH, MODULES_PATH, PDF_PATH, DOCX_PATH)):
        return
    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_samples import main as generate

    generate()


@pytest.fixture
def sample_excel_path() -> Path:
    return EXCEL_PATH


@pytest.fixture
def sample_modules_path() -> Path:
    return MODULES_PATH


@pytest.fixture
def sample_pdf_path() -> Path:
    return PDF_PATH


@pytest.fixture
def sample_docx_path() -> Path:
    return DOCX_PATH


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    out = tmp_path / "output"
    out.mkdir()
    return out


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch, output_dir: Path) -> object:
    monkeypatch.setenv("MCP_API_KEYS", "test-key")
    monkeypatch.setenv("EXCEL_GUIDE_PATH", str(EXCEL_PATH))
    monkeypatch.setenv("PDF_TEMPLATE_PATH", str(PDF_PATH))
    monkeypatch.setenv("DOCX_TEMPLATE_PATH", str(DOCX_PATH))
    monkeypatch.setenv("OUTPUT_DIR", str(output_dir))
    monkeypatch.setenv("LOG_JSON", "false")

    from mcp_market_research.config import get_settings

    get_settings.cache_clear()
    return get_settings()
