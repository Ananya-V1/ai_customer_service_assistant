import json

import requests
from django.conf import settings


class OllamaError(RuntimeError):
    pass


def embed(text):
    url = f"{settings.OLLAMA_BASE_URL}/api/embeddings"
    resp = requests.post(
        url,
        json={"model": settings.OLLAMA_EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    embedding = data.get("embedding")
    if not embedding:
        raise OllamaError(f"Ollama returned no embedding: {data}")
    return embedding


def chat(messages):
    url = f"{settings.OLLAMA_BASE_URL}/api/chat"
    resp = requests.post(
        url,
        json={"model": settings.OLLAMA_CHAT_MODEL, "messages": messages, "stream": False},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    message = data.get("message", {})
    content = message.get("content")
    if not content:
        raise OllamaError(f"Ollama returned no chat content: {data}")
    return content


def chat_json(messages):
    """Like chat(), but requests JSON-mode output and returns the parsed dict.

    No retry or schema validation here — that's the caller's job (see
    kb.agents.structured.call_structured), keeping this client a thin wrapper.
    """
    url = f"{settings.OLLAMA_BASE_URL}/api/chat"
    resp = requests.post(
        url,
        json={
            "model": settings.OLLAMA_CHAT_MODEL,
            "messages": messages,
            "stream": False,
            "format": "json",
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    message = data.get("message", {})
    content = message.get("content")
    if not content:
        raise OllamaError(f"Ollama returned no chat content: {data}")
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise OllamaError(f"Ollama returned invalid JSON: {content!r}") from exc
