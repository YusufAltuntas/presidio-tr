import pytest

from presidio_tr.context import IBAN_STEMS, PHONE_STEMS, TCKN_STEMS, VKN_STEMS, has_context, tr_lower


def test_tr_lower_follows_turkish_casing():
    assert tr_lower("IBAN İL") == "ıban il"


@pytest.mark.parametrize(
    ("text", "stems"),
    [
        ("Hesabıma yatırın: X", IBAN_STEMS),  # ünsüz yumuşaması: hesap → hesab
        ("IBAN'ımı yazıyorum: X", IBAN_STEMS),
        ("TC'm X", TCKN_STEMS),
        ("T.C. no: X", TCKN_STEMS),
        ("Kimliğimdeki numara X", TCKN_STEMS),  # kimlik → kimliğ
        ("X numaralı kimlik", TCKN_STEMS),  # bağlam sonra da gelebilir
        ("VKN'miz X", VKN_STEMS),  # kısa kök kesme işaretinden sonra da tam kelime
        ("Tel: X", PHONE_STEMS),
        ("Cep: X", PHONE_STEMS),
        ("Bana X numarasından ulaşabilirsiniz", PHONE_STEMS),
        ("Ulaşın: X", PHONE_STEMS),
    ],
)
def test_has_context_finds_inflected_context_words(text, stems):
    start = text.index("X")
    assert has_context(text, start, start + 1, stems)


def test_has_context_ignores_unrelated_words():
    text = "Sipariş numaranız X, kargoya verildi."
    start = text.index("X")
    assert not has_context(text, start, start + 1, TCKN_STEMS)


def test_has_context_ignores_words_outside_window():
    text = "kimlik " + "a" * 60 + " X"
    start = text.index("X")
    assert not has_context(text, start, start + 1, TCKN_STEMS)


def test_has_context_handles_uppercase_acronyms_and_turkish_capitals():
    for text, stems in [("IBAN: X", IBAN_STEMS), ("KİMLİK NO: X", TCKN_STEMS)]:
        start = text.index("X")
        assert has_context(text, start, start + 1, stems), text


@pytest.mark.parametrize("text", ["Telif hakkı X", "Telaşla X", "Cephe X", "Ulaşım kartı X"])
def test_has_context_ignores_words_that_only_share_a_short_prefix(text):
    start = text.index("X")
    assert not has_context(text, start, start + 1, PHONE_STEMS)
