"""Tests for tools/validate_guided_build.py.

Fixtures build small, self-contained canonical + guided dicts in memory (mirroring the
fixture-builder-with-**overrides pattern used by tests/test_validate_project.py) — the
production content/spendwise-guided-build.json is never written to or read by these tests;
"authored" content only ever exists as a synthetic in-memory fixture.
"""

from __future__ import annotations

import unittest

from tools.validate_project import EXPECTED_RELEASES
from tools.validate_guided_build import validate_guided_build

CANONICAL_OUT_OF_SCOPE = [
    "full double-entry accounting", "general ledger", "tax", "stock trading",
    "investment portfolio", "cryptocurrency", "bank synchronization", "Open Banking",
    "OCR receipt", "family/shared finance", "financial advisor", "loan system",
    "payment gateway", "microservices", "Kafka", "Kubernetes", "mobile app",
    "blockchain", "complex accounting reconciliation",
    "support for every bank file format", "full multi-currency accounting engine",
]


# ---------------------------------------------------------------------------
# Canonical-side fixtures (the "already-validated project dict" validate_guided_build
# takes as its second argument — small and synthetic, not content/spendwise-project.json).
# ---------------------------------------------------------------------------

def _release(rid, version, order, build_task_ids, **overrides):
    release = {
        "id": rid, "version": version, "title": f"Release {version}", "order": order,
        "status": "planned", "problem": "A problem.", "goal": "A goal.",
        "featureIds": ["feat-x"], "learningDependencies": [],
        "acceptanceCriteria": ["Something works"], "buildTaskIds": build_task_ids,
    }
    release.update(overrides)
    return release


def _releases(v01_task_ids):
    return [
        _release(rid, version, index + 1, v01_task_ids if rid == "v0-1" else [])
        for index, (rid, version) in enumerate(EXPECTED_RELEASES)
    ]


def _build_task(tid="task-x", **overrides):
    task = {
        "id": tid, "title": "Example build task", "releaseId": "v0-1",
        "featureIds": ["feat-x"], "problem": "A problem.", "goal": "A goal.",
        "constraints": [], "acceptanceCriteria": ["Compiles"],
        "relevantLessonIds": ["day-01"], "required": True,
    }
    task.update(overrides)
    return task


def _build_step(sid, task_id, order, **overrides):
    step = {
        "id": sid, "taskId": task_id, "order": order, "title": "A build step",
        "intent": "Because it matters.", "knowledgePrereqLessonIds": ["day-01"],
        "artifactPrereqTaskIds": [], "filesTouched": ["src/main/java/com/spendwise/X.java"],
        "doneWhen": "XTest passes.", "verifyCommand": "./mvnw -Dtest=XTest test",
        "architectureRules": ["R1"],
    }
    step.update(overrides)
    return step


def _project(build_tasks, build_steps, v01_task_ids):
    return {
        "schemaVersion": 1,
        "product": {
            "id": "spendwise", "name": "Spendwise", "type": "Personal Expense & Budget Tracker",
            "vision": "Track spending clearly.", "outOfScope": list(CANONICAL_OUT_OF_SCOPE),
        },
        "releases": _releases(v01_task_ids),
        "features": [{
            "id": "feat-x", "name": "Feature X", "description": "A feature.",
            "domainEntities": ["X"], "introducedInReleaseId": "v0-1",
        }],
        "buildTasks": build_tasks,
        "buildSteps": build_steps,
        "milestones": [],
        "architectureStages": [],
        "lessonMap": {"day-01": {
            "applicationType": "direct", "releaseId": "v0-1", "featureIds": ["feat-x"],
            "buildTaskIds": [t["id"] for t in build_tasks],
            "projectProblem": "A problem.", "context": "Some context.",
            "application": "Some application.",
        }},
    }


def _minimal_project():
    """v0-1 has one required task-x with two ordered buildSteps."""
    return _project(
        build_tasks=[_build_task(tid="task-x", required=True)],
        build_steps=[
            _build_step("step-x-01", "task-x", 1),
            _build_step("step-x-02", "task-x", 2),
        ],
        v01_task_ids=["task-x"],
    )


