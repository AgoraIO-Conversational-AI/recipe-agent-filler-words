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

A static phrase list (defined in `server/src/filler_config.py`) is passed to
`AgoraAgent` as `filler_words`. Agora plays a randomly selected phrase from the
list while the LLM is generating a response, masking dead air. SDK 2.0.0
supports `mode: "static"` only — LLM-generated fillers are not available in
this version.

### farewell_config

Embedded in `parameters` passed to `AgoraAgent`. When the session is stopped,
the agent speaks a farewell phrase and waits up to `graceful_timeout_seconds`
(5 s) before leaving the channel.

## Run

Use the repo-root `README.md` for the full local flow (`bun run dev`). To work on
this module directly:

```bash
cd server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/server.py
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
| `TTS_VOICE` | `English_captivating_female1` | MiniMax TTS voice |
| `AGENT_GREETING` | built-in | Optional opening line override |

## API

- `GET /get_config` — token + channel/UID config
- `POST /startAgent` — start an agent session
- `POST /stopAgent` — stop an agent session

The repo-root `bun run verify:local:fastapi` exercises these routes through the
Next proxy using a fake agent (`scripts/run_fake_server.py`), so no live Agora
session is required.
