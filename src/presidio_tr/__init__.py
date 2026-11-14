"""Microsoft Presidio için Türkçe PII tanıyıcıları (resmi olmayan topluluk paketi)."""

import spacy
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import SpacyNlpEngine

from presidio_tr.recognizers import all_recognizers

LANGUAGE = "tr"


class BlankTurkishNlpEngine(SpacyNlpEngine):
    """Model indirmeden çalışan Türkçe spaCy motoru.

    v1 tanıyıcıları regex tabanlı ve NLP çıktısı kullanmıyor; Presidio yine de
    dil başına bir motor istediği için boş (blank) Türkçe pipeline yeterli.
    """

    def __init__(self) -> None:
        super().__init__(models=[{"lang_code": LANGUAGE, "model_name": "blank"}])

    def load(self) -> None:
        self.nlp = {LANGUAGE: spacy.blank(LANGUAGE)}


def add_turkish_recognizers(registry: RecognizerRegistry) -> RecognizerRegistry:
    """Türkçe tanıyıcıları verilen registry'ye ekler ve registry'yi döndürür."""
    for recognizer in all_recognizers():
        registry.add_recognizer(recognizer)
    return registry


def build_analyzer() -> AnalyzerEngine:
    """Türkçe tanıyıcılarla `language="tr"` için hazır bir AnalyzerEngine kurar."""
    nlp_engine = BlankTurkishNlpEngine()
    nlp_engine.load()
    registry = add_turkish_recognizers(RecognizerRegistry(supported_languages=[LANGUAGE]))
    return AnalyzerEngine(registry=registry, nlp_engine=nlp_engine, supported_languages=[LANGUAGE])