def _two_task_project():
    """v0-1 has two required tasks, task-x and task-y, each with one buildStep."""
    return _project(
        build_tasks=[
            _build_task(tid="task-x", required=True),
            _build_task(tid="task-y", required=True),
        ],
        build_steps=[
            _build_step("step-x-01", "task-x", 1),
            _build_step("step-y-01", "task-y", 1),
        ],
        v01_task_ids=["task-x", "task-y"],
    )


# ---------------------------------------------------------------------------
# Guided-side fixtures.
# ---------------------------------------------------------------------------

def _guided_course(**overrides):
    course = {
        "id": "spendwise-guided-build", "title": "Spendwise Guided Rebuild",
        "workspaceExample": "D:\\spendwise-learning",
        "referenceWorkspaceExample": "D:\\spendwise",
    }
    course.update(overrides)
    return course


def _guided_releases(authored=frozenset()):
    return [
        {"releaseId": rid, "authoringStatus": "authored" if rid in authored else "planned"}
        for rid, _version in EXPECTED_RELEASES
    ]


def _session(sid="session-x", release_id="v0-1", task_id="task-x", order=1, **overrides):
    session = {
        "id": sid, "releaseId": release_id, "buildTaskId": task_id, "order": order,
        "title": "Xay X", "goal": "Hoc cach xay X.",
    }
    session.update(overrides)
    return session


def _step(sid, session_id="session-x", order=1, build_step_id="step-x-01",
          type_="code-with-me", **overrides):
    step = {
        "id": sid, "sessionId": session_id, "order": order, "buildStepId": build_step_id,
        "type": type_, "title": "Tao X", "goal": "Tao X dau tien.",
    }
    step.update(overrides)
    return step


def _checkpoint(cid="checkpoint-x", session_id="session-x", **overrides):
    checkpoint = {
        "id": cid, "sessionId": session_id,
        "expectedFiles": ["src/main/java/com/spendwise/X.java"],
        "understanding": ["Hieu vi sao X quan trong."],
        "whatYouBuilt": "Ban vua tao X.",
    }
    checkpoint.update(overrides)
    return checkpoint


def _guided(**overrides):
    guided = {
        "schemaVersion": 1,
        "guidedCourse": _guided_course(),
        "guidedReleases": _guided_releases(),
        "guidedSessions": [],
        "guidedSteps": [],
        "guidedCheckpoints": [],
    }
    guided.update(overrides)
    return guided


def _complete_authored_guided():
    """One session covering task-x, two steps covering step-x-01/02, one checkpoint."""
    return _guided(
        guidedReleases=_guided_releases(authored={"v0-1"}),
        guidedSessions=[_session()],
        guidedSteps=[
            _step("gstep-x-01", order=1, build_step_id="step-x-01"),
            _step("gstep-x-02", order=2, build_step_id="step-x-02"),
        ],
        guidedCheckpoints=[_checkpoint()],
    )


# ---------------------------------------------------------------------------
# Tests.
# ---------------------------------------------------------------------------

