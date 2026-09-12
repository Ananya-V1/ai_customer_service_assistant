from django.conf import settings


def chunk_text(text, chunk_size=None, overlap=None):
    """Split text into overlapping word-count windows.

    Returns a list of chunk strings. Empty/whitespace-only input returns [].
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE_WORDS
    overlap = overlap if overlap is not None else settings.CHUNK_OVERLAP_WORDS

    words = text.split()
    if not words:
        return []

    step = chunk_size - overlap
    if step <= 0:
        raise ValueError("chunk_size must be greater than overlap")

    chunks = []
    start = 0
    while start < len(words):
        window = words[start : start + chunk_size]
        chunks.append(" ".join(window))
        if start + chunk_size >= len(words):
            break
        start += step
    return chunks
