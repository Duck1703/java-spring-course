# Java Spring Course Content Improvement Plan

## Executive Summary

The audit scored 40 records at a corpus mean of **3.62** — theory 20 records **4.23**, hands-on 16 records **3.08**, terminal 4 records **2.77** — and assigned rewrite levels NONE 0 / LIGHT 17 / MEDIUM 17 / HEAVY 6. This plan turns that result into an executable rewrite programme without touching the syllabus, the roadmap, the unit/day structure, the lesson ids, the approved Spendwise track or the web UI.

The central finding of the planning pass is that **the corpus is in better shape than its headline numbers suggest, and three of the audit's structural causes were mis-diagnosed at the mechanism level.** Re-measuring the live repository rather than reasoning from the audit's prose changed three decisions:

1. **The 63% citation failure is a `references`-array granularity bug, not the no-cross-lesson-borrowing rule.** Of 919 marker instances, 579 are unresolved; **523 of those 579 (220 `sourceUsage` entries) already have their resource published in the same lesson under a different `citationId`.** No new sourcing, no schema change and no relaxed gate is required — 241 `reference` rows must be added to 36 lessons. This converts the single largest defect in the audit from a policy question into a mechanical migration.
2. **`@Version` / optimistic locking is already taught** — in Day 20's prose, correctly, including the `@Version`-in-`WHERE` mechanism, `OptimisticLockException`, the "default choice" recommendation, pessimistic `SELECT ... FOR UPDATE`, one `commonMistake` and a two-thread `enhancedExercise`. What is missing is a **code block**, not the teaching. Audit item 4's "absent from all 40 records" is wrong; the repair is one order of magnitude smaller than the audit implies.
3. **The LO conflict is narrower than audit item 12.** Every record's `objectives` array matches `course-catalog.json` exactly, and Day 33–Day 65-66 legitimately carry multiple LOs. What does not exist anywhere is **LO label and definition text**. The deliverable is a definition table, not a reconciliation of four disagreeing records.

Three causes survive re-measurement intact and are the real structural work: **no SQL / JOIN / index content exists anywhere in 66 days** while eight downstream deliverables assume it; **nine consecutive hands-on records carry no acceptance criteria**; and **63 of 104 Java blocks ship with `compile=False`**, which is why Day 22's `SecurityConfig` reached publication as an open API.

The programme is **eight waves — 0a, 0b, then 1–6.** Wave 0a is Citation Structural Repair and Wave 0b is Assessment Quality Repair + Code Classification; they run **strictly sequentially, each behind its own review gate, and neither runs in parallel with Wave 1.** Waves 1–6 rewrite 29 records in dependency order, 3–6 records per wave, each behind a gate. Order is derived from content dependency, not from the audit's priority list: Wave 1 repairs the four records that ship something false, insecure or vacuous; Wave 3 lays the SQL foundation before any record that reasons about query performance is touched; the capstone (Wave 5) is rewritten only after auth, SQL, locking, coverage and CI have real teaching behind them; the terminal band (Wave 6) is last because it summarises and grades everything the earlier waves change.

**Two sourcing gates precede authoring.** The corpus has zero catalog sources for SQL, and its only sourced auth option contradicts the approved self-issued-JWT flow. Neither gap may be closed by authoring under `authoring.limitations` alone: **foundational SQL claims and the canonical auth flow both require an explicit sourcing step against authoritative references before the affected records are rewritten.** Disclosure is the fallback for residual gaps, never the substitute for sourcing a foundation.

