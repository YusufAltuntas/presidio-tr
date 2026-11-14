"""Compose ayaktayken çalışan uçtan uca testler.

Kullanım: set -a && . deploy/.env && set +a && uv run pytest -m e2e -v
"""

import json
import os
import re
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


def _langfuse_observations_with_output(user: str) -> list[dict]:
    """Langfuse'ta bu kullanıcıya ait, en az bir tanesi çıktısı (generation) olan gözlemleri bekler (en çok 120 sn)."""
    deadline = time.time() + 120
    observations: list[dict] = []
    while time.time() < deadline:
        # Langfuse v4 "events_only" modunda v1 /traces uçları kapalı; v2 observations ucu kullanılır.
        response = httpx.get(
            f"{LANGFUSE}/api/public/v2/observations",
            params={"userId": user, "fields": "core,basic,io", "limit": 50},
            auth=_langfuse_auth(),
            timeout=10,
        )
        observations = response.json().get("data", []) if response.status_code == 200 else []
        # Gözlemler farklı anlarda yazılır; TC kimliği taşıyan içerik (maskeli ya da değil) gelene kadar bekle.
        serialized = json.dumps(observations, ensure_ascii=False)
        has_output = any(o.get("output") is not None for o in observations)
        if has_output and ("<TR_NATIONAL_ID" in serialized or TCKN_1 in serialized):
            return observations
        time.sleep(3)
    pytest.fail(
        "Langfuse'ta bu kullanıcıya ait çıktılı gözlem bulunamadı (attribution ya da callback çalışmıyor): "
        f"{len(observations)} gözlem"
    )


def _assert_langfuse_masked(observations: list[dict]) -> None:
    serialized = json.dumps(observations, ensure_ascii=False)
    assert TCKN_1 not in serialized
    # Pozitif kontrol: loglanan çıktıda maskeli etiket var (akışsız yanıtta logging hook'u numarasız,
    # akışlı yanıtta sağlayıcının döndürdüğü numaralı etiket loglanır).
    outputs = json.dumps([o.get("output") for o in observations], ensure_ascii=False)
    assert re.search(r"<TR_NATIONAL_ID(_\d+)?>", outputs)
    # Ön-çağrı maskelemesinin kanıtı: yalnızca pre_call guardrail'i (output_parse_pii) numaralı etiket üretir;
    # girdide <TR_NATIONAL_ID_1> varsa sağlayıcıya giden metin zaten maskeliydi.
    inputs = json.dumps([o.get("input") for o in observations], ensure_ascii=False)
    assert "<TR_NATIONAL_ID_1>" in inputs


def test_langfuse_never_sees_raw_pii_and_keeps_end_user():
    user = f"e2e-{time.time_ns()}"
    _content(_chat(_echo(f"TC kimlik no {TCKN_1}."), user=user))
    _assert_langfuse_masked(_langfuse_observations_with_output(user))


def test_langfuse_never_sees_raw_pii_for_streaming():
    user = f"e2e-stream-{time.time_ns()}"
    text = ""
    with httpx.stream(
        "POST",
        f"{LITELLM}/v1/chat/completions",
        headers={"Authorization": f"Bearer {_master_key()}"},
        json={
            "model": MODEL,
            "messages": _echo(f"TC kimlik no {TCKN_1}."),
            "user": user,
            "temperature": 0,
            "stream": True,
        },
        timeout=60,
    ) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if not line.startswith("data: ") or line == "data: [DONE]":
                continue
            for choice in json.loads(line[len("data: ") :]).get("choices", []):
                text += choice.get("delta", {}).get("content") or ""
    assert TCKN_1 in text
    _assert_langfuse_masked(_langfuse_observations_with_output(user))


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
