# Spendwise Guided Rebuild — Architecture Specification

**Status:** APPROVED — canonical planning document for the Guided Rebuild feature.
**Type:** Specification (not an execution report — see `docs/report/2026-09-17-spendwise-guided-rebuild-wave1-report.md`
for Wave 1 execution evidence).
**Owner responsibility split:** this document defines what Guided Rebuild is, what it owns, what it
must never duplicate, and the frozen design for every implementation wave. An implementer with no
access to the chat history that produced this document must be able to build Waves 2–5 from this
file alone.

## 1. Problem statement

The course site already has a complete canonical engineering plan for Spendwise
(`content/spendwise-project.json`): 10 releases, features, buildTasks, and (for V0.1) 18
buildSteps with `doneWhen`/`verifyCommand`/`filesTouched`/`architectureRules`. That artifact answers
**what** to build, **when** it belongs in the architecture, and **what proves it's done**. It does
not answer the question a first-time learner actually asks:

> "I have never built a Java/Spring project before. Tell me exactly what to create, what to type,
> why I am typing it, how to run it, what result I should expect, and how to diagnose common
> errors."

Guided Rebuild is the new instructional layer that answers that question, without turning the
canonical buildStep/buildTask model into a tutorial-content dumping ground.

## 2. Beginner persona

Assume the learner:
- knows only the theory taught so far in the course (Day-N lessons);
- has never created a real Maven/Spring project;
- does not know standard Java project structure, packages, or when to run Maven by instinct;
- should not need to reverse-engineer `D:\spendwise` (the finished reference app) to proceed.

## 3. Source-of-truth boundaries

| Concern | Owner | File |
|---|---|---|
| What must exist, engineering acceptance, file list, verify command, architecture rules | Canonical project data | `content/spendwise-project.json` |
| How a beginner learns to build it, why each step matters, what to type, what a beginner should attempt themselves, common beginner failures, "what did I just build" | Guided Rebuild data | `content/spendwise-guided-build.json` |
| UI/JS/CSS | `index.template.html` (source) → `index.html` (generated, never hand-edited) | |
| Publication assembly | `tools/build_site.py` | |
| Closed-schema/referential-integrity enforcement | `tools/validate_project.py` (canonical) + `tools/validate_guided_build.py` (guided, new) | |

**Invariant:** Guided Rebuild data never duplicates canonical engineering truth. It *references* it
by id (`releaseId`, `buildTaskId`, `buildStepId`, lesson id) and the two are joined at render time.
A guided step never repeats `doneWhen`, `verifyCommand`, `filesTouched`, `architectureRules`,
`mentorHint`, or `estimatedMinutes` — those stay singly-owned by the buildStep and are joined
through `buildStepId` when the UI renders.

## 4. Data model — `content/spendwise-guided-build.json`

Closed schema, `schemaVersion: 1`. Top level: `guidedCourse`, `guidedReleases`, `guidedSessions`,
`guidedSteps`, `guidedCheckpoints`.

### 4.1 `guidedCourse`
```json
{ "id": "spendwise-guided-build", "title": "Spendwise Guided Rebuild",
  "workspaceExample": "D:\\spendwise-learning", "referenceWorkspaceExample": "D:\\spendwise" }
```
Illustrative example paths only, not an enforced filesystem contract for every learner.

### 4.2 `guidedReleases`
One entry per canonical release, identity is `releaseId` itself (no separate authored id):
```json
{ "releaseId": "v0-1", "authoringStatus": "planned" }
```
`authoringStatus` ∈ `{planned, authored}`. Field is named `authoringStatus`, not `status`, because
canonical releases already own release-lifecycle `status` semantics — a different concept.
Title/goal/problem/featureIds/buildTaskIds are **not** duplicated here; they are joined from
`content/spendwise-project.json` by `releaseId` at render time.

### 4.3 `guidedSessions`
```json
{ "id": "session-money-vo", "releaseId": "v0-1", "buildTaskId": "task-money-vo",
  "order": 2, "title": "Xây Money", "goal": "..." }
```
**Not** a schema-enforced 1:1 with buildTask. One buildTask may eventually be taught across
multiple sessions (a future security/JPA/import task might need 2-3 sessions); the V0.1 pilot's
choice of one session per task is an *authoring* choice, not a schema invariant.

