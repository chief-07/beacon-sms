import pytest
from src.services.ai_service import sanitize_for_sms
from src.services.memory_service import MemoryService


def test_sanitize_removes_markdown():
    markdown_text = "**Emergency:** Do *not* apply oil to burns! Use `clean cold water`."
    clean = sanitize_for_sms(markdown_text, max_chars=280)
    assert "**" not in clean
    assert "*" not in clean
    assert "`" not in clean
    assert "Emergency: Do not apply oil to burns! Use clean cold water." in clean


def test_sanitize_preserves_gsm7_ascii():
    # Accented letters should be converted to plain ASCII
    accented_text = "Tọjú ọmọ rẹ pẹlu omi tútù ati suga."
    clean = sanitize_for_sms(accented_text, max_chars=280)
    # Check that diacritics are removed to prevent UCS-2 SMS downgrade
    assert "ọ" not in clean
    assert "ẹ" not in clean
    assert "Toju omo re pelu omi tutu ati suga." in clean


def test_sanitize_truncates_at_boundary():
    long_text = "This is a sentence. " * 30  # ~600 characters
    clean = sanitize_for_sms(long_text, max_chars=160)
    assert len(clean) <= 160
    assert clean.endswith("...")


def test_memory_service_multi_turn():
    mem = MemoryService(ttl_minutes=10, max_turns=2)
    phone = "+2348011112222"

    mem.add_user_message(phone, "My corn leaves have holes")
    mem.add_assistant_message(phone, "That sounds like fall armyworm. Check under the leaves.")
    mem.add_user_message(phone, "What organic spray can I use?")

    history = mem.get_conversation_history(phone)
    assert len(history) == 3
    assert history[0]["content"] == "My corn leaves have holes"
    assert history[2]["content"] == "What organic spray can I use?"

    # Adding a fourth message (2nd turn completion)
    mem.add_assistant_message(phone, "Mix neem leaf extract with water and mild soap.")
    history = mem.get_conversation_history(phone)
    assert len(history) == 4

    # Adding a fifth message should evict the oldest messages (max_turns=2 means max 4 messages)
    mem.add_user_message(phone, "How often should I spray?")
    history = mem.get_conversation_history(phone)
    assert len(history) == 4
    assert history[0]["role"] == "assistant"


def test_split_into_sms_segments_short():
    from src.services.sms_service import split_into_sms_segments
    short_text = "Take paracetamol and drink plenty of water."
    segments = split_into_sms_segments(short_text, max_len=160)
    assert len(segments) == 1
    assert segments[0] == short_text


def test_split_into_sms_segments_multi():
    from src.services.sms_service import split_into_sms_segments
    text = (
        "For malaria, go to a clinic immediately for a blood test. "
        "Do not rely on home remedies. While waiting, drink plenty of water to stay hydrated "
        "and take paracetamol to lower your fever. If you are vomiting or confused, seek emergency care at once."
    )
    segments = split_into_sms_segments(text, max_len=160)
    assert len(segments) == 2
    assert segments[0].startswith("(1/2) ")
    assert segments[1].startswith("(2/2) ")
    for seg in segments:
        assert len(seg) <= 160


@pytest.mark.asyncio
async def test_sms_service_segment_dispatch(monkeypatch):
    from src.services.sms_service import sms_service
    from src.config import settings

    # Reduce delay for fast test execution
    monkeypatch.setattr(settings, "sms_segment_delay_seconds", 0.01)

    long_text = (
        "For malaria, go to a clinic immediately for a blood test. "
        "Do not rely on home remedies. While waiting, drink plenty of water to stay hydrated "
        "and take paracetamol to lower your fever. If you are vomiting or confused, seek emergency care at once."
    )
    result = await sms_service.send_sms(
        to_phone="+2348011223344",
        content=long_text,
        from_phone="+2349132628938"
    )

    assert result.get("status") in ("sent", "simulated")
    assert result.get("segments_count") == 2
    assert len(result.get("results")) == 2


@pytest.mark.asyncio
async def test_gemini_fallback_cascade(monkeypatch):
    import httpx
    import re
    from src.services.ai_service import ai_service
    from src.config import settings

    called_models = []

    async def mock_post(self, url, json=None):
        m = re.search(r"models/([^:]+):", str(url))
        model_name = m.group(1) if m else "unknown"
        called_models.append(model_name)

        class MockResponse:
            def __init__(self, status_code, data_json, text=""):
                self.status_code = status_code
                self._json = data_json
                self.text = text
                self.request = httpx.Request("POST", str(url))

            def json(self):
                return self._json

            def raise_for_status(self):
                if self.status_code != 200:
                    raise httpx.HTTPStatusError("Error", request=self.request, response=self)

        # Primary model fails with 503 (Overloaded / high usage)
        if model_name == settings.gemini_model:
            return MockResponse(503, {}, "Model overloaded / High usage")
        else:
            # Fallback model succeeds
            return MockResponse(200, {
                "candidates": [{
                    "content": {
                        "parts": [{"text": f"Success from fallback model {model_name}"}]
                    }
                }]
            })

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    response = await ai_service._generate_gemini_rest(
        system_prompt="Test prompt",
        history=[],
        user_message="Hello"
    )

    assert len(called_models) >= 2
    assert called_models[0] == settings.gemini_model
    assert "Success from fallback model" in response
