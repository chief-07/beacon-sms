import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "BeaconSMS Gateway"


def test_cloudevents_webhook_incoming():
    payload = {
        "specversion": "1.0",
        "type": "message.phone.received",
        "source": "/v1/messages/receive",
        "id": "test-uuid-1234",
        "time": "2026-09-27T10:00:00Z",
        "datacontenttype": "application/json",
        "data": {
            "contact": "+2348012345678",
            "content": "Wetin be the fastest first aid for burn?",
            "owner": "+2348000000000",
            "sim": "SIM1",
            "message_id": "msg-001"
        }
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["sender"] == "+2348012345678"


def test_flat_webhook_incoming():
    payload = {
        "from": "+2348099999999",
        "text": "How do I protect my maize from armyworm?",
        "to": "+2348000000000"
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["sender"] == "+2348099999999"


def test_invalid_webhook_ignored():
    payload = {"random_key": "some value"}
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"