### 4.4 `guidedSteps`
```json
{ "id": "gstep-money-01", "sessionId": "session-money-vo", "order": 1,
  "buildStepId": "step-money-vo-01", "type": "your-turn",
  "title": "...", "goal": "...", "whyThisMatters": "...",
  "theoryBridge": [{ "lessonId": "day-04", "note": "..." }],
  "instructions": ["..."], "codeBlocks": [{ "language": "java", "code": "...", "caption": "..." }],
  "learnerAction": { "goal": "...", "constraints": ["..."], "hints": ["..."] },
  "commonErrors": [{ "symptom": "...", "likelyCause": "...", "fix": "..." }],
  "run": { "cwd": "D:\\spendwise-learning", "command": ".\\mvnw.cmd '-Dtest=MoneyTest' test",
           "expectedResult": "BUILD SUCCESS", "explanation": "..." },
  "reveal": { "label": "Xem lời giải tham khảo", "content": "..." },
  "projectStateBefore": "...", "projectStateAfter": "..." }
```
`buildStepId` may be `null` for pure pedagogical steps (orientation/explanation/debug/review) with
no canonical counterpart — these do not count toward the completeness gate (§6). Multiple
guidedSteps may reference the same `buildStepId` (one canonical "Implement Money" buildStep can be
taught across several beginner moments: explain → create file → add BigDecimal → your-turn → run →
review). `run` is the **learner-facing** instruction (where to stand, what to type, what success
looks like) and is a distinct concept from canonical `verifyCommand` (the machine acceptance
contract) — not a duplicate encoding of the same thing.

Step `type` enum (bounded, no ad-hoc additions): `orientation, setup, create-folder, create-file,
code-with-me, your-turn, explanation, run, checkpoint, debug, review`.

`learnerAction` is **required** when `type == "your-turn"` and **must be absent** otherwise.

### 4.5 `guidedCheckpoints`
```json
{ "id": "checkpoint-money-vo", "sessionId": "session-money-vo",
  "expectedFiles": ["src/main/java/com/spendwise/shared/Money.java"],
  "expectedProjectTree": "...", "understanding": ["..."],
  "whatYouBuilt": "...", "whyNotYet": ["..."] }
```
Exactly one checkpoint per guided session. Checkpoint owns pedagogical understanding/state; it does
not duplicate `doneWhen`/`verifyCommand` — those are joined from the canonical buildStep(s) the
session's steps reference.

## 5. Normalization rules

Relationships are stored in exactly one direction to avoid drift:
- `guidedSession` → `releaseId`, `buildTaskId`
- `guidedStep` → `sessionId`
- `guidedCheckpoint` → `sessionId`

There is **no** `guidedRelease.sessionIds`, **no** `guidedSession.stepIds`, **no**
`guidedSession.checkpointId`. Any UI or validator that needs "sessions for this release" or "steps
for this session" derives it by filtering, exactly the way `content/spendwise-project.json` derives
"buildSteps for this task" by filtering the top-level `buildSteps` array on `taskId` rather than
storing a reverse list on the task.

## 6. Validation rules (`tools/validate_guided_build.py`)

Mirrors the closed-schema, referential-integrity discipline of `tools/validate_project.py` (same
`_closed_keys`/`_check_id`/`_require_str`/`_is_known` helpers, reused by import rather than
reimplemented — see rationale in the Wave 1 report). Rules:

1. Closed schema at every nesting level (top-level, guidedCourse, guidedRelease, guidedSession,
   guidedStep, theoryBridge entry, codeBlock, learnerAction, commonError, run, reveal, checkpoint).
   Unknown keys fail.
2. Ids URL-safe (`^[a-z0-9][a-z0-9-]*$`) and unique in one global guided-id namespace
   (`guidedCourse.id`, every `guidedSession.id`, every `guidedStep.id`, every
   `guidedCheckpoint.id`) — same discipline as canonical project ids.
3. Exactly one `guidedReleases` entry per canonical release id (bijection with the 10-release
   spine); no unknown `releaseId`.
4. `guidedSession.releaseId` and `.buildTaskId` must resolve, and the canonical buildTask's
   `releaseId` **must equal** the session's `releaseId` — a V0.1 session cannot silently reference
   a V0.3 buildTask.
5. `guidedStep.sessionId` must resolve. `guidedStep.buildStepId`, when non-null, must resolve to a
   canonical buildStep **whose `taskId` equals the owning session's `buildTaskId`** — a Money
   session cannot reference an Account buildStep.
