import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import translation_config as cfg  # noqa: E402

def test_build_translation_system_messages():
    msgs = cfg.build_translation_system_messages("French")
    assert msgs[0]["role"] == "system"
    assert "French" in msgs[0]["content"]
    assert "only the translation" in msgs[0]["content"].lower()
