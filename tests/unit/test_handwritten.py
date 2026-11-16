import pytest

from benchmark.handwritten import parse_line


def test_parse_line_strips_marks_and_labels_spans():
    row = parse_line("merhaba ben [ayşe yılmaz](PERSON), sipariş [48213390571](NEGATIVE) gelmedi")
    assert row["text"] == "merhaba ben ayşe yılmaz, sipariş 48213390571 gelmedi"
    (span,) = row["spans"]
    (negative,) = row["negatives"]
    assert row["text"][span["start"] : span["end"]] == "ayşe yılmaz" and span["entity"] == "PERSON"
    assert row["text"][negative["start"] : negative["end"]] == "48213390571"


def test_parse_line_keeps_unmarked_sentence_as_is():
    assert parse_line("Barış görüşmeleri sürüyor.") == {
        "text": "Barış görüşmeleri sürüyor.",
        "spans": [],
        "negatives": [],
    }


def test_parse_line_rejects_unknown_label():
    with pytest.raises(ValueError):
        parse_line("[Ayşe](PER) aradı")
