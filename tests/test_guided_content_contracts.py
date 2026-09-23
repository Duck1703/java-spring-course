"""Semantic contracts for learner-visible Guided Rebuild content."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUIDED_PATH = ROOT / "content" / "spendwise-guided-build.json"
BOOT_VERSION = "3.5.16"


def _guided_step(step_id: str) -> dict:
    guided = json.loads(GUIDED_PATH.read_text(encoding="utf-8"))
    return next(step for step in guided["guidedSteps"] if step["id"] == step_id)


def _session_steps(session_id: str) -> list:
    guided = json.loads(GUIDED_PATH.read_text(encoding="utf-8"))
    return [s for s in guided["guidedSteps"] if s["sessionId"] == session_id]


def _text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_text(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(_text(item) for item in value.values())
    return ""


def test_v03_boot_path_pins_one_deterministic_version() -> None:
    guided = json.loads(GUIDED_PATH.read_text(encoding="utf-8"))
    v03_session_ids = {
        session["id"]
        for session in guided["guidedSessions"]
        if session["releaseId"] == "v0-3"
    }
    v03_text = _text([
        step for step in guided["guidedSteps"]
        if step["sessionId"] in v03_session_ids
    ])
    pin_step = _guided_step("step-v03-boot-pin")
    parent_step = _guided_step("step-v03-boot-parent")
    pin_text = _text(pin_step)
    parent_text = _text(parent_step)

    assert f"Use Spring Boot {BOOT_VERSION} for this course." in pin_text
    assert f"<version>{BOOT_VERSION}</version>" in parent_text
    assert BOOT_VERSION in pin_step["run"]["command"]

    time_dependent_choice = re.compile(
        r"latest supported|latest GA|newest compatible|mới nhất còn được hỗ trợ|"
        r"hết hỗ trợ OSS|lệch khỏi 3\.5\.16|phiên bản khác còn được hỗ trợ|"
        r"chọn dòng phiên bản còn khả dụng|tự tra cứu",
        re.IGNORECASE,
    )
    assert time_dependent_choice.search(v03_text) is None
    mentioned_versions = re.findall(
        r"Spring Boot\s+([0-9]+\.[0-9]+\.[0-9]+)", v03_text
    )
    assert mentioned_versions
    assert set(mentioned_versions) == {BOOT_VERSION}


def test_v03_pin_verifier_rejects_arbitrary_nonempty_notes() -> None:
    pin_step = _guided_step("step-v03-boot-pin")
    command = pin_step["run"]["command"]
    expected = pin_step["run"]["expectedResult"]

    assert "springBootVersion=3.5.16" in command
    assert "^springBootVersion=" in command
    assert "Count -ne 1" in command
    assert "springBootVersion=3.5.16" in expected
    assert "Length -eq 0" not in command


def test_v03_parent_verifier_checks_effective_exact_version() -> None:
    parent_step = _guided_step("step-v03-boot-parent")
    command = parent_step["run"]["command"]

    assert "-Dexpression=project.parent.version" in command
    assert "-ne '3.5.16'" in command
    assert ".\\mvnw.cmd test" in command


# --- V0.5 scalar Money persistence contract (progressive-audit repair) -------
# Canonical authority: D:\spendwise @ 8ead91c maps the Money value object by
# SCALAR DECOMPOSITION (BigDecimal amount + String currency @Column pairs),
# never @Embeddable/@Embedded/@AttributeOverride (0 occurrences in all history).
# These contracts pin that the learner-facing guidance teaches that pattern
# explicitly and respects build-step chronology (opening scalars at the
# jpa-entities session; balance scalars only at the balance-projection session).

def test_v05_money_roundtrip_teaches_scalar_decomposition() -> None:
    step = _guided_step("step-v05-jpa-entities-money-roundtrip")
    text = _text(step)

    # amount persisted as BigDecimal / NUMERIC(19,2); currency as its own column
    assert "BigDecimal" in text
    assert "NUMERIC(19,2)" in text
    assert "VARCHAR(3)" in text
    # the two scalar fields are named for the beginner
    assert "openingAmount" in text
    assert "openingCurrency" in text
    # Money stays the domain abstraction, reconstructed from the scalars
    assert "Money" in text
    # compareTo round-trip remains the proof
    assert "compareTo" in text


def test_v05_jpa_session_does_not_teach_embeddable_as_the_pattern() -> None:
    # On the AFFIRMATIVE teaching surfaces (instructions + learnerAction — what
    # the learner is told to DO), @Embeddable/@Embedded may appear only inside an
    # explicit negation. commonErrors/reveal are free to name the anti-pattern to
    # warn against it, so they are deliberately out of scope here.
    for step in _session_steps("session-jpa-entities"):
        affirmative = _text(step.get("instructions", [])) + "\n" + _text(step.get("learnerAction", {}))
        for line in affirmative.splitlines():
            if "@Embeddable" in line or "@Embedded" in line:
                negated = any(
                    marker in line
                    for marker in ("không dùng", "KHÔNG dùng", "không map", "không phải", "KHÔNG")
                )
                assert negated, f"@Embeddable stated affirmatively: {line!r}"


def test_v05_balance_scalars_are_named_only_at_projection_session() -> None:
    # Chronology (directive §8): opening_* scalars belong to the jpa-entities
    # session; balance_amount/balance_currency must NOT leak earlier and MUST
    # appear at the balance-projection session with canonical two-column naming.
    entities_text = _text(_session_steps("session-jpa-entities"))
    assert "balance_amount" not in entities_text
    assert "balance_currency" not in entities_text

    projection_text = _text(_session_steps("session-balance-projection"))
    assert "balance_amount" in projection_text
    assert "balance_currency" in projection_text


# --- V0.5 transfer migration lineage contract -------------------------------
# Canonical authority: D:\spendwise @ 8ead91c has no transaction-type or
# category-value CHECK in V1. V3 is exactly one statement adding nullable
# transfer_ref VARCHAR(36); Java's TransactionType enum owns the allowed values.


def test_v05_v1_does_not_teach_type_or_category_enum_checks() -> None:
    v1_text = _text(_guided_step("step-v05-flyway-init"))

    assert re.search(r"CHECK\s*\(\s*type\s+IN", v1_text, re.IGNORECASE) is None
    assert re.search(r"CHECK\s*\(\s*category(?:_code)?\s+IN", v1_text, re.IGNORECASE) is None


def test_v05_transfer_teaches_exact_canonical_v3_without_constraint_rewrite() -> None:
    transfer_text = _text(_guided_step("step-v05-transfer-implement"))

    assert "ALTER TABLE transactions ADD COLUMN transfer_ref VARCHAR(36);" in transfer_text
    assert "DROP CONSTRAINT" not in transfer_text
    assert "ADD CONSTRAINT" not in transfer_text
    assert re.search(
        r"V1(?:'s| đã).{0,120}(?:CHECK|khoá).{0,120}(?:INCOME|EXPENSE)",
        transfer_text,
        re.IGNORECASE | re.DOTALL,
    ) is None


def test_guided_never_drops_a_constraint_missing_from_earlier_steps() -> None:
    guided = json.loads(GUIDED_PATH.read_text(encoding="utf-8"))
    earlier_text = ""

    for step in guided["guidedSteps"]:
        step_text = _text(step)
        for constraint_name in re.findall(
            r"\bDROP\s+CONSTRAINT\s+(?!IF\s+EXISTS\b)([A-Za-z_][A-Za-z0-9_]*)",
            step_text,
            re.IGNORECASE,
        ):
            assert re.search(
                rf"\bADD\s+CONSTRAINT\s+{re.escape(constraint_name)}\b",
                earlier_text,
                re.IGNORECASE,
            ), (
                f"{step['id']} drops constraint {constraint_name!r}, but no earlier "
                "Guided step creates that named constraint"
            )
        earlier_text += "\n" + step_text


def test_v05_transfer_teaches_null_category_compatibility_without_sentinel() -> None:
    transfer_text = _text(_guided_step("step-v05-transfer-implement"))

    assert "category=null" in transfer_text
    assert "TransactionService" in transfer_text
    assert "StatisticsService" in transfer_text
    assert "TransactionMapper" in transfer_text
    assert "CsvTransactionStore" in transfer_text
    assert "category() != null" in transfer_text
    assert "category rỗng khi null" in transfer_text
    assert re.search(r"lọc.{0,80}category.{0,240}category\(\) != null", transfer_text, re.IGNORECASE | re.DOTALL)
    assert "Không tạo sentinel UNCATEGORIZED" in transfer_text
    assert re.search(r"Category\.UNCATEGORIZED|category\s*=\s*UNCATEGORIZED", transfer_text, re.IGNORECASE) is None

# --- V0.6 canonical-token-issuer auth-contract repair -----------------------
# CONFIRMED_CURRICULUM_CONTRADICTION (supervisor adjudication): AuthController
# is confined to step-auth-hardening-01 (task-auth-hardening-review, optional,
# prereq task-canonical-token-issuer) and is absent from
# checkpoint-canonical-token-issuer.expectedFiles. step-v06-canonical-swap-real-
# issuer must therefore prove the real-signer revocation contract through an
# already-existing protected route, never through a claimed /auth/login or
# /auth/logout HTTP endpoint.

def test_v06_canonical_swap_step_does_not_require_authcontroller() -> None:
    step = _guided_step("step-v06-canonical-swap-real-issuer")
    text = _text(step)

    assert "AuthController" not in text or "KHÔNG tạo AuthController" in text
    assert re.search(r"KHÔNG tạo AuthController", text)

def test_authcontroller_confined_to_optional_hardening_task() -> None:
    guided = json.loads(GUIDED_PATH.read_text(encoding="utf-8"))
    project = json.loads((ROOT / "content" / "spendwise-project.json").read_text(encoding="utf-8"))

    touching = [
        bs["id"]
        for bs in project["buildSteps"]
        if any("AuthController" in f for f in bs.get("filesTouched", []))
    ]
    assert touching == ["step-auth-hardening-01"]

    hardening_step = next(bs for bs in project["buildSteps"] if bs["id"] == "step-auth-hardening-01")
    assert hardening_step["taskId"] == "task-auth-hardening-review"
    assert "task-canonical-token-issuer" in hardening_step.get("artifactPrereqTaskIds", [])

    hardening_task = next(t for t in project["buildTasks"] if t["id"] == "task-auth-hardening-review")
    assert hardening_task["required"] is False

    checkpoint = next(c for c in guided["guidedCheckpoints"] if c["id"] == "checkpoint-canonical-token-issuer")
    assert "AuthController.java" not in checkpoint["expectedFiles"]

def test_v06_same_token_revocation_proof_uses_authservice_and_protected_route() -> None:
    step = _guided_step("step-v06-canonical-swap-real-issuer")
    text = _text(step)

    assert "AuthService.login" in text
    assert "AuthService.logout" in text
    assert re.search(r"route (được bảo vệ|đã được bảo vệ)", text)
    assert "MockMvc" in text
    assert "200" in text and "401" in text

def test_v06_checkpoint_does_not_claim_http_login_logout_endpoints() -> None:
    guided = json.loads(GUIDED_PATH.read_text(encoding="utf-8"))
    checkpoint = next(c for c in guided["guidedCheckpoints"] if c["id"] == "checkpoint-canonical-token-issuer")
    text = _text(checkpoint)

    assert not re.search(r"/auth/login.{0,40}(tồn tại|endpoint HTTP)", text, re.IGNORECASE)
    assert re.search(r"không qua endpoint /auth/login", text) or re.search(
        r"AuthController chưa tồn tại", text
    )

def test_v06_mandatory_run_commands_are_literal_windows_executables() -> None:
    guided = json.loads(GUIDED_PATH.read_text(encoding="utf-8"))
    v06_session_ids = {
        session["id"] for session in guided["guidedSessions"] if session["releaseId"] == "v0-6"
    }

    for step in guided["guidedSteps"]:
        if step["sessionId"] not in v06_session_ids:
            continue
        run = step.get("run")
        if not run or "command" not in run:
            continue
        cmd = run["command"]
        for segment in cmd.split(";"):
            segment = segment.strip()
            looks_like_maven_fragment = bool(re.match(r"^(-q\b|'-Dtest=|test$)", segment))
            assert not looks_like_maven_fragment, f"{step['id']} run.command segment not literal: {segment!r} in {cmd!r}"

def test_v07_through_v10_run_commands_are_literal_windows_executables() -> None:
    guided = json.loads(GUIDED_PATH.read_text(encoding="utf-8"))
    later_release_ids = {"v0-7", "v0-8", "v0-9", "v1-0"}
    later_session_ids = {
        session["id"] for session in guided["guidedSessions"] if session["releaseId"] in later_release_ids
    }

    for step in guided["guidedSteps"]:
        if step["sessionId"] not in later_session_ids:
            continue
        run = step.get("run")
        if not run or "command" not in run:
            continue
        cmd = run["command"]
        for segment in cmd.split(";"):
            segment = segment.strip()
            looks_like_maven_fragment = bool(re.match(r"^(-q\b|'-Dtest=|test$)", segment))
            assert not looks_like_maven_fragment, f"{step['id']} run.command segment not literal: {segment!r} in {cmd!r}"
