# presidio-tr — Tasarım

> Bu doküman `presidio-tr` v1'in **ne yapacağının ve neden böyle tasarlandığının** sahibidir.
> Uygulama planı yalnızca yerelde tutulur (`docs/plans/`, git dışı).

## Amaç

Microsoft Presidio için Türkçe kişisel veri (PII) tanıyıcı paketi. LiteLLM gateway'inin mevcut Presidio
guardrail'ine takılarak, Türkçe metindeki kişisel verilerin LLM sağlayıcısına gitmeden maskelenmesini ve
cevapta geri açılmasını sağlar. Etkisi sentetik Türkçe benchmark ile ölçülür.

**Neden:** Presidio'da `TrNationalIdRecognizer` (yalnızca checksum, varsayılan olarak kapalı) ve
`TrLicensePlateRecognizer` var; VKN tanıyıcısı yok; hazır `PhoneRecognizer`'ın varsayılan bölgelerinde TR yok (2.2.366, `supported_regions=["TR"]` ile kurulabilir). `presidio-tr` VKN'yi,
TCKN/VKN/IBAN için yazım hatası kademesini (checksum geçersiz + bağlam → 0.6), Türkiye'ye özel telefonu ve
Türkçe ek toleranslı bağlam eşleştirmeyi ekler. Varsayılan `AnalyzerEngine()` hazır tanıyıcıları yalnızca `en`
için kaydeder. Geri alınabilir maskeleme (`output_parse_pii`) ve streaming desteği LiteLLM'de zaten var;
yeniden yazılmaz, Türkçe veriyle çalıştığı testlerle kanıtlanır.

Paket Microsoft'un resmi projesi değildir; README'nin tepesinde bu açıkça yazar.

## Kapsam

**v1'de:**
- Tanıyıcılar: TC kimlik no, VKN, TR IBAN, TR telefon. `build_analyzer()` Presidio'nun hazır e-posta ve kredi kartı
  tanıyıcılarını da `tr` için ekler (`tr` registry'sine kendiliğinden gelmezler); hazır telefon ve tarih tanıyıcıları
  Türkçe metinde sipariş/referans numaralarını yanlış maskelediği için eklenmez.
- İsteğe bağlı isim tanıma (`PERSON`, `ner` eki; aşağıdaki "İsim tanıma" bölümü).
- Benchmark: varsayılan Presidio, hazır tanıyıcılı `tr` Presidio ve Presidio + `presidio-tr` karşılaştırması.
- Demo: `docker compose` ile LiteLLM + Presidio (paketli imaj) + Langfuse.
- Anahtar başı bütçe ve end-user attribution — yalnızca LiteLLM config'i, kod yok.

**v1'de yok:** adres, plaka (Presidio'da var), kendi guardrail kodumuz, Presidio'ya upstream PR
(v1 sonrası ayrı iş), PyPI yayını (en son, isteğe bağlı).

## Mimari

```
presidio-tr/
├── src/presidio_tr/
│   ├── validators.py        # saf fonksiyonlar, Presidio bağımlılığı yok
│   ├── recognizers/         # TcKimlikRecognizer, VknRecognizer, TrIbanRecognizer, TrPhoneRecognizer
│   ├── context.py           # Türkçe bağlam kelimeleri
│   ├── server.py            # Presidio analyzer HTTP API'siyle uyumlu /analyze (extra: server)
│   └── __init__.py          # add_turkish_recognizers(registry), build_analyzer()
├── benchmark/
│   ├── synth.py             # checksum'ı geçerli/geçersiz sentetik değer üreticileri
│   ├── generate.py          # Faker('tr_TR') + şablonlar → etiketli JSONL (sabit seed)
│   ├── run.py               # varlık türü başına precision / recall / F1 + yanlış maskeleme
│   └── results/             # <YYYY-MM-DD>.md — commit'lenir
├── deploy/
│   ├── docker-compose.yml   # Langfuse'un resmi compose'unu `include` eder
│   ├── langfuse/            # Langfuse'un resmi docker-compose.yml'i, sabit sürümden kopya
│   ├── analyzer.Dockerfile  # presidio-tr[server]
│   ├── litellm-config.yaml
│   └── measure_unmask.py    # model etiketi bozma oranı ölçümü
└── tests/
    ├── unit/
    └── e2e/                 # yalnızca `pytest -m e2e` ile, compose ayaktayken
```

