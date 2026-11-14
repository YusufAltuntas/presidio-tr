from presidio_tr import build_analyzer


def test_build_analyzer_detects_all_turkish_entities_in_one_text():
    text = "TC 10000000146, VKN 1234567890, IBAN TR330006100519786457841326, tel 0532 123 45 67."
    results = build_analyzer().analyze(text, language="tr")
    found = {(r.entity_type, text[r.start : r.end]) for r in results}
    assert found == {
        ("TR_NATIONAL_ID", "10000000146"),
        ("TR_TAX_ID", "1234567890"),
        ("IBAN_CODE", "TR330006100519786457841326"),
        ("PHONE_NUMBER", "0532 123 45 67"),
    }


def test_build_analyzer_returns_nothing_for_text_without_pii():
    assert build_analyzer().analyze("Kargonuz yarın teslim edilecek.", language="tr") == []
