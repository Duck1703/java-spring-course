# Spendwise ↔ Course Alignment — Phase 2 Implementation Plan (FINAL)

**Verdict:** `SPENDWISE_ALIGNMENT_PLAN_FINAL_READY_FOR_IMPLEMENTATION`
**Date:** 2026-09-05
**Repo baseline:** `e97c13a` (`COURSE_CONTENT_STABLE`)
**Scope:** the executable plan for bringing `content/spendwise-project.json`, the validator, the
site and the learner-progress model into alignment with the final architecture. This document plans;
it implements nothing. No artifact, lesson, validator, test, template or generated file was edited
in the session that produced it. No commit. No push.
**Supersedes:** the `SPENDWISE_ALIGNMENT_PLAN_READY_FOR_REVIEW` draft at this same path, revised in
place because the finalization directive named this exact filename as final output 2.
**Upstream authority:** `docs/report/2026-09-05-spendwise-architecture-blueprint.md`, verdict
`SPENDWISE_ARCHITECTURE_BLUEPRINT_FINAL`. This plan is downstream of it. Where the two disagree, the
blueprint wins, and any such disagreement is a defect in this document.

**Amended 2026-09-05 by the final planning reconciliation** (second amending pass, after the pre-P0
sanity gate). Six corrections, each marked in place with a dated note:

| # | What changed | Where |
|---|---|---|
| 1 | target total **58 → 64 tasks / 50 → 56 required** — the blueprint's total row was an addition error against its own per-release rows | §2 heading, §2 V0.3, §2 V0.4, §17 test diff, §18 P1/P2, reviewer orientation 1, Known gaps, Verdict |
| 2 | `task-actuator-baseline` **deleted** — Actuator is 0-hit at day-13/14 and belongs to V0.9's `task-production-packaging` | §2 V0.3 |
| 3 | V0.4 is **6 tasks, 6 required** | §2 V0.4 |
| 4 | `SPRING_BOOT_EXACT_PIN_PENDING` blocks **`task-spring-bootstrap` (V0.3)**, not `task-project-foundation` (V0.1) | §8, Known gap 2, Verdict |
| 5 | import identity is a **content fingerprint**, not `IMPORT:<batchId>:<rowNo>` | §13 |
| 6 | the **`#/task/:taskId` route and task detail view move from P0 to P3** — P0 is plumbing only, restoring "Data first. UI second." | §12, §18 P0, §18 P3 |

Full derivation and the fourteen-check consistency gate:
`docs/report/2026-09-05-spendwise-final-reconciliation-report.md`.

**Amended again 2026-09-05 by the final import-identity correction** (third amending pass).
**Row 5 of the table above is superseded.** A bare content fingerprint collapses two *legitimate*
transactions that share account, date, direction, amount and normalized description — for a finance
ledger that is not an acceptable frozen V1.0 dedup strategy, and the previous pass accepted the loss as
a disclosed cost. Reverting to `IMPORT:<batchId>:<rowNo>` remains forbidden, because a new
`ImportBatch` PK on re-upload breaks idempotency.

| # | What changed | Where |
|---|---|---|
| 7 | import identity becomes **two-level** — preferred `IMPORT:SRC:<sourceKey>:<accountId>:<sourceTxnId>`, else `IMPORT:<baseFingerprint>\|OCC:<occurrenceIndex>` | §13 table, **§13.1 rewritten**, §2 V0.8, §9 invariants 10/10a/16, §11, Known gaps, Verdict |
| 8 | the accepted false-duplicate collision is **withdrawn**; a **reordering limitation** replaces it | §13.1, Known gaps |
| 9 | **source-file order is load-bearing** — sequential parse only, `parallelStream` forbidden on the import path (blueprint **R22** second clause, not a new rule id) | §13.1, §11, §2 V0.8 (`task-csv-parse`) |
| 10 | retry / re-import acceptance criteria written out as **7 numbered statements**, including one explicit *Not claimed* | §13.1 |
| 11 | Maven + Wrapper at V0.1 is **project/tooling scaffolding, not a Day-01 learning objective** | §8 build-tool row, §8 clarification |
| 12 | P0 gains the **capstone-window regression guard** (Day 31–36 exposes no required Spendwise CTA) — **test/self-test only, no UI change** | §16, §17 row 7, §18 P0 |

**No count moved in this pass.** 64 buildTasks / 56 required / 8 optional / 31 features / 38 lessonMap
entries / ≈229 buildSteps are unchanged; the identity strategy changed *inside* existing task
contracts, not the task inventory. Full derivation and the eight-check consistency gate:
`docs/report/2026-09-05-spendwise-import-identity-finalization-report.md`.

---

## Purpose

The reviewed draft was a good inventory and a poor plan. It counted the artifact accurately, found
the real orphans, and then made eleven commitments that either contradicted the architecture, cited
requirements the frozen curriculum does not contain, or would have shipped a schema change and a
progress-data change in different commits. This revision keeps the inventory, fixes the eleven, and
recomputes every total from the corrected design rather than from the draft's.

## Inputs

| Input | What it is | Weight |
|---|---|---|
| `docs/report/2026-09-05-spendwise-architecture-blueprint.md` | final architecture (26 Constitution rules, 17 ADRs, toolchain freeze, recomputed scope) | **binding** |
| course content at `e97c13a` | 39 lesson files / 40 records, `content/spendwise-project.json`, `tools/validate_project.py`, `tools/build_site.py`, `index.template.html`, `tests/` | **frozen — binding** |
| `docs/build-while-you-learn-plan.md` | product master plan | binding |
| `docs/build-while-you-learn-implementation-plan.md` | site/data implementation reference | binding except where measured stale (§18) |
| `docs/SPENDWISE_ARCHITECTURE_RESEARCH.md` | external research | evidence only |

## Reviewer orientation — where to push back hardest

Weakest first.

> **Item 0, inserted 2026-09-05 by the final import-identity correction — now the weakest claim in
> this plan.** **§13.1's fallback identity `IMPORT:<baseFingerprint>|OCC:<occurrenceIndex>`.**
> Its idempotency guarantee is **conditional on row order** and is verified by nothing: no code exists,
> so no re-import — ordered or reordered — has ever been run. Both tiers are also lexically invented:
> `sourceRef`, `referenceId`, `externalId`, `OCC:`, `occurrenceIndex` and `occurrence` are **all 0-hit
> in `content/`**; only the *mechanism* is taught, in one block (`day08-blk-27`,
> `content/lessons/day-08.json:211`). And it deliberately forbids `parallelStream` on the import path,
> an idiom the course teaches in **12** places — so a learner following day-12 breaks idempotency.
> A reviewer may reasonably argue the honest options were (a) require a source-provided reference and
> reject files without one, or (b) keep the collision and report it. This plan chose neither.
> The secondary new item, **§16/§17's capstone-window guard**, is weak in a different way: it passes at
> zero cost today, so it proves nothing now — its entire value is as a P1 regression guard.

1. **§2, the 64-task decomposition.** Derived from the blueprint's Evolution Contract, not measured
   from anything. The per-release counts are authoring estimates; the true number moves when the
   tasks are written. Every other number in this plan depends on this one. **It has already been wrong
   once:** the blueprint printed a total of 58 / 50 / 8 whose own per-release rows summed to 64 / 56 / 8,
   and this plan carried the 58 forward without re-adding it. Corrected on 2026-09-05 by the final
   planning reconciliation. A reviewer should re-add the column rather than trust any total row,
   including this one.
2. **§7, the progress-migration map.** It hand-maps three id changes and then asserts that no other
   learner data is at risk. That assertion rests on `sanitizeState` dropping unknown build-task ids
   (`index.template.html:1761`), which is verified — but the *behavioural* claim (that a learner
   perceives the migration as lossless) is not verifiable without a learner.
3. **§9, replacing a coverage percentage with named invariants.** Strongly evidenced as a *deletion*
   (`70%` and `90%` are 0-hit; day-30 disowns its own 75%), but the replacement list of invariants
   is authored here. A reviewer may find it under- or over-specified.
4. **§13's wave boundaries.** Each wave claims to leave the repo buildable. Verified by construction,
   not by execution — nothing in this session ran `build_site.py` or `pytest`, because running them
   would require the artifact edits the directive forbids.
5. **§18, declaring `docs/build-while-you-learn-implementation-plan.md:745` stale.** It says the
   in-page project checks stop at #32; the file has numbered blocks up to #57. I am overruling a
   binding document on the strength of a measurement.

---

## 1. Verified current state

Measured directly from the frozen artifact, not from the previous draft.

| Dimension | Value | Source of measurement |
|---|---|---|
| top-level keys | `schemaVersion, product, releases, features, buildTasks, milestones, architectureStages, lessonMap` | `content/spendwise-project.json`; mirrored by `TOP_LEVEL_KEYS` (`tools/validate_project.py:78-81`) |
| releases | 10, all `status: "planned"`, `order` 1..10 | pinned by `EXPECTED_RELEASES` + `_validate_releases` (`:176`, `:191-198`) |
| features | 25 | `len(project["features"])` |
| buildTasks | 24 — **22 required, 2 optional** | `required: false` on exactly `task-config-profiles`, `task-optimistic-locking` |
| tasks per release | V0.1 5, V0.2 5, V0.3 3, V0.4 4, V0.5 5, V0.6 2, **V0.7–V1.0 = 0** | `release["buildTaskIds"]` |
| milestones | 4 (`ms-java-foundation`, `ms-spring-api`, `ms-product-engine`, `ms-production-smart`) | artifact |
| architectureStages | 10, one per release | artifact |
| lessonMap | 38 entries: **16 `direct` / 4 `future` / 18 `theory`** | artifact |
| `direct` entries with empty `buildTaskIds` | 6 — `day-01`, `day-24`, `day-25`, `day-26`, `day-29`, `day-30` | artifact |
| `future` entries | `day-05`→v0-7, `day-07`→v0-2, `day-11`→v0-8, `day-12`→v0-8 | artifact |
| unmapped lessons | `day-39-64`, `day-65-66` | absent from `lessonMap`; `LESSON_IDS` (`:31`) includes them |
| artifact size | 65,050 bytes | `os.path.getsize` |
| generated site | 1,578,405 bytes | `index.html` |

Two facts about the artifact that constrain everything below:

- **`product.outOfScope` is exact-match validated** against `CANONICAL_OUT_OF_SCOPE`
  (`tools/validate_project.py:161`), 21 items. It already contains `"full multi-currency accounting
  engine"`, `"microservices"`, `"Kafka"`, `"Kubernetes"` — so the blueprint's scope exclusions need
  no artifact change.
- **V0.8's async-import criterion already says `optional`**: *"Large datasets can be imported as a
  background job (optional, 202 Accepted + ImportBatch status)"*. The blueprint drops `202 Accepted`
  as a *goal*; because the criterion is already marked optional, **no acceptance-criteria edit is
  required** — only the corresponding build task must be authored `required: false`. This corrects
  the draft, which proposed rewriting the criterion.

---

## 2. Target artifact: 64 build tasks, 31 features, 38 lessonMap entries

**Corrected by the pre-P0 sanity gate, 2026-09-05.** This heading previously read "39 lessonMap
entries". The lessonMap does **not** grow: it holds 38 entries today and 38 after this plan, because
`day-33` — which §6 previously described as an addition — **already exists**. §6 is corrected to
match. See the blueprint §9 "How lessonMap stays at 38 entries and reaches 24/1/13".

**Corrected again by the final planning reconciliation, 2026-09-05.** This heading also read "58 build
tasks". That number came from the blueprint's §9 total row, which was an addition error: its own
per-release rows summed to **64 / 56 / 8**. Re-derived from the id lists below and now stated as
**64 build tasks, 56 required, 8 optional**. Two corrections land in the same pass — V0.3 loses
`task-actuator-baseline` and V0.4 is 6 not 5 — and they cancel in the grand total, which is itself
proof that 58 was never derived from these lists. Per-release check:
6+5+3+6+7+6+8+8+9+6 = **64**; required 6+5+2+6+6+5+7+7+8+4 = **56**; optional = **8**.

Totals and their derivation are in the blueprint §9 and are not restated. What follows is the
authoring contract per release: the task list, and for each task the two prerequisite kinds that
§3 separates.

### V0.1 — 6 tasks, 6 required

| id | required | lessons | note |
|---|---|---|---|
| `task-project-foundation` | ✔ | day-01 | **new.** Repo, Maven project + wrapper, `com.spendwise` root, `mvnw test` green, runnable `main()`. See §8 |
| `task-money-vo` | ✔ | day-01, day-04 | keep; re-specified to the blueprint's one rounding rule set |
| `task-account-entity` | ✔ | day-04, day-05 | keep; gains `openingBalance` + the projection constraint |
| `task-transaction-entity` | ✔ | day-04, day-08 | keep; gains **positive-amount + typed-direction** |
| `task-category-model` | ✔ | day-07 | **renamed** from `task-category-enum` — it becomes an entity at V0.5, so the id must not name the mechanism |
| `task-domain-validation` | ✔ | day-04, day-08 | keep |

### V0.2 — 5 tasks, 5 required

`task-repository-interface`, `task-inmemory-repository`, `task-transaction-service`,
`task-statistics-aggregation`, `task-csv-read-write` — all kept. Two re-specifications:
`task-transaction-service` becomes the first appearance of `TransactionCreationService` with
`sourceRef`, and `task-statistics-aggregation` forbids `summingDouble` and mandates
`reduce(BigDecimal.ZERO, BigDecimal::add)` (see §5).

### V0.3 — 3 tasks, 2 required, 1 optional

`task-spring-bootstrap` ✔, `task-di-service-beans` ✔, `task-config-profiles` ✗ (unchanged).
**Identical to the baseline shape — V0.3 gains nothing.**

**Corrected by the final planning reconciliation, 2026-09-05.** This section read *"4 tasks, 3
required"* and listed a fourth entry, `task-actuator-baseline` ✗ **new optional** — *"the health
endpoint V0.9 will need, wired while the container is the lesson"*. Both halves were wrong:

- The count contradicted its own list. Three of the four ids were `task-spring-bootstrap` ✔,
  `task-di-service-beans` ✔, `task-config-profiles` ✗ — that is **2 required + 1 optional**, and
  adding an optional fourth makes 2 required + 2 optional, never "3 required". The measured baseline
  agrees: `content/spendwise-project.json` has V0.3 at **3 tasks / 2 required / 1 optional**.
- `task-actuator-baseline` is **deleted outright.** V0.3 rests on day-13 and day-14, where Actuator is
  **0-hit**. Its only appearance before day-29 anywhere in the corpus is as a *distractor answer* in a
  day-17 multiple-choice. It is taught at day-29 (25 hits) and day-30 (14), and the frozen artifact
  files it exclusively under V0.9. The blueprint's own §6 Timing Matrix already puts Actuator at
  day-29, so requiring it at day-13–14 violated the timing rule this plan exists to enforce.
  **A learner must not be asked to use Actuator before Day 29.**
- Actuator's home is the existing V0.9 `task-production-packaging`, which §2's V0.9 list already
  defines as covering OpenAPI + MDC + Actuator + Compose. **No new V0.9 task is created and the V0.9
  count stays at 9.**

### V0.4 — 6 tasks, 6 required

`task-rest-controllers` is **retired** and split into `task-account-endpoints`,
`task-transaction-endpoints`, `task-category-endpoints`; `task-dto-mapping`,
`task-bean-validation`, `task-error-handling-advice` unchanged. This split is progress-migration
case B (§7).

**Corrected by the final planning reconciliation, 2026-09-05.** This section read *"5 tasks, 5
required"*, which does not match its own list: 3 endpoint tasks + 3 kept tasks = **6**, all required,
a net **+2** over the baseline's 4. The retired `task-rest-controllers` is not counted.

### V0.5 — 7 tasks, 6 required

