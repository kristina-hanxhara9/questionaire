from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Placeholder(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str = Field(description="Placeholder name without braces, e.g. COMPANY_NAME.")
    reserved: bool = Field(default=False, description="True for built-in placeholders.")
    hint: str | None = Field(default=None, description="Suggested value or formatting hint.")


class TemplateStructure(BaseModel):
    sections: list[str] = Field(description="Detected section headings, in document order.")
    placeholders: list[Placeholder] = Field(
        description="Detected {{KEY}} placeholders, deduplicated."
    )
    page_count: int = Field(description="Pages in the source PDF.")
    source_path: str = Field(description="Absolute path to the parsed PDF.")
