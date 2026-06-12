"""Pure builders for Agora filler-words + graceful-exit config (no agora_agent import)."""

FILLER_PHRASES = [
    "Let me think about that for a second.",
    "Good question — one moment.",
    "Hmm, let me check.",
    "Sure, give me just a sec.",
    "Right, let me look into that.",
]


def build_filler_words() -> dict:
    return {
        "enable": True,
        "content": {
            "mode": "static",
            "static_config": {"phrases": FILLER_PHRASES, "selection_rule": "shuffle"},
        },
    }


def build_farewell() -> dict:
    return {"graceful_enabled": True, "graceful_timeout_seconds": 5}
