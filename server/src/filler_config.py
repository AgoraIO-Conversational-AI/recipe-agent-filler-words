"""Pure builders for Agora filler-words + graceful-exit config.

The generated filler provider is called by Agora Engine. This module only
builds the join payload and never makes an LLM request itself.
"""

import os

# Match Engine's default wait. A primary LLM response before this deadline wins.
FILLER_RESPONSE_WAIT_MS = 1500

FILLER_PHRASES = [
    "Let me think about that for a second.",
    "Good question - one moment.",
    "Hmm, let me check.",
    "Sure, give me just a sec.",
    "Right, let me look into that.",
]


DEFAULT_GENERATED_PROMPT = (
    "Generate one short conversational filler phrase based on the recent "
    "conversation context. Return only the filler phrase and do not answer the user's "
    "question. End the phrase with appropriate punctuation."
)


def build_static_filler_words() -> dict:
    return {
        "enable": True,
        "trigger": {
            "mode": "fixed_time",
            "fixed_time_config": {"response_wait_ms": FILLER_RESPONSE_WAIT_MS},
        },
        "content": {
            "mode": "static",
            "static_config": {
                "phrases": list(FILLER_PHRASES),
                "selection_rule": "shuffle",
            },
        },
    }


def build_generated_filler_words(
    *,
    prompt: str | None = None,
) -> dict:
    """Build generated fillers using the SDK's default Engine-managed provider."""
    resolved_prompt = (prompt or DEFAULT_GENERATED_PROMPT).strip()

    # Omit llm_provider so the SDK uses Engine's default generator settings.
    generated_config = {
        "prompt": resolved_prompt,
        "fallback_strategy": "static",
        "context_message_limit": 4,
        "history_character_limit": 1000,
    }

    # Share the same trigger and phrase list with static mode. Generated mode
    # uses these phrases as its fallback when generation misses the deadline.
    filler_words = build_static_filler_words()
    filler_words["content"].update({
        "mode": "generated",
        "generated_config": generated_config,
    })
    return filler_words


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
