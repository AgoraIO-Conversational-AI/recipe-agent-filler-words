"""Construction smoke: the real AgoraAgent is built and a session is created (SDK session faked).

Closes the gap where the rest of the suite stubs the whole Agent (FakeAgent) and never
exercises AgoraAgent construction — the exact path that agora-agents 2.3.x changed.
"""
import asyncio
import sys

import pytest

from filler_config import build_filler_words


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


@pytest.mark.parametrize(("default_mode", "requested_mode", "expected_mode"), [
    ("static", "generated", "generated"),
    ("generated", "static", "static"),
    ("generated", None, "generated"),
    ("static", None, "static"),
])
def test_start_passes_session_filler_mode_to_engine(
    fake_env, monkeypatch, default_mode, requested_mode, expected_mode,
):
    agent = _fresh_agent_module()
    monkeypatch.setenv("FILLER_WORDS_MODE", default_mode)
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

    result = asyncio.run(agent.Agent().start(
        channel_name="ch", agent_uid=111, user_uid=222,
        filler_words_mode=requested_mode,
    ))

    content = captured["filler_words"]["content"]
    assert result["agent_id"] == "test-generated-agent-id"
    assert content["mode"] == expected_mode
    assert content["static_config"]["phrases"]
    if expected_mode == "generated":
        assert "llm_provider" not in content["generated_config"]


@pytest.mark.parametrize("mode", ["static", "generated"])
def test_filler_trigger_survives_sdk_serialization(mode):
    from agora_agent.agentkit import Agent as AgoraAgent

    filler_words = build_filler_words(mode)
    properties = AgoraAgent(object(), filler_words=filler_words).to_properties(
        channel="test-channel",
        agent_uid="1",
        remote_uids=[],
        token="test-token",
        allow_missing_vendor_categories={"asr", "llm", "tts"},
    )

    serialized = properties.filler_words.model_dump(exclude_none=True)
    assert serialized["content"]["mode"] == mode
    assert serialized["trigger"] == {
        "mode": "fixed_time",
        "fixed_time_config": {"response_wait_ms": 1500},
    }
    if mode == "generated":
        assert "llm_provider" not in serialized["content"]["generated_config"]
