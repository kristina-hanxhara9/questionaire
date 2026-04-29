from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    SCALE = "scale"
    OPEN_TEXT = "open_text"
    NUMERIC = "numeric"
    YES_NO = "yes_no"
    RATING = "rating"


class GuidanceRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    section: str = Field(description="Section grouping for related questions.")
    question_type: QuestionType = Field(description="Controlled-vocabulary question type.")
    guidance: str = Field(description="Instruction to the LLM on what to ask and why.")
    example: str | None = Field(default=None, description="Optional example wording.")
    required: bool = Field(default=False, description="Whether the LLM must include this row.")
    notes: str | None = Field(default=None, description="Optional author notes.")


class ChannelSection(BaseModel):
    heading: str = Field(description="Section heading as it should appear in the questionnaire.")
    rows: list[GuidanceRow] = Field(description="Guidance rows for this section, in order.")


class ChannelGuide(BaseModel):
    name: str = Field(description="Channel name (matches the Excel sheet name).")
    sections: list[ChannelSection] = Field(description="Sections for the channel, in order.")

    @property
    def total_rows(self) -> int:
        return sum(len(s.rows) for s in self.sections)
