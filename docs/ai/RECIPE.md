---
recipe_version: 1.0.0
recipe_status: experimental
extension_points:
  - id: api.routes
    name: Browser-facing API routes
  - id: agent.filler-config
    name: Filler phrases, farewell timeout, and selection rule
  - id: agent.vendors
    name: STT model, LLM model/prompt/temperature, TTS voice
  - id: web.conversation-ui
    name: Conversation UI panels and controls
  - id: verification.contracts
    name: Contract, proxy, and local FastAPI smoke verification
invariants:
  - id: api.rewrite-boundary
    summary: Browser calls stay on /api/* and Next rewrites to FastAPI; no Route Handlers for agent/token logic.
  - id: secrets.server-only
    summary: Agora App Certificate stays in the Python backend; OPENAI_API_KEY is optional and also server-only if set.
  - id: pipeline.cascading
    summary: Three Agora-managed vendors (DeepgramSTT → OpenAI → MiniMaxTTS) assembled via .with_stt().with_llm().with_tts(); no llm/ service.
  - id: filler.static-mode
    summary: filler_words mode must be "static"; SDK 2.0.0 supports no other mode.
  - id: farewell.in-parameters
    summary: farewell_config is embedded in the parameters dict, not as a top-level AgoraAgent argument.
  - id: token.uid-concrete
    summary: Backend resolves missing, zero, or negative UIDs before issuing an RTC+RTM token.
stable_contracts:
  - id: env.required
    summary: AGORA_APP_ID and AGORA_APP_CERTIFICATE are required; AGENT_BACKEND_URL is required by deployed web rewrites.
  - id: api.core-routes
    summary: GET /api/get_config, POST /api/startAgent, and POST /api/stopAgent remain the browser-facing contract.
  - id: response.envelope
    summary: Successful backend responses use { code, msg, data }.
---

# Recipe Contract

This base recipe defines the reusable surface for a Python-backed Agora Conversational AI **filler words** quickstart: a cascading STT→LLM→TTS pipeline with latency smoothing (filler phrases) and graceful exit behind a Next.js web client.

## Recipe Role

- Role: `base` recipe (self-contained, clone-and-run; no `Extends` pin).
- Target audience: developers building a voice agent that masks LLM latency with natural filler phrases and exits gracefully.
- Reuse model: clone, bind project, run, then customize filler phrases, vendors, or browser UI.

## Recipe Scope

- Python FastAPI token generation and managed agent lifecycle.
- Three Agora-managed vendors (`DeepgramSTT`, `OpenAI`, `MiniMaxTTS`) assembled via the cascading builder API.
- `filler_words` static phrase list played during LLM latency (SDK 2.0.0 supports `mode: "static"` only).
- `farewell_config` graceful exit on session stop.
- Next.js browser UI with RTC audio, RTM transcript/metrics, connection status.
- Rewrite-only `/api/*` browser facade hiding backend placement.
- Contract, proxy, and local FastAPI smoke verification that need no live Agora calls.

## Baseline Implementation Guidance

Use this repo's source and progressive disclosure docs as the starting point, then customize. Do not recreate the Agora ConvoAI integration from memory — vendor schemas, SDK builder fields, token behavior, and RTM details drift. Copy verified patterns from this repo.

## Extension Points

| ID | Surface | How to extend | Required follow-up |
| -- | ------- | ------------- | ------------------ |
| `api.routes` | `server/src/server.py`, `web/next.config.ts`, `web/src/services/api.ts` | Add FastAPI route, add rewrite, add browser fetch helper. | Extend `web/scripts/verify-api-contracts.ts`; add proxy/fastapi coverage if it belongs in local verification. |
| `agent.filler-config` | `server/src/filler_config.py` | Edit `FILLER_PHRASES`, `selection_rule`, or `graceful_timeout_seconds`. | Run `cd server && pytest tests -v`; phrase count must remain >= 3. |
| `agent.vendors` | `server/src/agent.py` | Change `OPENAI_MODEL`, `TTS_VOICE`, `temperature`, `system_messages`, `AGENT_GREETING`, or swap to a different Agora-managed vendor. | Run `bun run verify:backend` + `pytest tests`; document new env in `server/.env.example` (never add `PORT`). |
| `web.conversation-ui` | `web/src/components/*`, `web/src/lib/conversation.ts` | Customize pre-call, transcript, metrics, connection status, mic, or visualizer UI. | Preserve RTC/RTM lifecycle ownership and transcript UID normalization. |
| `verification.contracts` | `web/scripts/*.ts`, root `package.json` | Add checks for new browser/backend boundaries. | Keep checks runnable without live Agora credentials. |

## Invariants

- Browser code calls only `/api/get_config`, `/api/startAgent`, and `/api/stopAgent` for the default flow.
- Next.js owns `/api/*` through rewrites only; no `web/app/api/**/route.ts` for agent/token logic.
- FastAPI owns token generation, `AGORA_APP_CERTIFICATE`, and agent lifecycle.
- Three Agora-managed vendors handle the full cascading pipeline; `turn_detection` is set as a top-level `AgoraAgent` argument.
- `filler_words` `mode` must remain `"static"`.
- `farewell_config` is embedded in `parameters`, not a top-level argument.
- The backend issues one RTC+RTM-capable token for a concrete non-zero UID.

## Stable Contracts

| Contract | Stable shape |
| -------- | ------------ |
| Required backend env | `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE` |
| Optional backend env | `OPENAI_MODEL`, `OPENAI_API_KEY`, `TTS_VOICE`, `AGENT_GREETING`, `PORT` (env only) |
| Required web deploy env | `AGENT_BACKEND_URL` |
| `GET /api/get_config` | Query `channel?`, `uid?`; returns `data.app_id`, `data.token`, `data.uid`, `data.channel_name`, `data.agent_uid`. |
| `POST /api/startAgent` | Body `{ channelName, rtcUid, userUid, parameters? }`; returns `data.agent_id`, `data.channel_name`, `data.status`. |
| `POST /api/stopAgent` | Body `{ agentId }`; returns `{ code: 0, msg: "success" }`. |
| Success envelope | `{ "code": 0, "msg": "success", "data": ... }` where the route has data. |
| Verification entry points | `bun run verify:web`, `bun run verify:backend`, `bun run verify:web:proxy`, `bun run verify:local:fastapi`, `bun run verify:local`. |

## Internal / Subject to Change

- Visual layout, component composition, Tailwind classes, and assets under `web/src/components/`.
- Exact filler phrases, farewell timeout, and greeting text, as long as they stay documented extension points.
- In-memory `Agent._sessions` details; the stable behavior is start by channel/user and stop by returned `agent_id`.
- Verification internals under `web/scripts/`; the stable surface is the root script names and what they assert.
- `agora-agents` SDK minor-version behavior; this recipe lower-bounds `>=2.3.0` but does not freeze every field.

## Related Progressive Disclosure Docs

- `L1/01_setup.md` — setup, env, and commands.
- `L1/02_architecture.md` — request flow and topology.
- `L1/05_workflows.md` — common modification workflows.
- `L1/06_interfaces.md` — route, rewrite, env, and filler/farewell config contracts.
- `L1/L2/filler_words_config.md` — full filler/farewell/VAD config detail.
- `L1/L2/session_lifecycle.md` — RTC/RTM/session orchestration.
