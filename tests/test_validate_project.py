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
