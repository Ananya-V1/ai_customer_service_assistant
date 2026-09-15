from pydantic import ValidationError

from ..services import ollama_client
from ..services.ollama_client import OllamaError


def call_structured(messages, schema_cls, max_retries=1):
    """Call Ollama in JSON mode and validate the result against a Pydantic schema.

    Retries once (by default) with an explicit correction message if the
    model returns invalid JSON or JSON that doesn't match the schema.
    Raises the last error if every attempt fails.
    """
    attempt_messages = list(messages)
    last_error = None

    for _ in range(max_retries + 1):
        try:
            raw = ollama_client.chat_json(attempt_messages)
            return schema_cls.model_validate(raw)
        except (OllamaError, ValidationError) as exc:
            last_error = exc
            attempt_messages = attempt_messages + [
                {
                    "role": "user",
                    "content": (
                        f"Your previous response was invalid ({exc}). "
                        "Respond again with ONLY valid JSON matching the requested schema."
                    ),
                }
            ]

    raise last_error
