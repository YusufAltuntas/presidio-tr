"""Sentetik Türkçe PII değerleri üretir. Gerçek kişi verisi kullanılmaz."""

import random
from collections.abc import Callable

from presidio_tr.validators import tckn_valid, vkn_valid


def tckn(rng: random.Random) -> str:
    """Checksum'ı geçerli rastgele TC kimlik numarası."""
    d = [rng.randint(1, 9)] + [rng.randint(0, 9) for _ in range(8)]
    d.append((sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10)
    d.append(sum(d) % 10)
    return "".join(map(str, d))


def vkn(rng: random.Random) -> str:
    """Checksum'ı geçerli rastgele vergi kimlik numarası."""
    while True:
        candidate = "".join(str(rng.randint(0, 9)) for _ in range(10))
        if vkn_valid(candidate):
            return candidate


def tr_iban(rng: random.Random, spaced: bool) -> str:
    """mod-97'si geçerli rastgele TR IBAN."""
    bban = "".join(str(rng.randint(0, 9)) for _ in range(5)) + "0" + "".join(str(rng.randint(0, 9)) for _ in range(16))
    numeric = "".join(str(int(ch, 36)) for ch in bban + "TR00")
    iban = f"TR{98 - int(numeric) % 97:02d}{bban}"
    return " ".join(iban[i : i + 4] for i in range(0, 26, 4)) if spaced else iban


def phone(rng: random.Random) -> str:
    """+90 ya da 0 önekli Türk cep telefonu, rastgele yazım biçimiyle."""
    n = f"5{rng.randint(0, 5)}{rng.randint(0, 9)}{rng.randint(0, 9999999):07d}"
    return rng.choice(
        [
            f"+90 {n[:3]} {n[3:6]} {n[6:8]} {n[8:]}",
            f"0{n[:3]} {n[3:6]} {n[6:]}",
            f"0{n}",
            f"+90{n}",
        ]
    )


def bare_phone(rng: random.Random) -> str:
    """Öneksiz 10 haneli cep telefonu (bağlam olmadan telefon sayılmamalı)."""
    return f"5{rng.randint(0, 5)}{rng.randint(0, 9)}{rng.randint(0, 9999999):07d}"


def typo(value: str, rng: random.Random, still_valid: Callable[[str], bool]) -> str:
    """Bir hanesi değiştirilmiş, artık checksum'dan geçmeyen numara."""
    positions = [i for i, ch in enumerate(value) if ch.isdigit() and i > 0]
    while True:
        i = rng.choice(positions)
        candidate = value[:i] + str((int(value[i]) + rng.randint(1, 9)) % 10) + value[i + 1 :]
        if not still_valid(candidate):
            return candidate


def order_no(rng: random.Random) -> str:
    """TC kimliğe benzeyen ama checksum'dan geçmeyen 11 haneli sipariş numarası."""
    while True:
        candidate = str(rng.randint(10**10, 10**11 - 1))
        if not tckn_valid(candidate):
            return candidate
