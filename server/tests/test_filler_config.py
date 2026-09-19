import os, sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import filler_config as fc  # noqa: E402


def test_filler_words_payload_static_with_phrases(monkeypatch):
    monkeypatch.delenv("FILLER_WORDS_MODE", raising=False)
    payload = fc.build_filler_words()
    assert payload["enable"] is True
    assert payload["content"]["mode"] == "static"
    assert len(payload["content"]["static_config"]["phrases"]) >= 3
    assert payload["content"]["static_config"]["selection_rule"] in ("shuffle", "round_robin")


def test_filler_words_payload_generated_with_static_fallback(monkeypatch):
    monkeypatch.setenv("FILLER_WORDS_MODE", "generated")

    payload = fc.build_filler_words()
    content = payload["content"]

    assert content["mode"] == "generated"
    assert content["static_config"]["phrases"]
    assert "llm_provider" not in content["generated_config"]
    assert content["generated_config"]["prompt"] == fc.DEFAULT_GENERATED_PROMPT
    assert content["generated_config"]["fallback_strategy"] == "static"
    assert content["generated_config"]["context_message_limit"] == 4
    assert content["generated_config"]["history_character_limit"] == 1000


def test_generated_filler_uses_engine_provider_by_default(monkeypatch):
    for name in ("FILLER_LLM_BASE_URL", "FILLER_LLM_API_KEY", "FILLER_LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)

    content = fc.build_generated_filler_words()["content"]

    assert content["mode"] == "generated"
    assert content["static_config"]["phrases"]
    assert "llm_provider" not in content["generated_config"]
    assert content["generated_config"]["fallback_strategy"] == "static"


@pytest.mark.parametrize("mode", ["static", "generated"])
def test_both_filler_modes_use_default_wait_threshold(mode):
    payload = fc.build_filler_words(mode)

    assert payload["trigger"] == {
        "mode": "fixed_time",
        "fixed_time_config": {"response_wait_ms": 1500},
    }


def test_generated_filler_prompt_is_not_configured_from_environment(monkeypatch):
    monkeypatch.setenv("FILLER_LLM_PROMPT", "temporary local prompt")

    content = fc.build_generated_filler_words()["content"]

    assert content["generated_config"]["prompt"] == fc.DEFAULT_GENERATED_PROMPT


@pytest.mark.parametrize("legacy_fields", [
    {"FILLER_LLM_BASE_URL": "https://example.com/v1"},
    {
        "FILLER_LLM_BASE_URL": "https://example.com/v1",
        "FILLER_LLM_API_KEY": "unused-legacy-key",
        "FILLER_LLM_MODEL": "unused-legacy-model",
    },
])
def test_generated_filler_ignores_legacy_provider_environment(monkeypatch, legacy_fields):
    for name, value in legacy_fields.items():
        monkeypatch.setenv(name, value)

    content = fc.build_generated_filler_words()["content"]
    assert "llm_provider" not in content["generated_config"]


def test_filler_words_rejects_unknown_mode():
    with pytest.raises(ValueError, match="FILLER_WORDS_MODE"):
        fc.build_filler_words("unsupported")


def test_farewell_payload_graceful():
    fw = fc.build_farewell()
    assert fw["graceful_enabled"] is True
    assert fw["graceful_timeout_seconds"] >= 1
