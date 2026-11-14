# presidio-tr v1 Uygulama Planı

> **Tarihsel doküman.** Uygulamadan önce yazılmış plandır; bazı ifadeleri (ör. "Presidio'da TC kimlik tanıyıcısı yok") sonradan yanlış çıktı. Güncel durum: `README.md` ve spec.

> **Ajanlar için:** GEREKLİ ALT-SKILL: Bu planı görev görev uygulamak için `subagent-driven-development` (önerilen) ya da `executing-plans` kullan. Adımlar takip için checkbox (`- [ ]`) biçimindedir.

> Bu doküman v1'in **uygulama adımlarının** sahibidir. Ne yapıldığı ve nedeni: `docs/superpowers/specs/2026-11-14-presidio-tr-design.md`.

**Amaç:** Presidio için Türkçe PII tanıyıcı paketi, sentetik benchmark'ı ve LiteLLM + Langfuse gateway demosu.

**Mimari:** Saf `validators` → checksum + bağlamla skorlayan `recognizers` → `build_analyzer()` (blank Türkçe spaCy). Paketi Presidio analyzer HTTP API'siyle uyumlu küçük bir FastAPI sunucusu (`presidio_tr.server`) dışarı açar; LiteLLM'in hazır Presidio guardrail'i onu çağırır. Benchmark ve deploy paketi dışarıdan kullanır.

**Teknoloji:** Python 3.11, uv, presidio-analyzer 2.2.x, spaCy (blank `tr`), FastAPI, Faker, pytest, ruff, Docker Compose, LiteLLM `v1.109.1`, presidio-anonymizer `2.2.362`, Langfuse `v4.80.0` compose.

**Plan yazılırken doğrulananlar:** Görev 2–9'daki kod ve testler presidio-analyzer 2.2.366 ile bir prototipte çalıştırıldı (65 test geçti, benchmark üretildi). Validator'lar `python-stdnum` ile 40.000 rastgele sayıda karşılaştırıldı, fark 0. Compose `include` + ortak `.env` `docker compose config` ile doğrulandı. Görev 10–12 (Docker, e2e) gerçek API anahtarı istediği için prototipte çalıştırılmadı; o görevlerdeki "beklenen" çıktılar ilk kez uygulamada görülecek.

**Çalışma dizini:** Tüm komutlar repo kökünde: `~/Desktop/my-projects/presidio-tr`.

**Uygulama sırasında yapılan düzeltmeler** (görev incelemelerinden, kullanıcı onayıyla; aşağıdaki görev metinleri
ilk hâlidir, güncel davranış koddadır — commit `6d0217a..401cb73`):
- `TurkishPatternRecognizer`'a `requires_context` eklendi; `VknRecognizer` bağlamsız eşleşmeyi atar (spec, "VKN istisnası").
- Analyzer testi skorları da doğrular.
- Benchmark tarihleri seed'li rng'den üretilir; `ref_no` geçerli VKN olamaz; bağlam kelimeli zor negatif şablonlar eklendi.
- Bu yüzden Görev 8'deki prototip benchmark sayıları artık geçerli değil; yeni sonuç `benchmark/results/` altındadır.
- Test sayıları da değişti: Görev 9 sonunda ve Görev 14'te beklenen `65 passed` yerine `68 passed`.

---

## Dosya haritası

| Dosya | Sorumluluk | Görev |
|---|---|---|
| `pyproject.toml`, `LICENSE`, `README.md` (taslak) | Paket tanımı, araç ayarları | 1 |
| `src/presidio_tr/validators.py` | TCKN, VKN, TR IBAN, telefon doğrulama (saf) | 2 |
| `src/presidio_tr/context.py` | Bağlam kökleri, Türkçe küçültme, `has_context` | 3 |
| `src/presidio_tr/recognizers/base.py` | Üç kademeli skorlayan ortak tanıyıcı | 4 |
| `src/presidio_tr/recognizers/__init__.py` | Dört tanıyıcı + `all_recognizers()` | 4 |
| `src/presidio_tr/__init__.py` | `BlankTurkishNlpEngine`, `add_turkish_recognizers`, `build_analyzer` | 5 |
| `benchmark/synth.py` | Sentetik değer üreticileri | 6 |
| `benchmark/generate.py` | Şablonlardan etiketli JSONL | 7 |
| `benchmark/run.py` | İki sistemi karşılaştırır, markdown rapor | 8 |
| `src/presidio_tr/server.py` | `/analyze`, `/health` | 9 |
| `deploy/*` | Dockerfile, compose, LiteLLM config, `.env.example` | 10 |
| `tests/e2e/test_gateway.py` | Gateway uçtan uca testleri | 11 |
| `deploy/measure_unmask.py` | Etiket bozulma oranı | 12 |
| `.pre-commit-config.yaml`, `.github/workflows/ci.yml` | gitleaks + ruff, CI | 13 |
| `README.md`, `README_EN.md` | Dokümantasyon | 14 |

---

### Görev 1: Proje iskeleti

**Dosyalar:**
- Oluştur: `pyproject.toml`, `LICENSE`, `README.md`, `src/presidio_tr/__init__.py`

- [ ] **Adım 1: `pyproject.toml` yaz**

```toml
[project]
name = "presidio-tr"
version = "0.1.0"
description = "Turkish PII recognizers for Microsoft Presidio (unofficial community package)"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
dependencies = ["presidio-analyzer>=2.2.360,<2.3"]

[project.optional-dependencies]
server = ["fastapi>=0.115", "uvicorn>=0.30"]

[dependency-groups]
dev = [
    "pytest>=8",
    "ruff>=0.6",
    "python-stdnum>=1.20",
    "faker>=30",
    "fastapi>=0.115",
    "httpx>=0.27",
]
benchmark = [
    "en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/presidio_tr"]

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
ignore = ["E501"]  # uzun satırları formatter böler; uzun metin sabitleri kalabilir

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
markers = ["e2e: compose ayaktayken çalışan uçtan uca testler"]
addopts = "-m 'not e2e'"
```

- [ ] **Adım 2: `LICENSE` (MIT) ve taslak `README.md` yaz**

`LICENSE`:

```text
MIT License

Copyright (c) 2026 Yusuf Altuntaş

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

`README.md` (Görev 14'te tamamlanır; Docker build için şimdiden var olmalı):

```markdown
# presidio-tr

Microsoft Presidio için Türkçe PII tanıyıcıları (resmi olmayan topluluk paketi).
```

`src/presidio_tr/__init__.py`:

```python
"""Microsoft Presidio için Türkçe PII tanıyıcıları (resmi olmayan topluluk paketi)."""
```

- [ ] **Adım 3: Ortamı kur ve doğrula**

Run: `uv sync && uv run pytest`
Expected: bağımlılıklar kurulur; pytest `no tests ran` ile 5 koduyla çıkar (henüz test yok).

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: `All checks passed!` ve `1 file already formatted`

- [ ] **Adım 4: Commit**

```bash
git add pyproject.toml uv.lock LICENSE README.md src/presidio_tr/__init__.py
git commit -m "chore: scaffold package with uv, ruff and pytest"
```

---

### Görev 2: Validator'lar

**Dosyalar:**
- Test: `tests/unit/test_validators.py`
- Oluştur: `src/presidio_tr/validators.py`

`python-stdnum` yalnızca testte referans olarak kullanılır; paket ona bağımlı değildir.

- [ ] **Adım 1: Başarısız testi yaz** — `tests/unit/test_validators.py`

```python
import random

import pytest
from stdnum.tr import tckimlik, vkn

from presidio_tr.validators import tckn_valid, tr_iban_valid, tr_phone_valid, vkn_valid


@pytest.mark.parametrize("value", ["10000000146", "12345678950"])
def test_tckn_valid_accepts_known_valid_numbers(value):
    assert tckn_valid(value)


@pytest.mark.parametrize(
    "value",
    ["10000000147", "02345678950", "1000000014", "100000001460", "1000000014a", ""],
)
def test_tckn_valid_rejects_invalid_numbers(value):
    assert not tckn_valid(value)


def test_tckn_valid_matches_python_stdnum_reference():
    rng = random.Random(0)
    for _ in range(20_000):
        value = str(rng.randint(10**10, 10**11 - 1))
        assert tckn_valid(value) == tckimlik.is_valid(value), value


def test_vkn_valid_matches_python_stdnum_reference():
    rng = random.Random(0)
    for _ in range(20_000):
        value = "".join(rng.choice("0123456789") for _ in range(10))
        assert vkn_valid(value) == vkn.is_valid(value), value


@pytest.mark.parametrize("value", ["123456789", "12345678901", "123456789a"])
def test_vkn_valid_rejects_wrong_shape(value):
    assert not vkn_valid(value)


@pytest.mark.parametrize(
    "value",
    ["TR330006100519786457841326", "TR33 0006 1005 1978 6457 8413 26", "tr330006100519786457841326"],
)
def test_tr_iban_valid_accepts_valid_iban_in_any_spacing_or_case(value):
    assert tr_iban_valid(value)


