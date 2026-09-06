from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_project import EXPECTED_RELEASES, main, validate_project


ROOT = Path(__file__).resolve().parents[1]
REAL_PROJECT_PATH = ROOT / "content" / "spendwise-project.json"
CANONICAL_OUT_OF_SCOPE = [
    "full double-entry accounting",
    "general ledger",
    "tax",
    "stock trading",
    "investment portfolio",
    "cryptocurrency",
    "bank synchronization",
    "Open Banking",
    "OCR receipt",
    "family/shared finance",
    "financial advisor",
    "loan system",
    "payment gateway",
    "microservices",
    "Kafka",
    "Kubernetes",
    "mobile app",
    "blockchain",
    "complex accounting reconciliation",
    "support for every bank file format",
    "full multi-currency accounting engine",
]


def _feature(fid="feat-x", release_id="v0-1", **overrides):
    feature = {
        "id": fid,
        "name": "Example Feature",
        "description": "A feature used by the fixture.",
        "domainEntities": ["Money"],
        "introducedInReleaseId": release_id,
    }
    feature.update(overrides)
    return feature


def _release(rid, version, order, **overrides):
    release = {
        "id": rid,
        "version": version,
        "title": f"Release {version}",
        "order": order,
        "status": "planned",
        "problem": "A problem to solve.",
        "goal": "A goal to reach.",
        "featureIds": ["feat-x"],
        "learningDependencies": [],
        "acceptanceCriteria": ["Something works"],
        "buildTaskIds": ["task-x"] if rid == "v0-1" else [],
    }
    release.update(overrides)
    return release


def _releases():
    return [
        _release(rid, version, index + 1)
        for index, (rid, version) in enumerate(EXPECTED_RELEASES)
    ]

def _build_task(tid="task-x", **overrides):
    task = {
        "id": tid,
        "title": "Example build task",
        "releaseId": "v0-1",
        "featureIds": ["feat-x"],
        "problem": "A build problem.",
        "goal": "A build goal.",
        "constraints": [],
        "acceptanceCriteria": ["Compiles"],
        "relevantLessonIds": ["day-01"],
        "required": True,
    }
    task.update(overrides)
    return task


def _build_step(sid="step-task-x-01", **overrides):
    step = {
        "id": sid,
        "taskId": "task-x",
        "order": 1,
        "title": "Create the Money value object",
        "intent": "Money must be exact before anything totals it.",
        "knowledgePrereqLessonIds": ["day-01"],
        "artifactPrereqTaskIds": [],
        "filesTouched": ["src/main/java/com/spendwise/common/money/Money.java"],
        "doneWhen": "MoneyTest passes.",
        "verifyCommand": "./mvnw -Dtest=MoneyTest test",
        "architectureRules": ["R1"],
    }
    step.update(overrides)
    return step


def _milestone(mid="ms-x", **overrides):
    milestone = {
        "id": mid,
        "name": "Example milestone",
        "releaseIds": ["v0-1"],
        "summary": "A milestone summary.",
    }
    milestone.update(overrides)
    return milestone


def _arch_stage(sid="arch-x", **overrides):
    stage = {
        "id": sid,
        "releaseId": "v0-1",
        "title": "Example stage",
        "layers": ["domain"],
        "diagram": "domain -> service",
        "changesFromPrev": "initial layering",
        "rationale": "keeps the domain pure",
    }
    stage.update(overrides)
    return stage


def _lesson_entry(**overrides):
    entry = {
        "applicationType": "direct",
        "releaseId": "v0-1",
        "featureIds": ["feat-x"],
        "buildTaskIds": ["task-x"],
        "projectProblem": "A project problem.",
        "context": "Some context.",
        "application": "Some application.",
    }
    entry.update(overrides)
    return entry

def _project(**overrides):
    project = {
        "schemaVersion": 1,
        "product": {
            "id": "spendwise",
            "name": "Spendwise",
            "type": "Personal Expense & Budget Tracker",
            "vision": "Track spending clearly.",
            "outOfScope": list(CANONICAL_OUT_OF_SCOPE),
        },
        "releases": _releases(),
        "features": [_feature()],
        "buildTasks": [_build_task()],
        "milestones": [_milestone()],
        "architectureStages": [_arch_stage()],
        "lessonMap": {"day-01": _lesson_entry()},
    }
    project.update(overrides)
    return project


