from django.db import transaction
from pypdf import PdfReader

from . import ollama_client
from .chunking import chunk_text


def extract_text(file_field):
    """Return a list of per-page text strings from an uploaded PDF."""
    file_field.seek(0)
    reader = PdfReader(file_field)
    return [page.extract_text() or "" for page in reader.pages]


def ingest_document(document):
    """Extract, chunk, embed, and store chunks for a Document. Synchronous."""
    from .. import models

    document.status = models.Document.STATUS_PROCESSING
    document.save(update_fields=["status"])

    try:
        pages = extract_text(document.file)
        full_text = "\n\n".join(pages)
        chunks = chunk_text(full_text)

        chunk_rows = []
        for index, chunk in enumerate(chunks):
            embedding = ollama_client.embed(chunk)
            chunk_rows.append(
                models.DocumentChunk(
                    document=document,
                    knowledge_base=document.knowledge_base,
                    chunk_index=index,
                    text=chunk,
                    embedding=embedding,
                )
            )

        with transaction.atomic():
            models.DocumentChunk.objects.filter(document=document).delete()
            models.DocumentChunk.objects.bulk_create(chunk_rows)
            document.page_count = len(pages)
            document.status = models.Document.STATUS_READY
            document.error_message = ""
            document.save(update_fields=["page_count", "status", "error_message"])
    except Exception as exc:
        document.status = models.Document.STATUS_FAILED
        document.error_message = str(exc)
        document.save(update_fields=["status", "error_message"])
        raise
