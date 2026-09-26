"""Validate content/spendwise-guided-build.json: the Guided Rebuild instructional layer.

Guided Rebuild answers HOW a beginner learns to build what content/spendwise-project.json says
MUST be built. This validator enforces the same closed-schema, referential-integrity discipline as
tools/validate_project.py — and reuses that module's generic helpers directly (_closed_keys,
_check_id, _require_str, _require_str_list, _is_known, _error, ID_RE, LESSON_IDS) rather than
duplicating them, since the two artifacts share one id/schema discipline and the helpers have no
project-specific behavior baked in.

It enforces:

- a closed schema at every nesting level (unknown keys FAIL);
- one guided-id namespace, URL-safe and globally unique (guidedCourse.id, every guidedSession.id,
  guidedStep.id, guidedCheckpoint.id);
- exactly one guidedReleases row per canonical release (content/spendwise-project.json's 10-release
  spine) with authoringStatus in {planned, authored};
- guidedSession.releaseId/.buildTaskId resolve, and the canonical buildTask's releaseId must equal
  the session's releaseId (no cross-release session);
- guidedStep.sessionId resolves; a non-null buildStepId must resolve to a canonical buildStep whose
  taskId equals the owning session's buildTaskId (no cross-task step);
- session order contiguous 1..N per release, step order contiguous 1..N per session;
- a planned release has zero guidedSessions; an authored release has >=1 guidedSession and passes
  the GENERIC completeness gate: every required canonical buildTask in that release is covered by
  >=1 guidedSession, and every canonical buildStep belonging to each such task is covered by >=1
  guidedStep with a matching buildStepId. This rule is not hardcoded to V0.1 — it applies the
  moment any release is marked authored;
- exactly one guidedCheckpoint per guidedSession;
- theoryBridge[].lessonId resolves against the canonical lesson id list;
- type-specific rules: your-turn requires learnerAction, every other type forbids it; run and
  commonErrors sub-fields, when present, are non-empty.

Returns "ERROR ..." strings the same way validate_project.py does; an empty list means the artifact
is valid. A guided artifact can only be meaningfully checked against a VALID canonical project, so
validate_guided_build() takes the already-loaded canonical project dict as an argument rather than
re-reading a file, keeping it testable against small synthetic canonical fixtures.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:  # package import when run via pytest/`-m` (repo root on path)
    from tools.validate_project import (
        ID_RE,  # noqa: F401 (re-exported for callers/tests that want it from here)
        LESSON_IDS,
        _check_id,
        _closed_keys,
        _error,
        _is_known,
        _require_str,
        _require_str_list,
    )
    from tools.validate_project import validate_project as validate_canonical_project
except ImportError:  # script import when run as `python tools/validate_guided_build.py`
    from validate_project import (
        ID_RE,  # noqa: F401
        LESSON_IDS,
        _check_id,
        _closed_keys,
        _error,
        _is_known,
        _require_str,
        _require_str_list,
    )
    from validate_project import validate_project as validate_canonical_project

TOP_LEVEL_KEYS = {
    "schemaVersion", "guidedCourse", "guidedReleases", "guidedSessions",
    "guidedSteps", "guidedCheckpoints",
}
GUIDED_COURSE_KEYS = {"id", "title", "workspaceExample", "referenceWorkspaceExample"}
GUIDED_RELEASE_KEYS = {"releaseId", "authoringStatus"}
GUIDED_SESSION_KEYS = {"id", "releaseId", "buildTaskId", "order", "title", "goal", "projectNow", "sessionAdds"}
GUIDED_STEP_REQUIRED_KEYS = {"id", "sessionId", "order", "buildStepId", "type", "title", "goal"}
GUIDED_STEP_OPTIONAL_KEYS = {
    "whyThisMatters", "theoryBridge", "instructions", "codeBlocks", "learnerAction",
    "commonErrors", "run", "reveal", "projectStateBefore", "projectStateAfter", "selfCheck",
}
GUIDED_STEP_KEYS = GUIDED_STEP_REQUIRED_KEYS | GUIDED_STEP_OPTIONAL_KEYS
THEORY_BRIDGE_KEYS = {"lessonId", "note"}
CODE_BLOCK_REQUIRED_KEYS = {"language", "code"}
CODE_BLOCK_KEYS = CODE_BLOCK_REQUIRED_KEYS | {"caption", "explanation"}
LEARNER_ACTION_KEYS = {"goal", "constraints", "hints"}
COMMON_ERROR_KEYS = {"symptom", "likelyCause", "fix"}
RUN_KEYS = {"cwd", "command", "expectedResult", "explanation"}
REVEAL_KEYS = {"label", "content"}
SELF_CHECK_KEYS = {"question", "answer"}
GUIDED_CHECKPOINT_REQUIRED_KEYS = {"id", "sessionId", "expectedFiles", "understanding", "whatYouBuilt"}
GUIDED_CHECKPOINT_OPTIONAL_KEYS = {"expectedProjectTree", "whyNotYet"}
GUIDED_CHECKPOINT_KEYS = GUIDED_CHECKPOINT_REQUIRED_KEYS | GUIDED_CHECKPOINT_OPTIONAL_KEYS

STEP_TYPES = {
    "orientation", "setup", "create-folder", "create-file", "code-with-me",
    "your-turn", "explanation", "run", "checkpoint", "debug", "review",
}
AUTHORING_STATUSES = {"planned", "authored"}


def _canonical_release_ids(project: dict) -> set:
    releases = project.get("releases")
    if not isinstance(releases, list):
        return set()
    return {r["id"] for r in releases if isinstance(r, dict) and isinstance(r.get("id"), str)}


def _canonical_tasks(project: dict) -> dict:
    """taskId -> {"releaseId": ..., "required": bool}, tolerant of malformed input."""
    tasks = project.get("buildTasks")
    out: dict = {}
    if not isinstance(tasks, list):
        return out
    for task in tasks:
        if isinstance(task, dict) and isinstance(task.get("id"), str):
            out[task["id"]] = {
                "releaseId": task.get("releaseId"),
                "required": task.get("required") is True,
            }
    return out


def _canonical_step_task_ids(project: dict) -> dict:
    """buildStepId -> taskId, tolerant of malformed/absent input."""
    steps = project.get("buildSteps")
    out: dict = {}
    if not isinstance(steps, list):
        return out
    for step in steps:
        if isinstance(step, dict) and isinstance(step.get("id"), str) and isinstance(step.get("taskId"), str):
            out[step["id"]] = step["taskId"]
    return out


def _steps_by_task(project: dict) -> dict:
    """taskId -> set(buildStepId), from the canonical (optional) buildSteps array."""
    out: dict = {}
    for step_id, task_id in _canonical_step_task_ids(project).items():
        out.setdefault(task_id, set()).add(step_id)
    return out


def _validate_guided_course(course, seen_ids: dict, errors: list[str]) -> None:
    scope = "guidedCourse"
    if not isinstance(course, dict):
        errors.append(_error(scope, "guidedCourse must be an object"))
        return
    errors.extend(_closed_keys(course, GUIDED_COURSE_KEYS, scope))
    errors.extend(_check_id(course.get("id"), scope, seen_ids, "guidedCourse"))
    for key in ("title", "workspaceExample", "referenceWorkspaceExample"):
        errors.extend(_require_str(course, key, scope))


def _validate_guided_releases(guided_releases, canonical_release_ids: set, errors: list[str]) -> dict:
    """Returns {releaseId: authoringStatus} for every well-formed row."""
    status_by_release: dict = {}
    if not isinstance(guided_releases, list):
        errors.append(_error("guidedReleases", "guidedReleases must be a list"))
        return status_by_release

    seen_release_ids: set = set()
    for index, row in enumerate(guided_releases):
        scope = f"guidedRelease[{index}]"
        if not isinstance(row, dict):
            errors.append(_error(scope, "guidedRelease must be an object"))
            continue
        rid = row.get("releaseId")
        scope = f"guidedRelease {rid}" if isinstance(rid, str) and rid else scope
        errors.extend(_closed_keys(row, GUIDED_RELEASE_KEYS, scope))
        if not _is_known(rid, canonical_release_ids):
            errors.append(_error(scope, f"releaseId {rid!r} does not resolve to a canonical release"))
        elif rid in seen_release_ids:
            errors.append(_error(scope, f"duplicate guidedRelease entry for releaseId {rid!r}"))
        else:
            seen_release_ids.add(rid)
        status = row.get("authoringStatus")
        if not _is_known(status, AUTHORING_STATUSES):
            errors.append(_error(scope, f"authoringStatus must be one of {sorted(AUTHORING_STATUSES)}"))
        elif isinstance(rid, str) and rid:
            status_by_release[rid] = status

    missing = sorted(canonical_release_ids - seen_release_ids)
    if missing:
        errors.append(_error("guidedReleases", f"missing guidedRelease entry for release(s) {missing}"))
    return status_by_release


def _validate_guided_sessions(sessions, release_status: dict, canonical_tasks: dict, seen_ids: dict, errors: list[str]) -> dict:
    """Returns {sessionId: session_dict} for every well-formed session."""
    sessions_by_id: dict = {}
    if not isinstance(sessions, list):
        errors.append(_error("guidedSessions", "guidedSessions must be a list"))
        return sessions_by_id

    orders_by_release: dict = {}
    for index, session in enumerate(sessions):
        scope = f"guidedSession[{index}]"
        if not isinstance(session, dict):
            errors.append(_error(scope, "guidedSession must be an object"))
            continue
        sid = session.get("id")
        scope = f"guidedSession {sid}" if isinstance(sid, str) and sid else scope
        errors.extend(_closed_keys(session, GUIDED_SESSION_KEYS, scope))
        errors.extend(_check_id(sid, scope, seen_ids, "guidedSession"))
        errors.extend(_require_str(session, "title", scope))
        errors.extend(_require_str(session, "goal", scope))
        for key in ("projectNow", "sessionAdds"):
            if key in session:
                errors.extend(_require_str(session, key, scope))

        release_id = session.get("releaseId")
        task_id = session.get("buildTaskId")
        if not _is_known(release_id, set(release_status)):
            errors.append(_error(scope, f"releaseId {release_id!r} does not resolve to a guidedRelease"))
        if not _is_known(task_id, set(canonical_tasks)):
            errors.append(_error(scope, f"buildTaskId {task_id!r} does not resolve to a canonical buildTask"))
        elif isinstance(release_id, str):
            task_release = canonical_tasks[task_id]["releaseId"]
            if task_release != release_id:
                errors.append(_error(
                    scope,
                    f"buildTaskId {task_id!r} belongs to release {task_release!r}, "
                    f"not this session's releaseId {release_id!r}",
                ))
        if release_status.get(release_id) == "planned":
            errors.append(_error(scope, f"release {release_id!r} is authoringStatus=planned and must have zero guidedSessions"))

        order = session.get("order")
        if isinstance(order, bool) or not isinstance(order, int):
            errors.append(_error(scope, "order must be an integer"))
        elif isinstance(release_id, str):
            orders_by_release.setdefault(release_id, []).append(order)

        if isinstance(sid, str) and sid:
            sessions_by_id[sid] = session

    for release_id, orders in sorted(orders_by_release.items()):
        expected = list(range(1, len(orders) + 1))
        if sorted(orders) != expected:
            errors.append(_error(
                f"guidedRelease {release_id}",
                f"guidedSession order must be contiguous 1..{len(orders)}, found {sorted(orders)}",
            ))

    return sessions_by_id


def _validate_theory_bridge(entries, scope: str, errors: list[str]) -> None:
    if not isinstance(entries, list):
        errors.append(_error(scope, "theoryBridge must be a list"))
        return
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append(_error(scope, "theoryBridge entry must be an object"))
            continue
        errors.extend(_closed_keys(entry, THEORY_BRIDGE_KEYS, scope))
        errors.extend(_require_str(entry, "note", scope))
        lesson_id = entry.get("lessonId")
        if not _is_known(lesson_id, set(LESSON_IDS)):
            errors.append(_error(scope, f"theoryBridge lessonId {lesson_id!r} is not a known lesson"))


def _validate_code_blocks(blocks, scope: str, errors: list[str]) -> None:
    if not isinstance(blocks, list):
        errors.append(_error(scope, "codeBlocks must be a list"))
        return
    for block in blocks:
        if not isinstance(block, dict):
            errors.append(_error(scope, "codeBlock must be an object"))
            continue
        errors.extend(_closed_keys(block, CODE_BLOCK_KEYS, scope))
        for key in CODE_BLOCK_REQUIRED_KEYS:
            errors.extend(_require_str(block, key, scope))
        for key in ("caption", "explanation"):
            if key in block:
                errors.extend(_require_str(block, key, scope))


def _validate_learner_action(action, scope: str, errors: list[str]) -> None:
    if not isinstance(action, dict):
        errors.append(_error(scope, "learnerAction must be an object"))
        return
    errors.extend(_closed_keys(action, LEARNER_ACTION_KEYS, scope))
    errors.extend(_require_str(action, "goal", scope))
    for key in ("constraints", "hints"):
        if key in action:
            errors.extend(_require_str_list(action, key, scope))


def _validate_common_errors(entries, scope: str, errors: list[str]) -> None:
    if not isinstance(entries, list):
        errors.append(_error(scope, "commonErrors must be a list"))
        return
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append(_error(scope, "commonError must be an object"))
            continue
        errors.extend(_closed_keys(entry, COMMON_ERROR_KEYS, scope))
        for key in COMMON_ERROR_KEYS:
            errors.extend(_require_str(entry, key, scope))


def _validate_run(run, scope: str, errors: list[str]) -> None:
    if not isinstance(run, dict):
        errors.append(_error(scope, "run must be an object"))
        return
    errors.extend(_closed_keys(run, RUN_KEYS, scope))
    for key in RUN_KEYS:
        errors.extend(_require_str(run, key, scope))


def _validate_reveal(reveal, scope: str, errors: list[str]) -> None:
    if not isinstance(reveal, dict):
        errors.append(_error(scope, "reveal must be an object"))
        return
    errors.extend(_closed_keys(reveal, REVEAL_KEYS, scope))
    for key in REVEAL_KEYS:
        errors.extend(_require_str(reveal, key, scope))


def _validate_self_check(entries, scope: str, errors: list[str]) -> None:
    if not isinstance(entries, list) or not 1 <= len(entries) <= 4:
        errors.append(_error(scope, "selfCheck must be a list of 1-4 entries"))
        return
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append(_error(scope, "selfCheck entry must be an object"))
            continue
        errors.extend(_closed_keys(entry, SELF_CHECK_KEYS, scope))
        for key in SELF_CHECK_KEYS:
            errors.extend(_require_str(entry, key, scope))


def _validate_guided_steps(steps, sessions_by_id: dict, canonical_step_task_ids: dict, seen_ids: dict, errors: list[str]) -> list:
    """Returns the list of well-formed step dicts (for completeness computation)."""
    valid_steps: list = []
    if not isinstance(steps, list):
        errors.append(_error("guidedSteps", "guidedSteps must be a list"))
        return valid_steps

    orders_by_session: dict = {}
    for index, step in enumerate(steps):
        scope = f"guidedStep[{index}]"
        if not isinstance(step, dict):
            errors.append(_error(scope, "guidedStep must be an object"))
            continue
        stid = step.get("id")
        scope = f"guidedStep {stid}" if isinstance(stid, str) and stid else scope
        errors.extend(_closed_keys(step, GUIDED_STEP_KEYS, scope))
        errors.extend(_check_id(stid, scope, seen_ids, "guidedStep"))
        missing = sorted(GUIDED_STEP_REQUIRED_KEYS - set(step))
        if missing:
            errors.append(_error(scope, f"missing required key(s) {missing}"))
        errors.extend(_require_str(step, "title", scope))
        errors.extend(_require_str(step, "goal", scope))

        step_type = step.get("type")
        if not _is_known(step_type, STEP_TYPES):
            errors.append(_error(scope, f"type must be one of {sorted(STEP_TYPES)}"))

        session_id = step.get("sessionId")
        session = sessions_by_id.get(session_id) if isinstance(session_id, str) else None
        if session is None:
            errors.append(_error(scope, f"sessionId {session_id!r} does not resolve to a guidedSession"))

        build_step_id = step.get("buildStepId")
        if "buildStepId" not in step:
            pass  # already reported by the missing-required-key check above
        elif build_step_id is not None:
            if not isinstance(build_step_id, str) or build_step_id not in canonical_step_task_ids:
                errors.append(_error(scope, f"buildStepId {build_step_id!r} does not resolve to a canonical buildStep"))
            elif session is not None:
                owning_task = session.get("buildTaskId")
                step_task = canonical_step_task_ids[build_step_id]
                if step_task != owning_task:
                    errors.append(_error(
                        scope,
                        f"buildStepId {build_step_id!r} belongs to buildTask {step_task!r}, "
                        f"not this step's session buildTask {owning_task!r}",
                    ))

        for optional_key, validator in (
            ("theoryBridge", _validate_theory_bridge),
            ("codeBlocks", _validate_code_blocks),
            ("commonErrors", _validate_common_errors),
            ("selfCheck", _validate_self_check),
        ):
            if optional_key in step:
                validator(step.get(optional_key), scope, errors)
        if "instructions" in step:
            errors.extend(_require_str_list(step, "instructions", scope, nonempty_list=True))
        if "run" in step:
            _validate_run(step.get("run"), scope, errors)
        if "reveal" in step:
            _validate_reveal(step.get("reveal"), scope, errors)
        for key in ("whyThisMatters", "projectStateBefore", "projectStateAfter"):
            if key in step:
                errors.extend(_require_str(step, key, scope))

        if step_type == "your-turn":
            if "learnerAction" not in step:
                errors.append(_error(scope, "type=your-turn requires learnerAction"))
            else:
                _validate_learner_action(step.get("learnerAction"), scope, errors)
        elif "learnerAction" in step:
            errors.append(_error(scope, f"learnerAction is only allowed when type=your-turn (type={step_type!r})"))

        order = step.get("order")
        if isinstance(order, bool) or not isinstance(order, int):
            errors.append(_error(scope, "order must be an integer"))
        elif isinstance(session_id, str):
            orders_by_session.setdefault(session_id, []).append(order)

        if isinstance(stid, str) and stid:
            valid_steps.append(step)

    for session_id, orders in sorted(orders_by_session.items()):
        expected = list(range(1, len(orders) + 1))
        if sorted(orders) != expected:
            errors.append(_error(
                f"guidedSession {session_id}",
                f"guidedStep order must be contiguous 1..{len(orders)}, found {sorted(orders)}",
            ))

    return valid_steps


def _validate_guided_checkpoints(checkpoints, sessions_by_id: dict, seen_ids: dict, errors: list[str]) -> None:
    if not isinstance(checkpoints, list):
        errors.append(_error("guidedCheckpoints", "guidedCheckpoints must be a list"))
        return

    count_by_session: dict = {}
    for index, checkpoint in enumerate(checkpoints):
        scope = f"guidedCheckpoint[{index}]"
        if not isinstance(checkpoint, dict):
            errors.append(_error(scope, "guidedCheckpoint must be an object"))
            continue
        cid = checkpoint.get("id")
        scope = f"guidedCheckpoint {cid}" if isinstance(cid, str) and cid else scope
        errors.extend(_closed_keys(checkpoint, GUIDED_CHECKPOINT_KEYS, scope))
        errors.extend(_check_id(cid, scope, seen_ids, "guidedCheckpoint"))
        missing = sorted(GUIDED_CHECKPOINT_REQUIRED_KEYS - set(checkpoint))
        if missing:
            errors.append(_error(scope, f"missing required key(s) {missing}"))
        errors.extend(_require_str_list(checkpoint, "expectedFiles", scope, nonempty_list=True))
        errors.extend(_require_str_list(checkpoint, "understanding", scope, nonempty_list=True))
        errors.extend(_require_str(checkpoint, "whatYouBuilt", scope))
        if "expectedProjectTree" in checkpoint:
            errors.extend(_require_str(checkpoint, "expectedProjectTree", scope))
        if "whyNotYet" in checkpoint:
            errors.extend(_require_str_list(checkpoint, "whyNotYet", scope, nonempty_list=True))

        session_id = checkpoint.get("sessionId")
        if session_id not in sessions_by_id:
            errors.append(_error(scope, f"sessionId {session_id!r} does not resolve to a guidedSession"))
        elif isinstance(session_id, str):
            count_by_session[session_id] = count_by_session.get(session_id, 0) + 1

    for session_id in sessions_by_id:
        count = count_by_session.get(session_id, 0)
        if count == 0:
            errors.append(_error(f"guidedSession {session_id}", "authored session has no guidedCheckpoint"))
        elif count > 1:
            errors.append(_error(f"guidedSession {session_id}", f"has {count} guidedCheckpoints, expected exactly 1"))


def _validate_completeness(release_status: dict, sessions_by_id: dict, valid_steps: list, canonical_tasks: dict, steps_by_task: dict, errors: list[str]) -> None:
    sessions_for_release: dict = {}
    covered_tasks: dict = {}
    for session in sessions_by_id.values():
        rid = session.get("releaseId")
        tid = session.get("buildTaskId")
        if isinstance(rid, str):
            sessions_for_release.setdefault(rid, []).append(session)
            if isinstance(tid, str):
                covered_tasks.setdefault(rid, set()).add(tid)

    covered_steps_by_task: dict = {}
    for step in valid_steps:
        session = sessions_by_id.get(step.get("sessionId"))
        build_step_id = step.get("buildStepId")
        if session is None or not isinstance(build_step_id, str):
            continue
        task_id = session.get("buildTaskId")
        if isinstance(task_id, str):
            covered_steps_by_task.setdefault(task_id, set()).add(build_step_id)

    for release_id, status in sorted(release_status.items()):
        if status != "authored":
            continue
        scope = f"guidedRelease {release_id}"
        if not sessions_for_release.get(release_id):
            errors.append(_error(scope, "authoringStatus=authored requires at least one guidedSession"))
            continue

        required_tasks = {
            tid for tid, info in canonical_tasks.items()
            if info["releaseId"] == release_id and info["required"]
        }
        missing_tasks = sorted(required_tasks - covered_tasks.get(release_id, set()))
        if missing_tasks:
            errors.append(_error(scope, f"missing guidedSession coverage for required buildTask(s) {missing_tasks}"))

        for task_id in sorted(required_tasks):
            required_steps = steps_by_task.get(task_id, set())
            missing_steps = sorted(required_steps - covered_steps_by_task.get(task_id, set()))
            if missing_steps:
                errors.append(_error(scope, f"buildTask {task_id!r} missing guidedStep coverage for buildStep(s) {missing_steps}"))


def validate_guided_build(guided: dict, project: dict) -> list[str]:
    """Validate a Guided Rebuild artifact against an already-validated canonical project dict.

    Returns a list of "ERROR ..." strings; an empty list means the artifact is valid.
    """
    errors: list[str] = []

    if not isinstance(guided, dict):
        return [_error("guidedBuild", "guided artifact must be a JSON object")]

    errors.extend(_closed_keys(guided, TOP_LEVEL_KEYS, "guidedBuild"))
    if guided.get("schemaVersion") != 1:
        errors.append(_error("guidedBuild", "schemaVersion must equal 1"))

    seen_ids: dict = {}
    _validate_guided_course(guided.get("guidedCourse"), seen_ids, errors)

    canonical_release_ids = _canonical_release_ids(project)
    canonical_tasks = _canonical_tasks(project)
    canonical_step_task_ids = _canonical_step_task_ids(project)
    steps_by_task = _steps_by_task(project)

    release_status = _validate_guided_releases(guided.get("guidedReleases"), canonical_release_ids, errors)
    sessions_by_id = _validate_guided_sessions(
        guided.get("guidedSessions"), release_status, canonical_tasks, seen_ids, errors
    )
    valid_steps = _validate_guided_steps(
        guided.get("guidedSteps"), sessions_by_id, canonical_step_task_ids, seen_ids, errors
    )
    _validate_guided_checkpoints(guided.get("guidedCheckpoints"), sessions_by_id, seen_ids, errors)
    _validate_completeness(release_status, sessions_by_id, valid_steps, canonical_tasks, steps_by_task, errors)

    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate the Spendwise Guided Rebuild data artifact")
    parser.add_argument("--project", default="content/spendwise-project.json", type=Path)
    parser.add_argument("--guided", default="content/spendwise-guided-build.json", type=Path)
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    try:
        project = json.loads(Path(args.project).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(_error("project", f"could not read {args.project}: {error}"))
        return 2
    try:
        guided = json.loads(Path(args.guided).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(_error("guidedBuild", f"could not read {args.guided}: {error}"))
        return 2

    canonical_errors = sorted(validate_canonical_project(project))
    if canonical_errors:
        for error in canonical_errors:
            print(error)
        return 1

    errors = sorted(validate_guided_build(guided, project))
    if errors:
        for error in errors:
            print(error)
        return 1

    print(
        f"PASS guidedReleases={len(guided.get('guidedReleases', []))} "
        f"guidedSessions={len(guided.get('guidedSessions', []))} "
        f"guidedSteps={len(guided.get('guidedSteps', []))} "
        f"guidedCheckpoints={len(guided.get('guidedCheckpoints', []))}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