class ValidFixtureTests(unittest.TestCase):
    def test_accepts_a_complete_valid_fixture(self):
        self.assertEqual(validate_project(_project()), [])

    def test_accepts_theory_entry_without_release_or_feature(self):
        project = _project(lessonMap={"day-02": {
            "applicationType": "theory",
            "context": "Pure language foundation, no feature.",
        }})
        self.assertEqual(validate_project(project), [])

    def test_real_project_uses_the_canonical_checkpoint_contract(self):
        project = json.loads(REAL_PROJECT_PATH.read_text(encoding="utf-8"))

        self.assertEqual(validate_project(project), [])
        self.assertEqual(len(project["releases"]), 10)
        self.assertEqual([release["order"] for release in project["releases"]], list(range(1, 11)))
        self.assertEqual({release["status"] for release in project["releases"]}, {"planned"})
        self.assertTrue(all("title" in release and "name" not in release for release in project["releases"]))
        self.assertTrue(all(isinstance(release["buildTaskIds"], list) for release in project["releases"]))
        self.assertEqual(project["product"]["outOfScope"], CANONICAL_OUT_OF_SCOPE)
        self.assertNotIn("scope", project["product"])
        self.assertEqual(len(project["lessonMap"]), 38)
        self.assertTrue(all("concept" not in entry for entry in project["lessonMap"].values()))

        tasks_by_id = {task["id"]: task for task in project["buildTasks"]}
        listed_task_ids = []
        for release in project["releases"]:
            listed_task_ids.extend(release["buildTaskIds"])
            for task_id in release["buildTaskIds"]:
                self.assertEqual(tasks_by_id[task_id]["releaseId"], release["id"])
        self.assertCountEqual(listed_task_ids, tasks_by_id)


class TopLevelTests(unittest.TestCase):
    def test_rejects_unknown_top_level_key(self):
        project = _project()
        project["bogus"] = True
        errors = validate_project(project)
        self.assertTrue(any("unexpected key" in error for error in errors))

    def test_rejects_wrong_schema_version(self):
        errors = validate_project(_project(schemaVersion=2))
        self.assertTrue(any("schemaVersion" in error for error in errors))

    def test_rejects_non_object_artifact(self):
        self.assertTrue(any("JSON object" in error for error in validate_project([])))

class ReleaseSpineTests(unittest.TestCase):
    def test_rejects_wrong_release_count(self):
        project = _project(releases=_releases()[:-1])
        errors = validate_project(project)
        self.assertTrue(any("expected exactly 10 releases" in error for error in errors))

    def test_rejects_release_id_out_of_spine(self):
        releases = _releases()
        releases[1]["id"] = "v9-9"
        errors = validate_project(_project(releases=releases))
        self.assertTrue(any("must be 'v0-2'" in error for error in errors))

    def test_rejects_release_version_mismatch(self):
        releases = _releases()
        releases[0]["version"] = "V9.9"
        errors = validate_project(_project(releases=releases))
        self.assertTrue(any("version must be 'V0.1'" in error for error in errors))

    def test_rejects_non_contiguous_order(self):
        releases = _releases()
        releases[1]["order"] = 5
        errors = validate_project(_project(releases=releases))
        self.assertTrue(any("order must be 2" in error for error in errors))

    def test_rejects_release_featureid_dangling(self):
        releases = _releases()
        releases[0]["featureIds"] = ["feat-missing"]
        errors = validate_project(_project(releases=releases))
        self.assertTrue(any("feat-missing" in error for error in errors))

    def test_rejects_release_missing_acceptance_criteria(self):
        releases = _releases()
        releases[0]["acceptanceCriteria"] = []
        errors = validate_project(_project(releases=releases))
        self.assertTrue(any("acceptanceCriteria" in error for error in errors))

    def test_rejects_release_without_authored_status(self):
        releases = _releases()
        del releases[0]["status"]
        errors = validate_project(_project(releases=releases))
        self.assertTrue(any("status" in error for error in errors))

    def test_rejects_invalid_release_status(self):
        releases = _releases()
        releases[0]["status"] = "current"
        errors = validate_project(_project(releases=releases))
        self.assertTrue(any("status" in error and "planned" in error for error in errors))

    def test_accepts_every_valid_release_status(self):
        for status in ("released", "building", "planned"):
            with self.subTest(status=status):
                releases = _releases()
                releases[0]["status"] = status
                self.assertEqual(validate_project(_project(releases=releases)), [])

    def test_rejects_release_without_build_task_ids(self):
        releases = _releases()
        del releases[0]["buildTaskIds"]
        errors = validate_project(_project(releases=releases))
        self.assertTrue(any("buildTaskIds" in error for error in errors))

    def test_accepts_release_with_no_build_tasks(self):
        project = _project(buildTasks=[], lessonMap={})
        releases = _releases()
        releases[0]["buildTaskIds"] = []
        project["releases"] = releases
        self.assertEqual(validate_project(project), [])

    def test_rejects_release_build_task_id_that_does_not_resolve(self):
        releases = _releases()
        releases[0]["buildTaskIds"] = ["task-missing"]
        errors = validate_project(_project(releases=releases))
        self.assertTrue(any("task-missing" in error and "buildTask" in error for error in errors))

    def test_rejects_release_containing_task_owned_by_another_release(self):
        releases = _releases()
        releases[0]["buildTaskIds"] = []
        releases[1]["buildTaskIds"] = ["task-x"]
        errors = validate_project(_project(releases=releases))
        self.assertTrue(any("task-x" in error and "releaseId" in error for error in errors))

    def test_rejects_task_missing_from_its_release_ordering_list(self):
        releases = _releases()
        releases[0]["buildTaskIds"] = []
        errors = validate_project(_project(releases=releases))
        self.assertTrue(any("task-x" in error and "ordering" in error for error in errors))

    def test_rejects_duplicate_task_id_within_release_ordering_list(self):
        releases = _releases()
        releases[0]["buildTaskIds"] = ["task-x", "task-x"]
        errors = validate_project(_project(releases=releases))
        self.assertTrue(any("duplicate buildTaskId" in error for error in errors))