| Birim | Ne yapar | Neye bağlı |
|---|---|---|
| `validators` | "Bu numara geçerli mi?" — TCKN ve VKN checksum, TR IBAN uzunluk + mod-97 | Hiçbir şey |
| `recognizers` | Regex ile aday bulur, validator + bağlam ile skorlar | Presidio, `validators`, `context` |
| `context` | Türkçe bağlam kelimeleri ve ek toleranslı eşleştirme | Hiçbir şey |
| `benchmark` | Veri üretir, dört sistemi karşılaştırır | Paket (dışarıdan) |
| `deploy` | Gateway demosu | Paketin Docker imajı |

Paket, benchmark'tan ve deploy'dan habersizdir.

### Varlık adları

| Tanıyıcı | Entity | Not |
|---|---|---|
| `TcKimlikRecognizer` | `TR_NATIONAL_ID` | |
| `VknRecognizer` | `TR_TAX_ID` | |
| `TrIbanRecognizer` | `IBAN_CODE` | Presidio'nun adıyla aynı, mevcut config'lerle uyumlu kalsın diye. Varsayılan `AnalyzerEngine()` hazır tanıyıcıları yalnızca `en` için kaydeder; TR'ye özel (26 karakter, `TR` öneki, mod-97) sürüm yazım hatası kademesini de ekler. |
| `TrPhoneRecognizer` | `PHONE_NUMBER` | Aynı gerekçe. |

### Skorlama kuralı

Checksum'dan geçemeyen numarayı düz atlamak güvenlik açığıdır (bir hane yanlış yazılmış TC kimlik sızar).
Üç kademe:

| Durum | Sonuç |
|---|---|
| Checksum geçerli | Yüksek skor, maskelenir |
| Checksum geçersiz, yakınında bağlam kelimesi var | Orta skor, maskelenir |
| Checksum geçersiz, bağlam yok | Atlanır (sipariş no vb. maskelenmez) |

Telefonun checksum'ı yok; format (`+90`, `0`, `5xx`, boşluk/tire varyantları) + bağlam ile skorlanır.

