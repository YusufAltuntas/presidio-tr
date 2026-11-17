"""Üçüncü taraf Türkçe PII setlerini indirir ve benchmark JSONL biçimine çevirir.

Setler Hugging Face'ten sabit bir sürümle (commit) indirilir; veri `benchmark/data/` altında kalır, git'e girmez.
Ölçülmeyen türler (adres, plaka, sağlık…) `ignore` aralığı olur: üzerlerine düşen tahmin ne TP ne FP sayılır.

Kullanım: python -m benchmark.external && python -m benchmark.run --data benchmark/data/external/<ad>.jsonl --tag <ad>
"""

import argparse
import csv
import io
import json
import re
from collections.abc import Callable
from pathlib import Path

import httpx

OUT_DIR = Path("benchmark/data/external")

# Kaynak etiketi → benchmark varlığı. Listede olmayan etiketler `ignore` olur.
CAGRI_TAGS = {
    "AD": "PERSON",
    "TCKN": "TR_NATIONAL_ID",
    "VERGI_NO": "TR_TAX_ID",
    "IBAN": "IBAN_CODE",
    "TEL": "PHONE_NUMBER",
    "EMAIL": "EMAIL_ADDRESS",
    "KART": "CREDIT_CARD",
}
BTX_LABELS = {
    "private_person": "PERSON",
    "tckn": "TR_NATIONAL_ID",
    "vkn": "TR_TAX_ID",
    "iban": "IBAN_CODE",
    "private_phone": "PHONE_NUMBER",
    "private_email": "EMAIL_ADDRESS",
}
FEVZI_TYPES = {
    "TCKN": "TR_NATIONAL_ID",
    "VKN": "TR_TAX_ID",
    "IBAN": "IBAN_CODE",
    "PHONE": "PHONE_NUMBER",
    "EMAIL": "EMAIL_ADDRESS",
    "CREDIT_CARD": "CREDIT_CARD",
}

_TAG = re.compile(r"\[([A-Z_]+)\]")
# PII olmayan uzun sayılar (sipariş no, takip kodu) yanlış maskeleme ölçümü için negatif sayılır.
_LONG_NUMBER = re.compile(r"(?<!\d)\d{10,}(?!\d)")


def _row(text: str, labelled: list[tuple[int, int, str]]) -> dict:
    """(başlangıç, bitiş, varlık-ya-da-None) listesinden satır kurar; None olanlar `ignore` olur."""
    spans = [{"start": s, "end": e, "entity": ent} for s, e, ent in labelled if ent is not None]
    ignore = [{"start": s, "end": e} for s, e, ent in labelled if ent is None]
    taken = [(s, e) for s, e, _ in labelled]
    negatives = [
        {"start": m.start(), "end": m.end()}
        for m in _LONG_NUMBER.finditer(text)
        if not any(m.start() < e and s < m.end() for s, e in taken)
    ]
    return {"text": text, "spans": spans, "negatives": negatives, "ignore": ignore}


def align_masked(original: str, masked: str) -> list[tuple[int, int, str]] | None:
    """Maskelenmiş metindeki `[ETIKET]`lerin orijinal metinde hangi aralığa denk geldiğini bulur.

    Eşleşme kurulamazsa None döner.
    """
    parts = _TAG.split(masked)  # [düz, etiket, düz, etiket, …, düz]
    pattern = "".join(re.escape(p) if i % 2 == 0 else "(.+?)" for i, p in enumerate(parts))
    match = re.fullmatch(pattern, original, flags=re.DOTALL)
    if match is None:
        return None
    return [(match.start(g), match.end(g), parts[2 * g - 1]) for g in range(1, len(parts) // 2 + 1)]


def convert_cagri(raw: str) -> tuple[list[dict], int]:
    """Bankacılık seti: yalnızca 'tamamını maskele' (tam) ve 'PII yok' (negatif) kategorileri."""
    rows, skipped = [], 0
    for r in csv.DictReader(io.StringIO(raw.lstrip("﻿"))):
        if r["kategori"] not in ("tam", "negatif"):
            continue
        aligned = align_masked(r["input"], r["expected_output"])
        if aligned is None:
            skipped += 1
            continue
        rows.append(_row(r["input"], [(s, e, CAGRI_TAGS.get(tag)) for s, e, tag in aligned]))
    return rows, skipped


def convert_btx(raw: str) -> tuple[list[dict], int]:
    """BTX24 test bölümü; `*` içeren (zaten maskelenmiş) değerler ölçülmez."""
    rows = []
    for line in raw.splitlines():
        r = json.loads(line)
        text = r["text"]
        rows.append(
            _row(
                text,
                [
                    (
                        lb["start"],
                        lb["end"],
                        None if "*" in text[lb["start"] : lb["end"]] else BTX_LABELS.get(lb["category"]),
                    )
                    for lb in r["label"]
                ],
            )
        )
    return rows, 0


def convert_fevzi(raw: str) -> tuple[list[dict], int]:
    rows = []
    for line in raw.splitlines():
        r = json.loads(line)
        rows.append(_row(r["text"], [(e["start"], e["end"], FEVZI_TYPES.get(e["type"])) for e in r["entities"]]))
    return rows, 0


# ad → (Hugging Face deposu, sabit sürüm, dosya, dönüştürücü, lisans)
SOURCES: dict[str, tuple[str, str, str, Callable[[str], tuple[list[dict], int]], str]] = {
    "cagrigungor": (
        "cagrigungor/turkish-pii-masking-benchmark",
        "b2e6e68b260873cda53e90e623c1fa35d74fc7eb",
        "benchmark_1000.csv",
        convert_cagri,
        "CC0-1.0",
    ),
    "btx24": (
        "BTX24/turkish-privacy-pii-ner",
        "45a8e18edb57224b14368c910f701e064dbb1326",
        "test.jsonl",
        convert_btx,
        "CC-BY-4.0",
    ),
    "fevziegeyurtsevenler": (
        "fevziegeyurtsevenler/turkish-pii-corpus",
        "2e770a8321133c6cc135f6cb3f8cd2212ea76604",
        "pii_corpus.jsonl",
        convert_fevzi,
        "Apache-2.0",
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, (repo, revision, filename, convert, license_id) in SOURCES.items():
        raw_path = args.out_dir / f"{name}__{filename}"
        if not raw_path.exists():
            url = f"https://huggingface.co/datasets/{repo}/resolve/{revision}/{filename}"
            raw_path.write_bytes(httpx.get(url, follow_redirects=True, timeout=60).raise_for_status().content)
        rows, skipped = convert(raw_path.read_text(encoding="utf-8"))
        out = args.out_dir / f"{name}.jsonl"
        out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        print(f"{name}: {len(rows)} satır ({skipped} hizalanamadı), lisans {license_id} → {out}")


if __name__ == "__main__":
    main()
