from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .channel import QuestionType


class ModuleKind(str, Enum):
    CORE = "core"
    INDUSTRY = "industry"
    UNIQUE = "unique"


class ModuleQuestion(BaseModel):
    """A pre-authored question from a module sheet (core / industry / unique)."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Stable question ID (e.g. 'core_001', 'opt_std_023', 'opt_sm_004').")
    section: str = Field(description="Section grouping inside the module.")
    text: str = Field(description="The actual question text as authored.")
    question_type: QuestionType = Field(description="Controlled-vocabulary question type.")
    options: list[str] | None = Field(
        default=None,
        description="Choices for single_choice / multi_choice / rating; pipe-separated in the source.",
    )
    required: bool = Field(default=False)
    tags: list[str] = Field(
        default_factory=list,
        description="Topical tags (e.g. 'awareness', 'nps', 'purchase_intent') used for dedup/alignment.",
    )
    notes: str | None = Field(default=None, description="Author notes; not rendered.")

    @field_validator("tags", mode="before")
    @classmethod
    def _split_tags(cls, value: object) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [t.strip().lower() for t in value.split(",") if t.strip()]
        if isinstance(value, list):
            return [str(t).strip().lower() for t in value if str(t).strip()]
        return []

    @field_validator("options", mode="before")
    @classmethod
    def _split_options(cls, value: object) -> list[str] | None:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            parts = [p.strip() for p in value.split("|") if p.strip()]
            return parts or None
        if isinstance(value, list):
            cleaned = [str(p).strip() for p in value if str(p).strip()]
            return cleaned or None
        return None


class Module(BaseModel):
    """A logical group of pre-authored questions from one sheet."""

    kind: ModuleKind = Field(description="core | industry | unique")
    name: str = Field(description="Module name (e.g. 'core', 'opticians', 'opticians:social_media').")
    industry: str | None = Field(default=None, description="Industry slug if applicable.")
    channel: str | None = Field(default=None, description="Channel slug if applicable.")
    questions: list[ModuleQuestion] = Field(description="Questions in author-defined order.")

    @property
    def count(self) -> int:
        return len(self.questions)


class ModuleSet(BaseModel):
    """The 3-module bundle for one industry × channel combination."""

    industry: str
    channel: str
    core: Module
    industry_standard: Module
    unique: Module

    @property
    def total_questions(self) -> int:
        return self.core.count + self.industry_standard.count + self.unique.count


class DuplicateCandidate(BaseModel):
    """A pair of questions flagged as potential duplicates for the LLM to resolve."""

    primary_id: str
    duplicate_id: str
    overlap_tags: list[str]
    similarity: float = Field(ge=0.0, le=1.0, description="0..1 normalized text similarity.")
    primary_text: str
    duplicate_text: str
