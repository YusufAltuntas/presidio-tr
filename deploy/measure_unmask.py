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
