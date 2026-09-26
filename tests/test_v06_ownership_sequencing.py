"""Regression guards for the V0.6 ownership-sequencing repair (course commit 3e3ada2).

These pin the specific defect fixed in step-v06-auth-hash: V4__user_identity.sql makes
accounts.user_id/transactions.user_id NOT NULL, and the same learner-visible step must
teach enough Java-side ownership mapping to keep the project executable — it must never
defer that wiring to a later session while the NOT NULL constraint is already active.
See docs/report/2026-09-24-spendwise-v06-ownership-sequencing-repair.md for the full
repair rationale.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDED_PATH = ROOT / "content" / "spendwise-guided-build.json"
PRE_REPAIR_COMMIT = "f8ccecdfeab16710bcf0e2bb4284aab6c1e695bf"
PREFIX_RELEASES = {"v0-1", "v0-2", "v0-3", "v0-4", "v0-5"}


def _guided() -> dict:
    return json.loads(GUIDED_PATH.read_text(encoding="utf-8"))


def _guided_step(step_id: str) -> dict:
    return next(s for s in _guided()["guidedSteps"] if s["id"] == step_id)


def _text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_text(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(_text(item) for item in value.values())
    return ""


def _step_text(step_id: str) -> str:
    return _text(_guided_step(step_id))


# --- A: activating NOT NULL ownership columns without also teaching Java mapping ---

def test_v4_not_null_activation_step_does_not_defer_java_ownership_mapping() -> None:
    text = _step_text("step-v06-auth-hash")

    assert "user_id UUID NOT NULL REFERENCES users(id)" in text

    # The exact defect this repair removed: a step that activates NOT NULL ownership
    # columns while explicitly punting the Java-side assignment to a later session.
    deferral_phrase = "là việc của task-user-migration kế tiếp; ở bước này chỉ cần cột và FK đã tồn tại"
    assert deferral_phrase not in text

    # The same step must itself teach the Java-side assignment (see B/C below) — this
    # test only pins that the deferral language is gone; B/C pin what replaced it.


# --- B: Account gets a direct, non-null owner mapping in the activating step ---

def test_account_gets_direct_owner_mapping_in_the_v4_activating_step() -> None:
    text = _step_text("step-v06-auth-hash")

    assert "Account(UUID ownerId" in text
    assert 'private UUID ownerId' in text
    assert "ownerId()" in text
    assert "DomainException" in text
    assert "account owner is required" in text.replace("\\", "")


# --- C: Transaction's owner is copied from its Account, not inferred via a join ---

def test_transaction_owner_is_copied_from_account_not_derived_via_join() -> None:
    text = _step_text("step-v06-auth-hash")

    assert "this.ownerId = account.ownerId();" in text
    assert "R25" in text
    # explicit anti-join framing must survive, worded either way this repair or a
    # future edit might phrase it
    assert ("không suy ra qua join" in text) or ("không suy ra qua account_id" in text)


# --- D: no fake/default/system owner is ever taught ---

def test_no_fake_or_default_or_system_owner_is_taught() -> None:
    text = _step_text("step-v06-auth-hash")

    assert "owner mặc định" in text or "owner mặc định/hệ thống" in text
    common_error_texts = [_text(e) for e in _guided_step("step-v06-auth-hash")["commonErrors"]]
    assert any("mặc định" in t and "owner" in t.lower() for t in common_error_texts)


# --- E: disposable-DB reset guidance is distinct from valuable-data fail-fast guidance ---

def test_disposable_db_reset_is_distinct_from_valuable_data_fail_fast() -> None:
    text = _step_text("step-v06-auth-hash")

    assert "TRUNCATE TABLE transactions, accounts;" in text
    assert "KHÔNG được TRUNCATE" in text
    assert "RAISE EXCEPTION" in text
    # both branches must be present in the same step, not just one of them
    disposable_marker = "database local là loại phát triển/test"
    valuable_marker = "database chứa dữ liệu thật"
    assert disposable_marker in text
    assert valuable_marker in text


# --- F: V0.1-V0.5 technical skeleton is unchanged from baseline ---
# The teaching-experience redesign (2026-09-25) legitimately rewrites V0.1-V0.5
# PROSE (diacritics, selfCheck, commonErrors, run explanations, story fields),
# so this guard pins only what the learner executes or the build keys on: ids,
# order, type, canonical build-step join, run command/cwd, code, and the
# checkpoint file lists. Any of those drifting is still a failure.

STEP_SKELETON = ("id", "sessionId", "order", "buildStepId", "type")
SESSION_SKELETON = ("id", "releaseId", "buildTaskId", "order")


def _step_skeleton(step: dict) -> dict:
    out = {k: step.get(k) for k in STEP_SKELETON}
    run = step.get("run") or {}
    out["run"] = {k: run.get(k) for k in ("command", "cwd")} if run else None
    out["code"] = [(b["language"], b["code"]) for b in step.get("codeBlocks", [])]
    return out


def _prefix_slices(data: dict) -> dict:
    session_ids = {
        s["id"] for s in data["guidedSessions"] if s["releaseId"] in PREFIX_RELEASES
    }
    return {
        "releases": [r for r in data["guidedReleases"] if r["releaseId"] in PREFIX_RELEASES],
        "sessions": [
            {k: s.get(k) for k in SESSION_SKELETON}
            for s in data["guidedSessions"] if s["releaseId"] in PREFIX_RELEASES
        ],
        "steps": [_step_skeleton(s) for s in data["guidedSteps"] if s["sessionId"] in session_ids],
        "checkpoints": [
            {k: c.get(k) for k in ("id", "sessionId", "expectedFiles", "expectedProjectTree")}
            for c in data.get("guidedCheckpoints", []) if c.get("sessionId") in session_ids
        ],
    }


def test_v01_to_v05_prefix_skeleton_is_identical_to_baseline() -> None:
    baseline_raw = subprocess.check_output(
        ["git", "show", f"{PRE_REPAIR_COMMIT}:content/spendwise-guided-build.json"],
        cwd=ROOT,
    ).decode("utf-8")
    baseline = _prefix_slices(json.loads(baseline_raw))
    current = _prefix_slices(_guided())

    for key in ("releases", "sessions", "steps", "checkpoints"):
        assert json.dumps(baseline[key], sort_keys=True, ensure_ascii=False) == json.dumps(
            current[key], sort_keys=True, ensure_ascii=False
        ), f"V0.1-V0.5 {key} drifted from baseline {PRE_REPAIR_COMMIT}"

    assert len(baseline["releases"]) == 5
    assert len(baseline["sessions"]) == 25
    assert len(baseline["steps"]) == 90
    assert len(baseline["checkpoints"]) == 25