@pytest.mark.parametrize(
    "value",
    ["TR330006100519786457841327", "DE89370400440532013000", "TR33000610051978645784132"],
)
def test_tr_iban_valid_rejects_invalid_iban(value):
    assert not tr_iban_valid(value)


@pytest.mark.parametrize("value", ["+90 532 123 45 67", "0532 123 4567", "05321234567", "+902121234567"])
def test_tr_phone_valid_accepts_prefixed_numbers(value):
    assert tr_phone_valid(value)


@pytest.mark.parametrize("value", ["5321234567", "0632 123 4567", "+90 132 123 45 67", "123"])
def test_tr_phone_valid_rejects_bare_or_malformed_numbers(value):
    assert not tr_phone_valid(value)
```

- [ ] **Adım 2: Testin başarısız olduğunu gör**

Run: `uv run pytest tests/unit/test_validators.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'presidio_tr.validators'`

- [ ] **Adım 3: Uygula** — `src/presidio_tr/validators.py`

```python
"""Türkçe kimlik ve hesap numaraları için saf doğrulama fonksiyonları."""

import re

_NON_DIGIT = re.compile(r"\D")
_WHITESPACE = re.compile(r"\s")


def tckn_valid(candidate: str) -> bool:
    """TC kimlik numarasının resmi checksum kuralına uyup uymadığını döndürür."""
    if len(candidate) != 11 or not candidate.isdigit() or candidate[0] == "0":
        return False
    d = [int(c) for c in candidate]
    tenth = (sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10
    eleventh = sum(d[:10]) % 10
    return d[9] == tenth and d[10] == eleventh


def vkn_valid(candidate: str) -> bool:
    """Vergi kimlik numarasının (10 hane) checksum kuralına uyup uymadığını döndürür."""
    if len(candidate) != 10 or not candidate.isdigit():
        return False
    d = [int(c) for c in candidate]
    total = 0
    for i in range(9):
        tmp = (d[i] + 9 - i) % 10
        total += 9 if tmp == 9 else (tmp * 2 ** (9 - i)) % 9
    return (10 - total % 10) % 10 == d[9]


def tr_iban_valid(candidate: str) -> bool:
    """TR IBAN'ın uzunluk, önek ve mod-97 kontrolünden geçip geçmediğini döndürür."""
    iban = _WHITESPACE.sub("", candidate).upper()
    if len(iban) != 26 or not iban.startswith("TR") or not iban[2:].isdigit():
        return False
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(str(int(ch, 36)) for ch in rearranged)
    return int(numeric) % 97 == 1


def tr_phone_valid(candidate: str) -> bool:
    """Ülke ya da alan koduyla yazılmış Türk telefon numarasını doğrular.

    Öneksiz 10 haneli numara tek başına telefon sayılmaz; bağlam gerekir.
    """
    digits = _NON_DIGIT.sub("", candidate)
    if len(digits) == 12 and digits.startswith("90"):
        national = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        national = digits[1:]
    else:
        return False
    return national[0] in "2345"
```

- [ ] **Adım 4: Testlerin geçtiğini gör**

Run: `uv run pytest tests/unit/test_validators.py -q`
Expected: `27 passed`

- [ ] **Adım 5: Commit**

```bash
git add tests/unit/test_validators.py src/presidio_tr/validators.py
git commit -m "feat: add TCKN, VKN, TR IBAN and phone validators"
```

---

### Görev 3: Türkçe bağlam eşleştirmesi

**Dosyalar:**
- Test: `tests/unit/test_context.py`
- Oluştur: `src/presidio_tr/context.py`

Neden kendi eşleştirmemiz: Presidio bağlamı lemma ile eşleştirir; blank Türkçe pipeline'da lemma boş ve "IBAN'ımı" tek token kalır. Kök önekiyle eşleştirme ekleri tolere eder; ünsüz yumuşaması için kökün iki hali listelenir; Türkçe küçültme kısaltmaları bozduğu için ("IBAN" → "ıban") iki küçültme de denenir.

- [ ] **Adım 1: Başarısız testi yaz** — `tests/unit/test_context.py`

```python
import pytest

from presidio_tr.context import IBAN_STEMS, TCKN_STEMS, has_context, tr_lower


def test_tr_lower_follows_turkish_casing():
    assert tr_lower("IBAN İL") == "ıban il"


@pytest.mark.parametrize(
    ("text", "stems"),
    [
        ("Hesabıma yatırın: X", IBAN_STEMS),  # ünsüz yumuşaması: hesap → hesab
        ("IBAN'ımı yazıyorum: X", IBAN_STEMS),
        ("TC'm X", TCKN_STEMS),
        ("T.C. no: X", TCKN_STEMS),
        ("Kimliğimdeki numara X", TCKN_STEMS),  # kimlik → kimliğ
        ("X numaralı kimlik", TCKN_STEMS),  # bağlam sonra da gelebilir
    ],
)
def test_has_context_finds_inflected_context_words(text, stems):
    start = text.index("X")
    assert has_context(text, start, start + 1, stems)


def test_has_context_ignores_unrelated_words():
    text = "Sipariş numaranız X, kargoya verildi."
    start = text.index("X")
    assert not has_context(text, start, start + 1, TCKN_STEMS)


def test_has_context_ignores_words_outside_window():
    text = "kimlik " + "a" * 60 + " X"
    start = text.index("X")
    assert not has_context(text, start, start + 1, TCKN_STEMS)


def test_has_context_handles_uppercase_acronyms_and_turkish_capitals():
    for text, stems in [("IBAN: X", IBAN_STEMS), ("KİMLİK NO: X", TCKN_STEMS)]:
        start = text.index("X")
        assert has_context(text, start, start + 1, stems), text
```

- [ ] **Adım 2: Testin başarısız olduğunu gör**

Run: `uv run pytest tests/unit/test_context.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'presidio_tr.context'`

- [ ] **Adım 3: Uygula** — `src/presidio_tr/context.py`

```python
"""Türkçe bağlam kelimeleri ve ek toleranslı bağlam eşleştirmesi."""

import re

TCKN_STEMS = ("tc", "tckn", "kimlik", "kimliğ", "vatandaşlık", "vatandaşlığ", "nüfus")
VKN_STEMS = ("vkn", "vergi")
IBAN_STEMS = ("iban", "hesap", "hesab")
PHONE_STEMS = ("tel", "telefon", "gsm", "cep", "whatsapp", "ulaş")

WINDOW_BEFORE = 50
WINDOW_AFTER = 30

_WORD = re.compile(r"\w+")


def tr_lower(text: str) -> str:
    """Türkçe büyük/küçük harf kurallarıyla küçültür (I→ı, İ→i)."""
    return text.replace("I", "ı").replace("İ", "i").lower()


def has_context(text: str, start: int, end: int, stems: tuple[str, ...]) -> bool:
    """Eşleşmenin çevresinde, kökü verilen kelimelerden biriyle başlayan kelime var mı.

    Kök eşleştirmesi Türkçe ekleri tolere eder: "IBAN'ımı" → "iban", "hesabıma" → "hesab".
    """
    window = (text[max(0, start - WINDOW_BEFORE) : start] + " " + text[end : end + WINDOW_AFTER]).replace(".", "")
    # Kısaltmalar Latin büyük harfle yazılır: Türkçe kuralla "IBAN" → "ıban" olur, bu yüzden iki küçültme de denenir.
    words = set(_WORD.findall(tr_lower(window))) | set(_WORD.findall(window.lower()))
    return any(word.startswith(stem) for word in words for stem in stems)
```

- [ ] **Adım 4: Testlerin geçtiğini gör**

Run: `uv run pytest tests/unit/test_context.py -q`
Expected: `10 passed`

- [ ] **Adım 5: Commit**

```bash
git add tests/unit/test_context.py src/presidio_tr/context.py
git commit -m "feat: add suffix-tolerant Turkish context matching"
```

---

### Görev 4: Tanıyıcılar

**Dosyalar:**
- Test: `tests/unit/test_recognizers.py`
- Oluştur: `src/presidio_tr/recognizers/base.py`, `src/presidio_tr/recognizers/__init__.py`

Skor kuralı (spec, "Skorlama kuralı"): doğrulamadan geçen → `VALID_SCORE` (1.0); geçemeyen ama bağlamı olan → `CONTEXT_SCORE` (0.6); ikisi de yoksa atılır. Tanıyıcılara Presidio `context` parametresi **verilmez**, böylece Presidio'nun lemma güçlendiricisi skoru değiştirmez.

- [ ] **Adım 1: Başarısız testi yaz** — `tests/unit/test_recognizers.py`

```python
import pytest

from presidio_tr.recognizers import (
    TcKimlikRecognizer,
    TrIbanRecognizer,
    TrPhoneRecognizer,
    VknRecognizer,
)
from presidio_tr.recognizers.base import CONTEXT_SCORE, VALID_SCORE


def _run(recognizer, text):
    entity = recognizer.supported_entities[0]
    return [(text[r.start : r.end], r.score) for r in recognizer.analyze(text, [entity])]


@pytest.mark.parametrize(
    ("recognizer", "text", "expected"),
    [
        (TcKimlikRecognizer(), "Numaram 10000000146.", [("10000000146", VALID_SCORE)]),
        (TcKimlikRecognizer(), "TC kimlik no: 10000000147", [("10000000147", CONTEXT_SCORE)]),
        (TcKimlikRecognizer(), "Sipariş no: 10000000147", []),
        (VknRecognizer(), "Firma 1234567890 ile kayıtlı.", [("1234567890", VALID_SCORE)]),
        (VknRecognizer(), "Vergi no 1234567891", [("1234567891", CONTEXT_SCORE)]),
        (VknRecognizer(), "Referans 1234567891", []),
        (
            TrIbanRecognizer(),
            "Gönderin: TR33 0006 1005 1978 6457 8413 26.",
            [("TR33 0006 1005 1978 6457 8413 26", VALID_SCORE)],
        ),
        (TrIbanRecognizer(), "Hesabım TR330006100519786457841327", [("TR330006100519786457841327", CONTEXT_SCORE)]),
        (TrPhoneRecognizer(), "Arayın: +90 532 123 45 67", [("+90 532 123 45 67", VALID_SCORE)]),
        (TrPhoneRecognizer(), "Cep: 5321234567", [("5321234567", CONTEXT_SCORE)]),
        (TrPhoneRecognizer(), "Tutar 5321234567 TL", []),
    ],
)
def test_three_tier_scoring(recognizer, text, expected):
    assert _run(recognizer, text) == expected


def test_tckn_regex_does_not_match_inside_longer_numbers():
    assert _run(TcKimlikRecognizer(), "Kart 100000001460000 kimlik") == []


def test_recognizers_are_registered_for_turkish():
    assert TcKimlikRecognizer().supported_language == "tr"
```

- [ ] **Adım 2: Testin başarısız olduğunu gör**

Run: `uv run pytest tests/unit/test_recognizers.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'presidio_tr.recognizers'`

- [ ] **Adım 3: Ortak tanıyıcıyı yaz** — `src/presidio_tr/recognizers/base.py`

```python
"""Checksum + bağlam ile skorlayan ortak Türkçe tanıyıcı."""

from collections.abc import Callable

from presidio_analyzer import Pattern, PatternRecognizer, RecognizerResult

from presidio_tr.context import has_context

VALID_SCORE = 1.0
CONTEXT_SCORE = 0.6


class TurkishPatternRecognizer(PatternRecognizer):
    """Regex adaylarını üç kademeyle skorlar.

    Doğrulamadan geçen aday yüksek skor alır; geçemeyen ama yakınında bağlam
    kelimesi olan aday orta skor alır; ikisi de yoksa aday atılır.
    """

    def __init__(
        self,
        entity: str,
        patterns: list[Pattern],
        validator: Callable[[str], bool],
        context_stems: tuple[str, ...],
    ) -> None:
        self._validator = validator
        self._context_stems = context_stems
        super().__init__(
            supported_entity=entity,
            name=type(self).__name__,
            supported_language="tr",
            patterns=patterns,
        )

    def analyze(self, text, entities, nlp_artifacts=None, regex_flags=None) -> list[RecognizerResult]:
        kept = []
        for result in super().analyze(text, entities, nlp_artifacts, regex_flags):
            candidate = text[result.start : result.end]
            if self._validator(candidate):
                result.score = VALID_SCORE
            elif has_context(text, result.start, result.end, self._context_stems):
                result.score = CONTEXT_SCORE
            else:
                continue
            kept.append(result)
        return kept
```

- [ ] **Adım 4: Dört tanıyıcıyı yaz** — `src/presidio_tr/recognizers/__init__.py`

```python
"""Türkçe PII tanıyıcıları."""

from presidio_analyzer import Pattern

from presidio_tr.context import IBAN_STEMS, PHONE_STEMS, TCKN_STEMS, VKN_STEMS
from presidio_tr.recognizers.base import TurkishPatternRecognizer
from presidio_tr.validators import tckn_valid, tr_iban_valid, tr_phone_valid, vkn_valid

TCKN_REGEX = r"(?<!\d)[1-9]\d{10}(?!\d)"
VKN_REGEX = r"(?<!\d)\d{10}(?!\d)"
IBAN_REGEX = r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b"
PHONE_REGEX = r"(?<![\d+])(?:\+?90[\s-]?|0[\s-]?)?\(?[2-5]\d{2}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"


class TcKimlikRecognizer(TurkishPatternRecognizer):
    def __init__(self) -> None:
        super().__init__("TR_NATIONAL_ID", [Pattern("tckn", TCKN_REGEX, 0.5)], tckn_valid, TCKN_STEMS)


class VknRecognizer(TurkishPatternRecognizer):
    def __init__(self) -> None:
        super().__init__("TR_TAX_ID", [Pattern("vkn", VKN_REGEX, 0.5)], vkn_valid, VKN_STEMS)


class TrIbanRecognizer(TurkishPatternRecognizer):
    def __init__(self) -> None:
        super().__init__("IBAN_CODE", [Pattern("tr_iban", IBAN_REGEX, 0.5)], tr_iban_valid, IBAN_STEMS)


class TrPhoneRecognizer(TurkishPatternRecognizer):
    def __init__(self) -> None:
        super().__init__("PHONE_NUMBER", [Pattern("tr_phone", PHONE_REGEX, 0.5)], tr_phone_valid, PHONE_STEMS)


def all_recognizers() -> list[TurkishPatternRecognizer]:
    """Paketteki tüm tanıyıcıların yeni örneklerini döndürür."""
    return [TcKimlikRecognizer(), VknRecognizer(), TrIbanRecognizer(), TrPhoneRecognizer()]
```

- [ ] **Adım 5: Testlerin geçtiğini gör**

Run: `uv run pytest tests/unit/test_recognizers.py -q`
Expected: `13 passed`

- [ ] **Adım 6: Commit**

```bash
git add tests/unit/test_recognizers.py src/presidio_tr/recognizers/
git commit -m "feat: add Turkish recognizers with checksum and context scoring"
```

---

### Görev 5: `build_analyzer`

**Dosyalar:**
- Test: `tests/unit/test_analyzer.py`
- Değiştir: `src/presidio_tr/__init__.py` (Görev 1'deki tek satırlık docstring'in yerine tamamı)

- [ ] **Adım 1: Başarısız testi yaz** — `tests/unit/test_analyzer.py`

```python
from presidio_tr import build_analyzer


def test_build_analyzer_detects_all_turkish_entities_in_one_text():
    text = "TC 10000000146, VKN 1234567890, IBAN TR330006100519786457841326, tel 0532 123 45 67."
    results = build_analyzer().analyze(text, language="tr")
    found = {(r.entity_type, text[r.start : r.end]) for r in results}
    assert found == {
        ("TR_NATIONAL_ID", "10000000146"),
        ("TR_TAX_ID", "1234567890"),
        ("IBAN_CODE", "TR330006100519786457841326"),
        ("PHONE_NUMBER", "0532 123 45 67"),
    }


def test_build_analyzer_returns_nothing_for_text_without_pii():
    assert build_analyzer().analyze("Kargonuz yarın teslim edilecek.", language="tr") == []
```

- [ ] **Adım 2: Testin başarısız olduğunu gör**

Run: `uv run pytest tests/unit/test_analyzer.py -q`
Expected: FAIL — `ImportError: cannot import name 'build_analyzer' from 'presidio_tr'`

- [ ] **Adım 3: Uygula** — `src/presidio_tr/__init__.py` dosyasının tamamı

```python
"""Microsoft Presidio için Türkçe PII tanıyıcıları (resmi olmayan topluluk paketi)."""

import spacy
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import SpacyNlpEngine

from presidio_tr.recognizers import all_recognizers

LANGUAGE = "tr"


class BlankTurkishNlpEngine(SpacyNlpEngine):
    """Model indirmeden çalışan Türkçe spaCy motoru.

    v1 tanıyıcıları regex tabanlı ve NLP çıktısı kullanmıyor; Presidio yine de
    dil başına bir motor istediği için boş (blank) Türkçe pipeline yeterli.
    """

    def __init__(self) -> None:
        super().__init__(models=[{"lang_code": LANGUAGE, "model_name": "blank"}])

    def load(self) -> None:
        self.nlp = {LANGUAGE: spacy.blank(LANGUAGE)}


def add_turkish_recognizers(registry: RecognizerRegistry) -> RecognizerRegistry:
    """Türkçe tanıyıcıları verilen registry'ye ekler ve registry'yi döndürür."""
    for recognizer in all_recognizers():
        registry.add_recognizer(recognizer)
    return registry


def build_analyzer() -> AnalyzerEngine:
    """Türkçe tanıyıcılarla `language="tr"` için hazır bir AnalyzerEngine kurar."""
    nlp_engine = BlankTurkishNlpEngine()
    nlp_engine.load()
    registry = add_turkish_recognizers(RecognizerRegistry(supported_languages=[LANGUAGE]))
    return AnalyzerEngine(registry=registry, nlp_engine=nlp_engine, supported_languages=[LANGUAGE])
```

- [ ] **Adım 4: Tüm birim testlerin geçtiğini gör**

Run: `uv run pytest -q`
Expected: `52 passed`

- [ ] **Adım 5: Commit**

```bash
git add tests/unit/test_analyzer.py src/presidio_tr/__init__.py
git commit -m "feat: build Turkish analyzer on a blank spaCy pipeline"
```

---

### Görev 6: Sentetik değer üreticileri

**Dosyalar:**
- Test: `tests/unit/test_synth.py`
- Oluştur: `benchmark/__init__.py` (boş), `benchmark/synth.py`

- [ ] **Adım 1: Başarısız testi yaz** — `tests/unit/test_synth.py`

```python
import random

from benchmark import synth
from presidio_tr.validators import tckn_valid, tr_iban_valid, tr_phone_valid, vkn_valid


def test_generators_produce_valid_values():
    rng = random.Random(0)
    for _ in range(500):
        assert tckn_valid(synth.tckn(rng))
        assert vkn_valid(synth.vkn(rng))
        assert tr_iban_valid(synth.tr_iban(rng, spaced=rng.random() < 0.5))
        assert tr_phone_valid(synth.phone(rng))


def test_typo_and_order_no_fail_checksum():
    rng = random.Random(0)
    for _ in range(500):
        assert not tckn_valid(synth.typo(synth.tckn(rng), rng, tckn_valid))
        assert not vkn_valid(synth.typo(synth.vkn(rng), rng, vkn_valid))
        assert not tr_iban_valid(synth.typo(synth.tr_iban(rng, spaced=False), rng, tr_iban_valid))
        assert not tckn_valid(synth.order_no(rng))


def test_bare_phone_is_not_valid_without_prefix():
    assert not tr_phone_valid(synth.bare_phone(random.Random(0)))
```

- [ ] **Adım 2: Testin başarısız olduğunu gör**

Run: `mkdir -p benchmark && touch benchmark/__init__.py && uv run pytest tests/unit/test_synth.py -q`
Expected: FAIL — `ImportError: cannot import name 'synth' from 'benchmark'`

- [ ] **Adım 3: Uygula** — `benchmark/synth.py`

```python
"""Sentetik Türkçe PII değerleri üretir. Gerçek kişi verisi kullanılmaz."""

import random
from collections.abc import Callable

from presidio_tr.validators import tckn_valid, vkn_valid


def tckn(rng: random.Random) -> str:
    """Checksum'ı geçerli rastgele TC kimlik numarası."""
    d = [rng.randint(1, 9)] + [rng.randint(0, 9) for _ in range(8)]
    d.append((sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10)
    d.append(sum(d) % 10)
    return "".join(map(str, d))


def vkn(rng: random.Random) -> str:
    """Checksum'ı geçerli rastgele vergi kimlik numarası."""
    while True:
        candidate = "".join(str(rng.randint(0, 9)) for _ in range(10))
        if vkn_valid(candidate):
            return candidate


def tr_iban(rng: random.Random, spaced: bool) -> str:
    """mod-97'si geçerli rastgele TR IBAN."""
    bban = "".join(str(rng.randint(0, 9)) for _ in range(5)) + "0" + "".join(str(rng.randint(0, 9)) for _ in range(16))
    numeric = "".join(str(int(ch, 36)) for ch in bban + "TR00")
    iban = f"TR{98 - int(numeric) % 97:02d}{bban}"
    return " ".join(iban[i : i + 4] for i in range(0, 26, 4)) if spaced else iban


def phone(rng: random.Random) -> str:
    """+90 ya da 0 önekli Türk cep telefonu, rastgele yazım biçimiyle."""
    n = f"5{rng.randint(0, 5)}{rng.randint(0, 9)}{rng.randint(0, 9999999):07d}"
    return rng.choice(
        [
            f"+90 {n[:3]} {n[3:6]} {n[6:8]} {n[8:]}",
            f"0{n[:3]} {n[3:6]} {n[6:]}",
            f"0{n}",
            f"+90{n}",
        ]
    )


def bare_phone(rng: random.Random) -> str:
    """Öneksiz 10 haneli cep telefonu (bağlam olmadan telefon sayılmamalı)."""
    return f"5{rng.randint(0, 5)}{rng.randint(0, 9)}{rng.randint(0, 9999999):07d}"


def typo(value: str, rng: random.Random, still_valid: Callable[[str], bool]) -> str:
    """Bir hanesi değiştirilmiş, artık checksum'dan geçmeyen numara."""
    positions = [i for i, ch in enumerate(value) if ch.isdigit() and i > 0]
    while True:
        i = rng.choice(positions)
        candidate = value[:i] + str((int(value[i]) + rng.randint(1, 9)) % 10) + value[i + 1 :]
        if not still_valid(candidate):
            return candidate


def order_no(rng: random.Random) -> str:
    """TC kimliğe benzeyen ama checksum'dan geçmeyen 11 haneli sipariş numarası."""
    while True:
        candidate = str(rng.randint(10**10, 10**11 - 1))
        if not tckn_valid(candidate):
            return candidate
```

- [ ] **Adım 4: Testlerin geçtiğini gör**

Run: `uv run pytest tests/unit/test_synth.py -q`
Expected: `3 passed`

- [ ] **Adım 5: Commit**

```bash
git add tests/unit/test_synth.py benchmark/__init__.py benchmark/synth.py
git commit -m "feat: add synthetic Turkish PII value generators"
```

---

### Görev 7: Benchmark veri üretici

**Dosyalar:**
- Test: `tests/unit/test_generate.py`
- Oluştur: `benchmark/generate.py`

Her satır: `{"text", "spans": [{start, end, entity}], "negatives": [{start, end}]}`. `negatives` PII'ye benzeyen ama PII olmayan sayılardır (sipariş no, referans no); yanlış maskeleme oranı bunlarla ölçülür.

- [ ] **Adım 1: Başarısız testi yaz** — `tests/unit/test_generate.py`

```python
import random

from faker import Faker

from benchmark.generate import TEMPLATES, generate, render


def test_render_labels_pii_spans_and_negatives():
    row = render("TC {tckn}, sipariş {order_no}.", random.Random(0), Faker("tr_TR"))
    (span,) = row["spans"]
    (negative,) = row["negatives"]
    assert span["entity"] == "TR_NATIONAL_ID"
    assert row["text"][span["start"] : span["end"]].isdigit()
    assert len(row["text"][negative["start"] : negative["end"]]) == 11


def test_generate_is_deterministic_for_a_seed():
    assert generate(20, seed=7) == generate(20, seed=7)


def test_every_template_renders():
    rng, fake = random.Random(0), Faker("tr_TR")
    for template in TEMPLATES:
        row = render(template, rng, fake)
        assert "{" not in row["text"]
        for span in row["spans"] + row["negatives"]:
            assert 0 <= span["start"] < span["end"] <= len(row["text"])
```

- [ ] **Adım 2: Testin başarısız olduğunu gör**

Run: `uv run pytest tests/unit/test_generate.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'benchmark.generate'`

- [ ] **Adım 3: Uygula** — `benchmark/generate.py`

```python
"""Etiketli sentetik Türkçe benchmark verisi üretir.

Kullanım: python -m benchmark.generate --n 1000 --seed 42 --out benchmark/data/tr_pii.jsonl
"""

import argparse
import json
import random
import string
from pathlib import Path

from faker import Faker

from benchmark import synth
from presidio_tr.validators import tckn_valid, tr_iban_valid, vkn_valid

# Alan adı → (üretici, altın etiket). NEGATIVE: PII'ye benzeyen ama PII olmayan sayı;
# yanlış maskeleme oranı bunlar üzerinden ölçülür. None: ölçüme girmeyen dolgu.
NEGATIVE = "NEGATIVE"

FIELDS = {
    "tckn": (lambda r, f: synth.tckn(r), "TR_NATIONAL_ID"),
    "tckn_typo": (lambda r, f: synth.typo(synth.tckn(r), r, tckn_valid), "TR_NATIONAL_ID"),
    "vkn": (lambda r, f: synth.vkn(r), "TR_TAX_ID"),
    "vkn_typo": (lambda r, f: synth.typo(synth.vkn(r), r, vkn_valid), "TR_TAX_ID"),
    "iban": (lambda r, f: synth.tr_iban(r, spaced=r.random() < 0.5), "IBAN_CODE"),
    "iban_typo": (lambda r, f: synth.typo(synth.tr_iban(r, spaced=False), r, tr_iban_valid), "IBAN_CODE"),
    "phone": (lambda r, f: synth.phone(r), "PHONE_NUMBER"),
    "bare_phone": (lambda r, f: synth.bare_phone(r), "PHONE_NUMBER"),
    "name": (lambda r, f: f.name(), None),
    "city": (lambda r, f: f.city(), None),
    "order_no": (lambda r, f: synth.order_no(r), NEGATIVE),
    "amount": (lambda r, f: f"{r.randint(10, 99999):,}".replace(",", ".") + f",{r.randint(0, 99):02d} TL", None),
    "date": (lambda r, f: f.date(pattern="%d.%m.%Y"), None),
    "ref_no": (lambda r, f: str(r.randint(10**9, 10**10 - 1)), NEGATIVE),
}

TEMPLATES = [
    # TC kimlik
    "Merhaba, TC kimlik numaram {tckn}, başvurumun durumunu öğrenebilir miyim?",
    "Kimlik no: {tckn} — adım {name}.",
    "{name} adına kayıtlı {tckn} numaralı müşteri için işlem yapıldı.",
    "Nüfus cüzdanımdaki numara {tckn}, sistemde görünmüyor.",
    "TC'm {tckn_typo} olarak girildi ama hata veriyor.",
    "Kimliğimdeki numarayı yazıyorum: {tckn_typo}",
    "Başvuru formuna {tckn_typo} yazmışım, düzeltebilir misiniz?",
    # VKN
    "Şirketimizin vergi kimlik numarası {vkn}, faturayı buna kesin.",
    "VKN: {vkn} — {city} Vergi Dairesi.",
    "Vergi numaramız {vkn_typo} olarak görünüyor, kontrol eder misiniz?",
    # IBAN
    "Ödemeyi {iban} numaralı hesaba yapabilirsiniz.",
    "IBAN'ım {iban}, iade buraya yatsın.",
    "Hesabıma ({iban}) {amount} gönderildi mi?",
    "Hesap numaram {iban_typo} ama transfer reddedildi.",
    "İade için IBAN: {iban}",
    # Telefon
    "Bana {phone} numarasından ulaşabilirsiniz.",
    "Telefon: {phone}",
    "{name}, {phone} — {city} şubesi.",
    "Cep numaram {bare_phone}, SMS gelmedi.",
    "WhatsApp hattımız {phone}.",
    "Acil durumda {phone} arayın.",
    # Karışık
    "{name}, TC {tckn}, tel {phone}, IBAN {iban}.",
    "Müşteri {tckn} için {date} tarihli {amount} iade {iban} hesabına yapıldı.",
    "Firma VKN {vkn}, yetkili telefonu {phone}.",
    # Negatifler (PII yok)
    "Sipariş numaranız {order_no}, kargoya verildi.",
    "{date} tarihli {amount} tutarındaki faturanız hazır.",
    "Takip kodu {order_no} ile {city} aktarma merkezinde.",
    "Referans numarası {ref_no} olan talebiniz kapatıldı.",
    "Toplam {amount}, ödeme tarihi {date}.",
    "Kampanya kodu {ref_no} {date} tarihine kadar geçerli.",
]


def render(template: str, rng: random.Random, fake: Faker) -> dict:
    """Şablonu doldurur ve PII alanlarının karakter aralıklarını etiketler."""
    text, spans, negatives = "", [], []
    for literal, field, _, _ in string.Formatter().parse(template):
        text += literal
        if field is None:
            continue
        make, entity = FIELDS[field]
        value = make(rng, fake)
        if entity == NEGATIVE:
            negatives.append({"start": len(text), "end": len(text) + len(value)})
        elif entity is not None:
            spans.append({"start": len(text), "end": len(text) + len(value), "entity": entity})
        text += value
    return {"text": text, "spans": spans, "negatives": negatives}


def generate(n: int, seed: int) -> list[dict]:
    """Sabit seed ile n etiketli örnek üretir."""
    rng = random.Random(seed)
    fake = Faker("tr_TR")
    fake.seed_instance(seed)
    return [render(rng.choice(TEMPLATES), rng, fake) for _ in range(n)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("benchmark/data/tr_pii.jsonl"))
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in generate(args.n, args.seed):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{args.n} örnek yazıldı: {args.out}")


if __name__ == "__main__":
    main()
```

- [ ] **Adım 4: Testlerin geçtiğini ve verinin üretildiğini gör**

Run: `uv run pytest tests/unit/test_generate.py -q && uv run python -m benchmark.generate --n 1000 --seed 42`
Expected: `3 passed`, ardından `1000 örnek yazıldı: benchmark/data/tr_pii.jsonl`

Run: `git status --short benchmark/`
Expected: `benchmark/data/` listede **yok** (gitignore'da).

- [ ] **Adım 5: Commit**

```bash
git add tests/unit/test_generate.py benchmark/generate.py
git commit -m "feat: generate labelled synthetic Turkish benchmark data"
```

---

### Görev 8: Benchmark karşılaştırması

**Dosyalar:**
- Test: `tests/unit/test_run.py`
- Oluştur: `benchmark/run.py`, `benchmark/results/<YYYY-MM-DD>.md` (script üretir)

Baseline: hazır tanıyıcılar + `language=en` + `en_core_web_sm` (Türkçe desteği olmayan kullanıcının elindeki). `en_core_web_sm` `benchmark` bağımlılık grubunda.

- [ ] **Adım 1: Başarısız testi yaz** — `tests/unit/test_run.py`

```python
from benchmark.run import score

ROWS = [
    {
        "text": "TC 10000000146 sipariş 48213390571",
        "spans": [{"start": 3, "end": 14, "entity": "TR_NATIONAL_ID"}],
        "negatives": [{"start": 23, "end": 34}],
    }
]


def test_score_counts_typed_match_as_true_positive():
    counts, overmask = score(ROWS, lambda text: [(3, 14, "TR_NATIONAL_ID")])
    c = counts["TR_NATIONAL_ID"]
    assert (c.tp, c.fp, c.fn, c.masked) == (1, 0, 0, 1)
    assert overmask == 0.0


def test_score_counts_wrong_type_as_masked_but_not_recalled():
    counts, overmask = score(ROWS, lambda text: [(3, 14, "US_BANK_NUMBER"), (23, 34, "US_BANK_NUMBER")])
    c = counts["TR_NATIONAL_ID"]
    assert (c.tp, c.fn, c.masked) == (0, 1, 1)
    assert overmask == 1.0


def test_score_counts_unmatched_prediction_as_false_positive():
    counts, _ = score(ROWS, lambda text: [(23, 34, "TR_NATIONAL_ID")])
    assert counts["TR_NATIONAL_ID"].fp == 1
```

- [ ] **Adım 2: Testin başarısız olduğunu gör**

Run: `uv run pytest tests/unit/test_run.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'benchmark.run'`

- [ ] **Adım 3: Uygula** — `benchmark/run.py`

```python
"""Varsayılan Presidio ile Presidio + presidio-tr'yi aynı veri üzerinde karşılaştırır.

Kullanım: python -m benchmark.run --data benchmark/data/tr_pii.jsonl --out-dir benchmark/results
"""

import argparse
import datetime
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from presidio_tr import build_analyzer

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
```

- [ ] **Adım 4: Testleri ve benchmark'ı çalıştır**

Run: `uv run pytest tests/unit/test_run.py -q`
Expected: `3 passed`

Run: `uv sync --group benchmark && uv run python -m benchmark.run`
Expected: iki tablo basılır ve `Yazıldı: benchmark/results/<bugün>.md`. Prototipte (seed 42, 1000 satır) görülen değerler — Faker/Presidio sürümü farklıysa ±0.01–0.02 oynayabilir:

```text
| Presidio + presidio-tr | TR_NATIONAL_ID | 1.00 | 0.93 | 0.96 | 0.93 |
| Presidio + presidio-tr | TR_TAX_ID | 0.93 | 1.00 | 0.96 | 1.00 |
| Presidio + presidio-tr | IBAN_CODE | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr | PHONE_NUMBER | 0.96 | 1.00 | 0.98 | 1.00 |
| Presidio (en, varsayılan) | 1.00 |   ← yanlış maskeleme
| Presidio + presidio-tr | 0.06 |      ← yanlış maskeleme
```

TR_NATIONAL_ID recall'unun 0.93 olması beklenen: bağlamsız, checksum'ı bozuk TCKN şablonu ("Başvuru formuna … yazmışım") tasarım gereği maskelenmez. README'de bu takas olarak yazılır.

- [ ] **Adım 5: Commit**

```bash
git add tests/unit/test_run.py benchmark/run.py benchmark/results/
git commit -m "feat: compare default Presidio with presidio-tr on synthetic data"
```

---

### Görev 9: Analyzer HTTP sunucusu

**Dosyalar:**
- Test: `tests/unit/test_server.py`
- Oluştur: `src/presidio_tr/server.py`

LiteLLM `POST {base}/analyze` çağırır, gövdede `text`, `language` ve isteğe bağlı `entities` gönderir; cevapta `entity_type/start/end/score` listesi bekler. Bilinmeyen alanlar (ör. `ad_hoc_recognizers`) Pydantic tarafından yok sayılır. Desteklenmeyen dil 400 döner — LiteLLM `output_parse_pii` açıkken ≥400'de isteği reddeder (fail-closed).

- [ ] **Adım 1: Başarısız testi yaz** — `tests/unit/test_server.py`

```python
from fastapi.testclient import TestClient

from presidio_tr.server import app

client = TestClient(app)


def test_health():
    assert client.get("/health").status_code == 200


def test_analyze_returns_presidio_compatible_items():
    response = client.post("/analyze", json={"text": "TC 10000000146", "language": "tr"})
    assert response.status_code == 200
    assert response.json() == [{"entity_type": "TR_NATIONAL_ID", "start": 3, "end": 14, "score": 1.0}]


def test_analyze_filters_by_requested_entities():
    response = client.post(
        "/analyze",
        json={"text": "TC 10000000146, tel 0532 123 45 67", "language": "tr", "entities": ["PHONE_NUMBER"]},
    )
    assert [item["entity_type"] for item in response.json()] == ["PHONE_NUMBER"]


def test_analyze_rejects_unsupported_language():
    response = client.post("/analyze", json={"text": "x", "language": "en"})
    assert response.status_code == 400
```

- [ ] **Adım 2: Testin başarısız olduğunu gör**

Run: `uv run pytest tests/unit/test_server.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'presidio_tr.server'`

- [ ] **Adım 3: Uygula** — `src/presidio_tr/server.py`

```python
"""Presidio analyzer HTTP API'siyle uyumlu, presidio-tr tanıyıcılarını kullanan sunucu.

LiteLLM'in Presidio guardrail'i bu sunucunun /analyze ucunu çağırır.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from presidio_tr import LANGUAGE, build_analyzer

app = FastAPI(title="presidio-tr analyzer")
analyzer = build_analyzer()


class AnalyzeRequest(BaseModel):
    text: str
    language: str = LANGUAGE
    entities: list[str] | None = None


@app.get("/health")
def health() -> str:
    return "Presidio Analyzer service is up"


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> list[dict]:
    if request.language != LANGUAGE:
        raise HTTPException(status_code=400, detail=f"Desteklenmeyen dil: {request.language}")
    results = analyzer.analyze(text=request.text, language=request.language, entities=request.entities)
    return [{"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": r.score} for r in results]
```

- [ ] **Adım 4: Tüm birim testler + lint**

Run: `uv run pytest -q && uv run ruff check . && uv run ruff format --check .`
Expected: `65 passed`, `All checks passed!`, tüm dosyalar formatlı.

- [ ] **Adım 5: Commit**

```bash
git add tests/unit/test_server.py src/presidio_tr/server.py
git commit -m "feat: expose Presidio-compatible /analyze endpoint"
```

---

### Görev 10: Docker Compose demosu

**Dosyalar:**
- Oluştur: `deploy/analyzer.Dockerfile`, `deploy/docker-compose.yml`, `deploy/litellm-config.yaml`, `deploy/.env.example`, `deploy/langfuse/docker-compose.yml` (resmi dosyanın kopyası)

Ön koşul: Docker Desktop açık; `OPENAI_API_KEY` elinde. Yerelde şu portlar boş olmalı: 3000, 3030, 3031, 4000, 5432, 6379, 8123, 9000, 9090, 9091 (plan yazılırken boştu).

- [ ] **Adım 1: Langfuse'un resmi compose'unu sabit sürümden kopyala**

Run: `mkdir -p deploy/langfuse && curl -sf -o deploy/langfuse/docker-compose.yml https://raw.githubusercontent.com/langfuse/langfuse/v4.80.0/docker-compose.yml && wc -l deploy/langfuse/docker-compose.yml`
Expected: `299 deploy/langfuse/docker-compose.yml`

- [ ] **Adım 2: `deploy/analyzer.Dockerfile` yaz**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir ".[server]"

EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3000/health')"
CMD ["uvicorn", "presidio_tr.server:app", "--host", "0.0.0.0", "--port", "3000"]
```

- [ ] **Adım 3: `deploy/litellm-config.yaml` yaz**

```yaml
model_list:
  - model_name: gpt-4.1-mini
    litellm_params:
      model: openai/gpt-4.1-mini
      api_key: os.environ/OPENAI_API_KEY

guardrails:
  - guardrail_name: presidio-tr
    litellm_params:
      guardrail: presidio
      mode: pre_call
      default_on: true
      presidio_language: tr
      output_parse_pii: true
      presidio_analyzer_api_base: http://presidio-analyzer:3000
      presidio_anonymizer_api_base: http://presidio-anonymizer:3000

litellm_settings:
  success_callback: ["langfuse"]

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL
```

- [ ] **Adım 4: `deploy/docker-compose.yml` yaz**

```yaml
# Langfuse'un resmi compose'u (deploy/langfuse/) aynı .env ile dahil edilir.
include:
  - path: langfuse/docker-compose.yml
    env_file: .env

services:
  presidio-analyzer:
    build:
      context: ..
      dockerfile: deploy/analyzer.Dockerfile

  presidio-anonymizer:
    image: mcr.microsoft.com/presidio-anonymizer:2.2.362

  litellm-db:
    image: docker.io/postgres:17
    environment:
      POSTGRES_USER: litellm
      POSTGRES_PASSWORD: litellm
      POSTGRES_DB: litellm
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U litellm"]
      interval: 5s
      retries: 10

  litellm:
    image: ghcr.io/berriai/litellm:v1.109.1
    command: ["--config", "/app/config.yaml", "--port", "4000"]
    volumes:
      - ./litellm-config.yaml:/app/config.yaml:ro
    ports:
      - 127.0.0.1:4000:4000
    environment:
      DATABASE_URL: postgresql://litellm:litellm@litellm-db:5432/litellm
      LITELLM_MASTER_KEY: ${LITELLM_MASTER_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      LANGFUSE_PUBLIC_KEY: ${LANGFUSE_INIT_PROJECT_PUBLIC_KEY}
      LANGFUSE_SECRET_KEY: ${LANGFUSE_INIT_PROJECT_SECRET_KEY}
      LANGFUSE_HOST: http://langfuse-web:3000
    depends_on:
      presidio-analyzer:
        condition: service_healthy
      presidio-anonymizer:
        condition: service_started
      litellm-db:
        condition: service_healthy
      langfuse-web:
        condition: service_started
```

- [ ] **Adım 5: `deploy/.env.example` yaz ve kendi `.env`'ini oluştur**

```dotenv
# Kopyala: cp deploy/.env.example deploy/.env — deploy/.env git'e girmez.
OPENAI_API_KEY=
LITELLM_MASTER_KEY=sk-master-change-me

# Langfuse ilk açılışta bu org/proje/anahtarlarla kurulur (headless init).
LANGFUSE_INIT_ORG_ID=presidio-tr
LANGFUSE_INIT_ORG_NAME=presidio-tr
LANGFUSE_INIT_PROJECT_ID=presidio-tr-demo
LANGFUSE_INIT_PROJECT_NAME=presidio-tr-demo
LANGFUSE_INIT_PROJECT_PUBLIC_KEY=pk-lf-demo
LANGFUSE_INIT_PROJECT_SECRET_KEY=sk-lf-demo
LANGFUSE_INIT_USER_EMAIL=admin@example.com
LANGFUSE_INIT_USER_NAME=admin
LANGFUSE_INIT_USER_PASSWORD=change-me-please
```

Run: `cp deploy/.env.example deploy/.env` — sonra `deploy/.env` içinde `OPENAI_API_KEY`'i doldur (kullanıcı yapar; ajan anahtarı görmez, yazmaz).

Run: `git status --short deploy/`
Expected: `deploy/.env` listede **yok**; `.env.example` var.

- [ ] **Adım 6: Config'in çözüldüğünü doğrula**

Run: `docker compose -f deploy/docker-compose.yml config --services | sort`
Expected:

```text
clickhouse
langfuse-ai-gateway
langfuse-web
langfuse-worker
litellm
litellm-db
minio
postgres
presidio-analyzer
presidio-anonymizer
redis
```

Run: `docker compose -f deploy/docker-compose.yml config | grep -c "pk-lf-demo"`
Expected: `2` ya da daha fazla (Langfuse init + LiteLLM).

- [ ] **Adım 7: Ayağa kaldır ve duman testi**

Run: `docker compose -f deploy/docker-compose.yml up -d --build --wait` (ilk seferde imaj çekme birkaç dakika sürer; Bash'te `run_in_background` ile çalıştır)
Expected: tüm servisler `Healthy`/`Started`.

Run:

```bash
set -a && . deploy/.env && set +a
curl -s http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" -H "Content-Type: application/json" \
  -d '{"model":"gpt-4.1-mini","temperature":0,"messages":[{"role":"system","content":"Kullanıcının mesajını aynen tekrar et; <...> etiketlerini de aynen koru."},{"role":"user","content":"TC kimlik no 10000000146, telefon 0532 123 45 67."}]}' \
  | python -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

Expected: `TC kimlik no 10000000146, telefon 0532 123 45 67.` — gerçek değerler geri açılmış.

Run: `docker compose -f deploy/docker-compose.yml logs litellm 2>&1 | grep -i -E "error|exception" | head`
Expected: boş. Doluysa (ör. Langfuse callback hatası) Görev 11 Adım 3'teki yedek config'e bak.

- [ ] **Adım 8: Commit**

```bash
git add deploy/analyzer.Dockerfile deploy/docker-compose.yml deploy/litellm-config.yaml deploy/.env.example deploy/langfuse/docker-compose.yml
git commit -m "feat: add LiteLLM + Presidio + Langfuse compose demo"
```

---

### Görev 11: Uçtan uca testler

**Dosyalar:**
- Oluştur: `tests/e2e/test_gateway.py`

Compose ayaktayken çalışır; varsayılan `pytest` çalıştırmasında atlanır (`addopts = -m 'not e2e'`). Komut satırındaki `-m e2e` addopts'u geçersiz kılar.

- [ ] **Adım 1: Testleri yaz** — `tests/e2e/test_gateway.py`

```python
"""Compose ayaktayken çalışan uçtan uca testler.

Kullanım: set -a && . deploy/.env && set +a && uv run pytest -m e2e -v
"""

import json
import os
import subprocess
import time

import httpx
import pytest

pytestmark = pytest.mark.e2e

LITELLM = os.environ.get("LITELLM_BASE_URL", "http://localhost:4000")
LANGFUSE = os.environ.get("LANGFUSE_BASE_URL", "http://localhost:3000")
MODEL = os.environ.get("E2E_MODEL", "gpt-4.1-mini")
COMPOSE = ["docker", "compose", "-f", "deploy/docker-compose.yml"]

TCKN_1 = "10000000146"
TCKN_2 = "12345678950"
PHONE = "0532 123 45 67"


def _master_key() -> str:
    return os.environ["LITELLM_MASTER_KEY"]


def _langfuse_auth() -> tuple[str, str]:
    return os.environ["LANGFUSE_INIT_PROJECT_PUBLIC_KEY"], os.environ["LANGFUSE_INIT_PROJECT_SECRET_KEY"]


def _echo(payload: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": "Kullanıcının mesajını hiç değiştirmeden aynen tekrar et; <...> etiketlerini de aynen koru.",
        },
        {"role": "user", "content": payload},
    ]


def _chat(messages: list[dict], key: str | None = None, user: str = "e2e-user", **extra) -> httpx.Response:
    return httpx.post(
        f"{LITELLM}/v1/chat/completions",
        headers={"Authorization": f"Bearer {key or _master_key()}"},
        json={"model": MODEL, "messages": messages, "user": user, "temperature": 0, **extra},
        timeout=60,
    )


def _content(response: httpx.Response) -> str:
    assert response.status_code == 200, response.text
    return response.json()["choices"][0]["message"]["content"]


def test_non_streaming_masks_and_restores():
    content = _content(_chat(_echo(f"TC kimlik no {TCKN_1}, telefon {PHONE}.")))
    assert TCKN_1 in content
    assert PHONE in content


def test_streaming_masks_and_restores():
    text = ""
    with httpx.stream(
        "POST",
        f"{LITELLM}/v1/chat/completions",
        headers={"Authorization": f"Bearer {_master_key()}"},
        json={"model": MODEL, "messages": _echo(f"TC kimlik no {TCKN_1}."), "temperature": 0, "stream": True},
        timeout=60,
    ) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            for choice in json.loads(line[len("data: ") :]).get("choices", []):
                text += choice.get("delta", {}).get("content") or ""
    assert TCKN_1 in text


def test_two_values_of_same_type_are_restored_in_order():
    content = _content(_chat(_echo(f"Birinci TC {TCKN_1}, ikinci TC {TCKN_2}.")))
    assert content.index(TCKN_1) < content.index(TCKN_2)


def test_langfuse_never_sees_raw_pii_and_keeps_end_user():
    user = f"e2e-{time.time_ns()}"
    _content(_chat(_echo(f"TC kimlik no {TCKN_1}."), user=user))
    deadline = time.time() + 120
    traces: list[dict] = []
    while time.time() < deadline and not traces:
        response = httpx.get(
            f"{LANGFUSE}/api/public/traces", params={"userId": user}, auth=_langfuse_auth(), timeout=10
        )
        traces = response.json().get("data", []) if response.status_code == 200 else []
        if not traces:
            time.sleep(3)
    assert traces, "Langfuse'ta bu kullanıcıya ait iz bulunamadı (attribution ya da callback çalışmıyor)"
    trace = httpx.get(f"{LANGFUSE}/api/public/traces/{traces[0]['id']}", auth=_langfuse_auth(), timeout=10)
    assert trace.status_code == 200
    assert TCKN_1 not in trace.text


def test_budget_exceeded_key_is_rejected():
    created = httpx.post(
        f"{LITELLM}/key/generate",
        headers={"Authorization": f"Bearer {_master_key()}"},
        json={"max_budget": 0},
        timeout=30,
    )
    assert created.status_code == 200, created.text
    response = _chat([{"role": "user", "content": "merhaba"}], key=created.json()["key"])
    assert response.status_code >= 400
    assert "budget" in response.text.lower()


def test_fails_closed_when_analyzer_is_down():
    subprocess.run([*COMPOSE, "stop", "presidio-analyzer"], check=True)
    try:
        response = _chat(_echo(f"TC kimlik no {TCKN_1}."))
        assert response.status_code >= 400
    finally:
        subprocess.run([*COMPOSE, "up", "-d", "--wait", "presidio-analyzer"], check=True)
```

- [ ] **Adım 2: Testleri çalıştır**

Run: `set -a && . deploy/.env && set +a && uv run pytest -m e2e -v`
Expected: `6 passed`

- [ ] **Adım 3: Başarısızlık olursa — iki bilinen olasılık**

Spec "Riskler" 4: Langfuse'a ham PII gidiyorsa `test_langfuse_never_sees_raw_pii_and_keeps_end_user` `TCKN_1 not in trace.text` satırında düşer. Çözüm: `deploy/litellm-config.yaml` içinde `guardrails:` listesine ikinci bir giriş ekle (log kopyasını maskeler, canlı isteğe dokunmaz):

```yaml
  - guardrail_name: presidio-tr-logs
    litellm_params:
      guardrail: presidio
      mode: logging_only
      default_on: true
      presidio_language: tr
      presidio_analyzer_api_base: http://presidio-analyzer:3000
      presidio_anonymizer_api_base: http://presidio-anonymizer:3000
```

Aynı test "iz bulunamadı" ile düşüyorsa LiteLLM'in `langfuse` callback'i Langfuse v4'e yazamıyor demektir: `litellm_settings` altında `success_callback: ["langfuse"]` yerine `callbacks: ["langfuse_otel"]` yaz ve compose'da `litellm.environment` içine `LANGFUSE_OTEL_HOST: http://langfuse-web:3000` ekle.

`test_budget_exceeded_key_is_rejected` 200 dönüyorsa LiteLLM `max_budget: 0`'ı "limitsiz" sayıyor demektir: değeri `0.000001` yap, testte aynı anahtarla iki istek at ve ikincisinin reddedildiğini doğrula.

Her düzeltmeden sonra: `docker compose -f deploy/docker-compose.yml up -d --wait litellm` ve Adım 2'yi tekrarla. Hangi yedeğin gerektiğini spec'in "Riskler" bölümüne yaz (madde 4 ya da ilgili madde "çözüldü" olur).

- [ ] **Adım 4: Commit**

```bash
git add tests/e2e/test_gateway.py deploy/litellm-config.yaml deploy/docker-compose.yml docs/superpowers/specs/2026-11-14-presidio-tr-design.md
git commit -m "test: add end-to-end gateway tests for masking, logging, budget and fail-closed"
```

---

### Görev 12: Etiket bozulma oranı ölçümü

**Dosyalar:**
- Oluştur: `deploy/measure_unmask.py`

Spec "Hata yönetimi": model etiketi bozarsa geri açma başarısız olur. Bu script, modelin değeri kendi cümlesinde kullanması gereken görevlerde ne sıklıkla olduğunu ölçer.

- [ ] **Adım 1: Script'i yaz** — `deploy/measure_unmask.py`

```python
"""Modelin maskeleme etiketlerini koruyup korumadığını ölçer (compose ayaktayken).

Kullanım: set -a && . deploy/.env && set +a && uv run python deploy/measure_unmask.py
"""

import os
import re

import httpx

LITELLM = os.environ.get("LITELLM_BASE_URL", "http://localhost:4000")
MODEL = os.environ.get("E2E_MODEL", "gpt-4.1-mini")
PLACEHOLDER = re.compile(r"<[A-Z_]+_\d+>")

# (görev, cevapta görünmesi gereken değer)
TASKS = [
    (
        "Müşteri 10000000146 TC kimlik numarasıyla başvurdu. Başvurunun alındığını bildiren kısa bir mesaj yaz ve numarayı belirt.",
        "10000000146",
    ),
    ("TC kimlik no 12345678950 olan kişi için kayıt özetini tek cümleyle yaz, numarayı da yaz.", "12345678950"),
    (
        "İade TR33 0006 1005 1978 6457 8413 26 IBAN'ına yapılacak. Müşteriye iadenin hangi IBAN'a yatacağını söyleyen bir mesaj yaz.",
        "TR33 0006 1005 1978 6457 8413 26",
    ),
    (
        "Firmanın vergi kimlik numarası 1234567890. Fatura notuna eklenecek bir cümle yaz ve VKN'yi belirt.",
        "1234567890",
    ),
    (
        "Müşteriyi 0532 123 45 67 numarasından aramamız gerekiyor. Ekibe bunu hatırlatan bir not yaz, numarayı belirt.",
        "0532 123 45 67",
    ),
    ("Aşağıdaki bilgiyi resmi bir dille yeniden yaz: telefonum +90 532 123 45 67.", "+90 532 123 45 67"),
    ("TC 10000000146 için randevu oluşturuldu. Bunu İngilizceye çevir.", "10000000146"),
    (
        "Hesap bilgisi: TR330006100519786457841326. Bu IBAN'ı müşteriye teyit eden kısa bir e-posta yaz.",
        "TR330006100519786457841326",
    ),
    (
        "Şu cümleyi kısalt: 'Sayın müşterimiz, 12345678950 numaralı TC kimliğinize kayıtlı başvurunuz onaylanmıştır.'",
        "12345678950",
    ),
    ("VKN 1234567890 olan firma için bir hatırlatma SMS'i yaz, VKN'yi içersin.", "1234567890"),
]


def main() -> None:
    restored = placeholder_left = dropped = 0
    for task, value in TASKS:
        response = httpx.post(
            f"{LITELLM}/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['LITELLM_MASTER_KEY']}"},
            json={"model": MODEL, "temperature": 0, "messages": [{"role": "user", "content": task}]},
            timeout=60,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if value in content:
            restored += 1
        elif PLACEHOLDER.search(content):
            placeholder_left += 1
        else:
            dropped += 1
    print(
        f"{len(TASKS)} görev: {restored} geri açıldı, {placeholder_left} etiket açılamadan kaldı, {dropped} değer modelce düşürüldü/değiştirildi"
    )


if __name__ == "__main__":
    main()
```

- [ ] **Adım 2: Çalıştır**

Run: `set -a && . deploy/.env && set +a && uv run python deploy/measure_unmask.py`
Expected: `10 görev: X geri açıldı, Y etiket açılamadan kaldı, Z değer modelce düşürüldü/değiştirildi` — X+Y+Z=10. Bu satırı Görev 14'te README'nin "Bilinen sınırlamalar" bölümüne tarih ve model adıyla yaz.

- [ ] **Adım 3: Lint + commit**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: `All checks passed!`

```bash
git add deploy/measure_unmask.py
git commit -m "feat: measure how often the model breaks masking placeholders"
```

---

### Görev 13: pre-commit (gitleaks + ruff) ve CI

**Dosyalar:**
- Oluştur: `.pre-commit-config.yaml`, `.github/workflows/ci.yml`

- [ ] **Adım 1: `.pre-commit-config.yaml` yaz**

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
      - id: ruff-format
```

Run: `uvx pre-commit autoupdate && uvx pre-commit install && uvx pre-commit run --all-files`
Expected: `rev` değerleri en güncel sürümlere çekilir; `gitleaks....Passed`, `ruff....Passed`, `ruff format....Passed`.

- [ ] **Adım 2: gitleaks'in gerçekten yakaladığını gör**

Run: `printf 'OPENAI_API_KEY=sk-proj-%s\n' "$(python -c 'import secrets;print(secrets.token_hex(24))')" > leak_test.txt && git add leak_test.txt && uvx pre-commit run gitleaks; git rm --cached -q leak_test.txt; rm leak_test.txt`
Expected: `gitleaks....Failed` ve bulunan sır raporu. (Dosya commit'lenmez, sonra silinir.)

- [ ] **Adım 3: `.github/workflows/ci.yml` yaz**

```yaml
name: ci

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run pytest
```

E2E testleri API anahtarı istediği için CI'da yok (spec "Test").

- [ ] **Adım 4: Commit**

```bash
git add .pre-commit-config.yaml .github/workflows/ci.yml
git commit -m "ci: add gitleaks/ruff pre-commit and unit-test workflow"
```

---

### Görev 14: README (TR + EN)

**Dosyalar:**
- Değiştir: `README.md` (taslağın yerine tamamı)
- Oluştur: `README_EN.md`

- [ ] **Adım 1: `README.md` yaz** — bölümler ve içerikleri:

1. Başlık + tek cümle + **"Microsoft'un resmi projesi değildir; topluluk paketidir."** notu.
2. **Neden:** Presidio'da TC kimlik ve VKN tanıyıcısı yok; hazır tanıyıcılar `en` için kayıtlı, `language=tr` ile IBAN/telefon da çalışmıyor; `en` ile çalıştırınca her sayı `US_BANK_NUMBER`/`DATE_TIME` olarak maskeleniyor.
3. **Benchmark:** `benchmark/results/` altındaki en güncel dosyanın iki tablosunu aynen kopyala; altına "1000 sentetik cümle, seed 42, `uv run python -m benchmark.generate && uv run python -m benchmark.run` ile yeniden üretilir" yaz.
4. **Kurulum ve kullanım (kütüphane):**

```python
from presidio_tr import build_analyzer

analyzer = build_analyzer()
analyzer.analyze("TC kimlik no 10000000146", language="tr")
```

   Var olan bir registry'ye eklemek için `add_turkish_recognizers(registry)`.
5. **Skorlama:** spec'teki üç kademeli tablo (geçerli → 1.0, geçersiz + bağlam → 0.6, ikisi de yok → atılır) ve neden (bir hanesi yanlış TCKN sızmasın, sipariş no maskelenmesin).
6. **Türkçe bağlam notu:** lemma yerine kök öneki, ünsüz yumuşaması (`hesap`/`hesab`), "IBAN" → "ıban" küçültme tuzağı — üçer satır.
7. **Gateway demosu:** mimari şema (aşağıdaki), `cp deploy/.env.example deploy/.env`, `docker compose -f deploy/docker-compose.yml up -d --build --wait`, Görev 10 Adım 7'deki `curl`, Langfuse arayüzü `http://localhost:3000` (`.env`'deki kullanıcıyla).

```text
istemci ──► LiteLLM :4000 ──(pre-call)──► presidio-tr analyzer ──► presidio anonymizer
              │  maskeli istek                                     (<TR_NATIONAL_ID_1>)
              ▼
          LLM sağlayıcı ──► cevap ──► LiteLLM etiketleri geri açar ──► istemci
              │
              └──► Langfuse (yalnızca maskeli metin)
```

8. **Testler:** `uv run pytest` (birim), `set -a && . deploy/.env && set +a && uv run pytest -m e2e` (uçtan uca).
9. **Bilinen sınırlamalar:** bağlamsız ve checksum'ı bozuk TCKN maskelenmez; isim/adres yok (NER v2); model etiketi bozarsa geri açılamaz — Görev 12'nin çıktı satırı, tarih ve modelle; Anthropic native yolunda LiteLLM hatası (BerriAI/litellm#22821).
10. **Lisans:** MIT.

- [ ] **Adım 2: `README_EN.md` yaz** — `README.md`'nin İngilizce karşılığı, aynı bölümler ve aynı tablolar. En üstte iki dosya birbirine link versin: `[Türkçe](README.md) · [English](README_EN.md)`.

- [ ] **Adım 3: Doğrula**

Run: `grep -c "resmi projesi değildir" README.md && grep -c "not an official" README_EN.md`
Expected: `1` ve `1`

Run: `uv run pytest -q`
Expected: `65 passed`

- [ ] **Adım 4: Commit**

```bash
git add README.md README_EN.md
git commit -m "docs: add Turkish and English README with benchmark and demo"
```

---

## Bitti tanımı (spec'ten)

- [ ] `docker compose up` + README'deki tek `curl` demoyu gösteriyor (Görev 10 Adım 7).
- [ ] Benchmark tablosu README'de (Görev 14).
- [ ] Birim testler CI'da geçiyor (Görev 13 — ilk push'tan sonra Actions sekmesinde görülür; push kullanıcının kararı).
- [ ] E2E testler lokalde geçiyor (Görev 11).
