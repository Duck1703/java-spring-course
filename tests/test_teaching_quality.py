"""Teaching-quality guards for the 2026-09-25 teaching-experience redesign.

These pin the pedagogy contract, not engineering truth: every theory lesson
carries the A-D/I teaching scaffold, every hands-on guided step explains why
and gives a self-check, every test run says what green proves and what it does
not, every session tells the Spendwise story, and learner-visible prose is not
ASCII-stripped Vietnamese.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDED = json.loads((ROOT / "content" / "spendwise-guided-build.json").read_text(encoding="utf-8"))
HANDS_ON = {"code-with-me", "your-turn"}
# Whole-word ASCII-stripped Vietnamese that never appears in English/identifiers.
ASCII_VI = re.compile(r"\b(khong|duoc|nhung|chua|nguoi|thuc|viec|buoc|phien|kiem tra)\b")
PROSE_SKIP = {"code", "command", "cwd", "id", "sessionId", "buildStepId", "lessonId", "language",
              "citations", "sourceUsage", "references", "authoring", "resourceId", "url", "catalogRef",
              "expectedFiles", "expectedProjectTree", "compile", "partialReason"}


def _lessons() -> list[dict]:
    out = []
    for path in sorted((ROOT / "content" / "lessons").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        out += data.get("lessons", [data])
    return out


def _prose(value, key=""):
    if key in PROSE_SKIP:
        return
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _prose(item)
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _prose(v, k)


def test_every_lesson_has_teaching_scaffold() -> None:
    lessons = _lessons()
    assert len(lessons) == 40
    assert [l["id"] for l in lessons if "teaching" not in l] == []


def test_every_hands_on_step_has_why_selfcheck_and_failure_modes() -> None:
    missing = []
    for step in GUIDED["guidedSteps"]:
        if step["type"] in HANDS_ON:
            if not step.get("whyThisMatters"):
                missing.append((step["id"], "whyThisMatters"))
            if not step.get("selfCheck"):
                missing.append((step["id"], "selfCheck"))
            if len(step.get("commonErrors", [])) < 2:
                missing.append((step["id"], "commonErrors>=2"))
        if step["type"] == "checkpoint" and not step.get("selfCheck"):
            missing.append((step["id"], "selfCheck"))
    assert missing == []


def test_every_code_block_and_run_is_explained() -> None:
    assert [s["id"] for s in GUIDED["guidedSteps"] for b in s.get("codeBlocks", []) if not b.get("explanation")] == []
    assert [s["id"] for s in GUIDED["guidedSteps"] if "run" in s and not s["run"].get("explanation")] == []


def test_test_runs_say_what_green_does_not_prove() -> None:
    offenders = [
        s["id"] for s in GUIDED["guidedSteps"]
        if "run" in s and re.search(r"\btest\b|-Dtest=", s["run"]["command"])
        and "chưa chứng minh" not in s["run"]["explanation"]
    ]
    assert offenders == []


def test_every_session_tells_the_story_and_bridges_to_theory() -> None:
    bridged = {s["sessionId"] for s in GUIDED["guidedSteps"] if s.get("theoryBridge")}
    for session in GUIDED["guidedSessions"]:
        assert session.get("projectNow") and session.get("sessionAdds"), session["id"]
        assert session["id"] in bridged, session["id"]


def test_learner_prose_is_not_ascii_stripped_vietnamese() -> None:
    hits = []
    for record in GUIDED["guidedSessions"] + GUIDED["guidedSteps"] + GUIDED["guidedCheckpoints"]:
        hits += [(record["id"], m) for text in _prose(record) for m in ASCII_VI.findall(text)]
    for lesson in _lessons():
        hits += [(lesson["id"], m) for text in _prose(lesson) for m in ASCII_VI.findall(text)]
    assert hits == []