**Status: `CONTENT_REWRITE_PLAN_APPROVED`.** The Review Gate is closed — all seven structural decisions are approved, with revisions incorporated (citation target 0/0/0, safe MCQ rebalancing rather than blanket permutation, the 0a/0b split, both sourcing gates, and the authoring contract held in this plan rather than in Day 37). Four blockers remain open: the Tier 3 compile fixture, the 15 unavailable resources, the **D-4 SQL sourcing gate** (gates Wave 3) and the **auth sourcing gate** (gates Wave 5's auth chain). **First executable work is Wave 0a — Citation Structural Repair, and it is not started in this task.** No lesson has been rewritten, no JSON touched, no validator or build script changed.

## Inputs

| Input | Role in this plan | Status |
| --- | --- | --- |
| `docs/course-content-audit.md` (1080 lines) | Per-record findings, 42-item priority matrix, scores, rewrite levels | **Read-only.** Never modified by this plan. Its corrections are recorded here, not there |
| `course-catalog.json` | Authority for `objectives`, `syllabusAssignments`, `resourceIds`, `outline`, `activities` | Read-only. `_validate_catalog_mirror` deep-equals two of these fields |
| `content/lessons/day-*.json`, `ojt-evaluation.json` | The 40 authored records to be rewritten | Rewritten in Waves 1–6 only, never in this task |
| `content/lesson-schema.json` | Closed-key schema v1; `practices` bounded 2..4 | Unchanged — the cap **stays at 2..4** (approved); no wave depends on raising it |
| `content/source-notes/*.json` (6 files, 111 notes) | Read status and `facts[].locator` / `read.relevantHeadings` per resource | **96 read, 15 unavailable.** The 15 bound what can be cited |
| `content/source-manifest.json` | `resource_id` ↔ URL ↔ lessonIds mapping | Read-only |
| `tools/validate_lessons.py` | Citation, practice, reference and mirror gates | Not modified. Two new checks are *proposed* for a later task |
| `tools/build_site.py` | `_citation_locator_matches`, `_slim_authored_lesson` | Not modified. Its locator asymmetry is a Wave 0a input |
| `content/spendwise-project.json` | `lessonMap`, 38 entries | **FINAL_APPROVED, read-only.** Day 33–36 are `applicationType: "theory"` there |
| Live corpus measurement (this planning pass) | 919 markers, 241 missing reference rows, 9 locator failures, MCQ position histogram, block/compile census | Supersedes any conflicting figure carried in prose |

## Non-Negotiables

Carried from the phase specification and from the audit's own guardrails. Every wave below is constrained by these; where a repair would violate one, the plan says so and routes around it.

**Structure is frozen.** 15 units, 40 teaching records, `EXPECTED_LESSON_IDS = day-01..day-38 + day-39-64 + day-65-66`, groups java=12 / spring=24 / completion=4, the Java → Spring roadmap, topic order within each day, and course-progress semantics. No record is split, merged, reordered, renumbered or deleted.

**No new Days.** New foundational knowledge enters the best-fitting existing record as a section or subsection. Where the plan judges that a new Day would be the better engineering answer, it **flags** it in `### Blockers` and proceeds with the in-record placement. One such flag exists (SQL foundation, D-4), and the approved decision is explicit: **no new Day** — Day 19 + Day 20 + Day 32.

**The syllabus is untouchable.** `GST.CEN_Syllabus_JavaSpring_Dev2-3_v3.xlsx` and the `course-catalog.json` it generates are inputs, not deliverables. This has a hard consequence the plan honours everywhere: `_validate_catalog_mirror` deep-equals `objectives` and `syllabusAssignments`, so **any deliverable that appears in a mirrored syllabus row cannot be cut** — it must be taught. Rows 37 (Day 21 Flyway + `@DataJpaTest`), 42 (Day 24 Redis blacklist + benchmark) and 52 (Day 30 JaCoCo ≥75% + GitHub Actions CI) are mirrored and therefore locked.

**Approved tracks are read-only.** Build While You Learn, `content/spendwise-project.json` including `lessonMap`, `index.template.html`, `index.html`, the build scripts and the tests are FINAL_APPROVED at `8a0debc` / `9cd0424`. Where a record's brief depends on untaught content, the record is fixed, never the project track. `lessonMap` changes only if a mapping is demonstrably wrong; this plan found none.

**`index.html` is a build artifact.** All content edits target `content/lessons/*.json` and the site is regenerated by `tools/build_site.py`. The generated HTML is never hand-edited.

**Citation markers are never deleted to make a number go green.** An unresolved marker is repaired by publishing its `reference` row, by correcting its locator, or by retargeting it onto a source that supports the claim. Where none of those is possible the block is rewritten to stop making the uncitable claim — and the marker goes with the claim, as one authored decision recorded in the diff rationale. **Deleting the marker and keeping the claim is prohibited.** Note what this rules out in both directions: no bulk sweep to clear a count, and **no tolerated residual either** — the target is zero unresolved markers, and `authoring.limitations` discloses a missing *source*, never a dangling `[?]`.

**Citation gates are not weakened.** `read.status == "read"`, `_validate_sourceusage_entry`'s three checks and `_citation_locator_matches` stay as they are. Every repair in this plan works *inside* those gates — which is possible precisely because the dominant failure class needs no gate change.

**Baseline is fixed.** Java 17, Spring Boot 3.x, Spring Framework 6, Jakarta. No virtual threads, no `STR.` templates, no `javax.*`, no `WebSecurityConfigurerAdapter`. Day 25 correctly states Java 17 has no virtual threads and keeps saying so.

**Language contract is fixed.** Vietnamese prose with English technical terms, matching the existing corpus.

**Length is not the target.** The theory band already scores 4.23; LIGHT means surgical. No record is expanded to look improved. Day 36 is the largest record and one of the most duplicative; Day 37 is among the smallest and the best-cited.

**Strong content is preserved.** Day 11 (4.58), Day 26 (4.58), Day 25 (4.50), Day 13 / 16 / 17 (4.42), Unit 9 as a whole (4.28), the AOP-proxy mental model across Day 20 → 23 → 25 → 35, and Day 37's citation handling are the corpus's models. They are cited as templates, not rewritten. Every diff must be explainable as a named audit finding.

**External knowledge is disclosed, never substituted — and disclosure does not cover a foundation.** Where incremental content cannot be sourced from the catalog, it is authored and declared in `authoring.limitations` with the reason — the mechanism Day 15, 26, 27, 38, 39-64 and 65-66 already use. **Two exceptions are hard:** the SQL foundation (D-4) and the canonical auth flow each sit behind a sourcing gate and may **not** be authored on disclosure alone; an explicit sourcing step against authoritative references must complete first, or the work is descoped and escalated. **No custom crypto** in either case. No web research happened in the phase that produced this plan; unsourceable topics were classified only, and the two gates are the mechanism for changing that.

**No invented authority.** Day 39-64's refusal to describe FSU Project conventions the syllabus does not supply, and Day 65-66's refusal to invent an official grading scale, are correct and survive. New rubrics are labelled as suggestions unless an authoritative source exists.

## Structural Decisions

Five decisions that must be settled before any lesson is rewritten, because later waves resolve differently depending on the answers. Each is stated as a decision, the evidence behind it, the option set considered, and its migration / validator / authoring consequences.

### Citation Architecture

**Decision D-1: Option A — self-contained per-lesson references, completed.** No shared registry, no schema change, no gate relaxation.

**Measured baseline (live repo, not carried from the audit):**

| Metric | Value |
| --- | --- |
| Citation marker instances in `blocks[].citations` | **919** |
| Resolved (marker's `citationId` present in that lesson's `references`) | **340** |
| Unresolved, rendering as `[?]` | **579 (63.0%)** |
| `sourceUsage` entries total / cited / published as `references` | **376 / 366 / 127** |
| Existing `reference` rows across all 40 records | **168** |
| Rows that must be added to close every marker | **241** |
| Records needing zero new rows | day-07, day-38, day-39-64, day-65-66 |
| Orphan `references` (published `citationId` never cited by any block) | 2 |

**Why the audit's diagnosis needed correcting.** Audit item 11 attributes the failure to the no-cross-lesson-citation-borrowing rule stranding seven learning outcomes. That rule is real and does strand those outcomes — but it is not what produces the 63%. Classifying all 579 unresolved instances by cause:

| Class | Instances | Entries | Cause | Fix |
| --- | --- | --- | --- | --- |
| **A** | **523** | **220** | The resource **is already published in the same lesson** under a different `citationId`. Pure `references`-granularity artifact | Add one `reference` row per cited `sourceUsage` id |
| **B** | **55** | **20** | Resource not in `references` at all, but the locator gate already passes | Add the row; publishable today |
| **C** | **1** | **1** | `day-23` / `day23-src-11`, locator `"Using the XorCsrfTokenRequestAttributeHandler (BREACH)"` | Locator repair or disclosed rewrite |

523 of 579 instances are a bookkeeping omission. `resourceId` and `citationId` are different keys: `sourceUsage` records *which document a claim came from*, `references` records *what the reader is shown*. Authors added the former and only sometimes the latter. Nothing about cross-lesson borrowing is involved, no resource needs re-reading, and `_validate_sourceusage_entry` already passes for all of them.

**The orthogonal locator-repair set — this must be done first.** Independently of publication state, the build's own gate fails on **9 cited entries / 17 marker instances**:

`day01-src-10`, `day17-src-4`, `day17-src-11`, `day22-src-1`, `day23-src-11`, `day24-src-6`, `day28-src-7`, `day33-src-7`, `day37-src-1`

**8 of those 9 sit inside Class A.** `_slim_authored_lesson` **raises `ValueError`** when a *published* reference fails the locator gate — so a blind references-completion pass would break the build on 8 lessons that currently build fine. Locator repair is therefore sequenced strictly before or with the publication pass, never after.

The cause is a **validator/build asymmetry**, not bad data: `validate_lessons.py` matches `read.facts[].locator`, while `build_site.py::_citation_locator_matches` matches `read.relevantHeadings` after `_normalize_heading` (NFD, diacritic strip, `đ`→`d`, `[^a-z0-9]+`→`""`), `_strip_locator_prefix` (`mục|muc|phần|phan|section|§`) and `_locator_candidates` (split on `/` and `;`, first comma-segment, bare section numbers ≤24 chars plus ancestor root digit). A locator can be a legitimate `facts[].locator` and still be absent from `relevantHeadings`. `day22-src-1` and `day33-src-7` both use `"Specifying the Authorization Server"` — a real fact locator, not a heading. Repair is per-entry: retarget the locator onto a heading that exists in the same note, or split the fact.

**Options considered and rejected:**

- **Option B — shared canonical citation registry** (one `content/citations.json`, lessons reference by key). *Rejected.* It is the architecturally cleaner answer to a problem the corpus does not have: with 523/579 instances being same-lesson omissions, B pays a schema change, a validator rewrite, a build-time resolution step and a 40-record migration to fix something a data-entry pass fixes. It would also weaken the property that makes this corpus auditable — that a lesson's citations are verifiable by reading one file. And it does not fix the 9 locator failures, which are the only failures that actually break the build. Note that the *catalog* already models resource sharing (`resources[].lessonIds`), so B's supposed benefit is partly available already.
- **Option C — hybrid** (registry for resources cited by ≥3 lessons, per-lesson for the rest). *Rejected.* It creates two citation mechanisms, so every future author must decide which applies, and every validator check must handle both. The measured sharing is thin: only `res-553bbd92e5d0` reaches 4 lessons and it is `unavailable`. C's cost is B's cost plus permanent ambiguity.

**Consequences of D-1:**

- *Migration:* 241 `reference` rows into 36 records, derivable from existing `sourceUsage` data — for each cited `sourceUsage` id not yet in `references`, emit a row carrying that `resourceId` + `citationId`. Ordered after the 9 locator repairs. Largest: day-36 +13, day-28 +13, day-11 +13, day-35 +11, day-29 +11, day-26 +11, day-23 +11, day-19 +10, day-08 +10, day-01 +10.
- *Validator:* no change required. A new *check* is proposed for a future task (not implemented here): warn when a cited `sourceUsage` id has no `references` row, which is exactly the 241-row condition, so the class cannot silently reappear.
- *Authoring:* the rule becomes explicit — **every `citationId` a block cites must appear in that lesson's `references`.** Cite-then-publish, in one step.
- *Citation resolution:* unchanged at runtime. `buildRefIndex` keeps mapping `citationId` → 1-based number from the `references` array; it stops printing `[?]` because the lookup stops missing.
- *Terminal state:* **zero unresolved markers, zero locator failures, zero dangling references.** There is no residual `[?]` allowance. Where a marker cannot be supported, the resolution is a deliberate one of three: **retarget** it onto a locator or resource that does support the claim; **repair the claim** so it states only what the available source supports; or **remove the marker as invalid** — meaning the citation was wrong, not merely inconvenient, and the block is rewritten accordingly. Removal is an authored decision recorded in the wave's diff rationale, never a bulk sweep to clear a number.
- *Residual:* the no-cross-lesson-borrowing rule still stands and still strands the seven outcomes of audit item 11. D-1 does not fix that; it removes 579 markers of noise so that the ~20 genuinely stranded artifacts become visible and are handled per-record in Waves 1–5 — by disclosed authoring where the claim is legitimately unsourceable, and by the sourcing gates below where the claim is foundational.

### Learning Outcome Contract

**Decision D-2: the canonical LO authoring contract lives in this plan. Day 37 hosts a learner-facing LO definition/summary derived from it.** The two artifacts are deliberately different things, and the distinction is load-bearing: **Day 37 is not the canonical authoring source.** No record's `objectives` array changes.

- **Canonical authoring contract → this document, `### Learning Outcome Contract`.** It governs authors and reviewers. It is where the six required fields are defined, where a gap in any field is recorded, and what a wave gate checks a record against. It may name unfilled fields, unresolved dependencies and blockers — content a learner should never be shown.
- **Learner-facing LO definition/summary → Day 37**, if and only if it fits that record's purpose (it does: Day 37 carries LO1–LO10, its content *is* the revision map, and the audit names its citation handling as the corpus model). It is a derived, learner-appropriate rendering: definitions and Day pointers, with no authoring metadata and no gap markers.

Consequence of the split: when the two disagree, **this plan wins and Day 37 is corrected** — never the reverse. A future author changing an LO definition edits the contract here first, then re-derives Day 37. Day 38 (LO5–LO12), Day 39-64 (LO6–LO12) and Day 65-66 (LO10–LO12) reference **Day 37's learner-facing table** internally, because their readers are learners and evaluators; they are held to *this* contract at review.

**Correction to audit item 12 (recorded here, not in the audit, per §27).** The audit states that four records "give four incompatible readings of LO10/LO11". Checking every record's `objectives` against `course-catalog.json`: **all 40 match exactly.** The mapping is:

| LO | Unit title (the LO's subject) | Records |
| --- | --- | --- |
| LO1 | Java Platform & Language Basics | day-01, 02, 03 |
| LO2 | OOP in Java | day-04, 05, 06 |
| LO3 | Interface, Generics, Collections & Exception | day-07, 08, 09 |
| LO4 | Stream API, Concurrency & File I/O | day-10, 11, 12 |
| LO5 | Spring Boot Core & IoC Container | day-13, 14, 15 |
| LO6 | Spring MVC — In-Depth REST API | day-16, 17, 18 |
| LO7 | Spring Data JPA & Database | day-19, 20, 21 |
| LO8 | Spring Security & JPA Performance | day-22, 23, 24 |
| LO9 | Caching, Async, File Handling & External API | day-25, 26, 27 |
| LO10 | Testing, Documentation, Monitoring & Docker | day-28, 29, 30 |
| LO11 | Project Planning & Implementation | day-31, 32 |
| LO12 | Implementation Sprint & Final Defense | (via multi-LO records below) |

Multi-LO records, all catalog-exact: **day-33 [LO6, LO7, LO8, LO11]**, **day-34 [LO6, LO7, LO9, LO12]**, **day-35 [LO8, LO9, LO10, LO12]**, **day-36 [LO10, LO11, LO12]**, **day-37 LO1–LO10**, **day-38 LO5–LO12**, **day-39-64 LO6–LO12**, **day-65-66 LO10–LO12**.

So there is no LO→Day conflict to reconcile. **What does not exist anywhere in the corpus is LO label and definition text.** Day 37, 38, 39-64 and 65-66 each paraphrase LO meanings in their own prose because they have nothing to cite, and those paraphrases drift — which is what the audit observed. The defect is a missing artifact, not four contradictions. This also downgrades the fix: one table authored once, not four records reconciled against each other.

**Canonical LO contract.** Every LO definition row must answer six questions. This is the shape of the table, and it is also the contract each record's own `objectives`/`outcomes` prose is held to:

| Field | Question it answers | Source of truth |
| --- | --- | --- |
| **WHAT** | What can the learner do, stated as one observable capability with a verb the learner performs (not "understand") | Authored from the unit title + the three records' `outcomes` |
| **EVIDENCE** | What artifact proves it — a file, an endpoint, a passing test, a benchmark table, a defended answer | The unit's hands-on record's deliverables |
| **TEACHING SUPPORT** | Which records teach it, by id and section | `lesson-index.json` + per-record sections |
| **PRACTICE SUPPORT** | Which practices and `enhancedExercises` exercise it | Per-record `practices[]` / `enhancedExercises[]` |
| **ACCEPTANCE** | The pass threshold, stated so two evaluators agree | The hands-on record's acceptance table (created in this programme) |
| **REFERENCE SUPPORT** | Which catalog resources back it, or an explicit "authored, no source" disclosure | `resourceIds` + `read.status` |

Where a field cannot be filled from the corpus it is filled with an explicit gap marker rather than prose — a blank in this contract is the signal that a downstream record is grading something the course does not support. Gap markers live **here only** and are never rendered into Day 37. On the current corpus, **LO10's EVIDENCE and ACCEPTANCE fields cannot be completed until Day 30's coverage/CI deliverables are taught (see D-6 class A), and LO7's REFERENCE SUPPORT cannot be completed for the SQL layer until the D-4 sourcing gate closes.**

**Placement of the derived table.** Day 37 hosts the learner-facing rendering: it already carries LO1–LO10, its content *is* the revision map, and the audit names its citation handling as the corpus model. Day 38 (LO5–LO12), Day 39-64 (LO6–LO12) and Day 65-66 (LO10–LO12) reference Day 37's table via internal `reference` rows — which require only a `description`, no `resourceId`/`citationId`, so this creates no citation debt. Day 65-66's unexplained narrowing from LO6–LO12 to LO10–LO12 is then either justified in one sentence against the contract or corrected; the contract makes the choice visible for the first time.

**Consequences:** no `objectives` edit anywhere, so `_validate_catalog_mirror` is untouched; four records lose their improvised LO prose; Day 37's table is one `table` block and needs `citations` per the validator, satisfied by an internal reference to the catalog-derived unit titles plus disclosure that the definition text is authored. Because the contract is held in this document, a later LO change does not require editing four records — it requires editing this section and re-deriving one.

### Lesson Type Contracts

**Decision D-3: three distinct quality contracts and three distinct definitions of done.** The 40 records are not rewritten to one standard. The bands are the audit's own: 20 theory (mean 4.23), 16 hands-on (3.08), 4 terminal (2.77) — a 1.46-point spread that a single contract would flatten in the wrong direction, by expanding healthy theory instead of repairing broken labs.

**THEORY (20 records: day-01, 02, 04, 05, 07, 08, 10, 11, 13, 14, 16, 17, 19, 20, 22, 23, 25, 26, 28, 29)**

Required arc — Concept → Mental Model → Problem / Why → Core Mechanics → Simple Example → Realistic Example → Edge Cases → Common Mistakes → Connection forward to Spring.

**This is an arc, not a heading template.** Records must not be restructured into nine mandatory headings. The band's best records satisfy it inside their own section shapes — Day 11's "stack is where you write down the work, heap is where the stuff lives" is a mental model embedded in a section about something else, and Day 01's JIT warm-up is a Why embedded in a mechanics section. A rewrite that converts Day 11 into nine labelled headings makes it worse. The reviewer asks "is each beat present and doing work?", never "is each heading there?".

Theory DoD:
- Every stated outcome has at least one demonstrating block. *(This is the gate Day 25 fails: `@Async` and `@Scheduled` are outcomes with zero code.)*
- Simple example → realistic example, in that order. `TOY_ONLY` applies only where the toy is the *only* example; a toy followed by a realistic one is the desired shape and is never flagged.
- Every `commonMistake` the record calls critical is reachable from an example or a practice.
- At least one forward bridge to where the idea returns in the Spring half, by record id.
- One closing synthesis beat consolidating what was learned — **currently absent from all 40 records** (audit item 31). Required for unit-final theory records, optional elsewhere.
- Zero prose claims about mechanisms the record never shows. *(Day 20's `@Version` and `Specification` prose-without-code is this defect; see D-5 tier assignment.)*

**HANDS-ON (16 records: day-03, 06, 09, 12, 15, 18, 21, 24, 27, 30, 31, 32, 33, 34, 35, 36)**

Required arc — Scope & context → Prerequisites by record id → Requirements → **Acceptance criteria** → Starter scaffold → Hazards → Self-check rubric → Deliverable list.

**The learner must write the code.** A hands-on record must not contain the full solution. The line: *interfaces, signatures, entity field lists, config, one worked slice of a repeated pattern, and test skeletons are scaffold; the business logic of the assigned requirement is the learner's work.* This is why Day 35's `checkout()` returning `null` is a defect and not a virtue — it is not withholding a solution, it is withholding the specification. A stub that returns `null` teaches nothing about what checkout must do; the repair is to replace the body with **observable behaviour** — the ordered steps, the invariants, the failure modes and the expected outcome per step — so the learner knows what to build and how to know it works, without being handed the implementation. `null` is never an acceptable artifact.

Hands-on DoD:
- **An acceptance criteria table exists.** Nine records currently have none (day-15, 18, 21, 24, 27, 30, 33, 34, 35) — the day-03/06/09 scaffolding was dropped after Unit 3 and never restored. Restoring it is one pass, using day-03/06/09's table shape and day-36's weighted-rubric shape.
- Every required deliverable traces to a record that teaches it, by id. Untraceable deliverables are either taught (if syllabus-mirrored, therefore mandatory) or explicitly scoped out with a reason.
- Zero `null`/empty-body placeholders standing in for a specification.
- Prerequisites list is true. *(Day 19's is currently false about what precedes it.)*
- Hazards name a mechanism the course teaches. *(Day 35 raises oversell with no locking mechanism — resolved by D-5 promoting Day 20's `@Version` prose to code.)*
- A self-check the learner can run before submitting.

**TERMINAL / EVALUATION (4 records: day-37 exam, day-38 exam, day-39-64 ojt, day-65-66 evaluation)**

Required elements — scope (what is examinable, by record id) → prerequisites → assessment criteria → rubric with level descriptors → explicit pass/fail line → required artifact → **no new knowledge**.

The no-new-knowledge rule is the band's defining constraint: a terminal record may only assess what an earlier record taught. It is currently violated in the most damaging way available — **Day 38's premise is false.** It extends a "completed" capstone that Day 33/34/35 do not deliver, and no record discloses it, so 300 graded minutes assume a system that does not exist. Terminal records are therefore rewritten **last**, after the capstone is real.

Terminal DoD:
- Every assessed item maps to a teaching record by id; anything unmapped is cut or taught upstream.
- Rubric has level descriptors, not just weights. *(Day 65-66's evaluator rubric has none; Day 38's self-rubric has neither.)*
- Pass/fail stated as a threshold two evaluators would apply identically.
- Required artifact named concretely.
- Zero content that appears for the first time here.
- Day 39-64 and Day 65-66 keep their refusals to invent FSU conventions or an official grading scale; missing authority stays disclosed, never filled with plausible invention.

### SQL / Database Foundation

**Decision D-4: add a SQL foundation as sections inside Day 19, Day 20 and Day 32. No new Unit, no new Day.** Depth is strictly bounded: enough SQL to make the course's own performance claims checkable, and nothing more.

**Evidence that the gap is total.** Searching the whole corpus: **zero** `INNER JOIN` / `LEFT JOIN` / `RIGHT JOIN` / `OUTER JOIN`, **zero** `CREATE INDEX` / `@Index` / `EXPLAIN` / B-tree, **zero** `CREATE TABLE` / `PRIMARY KEY` / `FOREIGN KEY`. Meanwhile `JOIN FETCH` appears in day-19, day-23 and day-24; N+1 is diagnosed in day-02, day-19, day-20 and day-23; `@EntityGraph` and batch fetching are taught; day-21 requires Flyway `V1__init.sql` → `V2__seed_data.sql`; day-24 requires a before/after performance benchmark; day-32's syllabus row 54 assigns "Database design". **Eight downstream demands rest on a foundation that was never laid.** A learner is asked to conclude that one query is faster than another without ever having been shown what a query is.

**No catalog source teaches it.** Checked all 111 source notes: not one covers SQL syntax, JOIN semantics or indexing. Day 19 and Day 20's four resources each are Cascade, Eager/Lazy, Pagination-Sorting, Auditing, Derived queries, Projections — all JPA-level.

**Sourcing gate — mandatory, blocking Wave 3.** Foundational SQL claims **may not be authored on `authoring.limitations` disclosure alone.** Disclosure is the correct mechanism for a residual gap in an otherwise sourced record; it is not a licence to invent a foundation that three records and eight downstream deliverables then rest on. Before Day 19, Day 20 or Day 32 is rewritten, an **explicit sourcing step against authoritative references** must complete and add read notes to the pipeline:

| Requirement | Detail |
| --- | --- |
| **What must be sourced** | Relational basics (table/row/column/PK/FK); `SELECT`/`WHERE`/`ORDER BY`/`LIMIT`; `INNER` vs `LEFT JOIN` semantics and their effect on row count; index structure and lookup-vs-scan cost, including write and storage cost; transaction isolation levels and the anomalies they prevent |
| **Acceptable authority** | Primary database documentation for the engine the course uses, the SQL standard, and the Hibernate/Spring Data reference where it explains emitted SQL. Vendor-neutral where the claim is standard; explicitly engine-scoped where it is not — index defaults in particular differ by engine, and the record must say which one it describes |
| **Pipeline path** | New resources enter the same way every other source does — through the manifest and `content/source-notes/*.json` with `read.status == "read"`, `facts[].locator` and `read.relevantHeadings` populated. This makes the SQL sections **citable under the existing gates**, with no gate change and no borrowing |
| **Catalog constraint** | `course-catalog.json` is generated from the workbook, so new resources **cannot** be attached to a lesson's `resourceIds` by editing it. `_validate_sourceusage_entry` requires the cited resource to be linked to the citing lesson — so this gate's resolution requires either a workbook-level addition (outside content scope, needs its own approval) or an explicitly approved sourcing mechanism. **This is an open blocker, and it is the reason Wave 3 cannot start on approval of this plan alone** |
| **Fallback if the gate cannot close** | The SQL foundation is **descoped rather than authored unsourced**, and the consequence is accepted explicitly: Day 21's Flyway DDL and Day 24's benchmark are re-specified to demand only what the corpus can support, and the gap is disclosed to the learner as a known prerequisite they must acquire elsewhere. Descoping is worse for the course than sourcing it — but it is honest, and it is better than a foundation nobody can check |

`authoring.limitations` still records what remains unsourced after the gate closes. It is the record of a residual, not the justification for the foundation.

**Placement analysis (Day 18/19/20/21/32).**

| Candidate | Case for | Case against | Verdict |
| --- | --- | --- | --- |
| **Day 18** (Lab 6, MVC) | Earliest possible | Pre-JPA; no data layer exists yet, so SQL would be knowledge without use. It is also a hands-on record — new foundational teaching does not belong in a lab | Rejected |
| **Day 19** (Entity Design & Relationships, 4.25) | **Earliest point of need.** It is where relationships, `JOIN FETCH` and N+1 first appear; a learner meets the word "join" here for the first time | Its `syllabusAssignments` is mirrored-empty but its 150 minutes are fully committed to entity mapping | **Accepted — minimal layer** |
| **Day 20** (Query, Transaction & Patterns, 4.33) | **The only teaching record in Unit 7 with an empty `syllabusAssignments` and a 30-minute "Guides/Review" slot** (trainers PhonNT1 / LinhNT102, no Assignment row) — a genuine structural free slot. It already owns query and transaction semantics | Already a dense record | **Accepted — main host, and the index mental model lands here** |
| **Day 21** (Assignment 7, 2.50 lowest) | It is where SQL is first *required* (Flyway DDL) | Lowest-scoring record in the corpus and a hands-on record; adding foundational teaching to the weakest lab compounds the problem it already has | Rejected as host; consumes the foundation |
| **Day 32** (System Design, 3.25) | **The syllabus itself assigns "Database design" here** (row 54), and the audit flags `PREREQUISITE_GAP` "relational design/SQL never taught, required here" | Late — Unit 7 has already asked for performance reasoning by then, so this cannot be the learner's first encounter with an index | **Accepted — deepening / database-design layer only** |

**Sequencing requirement: the index mental model must be complete at Day 20, before Day 24.** Day 24 requires a before/after performance benchmark, which is unattemptable without knowing what an index does and what a query costs. So Day 20 — not Day 32 — is where the learner first meets indexes, and it must be a *usable* model, not a mention: what an index is structurally, why a lookup beats a scan, which columns get one by default (PK, and generally **not** FK), and what an index costs on write and in storage. **Day 32 is a deepening layer: index placement in a concrete schema design, alongside normalisation and key choice.** By Day 32 the learner has already used indexes at Day 20 and benchmarked with them at Day 24. Any wave that leaves the first index encounter at Day 32 has mis-sequenced the foundation and fails Wave 3's gate.

**Depth decisions.**

*In scope, Day 19 (minimal layer, one section):* what a table / row / column / primary key / foreign key is, and the **one** mapping that makes JPA legible — an entity is a table, a field is a column, a `@ManyToOne` is a foreign key. Plus: what SQL the ORM emits for a `findById`. This is the smallest possible amount of SQL that makes the rest of Unit 7 readable.

*In scope, Day 20 (main host, the 30-minute slot):* `SELECT` with column list, `WHERE` with `AND`/`OR` and comparison, `ORDER BY`, `LIMIT`; **`INNER JOIN` vs `LEFT JOIN` and why the choice changes the row count**; what an index is (a B-tree lookup instead of a full scan), which columns get one by default (PK, and *not* FK in most engines), and the cost side — writes and storage. Then the payoff the course has been assuming: **read the SQL Hibernate logs, count the queries, and see N+1 as a row of identical `SELECT`s.** This is the section that makes day-23's and day-24's performance work possible.

*In scope, Day 32 (design level, one section):* normalisation to 3NF stated practically, choosing keys, modelling the capstone's relationships, and where indexes belong in the Spendwise-shaped schema. No new syntax.

*Where the SQL-level transaction model appears:* **Day 20**, adjacent to the SQL section and before `@Transactional`. Isolation levels and the anomalies they prevent (dirty read, non-repeatable read, phantom) are taught at the SQL level exactly once, then `@Transactional` is presented as the Spring-level control over them. Day 35's resource `res-2c011d89d6e0` (Transaction Propagation & Isolation) is the deep treatment and stays at Day 35 — Day 20's layer is the SQL-level prerequisite for it, authored and disclosed, because **Day 20 has no `@Transactional` and no locking resource of its own** (its four are Cascade, Eager/Lazy, Pagination-Sorting, Auditing). That mechanical fact is why Day 20's best material is prose-only, and D-5 addresses the code side.

*Explicitly out of scope:* stored procedures, triggers, views, window functions, CTEs, query-plan reading beyond "index scan vs full scan", `GROUP BY`/`HAVING` aggregation pipelines, self-joins, subquery optimisation, database administration, replication, sharding, and any engine-specific dialect beyond what the course's own examples already use. **This is not an SQL course.** The test for every candidate line: does the course later ask the learner to reason about it? If not, it is out.

**Consequences:** three records gain one section each (Day 19 LIGHT-plus, Day 20 MEDIUM, Day 32 MEDIUM); Day 21's `PREREQUISITE_GAP` closes without editing Day 21's locked syllabus row; day-19/20/32's `authoring.limitations` each gain a disclosure that the SQL layer is authored without a catalog source; total added volume is bounded by the 30-minute Day 20 slot plus two shorter sections, so the corpus does not tip toward SQL.

### Code Validation Strategy

**Decision D-5: four snippet classes with four different validation strategies, and a tiered compile fixture rather than one monolithic classpath.** No build script is modified in this task; the tiers are specified for a later implementation task.

**Measured baseline.** 746 blocks; code languages java 104, text 11, properties 1, dockerfile 1. `_compile_java_snippets` runs `javac --release 17 -d <out> <snippet>` **with no `-cp`**, and only attempts blocks where `language == "java"` **and** `compile is True`. Result: **(java, compile=True) = 41, (java, compile=False) = 63.** All 41 compiled blocks are day-01 … day-12. **Every Java block from day-13 onward ships unverified** — which is precisely why Day 22's `SecurityConfig` reached publication as an **open API**, Day 19's `Product`/`ProductEntity` mismatch survived, and Day 24's missing `org.hibernate.annotations` imports survived. The audit states it plainly: 41 of 117 code blocks were compile-checked; 76 rest on review alone.

**Snippet classification.**

| Class | What it is | Count / examples | Validation strategy |
| --- | --- | --- | --- |
| **PURE JAVA** | Compiles against the JDK alone | The 41 already at `compile=True`, **plus 4 currently mislabelled `compile=False`** | `javac --release 17`, no classpath. Already works — the only action is relabelling |
| **SPRING** | Needs Spring / Jakarta / test / logging types | The bulk of the 63 `compile=False` blocks from day-13 on | Compile against a **pinned fixture classpath** (Spring Boot 3.x BOM-resolved jars) added in a later task. Until it exists: mandatory two-author review against the baseline lint |
| **CONFIG** | `properties`, `dockerfile`, YAML, SQL DDL | 1 properties, 1 dockerfile, plus the SQL blocks D-4 adds | Parse/lint, never compile. `properties` key-syntax check; Dockerfile instruction check; SQL blocks validated by syntax parse only, since no engine is in the pipeline |
| **PSEUDOCODE** | Illustrative, deliberately incomplete — templates, `<template>` blocks, partial signatures, ellipsis bodies | The 11 `text`-language blocks and the template-heavy day-31/32/39-64/65-66 blocks | **Must be explicitly marked, not silently `compile=False`.** Excluded from compilation by declaration, and required to be visually distinguishable so a learner never copies one expecting it to run |

**The `compile=False` audit is the point.** Today `compile=False` conflates four different things: "needs Spring", "is pseudocode", "is config", and "nobody checked". That ambiguity is the actual defect — it makes the 63 unverified blocks indistinguishable from the deliberately unverifiable ones. Every `compile=False` block must be reclassified into SPRING, CONFIG or PSEUDOCODE, so that "unverified" becomes a state the pipeline can report rather than a silence.

**Four blocks are mislabelled and need no Spring at all** — they are PURE JAVA today and are the cheapest verification wins in the corpus:

| Block | What it actually needs |
| --- | --- |
| `day26-blk-14` | Nothing but a stub class — compiles as-is |
| `day35-blk-15` | Nothing but a stub class — compiles as-is |
| `day28-blk-5` | `junit-jupiter` only |
| `day29-blk-6` | `slf4j-api` only |

**Tiered fixture (specified, not implemented):**

- **Tier 0 — JDK only.** The 41 existing + `day26-blk-14` + `day35-blk-15`. No classpath. Available immediately.
- **Tier 1 — test libraries.** `junit-jupiter`, `assertj`, `mockito`. Unblocks `day28-blk-5` and most of day-28/day-36's test snippets.
- **Tier 2 — logging.** `slf4j-api`. Unblocks `day29-blk-6` and day-29's logging material.
- **Tier 3 — Spring / Jakarta.** `spring-context`, `spring-web`, `spring-webmvc`, `spring-security-*`, `spring-data-jpa`, `jakarta.persistence-api`, `jakarta.validation-api`, `spring-boot-*`, versions pinned to the Boot 3.x BOM. This is the tier that would have caught Day 22.

Tiers exist so that no block waits on the hardest fixture. A monolithic "one classpath with everything" approach would gate all 63 blocks on Tier 3 and, worse, would let a Tier-0 snippet accidentally compile because an unrelated jar was on the path — which hides exactly the kind of missing-import defect found at Day 24.

**Baseline lint stays and is extended in scope, not in rules.** `JAVA_POST_17_PATTERNS` (`STR."`, `case X(...) when`, `Thread.ofVirtual(`) and `SPRING_LEGACY_PATTERNS` (`javax.persistence`, `javax.validation`, `WebSecurityConfigurerAdapter`) already run on every block regardless of `compile`, and `COPIED_RUN_THRESHOLD = 300` normalized chars guards against transcribing source material. These are the only checks currently covering the 63 unverified blocks; they remain the floor until Tier 3 exists.

**Consequences:** relabelling the four blocks and marking PSEUDOCODE are content edits inside **Wave 0b**, immediately verifiable at their stated tier; the Tier 1–3 fixtures are a **build-pipeline change recorded here and deliberately not implemented** — per the phase constraints, no build script, validator or test is modified in this task, and when that work happens it declares its own scope (`tools/`, tests, `docs/`) in a separately-approved task. Until Tier 3 lands, any wave that adds or edits Spring Java carries a mandatory review step, and Wave 1's Day 22 fix is reviewed by hand against the Spring Security 6 lambda-DSL semantics rather than by compilation.

## Capstone Repair Strategy

Five records — Day 30, 33, 34, 35, 38 — form one failure chain. Each is repaired as `Prerequisite → Theory → Artifact → Sprint → Evaluation`: the prerequisite that must exist first, the record that teaches it, the concrete artifact the learner receives, the sprint requirement it satisfies, and how it is evaluated. A repair is not complete until all five links exist.

**Two hard constraints shape every row.**

First, **`syllabusAssignments` is catalog-mirrored for Day 21, 24 and 30 but absent for Day 31–36.** Only 20 of 40 records have any `syllabusAssignments` at all: bare `{"row": N, "text": "Assignment"}` for day-01/04/07/10/13/16/19/22/25/28, and full briefs for day-03/06/09/12/15/18/21/24/27/30. **Day 31 through Day 38, day-39-64 and day-65-66 have none** — their "briefs" are authored lesson text. Consequence: **the sprint briefs are freely editable**, while Day 30's row-52 deliverables ("JaCoCo coverage report ≥ 75%", "GitHub Actions CI: build → test → docker build"), Day 21's row-37 ("Flyway migration V1__init.sql → V2__seed_data.sql", "@DataJpaTest integration test") and Day 24's row-42 ("Register + Login + Refresh + Logout (Redis blacklist)", "Benchmark before/after optimize") **cannot be cut** without breaking `_validate_catalog_mirror`. They must be taught.

Second, **the self-issued-JWT promise is in the workbook, not just in lesson prose.** Day 33's syllabus row 55 outline reads "Auth module (register, login, JWT)", and Day 31's authored API contract promises `POST /api/auth/login`. The syllabus cannot change. So the auth reconciliation must **keep self-issued JWT as the capstone's auth story** and adjust Day 33's OAuth2-Resource-Server configuration, not the reverse — even though `res-65703b737426` (OAuth2 Resource Server JWT, shared by day-22/24/33) is the only *sourced* canonical option. This inverts the recommendation an unsourced reading would produce, and matches what Day 22–24 actually teach.

**Auth sourcing gate — mandatory, blocking the Day 22 and Day 33 rewrites.** The decision to keep self-issued JWT is approved because the syllabus requires `register / login / JWT`; it is **not** approval to author the flow unsourced. `res-65703b737426` documents Resource Server *validation*. It does not document issuance — creating a signed token at login, choosing and holding a signing key, setting and checking expiry, or the refresh/rotation and revocation path Day 24's row 42 requires.

| Gate condition | Requirement |
| --- | --- |
| **Trigger** | Before Day 22 or Day 33 is rewritten, the current sources are checked against the canonical flow: token issuance at login, signing-key management, expiry and clock skew, validation on each request, refresh-token rotation, and logout/revocation |
| **If sources do not support it** | An **explicit sourcing step against authoritative references** runs first, and its notes enter the pipeline through the manifest and `content/source-notes/*.json` exactly as any other source does. Acceptable authority: the Spring Security reference for the parts it covers, the Spring Authorization Server reference where issuance is in play, and the JWT/JWS specifications for token structure and algorithm choice. This is the same mechanism and the same catalog constraint as the SQL gate in **D-4** — new resources cannot be attached by editing the generated `course-catalog.json`, so closing this gate needs the same approved sourcing mechanism |
| **No custom crypto — absolute** | The course must never author a hand-rolled signing, hashing or token format: no manual HMAC assembly, no bespoke base64 token layout, no invented key-derivation, no home-made password hashing. Issuance and validation use the framework's library primitives and a standard algorithm; password storage uses the framework's `PasswordEncoder` with a standard adaptive hash. A code block that constructs or verifies a token by hand fails review regardless of whether it works |
| **If the gate cannot close** | The canonical flow is **not** authored from memory under `authoring.limitations`. The record is held at the gate and the blocker is escalated, because an unsourced auth foundation is the one gap in this corpus that can teach a learner to build something insecure |

**Dependency, and it is strict: `Day 22 security foundation → Day 24 authorization / testing → Day 33 register-login-JWT artifact`.** Day 22 establishes the security foundation — filter chain, authentication, what a JWT is, how it is issued and validated, key handling. Day 24 builds authorization and the testable service on top of it: role/method-level access, the refresh and Redis-blacklist path of row 42, and the tests that prove the endpoints behave. Only then does Day 33 assemble the artifact — the register/login/refresh/logout module — **introducing no new auth theory.** Day 33 cannot be rewritten before Day 22 and Day 24 are correct, and no wave may schedule it earlier; see `## Dependency Graph` and Wave 5.


Also load-bearing: **`content/spendwise-project.json`'s `lessonMap` marks day-33/34/35/36 as `applicationType: "theory"`**, so none of this touches the approved Spendwise track.

### Day 30 — Production Readiness (2.58, HEAVY)

Four of seven deliverables are required and taught nowhere: JaCoCo ≥75%, traceId propagation, Prometheus metrics, CI pipeline. Two of them are in the locked row 52.

| Link | Resolution |
| --- | --- |
| **Prerequisite** | Day 28's testing content (4.25, strong) for coverage; Day 29's MDC/structured-logging material (4.33, strong) for traceId; Day 29's Docker material for the CI build step |
| **Theory** | **Day 28** gains a JaCoCo section: what line/branch coverage measures, how to read the report, and why 75% is a floor not a goal. **Day 29** gains traceId propagation as a section extending its existing MDC material — the adjacency the audit identified — and a GitHub Actions section (`build → test → docker build`) attached to its Docker content. Prometheus metrics stay in Day 29's monitoring section, promoted from mention to demonstrated `/actuator/prometheus` scrape with one custom metric |
| **Artifact** | A `jacoco` plugin config block + a report-reading walkthrough (Day 28); an MDC filter that injects and propagates a traceId through a request and into the log line (Day 29); a `.github/workflows/ci.yml` (CONFIG class, lint-validated); an actuator/Prometheus config + one `@Counted`-style custom metric (Day 29) |
| **Sprint** | Day 30's four deliverables become attemptable as written, with row 52 untouched. Day 30 itself is rewritten from a shell around untaught requirements into a lab that integrates them, plus its own acceptance table |
| **Evaluation** | Day 30's acceptance table states the ≥75% threshold explicitly and **Day 38 is reconciled to the same number** — the audit's "silently dropped at Day 38" defect. Day 36's rubric references the same threshold |

Also fixed here: `day30-ref-6` retargeted from Day 36 to the originating record; the jar-layers contradiction against Day 35 and its own Dockerfile resolved; `@MockBean` → `@MockitoBean` aligned with Day 28.

### Day 33 — Development Sprint 1 (3.08, HEAVY)

The record's brief and Day 31's contract promise a login endpoint returning a JWT; the record configures OAuth2 Resource Server with no authorization server anywhere in the corpus, and ends on `.oauth2ResourceServer(oauth2 -> oauth2.jwt(jwt -> {}))` — an empty configuration.

| Link | Resolution |
| --- | --- |
| **Prerequisite** | Day 22 (Authentication + JWT, 4.08) and Day 24 (Auth Service lab, 3.67) — the self-issued-JWT path the course actually teaches. **Both must be through the auth sourcing gate above and rewritten first**, in the order `Day 22 → Day 24 → Day 33` |
| **Theory** | Day 22's `SecurityConfig` fix (Wave 1) plus Day 24's refresh-token and Redis-blacklist repair. **Day 33 introduces no new auth theory** — the no-new-knowledge principle applied to a sprint record. If the gate shows Day 22 cannot source issuance, Day 33 is held, not authored around it |
| **Artifact** | `day33-blk-10` rewritten: keep resource-server-style JWT *validation* (which `res-65703b737426` sources) but wire it to the **course's own issuer** from Day 22 — a configured decoder over the application's signing key, with the empty `jwt -> {}` lambda replaced by a real decoder/converter. The register/login/refresh/logout flow comes from Day 24 by reference, not re-explanation |
| **Sprint** | Sprint 1's auth module matches row 55's "register, login, JWT" and Day 31's `POST /api/auth/login`. Profile API and Category CRUD get acceptance criteria; both are within taught material |
| **Evaluation** | Day 36's defense and Day 38's practical inherit one coherent auth story. Day 33's own acceptance table states the four endpoints and their expected status codes and token behaviour |

Constraint disclosed: `res-553bbd92e5d0` (Spring Data JPA reference) and `res-aa4cbb2b9a5c` (Spring Data sort) are **`unavailable`** for Day 33, so 2 of its 5 resources cannot be cited. Content leaning on them is authored with disclosure or drawn from Day 19/20 by internal reference.

### Day 34 — Development Sprint 2 (2.92, HEAVY)

Three independent defects: all four of Day 26's upload-security layers are lost (`day34-blk-6` calls `getOriginalFilename()`/`getContentType()` raw); search/filter/pagination is a bare `<template>` demanding untaught `Pageable + Specification`; Cart is a bare template.

| Link | Resolution |
| --- | --- |
| **Prerequisite** | Day 26 (4.58, the corpus's joint-best record) for upload security; Day 20 for `Pageable` and derived queries; Day 25 for caching |
| **Theory** | No new theory needed for uploads — Day 26 already teaches all four layers correctly. **`Specification` is deliberately not taught** (see D-6 class C): search/filter is re-specified against `Pageable` + derived queries + `@Query`, which Day 20 teaches and Day 20's own prose already names `Specification` without showing it — that prose mention is removed or marked out-of-scope so nothing dangles |
| **Artifact** | `day34-blk-6` rewritten to apply Day 26's four layers by reference (extension allowlist, content-type verification, size limit, path-traversal-safe storage name) rather than re-explaining them. `day34-blk-3` upgraded from `<template>` to a `Pageable`-based search/filter slice. Cart gets an interface + entity field list + one worked operation; the remaining operations are the learner's work |
| **Sprint** | Sprint 2 becomes attemptable, and stops teaching an insecure upload two records after teaching the secure one. Day 34's local-cache contradiction against Day 25's Redis is resolved in Day 25's favour |
| **Evaluation** | Acceptance table covering upload rejection cases, pagination correctness at boundaries, and Cart invariants |

Constraint disclosed: same two `unavailable` resources as Day 33, leaving Day 34 only File Upload + Caching as readable sources.

### Day 35 — Development Sprint 3 (3.50, MEDIUM)

`day35-blk-5`'s checkout is hollow — `loadCart` and `createOrderFromCart` return `null`, `clearCart` is empty — and the record raises the oversell hazard with no locking mechanism the learner has been shown in code.

| Link | Resolution |
| --- | --- |
| **Prerequisite** | Day 20's optimistic-locking prose — **which already teaches `@Version`, the `WHERE`-clause mechanism, `OptimisticLockException`, "prefer this by default", and pessimistic `SELECT ... FOR UPDATE`**, with a `commonMistake` and a two-thread `enhancedExercise`. Correction to audit item 4: this is not absent from the corpus, it is absent from *code* |
| **Theory** | **Day 20** promotes its `@Version` prose to a demonstrated block: the entity annotation, the emitted SQL with the version predicate, and the two-thread conflict outcome. Under D-5 this is a SPRING-class snippet needing Tier 3, so until the fixture exists it is authored under mandatory review. Day 20's transaction/isolation layer from D-4 sits directly beneath it |
| **Artifact** | `day35-blk-5`'s three placeholders replaced by **observable behaviour**: `loadCart` states its lookup and its empty-cart failure mode; `createOrderFromCart` states the ordered steps (validate stock → reserve → price → persist → return id) with the invariant that reserved stock never goes negative; `clearCart` states its post-condition. Signatures and the transaction boundary are given; the bodies remain the learner's work. Plus a worked `@Version` conflict slice showing what a retry looks like |
| **Sprint** | Sprint 3 has a working core specification and the oversell hazard becomes addressable with a mechanism Day 20 now demonstrates. The CSV duplication against Day 26 is resolved by reference (Day 26 is canonical; note that `res-ea68bcb99823` is linked to day-26 and day-35, **not** day-27) |
| **Evaluation** | Acceptance table with a concurrent-checkout case: two simultaneous orders against one unit of stock, exactly one succeeds |

### Day 38 — Final Practice (2.92, LIGHT)

The false-premise record. Its defect is entirely inherited, which is why it is LIGHT and last.

| Link | Resolution |
| --- | --- |
| **Prerequisite** | Waves 1–5 complete, so the capstone the exam extends actually exists |
| **Theory** | None — terminal band, no new knowledge |
| **Artifact** | Retarget `day38-ref-3` from Day 36 to Day 28; add weights and level descriptors to the self-rubric, aligned with Day 36's |
| **Sprint** | n/a |
| **Evaluation** | State concretely which capstone modules must be working (now a true statement), reconcile the testing expectation with Day 30's ≥75%, and add a 300-minute plan. If any Wave 5 repair is descoped, Day 38 gains an explicit disclosure instead — **an honest gap, never a false premise** |

Day 38 has **zero readable resources** (0/0), as do day-39-64 and day-65-66. All three are authored-with-disclosure by design and stay that way.

### Untaught-but-assessed topics — classification D-6

Five topics are graded or required but taught nowhere. Each is classified **A (add teaching)**, **B (optional / enrichment)** or **C (out of scope, and the demand removed)**. The governing constraint: **a topic in a catalog-mirrored `syllabusAssignments` row cannot be class C** — it must be taught. And no class-A topic is dumped into a single record; each lands where its prerequisite already lives.

| Topic | Class | Where it goes | Reasoning |
| --- | --- | --- | --- |
| **JaCoCo, coverage ≥ 75%** | **A** | **Day 28** (section), enforced at Day 30, reconciled at Day 36/38 | Day 30's row 52 is catalog-mirrored — "JaCoCo coverage report ≥ 75%" cannot be cut. Day 28 (4.25) already owns testing, so coverage is one section, not a new topic. No catalog source covers JaCoCo → authored with disclosure |
| **GitHub Actions CI** (`build → test → docker build`) | **A** | **Day 29** (section attached to its Docker material), consumed at Day 30, required again at Day 35 | Also row 52, also uncuttable. Day 29 already teaches the Docker build that CI's third step invokes, so the pipeline is a natural extension. CONFIG-class artifact (lint-validated, never compiled). Authored with disclosure |
| **Prometheus metrics / traceId propagation** | **A** | **Day 29** — traceId extends its existing MDC material; Prometheus promoted from mention to demonstrated scrape + one custom metric | Both are row-52 deliverables. Day 29 is the strongest adjacent record (4.33) and already has the MDC foundation the audit identified. Authored with disclosure |
| **`@Version` / `@Lock` (optimistic & pessimistic locking)** | **A** | **Day 20** — promote existing prose to code | **Correction to audit item 4:** this is not absent from the corpus. Day 20 already teaches `@Version` in the `WHERE` clause, `OptimisticLockException`, "prefer optimistic by default", and pessimistic `SELECT ... FOR UPDATE`, with one `commonMistake` and a two-thread `enhancedExercise`. Only the code block is missing. Day 35's oversell hazard and Day 36's rubric both require it, so class A is forced — but the work is one demonstrated block, not a new topic |
| **SQL / JOIN / index** | **A** | **Day 19** (minimal), **Day 20** (main, the 30-minute slot), **Day 32** (design level) — per D-4 | Eight downstream demands assume it, including day-21's mirrored Flyway DDL and day-24's mirrored benchmark. Zero catalog sources cover it, so it is the plan's largest authored-without-source commitment, split across three records so no single record tips toward SQL |
| **`Specification` / Criteria API** | **C** | Removed as a demand: Day 34's search/filter is re-specified on `Pageable` + derived queries + `@Query`; Day 20's dangling prose mention is scoped out | The only class-C ruling. `Specification` appears in **no** `syllabusAssignments` row — it entered the corpus through Day 34's authored brief and Day 20's prose, so nothing mirrored requires it. Day 20 teaches derived queries and `Pageable`, which satisfy every requirement Day 34 actually states. Teaching the Criteria API properly would cost a section in an already dense record to serve one unmirrored deliverable. It is scoped out explicitly, not silently dropped |

No topic is classified B. Every candidate either backs a mirrored deliverable (A) or backs nothing mirrored and can be removed cleanly (C); there is no topic in this set that is worth offering as optional enrichment, and marking a graded topic "optional" would reproduce exactly the gap the audit found.

## Assessment / Practice Strategy

### Hands-on acceptance contract

Every hands-on record gets an acceptance table with one row per requirement and these columns: **Requirement · Observable outcome · How the learner verifies it · Where it was taught (record id)**. A requirement whose "where taught" cell cannot be filled is a defect in the record, not in the learner — it is either taught upstream or scoped out with a reason.

Nine records need one built from nothing: **day-15, 18, 21, 24, 27, 30, 33, 34, 35** — the audit's item 14, nine consecutive hands-on records covering Unit 5 through Unit 12 with no definition of done anywhere. The shape already exists in the corpus at day-03 / 06 / 09 (acceptance tables) and day-36 (weighted rubric); this is restoration, not invention. It is executed as **one pass in Wave 4**, immediately after the SQL foundation and before the sprint band, so that each table can point at real teaching.

Verification must be something the learner can run: a command, a request with an expected status, a test that goes green, a log line that appears, a count that changes. "Works correctly" is not an acceptance criterion.

### MCQ contract

**Measured:** 66 multiple-choice practices, 90 self-check. Correct-answer position histogram from `correctChoiceIds`: **position 0 → 59, position 1 → 5, position 2 → 2 = 89.4% at option (a).** This is a generation artifact, and it means the MCQ layer currently measures whether a learner has noticed the pattern.

Contract for every MCQ:
- **Answer position is distributed — by safe rebalancing, never by blanket permutation.** There is no "permute all 66" pass in this plan. A mechanical shuffle of every item is rejected because option order carries meaning in some items and destroying it silently breaks them. Each item is first triaged:

| Class | Test | Treatment |
| --- | --- | --- |
| **Reorder-safe** | Options are mutually independent statements. No option references another ("both A and B", "neither of the above", "all of the above"), no option depends on position ("the first option", "(a) and (c)"), the options are not an ordered sequence (steps of a lifecycle, ascending values, chronological phases), and the stem does not read as ordered ("which comes first") | **Reorder.** Permute `choices` and update `correctChoiceIds` to match. Zero content change |
| **Positional semantics** | Any of the above holds | **Not reordered mechanically.** Either reviewed and left as-is with the reason recorded, or **deliberately rewritten** so the options become independent — which is a content edit, is diffed as one, and is reviewed as one |

- **Post-reorder verification is mandatory, per item.** After any reorder, three things are re-read together and confirmed consistent: the `choices` array (text and ids intact, nothing duplicated or dropped), the **correct answer** (`correctChoiceIds` still names the option that is actually correct — the answer key lives in `correctChoiceIds`, **not** in `choices[].correct`), and the **`solution` explanation** (any reference it makes to an option by letter, position or order still points at the right one). An item whose solution says "option (a) is correct" and now has the answer at (c) is a worse defect than the concentration it was fixing.
- **The ≤35% ceiling is a target, subordinate to correctness.** Target: no single position holds more than 35% of correct answers across the corpus (uniform over 4 options is 25%; the ceiling allows natural variation without allowing a pattern). But **quality and semantic correctness outrank the metric.** If the reorder-safe set is not large enough to reach 35% without touching positional-semantics items, the plan reports the residual number and the reason — it does not force reorders to hit a figure. Missing the target with every item correct is a pass; hitting the target with a broken item is a fail.
- **Every distractor is plausible and diagnostic** — each encodes a specific misconception a learner in this course plausibly holds, ideally one drawn from that record's own `commonMistakes`. "None of the above" and joke options are not distractors.
- **The `solution` explains the misconception, not just the answer.** 59 solutions are currently a bare choice id or a one-line restatement. The distractors are usually the best part of the item and nothing currently explains why each fails. Required shape: why the correct answer is correct, then one clause per wrong option naming the misconception it represents. **This is content-quality repair, not a mechanical pass** — it requires understanding the item and the misconception, and it is reviewed as authored content.
- The `explanation` field connects the item back to the record's material by section.


**MCQ is not the target form.** The corpus is 66 MCQ / 90 self-check and that balance is deliberate — `coding` and `applied` practices exercise things multiple choice cannot. No record is converted to MCQ to make it measurable, and the four `type ∈ concept|predict-output|coding|applied` values keep their current spread (concept/MC 60, predict-output/MC 6, concept/SC 42, coding/SC 41, applied/SC 7). `predict-output` at only 6 items is under-used given how much of this corpus is about surprising runtime behaviour; waves may add a few, but not by converting existing items.

### commonMistakes coverage

**Measured:** 240 `commonMistakes` across 40 records; 159 `enhancedExercises`; `practices` is **hard-capped at 2..4** by the schema, and **36 of 40 records already sit at 4**. The arithmetic is decisive: coverage cannot come from adding practices. Day 29 (15 mistakes : 4 practices), Day 26 (10:4), Day 25 (9:4) and Day 28 (11:4) are structurally unable to test their own lists.

Contract:
- Each record marks its **critical** mistakes — those that produce silently wrong behaviour, a security hole, or data loss — as distinct from the merely stylistic.
- **Every critical mistake must be reachable from either a practice, a worked example that demonstrates the failure, or an `enhancedExercise`.** Examples and exercises are uncapped; this is where coverage comes from.
- Coverage is **reported, never build-failing.** The validation strategy below adds a coverage report that lists records with 0% or low critical-mistake coverage. It emits numbers, not errors — a record can have a legitimate reason, and a failing build would pressure authors to delete mistakes to go green, which is the same anti-pattern as deleting citation markers.
- **The `practices` cap stays at 2..4 — approved, not raised.** Coverage is routed through uncapped `enhancedExercises` and worked examples, so no wave depends on the cap. Any future proposal to change it is a separate schema decision with its own approval, its own validator review and its own build consequences worked out first.

Also in scope: the 18 records with exactly 3 `commonMistakes` — **day-03, 06, 09, 12, 15, 18, 21, 27, 30, 31, 32, 33, 34, 35, 36, 38, 39-64, 65-66**. The audit describes this as a thin template "from Day 31 onward"; it is in fact **the whole hands-on band**, including six Java-half records. Records durations here range from 150 to 3960 minutes with the same three-mistake shape, which is strong evidence of a template rather than of judgement. Each gets a mistake list proportionate to its actual hazards.

Duplicate pairs are removed where the audit found them: Day 26's #1/#4 and #3/#10 (10 stated, 8 distinct), Day 13's #1/#5 and #3/#7, Day 23's #1/#4 and #2/#7, Day 29's #3/#10 and #1/#12.

## Reference Repair Strategy

Two separate problems have been conflated under "the citation problem". They have different costs, different risks, and different owners, and this plan keeps them apart.

### Track 1 — REFERENCE STRUCTURE FIX (in scope, Wave 0a)

Repairing the corpus's internal bookkeeping so that markers resolve. Entirely inside the repository; no external fetch; no judgement about whether a source is any good. Steps 1–4 are **Wave 0a** and are structural. Step 5 is **Wave 0b** — it is authored content, not bookkeeping.

1. **Locator repair, 9 entries / 17 instances, first.** `day01-src-10`, `day17-src-4`, `day17-src-11`, `day22-src-1`, `day23-src-11`, `day24-src-6`, `day28-src-7`, `day33-src-7`, `day37-src-1`. Each locator is retargeted onto a heading that exists in that resource's `read.relevantHeadings`, or the underlying fact is split so both gates match. **Must precede Track 1 step 2**, because 8 of the 9 are inside Class A and `_slim_authored_lesson` raises on a published reference whose locator fails.
2. **Publication pass, 241 rows into 36 records.** One `reference` row per cited `sourceUsage` id that has none. Derivable from existing `sourceUsage` data; no prose changes.
3. **Orphan cleanup, 2 rows.** Published `citationId`s no citation ever uses — either cite them or drop the row.
4. **Internal reference retargeting.** `day38-ref-3` → Day 28 (currently Day 36), `day30-ref-6` → the originating record. Internal references need only a `description`, so these carry no citation debt.
5. **Empty `deliverable` slots, 7 records — Wave 0b.** day-13, 16, 17, 22, 23, 25, 26 have `deliverable` blocks containing only the word "Assignment" / "Guides" / "Review". Filling them is writing a deliverable, so it belongs with the assessment-quality work, not with the citation repair.

**Required outcome of Track 1 steps 1–4 (Wave 0a acceptance):** **unresolved citation markers = 0, locator failures = 0, dangling references = 0.** Not "≤ 4". Every one of the 919 marker instances either resolves to a published `reference` row whose locator passes both gates, or the marker itself is gone by an authored decision — retargeted to a source that does support the claim, or removed together with the repair of the claim it was propping up. **No known `[?]` survives Wave 0a.** A marker that cannot be supported is not a residual to be tolerated; it is a claim without a source, and the record is corrected rather than annotated.


### Track 2 — SOURCE QUALITY RESEARCH (out of scope here, classified only)

Judging whether the cited documents are the right documents, still say what the notes claim, and cover what the course teaches. **No external web research happens in this plan** — per the phase constraints, sources are classified, not fetched. Recorded for a future task:

- **15 of 111 resources are `unavailable`** and cannot be cited at all: `res-062b84a9042d` (day-07), `res-0851edc9dd41` (day-10), `res-10672cc3a9fa` (day-05), `res-39bc1924ee00` (day-31), `res-4bc225ad1d9e` (day-07), `res-553bbd92e5d0` (day-21/32/33/34 — the most damaging, 4 lessons), `res-62d9985bbc6f` (day-01/03), `res-9458879c2540` (day-04), `res-9b1feb8ea22f` (day-10/12), `res-aa4cbb2b9a5c` (day-33/34), `res-af7171222f9a` (day-32), `res-b73632f693f7` (day-10/12), `res-c246ae22f99a` (day-07), `res-ec467b92f9e7` (day-07), `res-f31ffcf74f40` (day-04).
- **Day 07 is the worst-hit record: 1 of 5 resources readable.** Then day-34 2/4, day-32 2/2 readable of 4, day-10 2/5, day-33 3/5, day-04 3/5, day-12 3/5.
- **Day 38, day-39-64 and day-65-66 have zero resources**, by design.
- **Locator drift is unverified.** This plan fetched nothing, so it cannot confirm that any cited document still contains the heading its read notes record. Every locator repair in Track 1 is therefore made against the **stored notes**, not against the live web, and that limitation is stated wherever it matters.
- The seven stranded outcomes of audit item 11 belong to Track 2's boundary: they are stranded because the *right* resource is linked to a different lesson (e.g. `res-2c011d89d6e0` Transaction Propagation → day-35 only; `res-fa00cc21947b` Method Security → day-23 only; `res-97fce5fda99a` `@Scheduled` → day-27 only; `res-033c4bfa05f5` `@Async` → day-27/35 but **not** day-25; `res-b307e54a2685` Error Handling REST → day-32 only). Track 1 cannot fix these; Waves 1–6 handle each by authoring with disclosure. **Re-linking resources in the catalog is not an option** — the catalog is generated from the workbook.

Keeping the tracks separate matters because Track 1 is safe and high-volume while Track 2 is slow and requires external verification. Bundling them would make a mechanical 241-row fix wait on a research programme.

## Project Application Readiness

**`INSUFFICIENT_FOR_PROJECT_APPLICATION` is flagged on ten records — day-15, 21, 24, 27, 30, 33, 34, 35, 38, 39-64 — all in the hands-on and terminal bands, none in theory.** The theory band is application-ready as written and must not be touched to serve the project.

**Theory records are not rewritten into Spendwise tutorials.** A theory record teaches a mechanism; the project applies it. The connection is made by the existing Build While You Learn integration and by the record's forward-bridge sentence, not by replacing generic examples with Spendwise ones. Day 26 teaching upload security generically and Day 34 applying it to the project is the correct division of labour, and it is what makes Day 26 reusable.

**`lessonMap` is not modified.** `content/spendwise-project.json` holds 38 entries and is FINAL_APPROVED. Its day-33/34/35/36 entries are `applicationType: "theory"`, so the capstone repairs above touch nothing in the project track. This plan reviewed the mapping for correctness and found no wrong entry; the rule stands that `lessonMap` changes only on demonstrated error.

**Readiness after this programme, by band:**

| Band | Now | After |
| --- | --- | --- |
| Theory Units 1–10 (20 records, 4.23) | Ready as written | Unchanged, plus SQL foundation (day-19/20), JaCoCo/traceId/CI/metrics teaching (day-28/29), `@Version` in code (day-20), Day 22's `SecurityConfig` fixed |
| Ready with local repair — day-21, 24, 25, 27, 30's testing content | Blocked only by missing artifacts that exist in adjacent records | Resolved by disclosed authoring plus Track 1's reference completion |
| Not ready without new content — day-30, 33, 34, 35, and by inheritance 36 and 38 | Unattemptable as written | Resolved by the Capstone Repair Strategy above, in wave order |

**The three project-readiness gates a record must pass:** every deliverable traces to a teaching record by id; every deliverable has an observable acceptance criterion; and no deliverable depends on a resource that is `unavailable` without a disclosed authored substitute.

## Lesson Rewrite Matrix

Priorities are **CONTENT-CRITICAL / CONTENT-HIGH / CONTENT-POLISH** — never P0/P1/P2. "Audit Level" is the audit's rewrite level, carried verbatim. "Wave" is re-derived by dependency analysis (see `## Dependency Graph`), and deliberately does **not** follow the audit's priority order.

| Day | Title | Lesson Type | Audit Level | Content Priority | Primary Problems | Structural Dependency | Rewrite Scope | Validation Needed | Wave |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | JVM, JRE, JDK & Data Types | THEORY | LIGHT | CONTENT-POLISH | 10/15 markers unresolved; `day01-src-10` locator fails; Arrays section prose-only, no source; numeric-pitfall mistakes (#4/#5/#6) have no practice | D-1 | Locator fix + 10 reference rows; add numeric-pitfalls practice; give Arrays a worked example; MCQ reshuffle | REFERENCE, ANSWER DISTRIBUTION, PRACTICE | 0 → 2 |
| 02 | Operators & Control Flow | THEORY | LIGHT | CONTENT-HIGH | Stream intro snippet does not compile in either reading — first Stream code the learner sees; guard-clause block tells learner to compare a pair that does not exist; 3/4 practices on `switch` | D-5 tier 0 | Fix the snippet; supply the guard-clause pair; rebalance practices toward precedence/promotion/loops | CODE, PRACTICE, ANSWER DISTRIBUTION | 2 |
| 03 | Lab 1: StringCalculator | HANDS-ON | MEDIUM | CONTENT-HIGH | `SOLUTION_HANDED_OVER`; 3 commonMistakes | — | Withdraw the handed solution to scaffold; expand mistakes | PRACTICE, SCHEMA | 4 |
| 04 | Classes, Objects, Encapsulation | THEORY | LIGHT | CONTENT-POLISH | 2/5 resources unavailable; reference completion | D-1 | Reference rows; MCQ reshuffle; solution expansion | REFERENCE, ANSWER DISTRIBUTION | 0 → 2 |
| 05 | Inheritance, Polymorphism & Abstract | THEORY | LIGHT | CONTENT-POLISH | `PREREQUISITE_GAP` (interface/default → Day 07, try-catch → Day 08, generics → Day 08); 1/4 resources unavailable | — | Add forward-pointer notes for the three inversions; reference rows | REFERENCE, PREREQUISITE | 0 → 2 |
| 06 | Assignment 2: Employee Management | HANDS-ON | MEDIUM | CONTENT-HIGH | `SOLUTION_HANDED_OVER`; `PREREQUISITE_GAP` (generics/Stream/lambda → Day 08/10); 3 mistakes | — | Scaffold-not-solution; declare the forward deps; acceptance table already present, tighten | PRACTICE, PREREQUISITE | 4 |
| 07 | Interface, Inner Classes & Enums | THEORY | MEDIUM | CONTENT-HIGH | `DEFINITION_DUMP` (inner classes + enums); **4 of 5 resources unavailable** — worst-sourced record in the corpus | Track 2 | Convert definition dumps to worked examples; disclose the sourcing gap in `authoring.limitations` | REFERENCE, LO | 2 |
| 08 | Generics, Collections & Exception | THEORY | LIGHT | CONTENT-POLISH | `BAD_DUPLICATION` (two anti-pattern warnings); 10 reference rows missing | D-1 | Merge the duplicate warnings; reference rows | REFERENCE | 0 → 2 |
| 09 | Lab 3: Custom Collection & Exception | HANDS-ON | MEDIUM | CONTENT-HIGH | `MISSING_BACKEND_CONNECTION` — hand-built `DataAccessException` never connected to Spring's `@Repository` translation, the payoff the lesson sets up; `SOLUTION_HANDED_OVER` | — | Close the bridge with a forward reference to Day 13/19; scaffold-not-solution | PREREQUISITE, PRACTICE | 4 |
| 10 | Lambda & Stream API | THEORY | LIGHT | CONTENT-POLISH | 3/5 resources unavailable; reference completion | D-1, Track 2 | Reference rows; disclose sourcing gap | REFERENCE | 0 → 2 |
| 11 | Concurrency & File I/O | THEORY | LIGHT | CONTENT-POLISH | **4.58 — joint-best record.** 13 reference rows missing; internal contradiction commonMistake #1 vs body | D-1 | **Reference completion + the one contradiction only.** Used as the mental-model template for the corpus | REFERENCE | 0 |
| 12 | Assignment 4: Data Processing Pipeline | HANDS-ON | HEAVY | CONTENT-HIGH | **2.58 — weakest of the Java half.** `INSUFFICIENT_FOR_PROJECT_APPLICATION` (JMH, Stream transform, accumulator); `MISSING_BACKEND_CONNECTION` (JSON → Jackson Day 16); 2/5 resources unavailable; 3 mistakes | D-3 hands-on contract | Full hands-on rebuild: scope, acceptance table, hazards, self-check; specify JMH or scope it out; bridge JSON to Day 16 | PRACTICE, PREREQUISITE, PROJECT | 4 |
| 13 | Spring Boot Fundamentals & Bean Lifecycle | THEORY | LIGHT | CONTENT-POLISH | **4.42 — preserve.** `DEFINITION_DUMP` (architecture, stereotypes); `BAD_DUPLICATION` #1/#5 and #3/#7; empty `deliverable` | D-1 | Reference rows; merge duplicate mistakes; fill deliverable; thin the two definition dumps | REFERENCE, SCHEMA | 0 → 2 |
| 14 | Dependency Injection & Configuration | THEORY | LIGHT | CONTENT-POLISH | `BAD_DUPLICATION` (scope recap vs Day 13) | D-1 | Replace the recap with a back-reference; reference rows | REFERENCE | 0 → 2 |
| 15 | Assignment 5: Multi-module Notification | HANDS-ON | HEAVY | CONTENT-CRITICAL | **2.58.** Factory section contradicts itself; `PushSender` — the third required strategy — missing, so the lab cannot be completed from its own content; retry unspecified; no acceptance criteria | D-3 hands-on contract | Resolve the Factory contradiction against `prac-4` and exercise #1; supply `PushSender`; specify retry; acceptance table | PRACTICE, CODE, PROJECT | 4 |
| 16 | Controller & Request/Response | THEORY | LIGHT | CONTENT-POLISH | **4.42 — preserve.** `REFERENCE_GAP` severe (80%); `SOLUTION_HANDED_OVER` (`prac-2`); empty `deliverable` | D-1 | Reference completion; rewrite `prac-2` to stop returning a printed pattern; fill deliverable | REFERENCE, PRACTICE | 0 → 2 |
| 17 | Validation & Exception Handling | THEORY | LIGHT | CONTENT-POLISH | **4.42 — preserve.** `REFERENCE_GAP` severe; `day17-src-4` and `day17-src-11` locators fail; 9 reference rows missing; empty `deliverable` | D-1 | Two locator fixes + 9 rows; fill deliverable | REFERENCE | 0 |
| 18 | Lab 6: User & Task Management API | HANDS-ON | MEDIUM | CONTENT-CRITICAL | **2.75.** The constraint is annotated on the wrong class, so validation demonstrably does not fire as taught; `SOLUTION_HANDED_OVER` partial; Postman deliverable unspecified; validator-target vs `prac-3` contradiction; no acceptance criteria | D-5, D-3 | Move the constraint to the correct class and reconcile `prac-3`; specify the Postman deliverable; acceptance table | CODE, PRACTICE, PROJECT | 1 |
| 19 | Entity Design & Relationships | THEORY | MEDIUM | CONTENT-CRITICAL | `PREREQUISITES` string is **false** about what precedes it; `Product`/`ProductEntity` type mismatch means the sample does not compile; no SQL foundation beneath `JOIN FETCH`/N+1 | D-4, D-5 | Correct the prerequisites string; fix the type mismatch; **add the minimal SQL layer (table/row/PK/FK ↔ entity/field/`@ManyToOne`) — only after the D-4 sourcing gate closes**; the two code fixes are independent of the gate and may ship first | CODE, PREREQUISITE, REFERENCE | 1 (fixes) → 3 (SQL) |
| 20 | Query, Transaction & Patterns | THEORY | MEDIUM | CONTENT-CRITICAL | **4.33 but prose-only where it matters:** `@Version`/optimistic + pessimistic locking and `Specification` are taught in prose with **no code block**; misplaced cascade block; no `@Transactional` or locking resource among its four | D-4 (gate), D-5 tier 3 | **Main SQL host, behind the D-4 sourcing gate** (SELECT/WHERE/ORDER BY/LIMIT, INNER vs LEFT JOIN, **the complete index mental model — structure, lookup vs scan, what is indexed by default, write and storage cost**, reading Hibernate SQL logs, N+1 made visible) + SQL-level transaction/isolation layer + **promote `@Version` prose to code**; remove or scope-out the dangling `Specification` mention; relocate the cascade block. **The index model must be complete here — Day 24's benchmark depends on it and Day 32 must not be first contact** | CODE, REFERENCE, PREREQUISITE | 3 |
| 21 | Assignment 7: E-Commerce Data Layer | HANDS-ON | HEAVY | CONTENT-CRITICAL | **2.50 — lowest in the corpus.** 5 entities required against 2 supplied; Flyway and `@DataJpaTest` share one `note`; cascade/fetch has no artifact; `res-553bbd92e5d0` unavailable; **row 37 is catalog-mirrored so nothing can be cut**; no acceptance criteria | D-4, D-1, D-3 | Supply the 3 missing entities; split Flyway and `@DataJpaTest` into their own sections with worked artifacts; cascade/fetch artifact by disclosed authoring; acceptance table | SCHEMA, CODE, REFERENCE, PROJECT | 4 |
| 22 | Authentication with Spring Security + JWT | THEORY | MEDIUM | CONTENT-CRITICAL | **`SecurityConfig` as written ships an OPEN API**, never verified because `compile=False`; `day22-src-1` locator fails (`"Specifying the Authorization Server"`); config contradicts the lesson's own rules; empty `deliverable` | D-5, D-1 | Fix `SecurityConfig`; locator fix; fill deliverable; reconcile config against its own stated rules | CODE, REFERENCE | 1 |
| 23 | Authorization & JPA Performance | THEORY | LIGHT | CONTENT-POLISH | **4.33.** `REFERENCE_GAP` 79%; `day23-src-11` is the corpus's only Class-C citation; `BAD_DUPLICATION` #1/#4 and #2/#7; `SOLUTION_HANDED_OVER` (`prac-2`) | D-1 | 11 reference rows; resolve the Class-C entry; merge duplicate mistakes; rewrite `prac-2`; empty `deliverable` | REFERENCE, PRACTICE | 0 → 2 |
| 24 | Lab 8: Auth Service + Performance | HANDS-ON | MEDIUM | CONTENT-CRITICAL | Redis blacklist reduced to one `note`; refresh issuance/rotation never described; benchmark required with **no method** (no query counter, no timing harness, no sample size); missing `org.hibernate.annotations` imports; phantom `findAll()` override; `day24-src-6` locator fails; **row 42 mirrored — blacklist and benchmark cannot be cut**; no acceptance criteria | D-4 (benchmark needs SQL), D-1, D-3 | Full blacklist + refresh-rotation sections; **specify the benchmark method** (query counting via Hibernate statistics, timing, sample size, before/after table); fix imports and the phantom override; acceptance table | CODE, REFERENCE, PROJECT, PRACTICE | 4 |
| 25 | Caching & Async Processing | THEORY | LIGHT | CONTENT-HIGH | **4.50 — preserve structure.** `@Async` and `@Scheduled` are stated outcomes with **zero code** and no practice; mistakes #7/#8/#9 untested; `ProductQueryService.loadFromDatabase` returns `null` so the illustrated `unless = "#result == null"` has only one live branch; `res-033c4bfa05f5`/`res-97fce5fda99a` linked elsewhere | D-1, D-5 | Add `@Async` and `@Scheduled` artifacts by disclosed authoring; fix the `null`-returning sample; add practices for #7/#8/#9; empty `deliverable` | CODE, LO, PRACTICE, REFERENCE | 2 |
| 26 | File Upload/Download & External API | THEORY | LIGHT | CONTENT-POLISH | **4.58 — joint-best, preserve.** commonMistakes #1/#4 and #3/#10 duplicate (10 stated, 8 distinct); 11 reference rows missing; flat-directory traversal check unreconciled with Day 11's `normalize()` + `startsWith`; `day26-blk-14` mislabelled `compile=False` | D-1, D-5 | Reference rows; de-duplicate mistakes; reconcile or explain the traversal difference; relabel `day26-blk-14`; empty `deliverable` | REFERENCE, CODE | 0 → 2 |
| 27 | Assignment 9: Product & Order Features | HANDS-ON | MEDIUM | CONTENT-HIGH | Only 3 commonMistakes for a six-item brief, and the three live hazards of this exact assignment (`@Async` transaction boundary, multi-instance `@Scheduled`, cache-key collisions) are unmentioned; `new` collaborators contradict DI; `this::cancelOrder` self-invocation; inherited `WebClient` chain defect; thumbnail and CSV export unspecified; no acceptance criteria | D-3, D-1 | Add the three hazards; fix the DI and self-invocation violations; specify thumbnail and CSV (CSV canonical at Day 26); acceptance table | CODE, PRACTICE, PROJECT | 4 |
| 28 | Testing Spring Boot | THEORY | LIGHT | CONTENT-CRITICAL | **4.25.** `REFERENCE_GAP` 71%, 13 rows missing; `day28-src-7` locator fails; `@MockBean` contradicts its own prose; `SOLUTION_HANDED_OVER` (`prac-2`); `day28-blk-5` needs only junit-jupiter; **must gain JaCoCo teaching for Day 30's locked row 52** | D-1, D-5 tier 1, Capstone | Locator fix + 13 rows; `@MockBean` → `@MockitoBean`; **add JaCoCo section** (line/branch coverage, reading the report, why 75% is a floor); rewrite `prac-2` | REFERENCE, CODE, LO | 0 → 5 |
| 29 | Documentation, Logging, Monitoring & Docker | THEORY | LIGHT | CONTENT-CRITICAL | **4.33.** `REFERENCE_GAP` 69%, 11 rows missing; `BAD_DUPLICATION` #3/#10 and #1/#12; `SOLUTION_HANDED_OVER` (`prac-2`); 15 mistakes : 4 practices — structurally untestable; `day29-blk-6` needs only slf4j; **must gain traceId, CI and Prometheus teaching for Day 30's locked row 52** | D-1, D-5 tier 2, Capstone | Reference rows; de-duplicate; **add traceId propagation** (extends existing MDC material), **GitHub Actions `build → test → docker build`**, and promote Prometheus from mention to demonstrated scrape + one custom metric; mistake coverage via examples | REFERENCE, CODE, LO, PRACTICE | 0 → 5 |
| 30 | Lab 10: Production Readiness | HANDS-ON | HEAVY | CONTENT-CRITICAL | **2.58.** Four of seven deliverables (JaCoCo ≥75%, traceId, Prometheus, CI) taught nowhere; a shell around them; jar-layers contradiction vs Day 35 and vs its own Dockerfile; `@MockBean` vs Day 28; `day30-ref-6` wrong target; **row 52 mirrored — nothing cuttable**; no acceptance criteria | Day 28 + Day 29 first | Rebuild as an integration lab over the now-taught four; resolve jar layers; retarget `day30-ref-6`; acceptance table stating ≥75% | PROJECT, CODE, PRACTICE, REFERENCE | 5 |
| 31 | System Design & Project Kickoff | HANDS-ON | MEDIUM | CONTENT-HIGH | `BAD_DUPLICATION` (DispatcherServlet vs Day 16); duplicate title with Day 32; 3 mistakes / 4 practices / 2 exercises template; `res-39bc1924ee00` unavailable; its API contract promises `POST /api/auth/login` — load-bearing for Day 33 | D-2, Capstone | Replace the DispatcherServlet re-explanation with a back-reference; differentiate the title in-record; keep and honour the auth contract; proportionate mistakes | PROJECT, REFERENCE, PRACTICE | 5 |
| 32 | System Design & Project Kickoff *(dup title)* | HANDS-ON | MEDIUM | CONTENT-HIGH | `PREREQUISITE_GAP` — relational design/SQL never taught but required here (syllabus row 54 assigns "Database design"); ERD is a bare template; single `GlobalExceptionHandler` rule broken; 2/4 resources unavailable | **D-4** | **Design-level SQL section** (3NF stated practically, key choice, capstone relationships, where indexes belong); turn the ERD template into a worked model; fix the handler contradiction | PREREQUISITE, PROJECT, CODE | 3 |
| 33 | Development Sprint 1 | HANDS-ON | HEAVY | CONTENT-CRITICAL | Auth unreconciled — brief + row 55 + Day 31 contract promise self-issued JWT, record configures OAuth2 Resource Server with an empty `jwt -> {}` and no authorization server; profile API and Category CRUD unspecified; `day33-src-7` locator fails; 2/5 resources unavailable; nine of ten corpus prerequisite inversions are in this band; no acceptance criteria | Day 22 + Day 24 first; D-1 | **Keep self-issued JWT** (row 55 is unchangeable); rewire `day33-blk-10` to the course's own issuer with a real decoder; specify profile API and Category CRUD; locator fix; acceptance table | CODE, PREREQUISITE, PROJECT, REFERENCE | 5 |
| 34 | Development Sprint 2 | HANDS-ON | HEAVY | CONTENT-CRITICAL | All four of Day 26's upload-security layers lost — `day34-blk-6` uses `getOriginalFilename()`/`getContentType()` raw; `day34-blk-3` a `<template>` demanding untaught `Pageable + Specification`; Cart a bare template; local cache contradicts Day 25's Redis; `REFERENCE_GAP` 75%; 2/4 resources unavailable; no acceptance criteria | Day 26, Day 20, Day 25; **D-6 class C** | Apply Day 26's four layers by reference; re-specify search/filter on `Pageable` + derived queries (**not** `Specification`); scaffold Cart; resolve the cache contradiction toward Day 25 | CODE, PREREQUISITE, PROJECT | 5 |
| 35 | Development Sprint 3 | HANDS-ON | MEDIUM | CONTENT-CRITICAL | `checkout()` hollow — `loadCart`/`createOrderFromCart` return `null`, `clearCart` empty; oversell hazard raised with no locking the course shows in code; CSV escaping duplicates Day 26 divergently; jar layers contradict Day 30 and its own Dockerfile; `day35-blk-15` mislabelled `compile=False`; CI required, untaught; no acceptance criteria | **Day 20 `@Version` code first**; Day 26; Day 29 CI | Replace the three placeholders with observable behaviour (steps, invariants, failure modes); add a `@Version` conflict slice; CSV by reference to Day 26; resolve jar layers; relabel `day35-blk-15`; acceptance table with a concurrent-checkout case | CODE, PREREQUISITE, PROJECT | 5 |
| 36 | Final Defense | HANDS-ON | MEDIUM | CONTENT-HIGH | Largest record in the corpus and the most duplicative — Day 28/29/30/35 re-explained; becomes a wrong-target attractor for `day38-ref-3` and `day30-ref-6`; locking graded but (in code) never taught; `@MockBean` vs Day 28; `REFERENCE_GAP` 76%, 13 rows missing | D-2, Waves 1–5 complete | Replace re-explanations with back-references and spend the space on defense preparation; align to Day 20's now-coded locking; `@MockitoBean`; reference rows | REFERENCE, LO, PROJECT | 6 |
| 37 | Final theory | TERMINAL | MEDIUM | CONTENT-HIGH | **2.58.** `DEFINITION_DUMP` — the LO table is the entire record; 3 of 4 practices grade the structure of the reference documentation, none touches a technical idea from Day 01–36; only 2 commonMistakes for 36 days; revision map is one 5-row table with no Day pointers; `day37-src-1` locator fails | **D-2 rendering host**; Waves 1–5 | **Host the learner-facing LO definition table derived from this plan's canonical authoring contract** (the plan stays canonical; Day 37 is not the authoring source); build a Day-indexed, LO-clustered revision checklist from `lesson-index.json`; replace the two documentation-structure practices with technical ones; add a 60-minute plan. **Keep its citation handling unchanged — it is the corpus model** | LO, PRACTICE, REFERENCE | 6 |
| 38 | Final practice | TERMINAL | LIGHT | CONTENT-CRITICAL | **Premise is false** — extends a "completed" capstone Day 33/34/35 do not deliver, undisclosed; `day38-ref-3` → Day 36 should be Day 28; migration tooling named as a risk, never taught; self-rubric has no weights or descriptors; 0 resources | Waves 1–5 complete | State concretely which capstone modules must work (true after Wave 5); retarget `day38-ref-3`; reconcile the testing expectation with Day 30's ≥75%; weights + descriptors; 300-minute plan | PROJECT, LO, REFERENCE | 6 |
| 39-64 | OJT Phase | TERMINAL | MEDIUM | CONTENT-HIGH | Zero technical content for 3960 minutes; 5 of 6 blocks are `<template>`; no progression, no mid-phase checkpoint, no exit criteria; LO10/LO11 prose inconsistent with the catalog-derived table; example worklog row is Day 34's unimplemented `Pageable` deliverable; 0 resources | D-2 | Per-LO technical refresher with Day pointers; mid-phase checkpoint; exit criteria; apply the LO table; fix the worklog example. **Keep the refusal to invent FSU conventions** | LO, PROJECT, PRACTICE | 6 |
| 65-66 | Evaluation Phase | TERMINAL | MEDIUM | CONTENT-HIGH | **2.75.** 5 of 6 blocks `<template>`; no Java and no Spring in the course's final record; assessment narrows to LO10–LO12 unexplained after a phase collecting LO6–LO12; evaluator rubric has no level descriptors; no agenda for 600 minutes; 0 resources | D-2, Day 36/38 first | Explain or close the LO6–LO9 gap against the LO table; add level descriptors; add two technical defense questions; 600-minute agenda. **Keep the refusal to invent an official grading scale** | LO, PRACTICE, PROJECT | 6 |

**Priority distribution:** CONTENT-CRITICAL 14 (day-15, 18, 19, 20, 21, 22, 24, 28, 29, 30, 33, 34, 35, 38 — of which day-19/20/22/28/29 are critical for what they must *supply* downstream), CONTENT-HIGH 14 (day-02, 03, 06, 07, 09, 12, 25, 27, 31, 32, 36, 37, 39-64, 65-66), CONTENT-POLISH 12 (day-01, 04, 05, 08, 10, 11, 13, 14, 16, 17, 23, 26). Every CONTENT-CRITICAL record either blocks a deliverable, ships incorrect code, or states something false.

## Dependency Graph

Rewrite order is derived here and only here. **The audit's priority list is not the order** — it ranks by learner consequence, which puts Day 30/33/34/35 first, but those four are the *most* dependent records in the corpus and rewriting them first would mean rewriting them twice. The ordering rule is: **a record is rewritten only after every record it depends on is final.**

**Supply edges** (X must be final before Y is rewritten):

```
D-1 citation architecture ──► every record with markers (36 records)
D-1 locator repair (9)    ──► D-1 publication pass (241 rows)   [build raises otherwise]
D-2 LO authoring contract ──► Day 37 learner-facing table ──► Day 38, Day 39-64, Day 65-66
D-4 SQL sourcing gate     ──► Day 19, Day 20, Day 32        [no authoring before it closes]
D-4 SQL @ Day 19/20       ──► Day 21 (Flyway DDL), Day 24 (benchmark), Day 32, Day 34
Day 20 index model        ──► Day 24 (benchmark), Day 32 (deepening, not first contact)
D-5 tier 0 relabel        ──► Day 26, Day 35 (block labels)
D-5 tier 1 junit          ──► Day 28, Day 36 test snippets
D-5 tier 2 slf4j          ──► Day 29 logging snippets
D-5 tier 3 Spring fixture ──► every Spring Java edit  [NOT IMPLEMENTED — review substitutes]

Auth sourcing gate        ──► Day 22, Day 33            [no canonical flow authored before it closes]
Day 22 security foundation──► Day 24 authorization/testing ──► Day 33 register/login/JWT artifact
Day 20 @Version in code   ──► Day 35 (oversell), Day 36 (rubric grades locking)
Day 20 Pageable/derived   ──► Day 34 (search/filter, replacing Specification)
Day 22 SecurityConfig fix ──► Day 24, Day 33  [an open API must not propagate]
Day 24 refresh + blacklist──► Day 33 (auth module)
Day 26 upload security    ──► Day 34 (four layers by reference)
Day 26 CSV                ──► Day 35 (CSV by reference, canonical)
Day 25 Redis caching      ──► Day 34 (resolves the local-cache contradiction)
Day 28 JaCoCo             ──► Day 30 (row 52), Day 38 (threshold), Day 36 (rubric)
Day 29 traceId+CI+metrics ──► Day 30 (row 52), Day 35 (CI)
Day 19 prerequisites fix  ──► Day 20, Day 21
Day 31 auth contract      ──► Day 33  [POST /api/auth/login is load-bearing]
Day 33 + Day 34 + Day 35  ──► Day 36 (defense), Day 38 (premise), Day 39-64, Day 65-66
Day 36 rubric             ──► Day 38 (self-rubric alignment), Day 65-66 (descriptors)
```

**The auth chain is a three-link sequence, not a set.** `Day 22 → Day 24 → Day 33` is strict: Day 22 establishes the security foundation (filter chain, authentication, what a JWT is, issuance and validation, key handling); Day 24 adds authorization and the testable service over it (method/role access, refresh rotation, the row-42 Redis blacklist, and the tests that prove the endpoints behave); Day 33 only assembles the artifact and introduces no new auth theory. Two consequences the waves must honour: **Day 33 is never scheduled before Day 22 and Day 24 are final**, and **the auth sourcing gate applies at Day 22** — the earliest link — so a gate failure stalls the chain at its head rather than being discovered at Day 33.


**Inversions the graph exposes.** Nine of the corpus's ten prerequisite inversions sit in the day-33/34/35 band, and all nine are *forward* dependencies — the sprints require material that arrives later or never. This is why the sprint band cannot lead the programme regardless of how urgent it is: **every one of its repairs is downstream of a theory repair.** The remaining inversion band is day-05/06 (interface/default → Day 07, generics/Stream → Day 08/10), which is benign and handled with forward-pointer notes rather than reordering.

**Critical path**, longest chain in the graph, five links:

```
D-1 locators → D-5 relabel → Day 20 (SQL + @Version code) → Day 35 (checkout + locking) → Day 36 (rubric) → Day 38 (premise + threshold)
```

Nothing in Wave 6 can start before Day 20 is final, and Day 20 cannot start before **the D-4 sourcing gate closes** — approval of the placement decision is not enough on its own. **The D-4 sourcing gate is the single highest-leverage gate in this plan;** the auth sourcing gate is second, because it gates a three-record chain that terminates in the capstone.


**Records with no inbound dependencies** — rewritable at any time, which is why they absorb the mechanical waves: day-01, 02, 04, 05, 07, 08, 10, 11, 13, 14, 16, 17, 23.

## Rewrite Waves

Eight waves — **0a, 0b, then 1–6** — 3–6 records each for the rewrite waves. **No wave batches 20 records to look fast**; Wave 0a is corpus-wide by nature because it is one structural operation repeated, not 40 rewrites.

**The order is strictly sequential and there is no parallelism:**

```
Wave 0a → Review Gate → Wave 0b → Review Gate → Wave 1 → … → Wave 6
```

**Wave 0b does not run concurrently with Wave 1.** Each wave, 0a and 0b included, passes its own review gate before the next begins. The reason is that 0b changes assessment content and code-block classification across the same records Wave 1 rewrites for correctness; running them together would put two authored changes to one record in a single unreviewable diff, and Wave 1's hand-verification of `SecurityConfig` and the compile tiers depends on 0b's classification already being final and reviewed.

### Wave 0a — Citation Structural Repair

*No lesson is rewritten for content.* This wave repairs the corpus's citation bookkeeping — the structural half — and nothing else.

1. Confirm the approved structural decisions D-1…D-6 are in force (all approved; recorded in `## Review Gate`).
2. **Locator repair — 9 entries / 17 instances.** `day01-src-10`, `day17-src-4`, `day17-src-11`, `day22-src-1`, `day23-src-11`, `day24-src-6`, `day28-src-7`, `day33-src-7`, `day37-src-1`. **Strictly first** — 8 are inside Class A and publishing before repairing makes `_slim_authored_lesson` raise.
3. **Reference publication — 241 rows into 36 records.** Resolves the Class A + Class B markers.
4. Orphan cleanup (2 rows); internal retargets (`day38-ref-3` → Day 28, `day30-ref-6` → origin).
5. **Resolve every remaining marker to zero.** Any marker still unresolved after steps 2–4 — including the single Class C entry — is closed by an authored decision: retargeted to a source that supports the claim, or removed together with the repair of the claim it supported. Each such decision is recorded in the wave's diff rationale.

**Wave 0a acceptance — absolute, no residual allowance:**

| Criterion | Required value |
| --- | --- |
| Unresolved citation markers | **0** (from 579 of 919) |
| Locator failures against `build_site.py::_citation_locator_matches` | **0** (from 9 entries / 17 instances) |
| Dangling references — published `reference` rows no citation uses | **0** (from 2) |
| `validate_lessons.py` | Clean |
| `build_site.py` | Completes with no `ValueError` |
| Known `[?]` surviving the wave | **None.** Not "≤ 4", not "listed with a reason" |

### Wave 0b — Assessment Quality Repair + Code Classification

*This is content-quality work, not a mechanical pass.* Expanding a bare solution means understanding the item and the misconception behind each distractor; filling an empty deliverable means writing a deliverable. Both are authored and both are reviewed as authored content.

1. **MCQ answer-position rebalancing — safe, per-item, not a blanket permutation.** Triage all 66 items into reorder-safe and positional-semantics classes per `### MCQ contract`. Reorder only the reorder-safe ones; review or deliberately rewrite the rest. After every reorder, verify `choices`, the correct answer in `correctChoiceIds`, and the `solution` explanation together.
2. **Expand the 59 bare/short solutions** to explain why the correct answer is correct and, per wrong option, which misconception it encodes. **Authored content-quality repair.**
3. Fill the 7 empty `deliverable` slots (day-13, 16, 17, 22, 23, 25, 26) with real deliverables.
4. **Relabel the 4 mislabelled blocks** (`day26-blk-14`, `day35-blk-15` → tier 0; `day28-blk-5` → tier 1; `day29-blk-6` → tier 2) and classify every remaining `compile=False` block as SPRING / CONFIG / PSEUDOCODE.
5. Write the Tier 1–3 fixture specification into the repo's tooling notes. **Do not implement it.**

**Wave 0b gate:** `validate_lessons.py` clean; `build_site.py` completes; the 4 relabelled blocks compile at their stated tier; every `compile=False` block carries a classification; every reordered MCQ verified on all three axes; MCQ concentration ≤ 35% **or** the residual reported with the reason it cannot be reached without touching positional-semantics items — **quality outranks the metric**; each expanded solution reviewed as authored content.

**Records expected to require no further rewrite after Wave 0b:** day-11 and day-17 — their remaining audit findings are reference-only. This is an expectation, not a status. **Only a Review Gate may mark a record DONE.**


### Wave 1 — Records that ship something false or unsafe (4 records)

Ordered first on consequence, and possible first because none of them depends on new teaching.

- **Day 22** — fix `SecurityConfig` so it does not ship an open API. Reviewed by hand against Spring Security 6 lambda DSL; Tier 3 does not exist yet. **Scoped to the config defect only.** Day 22's *canonical auth flow* content — issuance, key handling, expiry, refresh — sits behind the auth sourcing gate and is authored in Wave 5's chain head, not here. Closing an open API is a safety fix and does not need the gate; teaching how to mint a token does.
- **Day 18** — move the constraint to the correct class so validation fires as taught; reconcile `prac-3`.
- **Day 19** — correct the false `PREREQUISITES` string; fix the `Product`/`ProductEntity` mismatch. *(SQL layer deferred to Wave 3.)*
- **Day 02** — fix the non-compiling Stream snippet, the first Stream code the learner sees; supply the missing guard-clause comparison pair.

Gate: each fix hand-verified against the baseline lint; day-22's config reviewed by a second reader; no downstream record edited.

### Wave 2 — The LIGHT theory band (6 records)

Cheap, independent, and it establishes the theory contract on the records that nearly satisfy it already.

- **Day 25** — `@Async` and `@Scheduled` artifacts (disclosed authoring; their resources are linked elsewhere); fix the `null`-returning `ProductQueryService` sample; practices for mistakes #7/#8/#9.
- **Day 26** — de-duplicate mistakes #1/#4 and #3/#10; reconcile the traversal check with Day 11's or state why they differ.
- **Day 23** — resolve the Class-C citation; merge duplicate mistakes; rewrite `prac-2`.
- **Day 07** — convert the inner-classes and enums definition dumps into worked examples; disclose 4-of-5 unavailable sourcing.
- **Day 13, Day 14** — thin Day 13's two definition dumps, merge its duplicate mistakes, replace Day 14's scope recap with a back-reference to Day 13.

Also closes here with no further work: day-01, 04, 05, 08, 10, 16 (Waves 0a/0b handled their findings; each gets a synthesis beat and a practice rebalance).

Gate: theory DoD applied to all six; no record grew in volume without a named finding justifying it.

### Wave 3 — The SQL foundation (3 records)

The structural wave. Nothing downstream of Unit 7 can be correct before this.

**Entry condition — the D-4 sourcing gate must be closed before this wave starts.** Approval of the Day 19/20/32 placement is not sufficient. The authoritative sourcing step defined in `### SQL / Database Foundation` must have completed and its read notes must be in the pipeline, or the wave does not start. **No foundational SQL claim is authored on `authoring.limitations` alone.** If the gate cannot close, the wave executes the descoping fallback instead of authoring unsourced material, and that is escalated as a scope change rather than absorbed quietly.

- **Day 20** — the main host: SELECT/WHERE/ORDER BY/LIMIT, INNER vs LEFT JOIN, **the complete index mental model** (structure, lookup vs scan, what is indexed by default, write and storage cost), reading Hibernate SQL logs, N+1 made visible; the SQL-level transaction/isolation layer; **promote `@Version`/pessimistic prose to code**; relocate the misplaced cascade block; scope out the dangling `Specification` mention. Uses the 30-minute "Guides/Review" slot. **The index model must be complete here, because Day 24's benchmark cannot be attempted without it.**
- **Day 19** — the minimal layer: table/row/column/PK/FK ↔ entity/field/`@ManyToOne`, and what SQL a `findById` emits.
- **Day 32** — **deepening / database-design layer, not first contact with indexes:** 3NF stated practically, key choice, capstone relationships, and index *placement* in a concrete schema — building on what Day 20 taught and Day 24 measured; ERD template → worked model; fix the `GlobalExceptionHandler` contradiction.

Gate: every SQL claim traceable to a sourced reference **and** a demonstrated example; the index mental model complete at Day 20 and verifiably upstream of Day 24; Day 32 reads as deepening, with no first-encounter index teaching in it; `authoring.limitations` on all three discloses only what remains unsourced *after* the gate; the out-of-scope list is present so depth cannot creep; Day 20 still reads as a JPA record, not an SQL record.


### Wave 4 — The hands-on band + the acceptance-criteria pass (6 records)

- **Day 21** (2.50, lowest) — 3 missing entities; split Flyway and `@DataJpaTest` into worked sections; cascade/fetch artifact by disclosed authoring.
- **Day 24** — Redis blacklist and refresh rotation as real sections; **specify the benchmark method** (Hibernate statistics query counting, timing, sample size, before/after table) — now possible because Wave 3 taught what a query costs; fix imports and the phantom `findAll()`.
- **Day 15** — resolve the Factory self-contradiction; supply `PushSender`; specify retry.
- **Day 12** (2.58) — full hands-on rebuild; specify or scope out JMH; bridge JSON to Day 16's Jackson.
- **Day 27** — add the three real hazards (`@Async` transaction boundary, multi-instance `@Scheduled`, cache-key collisions); fix the DI and self-invocation violations; specify thumbnail and CSV.
- **Day 03, 06, 09, 18** — withdraw handed-over solutions to scaffold; close Day 09's `DataAccessException` → `@Repository` bridge.

**Then, as one pass: the acceptance-criteria restoration across all nine records** — day-15, 18, 21, 24, 27, 30, 33, 34, 35 — using day-03/06/09's table shape and day-36's rubric shape. Day 30/33/34/35's tables are written here and *validated* in Wave 5 once their content lands.

Gate: hands-on DoD on every record; zero `null`/empty-body specifications; every deliverable traces to a teaching record by id; every verification step is runnable.

### Wave 5 — The capstone chain (6 records)

Strictly after Waves 1–4: this is where every supply edge terminates.

**Entry condition for the auth chain — the auth sourcing gate must be closed.** The chain is executed in the order `Day 22 (security foundation) → Day 24 (authorization / testing) → Day 33 (register-login-JWT artifact)`, and **Day 33 is not started before Day 22 and Day 24 are final.** Day 22's foundation and Day 24's refresh/blacklist work are where the sourced canonical flow lands; Day 33 assembles it and introduces no new auth theory. **No custom crypto anywhere in the chain** — library primitives and standard algorithms only.

- **Day 28** — JaCoCo section (line/branch coverage, reading the report, 75% as a floor); `@MockBean` → `@MockitoBean`.
- **Day 29** — traceId propagation extending MDC; GitHub Actions `build → test → docker build`; Prometheus scrape + one custom metric.
- **Day 30** — rebuild as an integration lab over the now-taught four; resolve jar layers; state ≥75% in the acceptance table.
- **Day 22, then Day 24** — the sourced canonical auth flow: issuance at login, signing-key handling, expiry, validation, refresh rotation and the row-42 Redis blacklist, with the authorization and testing layer on top.
- **Day 33** — *after* Day 22 and Day 24: keep self-issued JWT (row 55 is unchangeable); rewire `day33-blk-10` to the course's own issuer with a real decoder; specify profile API and Category CRUD.
- **Day 34** — Day 26's four upload layers by reference; search/filter on `Pageable` + derived queries; scaffold Cart; resolve the cache contradiction toward Day 25.
- **Day 35** — replace the three `checkout()` placeholders with observable behaviour; add the `@Version` conflict slice; CSV by reference to Day 26; resolve jar layers.
- **Day 31** — replace the DispatcherServlet re-explanation with a back-reference; honour and keep the `POST /api/auth/login` contract.

Gate: the `Prerequisite → Theory → Artifact → Sprint → Evaluation` chain complete for all five capstone records; the `Day 22 → Day 24 → Day 33` order demonstrably respected; every auth claim traceable to a sourced reference; no hand-rolled crypto in any block; a reader can build Sprints 1–3 from the corpus alone; no mirrored syllabus row edited.

### Wave 6 — The terminal band (5 records)

Last, because each summarises or grades what Waves 1–5 changed.

- **Day 37** — host the **learner-facing LO definition table derived from this plan's canonical authoring contract** (D-2; the plan stays canonical, Day 37 is the rendering); build the Day-indexed, LO-clustered revision checklist; replace the two documentation-structure practices with technical ones; add a 60-minute plan; **citation handling unchanged**.

- **Day 36** — re-explanations → back-references; space to defense preparation; align to Day 20's coded locking; `@MockitoBean`.
- **Day 38** — state which capstone modules must work (now true); reconcile the testing expectation with ≥75%; weights and level descriptors; 300-minute plan.
- **Day 39-64** — per-LO refresher with Day pointers; mid-phase checkpoint; exit criteria; fix the worklog example; keep the FSU refusal.
- **Day 65-66** — explain or close the LO6–LO9 gap; level descriptors; two technical defense questions; 600-minute agenda; keep the grading-scale refusal.

Gate: terminal DoD — every assessed item maps to a teaching record by id, zero first-appearances, both refusals intact, no false premises anywhere.

## Review Gates

One gate per wave, **Wave 0a and Wave 0b each having their own**. A wave is not finished when its edits are made; it is finished when its gate passes. **Gates are sequential and there is no parallel execution** — `0a → gate → 0b → gate → 1 → gate → …`. A failed gate blocks the next wave rather than being carried as debt, because the dependency graph means carried debt propagates into records that are harder to fix.

**Only a Review Gate may mark a record DONE.** No wave, and no part of this plan, declares a record final in advance. Where this plan says a record is "expected to require no further rewrite" after some wave, that is a prediction about scope, not a status — the record's status changes only when its gate passes.

Every gate, all waves:

1. `python tools/validate_lessons.py` exits clean.
2. `python tools/build_site.py` completes — specifically **without `_slim_authored_lesson` raising `ValueError`**, the failure mode a careless reference edit produces.
3. Unresolved citation markers did not increase. From Wave 0a's gate onward the count is **0**, and any wave that reintroduces one fails.
4. **No file outside the approved scope for the current wave changed.** Verified by `git status`, not by assertion. Each wave declares its scope before it starts, and the gate checks the diff against *that* declaration — not against a fixed path list. Content waves declare `content/lessons/*.json`. The sourcing gates for D-4 and auth legitimately need `content/source-manifest.json` and `content/source-notes/*.json`. Tooling work — the Tier 1–3 fixture, a coverage report, a citation-integrity check — legitimately needs `tools/`, its tests, and `docs/`. A file touched inside the declared scope is reviewed; a file touched outside it fails the gate.
5. Every diff traces to a named audit item or a named structural decision. A diff nobody can attribute is reverted.
6. No record grew in volume without a finding that required it.
7. `authoring.reviewStatus` is set honestly, and any authored-without-source content is disclosed in `authoring.limitations`. **Disclosure is not a substitute for the D-4 or auth sourcing gate** — a foundational claim inside either gate's scope may not ship disclosed-but-unsourced.

Per-wave additions:

| Wave | Additional gate |
| --- | --- |
| **0a** | **Unresolved citation markers = 0, locator failures = 0, dangling references = 0.** No known `[?]` survives. Every marker closed by removal or retarget has its rationale recorded in the diff. Declared scope: `content/lessons/*.json` |
| **0b** | Every reordered MCQ verified on all three axes — `choices` intact, `correctChoiceIds` still names the actually-correct option, `solution` text consistent with the new order. Positional-semantics items either left with a recorded reason or deliberately rewritten and reviewed as content. MCQ concentration ≤ 35%, **or** the residual reported with the reason — quality outranks the metric. The 4 relabelled blocks compile at their stated tier; every `compile=False` block carries a SPRING/CONFIG/PSEUDOCODE classification. The 59 expanded solutions reviewed as authored content, not as a mechanical pass |
| 1 | Day 22's `SecurityConfig` reviewed by a second reader against Spring Security 6 semantics and confirmed **not** to permit unauthenticated access. Day 02's snippet and Day 18's constraint verified by execution, not reading |
| 2 | Theory DoD checklist per record. Day 11, 25, 26 confirmed structurally unchanged — reference and defect fixes only |
| 3 | **The D-4 sourcing gate is closed and its notes are in the pipeline** — checked before the wave's diff is reviewed. Every SQL claim traces to a sourced reference. **The index mental model is complete at Day 20 and Day 32 contains no first-encounter index teaching.** The SQL out-of-scope list is present and honoured. Day 20 reviewed as a JPA record that now has SQL beneath it, not as an SQL record. `@Version` code compiles or carries a documented review sign-off |
| 4 | All nine acceptance tables exist and every row's "where taught" cell is filled with a real record id. Zero `null`-body specifications remain in the corpus |
| 5 | **The auth sourcing gate is closed**, the `Day 22 → Day 24 → Day 33` order was respected, and **no block contains hand-rolled crypto**. An independent reader attempts Sprint 1 → 2 → 3 from the corpus alone and reports any step they cannot complete. `_validate_catalog_mirror` confirms rows 37/42/52 untouched |
| 6 | Every assessed item in day-37/38/39-64/65-66 maps to a teaching record. Day 37's LO table matches this plan's canonical authoring contract and carries no authoring metadata. Day 38's premise verified true against the Wave 5 output. Both authored refusals confirmed intact |


## Definition of Done

**A lesson is not DONE because its JSON validates.** `validate_lessons.py` passing means the record is well-formed, not that it teaches. Every gate below is additional to schema validity, and the ordering is deliberate: the mechanical checks are the floor, not the finish line.

**DONE is a Review Gate verdict, never a self-assessment and never a prediction.** A record's status changes only when a Review Gate passes on it. Nothing in this plan pre-declares a record final: where a wave says a record is "expected to require no further rewrite", that is a scope forecast for planning, and the record remains not-DONE until its gate says otherwise. An author may report that every criterion below appears satisfied; the gate decides.

A record is DONE when all of the following hold **and a Review Gate has confirmed them**:

1. **Schema-valid and build-clean.** `validate_lessons.py` passes and `build_site.py` renders the record without `ValueError`.
2. **Zero unresolved citation markers.** Not "or listed with a reason" — zero. A marker that no source supports is retargeted, or removed together with the repair of the claim it supported, as an authored and recorded decision. No marker is deleted merely to reach the number.
3. **Its lesson-type contract is satisfied** — the theory arc, the hands-on arc, or the terminal element list from D-3, judged as beats present and working, not as headings present.
4. **Every stated outcome has a demonstrating artifact.** An outcome backed only by prose is not done; this is the gate Day 25 currently fails on `@Async`/`@Scheduled` and Day 20 on `@Version`.
5. **Every critical `commonMistake` is reachable** from a practice, a worked example, or an `enhancedExercise`.
6. **Every code block is either verified at its tier or explicitly classified** SPRING (pending Tier 3, with review sign-off), CONFIG (lint-passed), or PSEUDOCODE (marked as such and visually distinguishable). No block is silently `compile=False`.
7. **Prerequisites are true.** Every named prerequisite is taught in a record that precedes this one, by id; every forward dependency is disclosed as such.
8. **Hands-on records:** an acceptance table with a runnable verification per requirement, and every deliverable traceable to a teaching record by id. No `null`, no empty body, no `<template>` standing in for a specification.
9. **Terminal records:** every assessed item maps to a teaching record; rubric has level descriptors; pass/fail is a threshold two evaluators would apply identically; nothing appears here for the first time.
10. **Nothing false.** No statement about the corpus, the prerequisites, the capstone's state, or a mechanism's behaviour that is not true after the wave lands.
11. **Every diff is explainable** by a named audit finding or structural decision, and the record's strong material is intact — for the eleven preserve-list records, a reviewer can confirm the strengths the audit named are still present verbatim in substance.
12. **Disclosure is honest.** `authoring.reviewStatus` reflects reality, and every authored-without-source claim says so.

## Validation Strategy

Eight validation classes. Each names what it checks, how it runs, and whether it blocks. **Nothing in this section is implemented in this task** — the two proposed validator checks and the compile tiers are specified for later work.

**1. SCHEMA** — existing `validate_lessons.py`. Closed-key objects, block types, `kind`, `practices` 2..4, id uniqueness corpus-wide, `_validate_catalog_mirror` deep-equality on `objectives` and `syllabusAssignments`. **Blocking, unchanged.** This is also the gate that makes rows 37/42/52 uncuttable, and that property is a feature here.

**2. REFERENCE** — existing gates: `important`/`warning`/`table`/non-`text` `code` blocks need nonempty `citations`; external `reference` needs `resourceId` + `citationId` resolving in the same lesson's `sourceUsage`; internal `reference` needs `description`; `_validate_sourceusage_entry`'s three checks (resource linked to this lesson, `readStatus == "read"`, locator ∈ `facts[].locator`). **Blocking, unchanged.** *Proposed addition (not implemented):* warn when a cited `sourceUsage` id has no `references` row — the exact 241-row condition, so Class A cannot silently return. **Warning, not blocking**, because a legitimately disclosed uncited claim must remain possible.

**3. LO** — every record's `objectives` matches `course-catalog.json` (already covered by SCHEMA's mirror check) **plus** every LO referenced by a terminal record resolves in Day 37's learner-facing definition table, **which is itself checked against this plan's canonical authoring contract (D-2)**. **Report,** not blocking: the table is content, and a missing row is an authoring gap, not a corruption. When the table and the plan disagree, the plan is correct and the table is the defect.

**4. PRACTICE** — existing: every practice needs nonempty `prompt`, `hint`, `solution`, `explanation`, `rubric`. **Blocking, unchanged.** *Report added:* solution length distribution, to keep the 59 bare-solution class from reappearing. Note the existing gate cannot catch it — a one-word solution is nonempty.

**5. ANSWER DISTRIBUTION** — the MCQ position histogram over `correctChoiceIds` (never `choices[].correct`, which is not the answer key). **Report with a threshold:** flag when any position holds ≥35% corpus-wide. Deliberately not blocking — a per-record block would be meaningless at 4 items per record, a corpus-wide block would fail the build on unrelated edits, and a blocking histogram would pressure authors into reordering items whose options carry positional meaning. **A machine cannot tell a reorder-safe item from a positional-semantics one**; that triage is human, per `### MCQ contract`, and the report exists to direct it, not to replace it.

**6. CODE** — tiered compilation per D-5: Tier 0 JDK-only (43 blocks after relabelling), Tier 1 junit/assertj/mockito, Tier 2 slf4j, Tier 3 Spring/Jakarta pinned to the Boot 3.x BOM. Plus the existing always-on lint: `JAVA_POST_17_PATTERNS` (`STR."`, `case X(...) when`, `Thread.ofVirtual(`), `SPRING_LEGACY_PATTERNS` (`javax.persistence`, `javax.validation`, `WebSecurityConfigurerAdapter`), and `COPIED_RUN_THRESHOLD = 300`. **Blocking at whatever tier exists**; the lint is blocking today and stays the floor for the 63 currently unverified blocks. CONFIG blocks are parsed, never compiled; PSEUDOCODE is excluded by declaration.

**7. PREREQUISITE** — every prerequisite named in a record resolves to an earlier record id; forward references are declared, not implied. **Report.** The corpus's ten inversions are content decisions — nine in the sprint band are defects, day-05/06's are benign — so a machine cannot tell them apart. It can list them.

**8. PROJECT** — every hands-on deliverable traces to a teaching record by id; every deliverable has an acceptance criterion; no deliverable depends on an `unavailable` resource without a disclosed authored substitute. **Report,** run at each wave gate. This is the check that would have caught Day 30's four untaught deliverables and Day 38's false premise before publication.

**Why so few are blocking.** Three of the corpus's worst defects — 89.4%-at-(a), the 3-mistake template, the untaught deliverables — are *statistical* properties. A blocking check on any of them creates pressure to delete content until the number goes green: delete mistakes to fix coverage, delete markers to fix citations, delete deliverables to fix traceability. Every one of those is worse than the defect. Blocking checks guard correctness; reports guard quality; the review gates are where a human reads the reports.

## Course Quality Targets

Measurable, each with a live baseline and a verification method. No vanity metrics: **word count, section count, block count and record length are explicitly not targets**, and no target can be satisfied by adding volume.

| # | Target | Baseline (measured) | Goal | Verified by |
| --- | --- | --- | --- | --- |
| 1 | Unresolved citation markers | **579 of 919 (63.0%)** | **0.** No residual allowance; a marker that cannot be supported is retargeted or removed with its claim repaired | Marker-vs-`references` walk |
| 2 | Locator-gate failures on published references | **9 entries / 17 instances** | **0** | `_citation_locator_matches` over every published reference |
| 2b | Dangling references — published `reference` rows no citation uses | **2** | **0** | `references` -vs- marker walk |
| 3 | `build_site.py` raises `ValueError` | 0 today (would become 8 after a naive fix) | **0, maintained** | Build run at every gate |
| 4 | MCQ correct-answer concentration | **89.4% at position (a)** (59/5/2 of 66) | **no position ≥ 35%**, achieved by safe rebalancing only — **subordinate to semantic correctness**, and a reported residual with its reason is a pass where reordering would break an item | `correctChoiceIds` histogram + per-item reorder-safety review |
| 5 | Practices with bare or one-line solutions | **59** | **0** | Solution length + distractor-mention check |
| 6 | Java blocks compiled | **41 of 104** (all day-01…day-12) | **≥ 43 at Tier 0 immediately; 100% classified**; ≥ 90% compiled once Tier 3 exists | Compile run + classification census |
| 7 | Hands-on records with an acceptance table | **7 of 16** (day-03, 06, 09, 12, 31, 32, 36 partial) | **16 of 16** | Structural check per record |
| 8 | Deliverables with no teaching record | **12** | **0** — taught or explicitly scoped out with a reason | PROJECT report |
| 9 | Records with a stated outcome and no demonstrating artifact | Day 20 (`@Version`, `Specification`), Day 25 (`@Async`, `@Scheduled`) — **2 records, 4 outcomes** | **0** | Outcome → block mapping |
| 10 | Records at exactly 3 `commonMistakes` | **18** (day-03, 06, 09, 12, 15, 18, 21, 27, 30, 31, 32, 33, 34, 35, 36, 38, 39-64, 65-66) | **0 template-driven cases** — count follows hazards, not a template | Per-record hazard review |
| 11 | Critical `commonMistakes` with no practice, example or exercise | Unmeasured — needs the critical flag first | **0 uncovered critical mistakes** | Coverage report |
| 12 | Records with `INSUFFICIENT_FOR_PROJECT_APPLICATION` | **10** (day-15, 21, 24, 27, 30, 33, 34, 35, 38, 39-64) | **0** | Flag re-audit against the DoD |
| 13 | False statements about prerequisites or capstone state | **≥ 3** (Day 19's prerequisites string, Day 38's premise, Day 35's oversell-without-mechanism) | **0** | Per-record claim check |
| 14 | Records whose stated arc is complete for their type | Theory 20 records mean 4.23; hands-on 3.08; terminal 2.77 | Hands-on and terminal bands reach the theory band's shape; **theory does not regress** | D-3 checklist at each gate |
| 15 | Records with a closing synthesis beat | **0 of 40** | **all unit-final records** | Structural check |
| 16 | Duplicate `commonMistake` pairs | 4 known pairs (day-13, 23, 26, 29) | **0** | Pairwise similarity review |
| 17 | Preserve-list records structurally changed | n/a | **0** — day-11, 26, 25, 13, 16, 17 change only by named finding | Diff review at each gate |

Target 14 is the one that matters most and is the hardest to automate; it is why the review gates exist. Note that targets 1–8 are structural or assessment-level and land almost entirely in Waves 0a and 0b, which is why they are scheduled first despite rewriting no lesson for content: **they move eight of seventeen targets before any judgement call about teaching is made.** Targets 1, 2, 2b and 3 are Wave 0a; targets 4, 5 and 6's classification half are Wave 0b.

## Risks

| # | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R1 | **A naive references-completion pass breaks the build on 8 lessons.** `_slim_authored_lesson` raises `ValueError` when a *published* reference fails the locator gate, and 8 of the 9 failing entries are inside Class A | **High** if sequencing is ignored — it is the obvious way to do the work | Build fails; 8 records unpublishable | Locator repair is a separate, strictly-first step in Wave 0a. Gate 2 (`build_site.py` completes) runs before the publication pass is accepted |
| R2 | **The SQL foundation grows into an SQL course.** Three records gain SQL sections and authored content has no natural stopping point | Medium | Unit 7 stops being a JPA unit; the roadmap distorts | The explicit out-of-scope list in D-4 is part of the Wave 3 gate. The test for each line: does the course later ask the learner to reason about it? Bounded by Day 20's 30-minute slot. The sourcing gate also bounds it — content must trace to a sourced reference, so depth cannot be improvised |
| R3 | **Tier 3 never gets built, so 63 Spring blocks stay unverified through the whole programme.** It is a build-pipeline change, out of scope here, and easy to defer indefinitely | Medium-high | The defect that produced Day 22's open API stays live; every Spring edit in Waves 1–5 ships on review alone | Tiers 0–2 deliver value without Tier 3 and are ordered first. Every Spring Java edit carries mandatory second-reader review until Tier 3 exists. Wave 1's Day 22 fix is explicitly hand-reviewed. Recorded as a blocker, not a footnote |
| R4 | **Authored-without-source content accumulates** — JaCoCo, CI, traceId, Prometheus, `@Async`/`@Scheduled` artifacts, cascade/fetch artifact | Medium — reduced from high now that the two foundations are gated | The corpus drifts from "sourced" to "asserted", weakening what makes it auditable | **The two foundational cases are no longer in this class:** SQL is behind the D-4 sourcing gate and the canonical auth flow behind the auth sourcing gate, and neither may ship disclosed-but-unsourced. What remains is *incremental* content attached to already-sourced records; each discloses in `authoring.limitations` with the reason, Track 2 records it as a future sourcing target, and disclosure is a DoD item, not a courtesy |
| R5 | **The canonical auth flow has no source for issuance.** `res-65703b737426` documents Resource Server *validation*; the plan keeps self-issued JWT because row 55 and Day 31's contract demand it | Certain — the syllabus forces the decision | Without a gate, Day 22/33 would teach token minting from memory — the one gap that can teach a learner to build something insecure | **The auth sourcing gate**, applied at Day 22 as the chain head: sources are checked against the full flow first, and researched into the pipeline if they do not support it. **No custom crypto under any circumstances** — library primitives and standard algorithms only. If the gate cannot close, the record is held and the blocker escalated; it is not authored under disclosure |
| R6 | **Editing a mirrored `syllabusAssignments` row breaks `_validate_catalog_mirror`.** Rows 37, 42 and 52 carry deliverables an author would naturally want to cut as untaught | Medium — the temptation is strongest exactly where the content is worst (Day 21, 24, 30) | Validation failure, or worse, a catalog edit that silently diverges from the workbook | Named explicitly in Non-Negotiables and in the Day 21/24/30 matrix rows. Wave 5's gate re-runs the mirror check. The rule is stated as: mirrored deliverable → must be taught, never cut |
| R7 | **Waves 1–4 finish and Wave 5 is descoped**, leaving Day 38's premise false | Medium — Wave 5 is the largest and most dependent wave | The worst defect in the corpus survives the programme | Day 38's fallback is explicit: if any Wave 5 repair is descoped, Day 38 gains a **disclosure** of exactly which capstone modules are unimplemented. An honest gap, never a false premise |
| R8 | **The 2..4 `practices` cap blocks mistake coverage** and someone raises it as an incidental edit mid-wave | Medium | A schema change lands without its validator and build consequences worked out | The cap **stays at 2..4** (approved). Coverage is routed through examples and `enhancedExercises`, which are uncapped, so no wave depends on raising it. Any future proposal to raise it is a separate schema decision with its own approval |
| R9 | **Preserve-list records get "improved".** Day 11, 25, 26, 13, 16, 17 are open during Waves 0a/0b and 2 for reference fixes and are easy to over-edit | Medium | The corpus loses its best material and its templates | Target 17 (zero structural change to preserve-list records) is checked by diff review at every gate. Their matrix rows state reference-and-named-defect only |
| R10 | **15 unavailable resources cannot be cited**, worst at Day 07 (1 of 5 readable), Day 34 (2 of 4), Day 10 (2 of 5) | Certain — already true | Some records cannot cite a source for every claim regardless of effort | **This is not a licence to leave markers unresolved** — Target 1 is 0 and admits no residual. An unsupported marker is retargeted to a readable source or removed together with the repair of its claim; the *sourcing* gap is then disclosed in `authoring.limitations`. Disclosure explains a missing source; it never leaves a dangling `[?]`. Track 2 owns re-sourcing. **No marker is deleted to hide it** |
| R11 | **Wave 0a's 241-row pass is done by hand and introduces `citationId`/`resourceId` mismatches** | Medium | Silent mis-citation — worse than an unresolved marker, because it looks correct | The mapping is derivable from existing `sourceUsage` data, so it is scripted and diffed, not typed. The REFERENCE gate validates every row against `sourceUsage`; a mismatch fails validation rather than shipping |
| R12 | **Rewriting 29 records causes drift in shared explanations** — the AOP-proxy model across Day 20 → 23 → 25 → 35, the traversal check across Day 11 → 26, CSV across Day 26 → 35 | Medium | The corpus's one genuinely reused mental model fragments | Canonical owners are fixed: AOP-proxy at Day 20, traversal at Day 11, CSV at Day 26, caching at Day 25, upload security at Day 26, testing at Day 28. Downstream records reference, never re-explain — which is also how Day 36's duplication is repaired |
| R13 | **A mechanical MCQ permutation breaks items whose options carry positional meaning** — "both A and B", ordered sequences, options referenced by letter in the solution | **High if a blanket permutation is attempted**; it is the fast way to move the histogram | An item becomes unanswerable or its solution points at the wrong option — a defect worse than the concentration it was fixing, and invisible to every validator | The plan contains **no blanket permutation.** Per-item triage into reorder-safe and positional-semantics classes, reorder only the former, deliberate review or rewrite for the latter, and mandatory three-axis verification after every reorder. The ≤35% target is explicitly subordinate to correctness, so missing it is a pass and breaking an item is not |

## Change Guardrails

Rules any executing agent or author must follow. Violating one is a revert, not a discussion.

**Scope is declared per wave, not fixed for the programme.** Each wave states the paths it may touch before it starts, and its review gate checks the diff against that declaration (gate item 4). The default for a content wave is `content/lessons/day-*.json` and `content/lessons/ojt-evaluation.json` — Waves 0a, 0b and 1–6 all declare exactly that. Two categories of work legitimately declare more, and are the reason the rule is scope-based rather than a fixed allowlist:

| Work | Additional in-scope paths | Approval |
| --- | --- | --- |
| **The D-4 and auth sourcing gates** | `content/source-manifest.json`, `content/source-notes/*.json` — new read notes must enter the pipeline for the new material to be citable at all | The sourcing mechanism itself needs approval (see `### Blockers`); once approved, these paths are in scope for that step |
| **Tooling and validation work** (Tier 1–3 fixtures, the proposed REFERENCE/PRACTICE reports, a citation-integrity check) | `tools/*.py`, the test suite, `docs/` | A separate, separately-approved task. **Never inside a content wave** |

**Files that may never be modified by any wave:** `docs/course-content-audit.md` (read-only per §27 — its corrections are recorded in this plan instead), `course-catalog.json`, `course-catalog.md`, `content/lesson-schema.json`, `content/spendwise-project.json`, `index.template.html`, and the syllabus workbook.

**`content/lesson-index.json` is generated** by `validate_lessons.py` and `index.html` by `build_site.py`. Both are regenerated, never hand-edited, and their changes are build output rather than authored diffs.

**Hard rules:**

1. **No new Day, no renumbering, no reordering, no split, no merge, no deletion.** New knowledge goes into an existing record as a section.
2. **No syllabus change**, and therefore no edit to any `objectives` or `syllabusAssignments` value. A mirrored deliverable is taught, never cut.
3. **No citation marker deleted to reach a number.** Publish the row, fix the locator, retarget the marker, or repair the claim the marker was propping up — each an authored decision recorded in the diff rationale.
4. **No citation gate weakened.** `read.status == "read"`, `_validate_sourceusage_entry` and `_citation_locator_matches` are fixed.
5. **No cross-lesson citation borrowing.** Where an artifact needs a resource linked to another lesson, it is authored and disclosed in `authoring.limitations` — never cited from the neighbour.
6. **No foundational claim authored on disclosure alone.** The SQL foundation (D-4) and the canonical auth flow each sit behind a sourcing gate. `authoring.limitations` records a residual; it does not license a foundation.
7. **No custom crypto.** No hand-rolled signing, token format, key derivation or password hashing anywhere in the corpus — framework primitives and standard algorithms only.
8. **No baseline drift.** Java 17, Spring Boot 3.x, Framework 6, Jakarta. No virtual threads, no `STR.`, no `javax.*`, no `WebSecurityConfigurerAdapter`.
9. **No Spendwise or UI edit**, including `lessonMap`.
10. **No build script, validator or test change during a content wave.** Tooling changes are proposed here and executed as separate, separately-approved tasks with their own declared scope.
11. **No `null`, empty body or `<template>` used as a specification** in a hands-on record.
12. **No volume added without a named finding.** Length is not a quality signal, and the theory band is already at 4.23.
13. **Preserve-list records** (day-11, 26, 25, 13, 16, 17, plus Day 37's citation handling and the Day 20 → 23 → 25 → 35 AOP chain) change only by named finding.
14. **One wave at a time**, each behind its own gate, `0a → 0b → 1 → … → 6`. **No two waves run concurrently**, and no wave starts while a prior gate is failing.
15. **No mechanical MCQ permutation.** Reorder only items triaged reorder-safe, and verify `choices`, `correctChoiceIds` and the `solution` after every reorder.
16. **No record declared DONE outside a Review Gate**, and no record pre-declared final in advance of one.
17. **Every diff attributable** to an audit item or a structural decision, checkable at review.
18. **No commit or push** unless the user asks for one.

**Canonical owners** — for any content that appears in more than one record, the owner teaches and everyone else references: SQL and JOIN → Day 20; indexes → Day 20 (Day 32 deepens, never introduces); transaction and isolation → Day 20 (SQL level), Day 35 (propagation depth); locking → Day 20; AOP proxy → Day 20; path traversal → Day 11; upload security → Day 26; CSV → Day 26; caching → Day 25; `@Async`/`@Scheduled` → Day 25; testing and JaCoCo → Day 28; logging, traceId, metrics, Docker, CI → Day 29; auth issuance and key handling → Day 22; auth authorization → Day 23; **LO authoring contract → this plan (Day 37 hosts the derived learner-facing table)**.

## Implementation Order

The execution sequence, with what each step depends on and what it unblocks. **Step 1 is the only approval gate that is already closed** — the structural decisions are approved. Steps 2a and 2b are sourcing gates that block their dependent waves.

| Step | Action | Depends on | Unblocks |
| --- | --- | --- | --- |
| 1 | **Structural decisions D-1…D-6 — APPROVED** (see `## Review Gate`) | This plan | Everything |
| 2 | Resolve or accept the remaining blockers | Step 1 | Waves 3, 5 |
| 2a | **D-4 SQL sourcing gate** — authoritative sourcing step, notes into the pipeline | Step 2's sourcing-mechanism approval | Wave 3 |
| 2b | **Auth sourcing gate** — canonical flow checked, researched if unsupported, no custom crypto | Step 2's sourcing-mechanism approval | Wave 5's auth chain |
| 3 | **WAVE 0a — Citation Structural Repair.** Locator repair (9 entries) → reference publication (241 rows / 36 records) → orphan and internal-reference cleanup → resolve every residual marker to zero | Step 1 | Targets 1, 2, 2b, 3 |
| 4 | **Review Gate 0a** — unresolved markers 0, locator failures 0, dangling references 0 | Step 3 | Wave 0b |
| 5 | **WAVE 0b — Assessment Quality Repair + Code Classification.** Safe MCQ rebalancing with per-item triage and three-axis verification + solution expansion (59, authored) + 7 deliverable slots + block relabelling (4) + full `compile=False` classification + Tier 1–3 fixture **spec** | Step 4 | Targets 4, 5, 6; Wave 3's `@Version` code |
| 6 | **Review Gate 0b** | Step 5 | Wave 1 |
| 7 | **Wave 1** — Day 22 (config defect only), 18, 19 (fixes), 02 | Step 6 | Day 24, 33 (no open API propagates); Day 20, 21 (true prerequisites) |
| 8 | **Wave 2** — Day 25, 26, 23, 07, 13, 14 | Step 7 | Day 34 (caching, upload security); theory contract established |
| 9 | **Wave 3** — Day 20, 19 (SQL), 32 | Steps 2a, 7 | Day 21, 24, 34, 35 — the critical path's widest gate |
| 10 | **Wave 4** — Day 21, 24, 15, 12, 27, and 03/06/09/18 scaffolding | Step 9 | Day 33 (refresh + blacklist) |
| 11 | **Acceptance-criteria pass, 9 records** — as one operation | Step 10 | Target 7; Wave 5's tables |
| 12 | **Wave 5** — Day 28, 29 → Day 30; then the auth chain **Day 22 → Day 24 → Day 33**; then Day 34, 35, 31 | Steps 2b, 8, 10, 11 | Day 36, 38, 39-64, 65-66 — makes Day 38's premise true |
| 13 | **Wave 6** — Day 37 (derived LO table), 36, 38, 39-64, 65-66 | Step 12 | Programme complete |
| 14 | Final corpus verification: all 17 targets re-measured, full validate + build, and `git status` checked against **each wave's declared scope** — no file outside the approved scope for the wave that touched it | Step 13 | Sign-off |
| 15 | *(Separate, separately-approved task, own declared scope)* Implement Tier 1–3 compile fixtures and the two proposed validator reports | Step 5's spec | Retro-verification of the 63 Spring blocks |

**Sequencing constraints that are not negotiable:** locator repair before publication within step 3 (the build raises otherwise); step 4 before step 5 and step 6 before step 7 — **Wave 0b does not run in parallel with Wave 1**; step 2a before step 9 and step 2b before step 12's auth chain (no foundation authored unsourced); step 9 before steps 10 and 12 (no performance or DDL work without SQL); the index model complete at Day 20 in step 9 before Day 24's benchmark in step 10; Day 22 before Day 24 before Day 33 inside step 12; Day 28 and Day 29 before Day 30 within step 12 (row 52 is uncuttable); step 12 before step 13 (a terminal record cannot grade a capstone that does not exist).

**Deliberate ordering choices worth naming.** Waves 0a and 0b rewrite no lesson for content yet move 8 of 17 targets — structural and assessment repair first, teaching judgement later — and they are **two waves, not one**, because citation bookkeeping is structural while solution expansion and deliverable authoring are content quality that must be reviewed as such. Wave 1 precedes Wave 2 on consequence, not dependency: Day 22 ships an open API and Day 02 ships non-compiling code in the learner's first encounter with Streams. The audit's own top-priority records (Day 30, 33, 34, 35) land in Wave 5, next-to-last, because the dependency graph puts every one of their repairs downstream of a theory repair — **fixing them first would mean fixing them twice**, which is the failure mode this ordering exists to prevent.

## Review Gate

### Approved structural decisions

The Content Improvement Plan Review Gate is **closed**. All seven decisions below are **APPROVED**, with the revisions listed against each incorporated into the plan above. No decision remains open.

1. **D-1 — Citation Architecture: Option A, self-contained per-lesson references. APPROVED.** 241 `reference` rows added to 36 records; the 9-entry locator repair executed strictly first. Options B (shared registry) and C (hybrid) rejected because 523 of 579 unresolved instances are same-lesson omissions, so a schema change buys nothing a data pass does not. **Revision incorporated:** the acceptance target is **0 unresolved markers / 0 locator failures / 0 dangling references**, not "≤ 4". A marker that cannot be supported is retargeted, or removed together with the repair of the claim it propped up, as an authored and recorded decision. **No known `[?]` survives Wave 0a.**
2. **D-4 — SQL foundation placed inside Day 19, Day 20 and Day 32; no new Day. APPROVED.** Day 20 hosts the main layer in its empty-`syllabusAssignments` 30-minute "Guides/Review" slot. **Revision incorporated:** a **sourcing gate now precedes authoring.** Foundational SQL claims may not rest on `authoring.limitations` alone; an explicit sourcing step against authoritative references must complete and enter the pipeline first. **Day 20 must establish the complete index mental model before Day 24's benchmark**, and **Day 32 is the deepening / database-design layer, not the learner's first encounter with an index.**
3. **D-3 — three lesson-type contracts (Theory / Hands-on / Terminal). APPROVED** as written.
4. **Capstone auth kept as canonical self-issued JWT. APPROVED**, to match the syllabus's `register / login / JWT` (row 55) and Day 31's `POST /api/auth/login` contract. **Revision incorporated:** approval of the *decision* is not approval to author the flow unsourced. Before Day 22 or Day 33 is rewritten, current sources are checked against the canonical flow and **researched against authoritative references if they do not support it** — `res-65703b737426` covers validation, not issuance. **No custom crypto**, ever. The dependency `Day 22 security foundation → Day 24 authorization/testing → Day 33 register-login-JWT artifact` is explicit in `## Dependency Graph`, Wave 5 and the Implementation Order.
5. **`practices` cap stays at 2..4. APPROVED — not raised.** All mistake coverage routes through uncapped `enhancedExercises` and worked examples. No wave depends on the cap; any future proposal to change it is a separate schema decision.
6. **D-5 — tiered snippet validation (Tier 0 JDK / Tier 1 test libs / Tier 2 slf4j / Tier 3 Spring+Jakarta). APPROVED** as a direction. Tier 3 remains unimplemented in this phase and is Blocker 1.
7. **D-6 — classification of untaught-but-assessed topics as written. APPROVED**, including **`Specification` as an out-of-scope required assessment** (class C): it is scoped out rather than taught, Day 34's search/filter is re-specified on `Pageable` + derived queries, and Day 20's dangling prose mention is removed or marked out-of-scope. It is the only demand this plan removes rather than teaches, and it is removable only because it appears in no mirrored syllabus row.

**Also incorporated, from the same review:** the MCQ repair is **safe rebalancing, never a blanket permutation of all 66**; **Wave 0 is split into 0a and 0b**, which run **strictly sequentially with no parallelism against Wave 1**; **bare-solution expansion is content-quality repair, not a mechanical pass**; the **canonical LO authoring contract lives in this plan** and Day 37 hosts only the derived learner-facing table; **no record is pre-declared final and only a Review Gate marks DONE**; and the per-gate file rule is now **"no file outside the approved scope for the current wave"** rather than a fixed `content/lessons` allowlist.

### Blockers

1. **Tier 3 compile fixture does not exist and cannot be built in this phase.** 63 Java blocks from day-13 onward ship unverified; this is the direct cause of Day 22's open `SecurityConfig`, Day 19's type mismatch and Day 24's missing imports. Every Spring Java edit in Waves 1–5 therefore rests on review alone. *Fallback:* Tiers 0–2 land first (43 blocks verifiable immediately), the always-on lint remains the floor, and every Spring edit carries mandatory second-reader review. *Resolution:* step 15, a separate approved task. **Open.**
2. **15 of 111 resources are `unavailable`**, so some records cannot cite a source for every claim by any amount of authoring effort. Worst: **Day 07 has 1 of 5 readable**; Day 34 2 of 4; Day 10 2 of 5; Day 33 3 of 5; `res-553bbd92e5d0` alone blocks four lessons (day-21, 32, 33, 34). Day 38, day-39-64 and day-65-66 have **zero** resources by design. *Fallback:* the **sourcing** gap is disclosed per record in `authoring.limitations` — but this no longer permits a residual marker, because Target 1 is 0. An unsupportable marker is retargeted to a readable source or removed with its claim repaired. *Resolution:* Track 2, out of scope here. **Open.**
3. **The D-4 SQL sourcing gate is open, and it now gates Wave 3 in place of the former "authored without source" acceptance.** No catalog source teaches SQL, JOIN or indexing — all 111 notes checked. The gate requires authoritative references whose read notes enter the pipeline. **The obstacle is mechanical, not editorial:** `course-catalog.json` is generated from the workbook and `_validate_sourceusage_entry` requires a cited resource to be linked to the citing lesson, so new sources cannot simply be attached. Closing this needs **either a workbook-level addition or an approved sourcing mechanism** — and external research was prohibited in the phase that produced this plan. *Fallback if it cannot close:* the SQL foundation is **descoped rather than authored unsourced**, with Day 21's Flyway DDL and Day 24's benchmark re-specified to what the corpus supports, and the prerequisite gap disclosed to the learner. **Open — gates Wave 3 and, through it, the critical path.**
4. **The auth sourcing gate is open, and it gates Wave 5's auth chain.** The approved canonical self-issued-JWT flow has no source for issuance, key handling, expiry, refresh rotation or revocation. Same mechanical obstacle as Blocker 3, and the same resolution path. *Fallback:* the record is **held at the gate and escalated** — the flow is not authored from memory under disclosure, because an unsourced auth foundation is the one gap in this corpus that can teach a learner to build something insecure. **No custom crypto** under any fallback. **Open — gates Day 22's canonical-flow content, and therefore Day 24 and Day 33.**
5. **A new Day would be the cleaner engineering answer for the SQL foundation, and the constraints forbid it.** Flagged, not acted on: a dedicated SQL/database record between Day 18 and Day 19 would avoid loading Day 20 (already 4.33 and dense) with a second foundational job. The plan proceeds with in-record placement per the approved D-4. *Decision needed only if Wave 3's gate finds Day 20 has become an SQL record rather than a JPA record with SQL beneath it.* **Accepted, monitored.**

**Nothing in this list blocks Wave 0a, Wave 0b, Wave 1, Wave 2 or Wave 4.** Blockers 3 and 5 gate **Wave 3**; Blocker 4 gates **Wave 5's auth chain**. Blocker 1 degrades every wave's confidence without stopping any, and Blocker 2 constrains sourcing without permitting a single unresolved marker.

### Recommended first rewrite wave

**WAVE 0a — Citation Structural Repair.** This is the first executable work in the programme. **It is not started in this task.**

No lesson is rewritten for content. Contents, in this exact order:

1. **Repair 9 locators** — `day01-src-10`, `day17-src-4`, `day17-src-11`, `day22-src-1`, `day23-src-11`, `day24-src-6`, `day28-src-7`, `day33-src-7`, `day37-src-1`. **Strictly first.**
2. **Publish 241 `reference` rows** across 36 records.
3. **Clean 2 orphan references**; retarget `day38-ref-3` → Day 28 and `day30-ref-6` → its originating record.
4. **Resolve every remaining marker to zero**, including the single Class C entry, by retarget or by removal-with-claim-repair, each recorded in the diff rationale.

**Acceptance criteria — absolute:**

| Criterion | Required |
| --- | --- |
| Unresolved citation markers | **0** |
| Locator failures | **0** |
| Dangling references | **0** |
| `validate_lessons.py` | Clean |
| `build_site.py` | No `ValueError` |
| Known `[?]` remaining | **None** |
| Declared scope | `content/lessons/*.json` only |

Why this first: it is the only wave with no content-quality judgement in it, so it carries no teaching risk; it is a prerequisite for 36 records; it removes 579 markers of noise that would otherwise hide the ~20 genuinely stranded artifacts; and its internal ordering constraint — **locators before publication, or `_slim_authored_lesson` raises on 8 lessons** — is the single highest-risk detail in the whole programme, so it is best executed while attention is on it.

Expected result: unresolved markers 579 → **0**; locator failures 9 → **0**; dangling references 2 → **0**. **Day 11 and Day 17 are expected to require no further rewrite after Wave 0b**, but neither is DONE until a Review Gate says so.

**Wave 0b — Assessment Quality Repair + Code Classification — follows only after Review Gate 0a passes**, and **does not run in parallel with Wave 1**. The programme flow is `Wave 0a → Review Gate → Wave 0b → Review Gate → Wave 1 → …`.

### Verdict

CONTENT_REWRITE_PLAN_APPROVED
