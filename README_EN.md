# presidio-tr

[Türkçe](https://github.com/YusufAltuntas/presidio-tr/blob/main/README.md) · [English](https://github.com/YusufAltuntas/presidio-tr/blob/main/README_EN.md)

Turkish personal data (PII) recognizers for Microsoft Presidio: national ID (TCKN), tax ID (VKN), TR IBAN, TR phone.
This is not an official Microsoft project; it is a community package.

**In short** (1000 synthetic sentences, against the fair baseline):

- TR phone F1: 0.51 → 0.89 (against Presidio's built-in phone recognizer).
- VKN: no recognizer upstream; F1 0.79 with `presidio-tr`.
- A TCKN/VKN/IBAN with one mistyped digit is still masked when a context word is nearby.
- LiteLLM gateway demo: the LLM provider only sees masked text; so does Langfuse while the analyzer and anonymizer are healthy.

## Why

Presidio already ships `TrNationalIdRecognizer` (checksum-validated, no typo tier, disabled by default) and
`TrLicensePlateRecognizer`. `presidio-tr` adds:

- A VKN (tax ID) recognizer (none upstream).
- A typo tier for TCKN, VKN and IBAN: a checksum-invalid value with a context word nearby is masked at score 0.6.
- A Turkey-specific phone recognizer (none in presidio-analyzer 2.2.366).
- Turkish suffix-tolerant context matching ("IBAN'ım", "hesabınız").
- The gateway demo and its findings (below).

Entity names intentionally match upstream (`TR_NATIONAL_ID`, `IBAN_CODE`, `PHONE_NUMBER`). The default
`AnalyzerEngine()` registers the built-in recognizers for `en` only; running Turkish text through `en` masks every
number under wrong types such as `US_BANK_NUMBER` / `DATE_TIME`.

## Benchmark

| System | Entity | Precision | Recall | F1 | Masked |
|---|---|---|---|---|---|
| Presidio (en, default) | TR_NATIONAL_ID | 0.00 | 0.00 | 0.00 | 1.00 |
| Presidio (en, default) | TR_TAX_ID | 0.00 | 0.00 | 0.00 | 1.00 |
| Presidio (en, default) | IBAN_CODE | 1.00 | 0.87 | 0.93 | 0.88 |
| Presidio (en, default) | PHONE_NUMBER | 0.36 | 0.86 | 0.51 | 0.99 |
| Presidio (tr, built-in recognizers + TrNationalIdRecognizer) | TR_NATIONAL_ID | 0.99 | 0.64 | 0.78 | 0.70 |
| Presidio (tr, built-in recognizers + TrNationalIdRecognizer) | TR_TAX_ID | 0.00 | 0.00 | 0.00 | 0.91 |
| Presidio (tr, built-in recognizers + TrNationalIdRecognizer) | IBAN_CODE | 1.00 | 0.87 | 0.93 | 0.88 |
| Presidio (tr, built-in recognizers + TrNationalIdRecognizer) | PHONE_NUMBER | 0.36 | 0.86 | 0.51 | 0.86 |
| Presidio + presidio-tr | TR_NATIONAL_ID | 0.75 | 0.87 | 0.81 | 0.87 |
| Presidio + presidio-tr | TR_TAX_ID | 0.78 | 0.79 | 0.79 | 0.79 |
| Presidio + presidio-tr | IBAN_CODE | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr | PHONE_NUMBER | 0.89 | 0.88 | 0.89 | 0.88 |
| Presidio + presidio-tr (score_threshold=0.7) | TR_NATIONAL_ID | 0.99 | 0.64 | 0.78 | 0.64 |
| Presidio + presidio-tr (score_threshold=0.7) | TR_TAX_ID | 0.96 | 0.64 | 0.77 | 0.64 |
| Presidio + presidio-tr (score_threshold=0.7) | IBAN_CODE | 1.00 | 0.87 | 0.93 | 0.87 |
| Presidio + presidio-tr (score_threshold=0.7) | PHONE_NUMBER | 1.00 | 0.77 | 0.87 | 0.77 |

| System | Over-masking (non-PII numbers) |
|---|---|
| Presidio (en, default) | 1.00 |
| Presidio (tr, built-in recognizers + TrNationalIdRecognizer) | 0.49 |
| Presidio + presidio-tr | 0.45 |
| Presidio + presidio-tr (score_threshold=0.7) | 0.02 |

The `en` row is what a user gets without any Turkish setup; the `tr` (built-in recognizers) row is the fair
baseline. "Masked": share of PII covered by some prediction, even of the wrong type. The data is 1000 synthetic
sentences (Faker `tr_TR` + templates, seed 42); it includes non-PII numbers placed next to context words ("Kimlik
doğrulama kodunuz ..." / "Your ID verification code ...") and context-free hard PII cases. Non-PII numbers are not
filtered by checksum: as in real traffic, some of them pass a checksum by chance. Results file:
`benchmark/results/2026-11-16.md`. To reproduce:

```bash
uv sync --group benchmark && uv run python -m benchmark.generate --n 1000 --seed 42 && uv run python -m benchmark.run
```

Held-out set: `uv run python -m benchmark.generate --templates heldout --out benchmark/data/tr_pii_heldout.jsonl && uv run python -m benchmark.run --data benchmark/data/tr_pii_heldout.jsonl --tag heldout`

Plain `uv sync` removes the benchmark group's model again.

### Trade-off: over-masking 0.45

1.00 for default Presidio, 0.49 for `tr` with built-in recognizers, 0.45 for `presidio-tr`. Most of the
`presidio-tr` over-masking comes from the 0.6 context tier, which masks checksum-invalid numbers that sit near a
context word (see Scoring below); with `score_threshold=0.7` over-masking drops to 0.02. The remaining 0.02 (6 of
253 negatives) are order/reference numbers that pass a checksum by chance: about 1% of random 11-digit numbers pass
the TCKN checksum and about 10% of random 10-digit numbers pass the VKN checksum. They score 1.0 and no threshold
can separate them; this is a limit of any checksum-based recognizer. The context tier is deliberate: security comes
first, and a national ID with one mistyped digit should still be masked. The 0.45 figure mostly
reflects the share of hard negatives in the template mix, not a rate for real traffic. If you prefer precision,
drop the context tier with a score threshold:

```python
analyzer.analyze(text, language="tr", score_threshold=0.7)
```

The thresholded version is the `score_threshold=0.7` row in the table.

### Held-out template set

The main templates were written by the same person who wrote the recognizers. There is also a separate 24-template
set (`HELDOUT_TEMPLATES`, `benchmark/generate.py`) written by a separate LLM agent with no access to the code. The agent
was given the field list, which fields are PII, and a requested mix: 12 templates with PII (at least 3 without cue words,
at least 2 with mistyped fields) and 12 without PII (including numbers near PII-related words). The value generators are
shared with the main set; only the sentence templates are independent. The recognizers were not tuned on this set. Results: `benchmark/results/2026-11-16-heldout.md`.

| System | Entity | Precision | Recall | F1 | Masked |
|---|---|---|---|---|---|
| Presidio (tr, built-in recognizers + TrNationalIdRecognizer) | TR_NATIONAL_ID | 0.97 | 0.70 | 0.82 | 0.75 |
| Presidio (tr, built-in recognizers + TrNationalIdRecognizer) | TR_TAX_ID | 0.00 | 0.00 | 0.00 | 0.90 |
| Presidio (tr, built-in recognizers + TrNationalIdRecognizer) | IBAN_CODE | 1.00 | 0.71 | 0.83 | 0.74 |
| Presidio (tr, built-in recognizers + TrNationalIdRecognizer) | PHONE_NUMBER | 0.25 | 0.81 | 0.38 | 0.81 |
| Presidio + presidio-tr | TR_NATIONAL_ID | 0.79 | 1.00 | 0.88 | 1.00 |
| Presidio + presidio-tr | TR_TAX_ID | 0.63 | 1.00 | 0.77 | 1.00 |
| Presidio + presidio-tr | IBAN_CODE | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr | PHONE_NUMBER | 1.00 | 0.75 | 0.85 | 0.75 |

Over-masking: built-in recognizers 0.63, presidio-tr 0.18, 0.01 with `score_threshold=0.7` (from the held-out file).

Phone recall below the baseline (0.75 vs 0.81) is by design: a bare 10-digit number with no prefix and no context is not masked (the `{name} {bare_phone}` template); the baseline catches those at 0.25 precision.

On this set, recall with `score_threshold=0.7` is `TR_NATIONAL_ID` 0.70, `TR_TAX_ID` 0.49, `IBAN_CODE` 0.71, `PHONE_NUMBER` 0.49; thresholded recall is lower than on the main set for VKN, IBAN and phone.

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

`add_turkish_recognizers(registry)` only works with a registry/analyzer set up for `tr` with a Turkish NLP engine;
adding it to a default `en` registry does not help. See the `build_analyzer()` source (`src/presidio_tr/__init__.py`)
for the correct setup. A blank spaCy `tr` pipeline is used, so no model download is needed.

## Scoring

| Case | Result |
|---|---|
| Checksum valid | Score 1.0, masked |
| Checksum invalid, context word nearby | Score 0.6, masked |
| Checksum invalid, no context | Dropped |

Three tiers so that a national ID with one wrong digit does not leak, and a context-free order number is not
masked. Phone numbers have no checksum; the validator checks format only (a +90 / 0090 / 90 / 0-prefixed number is masked without context, a bare 10-digit number needs context).

VKN exception: a VKN has a single mod-10 check digit, so about 10% of random 10-digit numbers pass it. VKN
therefore requires context; a valid VKN written without context is not masked.

## Turkish context matching

- Stem prefixes instead of lemmas: inflected forms like "hesabınız" and "hesaplarım" match the `hesap` / `hesab` stems.
- Short stems (`tc`, `vkn`, `tel`, `gsm`, `cep`) match whole words only, so "telif" (copyright) and "cephe" (facade)
  are not context. `ulaş` is narrowed to its verb forms (`ulaşa`, `ulaşın`, `ulaşıl`), so "ulaşım" (transport) is not.
  Common compound/suffixed forms are listed as separate stems (`tcno`, `tckimlik`, `vkno`, `telno`, `gsmno`, `ceptel`, `cepno`, `cepte`, `cebim`, `ulaşm`); other suffixed forms such as `telim`, `telden` are not context.
- Softened consonants are listed in the stems: `hesap`/`hesab`, `kimlik`/`kimliğ`.
- Turkish lowercasing turns "IBAN" into "ıban", so both Turkish and standard lowercasing are tried.

Recognizers get no Presidio `context` parameter; Presidio's lemma-based score enhancer does not change scores.

## Gateway demo

`presidio-tr` plugs into the Presidio guardrail built into LiteLLM `v1.109.1`. The LLM provider sees only masked
text, placeholders are restored in the answer, and, while the analyzer and anonymizer are healthy, Langfuse
receives only masked text (see "Leak-guarantee limit" under Known limitations).

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
`http://localhost:3000`; the user and password are the `LANGFUSE_INIT_USER_*` fields in `deploy/.env`.
Published ports are bound to `127.0.0.1` only. LiteLLM needs about 15 s after start before it answers
(`/health/liveliness`). To stop: `docker compose -f deploy/docker-compose.yml down`.

Failure behavior: if the analyzer is unreachable the request is rejected (fail-closed; verified by an e2e test).
If the analyzer returns an error or an invalid response, rejection depends on `output_parse_pii` being enabled on the guardrail.

Demo findings (LiteLLM 1.109.1):

- `presidio_filter_scope: input` is required on the guardrail. The default `both` re-masks values already
  restored by `output_parse_pii`, so the user sees `<TR_NATIONAL_ID>`.
- A second guardrail with `mode: logging_only` (also `presidio_filter_scope: input`) is required; otherwise
  Langfuse stored the restored raw TCKN in the generation output. Verified by e2e tests for both streaming and
  non-streaming requests.
- Langfuse v4 serves observations via `/api/public/v2/observations` (v1 `/api/public/traces` is disabled in its
  events-only mode); the e2e test uses it.

## Tests and development

```bash
uv run pytest                                                 # unit tests (115)
set -a && . deploy/.env && set +a && uv run pytest -m e2e     # end-to-end (7)
```

The e2e tests need the running compose stack and an OpenAI key; each run costs a fraction of a cent.
Pre-commit: gitleaks + ruff (`uvx pre-commit install`). CI runs ruff and the unit tests on every push.

## Known limitations

- A checksum-invalid national ID with no context is not masked; neither is a VKN without context.
- Unsupported forms: spaced TCKN (`100 000 001 46`), IBAN with a space after `TR` (`TR 33 …`), 0850/0800
  numbers.
- Non-PII numbers that pass a checksum by chance (about 1% of random 11-digit numbers, about 10% of 10-digit numbers
  next to a context word) are masked at score 1.0; a score threshold cannot separate them.
- Context matching can leak across neighbouring labels: one label's context word can push a nearby value into the 0.6 tier.
- Leak-guarantee limit: LiteLLM's logging hook is non-blocking. If Presidio fails between the call and logging,
  the logged copy can be unmasked (fail-open for logs); "Langfuse sees only masked text" holds while the
  analyzer/anonymizer are healthy.
- No names or addresses (NER, v2).
- If the model corrupts a placeholder, the value cannot be restored. Measured with `deploy/measure_unmask.py`
  (gpt-4.1-mini, 2026-11-14): 10 tasks: 9 restored, 0 placeholders left unrestored, 1 value dropped or altered by the model.
- Known LiteLLM issue on the Anthropic-native path (BerriAI/litellm#22821); the demo uses the OpenAI-compatible
  path with `gpt-4.1-mini`.
- The data is entirely synthetic; results are no guarantee for real traffic.

## License

MIT. Not affiliated with Microsoft.
