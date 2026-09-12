from django.test import SimpleTestCase

from kb.services.chunking import chunk_text


class ChunkTextTests(SimpleTestCase):
    def test_empty_input_returns_no_chunks(self):
        self.assertEqual(chunk_text(""), [])
        self.assertEqual(chunk_text("   "), [])

    def test_text_shorter_than_chunk_size_returns_single_chunk(self):
        text = " ".join(f"word{i}" for i in range(10))
        chunks = chunk_text(text, chunk_size=1000, overlap=150)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)

    def test_splits_into_windows_with_overlap(self):
        words = [f"w{i}" for i in range(2500)]
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=1000, overlap=150)

        # step = 850, windows start at 0, 850, 1700
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].split()[0], "w0")
        self.assertEqual(chunks[0].split()[-1], "w999")
        self.assertEqual(chunks[1].split()[0], "w850")
        self.assertEqual(chunks[2].split()[0], "w1700")
        self.assertEqual(chunks[2].split()[-1], "w2499")

    def test_overlap_words_appear_in_consecutive_chunks(self):
        words = [f"w{i}" for i in range(1200)]
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=1000, overlap=150)

        first_words = chunks[0].split()
        second_words = chunks[1].split()
        overlap_words = set(first_words[-150:])
        self.assertTrue(overlap_words.issubset(set(second_words)))

    def test_invalid_overlap_raises(self):
        with self.assertRaises(ValueError):
            chunk_text("a b c", chunk_size=100, overlap=100)
