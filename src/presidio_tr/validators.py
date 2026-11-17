"""Türkçe kimlik ve hesap numaraları için saf doğrulama fonksiyonları."""

import re

_NON_DIGIT = re.compile(r"\D")
_WHITESPACE = re.compile(r"\s")
_TCKN_SEPARATOR = re.compile(r"[ -]")


def tckn_valid(candidate: str) -> bool:
    """TC kimlik numarasının resmi checksum kuralına uyup uymadığını döndürür; boşluk ve tire yok sayılır."""
    candidate = _TCKN_SEPARATOR.sub("", candidate)
    if len(candidate) != 11 or not candidate.isdigit() or candidate[0] == "0":
        return False
    d = [int(c) for c in candidate]
    tenth = (sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10
    eleventh = sum(d[:10]) % 10
    return d[9] == tenth and d[10] == eleventh


def vkn_valid(candidate: str) -> bool:
    """Vergi kimlik numarasının (10 hane) checksum kuralına uyup uymadığını döndürür."""
    if len(candidate) != 10 or not candidate.isdigit():
        return False
    d = [int(c) for c in candidate]
    total = 0
    for i in range(9):
        tmp = (d[i] + 9 - i) % 10
        total += 9 if tmp == 9 else (tmp * 2 ** (9 - i)) % 9
    return (10 - total % 10) % 10 == d[9]


def tr_iban_valid(candidate: str) -> bool:
    """TR IBAN'ın uzunluk, önek ve mod-97 kontrolünden geçip geçmediğini döndürür."""
    iban = _WHITESPACE.sub("", candidate).upper()
    if len(iban) != 26 or not iban.startswith("TR") or not iban[2:].isdigit():
        return False
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(str(int(ch, 36)) for ch in rearranged)
    return int(numeric) % 97 == 1


def tr_phone_valid(candidate: str) -> bool:
    """Ülke ya da alan koduyla yazılmış Türk telefon numarasını doğrular.

    Öneksiz 10 haneli numara tek başına telefon sayılmaz; bağlam gerekir.
    """
    digits = _NON_DIGIT.sub("", candidate)
    if len(digits) == 14 and digits.startswith("0090"):
        national = digits[4:]
    elif len(digits) == 12 and digits.startswith("90"):
        national = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        national = digits[1:]
    else:
        return False
    return national[0] in "2345"