**VKN istisnası — bağlam zorunlu.** VKN'nin tek kontrol hanesi var; rastgele 10 haneli sayıların ~%10'u checksum'dan
geçer. Bu yüzden VKN yakınında bağlam kelimesi yoksa checksum geçerli olsa da atlanır; bağlam varsa yukarıdaki iki
kademe uygulanır. Bedeli: bağlamsız yazılmış gerçek VKN maskelenmez. (TCKN'de iki kontrol hanesi var, rastgele
geçme ~%1; IBAN'da `TR` öneki + mod-97 — bunlarda bağlam zorunlu değil.)

### İsim tanıma (isteğe bağlı)

- Presidio'nun hazır `HuggingFaceNerRecognizer`'ı ile Hugging Face'teki `akdeniz27/bert-base-turkish-cased-ner`
  (MIT, en çok indirilen Türkçe NER modeli). spaCy üzerinden gitmez: ekli kelimelerde ("Ayşe'nin") spaCy token
  sınırları model çıktısıyla hizalanmıyor; bu tanıyıcı modelin kendi tokenizer'ını kullanır.
- `aggregation_strategy="first"`: varsayılan `simple`, küçük/büyük harfle yazılmış isimleri alt kelime parçalarına
  bölüyordu ("ayşe yılmaz" → "ay" + "şe yılmaz", "AHMET" → "AH" + "MET").
- Yalnızca `PER` → `PERSON` tutulur. Presidio eşlenmemiş etiketleri olduğu gibi geçirir; yer (`LOC`) ve kurum (`ORG`)
  maskelenirse şube/şehir adları da gider, kullanışlılık düşer.
- Varsayılan kapalıdır: transformers + torch ve ~440 MB model ister, CPU'da cümle başına ~50 ms ekler. Docker imajında
  `NER=1` build argümanıyla açılır; Linux'ta torch'un CPU sürümü kurulur (`tool.uv.sources`), model imaja gömülür.
- Bilinen hatalar: isme benzeyen sıradan kelimeler ("Barış görüşmeleri") maskelenir, bazı isimler kaçar
  ("Umut Barış Gül"de "Gül"); skor bazen 0.7'nin altındadır, eşikli kullanımda isim düşebilir.

## Veri akışı

1. İstemci → LiteLLM (virtual key + `user` alanı).
2. **Pre-call:** LiteLLM Presidio guardrail'i → analyzer (`language=tr`, `presidio-tr` tanıyıcıları) →
   anonymizer `replace` ile etiketler. Etiket ↔ değer eşlemesi LiteLLM'de, istek süresince bellekte.
3. Sağlayıcı yalnızca maskeli metni görür.
4. Cevap (streaming veya değil) → LiteLLM etiketleri geri açar (`output_parse_pii: true`).
5. Langfuse'a yalnızca maskeli metin gider.

Bütçe: virtual key'de `max_budget`. Attribution: `user` alanı Langfuse'a etiket olarak gider.

## Hata yönetimi

- **Presidio erişilemezse istek reddedilir (fail-closed).** Maskesiz veri sağlayıcıya gitmez.
- **Model etiketi bozarsa** (ör. etiketi kendi cümlesiyle yeniden yazarsa) geri açma başarısız olur ve
  kullanıcı etiketi görür. Sızıntı değil, kullanılabilirlik sorunu: README'de bilinen sınırlama olarak yazılır,
  oranı `deploy/measure_unmask.py` ile ölçülür.

## Riskler

Plan yazılırken presidio-analyzer 2.2.366 ve LiteLLM 1.109.1 ile bir deneme (spike) yapıldı.

1. **Türkçe NLP motoru — çözüldü.** `SpacyNlpEngine` alt sınıfı `spacy.blank("tr")` yükler; model indirmek
   gerekmez. v1 tanıyıcıları NLP çıktısı kullanmaz.
2. **Ekli bağlam kelimeleri — çözüldü, tasarım değişti.** Blank pipeline'da lemma boş ve "IBAN'ımı" tek token
   kalıyor; Presidio'nun lemma tabanlı bağlam güçlendirmesi Türkçede çalışmaz. Bu yüzden bağlam kontrolü
   tanıyıcının içinde yapılır: eşleşmenin çevresindeki kelimeler, Türkçe küçük harfe çevrilip kök önekiyle
   karşılaştırılır. Ünsüz yumuşaması için kökün iki hali de listelenir (`hesap`/`hesab`, `kimlik`/`kimliğ`).
   Türkçe küçültme kısaltmaları bozar ("IBAN" → "ıban"), bu yüzden hem Türkçe hem standart küçültme denenir.
   Tanıyıcılara Presidio `context` verilmez, böylece Presidio'nun güçlendiricisi devreye girmez.
   ≤3 karakterli kökler (`tc`, `vkn`, `tel`, `gsm`, `cep`) yalnızca tam kelimeyle eşleşir ("telif", "cephe" bağlam sayılmasın diye); yaygın bileşik biçimler (`tcno`, `vkno`, `telno` …) ayrı önek kökü olarak listelenir; `telim`, `telden` gibi diğer ekli biçimler bağlam sayılmaz. `ulaş` yerine fiil biçimleri (`ulaşa`, `ulaşın`, `ulaşıl`) kullanılır, "ulaşım" eşleşmez. Nokta hem silinir hem boşluğa çevrilir ("T.C." → `tc`, "Tel.No" → `tel`).
3. **Aynı türden iki değer — çözüldü.** LiteLLM etiketleri kendisi numaralıyor (`<TR_NATIONAL_ID_1>`,
   `<TR_NATIONAL_ID_2>`); e2e testi yine de doğrular.
4. **Langfuse'a ne gidiyor — çözüldü.** E2E testi, geri açılan cevabın Langfuse'a ham PII olarak gittiğini
   gösterdi (girdi zaten maskeliydi). Yedek uygulandı: ikinci guardrail `presidio-tr-logs`
   (`mode: logging_only`) log kopyasını maskeler; bu girişte `presidio_filter_scope: input` şart (doğrulandı):
   yoksa LiteLLM maskelemeyi canlı cevap nesnesine de uygulayıp kullanıcıya `<TR_NATIONAL_ID>` döndürüyor.
   Langfuse v4 `events_only` modunda v1 `/api/public/traces` kapalı; test `/api/public/v2/observations` kullanır.
   - Streaming: akışlı yanıt da Langfuse'a ham PII olarak gitmiyor (e2e testi `test_langfuse_never_sees_raw_pii_for_streaming`
     geçti: ham TCKN yok, `<TR_NATIONAL_ID` etiketi var).
   - Filter scope mekanizması: `both` ile LiteLLM ek bir `mask_output_callback` (`apply_to_output=True`) yaratır;
     bunun `_presidio_output_mode("logging_only")` sonucu `post_call`'a çözülür ve canlı cevabı maskeler.
     `input` ile bu callback yaratılmaz; logging_only callback'inin `async_logging_hook`'u yine de log kopyasını maskeler.
   - Bu iki davranış LiteLLM'e hata olarak bildirildi (BerriAI/litellm#52045, #52046) ve düzeltme PR'ları açıldı
     (BerriAI/litellm#52112, #52113). Birleşip yayınlanana kadar demo `presidio_filter_scope: input` ile kalır.
   - Fail-open (log): LiteLLM'in logging hook'u bloklamaz; çağrıdan sonra, loglamadan önce Presidio hata verirse
     loglanan kopya maskesiz kalabilir. "Langfuse yalnızca maskeli metin görür" analyzer/anonymizer sağlıklıyken geçerlidir.
5. **Fail-closed — kısmen çözüldü.** LiteLLM 1.109.1, `output_parse_pii` açıkken analyzer'dan geçersiz cevap
   gelirse isteği reddediyor. Analyzer'a hiç ulaşılamama durumu e2e testinde doğrulanır. Sunucu desteklenmeyen
   dil için 400 döner, LiteLLM bunu da reddeder.
6. **Bilinen LiteLLM hatası — açık.** Anthropic native yolunda `output_parse_pii` hatası bildirilmiş
   (BerriAI/litellm#22821). Demo OpenAI-uyumlu yolla kurulur.

## Test

**Birim (CI'da):**
- `validators`: algoritmayla üretilmiş geçerli/geçersiz TCKN ve VKN; TR IBAN; sınır durumlar (0 ile başlayan,
  10/12 hane, boşluklu yazım).
- `recognizers`: üç kademeli skor kuralı; Türkçe ekli bağlam ("IBAN'ımı", "TC'm").

**Uçtan uca (lokal, `-m e2e`):**
- Streaming ve non-streaming'de maskeleme + geri açma.
- Aynı türden iki değerin karışmadan geri açılması.
- Langfuse API'sinde ham PII olmaması.
- Presidio kapalıyken isteğin reddedilmesi.
- Bütçe aşımında isteğin reddedilmesi.

**CI:** GitHub Actions — birim testler + lint. E2E API anahtarı gerektirdiği için CI'da yok.

## Benchmark

- ~1.000 etiketli cümle; `Faker('tr_TR')` + 30–50 şablon (müşteri hizmetleri, banka, telco tonu).
- Bilerek: hatalı yazılmış numaralar, PII'ye benzeyen ama olmayan sayılar (sipariş no, tutar, tarih).
- **Zor negatifler:** bağlam kelimesi taşıyan ama PII olmayan sayılar ("Kimlik doğrulama kodunuz …", "Vergi dairesi
  başvuru numaranız …"). Bunlar olmadan 0.6 kademesinin yanlış pozitifleri hiç ölçülmez ve benchmark kendi
  şablonlarıyla kendini doğrular.
- Negatif sayılar checksum'a göre süzülmez. Tesadüfen checksum'ı tutan sipariş/referans no da PII değildir ve
  gerçek trafikte vardır (rastgele 11 hanelilerin ~%1'i TCKN, 10 hanelilerin ~%10'u VKN checksum'ını tutar).
  Süzmek yanlış maskelemeyi, özellikle eşikli sistemde, yapay olarak sıfıra çeker.
- Tüm değerler (tarih dahil) seed'li `random.Random`'dan üretilir; aynı seed her gün aynı veriyi verir.
- Karşılaştırma, dört sistem: (a) varsayılan Presidio — `language=en` ve hazır tanıyıcılarla, yani Türkçe
  kurulumu olmayan bir kullanıcının elinde olan; (b) adil taban çizgisi — `language=tr`, Presidio'nun hazır
  tanıyıcıları ve kendi `TrNationalIdRecognizer`'ı (varsayılan kapalı, elle eklenir); hazır `PhoneRecognizer`'ın
  bölge listesinde TR olmadığı için `supported_regions=["TR"]` ile kurulmuşu kullanılır; (c) Presidio +
  `presidio-tr`, `language=tr`; (d) (c)'nin `score_threshold=0.7` ile çalıştırılmışı —
  bağlam kademesi kapalı, kesinlik tercih edenler için. Varlık türü başına P/R/F1.
- Bağlamsız zor PII şablonları (bağlamsız VKN, öneksiz telefon) bilerek eklenir; recall şablon bağlamıyla şişmesin.
- Şablonlardaki `{name}` alanı `PERSON` olarak etiketlenir; isim tanımalı sistem `--ner` ile eklenir.
- **Üçüncü taraf setler:** `benchmark/external.py` üç Hugging Face setini sabit commit ile indirir ve çevirir:
  cagrigungor/turkish-pii-masking-benchmark (bankacılık mesajları; yalnızca `tam` ve `negatif` kategorileri, çünkü
  diğerleri yalnızca istenen etiketlerin maskelenmesini ister; aralıklar maskeli çıktıyla hizalanarak çıkarılır),
  BTX24/turkish-privacy-pii-ner (test bölümü) ve fevziegeyurtsevenler/turkish-pii-corpus. Ölçmediğimiz türler
  (adres, plaka, sağlık…) ve `*` içeren, zaten maskelenmiş değerler `ignore` aralığı olur: üzerlerine düşen tahmin
  ne TP ne FP sayılır. 10+ haneli etiketsiz sayılar yanlış maskeleme negatifi sayılır. Tanıyıcılar bu setlere göre
  ayarlanmadı; ilk sonuçlar körlemesine alındı (2026-11-17).
- **Elle yazılmış set:** `benchmark/handwritten.txt`, `[değer](VARLIK)` işaretli cümleler; isme benzeyen sıradan
  kelimeler gibi şablonlarda olmayan zor durumlar için. Tanıyıcıları görmeden yazılır.
- **Bağımsız set:** `HELDOUT_TEMPLATES`, koda erişimi olmayan ayrı bir LLM ajanına yalnızca alan listesi, hangi alanın PII olduğu ve bir dağılım isteğiyle yazdırılmış 24 şablon: 12 PII'li (en az 3'ü ipucu kelimesiz, en az 2'si yazım hatalı alanla) ve 12 PII'siz (PII kelimelerine yakın numaralar dahil). Değer üreteçleri ana setle ortaktır; yalnızca cümle şablonları bağımsızdır.
  Tanıyıcılar bu sete göre ayarlanmaz; sonucu ana setten ayrı raporlanır.
- Tür gözetmeyen "maskelenen" oranı da raporlanır: varsayılan Presidio TC kimliği yanlış türle
  (`US_BANK_NUMBER`, `DATE_TIME`…) yakalayıp yine maskeleyebilir. Bu yüzden asıl karşılaştırma
  **yanlış maskeleme** oranıdır: PII olmayan sayıların (sipariş no, referans no) maskelenme oranı.
  Veri satırı bu sayıları `negatives` alanında taşır.
- Sonuç `benchmark/results/<YYYY-MM-DD>[-<etiket>].md` (ör. `-heldout`); README tablosu buradan.
- Üretilen veri commit'lenmez (`benchmark/data/` gitignore'da); script + sabit seed commit'lenir.

## Repo kuralları

- Gerçek kişi verisi yok; her şey sentetik.
- Şirket kodu, prompt'u ya da verisi yok; sıfırdan yazılır.
- `.env*` commit'lenmez; pre-commit'te gitleaks.
- README iki dilli: `README.md` Türkçe, `README_EN.md` İngilizce.

## Bitti tanımı

- `docker compose up` + README'deki tek `curl` demoyu gösterir.
- Benchmark tablosu README'de.
- Birim testler CI'da, e2e testler lokalde geçer.
