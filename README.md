# presidio-tr

[Türkçe](https://github.com/YusufAltuntas/presidio-tr/blob/main/README.md) · [English](https://github.com/YusufAltuntas/presidio-tr/blob/main/README_EN.md)

Microsoft Presidio için Türkçe kişisel veri (PII) tanıyıcıları: TC kimlik no, VKN, TR IBAN, TR telefon.
Microsoft'un resmi projesi değildir; topluluk paketidir.

**Kısaca** (1000 sentetik cümle, adil taban çizgisine karşı):

- VKN F1: 0.00 → 0.80; TR telefon F1: 0.49 → 0.90
- Bir hanesi yanlış yazılmış TCKN/VKN/IBAN, yanında bağlam kelimesi varsa yine maskelenir.
- LiteLLM gateway demosu: LLM sağlayıcısı yalnızca maskeli metni görür; Langfuse da analyzer ve anonymizer sağlıklıyken.

## Neden

Presidio'da `TrNationalIdRecognizer` (checksum doğrulamalı, yazım hatası kademesi yok, varsayılan olarak kapalı) ve `TrLicensePlateRecognizer`
zaten var. `presidio-tr` şunları ekler:

- VKN tanıyıcısı (upstream'de yok).
- TCKN, VKN ve IBAN için yazım hatası kademesi: checksum'ı geçmeyen ama yakınında bağlam kelimesi olan değer 0.6 skorla maskelenir.
- Türkiye'ye özel telefon tanıyıcısı (presidio-analyzer 2.2.366'da yok).
- Türkçe ek toleranslı bağlam eşleştirme ("IBAN'ım", "hesabınız").
- Gateway demosu ve bulguları (aşağıda).

Varlık adları bilerek upstream ile aynıdır (`TR_NATIONAL_ID`, `IBAN_CODE`, `PHONE_NUMBER`). Varsayılan
`AnalyzerEngine()` hazır tanıyıcıları yalnızca `en` için kaydeder; Türkçe metni `en` ile çalıştırınca her sayı
`US_BANK_NUMBER` / `DATE_TIME` gibi yanlış türlerle maskelenir.

## Benchmark

| Sistem | Varlık | Precision | Recall | F1 | Maskelenen |
|---|---|---|---|---|---|
| Presidio (en, varsayılan) | TR_NATIONAL_ID | 0.00 | 0.00 | 0.00 | 1.00 |
| Presidio (en, varsayılan) | TR_TAX_ID | 0.00 | 0.00 | 0.00 | 1.00 |
| Presidio (en, varsayılan) | IBAN_CODE | 1.00 | 0.83 | 0.91 | 0.85 |
| Presidio (en, varsayılan) | PHONE_NUMBER | 0.34 | 0.88 | 0.49 | 1.00 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | TR_NATIONAL_ID | 1.00 | 0.62 | 0.77 | 0.69 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | TR_TAX_ID | 0.00 | 0.00 | 0.00 | 0.91 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | IBAN_CODE | 1.00 | 0.83 | 0.91 | 0.85 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | PHONE_NUMBER | 0.34 | 0.88 | 0.49 | 0.88 |
| Presidio + presidio-tr | TR_NATIONAL_ID | 0.77 | 0.85 | 0.81 | 0.85 |
| Presidio + presidio-tr | TR_TAX_ID | 0.80 | 0.81 | 0.80 | 0.81 |
| Presidio + presidio-tr | IBAN_CODE | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr | PHONE_NUMBER | 0.89 | 0.91 | 0.90 | 0.91 |
| Presidio + presidio-tr (score_threshold=0.7) | TR_NATIONAL_ID | 1.00 | 0.62 | 0.77 | 0.62 |
| Presidio + presidio-tr (score_threshold=0.7) | TR_TAX_ID | 1.00 | 0.60 | 0.75 | 0.60 |
| Presidio + presidio-tr (score_threshold=0.7) | IBAN_CODE | 1.00 | 0.83 | 0.91 | 0.83 |
| Presidio + presidio-tr (score_threshold=0.7) | PHONE_NUMBER | 1.00 | 0.77 | 0.87 | 0.77 |

| Sistem | Yanlış maskeleme (PII olmayan sayılar) |
|---|---|
| Presidio (en, varsayılan) | 1.00 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | 0.51 |
| Presidio + presidio-tr | 0.41 |
| Presidio + presidio-tr (score_threshold=0.7) | 0.00 |

`en` satırı, Türkçe kurulumu olmayan bir kullanıcının elde ettiği sonuçtur; `tr` (hazır tanıyıcılar) satırı adil
taban çizgisidir. "Maskelenen": türü yanlış da olsa bir tahminle örtülen PII oranı. Veri 1000 sentetik cümledir
(Faker `tr_TR` + şablonlar, seed 42); bağlam kelimesinin yanında duran PII olmayan sayılar ("Kimlik doğrulama
kodunuz ...") ve bağlamsız zor PII örnekleri de içerir. Sonuç dosyası: `benchmark/results/2026-11-15.md`.
Yeniden üretmek için:

```bash
uv sync --group benchmark && uv run python -m benchmark.generate --n 1000 --seed 42 && uv run python -m benchmark.run
```

Bağımsız set: `uv run python -m benchmark.generate --templates heldout --out benchmark/data/tr_pii_heldout.jsonl && uv run python -m benchmark.run --data benchmark/data/tr_pii_heldout.jsonl --tag heldout`

Düz `uv sync` benchmark grubunun modelini yine kaldırır.

### Ödünleşim: yanlış maskeleme 0.41

Varsayılan Presidio'da 1.00, hazır tanıyıcılarla `tr`'de 0.51, `presidio-tr` ile 0.41. `presidio-tr`'nin yanlış
maskelemesinin tamamı, bağlam kelimesi yakınında bulunan geçersiz checksum'lu sayıları maskeleyen 0.6 skorlu
kademeden gelir (aşağıdaki Skorlama bölümü); `score_threshold=0.7` ile yanlış maskeleme 0.00 olur. Bu bilinçli
bir seçimdir: güvenlik önce gelir, bir hanesi yanlış yazılmış TC kimlik no yine maskelenmelidir. 0.41 değeri
çoğunlukla şablon karışımındaki zor negatiflerin payını yansıtır, gerçek trafikteki oranı değil. Kesinliği
tercih ediyorsanız bağlam kademesini skor eşiğiyle kapatın:

```python
analyzer.analyze(text, language="tr", score_threshold=0.7)
```

Eşikli sürüm tablodaki `score_threshold=0.7` satırıdır.

### Bağımsız şablon seti

Ana şablonları tanıyıcıları yazan kişi yazdı. Ayrıca, repodaki koda erişimi olmayan ayrı bir LLM ajanına yalnızca
alan listesiyle yazdırılmış 24 şablonluk bir set var (`HELDOUT_TEMPLATES`, `benchmark/generate.py`); tanıyıcılar bu sete göre
ayarlanmadı. Sonuç: `benchmark/results/2026-11-15-heldout.md`.

| Sistem | Varlık | Precision | Recall | F1 | Maskelenen |
|---|---|---|---|---|---|
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | TR_NATIONAL_ID | 1.00 | 0.71 | 0.83 | 0.76 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | TR_TAX_ID | 0.00 | 0.00 | 0.00 | 0.86 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | IBAN_CODE | 1.00 | 0.72 | 0.84 | 0.75 |
| Presidio (tr, hazır tanıyıcılar + TrNationalIdRecognizer) | PHONE_NUMBER | 0.25 | 0.81 | 0.38 | 0.81 |
| Presidio + presidio-tr | TR_NATIONAL_ID | 0.78 | 1.00 | 0.88 | 1.00 |
| Presidio + presidio-tr | TR_TAX_ID | 0.64 | 1.00 | 0.78 | 1.00 |
| Presidio + presidio-tr | IBAN_CODE | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr | PHONE_NUMBER | 1.00 | 0.76 | 0.86 | 0.76 |

Yanlış maskeleme: hazır tanıyıcılar 0.61, presidio-tr 0.17 (heldout dosyasından).

Bu sette `score_threshold=0.7` ile recall: `TR_NATIONAL_ID` 0.71, `TR_TAX_ID` 0.47, `IBAN_CODE` 0.72, `PHONE_NUMBER` 0.49; VKN, IBAN ve telefonda eşiğin bedeli ana setten yüksektir.

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

`add_turkish_recognizers(registry)` yalnızca `tr` için kurulmuş, Türkçe NLP motorlu bir registry/analyzer ile
çalışır; varsayılan bir `en` registry'sine eklemek işe yaramaz. Doğru kurulum için `build_analyzer()` kaynağına
bakın (`src/presidio_tr/__init__.py`). Boş (blank) spaCy `tr` pipeline'ı kullanılır, model indirmek gerekmez.

## Skorlama

| Durum | Sonuç |
|---|---|
| Checksum geçerli | Skor 1.0, maskelenir |
| Checksum geçersiz, yakında bağlam kelimesi var | Skor 0.6, maskelenir |
| Checksum geçersiz, bağlam yok | Atılır |

Bir hanesi yanlış yazılmış TC kimlik no sızmasın, bağlamsız bir sipariş no maskelenmesin diye üç kademe vardır.
Telefonun checksum'ı yok; doğrulayıcı yalnızca biçime bakar (+90 / 0090 / 90 / 0 önekli numara bağlamsız da maskelenir, öneksiz 10 hane bağlam ister).

VKN istisnası: VKN'nin tek bir mod-10 kontrol hanesi var, rastgele 10 haneli sayıların yaklaşık %10'u geçer.
Bu yüzden VKN için bağlam zorunludur; bağlamsız yazılmış geçerli VKN maskelenmez.

## Türkçe bağlam eşleştirme

- Lemma yerine kök öneki: "hesabınız", "hesaplarım" gibi ekli biçimler `hesap` / `hesab` köküyle yakalanır.
- Kısa kökler (`tc`, `vkn`, `tel`, `gsm`, `cep`) yalnızca tam kelimeyle eşleşir; "telif", "cephe" bağlam sayılmaz.
  `ulaş` yerine fiil biçimleri (`ulaşa`, `ulaşın`, `ulaşıl`) kullanılır, "ulaşım" eşleşmez.
- Ünsüz yumuşaması kök listesindedir: `hesap`/`hesab`, `kimlik`/`kimliğ`.
- Türkçe küçültme "IBAN"ı "ıban" yapar; bu yüzden hem Türkçe hem standart küçültme denenir.

Tanıyıcılara Presidio'nun `context` parametresi verilmez; Presidio'nun lemma tabanlı skor artırıcısı skorları
değiştirmez.

## Gateway demosu

LiteLLM `v1.109.1` içindeki Presidio guardrail'ine `presidio-tr` takılır; LLM sağlayıcısı yalnızca maskeli metni
görür, cevapta etiketler geri açılır, analyzer ve anonymizer sağlıklıyken Langfuse'a yalnızca maskeli metin gider
(aşağıdaki "Sızıntı garantisinin sınırı" notuna bakın).

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
`http://localhost:3000`; kullanıcı ve parola `deploy/.env` içindeki `LANGFUSE_INIT_USER_*` alanlarıdır.
Yayınlanan portlar yalnızca `127.0.0.1`'e bağlıdır. LiteLLM başladıktan sonra yaklaşık 15 sn içinde
(`/health/liveliness`) cevap vermeye başlar. Durdurmak için: `docker compose -f deploy/docker-compose.yml down`.

Hata davranışı: analyzer erişilemezse istek reddedilir (fail-closed; e2e testle doğrulandı). Analyzer hata ya da geçersiz
cevap dönerse reddedilmesi guardrail'de `output_parse_pii`'nin açık olmasına bağlıdır.

Demo bulguları (LiteLLM 1.109.1):

- Guardrail'de `presidio_filter_scope: input` şarttır. Varsayılan `both`, `output_parse_pii` ile geri açılan
  değerleri tekrar maskeler ve kullanıcı `<TR_NATIONAL_ID>` görür.
- `mode: logging_only` ile ikinci bir guardrail (o da `presidio_filter_scope: input`) şarttır; yoksa Langfuse
  generation çıktısına geri açılmış ham TCKN yazılıyordu. Streaming ve non-streaming için e2e testle doğrulandı.
- Langfuse v4 gözlemleri `/api/public/v2/observations` ile sunar (v1 `/api/public/traces` events-only modunda
  kapalı); e2e test bunu kullanır.

## Testler ve geliştirme

```bash
uv run pytest                                                 # birim testler (98)
set -a && . deploy/.env && set +a && uv run pytest -m e2e     # uçtan uca (7)
```

E2E testler çalışan compose yığınını ve bir OpenAI anahtarını ister; her koşu bir sentin kesri kadar tutar.
Pre-commit: gitleaks + ruff (`uvx pre-commit install`). CI her push'ta ruff ve birim testleri çalıştırır.

## Bilinen sınırlamalar

- Bağlamsız ve checksum'ı bozuk TC kimlik no maskelenmez; bağlamsız VKN de maskelenmez.
- Desteklenmeyen yazımlar: boşluklu TCKN (`100 000 001 46`), `TR` sonrası boşluklu IBAN (`TR 33 …`), 0850/0800
  numaraları.
- Bağlam eşleştirmesi komşu etiketlere taşabilir: bir etiketin bağlam kelimesi yanındaki başka bir değeri de
  0.6 kademesine sokabilir.
- Sızıntı garantisinin sınırı: LiteLLM'in logging hook'u bloklamaz. Çağrıdan sonra, loglamadan önce Presidio
  hata verirse loglanan kopya maskesiz kalabilir (log için fail-open); yani "Langfuse yalnızca maskeli metin görür"
  analyzer/anonymizer sağlıklıyken geçerlidir.
- İsim ve adres yok (NER, v2).
- Model etiketi bozarsa değer geri açılamaz. `deploy/measure_unmask.py` ile ölçüm (gpt-4.1-mini, 2026-11-14):
  10 görev: 9 geri açıldı, 0 etiket açılamadan kaldı, 1 değer modelce düşürüldü/değiştirildi.
- Anthropic native yolunda bilinen LiteLLM hatası (BerriAI/litellm#22821); demo OpenAI uyumlu yolu ve
  `gpt-4.1-mini` kullanır.
- Veri tamamen sentetiktir; sonuçlar gerçek trafik için garanti vermez.

## Lisans

MIT. Microsoft ile bağlantısı yoktur.
