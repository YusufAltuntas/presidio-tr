# Benchmark — 2026-11-17

Veri: `benchmark/data/external/cagrigungor.jsonl` (550 sentetik cümle). Maskelenen: türü yanlış da olsa bir tahminle örtülen PII oranı.

| Sistem | Varlık | Precision | Recall | F1 | Maskelenen |
|---|---|---|---|---|---|
| Presidio (en, varsayılan) | TR_NATIONAL_ID | 0.00 | 0.00 | 0.00 | 0.74 |
| Presidio (en, varsayılan) | TR_TAX_ID | 0.00 | 0.00 | 0.00 | 0.71 |
| Presidio (en, varsayılan) | IBAN_CODE | 0.00 | 0.00 | 0.00 | 0.63 |
| Presidio (en, varsayılan) | PHONE_NUMBER | 0.69 | 0.84 | 0.76 | 0.94 |
| Presidio (en, varsayılan) | PERSON | 0.16 | 0.53 | 0.24 | 0.79 |
| Presidio (en, varsayılan) | EMAIL_ADDRESS | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio (en, varsayılan) | CREDIT_CARD | 0.67 | 0.05 | 0.10 | 0.81 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | TR_NATIONAL_ID | 1.00 | 0.45 | 0.62 | 0.45 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | TR_TAX_ID | 0.00 | 0.00 | 0.00 | 0.14 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | IBAN_CODE | 0.00 | 0.00 | 0.00 | 0.00 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | PHONE_NUMBER | 0.94 | 0.91 | 0.92 | 0.91 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | PERSON | 0.00 | 0.00 | 0.00 | 0.00 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | EMAIL_ADDRESS | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | CREDIT_CARD | 0.00 | 0.00 | 0.00 | 0.00 |
| Presidio + presidio-tr | TR_NATIONAL_ID | 1.00 | 0.77 | 0.87 | 0.77 |
| Presidio + presidio-tr | TR_TAX_ID | 1.00 | 0.50 | 0.67 | 0.50 |
| Presidio + presidio-tr | IBAN_CODE | 1.00 | 0.44 | 0.62 | 0.44 |
| Presidio + presidio-tr | PHONE_NUMBER | 0.97 | 0.88 | 0.92 | 0.88 |
| Presidio + presidio-tr | PERSON | 0.00 | 0.00 | 0.00 | 0.00 |
| Presidio + presidio-tr | EMAIL_ADDRESS | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr | CREDIT_CARD | 0.67 | 0.05 | 0.10 | 0.05 |
| Presidio + presidio-tr (score_threshold=0.7) | TR_NATIONAL_ID | 1.00 | 0.77 | 0.87 | 0.77 |
| Presidio + presidio-tr (score_threshold=0.7) | TR_TAX_ID | 1.00 | 0.07 | 0.13 | 0.07 |
| Presidio + presidio-tr (score_threshold=0.7) | IBAN_CODE | 0.00 | 0.00 | 0.00 | 0.04 |
| Presidio + presidio-tr (score_threshold=0.7) | PHONE_NUMBER | 1.00 | 0.47 | 0.64 | 0.47 |
| Presidio + presidio-tr (score_threshold=0.7) | PERSON | 0.00 | 0.00 | 0.00 | 0.00 |
| Presidio + presidio-tr (score_threshold=0.7) | EMAIL_ADDRESS | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr (score_threshold=0.7) | CREDIT_CARD | 0.67 | 0.05 | 0.10 | 0.05 |
| Presidio + presidio-tr + NER | TR_NATIONAL_ID | 1.00 | 0.77 | 0.87 | 0.77 |
| Presidio + presidio-tr + NER | TR_TAX_ID | 1.00 | 0.50 | 0.67 | 0.50 |
| Presidio + presidio-tr + NER | IBAN_CODE | 1.00 | 0.44 | 0.62 | 0.44 |
| Presidio + presidio-tr + NER | PHONE_NUMBER | 0.97 | 0.88 | 0.92 | 0.88 |
| Presidio + presidio-tr + NER | PERSON | 0.87 | 0.99 | 0.93 | 0.99 |
| Presidio + presidio-tr + NER | EMAIL_ADDRESS | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr + NER | CREDIT_CARD | 0.67 | 0.05 | 0.10 | 0.05 |

| Sistem | Yanlış maskeleme (PII olmayan sayılar) |
|---|---|
| Presidio (en, varsayılan) | 0.00 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | 0.00 |
| Presidio + presidio-tr | 0.00 |
| Presidio + presidio-tr (score_threshold=0.7) | 0.00 |
| Presidio + presidio-tr + NER | 0.00 |
