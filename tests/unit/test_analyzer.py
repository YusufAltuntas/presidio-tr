from presidio_tr import build_analyzer


def test_build_analyzer_detects_all_turkish_entities_in_one_text():
    text = "TC 10000000146, VKN 1234567890, IBAN TR330006100519786457841326, tel 0532 123 45 67."
    results = build_analyzer().analyze(text, language="tr")
    found = {(r.entity_type, text[r.start : r.end], r.score) for r in results}
    assert found == {
        ("TR_NATIONAL_ID", "10000000146", 1.0),
        ("TR_TAX_ID", "1234567890", 1.0),
        ("IBAN_CODE", "TR330006100519786457841326", 1.0),
        ("PHONE_NUMBER", "0532 123 45 67", 1.0),
    }


def test_build_analyzer_keeps_context_tier_score():
    text = "Cep: 5321234567"
    results = build_analyzer().analyze(text, language="tr")
    assert [(r.entity_type, text[r.start : r.end], r.score) for r in results] == [("PHONE_NUMBER", "5321234567", 0.6)]


def test_build_analyzer_returns_nothing_for_text_without_pii():
    assert build_analyzer().analyze("Kargonuz yarın teslim edilecek.", language="tr") == []


def test_build_analyzer_explanation_score_matches_result_score():
    results = build_analyzer().analyze("TC 10000000146", language="tr", return_decision_process=True)
    assert len(results) == 1
    assert results[0].score == 1.0
    assert results[0].analysis_explanation.score == 1.0


def test_build_analyzer_ignores_bare_number_next_to_false_friend_words():
    text = "Telif hakkı 2024 tarihli 5321234567 numaralı dosya"
    assert build_analyzer().analyze(text, language="tr") == []


def test_build_analyzer_masks_valid_vkn_with_compound_context_word():
    text = "VKNo: 1234567890"
    results = build_analyzer().analyze(text, language="tr")
    assert [(r.entity_type, text[r.start : r.end], r.score) for r in results] == [("TR_TAX_ID", "1234567890", 1.0)]


def test_build_analyzer_masks_email_and_credit_card():
    text = "E-posta ayse.yilmaz@example.com, kart 4111 1111 1111 1111."
    results = build_analyzer().analyze(text, language="tr")
    found = {(r.entity_type, text[r.start : r.end], r.score) for r in results}
    assert found == {
        ("EMAIL_ADDRESS", "ayse.yilmaz@example.com", 1.0),
        ("CREDIT_CARD", "4111 1111 1111 1111", 1.0),
    }


def test_build_analyzer_ignores_card_shaped_number_failing_luhn():
    assert build_analyzer().analyze("Kart 4111 1111 1111 1112", language="tr") == []
