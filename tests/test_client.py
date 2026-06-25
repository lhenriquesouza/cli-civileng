"""Tests for llm/client.py."""
import json
import pytest
from cli_civileng.llm.client import _extract_json_from_response


class TestExtractJsonFromResponse:
    def test_plain_json(self):
        content = '{"name": "test", "rules": []}'
        result = _extract_json_from_response(content)
        assert "test" in result

    def test_json_in_fence(self):
        content = '```json\n{"name": "test"}\n```'
        result = _extract_json_from_response(content)
        assert result == '{"name": "test"}'

    def test_json_in_generic_fence(self):
        content = '```\n{"name": "test"}\n```'
        result = _extract_json_from_response(content)
        assert result == '{"name": "test"}'

    def test_no_fence(self):
        content = '{"x": 1}'
        result = _extract_json_from_response(content)
        assert result == '{"x": 1}'

    def test_json_fence_preferred_over_generic(self):
        content = '```json\n{"type": "json"}\n```\n```\n{"type": "generic"}\n```'
        result = _extract_json_from_response(content)
        assert "json" in result
        assert "generic" not in result

    def test_response_with_text_before_json(self):
        content = 'Here is the result:\n```json\n{"ok": true}\n```'
        result = _extract_json_from_response(content)
        assert result == '{"ok": true}'


class TestExtractRulesFromTextErrorHandling:
    """Test that extract_rules_from_text handles bad LLM responses gracefully."""

    def test_raises_value_error_on_bad_json(self, monkeypatch):
        """If LLM returns non-JSON, ValueError should be raised."""
        from cli_civileng.llm import client as llm_client

        # Mock get_client
        class FakeChoice:
            class Message:
                content = "Not valid JSON at all!!!"
            message = Message()

        class FakeResponse:
            choices = [FakeChoice()]

        class FakeClient:
            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        return FakeResponse()

        def fake_get_client(*args, **kwargs):
            return (FakeClient(), "test-model")

        monkeypatch.setattr(llm_client, "get_client", fake_get_client)

        with pytest.raises(ValueError, match="invalid JSON"):
            llm_client.extract_rules_from_text("some text")
