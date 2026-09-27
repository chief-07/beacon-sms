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


def test_landing_page_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "BeaconSMS" in response.text
    assert "+234 913 262 8938" in response.text
    assert "+234 814 688 2274" in response.text


def test_sms_service_gateway_key_resolution():
    from src.services.sms_service import sms_service
    key1 = sms_service._get_api_key_for_sender("+2349132628938")
    assert key1 == "uk_54q08c8whrt6id9QfbEh8G0t11I0LeCF__BTXYVozvQirAixmaVANNCEvvzqVSAa"
    key2 = sms_service._get_api_key_for_sender("+2348146882274")
    assert key2 == "uk_f6fS89DCOdiuDuttQoXlttOYc7mP3QLiToXjiPmwUR6jeN7jgtSk-yNCF18r7_sC"


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


def test_sent_and_delivered_events_ignored():
    # Outbound delivery events should be instantly discarded to prevent loops
    for event_type in ["message.phone.sent", "message.phone.delivered", "message.send.failed"]:
        payload = {
            "type": event_type,
            "data": {
                "contact": "+2348012345678",
                "content": "This is an outbound AI message that must not loop",
                "owner": "+2348000000000"
            }
        }
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
        assert "not an incoming message" in data["reason"]


def test_duplicate_message_ignored():
    payload = {
        "type": "message.phone.received",
        "data": {
            "contact": "+2348011223344",
            "content": "First message",
            "message_id": "unique-msg-999"
        }
    }
    r1 = client.post("/webhook", json=payload)
    assert r1.status_code == 200
    assert r1.json()["status"] == "queued"

    # Exact same message ID again should be ignored
    r2 = client.post("/webhook", json=payload)
    assert r2.status_code == 200
    assert r2.json()["status"] == "ignored"
    assert r2.json()["reason"] == "Duplicate message"

