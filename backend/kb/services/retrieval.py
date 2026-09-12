from django.conf import settings
from pgvector.django import CosineDistance

from . import ollama_client

SYSTEM_PROMPT = (
    "You are a customer support assistant. Answer the user's question using "
    "ONLY the information in the provided context. Cite which knowledge base "
    "the answer comes from. If the context does not contain the answer, say "
    "you don't have information about that instead of guessing."
)

NO_INFO_ANSWER = "I don't have information about that."


def retrieve(question, top_k=None, max_distance=None):
    """Embed the question and return the closest DocumentChunks across all KBs."""
    from ..models import DocumentChunk

    top_k = top_k or settings.RAG_TOP_K
    max_distance = max_distance if max_distance is not None else settings.RAG_MAX_DISTANCE
    query_embedding = ollama_client.embed(question) # embed question into 768-number vector

    chunks = list(
        DocumentChunk.objects.annotate(distance=CosineDistance("embedding", query_embedding)) # computes distance using CosineDistance and
        # adds computed distance column to each row in the SQL query
        .order_by("distance") # sorts smallest to largest
        .select_related("document", "knowledge_base")[:top_k]
    )

    if not chunks or chunks[0].distance > max_distance:
        return []
    return chunks


def _build_context_block(chunks):
    parts = []
    for chunk in chunks:
        label = f"[{chunk.knowledge_base.name} / {chunk.document.title}]"
        parts.append(f"{label}\n{chunk.text}")
    return "\n\n---\n\n".join(parts)


def _chunk_to_source(chunk):
    # converts DocumentChunk and distance into JSON dict
    return {
        "knowledge_base": chunk.knowledge_base.name,
        "document": chunk.document.title,
        "document_id": chunk.document_id,
        "chunk_id": chunk.id,
        "distance": round(float(chunk.distance), 4),
    }


def answer_question(question, conversation=None, top_k=None, max_distance=None):
    """Run retrieval + chat and return (answer_text, sources)."""
    chunks = retrieve(question, top_k=top_k, max_distance=max_distance)

    if not chunks:
        return NO_INFO_ANSWER, []

    context_block = _build_context_block(chunks)

    messages = [{"role": "system", "content": f"{SYSTEM_PROMPT}\n\nContext:\n{context_block}"}]

    if conversation is not None:
        history = list(
            conversation.messages.order_by("-created_at")[: settings.RAG_HISTORY_TURNS]
        )
        for message in reversed(history):
            messages.append({"role": message.role, "content": message.content})

    messages.append({"role": "user", "content": question})

    answer = ollama_client.chat(messages)
    sources = [_chunk_to_source(chunk) for chunk in chunks]
    return answer, sources
