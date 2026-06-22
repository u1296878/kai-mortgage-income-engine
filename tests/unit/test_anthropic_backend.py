from types import SimpleNamespace

import pytest

from app.exceptions import ModelExtractionFailed
from app.extractors.anthropic_backend import AnthropicBackend


class FakeMessages:
    def __init__(self, response=None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def test_anthropic_backend_sends_images_and_parses_tool_json():
    response = SimpleNamespace(
        content=[
            SimpleNamespace(
                type="tool_use",
                name="extract_fields",
                input={"fields": {"agi": {"value": 79000}}},
            )
        ]
    )
    messages = FakeMessages(response=response)
    backend = AnthropicBackend(
        client=SimpleNamespace(messages=messages),
        model="claude-test",
    )

    result = backend.complete_json("prompt", {"type": "object"}, images=[b"png"])

    call = messages.calls[0]
    content = call["messages"][0]["content"]
    assert result["fields"]["agi"]["value"] == 79000
    assert call["model"] == "claude-test"
    assert call["tools"][0]["input_schema"] == {"type": "object"}
    assert call["tool_choice"] == {"type": "tool", "name": "extract_fields"}
    assert content[0]["type"] == "image"
    assert content[0]["source"]["data"] == "cG5n"
    assert content[1] == {"type": "text", "text": "prompt"}


def test_anthropic_backend_maps_errors_to_model_extraction_failed():
    messages = FakeMessages(error=RuntimeError("network down"))
    backend = AnthropicBackend(client=SimpleNamespace(messages=messages), model="claude-test")

    with pytest.raises(ModelExtractionFailed):
        backend.complete_json("prompt", {"type": "object"}, images=[b"png"])
