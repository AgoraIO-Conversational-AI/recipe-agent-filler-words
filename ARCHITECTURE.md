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
- No tunnel (ngrok) is required for static mode.
- The only required credentials are `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.

Generated mode uses the generator provisioned for the App ID when available.
Otherwise, developers provide a third-party public OpenAI-compatible provider.

## Filler words

`server/src/filler_config.py` contains pure builder functions:

- `build_filler_words()` — returns the `filler_words` dict passed to
  `AgoraAgent(...)`. It uses `mode: "static"` by default. Set
  `FILLER_WORDS_MODE=generated` to add the Engine 2.12
  `content.generated_config`. Generated mode uses the App ID's Engine-managed
  generator by default, uses a fixed 1500 ms trigger, and always includes the
  static fallback list.
- `build_generated_filler_words()` — optionally adds a BYO OpenAI-compatible
  provider when all three provider fields are set.
- `build_farewell()` — returns the `farewell_config` dict embedded in
  `parameters`. Enables graceful exit with a 5-second window for the agent to
  speak a farewell before leaving the channel.

In generated mode the backend omits `llm_provider` unless the developer sets all
three `FILLER_LLM_*` fields. This selects the SDK's Engine-managed path. A BYO
provider must be reachable from Agora's service, and its API key must be scoped
and managed as a server-side secret.

## Generated filler verification

For the default path, set `FILLER_WORDS_MODE=generated` and leave the
`FILLER_LLM_*` fields unset. The App ID must have the Engine generator enabled.
Otherwise, set a third-party public provider URL, API key, and model together.
If that provider runs locally, expose it with ngrok or another HTTPS tunnel;
the tunnel request log can confirm Engine calls `POST /chat/completions`.

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
