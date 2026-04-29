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
