import json

from benchmark.external import align_masked, convert_btx, convert_cagri


def test_align_masked_maps_each_tag_to_its_original_span():
    original = "müşteri Ayşe Kılıç tc 10000000146 aradı"
    spans = align_masked(original, "müşteri [AD] tc [TCKN] aradı")
    assert [(original[s:e], tag) for s, e, tag in spans] == [("Ayşe Kılıç", "AD"), ("10000000146", "TCKN")]


def test_align_masked_returns_none_when_the_texts_do_not_match():
    assert align_masked("tamamen başka bir metin", "müşteri [AD] aradı") is None


def test_convert_cagri_keeps_full_masking_rows_and_ignores_unmeasured_tags():
    raw = (
        "id,kategori,ozellikler,instruction,input,expected_output,metindeki_etiketler,maskelenecek_etiketler\n"
        '1,tam,duz,x,"Ayşe pasaport U123",[AD] pasaport [PASAPORT_NO],[AD] [PASAPORT_NO],[AD] [PASAPORT_NO]\n'
        "2,beyaz_liste,duz,x,Ayşe,[AD],[AD],\n"
    )
    rows, skipped = convert_cagri(raw)
    assert skipped == 0
    (row,) = rows
    assert [(row["text"][s["start"] : s["end"]], s["entity"]) for s in row["spans"]] == [("Ayşe", "PERSON")]
    assert [row["text"][s["start"] : s["end"]] for s in row["ignore"]] == ["U123"]


def test_convert_btx_does_not_measure_already_masked_values():
    line = {
        "text": "vergi no 753347**** ve tel 0532 123 45 67",
        "label": [
            {"category": "vkn", "start": 9, "end": 19},
            {"category": "private_phone", "start": 27, "end": 41},
        ],
    }
    (row,), _ = convert_btx(json.dumps(line, ensure_ascii=False))
    assert [s["entity"] for s in row["spans"]] == ["PHONE_NUMBER"]
    assert [row["text"][s["start"] : s["end"]] for s in row["ignore"]] == ["753347****"]
