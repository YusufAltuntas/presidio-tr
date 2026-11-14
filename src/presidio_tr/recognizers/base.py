"""Checksum + bağlam ile skorlayan ortak Türkçe tanıyıcı."""

from collections.abc import Callable

from presidio_analyzer import Pattern, PatternRecognizer, RecognizerResult

from presidio_tr.context import has_context

VALID_SCORE = 1.0
CONTEXT_SCORE = 0.6


class TurkishPatternRecognizer(PatternRecognizer):
    """Regex adaylarını üç kademeyle skorlar.

    Doğrulamadan geçen aday yüksek skor alır; geçemeyen ama yakınında bağlam
    kelimesi olan aday orta skor alır; ikisi de yoksa aday atılır.
    """

    def __init__(
        self,
        entity: str,
        patterns: list[Pattern],
        validator: Callable[[str], bool],
        context_stems: tuple[str, ...],
    ) -> None:
        self._validator = validator
        self._context_stems = context_stems
        super().__init__(
            supported_entity=entity,
            name=type(self).__name__,
            supported_language="tr",
            patterns=patterns,
        )

    def analyze(self, text, entities, nlp_artifacts=None, regex_flags=None) -> list[RecognizerResult]:
        kept = []
        for result in super().analyze(text, entities, nlp_artifacts, regex_flags):
            candidate = text[result.start : result.end]
            if self._validator(candidate):
                result.score = VALID_SCORE
            elif has_context(text, result.start, result.end, self._context_stems):
                result.score = CONTEXT_SCORE
            else:
                continue
            kept.append(result)
        return kept
