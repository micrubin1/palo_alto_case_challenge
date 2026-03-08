from unittest.mock import patch

from backend.ai_engine import _fallback_parse, parse_resume


def test_keyword_fallback_returns_list():
    result = _fallback_parse("I know Python and AWS and some Docker.")
    assert isinstance(result, list)
    assert "Python" in result
    assert "AWS" in result


def test_api_failure_triggers_fallback():
    with patch("backend.ai_engine._get_client", side_effect=Exception("API down")):
        result = parse_resume("Experienced with Python and Kubernetes.")
    assert isinstance(result, list)
    assert len(result) > 0
