import json
from typing import Protocol

import httpx

from app.config import settings
from app.exceptions import ModelExtractionFailed


class ModelBackend(Protocol):
    def complete_json(self, prompt: str, schema: dict) -> dict:
        """Return model output parsed as JSON."""


class OllamaBackend:
    def __init__(
        self,
        url: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        self.url = (url or settings.ollama_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.temperature = settings.ollama_temperature if temperature is None else temperature

    def complete_json(self, prompt: str, schema: dict) -> dict:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": schema,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        try:
            response = httpx.post(f"{self.url}/api/generate", json=payload, timeout=120)
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPError as error:
            raise ModelExtractionFailed("Ollama request failed") from error
        except ValueError as error:
            raise ModelExtractionFailed("Ollama returned invalid response JSON") from error
        return _parse_model_json(body)


def _parse_model_json(body: dict) -> dict:
    raw = body.get("response", body)
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        raise ModelExtractionFailed("Model response did not contain JSON text")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ModelExtractionFailed("Model returned malformed JSON") from error
    if not isinstance(parsed, dict):
        raise ModelExtractionFailed("Model JSON must be an object")
    return parsed