class ProductContractTests(unittest.TestCase):
    def test_rejects_product_id_that_is_not_url_safe(self):
        project = _project()
        project["product"]["id"] = "Spendwise_App"
        errors = validate_project(project)
        self.assertTrue(any("product id" in error and "URL-safe" in error for error in errors))

    def test_rejects_product_id_duplicated_by_another_object(self):
        project = _project(features=[_feature(fid="spendwise")])
        errors = validate_project(project)
        self.assertTrue(any("duplicate id 'spendwise'" in error for error in errors))

    def test_rejects_nested_scope_shape(self):
        project = _project()
        out_of_scope = project["product"].pop("outOfScope")
        project["product"]["scope"] = {"outOfScope": out_of_scope}
        errors = validate_project(project)
        self.assertTrue(any("scope" in error and "unexpected key" in error for error in errors))
        self.assertTrue(any("outOfScope" in error for error in errors))

    def test_rejects_changed_finance_lite_out_of_scope_list(self):
        project = _project()
        project["product"]["outOfScope"].remove("tax")
        errors = validate_project(project)
        self.assertTrue(any("outOfScope" in error and "tax" in error for error in errors))

    def test_rejects_duplicate_out_of_scope_item(self):
        project = _project()
        project["product"]["outOfScope"].append("tax")
        errors = validate_project(project)
        self.assertTrue(any("outOfScope" in error and "duplicate" in error for error in errors))


class FeatureTests(unittest.TestCase):
    def test_rejects_duplicate_ids_across_objects(self):
        project = _project(buildTasks=[_build_task(tid="feat-x")])
        errors = validate_project(project)
        self.assertTrue(any("duplicate id 'feat-x'" in error for error in errors))

    def test_rejects_non_url_safe_id(self):
        project = _project(features=[_feature(fid="Feat_X")])
        errors = validate_project(project)
        self.assertTrue(any("URL-safe" in error for error in errors))

    def test_rejects_feature_release_link_dangling(self):
        project = _project(features=[_feature(release_id="v9-9")])
        errors = validate_project(project)
        self.assertTrue(any("introducedInReleaseId" in error for error in errors))

class BuildTaskTests(unittest.TestCase):
    def test_rejects_releaseid_dangling(self):
        project = _project(buildTasks=[_build_task(releaseId="v9-9")])
        errors = validate_project(project)
        self.assertTrue(any("does not resolve to a release" in error for error in errors))

    def test_rejects_required_not_boolean(self):
        project = _project(buildTasks=[_build_task(required="yes")])
        errors = validate_project(project)
        self.assertTrue(any("required must be a boolean" in error for error in errors))

    def test_rejects_featureid_dangling(self):
        project = _project(buildTasks=[_build_task(featureIds=["feat-missing"])])
        errors = validate_project(project)
        self.assertTrue(any("feat-missing" in error for error in errors))

    def test_rejects_unknown_relevant_lesson(self):
        project = _project(buildTasks=[_build_task(relevantLessonIds=["day-99"])])
        errors = validate_project(project)
        self.assertTrue(any("day-99" in error and "known lesson" in error for error in errors))


