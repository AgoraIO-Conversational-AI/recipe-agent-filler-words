# Architecture — Filler Words Recipe

Two processes. The browser talks only to Next.js `/api/*`, which rewrites to the
agent backend. The agent backend owns Agora tokens and agent lifecycle. OpenAI is
Agora-managed (keyless) — no separate LLM service is needed.

## Request flow

```
Browser
  │  GET /api/filler_config         → initial mode from FILLER_WORDS_MODE
  │  GET /api/get_config            → token + channel/UIDs
  │  POST /api/startAgent           → start session with fillerWordsMode
  ▼
Next.js  (rewrites /api/* → AGENT_BACKEND_URL)
  ▼
Agent backend (server/, :8000)
  │  builds session with OpenAI(model=OPENAI_MODEL, system_messages=[friendly assistant])
  │  filler_words: static or Engine 2.12 generated phrase during LLM latency
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
- No tunnel (ngrok) is required for either filler mode.
- The only required credentials are `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.

Generated mode uses the SDK's default Engine-managed generator for the App ID.
No filler provider URL, API key, or model is configured by the developer.

## Filler words

`server/src/filler_config.py` contains pure builder functions:

- `build_filler_words(mode)` — returns the `filler_words` dict passed to
  `AgoraAgent(...)`. The web UI initializes its selector from `/filler_config`,
  which resolves `FILLER_WORDS_MODE` (default `static`), then lets the user select
  `static` or `generated` per conversation. It sends the selection as
  `fillerWordsMode` in `/startAgent`. When omitted, the backend uses the same
  environment default. Generated mode adds the Engine 2.12
  `content.generated_config`. Generated mode uses the App ID's Engine-managed
  generator by default and always includes the static fallback list. Both modes
  explicitly use `FILLER_RESPONSE_WAIT_MS = 1500`, matching the Engine default.
  A primary LLM response before the deadline cancels the filler. Generated mode
  starts filler generation in parallel with the primary LLM; at the deadline it
  plays a ready generated phrase or the static fallback and cancels any pending
  generation.
- `build_generated_filler_words()` — omits `llm_provider` to use the SDK's
  default Engine-managed generator.
- `build_farewell()` — returns the `farewell_config` dict embedded in
  `parameters`. Enables graceful exit with a 5-second window for the agent to
  speak a farewell before leaving the channel.

Generated mode always omits `llm_provider`, selecting the SDK's Engine-managed
path. Legacy `FILLER_LLM_*` environment variables are ignored.

## Generated filler verification

Select **Generated** in the web UI and start a conversation. The App ID must
have the Engine generator enabled. API callers can send `fillerWordsMode` or
use the `FILLER_WORDS_MODE=generated` backend default. No custom endpoint is
required.

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/filler_config` | GET | Default filler mode from the backend environment; no token or session |
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
