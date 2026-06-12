# Agora Conversational AI — Translator Recipe (Python)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Bun](https://img.shields.io/badge/bun-latest-black)](https://bun.sh/)

The **translator** recipe in the Agora Conversational AI recipes family.
Real-time speech translation: speak in a source language, the agent translates and
speaks back in the target language. Fully **zero-key** — OpenAI is Agora-managed
(no `OPENAI_API_KEY` required unless you bring your own account).

**Pipeline:** `DeepgramSTT(language=SOURCE_LANG)` → `OpenAI` (translate) → `MiniMaxTTS(voice=TTS_VOICE)`

## Prerequisites

- [Python 3.10+](https://www.python.org/)
- [Bun](https://bun.sh/)
- [Agora CLI](https://github.com/AgoraIO/cli) — makes generating an App ID + App Certificate easy

## Run It

```bash
# 1. Install web deps + create the Python venv
bun run setup

# 2. Add Agora credentials (CLI), or edit server/.env.local by hand
agora login
agora project use <your-project>          # select which project to use
agora project env write server/.env.local # writes App ID + Certificate

# 3. (Optional) customise language pair in server/.env.local
#    SOURCE_LANG=es       # Deepgram language code for the speaker
#    TARGET_LANG=English  # language name used in the translation prompt
#    TTS_VOICE=English_captivating_female1  # MiniMax voice matching the target

# 4. Run backend + web
bun run dev
```

Open [http://localhost:3000](http://localhost:3000) → **Start Conversation** → speak in `SOURCE_LANG`.

### Working from a clone

If you cloned this repo (rather than scaffolding via the Agora CLI), the steps
above are complete as written: `bun run setup` creates the Python venv and
installs web dependencies, then `bun run dev` brings up both services. You
still need Agora credentials in `server/.env.local` before a conversation can connect.

Services:

- Frontend — http://localhost:3000
- Backend — http://localhost:8000
- Mock LLM — N/A (managed OpenAI, no local service)
- API docs — http://localhost:8000/docs

## Deploy

Deploy `web` (Next.js) and `server` (a reachable FastAPI backend). Set
`AGENT_BACKEND_URL` in the web deployment so the Next rewrites reach the backend.

A backend-only Docker image is published to
`ghcr.io/AgoraIO-Conversational-AI/recipe-agent-translator` on `v*` tags.
It exposes **BACKEND-ONLY** (:8000). No separate LLM container is needed —
OpenAI is Agora-managed.

## Environment variables

Backend env file: [`server/.env.example`](server/.env.example).

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | ✅ | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | ✅ | — | Agora Console → Project → App Certificate |
| `SOURCE_LANG` | | `es` | Deepgram STT language code (speaker's language) |
| `TARGET_LANG` | | `English` | Language name used in the translation prompt |
| `TTS_VOICE` | | `English_captivating_female1` | MiniMax voice matching `TARGET_LANG` |
| `OPENAI_MODEL` | | `gpt-4o-mini` | OpenAI model for translation |
| `OPENAI_API_KEY` | | — | Optional — Agora manages the OpenAI key by default (keyless). Set only if your account requires it. |
| `AGENT_GREETING` | | built-in | Optional opening line override |

> Note: when you change `TARGET_LANG`, also pick a matching `TTS_VOICE` for
> that target language.

## Commands

```bash
bun run setup            # install web deps + create server/ venv
bun run dev              # run backend (:8000) + web (:3000)

bun run doctor           # prerequisite check (no creds needed)
bun run doctor:local     # + .env.local + credentials checks

bun run verify           # web-only gate (no Agora creds needed)
bun run verify:local     # full local gate: backend compile + smoke tests + web build
bun run clean            # remove venvs and build artifacts
```

Tests run standalone (no Agora cloud needed): `pytest` in `server/`, plus
`bun run verify` in `web/`. CI runs them on Linux/macOS/Windows × Python 3.10 & 3.13.

## Architecture

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js  ──rewrite──▶  Agent backend  (server/, localhost:8000)
                          │  starts agent session (managed OpenAI vendor)
                          ▼
                       Agora ConvoAI Cloud
                          │  Deepgram STT (managed, SOURCE_LANG)
                          │  OpenAI translation (Agora-managed, keyless)
                          │  MiniMax TTS (managed, TTS_VOICE)
                          ▼
                       User hears translated speech
```

No separate `llm/` service — OpenAI is Agora-managed and requires no API key.
See [ARCHITECTURE.md](./ARCHITECTURE.md).

## What You Get

- A **Next.js** web client (:3000) that drives the RTC/RTM lifecycle and only ever calls `/api/*`.
- A **FastAPI** agent backend (:8000) that owns Agora token generation and the agent session lifecycle.
- The `/api/get_config` · `/api/startAgent` · `/api/stopAgent` contract between the web client and the backend (Next rewrites, no Route Handlers).
- **Managed keyless OpenAI** translating STT(source) → TTS(target) — Agora-managed, no `OPENAI_API_KEY` required.
- **Configurable language pair** via `SOURCE_LANG` / `TARGET_LANG` / `TTS_VOICE` environment variables.
- **Zero-key** setup — the full pipeline runs with no LLM API key by default.

## How It Works

1. The browser calls `/api/get_config`, which Next rewrites to the backend; the
   backend mints an Agora token from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
2. The browser joins the RTC channel, then calls `/api/startAgent`; the backend
   starts an agent session using the managed OpenAI vendor.
3. The user speaks in `SOURCE_LANG`. Agora runs STT (Deepgram, `SOURCE_LANG` locale)
   and produces a transcript.
4. Agora's managed OpenAI stage receives the transcript with a translation system
   prompt and produces the translated text in `TARGET_LANG`.
5. Agora runs TTS (MiniMax, `TTS_VOICE`) on the translated text and plays it back
   in the channel. No API key is required — Agora manages the OpenAI account.
6. `/api/stopAgent` ends the session.

## Repo Map

- `web/` — Next.js frontend (:3000); RTC/RTM lifecycle and UI.
- `server/` — FastAPI agent backend (:8000); Agora tokens + agent lifecycle, managed OpenAI translation.
- `ARCHITECTURE.md` — system shape and component boundaries.
- `AGENTS.md` — guide for coding agents working in this repo.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Agent starts but does not translate | Check `SOURCE_LANG` is a valid Deepgram BCP-47 code. |
| Wrong TTS voice / language | Set `TTS_VOICE` to a MiniMax voice matching your `TARGET_LANG`. |
| Local calls fail under a global proxy (Clash, etc.) | Configure your proxy to send `127.0.0.1`, `localhost`, and RFC-1918 ranges DIRECT. |

## More Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [AGENTS.md](./AGENTS.md)

## License

Released under the [MIT License](./LICENSE).
