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
