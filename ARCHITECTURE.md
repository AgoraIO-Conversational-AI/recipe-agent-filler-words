# Architecture — Translator Recipe

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
  │  builds session with OpenAI(model=OPENAI_MODEL, system_messages=[translate to TARGET_LANG])
  ▼
Agora ConvoAI Cloud
  │  user speech → Deepgram STT (managed, language=SOURCE_LANG)
  │  text → OpenAI translation (Agora-managed, keyless, model=OPENAI_MODEL)
  │  translation → MiniMax TTS (managed, voice_id=TTS_VOICE)
  ▼
User hears translated speech; RTM transcript + metrics → web UI
```

`POST /api/stopAgent { agentId }` ends the session.

## Why no llm/ service

Unlike the custom-llm recipe, the translator uses the **managed OpenAI vendor**
(`agora_agent.agentkit.vendors.OpenAI`). Agora holds the OpenAI API key on its
cloud; the recipe is zero-key by default. An optional `OPENAI_API_KEY` env var
lets you bring your own account if needed.

This means:
- No `llm/` service to expose publicly.
- No tunnel (ngrok) required.
- The only required credentials are `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.

## Translation prompt

`server/src/translation_config.py` contains the pure `build_translation_system_messages`
function, which builds the system prompt injected into every OpenAI call:

> "Translate the user's message into {TARGET_LANG}. Output only the translation,
> with no extra commentary, quotation marks, or explanations."

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/get_config` | GET | Token + channel/UID config |
| `/startAgent` | POST | Start the translation agent session |
| `/stopAgent` | POST | Stop the agent by `agent_id` |

The browser calls these as `/api/*`; Next rewrites them to `AGENT_BACKEND_URL`.

## Auth

- Browser → agent backend: none (local dev).
- Agent backend → Agora cloud: Token007, generated from `AGORA_APP_ID` +
  `AGORA_APP_CERTIFICATE`.
- Agora cloud → OpenAI: Agora-managed key (transparent to this recipe).
  Optionally overridden by `OPENAI_API_KEY` if provided.
