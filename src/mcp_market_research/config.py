from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_ROOT = Path(__file__).resolve().parent
SAMPLES_DIR = PACKAGE_ROOT / "samples"

DEFAULT_EXCEL_GUIDE = SAMPLES_DIR / "sample_channel_guide.xlsx"
DEFAULT_PDF_TEMPLATE = SAMPLES_DIR / "sample_template.pdf"
DEFAULT_DOCX_TEMPLATE = SAMPLES_DIR / "sample_template.docx"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    mcp_api_keys: str = Field(
        default="dev-key",
        description="Comma-separated bearer tokens.",
    )

    excel_guide_path: Path = Field(default=DEFAULT_EXCEL_GUIDE)
    pdf_template_path: Path = Field(default=DEFAULT_PDF_TEMPLATE)
    docx_template_path: Path = Field(default=DEFAULT_DOCX_TEMPLATE)
    output_dir: Path = Field(default=Path("./output"))

    log_level: str = Field(default="INFO")
    log_json: bool = Field(default=True)

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080)

    translation_timeout_s: int = Field(default=15, ge=1, le=120)

    otel_exporter_otlp_endpoint: str | None = Field(default=None)

    @field_validator("excel_guide_path", "pdf_template_path", "docx_template_path", mode="before")
    @classmethod
    def _resolve_path(cls, value: object) -> object:
        if value in (None, "", "None"):
            return None
        return value

    @field_validator("excel_guide_path")
    @classmethod
    def _excel_fallback(cls, value: Path | None) -> Path:
        return _resolve_or_default(value, DEFAULT_EXCEL_GUIDE)

    @field_validator("pdf_template_path")
    @classmethod
    def _pdf_fallback(cls, value: Path | None) -> Path:
        return _resolve_or_default(value, DEFAULT_PDF_TEMPLATE)

    @field_validator("docx_template_path")
    @classmethod
    def _docx_fallback(cls, value: Path | None) -> Path:
        return _resolve_or_default(value, DEFAULT_DOCX_TEMPLATE)

    @property
    def api_keys(self) -> tuple[str, ...]:
        return tuple(k.strip() for k in self.mcp_api_keys.split(",") if k.strip())

    @property
    def using_sample_excel(self) -> bool:
        return self.excel_guide_path == DEFAULT_EXCEL_GUIDE

    @property
    def using_sample_pdf(self) -> bool:
        return self.pdf_template_path == DEFAULT_PDF_TEMPLATE

    @property
    def using_sample_docx(self) -> bool:
        return self.docx_template_path == DEFAULT_DOCX_TEMPLATE


def _resolve_or_default(value: Path | None, default: Path) -> Path:
    if value is None:
        return default
    path = Path(value).expanduser()
    if path.exists():
        return path.resolve()
    return default


@lru_cache
def get_settings() -> Settings:
    return Settings()
