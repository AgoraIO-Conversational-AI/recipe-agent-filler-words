# Architecture — Filler Words Recipe

Two processes. The browser talks only to Next.js `/api/*`, which rewrites to the
agent backend. The agent backend owns Agora tokens and agent lifecycle. OpenAI is
Agora-managed (keyless) — no separate LLM service is needed.

## Request flow

```
Browser
  │  GET /api/get_config            → token + channel/UIDs
  │  POST /api/startAgent           → start agent session
  ▼
Next.js  (rewrites /api/* → AGENT_BACKEND_URL)
  ▼
Agent backend (server/, :8000)
  │  builds session with OpenAI(model=OPENAI_MODEL, system_messages=[friendly assistant])
  │  filler_words: static phrase list played during LLM latency
  │  farewell_config: graceful exit on stop (graceful_enabled=true, graceful_timeout_seconds=5)
  ▼
Agora ConvoAI Cloud
  │  user speech → Deepgram STT (managed, nova-3)
  │  text → OpenAI assistant (Agora-managed, keyless, model=OPENAI_MODEL)
  │         [filler phrase plays while LLM generates]
  │  response → MiniMax TTS (managed)
  ▼
User hears the agent; RTM transcript + metrics → web UI
```

`POST /api/stopAgent { agentId }` ends the session. The agent speaks a farewell
phrase before leaving the channel (`farewell_config`).

## Why no llm/ service

This recipe uses the **managed OpenAI vendor**
(`agora_agent.agentkit.vendors.OpenAI`). Agora holds the OpenAI API key on its
cloud; the recipe is zero-key by default. An optional `OPENAI_API_KEY` env var
lets you bring your own account if needed.

This means:
- No `llm/` service to expose publicly.
- No tunnel (ngrok) required.
- The only required credentials are `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.

## Filler words

`server/src/filler_config.py` contains two pure builder functions:

- `build_filler_words()` — returns the `filler_words` dict passed to
  `AgoraAgent(...)`. Uses `mode: "static"` with a shuffled phrase list. SDK
  2.0.0 supports static mode only; LLM-generated fillers are not available in
  this version.
- `build_farewell()` — returns the `farewell_config` dict embedded in
  `parameters`. Enables graceful exit with a 5-second window for the agent to
  speak a farewell before leaving the channel.

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/get_config` | GET | Token + channel/UID config |
| `/startAgent` | POST | Start the filler-words agent session |
| `/stopAgent` | POST | Stop the agent by `agent_id` |

The browser calls these as `/api/*`; Next rewrites them to `AGENT_BACKEND_URL`.

## Auth

- Browser → agent backend: none (local dev).
- Agent backend → Agora cloud: Token007, generated from `AGORA_APP_ID` +
  `AGORA_APP_CERTIFICATE`.
- Agora cloud → OpenAI: Agora-managed key (transparent to this recipe).
  Optionally overridden by `OPENAI_API_KEY` if provided.