class BuildStepTests(unittest.TestCase):
    """The optional top-level buildSteps array (absent is valid; see
    ValidFixtureTests, whose fixture carries no buildSteps key)."""

    def test_accepts_absent_build_steps(self):
        project = _project()
        self.assertNotIn("buildSteps", project)
        self.assertEqual(validate_project(project), [])

    def test_accepts_empty_build_steps(self):
        self.assertEqual(validate_project(_project(buildSteps=[])), [])

    def test_rejects_explicit_null_build_steps(self):
        """An absent key means "not authored yet"; an explicit null means a
        truncated write, and must not be silently tolerated as the same thing."""
        errors = validate_project(_project(buildSteps=None))
        self.assertTrue(any("buildSteps must be a list" in error for error in errors))

    def test_accepts_a_valid_step(self):
        self.assertEqual(validate_project(_project(buildSteps=[_build_step()])), [])

    def test_accepts_optional_keys(self):
        step = _build_step(
            commonMistake="Using double for money.",
            mentorHint="Point at BigDecimal, not the answer.",
            estimatedMinutes=45,
        )
        self.assertEqual(validate_project(_project(buildSteps=[step])), [])

    def test_rejects_non_list_build_steps(self):
        errors = validate_project(_project(buildSteps={"id": "step-x"}))
        self.assertTrue(any("buildSteps must be a list" in error for error in errors))

    def test_rejects_unknown_step_key(self):
        errors = validate_project(_project(buildSteps=[_build_step(steps=[])]))
        self.assertTrue(any("unexpected key" in error for error in errors))

    def test_rejects_missing_required_key(self):
        step = _build_step()
        del step["doneWhen"]
        errors = validate_project(_project(buildSteps=[step]))
        self.assertTrue(any("missing required key(s)" in error and "doneWhen" in error for error in errors))

    def test_rejects_duplicate_step_id(self):
        steps = [_build_step(), _build_step(order=2)]
        errors = validate_project(_project(buildSteps=steps))
        self.assertTrue(any("duplicate id 'step-task-x-01'" in error for error in errors))

    def test_rejects_step_id_colliding_with_another_object(self):
        errors = validate_project(_project(buildSteps=[_build_step(sid="task-x")]))
        self.assertTrue(any("duplicate id 'task-x'" in error for error in errors))

    def test_rejects_dangling_task_id(self):
        errors = validate_project(_project(buildSteps=[_build_step(taskId="task-missing")]))
        self.assertTrue(any("task-missing" in error and "does not resolve" in error for error in errors))

    def test_rejects_non_integer_order(self):
        errors = validate_project(_project(buildSteps=[_build_step(order="1")]))
        self.assertTrue(any("order must be an integer" in error for error in errors))

    def test_rejects_order_gap_within_a_task(self):
        steps = [_build_step(), _build_step(sid="step-task-x-03", order=3)]
        errors = validate_project(_project(buildSteps=steps))
        self.assertTrue(any("contiguous 1..2" in error and "[1, 3]" in error for error in errors))

    def test_rejects_duplicate_order_within_a_task(self):
        steps = [_build_step(), _build_step(sid="step-task-x-02", order=1)]
        errors = validate_project(_project(buildSteps=steps))
        self.assertTrue(any("contiguous 1..2" in error for error in errors))

    def test_accepts_contiguous_orders_across_two_tasks(self):
        project = _project(
            buildTasks=[_build_task(), _build_task(tid="task-y", releaseId="v0-2")],
            buildSteps=[
                _build_step(),
                _build_step(sid="step-task-x-02", order=2),
                _build_step(sid="step-task-y-01", taskId="task-y", order=1),
            ],
        )
        releases = _releases()
        releases[1]["buildTaskIds"] = ["task-y"]
        project["releases"] = releases
        self.assertEqual(validate_project(project), [])

    def test_rejects_unknown_knowledge_prereq_lesson(self):
        errors = validate_project(_project(buildSteps=[_build_step(knowledgePrereqLessonIds=["day-99"])]))
        self.assertTrue(any("day-99" in error and "known lesson" in error for error in errors))

    def test_accepts_empty_prereq_lists(self):
        step = _build_step(knowledgePrereqLessonIds=[], artifactPrereqTaskIds=[])
        self.assertEqual(validate_project(_project(buildSteps=[step])), [])

    def test_rejects_empty_files_touched(self):
        errors = validate_project(_project(buildSteps=[_build_step(filesTouched=[])]))
        self.assertTrue(any("filesTouched" in error and "nonempty list" in error for error in errors))

    def test_rejects_dangling_artifact_prereq(self):
        errors = validate_project(_project(buildSteps=[_build_step(artifactPrereqTaskIds=["task-missing"])]))
        self.assertTrue(any("artifactPrereqTaskId 'task-missing'" in error for error in errors))

    def test_rejects_self_referential_artifact_prereq(self):
        errors = validate_project(_project(buildSteps=[_build_step(artifactPrereqTaskIds=["task-x"])]))
        self.assertTrue(any("own task" in error for error in errors))

    def test_rejects_artifact_prereq_from_a_later_release(self):
        """The rule that makes learning-order dependency mechanical: a V0.1 step
        may not require an artifact that V0.4 produces."""
        project = _project(
            buildTasks=[_build_task(), _build_task(tid="task-later", releaseId="v0-4")],
            buildSteps=[_build_step(artifactPrereqTaskIds=["task-later"])],
        )
        releases = _releases()
        releases[3]["buildTaskIds"] = ["task-later"]
        project["releases"] = releases
        errors = validate_project(project)
        self.assertTrue(any(
            "task-later" in error and "ordered after" in error for error in errors
        ))

    def test_accepts_artifact_prereq_from_an_earlier_release(self):
        project = _project(
            buildTasks=[_build_task(), _build_task(tid="task-later", releaseId="v0-4")],
            buildSteps=[_build_step(
                sid="step-task-later-01", taskId="task-later",
                artifactPrereqTaskIds=["task-x"],
            )],
        )
        releases = _releases()
        releases[3]["buildTaskIds"] = ["task-later"]
        project["releases"] = releases
        self.assertEqual(validate_project(project), [])

    def test_accepts_artifact_prereq_from_the_same_release(self):
        project = _project(
            buildTasks=[_build_task(), _build_task(tid="task-sibling")],
            buildSteps=[_build_step(artifactPrereqTaskIds=["task-sibling"])],
        )
        releases = _releases()
        releases[0]["buildTaskIds"] = ["task-x", "task-sibling"]
        project["releases"] = releases
        self.assertEqual(validate_project(project), [])

    def test_rejects_architecture_rule_not_matching_the_pattern(self):
        for rule in ("R22a", "R100", "r22", "R", "RULE22"):
            with self.subTest(rule=rule):
                errors = validate_project(_project(buildSteps=[_build_step(architectureRules=[rule])]))
                self.assertTrue(any("architectureRules entry" in error for error in errors))

    def test_accepts_one_and_two_digit_architecture_rules(self):
        step = _build_step(architectureRules=["R1", "R9", "R22", "R26"])
        self.assertEqual(validate_project(_project(buildSteps=[step])), [])

    def test_rejects_non_positive_estimated_minutes(self):
        for minutes in (0, -5, "30", 12.5, True):
            with self.subTest(minutes=minutes):
                errors = validate_project(_project(buildSteps=[_build_step(estimatedMinutes=minutes)]))
                self.assertTrue(any("estimatedMinutes" in error for error in errors))

    def test_rejects_blank_optional_string(self):
        errors = validate_project(_project(buildSteps=[_build_step(mentorHint="")]))
        self.assertTrue(any("mentorHint" in error for error in errors))

    def test_reports_non_string_ids_instead_of_raising(self):
        """A non-string id must produce an ERROR line, never a TypeError from a
        set-membership test: the validator's contract is to return errors, and a
        crash inside build_site.py would surface as a traceback, not a message."""
        step = _build_step(
            taskId=["task-x"],
            artifactPrereqTaskIds=[{}],
            knowledgePrereqLessonIds=[["day-01"]],
        )
        errors = validate_project(_project(buildSteps=[step]))
        self.assertTrue(any("taskId" in error for error in errors))
        self.assertTrue(any("artifactPrereqTaskId" in error for error in errors))
        self.assertTrue(any("knowledgePrereqLessonId" in error for error in errors))


