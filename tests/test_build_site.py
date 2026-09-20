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

    AUTHORED_RELEASE_IDS = {"v0-1", "v0-2", "v0-3", "v0-4", "v0-5", "v0-6", "v0-7", "v0-8"}

    def test_guided_build_v0_1_authored_shape(self):
        # V0.1-V0.8 are authored content now; the remaining 2 releases stay
        # planned with zero sessions until their own authoring work happens.
        guided = self.model["guidedBuild"]
        self.assertEqual(len(guided["guidedReleases"]), 10)
        status_by_release = {r["releaseId"]: r["authoringStatus"] for r in guided["guidedReleases"]}
        for release_id in self.AUTHORED_RELEASE_IDS:
            self.assertEqual(status_by_release[release_id], "authored", release_id)
        for release_id, status in status_by_release.items():
            if release_id not in self.AUTHORED_RELEASE_IDS:
                self.assertEqual(status, "planned", release_id)

        sessions = guided["guidedSessions"]
        steps = guided["guidedSteps"]
        checkpoints = guided["guidedCheckpoints"]
        self.assertTrue(sessions)
        self.assertTrue(steps)
        self.assertTrue(checkpoints)
        self.assertTrue(all(s["releaseId"] in self.AUTHORED_RELEASE_IDS for s in sessions))
        self.assertEqual(len(checkpoints), len(sessions))

    def test_guided_build_v0_1_covers_every_required_canonical_build_step(self):
        project = self.model["project"]
        guided = self.model["guidedBuild"]
        required_task_ids = {
            t["id"] for t in project["buildTasks"]
            if t.get("required") and t["releaseId"] in self.AUTHORED_RELEASE_IDS
        }
        covered_task_ids = {s["buildTaskId"] for s in guided["guidedSessions"]}
        # Coverage must be a superset of required tasks, not an exact match:
        # guided content is allowed to also cover an optional/deferred
        # canonical task (e.g. task-config-profiles in V0.3), and is allowed
        # to leave some uncovered (e.g. task-optimistic-locking in V0.5,
        # task-auth-hardening-review in V0.6, task-advanced-aggregation in
        # V0.7, task-async-import in V0.8, all required=false) —
        # matching tools/validate_guided_build.py's own completeness check,
        # which is a subset test (`required_tasks - covered_tasks`), not
        # equality.
        self.assertLessEqual(required_task_ids, covered_task_ids)

        steps_by_task = {}
        for build_step in project["buildSteps"]:
            steps_by_task.setdefault(build_step["taskId"], set()).add(build_step["id"])
        session_task_by_id = {s["id"]: s["buildTaskId"] for s in guided["guidedSessions"]}
        covered_build_steps_by_task = {}
        for step in guided["guidedSteps"]:
            build_step_id = step.get("buildStepId")
            if build_step_id is None:
                continue
            task_id = session_task_by_id[step["sessionId"]]
            covered_build_steps_by_task.setdefault(task_id, set()).add(build_step_id)
        for task_id in required_task_ids:
            self.assertEqual(steps_by_task.get(task_id, set()), covered_build_steps_by_task.get(task_id, set()), task_id)

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
