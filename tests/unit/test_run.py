import datetime
from pathlib import Path

from benchmark.run import report_path, score, turkish_predictor, vanilla_turkish_predictor

ROWS = [
    {
        "text": "TC 10000000146 sipariş 48213390571",
        "spans": [{"start": 3, "end": 14, "entity": "TR_NATIONAL_ID"}],
        "negatives": [{"start": 23, "end": 34}],
    }
]


def test_score_counts_typed_match_as_true_positive():
    counts, overmask = score(ROWS, lambda text: [(3, 14, "TR_NATIONAL_ID")])
    c = counts["TR_NATIONAL_ID"]
    assert (c.tp, c.fp, c.fn, c.masked) == (1, 0, 0, 1)
    assert overmask == 0.0


def test_score_counts_wrong_type_as_masked_but_not_recalled():
    counts, overmask = score(ROWS, lambda text: [(3, 14, "US_BANK_NUMBER"), (23, 34, "US_BANK_NUMBER")])
    c = counts["TR_NATIONAL_ID"]
    assert (c.tp, c.fn, c.masked) == (0, 1, 1)
    assert overmask == 1.0


def test_score_counts_unmatched_prediction_as_false_positive():
    counts, _ = score(ROWS, lambda text: [(23, 34, "TR_NATIONAL_ID")])
    assert counts["TR_NATIONAL_ID"].fp == 1


def test_vanilla_turkish_predictor_detects_valid_tckn_as_national_id():
    text = "TC kimlik no 10000000146"
    spans = vanilla_turkish_predictor()(text)
    assert any(entity == "TR_NATIONAL_ID" and text[start:end] == "10000000146" for start, end, entity in spans)


def test_vanilla_turkish_predictor_uses_turkish_phone_region():
    # Varsayılan bölgelerle (US…) bu VKN telefon sayılır; TR bölgesiyle sayılmaz.
    spans = vanilla_turkish_predictor()("VKN: 1234567890")
    assert not [s for s in spans if s[2] == "PHONE_NUMBER"]


def test_turkish_predictor_threshold_drops_context_tier():
    text = "Cep: 5321234567"
    assert turkish_predictor()(text) == [(5, 15, "PHONE_NUMBER")]
    assert turkish_predictor(score_threshold=0.7)(text) == []


def test_report_path_appends_tag_to_date():
    today = datetime.date.today().isoformat()
    assert report_path(Path("r")) == Path("r") / f"{today}.md"
    assert report_path(Path("r"), "heldout") == Path("r") / f"{today}-heldout.md"


def test_score_ignores_predictions_on_unmeasured_spans():
    rows = [{"text": "Adres 1234567890", "spans": [], "negatives": [], "ignore": [{"start": 6, "end": 16}]}]
    counts, _ = score(rows, lambda text: [(6, 16, "TR_TAX_ID")])
    assert counts["TR_TAX_ID"].fp == 0
