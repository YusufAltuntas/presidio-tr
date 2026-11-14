"""Varsayılan Presidio (en), Türkçe kurulmuş Presidio ve Presidio + presidio-tr'yi aynı veri üzerinde karşılaştırır.

Kullanım: python -m benchmark.run --data benchmark/data/tr_pii.jsonl --out-dir benchmark/results
"""

import argparse
import datetime
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import TrNationalIdRecognizer

from presidio_tr import BlankTurkishNlpEngine, build_analyzer

ENTITIES = ("TR_NATIONAL_ID", "TR_TAX_ID", "IBAN_CODE", "PHONE_NUMBER")

Span = tuple[int, int, str]


@dataclass
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    masked: int = 0  # türü ne olursa olsun bir tahminle örtülen altın aralık sayısı

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0

    @property
    def masked_rate(self) -> float:
        return self.masked / (self.tp + self.fn) if self.tp + self.fn else 0.0


def overlaps(a: Span, b: Span) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def score(rows: list[dict], predict: Callable[[str], list[Span]]) -> tuple[dict[str, Counts], float]:
    """Varlık türü başına TP/FP/FN, tür gözetmeyen maskeleme oranı ve yanlış maskeleme oranı.

    Bir altın aralık, aynı türden ve onunla çakışan bir tahmin varsa TP sayılır.
    Yanlış maskeleme: PII olmayan sayıların (sipariş no, referans no) bir tahminle örtülme oranı.
    """
    counts = {entity: Counts() for entity in ENTITIES}
    negatives_total = negatives_masked = 0
    for row in rows:
        gold = [(s["start"], s["end"], s["entity"]) for s in row["spans"]]
        preds = predict(row["text"])
        for g in gold:
            c = counts[g[2]]
            if any(p[2] == g[2] and overlaps(p, g) for p in preds):
                c.tp += 1
            else:
                c.fn += 1
            if any(overlaps(p, g) for p in preds):
                c.masked += 1
        for p in preds:
            if p[2] in counts and not any(g[2] == p[2] and overlaps(p, g) for g in gold):
                counts[p[2]].fp += 1
        for n in row["negatives"]:
            negatives_total += 1
            if any(overlaps(p, (n["start"], n["end"], "")) for p in preds):
                negatives_masked += 1
    return counts, (negatives_masked / negatives_total if negatives_total else 0.0)


def baseline_predictor() -> Callable[[str], list[Span]]:
    """Türkçe desteği olmayan kullanıcının elindeki Presidio: hazır tanıyıcılar, language=en."""
    provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
    )
    analyzer = AnalyzerEngine(nlp_engine=provider.create_engine())
    return lambda text: [(r.start, r.end, r.entity_type) for r in analyzer.analyze(text, language="en")]


def vanilla_turkish_predictor() -> Callable[[str], list[Span]]:
    """Adil taban çizgisi: Türkçe motor, Presidio'nun hazır tanıyıcıları ve kendi TrNationalIdRecognizer'ı.

    TrNationalIdRecognizer presidio-analyzer'da varsayılan olarak kapalı gelir; burada elle eklenir.
    """
    nlp_engine = BlankTurkishNlpEngine()
    nlp_engine.load()
    registry = RecognizerRegistry(supported_languages=["tr"])
    registry.load_predefined_recognizers(languages=["tr"], nlp_engine=nlp_engine)
    registry.add_recognizer(TrNationalIdRecognizer())
    analyzer = AnalyzerEngine(registry=registry, nlp_engine=nlp_engine, supported_languages=["tr"])
    return lambda text: [(r.start, r.end, r.entity_type) for r in analyzer.analyze(text, language="tr")]


def turkish_predictor() -> Callable[[str], list[Span]]:
    analyzer = build_analyzer()
    return lambda text: [(r.start, r.end, r.entity_type) for r in analyzer.analyze(text, language="tr")]


def to_markdown(results: dict[str, tuple[dict[str, Counts], float]], n_rows: int, data_path: Path) -> str:
    lines = [
        f"# Benchmark — {datetime.date.today().isoformat()}",
        "",
        f"Veri: `{data_path}` ({n_rows} sentetik cümle). "
        "Maskelenen: türü yanlış da olsa bir tahminle örtülen PII oranı.",
        "",
        "| Sistem | Varlık | Precision | Recall | F1 | Maskelenen |",
        "|---|---|---|---|---|---|",
    ]
    for system, (counts, _) in results.items():
        for entity, c in counts.items():
            lines.append(
                f"| {system} | {entity} | {c.precision:.2f} | {c.recall:.2f} | {c.f1:.2f} | {c.masked_rate:.2f} |"
            )
    lines += ["", "| Sistem | Yanlış maskeleme (PII olmayan sayılar) |", "|---|---|"]
    for system, (_, overmask) in results.items():
        lines.append(f"| {system} | {overmask:.2f} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("benchmark/data/tr_pii.jsonl"))
    parser.add_argument("--out-dir", type=Path, default=Path("benchmark/results"))
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.data.read_text(encoding="utf-8").splitlines()]
    results = {
        "Presidio (en, varsayılan)": score(rows, baseline_predictor()),
        "Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer)": score(rows, vanilla_turkish_predictor()),
        "Presidio + presidio-tr": score(rows, turkish_predictor()),
    }
    report = to_markdown(results, len(rows), args.data)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"{datetime.date.today().isoformat()}.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"Yazıldı: {out}")


if __name__ == "__main__":
    main()
