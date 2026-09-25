"""Guard: learner-facing renderer strings stay Vietnamese-first.

Scans index.template.html from COURSE_CORE_END to runSelfTest (the app
renderer; the core and the self-test harness are out of scope) for the English
UI labels the teaching-experience redesign replaced.
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "index.template.html"

FORBIDDEN = [
    "Current Learning", "Current Build Target", "Today's Project Impact",
    "Expected Result", "Common Errors", "Acceptance Criteria", "Relevant Lessons",
    "Done when", "Mentor Prompt", "Mentor hint", "Build Steps", "Project Track",
    "Learning Track", "Product Vision", "Current Milestone", "Next Build Task",
    "Domain Overview", "Project Boundaries", "Build Tasks", "Guided Build",
    "Release Roadmap", "Release Progress", "User progress", "Course ↔ Project",
    "Architecture Evolution", "Architecture Constitution", "Architecture Change",
    "Initial Architecture", "Defense Readiness", "Theory / Unmapped",
]
EXACT = ["Next", "Goal", "Features", "Sessions", "Problem", "Constraints", "Intent",
         "Prerequisites", "Files", "Verify", "Learn →", "Build →", "Direct", "Future", "Before · ", "After · "]


def _renderer_strings() -> list[str]:
    src = TEMPLATE.read_text(encoding="utf-8")
    body = src[src.index("/* COURSE_CORE_END */"):src.index("function runSelfTest")]
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    body = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith("//"))
    return re.findall(r"'((?:[^'\\\n]|\\.)*)'|\"((?:[^\"\\\n]|\\.)*)\"", body)


def test_renderer_has_no_forbidden_english_labels() -> None:
    hits = []
    for single, double in _renderer_strings():
        text = single or double
        hits += [f for f in FORBIDDEN if f in text]
        hits += [e for e in EXACT if text.strip() == e.strip() or text.startswith(e + ":")]
    assert hits == []
