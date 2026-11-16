"""Elle yazılmış cümleleri (`benchmark/handwritten.txt`) benchmark JSONL'ine çevirir.

Biçim: satır başına bir cümle; kişisel veri `[değer](VARLIK)` ile işaretlenir. VARLIK: TR_NATIONAL_ID, TR_TAX_ID,
IBAN_CODE, PHONE_NUMBER, PERSON ya da NEGATIVE (PII'ye benzeyen ama PII olmayan sayı). `#` ile başlayan ve boş
satırlar atlanır.

Kullanım: python -m benchmark.handwritten && python -m benchmark.run --data benchmark/data/tr_pii_handwritten.jsonl --tag handwritten
"""

import argparse
import json
import re
from pathlib import Path

from benchmark.generate import NEGATIVE
from benchmark.run import ENTITIES

_MARK = re.compile(r"\[([^\]]+)\]\(([A-Z_]+)\)")


def parse_line(line: str) -> dict:
    """İşaretli cümleyi düz metne çevirir ve işaretli değerlerin karakter aralıklarını etiketler."""
    text, spans, negatives, pos = "", [], [], 0
    for m in _MARK.finditer(line):
        value, label = m.group(1), m.group(2)
        if label != NEGATIVE and label not in ENTITIES:
            raise ValueError(f"Bilinmeyen etiket {label!r}: {line}")
        text += line[pos : m.start()]
        target = negatives if label == NEGATIVE else spans
        span = {"start": len(text), "end": len(text) + len(value)}
        target.append(span if label == NEGATIVE else {**span, "entity": label})
        text += value
        pos = m.end()
    return {"text": text + line[pos:], "spans": spans, "negatives": negatives}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, default=Path("benchmark/handwritten.txt"))
    parser.add_argument("--out", type=Path, default=Path("benchmark/data/tr_pii_handwritten.jsonl"))
    args = parser.parse_args()
    lines = [ln.strip() for ln in args.src.read_text(encoding="utf-8").splitlines()]
    rows = [parse_line(ln) for ln in lines if ln and not ln.startswith("#")]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"{len(rows)} cümle yazıldı: {args.out}")


if __name__ == "__main__":
    main()
