"""Construction smoke: the real AgoraAgent is built and a session is created (SDK session faked).

Closes the gap where the rest of the suite stubs the whole Agent (FakeAgent) and never
exercises AgoraAgent construction — the exact path that agora-agents 2.3.x changed.
"""
import asyncio
import sys

from filler_config import build_generated_filler_words


def _fresh_agent_module():
    sys.modules.pop("agent", None)
    import agent
    return agent


def test_start_constructs_real_agent_and_returns_shape(fake_env, monkeypatch):
    agent = _fresh_agent_module()
    monkeypatch.setenv("FILLER_WORDS_MODE", "static")
    captured = {}

    class FakeSession:
        async def start(self):
            return "test-agent-id"

        async def stop(self):
            captured["stopped"] = True

    def fake_create_async_session(self, **kwargs):
        captured["channel"] = kwargs.get("channel")
        captured["remote_uids"] = kwargs.get("remote_uids")
        captured["filler_words"] = self.filler_words
        return FakeSession()

    from agora_agent.agentkit import Agent as AgoraAgent
    monkeypatch.setattr(AgoraAgent, "create_async_session", fake_create_async_session)

    instance = agent.Agent()
    result = asyncio.run(instance.start(channel_name="ch", agent_uid=111, user_uid=222))

    assert result["agent_id"] == "test-agent-id"
    assert result["channel_name"] == "ch"
    assert result["status"] == "started"
    assert captured["channel"] == "ch"
    assert captured["remote_uids"] == ["222"]
    assert captured["filler_words"]["content"]["mode"] == "static"


def test_start_passes_generated_filler_config_to_engine(fake_env, monkeypatch):
    agent = _fresh_agent_module()
    monkeypatch.setenv("FILLER_WORDS_MODE", "generated")
    for name in ("FILLER_LLM_BASE_URL", "FILLER_LLM_API_KEY", "FILLER_LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    captured = {}

    class FakeSession:
        async def start(self):
            return "test-generated-agent-id"

    def fake_create_async_session(self, **kwargs):
        captured["filler_words"] = self.filler_words
        return FakeSession()

    from agora_agent.agentkit import Agent as AgoraAgent
    monkeypatch.setattr(AgoraAgent, "create_async_session", fake_create_async_session)

    result = asyncio.run(agent.Agent().start(channel_name="ch", agent_uid=111, user_uid=222))

    generated = captured["filler_words"]["content"]
    assert result["agent_id"] == "test-generated-agent-id"
    assert generated["mode"] == "generated"
    assert "llm_provider" not in generated["generated_config"]
    assert generated["static_config"]["phrases"]


def test_generated_filler_uses_sdk_provider_url():
    from agora_agent.agentkit import Agent as AgoraAgent

    filler_words = build_generated_filler_words(
        base_url="https://api.deepseek.com",
        api_key="test-filler-key",
        model="test-model",
    )
    properties = AgoraAgent(object(), filler_words=filler_words).to_properties(
        channel="test-channel",
        agent_uid="1",
        remote_uids=[],
        token="test-token",
        allow_missing_vendor_categories={"asr", "llm", "tts"},
    )
    provider = properties.filler_words.content.generated_config.llm_provider
    serialized = provider.model_dump(exclude_none=True)

    assert serialized["url"] == "https://api.deepseek.com/chat/completions"
    assert "base_url" not in serialized


def test_generated_filler_supports_engine_provider_in_current_sdk(monkeypatch):
    from agora_agent.agentkit import Agent as AgoraAgent

    for name in ("FILLER_LLM_BASE_URL", "FILLER_LLM_API_KEY", "FILLER_LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)

    filler_words = build_generated_filler_words(prompt="Generate one short filler")
    properties = AgoraAgent(object(), filler_words=filler_words).to_properties(
        channel="test-channel",
        agent_uid="1",
        remote_uids=[],
        token="test-token",
        allow_missing_vendor_categories={"asr", "llm", "tts"},
    )

    generated = properties.filler_words.content.generated_config
    assert generated.llm_provider is None
    assert generated.prompt == "Generate one short filler"
