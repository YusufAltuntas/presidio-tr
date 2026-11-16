"""İsim tanıma testleri; `presidio-tr[ner]` kurulu değilse atlanır (model ilk koşuda indirilir, ~440 MB)."""

import pytest

pytest.importorskip("transformers")

from presidio_tr import build_analyzer  # noqa: E402


@pytest.fixture(scope="module")
def analyzer():
    return build_analyzer(ner=True)


def _found(analyzer, text):
    return [(r.entity_type, text[r.start : r.end]) for r in analyzer.analyze(text, language="tr")]


def test_ner_masks_person_name_next_to_tckn(analyzer):
    found = _found(analyzer, "Merhaba ben Ayşe Yılmaz, TC 10000000146")
    assert ("TR_NATIONAL_ID", "10000000146") in found
    assert {span for entity, span in found if entity == "PERSON"} == {"Ayşe", "Yılmaz"}


@pytest.mark.parametrize(
    "text, name",
    [
        ("merhaba ben ayşe yılmaz, siparişim gelmedi", "ayşe yılmaz"),
        ("AHMET KAYA adına kayıtlı hesap", "AHMET KAYA"),
    ],
)
def test_ner_keeps_lower_and_upper_case_names_in_one_span(analyzer, text, name):
    assert ("PERSON", name) in _found(analyzer, text)


def test_ner_drops_location_and_organization_labels(analyzer):
    assert _found(analyzer, "Mehmet Bey'e iletir misiniz, Kadıköy şubesinden aradı") == [("PERSON", "Mehmet")]


def test_build_analyzer_without_ner_ignores_names():
    assert build_analyzer().analyze("Merhaba ben Ayşe Yılmaz", language="tr") == []
