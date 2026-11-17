# presidio-tr

[Türkçe](https://github.com/YusufAltuntas/presidio-tr/blob/main/README.md) · [English](https://github.com/YusufAltuntas/presidio-tr/blob/main/README_EN.md)

Microsoft Presidio için Türkçe kişisel veri (PII) tanıyıcıları: TC kimlik no, VKN, TR IBAN, TR telefon ve isteğe bağlı
isim.
Bir LiteLLM gateway demosuyla birlikte gelir: Türkçe metindeki kişisel veri LLM sağlayıcısına gitmeden maskelenir,
cevapta geri açılır. Microsoft'un resmi projesi değildir; topluluk paketidir.

**Kısaca** (1000 sentetik cümle, Türkçe kurulmuş Presidio'ya karşı):

- VKN: Presidio'da tanıyıcısı yok; `presidio-tr` ile F1 0.79.
- TR telefon F1: 0.72 → 0.89. IBAN F1: 0.93 → 1.00.
- Bir hanesi yanlış yazılmış TCKN/VKN/IBAN, yanında bağlam kelimesi varsa yine maskelenir. Bedeli:
  PII olmayan sayıların daha çoğu maskelenir (aşağıdaki Ödünleşim).
- İsim (isteğe bağlı, Türkçe NER modeli): üçüncü taraf bir bankacılık mesajı setinde F1 0.93 (124 isimden 123'ü).
- Gateway demosu: LLM sağlayıcısı yalnızca maskeli metni görür; Langfuse da analyzer ve anonymizer sağlıklıyken.

## Kurulum ve kullanım

PyPI'da yayınlı değil; repodan kurulur:

```bash
git clone https://github.com/YusufAltuntas/presidio-tr.git && cd presidio-tr
uv sync
```

```python
from presidio_tr import build_analyzer

analyzer = build_analyzer()
analyzer.analyze("TC kimlik no 10000000146", language="tr")
```

Model indirmek gerekmez (boş spaCy `tr` pipeline'ı). Varlık adları upstream ile aynıdır (`TR_NATIONAL_ID`,
`TR_TAX_ID`, `IBAN_CODE`, `PHONE_NUMBER`). `build_analyzer()` Presidio'nun hazır e-posta (`EMAIL_ADDRESS`) ve kredi
kartı (`CREDIT_CARD`) tanıyıcılarını da ekler. `add_turkish_recognizers(registry)` yalnızca dört Türkçe tanıyıcıyı
ekler ve yalnızca `tr` için kurulmuş bir registry ile çalışır; doğru kurulum için `build_analyzer()` kaynağına bakın (`src/presidio_tr/__init__.py`).

İsim tanıma (`PERSON`) isteğe bağlıdır: Hugging Face'teki `akdeniz27/bert-base-turkish-cased-ner` modelini kullanır,
transformers + torch ister ve model ilk kullanımda indirilir (~440 MB). CPU'da cümle başına ~50 ms ekler.

```bash
uv sync --extra ner
```

```python
analyzer = build_analyzer(ner=True)
```

## Nasıl çalışır

Regex aday bulur, doğrulayıcı (checksum) ve yakındaki bağlam kelimesi skoru belirler:

| Durum | Sonuç |
|---|---|
| Checksum geçerli | Skor 1.0, maskelenir |
| Checksum geçersiz, yakında bağlam kelimesi var | Skor 0.6, maskelenir |
| Checksum geçersiz, bağlam yok | Atılır |

- Telefonun checksum'ı yok; önekli (+90 / 0090 / 90 / 0) numara bağlamsız da maskelenir, öneksiz 10 hane bağlam ister.
- VKN'nin tek kontrol hanesi var, rastgele 10 haneli sayıların ~%10'u geçer; bu yüzden VKN her zaman bağlam ister.
- Bağlam eşleştirme Türkçe ekleri tolere eder ("IBAN'ım", "hesabınız", "T.C."). Kısa kökler (`tc`, `tel`, `cep`)
  yalnızca tam kelimeyle eşleşir, "telif" ya da "cephe" bağlam sayılmaz.

Tasarım gerekçeleri ve ayrıntılar: [`docs/design.md`](docs/design.md).

## Benchmark

F1, varlık türü başına. Yanlış maskeleme: PII olmayan sayıların (sipariş no, referans no) maskelenme oranı.

**Ana set** (1000 cümle):

| Sistem | TCKN | VKN | IBAN | Telefon | İsim | Yanlış maskeleme |
|---|---|---|---|---|---|---|
| Presidio, varsayılan (`en`) | 0.00 | 0.00 | 0.93 | 0.51 | 0.34 | 1.00 |
| Presidio, Türkçe kurulmuş (adil taban çizgisi) | 0.78 | 0.00 | 0.93 | 0.72 | 0.00 | 0.10 |
| Presidio + presidio-tr | 0.81 | 0.79 | 1.00 | 0.89 | — | 0.45 |
| Presidio + presidio-tr, `score_threshold=0.7` | 0.78 | 0.77 | 0.93 | 0.87 | — | 0.02 |
| Presidio + presidio-tr, `ner=True` | 0.81 | 0.79 | 1.00 | 0.89 | 0.98 | 0.45 |

**Bağımsız set** (tanıyıcıları görmeden, koda erişimi olmayan ayrı bir LLM ajanına yazdırılmış 24 şablon):

| Sistem | TCKN | VKN | IBAN | Telefon | İsim | Yanlış maskeleme |
|---|---|---|---|---|---|---|
| Presidio, varsayılan (`en`) | 0.00 | 0.00 | 0.83 | 0.38 | 0.46 | 1.00 |
| Presidio, Türkçe kurulmuş (adil taban çizgisi) | 0.82 | 0.00 | 0.83 | 0.69 | 0.00 | 0.11 |
| Presidio + presidio-tr | 0.88 | 0.77 | 1.00 | 0.85 | — | 0.18 |
| Presidio + presidio-tr, `score_threshold=0.7` | 0.82 | 0.65 | 0.83 | 0.65 | — | 0.01 |
| Presidio + presidio-tr, `ner=True` | 0.88 | 0.77 | 1.00 | 0.85 | 1.00 | 0.18 |

Adil taban çizgisi: `language="tr"`, Presidio'nun hazır tanıyıcıları, elle açılan `TrNationalIdRecognizer` ve
`supported_regions=["TR"]` ile kurulmuş `PhoneRecognizer`. Precision, recall ve tür gözetmeyen maskeleme oranı
sonuç dosyalarında: [`benchmark/results/2026-11-16.md`](benchmark/results/2026-11-16.md),
[`2026-11-16-heldout.md`](benchmark/results/2026-11-16-heldout.md). "—": isim tanıma kapalı.

Şablonlardaki isimler kolaydır (büyük harfle, tam ad, belirgin yerlerde); gerçekçi isim sonucu için aşağıdaki
üçüncü taraf setlere bakın. Model skorları bazen 0.7'nin altında kalır ("Ayşe Yılmaz"da "Yılmaz" 0.58);
`score_threshold=0.7` ile bu isimler maskelenmez.

Veri tamamen sentetiktir (Faker `tr_TR` + şablonlar, seed 42). Bağlam kelimesinin yanında duran PII olmayan
sayılar ("Kimlik doğrulama kodunuz ...") ve bağlamsız zor PII örnekleri bilerek eklenmiştir. Yeniden üretmek için:

```bash
uv sync --group benchmark && uv run python -m benchmark.generate --n 1000 --seed 42 && uv run python -m benchmark.run
uv run python -m benchmark.generate --templates heldout --out benchmark/data/tr_pii_heldout.jsonl && uv run python -m benchmark.run --data benchmark/data/tr_pii_heldout.jsonl --tag heldout
```

İsim satırı için `uv sync --group benchmark --extra ner` ile kurup `benchmark.run`'a `--ner` ekleyin.

### Üçüncü taraf setler

Başkalarının yayınladığı üç Türkçe PII seti sabit sürümle indirilir (`uv run python -m benchmark.external`). Hepsi
sentetiktir ama bizim şablonlarımızdan bağımsızdır; tanıyıcılar bu setlere göre ayarlanmadı. F1:

| Set | Sistem | TCKN | VKN | IBAN | Telefon | İsim | E-posta | Kart |
|---|---|---|---|---|---|---|---|---|
| Bankacılık mesajları ([cagrigungor](https://huggingface.co/datasets/cagrigungor/turkish-pii-masking-benchmark), 550) | Presidio, Türkçe kurulmuş | 0.62 | 0.00 | 0.00 | 0.92 | 0.00 | 1.00 | 0.00 |
| | presidio-tr, `ner=True` | 0.62 | 0.67 | 0.31 | 0.92 | 0.93 | 1.00 | 0.10 |
| [BTX24](https://huggingface.co/datasets/BTX24/turkish-privacy-pii-ner) test (10.393) | Presidio, Türkçe kurulmuş | 0.12 | 0.00 | 0.02 | 0.93 | 0.00 | 0.84 | — |
| | presidio-tr, `ner=True` | 0.70 | 0.72 | 0.86 | 0.96 | 0.84 | 0.84 | — |
| [fevziegeyurtsevenler](https://huggingface.co/datasets/fevziegeyurtsevenler/turkish-pii-corpus) (155) | Presidio, Türkçe kurulmuş | 1.00 | 0.00 | 1.00 | 0.95 | — | 1.00 | 0.00 |
| | presidio-tr, `ner=True` | 1.00 | 1.00 | 1.00 | 1.00 | — | 1.00 | 0.93 |

Okurken:

- Bankacılık ve BTX24 setlerindeki numaraların çoğu checksum'ı tutmaz (bankacılıkta IBAN ve kartların hiçbiri,
  BTX24'te TCKN'lerin %6'sı). presidio-tr bunları yalnızca yanında bağlam kelimesi varsa yakalar; düşük recall
  büyük ölçüde buradan gelir.
- Bankacılık setinde kaçanlar ayrıca: yazıyla yazılmış rakamlar ("tc dokuz dokuz yedi …"), tireli/boşluklu TCKN
  (`645-175-336-66`) ve küçük harfle "ıban" yazılmış bağlam kelimesi ("ıban paylaşıyorum TR81 …").
- İsim yanlış pozitiflerinin çoğu e-posta adresi içindeki isim parçalarıdır (`halil.ozdemir@…`); e-posta zaten
  maskelendiği için maskelemeye zarar vermez. BTX24'ten 2500 cümlelik örnekte 98 yanlış pozitifin hepsi böyledir.
- BTX24'te kaçan e-postalar `.invalid` gibi gerçek olmayan alan adlarıdır; Presidio'nun e-posta tanıyıcısı bunları
  kabul etmez.
- Kısmen maskelenmiş değerler (`753347****`) ve ölçülmeyen türler (adres, plaka, sağlık…) ölçüme girmez. Ayrıntı:
  [`docs/design.md`](docs/design.md). BTX24 CC BY 4.0, bankacılık seti CC0, fevziegeyurtsevenler Apache 2.0 lisanslıdır.

Sonuç dosyaları: [`2026-11-17-cagrigungor.md`](benchmark/results/2026-11-17-cagrigungor.md),
[`2026-11-17-btx24.md`](benchmark/results/2026-11-17-btx24.md),
[`2026-11-17-fevziegeyurtsevenler.md`](benchmark/results/2026-11-17-fevziegeyurtsevenler.md).

### Ödünleşim

0.6 skorlu bağlam kademesi, bir hanesi yanlış yazılmış kimliği yakalamak içindir; bedeli, bağlam kelimesi
yakınındaki PII olmayan sayıları da maskelemesidir. Varsayılan ayarda `presidio-tr` PII olmayan sayıları taban
çizgisinden daha çok maskeler (0.45'e karşı 0.10). 0.45, şablon karışımındaki zor negatiflerin payını yansıtır,
gerçek trafikteki oranı değil. Kesinliği tercih ediyorsanız kademeyi skor eşiğiyle kapatın: yanlış maskeleme 0.02'ye
iner, ama yazım hatalı kimlikler artık yakalanmaz ve recall düşer (ana sette TCKN 0.87 → 0.64).

```python
analyzer.analyze(text, language="tr", score_threshold=0.7)
```

Eşikle kalan 0.02, checksum'ı tesadüfen tutan sipariş/referans numaralarıdır (rastgele 11 hanelilerin ~%1'i TCKN,
10 hanelilerin ~%10'u VKN checksum'ını tutar); hiçbir eşik bunları ayıramaz. HTTP sunucusu (`/analyze`) da
`score_threshold` alır; LiteLLM 1.109.1 bu alanı göndermez, gateway'de eşik guardrail ayarında verilir:
`presidio_score_thresholds: {ALL: 0.7}`.

## Gateway demosu

LiteLLM `v1.109.1` içindeki Presidio guardrail'ine `presidio-tr` takılır:

```text
istemci ──► LiteLLM :4000 ──(pre-call)──► presidio-tr analyzer ──► presidio anonymizer
              │  maskeli istek                                     (<TR_NATIONAL_ID_1>)
              ▼
          LLM sağlayıcı ──► cevap ──► LiteLLM etiketleri geri açar ──► istemci
              │
              └──► Langfuse (yalnızca maskeli metin)
```

```bash
cp deploy/.env.example deploy/.env      # OPENAI_API_KEY alanını doldurun
docker compose -f deploy/docker-compose.yml up -d --build --wait

set -a && . deploy/.env && set +a
curl -s http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" -H "Content-Type: application/json" \
  -d '{"model":"gpt-4.1-mini","temperature":0,"messages":[{"role":"system","content":"Kullanıcının mesajını aynen tekrar et; <...> etiketlerini de aynen koru."},{"role":"user","content":"TC kimlik no 10000000146, telefon 0532 123 45 67."}]}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

Beklenen çıktı: `TC kimlik no 10000000146, telefon 0532 123 45 67.` (değerler geri açılmış). Langfuse arayüzü
`http://localhost:3000`; giriş bilgileri `deploy/.env` içindeki `LANGFUSE_INIT_USER_*` alanları. Portlar yalnızca
`127.0.0.1`'e bağlıdır. Durdurmak için: `docker compose -f deploy/docker-compose.yml down`.

İsim maskelemeyi açmak için `PRESIDIO_TR_NER=1 docker compose -f deploy/docker-compose.yml up -d --build --wait`.
Analyzer imajı torch (CPU) ve gömülü modelle ~0,7 GB'tan ~2,6 GB'a çıkar.

Analyzer erişilemezse istek reddedilir (fail-closed; e2e testle doğrulandı). Guardrail ayarında neyin neden şart
olduğu (`presidio_filter_scope: input`, ikinci `logging_only` guardrail'i) [`docs/design.md`](docs/design.md)
"Riskler" bölümünde.

## Testler

```bash
uv run pytest                                                 # birim testler (127; `ner` eki yoksa isim testleri atlanır)
set -a && . deploy/.env && set +a && uv run pytest -m e2e     # uçtan uca (7)
```

E2E testler çalışan compose yığınını ve bir OpenAI anahtarını ister. CI her push'ta ruff ve birim testleri
çalıştırır; pre-commit'te gitleaks + ruff var (`uvx pre-commit install`).

## Bilinen sınırlamalar

- Adres tanınmaz. İsim tanıma isteğe bağlıdır; isme benzeyen sıradan kelimeler ("Barış", "Umut") yanlış
  maskelenebilir, isim kaçabilir ("Umut Barış Gül"de "Gül").
- Bağlamsız ve checksum'ı bozuk TCKN maskelenmez; bağlamsız VKN de maskelenmez.
- Desteklenmeyen yazımlar: yazıyla yazılmış rakamlar ("dokuz dokuz yedi …"), küçük harfle "ıban" yazılmış bağlam
  kelimesi, boşluklu ya da tireli TCKN (`100 000 001 46`, `645-175-336-66`), `TR` sonrası boşluklu ya da tireli IBAN (`TR 33 …`,
  `TR33-0006-…`), noktalı telefon (`0532.123.45.67`), 0850/0800 ve 444'lü numaralar.
- Bir değerin bağlam kelimesi, yanındaki başka bir değeri de 0.6 kademesine sokabilir.
- Langfuse'a giden log kopyası için garanti fail-open'dır: LiteLLM'in logging hook'u bloklamaz, Presidio o anda hata
  verirse log maskesiz kalabilir.
- Model etiketi bozarsa değer geri açılamaz. `deploy/measure_unmask.py` ile ölçüm (gpt-4.1-mini, 10 görev): 9 geri
  açıldı, 1 değer modelce düşürüldü/değiştirildi.
- Anthropic native yolunda bilinen bir LiteLLM hatası var (BerriAI/litellm#22821); demo OpenAI uyumlu yolu kullanır.
- Veri tamamen sentetiktir; sonuçlar gerçek trafik için garanti vermez.

## Lisans

MIT. Microsoft ile bağlantısı yoktur.
