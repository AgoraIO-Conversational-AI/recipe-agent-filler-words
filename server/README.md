# Agora Agent Backend — Filler Words Recipe

FastAPI service that owns Agora token generation and agent session lifecycle for
the filler words recipe. It is the service the web client reaches through the
Next.js `/api/*` rewrite proxy (port 8000).

## What this service does

Runs the assistant pipeline using only Agora-managed vendors — **zero-key**:

**Pipeline:** `DeepgramSTT(nova-3)` → `OpenAI` (friendly assistant) → `MiniMaxTTS`

The `OpenAI` vendor is Agora-managed (keyless by default). There is **no
separate `llm/` service** in this recipe.

### filler_words

The builder in `server/src/filler_config.py` is passed to `AgoraAgent` as
`filler_words`. Static mode (the default) plays a randomly selected phrase from
the built-in list while the LLM is generating a response. Set
`FILLER_WORDS_MODE=generated` to use the Engine 2.12 generated filler
configuration. By default, Engine uses the generator provisioned for the App
ID in parallel with the main business LLM and falls back to the static list if
generation is not ready, fails, or returns empty text.

Developers can override the Engine-managed generator with a public
OpenAI-compatible provider by setting all three `FILLER_LLM_*` fields. The
backend only sends this configuration; Engine calls the provider directly.

### farewell_config

Embedded in `parameters` passed to `AgoraAgent`. When the session is stopped,
the agent speaks a farewell phrase and waits up to `graceful_timeout_seconds`
(5 s) before leaving the channel.

## Run

Use the repo-root `README.md` for the full local flow (`bun run dev`). To work on
this module directly:

The root commands below select the correct virtualenv interpreter on macOS,
Linux, and Windows, so activation is not required:

```shell
bun run setup:server
bun run backend
```

## Environment

`server/.env.example` is the template. Required:

- `AGORA_APP_ID` — Agora project App ID.
- `AGORA_APP_CERTIFICATE` — Agora project App Certificate.

Optional:

| Variable | Default | Notes |
| --- | :---: | --- |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model for the assistant |
| `OPENAI_API_KEY` | — | BYO only — Agora manages the OpenAI key by default (keyless). Set only if your account requires it. |
| `FILLER_WORDS_MODE` | `static` | `static` or `generated`. |
| `FILLER_LLM_BASE_URL` | — | Optional BYO provider URL; set all three `FILLER_LLM_*` fields together. |
| `FILLER_LLM_API_KEY` | — | Optional BYO provider key used by Engine. |
| `FILLER_LLM_MODEL` | — | Optional BYO provider model. |
| `TTS_VOICE` | `English_captivating_female1` | MiniMax TTS voice |
| `AGENT_GREETING` | built-in | Optional opening line override |

Generated mode uses the built-in prompt and the App ID's Engine-managed
generator when no provider fields are set. Otherwise, set all three fields to a
third-party public OpenAI-compatible provider. Use ngrok or another HTTPS tunnel
only when that provider runs locally; Agora Engine cannot call `localhost`.
Generated fillers use a fixed 1500 ms response-wait trigger.

## API

- `GET /get_config` — token + channel/UID config
- `POST /startAgent` — start an agent session
- `POST /stopAgent` — stop an agent session

The repo-root `bun run verify:local:fastapi` exercises these routes through the
Next proxy using a fake agent (`scripts/run_fake_server.py`), so no live Agora
session is required.