6. `guidedSession.order` contiguous `1..N` within each release; `guidedStep.order` contiguous
   `1..N` within each session. No gaps, no duplicates, no zero.
7. `authoringStatus == "planned"` ⇒ zero guidedSessions reference that release.
8. `authoringStatus == "authored"` ⇒ at least one guidedSession references that release, **and**
   the generic completeness gate (below) holds.
9. **Generic completeness gate** (not hardcoded to V0.1 — applies to any release the moment it's
   marked authored): every `required: true` canonical buildTask belonging to that release must be
   covered by ≥1 guidedSession (`session.buildTaskId`); every canonical buildStep belonging to each
   such required buildTask must be covered by ≥1 guidedStep with a matching `buildStepId`. Optional
   (non-required) buildTasks do not block completeness. A release with no canonical `buildSteps`
   entries at all for a task is vacuously satisfied at the step level (nothing to cover yet).
10. Exactly one `guidedCheckpoint` per guidedSession — zero or duplicate both fail.
11. `theoryBridge[].lessonId` must resolve to a real lesson id — reused directly from
    `tools/validate_project.LESSON_IDS` (day-01..day-38, day-39-64, day-65-66), not a second
    hardcoded list.
12. Type-specific: `your-turn` requires `learnerAction`; every other type forbids it. `run`, when
    present, requires all four sub-fields non-empty. `commonErrors` entries require all three
    sub-fields non-empty.

CLI: `python tools/validate_guided_build.py` — loads and validates
`content/spendwise-project.json` first (guided referential checks are meaningless against an
invalid canonical artifact), then `content/spendwise-guided-build.json`. Prints
`PASS guidedReleases=N guidedSessions=N guidedSteps=N guidedCheckpoints=N` or `ERROR ...` lines,
exit code 0/1, matching `validate_project.py`'s CLI contract.

## 7. Wave 1 production skeleton

`content/spendwise-guided-build.json` at the end of Wave 1: `guidedCourse` populated, all 10
`guidedReleases` rows present with `authoringStatus: "planned"` (including `v0-1`), and
`guidedSessions`/`guidedSteps`/`guidedCheckpoints` all empty. This is intentional — it represents
"the architecture exists, no content is authored yet" and must pass validation as-is. No fake
tutorial text is inserted to exercise the schema; the validator test suite exercises the schema
using synthetic fixtures instead (§6 of the Wave 1 report), never the production file.

## 8. Implementation wave sequence (frozen)

| Wave | Scope |
|---|---|
| **Wave 1** (this task) | Schema + validator + validator tests. No UI, no state, no build-pipeline change. |
| **Wave 2** | Build embedding (`courseData.guidedBuild` joins `courseData.project` inside the existing `#course-data` payload — no second `<script>` tag) + Guided Progress state (`guidedProgress: { completedSteps: [] }` added to `defaultState()`/`sanitizeState()`) + export/import schema migration. |
| **Wave 3** | Routes (`#/guided-build`, `#/guided-build/:releaseId`, `#/guided-build/:releaseId/:sessionId`, `#/guided-build/:releaseId/:sessionId/:stepId`) + navigation (3-concept model: HỌC LÝ THUYẾT / XÂY PROJECT / XEM KIẾN TRÚC-ROADMAP) + UI shell. |
| **Wave 4** | Complete V0.1 beginner content — flips `v0-1` guidedRelease to `authoringStatus: "authored"` atomically with its full session/step/checkpoint content, satisfying the completeness gate. |
| **Wave 5** | Pedagogy self-review, responsive/accessibility/UI smoke QA, fixes. |

Each wave ends in its own dated report under `docs/report/`, following this repository's existing
phase-gate convention (P0/P1/P2/... on the Spendwise engineering side).

## 9. Wave 2 design, frozen now (not implemented until Wave 2)

- **State**: `guidedProgress: { completedSteps: [] }` added to `defaultState()`. Independent of
  `completed[]` (theory) and `projectProgress.buildTasks[]` (canonical engineering progress) —
  completing a guided step never marks a lesson or a canonical buildTask complete, and vice versa.
