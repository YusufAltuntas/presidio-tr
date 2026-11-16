# presidio-tr

[Türkçe](https://github.com/YusufAltuntas/presidio-tr/blob/main/README.md) · [English](https://github.com/YusufAltuntas/presidio-tr/blob/main/README_EN.md)

Turkish personal data (PII) recognizers for Microsoft Presidio: national ID (TCKN), tax ID (VKN), TR IBAN, TR phone.
Ships with a LiteLLM gateway demo: personal data in Turkish text is masked before it reaches the LLM provider and
restored in the answer. This is not an official Microsoft project; it is a community package.

**In short** (1000 synthetic sentences, against Presidio set up for Turkish):

- VKN: no recognizer upstream; F1 0.79 with `presidio-tr`.
- TR phone F1: 0.72 → 0.89. IBAN F1: 0.93 → 1.00.
- A TCKN/VKN/IBAN with one mistyped digit is still masked when a context word is nearby. The cost: more non-PII
  numbers get masked (see Trade-off below).
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

| System | TCKN | VKN | IBAN | Phone | Over-masking |
|---|---|---|---|---|---|
| Presidio, default (`en`) | 0.00 | 0.00 | 0.93 | 0.51 | 1.00 |
| Presidio set up for Turkish (fair baseline) | 0.78 | 0.00 | 0.93 | 0.72 | 0.10 |
| Presidio + presidio-tr | 0.81 | 0.79 | 1.00 | 0.89 | 0.45 |
| Presidio + presidio-tr, `score_threshold=0.7` | 0.78 | 0.77 | 0.93 | 0.87 | 0.02 |

**Held-out set** (24 templates written by a separate LLM agent with no access to the code):

| System | TCKN | VKN | IBAN | Phone | Over-masking |
|---|---|---|---|---|---|
| Presidio, default (`en`) | 0.00 | 0.00 | 0.83 | 0.38 | 1.00 |
| Presidio set up for Turkish (fair baseline) | 0.82 | 0.00 | 0.83 | 0.69 | 0.11 |
| Presidio + presidio-tr | 0.88 | 0.77 | 1.00 | 0.85 | 0.18 |
| Presidio + presidio-tr, `score_threshold=0.7` | 0.82 | 0.65 | 0.83 | 0.65 | 0.01 |

Fair baseline: `language="tr"`, Presidio's built-in recognizers, `TrNationalIdRecognizer` enabled by hand, and
`PhoneRecognizer` set up with `supported_regions=["TR"]`. Precision, recall and the type-agnostic masked rate are in
the results files: [`benchmark/results/2026-11-16.md`](benchmark/results/2026-11-16.md),
[`2026-11-16-heldout.md`](benchmark/results/2026-11-16-heldout.md).

The data is entirely synthetic (Faker `tr_TR` + templates, seed 42). It deliberately includes non-PII numbers next
to context words ("Kimlik doğrulama kodunuz ..." / "Your ID verification code ...") and context-free hard PII cases.
To reproduce:

```bash
uv sync --group benchmark && uv run python -m benchmark.generate --n 1000 --seed 42 && uv run python -m benchmark.run
uv run python -m benchmark.generate --templates heldout --out benchmark/data/tr_pii_heldout.jsonl && uv run python -m benchmark.run --data benchmark/data/tr_pii_heldout.jsonl --tag heldout
```

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

If the analyzer is unreachable the request is rejected (fail-closed; verified by an e2e test). Which guardrail
settings are required and why (`presidio_filter_scope: input`, a second `logging_only` guardrail) is in the "Riskler"
section of [`docs/design.md`](docs/design.md).

## Tests

```bash
uv run pytest                                                 # unit tests (118)
set -a && . deploy/.env && set +a && uv run pytest -m e2e     # end-to-end (7)
```

The e2e tests need the running compose stack and an OpenAI key. CI runs ruff and the unit tests on every push;
pre-commit runs gitleaks + ruff (`uvx pre-commit install`).

## Known limitations

- Names and addresses are not recognized (no NER).
- A checksum-invalid TCKN with no context is not masked; neither is a VKN without context.
- Unsupported forms: spaced TCKN (`100 000 001 46`), IBAN with a space or hyphens after `TR` (`TR 33 …`,
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
