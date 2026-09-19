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
the built-in list while the LLM is generating a response. Choose **Generated**
in the web UI or send `"fillerWordsMode": "generated"` to `/startAgent` to use
Engine 2.12 generated fillers. The SDK's default Engine-managed generator runs
in parallel with the main business LLM and falls back to the static list if
generation is not ready, fails, or returns empty text. No filler provider URL,
API key, or model is needed.

`FILLER_WORDS_MODE` supplies the initial web selection and the mode for requests
that omit `fillerWordsMode`; it defaults to `static`. The web app reads the
default through `/filler_config` before enabling its mode selector. Each start
request's selection takes precedence without affecting other sessions. Restart
the backend and refresh the page after changing this environment variable.

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
| `FILLER_WORDS_MODE` | `static` | Initial web selection and default when a start request omits `fillerWordsMode`; `static` or `generated`. |
| `TTS_VOICE` | `English_captivating_female1` | MiniMax TTS voice |
| `AGENT_GREETING` | built-in | Optional opening line override |

Generated mode uses the built-in prompt and the SDK's default Engine-managed
generator. Legacy `FILLER_LLM_*` variables are ignored and can be removed.
Both modes use a 1500 ms response-wait trigger, matching the Engine default and
configured by `FILLER_RESPONSE_WAIT_MS` in `src/filler_config.py`. If the primary
LLM responds before the deadline, no filler plays. In Generated mode, generation
runs in parallel with the primary LLM; if no generated phrase is ready at the
deadline, Engine plays a static fallback and cancels the pending generation.
A shorter wait makes static fallback more likely. Generated fillers use up to
four recent messages, capped at 1000 characters, as conversation context.

Startup logs include the selected mode and threshold. Restart the backend and
start a new conversation after changes. No custom endpoint or public tunnel is
required.

## API

- `GET /filler_config` — public defaults as `data.default_mode`; no token or
  session is created
- `GET /get_config` — token + channel/UID config
- `POST /startAgent` — start an agent session; optional `fillerWordsMode` accepts
  `static` or `generated` (invalid values return HTTP 422)
- `POST /stopAgent` — stop an agent session

The repo-root `bun run verify:local:fastapi` exercises these routes through the
Next proxy using a fake agent (`scripts/run_fake_server.py`), so no live Agora
session is required.
