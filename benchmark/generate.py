"""Etiketli sentetik Türkçe benchmark verisi üretir.

Kullanım: python -m benchmark.generate --n 1000 --seed 42 --out benchmark/data/tr_pii.jsonl
Bağımsız set: python -m benchmark.generate --templates heldout --out benchmark/data/tr_pii_heldout.jsonl
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
    "date": (lambda r, f: f"{r.randint(1, 28):02d}.{r.randint(1, 12):02d}.{r.randint(2015, 2026)}", None),
    "ref_no": (lambda r, f: synth.ref_no(r), NEGATIVE),
}

TEMPLATES = [
    # TC kimlik
    "Merhaba, TC kimlik numaram {tckn}, başvurumun durumunu öğrenebilir miyim?",
    "Kimlik no: {tckn} — adım {name}.",
    "{name} adına kayıtlı {tckn} numaralı müşteri için işlem yapıldı.",
    "Nüfus cüzdanımdaki numara {tckn}, sistemde görünmüyor.",
    "TC'm {tckn_typo} olarak girildi ama hata veriyor.",
    "Kimliğimdeki numarayı yazıyorum: {tckn_typo}",
    "Başvuru formuna {tckn_typo} yazmışım, düzeltebilir misiniz?",  # zor durum: bağlam yok, tasarım gereği kaçar
    # VKN
    "Firma {vkn} numarasıyla kayıtlı.",  # zor durum: bağlam yok, tasarım gereği kaçar
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
    "Bana {bare_phone} üzerinden dönebilir misiniz?",  # zor durum: bağlam yok, tasarım gereği kaçar
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
    "Hesap hareketi referansı {ref_no} olarak kaydedildi.",
    "Toplam {amount}, ödeme tarihi {date}.",
    "Kampanya kodu {ref_no} {date} tarihine kadar geçerli.",
    # Zor negatifler: bağlam kelimesi var ama sayı PII değil
    "Kimlik doğrulama kodunuz {order_no}, kimseyle paylaşmayın.",
    "Vergi dairesi başvuru numaranız {ref_no}.",
    "Telefon faturanızın numarası {ref_no}, son ödeme {date}.",
    "TC Kargo takip numaranız {order_no}.",
]

HELDOUT_TEMPLATES = [
    # PII içeren
    "Merhaba, ben {name}. Kimlik numaram {tckn}, sözleşmemi yenilemek istiyorum.",  # resmi, "kimlik numaram" ipucu
    "abi tc'si {tckn} olan hattı kapatır mısınız",  # samimi, küçük harf, ekli "tc'si"
    "Şirketimizin vergi no'su {vkn}, faturaları bu numaraya kesin lütfen.",  # ekli "vergi no'su"
    "İade tutarı {amount} IBAN'ıma yatırılsın: {iban}",  # ekli "IBAN'ıma"
    "Beni şu numaradan arayabilirsiniz: {phone}. Akşam 18:00 sonrası müsaitim.",  # telefon, ipucu kelime var
    "{name} {bare_phone}",  # ipucusuz: isim + öneksiz telefon
    "{name} {tckn}",  # ipucusuz: isim + TCKN
    "{iban}",  # ipucusuz: tek başına IBAN
    "TC kimlik no yanlış yazdım galiba: {tckn_typo}, kontrol eder misiniz? {city} şubesinden başvurmuştum.",  # typo TCKN
    "Vergi numaramız {vkn_typo} diye kayıtlı görünüyor ama sistem hata veriyor, {date} tarihli fatura için.",  # typo VKN
    "havale için hesap: {iban_typo} ismi {name}, {amount} gönderilecek",  # typo IBAN, samimi
    "Sn. {name}, müşteri irtibat tel: {bare_phone} / alternatif GSM {phone} olarak kayda geçirildi.",  # iki telefon biçimi
    # PII içermeyen
    "Siparişiniz {order_no} numarasıyla kargoya verilmiştir, tahmini teslim {date}.",  # kargo takip no
    "Fatura no {ref_no} için ödeme hatırlatması: {amount} son ödeme tarihi {date}.",  # fatura referansı
    "{name} Hanım, {ref_no} numaralı dosyanız incelemeye alındı.",  # dosya no, isimle birlikte
    "Başvuru numaranız {ref_no}. Sonucu SMS ile bildireceğiz.",  # başvuru no, "SMS" telefona yakın
    "Poliçe no {ref_no} kapsamındaki hasar talebiniz {city} servisine iletildi.",  # poliçe numarası
    "Abonelik kodunuz {ref_no}; {date} itibarıyla {amount} tutarında yenilendi.",  # abonelik kodu
    "Sözleşme numarası {ref_no} olan hattınızın tarifesi değişti, bilgi için müşteri hizmetlerini arayın.",  # "hat", "arayın"
    "Takip numarası: {order_no} - kargonuz {city} dağıtım merkezinde bekliyor.",  # 11 haneli takip no
    "iade talebi oluşturdum, sipariş numaram {order_no}, ürün hasarlı geldi",  # samimi, 11 haneli sipariş no
    "Dekont: {ref_no}. {amount} tutarındaki havale {date} tarihinde hesabınıza geçti.",  # "hesap" yakın, referans
    "Vergi dairesi işlem no {ref_no} ile e-arşiv faturanız oluşturuldu.",  # "vergi" + 10 hane, VKN değil
    "Kimlik doğrulama talebiniz {order_no} numaralı işlem olarak kaydedildi, {name}.",  # "kimlik" + 11 haneli işlem no
]

TEMPLATE_SETS = {"main": TEMPLATES, "heldout": HELDOUT_TEMPLATES}


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


def generate(n: int, seed: int, templates: list[str] = TEMPLATES) -> list[dict]:
    """Sabit seed ile verilen şablonlardan n etiketli örnek üretir."""
    rng = random.Random(seed)
    fake = Faker("tr_TR")
    fake.seed_instance(seed)
    return [render(rng.choice(templates), rng, fake) for _ in range(n)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("benchmark/data/tr_pii.jsonl"))
    parser.add_argument("--templates", choices=sorted(TEMPLATE_SETS), default="main")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in generate(args.n, args.seed, TEMPLATE_SETS[args.templates]):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{args.n} örnek yazıldı: {args.out}")


if __name__ == "__main__":
    main()
