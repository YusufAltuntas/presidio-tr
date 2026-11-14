import pytest

from presidio_tr.recognizers import (
    TcKimlikRecognizer,
    TrIbanRecognizer,
    TrPhoneRecognizer,
    VknRecognizer,
)
from presidio_tr.recognizers.base import CONTEXT_SCORE, VALID_SCORE


def _run(recognizer, text):
    entity = recognizer.supported_entities[0]
    return [(text[r.start : r.end], r.score) for r in recognizer.analyze(text, [entity])]


@pytest.mark.parametrize(
    ("recognizer", "text", "expected"),
    [
        (TcKimlikRecognizer(), "Numaram 10000000146.", [("10000000146", VALID_SCORE)]),
        (TcKimlikRecognizer(), "TC kimlik no: 10000000147", [("10000000147", CONTEXT_SCORE)]),
        (TcKimlikRecognizer(), "Sipariş no: 10000000147", []),
        (VknRecognizer(), "Firma 1234567890 ile kayıtlı.", []),
        (VknRecognizer(), "VKN: 1234567890", [("1234567890", VALID_SCORE)]),
        (VknRecognizer(), "Vergi no 1234567891", [("1234567891", CONTEXT_SCORE)]),
        (VknRecognizer(), "Referans 1234567891", []),
        (
            TrIbanRecognizer(),
            "Gönderin: TR33 0006 1005 1978 6457 8413 26.",
            [("TR33 0006 1005 1978 6457 8413 26", VALID_SCORE)],
        ),
        (TrIbanRecognizer(), "Hesabım TR330006100519786457841327", [("TR330006100519786457841327", CONTEXT_SCORE)]),
        (TrIbanRecognizer(), "IBAN TR330006100519786457841326ya", [("TR330006100519786457841326", VALID_SCORE)]),
        (
            TrIbanRecognizer(),
            "IBAN TR33 0006 1005 1978 6457 8413 26'ya yatırın",
            [("TR33 0006 1005 1978 6457 8413 26", VALID_SCORE)],
        ),
        (TrPhoneRecognizer(), "Arayın: +90 532 123 45 67", [("+90 532 123 45 67", VALID_SCORE)]),
        (TrPhoneRecognizer(), "Tel: +905321234567", [("+905321234567", VALID_SCORE)]),
        (TrPhoneRecognizer(), "Tel: 905321234567", [("905321234567", VALID_SCORE)]),
        (TrPhoneRecognizer(), "Tel: 0 (532) 123-45-67", [("0 (532) 123-45-67", VALID_SCORE)]),
        (TrPhoneRecognizer(), "Tel: 00905321234567", [("00905321234567", VALID_SCORE)]),
        (TrPhoneRecognizer(), "Tel: 0090 532 123 45 67", [("0090 532 123 45 67", VALID_SCORE)]),
        (TrPhoneRecognizer(), "Cep: 5321234567", [("5321234567", CONTEXT_SCORE)]),
        (TrPhoneRecognizer(), "Tutar 5321234567 TL", []),
    ],
)
def test_three_tier_scoring(recognizer, text, expected):
    assert _run(recognizer, text) == expected


def test_tckn_regex_does_not_match_inside_longer_numbers():
    assert _run(TcKimlikRecognizer(), "Kart 100000001460000 kimlik") == []


def test_recognizers_are_registered_for_turkish():
    assert TcKimlikRecognizer().supported_language == "tr"
