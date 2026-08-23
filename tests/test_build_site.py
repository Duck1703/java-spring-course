"""Tests for tools/build_site.py — publication model assembly and safe embedding."""

import json
import unittest
from pathlib import Path

from tools.build_site import build_publication_model, embed_course_data

ROOT = Path(__file__).resolve().parents[1]


class EmbedTests(unittest.TestCase):
    def test_embeds_json_without_closing_script_injection(self):
        html = '<script id="course-data" type="application/json">{}</script>'
        model = {"text": "</script><script>alert(1)</script>"}
        built = embed_course_data(html, model)
        self.assertEqual(built.count('id="course-data"'), 1)
        self.assertNotIn("</script><script>alert", built)
        payload = built.split('id="course-data" type="application/json">', 1)[1].split("</script>", 1)[0]
        self.assertEqual(json.loads(payload)["text"], "</script><script>alert(1)</script>")

    def test_requires_one_data_marker(self):
        with self.assertRaisesRegex(ValueError, "exactly one course-data marker"):
            embed_course_data("<html></html>", {})


class PublicationModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = build_publication_model(
            catalog_path=ROOT / "course-catalog.json",
            lesson_index_path=ROOT / "content" / "lesson-index.json",
            lessons_dir=ROOT / "content" / "lessons",
            manifest_path=ROOT / "content" / "source-manifest.json",
            source_notes_dir=ROOT / "content" / "source-notes",
            built_at="2026-08-23T00:00:00Z",
        )

    def test_exactly_40_ordered_lessons(self):
        ids = [lesson["id"] for lesson in self.model["lessons"]]
        expected = [f"day-{n:02d}" for n in range(1, 39)] + ["day-39-64", "day-65-66"]
        self.assertEqual(ids, expected)

    def test_units_1_to_15(self):
        numbers = [unit["number"] for unit in self.model["units"]]
        self.assertEqual(numbers, list(range(1, 16)))

    def test_group_counts_12_24_4(self):
        counts = {"java": 0, "spring": 0, "completion": 0}
        for lesson in self.model["lessons"]:
            counts[lesson["group"]] += 1
        self.assertEqual(counts, {"java": 12, "spring": 24, "completion": 4})

    def test_references_reduced_to_metadata_only(self):
        for lesson in self.model["lessons"]:
            for ref in lesson.get("references", []):
                allowed = {
                    "id", "type", "resourceId", "citationId",
                    "url", "label", "checkStatus", "readStatus",
                    "pageTitle", "limitation",
                }
                extra = set(ref) - allowed
                self.assertEqual(extra, set(), f"unexpected ref keys {extra}")
                if ref["type"] == "external":
                    # every embedded reference must carry resolved metadata
                    self.assertIn("url", ref)
                    self.assertIn("label", ref)

    def test_no_source_note_body_embedded(self):
        raw = json.dumps(self.model, ensure_ascii=False)
        # facts corpus is never published; only lesson-authored content is
        self.assertNotIn('"facts"', raw)
        self.assertNotIn("relevantHeadings", raw)
        self.assertNotIn("fallbackEvidence", raw)


if __name__ == "__main__":
    unittest.main()
