import unittest
import importlib
from unittest.mock import MagicMock, patch
import os
import sys


class TestEntityUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Patch heavy dependencies before importing
        modules = {
            "torch": MagicMock(),
            "transformers": MagicMock(),
            "opendiscourse.vector_database": MagicMock(),
            "psycopg2": MagicMock(),
            "psycopg2.extras": MagicMock(),
            "dotenv": MagicMock(),
            "numpy": MagicMock(),
        }
        with patch.dict("sys.modules", modules):
            # Import after patching dependencies
            from opendiscourse import entity_utils

            cls.entity_extractor = entity_utils.EntityExtractor()

    def test_deduplicate_entities(self):
        entities = [
            {"text": "Senate", "type": "GOVERNMENT_BODY"},
            {"text": "senate", "type": "GOVERNMENT_BODY"},
            {"text": "House", "type": "GOVERNMENT_BODY"},
        ]
        deduped = self.entity_extractor.deduplicate_entities(entities)
        self.assertEqual(len(deduped), 2)

    def test_infer_relationships(self):
        entities = [
            {"id": 1, "text": "Alice", "type": "PERSON"},
            {"id": 2, "text": "Committee", "type": "GOVERNMENT_BODY"},
        ]
        text = "Alice of Committee"
        rels = self.entity_extractor.infer_relationships(entities, text)
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0]["relationship_type"], "MEMBER_OF")

    def test_extract_declarations(self):
        entities = [{"text": "Committee", "type": "GOVERNMENT_BODY"}]
        text = "The Committee shall convene next week."
        decls = self.entity_extractor.extract_declarations(entities, text)
        self.assertTrue(any("shall" in d["declaration_text"].lower() for d in decls))


if __name__ == "__main__":
    unittest.main()
