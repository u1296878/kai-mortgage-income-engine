from types import SimpleNamespace

import pytest

from app.exceptions import ModelExtractionFailed
from app.extractors.model_backend import OllamaBackend


class FakeResponse:
    def __init__(self, body: dict) -> None:
        self.body = body

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.body


def test_ollama_backend_parses_json_response(monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append(SimpleNamespace(url=url, json=json, timeout=timeout))
        return FakeResponse({"response": '{"fields": {"agi": {"value": 79000}}}'})

    monkeypatch.setattr("app.extractors.model_backend.httpx.post", fake_post)
    backend = OllamaBackend(url="http://localhost:11434", model="test-model", temperature=0)

    result = backend.complete_json("prompt", {"type": "object"})

    assert result["fields"]["agi"]["value"] == 79000
    assert calls[0].json["options"]["temperature"] == 0
    assert calls[0].json["options"]["num_ctx"] == 4096
    assert calls[0].json["model"] == "test-model"


def test_ollama_backend_raises_on_malformed_model_json(monkeypatch):
    monkeypatch.setattr(
        "app.extractors.model_backend.httpx.post",
        lambda url, json, timeout: FakeResponse({"response": "{not json"}),
    )
    backend = OllamaBackend(url="http://localhost:11434", model="test-model")

    with pytest.raises(ModelExtractionFailed):
        backend.complete_json("prompt", {"type": "object"})
