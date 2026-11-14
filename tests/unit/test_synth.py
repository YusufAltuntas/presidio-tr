import random

from benchmark import synth
from presidio_tr.validators import tckn_valid, tr_iban_valid, tr_phone_valid, vkn_valid


def test_generators_produce_valid_values():
    rng = random.Random(0)
    for _ in range(500):
        assert tckn_valid(synth.tckn(rng))
        assert vkn_valid(synth.vkn(rng))
        assert tr_iban_valid(synth.tr_iban(rng, spaced=rng.random() < 0.5))
        assert tr_phone_valid(synth.phone(rng))


def test_typo_order_no_and_ref_no_fail_checksum():
    rng = random.Random(0)
    for _ in range(500):
        assert not tckn_valid(synth.typo(synth.tckn(rng), rng, tckn_valid))
        assert not vkn_valid(synth.typo(synth.vkn(rng), rng, vkn_valid))
        assert not tr_iban_valid(synth.typo(synth.tr_iban(rng, spaced=False), rng, tr_iban_valid))
        assert not tckn_valid(synth.order_no(rng))
        assert not vkn_valid(synth.ref_no(rng))


def test_bare_phone_is_not_valid_without_prefix():
    rng = random.Random(0)
    for _ in range(200):
        assert not tr_phone_valid(synth.bare_phone(rng))
