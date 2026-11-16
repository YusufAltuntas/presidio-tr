"""Microsoft Presidio için Türkçe PII tanıyıcıları (resmi olmayan topluluk paketi)."""

import spacy
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import SpacyNlpEngine
from presidio_analyzer.predefined_recognizers import CreditCardRecognizer, EmailRecognizer

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


def build_analyzer(*, ner: bool = False) -> AnalyzerEngine:
    """Türkçe tanıyıcılarla `language="tr"` için hazır bir AnalyzerEngine kurar.

    Presidio'nun dilden bağımsız e-posta ve kredi kartı tanıyıcıları da eklenir; bunlar `tr` registry'sine
    kendiliğinden gelmez. Hazır telefon ve tarih tanıyıcıları bilerek eklenmez: Türkçe metinde sipariş/referans
    numaralarını yanlış maskeliyorlar.

    `ner=True` isim tanımayı (PERSON) da açar; `presidio-tr[ner]` ekini ister (bkz. `presidio_tr.ner`).
    """
    nlp_engine = BlankTurkishNlpEngine()
    nlp_engine.load()
    registry = add_turkish_recognizers(RecognizerRegistry(supported_languages=[LANGUAGE]))
    registry.add_recognizer(EmailRecognizer(supported_language=LANGUAGE))
    registry.add_recognizer(CreditCardRecognizer(supported_language=LANGUAGE))
    if ner:
        from presidio_tr.ner import TurkishPersonRecognizer

        registry.add_recognizer(TurkishPersonRecognizer())
    return AnalyzerEngine(registry=registry, nlp_engine=nlp_engine, supported_languages=[LANGUAGE])
