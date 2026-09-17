"""Tests for tools/build_site.py — publication model assembly and safe embedding."""

import json
import unittest
from pathlib import Path

from tools.build_site import build_publication_model, embed_course_data

ROOT = Path(__file__).resolve().parents[1]

BUILD_KWARGS = dict(
    catalog_path=ROOT / "course-catalog.json",
    lesson_index_path=ROOT / "content" / "lesson-index.json",
    lessons_dir=ROOT / "content" / "lessons",
    manifest_path=ROOT / "content" / "source-manifest.json",
    source_notes_dir=ROOT / "content" / "source-notes",
    built_at="2026-08-23T00:00:00Z",
    project_path=ROOT / "content" / "spendwise-project.json",
)


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
            **BUILD_KWARGS,
            guided_build_path=ROOT / "content" / "spendwise-guided-build.json",
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
                    "pageTitle", "limitation", "description",
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

    def test_project_data_layer_embedded(self):
        project = self.model["project"]
        self.assertEqual(len(project["releases"]), 10)
        self.assertEqual(len(project["features"]), 31)
        self.assertEqual(len(project["buildTasks"]), 64)
        self.assertEqual(project["product"]["id"], "spendwise")

    def test_project_lesson_map_keys_are_published_lessons(self):
        lesson_ids = {lesson["id"] for lesson in self.model["lessons"]}
        for lesson_id in self.model["project"]["lessonMap"]:
            self.assertIn(lesson_id, lesson_ids)

    def test_project_data_unchanged_by_guided_build_embedding(self):
        # Embedding guidedBuild must not mutate/duplicate/alter the canonical
        # project layer at all — same assertions as a build with no guided
        # artifact would produce.
        without_guided = build_publication_model(**BUILD_KWARGS)
        self.assertEqual(self.model["project"], without_guided["project"])


class GuidedBuildEmbeddingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guided_path = ROOT / "content" / "spendwise-guided-build.json"
        cls.model = build_publication_model(
            **BUILD_KWARGS, guided_build_path=cls.guided_path,
        )

    def test_guided_build_embedded_and_matches_authored_json(self):
        with self.guided_path.open(encoding="utf-8") as fh:
            authored = json.load(fh)
        self.assertEqual(self.model["guidedBuild"], authored)

    def test_guided_build_skeleton_shape(self):
        guided = self.model["guidedBuild"]
        self.assertEqual(len(guided["guidedReleases"]), 10)
        self.assertEqual(guided["guidedSessions"], [])
        self.assertEqual(guided["guidedSteps"], [])
        self.assertEqual(guided["guidedCheckpoints"], [])

    def test_absent_guided_build_path_omits_key(self):
        model = build_publication_model(**BUILD_KWARGS)
        self.assertNotIn("guidedBuild", model)

    def test_malformed_guided_build_fails_the_build(self):
        import tempfile
        bad = {"schemaVersion": 1, "guidedCourse": {}, "guidedReleases": [],
               "guidedSessions": [], "guidedSteps": [], "guidedCheckpoints": [],
               "unexpectedKey": True}
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = Path(tmp) / "bad-guided-build.json"
            bad_path.write_text(json.dumps(bad), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "failed validation"):
                build_publication_model(**BUILD_KWARGS, guided_build_path=bad_path)

    def test_unknown_cross_source_lesson_reference_fails_the_build(self):
        import tempfile
        guided = json.loads(self.guided_path.read_text(encoding="utf-8"))
        guided["guidedReleases"] = [
            {"releaseId": r["releaseId"], "authoringStatus": "authored"}
            if r["releaseId"] == "v0-1" else r
            for r in guided["guidedReleases"]
        ]
        guided["guidedSessions"] = [{
            "id": "session-x", "releaseId": "v0-1", "buildTaskId": "task-money-vo",
            "order": 1, "title": "X", "goal": "X",
        }]
        guided["guidedSteps"] = [{
            "id": "gstep-x", "sessionId": "session-x", "order": 1, "buildStepId": None,
            "type": "explanation", "title": "X", "goal": "X",
            "theoryBridge": [{"lessonId": "day-999-does-not-exist", "note": "x"}],
        }]
        guided["guidedCheckpoints"] = [{
            "id": "cp-x", "sessionId": "session-x", "expectedFiles": [],
            "understanding": ["x"], "whatYouBuilt": "x",
        }]
        with tempfile.TemporaryDirectory() as tmp:
            bad_path = Path(tmp) / "bad-lesson-ref.json"
            bad_path.write_text(json.dumps(guided), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not a known lesson"):
                build_publication_model(**BUILD_KWARGS, guided_build_path=bad_path)

    def test_exactly_one_course_data_marker_with_guided_build_present(self):
        template = (ROOT / "index.template.html").read_text(encoding="utf-8")
        built = embed_course_data(template, self.model)
        self.assertEqual(built.count('id="course-data"'), 1)

    def test_no_external_filesystem_dependency_on_reference_app(self):
        source = (ROOT / "tools" / "build_site.py").read_text(encoding="utf-8")
        self.assertNotIn("D:\\spendwise", source)
        self.assertNotIn("D:/spendwise", source)


if __name__ == "__main__":
    unittest.main()
