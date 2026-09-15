# Agent Development Guide

For coding agents working in `recipe-agent-filler-words`. This repository is the
**filler words** recipe in the Agora Conversational AI recipes family.

## System shape

- **`server/`** — Python FastAPI agent backend (:8000). Owns Agora token
  generation and agent session lifecycle. Uses the managed `OpenAI` vendor
  (Agora-managed, keyless) for the assistant. SDK: `agora-agents`
  (`import agora_agent`); the dependency version is defined in
  `server/requirements.txt`.
- **`web/`** — Next.js 16 / React 19 / TypeScript frontend (:3000).
- Auth: Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
- No `llm/` service — OpenAI is Agora-managed (zero-key by default).

## Pipeline

`DeepgramSTT(nova-3)` → `OpenAI` (friendly assistant) → `MiniMaxTTS`

With:
- `filler_words`: built-in static phrases by default, or Engine 2.12 generated phrases with static fallback
- `farewell_config`: graceful exit before the agent leaves on stop

## Routing / ownership

- UI and RTC/RTM lifecycle live in `web/`.
- Browser-facing `/api/*` paths are Next rewrites (`web/next.config.ts`) to the
  agent backend; do not add `web/app/api/**/route.ts` for agent/token logic.
- Token generation and agent lifecycle live in `server/src/`.
- Filler-words and farewell builders live in `server/src/filler_config.py`.

## Supported modes

- **Local:** `bun run dev` starts `server` (:8000) and `web` (:3000).
  The web app calls `/api/*`; Next rewrites to
  `AGENT_BACKEND_URL=http://localhost:8000`.
- **Deploy:** deploy `web` (Next) + `server` (reachable FastAPI).
  Set `AGENT_BACKEND_URL` in the web deployment.

## Env vars

| Variable | Default | Notes |
|---|---|---|
| `AGORA_APP_ID` | — | required |
| `AGORA_APP_CERTIFICATE` | — | required |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model for the assistant |
| `OPENAI_API_KEY` | — | optional — BYO only if your account requires it |
| `TTS_VOICE` | `English_captivating_female1` | MiniMax TTS voice |
| `AGENT_GREETING` | built-in | Optional opening line override |
| `FILLER_WORDS_MODE` | `static` | Initial web selection (via `/filler_config`) and default when `/startAgent` omits `fillerWordsMode` |

## Patterns

- Keep the web client calling `/api/*`; hide backend placement behind Next rewrites.
- Keep token generation and the App Certificate in `server/`.
- `OPENAI_API_KEY` is optional: Agora manages the OpenAI key by default (keyless).
- Edit `FILLER_PHRASES` in `server/src/filler_config.py` to customise the filler list.
- Read `/api/filler_config` before enabling the mode selector. Use the backend's
  `default_mode` for the initial selection and preserve later user selections.
- Both modes use `FILLER_RESPONSE_WAIT_MS = 1500`, matching the Engine default.
  Primary LLM content before the deadline cancels the filler; generated content
  that is not ready at the deadline uses the static fallback.
- `build_filler_words()` and `build_farewell()` are pure functions — test them
  without any agora_agent import.

## Anti-patterns

- Do not reintroduce `llm/` or the `CustomLLM` vendor.
- Do not reintroduce Next Route Handlers for agent/token logic.
- Do not put `PORT` in `server/.env.example` (it would clobber the random port
  that `verify:local:fastapi` injects via `load_dotenv(override=True)`).
- Do not link to `docs/ai/` — that progressive-disclosure tree is not present yet.
- Generated mode omits `llm_provider` and uses the SDK's default Engine-managed
  generator. Do not require filler provider configuration; legacy `FILLER_LLM_*`
  variables are ignored.

## Commands

```bash
bun run setup
bun run dev
bun run doctor
bun run doctor:local
bun run verify         # web-only, no creds
bun run verify:local   # full local gate
```

Narrower checks: `bun run verify:backend`, `bun run verify:local:fastapi`,
`bun run verify:web:proxy`.

## Done criteria

1. Run the narrowest relevant verification command.
2. Web-affecting changes: `bun run verify:web` passes.
3. Backend-affecting changes: `bun run verify:local` (or narrower
   `verify:local:fastapi` / `verify:backend`) passes.
4. If you change required env vars or setup steps, update the root README,
   the relevant module README, and `server/.env.example` together.

## Git conventions

- Conventional Commits: `type: description` or `type(scope): description`
  (`feat`, `fix`, `chore`, `test`, `docs`). Lowercase after the prefix, present
  tense.
- No AI tool names in commit messages or PR descriptions. No `Co-Authored-By`
  trailers. No `--no-verify`. No git config changes.
- Branch names: `type/short-description` (e.g. `feat/add-filler-phrases`).
