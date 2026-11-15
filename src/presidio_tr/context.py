"""Türkçe bağlam kelimeleri ve ek toleranslı bağlam eşleştirmesi."""

import re

TCKN_STEMS = ("tc", "tckn", "kimlik", "kimliğ", "vatandaşlık", "vatandaşlığ", "nüfus")
VKN_STEMS = ("vkn", "vergi")
IBAN_STEMS = ("iban", "hesap", "hesab")
PHONE_STEMS = ("tel", "telefon", "gsm", "cep", "whatsapp", "ulaşa", "ulaşın", "ulaşıl")

WINDOW_BEFORE = 50
WINDOW_AFTER = 30
# Bu uzunluktaki kökler önek olarak eşleşirse "tel" → "telif", "cep" → "cephe" gibi alakasız kelimeleri yakalar.
SHORT_STEM_MAX = 3

_WORD = re.compile(r"\w+")


def tr_lower(text: str) -> str:
    """Türkçe büyük/küçük harf kurallarıyla küçültür (I→ı, İ→i)."""
    return text.replace("I", "ı").replace("İ", "i").lower()


def _matches(word: str, stem: str) -> bool:
    """Kısa kök yalnızca kelimenin tamamıyla, uzun kök ek alabilecek önek olarak eşleşir."""
    return word == stem if len(stem) <= SHORT_STEM_MAX else word.startswith(stem)


def has_context(text: str, start: int, end: int, stems: tuple[str, ...]) -> bool:
    """Eşleşmenin çevresinde, kökü verilen kelimelerden biriyle başlayan kelime var mı.

    Kök eşleştirmesi Türkçe ekleri tolere eder: "IBAN'ımı" → "iban", "hesabıma" → "hesab".
    Kısa kökler (`tc`, `tel`, `cep`…) yalnızca tam kelimeyle eşleşir.
    """
    window = text[max(0, start - WINDOW_BEFORE) : start] + " " + text[end : end + WINDOW_AFTER]
    # Nokta hem silinir ("T.C." → "tc") hem boşluğa çevrilir ("Tel.No" → "tel no"); ikisinin kelimeleri birleştirilir.
    words: set[str] = set()
    for variant in (window.replace(".", ""), window.replace(".", " ")):
        # Kısaltmalar Latin büyük harfle yazılır: Türkçe kuralla "IBAN" → "ıban" olur, bu yüzden iki küçültme de denenir.
        words |= set(_WORD.findall(tr_lower(variant))) | set(_WORD.findall(variant.lower()))
    return any(_matches(word, stem) for word in words for stem in stems)
