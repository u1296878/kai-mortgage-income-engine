import base64

from app.config import settings
from app.exceptions import ModelExtractionFailed


class AnthropicBackend:
    def __init__(
        self,
        client=None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.model = model or settings.anthropic_model
        self.client = client or _anthropic_client(api_key or settings.anthropic_api_key)

    def complete_json(
        self,
        prompt: str,
        schema: dict,
        images: list[bytes] | None = None,
    ) -> dict:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0,
                tools=[_tool_schema(schema)],
                tool_choice={"type": "tool", "name": "extract_fields"},
                messages=[{"role": "user", "content": _content(prompt, images or [])}],
            )
            return _tool_input(response)
        except ModelExtractionFailed:
            raise
        except Exception as error:
            raise ModelExtractionFailed("Anthropic request failed") from error


def _anthropic_client(api_key: str | None):
    if not api_key:
        raise ModelExtractionFailed("Anthropic API key is not configured")
    try:
        from anthropic import Anthropic
    except ImportError as error:
        raise ModelExtractionFailed("Anthropic SDK is not installed") from error
    return Anthropic(api_key=api_key)


def _tool_schema(schema: dict) -> dict:
    return {
        "name": "extract_fields",
        "description": "Extract income document fields as structured JSON.",
        "input_schema": schema,
    }


def _content(prompt: str, images: list[bytes]) -> list[dict]:
    image_blocks = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": base64.b64encode(image).decode("ascii"),
            },
        }
        for image in images
    ]
    return [*image_blocks, {"type": "text", "text": prompt}]


def _tool_input(response) -> dict:
    for item in _value(response, "content") or []:
        if _value(item, "type") == "tool_use" and _value(item, "name") == "extract_fields":
            payload = _value(item, "input")
            if isinstance(payload, dict):
                return payload
    raise ModelExtractionFailed("Anthropic response did not include extraction JSON")


def _value(item, name: str):
    if isinstance(item, dict):
        return item.get(name)
    return getattr(item, name, None)
