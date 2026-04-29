from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Protocol

from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config import Settings
from ..errors import TranslationError
from ..logging_setup import traced_tool
from ..models import Question, RenderRequest, Section


class TranslatorProtocol(Protocol):
    def translate(self, text: str) -> str:
        ...


def translate_text_blocks_tool(
    settings: Settings,
    blocks: list[str],
    target_language: str,
    source_language: str = "en",
) -> list[str]:
    @traced_tool("translate_text_blocks")
    def _impl() -> list[str]:
        if not blocks:
            return []
        target = target_language.strip().lower()
        source = source_language.strip().lower()
        if target == source:
            return list(blocks)

        translator = _get_translator(source=source, target=target)
        return _translate_with_timeout(blocks, translator, settings.translation_timeout_s)

    return _impl()


def _get_translator(source: str, target: str) -> TranslatorProtocol:
    try:
        from deep_translator import GoogleTranslator
    except ImportError as err:
        raise TranslationError("deep-translator is not installed.") from err
    return GoogleTranslator(source=source, target=target)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _translate_one(translator: TranslatorProtocol, text: str) -> str:
    if not text or not text.strip():
        return text
    return translator.translate(text)


def _translate_with_timeout(
    blocks: list[str], translator: TranslatorProtocol, timeout_s: int
) -> list[str]:
    results: list[str] = [""] * len(blocks)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(_translate_one, translator, text): index
            for index, text in enumerate(blocks)
        }
        try:
            for future, index in futures.items():
                results[index] = future.result(timeout=timeout_s)
        except FuturesTimeoutError as err:
            raise TranslationError(
                f"Translation timed out after {timeout_s}s."
            ) from err
        except RetryError as err:
            raise TranslationError(
                f"Translation failed after retries: {err.last_attempt.exception()}"
            ) from err
        except Exception as err:
            raise TranslationError(f"Translation backend error: {err}") from err
    return results


def translate_questionnaire_tool(
    settings: Settings,
    payload: RenderRequest,
    target_language: str,
    source_language: str = "en",
) -> RenderRequest:
    """Translate a fully-composed RenderRequest into another language while preserving
    structure (section count, question order, options count, required flags). The
    returned RenderRequest can be rendered directly via render_questionnaire_docx.

    The agent should usually translate idiomatically itself; this is a fallback for
    bulk pipelines or when consistency with a glossary matters more than nuance."""

    @traced_tool("translate_questionnaire")
    def _impl() -> RenderRequest:
        target = target_language.strip().lower()
        source = source_language.strip().lower()
        if target == source:
            return payload.model_copy()

        all_strings: list[str] = [payload.title]
        for section in payload.sections:
            all_strings.append(section.heading)
            for question in section.questions:
                all_strings.append(question.text)
                if question.options:
                    all_strings.extend(question.options)

        translated = translate_text_blocks_tool(
            settings,
            blocks=all_strings,
            target_language=target,
            source_language=source,
        )

        cursor = 0
        translated_title = translated[cursor]
        cursor += 1

        new_sections: list[Section] = []
        for section in payload.sections:
            new_heading = translated[cursor]
            cursor += 1
            new_questions: list[Question] = []
            for question in section.questions:
                new_text = translated[cursor]
                cursor += 1
                new_options: list[str] | None = None
                if question.options:
                    n = len(question.options)
                    new_options = translated[cursor : cursor + n]
                    cursor += n
                new_questions.append(
                    Question(
                        text=new_text,
                        type=question.type,
                        options=new_options,
                        required=question.required,
                    )
                )
            new_sections.append(Section(heading=new_heading, questions=new_questions))

        return RenderRequest(
            title=translated_title,
            language=target,
            country_code=payload.country_code,
            company_name=payload.company_name,
            sections=new_sections,
            extra_placeholders={**payload.extra_placeholders, "LANGUAGE": target},
        )

    return _impl()
