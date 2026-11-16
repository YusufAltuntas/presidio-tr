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


def test_typo_fails_checksum():
    rng = random.Random(0)
    for _ in range(500):
        assert not tckn_valid(synth.typo(synth.tckn(rng), rng, tckn_valid))
        assert not vkn_valid(synth.typo(synth.vkn(rng), rng, vkn_valid))
        assert not tr_iban_valid(synth.typo(synth.tr_iban(rng, spaced=False), rng, tr_iban_valid))


def test_negatives_are_not_filtered_by_checksum():
    # Gerçek sipariş/referans numaraları da tesadüfen checksum'dan geçer; negatifler bunu temsil etmeli.
    rng = random.Random(0)
    order_nos = [synth.order_no(rng) for _ in range(5000)]
    ref_nos = [synth.ref_no(rng) for _ in range(5000)]
    assert all(len(n) == 11 for n in order_nos) and all(len(n) == 10 for n in ref_nos)
    assert 0.005 < sum(map(tckn_valid, order_nos)) / len(order_nos) < 0.02
    assert 0.07 < sum(map(vkn_valid, ref_nos)) / len(ref_nos) < 0.13


def test_bare_phone_is_not_valid_without_prefix():
    rng = random.Random(0)
    for _ in range(200):
        assert not tr_phone_valid(synth.bare_phone(rng))
