from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from .channel import QuestionType


class Question(BaseModel):
    text: str = Field(description="The question as it should appear in the document.")
    type: QuestionType = Field(description="Question type, drawn from controlled vocabulary.")
    options: list[str] | None = Field(
        default=None,
        description="Choices for single_choice / multi_choice / rating types.",
    )
    required: bool = Field(default=False)

    @field_validator("options")
    @classmethod
    def _strip_empty_options(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = [opt.strip() for opt in value if opt and opt.strip()]
        return cleaned or None


class Section(BaseModel):
    heading: str = Field(description="Section heading text.")
    questions: list[Question] = Field(description="Questions in this section, in order.")


class RenderRequest(BaseModel):
    title: str = Field(description="Questionnaire title (replaces {{QUESTIONNAIRE_TITLE}}).")
    language: str = Field(description="ISO 639-1 language code, e.g. 'en', 'fr', 'de'.")
    country_code: str | None = Field(
        default=None, description="ISO 3166-1 alpha-2 country code, e.g. 'FR'."
    )
    company_name: str = Field(description="Replaces {{COMPANY_NAME}}.")
    sections: list[Section] = Field(description="Composed sections with questions.")
    extra_placeholders: dict[str, str] = Field(
        default_factory=dict, description="Custom placeholder values keyed by placeholder name."
    )

    @field_validator("language")
    @classmethod
    def _normalize_language(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("country_code")
    @classmethod
    def _normalize_country(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().upper() or None


class RenderResult(BaseModel):
    path: str = Field(description="Absolute path to the rendered .docx on disk.")
    filename: str = Field(description="Just the file name, no directory.")
    bytes_b64: str | None = Field(
        default=None,
        description="Base64-encoded .docx content. Only included for files smaller than 4 MB.",
    )
    size_bytes: int = Field(description="Rendered file size in bytes.")


class DualLanguageRenderResult(BaseModel):
    """Result of rendering both English and a target-language version."""

    english: RenderResult
    translated: RenderResult | None = Field(
        default=None,
        description="None if the requested language was English (no translation needed).",
    )
