# 08 · Security

> Trust boundaries, secret handling, and auth for the filler-words recipe.

## Trust boundaries

| Hop                          | Auth                                                                          |
| ---------------------------- | ----------------------------------------------------------------------------- |
| Browser → agent backend      | None in local dev (the `/api/*` rewrite is same-origin).                      |
| Agent backend → Agora cloud  | Token007, generated from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.            |
| Agora cloud → OpenAI         | Agora-managed key (transparent to this recipe). Optionally `OPENAI_API_KEY`. |
| Agora cloud → Deepgram/MiniMax | Agora-managed (transparent to this recipe).                                 |

## Secret handling

- **Server-only secrets:** `AGORA_APP_CERTIFICATE` lives only in `server/.env.local` and never reaches the browser. The browser receives a short-lived token, never the certificate.
- `OPENAI_API_KEY` is optional and, when provided, lives only in `server/.env.local`. Agora manages the OpenAI key by default.
- `server/.env.local` is gitignored; `server/.env.example` ships placeholders only.
- Tokens (`generate_convo_ai_token`) expire after 3600s and are minted per `get_config` call for a concrete non-zero UID.

## CORS

The backend sets `CORSMiddleware` with `allow_origins=["*"]` — open by design for a local/dev recipe. **Lock this down to known origins before any production deployment.**

## Validation

- `Agent.__init__` rejects missing `AGORA_APP_ID`/`AGORA_APP_CERTIFICATE` immediately on boot.
- `Agent.start()` rejects empty `channel_name` and non-positive `agent_uid`/`user_uid` before issuing tokens or starting a session.
- Route errors are sanitized: `_log_route_error` logs only non-`None` context; SDK exceptions map to 400/500 without leaking internals to the client beyond the message.

## Deployment notes

- Set `AGENT_BACKEND_URL` only to a backend you control; the rewrite forwards browser requests there verbatim.
- The published Docker image is **backend-only** (`:8000`); it does not bundle secrets.

## Related Deep Dives

- None.
