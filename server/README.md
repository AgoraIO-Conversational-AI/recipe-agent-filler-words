# Agora Agent Backend — Translator Recipe

FastAPI service that owns Agora token generation and agent session lifecycle for
the translator recipe. It is the service the web client reaches through the
Next.js `/api/*` rewrite proxy (port 8000).

## What this service does

Runs the translation pipeline using only Agora-managed vendors — **zero-key**:

**Pipeline:** `DeepgramSTT(language=SOURCE_LANG)` → `OpenAI` (translate to `TARGET_LANG`) → `MiniMaxTTS(voice_id=TTS_VOICE)`

The `OpenAI` vendor is Agora-managed (keyless by default). There is **no
separate `llm/` service** in this recipe.

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
| `SOURCE_LANG` | `es` | Deepgram STT language code for the speaker |
| `TARGET_LANG` | `English` | Language name used in the translation prompt |
| `TTS_VOICE` | `English_captivating_female1` | MiniMax voice matching `TARGET_LANG` |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model for translation |
| `OPENAI_API_KEY` | — | BYO only — Agora manages the OpenAI key by default (keyless). Set only if your account requires it. |
| `AGENT_GREETING` | built-in | Optional opening line override |

> Note: when you change `TARGET_LANG`, also pick a matching `TTS_VOICE` for
> that target language.

## API

- `GET /get_config` — token + channel/UID config
- `POST /startAgent` — start an agent session
- `POST /stopAgent` — stop an agent session

The repo-root `bun run verify:local:fastapi` exercises these routes through the
Next proxy using a fake agent (`scripts/run_fake_server.py`), so no live Agora
session is required.
