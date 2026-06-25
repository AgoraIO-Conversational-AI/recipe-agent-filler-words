# Deep Dive — Filler Words Config

> **When to Read This:** You are changing filler phrases, farewell behavior, VAD turn detection, session parameters, or any aspect of the `AgoraAgent` construction in `agent.py`. For the high-level picture, start at [02_architecture](../02_architecture.md).

The filler-words recipe configures three distinct behavioral layers on `AgoraAgent`: filler phrases (latency smoothing), farewell (graceful exit), and turn detection (VAD). All three live in `server/src/`.

## Filler words (`build_filler_words`)

Source: `server/src/filler_config.py`

```python
def build_filler_words() -> dict:
    return {
        "enable": True,
        "content": {
            "mode": "static",
            "static_config": {"phrases": FILLER_PHRASES, "selection_rule": "shuffle"},
        },
    }
```

- `FILLER_PHRASES` is a module-level list of strings — edit it freely.
- `mode` must be `"static"` — SDK 2.0.0 does not support any other mode (see [07_gotchas](../07_gotchas.md)).
- `selection_rule` is `"shuffle"` (random); `"round_robin"` is also accepted by the test.
- The dict is passed as `filler_words=build_filler_words()` to `AgoraAgent(...)`.

## Farewell (`build_farewell`)

Source: `server/src/filler_config.py`

```python
def build_farewell() -> dict:
    return {"graceful_enabled": True, "graceful_timeout_seconds": 5}
```

- Embedded in the `parameters` dict as `parameters["farewell_config"]`, **not** as a top-level arg to `AgoraAgent`.
- `graceful_timeout_seconds: 5` gives the agent 5 seconds to speak a farewell before leaving the channel.
- To disable graceful exit, set `graceful_enabled: False`.

## Turn detection (VAD)

Set as a top-level argument on `AgoraAgent(...)` in `Agent.start()` (`server/src/agent.py`):

```python
turn_detection={
    "config": {
        "speech_threshold": 0.5,
        "start_of_speech": {
            "mode": "vad",
            "vad_config": {
                "interrupt_duration_ms": 160,
                "prefix_padding_ms": 300,
            },
        },
        "end_of_speech": {
            "mode": "vad",
            "vad_config": {
                "silence_duration_ms": 480,
            },
        },
    },
},
```

This is **different** from the MLLM recipe: in the cascading pipeline, VAD is agent-owned, not vendor-owned.

## Session `parameters`

Set in `Agent.start()` and passed to `AgoraAgent`:

| Key                    | Value                              | Why                                               |
| ---------------------- | ---------------------------------- | ------------------------------------------------- |
| `audio_scenario`       | `chorus`                           | Ultra-low-latency profile for web clients.        |
| `data_channel`         | `rtm`                              | Transcript + metrics delivered over RTM.          |
| `enable_error_message` | `true`                             | Surface agent-side errors to the client.          |
| `enable_metrics`       | `true`                             | Emit pipeline metrics to the UI.                  |
| `farewell_config`      | `build_farewell()` result          | Graceful exit on stop.                            |
| `output_audio_codec`   | optional string                    | Forwarded from `POST /startAgent` `parameters`.   |

## How it is all wired into the session

In `Agent.start()` (`agent.py`):

```python
llm = OpenAI(api_key=self.openai_api_key, model=self.openai_model,
             system_messages=[...], greeting_message=self.greeting, temperature=0.7)
stt = DeepgramSTT(model="nova-3")
tts = MiniMaxTTS(model="speech_2_6_turbo", voice_id=self.tts_voice)

agora_agent = AgoraAgent(
    client=self.client,
    greeting=self.greeting,
    failure_message="Please wait a moment.",
    max_history=50,
    turn_detection={...},
    advanced_features={"enable_rtm": True},
    parameters={"farewell_config": build_farewell(), ...},
    filler_words=build_filler_words(),
)
agora_agent = agora_agent.with_stt(stt).with_llm(llm).with_tts(tts)

session = agora_agent.create_async_session(
    channel=channel_name,
    agent_uid=str(agent_uid),
    remote_uids=[str(user_uid)],
    enable_string_uid=False,
    idle_timeout=30,
    expires_in=3600,
)
agent_id = await session.start()
```

## Related L1

- [02_architecture](../02_architecture.md) · [06_interfaces](../06_interfaces.md) · [07_gotchas](../07_gotchas.md)