- **No `legacyCompleted`/rename-map for guided progress in the initial Wave 2 cut.** No guided step
  id has ever shipped, so there is nothing to migrate yet. When the first real guided-step
  id rename/split happens in a later revision, migration machinery (mirroring
  `migrateProjectProgress`'s `RENAME_MAP` pattern) is introduced **atomically with that change**,
  not speculatively now.
- **`STATE_VERSION`**: currently `3` (confirmed at `index.template.html:2266` as of this Wave 1
  baseline, commit `cbb6f9c`). Wave 2 should bump to `4` for the audit trail, **after re-verifying
  the actual value at Wave 2 implementation time** — do not assume it is still 3. Note:
  `sanitizeState` does not itself branch on the version number (verified by reading
  `index.template.html:2321-2352`); it always re-derives from `defaultState()` and validates each
  field independently, so old saved state missing `guidedProgress` is backward-compatible by
  construction. The version bump is for auditability, not correctness.
- **Export/import**: Guided Progress lives inside `state`, so exported progress files will contain
  it once Wave 2 ships. Wave 2 must inspect the current `APP_SCHEMA.schemaVersion` at
  implementation time, bump it by one, and the importer must keep accepting older export versions
  without losing Theory progress or Project progress when `guidedProgress` is absent from the
  imported file.
- **Build embedding**: `guidedBuild` becomes a sibling key inside the existing `course-data`
  publication model (`courseData.project`, `courseData.guidedBuild`) — no second script marker, no
  duplication of canonical data inside the guided blob; joins happen by id at render time.

## 10. Route/UI model, frozen now (not implemented until Wave 3)

Routes: `#/guided-build`, `#/guided-build/:releaseId`, `#/guided-build/:releaseId/:sessionId`,
`#/guided-build/:releaseId/:sessionId/:stepId`. An unresolvable guided id renders a Guided-Build
"not found/unavailable" state — never a crash, never a silent redirect to the dashboard.

Learner-facing concept split (Vietnamese labels, frozen): **HỌC LÝ THUYẾT** (existing lesson
content), **XÂY PROJECT** (new Guided Build), **XEM KIẾN TRÚC / ROADMAP** (existing canonical
project pages). Internal ids like `buildTaskId`/`schema`/`artifactPrereqTaskId` never surface on
primary UI copy.

## 11. Code-with-me / your-turn / reveal model, frozen now

- **Code-with-me**: small bootstrap/mechanical code (package declaration, class shell, POM
  fragment) may be shown fully.
- **Your-turn**: domain/business logic gives goal, constraints, reasoning, hints — not an immediate
  full solution.
- **Reveal**: optional, learner-initiated, after an attempt. Reveal content must represent the
  class **as it should exist at that specific guided step**, not the final V1.0 file. Wave 4
  authoring may inspect `D:\spendwise` read-only (`git show <v0.1-commit>:<path>`, no checkout, no
  reset, no local modification) to source historically-accurate reveal content, but the content
  itself must be authored directly into `content/spendwise-guided-build.json` before publication —
  see §12.

## 12. Runtime independence from `D:\spendwise` (hard invariant)

`tools/build_site.py`, `tools/validate_guided_build.py`, the test suite, and the published static
site **must never** depend on `D:\spendwise` existing on the machine, at any wave. It is authoring
reference material only. Any stage-specific content a future learner-facing reveal needs must be
baked into `content/spendwise-guided-build.json` at authoring time. No `referenceCommit`/
`referencePath` runtime fields were added to the schema for this reason — provenance, if ever
needed, lives in authoring documentation/report history, not in a schema field with no runtime
consumer (avoiding a dead field per the repository's own "no fields without a consumer" discipline
already followed by `validate_project.py`'s `BUILD_STEP_OPTIONAL_KEYS`).

## 13. Payload-size policy

The V0.1-only pilot keeps `guidedBuild` inside the existing `course-data` payload (§9). After the
complete V0.1 pilot (end of Wave 4/5), review the generated `index.html`/embedded-JSON size before
scaling authoring to V0.2 → V1.0; do not pre-split the payload now on a hypothetical future size
concern (YAGNI).

## 14. Explicit non-goals of this specification / Wave 1

- No numeric guided-step-count target anywhere in schema or spec. The V0.1 acceptance bar (owned by
  Wave 4/5, not this document's validator) is: a learner starting from an empty folder can reach
  the canonical V0.1 state without opening `D:\spendwise` source and guessing — not "40 steps" or
  "50 steps" or exact parity with the 18 canonical buildSteps.
- No V0.2+ tutorial content, ever, until each release is explicitly authored in its own wave.
- No UI, routing, state, or build-pipeline change in Wave 1.
- No modification to `content/spendwise-project.json`, `index.template.html`, `index.html`, or
  `D:\spendwise`.
