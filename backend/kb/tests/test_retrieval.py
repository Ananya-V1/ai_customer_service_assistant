from unittest.mock import patch

from django.test import TestCase

from kb.models import Document, DocumentChunk, KnowledgeBase
from kb.services.retrieval import retrieve


def _vec(x, y):
    # 768-dim vector that only uses the first two dimensions
    return [x, y] + [0.0] * 766


class RetrieveThresholdTests(TestCase):
    def setUp(self):
        kb = KnowledgeBase.objects.create(name="Returns")
        # a path string avoids writing a real file into MEDIA_ROOT
        doc = Document.objects.create(knowledge_base=kb, file="documents/policy.pdf")
        # Question vector will be (1, 0). Cosine distances:
        #   (1, 0)   -> 0.0   (identical)
        #   (1, 1)   -> ~0.29 (45 degrees)
        #   (0, 1)   -> 1.0   (unrelated)
        for index, vec in enumerate([_vec(1, 0), _vec(1, 1), _vec(0, 1)]):
            DocumentChunk.objects.create(
                document=doc, knowledge_base=kb, chunk_index=index, text=f"chunk {index}", embedding=vec
            )

    @patch("kb.services.retrieval.ollama_client.embed", return_value=_vec(1, 0))
    def test_drops_chunks_beyond_threshold(self, _embed):
        chunks = retrieve("question", top_k=5, max_distance=0.5)
        self.assertEqual([c.text for c in chunks], ["chunk 0", "chunk 1"])

    @patch("kb.services.retrieval.ollama_client.embed", return_value=_vec(0, -1))
    def test_returns_empty_when_nothing_is_close(self, _embed):
        self.assertEqual(retrieve("question", top_k=5, max_distance=0.5), [])
