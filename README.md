# presidio-tr

[Türkçe](README.md) · [English](README_EN.md)

Microsoft Presidio için Türkçe kişisel veri (PII) tanıyıcıları: TC kimlik no, VKN, TR IBAN, TR telefon.
Microsoft'un resmi projesi değildir; topluluk paketidir.

## Neden

- Presidio'da TC kimlik no ve VKN tanıyıcısı yok.
- Hazır tanıyıcılar `en` için kayıtlı; `language="tr"` ile IBAN ve telefon da çalışmıyor.
- `en` ile çalıştırınca Türkçe metindeki her sayı `US_BANK_NUMBER` / `DATE_TIME` gibi yanlış türlerle maskeleniyor.

## Benchmark

| Sistem | Varlık | Precision | Recall | F1 | Maskelenen |
|---|---|---|---|---|---|
| Presidio (en, varsayılan) | TR_NATIONAL_ID | 0.00 | 0.00 | 0.00 | 1.00 |
| Presidio (en, varsayılan) | TR_TAX_ID | 0.00 | 0.00 | 0.00 | 1.00 |
| Presidio (en, varsayılan) | IBAN_CODE | 1.00 | 0.83 | 0.91 | 0.84 |
| Presidio (en, varsayılan) | PHONE_NUMBER | 0.36 | 0.86 | 0.50 | 1.00 |
| Presidio + presidio-tr | TR_NATIONAL_ID | 0.72 | 0.88 | 0.79 | 0.88 |
| Presidio + presidio-tr | TR_TAX_ID | 0.85 | 1.00 | 0.92 | 1.00 |
| Presidio + presidio-tr | IBAN_CODE | 1.00 | 1.00 | 1.00 | 1.00 |
| Presidio + presidio-tr | PHONE_NUMBER | 0.91 | 1.00 | 0.95 | 1.00 |

| Sistem | Yanlış maskeleme (PII olmayan sayılar) |
|---|---|
| Presidio (en, varsayılan) | 1.00 |
| Presidio + presidio-tr | 0.41 |

"Maskelenen": türü yanlış da olsa bir tahminle örtülen PII oranı. Veri 1000 sentetik cümledir (Faker `tr_TR` +
şablonlar, seed 42); bağlam kelimesinin yanında duran PII olmayan sayılar ("Kimlik doğrulama kodunuz ...") de
içerir. Sonuç dosyası: `benchmark/results/2026-11-14.md`. Yeniden üretmek için:

```bash
uv sync --group benchmark && uv run python -m benchmark.generate --n 1000 --seed 42 && uv run python -m benchmark.run
```

Düz `uv sync` benchmark grubunun modelini yine kaldırır.

### Ödünleşim: yanlış maskeleme 0.41

Varsayılan Presidio'da 1.00, `presidio-tr` ile 0.41. Farkın büyük kısmı, bağlam kelimesi yakınında bulunan
geçersiz checksum'lu sayıları maskeleyen 0.6 skorlu kademeden gelir (aşağıdaki Skorlama bölümü). Bu bilinçli bir
seçimdir: güvenlik önce gelir, bir hanesi yanlış yazılmış TC kimlik no yine maskelenmelidir. `TR_NATIONAL_ID`
precision değerinin 0.72 olması da aynı kademeden kaynaklanır; recall'daki kayıp ise tasarım gereği bağlamsız
ve checksum'ı bozuk numaralardır. Kesinliği tercih ediyorsanız bağlam kademesini skor eşiğiyle kapatın:

```python
analyzer.analyze(text, language="tr", score_threshold=0.7)
```

Eşikli sürüm için ayrı bir benchmark satırı yoktur.

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

Var olan bir registry'ye eklemek için `add_turkish_recognizers(registry)`. Boş (blank) spaCy `tr` pipeline'ı
kullanılır, model indirmek gerekmez.

## Skorlama

| Durum | Sonuç |
|---|---|
| Checksum geçerli | Skor 1.0, maskelenir |
| Checksum geçersiz, yakında bağlam kelimesi var | Skor 0.6, maskelenir |
| Checksum geçersiz, bağlam yok | Atılır |

Bir hanesi yanlış yazılmış TC kimlik no sızmasın, bağlamsız bir sipariş no maskelenmesin diye üç kademe vardır.
Telefonun checksum'ı yok; doğrulayıcı yalnızca biçime bakar (+90/0 önekli numara bağlamsız da maskelenir, öneksiz 10 hane bağlam ister).

VKN istisnası: VKN'nin tek bir mod-10 kontrol hanesi var, rastgele 10 haneli sayıların yaklaşık %10'u geçer.
Bu yüzden VKN için bağlam zorunludur; bağlamsız yazılmış geçerli VKN maskelenmez.

## Türkçe bağlam eşleştirme

- Lemma yerine kök öneki: "hesabınız", "hesaplarım" gibi ekli biçimler `hesap` / `hesab` köküyle yakalanır.
- Ünsüz yumuşaması kök listesindedir: `hesap`/`hesab`, `kimlik`/`kimliğ`.
- Türkçe küçültme "IBAN"ı "ıban" yapar; bu yüzden hem Türkçe hem standart küçültme denenir.

Tanıyıcılara Presidio'nun `context` parametresi verilmez; Presidio'nun lemma tabanlı skor artırıcısı skorları
değiştirmez.

## Gateway demosu

LiteLLM `v1.109.1` içindeki Presidio guardrail'ine `presidio-tr` takılır; LLM sağlayıcısı yalnızca maskeli metni
görür, cevapta etiketler geri açılır, Langfuse'a yalnızca maskeli metin gider.

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

Demo bulguları (LiteLLM 1.109.1):

- Guardrail'de `presidio_filter_scope: input` şarttır. Varsayılan `both`, `output_parse_pii` ile geri açılan
  değerleri tekrar maskeler ve kullanıcı `<TR_NATIONAL_ID>` görür.
- `mode: logging_only` ile ikinci bir guardrail (o da `presidio_filter_scope: input`) şarttır; yoksa Langfuse
  generation çıktısına geri açılmış ham TCKN yazılıyordu. Streaming ve non-streaming için e2e testle doğrulandı.
- Langfuse v4 gözlemleri `/api/public/v2/observations` ile sunar (v1 `/api/public/traces` events-only modunda
  kapalı); e2e test bunu kullanır.

## Testler ve geliştirme

```bash
uv run pytest                                                 # birim testler (68)
set -a && . deploy/.env && set +a && uv run pytest -m e2e     # uçtan uca (7)
```

E2E testler çalışan compose yığınını ve bir OpenAI anahtarını ister; her koşu bir sentin kesri kadar tutar.
Pre-commit: gitleaks + ruff (`uvx pre-commit install`). CI her push'ta ruff ve birim testleri çalıştırır.

## Bilinen sınırlamalar

- Bağlamsız ve checksum'ı bozuk TC kimlik no maskelenmez; bağlamsız VKN de maskelenmez.
- İsim ve adres yok (NER, v2).
- Model etiketi bozarsa değer geri açılamaz. `deploy/measure_unmask.py` ile ölçüm (gpt-4.1-mini, 2026-11-14):
  10 görev: 9 geri açıldı, 0 etiket açılamadan kaldı, 1 değer modelce düşürüldü/değiştirildi.
- Anthropic native yolunda bilinen LiteLLM hatası (BerriAI/litellm#22821); demo OpenAI uyumlu yolu ve
  `gpt-4.1-mini` kullanır.
- Veri tamamen sentetiktir; sonuçlar gerçek trafik için garanti vermez.

## Lisans

MIT. Microsoft ile bağlantısı yoktur.
