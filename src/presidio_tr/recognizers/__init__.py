"""Türkçe PII tanıyıcıları."""

from presidio_analyzer import Pattern

from presidio_tr.context import IBAN_STEMS, PHONE_STEMS, TCKN_STEMS, VKN_STEMS
from presidio_tr.recognizers.base import TurkishPatternRecognizer
from presidio_tr.validators import tckn_valid, tr_iban_valid, tr_phone_valid, vkn_valid

TCKN_REGEX = r"(?<!\d)[1-9]\d{10}(?!\d)"
VKN_REGEX = r"(?<!\d)\d{10}(?!\d)"
IBAN_REGEX = r"(?<![A-Za-z0-9])TR\d{2}(?:\s?\d{4}){5}\s?\d{2}(?!\d)"
PHONE_REGEX = r"(?<![\d+])(?:(?:\+|00)?90[\s-]?|0[\s-]?)?\(?[2-5]\d{2}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"


class TcKimlikRecognizer(TurkishPatternRecognizer):
    def __init__(self) -> None:
        super().__init__("TR_NATIONAL_ID", [Pattern("tckn", TCKN_REGEX, 0.5)], tckn_valid, TCKN_STEMS)


class VknRecognizer(TurkishPatternRecognizer):
    def __init__(self) -> None:
        super().__init__("TR_TAX_ID", [Pattern("vkn", VKN_REGEX, 0.5)], vkn_valid, VKN_STEMS, requires_context=True)


class TrIbanRecognizer(TurkishPatternRecognizer):
    def __init__(self) -> None:
        super().__init__("IBAN_CODE", [Pattern("tr_iban", IBAN_REGEX, 0.5)], tr_iban_valid, IBAN_STEMS)


class TrPhoneRecognizer(TurkishPatternRecognizer):
    def __init__(self) -> None:
        super().__init__("PHONE_NUMBER", [Pattern("tr_phone", PHONE_REGEX, 0.5)], tr_phone_valid, PHONE_STEMS)


def all_recognizers() -> list[TurkishPatternRecognizer]:
    """Paketteki tüm tanıyıcıların yeni örneklerini döndürür."""
    return [TcKimlikRecognizer(), VknRecognizer(), TrIbanRecognizer(), TrPhoneRecognizer()]
