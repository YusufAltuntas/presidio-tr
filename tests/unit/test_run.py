from benchmark.run import score

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
