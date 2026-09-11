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
    monkeypatch.setenv("FILLER_LLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("FILLER_LLM_API_KEY", "test-filler-key")
    monkeypatch.setenv("FILLER_LLM_MODEL", "test-model")

    payload = fc.build_filler_words()
    content = payload["content"]
    provider = content["generated_config"]["llm_provider"]

    assert content["mode"] == "generated"
    assert content["static_config"]["phrases"]
    assert provider["api_key"] == "test-filler-key"
    assert provider["url"] == "https://api.openai.com/v1/chat/completions"
    assert "base_url" not in provider
    assert provider["params"] == {"model": "test-model"}
    assert content["generated_config"]["prompt"] == fc.DEFAULT_GENERATED_PROMPT
    assert content["generated_config"]["fallback_strategy"] == "static"


def test_generated_filler_uses_engine_provider_by_default(monkeypatch):
    for name in ("FILLER_LLM_BASE_URL", "FILLER_LLM_API_KEY", "FILLER_LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)

    content = fc.build_generated_filler_words()["content"]

    assert content["mode"] == "generated"
    assert content["static_config"]["phrases"]
    assert "llm_provider" not in content["generated_config"]
    assert content["generated_config"]["fallback_strategy"] == "static"


def test_generated_filler_sets_fixed_time_trigger():
    payload = fc.build_generated_filler_words()

    assert payload["trigger"] == {
        "mode": "fixed_time",
        "fixed_time_config": {"response_wait_ms": 1500},
    }


def test_generated_filler_prompt_is_not_configured_from_environment(monkeypatch):
    monkeypatch.setenv("FILLER_LLM_PROMPT", "temporary local prompt")

    content = fc.build_generated_filler_words()["content"]

    assert content["generated_config"]["prompt"] == fc.DEFAULT_GENERATED_PROMPT


def test_generated_filler_rejects_partial_explicit_provider(monkeypatch):
    monkeypatch.setenv("FILLER_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.delenv("FILLER_LLM_API_KEY", raising=False)
    monkeypatch.delenv("FILLER_LLM_MODEL", raising=False)

    with pytest.raises(ValueError, match="requires .* together"):
        fc.build_generated_filler_words()


def test_filler_words_rejects_unknown_mode():
    with pytest.raises(ValueError, match="FILLER_WORDS_MODE"):
        fc.build_filler_words("unsupported")


def test_generated_filler_appends_chat_completions_to_provider_url():
    payload = fc.build_generated_filler_words(
        base_url="https://api.deepseek.com/",
        api_key="test-filler-key",
        model="test-model",
    )

    provider = payload["content"]["generated_config"]["llm_provider"]
    assert provider["url"] == "https://api.deepseek.com/chat/completions"


@pytest.mark.parametrize(
    ("base_url", "expected"),
    [
        (
            "https://example.azure.com/openai/deployments/demo?api-version=2026-01-01",
            "https://example.azure.com/openai/deployments/demo/chat/completions?api-version=2026-01-01",
        ),
        (
            "https://example.azure.com/chat/completions?api-version=2026-01-01",
            "https://example.azure.com/chat/completions?api-version=2026-01-01",
        ),
    ],
)
def test_generated_filler_preserves_provider_url_query(base_url, expected):
    payload = fc.build_generated_filler_words(
        base_url=base_url,
        api_key="test-filler-key",
        model="test-model",
    )

    provider = payload["content"]["generated_config"]["llm_provider"]
    assert provider["url"] == expected


def test_farewell_payload_graceful():
    fw = fc.build_farewell()
    assert fw["graceful_enabled"] is True
    assert fw["graceful_timeout_seconds"] >= 1
