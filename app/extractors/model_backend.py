import json
from typing import Protocol

import httpx

from app.config import settings
from app.exceptions import ModelExtractionFailed


class ModelBackend(Protocol):
    def complete_json(
        self,
        prompt: str,
        schema: dict,
        images: list[bytes] | None = None,
    ) -> dict:
        """Return model output parsed as JSON."""


class OllamaBackend:
    def __init__(
        self,
        url: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        num_ctx: int | None = None,
        num_gpu: int | None = None,
    ) -> None:
        self.url = (url or settings.ollama_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.temperature = settings.ollama_temperature if temperature is None else temperature
        self.num_ctx = settings.ollama_num_ctx if num_ctx is None else num_ctx
        self.num_gpu = settings.ollama_num_gpu if num_gpu is None else num_gpu

    def complete_json(
        self,
        prompt: str,
        schema: dict,
        images: list[bytes] | None = None,
    ) -> dict:
        options = {"temperature": self.temperature, "num_ctx": self.num_ctx}
        if self.num_gpu is not None:
            options["num_gpu"] = self.num_gpu
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": schema,
            "stream": False,
            "options": options,
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
