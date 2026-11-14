import random

from faker import Faker

from benchmark.generate import TEMPLATES, generate, render


def test_render_labels_pii_spans_and_negatives():
    row = render("TC {tckn}, sipariş {order_no}.", random.Random(0), Faker("tr_TR"))
    (span,) = row["spans"]
    (negative,) = row["negatives"]
    assert span["entity"] == "TR_NATIONAL_ID"
    assert row["text"][span["start"] : span["end"]].isdigit()
    assert len(row["text"][negative["start"] : negative["end"]]) == 11


def test_generate_is_deterministic_for_a_seed():
    assert generate(20, seed=7) == generate(20, seed=7)


def test_every_template_renders():
    rng, fake = random.Random(0), Faker("tr_TR")
    for template in TEMPLATES:
        row = render(template, rng, fake)
        assert "{" not in row["text"]
        for span in row["spans"] + row["negatives"]:
            assert 0 <= span["start"] < span["end"] <= len(row["text"])
