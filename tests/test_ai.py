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
