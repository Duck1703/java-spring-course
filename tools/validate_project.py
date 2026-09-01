"""Validate content/spendwise-project.json: the Spendwise project data layer.

This is the authoritative validator for the project artifact, mirroring the
closed-schema, referential-integrity discipline of tools/validate_lessons.py
(the standard library has no JSON Schema engine). It enforces:

- a closed top-level schema and closed per-object schemas (unknown keys FAIL);
- URL-safe, globally-unique stable ids (^[a-z0-9][a-z0-9-]*$, no dots);
- the exact 10-release V0.1..V1.0 spine in contiguous order (no scope creep);
- every cross-object id reference resolves (release<->feature<->buildTask,
  milestone->release, architectureStage->release, lessonMap->release/feature/
  buildTask, buildTask/lessonMap->lesson);
- lessonMap applicationType enum and per-type required fields.

Returns "ERROR ..." strings the same way validate_lessons.py does; an empty
list means the artifact is valid. build_site.py imports validate_project() and
refuses to build when it returns any error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

# Canonical 40-lesson course sequence (matches build_site.EXPECTED_LESSON_IDS).
LESSON_IDS = [f"day-{n:02d}" for n in range(1, 39)] + ["day-39-64", "day-65-66"]

# The fixed 10-release spine, master-plan order. ids/versions are stable and
# language-neutral, so they are enforced exactly; titles are authored (only
# required to be nonempty) to allow localized wording.
EXPECTED_RELEASES = [
    ("v0-1", "V0.1"),
    ("v0-2", "V0.2"),
    ("v0-3", "V0.3"),
    ("v0-4", "V0.4"),
    ("v0-5", "V0.5"),
    ("v0-6", "V0.6"),
    ("v0-7", "V0.7"),
    ("v0-8", "V0.8"),
    ("v0-9", "V0.9"),
    ("v1-0", "V1.0"),
]

APPLICATION_TYPES = {"direct", "future", "theory"}
RELEASE_STATUSES = {"released", "building", "planned"}

# Canonical Finance Lite boundary from the master plan. Exact equality prevents
# the product contract, validator, and plan from silently drifting apart.
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

TOP_LEVEL_KEYS = {
    "schemaVersion", "product", "releases", "features", "buildTasks",
    "milestones", "architectureStages", "lessonMap",
}
PRODUCT_KEYS = {"id", "name", "type", "vision", "outOfScope"}
RELEASE_KEYS = {
    "id", "version", "title", "order", "status", "problem", "goal",
    "featureIds", "learningDependencies", "acceptanceCriteria", "buildTaskIds",
}
FEATURE_KEYS = {"id", "name", "description", "domainEntities", "introducedInReleaseId"}
BUILD_TASK_KEYS = {
    "id", "title", "releaseId", "featureIds", "problem", "goal",
    "constraints", "acceptanceCriteria", "relevantLessonIds", "required",
}
MILESTONE_KEYS = {"id", "name", "releaseIds", "summary"}
ARCH_STAGE_KEYS = {"id", "releaseId", "title", "layers", "diagram", "changesFromPrev", "rationale"}
LESSON_MAP_KEYS = {
    "applicationType", "releaseId", "featureIds", "buildTaskIds",
    "projectProblem", "context", "application",
}


def _error(scope: str, message: str) -> str:
    return f"ERROR {scope} {message}"


def _check_id(value, scope: str, seen: dict, kind: str) -> list[str]:
    """Validate one id is a nonempty URL-safe string, unique across the file."""
    errors = []
    if not isinstance(value, str) or not value:
        return [_error(scope, f"{kind} id must be a nonempty string")]
    if not ID_RE.match(value):
        errors.append(_error(scope, f"{kind} id {value!r} is not URL-safe (^[a-z0-9][a-z0-9-]*$)"))
    owner = seen.get(value)
    if owner is not None:
        errors.append(_error(scope, f"duplicate id {value!r} (already used by {owner})"))
    else:
        seen[value] = kind
    return errors


def _closed_keys(obj: dict, allowed: set, scope: str) -> list[str]:
    extra = set(obj) - allowed
    if extra:
        return [_error(scope, f"unexpected key(s) {sorted(extra)}")]
    return []


def _require_str(obj: dict, key: str, scope: str) -> list[str]:
    if not isinstance(obj.get(key), str) or not obj.get(key):
        return [_error(scope, f"{key} must be a nonempty string")]
    return []


def _require_str_list(obj: dict, key: str, scope: str, *, nonempty_list: bool = False) -> list[str]:
    value = obj.get(key)
    if not isinstance(value, list):
        return [_error(scope, f"{key} must be a list")]
    errors = []
    if nonempty_list and not value:
        errors.append(_error(scope, f"{key} must be a nonempty list"))
    for item in value:
        if not isinstance(item, str) or not item:
            errors.append(_error(scope, f"{key} entries must be nonempty strings"))
            break
    return errors


def _validate_product(product, seen_ids: dict, errors: list[str]) -> None:
    if not isinstance(product, dict):
        errors.append(_error("product", "product must be an object"))
        return
    errors.extend(_closed_keys(product, PRODUCT_KEYS, "product"))
    errors.extend(_check_id(product.get("id"), "product", seen_ids, "product"))
    errors.extend(_require_str(product, "name", "product"))
    errors.extend(_require_str(product, "type", "product"))
    errors.extend(_require_str(product, "vision", "product"))
    out_of_scope = product.get("outOfScope")
    errors.extend(_require_str_list(product, "outOfScope", "product", nonempty_list=True))
    if isinstance(out_of_scope, list):
        duplicates = sorted({item for item in out_of_scope if out_of_scope.count(item) > 1})
        if duplicates:
            errors.append(_error("product", f"outOfScope has duplicate item(s) {duplicates}"))
        if out_of_scope != CANONICAL_OUT_OF_SCOPE:
            missing = [item for item in CANONICAL_OUT_OF_SCOPE if item not in out_of_scope]
            extra = [item for item in out_of_scope if item not in CANONICAL_OUT_OF_SCOPE]
            errors.append(_error(
                "product",
                "outOfScope must exactly match the canonical Finance Lite list"
                f"; missing={missing}; extra={extra}",
            ))


def _validate_releases(releases, feature_ids: set, seen_ids: dict, errors: list[str]) -> set:
    release_ids: set = set()
    if not isinstance(releases, list):
        errors.append(_error("releases", "releases must be a list"))
        return release_ids
    if len(releases) != len(EXPECTED_RELEASES):
        errors.append(_error("releases", f"expected exactly {len(EXPECTED_RELEASES)} releases, found {len(releases)}"))
    for index, release in enumerate(releases):
        scope = f"release[{index}]"
        if not isinstance(release, dict):
            errors.append(_error(scope, "release must be an object"))
            continue
        rid = release.get("id")
        scope = f"release {rid}" if isinstance(rid, str) and rid else scope
        errors.extend(_closed_keys(release, RELEASE_KEYS, scope))
        errors.extend(_check_id(rid, scope, seen_ids, "release"))
        if isinstance(rid, str) and rid:
            release_ids.add(rid)
        # Fixed spine: id + version must match the master-plan release at this
        # position exactly; no new/reordered/renamed releases.
        if index < len(EXPECTED_RELEASES):
            exp_id, exp_version = EXPECTED_RELEASES[index]
            if rid != exp_id:
                errors.append(_error(scope, f"id must be {exp_id!r} at order {index + 1}"))
            if release.get("version") != exp_version:
                errors.append(_error(scope, f"version must be {exp_version!r}"))
        if release.get("order") != index + 1:
            errors.append(_error(scope, f"order must be {index + 1} (contiguous 1..N)"))
        status = release.get("status")
        if status not in RELEASE_STATUSES:
            errors.append(_error(scope, f"status must be one of {sorted(RELEASE_STATUSES)}"))
        errors.extend(_require_str(release, "title", scope))
        errors.extend(_require_str(release, "problem", scope))
        errors.extend(_require_str(release, "goal", scope))
        errors.extend(_require_str_list(release, "featureIds", scope, nonempty_list=True))
        errors.extend(_require_str_list(release, "learningDependencies", scope))
        errors.extend(_require_str_list(release, "acceptanceCriteria", scope, nonempty_list=True))
        errors.extend(_require_str_list(release, "buildTaskIds", scope))
        for fid in release.get("featureIds") or []:
            if fid not in feature_ids:
                errors.append(_error(scope, f"featureId {fid!r} does not resolve to a feature"))
    return release_ids


def _validate_features(features, seen_ids: dict, errors: list[str]) -> set:
    feature_ids: set = set()
    if not isinstance(features, list):
        errors.append(_error("features", "features must be a list"))
        return feature_ids
    for index, feature in enumerate(features):
        scope = f"feature[{index}]"
        if not isinstance(feature, dict):
            errors.append(_error(scope, "feature must be an object"))
            continue
        fid = feature.get("id")
        scope = f"feature {fid}" if isinstance(fid, str) and fid else scope
        errors.extend(_closed_keys(feature, FEATURE_KEYS, scope))
        errors.extend(_check_id(fid, scope, seen_ids, "feature"))
        if isinstance(fid, str) and fid:
            feature_ids.add(fid)
        errors.extend(_require_str(feature, "name", scope))
        errors.extend(_require_str(feature, "description", scope))
        errors.extend(_require_str_list(feature, "domainEntities", scope))
        errors.extend(_require_str(feature, "introducedInReleaseId", scope))
    return feature_ids


def _validate_build_tasks(build_tasks, release_ids, feature_ids, lesson_ids, seen_ids, errors) -> set:
    task_ids: set = set()
    if not isinstance(build_tasks, list):
        errors.append(_error("buildTasks", "buildTasks must be a list"))
        return task_ids
    for index, task in enumerate(build_tasks):
        scope = f"buildTask[{index}]"
        if not isinstance(task, dict):
            errors.append(_error(scope, "buildTask must be an object"))
            continue
        tid = task.get("id")
        scope = f"buildTask {tid}" if isinstance(tid, str) and tid else scope
        errors.extend(_closed_keys(task, BUILD_TASK_KEYS, scope))
        errors.extend(_check_id(tid, scope, seen_ids, "buildTask"))
        if isinstance(tid, str) and tid:
            task_ids.add(tid)
        errors.extend(_require_str(task, "title", scope))
        errors.extend(_require_str(task, "releaseId", scope))
        errors.extend(_require_str_list(task, "featureIds", scope, nonempty_list=True))
        errors.extend(_require_str(task, "problem", scope))
        errors.extend(_require_str(task, "goal", scope))
        errors.extend(_require_str_list(task, "constraints", scope))
        errors.extend(_require_str_list(task, "acceptanceCriteria", scope, nonempty_list=True))
        errors.extend(_require_str_list(task, "relevantLessonIds", scope, nonempty_list=True))
        if task.get("releaseId") not in release_ids:
            errors.append(_error(scope, f"releaseId {task.get('releaseId')!r} does not resolve to a release"))
        if not isinstance(task.get("required"), bool):
            errors.append(_error(scope, "required must be a boolean"))
        for fid in task.get("featureIds") or []:
            if fid not in feature_ids:
                errors.append(_error(scope, f"featureId {fid!r} does not resolve to a feature"))
        for lid in task.get("relevantLessonIds") or []:
            if lid not in lesson_ids:
                errors.append(_error(scope, f"relevantLessonId {lid!r} is not a known lesson"))
    return task_ids


def _validate_release_task_links(releases, build_tasks, task_ids, errors) -> None:
    if not isinstance(releases, list) or not isinstance(build_tasks, list):
        return
    tasks_by_id = {
        task.get("id"): task
        for task in build_tasks
        if isinstance(task, dict) and isinstance(task.get("id"), str)
    }
    listed_under: dict[str, str] = {}
    for release in releases:
        if not isinstance(release, dict):
            continue
        release_id = release.get("id")
        ordered_ids = release.get("buildTaskIds")
        if not isinstance(ordered_ids, list):
            continue
        seen_in_release: set[str] = set()
        for task_id in ordered_ids:
            if task_id in seen_in_release:
                errors.append(_error(
                    f"release {release_id}",
                    f"duplicate buildTaskId {task_id!r} in buildTaskIds ordering",
                ))
            seen_in_release.add(task_id)
            if task_id not in task_ids:
                errors.append(_error(
                    f"release {release_id}",
                    f"buildTaskId {task_id!r} does not resolve to a buildTask",
                ))
                continue
            previous_release = listed_under.get(task_id)
            if previous_release is not None and previous_release != release_id:
                errors.append(_error(
                    f"release {release_id}",
                    f"buildTaskId {task_id!r} is already listed by release {previous_release!r}",
                ))
            else:
                listed_under[task_id] = release_id
            owner = tasks_by_id[task_id].get("releaseId")
            if owner != release_id:
                errors.append(_error(
                    f"release {release_id}",
                    f"buildTaskId {task_id!r} has releaseId {owner!r}, expected {release_id!r}",
                ))

    for task_id, task in tasks_by_id.items():
        owner = task.get("releaseId")
        if listed_under.get(task_id) != owner:
            errors.append(_error(
                f"buildTask {task_id}",
                f"must appear exactly once in release {owner!r} buildTaskIds ordering",
            ))


def _validate_feature_release_links(features, release_ids, errors) -> None:
    if not isinstance(features, list):
        return
    for feature in features:
        if not isinstance(feature, dict):
            continue
        rid = feature.get("introducedInReleaseId")
        if rid not in release_ids:
            errors.append(_error(f"feature {feature.get('id')}", f"introducedInReleaseId {rid!r} does not resolve to a release"))


def _validate_milestones(milestones, release_ids, seen_ids, errors) -> None:
    if not isinstance(milestones, list):
        errors.append(_error("milestones", "milestones must be a list"))
        return
    for index, milestone in enumerate(milestones):
        scope = f"milestone[{index}]"
        if not isinstance(milestone, dict):
            errors.append(_error(scope, "milestone must be an object"))
            continue
        mid = milestone.get("id")
        scope = f"milestone {mid}" if isinstance(mid, str) and mid else scope
        errors.extend(_closed_keys(milestone, MILESTONE_KEYS, scope))
        errors.extend(_check_id(mid, scope, seen_ids, "milestone"))
        errors.extend(_require_str(milestone, "name", scope))
        errors.extend(_require_str(milestone, "summary", scope))
        release_id_list = milestone.get("releaseIds")
        if not isinstance(release_id_list, list) or not release_id_list:
            errors.append(_error(scope, "releaseIds must be a nonempty list"))
            release_id_list = []
        for rid in release_id_list:
            if rid not in release_ids:
                errors.append(_error(scope, f"releaseId {rid!r} does not resolve to a release"))


def _validate_arch_stages(stages, release_ids, seen_ids, errors) -> None:
    if not isinstance(stages, list):
        errors.append(_error("architectureStages", "architectureStages must be a list"))
        return
    for index, stage in enumerate(stages):
        scope = f"architectureStage[{index}]"
        if not isinstance(stage, dict):
            errors.append(_error(scope, "architectureStage must be an object"))
            continue
        sid = stage.get("id")
        scope = f"architectureStage {sid}" if isinstance(sid, str) and sid else scope
        errors.extend(_closed_keys(stage, ARCH_STAGE_KEYS, scope))
        errors.extend(_check_id(sid, scope, seen_ids, "architectureStage"))
        errors.extend(_require_str(stage, "releaseId", scope))
        errors.extend(_require_str(stage, "title", scope))
        errors.extend(_require_str_list(stage, "layers", scope, nonempty_list=True))
        errors.extend(_require_str(stage, "diagram", scope))
        errors.extend(_require_str(stage, "changesFromPrev", scope))
        errors.extend(_require_str(stage, "rationale", scope))
        if stage.get("releaseId") not in release_ids:
            errors.append(_error(scope, f"releaseId {stage.get('releaseId')!r} does not resolve to a release"))


def _validate_lesson_map(
    lesson_map, release_ids, feature_ids, task_ids, build_tasks, lesson_ids, errors
) -> None:
    if not isinstance(lesson_map, dict):
        errors.append(_error("lessonMap", "lessonMap must be an object keyed by lesson id"))
        return
    tasks_by_id = {
        task.get("id"): task
        for task in build_tasks or []
        if isinstance(task, dict) and isinstance(task.get("id"), str)
    }
    for lesson_id, entry in lesson_map.items():
        scope = f"lessonMap {lesson_id}"
        if lesson_id not in lesson_ids:
            errors.append(_error(scope, "key is not a known lesson id"))
        if not isinstance(entry, dict):
            errors.append(_error(scope, "entry must be an object"))
            continue
        errors.extend(_closed_keys(entry, LESSON_MAP_KEYS, scope))
        app_type = entry.get("applicationType")
        if app_type not in APPLICATION_TYPES:
            errors.append(_error(scope, f"applicationType must be one of {sorted(APPLICATION_TYPES)}"))
        errors.extend(_require_str(entry, "context", scope))
        if app_type in {"direct", "future"}:
            rid = entry.get("releaseId")
            if rid not in release_ids:
                errors.append(_error(scope, f"releaseId {rid!r} does not resolve to a release"))
            errors.extend(_require_str_list(entry, "featureIds", scope, nonempty_list=True))
            errors.extend(_require_str_list(entry, "buildTaskIds", scope))
            if app_type == "direct" or "projectProblem" in entry:
                errors.extend(_require_str(entry, "projectProblem", scope))
            errors.extend(_require_str(entry, "application", scope))
            for fid in entry.get("featureIds") or []:
                if fid not in feature_ids:
                    errors.append(_error(scope, f"featureId {fid!r} does not resolve to a feature"))
        entry_features = set(entry.get("featureIds") or [])
        for tid in entry.get("buildTaskIds") or []:
            if tid not in task_ids:
                errors.append(_error(scope, f"buildTaskId {tid!r} does not resolve to a buildTask"))
                continue
            task = tasks_by_id[tid]
            if task.get("releaseId") != entry.get("releaseId"):
                errors.append(_error(
                    scope,
                    f"buildTaskId {tid!r} has releaseId {task.get('releaseId')!r}, "
                    f"not lesson releaseId {entry.get('releaseId')!r}",
                ))
            missing_features = sorted(set(task.get("featureIds") or []) - entry_features)
            if missing_features:
                errors.append(_error(
                    scope,
                    f"featureIds must include task {tid!r} featureIds {missing_features}",
                ))


def validate_project(project: dict, *, valid_lesson_ids: set | None = None) -> list[str]:
    """Validate a Spendwise project artifact. Returns a list of error strings."""
    errors: list[str] = []
    lesson_ids = valid_lesson_ids if valid_lesson_ids is not None else set(LESSON_IDS)

    if not isinstance(project, dict):
        return [_error("project", "project artifact must be a JSON object")]

    errors.extend(_closed_keys(project, TOP_LEVEL_KEYS, "project"))
    if project.get("schemaVersion") != 1:
        errors.append(_error("project", "schemaVersion must equal 1"))

    seen_ids: dict = {}
    _validate_product(project.get("product"), seen_ids, errors)
    feature_ids = _validate_features(project.get("features"), seen_ids, errors)
    release_ids = _validate_releases(
        project.get("releases"), feature_ids, seen_ids, errors
    )
    _validate_feature_release_links(project.get("features"), release_ids, errors)
    build_tasks = project.get("buildTasks")
    task_ids = _validate_build_tasks(
        build_tasks, release_ids, feature_ids, lesson_ids, seen_ids, errors
    )
    _validate_release_task_links(
        project.get("releases"), build_tasks, task_ids, errors
    )
    _validate_milestones(project.get("milestones"), release_ids, seen_ids, errors)
    _validate_arch_stages(project.get("architectureStages"), release_ids, seen_ids, errors)
    _validate_lesson_map(
        project.get("lessonMap"), release_ids, feature_ids, task_ids,
        build_tasks, lesson_ids, errors
    )
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate the Spendwise project data artifact")
    parser.add_argument("--project", default="content/spendwise-project.json", type=Path)
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    try:
        project = json.loads(Path(args.project).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(_error("project", f"could not read {args.project}: {error}"))
        return 2

    errors = sorted(validate_project(project))
    if errors:
        for error in errors:
            print(error)
        return 1

    print(
        f"PASS releases={len(project.get('releases', []))} "
        f"features={len(project.get('features', []))} "
        f"buildTasks={len(project.get('buildTasks', []))} "
        f"lessonMap={len(project.get('lessonMap', {}))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
