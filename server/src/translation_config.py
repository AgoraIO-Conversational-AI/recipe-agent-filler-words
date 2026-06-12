"""Pure builder for the translator recipe — no agora_agent import."""
from typing import Dict, List


def build_translation_system_messages(target_lang: str) -> List[Dict[str, str]]:
    content = (
        f"You are a translation assistant. Translate the user's message into "
        f"{target_lang}. Output only the translation, with no extra commentary, "
        f"quotation marks, or explanations."
    )
    return [{"role": "system", "content": content}]
