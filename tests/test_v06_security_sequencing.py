"""Regression guards for the V0.6 auth-foundation step-1/step-2 sequencing repair.

Pins two defects found by literally executing step-v06-auth-hash and step-v06-auth-filterchain
against a real probe (D:\\spendwise-v06-final-repair-probe):

1. step-v06-auth-hash used to require the ENTIRE Maven suite green before considering itself
   done. That's wrong: adding spring-boot-starter-security (this step's own instruction 1)
   activates Spring Boot's default security auto-configuration and makes TransactionValidationTest
   (the only real MockMvc/HTTP test in the project) return 403 — a break that step-v06-auth-hash
   has no way to fix, because SecurityFilterChain is deliberately taught one step later, in
   step-v06-auth-filterchain. The old gate turned an expected, by-design intermediate state into
   an apparent failure with no instructed fix.
2. step-v06-auth-filterchain used to name TransactionControllerTest, AccountControllerTest, and
   CategoryControllerTest as MockMvc tests needing a jwt() fix. Empirically (read from the probe's
   actual test sources), only TransactionValidationTest uses MockMvc; TransactionControllerTest and
   AccountControllerTest call the controller directly in plain Java; CategoryControllerTest does
   not exist in the codebase at all.

See docs/report/2026-09-24-spendwise-v06-security-sequencing-repair.md for the full rationale,
including the literal step-2 dry-run proving `.with(jwt())` alone (no CSRF-disable) is sufficient.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDED_PATH = ROOT / "content" / "spendwise-guided-build.json"
PRE_REPAIR_COMMIT = "e326d71784b0b2cf3279ac5b91154ff2b5678df0"


def _guided(data: dict | None = None) -> dict:
    if data is not None:
        return data
    return json.loads(GUIDED_PATH.read_text(encoding="utf-8"))


def _guided_step(step_id: str, data: dict | None = None) -> dict:
    return next(s for s in _guided(data)["guidedSteps"] if s["id"] == step_id)


def _text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_text(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(_text(item) for item in value.values())
    return ""


def _step_text(step_id: str, data: dict | None = None) -> str:
    return _text(_guided_step(step_id, data))


def _baseline() -> dict:
    raw = subprocess.check_output(
        ["git", "show", f"{PRE_REPAIR_COMMIT}:content/spendwise-guided-build.json"],
        cwd=ROOT,
    ).decode("utf-8")
    return json.loads(raw)


OLD_FULL_SUITE_GATE = (
    "toàn bộ suite, không chỉ AppUserServiceTest"
)
OLD_FALSE_TEST_CLAIM = "CategoryControllerTest"


# --- A: step 1 no longer gates on the full suite; the old phrasing is gone ---

def test_step1_full_suite_gate_removed() -> None:
    text = _step_text("step-v06-auth-hash")
    assert OLD_FULL_SUITE_GATE not in text

    # confirm this was genuinely a defect at the pre-repair baseline (RED reproduction)
    baseline_text = _step_text("step-v06-auth-hash", _baseline())
    assert OLD_FULL_SUITE_GATE in baseline_text


# --- B: step 1 instead names the actual, real, non-HTTP persistence tests ---

def test_step1_names_focused_persistence_tests() -> None:
    text = _step_text("step-v06-auth-hash")
    for class_name in (
        "AppUserServiceTest",
        "AccountJpaTest",
        "TransactionRepositoryTest",
        "BalanceReconciliationTest",
        "TransferServiceTest",
    ):
        assert class_name in text


# --- C: step 1 explains the expected 403 instead of presenting it as a mystery, and does not
#     invent a filter chain to silence it ---

def test_step1_explains_expected_403_without_inventing_filter_chain() -> None:
    text = _step_text("step-v06-auth-hash")
    assert "403" in text
    assert "@Bean SecurityFilterChain" not in text
    assert "SessionCreationPolicy.STATELESS" not in text
    common_error_texts = [_text(e) for e in _guided_step("step-v06-auth-hash")["commonErrors"]]
    assert any("403" in t for t in common_error_texts)


# --- D: step 2 is the first step that owns the actual SecurityFilterChain bean ---

def test_step2_is_first_step_owning_filter_chain() -> None:
    step1_text = _step_text("step-v06-auth-hash")
    step2_text = _step_text("step-v06-auth-filterchain")

    assert "@Bean SecurityFilterChain" not in step1_text
    assert "@Bean SecurityFilterChain" in step2_text
    assert "SessionCreationPolicy.STATELESS" in step2_text


# --- E: step 2 names only real MockMvc tests; the nonexistent-class false claim is gone ---

def test_step2_names_only_real_mockmvc_tests() -> None:
    text = _step_text("step-v06-auth-filterchain")
    assert OLD_FALSE_TEST_CLAIM not in text
    assert "TransactionValidationTest" in text
    # explicit statement that the same-named "Controller" tests are unaffected
    assert "không đi qua MockMvc" in text

    # confirm this was genuinely a defect at the pre-repair baseline (RED reproduction)
    baseline_text = _step_text("step-v06-auth-filterchain", _baseline())
    assert OLD_FALSE_TEST_CLAIM in baseline_text


# --- F: step 2 does not teach disabling CSRF (empirically unnecessary — .with(jwt()) alone
#     passes both TransactionValidationTest cases in a literal dry run) ---

def test_step2_does_not_teach_disabling_csrf() -> None:
    text = _step_text("step-v06-auth-filterchain")
    # CSRF-disable syntax may be *mentioned* only inside an explicit "don't do this" framing,
    # never as an instruction to actually call it.
    assert "Không cần và không nên tắt CSRF" in text
    assert "CSRF không phải nguyên nhân" in text