class CapstoneWindowGuardTests(unittest.TestCase):
    """R-CAPSTONE-GUARD: day-31..day-36 unlock knowledge; they never schedule
    Spendwise execution, so they must expose no build-task CTA."""

    def test_rejects_non_empty_build_task_ids_in_the_capstone_window(self):
        for lesson_id in ("day-31", "day-32", "day-33", "day-34", "day-35", "day-36"):
            with self.subTest(lesson_id=lesson_id):
                project = _project(lessonMap={lesson_id: _lesson_entry()})
                errors = validate_project(project)
                self.assertTrue(any(
                    "capstone window" in error and lesson_id in error for error in errors
                ))

    def test_accepts_capstone_window_direct_entry_with_empty_build_task_ids(self):
        project = _project(lessonMap={"day-33": _lesson_entry(buildTaskIds=[])})
        self.assertEqual(validate_project(project), [])

    def test_accepts_capstone_window_theory_entry(self):
        project = _project(lessonMap={"day-33": {
            "applicationType": "theory",
            "context": "Unlocks JwtEncoder knowledge; execution is post-day-36.",
        }})
        self.assertEqual(validate_project(project), [])

    def test_allows_build_task_ids_immediately_outside_the_window(self):
        for lesson_id in ("day-30", "day-37"):
            with self.subTest(lesson_id=lesson_id):
                project = _project(lessonMap={lesson_id: _lesson_entry()})
                self.assertEqual(validate_project(project), [])

    def test_real_artifact_capstone_window_carries_no_build_task_ids(self):
        project = json.loads(REAL_PROJECT_PATH.read_text(encoding="utf-8"))
        for lesson_id in ("day-31", "day-32", "day-33", "day-34", "day-35", "day-36"):
            entry = project["lessonMap"][lesson_id]
            self.assertEqual(entry.get("buildTaskIds", []), [], lesson_id)


