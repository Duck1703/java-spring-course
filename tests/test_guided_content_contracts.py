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
