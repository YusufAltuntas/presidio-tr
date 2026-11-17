# Benchmark — 2026-11-17

Veri: `benchmark/data/external/fevziegeyurtsevenler.jsonl` (155 sentetik cümle). Maskelenen: türü yanlış da olsa bir tahminle örtülen PII oranı.

| Sistem | Varlık | Precision | Recall | F1 | Maskelenen |
|---|---|---|---|---|---|
| Presidio (en, varsayılan) | TR_NATIONAL_ID | 0.00 | 0.00 | 0.00 | 1.00 |
| Presidio (en, varsayılan) | TR_TAX_ID | 0.00 | 0.00 | 0.00 | 1.00 |
| Presidio (en, varsayılan) | IBAN_CODE | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio (en, varsayılan) | PHONE_NUMBER | 0.45 | 1.00 | 0.62 | 1.00 |
| Presidio (en, varsayılan) | EMAIL_ADDRESS | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio (en, varsayılan) | CREDIT_CARD | 0.87 | 1.00 | 0.93 | 1.00 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | TR_NATIONAL_ID | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | TR_TAX_ID | 0.00 | 0.00 | 0.00 | 0.10 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | IBAN_CODE | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | PHONE_NUMBER | 0.91 | 1.00 | 0.95 | 1.00 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | EMAIL_ADDRESS | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | CREDIT_CARD | 0.00 | 0.00 | 0.00 | 0.00 |
| Presidio + presidio-tr | TR_NATIONAL_ID | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr | TR_TAX_ID | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr | IBAN_CODE | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr | PHONE_NUMBER | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr | EMAIL_ADDRESS | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr | CREDIT_CARD | 0.87 | 1.00 | 0.93 | 1.00 |
| Presidio + presidio-tr (score_threshold=0.7) | TR_NATIONAL_ID | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr (score_threshold=0.7) | TR_TAX_ID | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr (score_threshold=0.7) | IBAN_CODE | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr (score_threshold=0.7) | PHONE_NUMBER | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr (score_threshold=0.7) | EMAIL_ADDRESS | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr (score_threshold=0.7) | CREDIT_CARD | 0.87 | 1.00 | 0.93 | 1.00 |
| Presidio + presidio-tr + NER | TR_NATIONAL_ID | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr + NER | TR_TAX_ID | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr + NER | IBAN_CODE | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr + NER | PHONE_NUMBER | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr + NER | EMAIL_ADDRESS | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr + NER | CREDIT_CARD | 0.87 | 1.00 | 0.93 | 1.00 |

| Sistem | Yanlış maskeleme (PII olmayan sayılar) |
|---|---|
| Presidio (en, varsayılan) | 1.00 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | 0.00 |
| Presidio + presidio-tr | 0.00 |
| Presidio + presidio-tr (score_threshold=0.7) | 0.00 |
| Presidio + presidio-tr + NER | 0.00 |