class AlsoUsedInTests(unittest.TestCase):
    def test_accepts_a_resolving_also_used_in(self):
        project = _project(
            buildTasks=[_build_task(), _build_task(tid="task-y")],
            lessonMap={"day-01": _lesson_entry(alsoUsedIn=["task-y"])},
        )
        releases = _releases()
        releases[0]["buildTaskIds"] = ["task-x", "task-y"]
        project["releases"] = releases
        self.assertEqual(validate_project(project), [])

    def test_also_used_in_task_need_not_share_the_lesson_release(self):
        """The point of the key: reference a task another lesson owns, without
        inheriting the release/feature-coverage obligations of buildTaskIds."""
        project = _project(
            buildTasks=[_build_task(), _build_task(tid="task-later", releaseId="v0-4")],
            lessonMap={"day-01": _lesson_entry(alsoUsedIn=["task-later"])},
        )
        releases = _releases()
        releases[3]["buildTaskIds"] = ["task-later"]
        project["releases"] = releases
        self.assertEqual(validate_project(project), [])

    def test_rejects_dangling_also_used_in(self):
        project = _project(lessonMap={"day-01": _lesson_entry(alsoUsedIn=["task-missing"])})
        errors = validate_project(project)
        self.assertTrue(any("alsoUsedIn" in error and "task-missing" in error for error in errors))

    def test_rejects_also_used_in_duplicating_an_owned_task(self):
        project = _project(lessonMap={"day-01": _lesson_entry(alsoUsedIn=["task-x"])})
        errors = validate_project(project)
        self.assertTrue(any("alsoUsedIn" in error and "already owned" in error for error in errors))

    def test_rejects_empty_also_used_in(self):
        project = _project(lessonMap={"day-01": _lesson_entry(alsoUsedIn=[])})
        errors = validate_project(project)
        self.assertTrue(any("alsoUsedIn" in error and "nonempty list" in error for error in errors))

    def test_also_used_in_stays_optional(self):
        project = _project()
        self.assertNotIn("alsoUsedIn", project["lessonMap"]["day-01"])
        self.assertEqual(validate_project(project), [])

    def test_reports_non_string_also_used_in_instead_of_raising(self):
        project = _project(lessonMap={"day-01": _lesson_entry(alsoUsedIn=[{}])})
        errors = validate_project(project)
        self.assertTrue(any("alsoUsedIn" in error for error in errors))


class MilestoneAndArchStageTests(unittest.TestCase):
    def test_rejects_milestone_releaseid_dangling(self):
        project = _project(milestones=[_milestone(releaseIds=["v9-9"])])
        errors = validate_project(project)
        self.assertTrue(any("v9-9" in error for error in errors))

    def test_rejects_archstage_releaseid_dangling(self):
        project = _project(architectureStages=[_arch_stage(releaseId="v9-9")])
        errors = validate_project(project)
        self.assertTrue(any("v9-9" in error for error in errors))


class LessonMapTests(unittest.TestCase):
    def test_rejects_unknown_lesson_key(self):
        project = _project(lessonMap={"day-99": _lesson_entry()})
        errors = validate_project(project)
        self.assertTrue(any("known lesson id" in error for error in errors))

    def test_rejects_invalid_application_type(self):
        project = _project(lessonMap={"day-01": _lesson_entry(applicationType="maybe")})
        errors = validate_project(project)
        self.assertTrue(any("applicationType" in error for error in errors))

    def test_rejects_missing_context(self):
        entry = _lesson_entry()
        del entry["context"]
        project = _project(lessonMap={"day-01": entry})
        errors = validate_project(project)
        self.assertTrue(any("context" in error for error in errors))

    def test_rejects_direct_entry_dangling_release(self):
        project = _project(lessonMap={"day-01": _lesson_entry(releaseId="v9-9")})
        errors = validate_project(project)
        self.assertTrue(any("does not resolve to a release" in error for error in errors))

    def test_rejects_direct_entry_dangling_feature(self):
        project = _project(lessonMap={"day-01": _lesson_entry(featureIds=["feat-missing"])})
        errors = validate_project(project)
        self.assertTrue(any("feat-missing" in error for error in errors))

    def test_rejects_dangling_build_task(self):
        project = _project(lessonMap={"day-01": _lesson_entry(buildTaskIds=["task-missing"])})
        errors = validate_project(project)
        self.assertTrue(any("task-missing" in error for error in errors))

    def test_rejects_lesson_task_from_another_release(self):
        project = _project(lessonMap={"day-01": _lesson_entry(releaseId="v0-2")})
        errors = validate_project(project)
        self.assertTrue(any("task-x" in error and "releaseId" in error for error in errors))

    def test_rejects_lesson_features_that_do_not_cover_task_features(self):
        project = _project(
            features=[_feature(), _feature(fid="feat-y")],
            buildTasks=[_build_task(featureIds=["feat-x", "feat-y"])],
            lessonMap={"day-01": _lesson_entry(featureIds=["feat-x"])},
        )
        errors = validate_project(project)
        self.assertTrue(any("feat-y" in error and "featureIds" in error for error in errors))

    def test_rejects_future_entry_without_application(self):
        entry = _lesson_entry(applicationType="future")
        del entry["application"]
        errors = validate_project(_project(lessonMap={"day-01": entry}))
        self.assertTrue(any("application" in error for error in errors))

    def test_accepts_future_entry_without_project_problem(self):
        entry = _lesson_entry(applicationType="future")
        del entry["projectProblem"]
        self.assertEqual(validate_project(_project(lessonMap={"day-01": entry})), [])


class ObjectShapeTests(unittest.TestCase):
    def test_rejects_release_name_instead_of_canonical_title(self):
        releases = _releases()
        releases[0]["name"] = releases[0].pop("title")
        errors = validate_project(_project(releases=releases))
        self.assertTrue(any("name" in error and "unexpected key" in error for error in errors))
        self.assertTrue(any("title" in error for error in errors))

    def test_rejects_lesson_concept_field(self):
        entry = _lesson_entry(concept="Encapsulation")
        errors = validate_project(_project(lessonMap={"day-01": entry}))
        self.assertTrue(any("concept" in error and "unexpected key" in error for error in errors))


