import random

import pytest
from stdnum.tr import tckimlik, vkn

from presidio_tr.validators import tckn_valid, tr_iban_valid, tr_phone_valid, vkn_valid


@pytest.mark.parametrize("value", ["10000000146", "12345678950"])
def test_tckn_valid_accepts_known_valid_numbers(value):
    assert tckn_valid(value)


@pytest.mark.parametrize(
    "value",
    ["10000000147", "02345678950", "1000000014", "100000001460", "1000000014a", ""],
)
def test_tckn_valid_rejects_invalid_numbers(value):
    assert not tckn_valid(value)


def test_tckn_valid_matches_python_stdnum_reference():
    rng = random.Random(0)
    for _ in range(20_000):
        value = str(rng.randint(10**10, 10**11 - 1))
        assert tckn_valid(value) == tckimlik.is_valid(value), value


def test_vkn_valid_matches_python_stdnum_reference():
    rng = random.Random(0)
    for _ in range(20_000):
        value = "".join(rng.choice("0123456789") for _ in range(10))
        assert vkn_valid(value) == vkn.is_valid(value), value


@pytest.mark.parametrize("value", ["123456789", "12345678901", "123456789a"])
def test_vkn_valid_rejects_wrong_shape(value):
    assert not vkn_valid(value)


@pytest.mark.parametrize(
    "value",
    ["TR330006100519786457841326", "TR33 0006 1005 1978 6457 8413 26", "tr330006100519786457841326"],
)
def test_tr_iban_valid_accepts_valid_iban_in_any_spacing_or_case(value):
    assert tr_iban_valid(value)


@pytest.mark.parametrize(
    "value",
    ["TR330006100519786457841327", "DE89370400440532013000", "TR33000610051978645784132"],
)
def test_tr_iban_valid_rejects_invalid_iban(value):
    assert not tr_iban_valid(value)


@pytest.mark.parametrize(
    "value",
    ["+90 532 123 45 67", "0532 123 4567", "05321234567", "+902121234567", "00905321234567", "0090 532 123 45 67"],
)
def test_tr_phone_valid_accepts_prefixed_numbers(value):
    assert tr_phone_valid(value)


@pytest.mark.parametrize("value", ["5321234567", "0632 123 4567", "+90 132 123 45 67", "123", "0090 132 123 45 67"])
def test_tr_phone_valid_rejects_bare_or_malformed_numbers(value):
    assert not tr_phone_valid(value)