class GuidedBuildValidatorTests(unittest.TestCase):

    def test_01_production_skeleton_passes(self):
        self.assertEqual(validate_guided_build(_guided(), _minimal_project()), [])

    def test_02_unknown_top_level_key_fails(self):
        guided = _guided(extra="nope")
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("unexpected key" in e for e in errors))

    def test_03_unknown_nested_key_fails(self):
        guided = _guided(guidedCourse=_guided_course(extra="nope"))
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("unexpected key" in e for e in errors))

    def test_04_invalid_authoring_status_fails(self):
        releases = _guided_releases()
        releases[0]["authoringStatus"] = "bogus"
        guided = _guided(guidedReleases=releases)
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("authoringStatus must be one of" in e for e in errors))

    def test_05_invalid_guided_step_type_fails(self):
        guided = _complete_authored_guided()
        guided["guidedSteps"][0]["type"] = "bogus"
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("type must be one of" in e for e in errors))

    def test_06_duplicate_guided_ids_fails(self):
        guided = _guided(guidedSessions=[
            _session(sid="session-x", order=1),
            _session(sid="session-x", order=2),
        ])
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("duplicate id 'session-x'" in e for e in errors))

    def test_07_unknown_release_id_fails(self):
        guided = _guided(guidedSessions=[_session(release_id="v9-9")])
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("does not resolve to a guidedRelease" in e for e in errors))

    def test_08_unknown_build_task_id_fails(self):
        guided = _guided(guidedSessions=[_session(task_id="task-nonexistent")])
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("does not resolve to a canonical buildTask" in e for e in errors))

    def test_09_session_release_mismatches_task_release_fails(self):
        guided = _guided(guidedSessions=[_session(release_id="v0-2", task_id="task-x")])
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("belongs to release" in e for e in errors))

    def test_10_unknown_build_step_id_fails(self):
        guided = _complete_authored_guided()
        guided["guidedSteps"][0]["buildStepId"] = "step-nonexistent"
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("does not resolve to a canonical buildStep" in e for e in errors))

    def test_11_build_step_belongs_to_different_task_fails(self):
        guided = _guided(
            guidedReleases=_guided_releases(authored={"v0-1"}),
            guidedSessions=[_session(task_id="task-x")],
            guidedSteps=[_step("gstep-x-01", build_step_id="step-y-01")],
            guidedCheckpoints=[_checkpoint()],
        )
        errors = validate_guided_build(guided, _two_task_project())
        self.assertTrue(any("not this step's session buildTask" in e for e in errors))

    def test_12_unknown_lesson_id_fails(self):
        guided = _complete_authored_guided()
        guided["guidedSteps"][0]["theoryBridge"] = [{"lessonId": "day-99", "note": "x"}]
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("is not a known lesson" in e for e in errors))

    def test_13_session_order_gap_fails(self):
        guided = _guided(
            guidedReleases=_guided_releases(authored={"v0-1"}),
            guidedSessions=[
                _session(sid="session-x1", order=1),
                _session(sid="session-x2", order=3),
            ],
        )
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("guidedSession order must be contiguous" in e for e in errors))

    def test_14_step_order_gap_fails(self):
        guided = _guided(
            guidedReleases=_guided_releases(authored={"v0-1"}),
            guidedSessions=[_session()],
            guidedSteps=[
                _step("gstep-x-01", order=1, build_step_id="step-x-01"),
                _step("gstep-x-02", order=3, build_step_id="step-x-02"),
            ],
        )
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("guidedStep order must be contiguous" in e for e in errors))

    def test_15_planned_release_containing_session_fails(self):
        guided = _guided(guidedSessions=[_session()])
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("planned and must have zero guidedSessions" in e for e in errors))

    def test_16_authored_release_with_no_sessions_fails(self):
        guided = _guided(guidedReleases=_guided_releases(authored={"v0-1"}))
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("requires at least one guidedSession" in e for e in errors))

    def test_17_authored_release_missing_required_build_task_coverage_fails(self):
        guided = _guided(
            guidedReleases=_guided_releases(authored={"v0-1"}),
            guidedSessions=[_session(task_id="task-x")],
            guidedSteps=[_step("gstep-x-01", build_step_id="step-x-01")],
            guidedCheckpoints=[_checkpoint()],
        )
        errors = validate_guided_build(guided, _two_task_project())
        self.assertTrue(any(
            "missing guidedSession coverage for required buildTask(s) ['task-y']" in e
            for e in errors
        ))

    def test_18_authored_release_missing_required_build_step_coverage_fails(self):
        guided = _guided(
            guidedReleases=_guided_releases(authored={"v0-1"}),
            guidedSessions=[_session()],
            guidedSteps=[_step("gstep-x-01", order=1, build_step_id="step-x-01")],
            guidedCheckpoints=[_checkpoint()],
        )
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any(
            "missing guidedStep coverage for buildStep(s) ['step-x-02']" in e for e in errors
        ))

    def test_19_complete_authored_release_synthetic_fixture_passes(self):
        self.assertEqual(
            validate_guided_build(_complete_authored_guided(), _minimal_project()), []
        )

    def test_20_one_build_task_mapped_to_multiple_sessions_passes(self):
        guided = _guided(
            guidedReleases=_guided_releases(authored={"v0-1"}),
            guidedSessions=[
                _session(sid="session-x1", order=1, task_id="task-x"),
                _session(sid="session-x2", order=2, task_id="task-x"),
            ],
            guidedSteps=[
                _step("gstep-x1-01", session_id="session-x1", order=1, build_step_id="step-x-01"),
                _step("gstep-x2-01", session_id="session-x2", order=1, build_step_id="step-x-02"),
            ],
            guidedCheckpoints=[
                _checkpoint(cid="checkpoint-x1", session_id="session-x1"),
                _checkpoint(cid="checkpoint-x2", session_id="session-x2"),
            ],
        )
        self.assertEqual(validate_guided_build(guided, _minimal_project()), [])

    def test_21_multiple_guided_steps_mapped_to_one_build_step_passes(self):
        guided = _guided(
            guidedReleases=_guided_releases(authored={"v0-1"}),
            guidedSessions=[_session()],
            guidedSteps=[
                _step("gstep-x-01a", order=1, build_step_id="step-x-01", type_="explanation"),
                _step("gstep-x-01b", order=2, build_step_id="step-x-01", type_="code-with-me"),
                _step("gstep-x-02", order=3, build_step_id="step-x-02"),
            ],
            guidedCheckpoints=[_checkpoint()],
        )
        self.assertEqual(validate_guided_build(guided, _minimal_project()), [])

    def test_22_null_build_step_pedagogical_step_passes(self):
        guided = _guided(
            guidedReleases=_guided_releases(authored={"v0-1"}),
            guidedSessions=[_session()],
            guidedSteps=[
                _step("gstep-x-00", order=1, build_step_id=None, type_="orientation"),
                _step("gstep-x-01", order=2, build_step_id="step-x-01"),
                _step("gstep-x-02", order=3, build_step_id="step-x-02"),
            ],
            guidedCheckpoints=[_checkpoint()],
        )
        self.assertEqual(validate_guided_build(guided, _minimal_project()), [])

    def test_23_your_turn_missing_learner_action_fails(self):
        guided = _complete_authored_guided()
        guided["guidedSteps"][0]["type"] = "your-turn"
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("requires learnerAction" in e for e in errors))

    def test_24_non_your_turn_with_learner_action_fails(self):
        guided = _complete_authored_guided()
        guided["guidedSteps"][0]["learnerAction"] = {"goal": "Do it"}
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("only allowed when type=your-turn" in e for e in errors))

    def test_25_bad_run_object_fails(self):
        guided = _complete_authored_guided()
        guided["guidedSteps"][0]["run"] = {"cwd": "D:\\spendwise-learning"}
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("command must be a nonempty string" in e for e in errors))

    def test_26_bad_common_errors_object_fails(self):
        guided = _complete_authored_guided()
        guided["guidedSteps"][0]["commonErrors"] = [{"symptom": "It fails"}]
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("likelyCause must be a nonempty string" in e for e in errors))

    def test_27_duplicate_checkpoint_per_session_fails(self):
        guided = _complete_authored_guided()
        guided["guidedCheckpoints"].append(_checkpoint(cid="checkpoint-x2"))
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("expected exactly 1" in e for e in errors))

    def test_28_authored_session_without_checkpoint_fails(self):
        guided = _complete_authored_guided()
        guided["guidedCheckpoints"] = []
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("authored session has no guidedCheckpoint" in e for e in errors))

    def test_29_teaching_fields_pass(self):
        guided = _complete_authored_guided()
        guided["guidedSessions"][0].update(projectNow="Co X.", sessionAdds="Them Y.")
        guided["guidedSteps"][0]["codeBlocks"] = [{"language": "java", "code": "class X {}", "explanation": "Vi sao X."}]
        guided["guidedSteps"][0]["selfCheck"] = [{"question": "Vi sao?", "answer": "Vi vay."}]
        self.assertEqual(validate_guided_build(guided, _minimal_project()), [])

    def test_30_bad_self_check_fails(self):
        guided = _complete_authored_guided()
        guided["guidedSteps"][0]["selfCheck"] = [{"question": "Vi sao?"}]
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("answer must be a nonempty string" in e for e in errors))
        guided["guidedSteps"][0]["selfCheck"] = []
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("1-4 entries" in e for e in errors))

    def test_31_empty_session_continuity_fails(self):
        guided = _complete_authored_guided()
        guided["guidedSessions"][0]["projectNow"] = ""
        errors = validate_guided_build(guided, _minimal_project())
        self.assertTrue(any("projectNow must be a nonempty string" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