# --- Malformed-input totality -------------------------------------------------
# The validator's contract is TOTAL: any JSON that parses must come back as a
# list of "ERROR ..." diagnostics, never as an uncaught exception. build_site.py
# calls validate_project() before embedding, so a raised TypeError reaches the
# author as a bare traceback with no scope and no file, and the closed schema
# stops functioning as a gate. Two crash families are covered here:
#   unhashable   -- `["v0-1"] in release_ids` -> TypeError: unhashable type
#   not iterable -- `for fid in 7`            -> TypeError: 'int' is not iterable
# Each case must ALSO stay invalid: turning a crash into silent acceptance would
# be a loosened schema, which is the one outcome worse than the crash.

MALFORMED_LIST_VALUES = (
    [["task-x"]],
    [{}],
    [{"id": "task-x"}],
    [7],
    [None],
    [[]],
    {"0": "task-x"},
    7,
)

MALFORMED_SCALAR_VALUES = (
    ["v0-1"],
    [["v0-1"]],
    {"id": "v0-1"},
    {},
    [],
    7,
)


def _with_release(key, value):
    releases = _releases()
    releases[0][key] = value
    return _project(releases=releases)


def _with_feature(key, value):
    return _project(features=[_feature(**{key: value})])


def _with_task(key, value):
    return _project(buildTasks=[_build_task(**{key: value})])


def _with_milestone(key, value):
    return _project(milestones=[_milestone(**{key: value})])


def _with_arch_stage(key, value):
    return _project(architectureStages=[_arch_stage(**{key: value})])


def _with_lesson_entry(key, value):
    return _project(lessonMap={"day-01": _lesson_entry(**{key: value})})


def _with_build_step(key, value):
    return _project(buildSteps=[_build_step(**{key: value})])


# (label, fixture builder, singular stem that must appear in some diagnostic).
# The stem is singular because a malformed *entry* is reported by the resolver
# ("featureId 7 does not resolve") while a malformed *container* is reported by
# the type check ("featureIds must be a list"); the stem matches both.
LIST_REFERENCE_PATHS = (
    ("release.featureIds", lambda v: _with_release("featureIds", v), "featureId"),
    ("release.buildTaskIds", lambda v: _with_release("buildTaskIds", v), "buildTaskId"),
    ("buildTask.featureIds", lambda v: _with_task("featureIds", v), "featureId"),
    ("buildTask.relevantLessonIds", lambda v: _with_task("relevantLessonIds", v), "relevantLessonId"),
    ("milestone.releaseIds", lambda v: _with_milestone("releaseIds", v), "releaseId"),
    ("lessonMap.featureIds", lambda v: _with_lesson_entry("featureIds", v), "featureId"),
    ("lessonMap.buildTaskIds", lambda v: _with_lesson_entry("buildTaskIds", v), "buildTaskId"),
    ("lessonMap.alsoUsedIn", lambda v: _with_lesson_entry("alsoUsedIn", v), "alsoUsedIn"),
    (
        "buildStep.knowledgePrereqLessonIds",
        lambda v: _with_build_step("knowledgePrereqLessonIds", v),
        "knowledgePrereqLessonId",
    ),
    (
        "buildStep.artifactPrereqTaskIds",
        lambda v: _with_build_step("artifactPrereqTaskIds", v),
        "artifactPrereqTaskId",
    ),
)

SCALAR_REFERENCE_PATHS = (
    ("feature.introducedInReleaseId", lambda v: _with_feature("introducedInReleaseId", v), "introducedInReleaseId"),
    ("buildTask.releaseId", lambda v: _with_task("releaseId", v), "releaseId"),
    ("architectureStage.releaseId", lambda v: _with_arch_stage("releaseId", v), "releaseId"),
    ("lessonMap.releaseId", lambda v: _with_lesson_entry("releaseId", v), "releaseId"),
    ("buildStep.taskId", lambda v: _with_build_step("taskId", v), "taskId"),
)


