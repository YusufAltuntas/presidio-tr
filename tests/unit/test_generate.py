import random

from faker import Faker

from benchmark.generate import HELDOUT_TEMPLATES, TEMPLATES, generate, render


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


def test_date_depends_only_on_rng():
    first = render("{date}", random.Random(1), Faker("tr_TR"))
    fake = Faker("tr_TR")
    fake.seed_instance(999)
    assert render("{date}", random.Random(1), fake) == first


def test_every_heldout_template_renders():
    rng, fake = random.Random(0), Faker("tr_TR")
    for template in HELDOUT_TEMPLATES:
        row = render(template, rng, fake)
        assert "{" not in row["text"]
        for span in row["spans"] + row["negatives"]:
            assert 0 <= span["start"] < span["end"] <= len(row["text"])


def test_heldout_templates_are_disjoint_from_main_templates():
    assert not set(HELDOUT_TEMPLATES) & set(TEMPLATES)


def test_generate_uses_given_template_set():
    rows = generate(30, seed=3, templates=["Sadece {order_no}."])
    assert all(row["text"].startswith("Sadece ") for row in rows)


def test_render_labels_name_as_person():
    row = render("Sayın {name}", random.Random(0), Faker("tr_TR"))
    (span,) = row["spans"]
    assert span["entity"] == "PERSON"
    assert row["text"][span["start"] : span["end"]] == row["text"][len("Sayın ") :]
