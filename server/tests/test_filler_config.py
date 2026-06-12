import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import filler_config as fc  # noqa: E402


def test_filler_words_payload_static_with_phrases():
    payload = fc.build_filler_words()
    assert payload["enable"] is True
    assert payload["content"]["mode"] == "static"
    assert len(payload["content"]["static_config"]["phrases"]) >= 3
    assert payload["content"]["static_config"]["selection_rule"] in ("shuffle", "round_robin")


def test_farewell_payload_graceful():
    fw = fc.build_farewell()
    assert fw["graceful_enabled"] is True
    assert fw["graceful_timeout_seconds"] >= 1
