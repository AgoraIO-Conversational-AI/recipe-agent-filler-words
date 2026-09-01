"""Pure builders for Agora filler-words + graceful-exit config.

The generated filler provider is called by Agora Engine. This module only
builds the join payload and never makes an LLM request itself.
"""

import os

FILLER_PHRASES = [
    "Let me think about that for a second.",
    "Good question - one moment.",
    "Hmm, let me check.",
    "Sure, give me just a sec.",
    "Right, let me look into that.",
]


DEFAULT_GENERATED_PROMPT = (
    "Generate one short conversational filler phrase based on the user's last "
    "message. Do not answer the user or add punctuation beyond the phrase."
)
FILLER_PROVIDER_ENV_VARS = (
    "FILLER_LLM_BASE_URL",
    "FILLER_LLM_API_KEY",
    "FILLER_LLM_MODEL",
)


def build_static_filler_words() -> dict:
    return {
        "enable": True,
        "content": {
            "mode": "static",
            "static_config": {
                "phrases": list(FILLER_PHRASES),
                "selection_rule": "shuffle",
            },
        },
    }


def _chat_completions_url(base_url: str) -> str:
    """Accept a provider base URL or a full chat-completions endpoint."""
    normalized = base_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def build_generated_filler_words(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    prompt: str | None = None,
) -> dict:
    """Build Engine 2.12 generated filler config.

    With no provider settings, Engine uses the generator provisioned for the
    App ID. Setting all FILLER_LLM_* fields selects a developer-provided
    OpenAI-compatible endpoint instead.
    """
    resolved_prompt = (prompt or DEFAULT_GENERATED_PROMPT).strip()

    provider_values = {
        "FILLER_LLM_BASE_URL": (
            base_url if base_url is not None else os.getenv("FILLER_LLM_BASE_URL")
        ),
        "FILLER_LLM_API_KEY": (
            api_key if api_key is not None else os.getenv("FILLER_LLM_API_KEY")
        ),
        "FILLER_LLM_MODEL": (
            model if model is not None else os.getenv("FILLER_LLM_MODEL")
        ),
    }
    provider_values = {
        name: (value or "").strip() for name, value in provider_values.items()
    }
    configured_fields = [name for name, value in provider_values.items() if value]
    if configured_fields and len(configured_fields) != len(FILLER_PROVIDER_ENV_VARS):
        missing_fields = [
            name for name in FILLER_PROVIDER_ENV_VARS if not provider_values[name]
        ]
        raise ValueError(
            "Explicit generated filler provider requires "
            "FILLER_LLM_BASE_URL, FILLER_LLM_API_KEY, and FILLER_LLM_MODEL "
            f"together; missing {', '.join(missing_fields)}"
        )

    generated_config = {
        "prompt": resolved_prompt,
        "fallback_strategy": "static",
    }
    if configured_fields:
        generated_config["llm_provider"] = {
            "url": _chat_completions_url(provider_values["FILLER_LLM_BASE_URL"]),
            "api_key": provider_values["FILLER_LLM_API_KEY"],
            "params": {"model": provider_values["FILLER_LLM_MODEL"]},
        }

    return {
        "enable": True,
        "trigger": {
            "mode": "fixed_time",
            "fixed_time_config": {"response_wait_ms": 1500},
        },
        "content": {
            "mode": "generated",
            # Generated mode requires static phrases as its fallback.
            "static_config": {
                "phrases": list(FILLER_PHRASES),
                "selection_rule": "shuffle",
            },
            "generated_config": generated_config,
        },
    }


def build_filler_words(mode: str | None = None) -> dict:
    """Build filler config, keeping static mode as the safe default."""
    selected_mode = (mode or os.getenv("FILLER_WORDS_MODE", "static")).strip().lower()
    if selected_mode == "static":
        return build_static_filler_words()
    if selected_mode == "generated":
        return build_generated_filler_words()
    raise ValueError("FILLER_WORDS_MODE must be 'static' or 'generated'")


def build_farewell() -> dict:
    return {"graceful_enabled": True, "graceful_timeout_seconds": 5}
