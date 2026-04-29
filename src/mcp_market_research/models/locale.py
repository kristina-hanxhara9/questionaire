from __future__ import annotations

from pydantic import BaseModel, Field


class LocaleInfo(BaseModel):
    language: str = Field(description="ISO 639-1 language code.")
    language_native: str = Field(description="Language name in its own script.")
    country_code: str | None = Field(default=None, description="ISO 3166-1 alpha-2 country code.")
    country_name: str | None = Field(default=None)
    date_format: str = Field(default="d MMM y", description="Babel-style date pattern.")
    decimal_separator: str = Field(default=".")
    first_day_of_week: int = Field(
        default=0, description="0=Sunday, 1=Monday (matches Babel)."
    )
    rtl: bool = Field(default=False, description="True for right-to-left languages.")
