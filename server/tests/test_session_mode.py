"""Verify mode selection crosses the HTTP boundary before starting a session."""

import pytest


@pytest.mark.parametrize(("env_mode", "expected"), [
    (None, "static"),
    ("static", "static"),
    ("generated", "generated"),
    (" GENERATED ", "generated"),
])
def test_filler_config_exposes_environment_default(client, monkeypatch, env_mode, expected):
    if env_mode is None:
        monkeypatch.delenv("FILLER_WORDS_MODE", raising=False)
    else:
        monkeypatch.setenv("FILLER_WORDS_MODE", env_mode)

    response = client.get("/filler_config")

    assert response.status_code == 200
    assert response.json() == {"code": 0, "data": {"default_mode": expected}, "msg": "success"}
    assert client.fake_agent.started == []


def test_filler_config_rejects_invalid_environment_default(client, monkeypatch):
    monkeypatch.setenv("FILLER_WORDS_MODE", "unsupported")

    response = client.get("/filler_config")

    assert response.status_code == 400
    assert "FILLER_WORDS_MODE" in response.json()["detail"]


@pytest.mark.parametrize("mode", ["static", "generated", None])
def test_start_forwards_mode_and_preserves_optional_codec(client, mode):
    payload = {
        "channelName": "mode-test",
        "rtcUid": 111,
        "userUid": 222,
        "parameters": {"output_audio_codec": "OPUS"},
    }
    if mode is not None:
        payload["fillerWordsMode"] = mode

    response = client.post("/startAgent", json=payload)

    assert response.status_code == 200
    assert response.json()["data"]["agent_id"] == "fake-agent-111"
    assert client.fake_agent.started == [("mode-test", 111, 222, "OPUS", mode)]


@pytest.mark.parametrize("mode", ["unsupported", "", 123])
def test_start_rejects_invalid_mode_before_creating_a_session(client, mode):
    response = client.post("/startAgent", json={
        "channelName": "mode-test",
        "rtcUid": 111,
        "userUid": 222,
        "fillerWordsMode": mode,
    })

    assert response.status_code == 422
    assert client.fake_agent.started == []
