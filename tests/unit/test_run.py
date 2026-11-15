from benchmark.run import score, turkish_predictor, vanilla_turkish_predictor

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


def test_turkish_predictor_threshold_drops_context_tier():
    text = "Cep: 5321234567"
    assert turkish_predictor()(text) == [(5, 15, "PHONE_NUMBER")]
    assert turkish_predictor(score_threshold=0.7)(text) == []
