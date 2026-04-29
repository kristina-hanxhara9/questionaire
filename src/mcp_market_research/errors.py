from __future__ import annotations


class QuestionnaireError(Exception):
    """Base class for all server errors that should map to MCP error responses."""


class ConfigurationError(QuestionnaireError):
    """Raised when settings or required files are misconfigured."""


class ChannelNotFoundError(QuestionnaireError):
    def __init__(self, channel: str, available: list[str]) -> None:
        self.channel = channel
        self.available = available
        super().__init__(
            f"Channel '{channel}' not found. Available: {', '.join(available) or '<none>'}"
        )


class ExcelGuideValidationError(QuestionnaireError):
    """Raised when the Excel guide is structurally invalid."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        joined = "; ".join(errors)
        super().__init__(f"Excel guide validation failed: {joined}")


class TemplateExtractionError(QuestionnaireError):
    """Raised when the PDF template cannot be parsed."""


class RenderingError(QuestionnaireError):
    """Raised when DOCX rendering fails."""


class TranslationError(QuestionnaireError):
    """Raised when translation fails after retries."""


class LocaleNotSupportedError(QuestionnaireError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Locale '{code}' is not recognized.")
