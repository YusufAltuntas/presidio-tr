# presidio-tr

[Türkçe](https://github.com/YusufAltuntas/presidio-tr/blob/main/README.md) · [English](https://github.com/YusufAltuntas/presidio-tr/blob/main/README_EN.md)

Turkish personal data (PII) recognizers for Microsoft Presidio: national ID (TCKN), tax ID (VKN), TR IBAN, TR phone,
and optional person names.
Ships with a LiteLLM gateway demo: personal data in Turkish text is masked before it reaches the LLM provider and
restored in the answer. This is not an official Microsoft project; it is a community package.

**In short** (1000 synthetic sentences, against Presidio set up for Turkish):

- VKN: no recognizer upstream; F1 0.79 with `presidio-tr`.
- TR phone F1: 0.72 → 0.89. IBAN F1: 0.93 → 1.00.
- A TCKN/VKN/IBAN with one mistyped digit is still masked when a context word is nearby. The cost: more non-PII
  numbers get masked (see Trade-off below).
- Names (optional, Turkish NER model): F1 0.93 on a third-party set of banking messages (123 of 124 names).
- Gateway demo: the LLM provider only sees masked text; so does Langfuse while the analyzer and anonymizer are healthy.

## Install and usage

Not published on PyPI; install from the repo:

```bash
git clone https://github.com/YusufAltuntas/presidio-tr.git && cd presidio-tr
uv sync
```

```python
from presidio_tr import build_analyzer

analyzer = build_analyzer()
analyzer.analyze("TC kimlik no 10000000146", language="tr")
```

No model download is needed (blank spaCy `tr` pipeline). Entity names match upstream (`TR_NATIONAL_ID`,
`TR_TAX_ID`, `IBAN_CODE`, `PHONE_NUMBER`). `build_analyzer()` also adds Presidio's built-in email (`EMAIL_ADDRESS`)
and credit card (`CREDIT_CARD`) recognizers. `add_turkish_recognizers(registry)` adds only the four Turkish
recognizers and only works with a registry set up for `tr`; see the `build_analyzer()` source (`src/presidio_tr/__init__.py`) for the correct setup.

Name recognition (`PERSON`) is optional: it uses the `akdeniz27/bert-base-turkish-cased-ner` model from Hugging Face,
needs transformers + torch, and downloads the model on first use (~440 MB). It adds ~50 ms per sentence on CPU.

```bash
uv sync --extra ner
```

```python
analyzer = build_analyzer(ner=True)
```

## How it works

A regex finds candidates; a validator (checksum) and nearby context words set the score:

| Case | Result |
|---|---|
| Checksum valid | Score 1.0, masked |
| Checksum invalid, context word nearby | Score 0.6, masked |
| Checksum invalid, no context | Dropped |

- Phone numbers have no checksum; a prefixed number (+90 / 0090 / 90 / 0) is masked without context, a bare 10-digit
  number needs context.
- A VKN has a single check digit and about 10% of random 10-digit numbers pass it, so VKN always requires context.
- Context matching tolerates Turkish suffixes ("IBAN'ım", "hesabınız", "T.C."). Short stems (`tc`, `tel`, `cep`)
  match whole words only, so "telif" (copyright) and "cephe" (facade) are not context.

Design rationale and details (in Turkish): [`docs/design.md`](docs/design.md).

## Benchmark

F1 per entity type. Over-masking: share of non-PII numbers (order no, reference no) that get masked.

**Main set** (1000 sentences):

| System | TCKN | VKN | IBAN | Phone | Name | Over-masking |
|---|---|---|---|---|---|---|
| Presidio, default (`en`) | 0.00 | 0.00 | 0.93 | 0.51 | 0.34 | 1.00 |
| Presidio set up for Turkish (fair baseline) | 0.78 | 0.00 | 0.93 | 0.72 | 0.00 | 0.10 |
| Presidio + presidio-tr | 0.81 | 0.79 | 1.00 | 0.89 | — | 0.45 |
| Presidio + presidio-tr, `score_threshold=0.7` | 0.78 | 0.77 | 0.93 | 0.87 | — | 0.02 |
| Presidio + presidio-tr, `ner=True` | 0.81 | 0.79 | 1.00 | 0.89 | 0.98 | 0.45 |

**Held-out set** (24 templates written by a separate LLM agent with no access to the code):

| System | TCKN | VKN | IBAN | Phone | Name | Over-masking |
|---|---|---|---|---|---|---|
| Presidio, default (`en`) | 0.00 | 0.00 | 0.83 | 0.38 | 0.46 | 1.00 |
| Presidio set up for Turkish (fair baseline) | 0.82 | 0.00 | 0.83 | 0.69 | 0.00 | 0.11 |
| Presidio + presidio-tr | 0.88 | 0.77 | 1.00 | 0.85 | — | 0.18 |
| Presidio + presidio-tr, `score_threshold=0.7` | 0.82 | 0.65 | 0.83 | 0.65 | — | 0.01 |
| Presidio + presidio-tr, `ner=True` | 0.88 | 0.77 | 1.00 | 0.85 | 1.00 | 0.18 |

Fair baseline: `language="tr"`, Presidio's built-in recognizers, `TrNationalIdRecognizer` enabled by hand, and
`PhoneRecognizer` set up with `supported_regions=["TR"]`. Precision, recall and the type-agnostic masked rate are in
the results files: [`benchmark/results/2026-11-16.md`](benchmark/results/2026-11-16.md),
[`2026-11-16-heldout.md`](benchmark/results/2026-11-16-heldout.md). "—": name recognition off.

Names in the templates are easy (capitalized full names in obvious places); see the third-party sets below for a
realistic name result. Model scores sometimes fall below 0.7 ("Yılmaz" in "Ayşe Yılmaz" scores 0.58); with
`score_threshold=0.7` such names are not masked.

The data is entirely synthetic (Faker `tr_TR` + templates, seed 42). It deliberately includes non-PII numbers next
to context words ("Kimlik doğrulama kodunuz ..." / "Your ID verification code ...") and context-free hard PII cases.
To reproduce:

```bash
uv sync --group benchmark && uv run python -m benchmark.generate --n 1000 --seed 42 && uv run python -m benchmark.run
uv run python -m benchmark.generate --templates heldout --out benchmark/data/tr_pii_heldout.jsonl && uv run python -m benchmark.run --data benchmark/data/tr_pii_heldout.jsonl --tag heldout
```

For the name row, install with `uv sync --group benchmark --extra ner` and add `--ner` to `benchmark.run`.

### Third-party sets

Three Turkish PII sets published by others are downloaded at a pinned revision (`uv run python -m benchmark.external`).
All are synthetic but independent of our templates; the recognizers were not tuned on them. F1:

| Set | System | TCKN | VKN | IBAN | Phone | Name | Email | Card |
|---|---|---|---|---|---|---|---|---|
| Banking messages ([cagrigungor](https://huggingface.co/datasets/cagrigungor/turkish-pii-masking-benchmark), 550) | Presidio set up for Turkish | 0.62 | 0.00 | 0.00 | 0.92 | 0.00 | 1.00 | 0.00 |
| | presidio-tr, `ner=True` | 0.62 | 0.67 | 0.31 | 0.92 | 0.93 | 1.00 | 0.10 |
| [BTX24](https://huggingface.co/datasets/BTX24/turkish-privacy-pii-ner) test (10,393) | Presidio set up for Turkish | 0.12 | 0.00 | 0.02 | 0.93 | 0.00 | 0.84 | — |
| | presidio-tr, `ner=True` | 0.70 | 0.72 | 0.86 | 0.96 | 0.84 | 0.84 | — |
| [fevziegeyurtsevenler](https://huggingface.co/datasets/fevziegeyurtsevenler/turkish-pii-corpus) (155) | Presidio set up for Turkish | 1.00 | 0.00 | 1.00 | 0.95 | — | 1.00 | 0.00 |
| | presidio-tr, `ner=True` | 1.00 | 1.00 | 1.00 | 1.00 | — | 1.00 | 0.93 |

Reading notes:

- Most numbers in the banking and BTX24 sets fail their checksum (none of the banking IBANs and cards, 6% of the
  BTX24 TCKNs). presidio-tr only catches those with a context word nearby, which explains most of the low recall.
- The banking set also has misses from numbers written as words ("tc dokuz dokuz yedi …"), hyphenated or spaced
  TCKNs (`645-175-336-66`) and the context word typed as "ıban" ("ıban paylaşıyorum TR81 …").
- Most name false positives are name parts inside email addresses (`halil.ozdemir@…`); the email is masked anyway, so
  masking is not affected. In a 2,500-sentence BTX24 sample, all 98 name false positives are of this kind.
- The emails missed in BTX24 use non-existent domains such as `.invalid`, which Presidio's email recognizer rejects.
- Partially masked values (`753347****`) and unmeasured types (address, plate, health…) are left out. Details:
  [`docs/design.md`](docs/design.md). BTX24 is CC BY 4.0, the banking set CC0, fevziegeyurtsevenler Apache 2.0.

Results files: [`2026-11-17-cagrigungor.md`](benchmark/results/2026-11-17-cagrigungor.md),
[`2026-11-17-btx24.md`](benchmark/results/2026-11-17-btx24.md),
[`2026-11-17-fevziegeyurtsevenler.md`](benchmark/results/2026-11-17-fevziegeyurtsevenler.md).

### Trade-off

The 0.6 context tier exists to catch an ID with one mistyped digit; the cost is that it also masks non-PII numbers
near a context word. With default settings `presidio-tr` masks more non-PII numbers than the baseline (0.45 vs 0.10).
The 0.45 reflects the share of hard negatives in the template mix, not a rate for real traffic. If you prefer
precision, turn the tier off with a score threshold: over-masking drops to 0.02, but mistyped IDs are no longer
caught and recall drops (TCKN 0.87 → 0.64 on the main set).

```python
analyzer.analyze(text, language="tr", score_threshold=0.7)
```

The remaining 0.02 are order/reference numbers that pass a checksum by chance (about 1% of random 11-digit numbers
pass the TCKN checksum, about 10% of 10-digit numbers the VKN one); no threshold can separate them. The HTTP server
(`/analyze`) also accepts `score_threshold`; LiteLLM 1.109.1 does not send that field, so in the gateway set the
threshold in the guardrail config: `presidio_score_thresholds: {ALL: 0.7}`.

## Gateway demo

`presidio-tr` plugs into the Presidio guardrail built into LiteLLM `v1.109.1`:

```text
client ──► LiteLLM :4000 ──(pre-call)──► presidio-tr analyzer ──► presidio anonymizer
             │  masked request                                    (<TR_NATIONAL_ID_1>)
             ▼
         LLM provider ──► answer ──► LiteLLM restores placeholders ──► client
             │
             └──► Langfuse (masked text only)
```

```bash
cp deploy/.env.example deploy/.env      # fill in OPENAI_API_KEY
docker compose -f deploy/docker-compose.yml up -d --build --wait

set -a && . deploy/.env && set +a
curl -s http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" -H "Content-Type: application/json" \
  -d '{"model":"gpt-4.1-mini","temperature":0,"messages":[{"role":"system","content":"Kullanıcının mesajını aynen tekrar et; <...> etiketlerini de aynen koru."},{"role":"user","content":"TC kimlik no 10000000146, telefon 0532 123 45 67."}]}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

Expected output: `TC kimlik no 10000000146, telefon 0532 123 45 67.` (values restored). The Langfuse UI is at
`http://localhost:3000`; the login is in the `LANGFUSE_INIT_USER_*` fields of `deploy/.env`. Ports are bound to
`127.0.0.1` only. To stop: `docker compose -f deploy/docker-compose.yml down`.

To turn on name masking: `PRESIDIO_TR_NER=1 docker compose -f deploy/docker-compose.yml up -d --build --wait`.
With torch (CPU) and the bundled model, the analyzer image grows from ~0.7 GB to ~2.6 GB.

If the analyzer is unreachable the request is rejected (fail-closed; verified by an e2e test). Which guardrail
settings are required and why (`presidio_filter_scope: input`, a second `logging_only` guardrail) is in the "Riskler"
section of [`docs/design.md`](docs/design.md).

## Tests

```bash
uv run pytest                                                 # unit tests (127; name tests are skipped without the `ner` extra)
set -a && . deploy/.env && set +a && uv run pytest -m e2e     # end-to-end (7)
```

The e2e tests need the running compose stack and an OpenAI key. CI runs ruff and the unit tests on every push;
pre-commit runs gitleaks + ruff (`uvx pre-commit install`).

## Known limitations

- Addresses are not recognized. Name recognition is optional; ordinary words that look like names ("Barış",
  "Umut") can be masked, and names can be missed ("Gül" in "Umut Barış Gül").
- A checksum-invalid TCKN with no context is not masked; neither is a VKN without context.
- Unsupported forms: numbers written as words ("dokuz dokuz yedi …"), the context word typed as "ıban", spaced or
  hyphenated TCKN (`100 000 001 46`, `645-175-336-66`), IBAN with a space or hyphens after `TR` (`TR 33 …`,
  `TR33-0006-…`), dotted phone (`0532.123.45.67`), 0850/0800 and 444 numbers.
- One value's context word can push a neighbouring value into the 0.6 tier.
- The guarantee for the log copy sent to Langfuse is fail-open: LiteLLM's logging hook is non-blocking, so if
  Presidio fails at that moment the log can stay unmasked.
- If the model corrupts a placeholder, the value cannot be restored. Measured with `deploy/measure_unmask.py`
  (gpt-4.1-mini, 10 tasks): 9 restored, 1 value dropped or altered by the model.
- Known LiteLLM issue on the Anthropic-native path (BerriAI/litellm#22821); the demo uses the OpenAI-compatible path.
- The data is entirely synthetic; results are no guarantee for real traffic.

## License

MIT. Not affiliated with Microsoft.
