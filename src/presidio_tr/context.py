"""Türkçe bağlam kelimeleri ve ek toleranslı bağlam eşleştirmesi."""

import re

TCKN_STEMS = ("tc", "tckn", "kimlik", "kimliğ", "vatandaşlık", "vatandaşlığ", "nüfus")
VKN_STEMS = ("vkn", "vergi")
IBAN_STEMS = ("iban", "hesap", "hesab")
PHONE_STEMS = ("tel", "telefon", "gsm", "cep", "whatsapp", "ulaş")

WINDOW_BEFORE = 50
WINDOW_AFTER = 30

_WORD = re.compile(r"\w+")


def tr_lower(text: str) -> str:
    """Türkçe büyük/küçük harf kurallarıyla küçültür (I→ı, İ→i)."""
    return text.replace("I", "ı").replace("İ", "i").lower()


def has_context(text: str, start: int, end: int, stems: tuple[str, ...]) -> bool:
    """Eşleşmenin çevresinde, kökü verilen kelimelerden biriyle başlayan kelime var mı.

    Kök eşleştirmesi Türkçe ekleri tolere eder: "IBAN'ımı" → "iban", "hesabıma" → "hesab".
    """
    window = (text[max(0, start - WINDOW_BEFORE) : start] + " " + text[end : end + WINDOW_AFTER]).replace(".", "")
    # Kısaltmalar Latin büyük harfle yazılır: Türkçe kuralla "IBAN" → "ıban" olur, bu yüzden iki küçültme de denenir.
    words = set(_WORD.findall(tr_lower(window))) | set(_WORD.findall(window.lower()))
    return any(word.startswith(stem) for word in words for stem in stems)