`task-jpa-entities` ✔, `task-jpa-relationships` ✔, `task-spring-data-repositories` ✔,
`task-flyway-baseline` ✔ **new** (migration + `ddl-auto: validate`), `task-balance-projection` ✔
**new** (the `@Version`-guarded projection and its invariant), `task-atomic-transfer` ✔ (kept,
re-specified to the linked-pair + `transferRef` model), `task-optimistic-locking` ✗ (kept optional —
see §5 for why the draft's promotion is reversed).

### V0.6 — 6 tasks, 5 required, one of them post-capstone

| id | required | lessons | window |
|---|---|---|---|
| `task-auth-foundation` | ✔ | day-22 | day-22 |
| `task-user-migration` | ✔ | day-22, day-23 | day-22/23 — `user_id` columns + scoped queries |
| `task-ownership-checks` | ✔ | day-23 | day-23 |
| `task-token-lifecycle` | ✔ | day-24 | day-24 — flow + **`TokenIssuer` seam** + logout revocation |
| `task-canonical-token-issuer` | ✔ | day-24 *(knowledge: day-33)* | **after day-36** — see §6. Not listed in `lessonMap["day-33"].buildTaskIds` |
| `task-auth-hardening-review` | ✗ | day-24 | optional; refresh rotation lives here and nowhere else |

`task-jwt-auth` is **retired**. Progress-migration case B.

### V0.7 — 8 tasks, 7 required

`task-budget-model` ✔, `task-budget-calculation` ✔, `task-recurring-model` ✔,
`task-recurring-generation` ✔, `task-rule-model` ✔, `task-rule-engine` ✔, `task-dashboard-read-model`
✔, `task-advanced-aggregation` ✗.

### V0.8 — 8 tasks, 7 required

`task-csv-parse` ✔, `task-import-batch-model` ✔, `task-import-row-transaction` ✔,
`task-duplicate-detection` ✔, `task-import-rule-application` ✔, `task-import-result-report` ✔,
`task-csv-export` ✔, `task-async-import` ✗ (optional, and **no `202 Accepted` contract** — ADR-012).

**Identity obligations placed on four of these tasks, 2026-09-05 (final import-identity correction).**
The task inventory does **not** change — 8 tasks, 7 required, exactly as above — only what these four
contracts must say. Full model: §13.1.

| Task | What its contract must carry |
|---|---|
| `task-csv-parse` | the parse loop is **sequential, in source-file order** — `parallelStream()` / `.parallel()` are forbidden on the import path, because occurrence indices are order-derived (R22 second clause). It must also expose whether a parsed row carries a **stable source reference**, since that selects the identity tier |
| `task-duplicate-detection` | both identity forms verbatim — `IMPORT:SRC:<sourceKey>:<accountId>:<sourceTxnId>` preferred, `IMPORT:<baseFingerprint>\|OCC:<occurrenceIndex>` fallback — the `normalize` rules, the `Map.merge` occurrence counter (`day08-blk-27`), the two-column `UNIQUE (user_id, source_ref)` DDL spelled out in full (composite `UNIQUE` is 0-hit), and the caught-exception decision (`DataIntegrityViolationException` is 0-hit and must be introduced by the task) |
| `task-import-row-transaction` | per-row `@Transactional`; the row goes through `TransactionCreationService.create(...)` and never inserts directly; a duplicate is recorded `DUPLICATE` and creates **no** transaction, applies **no** rule, touches **no** balance projection; two identical legitimate rows in one file legitimately produce two transactions |
| `task-import-result-report` | `ImportBatch` / `ImportRow` are **import history and reporting only** — their PKs are never identity inputs, though `batchId` and `rowNo` are displayed; the report distinguishes `OK` / `DUPLICATE` / `FAILED` per row and states the retry semantics of each |

### V0.9 — 9 tasks, 8 required

`task-reference-data-cache` ✔, `task-scheduled-reconciliation` ✔, `task-recurring-scheduler` ✔,
`task-exchange-rate-client` ✔, `task-invariant-test-suite` ✔, `task-slice-test-suite` ✔,
`task-integration-test-suite` ✔, `task-observability` ✔, `task-docker-compose` ✔ …and
`task-redis-cache-backend` ✗ optional. That is 9 required + 1 optional = 10 slots; the released
count is **9** because `task-observability` and `task-docker-compose` are authored as one
`task-production-packaging` ✔ covering OpenAPI + MDC + Actuator + Compose, which is how day-29 and
day-30 actually teach them (one lab, one deliverable).

Final V0.9 list: `task-reference-data-cache` ✔, `task-scheduled-reconciliation` ✔,
`task-recurring-scheduler` ✔, `task-exchange-rate-client` ✔, `task-invariant-test-suite` ✔,
`task-slice-test-suite` ✔, `task-integration-test-suite` ✔, `task-production-packaging` ✔,
`task-redis-cache-backend` ✗ — **8 required + 1 optional = 9**.

### V1.0 — 6 tasks, 4 required

`task-hardening-reconciliation` ✔, `task-portfolio-readme` ✔, `task-final-demo` ✔,
`task-defense-audit` ✔, `task-ai-category-suggestion` ✗, `task-ai-monthly-insight` ✗.

### Features 25 → 31

Six additions, each named by a promise the ten releases already make:
`feat-project-foundation` (v0-1), `feat-schema-migration` (v0-5), `feat-dashboard` (v0-7),
`feat-csv-export` (v0-8), `feat-testing` (v0-9), `feat-deployment` (v0-9).

Two corrections to the draft's feature proposal:

- **`feat-hardening` is dropped.** V1.0 hardening is tasks under existing features.
- **The proposed `Release` and `Class` columns are dropped from the data model.** `FEATURE_KEYS` is
  a closed five-key schema (`tools/validate_project.py:87`); adding presentational fields fails
  `_closed_keys` for no gain. `introducedInReleaseId` already carries the release.
- **`feat-testing`'s justification is rewritten.** The draft justified it with *"day-30 sets a
  JaCoCo ≥75% gate"* — a claim the curriculum contradicts (§9). Its real justification is that
  V1.0's `learningDependencies` include `"test coverage"` and V0.9's include
  `"Unit Testing", "Integration Testing", "Testcontainers"`, none of which any feature covered.

---

## 3. Two prerequisite kinds, never conflated

The draft's central structural defect: it used one "prerequisites" notion, so nothing stopped a task
from depending on an artifact that did not yet exist. Every task carries **two** lists.

**KNOWLEDGE PREREQUISITES** — lesson ids whose techniques the task requires. Bounded below by the
blueprint's Timing Matrix. A task may not be scheduled before its latest knowledge prerequisite.

**PROJECT-ARTIFACT PREREQUISITES** — task ids whose *output* must already exist in the learner's
repository. Bounded by the release order and by nothing else.

The rule that follows, and the two violations it kills:

> **No task may require a project artifact that a later task creates.**

- **Killed violation 1 — the dashboard cache at day-25.** The draft attached a
  `task-dashboard-cache` to day-25. The dashboard is a **V0.7** read model; day-25 sits inside V0.9's
  knowledge window but *before* V0.7 in the draft's own execution order. A learner reaching day-25
  has no dashboard to cache. Replaced per §4.
- **Killed violation 2 — the recurring scheduler at day-25.** Same shape: `RecurringTransaction` is
  a V0.7 entity. Scheduling its generation at day-25 requires an engine that does not exist.

Mechanically, each `buildStep` (§11) carries both lists as separate keys, and each task's
`relevantLessonIds` remains the knowledge list — which is what the validator already checks against
`LESSON_IDS` (`tools/validate_project.py:269-271`). The project-artifact list is a `buildStep` field,
because `BUILD_TASK_KEYS` is closed (`:88-91`) and adding a key to `buildTask` would break every
existing task object.

---

## 4. Day 25's three real subjects

Day-25 is `kind: theory` and states outright that it has no programming exercise of its own
(`day25-blk-1`: *"Ngày này không có đề bài lập trình riêng"*). It teaches four things, and three of
them can attach to artifacts that exist by then.

| Subject | Taught at | Spendwise task | Why it is legal here |
|---|---|---|---|
| reference-data cache | `day25-blk-3`/`blk-5` (`@Cacheable`, `@CacheEvict`, `ConcurrentMapCacheManager`), `blk-22` (`SimpleKeyGenerator` pitfalls), **`blk-24` (eviction runs before commit)** | `task-reference-data-cache` | **Category / reference data exists from V0.1** and is read-mostly, so day-25 has a real subject to cache. **Rule lists are NOT a day-25 subject** — the Rule engine is V0.7 and does not exist yet; once it ships, rule lists become cacheable behind the *same* annotations, which is later reuse of a taught technique, not new capability. **No money value is cached** (R11) — *corrected 2026-09-05, this cell previously read "categories and rules exist from V0.1/V0.7", which implied a Rule engine at day-25* |
| scheduled **balance reconciliation** | `day-25.json:290` `day25-blk-11` (`@Scheduled` semantics), `:296` (`fixedRate` vs `fixedDelay` vs `cron`, with an **explicit `zone` because the default is the JVM timezone**), `:303` `day25-blk-37` (`@EnableScheduling` + `@Scheduled(fixedDelay = 5*60*1000)`), `day25-blk-33` (single-thread scheduler trap) | `task-scheduled-reconciliation` | the invariant it checks is introduced at **V0.5**, so the artifact exists. This is the task the draft was missing |
| taught **async side effect** | `@Async`, `@EnableAsync`, `ThreadPoolTaskExecutor`, `CompletableFuture`, `AsyncUncaughtExceptionHandler`; `day25-blk-31` notes Java 17 has no virtual threads | folded into `task-production-packaging` as the fire-and-forget notification path | it has **no HTTP contract**, so it needs no endpoint and no `202` |
| Redis cache **backend** | `day25-blk-6`/`blk-7` (`entryTtl`, TTI needs Redis 6.2, KEYS+DEL vs `BatchStrategy`, JDK-serialization trap, stampede) | `task-redis-cache-backend` (**optional**, V0.9) | it is a configuration swap behind the same annotations, per ADR-010 |

**Later releases reuse the same APIs rather than introducing new ones.** V0.7's recurring generation
uses the `@Scheduled` learned here; V0.9's optional Redis task swaps the backend behind the
`@Cacheable` learned here. That is the whole point of attaching day-25 to reference data and
reconciliation: the *technique* lands early on an artifact that exists, and the *hard* application
arrives when its artifact does.

One citation caveat, recorded because a reader will notice it: `content/lessons/day-25.json:290` and
`:581` record that the `@Scheduled` **resource belongs to Day 27's `resourceIds`**, so day-25
presents `@Scheduled` as uncited general knowledge and **day-27 is where it is applied with
citations** — `content/lessons/day-27.json:139` (a cancel-pending-orders job), `:112` (`@Async`
email/inventory), `:278` (the after-commit rule), `:279` (`fixedDelay` non-overlap holds only for
consecutive runs of one method on one scheduler; multi-instance needs a distributed lock). This is
why §5 converts day-27 from `theory` to `direct v0-7`.

---

## 5. Task-level edits to existing tasks

| Edit | Reason |
|---|---|
| `task-category-enum` → **`task-category-model`** | it becomes a JPA entity at V0.5; the id must not name the mechanism. Progress-migration case A |
| `task-rest-controllers` **retired** → 3 endpoint tasks | one task covering three resources cannot be marked partially done, and the site's task view needs a leaf per resource. Case B |
| `task-jwt-auth` **retired** → 4 tasks + 1 optional | it conflated verification (day-22), flow (day-24) and issuance (day-33). Case B |
| `task-account-entity` gains `openingBalance` + the projection constraint | R8/R9 |
| `task-transaction-entity` gains positive-amount + typed-direction | R7 |
| `task-transaction-service` becomes the canonical `TransactionCreationService` with `sourceRef` | R20 |
| `task-statistics-aggregation` forbids `summingDouble`, mandates `reduce` | see below |
| `task-atomic-transfer` re-specified to the linked-pair + shared `transferRef` model | R21 |
| **`task-optimistic-locking` stays optional** | reverses the draft |

**Why `task-optimistic-locking` stays optional.** The draft promoted it to required, citing
`index.template.html:1588-1595` — but that citation is to `calculateReleaseProgress`, which counts
only `required !== false` tasks; it says nothing about whether *this* task should be required. The
substantive reason to leave it optional is that `@Version` is *already required* by
`task-balance-projection` (R8 mandates the versioned projection), so the standalone
optimistic-locking task is now genuinely supplementary hardening rather than the only place
`@Version` appears. Promoting it would double-count the same requirement.

**The `summingDouble` correction.** Day-10 counts, measured: `groupingBy` 10, `toMap` 8,
`summingDouble` 3, `reduce` 2, `Collectors.reducing` 0, **`BigDecimal` 0**. So the lesson that
teaches aggregation never once aggregates money, and its most prominent collector is
type-incompatible with R1. The taught-and-safe route is
`stream().map(Transaction::amount).reduce(BigDecimal.ZERO, BigDecimal::add)`, and
`Collectors.groupingBy` remains fine as the *grouping* half. Additionally,
`lessonMap["day-12"].application` currently endorses `summingDouble` — *"the groupingBy/summingDouble
step also mirrors the V0.2 statistics aggregation"* — which must be corrected in the same wave that
converts day-12 to `direct`, or the site will teach a rule the architecture forbids.

---

## 6. JWT task placement

Three tasks in the taught window, one after the capstone, one optional. Full rationale is blueprint
§7; the executable contract is here.

| Task | Window | Knowledge prereqs | Artifact prereqs | Acceptance |
|---|---|---|---|---|
| `task-auth-foundation` | day-22 | day-22 | V0.5 persistence | `PasswordEncoderFactories.createDelegatingPasswordEncoder()` hashes on register; `matches(raw, encoded)` verifies on login; `SecurityFilterChain` with `SessionCreationPolicy.STATELESS`; a request with no token gets 401, with a bad token 401, with a valid token 200 |
| `task-user-migration` | day-22/23 | day-21, day-22 | `task-flyway-baseline` | a versioned migration adds `user_id` + FK to every owned table; every list query is scoped |
| `task-ownership-checks` | day-23 | day-23 | `task-user-migration` | User A requesting User B's account gets **404**; `SecurityContextHolder` is read in exactly one class |
| `task-token-lifecycle` | day-24 | day-24 | `task-auth-foundation` | login returns a token produced through a **`TokenIssuer` interface**; after logout the same token is rejected with 401 (`content/lessons/day-24.json:246`, required group); the interface has no signing implementation in the learner's code yet |
| `task-canonical-token-issuer` | **after day-36** | day-33 | `task-token-lifecycle` | the single `TokenIssuer` implementation uses `NimbusJwtEncoder` + `ImmutableSecret` + `JwtClaimsSet`; **the test calls `encode()`**, because a short secret fails at first encode and not at startup (`content/lessons/day-33.json:254`); the HS256 secret is ≥32 bytes UTF-8. `relevantLessonIds = ["day-24", "day-33"]`; **absent from `lessonMap["day-33"].buildTaskIds`** |
| `task-auth-hardening-review` | optional | day-24 | `task-canonical-token-issuer` | refresh rotation and replay detection live here **only**, explicitly labelled not-graded |

**The draft's "syntax hint, not a solution" instruction is deleted.** It attempted to give day-24 a
partial `JwtEncoder` snippet with the reassurance that it was only a hint — which is precisely
handing a learner an implementation of an API taught nine lessons later. The seam replaces it.

**Nothing is added inside day-31→36.** `day-33` **already has** a `lessonMap` entry, so this is a
**MODIFICATION of an existing entry, not an addition** — the entry count stays at 38. Today it reads:

```json
"day-33": {
  "applicationType": "theory",
  "context": "Sprint 1 của dự án capstone e-commerce: … không xây tính năng Spendwise."
}
```

**Corrected by the pre-P0 sanity gate, 2026-09-05.** This paragraph previously said day-33 "gains a
`lessonMap` entry (it must, to be reachable from the site as the knowledge source)" and that the
entry's `buildTaskIds` lists `task-canonical-token-issuer`. Both halves are now overruled by the
blueprint's **§7.1 R-DAY33**, which is binding on this plan:

- The entry is **retyped** `theory` → `direct v0-6` and its five missing keys are filled
  (`releaseId`, `featureIds`, `projectProblem`, `application`, keeping the existing `context`).
- **`buildTaskIds` stays EMPTY (`[]`), permanently.** `task-canonical-token-issuer` is **not** listed
  there.

The reason is the CTA. `direct` + a non-empty `buildTaskIds` renders a clickable toggle with
`aria-label` *"Đánh dấu hoàn thành: …"* and a `required` chip (`index.template.html:2042`), i.e. it
tells the learner *build this required Spendwise task now* — on a lesson that sits inside the graded
capstone, which is precisely what §6's post-day-36 scheduling exists to prevent. `direct` with an
**empty** `buildTaskIds` renders the project context and feature list but **no toggle**, because
`appendBuildTaskList` returns early on an empty array (`index.template.html:2074`). That is
schema-legal: `_require_str_list` is called on `buildTaskIds` **without** `nonempty_list`
(`tools/validate_project.py:415`), which is the same allowance that lets day-08 and day-21 convert.
Six entries already ship in that shape (day-01, 24, 25, 26, 29, 30).

**KNOWLEDGE UNLOCK ≠ PROJECT EXECUTION.** Day-33's role is to unlock `JwtEncoder` / `JwtClaimsSet` /
`NimbusJwtEncoder` knowledge; the Spendwise execution of `task-canonical-token-issuer` happens
**after day-36**, inside the self-study roadmap. The task remains valid without a lessonMap
back-reference: task ownership runs task → release
(`_validate_release_task_links`, `tools/validate_project.py:320-326`), not task → lesson, so nothing
is orphaned and no validator rule is violated. Day-33 **discoverability is solved in the other
direction**: `task-canonical-token-issuer.relevantLessonIds` becomes `["day-24", "day-33"]` — that
field is validated non-empty (`tools/validate_project.py:261`, ids checked at `:269`) and is rendered
as a *"Relevant Lessons"* disclosure of real `#lesson/<id>` links on the task's own article
(`index.template.html:2088`). So the link exists on the **task** page, where no build-now framing
applies, and `alsoUsedIn` (§16) is **not** needed for this. ~~The **execution window** stays where it
was: in the task's `constraints` prose and its `buildStep` ordering, **not** in the mapping.~~

**That last sentence is withdrawn (pre-P0 sanity gate, 2026-09-05 — measured).** Neither named carrier
can reach a lesson page, so the window cannot live there:

- **`constraints` never renders on a lesson page.** It is emitted only by `appendBuildTaskDetails`
  (`index.template.html:2085`, its label at `:2097`), reached only via
  `createExpandableBuildTaskItem` (`:2128`) → `appendExpandableBuildTaskList` (`:2135`), whose only
  two call sites are the Build Tasks workspace (`:3396`) and the release detail view (`:3516`). The
  lesson page calls `appendBuildTaskList` (`:2912`), which never reads `constraints`.
- **`buildSteps` has no renderer at all** — 0 hits across `index.template.html`, `tools/`, `tests/`
  and `content/`. It is a key P0 *adds*; today nothing reads it, so "buildStep ordering" communicates
  nothing to anyone.
- **"after day 36" is 0-hit in the artifact** — `content/spendwise-project.json` has one `day-36`
  occurrence and no spelling of the window at all.

The window must therefore be written into **`application` and `projectProblem`**, the only strings on
this route a learner sees. That is constraint 2 below, and it is why it is mandatory.

**Three P1 authoring constraints added by adversarial verification (pre-P0 sanity gate, 2026-09-05).**
Detail: `docs/report/2026-09-05-spendwise-pre-p0-sanity-gate.md` §2.1.

1. **Write `"buildTaskIds": []` explicitly — never omit the key.** `_require_str_list` rejects a
   missing key at `tools/validate_project.py:134-135` before the `nonempty_list` branch at `:137` is
   reached. Measured: `direct` with the key absent → `ERROR lessonMap day-33 buildTaskIds must be a
   list`; `direct` with `[]` → 0 errors.
2. **`application` and `projectProblem` must state the post-day-36 scheduling in their own text.**
   Converting to `direct` **deletes the "not now" framing from two surfaces**. The lesson page loses
   nothing (the `context` string is retained), but the dashboard's "Today's Project Impact" panel
   branches on `application` at `index.template.html:2426-2433` — today a learner resuming at day-33
   sees the `context` prose there *including* "không xây tính năng Spendwise"; once `application`
   exists, that sentence disappears from the dashboard entirely. And `index.template.html:3623`
   glosses the map badge as *"direct (xây trực tiếp)"* — "build directly" — by type alone. The prose
   must carry what the type now contradicts.
3. **Do not leave day-33 `theory` while filling the other five keys.** A `theory` entry carrying
   `application` renders the **full** application section including the build-task CTA — the guard at
   `index.template.html:2895` is on the *field*, not the type, and `:2911-2912` have no type gate.
   Measured: `theory` + `application` + `buildTaskIds: ["task-jwt-auth"]` validates with **0 errors**.
   `theory` is not a safety mechanism; only an empty `buildTaskIds` is.

**The rejected alternative, recorded so it is not re-litigated.** `applicationType: future` +
`buildTaskIds: []` also suppresses the CTA *and* renders *"Áp dụng ở release sau; đây không phải build
ngay trong bài học này."* (`index.template.html:2876-2882`), and it already ships on **day-05, day-11
and day-12**. It was rejected on wording, not mechanism: *"Áp dụng ở release sau"* asserts a **later
release**, which is false — day-33's release is V0.6 and only its *execution* is later in lesson time.
Suppressing a CTA by misstating the release spine is the wrong trade in a project organized around
that spine. A reviewer who weighs the deleted disclaimer more heavily than the release-order claim
should overrule this and use `future`; constraint 2 above is what makes `direct` acceptable.

---

## 7. Progress migration: three cases, one shipping boundary

The draft claimed a `STATE_VERSION` 2→3 bump with *"no data loss, no special-case migration code"*.
That claim was false in one direction and unfounded in the other: three task ids change
incompatibly, and adding `steps: []` to a state object is not evidence that renamed ids survive.

Current mechanics, verified: `STATE_VERSION = 2` (`index.template.html:1714`);
`sanitizeState(input, validLessonIds, validUnitIds, validPracticeKeys, validBuildTaskIds = new Set())`
(`:1732`) rebuilds `projectProgress` from scratch every call (`:1758`) and keeps only ids present in
`validBuildTaskIds` (`:1761`). **So an unmapped renamed id is silently dropped today.** That is
correct sanitization and wrong migration.

| Case | Instance | Strategy |
|---|---|---|
| **A — renamed id** | `task-category-enum` → `task-category-model` | **map it.** A one-entry rename table applied *before* the `validBuildTaskIds` filter. Completion is preserved because the work is identical |
| **B — split task** | `task-rest-controllers` → 3; `task-jwt-auth` → 4+1 | **preserve history, do not auto-complete.** The old id is recorded in a new `projectProgress.legacyCompleted[]` array and **none** of the successor tasks is marked complete. Auto-completing all successors would claim work the learner never did (the JWT split in particular now contains a post-capstone task) |
| **C — changed acceptance semantics** | `task-account-entity`, `task-transaction-entity`, `task-transaction-service`, `task-atomic-transfer` | **old completion is historical evidence only.** The id survives, so the checkbox survives, but the release view shows a "criteria changed" marker sourced from the artifact, not from state. The learner is not silently credited with meeting criteria that did not exist when they ticked it |

Shape of the v3 state object:

```js
projectProgress: {
  buildTasks: [],        // ids valid under the CURRENT artifact
  legacyCompleted: [],   // ids completed under a previous artifact, retired since
}
```

Migration function, and the two things it must not be:

```
migrateProjectProgress(v2Progress):
  1. apply RENAME_MAP (case A) to every id
  2. partition: known ids  -> buildTasks
               retired ids -> legacyCompleted
  3. never synthesize a completion for a successor task (case B)
```

It must not be a no-op that relies on sanitization, and it must not be a blanket carry-forward.

**Shipping boundary.** The `STATE_VERSION` 2→3 bump, `migrateProjectProgress`, `RENAME_MAP`, the
`legacyCompleted` field, the artifact rewrite that introduces the incompatible ids, and
`tests/site_core.test.js:161`'s `assert.equal(core.STATE_VERSION, 2)` **all ship in one commit**. A
learner who loads the site between an artifact commit and a migration commit loses their build
progress to sanitization, permanently and silently. This is the single hardest ordering constraint in
the plan.

---

## 8. Empty-project onboarding

A learner arrives with **no Spendwise repository**. Today the artifact's first task is
`task-money-vo`, which presumes a compiling Maven project. `task-project-foundation` closes that gap
in exactly one task — not a padded sequence — and its content is fully specified so the mentor
invents nothing:

| Element | Specified value | Authority |
|---|---|---|
| repository | one new git repository, `spendwise` | decision |
| build tool | Maven with the **wrapper** committed (`mvnw`, `mvnw.cmd`, `.mvn/wrapper/`) — **project/tooling scaffolding, not a Day-01 learning objective**; the mentor may guide the setup (see the clarification below) | blueprint §8; `content/lessons/day-35.json:320` runs `./mvnw` |
| Java | **17**, `maven.compiler.release=17` | `tools/validate_lessons.py:1005` compiles the corpus with `--release 17` |
| Spring Boot | **not yet.** V0.1 has no Spring dependency at all — and therefore `SPRING_BOOT_EXACT_PIN_PENDING` **does not block this task** | V0.1 acceptance: *"No dependency on Spring, database, or REST"*; blueprint §8.1 as amended 2026-09-05 |
| parent POM | added at **V0.3** by `task-spring-bootstrap`, `spring-boot-starter-parent`, minor pinned then and frozen. **That task is where `SPRING_BOOT_EXACT_PIN_PENDING` is a hard prerequisite**, and it must be resolved before the learner executes it | blueprint ADR-017, §8.1 |
| package root | `com.spendwise`; first code in `com.spendwise.shared` and `com.spendwise.account` | blueprint D1 |
| how to run | `./mvnw test` and `./mvnw exec:java` / a `main()` in `com.spendwise.SpendwiseApp` | decision |
| where first code belongs | `src/main/java/com/spendwise/shared/Money.java` | blueprint D1 |
| acceptance | `./mvnw test` exits 0 with at least one passing test; `git log` has one commit; the tree has no IDE files | decision |

**Canonical V0.1 contract, restated so it cannot drift again** (final planning reconciliation,
2026-09-05): `task-project-foundation` = Java 17 + Maven with the Wrapper + root package
`com.spendwise` + a runnable `main()` + tests green + **NO Spring Boot dependency**. A plain Maven
POM. The blueprint §8.1 previously called the Boot pin a *"HARD prerequisite of
`task-project-foundation`"*; that has been withdrawn in favour of this section, which was right all
along. The pin is now a hard prerequisite of **`task-spring-bootstrap` (V0.3)**.

**A structural exception that must be disclosed rather than assumed** (measured 2026-09-05): **Maven
is 0-hit in day-01 – day-11 and in day-13/day-14.** The corpus's only early `pom.xml` is a JMH snippet
in day-12, and `mvnw` first appears at day-35 (`content/lessons/day-35.json:320`, cited above). So
`task-project-foundation` requires a build tool that no lesson in its own window teaches. That is
accepted — a learner cannot build anything without one — but it means the task must carry its own
Maven commands in its `constraints` instead of citing a lesson, exactly as V0.7's rounding contract
must. Recorded as blueprint §11 gap 12.

**What that exception means, stated precisely** (clarified 2026-09-05 by the final import-identity
correction — wording only, no task, count or criterion changes):

- Maven and the Maven Wrapper at V0.1 are **project/tooling scaffolding**, not a **Day-01 learning
  objective**. Nothing here asks Day 01 to teach Maven, and nothing asks the learner to derive a
  build configuration from Day-01 theory.
- The **mentor may guide the setup directly** — supply the `pom.xml`, run `mvn -N wrapper:wrapper`,
  explain `./mvnw test` — because this is environment preparation, not the graded work.
- What the learner is accountable for at V0.1 is the **Java** content: `Money`, the domain types, the
  tests. The build tool is the vehicle.
- The task's `constraints` therefore read as **setup instructions**, not as a lesson to be mastered.
- **Spring Boot remains absent until V0.3.** V0.1's POM is a plain Maven POM with no Spring
  dependency, which is why `SPRING_BOOT_EXACT_PIN_PENDING` does not block this task (see the table's
  Spring Boot row).

**Why the mentor cannot improvise here.** Left unspecified, a coding mentor asked to "start
Spendwise" will scaffold from `start.spring.io` (0-hit in the corpus), pick a Spring Boot version at
random, and very likely choose Gradle — which appears **zero times repo-wide**. Each of those is an
architecture change under blueprint §10 trigger 13, made silently on turn one.

---

## 9. Testing requirements, without an invented percentage

**No coverage percentage is a graduation condition.** Evidence, measured across `content/`:
`75%` 17 hits, `80%` 11, `100%` 1, **`70%` 0, `90%` 0**. So the research's *"≥ 70% line, ≥ 90% cho
`common/money`, `budget/`, `recurring/`, `rule/`"* (`docs/SPENDWISE_ARCHITECTURE_RESEARCH.md:1143`)
is invented and is rejected, and the draft's *"day-30 sets a JaCoCo ≥75% gate"* misreads its own
source. Day-30 disowns it: `content/lessons/day-30.json:253` — *"CHƯA CHỐT - không dùng làm điều
kiện chấm ở bài này … Mức quan sát duy nhất áp dụng ở đây: report được sinh ra và mở được."* —
and `:120` records JaCoCo threshold configuration as *"khoảng trống kiến thức thật sự"*, one of the
four items `:233` lists as genuine gaps in Lab 10. The one in-curriculum percentage,
`content/lessons/day-09.json:161` *"Test coverage ≥ 80% (theo đề bài)"*, is Lab 3's own requirement
for `SimpleArrayList`/`SimpleHashMap` — not Spendwise.

What **is** required, as the acceptance criteria of `task-invariant-test-suite`,
`task-slice-test-suite` and `task-integration-test-suite`:

**Named financial invariants** — each with at least one test:
1. `balance == openingBalance + Σ signedEffect(t)` after an arbitrary create sequence
2. `Transaction.amount` is always positive; a negative input is rejected
3. money arithmetic never loses a cent across a CSV write→read→aggregate round trip
4. cross-currency arithmetic throws
5. a budget's `spent` equals a hand-computed `SUM` over the same period
6. reconciliation reports zero drift on a seeded history

**Critical business flows** — each with an end-to-end test:
7. transfer commits both rows and both projections, or neither
8. the same recurring period never generates twice
9. rules apply in priority order, deterministically
10. importing the same **statement** twice adds zero transactions — *amended 2026-09-05 (final
    import-identity correction): the subject is the statement's rows, identified per §13.1; the old
    wording "the same file" invited a whole-file identity, which day-26's `MultipartFile` cannot even
    express*
10a. a statement containing **two byte-identical data rows** and no source reference adds **2**
    transactions (`OCC:1`, `OCC:2`), and re-importing it adds **0** while reporting **2**
    `DUPLICATE` rows — *added 2026-09-05; this is the regression test for the withdrawn
    collapse-into-one behaviour*

**Ownership and security boundaries:**
11. User A gets 404 for User B's account, transaction and budget
12. no token → 401; bad token → 401; valid token → 200
13. a token rejected with 401 after logout

**Persistence behaviour:**
14. data survives restart (Testcontainers, `postgres:16-alpine`)
15. `ddl-auto: validate` starts against the migrated schema
16. the `UNIQUE (user_id, source_ref)` constraint rejects a duplicate at the database level — and
    **accepts** two rows differing only by their `OCC:` suffix, because those are different strings
    (*second clause added 2026-09-05*)

**Failure scenarios:**
17. a mid-transfer failure rolls back entirely
18. a malformed CSV row fails alone; its 99 siblings commit
19. the FX client's failure degrades display, never a ledger write

**JaCoCo:** the report is generated by `mvn verify` and opened at
`target/site/jacoco/index.html` (`content/lessons/day-30.json:252`). Reading it is the deliverable.
The percentage is not a gate — day-28's own pedagogy is the reason:
*"con số phần trăm là chỉ dấu, không phải mục tiêu"* (`content/lessons/day-28.json:349`), with the
commonMistake at `:369`: *"Coi tỉ lệ coverage là mục tiêu và viết test cho getter/setter thay vì phủ
các nhánh xử lý lỗi."*

**Tier placement** (correcting the draft, which put both suites on day-28): day-28 owns unit +
MVC slice + JPA slice; **day-29 owns Testcontainers integration**. Day-28's Testcontainers content
is a single `note` block, `day28-blk-13`, stating no resource describes it; day-29 carries the real
code in `day29-blk-13`.

---

## 10. Three states, never conflated

The draft treated "the project" as one thing. It is three, and a mentor that confuses them will tell a
learner their code is wrong when it is merely unfinished.

| State | Where it lives | Who writes it | What it means |
|---|---|---|---|
| **AUTHORED EXPECTED** | `content/spendwise-project.json` → embedded verbatim in `index.html` | the course author | what Spendwise *should* become. Same for every learner. Changes only by a repo commit |
| **LEARNER PROGRESS** | `localStorage`, `projectProgress` | the learner, by clicking | what the learner *claims* to have finished. Self-reported. Never verified by anything |
| **ACTUAL CODE** | the learner's own git repository | the learner | what actually exists. **The site cannot see this. It never has and this plan does not change that** |

Consequences that the plan is built on:

- A ticked checkbox is **not** evidence the code exists. `calculateReleaseProgress`
  (`index.template.html:1588-1595`) counts ticks, nothing more.
- The mentor prompt (§14) must therefore say *"read the repository, do not trust the checklist"* — and
  it does, as a required field.
- Task **acceptance criteria** are written to be verifiable **by running the learner's code**, never
  by consulting site state. Every criterion in §9 is a test or an observable command result.
- `legacyCompleted` (§7) is LEARNER PROGRESS about a *retired* AUTHORED id. It is history, never
  input to a completion calculation.

---

## 11. The step contract

`buildSteps` is a new **top-level** array, not a nested field. Reason: `BUILD_TASK_KEYS` is closed at
`tools/validate_project.py:88-91`, so adding `steps` inside a `buildTask` object fails validation for
every existing task; and `tests/test_build_site.py:73-75` assert that `"facts"`,
`relevantHeadings` and `fallbackEvidence` are never embedded, which establishes the precedent that
the embedded model is a deliberate subset — a new top-level array is the additive shape that does not
disturb it.

Fourteen keys, all required unless noted:

| Key | Type | Purpose |
|---|---|---|
| `id` | string | `step-<task-slug>-<nn>` |
| `taskId` | string | must exist in `buildTasks` |
| `order` | int | 1..n contiguous within a task |
| `title` | string | imperative, one line |
| `intent` | string | *why* this step, in business terms |
| `knowledgePrereqLessonIds` | string[] | §3, may be empty |
| `artifactPrereqTaskIds` | string[] | §3, may be empty |
| `filesTouched` | string[] | paths relative to the learner's repo root |
| `doneWhen` | string | one observable outcome |
| `verifyCommand` | string | e.g. `./mvnw -Dtest=MoneyTest test` |
| `architectureRules` | string[] | Constitution rule ids this step must not violate |
| `commonMistake` | string, optional | one sentence |
| `mentorHint` | string, optional | what the mentor may reveal if asked |
| `estimatedMinutes` | int, optional | |

Volume: **≈229 steps** across 64 tasks (≈3.6 per task) — *corrected 2026-09-05 from "≈205 steps across
58 tasks"; the task count was an addition error and the step estimate followed it. Recomputed as 56
required × ~4 + ~5 for the two multi-step optionals.* This is an authoring estimate, not a
measurement — it is derived from the per-release contracts in §2 and is the number a reviewer should
challenge first if the wave sizing looks wrong.

Validator additions, all in the same closed-schema style as the existing code:

```
BUILD_STEP_KEYS = {...}                      # closed, mirrors the table above
_validate_build_steps(project, errors):
  - every id unique
  - every taskId ∈ buildTask ids
  - order contiguous 1..n per task, no gaps, no duplicates
  - every knowledgePrereqLessonId ∈ LESSON_IDS      (same source as :269-271)
  - every artifactPrereqTaskId ∈ buildTask ids
  - every architectureRules entry matches ^R\d{1,2}$
  - **no artifactPrereqTaskId belongs to a release ordered later than this step's task's release**
```

That last check is what makes §3's rule mechanical rather than aspirational — the day-25 dashboard
violation would have failed the build.

**Two step-contract constraints the import identity model imposes** (added 2026-09-05 by the final
import-identity correction; both are *authoring* obligations on step data, not new validator rules):

1. **Every V0.8 import-path step cites `R22` in its `architectureRules`.** R22 now carries the
   sequential-parse clause (blueprint §3), so a step that parses, fingerprints or inserts an imported
   row is bound by it. Steps whose `verifyCommand` exercises the parse loop must state in
   `commonMistake` that `parallelStream()` breaks occurrence indices — `parallelStream` has **12**
   corpus hits and a learner arriving from day-12 will reach for it.
2. **The identity clause stays inside `R22`, not a new rule id.** `architectureRules` entries are
   validated against `^R\d{1,2}$` (the pattern in the block above), so `R22a`, `R22-1` and any
   suffixed id would fail `_validate_build_steps`. The Constitution therefore stays at **26 rules**,
   and the order-dependence requirement is written as R22's second clause. This is the reason it is a
   clause and not a rule; it is recorded here so a later author does not "tidy" it into `R27` and
   silently change the rule count.

---

## 12. Site changes

**Wave column added by the final planning reconciliation, 2026-09-05.** The table previously listed
these seven changes without saying which wave owns each, and §18 assigned the route and the task
detail view to P0. Both are learner-facing UI, and P0 is data plumbing — the master plan's governing
principle is *"Data first. UI second."* (`docs/build-while-you-learn-plan.md` §25). They move to **P3**.

| Change | File:line | Wave | Note |
|---|---|---|---|
| `STATE_VERSION` 2 → 3 | `index.template.html:1714` | **P0** | with §7's migration, same commit |
| `projectProgress.legacyCompleted` | `:1716-1730` `defaultState()`, `:1758-1761` `sanitizeState` | **P0** | new array, sanitized against retired ids |
| `CourseCore` export surface | `:1804-1812` | **P0** | export `migrateProjectProgress` so `tests/site_core.test.js` can test it without a DOM |
| self-test #53 rewrite | `:5115-5142` | **P0** | see below — rewritten before it can crash |
| day-20 toggle count 3 → 5 | `:4792` | **P1** | self-test #37; V0.5 grows from 5 to 7 tasks. Moves with the V0.5 task edits that cause it |
| `#/task/:taskId` route | `:1539-1552` `parseRoute` | **P3** *(moved from P0)* | new branch; today there is none. **Learner-visible navigation — not plumbing** |
| task detail view rendering `buildSteps` | new render function near `createProjectProgress` (`:1953-1974`) | **P3** *(moved from P0)* | shows the 14 fields; per-step ticks are **display only**, never new state. Lands with the Mentor Prompt UI, once `buildSteps` data actually exists |

**Why the two moved.** A route and a detail view are the learner-facing surface of `buildSteps` data
that does not exist until P1/P2 writes it. Building them in P0 means shipping a view of an empty array
— "degrading gracefully with no steps" was the previous wording, which is another way of saying the
feature is inert until two waves later. It also inverts the wave model: P0 would become the largest
UI change in the plan while claiming to be schema plumbing. Deferring them to P3 puts them beside the
Mentor Prompt contract, which reads the same task fields, so one wave owns all task-detail rendering.

**Self-test #53 is the subtle breakage.** At `:5120-5122`:

```js
var emptyRelease = (projectData.releases || []).find(function(r) { return (r.buildTaskIds || []).length === 0; });
...
location.hash = "#/release/" + emptyRelease.id;
```

Once V0.7–V1.0 own tasks, **no release has an empty `buildTaskIds`**, `emptyRelease` is `undefined`,
and `emptyRelease.id` throws a `TypeError` that the outer `catch` at `:5209` converts into
`"self-test crashed: …"`. The symptom is a whole-harness crash reported as one opaque failure, not
"#53 failed" — which is exactly the kind of failure that costs an hour. The rewrite asserts the new
invariant instead: **every release has at least one task**, and the empty-state branch is exercised by
a synthetic release object rather than by a real one.

For the record, the harness is larger than `docs/build-while-you-learn-implementation-plan.md:745`
claims (*checks reach only #32*): measured **49 numbered blocks, 62 `assert(` calls, highest id #57 at
`:5194`**, tallied at `:5226` by `passed === results.length && results.length >= 15`. That
implementation-plan line is stale and should not be used for sizing.

---

## 13. Import semantics, fully explicit

The draft said *"no partial commit"* and left it there. That phrase has two incompatible readings and
the wrong one is unimplementable with the taught toolset. Resolved:

**Per-row atomicity. Not per-file.** A malformed row fails alone; its siblings commit.

| Question | Answer |
|---|---|
| unit of atomicity | **one row** = one `@Transactional` service call |
| a malformed row | rejected, recorded in the batch's error list with its row number, **does not** roll back other rows |
| a duplicate row | detected by the row identity of §13.1 (`sourceRef = IMPORT:SRC:…` where the file supplies a stable reference, otherwise `IMPORT:<baseFingerprint>\|OCC:<occurrenceIndex>`) and the `UNIQUE (user_id, source_ref)` constraint; re-importing the same statement adds **zero** transactions |
| two *legitimate* rows with identical business fields in one file | **two** transactions, not one — they differ by `OCC:1` / `OCC:2` (§13.1). This row was added 2026-09-05 by the final import-identity correction; the earlier model collapsed them and reported the loss |
| re-import of a *partially* imported file | identity is recomputed from row content plus its occurrence position, so already-imported rows produce the **same** `sourceRef` and are skipped as `DUPLICATE`; previously-failed rows committed nothing, so they insert cleanly on the retry. **No dependence on reusing a `batchId`**. Requires the retry to present the same rows in the same order — see §13.1's limitation |
| what the caller sees | a synchronous `ImportBatch` summary: total / imported / skipped-duplicate / failed, plus per-row errors |
| status code | **200**, with the summary body. **`202 Accepted` is deleted** — it is 0-hit in `content/` and there is no taught mechanism for polling an async job status |
| the async path | the *optional* V0.9 task, using day-25's `@Async`, with **no HTTP contract change** — the endpoint stays synchronous; async is used only for the fire-and-forget notification |
| bulk-insert optimizations | **not used.** `ON CONFLICT` and `SKIP LOCKED` are 0-hit; duplicate handling is the JPA-level constraint violation |

**Why per-row and not per-file.** Per-file atomicity means one bad row in a 5,000-row bank export
discards the other 4,999 — pedagogically it teaches the wrong lesson about resilient ingestion, and
it makes `sourceRef`'s row-level idempotency pointless. Per-row is also the only version the taught
stack can express cleanly: a `@Transactional` method per row, and a caller loop that catches the
constraint violation. There is nothing in the corpus about batch-scoped rollback with
partial recovery.

### 13.1 Import identity — the canonical model (added by the final planning reconciliation, 2026-09-05; **rewritten the same day by the final import-identity correction**)

> **Two corrections, in order.** The *first* pass killed `IMPORT:<batchId>:<rowNo>`, because a
> regenerated `ImportBatch` PK can never collide on re-upload, and replaced it with a bare content
> fingerprint. The *second* pass — this one — kills the bare fingerprint, because it collapses two
> **legitimate** transactions that happen to share every business field. Reverting to
> `IMPORT:<batchId>:<rowNo>` remains forbidden for the original reason. What is withdrawn from the
> first pass, quoted so nothing is silently rewritten:
>
> > *"**The collision, stated rather than hidden.** … A real transaction is lost. This is an accepted
> > cost, not a solved problem…"*
> >
> > *"**no automatic occurrence counter** — a counter would restore order-dependence and break
> > stability across re-import, which is the whole defect being fixed."*
>
> Both are overturned. Losing a real transaction is not an acceptable frozen V1.0 dedup strategy for a
> finance ledger, and the order-dependence objection is answered — not dissolved — by making
> source-file order an explicit architectural constraint (R22's second clause) and by documenting the
> residual limitation rather than claiming universal bank-file dedup.

**The hole the first pass closed.** The table above previously said a duplicate row is detected by
`sourceRef = IMPORT:<batchId>:<rowNo>`, and that re-importing a partially imported file works because
it carries the *"same `batchId`"*. **Nothing in this plan or the blueprint made that true.**
`ImportBatch` is a JPA entity created once per upload, so `batchId` is a freshly generated PK every
time. Upload the same file twice and every row gets a *different* `sourceRef`; the
`UNIQUE (user_id, source_ref)` constraint never fires; every row imports again. Duplicate detection
would have failed silently, contradicting the frozen V0.8 acceptance criterion — *"Importing the same
**transaction** multiple times does not create uncontrolled duplicates"*. The criterion's subject is
the **transaction**, not the file, and that is what fixes the model.

**Level 1 — preferred: a stable source-provided reference.** If the imported row carries an id the
*source* assigned it (a bank reference number, a statement transaction id, an end-to-end id), that is
the row identity. It is scoped so one source's id space cannot collide with another's:

```
sourceRef = "IMPORT:SRC:" + sourceKey + ":" + accountId + ":" + normalize(sourceTxnId)
```

`sourceKey` identifies the statement source/format the learner is importing from; `accountId` scopes
it to the owning account (and `user_id` is already the constraint's first column). This tier is
preferred because it is **order-independent** — it survives arbitrary reordering, filtering and
reconstruction of the file.

**Level 2 — fallback, when the file supplies no such reference:**

```
baseFingerprint = accountId | occurredOn | direction | amount(scale 2, toPlainString)
                            | normalize(description)
occurrenceIndex = the 1-based occurrence number of that SAME baseFingerprint within the
                  current imported statement, counted in source-file order
sourceRef       = "IMPORT:" + baseFingerprint + "|OCC:" + occurrenceIndex
normalize(s)    = trim → collapse internal whitespace to a single space → uppercase
```

So a statement containing two byte-identical data rows yields **two** identities — `…|OCC:1` and
`…|OCC:2` — and therefore **two** transactions. Re-importing that same statement recomputes both,
collides with both, and adds **zero**, reporting **two** `DUPLICATE` rows.

- Identity is a pure function of **row content plus the row's occurrence position among its own
  duplicates**. `batchId` and `rowNo` are still stored on the `ImportRow` record — they are what the
  error list and the summary display — but they are **not** inputs to identity.
- `amount` uses `toPlainString()` at the DDL scale so `100.5` and `100.50` cannot yield two
  identities; `direction` is the enum name; `occurredOn` is the `DATE`, never an ingestion timestamp;
  fields are joined with `|`, which `normalize` cannot emit. `OCC:` is separated by the same `|`.
- **Implementation shape** — a counter keyed by base fingerprint, incremented as the file is walked:

  ```java
  int occ = counts.merge(baseFingerprint, 1, Integer::sum);   // 1, then 2, then 3 …
  ```

  `Map.merge` / `computeIfAbsent` / `getOrDefault` are taught together in **one** block,
  `day08-blk-27` (`content/lessons/day-08.json:211`), and `HashMap` has 56 corpus hits — so the
  mechanism is inside the taught window even though the *concept* has no citation.
- **The parse loop must be sequential and in source-file order.** `occurrenceIndex` is
  order-derived, so `parallelStream()` / `.parallel()` anywhere on the import path makes identity
  nondeterministic. This is now a clause of blueprint rule **R22**, and it is a *deliberate*
  exception to a taught idiom: `parallelStream` has **12** corpus hits (day-12 ×8, day-10 ×4).
  Sequential `Files.lines` consumption (25 hits) is what the task requires.

| Requirement from the directive | How this meets it |
|---|---|
| a stable source-provided id is used when present | Level 1, scoped by `sourceKey` + `accountId` (+ `user_id` in the constraint) |
| must **not** depend solely on a generated `ImportBatch` PK | the PK is not an input at either level |
| must support **retry of a partially imported file** | successful rows recompute the same key and skip; failed rows wrote nothing and insert |
| already-successful rows recognised as duplicates | the `UNIQUE` constraint, or the pre-check in front of it |
| previously failed rows may be retried | nothing was committed for them, so nothing collides |
| **two identical legitimate rows must become two identities** | `OCC:1` and `OCC:2` — the defect this pass fixes |
| re-import of the same statement in the same logical order reproduces the same identities | the counter is a deterministic function of (content, position among equals) |
| duplicates create no second transaction | the row is recorded `DUPLICATE` on `ImportRow`; nothing is inserted |
| rule application still goes through the canonical path | unchanged — `TransactionCreationService.create(...)` (blueprint D10/R20); import never writes a transaction directly |
| `ImportBatch` remains import history/reporting only | unchanged — batch/row records are provenance and display, never identity |
| per-row atomicity remains | unchanged — one row, one `@Transactional` call |
| `UNIQUE` remains the final race-safe guard | unchanged — two concurrent uploads both pass the pre-check, one loses at the constraint. The constraint tolerates rows differing only by `OCC:`, because those are different strings |
| no Spring Batch / `ON CONFLICT` / `SKIP LOCKED` / `Idempotency-Key` / mandatory hashing / Kafka | none used; both forms are string concatenation plus one `HashMap` counter, all of it reachable by V0.2 knowledge |

**The limitation, stated rather than hidden.** The fallback guarantees stable identity for
**re-importing the same logical statement ordering**. It does not guarantee it under arbitrary
reordering: if a source without a stable reference is re-exported with its rows shuffled, filtered or
reconstructed, occurrence indices among a group of identical rows may be assigned differently, and an
identity may change — surfacing as an apparent duplicate or an apparent new row in the import report,
not as silent corruption. A source-supplied reference (Level 1) removes the limitation entirely, which
is why it is the preferred tier. **This is not universal bank-file deduplication and must never be
described as such.**

**Corpus limits this model runs into — measured 2026-09-05, recorded as gaps, not resolved here:**

| Measured | Consequence for the V0.8 tasks |
|---|---|
| `sourceRef` / `source_ref` — **0 hits in all of `content/`** | wholly a Spendwise invention; the task teaches it from scratch in its own `constraints` |
| `OCC:`, `occurrenceIndex`, `occurrence` — **all 0-hit in `content/`** (measured 2026-09-05) | the occurrence counter is equally invented. What *is* taught is the mechanism it needs — `Map.merge` / `computeIfAbsent` / `getOrDefault`, together in `day08-blk-27` (`content/lessons/day-08.json:211`), with `HashMap` at 56 hits — so the technique is reachable even though the concept is uncited |
| `referenceId`, `externalId` — **both 0-hit in `content/`** (measured 2026-09-05) | Level 1's field name is a Spendwise invention too; the task must name and define it, and must state how a row is judged to *have* a stable source reference |
| `parallelStream` — **12 hits** (day-12 ×8, day-10 ×4); `Files.lines` — 25 | the import path must **forbid** an idiom the course teaches, on identity grounds (R22 second clause). The task's `constraints` must say so explicitly, or a learner following day-12 will break idempotency |
| composite `UNIQUE (a, b)`, `CONSTRAINT … UNIQUE`, `uniqueConstraints` — **all 0-hit** | the only `UNIQUE` taught is single-column inline (`email VARCHAR(255) NOT NULL UNIQUE`, `day21-blk-10`'s `V1__init.sql`). `task-user-migration` / the V0.8 duplicate task must spell the two-column DDL out in full |
| `DataIntegrityViolationException` — **0-hit corpus-wide** | this section previously named it as the caught type. The task must introduce it explicitly (or catch a taught supertype); it cannot be cited as taught |
| `existsBy…` — only `existsByEmail`, only at **day-33** | the pre-check lands *after* day-26's import lesson, so it is **optional politeness**. The constraint is the guard |
| `MessageDigest.getInstance("SHA-256")` is taught (day-24, required) but `Base64`, `HexFormat` and any `bytesToHex` are **0-hit** | **neither identity is hashed.** There is no taught way to render a digest as a string, so plain concatenation is the only fully-taught option — which the directive also mandates (no mandatory hashing) |
| day-26's `MultipartFile` exposes only `getOriginalFilename()`, `getInputStream()`, `isEmpty()` — no `getSize()`, `getBytes()`, `transferTo` | a **whole-file** identity is not implementable with what is taught. Row-level identity is not just preferable, it is the only reachable one |

**Retry and re-import acceptance criteria** — these are the observable statements the V0.8 task
contracts must carry (added 2026-09-05 by the final import-identity correction):

1. Importing a statement whose rows all carry a stable source reference, twice, adds N transactions
   then **0**, and reports N `DUPLICATE` rows on the second run.
2. Importing a statement with **no** source reference that contains **two byte-identical data rows**
   adds **2** transactions (`OCC:1`, `OCC:2`), not 1.
3. Re-importing that same statement in the same order adds **0** and reports **2** `DUPLICATE` rows.
4. Re-uploading a statement in which some rows previously **failed**: the previously-successful rows
   report `DUPLICATE` and insert nothing; the previously-failed rows insert cleanly, because a failed
   row committed nothing.
5. A `DUPLICATE` row creates no transaction, applies no rule, and touches no balance projection.
6. Every created row went through `TransactionCreationService.create(...)` — import never inserts a
   transaction directly (blueprint D10/R20).
7. **Not claimed:** that a reordered, filtered or reconstructed export of the same underlying
   transactions is idempotent when the source supplies no stable reference. See the limitation above.

**Not implemented in this pass.** §13.1 is a planning decision; the V0.8 task contracts that carry it
are authored in P2.

The V0.8 acceptance criterion in `content/spendwise-project.json` already reads *"Large datasets can
be imported as a background job (optional, 202 Accepted + ImportBatch status)"* — the words
`202 Accepted` must be struck from it, and `optional` is already correct, so this is a **one-phrase
edit, not a criterion rewrite** (correcting the draft, which planned a full rewrite here).

---

## 14. Mentor Prompt Contract

The Copy Coding Mentor Prompt button already exists in principle (`tools/ui_smoke_test.py:345`
pins the clipboard label *"Sao chép mã mẫu vào clipboard"*). What is new is the **contract** — the
required fields of the generated prompt. Every field below is mandatory; a generated prompt missing
any of them is a bug.

1. **Role** — a mentor for a learner following a fixed 40-lesson curriculum, not a free-form
   architect.
2. **Current task** — id, title, release, and the task's own acceptance criteria verbatim.
3. **Steps** — the task's `buildSteps` in order, each with `doneWhen` and `verifyCommand`.
4. **Knowledge boundary** — the lesson ids taught **so far**, and the explicit instruction: *do not
   use techniques from later lessons*. This is the field that prevents a mentor from "helpfully"
   introducing `@Embeddable`, MapStruct or an event bus.
5. **Architecture rules in force** — the Constitution rule ids attached to these steps, quoted.
6. **Toolchain** — Java 17, Maven wrapper, the pinned Spring Boot minor, PostgreSQL, root package
   `com.spendwise`.
7. **Repository truth clause** — *read the learner's repository; the website checklist is
   self-reported and may be wrong in either direction* (§10).
8. **Convention clause** — verbatim: **"Prefer the established Spendwise convention over your own
   preference, even where your preference is defensible."**
9. **Stop clause** — verbatim shape, from blueprint §10:

   > If completing this task requires deviating from the architecture above, do not deviate. Stop and
   > output:
   > ```
   > ARCHITECTURE_CHANGE_REQUIRED
   > Rule: <rule id or ADR>
   > Why it blocks: <one sentence>
   > Proposed change: <one sentence>
   > Cheapest alternative that keeps the rule: <one sentence>
   > ```

10. **Non-goals** — the mentor does not refactor unrelated code, does not add dependencies, does not
    change the build, does not introduce a new package.

**The mentor is not permitted to optimize the architecture according to its own preferences.** That is
the single sentence this contract exists to enforce. A capable model handed "build a Spring Boot
expense tracker" will reach for hexagonal layering, MapStruct, an outbox table and a Redis cache —
all of which are 0-hit in this curriculum and all of which would make the learner's code unteachable
against the lessons they are actually reading.

---

## 15. Self-study roadmap for Day 39–64

The capstone window (`day-31` → `day-36`) and the OJT/evaluation frames are **untouched**. Not one
build task, step, criterion or lesson entry is added inside them. Verified: `content/lessons/ojt-evaluation.json`
holds `day-39-64` (kind `ojt`, *"khung tổ chức nội bộ"*) and `day-65-66` (kind `evaluation`,
*"khung đánh giá nội bộ, không đặt ra thang điểm chính thức"*), and self-test #37 at
`index.template.html:4807-4810` asserts `day-39-64` renders **no** project composition. That assertion
stays true.

`SPENDWISE_SELF_STUDY_ROADMAP` is therefore a **separate document-level construct**, surfaced in the
site as prose attached to V0.7–V1.0, worded as a recommendation:

> V0.7 through V1.0 are **not part of the 40-lesson course**. They are a suggested continuation. The
> Day 39–64 OJT window is the **primary suggested execution window** because it is the only stretch of
> time in the programme with no new lessons competing for it — but it is **recommended, not required**,
> and the OJT frame itself remains internal and ungraded.

| Release | Suggested window | Why |
|---|---|---|
| V0.7 | Day 39–46 | needs day-25/27 scheduling + day-27's after-commit rule; nothing later |
| V0.8 | Day 47–52 | CSV import/export needs only core Java IO + JPA |
| V0.9 | Day 53–60 | testing depth (day-28/29/30) and the optional Redis swap |
| V1.0 | Day 61–64 | packaging/deployment from day-35 |

Three things this deliberately does **not** do: it does not renumber lessons; it does not add
`day-39-64` build tasks (the four `future`→`direct` conversions all point at *taught* lessons); it does
not make any V0.7+ task a graduation condition. A learner who stops at V0.6 has completed the course.

---

## 16. Validator diff

All additions preserve the closed-schema, fail-before-embed property (`tools/validate_project.py` runs
ahead of `tools/build_site.py`'s embedding, so an invalid artifact fails the build rather than
shipping).

| Change | Location | Kind |
|---|---|---|
| `BUILD_STEP_KEYS` + `_validate_build_steps` | new, near `BUILD_TASK_KEYS` `:88` | addition, §11 |
| call `_validate_build_steps` from the top-level validate | the existing validate sequence | addition |
| **capstone-window guard: `day-31` … `day-36` may not carry a non-empty `buildTaskIds`** | inside `_validate_lesson_map` (`:387` onward) | **addition, new 2026-09-05** (final import-identity correction). Closes the pre-P0 gate's finding that R-DAY33 had **0** validator rules and **0** tests behind it. Passes at zero cost against `e97c13a`: all six entries are `theory` with keys exactly `{applicationType, context}` and no `buildTaskIds` key. Lands in **P0**, before P1 fills `lessonMap["day-33"]`. Changes no count and no UI |
| `outOfScope` | `:161` `CANONICAL_OUT_OF_SCOPE` | **no change** — measured: the 21-item list already ends *"full multi-currency accounting engine"* and already carries the scope exclusions the draft wanted to add. The draft was wrong that an edit was needed |
| release id/version position pins | `:176`, `:191-198` | **no change** — the 10-release spine is frozen |
| `_validate_release_task_links` "exactly once in owner's ordering" | `:320-326` | **no change**; the **64** new-and-kept tasks must satisfy it as-is (*count corrected 2026-09-05 from 58*) |
| `_validate_lesson_map` `direct` with empty `buildTaskIds` | `:415` (`_require_str_list` **without** `nonempty_list`) | **no change** — this is what legally permits day-08 and day-21 to become `direct` without owning a task, and it is load-bearing for §2 |
| optional `alsoUsedIn` lessonMap key | `_validate_lesson_map` `:387` | addition; permits a lesson to reference a task owned by another lesson |
| `feat-*` keys | `FEATURE_KEYS` `:87` | **no change to the key set.** The six new features are new *objects*, not new keys — which is why the draft's proposed `Release` and `Class` columns are dropped |

---

## 17. Test diff — four breakages, one crash, one non-breakage, one new assertion

**Corrected by the pre-P0 sanity gate, 2026-09-05.** This section previously listed five breakages.
Row 3 is struck: it is not a breakage.

**Extended 2026-09-05 by the final import-identity correction.** Row **7** is new and is **not** a
breakage either — it is an added self-test (the capstone-window guard). The breakage count is
unchanged at four.

| # | File:line | Current | New | Failure mode if missed |
|---|---|---|---|---|
| 1 | `tests/test_build_site.py:80` | `len(...features) == 25` | `== 27` at the end of P1, `== 31` at the end of P2 | clean assertion failure. *P1/P2 split stated explicitly, 2026-09-05: P1 adds `feat-project-foundation` + `feat-schema-migration`, P2 adds the other four* |
| 2 | `tests/test_build_site.py:81` | `len(...buildTasks) == 24` | `== 33` at the end of P1, `== 64` at the end of P2 | clean assertion failure. *Corrected 2026-09-05: the final value read `58`, which was an addition error in the blueprint's total row; and the two-step P1/P2 values are now stated explicitly, because §18 already said this assertion changes twice* |
| ~~3~~ | ~~`tests/test_validate_project.py:174`~~ | `len(project["lessonMap"]) == 38` | **NO CHANGE — row struck** | **none.** Corrected by the pre-P0 sanity gate, 2026-09-05: `day-33` already exists, so the entry count stays 38. Editing this to `39` would break a test that passes today |
| 4 | `index.template.html:4792` | day-20 `toggle-build-task` count `=== 3` | `=== 5` | in-page self-test #37 fails |
| 5 | `index.template.html:5120-5122` | self-test #53 `emptyRelease.id` | rewritten per §12 | **whole-harness crash** via the `catch` at `:5209`, reported as one opaque message |
| 6 | `tests/site_core.test.js:161` | `core.STATE_VERSION === 2` | `=== 3` | clean failure, but **must ship in the same commit as `:1714`** (§7) |
| 7 | **new self-test, `index.template.html`** (near the day-20 count at `:4792`) | none exists | `#/lesson/day-33` renders **0** `[data-action="toggle-build-task"]` elements | *added 2026-09-05 (final import-identity correction).* **Not a breakage** — a new assertion. It passes at `e97c13a` and its value is as a **P1 regression guard**: nothing today stops a later author filling `lessonMap["day-33"].buildTaskIds`. Lands in **P0** with the validator counterpart (§16). No UI change |

Two counts that do **not** change and must not be "helpfully" updated:
`tests/test_build_site.py:53`'s `{"java": 12, "spring": 24, "completion": 4}` (unit structure is
untouched) and `tests/test_build_site.py:73-75`'s never-embedded assertions.

**Ordering constraint:** `python tools/build_site.py` must run **before** `node --test`, because
`tests/site_core.test.js` reads the generated `index.html`. A test-first habit inverts this and
produces failures against a stale build.

---

## 18. Implementation waves P0–P4

Every wave ends with the repository **valid, buildable and testable**. That is a hard boundary
condition, not an aspiration: no wave may leave the artifact failing `validate_project.py`, and no wave
may leave `index.html` out of sync with `index.template.html`. Because `index.html` is generated and
never hand-edited, **every wave that touches the template or the artifact re-runs
`python tools/build_site.py` and commits the regenerated `index.html` in the same commit.**

### The six-step validation gate — run at the end of every wave, in this order

```
1. PYTHONIOENCODING=utf-8 python tools/validate_lessons.py \
     --catalog course-catalog.json \
     --manifest content/source-manifest.json \
     --source-notes-dir content/source-notes \
     --lessons-dir content/lessons
2. PYTHONIOENCODING=utf-8 python tools/validate_project.py
3. PYTHONIOENCODING=utf-8 python tools/build_site.py      # regenerates index.html
4. PYTHONIOENCODING=utf-8 python -m pytest tests -q
5. node --test tests/site_core.test.js                     # reads the built index.html
6. PYTHONIOENCODING=utf-8 python tools/ui_smoke_test.py
```

**Corrected by the pre-P0 sanity gate, 2026-09-05 — two of these six steps were unrunnable as
previously written, and both were verified by running them:**

- **Step 1** was `python tools/validate_lessons.py` with no arguments. That exits **2**:
  *"error: the following arguments are required: --catalog, --manifest, --source-notes-dir,
  --lessons-dir"*. With the four arguments above it exits 0 and prints
  `PASS lessons=40 sections=212 practices=156 citations=425 assignments=20`.
- **Step 5** was `node --test tests/`. That exits **1** with
  `Cannot find module 'D:\java_spring\tests'` — Node treats the bare directory as a module
  specifier here. `node --test tests/site_core.test.js` runs and reports **25/25 pass**.

Expected output of a green gate, recorded so a drift is visible: step 2
`PASS releases=10 features=25 buildTasks=24 lessonMap=38`; step 3
`PASS output=index.html units=15 lessons=40 practices=156 citations=1054 resources=118 external_dependencies=0`;
step 4 `206 passed, 6 subtests passed`; step 5 `25/25`; step 6
`PASS desktop selftest=61/61` + `PASS mobile selftest=61/61` + `PASS static accessibility + hygiene checks`.
Those are the numbers at baseline `e97c13a`; the counts in steps 2 and 4 change as the artifact grows.

**`index.html` is never byte-identical across two builds.** `tools/build_site.py:414` embeds
`built_at=datetime.datetime.now(datetime.timezone.utc).isoformat()` into the page as `"builtAt"`
(`:362`), so step 3 always dirties `index.html` even when nothing else changed — verified: md5
`8c46a9c9…` → `c8d1e6c9…` on a no-op rebuild, and both hash to `fb286fa27…` once the `builtAt` line is
normalized away. `tests/test_build_site.py:36` avoids this by passing a fixed
`built_at="2026-08-23T00:00:00Z"`, and no test asserts an `index.html` hash. Consequence for P0's exit
criterion: see P0 below.

Steps 3-before-5 is mandatory (§17). `PYTHONIOENCODING=utf-8` is mandatory on Windows: the corpus is
Vietnamese and cp1252 stdout raises `UnicodeEncodeError` on section titles.

### P0 — Schema and site plumbing, artifact unchanged in content

**Scope narrowed by the final planning reconciliation, 2026-09-05.** P0 is **strict plumbing**. The
governing principle is `docs/build-while-you-learn-plan.md` §25 — *"Data first. UI second."* — and the
previous P0 list violated it by adding a learner-facing route and view. Those moved to P3 (§12).

**Allowed in P0 — and nothing else:**

- add `BUILD_STEP_KEYS` + `_validate_build_steps` (§11) — tolerant of an **absent** `buildSteps`
- add the optional `alsoUsedIn` key (§16)
- `STATE_VERSION` 2→3, `legacyCompleted`, `migrateProjectProgress`, `RENAME_MAP` (empty for now),
  export `migrateProjectProgress` on `CourseCore`, update `tests/site_core.test.js:161`
- compatibility tests for the migration and the new validator branch
- rewrite self-test #53 (§12) **now**, before it can crash — this is a *prerequisite fix* for data that
  P2 will write, and is the one self-test P0 touches
- **add the capstone-window regression guard** (added 2026-09-05 by the final import-identity
  correction; blueprint §7.1 **R-CAPSTONE-GUARD**): **Day 31–36 must not expose a required Spendwise
  build-task CTA.** This is a **TEST / SELF-TEST addition only — it changes no UI**, and it is in P0
  precisely because it must be in place *before* P1 modifies `lessonMap["day-33"]`. Two mechanical
  forms, either or both:
  - a **validator rule** — for each of `day-31` … `day-36`, the `lessonMap` entry must not carry a
    non-empty `buildTaskIds`. It passes today at zero cost: measured against `e97c13a`, all six
    entries are `applicationType: theory` with exactly the keys `{applicationType, context}` and **no
    `buildTaskIds` key at all**;
  - a **self-test** asserting that `#/lesson/day-33` renders **zero** `[data-action="toggle-build-task"]`
    elements — the same shape as the existing day-20 count assertion at `index.template.html:4792`.

  Why it belongs here: the pre-P0 sanity gate found R-DAY33 was *"an authoring convention with no
  mechanical guard"* — **0** validator rules and **0** tests enforced *"KNOWLEDGE UNLOCK ≠ PROJECT
  EXECUTION"*. P1 fills `lessonMap["day-33"]` with a `direct v0-6` entry whose `buildTaskIds` must stay
  empty; nothing today would catch a later author filling it in. It **changes no count** — not tasks,
  not features, not lessonMap entries — and it is not a UI change.
- **no learner-facing Project Mode redesign, no new route, no new render function**

**Explicitly moved OUT of P0 → P3:**

| Item | Why it is not plumbing |
|---|---|
| `#/task/:taskId` route (`index.template.html:1539-1552`) | new learner-visible navigation |
| task detail view rendering `buildSteps` | learner-facing rendering of data that does not exist until P1/P2 |
| any substantial Project Mode rendering change | same |
| learner-facing per-step UI | same; per-step ticks stay display-only whenever they land |

- **Exit:** all six gate steps pass; **the artifact's parsed content is unchanged** — `releases`,
  `features`, `buildTasks`, `milestones`, `architectureStages` and `lessonMap` all compare equal to
  their `e97c13a` values, and `validate_project.py` still reports
  `releases=10 features=25 buildTasks=24 lessonMap=38`; **and no route is added and no learner-visible
  rendering changes** — a learner navigating the site after P0 sees byte-for-byte the same pages, the
  same lesson views and the same release views as at `e97c13a`, with only persisted-state *shape*
  differing. **Not** "byte-identical" as a file claim: the previous wording was *"artifact content
  byte-identical except formatting"*, which is unachievable for `index.html` because `builtAt` changes
  every build (§18). Compare parsed JSON, not bytes.

Rationale for doing the state migration in P0 with an empty rename map: the migration code lands and
is tested while it is a no-op, so P1's incompatible ids meet already-working machinery.

### P1 — V0.1–V0.6 task rewrite (the taught window)

- `task-project-foundation` (§8)
- rename `task-category-enum` → `task-category-model`, fill `RENAME_MAP`
- retire `task-rest-controllers` → 3 endpoint tasks; retire `task-jwt-auth` → 4 + 1 optional (§6)
- re-specify the six changed-semantics tasks (§5)
- add `feat-project-foundation`, `feat-schema-migration`
- **modify** the existing `day-33` lessonMap entry: `theory` → `direct v0-6`, fill `releaseId`,
  `featureIds`, `projectProblem`, `application`, keep `context`, and leave `buildTaskIds` **empty**
  (§6, blueprint §7.1 R-DAY33). This does **not** change the entry count — it is already 38
- convert day-07, day-08 (→v0-2), day-21 (→v0-5)
- write `buildSteps` for every V0.1–V0.6 task
- update `tests/test_build_site.py:80-81` **to the P1 numbers**, then again in P2 — those two counts
  are asserted exactly, so they change twice. **Do not touch `tests/test_validate_project.py:174`** —
  it asserts `lessonMap == 38` and 38 is still correct (§17 row 3, struck)
- fix `index.template.html:4792` 3→5 (self-test #37; this is the wave that grows V0.5 to 7 tasks)
- **Exit:** gate passes; a learner's V0.6 completion state either survives (case A) or is preserved as
  history (case B); no successor task is auto-completed. **P1 adds V0.1–V0.6 tasks: 6 + 5 + 3 + 6 + 7 +
  6 = 33 tasks, 30 required, 3 optional** (V0.3 `task-config-profiles`, V0.5 `task-optimistic-locking`,
  V0.6 `task-auth-hardening-review`) — so `tests/test_build_site.py:81` reads **33** at the end of P1
  and `:80` reads **27** features (25 + `feat-project-foundation` + `feat-schema-migration`).

### P2 — V0.7–V1.0 authoring (the self-study window)

- **31 new tasks** across V0.7/V0.8/V0.9/V1.0 per §2's per-release contracts — 8 + 8 + 9 + 6 = 31,
  of which 26 required and 5 optional
- `feat-dashboard`, `feat-csv-export`, `feat-testing`, `feat-deployment`
- day-25's three tasks (§4); day-11/day-12 → `direct v0-8`; day-27 → `direct v0-7`;
  day-28 → `direct v0-9`
- strike `202 Accepted` from the V0.8 criterion (§13) — the **only** acceptance-criteria edit in the
  whole plan
- correct `lessonMap["day-12"].application`'s `summingDouble` endorsement (§5)
- `SPENDWISE_SELF_STUDY_ROADMAP` prose (§15)
- `buildSteps` for all V0.7–V1.0 tasks
- **Exit:** gate passes; counts reach **64** / 31 / **38** (*corrected 2026-09-05 from 58 — see §2*; the
  lessonMap count does not move). Arithmetic check across the two waves: **33 (P1) + 31 (P2) = 64**,
  required **30 + 26 = 56**, optional **3 + 5 = 8**. **Every release has ≥1 task**, which is precisely
  why #53 had to be rewritten in P0.

### P3 — Task UI and the mentor prompt contract

**Renamed and widened by the final planning reconciliation, 2026-09-05.** P3 was *"Mentor prompt
contract"* only. It now also owns the two items moved out of P0, because all three read the same task
fields and all three are learner-facing:

- the `#/task/:taskId` route (`index.template.html:1539-1552` `parseRoute`) — *moved from P0*
- the task detail view rendering `buildSteps` (new render function near `createProjectProgress`,
  `:1953-1974`); per-step ticks are **display only**, never new persisted state — *moved from P0*
- generate the prompt from the artifact per §14's ten fields
- keep the clipboard label `"Sao chép mã mẫu vào clipboard"` intact (`tools/ui_smoke_test.py:345`)
- **Exit:** gate passes; a copied prompt for an arbitrary task contains all ten fields, verifiably;
  the route resolves for every task id in the artifact and the detail view renders that task's
  `buildSteps` — which by P3 **exist**, because P1 and P2 wrote them. This ordering is the point of the
  move: the UI is built against real data, not against an empty array.

### P4 — Documentation and defense

- the 15-row defense matrix (§19)
- the architecture Constitution surfaced as reader-facing prose
- **Exit:** gate passes.

**What no wave does:** touch lesson content (`content/lessons/*` is frozen at `e97c13a`), hand-edit
`index.html`, or add a build file to this repository (Spendwise is the *learner's* repo; this repo
ships the course).

---

## 19. Defense matrix

**Count discrepancy, flagged rather than silently resolved:** `docs/build-while-you-learn-plan.md` §45
specifies **13** defense questions; `docs/SPENDWISE_ARCHITECTURE_RESEARCH.md` PART 15 gives **15**; the
draft's matrix had 15 rows. This plan uses **15** — the master plan outranks the research
(authority order 2 over 5), but 15 is a superset of 13 and adding two questions does not violate a
"13 questions" requirement the way dropping two would violate a 15-question one. **A reviewer should
confirm this reading**; if §45's 13 is exact rather than minimum, rows 14–15 move to an appendix.

| # | Question | Answer anchored in |
|---|---|---|
| 1 | Why `BigDecimal` and not `double`? | R1; `content/lessons/day-10.json`'s 3 `summingDouble` hits are the counter-example the learner must be able to explain (§5) |
| 2 | Why scale 2 everywhere? | the **Spendwise V1.0 precision convention**, ADR-002 — not a claim about world currencies |
| 3 | Why `compareTo` and never `equals`? | R2; `BigDecimal("1.0").equals(BigDecimal("1.00"))` is false |
| 4 | Why is `amount` always positive? | R7; direction is typed, sign is derived (§ signed-effect model) |
| 5 | Why no `Transfer` aggregate? | ADR-013; one `@Transactional` + a shared `transferRef` is expressible with day-19 knowledge; an aggregate is not |
| 6 | Why a stored balance **and** a recomputable one? | R8; `balance = openingBalance + Σ signedEffect` is the invariant, the projection is the cache, reconciliation (§4) proves they agree |
| 7 | Why `Instant` for timestamps and `LocalDate` for business dates? | ADR-004; justified by **Spring Boot 3.x + Hibernate 6** behaviour, not by a JPA 3.1 portability claim |
| 8 | Why `VARCHAR(7)` for a period and not two ints? | ADR-005; `YearMonth`-shaped, sorts lexicographically, one column to index |
| 9 | Why is `sourceRef` unique per user? | R20; it is the idempotency key for recurring generation *and* import (§13) |
| 10 | Why one canonical creation path? | R20; every write goes through `TransactionCreationService.create(CreateTransactionCommand)` so invariants cannot be bypassed. **Production code only** — tests may seed fixtures, except when the thing under test *is* creation |
| 11 | Why may domain classes carry JPA annotations? | D2/D20 as resolved: **business-centric JPA entities**. Domain may import `jakarta.persistence`; it may **not** import Spring MVC, Spring Security, service types, repository implementations or infrastructure clients. The framework-purity claim is withdrawn |
| 12 | Why hand-write repositories before `JpaRepository`? | ADR-008; the interface is stable, the implementation is swapped at V0.5, which is the lesson |
| 13 | Why is token *issuance* after the capstone? | §6; day-24 teaches the flow and owns a `TokenIssuer` seam, day-33 teaches `NimbusJwtEncoder`. No unsafe temporary signer is written in between |
| 14 | Why is refresh-token rotation optional? | `content/lessons/day-24.json:246` puts rotation in the *"CHƯA CHỐT, KHÔNG dùng làm điều kiện chấm"* group and logout revocation in the required group |
| 15 | Why is there no coverage percentage? | §9; `70%`/`90%` are 0-hit in `content/`, and `content/lessons/day-30.json:253` disowns its own 75% |

---

## Known gaps

1. **The 64 / 56 / 8 / 31 / ≈229 numbers are derived, not measured.** They come from the blueprint's
   Evolution Contract and this plan's per-release contracts. Nothing in the repository asserts them
   yet; the first thing P1 does is make two test assertions agree with them (and again in P2).
   **These numbers read 58 / 50 / 8 / 31 / ≈205 until 2026-09-05**, when the final planning
   reconciliation found the blueprint's total row did not match its own per-release rows. Re-derived
   from the id lists in §2 and cross-checked two ways: per-release column sum = 64, and 22 surviving
   baseline slots + 42 new ids = 64.
2. **Spring Boot is not pinned at all — `SPRING_BOOT_EXACT_PIN_PENDING`.**
   `content/lessons/day-28.json:145` (`@MockitoBean`) and
   `content/lessons/day-29.json:120` (structured logging) require ≥3.4; nothing requires exactly
   3.4.x, and **no build file exists in this repository** to enforce it — `pom.xml`, `mvnw`,
   `gradlew`, `build.gradle`, `.mvn/`, `Dockerfile`, `compose.yml` are **0 files** in the working
   tree, and `git log --all --diff-filter=A` confirms **none ever existed** in this repository's
   history. The freeze is documentary. Escalated by the pre-P0 sanity gate, 2026-09-05: the **line**
   itself is open too, because the only version-pinned Spring documentation anywhere in the corpus is
   Spring Security **`6.5`/`6.5.x`** (13 resources, 69 `sourceRef` occurrences in day-22, day-33,
   day-35), and Spring Boot 3.4.13 manages Spring Security 6.4.13 while 3.5.16 manages 6.5.11
   (verified from the published `spring-boot-dependencies` POMs on Maven Central).

   **Amended the same day after adversarial verification.** The sharp form of that argument — "3.4.x
   is wrong because day-33 needs 6.5" — is **refuted**: day-33's `NimbusJwtEncoder` block and its
   `SecurityConfig` both compile clean *and* deprecation-clean on 6.4.13, all 26
   `org.springframework.security.*` types used in `content/` resolve there, the repo's own JWT probe
   produces byte-identical output on 6.4.13, and every 6.5-only API is 0-hit in `content/`
   (`setJwkSelector`, `PathPatternRequestMatcher`, `oneTimeTokenLogin`, `AuthorizationManagerFactory`,
   `NimbusJwtEncoder.withSecretKey`, WebAuthn/passkey). What survives is a **citation mismatch with no
   API consequence** — too weak to decide a toolchain.

   **The constraint that replaces it is harder.** Per `api.spring.io/projects/spring-boot/generations`,
   **3.4.x OSS support ended 2025-12-31 and 3.5.x ended 2026-06-30** — both candidate lines are out of
   OSS support as of 2026-09-05 (current: 4.0.x to 2026-12-31, 4.1.x to 2027-07-31, latest `v4.1.1`).
   So the decision is no longer 3.4-vs-3.5; it is **pin an expired line that matches the corpus's
   Security 6.5 citations, or move to 4.x and accept that Security 7.0 falsifies day-33's own comment**
   (7.0 adds the static builders that comment says do not exist yet). No free option — which is why
   this stays pending rather than being answered here.

   Also: `spring-security-oauth2-jose` declares `nimbus-jose-jwt:9.37.4` at compile scope identically
   in 6.4.13 and 6.5.11, while the corpus cites the **9.37.3** javadoc in five places
   (`content/source-manifest.json:4135,4154`, `content/source-notes/project-final.json:860,867`,
   `content/supplemental-sources.json:131`) — a citation drift to fix, not an unpinned coordinate.
   Full evidence: `docs/report/2026-09-05-spendwise-pre-p0-sanity-gate.md` §3 and blueprint **§8.1**.
   **Corrected by the final planning reconciliation, 2026-09-05:** this paragraph previously ended
   *"Unchanged: **HARD prerequisite of `task-project-foundation`**"*. That was wrong, and this plan's own
   §8 already contradicted it — V0.1 has no Spring dependency (*"No dependency on Spring, database, or
   REST"*) and the parent POM arrives at V0.3. The blocker is a **HARD prerequisite of
   `task-spring-bootstrap` (V0.3)**, must be resolved before the learner executes the first V0.3 Spring
   task, and is **NOT a blocker for P0, for V0.1 or for V0.2**. Once chosen, any change — patch, minor or
   major — requires an explicit toolchain/architecture decision under blueprint §10, never an
   opportunistic upgrade.
3. **Root package `com.spendwise` is 0-hit in `content/`.** No snippet in the corpus declares a package
   at all. This is a Spendwise-side decision with no curriculum support — defensible, but not evidenced.
   **Related, measured 2026-09-05:** **Maven is 0-hit in day-01 – day-11 and day-13/day-14** — the only
   early `pom.xml` is a JMH snippet in day-12 and `mvnw` first appears at day-35. `task-project-foundation`
   therefore requires a build tool no lesson in its window teaches; it must carry its own Maven commands
   in `constraints`. Labelled, not hidden (blueprint §11 gap 12).
4. **The defense-question count is 13 vs 15** (§19). Unresolved by design; flagged for the reviewer.
5. **`estimatedMinutes` is guessed.** No lesson carries a duration, so every step estimate is
   judgement. If it is going to mislead a learner, drop the field — it is optional in the schema for
   exactly this reason.
6. **Per-step ticking is display-only in P2.** The 14-key step contract supports per-step state, but
   `projectProgress` gains no `steps` array in this plan. Adding one later is a second
   `STATE_VERSION` bump.
7. **The GPA/scoring formula remains unspecified** — carried forward from the content-rewrite
   checkpoint. `day-65-66` explicitly declines to set an official scale, so nothing here can supply
   one.
8. **Nothing in this plan has been implemented or tested.** The test breakages in §17 are
   predicted from reading the assertions, not observed by running them; #5's crash mode in particular
   is inferred from the `catch` at `index.template.html:5209`. **Exception, added 2026-09-05:** the
   §18 gate commands *were* run, which is how two of them were found to be unrunnable as written and
   how row 3 of §17 was found to be a non-breakage.
9. **`task-canonical-token-issuer` has no lessonMap back-reference** (§6, blueprint §7.1 R-DAY33).
   Its `buildTaskIds` slot in `lessonMap["day-33"]` is deliberately empty so no build-now CTA renders
   inside the capstone window. Day-33 is still reachable from the task via
   `relevantLessonIds = ["day-24", "day-33"]`, rendered as a *"Relevant Lessons"* link list
   (`index.template.html:2088`) — but **not** the reverse: a learner reading day-33 gets no in-page
   link to the task and reaches it from the V0.6 release view. That asymmetry is the intended
   trade-off, not an oversight.

   **Amended 2026-09-05 (adversarial verification, pre-P0 sanity gate):** this was written as though
   `direct` + `[]` were the only shape that suppresses the CTA. It is not. **`future` + `[]`
   suppresses it too, and already ships on three lessons — day-05, day-11, day-12.** So the choice of
   `direct` for day-33 is a *preference*, not a forced move, and a reviewer is entitled to challenge
   it. The preference stands because `future` renders the fixed disclaimer *"Áp dụng ở release sau"*
   (`index.template.html:2876-2882`, unconditional whenever the type is `future`), which would falsely
   assert that day-33's knowledge lands in a **later release** — `task-canonical-token-issuer` belongs
   to **V0.6**, a release the learner has already passed by day 33; only its *execution* is scheduled
   after day 36. Two further facts that were missing here: the empty **list** is what is legal, the
   **key** is mandatory (`_require_str_list` rejects an absent key at `validate_project.py:134-135`
   before the `nonempty_list` branch at `:137` is reached), and `applicationType: theory` is **not** a
   safety mechanism — a `theory` entry that carries an `application` key renders the full required CTA
   and validates clean, because the guard at `index.template.html:2895` tests the *field*, not the
   type. Nothing about CTA suppression is type-enforced; it is entirely data-contingent. See §6's
   three authoring constraints, which are mandatory for this reason.

   **Amended again 2026-09-05 (final import-identity correction):** the "enforced by nothing" property
   is now **closed in plan**, not just noted. P0 gains the capstone-window guard — a validator rule
   (`day-31` … `day-36` may not carry a non-empty `buildTaskIds`) and/or a self-test asserting
   `#/lesson/day-33` renders **zero** `[data-action="toggle-build-task"]` elements. See §16, §17 row 7
   and §18 P0. It is **test/validator only and changes no UI**, and it passes at zero cost today,
   which is precisely why its value is as a **P1 regression guard** rather than as evidence of anything
   now.
10. **The fallback import identity is order-sensitive, and this is not universal bank-file dedup**
    (new 2026-09-05, final import-identity correction). `IMPORT:<baseFingerprint>|OCC:<n>` (§13.1)
    reproduces the same identities when the **same logical statement ordering** is re-imported. Under
    arbitrary reordering, filtering or reconstruction of a source that supplies **no** stable
    reference, occurrence indices among a group of identical rows may be assigned differently and an
    identity may change — surfacing as an apparent duplicate or an apparent new row in the import
    report, not as silent corruption. Level 1 (a source-provided reference) removes the limitation,
    which is why it is preferred. **Unverified:** no re-import has been executed at all, ordered or
    reordered, because nothing is implemented; the guarantee is argued from the definition of the
    counter, not demonstrated.
11. **Both identity tiers are lexically invented** (new 2026-09-05). Measured in `content/`:
    `sourceRef` / `source_ref` **0**, `referenceId` **0**, `externalId` **0**, `OCC:` **0**,
    `occurrenceIndex` **0**, `occurrence` **0**. The V0.8 tasks must define the vocabulary from
    scratch in their own `constraints`. The *mechanism* is inside the taught window — `Map.merge` /
    `computeIfAbsent` / `getOrDefault` in one block, `day08-blk-27`
    (`content/lessons/day-08.json:211`), with `HashMap` at 56 hits — but no lesson names the concept.
12. **The import path forbids an idiom the course teaches** (new 2026-09-05). `parallelStream` has
    **12** corpus hits (day-12 ×8, day-10 ×4) and is presented as good practice, yet R22's second
    clause bans it on the import path because `occurrenceIndex` is order-derived. `task-csv-parse` must
    say so explicitly in `constraints`; a learner arriving from day-12 who parallelizes the parse loop
    will silently break idempotency, and **no test in this plan would catch it** unless the invariant
    suite's item 10a is run against a deliberately parallel implementation.

---

## Verdict

```
SPENDWISE_ALIGNMENT_PLAN_FINAL_READY_FOR_IMPLEMENTATION
```

**Amended 2026-09-05 by the pre-P0 sanity gate.** Seven corrections were applied to this file after
it was first finalized, each marked in place: the §2 heading (39 → **38** lessonMap entries); §6's
day-33 paragraph (an *addition* → a **modification**, and `buildTaskIds` now **permanently empty** per
blueprint §7.1 R-DAY33); §17's title and row 3 (**five breakages → four**, row 3 struck);
§18's gate steps 1 and 5 (both were **unrunnable as written**, now corrected and verified);
§18's P0 exit criterion (byte-identical → **parsed-content-equal**, because `builtAt` makes
`index.html` differ on every build); §18's P1 bullet (do **not** edit
`tests/test_validate_project.py:174`); §18's P2 exit (58/31/**38**); and Known gap 2
(**`SPRING_BOOT_EXACT_PIN_PENDING`**). Evidence for every one:
`docs/report/2026-09-05-spendwise-pre-p0-sanity-gate.md`.

**Amended again 2026-09-05 by the final planning reconciliation** (second amending pass). Six further
corrections, each marked in place: §2's heading and the V0.3/V0.4 contracts (**58 → 64 tasks / 50 → 56
required**; V0.3 **4 → 3 tasks** with `task-actuator-baseline` **deleted**; V0.4 **5 → 6 tasks**); §4's
day-25 cache row (Category/reference data only — **the V0.7 Rule engine does not exist at day-25**);
§8 and gap 2 (`SPRING_BOOT_EXACT_PIN_PENDING` blocks **`task-spring-bootstrap` (V0.3)**, not
`task-project-foundation`); §11's step volume (**≈205 → ≈229**); §13's import identity (new **§13.1** —
a **content fingerprint**, because `IMPORT:<batchId>:<rowNo>` could never fire the `UNIQUE` guard on
re-import); and §12 / §18 (the **`#/task/:taskId` route and task detail view move from P0 to P3**, so
P0 is plumbing only). Evidence for every one:
`docs/report/2026-09-05-spendwise-final-reconciliation-report.md`.

**Amended a third time 2026-09-05 by the final import-identity correction.** Six further changes, each
marked in place, **none of which moves a count**: §13's duplicate/re-import table rows and a new row for
two identical legitimate rows; **§13.1 rewritten** to the two-level model — a preferred
source-provided reference, otherwise `IMPORT:<baseFingerprint>|OCC:<occurrenceIndex>` — with the
withdrawn *"accepted cost"* and *"no automatic occurrence counter"* passages quoted before they are
overturned, seven retry/re-import acceptance criteria including one explicit **Not claimed**, and the
reordering limitation stated; §2's V0.8 identity obligations on four task contracts (`task-csv-parse`,
`task-duplicate-detection`, `task-import-row-transaction`, `task-import-result-report`); §9's
invariants **10**, **10a** and **16**; §11's two step-contract constraints (cite `R22`; the clause stays
inside `R22` because `architectureRules` is validated against `^R\d{1,2}$`, so the rule set stays at
**26**); §8's Maven-as-scaffolding clarification; and §16 / §17 row 7 / §18 P0's **capstone-window
regression guard** — test and validator only, **no UI change**. Evidence for every one:
`docs/report/2026-09-05-spendwise-import-identity-finalization-report.md`.

**What to challenge hardest**, in order: **§13.1's fallback identity
`IMPORT:<baseFingerprint>|OCC:<occurrenceIndex>`** (gaps 10–12) — its idempotency guarantee is
**conditional on row order** and demonstrated by nothing, both tiers' vocabulary is **0-hit** in the
corpus, and it forbids `parallelStream` (12 corpus hits) on the import path; a reviewer may argue the
honest options were to *require* a source-provided reference or to keep the collision and report it;
the **64**-task decomposition (gap 1) — *note it has already
been wrong once, as 58, and a reviewer should re-add the per-release column rather than trust the
total*; **§6's empty
`buildTaskIds` for day-33** (gap 9) — it suppresses the build-now CTA at the cost of
discoverability, and the alternative shape `future` + `[]` (live on day-05/11/12) achieves the same
suppression, so this is a preference over a shipping alternative rather than the only option; the
per-row import
atomicity resolution (§13) — it is a judgement call the corpus does not settle; the decision to place
`task-canonical-token-issuer` after day-36 rather than accepting a temporary HS256 signer at day-24
(§6); **blueprint §8.1's Reason 3 — that the Boot pin is now a choice between two out-of-OSS-support
lines** (gap 2), which rests entirely on external lifecycle data fetched 2026-09-05, not on anything
in this repository (§8.1's earlier argument, that the line should be 3.5.x because the corpus cites
Security 6.5 docs, is **withdrawn as refuted**: day-33 compiles clean and deprecation-free against
6.4.13); the claim that self-test #53
crashes the whole harness (gap 8); and the 15-vs-13 defense count (§19).

*(Superseded, kept for traceability: the previous pass listed here **"§13.1's content fingerprint — it
trades a visible false-duplicate on two identical same-day transactions for a silent dedup failure"**.
That trade is **withdrawn**; the fingerprint no longer stands alone. The composite `UNIQUE (a, b)`
0-hit measurement inside that item still stands and is unchanged.)*

**Repository state.** Baseline `e97c13a`, `COURSE_CONTENT_STABLE`, **unchanged** — `git status --short`
reports zero modified tracked files. Four untracked planning documents exist:
`docs/report/2026-09-05-spendwise-architecture-blueprint.md`
(verdict `SPENDWISE_ARCHITECTURE_BLUEPRINT_FINAL`, amended twice the same day), this file,
`docs/report/2026-09-05-spendwise-pre-p0-sanity-gate.md`, and
`docs/report/2026-09-05-spendwise-final-reconciliation-report.md`. **Nothing else was created or
modified.** `content/spendwise-project.json`, `content/lessons/*`, `tools/*`, `tests/*`,
`index.template.html` and the generated `index.html` are all untouched. **Nothing was staged, committed
or pushed.**

> *Amended 2026-09-05 (third pass).* A **fifth** untracked planning document now exists —
> `docs/report/2026-09-05-spendwise-import-identity-finalization-report.md` — and the blueprint has
> now been amended **four** times, this file **three**. The implementation statement is **unchanged and
> re-verified**: zero modified tracked files, nothing staged, nothing committed, nothing pushed.

**If approved**, P0 begins — validator schema additions plus the `STATE_VERSION` 2→3 migration with an
empty rename map, landing the migration machinery while it is still a no-op. P0 changes no artifact
content, **adds no route and no learner-visible rendering**, and must leave the site behaviourally
identical to a learner. `SPRING_BOOT_EXACT_PIN_PENDING` does **not** block P0, and does **not** block
`task-project-foundation` either — it blocks **`task-spring-bootstrap` (V0.3)**, which P1 authors.