class MalformedInputTotalityTests(unittest.TestCase):
    def _assert_diagnostics(self, project, stem):
        try:
            errors = validate_project(project)
        except Exception as exception:
            self.fail(f"validate_project raised {type(exception).__name__}: {exception}")
        self.assertIsInstance(errors, list)
        for error in errors:
            self.assertIsInstance(error, str)
            self.assertTrue(error.startswith("ERROR "), error)
        self.assertTrue(errors, "malformed input must stay invalid, not become valid")
        self.assertTrue(any(stem in error for error in errors), errors)
        return errors

    def test_malformed_reference_lists_report_instead_of_raising(self):
        for label, build, stem in LIST_REFERENCE_PATHS:
            for value in MALFORMED_LIST_VALUES:
                with self.subTest(path=label, value=value):
                    self._assert_diagnostics(build(value), stem)

    def test_malformed_reference_scalars_report_instead_of_raising(self):
        for label, build, stem in SCALAR_REFERENCE_PATHS:
            for value in MALFORMED_SCALAR_VALUES:
                with self.subTest(path=label, value=value):
                    self._assert_diagnostics(build(value), stem)

    def test_duplicate_unhashable_out_of_scope_items_report(self):
        """The duplicate scan built a set from authored values."""
        project = _project()
        project["product"]["outOfScope"] = [["tax"], ["tax"]]
        self._assert_diagnostics(project, "outOfScope")

    def test_non_string_enum_values_report(self):
        releases = _releases()
        releases[0]["status"] = ["planned"]
        self._assert_diagnostics(_project(releases=releases), "status")
        self._assert_diagnostics(_with_lesson_entry("applicationType", {"direct": 1}), "applicationType")

    def test_capstone_guard_survives_a_non_list_build_task_ids(self):
        """R-CAPSTONE-GUARD formatted the offending value with list()."""
        project = _project(lessonMap={"day-33": _lesson_entry(buildTaskIds=7)})
        self._assert_diagnostics(project, "buildTaskId")

    def test_theory_entry_reference_lists_are_still_type_checked(self):
        """A theory entry need not carry references, but a malformed one must not
        pass: the shared coverage and capstone logic below reads these keys for
        every applicationType, not just direct/future."""
        for key in ("featureIds", "buildTaskIds"):
            for value in ([{}], 7, [["x"]], {"a": "x"}):
                with self.subTest(key=key, value=value):
                    project = _project(lessonMap={"day-01": {
                        "applicationType": "theory",
                        "context": "Pure language foundation.",
                        key: value,
                    }})
                    self._assert_diagnostics(project, key[:-1])

    def test_step_release_order_lookup_survives_a_malformed_task_release(self):
        project = _project(
            buildTasks=[_build_task(releaseId=["v0-1"])],
            buildSteps=[_build_step()],
        )
        self._assert_diagnostics(project, "releaseId")

    def test_prereq_release_order_lookup_survives_a_malformed_task_release(self):
        project = _project(
            buildTasks=[_build_task(), _build_task(tid="task-later", releaseId=["v0-4"])],
            buildSteps=[_build_step(artifactPrereqTaskIds=["task-later"])],
        )
        releases = _releases()
        releases[3]["buildTaskIds"] = ["task-later"]
        project["releases"] = releases
        self._assert_diagnostics(project, "releaseId")

    def test_lesson_feature_coverage_survives_a_malformed_task_feature_list(self):
        project = _project(buildTasks=[_build_task(featureIds=[["feat-x"]])])
        self._assert_diagnostics(project, "featureId")

    def test_also_used_in_survives_a_non_list_build_task_ids(self):
        project = _project(
            buildTasks=[_build_task(), _build_task(tid="task-y")],
            lessonMap={"day-01": _lesson_entry(buildTaskIds=7, alsoUsedIn=["task-y"])},
        )
        releases = _releases()
        releases[0]["buildTaskIds"] = ["task-x", "task-y"]
        project["releases"] = releases
        self._assert_diagnostics(project, "buildTaskId")

    def test_non_list_build_tasks_reports_instead_of_raising(self):
        """`build_tasks or []` guarded only the falsy case, so a truthy non-list
        (7, True, 1.5) still reached `for task in 7` in the lessonMap and
        buildSteps id indexes."""
        for value in (7, True, 1.5, "task-x", {"task-x": {}}):
            with self.subTest(value=value):
                self._assert_diagnostics(_project(buildTasks=value), "buildTasks")
                self._assert_diagnostics(
                    _project(buildTasks=value, buildSteps=[_build_step()]), "buildTasks"
                )

    def test_hardening_adds_no_diagnostics_to_valid_data(self):
        self.assertEqual(validate_project(_project()), [])
        self.assertEqual(validate_project(_project(buildSteps=[_build_step()])), [])
        self.assertEqual(validate_project(_project(lessonMap={"day-02": {
            "applicationType": "theory",
            "context": "Pure language foundation, no feature.",
        }})), [])


class CliTests(unittest.TestCase):
    def _run(self, project):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spendwise-project.json"
            path.write_text(json.dumps(project), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main(["--project", str(path)])
            return exit_code, output.getvalue()

    def test_valid_project_passes(self):
        exit_code, output = self._run(_project())
        self.assertEqual(exit_code, 0)
        self.assertIn("PASS releases=10", output)

    def test_invalid_project_exits_nonzero_with_error_lines(self):
        exit_code, output = self._run(_project(schemaVersion=2))
        self.assertEqual(exit_code, 1)
        lines = [line for line in output.splitlines() if line]
        self.assertTrue(all(line.startswith("ERROR ") for line in lines))

    def test_missing_file_exits_with_read_error(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = main(["--project", "does-not-exist.json"])
        self.assertEqual(exit_code, 2)
        self.assertIn("could not read", output.getvalue())


if __name__ == "__main__":
    unittest.main()
