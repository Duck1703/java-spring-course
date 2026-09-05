# Spendwise Architecture Blueprint — V0.1 → V1.0 (FINAL)

**Verdict:** `SPENDWISE_ARCHITECTURE_BLUEPRINT_FINAL`
**Date:** 2026-09-05
**Repo baseline:** `e97c13a` (`COURSE_CONTENT_STABLE`) — course curriculum is frozen
**Scope:** architecture decisions only. No code written, no course content edited, no artifact
edited, no commit, no push. Two files changed on disk: this one and
`docs/spendwise-alignment-phase2-plan.md`.
**Supersedes:** the `SPENDWISE_ARCHITECTURE_BLUEPRINT_READY_FOR_REVIEW` draft that occupied this
same path. Overwritten in place because the finalization directive named this exact filename as
final output 1. That directive overrides the "never overwrite a dated report" rule in
`CLAUDE.md`; the superseded draft survives only in the session transcript, and §1 below lists
every decision that changed, so nothing is silently lost.
**Relationship to Phase 2:** `docs/spendwise-alignment-phase2-plan.md` has been revised in the
same session and now carries `SPENDWISE_ALIGNMENT_PLAN_FINAL_READY_FOR_IMPLEMENTATION`. It is
downstream of this document: where the two disagree, this one wins.

**Amended 2026-09-05 by the final planning reconciliation** (third amending pass, after the pre-P0
sanity gate). Six corrections, each marked in place with a dated note:

| # | What changed | Where |
|---|---|---|
| 1 | buildTask total **58 / 50 / 8 → 64 / 56 / 8** — the total row never matched its own per-release rows | §9 Final target, §9 per-release table, §9 `buildSteps ≈ 229`, §9 test-impact table, reviewer orientation 6, Verdict, gap 10 |
| 2 | `task-actuator-baseline` **removed from V0.3** — Actuator is 0-hit at day-13/14, taught day-29, and lives in V0.9's `task-production-packaging` | §5 V0.3 header, §9 delta list |
| 3 | V0.4 **5 → 6 tasks** — the retire-and-split was mis-added | §5 V0.4 header, §9 per-release table |
| 4 | `SPRING_BOOT_EXACT_PIN_PENDING` moves from `task-project-foundation` (V0.1) to **`task-spring-bootstrap` (V0.3)** — V0.1 has no Spring dependency | §8 opening, §8 Spring Boot row, §8.1 blocking rules, ADR-017, gap 3, Verdict |
| 5 | Import identity is a **content fingerprint**, not `IMPORT:<batchId>:<rowNo>` | new **D10.1**, D10, D14, R22, ADR-007, gap 11 |
| 6 | Day-25 caches **Category/reference data only** — the V0.7 Rule engine does not exist yet | D16, ADR-011 |

Full derivation, evidence and the fourteen-check consistency gate:
`docs/report/2026-09-05-spendwise-final-reconciliation-report.md`.

**Amended 2026-09-05 by the final import-identity correction** (fourth amending pass). **Row 5 of the
table above is superseded.** A bare content fingerprint collapses two *legitimate* transactions that
happen to share account, date, direction, amount and normalized description — for a finance ledger
that is not an acceptable frozen V1.0 dedup strategy, and the previous pass accepted it as a
deliberate cost. The frozen model is now a **two-level fallback identity**: a stable
source-provided reference when the file carries one, otherwise the base fingerprint **plus a
1-based occurrence index within the current statement**. Reverting to `IMPORT:<batchId>:<rowNo>` stays
forbidden — a new `ImportBatch` PK on re-upload breaks idempotency.

| # | What changed | Where |
|---|---|---|
| 7 | import identity becomes **two-level**: preferred source reference, else `IMPORT:<baseFingerprint>\|OCC:<n>` | **D10.1** (rewritten), D10, D14, R22, ADR-007, §5 V0.8, gap 11, new gap 13, reviewer orientation **item 0**, Verdict |
| 8 | the accepted false-duplicate collision is **withdrawn**; a **reordering limitation** replaces it | D10.1, ADR-007 Rejected, gap 11, new gap 13 |
| 9 | **source-file order is now load-bearing** — sequential parse only, no `parallelStream` in the import path | D10.1, R22 second clause, §5 V0.8 invariants + constraints |
| 10 | Maven + Wrapper at V0.1 is **project/tooling scaffolding, not a Day-01 learning objective** | §8 opening, §8 Build-tool row, gap 12 |
| 11 | P0 gains a **capstone-window regression guard** (Day 31–36 exposes no required Spendwise CTA) — test/self-test only, no UI change | §7.1 **R-CAPSTONE-GUARD**, reviewer orientation item 0 |

**No count moved in this pass.** 64 buildTasks / 56 required / 8 optional / 31 features / 38
lessonMap entries / ≈229 buildSteps are all unchanged; the identity strategy changed inside existing
task contracts, not the task inventory. Full derivation and the eight-check consistency gate:
`docs/report/2026-09-05-spendwise-import-identity-finalization-report.md`.

---

## Purpose

One architecture, fixed from V0.1 to V1.0, so a learner building Spendwise across 40 lessons plus
an OJT window never has to rewrite a decision — and so any future coding mentor, human or AI,
asked to change one of those decisions **stops and says so** instead of quietly introducing a
second architecture.

The reviewed draft was approved in direction and required fifteen targeted corrections. All
fifteen are applied. Four of them reverse a decision the draft asserted; those four are the first
four rows of §1 and the first three items of the reviewer orientation.

## Inputs

| Input | What it is | Weight |
|---|---|---|
| course content at `e97c13a` | 39 lesson files / 40 lesson records, `content/lesson-index.json`, `content/spendwise-project.json`, `tools/validate_project.py`, `tools/validate_lessons.py`, `index.template.html`, `tests/` | **frozen — binding** |
| `docs/build-while-you-learn-plan.md` | product master plan (2576 lines; §8 §9 §10 §25 §29 §35 §41–§47) | binding |
| this document | final architecture decisions | binding on Phase 2 |
| `docs/spendwise-alignment-phase2-plan.md` | 980-line implementation proposal, now revised | downstream |
| `docs/SPENDWISE_ARCHITECTURE_RESEARCH.md` | external research (Genspark, 18 parts, 1272 lines) | **evidence, not authority** |

**Authority order:** frozen curriculum > master plan > this blueprint > Phase 2 plan > external
research. The research is cited below only where the corpus independently corroborates it, or
where it is being rejected.

## Reviewer orientation — where to push back hardest

Ranked weakest-first. The first four are reversals of the reviewed draft; a reviewer who only has
time for four should read these.

> **Item 0, inserted 2026-09-05 by the final import-identity correction — now the weakest claim in
> the document, ahead of everything below.** **§2 D10.1's fallback identity
> `IMPORT:<baseFingerprint>|OCC:<occurrenceIndex>`.** Three reasons to push here first:
> 1. **Its idempotency guarantee is conditional and untested.** Re-importing a statement produces the
>    same identities *only if the rows arrive in the same order*. That condition is asserted from the
>    shape of the format, never demonstrated — **nothing is implemented**, so no reordered-file
>    scenario has been run. See gap **13**.
> 2. **Both tiers' vocabulary is invented.** `referenceId`, `externalId`, `OCC:`, `occurrenceIndex`
>    and `occurrence` are **all 0-hit in `content/`**. The *mechanism* the counter needs is taught
>    exactly once — `Map.merge` / `computeIfAbsent` / `getOrDefault` at `day08-blk-27`
>    (`content/lessons/day-08.json:211`) — but the concept has no citation anywhere in the corpus.
> 3. **It replaced a rejected alternative with a different failure mode, not with none.** The prior
>    model dropped a second identical legitimate row and *reported* the loss; this one creates it, and
>    pays with a reordering failure mode that is arguably harder for a learner to reason about than a
>    duplicate line in an import report. A reviewer may legitimately prefer requiring a
>    source-provided reference and refusing files without one.
>
> Also new and weakly evidenced, though far smaller: **R22's second clause** (sequential parse) is a
> *prohibition* on `parallelStream`, which has **12** corpus hits and is taught as good practice at
> day-10/day-12 — so the import path deliberately contradicts a taught idiom, on identity grounds
> only. And **§7.1's R-CAPSTONE-GUARD** is a test that currently passes at zero cost, which means it
> proves nothing today; its whole value is as a *future* regression guard.

1. **§2 D5/R5–R7, the signed-effect ledger.** The single most consequential rule set in the
   document, and the one with the least corpus support: `openingBalance` is **0 hits across all 39
   lesson files** and the words TRANSFER_IN / TRANSFER_OUT appear nowhere in the frozen artifact.
   The invariant `balance = openingBalance + Σ signedEffect(t)` is a Spendwise design decision, not
   a taught pattern. It is *defensible* — day-20 teaches `@Version` on a contended counter and
   day-21 teaches `SUM`/`GROUP BY` — but the specific four-way sign table is invented here.
2. **§2 D2/R11, "business-centric JPA entities."** The draft claimed the domain stays
   framework-pure. That claim is withdrawn: after V0.5 the domain classes carry
   `jakarta.persistence` annotations and are therefore *not* framework-pure. A reviewer who
   believes a finance domain must be persistence-ignorant will disagree with this on principle,
   and the disagreement is legitimate — it is being resolved in favour of not maintaining twin
   models, on the evidence that `MapStruct` and every mapping mechanism that would make twins
   affordable are 0-hit.
3. **§4 ADR-017, the toolchain freeze.** The corpus never states a Spring Boot
   triple. `3.4` is a *demonstrable floor* (two features are dated to it) and there is no upper
   bound in evidence, so the earlier `3.4.x` pin has been withdrawn — §8.1 now carries
   `SPRING_BOOT_EXACT_PIN_PENDING`. **The intermediate argument that the corpus's Spring Security
   `6.5`/`6.5.x` citations point at the 3.5.x line has itself been withdrawn** (pre-P0 sanity gate,
   2026-09-05): day-33's code compiles clean and deprecation-free against Security **6.4.13**, all 26
   security types resolve, and every 6.5-only API is 0-hit in the corpus. So the pin is open in *both*
   directions — no line is preferred here, and the real constraint is the one in §8.1 Reason 3: as of
   2026-09-05 **both** 3.4.x and 3.5.x are past OSS end-of-support. This is the weakest area of §8:
   the decision is externally time-bound, not derivable from this repository.
   Worse: **there are no build files in this repository at all** — 0 files for `pom.xml`,
   `mvnw`, `Dockerfile`, `compose.yml`, `docker-compose*`, `gradlew`, `build.gradle`, `.mvn/` in the
   entire working tree — so nothing mechanically
   enforces this pin. It is a documentary freeze only.
4. **§6 D12/R18–R20, JWT scope.** Reversed from the draft: refresh-token rotation and replay
   detection are now **explicitly optional**. This is the best-evidenced correction in the document
   (`content/lessons/day-24.json:246` says in so many words that they are not grading conditions),
   but it *reduces* what a learner is required to build, so a reviewer optimizing for portfolio
   strength will object.
5. **§7 and §7.1 the post-capstone execution window.** Day 33 teaches canonical JWT issuance but sits inside
   the graded e-commerce capstone (day-31→36), so the required Spendwise `TokenIssuer` task is
   scheduled *after* day-36. That means V0.6 is not architecturally complete until day-37+, and a
   reviewer may argue this leaves V0.6 in a half-finished state for thirteen lessons. The
   counter-argument — that the alternative is either untaught work or an unsafe temporary signer
   rewritten later — is in §7. **§7.1 goes further** and forbids `task-canonical-token-issuer` from
   appearing in `lessonMap["day-33"].buildTaskIds` at all, so the day-33 page renders no build-task
   CTA. That reverses the Phase 2 plan's §6 and costs day-33 → task navigability; a reviewer who
   values discoverability over CTA suppression will disagree.
6. **§9 the recomputed counts (64 build tasks / 56 required).** Derived, not measured. Every input
   to the derivation is cited in §9, but the per-release task decomposition is an authoring
   estimate and the true number will move when the tasks are actually written. **Two count families
   in this section have now been wrong once each:** the lessonMap counts in the first finalization
   (39 entries / 24-1-14, corrected 2026-09-05 to 38 / 24-1-13) and the buildTask total (**58 / 50,
   corrected 2026-09-05 to 64 / 56 — the total row never matched its own per-release rows**). Treat
   any count in this document that does not cite a re-measurement or an explicit column sum as
   suspect.
7. **ADR-006, rejecting the event architecture.** Unchanged from the draft and still the largest
   single deletion from the external research.

---

## 0. Method, and the one measurement that drove most decisions

Every load-bearing API name was counted across all 39 lesson files (40 lesson records — one file,
`content/lessons/ojt-evaluation.json`, carries both `day-39-64` and `day-65-66`) rather than
trusted from either the Phase 2 plan or the research document.

**Zero occurrences corpus-wide:** `ArchUnit`, `Spring Modulith`, `hexagonal`, `outbox`,
`Spring Batch`, `MapStruct`, `Moneta`/JSR-354, `@Embeddable`, `@Embedded`,
`AttributeConverter`/`@Convert`, `@Column(precision/scale)`, `NUMERIC`, `CHECK (`,
`@UniqueConstraint`, `ON CONFLICT`, `SKIP LOCKED`, `Idempotency-Key`, `202 Accepted`, `setScale`,
`RoundingMode`, `@AuthenticationPrincipal`, `@EnableWebSecurity`, `ZoneId`, `Collectors.reducing`,
`Collectors.mapping`, `openingBalance`, `ImportBatch`, `ExchangeRate`, `spring-security-test`,
`mockJwt`, `com.spendwise` (0 in `content/`, all 8 hits are in `docs/`), and `package com.` — **every
Java snippet in the corpus is import-only; no snippet ever declares a package.**

**Near-zero:** `@TransactionalEventListener` **1** (one exercise hint in
`content/lessons/day-27.json`, offered as one of two options, with no publisher, event class or
listener anywhere); `ApplicationEventPublisher` / `publishEvent` / `@EventListener` **0** each;
`Caffeine` **1**; `ShedLock` **4**, all in `content/lessons/day-25.json`, named as an answer and
never configured; `@Retryable` **1** (day-15); `RestClient` **3** (day-14, day-28, day-36 — one
mention each); `TokenIssuer` **8**, *all eight in `content/lessons/day-33.json`*; `MessageDigest`
**2**, both day-24.

**Meanwhile the things the research defers are taught in depth**, and one of them is taught in
two incompatible ways. `@Cacheable` 54, `@Scheduled` 41, `@Async` 113, `PasswordEncoder` 57,
`AuthenticationManager` 17, `WebClient` 47, `springdoc` 29, `Flyway`+`flyway` 21, `WithMockUser` 24.

**The Redis correction.** The reviewed draft asserted Redis is "core" and made
`RedisCacheManager` the canonical cache. That is now qualified. Day-25 does teach the Redis
cache backend in depth, but:

- `redis:7-alpine` appears **exactly once**, at `content/lessons/day-30.json:334`, and it is an
  *exercise answer key*, not a reference configuration.
- The reference compose file at `content/lessons/day-30.json:204` deliberately omits Redis:
  `"# Redis KHONG bat buoc: du an hien chi dung ConcurrentMapCacheManager mac dinh cho cache (Day 34), chua co code nao ket noi Redis."`
- Day-34 — the capstone's own cache sprint — teaches `ConcurrentMapCacheManager`
  (`day34-blk-11`, `day34-blk-13`), not Redis.

So the corpus teaches Redis as *knowledge* and `ConcurrentMapCacheManager` as *the configuration
the project actually runs*. ADR-010 is corrected accordingly in §4.

That inversion is the spine of this blueprint. Adopting the research's event architecture,
`AttributeConverter` money mapping, `Idempotency-Key` header and Caffeine-first cache path would
require the learner to invent five techniques the course never provides — which is precisely the
drift this document exists to prevent.

---

## 1. What changed from the reviewed draft

Fifteen corrections. Four reverse a decision; eleven sharpen one. Nothing else in the draft's
direction was disturbed.

| # | Draft said | Final says | Kind |
|---|---|---|---|
| 1 | domain is framework-pure; `domain` imports only `shared` + JDK (draft D20) | domain MAY import `jakarta.persistence` mapping annotations from V0.5; **business-centric JPA entities**, purity claim withdrawn | **reversal** |
| 2 | package `com.spendwise.import` | `com.spendwise.imports` — `import` is a Java keyword and `package com.spendwise.import;` does not compile | fix |
| 3 | `balance == SUM(transactions.amount)` | `Transaction.amount` always positive; signed effect per type; `balance = openingBalance + Σ signedEffect(t)` | sharpen |
| 4 | transfer = two transactions (implied) | `TransferService.transfer(...)`, one `@Transactional`, linked TRANSFER_OUT + TRANSFER_IN sharing a `transferRef`, both projections updated, all-or-nothing; **no Transfer aggregate** | sharpen |
| 5 | "an engine may call *down* the spine, never up" (draft D15) | rule **deleted**. Build order and runtime dependency flow are separate axes; Recurring and Import *do* call the canonical creation use case | **reversal** |
| 6 | refresh-token rotation is core (draft D12) | rotation + replay detection are **optional**; required set is hashing / filter chain / stateless / verification / issuance / ownership / logout revocation | **reversal** |
| 7 | the day-33 task is required, inside the capstone (draft §4 V0.6) | required TokenIssuer task moves to **after day-36**; day-22→24 build the seam, day-33 unlocks the knowledge; no unsafe temporary signer | **reversal** |
| 8 | R16: no second creation path "not for a fixture" | R16 scoped to **production code**; tests may seed via fixture builders to arrange history, but not when testing creation behaviour itself | sharpen |
| 9 | money scale 2, stated as fact | scale 2 labelled **the Spendwise V1.0 precision convention**, not an ISO-4217 claim; arbitrary minor units out of scope | sharpen |
| 10 | `Instant` justified by JPA | `Instant` justified by **Spring Boot 3.x + Hibernate 6**, explicitly *not* a portable Jakarta Persistence 3.1 guarantee; day-19's `OffsetDateTime` advice acknowledged as the conflicting authority | sharpen |
| 11 | no toolchain section | new **§8 toolchain freeze** + ADR-017: Java 17, Maven + Wrapper, PostgreSQL 16, root `com.spendwise`; the Spring Boot version is left as `SPRING_BOOT_EXACT_PIN_PENDING` (§8.1) | addition |
| 12 | two governance questions left open | resolved: `AUTHOR_V0_7_TO_V1_0_TASKS = YES`; `DAY_39_64 = PRIMARY_SUGGESTED_EXECUTION_WINDOW` + a `SPENDWISE_SELF_STUDY_ROADMAP`; `202 Accepted` dropped as a goal | addition |
| 13 | 22 Constitution rules with three internal contradictions | 26 rules, contradiction-free; see §2 | sharpen |
| 14 | 16 ADRs | 17 ADRs — 001–016 updated in place, 017 added for the toolchain. No new ADR for trivia | sharpen |
| 15 | 8 stop triggers | 13 triggers + required output shape; see §10 | sharpen |

---

## 2. The twenty decisions

Renumbered but same identifiers as the draft, so ADR and Phase 2 cross-references stay valid.

**D1 — Package structure.** Root `com.spendwise`. Package by feature, layered inside the feature:

```
com.spendwise
├── shared           Money, DomainException, CurrentUser, page/response primitives
├── account          Account, AccountService, AccountRepository, AccountController, dto/
├── transaction      Transaction, TransactionType, TransactionCreationService, TransferService, …
├── category         Category, CategoryService, …
├── budget           Budget, BudgetService, BudgetView, …
├── recurring        RecurringTransaction, RecurringGenerationService, …
├── rule             Rule, RuleCondition, RuleAction, RuleEngine, …
├── imports          ImportBatch, ImportRow, ImportService, CsvParser, …
├── report           ReportService, DashboardView, …
├── user             User, UserService, AuthController, TokenIssuer, …
└── config           SecurityConfig, CacheConfig, SchedulingConfig, JacksonConfig
```

`imports`, never `import`. `import` is a reserved word; `package com.spendwise.import;` is a
compile error. The external research reached the same conclusion independently
(`docs/SPENDWISE_ARCHITECTURE_RESEARCH.md:423`, `:974`, with the note that `imports` is used
"vì 'import' là reserved") — one of the few places the research is corroborated rather than
overruled. Note that `com.spendwise` itself is **0-hit in `content/`**: the course teaches
`com.example.ecommerce` (`content/lessons/day-31.json:74`) and `com.example.shop.api`
(`content/lessons/day-29.json:75`). `com.spendwise` is a Spendwise-side decision, recorded as such.

**D2 — One class per concept, and the domain is not framework-pure after V0.5.**

There is exactly one `Transaction` class, one `Account`, one `Budget`. There is no
`TransactionEntity` twin and no mapper between them. At V0.1–V0.4 these are plain Java. **At V0.5
the same classes gain `jakarta.persistence` mapping annotations.** From that point the design is
deliberately **business-centric JPA entities** — classes that own their invariants and also carry
their own mapping — and **not** a framework-pure domain plus a duplicate persistence model.

Import rules for domain classes (superseding the draft's D20):

- **MAY import:** the JDK; `com.spendwise.shared`; `jakarta.persistence` **mapping** annotations
  (`@Entity`, `@Table`, `@Id`, `@GeneratedValue`, `@Column`, `@Enumerated`, `@ManyToOne`,
  `@OneToMany`, `@JoinColumn`, `@Version`).
- **MUST NOT import:** Spring MVC (`org.springframework.web.*`), Spring Security
  (`org.springframework.security.*`), Spring service/application types (`@Service`,
  `@Component`, `@Transactional`, `ApplicationContext`), repository implementations, any
  infrastructure client (Redis, HTTP, file system, mail).

Rejected: separate rich domain + anemic entity. The mechanisms that make twin models affordable
are absent from the course — `MapStruct` 0-hit, and the learner would hand-write and hand-maintain
two dozen mappers for no lesson-supported benefit. Day-19's own template shows the JPA-friendly
`protected Product() {}` no-arg constructor on a business class, which is the shape this decision
adopts.

**D3 — Money.** `Money` is a value object wrapping `BigDecimal` + a currency. Scale **2**.
Persisted as two plain columns declared in migration DDL: `NUMERIC(19,2)` + `VARCHAR(3)`.

This is **the Spendwise V1.0 precision convention.** It is not a claim that scale 2 models every
ISO-4217 currency — it does not: JPY has 0 minor units, and BHD/KWD/TND have 3. Arbitrary-currency
minor units and a full multi-currency accounting engine are out of scope, and the last item of
`content/spendwise-project.json` `product.outOfScope` already says so verbatim: `"full
multi-currency accounting engine"`.

The one rounding rule set, in full:

- **Construction** normalizes to scale 2 with `RoundingMode.HALF_UP`. Every `Money` in the system
  is at scale 2; no code downstream re-rounds.
- **Addition/subtraction** of same-currency `Money` is exact and stays at scale 2.
- **Multiplication by a plain factor** (percentage, share) rounds HALF_UP back to scale 2 at the
  end of the expression, not between terms.
- **Division** is the *only* operation that may lose value; it requires an explicit scale and
  `RoundingMode` at the call site. `BigDecimal.divide` without a `MathContext`/scale is forbidden —
  it throws `ArithmeticException` on non-terminating results, which is the V0.7 budget-percentage
  trap named in §11.
- **Comparison** is `compareTo(...) == 0`. `BigDecimal.equals` compares scale and is never used for
  monetary equality. `Money.equals` is implemented over `compareTo` + currency.
- **Cross-currency arithmetic throws.** FX is a display-time conversion in the report layer only,
  never a ledger entry. `feat-exchange-rate` therefore never writes a `Transaction`.
- `double` and `float` never touch money, including to satisfy a `Collectors.summingDouble(...)`
  signature. This one bites: day-10 teaches `summingDouble` (3 hits) and `BigDecimal` appears 0
  times in day-10. The taught-and-safe route is
  `stream().map(Transaction::amount).reduce(BigDecimal.ZERO, BigDecimal::add)`.

Rejected: `NUMERIC(19,4)` and `setScale(4, HALF_UP)` from the research
(`docs/SPENDWISE_ARCHITECTURE_RESEARCH.md`, PART 18/ADR-002); `@Embeddable`; `AttributeConverter`;
`@Column(precision=…, scale=…)`; JSR-354/Moneta. All five mechanisms are 0-hit in the corpus, and
scale 4 buys sub-cent precision that no Spendwise use case needs while making every stored figure
disagree with every displayed figure.

**D4 — Time.** System event instants are `Instant` → `TIMESTAMPTZ`. Economic dates
(`Transaction.occurredOn`, `Budget` period bounds, `RecurringTransaction.nextDueDate`) are
`LocalDate` → `DATE`. Period keys are `YearMonth`-shaped `VARCHAR(7)` (`"2026-09"`). Bare
`LocalDateTime` is forbidden in persisted state.

**This is an implementation choice, not a portability guarantee.** It rests on Spring Boot 3.x +
Hibernate 6 mapping `Instant` regardless of the JPA specification level. It is explicitly *not* a
Jakarta Persistence 3.1 guarantee, and the frozen curriculum says the opposite:
`content/lessons/day-19.json:172` — *"Jakarta Persistence 3.1 đã hỗ trợ trực tiếp một tập kiểu
java.time gồm LocalDate, LocalTime, LocalDateTime, OffsetTime và OffsetDateTime"* — a list that
excludes `Instant`; and `content/lessons/day-19.json:182`, in a code comment: *"`java.time.Instant`
thì phải JPA 3.2 trở lên mới được chuẩn hoá, nên chưa dùng ở đây."*

So day-19 recommends `OffsetDateTime` and this blueprint chooses `Instant`. That is a live
two-authority conflict and it is resolved in favour of `Instant`, on these grounds: day-21 uses
`Instant` with `@CreatedDate` in a persisted auditing field; Hibernate 6 (the only provider this
project will ever run) maps it; and `TIMESTAMPTZ` + `Instant` removes offset ambiguity from stored
audit data. A mentor who prefers `OffsetDateTime` on portability grounds must file
`ARCHITECTURE_CHANGE_REQUIRED` (§10) rather than switch, because the type appears in migration DDL.

**D5 — Financial source of truth: the signed-effect ledger.**

- `Transaction` rows are the sole source of financial truth.
- `Transaction.amount` is **always a positive `Money`**. A negative amount is a validation
  failure, not a withdrawal.
- Direction lives in `Transaction.type`, and each type has exactly one signed effect:

  | `TransactionType` | signed effect on its account |
  |---|---|
  | `INCOME` | `+amount` |
  | `EXPENSE` | `−amount` |
  | `TRANSFER_IN` | `+amount` |
  | `TRANSFER_OUT` | `−amount` |

- `Account.openingBalance` is an immutable `Money` set once at account creation.
- `Account.balance` is a **stored projection**, never independent truth.
- **The invariant, and there is exactly one canonical interpretation of it:**

  ```
  Account.balance  ==  Account.openingBalance  +  Σ signedEffect(t)
                                                  for all t where t.accountId == Account.id
  ```

- Every `Budget.spent` / `remaining` / `percentage` / `status`, every dashboard figure and every
  report figure is **derived at read time from persisted transaction rows** and never stored.
- No money value is ever cached (see D16).

The projection is written only inside the same transaction that writes the `Transaction` row, and
guarded by `@Version`. The ledger must remain able to reconstruct and to reconcile: a scheduled
reconciliation job (D16) recomputes the right-hand side and reports drift.

Rejected: pure derivation on every read (deletes the `@Version` concurrency lesson day-20 teaches,
and makes the dashboard a full table scan); a naked stored balance with no invariant (corrupts
silently and cannot be repaired). Caveat, stated plainly: `openingBalance` is **0-hit** in the
corpus and the four-way sign table is invented here — see reviewer orientation item 1.

**D6 — Repository evolution.** V0.2 defines a hand-written interface, shaped as a deliberate
subset of Spring Data's method-name conventions (`save`, `findById`, `findAll`,
`findByAccountId`, `existsBy…`, `deleteById`), with an in-memory `ConcurrentHashMap`
implementation. At V0.5 the interface is **re-declared** as `extends JpaRepository<Transaction,
Long>` and the in-memory implementation is **deleted**. Call sites do not change, which is the
whole pedagogical point.

Rejected: a permanent port/adapter pair. `hexagonal` is 0-hit; `@DataJpaTest` + Testcontainers
already supply the testability the adapter would exist to provide.

**D7 — DTO boundary.** No entity and no VO crosses the HTTP boundary in either direction. Request
and response `record`s per endpoint, mapped by hand in the service or a small static factory.
Errors are `ProblemDetail` (RFC 7807), which V0.4's acceptance criteria already require verbatim.

**D8 — Layers.** `controller → service → repository`; `service → domain`. A controller never
touches a repository. A service never returns `ResponseEntity`. `@RestControllerAdvice` is the
single error-translation point in the application.

**D9 — Transaction boundaries.** `@Transactional` on public service methods only — never on a
controller, a repository, a private method or a `final` method (self-invocation and proxying both
break silently). Read paths are `@Transactional(readOnly = true)`. **No external HTTP call, no file
I/O and no `@Async` dispatch inside a transaction**; day-27 states the rule and the reason:
*"Gọi một method @Async … từ bên trong cùng một @Transactional method tạo đơn hàng … @Async nên
được gọi SAU KHI transaction … đã commit"* (`content/lessons/day-27.json:278`).

**D10 — One canonical creation path, in production code.**

In **production code**, every `Transaction` is created by
`TransactionCreationService.create(CreateTransactionCommand)`. There is no second path — not for
manual REST, not for the recurring generator, not for CSV import. The command carries a
`sourceRef` recording provenance, in exactly three grammars:

```
MANUAL
RECURRING:<recurringId>:<periodKey>
IMPORT:<rowIdentity>              ← two forms, see D10.1
```

`IMPORT:<rowIdentity>` resolves to **either** a source-provided reference
(`IMPORT:SRC:<source>:<accountId>:<sourceTxnId>`) **or**, when the file supplies none, the fallback
`IMPORT:<baseFingerprint>|OCC:<occurrenceIndex>`. **See D10.1** — and note that the import form is
still *never* `IMPORT:<batchId>:<rowNo>`, because a regenerated `ImportBatch` PK on re-upload breaks
idempotency.

**D10.1 — Import identity, canonical. Two-level fallback model** (added by the final planning
reconciliation, 2026-09-05; **rewritten the same day by the final import-identity correction**).

> **Amendment, 2026-09-05 — what this rewrite overturns.** The version of D10.1 written earlier the
> same day froze a bare content fingerprint and accepted its collision, verbatim:
>
> > *"A content fingerprint cannot distinguish two genuinely distinct transactions that share account,
> > date, direction, amount and description — two identical 25,000₫ coffees on the same day. The second
> > one imports as `DUPLICATE` and the learner loses a real transaction. This is a **real, accepted
> > cost** …"*
>
> and it explicitly rejected the remedy now adopted:
>
> > *"**No automatic occurrence counter is used** — a counter would reintroduce order dependence and
> > make the fingerprint unstable across re-import, which is the defect being fixed."*
>
> **Both are withdrawn.** Silently dropping a real transaction because another row happens to carry
> the same five business values is not an acceptable frozen V1.0 dedup strategy for a finance ledger —
> a duplicate-detection mechanism that eats legitimate money entries fails the ledger invariant
> (ADR-003) that transactions are the source of truth. The occurrence counter's cost was also
> mis-stated: it does not break stability across re-import of the *same* statement, because the
> counter is derived from the statement's own row order, which a re-upload of the same file
> reproduces. What it does cost is stability under **arbitrary reordering** of a reconstructed file,
> which is a narrower and honestly-statable limitation (below).

**The defect the original D10.1 closed, still closed.** Every revision before it defined the import
provenance as `IMPORT:<batchId>:<rowNo>` and Phase 2 §13 claimed *"re-import of a partially imported
file → same `batchId` → the already-imported rows collide on the constraint and are skipped"*.
**Nothing guaranteed the same `batchId`.** `ImportBatch` is a JPA entity created per upload, so its PK
is a fresh generated value every time; a second upload produced `IMPORT:<newId>:<rowNo>` for every
row, the `UNIQUE (user_id, source_ref)` constraint never fired, and duplicate detection silently
failed — contradicting V0.8's own acceptance criterion in `content/spendwise-project.json`:
*"Importing the same transaction multiple times does not create uncontrolled duplicates."* Note the
criterion's subject: **the same transaction, not the same file.** `IMPORT:<batchId>:<rowNo>` remains
**forbidden**, and this pass does not reintroduce it.

**The rule — two levels, preferred first.**

*Level 1 — preferred identity: a stable source-provided reference.* If an imported row carries a
transaction/reference id supplied by the source (a bank statement's transaction id, reference number
or end-to-end id), **that** is the row identity. It is scoped so one bank's id space cannot collide
with another's, nor one owner's with another's:

```
sourceRef = "IMPORT:SRC:" + sourceKey + ":" + accountId + ":" + normalize(sourceTxnId)
sourceKey = the import source identifier recorded on the ImportBatch (e.g. the
            statement profile / institution key); a single stable string per source
```

Ownership scoping is already carried by the `UNIQUE (user_id, source_ref)` constraint (D14), so
`user_id` is not repeated inside the string. `accountId` is included because a source id is only
guaranteed unique within the account it was issued against.

*Level 2 — fallback identity, used only when the row supplies no source reference:*

```
baseFingerprint = accountId | occurredOn | direction | amount(scale 2, toPlainString)
                            | normalize(description)
occurrenceIndex = the 1-based occurrence number of that SAME baseFingerprint within the
                  current imported statement, counted in source-file order
sourceRef       = "IMPORT:" + baseFingerprint + "|OCC:" + occurrenceIndex

normalize(s)    = trim, collapse internal whitespace to one space, uppercase
```

- `occurredOn` is the economic `DATE` (R12), never an ingestion timestamp.
- `amount` is the positive `BigDecimal` at DDL scale rendered with `toPlainString()`, so `100.5` and
  `100.50` cannot produce two identities. `direction` is the typed enum name.
- Fields are joined with `|`, a delimiter `normalize` cannot emit, so boundaries are unambiguous.
- `occurrenceIndex` counts **within one statement**, not across history: the first occurrence of a
  base fingerprint in the file is `OCC:1`, the second `OCC:2`. Two identical legitimate rows in one
  file therefore become **two different transaction identities** and both import.
- Re-importing the same statement in the same logical order recomputes the same
  `OCC:1` / `OCC:2` assignment, so both rows are recognised as `DUPLICATE` and zero transactions are
  added.
- `batchId` and `rowNo` are still recorded — on the **`ImportRow`** record, as reporting columns
  driving the per-row error list and the summary. They are **not** inputs to identity.

**Implementation shape, and why it is reachable at the taught level.** The counter is one
`Map<String, Integer>` keyed by `baseFingerprint`, incremented as rows are read:
`occ = counts.merge(baseFingerprint, 1, Integer::sum)`. `merge`, `computeIfAbsent` and
`getOrDefault` are all taught together in one day-08 block, `day08-blk-27`
(`content/lessons/day-08.json:211`): *"orders.merge(new CustomerId(\"C1\"), 2, Integer::sum);"*,
`computeIfAbsent`, `getOrDefault` — measured 2026-09-05, and `HashMap` has 56 corpus hits. No new
technique is introduced.

**One new constraint this creates, and it is load-bearing: the import path must parse sequentially,
in source-file order.** `occurrenceIndex` is order-dependent by construction, so any parallelism in
the parse loop makes it nondeterministic. `parallelStream` has **12 corpus hits** (day-12 ×8,
day-10 ×4) and `Files.lines` **25**, so a learner has been shown exactly the tool that would break
this — the V0.8 task contracts must forbid it in the import path explicitly. Ordinary `Files.lines`
consumed sequentially is fine; `.parallel()` / `parallelStream()` is not.

**Why this satisfies every requirement the plan needs:**

| Requirement | How it is met |
|---|---|
| two identical *legitimate* rows in one file both import | they receive `OCC:1` and `OCC:2` — different identities. **This is the defect this pass fixes** |
| stable across re-import of the same statement | both levels are pure functions of file content plus its own row order, so upload #2 of the same file yields byte-identical `sourceRef`s |
| does not depend on a generated `ImportBatch` PK | the PK is not an input at either level |
| retry of a partially imported file works | already-successful rows recompute the same `sourceRef` and are rejected as duplicates; previously failed rows committed nothing, so they insert cleanly |
| already-successful rows recognised as duplicates | by the `UNIQUE` constraint, or by the `existsBy…` pre-check in front of it |
| previously failed rows may be retried | a failed row wrote nothing, so nothing collides |
| duplicate rows do not create a second transaction | the row is recorded `DUPLICATE` on `ImportRow`; no `Transaction` is created |
| rule application unchanged | still the canonical `TransactionCreationService` path (R20) |
| per-row atomicity preserved | unchanged: one row = one `@Transactional` call (R22) |
| `UNIQUE` remains the final race-safe guard | unchanged: two concurrent uploads of the same file both pass the pre-check and one loses at the constraint |
| no new infrastructure | no Spring Batch, no `ON CONFLICT`, no `SKIP LOCKED`, no `Idempotency-Key`, no `IdempotencyRecord`, no mandatory hashing, no Kafka/event architecture — a `Map` counter and string concatenation, both taught |

**The limitation, stated explicitly rather than overclaimed.** The fallback guarantees stable identity
only for **re-importing the same logical statement ordering**. If a source file is arbitrarily
reordered, filtered or reconstructed — rows sorted differently, an earlier row deleted, two
statements merged — the occurrence indices may be assigned differently and the fallback identities
may change. Consequences a mentor must not hide:

- A reordered re-import can insert a row that history already holds (an apparent duplicate), or mask
  one (an apparent loss). The import result report names every row and its outcome, so the delta is
  visible rather than silent.
- **A source-supplied stable transaction id avoids this limitation entirely**, which is exactly why
  Level 1 is *preferred* rather than merely allowed. Where a bank export carries a reference column,
  use it.
- **This is not universal bank-file deduplication and must never be described as such.** It is
  statement-scoped, order-sensitive dedup with a preferred exact path. `referenceId` and `externalId`
  are **0-hit** in `content/` (measured 2026-09-05), so Level 1's field name is a Spendwise
  invention the task must define.

**Corpus limits that constrain this decision — all measured on 2026-09-05, all recorded as gaps
rather than papered over:**

| Measured | Consequence |
|---|---|
| `sourceRef` / `source_ref`: **0 hits anywhere in `content/`** | the whole provenance column is a Spendwise invention; the task must teach it from scratch in its own `constraints` |
| `OCC:`, `occurrenceIndex`, `occurrence`: **all 0-hit in `content/`** | the occurrence counter is likewise wholly invented. What *is* taught is the mechanism it needs — `Map.merge` / `computeIfAbsent` / `getOrDefault` in `day08-blk-27` — so the technique is reachable even though the concept is not cited |
| `parallelStream` **12 hits** (day-12 ×8, day-10 ×4), `.parallel(` 1 (day-10) | the learner has been taught the one thing that silently breaks `occurrenceIndex`. The V0.8 task must forbid parallel parsing in the import path in its `constraints` |
| composite `UNIQUE (a, b)`, `CONSTRAINT … UNIQUE`, `uniqueConstraints`: **all 0-hit** | the corpus's only `UNIQUE` is single-column inline — `email VARCHAR(255) NOT NULL UNIQUE` in `day21-blk-10`'s `V1__init.sql`. ADR-007 / D14 / R22 / Phase 2 §13 all rest on a two-column form the learner has never seen. The V0.8 task must show the exact DDL |
| `DataIntegrityViolationException`: **0 hits corpus-wide** | Phase 2 §13's caller loop cites an untaught type. The task must name and demonstrate it, or catch a taught supertype |
| `existsBy…`: only `existsByEmail`, and only at **day-33** | D14's "taught `existsBy…` pre-check" is weakly supported and lands *after* day-26's import lesson. The pre-check is therefore **optional politeness**, not the guard: the constraint is the guard |
| `MessageDigest.getInstance("SHA-256")` **is** taught (day-24, required exercise) but `Base64`, `HexFormat` and any `bytesToHex` helper are **0-hit** | hashing the fingerprint is *not* used. There is no taught way to render the digest as a string, so a plain concatenated identity string is the only fully-taught option. This is why nothing here is hashed |
| `MultipartFile` at day-26 exposes only `getOriginalFilename()`, `getInputStream()`, `isEmpty()` — no `getSize()`, no `getBytes()`, no `transferTo` | **a whole-file identity is not implementable with what is taught.** Even if file-level dedup were desirable, the learner cannot cheaply obtain file bytes or length twice. Row-level identity is not merely preferable here; it is the only reachable one |

**Not implemented in this pass.** D10.1 is a planning decision. No code, no artifact edit, no DDL is
written; the V0.8 task contracts that carry it are authored in P2.

In **tests**, dedicated fixture builders and direct repository seeding are permitted, for one
purpose only: arranging valid historical state that a scenario needs to exist before the behaviour
under test runs. Tests **must not** bypass the canonical use case when the behaviour under test
*is* transaction creation — a rule-application test, a balance-projection test, a duplicate-
detection test and a transfer test all go through `TransactionCreationService`.

**D11 — Ownership.** Enforced in the service layer, not the controller and not the client. Every
user-owned table carries `user_id` from the migration that creates it. Reads reload by
`(id, userId)`; lists scope by `userId`. A record that exists but belongs to someone else returns
**404, never 403** — 403 confirms the row exists. `SecurityContextHolder` is read in exactly one
class, `CurrentUser`, over `authentication.name` (day-23's taught route), upgradeable to a
principal id later without touching call sites.

Rejected: `@AuthenticationPrincipal` (0-hit corpus-wide, despite the research recommending it at
`docs/SPENDWISE_ARCHITECTURE_RESEARCH.md:860`); trusting a user id embedded in a client-supplied
claim. Note `findByIdAndUserId` appears nowhere in the corpus; the nearest taught shape is
`findByUserId` (day-21), so the `(id, userId)` reload is derived, not copied.

**D12 — Security scope. Required vs optional, corrected.**

*Required for V0.6 to be complete:*

| Requirement | Where taught | Evidence |
|---|---|---|
| password hashing | day-22 | `day22-blk-13`, `PasswordEncoderFactories.createDelegatingPasswordEncoder()` (`content/lessons/day-22.json:255`); `matches(raw, encoded)` not `encode().equals(...)` (`:284`) |
| `SecurityFilterChain` + `HttpSecurity` | day-22 | `day22-blk-8` (`content/lessons/day-22.json:185`) |
| stateless authentication | day-22 | `SessionCreationPolicy.STATELESS`, outcome `:47`, prose `:176`, `:205` |
| JWT **verification** | day-22, day-33 | `oauth2ResourceServer().jwt()` (`day-22.json:185`); `NimbusJwtDecoder.withSecretKey(key).build()` (`content/lessons/day-33.json:276`) |
| a canonical application-issued access JWT | day-33 | `day33-blk-29` (`content/lessons/day-33.json:239`): `ImmutableSecret`, `JWKSource`, `MacAlgorithm`, `JwsHeader`, `JwtClaimsSet`, `JwtEncoder`, `NimbusJwtEncoder`, `SecretKeySpec` |
| ownership enforcement | day-23 | `authentication.name`, `@PreAuthorize` |
| **logout revocation** | day-24 | `content/lessons/day-24.json:246`: *"Nhóm BẮT BUỘC: access token bị từ chối với 401 sau khi logout - chấm theo hành vi quan sát được, không bắt buộc một cách hiện thực cụ thể"*; `StringRedisTemplate` in `day24-blk-16` (`:93`) |

*Optional / extension, and never a completion requirement:*

- refresh-token **rotation** (single-use)
- refresh-token **replay detection**

The frozen curriculum is unambiguous. `content/lessons/day-24.json:246`: *"Nhóm CHƯA CHỐT, KHÔNG
dùng làm điều kiện chấm cho tới khi bộ nguồn của Day 24 có tài liệu tương ứng: refresh-token
rotation (single-use) và phát hiện replay … RefreshTokenService.rotate() ở day24-blk-18 vẫn là khối
TODO minh hoạ/enhancedExercise, không phải yêu cầu để Lab 8 đạt."* Restated at `:266-267`:
*"Refresh-token rotation và phát hiện replay CHƯA CHỐT, KHÔNG nằm trong điều kiện đạt."*

The frozen artifact agrees: V0.6's three acceptance criteria in `content/spendwise-project.json`
mention JWT issuance, backend-enforced ownership and cross-user isolation, and **do not mention
refresh rotation at all**. The reviewed draft made rotation core; that was an upgrade of deferred
curriculum knowledge into a graduation requirement, and it is withdrawn.

Also note two corpus facts that constrain what may be *required* here: no `UserDetailsService`
implementation is ever written in the corpus, and day-33's own `SecurityFilterChain`
(`content/lessons/day-33.json:276`) omits `sessionManagement(...STATELESS)`. Spendwise keeps the
stateless policy because day-22 teaches it as an outcome; it does not inherit day-33's omission.

**D13 — Schema.** Flyway, versioned migrations only, never edited after being applied. `ddl-auto`
is permitted as `update` across day-19/day-20 only — those two lessons contain **zero Flyway**
(the 21 Flyway hits are day-21 ×17, day-29, day-33, day-38 ×2) — and is switched to `validate` by
the V0.5 migration-baseline task, permanently. Money scale, `NOT NULL`, `UNIQUE` and foreign keys
are declared in DDL, not inferred from annotations.

**D14 — Concurrency and idempotency.** `@Version` on `Account` for the balance projection.
`@Lock(PESSIMISTIC_WRITE)` where two accounts must be ordered deterministically (transfer, by
ascending id, to avoid deadlock). The **final** idempotency guard is a `UNIQUE` constraint in a
migration — `(user_id, source_ref)` for imported and recurring rows — with a taught `existsBy…`
pre-check in front of it for the friendly error path.

*Amended 2026-09-05 (final planning reconciliation), two corrections:*

- **`source_ref` must be content-derived for imports, not batch-derived.** A `UNIQUE` constraint is
  only a guard if the same input produces the same key on a second attempt. `IMPORT:<batchId>:<rowNo>`
  did not, because `batchId` is generated per upload — so the constraint could never fire on
  re-import. The canonical form is **`IMPORT:<rowFingerprint>`**; see **D10.1** for the exact
  fingerprint, the accepted collision cost, and the corpus limits.
- **The `existsBy…` pre-check is optional, not load-bearing.** `existsBy` appears in the corpus
  exactly once, as `existsByEmail` at **day-33** — after day-26's import lesson. It is the friendly
  error path only. **The constraint is the guard**, and the caller must handle the constraint
  violation whether or not the pre-check ran.

*Further amended 2026-09-05 (final import-identity correction).* The first bullet above is correct
that identity must not be batch-derived, but its canonical form is superseded. It read
**`IMPORT:<rowFingerprint>`** with an *"accepted collision cost"*; that cost — silently dropping a
second legitimate transaction with identical business fields — is **withdrawn**. The frozen form is
now **two-level**:

- **preferred:** `IMPORT:SRC:<sourceKey>:<accountId>:<normalized sourceTxnId>` when the row carries a
  stable source-provided reference;
- **fallback:** `IMPORT:<baseFingerprint>|OCC:<occurrenceIndex>`, the occurrence index being the
  1-based count of that same base fingerprint within the current statement in source-file order.

Everything else in D14 is unchanged: `(user_id, source_ref)` remains the constraint, it remains the
**final race-safe guard**, and the pre-check remains optional politeness. The one addition is that
the constraint now also has to tolerate two rows of the *same* upload legitimately differing only by
`OCC:` — which it does, because they are different strings. See **D10.1**, including the
reordering limitation the fallback carries.

Rejected: `Idempotency-Key` headers, `ON CONFLICT`, `SKIP LOCKED`, a separate `IdempotencyRecord`
table, SHA-256 dedup keys — every one 0-hit. Day-21 teaches `UNIQUE` in `V1__init.sql`, which is
the mechanism used — **but only in its single-column inline form** (`email VARCHAR(255) NOT NULL
UNIQUE`, `day21-blk-10`). Composite `UNIQUE (a, b)`, `CONSTRAINT … UNIQUE` and JPA
`uniqueConstraints` are **all 0-hit**, so the two-column constraint this decision depends on is a
documented extension of the taught form and the V0.8 task must spell out its DDL (§11 known gaps).

**D15 — Build order and runtime dependency flow are two different things.**

*Build order* (development sequence only, no runtime meaning):
Transaction → Rule → Budget → Recurring → Import → Reporting.

*Runtime dependency flow* (what actually calls what):

```
Manual REST ─┐
Recurring   ─┼──►  TransactionCreationService  ──►  deterministic Rule evaluation
Import      ─┘                │
                              ├──►  Transaction persistence
                              └──►  Account balance projection update
Budget          ──reads──►  persisted transaction data
Report/Dashboard──reads──►  persisted transaction + budget data
```

Rules, no cycles:

- **R-DEP-1** Recurring and Import **are allowed** to invoke `TransactionCreationService`. That is
  the intended direction, not a violation.
- **R-DEP-2** `TransactionCreationService` invokes deterministic rule evaluation and nothing else
  that writes.
- **R-DEP-3** Budget, Report and Dashboard are **read-only consumers of persisted data**. They
  never call a creation path and nothing calls them to produce a write.
- **R-DEP-4** The rule engine never calls Budget, Recurring, Import or Report.
- **R-DEP-5** No feature package imports `imports` or `recurring` except `config`.
- **R-DEP-6** The resulting graph is acyclic. Any proposed edge that creates a cycle is an
  `ARCHITECTURE_CHANGE_REQUIRED`.

**The draft's rule "an engine may call *down* the spine, never up" is deleted.** It contradicted
D10: it forbade exactly the calls D10 requires, since Recurring and Import sit *later* in the build
order than Transaction and must nevertheless call into it.

**D16 — Cache, async, scheduled.**

- **Cache backend:** `ConcurrentMapCacheManager` is the configuration Spendwise runs, matching
  day-34's capstone cache (`day34-blk-11`, `day34-blk-13`) and day-30's reference compose file,
  which states outright that Redis is not required (`content/lessons/day-30.json:204`). The Redis
  backend (`RedisCacheManager`, `RedisCacheConfiguration`, `entryTtl`) is taught in day-25 and is
  an **optional** V0.9 upgrade behind the same `@Cacheable` annotations — a configuration change,
  not an architecture change. This corrects the draft's Redis-is-canonical claim.
- **What may be cached:** reference data only. **No money value, no balance, no budget figure, no
  report total is ever cached.** The cached-stale-balance failure mode is not worth the milliseconds.
  *Amended 2026-09-05 (final planning reconciliation) — this bullet read "category lists, rule sets,
  FX quotes" without saying when each becomes cacheable, which let day-25 appear to cache a Rule
  engine that does not exist yet.* The cacheable set is **release-gated**:
  - **Category / reference lists — cacheable from day-25 (V0.9's `task-reference-data-cache`).**
    Categories exist from V0.1, so the subject of the cache is real at day-25 and this is the only
    thing that task caches.
  - **Rule lists — later reuse, not a day-25 subject.** The V0.7 Rule engine does not exist at
    day-25. Once V0.7 has shipped, rule lists become cacheable behind the *same* `@Cacheable` /
    `@CacheEvict` annotations with no new mechanism — that is reuse of a taught technique, not a new
    capability, and it must not be phrased as though Rule already existed on day-25.
  - **FX quotes — from V0.9's `task-exchange-rate-client`,** which is where they first exist.
- **Eviction:** `@CacheEvict` on the writes that invalidate the reference data. Day-25 warns that
  eviction runs *before* commit (`day25-blk-24`), so eviction is placed on the outermost service
  method, and anything genuinely commit-ordered is done after the transaction returns.
- **Async:** `@Async` for side effects with **no HTTP contract** — notification, batch-finished
  logging. Dispatched only after commit (day-27's rule, `content/lessons/day-27.json:278`). Java 17
  has no virtual threads and day-25 says so (`content/lessons/day-25.json:278`: *"Java 17 chưa có
  virtual thread (đó là Java 21)"*), so a bounded `ThreadPoolTaskExecutor` with an
  `AsyncUncaughtExceptionHandler` is configured explicitly.
- **Scheduled:** `@Scheduled` with an explicit `zone`, because the default is the JVM timezone
  (`content/lessons/day-25.json:296`). Two jobs: recurring generation (V0.7+) and **balance
  reconciliation** (from V0.5's invariant onward). `fixedDelay` non-overlap holds only for
  consecutive runs of one method on one scheduler; multi-instance needs a distributed lock, which
  Spendwise does not attempt (`ShedLock` is named 4× in day-25 and never configured).
- **No `202 Accepted` API.** Dropped as a project goal — `202` is 0-hit corpus-wide. Async import
  with status polling may exist as a future extension; it is not a graduation requirement.

**D17 — AI is advisory only.** Feature-flagged off by default. AI may *suggest* a category and
*narrate* numbers the backend already computed. AI never computes a monetary figure, never queries
the database, never transfers money, never edits or deletes anything. An accepted suggestion
executes the ordinary `TransactionCreationService` write path with a normal audit trail.

**D18 — Testing tiers start where taught.**

| Tier | From | Evidence |
|---|---|---|
| domain invariant tests, plain JUnit | V0.1 | day-03/day-09 already use JUnit |
| JUnit 5 structure, `assertAll`, Mockito | day-28 | `day28-blk-3`, `day28-blk-4`, `Mockito` 10 hits all in day-28 |
| MVC slice `@WebMvcTest` + `MockMvc` | day-28 | `day28-blk-6/7`; `day28-blk-25` warns it does *not* load `@Service`/`@Repository` |
| JPA slice `@DataJpaTest` | day-28 | `day28-blk-9/10`; `day28-blk-28` warns auto-H2 ≠ PostgreSQL |
| **Testcontainers integration** | **day-29** | day-28's Testcontainers section is a single `note` block (`day28-blk-13`) stating no resource describes it; day-29 has the real code — `PostgreSQLContainer<>("postgres:16-alpine")`, `@ServiceConnection`, `@DynamicPropertySource` (`day29-blk-13`) |
| JaCoCo **report generated and read** | day-30 | `content/lessons/day-30.json:252`: *"Chạy mvn verify, mở report tại target/site/jacoco/index.html"* |

**No coverage percentage is a requirement.** Percentage counts across `content/`: `75%` 17 hits,
`80%` 11, `100%` 1, and **`70%` = 0, `90%` = 0** — so the research's *"Coverage target: ≥ 70% line,
≥ 90% cho `common/money`, `budget/`, `recurring/`, `rule/`"*
(`docs/SPENDWISE_ARCHITECTURE_RESEARCH.md:1143`) is entirely invented and is rejected. The only
75% in scope is day-30's Lab 10 item, and day-30 disowns it as a grading condition:
`content/lessons/day-30.json:253` — *"CHƯA CHỐT - không dùng làm điều kiện chấm ở bài này … Mức
quan sát duy nhất áp dụng ở đây: **report được sinh ra và mở được.**"* — with
`content/lessons/day-30.json:120` recording JaCoCo threshold configuration as *"khoảng trống kiến
thức thật sự"*. Day-28 supplies the replacement pedagogy: *"con số phần trăm là chỉ dấu, không phải
mục tiêu. 100% dòng được chạy qua vẫn có thể không có một assertion nào ý nghĩa, còn 60% tập trung
vào logic nghiệp vụ cốt lõi có thể bảo vệ tốt hơn nhiều"* (`content/lessons/day-28.json:349`).

What is required instead: named financial invariants, critical business flows, ownership/security
boundaries, persistence behaviour, and failure scenarios — enumerated in Phase 2 §9.

**D19 — Production shape.** One Spring Boot jar, PostgreSQL, optional Redis, Docker Compose for
local dependencies. Actuator health + metrics, structured JSON logging with an MDC `traceId`
cleared in a `finally` block (`day29-blk-25`), springdoc OpenAPI. No microservices, no Kafka, no
Kubernetes — all three are in `product.outOfScope`.

**D20 — Boundary enforcement is a review checklist, not a tool.** Five greps: `jakarta.servlet` or
`org.springframework.web` inside a domain class; `org.springframework.security` inside a domain
class; `ResponseEntity` in a service; `@Transactional` on a controller or a `private` method; a
`new Transaction(` outside `TransactionCreationService` or a test fixture. Rejected: ArchUnit and
Spring Modulith, both 0-hit.

---

## 3. Architecture Constitution

Twenty-six rules. Each is specific, falsifiable, and consistent with every other. Violating one is
not a style disagreement; it is drift. The draft's three internal contradictions (R6 vs D5, R10 vs
D2, R16 vs test fixtures) are resolved here rather than deferred to implementation.

**Money and numbers**

- **R1** Money is `BigDecimal` scale 2 from input to storage to output. `double`/`float` never touch
  money, including to satisfy a collector signature. Scale 2 is the Spendwise V1.0 precision
  convention, not a universal ISO-4217 claim.
- **R2** Monetary comparison is `compareTo(...) == 0`. `BigDecimal.equals` is never used for
  monetary equality.
- **R3** Money scale and precision are declared in migration DDL (`NUMERIC(19,2)`), not in
  `@Column`.
- **R4** Cross-currency arithmetic throws. FX is display-only conversion in the report layer and
  never produces a ledger entry.
- **R5** Construction normalizes to scale 2 HALF_UP; division requires an explicit scale +
  `RoundingMode` at the call site; multiplication rounds once at the end of the expression.

**Truth**

- **R6** `Transaction` rows are the sole source of financial truth.
- **R7** `Transaction.amount` is always positive. Direction is `Transaction.type`, and the signed
  effect is exactly: `INCOME +`, `EXPENSE −`, `TRANSFER_IN +`, `TRANSFER_OUT −`.
- **R8** `Account.balance` is a stored projection, written only inside the transaction that writes
  the `Transaction` row, guarded by `@Version`, permanently subject to
  `balance == openingBalance + Σ signedEffect(t)`.
- **R9** `Account.openingBalance` is immutable after account creation.
- **R10** `Budget.spent` / `remaining` / `percentage` / `status` and every report and dashboard
  figure are derived at read time and never stored.
- **R11** No money value, balance, budget figure or report total is ever cached.

**Time**

- **R12** System events are `Instant`/`TIMESTAMPTZ`; economic dates are `LocalDate`/`DATE`; period
  keys are `YearMonth`-shaped `VARCHAR(7)`. Bare `LocalDateTime` is forbidden in persisted state.
  This rests on Hibernate 6, not on Jakarta Persistence 3.1.

**Structure**

- **R13** Package by feature under `com.spendwise`; layered inside the feature;
  `controller → service → repository`, `service → domain`. The import package is `imports`.
- **R14** A domain class MAY import the JDK, `com.spendwise.shared`, and `jakarta.persistence`
  mapping annotations. It MUST NOT import Spring MVC, Spring Security, Spring service/application
  types, repository implementations, or any infrastructure client.
- **R15** One class per concept. No domain/entity twin, no mapper between them. JPA annotations are
  added to the existing class at V0.5. After V0.5 the domain is **not** framework-pure, by design.
- **R16** No entity and no VO crosses the HTTP boundary. Request and response `record`s only.
- **R17** Services never return `ResponseEntity`; controllers never contain business logic;
  `@RestControllerAdvice` is the single error-translation point.

**Writes**

- **R18** `@Transactional` on public service methods only — never a controller, repository, private
  or `final` method. Read paths are `readOnly = true`.
- **R19** No external call, file I/O or `@Async` dispatch inside a transaction.
- **R20** **In production code**, every `Transaction` is created by
  `TransactionCreationService.create(command)` — manual, recurring and imported alike — and carries
  a `sourceRef`. Tests MAY seed history via fixture builders or the repository, but MUST NOT bypass
  the canonical use case when the behaviour under test is transaction creation itself.
- **R21** A transfer is one `@Transactional` unit that creates a linked `TRANSFER_OUT` and
  `TRANSFER_IN` sharing one `transferRef` and updates both balance projections. Balances are never
  mutated without corresponding transaction rows. There is no `Transfer` aggregate.
- **R22** An import batch is not atomic; **each row is**. Every batch reaches a terminal state and
  every row is exactly one of `OK` / `DUPLICATE` / `FAILED`. A row's identity is its **row identity**
  as defined in D10.1 — a source-provided reference where one exists, otherwise the base content
  fingerprint **plus its 1-based occurrence index within the statement** — never its `ImportBatch` PK.
  So re-importing the same statement is deterministic, `DUPLICATE` is reachable on the second upload,
  and two *legitimate* rows with identical business fields remain two distinct transactions
  (D10.1, rewritten 2026-09-05 by the final import-identity correction; the earlier wording read
  *"A row's identity is its **content fingerprint**, not its position in a batch"*, which collapsed
  those two rows into one). `batchId` and `rowNo` are reporting data only and never participate in
  identity.
- **R22, second clause, added 2026-09-05 with D10.1's fallback model: the import parse loop is
  sequential, in source-file order.** `occurrenceIndex` is order-derived, so `parallelStream()` /
  `.parallel()` anywhere in the import path makes identity nondeterministic. Sequential `Files.lines`
  consumption is required; parallel consumption is an `ARCHITECTURE_CHANGE_REQUIRED` (§10). This is a
  clause of R22, **not a new rule id** — the rule set stays at 26, and `buildSteps.architectureRules`
  is validated against `^R\d{1,2}$` (Phase 2 §11), which an id like `R22a` would fail.


**Ownership**

- **R23** The JWT carries identity only — no authorization data that the server does not
  re-verify.
- **R24** `SecurityContextHolder` is read in exactly one class. Ownership is enforced in the service
  layer by reloading with the owner id and by scoping every list query. A record owned by someone
  else returns 404, never 403.
- **R25** Every user-owned table has a `user_id` column and scoped queries from the migration that
  creates it.

**Schema, toolchain and knowledge**

- **R26** Migrations own the schema; `ddl-auto: validate` from the V0.5 baseline task onward;
  applied migrations are never edited. The toolchain (§8) is pinned; no release after V0.6 may
  require a technique not taught by Day 30.

R26's second clause is checkable and has been checked. V0.7 needs `@Query`/`GROUP BY` (day-21),
`@Version` (day-20), `@Scheduled`/`@Cacheable` (day-25), a new Flyway migration (day-21), and
`BigDecimal.divide` (a named gap, §11). V0.8 needs `MultipartFile` and CSV escaping (day-26),
per-row transactions and `REQUIRES_NEW` (day-20), unique-constraint DDL (day-21), `@Async`
(day-25). V0.9 needs Testcontainers (day-29), Actuator/springdoc/MDC (day-29), Docker (day-29/30),
`WebClient` + retry (day-26). V1.0 needs documentation and `WebClient`. **Zero new techniques after
Day 30** — with one deliberate exception, the canonical `JwtEncoder` at day-33, which is why §7
exists.

---

## 4. ADR set

Seventeen ADRs. 001–016 are the draft's, updated in place — no duplicates were created. 017 is new
and covers the frozen toolchain. No ADR was written for a trivial implementation detail.

Each records: Decision / Reason / Rejected alternative / Consequence / When reconsideration is
allowed.

| ADR | Decision | Rejected | Deciding evidence | Reconsider when |
|---|---|---|---|---|
| **001** | `Money` VO, two plain columns, scale 2, DDL-declared, labelled the Spendwise V1.0 precision convention | `@Embeddable`; `AttributeConverter`; `@Column(precision/scale)`; `NUMERIC(19,4)`; JSR-354 | all four mechanisms 0-hit; raw DDL taught day-21 | a real currency with ≠2 minor units enters scope |
| **002** | `Instant` for events, `LocalDate` for economic dates — on Hibernate-6 grounds, **not** JPA 3.1 portability | `OffsetDateTime` (day-19's explicit advice); `LocalDateTime`; `ZoneId` arithmetic | `day-19.json:172`/`:182` conflict acknowledged; day-21 persists `Instant` with `@CreatedDate`; `ZoneId` 0-hit | the project must run on a non-Hibernate provider |
| **003** | Signed-effect ledger: transactions are truth, `balance = openingBalance + Σ signedEffect`, versioned projection, budget figures derived | pure derivation (kills the day-20 concurrency lesson); naked stored balance (corrupts) | master plan §8 leaves it open; day-20 teaches `@Version` on a contended counter; day-21 teaches `SUM`/`GROUP BY` | never, while `Money` and `Transaction` shapes hold |
| **004** | One class per concept; JPA annotations added in place at V0.5; business-centric entities, purity claim withdrawn | separate rich domain + anemic entity + mappers | `MapStruct` 0-hit; day-19's template shows `protected Product() {}` | a second persistence technology is added |
| **005** | Hand-written repository interface at V0.2, re-declared `JpaRepository` at V0.5, in-memory impl deleted | permanent port/adapter pair | `hexagonal` 0-hit; `@DataJpaTest` + Testcontainers give the testability | a non-JPA store is added |
| **006** | **Direct service calls, no event architecture** | `ApplicationEventPublisher` + `@TransactionalEventListener(AFTER_COMMIT)`; outbox; Kafka | `@TransactionalEventListener` 1 hit (an exercise hint); publisher/listener/event class 0; Kafka in `outOfScope` | a second deployable consumes Spendwise writes |
| **007** | `UNIQUE` migration constraint on `(user_id, source_ref)` as the final idempotency guard, with `source_ref` **row-derived** for imports — **preferred:** a stable source-provided reference (`IMPORT:SRC:<sourceKey>:<accountId>:<sourceTxnId>`); **fallback:** `IMPORT:<baseFingerprint>\|OCC:<occurrenceIndex>`, the index counted per statement in source-file order (D10.1) — so the same statement re-imported yields the same keys *and* two identical legitimate rows stay two transactions; the `existsBy` pre-check in front is the friendly error path only, **not** the guard — *amended 2026-09-05, twice* | `Idempotency-Key`; `ON CONFLICT`; `SKIP LOCKED`; `IdempotencyRecord`; SHA-256 keys; **`IMPORT:<batchId>:<rowNo>`, which is not stable across re-import**; **a bare content fingerprint with no occurrence index, which silently collapses two legitimate identical rows into one — withdrawn 2026-09-05** | all 0-hit; day-21 teaches `UNIQUE` in `V1__init.sql` — **single-column inline only**; composite `UNIQUE (a, b)`, `CONSTRAINT … UNIQUE` and `uniqueConstraints` are 0-hit, so the two-column form is a documented extension; `existsBy` is `existsByEmail` at day-33 only; the occurrence counter's mechanism (`Map.merge`/`computeIfAbsent`/`getOrDefault`) is taught in one block, `day08-blk-27` | a client needs at-most-once POST semantics, **or** a source format arrives whose rows can be reordered between imports and carry no reference id (the fallback's stated limitation) |
| **008** | Issuance behind a one-implementation `TokenIssuer`; seam at day-22→24, canonical signing knowledge at day-33, **required task after day-36** | issuance as a day-24 obligation with a "syntax hint"; day-33 work left optional; a temporary unsafe signer rewritten later | day-22 defers `JwtEncoder` to day-33 (`day-22.json:78`); all 8 `TokenIssuer` hits are in day-33; `day33-blk-33` carries the HS256 ≥256-bit warning | the curriculum moves issuance earlier |
| **009** | One `CurrentUser` seam over `authentication.name` | `@AuthenticationPrincipal`; trusting a client-supplied id claim | `@AuthenticationPrincipal` 0-hit; `authentication.name` is day-23's route; no `UserDetailsService` is ever implemented in the corpus | a principal id must be read in more than one place |
| **010** | **`ConcurrentMapCacheManager` is what Spendwise runs**; Redis is an optional V0.9 upgrade behind the same annotations | Redis-as-canonical (the draft's position); Caffeine-first (the research's) | `day-30.json:204` states Redis is not required; day-34 caches with `ConcurrentMapCacheManager`; `redis:7-alpine` appears once, as an answer key; `Caffeine` 1 hit | multi-instance deployment makes a shared cache necessary |
| **011** | Day-25 owns reference-data cache, scheduled reconciliation and fire-and-forget async — not dashboard cache or recurring scheduling. **The reference data day-25 caches is Category/reference lists only** — rule-list caching is later reuse of the same annotations after V0.7 ships, and FX quotes arrive with `task-exchange-rate-client` (*amended 2026-09-05, see D16*) | attaching V0.7-dependent tasks to a day-25 lesson; **wording that implies a Rule engine exists at day-25** | the dashboard and the recurring engine do not exist at day-25; **neither does Rule — it is V0.7**; the ADR-003 reconciliation invariant does, and Category exists from V0.1 | the release order changes |
| **012** | `@Async` for side effects with no HTTP contract; **no `202 Accepted` API** | async import with status polling as a required goal | `202` 0-hit; day-27's taught model is async-after-commit; the artifact already marks async import optional | a real long-running import appears with a real client |
| **013** | `ddl-auto: update` only across day-19/20, killed by the V0.5 baseline task; `validate` thereafter | requiring hand-written DDL at day-19 (untaught); hiding the gap | day-19 and day-20 contain zero Flyway; the 21 Flyway hits start at day-21 | never |
| **014** | Testing tiers start where taught: invariants V0.1, JUnit/slice day-28, Testcontainers day-**29**, JaCoCo report-not-gate day-30 | Testcontainers at day-28; a 70/75/90% coverage gate | day-28 defers Testcontainers to a bare note; `day-30.json:253` marks 75% `"CHƯA CHỐT"`; `70%`/`90%` are 0-hit | the curriculum adds a coverage resource |
| **015** | Boundaries enforced by a five-grep review checklist | ArchUnit; Spring Modulith | both 0-hit | the codebase outgrows manual review |
| **016** | AI advisory-only, flag-off-by-default; accepted suggestions execute the ordinary write path | AI with any write authority; AI computing money | master plan §10 | never |
| **017** | **Toolchain frozen** (§8): Java 17, Maven + Wrapper, PostgreSQL 16, root `com.spendwise`. **The Spring Boot version is NOT pinned by this ADR** — it carries `SPRING_BOOT_EXACT_PIN_PENDING` (§8.1) and is a hard prerequisite of **`task-spring-bootstrap` (V0.3)**, *not* of `task-project-foundation` (V0.1), which is pure Java with no Spring dependency — *amended 2026-09-05, see §8.1* | an unpinned "3.x" *at initialization time*; Gradle; Java 21; opportunistic version bumps | `--release 17` enforced by `tools/validate_lessons.py:1005`; identical `"baseline"` string in all 39 lesson files (40 records); Gradle 0-hit repo-wide; `postgres:16*` is the only tag; 3.4-dated features in day-28/day-29 — but Spring Security `6.5`/`6.5.x` is the only version-pinned Spring doc path in the corpus, and 6.5 ships with Boot 3.5, not 3.4; V0.1's own acceptance criterion in `content/spendwise-project.json` reads *"No dependency on Spring, database, or REST"* | an explicit decision under §10, never opportunistically |

---

## 5. V0.1 → V1.0 Evolution Contract

Ten releases, seven fields each. The release spine is frozen by
`tools/validate_project.py` — `EXPECTED_RELEASES` pins id + version at each of ten positions and
`_validate_releases` (`:176`, `:191-198`) rejects any addition, rename or reorder. Nothing below
changes that spine.

Field order per release: **Problem → Capability → Architecture change → Knowledge prerequisites →
Project-artifact prerequisites → Invariants introduced → Done when.**

### V0.1 Java Domain — 6 tasks (6 required)

- **Problem.** There is no code and no repository. Money must be represented correctly before
  anything else exists, because every later layer inherits the representation.
- **Capability.** `Account`, `Money`, `Transaction`, `Category` exist as plain Java with enforced
  invariants. `main()` prints a balance.
- **Architecture change.** From nothing to a single `domain` layer. `arch-v0-1`, 1 layer.
- **Knowledge prerequisites.** day-01 (BigDecimal, wrappers), day-02, day-04 (encapsulation,
  constructor validation), day-07 (enum).
- **Project-artifact prerequisites.** **None** — this is the empty-project boundary. The repository,
  the Maven project, the package root and the runnable `main()` are *created by this release*, by a
  dedicated foundation task (see §9 and Phase 2 §8).
- **Invariants introduced.** R1–R5 (money), R7 (positive amount + typed direction), R9
  (`openingBalance` immutable), R13/R14/R15 (structure).
- **Done when.** `mvn test` runs; an invalid `Account` or negative `Transaction.amount` throws;
  `double` appears nowhere; nothing imports Spring.

### V0.2 Java Application — 5 tasks (5 required)

- **Problem.** Objects exist but nothing stores, searches or aggregates them.
- **Capability.** In-memory repository, `TransactionCreationService`, category/month aggregation,
  CSV read/write.
- **Architecture change.** 1 layer → 4 (`app → service → repository → domain`). `arch-v0-2`.
- **Knowledge prerequisites.** day-07 (interface, DIP), day-08 (generics, collections, exceptions),
  day-10 (stream/collector), day-11 (NIO.2 `Files.lines`, charset, path-traversal).
- **Project-artifact prerequisites.** V0.1 domain classes.
- **Invariants introduced.** R20 (canonical creation path, from the first service), R6 (transactions
  are truth), R8 (projection with the invariant, enforced in memory first).
- **Done when.** Aggregation totals are `BigDecimal` produced by `reduce(BigDecimal.ZERO,
  BigDecimal::add)`; a round-trip CSV write→read preserves every amount exactly; the invariant
  `balance == openingBalance + Σ signedEffect` holds after a random sequence of creates.

### V0.3 Spring Boot Core — 3 tasks (2 required, 1 optional)

> **Amended by the final planning reconciliation, 2026-09-05.** An earlier revision read *"4 tasks
> (3 required, 1 optional)"* and added `task-actuator-baseline` here. That task is **removed** —
> Actuator is 0-hit in day-13 and day-14, is taught at day-29, and the artifact files it exclusively
> under V0.9. V0.3 therefore keeps its baseline shape. See §9's delta list and the reconciliation
> report `docs/report/2026-09-05-spendwise-final-reconciliation-report.md`.

- **Problem.** The application is a `main()`; it cannot be configured, wired or deployed.
- **Capability.** Boots on Spring Boot; services and repositories are beans; the domain is reused
  **unchanged**.
- **Architecture change.** Same four layers, now inside the Spring container. `arch-v0-3`.
- **Knowledge prerequisites.** day-13 (Boot fundamentals, bean lifecycle), day-14 (DI,
  configuration, profiles).
- **Project-artifact prerequisites.** V0.2 service + repository interfaces.
- **Invariants introduced.** R18 (`@Transactional` placement rules, stated before there is a
  database so the rule is learned before it can be violated).
- **Done when.** The app starts; not one domain class was edited; business logic was not rewritten
  because of the migration.

### V0.4 REST API — 6 tasks (6 required)

> **Amended by the final planning reconciliation, 2026-09-05.** An earlier revision read *"5 tasks
> (5 required)"*. That number was wrong against its own id list: `task-rest-controllers` is retired
> and split into three endpoint tasks, and `task-dto-mapping`, `task-bean-validation`,
> `task-error-handling-advice` are all kept — 3 + 3 = **6**, a net **+2** over the baseline 4.

- **Problem.** Only a developer can run it.
- **Capability.** HTTP endpoints for account, transaction, category with DTOs, bean validation and
  `ProblemDetail` errors.
- **Architecture change.** + `controller` layer. `arch-v0-4`.
- **Knowledge prerequisites.** day-16 (controller, request/response), day-17 (validation,
  `@RestControllerAdvice`, `ProblemDetail`).
- **Project-artifact prerequisites.** V0.3 beans.
- **Invariants introduced.** R16 (no entity/VO on the wire), R17 (no `ResponseEntity` in services,
  single advice).
- **Done when.** A malformed request returns a `ProblemDetail` with field errors; no entity appears
  in any JSON payload; no controller touches a repository.

### V0.5 Persistence — 7 tasks (6 required, 1 optional)

- **Problem.** Restart loses everything, and a transfer can half-succeed.
- **Capability.** PostgreSQL via Spring Data JPA; Flyway baseline; atomic transfer.
- **Architecture change.** + `database`; the in-memory repository is **deleted**. `arch-v0-5`,
  5 layers.
- **Knowledge prerequisites.** day-19 (entity design, relationships), day-20 (query,
  `@Transactional`, `@Version`, `REQUIRES_NEW`), day-21 (Flyway, `UNIQUE`, `SUM`/`GROUP BY`).
- **Project-artifact prerequisites.** V0.4 API + V0.2 repository interfaces.
- **Invariants introduced.** R3 (DDL owns scale), R8 (`@Version` on the projection), R12
  (`TIMESTAMPTZ`/`DATE`), R21 (transfer semantics), R26 (`ddl-auto: validate`).
- **Done when.** Data survives restart; a transfer of 500 000 moves both balances and writes exactly
  two linked rows sharing a `transferRef`; a forced failure mid-transfer leaves both balances and
  both row counts unchanged; `ddl-auto` is `validate`.

### V0.6 Security — 6 tasks (5 required, 1 optional), one of the 5 executed post-capstone

> **Clarified by the final planning reconciliation, 2026-09-05.** This header read *"6 tasks (5
> required, 1 optional) **+ 1 post-capstone required task**"*, which parses as **7**. It is **6**.
> `task-canonical-token-issuer` is one of the five required tasks, not a seventh — only its *execution
> window* is after day-36, which is a scheduling fact, not an extra slot. Phase 2 §2's V0.6 table
> lists exactly six ids (five ✔, one ✗) and §9's per-release row has always been 6.

- **Problem.** Every user sees every row.
- **Capability.** Register/login, hashed passwords, stateless JWT-verified requests, service-layer
  ownership, logout revocation.
- **Architecture change.** + `security` filter layer; `user_id` on every owned table. `arch-v0-6`,
  6 layers.
- **Knowledge prerequisites.** day-22 (hashing, `SecurityFilterChain`, STATELESS, JWT
  verification), day-23 (`@PreAuthorize`, `authentication.name`, JOIN FETCH), day-24 (logout
  revocation) — **and day-33 for canonical issuance**, which is why the issuance task executes
  after day-36 (§7).
- **Project-artifact prerequisites.** V0.5 persistence (a `user_id` column needs a migration).
- **Invariants introduced.** R23 (identity-only token), R24 (single `SecurityContextHolder` reader,
  404-not-403), R25 (`user_id` from the creating migration).
- **Done when.** User A gets 404 for User B's account; an access token is rejected with 401 after
  logout; passwords verify via `matches(...)`; **and, after day-36**, the token is signed by the
  canonical `NimbusJwtEncoder`-backed `TokenIssuer` with a ≥32-byte secret.
- **Not required.** Refresh-token rotation; replay detection (`content/lessons/day-24.json:246`).

### V0.7 Business Engine — 8 tasks (7 required, 1 optional)

- **Problem.** It is still CRUD. No budget, no recurring, no categorization rules.
- **Capability.** Budget with limit/spent/remaining/percentage/status per category+period;
  recurring transactions with a next-due date; a priority-ordered rule engine; the dashboard.
- **Architecture change.** + domain-service tier inside `budget`/`recurring`/`rule`. `arch-v0-7`.
- **Knowledge prerequisites.** day-05 (Strategy/polymorphism → rule implementations), day-20/21
  (`@Query`, `GROUP BY`, aggregation), day-25 (`@Scheduled` for generation).
- **Project-artifact prerequisites.** V0.5 persistence, V0.6 ownership, and
  `TransactionCreationService` — the recurring generator calls it (R-DEP-1).
- **Invariants introduced.** R10 (budget figures derived, never stored), R-DEP-3/R-DEP-4 (read-only
  consumers, rule engine calls nothing).
- **Done when.** A budget overrun changes no transaction; the same recurring period never generates
  twice; rules apply in priority order deterministically; the dashboard's numbers equal a
  hand-computed `SUM`.

### V0.8 Data Processing — 8 tasks (7 required, 1 optional)

- **Problem.** Real statement data cannot get in, and importing twice would duplicate.
- **Capability.** CSV upload → `ImportBatch` with per-row outcomes; duplicate detection; CSV export.
- **Architecture change.** + `imports` pipeline (parse → validate → dedup → create → record).
  `arch-v0-8`.
- **Knowledge prerequisites.** day-11/day-12 (`Files.lines`, large-file aggregation), day-26
  (`MultipartFile`, CSV escaping), day-20 (`REQUIRES_NEW`), day-21 (`UNIQUE`), **day-08
  (`Map.merge`/`computeIfAbsent`/`getOrDefault`, `day08-blk-27` — the occurrence counter, added
  2026-09-05 with D10.1)**.
- **Project-artifact prerequisites.** V0.7 rule engine (import applies rules) and
  `TransactionCreationService`.
- **Invariants introduced.** R22 (**per-row atomicity**, batch not atomic; **plus the sequential-parse
  clause** — no `parallelStream` in the import path, because `occurrenceIndex` is order-derived), R7
  (a CSV negative amount becomes type + positive amount, never a negative stored amount).
- **Done when.** A 100-row file with 3 malformed rows yields a `COMPLETED_WITH_ERRORS` batch, 97
  committed transactions and 3 `FAILED` rows carrying row numbers and reasons; re-importing the same
  file adds 0 transactions and 97 `DUPLICATE` rows. **And, added 2026-09-05 by the final
  import-identity correction:** a file containing **two byte-identical data rows** (same account,
  date, direction, amount, description, no source reference) imports **2** transactions, not 1 —
  `OCC:1` and `OCC:2` — and re-importing that same file adds **0** and reports **2** `DUPLICATE`
  rows. Where the file carries a source reference column, identity comes from it instead (D10.1
  Level 1) and the same two assertions hold.
- **Retry and re-import acceptance criteria** (explicit, 2026-09-05): re-uploading a *partially*
  imported statement turns previously-successful rows into `DUPLICATE` and inserts previously-`FAILED`
  rows normally, with no dependence on the `ImportBatch` PK; a `DUPLICATE` row creates no second
  `Transaction`; rule application on the inserted rows still goes through
  `TransactionCreationService` (R20); the `UNIQUE (user_id, source_ref)` constraint is the final
  race-safe guard under two concurrent uploads of the same file. **Not claimed:** stability when the
  source file is arbitrarily reordered or reconstructed and carries no source reference — see D10.1's
  stated limitation.
- **Not required.** Async import with `202 Accepted` — dropped as a goal (ADR-012). The artifact
  already marks it optional.

### V0.9 Production Engineering — 9 tasks (8 required, 1 optional)

- **Problem.** No tests worth the name, no observability, no reproducible run, no FX data.
- **Capability.** Reference-data cache; scheduled reconciliation + recurring generation; external FX
  via `WebClient` with retry; unit + slice + Testcontainers suites; OpenAPI; structured logging with
  `traceId`; Actuator; Docker Compose.
- **Architecture change.** + cache, scheduler, external client, container packaging. `arch-v0-9`,
  8 layers.
- **Knowledge prerequisites.** day-25 (cache/async/scheduled), day-26 (`WebClient`, retry), day-28
  (JUnit 5, `@WebMvcTest`, `@DataJpaTest`), day-29 (**Testcontainers**, springdoc, MDC, Actuator),
  day-30 (Docker Compose, JaCoCo report).
- **Project-artifact prerequisites.** everything through V0.8.
- **Invariants introduced.** R11 (no money value cached — enforced here, where the temptation
  starts), R19 (no external call inside a transaction).
- **Done when.** Every named invariant in Phase 2 §9 has a test; the Testcontainers suite runs
  against `postgres:16-alpine`; `/actuator/health` reports database status; a JaCoCo report is
  generated and read (**no percentage gate**); `docker compose up` starts app + database.

### V1.0 Smart Finance — 6 tasks (4 required, 2 optional)

- **Problem.** Core behaviour needs stabilizing, and there is one safe place for AI.
- **Capability.** Hardening pass; portfolio README + demo; optional AI category suggestion; optional
  AI monthly insight.
- **Architecture change.** + an advisory `ai` package with no write authority. `arch-v1-0`.
- **Knowledge prerequisites.** day-26/day-29 (`WebClient` to an LLM, documentation), day-36
  (defense/presentation).
- **Project-artifact prerequisites.** V0.9 complete.
- **Invariants introduced.** none new — V1.0 exists to prove the previous twenty-six hold.
- **Done when.** The reconciliation job reports zero drift on a seeded history; every defense
  question in Phase 2 §12 is answerable from code; AI is off by default, suggests only, and an
  accepted suggestion is indistinguishable in the audit trail from a manual create.

---

## 6. Course Knowledge Timing Matrix

Earliest lesson at which each technique may be *required*. A task scheduled before this bound would
require the learner to invent the technique.

| Technique | Earliest | Evidence |
|---|---|---|
| `BigDecimal`, wrapper vs primitive | day-01 | `lessonMap.day-01` is `direct v0-1 feat-money` |
| encapsulation, constructor validation | day-04 | `day-04` maps 4 V0.1 tasks |
| interface + DIP, enum | day-07 | `lessonMap.day-07` `future v0-2` `task-repository-interface` |
| generics, collections, exceptions | day-08 | day-08 is `theory` |
| stream/collector aggregation | day-10 | `groupingBy` 10, `toMap` 8, `summingDouble` 3, `reduce` 2, `BigDecimal` **0** |
| `Files.lines`, charset, path-traversal | day-11 | `lessonMap.day-11` `future v0-8 feat-import` |
| large-CSV pipeline shape | day-12 | `lessonMap.day-12` `future v0-8` |
| Spring Boot bootstrap, bean lifecycle | day-13 | `direct v0-3` |
| DI, configuration, profiles | day-14 | `direct v0-3` |
| controller, request/response | day-16 | `direct v0-4` |
| bean validation, `ProblemDetail`, advice | day-17 | `direct v0-4` |
| JPA entity, relationships | day-19 | `direct v0-5` |
| `@Query`, `@Transactional`, `@Version`, pagination, `REQUIRES_NEW` | day-20 | `direct v0-5`; `REQUIRES_NEW` 2 hits day-20 |
| Flyway, `UNIQUE` DDL, `SUM`/`GROUP BY` | day-21 | Flyway 17 hits in day-21 |
| password hashing, filter chain, STATELESS, JWT verification | day-22 | `direct v0-6` |
| `@PreAuthorize`, `authentication.name`, JOIN FETCH | day-23 | `direct v0-6` |
| logout revocation | day-24 | `content/lessons/day-24.json:246` (required group) |
| `@Cacheable`/`@CacheEvict`, `@Async`, `@Scheduled` | day-25 | 54 / 113 / 41 hits |
| `MultipartFile`, CSV escaping, `WebClient` + retry | day-26 | `direct v0-8` |
| async-after-commit ordering, distributed-lock caveat | day-27 | `content/lessons/day-27.json:278-279` |
| JUnit 5, Mockito, `@WebMvcTest`, `@DataJpaTest` | day-28 | `Mockito` 10 hits, all day-28 |
| **Testcontainers** | **day-29** | day-28's is a bare note (`day28-blk-13`); day-29 has `day29-blk-13` |
| springdoc, MDC `traceId`, Actuator, structured logging | day-29 | `springdoc` 29; `day29-blk-6`/`:25` |
| Docker Compose, layered jar, JaCoCo **report** | day-30 | `content/lessons/day-30.json:204`, `:252` |
| **canonical `JwtEncoder` issuance** | **day-33** | all 8 `TokenIssuer` hits; `day33-blk-29`; `day33-blk-33` HS256 ≥256-bit |
| `ConcurrentMapCacheManager` as project cache | day-34 | `day34-blk-11`, `day34-blk-13` |
| `./mvnw` + build-image pipeline | day-35 | `content/lessons/day-35.json:320` |
| defense/presentation | day-36 | day-36 is Final Defense |

---

## 7. Day 24 / Day 33 execution timing, and why the required task lands after day-36

Three constraints collide:

1. **Canonical JWT issuance is taught only at day-33.** All 8 `TokenIssuer` hits are in
   `content/lessons/day-33.json`; `day33-blk-29` is the block with `ImmutableSecret`, `JWKSource`,
   `MacAlgorithm`, `JwsHeader`, `JwtClaimsSet`, `JwtEncoder`, `NimbusJwtEncoder`, `SecretKeySpec`.
   Day-22 says so explicitly (`content/lessons/day-22.json:78`): *"Luồng phát hành cụ thể
   (AuthenticationManager, DaoAuthenticationProvider, JwtEncoder) được dạy đầy đủ ở Day 33 khi lắp
   ráp module Auth của dự án capstone."*
2. **Day-31→36 is the formal graded e-commerce capstone.** No required Spendwise implementation work
   may be added inside that window.
3. **A learner must not implement an API before it is taught**, and must not be handed a hidden
   implementation solution at day-24.

Resolution — knowledge unlock and project execution are separate axes:

| Window | Spendwise work | Nature |
|---|---|---|
| **day-22 → day-23** | security foundation: hashing, `SecurityFilterChain`, STATELESS, JWT **verification**, `@PreAuthorize`, service-layer ownership | required |
| **day-24** | authentication flow end-to-end against a **`TokenIssuer` contract/seam** — an interface plus a wiring point, with logout revocation behind it. The learner implements the flow, the ownership checks and the revocation behaviour, not the signer | required |
| **day-25 → day-30** | V0.7 / V0.8 / V0.9 proceed normally; V0.6 is functionally complete and architecturally *sealed at the seam* | required |
| **day-31 → day-36** | **nothing.** The capstone is untouched. Day-33 delivers the canonical issuance knowledge as formal curriculum | knowledge only |
| **after day-36** | one required task: implement the canonical `TokenIssuer` using day-33's `NimbusJwtEncoder` + `JwtClaimsSet`, with a ≥32-byte HS256 secret. **V0.6 becomes complete here** | required |

**No unsafe temporary signer is ever written and later rewritten.** At day-24 the seam is a contract
with no signing implementation behind it in the learner's own code; the learner exercises the flow
against JWT verification, which *is* taught at day-22. The single implementation of `TokenIssuer`
that Spendwise ever contains is the canonical one, written once, after day-36.

The HS256 constraint is carried verbatim into the post-capstone task, from
`content/lessons/day-33.json:254` (`day33-blk-33`, type `warning`): a MACSigner secret *"phải dài ít
nhất 256 bit"*, and *"256 bit = 32 byte UTF-8, và secret ngắn hơn KHÔNG làm ứng dụng chết lúc khởi
động - bean JwtEncoder vẫn tạo được, chỉ tới lần encode() đầu tiên … mới thất bại"* — a
fail-at-first-use trap, which is why the task's acceptance criterion is an actual `encode()` call,
not a successful application start.

### 7.1 KNOWLEDGE UNLOCK is a data shape, not a prose promise

**Added by the pre-P0 sanity gate, 2026-09-05.** §7's separation of the two axes was
stated only in prose. Prose does not reach the learner; the rendered artifact does. The rule below
binds the separation to the data.

**Correction, same day, after the late verifier reports:** the sentence that stood here — *"so it
cannot be lost in authoring"* — was **false and has been withdrawn**. Nothing enforces R-DAY33.
Re-adding `task-jwt-auth` (or any V0.6 task) to `lessonMap["day-33"].buildTaskIds` later validates at
**0 errors**, because the referential checks at `validate_project.py:428` and `:434` are satisfied
whenever the task's `releaseId` matches the entry's and the entry's `featureIds` is a superset. And
`day-33` has **zero** coverage: 0 hits in `index.template.html`, 0 hits across `tests/`; self-test #37
probes day-20, day-05, day-02 and day-39-64, never `direct`-with-empty-`buildTaskIds`. R-DAY33 is an
**authoring convention with no mechanical guard.** P0 should close it — a validator rule freezing the
capstone window (`day-31`…`day-36` may not carry a non-empty `buildTaskIds`), and/or a self-test that
`#/lesson/day-33` renders zero `[data-action="toggle-build-task"]` elements. Until then this rule has
exactly the status §7.1 was written to escape.

Measured rendering behaviour of `index.template.html`, per `applicationType`:

| `applicationType` | `buildTaskIds` | What a learner sees | Mechanism |
|---|---|---|---|
| `theory`, no `application` key | n/a | no feature list, no application section, **no toggle** | `:2889` `if (type !== 'theory') appendFeatureList(...)`; `renderProjectApplication` never reached for a 2-key entry because `:2895` returns early when `mapping.application` is absent |
| `theory`, **with** `application` | non-empty | **the full CTA** — heading, release line, prose, feature list, toggles | the `:2895` guard is on the *field*, not the type; `:2911-2912` have no type gate. Validates with 0 errors |
| `direct` | **empty `[]`** | **the whole "Used in Spendwise" section still renders** — heading, the release line *"V0.6 Security & Ownership"*, the `application` paragraph and the feature list. What is absent is only the build-task list and its clickable CTA | `appendBuildTaskList` no-ops at `:2074` (`if (!tasks.length) return`), so no `[data-action="toggle-build-task"]` element is created — **but nothing else in `renderProjectApplication` is gated on the task list**, and `application` is *mandatory* for `direct` (`validate_project.py:418`), so the section cannot be suppressed by omitting it |
| `future` | **empty `[]`** | the same section, **plus** the fixed sentence *"Áp dụng ở release sau; đây không phải build ngay trong bài học này."* | the note at `:2876-2882` is unconditional whenever `type === 'future'`; `:2074` still no-ops. **This is the only shape in the site that renders an explicit "not now" string** — and it validates at 0 errors |
| `direct` | non-empty | the full CTA: a toggle per task, `aria-label` *"Đánh dấu hoàn thành: …"*, a `required`/`optional` chip, and a *"Đã hoàn thành build task"* toast | `createBuildTaskItem` `:2042` |
| `future` | **empty `[]`** | **no CTA, plus** *"Áp dụng ở release sau; đây không phải build ngay trong bài học này."* | the note at `:2876-2882` is unconditional for `future`; `:2074` still no-ops. **Ships on day-05, day-11, day-12** |
| `future` | non-empty | the CTA **plus** that same disclaimer | both paths fire; only day-07 is in this shape |

**Is `direct` with an empty `buildTaskIds` legal?** Yes, and it is already in production.
`_validate_lesson_map` validates `featureIds` with `nonempty_list=True`
(`tools/validate_project.py:414`) but calls `_require_str_list` on `buildTaskIds` **without** it
(`:415`). Six entries exercise this today — day-01, 24, 25, 26, 29, 30 — and
`python tools/validate_project.py` exits 0 against them.

**R-DAY33 (binding on Phase 2).** `lessonMap["day-33"]` is authored as:

```
applicationType : "direct"
releaseId       : "v0-6"
featureIds      : the V0.6 auth feature ids (non-empty — required by :414)
buildTaskIds    : []            ← EMPTY, deliberately and permanently — but note that
                                  nothing enforces this; see the withdrawal above
projectProblem  : names the knowledge gap, not a deliverable
application     : states that day-33 supplies the JwtEncoder knowledge and that the
                  Spendwise TokenIssuer is implemented AFTER day-36.
                  ** MANDATORY: the scheduling must be in THIS string (and in
                  projectProblem), not in the task's `constraints` and not in
                  `buildSteps` ordering. Measured: `constraints` renders only via
                  appendBuildTaskDetails (:2085), reachable only from the Build Tasks
                  workspace (:3396) and the release view (:3516) — never from a lesson
                  page, which calls appendBuildTaskList (:2912) instead. `buildSteps`
                  has NO renderer anywhere (0 hits in index.template.html, tools/,
                  tests/, content/). "after day 36" is 0-hit in the artifact. **
context         : keep the existing string — it already ends
                  "không xây tính năng Spendwise"
```

**What `direct` + `[]` does *not* suppress.** The `.project-application` section still renders in
full: the `h2` *"Used in Spendwise"*, the release line *"V0.6" / "Security & Ownership"*, the
`application` paragraph and the feature list. `application` is mandatory for `direct` *and* for
`future` (`:410` scopes the block to both, `:418` requires the string), so this is a cost of **mapping
day-33 at all**, not of the type choice — the only shape that avoids it is the unmapped 2-key `theory`
entry day-33 has today. Only the build-task list and its toggle are removed by the empty list.

`task-canonical-token-issuer` is therefore **not** listed in `lessonMap["day-33"].buildTaskIds`.
This reverses the Phase 2 plan's §6, which had day-33's entry carry that task id. Rationale, in
order of weight:

1. **It makes the separation visible.** With `buildTaskIds: []` the learner reading
   day-33 — a lesson that sits *inside* the graded capstone — is shown no checkbox, no
   `required` chip and no "Đánh dấu hoàn thành" affordance. With the task id present they are shown a
   required Spendwise deliverable on a capstone day, which is exactly the outcome §7 exists to
   prevent. The Phase 2 formulation satisfied the validator and defeated the intent. (Corrected from
   "the only way" — see the amendment below; `future` + `[]` suppresses the CTA too.)
2. **The lesson's own text already says so.** `lessonMap["day-33"].context` ends *"không xây tính
   năng Spendwise"*, and day-33's canonical `TokenIssuer` code is written as capstone code — its
   issuer literal is `"spendwise-capstone"`, the single occurrence of the string `spendwise`
   anywhere in `content/lessons/`.
3. **Discoverability is already solved in the other direction.** `task-canonical-token-issuer` carries
   `relevantLessonIds`, which is validated **non-empty** (`tools/validate_project.py:261`) with every
   id checked against the lesson set (`:269`), and which the site renders as a *"Relevant Lessons"*
   disclosure of real `#lesson/<id>` links on the task's own article
   (`index.template.html:2088`, `appendBuildTaskDetails`). So the task **must** name day-33 there:

   ```
   task-canonical-token-issuer.relevantLessonIds = ["day-24", "day-33"]
   ```

   That gives task → day-33 navigation with no build-now affordance anywhere, because the link lives
   on the task page, not on the lesson page. The direction that renders a CTA (lesson → task, via
   `lessonMap.buildTaskIds`) stays empty; the direction that renders a link (task → lesson, via
   `relevantLessonIds`) is filled. This is strictly better than the `alsoUsedIn` key Phase 2 §16
   proposes for the same purpose — `relevantLessonIds` exists today, is already validated, and is
   already rendered, so no schema change is needed for day-33's discoverability.
4. **Nothing is orphaned.** A build task does not need a lessonMap entry to exist or to render;
   ownership runs task → release (`_validate_release_task_links`, `:320-326`), not task → lesson.
   `task-canonical-token-issuer` is owned by V0.6's ordering and reached from the release view. No
   validator rule requires a task to be referenced from `lessonMap`.

**Consequence for the counts:** day-33 still moves `theory` → `direct`, so 24/1/13 is unchanged by
R-DAY33. It joins the `direct`-with-empty-`buildTaskIds` set, which therefore goes from 6 entries to
**1** after P1 fills the other six — not to 0.

**Amended by adversarial verification, pre-P0 sanity gate, 2026-09-05.** Three additions; R-DAY33
itself stands, but its justification was overstated and its authoring requirements were incomplete.
Full detail: `docs/report/2026-09-05-spendwise-pre-p0-sanity-gate.md` §2.1–2.2.

1. **CTA suppression is data-contingent, never type-enforced.** Only *two* things in the lesson
   renderer are gated on `applicationType` — `appendFeatureList` in the context panel (`:2889`) and the
   `future` disclaimer (`:2876`). Everything else is gated on **fields**: the application section on
   `application` (`:2895`), the release link on `releaseId` (`:2865`), the "Project problem:" line on
   `projectProblem` (`:2883`), the CTA on `buildTaskIds.length` (`:2074`). Measured: a **`theory`** entry
   carrying `application` + `buildTaskIds: ["task-jwt-auth"]` renders the full CTA and validates with
   **0 errors**. `theory` looks safe today only because all 18 shipping `theory` entries carry exactly
   `{applicationType, context}`. So R-DAY33's protection comes from the empty array alone.
2. **Two mechanical requirements.** `"buildTaskIds": []` must be written **explicitly** — omitting the
   key fails at `tools/validate_project.py:134-135` (`ERROR … buildTaskIds must be a list`) before the
   `nonempty_list` branch at `:137` is reached. And day-33 must **not** stay `theory` while gaining the
   other five keys, per (1).
3. **The rejected alternative, and what `direct` costs.** `applicationType: future` + `buildTaskIds: []`
   also suppresses the CTA *and* renders the disclaimer — and it already ships on **day-05, day-11,
   day-12** (three of the four `future` entries have empty `buildTaskIds`; only day-07 carries a task).
   It is rejected on wording: *"Áp dụng ở release sau"* asserts a **later release**, which is false —
   day-33's release is V0.6 and only its *execution* is later in lesson time. But choosing `direct`
   carries three real costs, which P1 must offset in prose: the map legend glosses the badge as
   *"direct (xây trực tiếp)"* by type alone (`:3623`); there is **no `.project-type--direct` or
   `.map-type--direct` CSS rule**, so `direct` falls through to the actionable teal base style at
   `:1215-1222` (`theory` explicitly overrides to grey at `:1238-1239`); and the dashboard's "Today's
   Project Impact" panel branches on `application` at `:2426-2433`, so once `application` exists the
   `context` prose — *including* "không xây tính năng Spendwise" — **disappears from the dashboard**.
   Therefore `application` and `projectProblem` must state the post-day-36 scheduling in their own text.
4. **No assertion breaks.** `directCount` 16 → 17 (`:4972`) and `theoryUnmappedCount` 20 → 19 (`:4979`)
   both compare against runtime-derived row counts, so both sides move together. The `direct` probe in
   self-test #37 is **day-20** (`:4792`), the `theory` probe is **day-02** (`:4805`), and the `future`
   probe is **day-05** — which, being `future` + `[]`, already asserts the no-CTA-plus-disclaimer shape.
   `tests/test_validate_project.py:174` stays **38**.

**Amended 2026-09-05 by the final import-identity correction — the guard is promoted from a
recommendation into a P0 requirement.** The withdrawal above ends *"P0 should close it"* and the
pre-P0 sanity gate's Known gap 11 records the two closures as *"recommendations for P0, not
decisions"*, present *"in neither §16's validator diff nor §12's site-change list"*. That is now
decided, as a **planning** decision only:

> **R-CAPSTONE-GUARD (P0, test/self-test scope only).** **Day 31–36 must not expose a required
> Spendwise build-task CTA.** P0 must add a mechanical guard so this cannot be lost in authoring —
> a validator rule that `lessonMap["day-31"]`…`lessonMap["day-36"]` may not carry a non-empty
> `buildTaskIds`, and/or a self-test asserting `#/lesson/day-33` renders zero
> `[data-action="toggle-build-task"]` elements.

Scope discipline, stated so the next session cannot widen it:

- **This is a TEST / SELF-TEST requirement. It changes no UI.** No route, no render function, no
  template markup, no learner-visible string. It asserts the *current* behaviour and freezes it.
- It is satisfiable today at zero cost: measured 2026-09-05, all six of `day-31`…`day-36` are
  `applicationType: theory` with exactly `{applicationType, context}` and **no `buildTaskIds` key at
  all**, so the rule passes on the frozen artifact and passes again after P1 gives day-33
  `"buildTaskIds": []`.
- It exists to mechanically protect the approved rule **"formal capstone window ≠ required Spendwise
  build window"** — the rule §7.1 was written for and which, per the sanity gate, nothing enforces:
  re-adding a V0.6 task id to day-33 validates at **0 errors**, and `day-33` has **0** hits in
  `index.template.html` and **0** across `tests/`.
- It does **not** change any count: no task, feature or lessonMap entry is added or removed by a
  validator rule.

---

## 8. Toolchain freeze (ADR-017)

A prerequisite that must be satisfied **before** Spendwise initialization, and pinned thereafter —
with one exception recorded on 2026-09-05: **the Spring Boot version is not a V0.1 prerequisite.**
V0.1 and V0.2 are pure Java (V0.1's acceptance criterion in `content/spendwise-project.json` reads
*"No dependency on Spring, database, or REST"*), so the Boot pin must be settled before the first
**V0.3** task, `task-spring-bootstrap`, and not before `task-project-foundation`. Java 17, Maven +
Wrapper, the `com.spendwise` root and the PostgreSQL 16 tag are unaffected and remain V0.1-time
decisions. See §8.1.

**What "Maven at V0.1" means, and what it does not** (clarified 2026-09-05 by the final
import-identity correction; **the project foundation itself is unchanged**). Maven + the Maven
Wrapper at V0.1 is **project and tooling scaffolding, not a Day-01 learning objective.** Concretely:

- The learner is **not** expected to derive Maven configuration from Day-01 theory. Day-01 teaches
  Java fundamentals; it does not teach a build tool, and §11 gap 12 measures why (**Maven is 0-hit in
  day-01 – day-11 and in day-13/day-14**).
- The coding mentor **may guide the setup** — generate the POM, add the wrapper, explain
  `./mvnw test` — because a learner cannot compile or run a test without a build tool. That guidance
  is scaffolding, and it is why `task-project-foundation` carries its own Maven commands in
  `constraints` rather than citing a lesson.
- What the learner **is** accountable for at V0.1 is the Java: the `Money` VO, the domain types, the
  invariants and green tests. The build file is a means, not an outcome.
- **Spring Boot remains absent until V0.3.** V0.1's acceptance criterion is *"No dependency on
  Spring, database, or REST"*; the `spring-boot-starter-parent` arrives with `task-spring-bootstrap`,
  which is where `SPRING_BOOT_EXACT_PIN_PENDING` is the hard prerequisite.

This changes no task, no count and no acceptance criterion — it fixes how the requirement is
*described*, so a mentor does not read "Maven at day-01" as a knowledge prerequisite the curriculum
was supposed to supply.

**The starting fact that shapes this section: there are no build files in this repository at all.**
0 hits, tracked files and full working tree, for `pom.xml`, `build.gradle*`, `package.json`,
`requirements*.txt`, `Makefile`, `Dockerfile*`, `docker-compose*`, `mvnw*`, `gradlew*`. The 87
tracked files are 52 `.json`, 17 `.py`, 12 `.md`, 2 `.html`, 1 `.xlsx`, 1 `.txt`, 1 `.js`, 1
`.gitignore`. The only `.java` files anywhere are javac scratch under gitignored `.course-cache/`.
So this freeze is a **documentary** pin, not a mechanically enforced one — see reviewer orientation
item 3.

| Element | Pinned value | Evidence | Confidence |
|---|---|---|---|
| **Java** | **17** | `tools/validate_lessons.py:1005` runs `[javac, "--release", "17", …]`; `JAVA_POST_17_PATTERNS` at `:33-37` lints out `STR."`, record-pattern switch guards and `Thread.ofVirtual(`; `content/lesson-schema.json:127` mandates the baseline field; **all 39 lesson files carry the byte-identical `"baseline": "Java 17 / Spring Boot 3.x / Spring Framework 6 / Jakarta"` — 40 records, zero variants** (38 at `/authoring/baseline`, plus 2 at `/lessons[]/authoring/baseline` inside `content/lessons/ojt-evaluation.json`, which holds `day-39-64` and `day-65-66`) | **mechanically enforced** |
| **Build tool** | **Maven**, via the **Maven Wrapper** (`./mvnw`) — **project/tooling scaffolding at V0.1, not a Day-01 learning objective** (see the §8 opening) | Gradle is **0 hits repo-wide**, case-insensitive, including `index.html`; `mvnw` 5 hits, e.g. `content/lessons/day-35.json:320`: *"(1) checkout code, (2) ./mvnw test (unit + integration test bằng Testcontainers), (3) ./mvnw spring-boot:build-image, (4) push image lên registry"*. Maven is **0-hit in day-01 – day-11 and day-13/day-14** (gap 12), which is exactly why the requirement is scaffolding the mentor may guide rather than theory the learner derives | strong |
| Maven version | **not pinned** | the corpus never names one; the wrapper makes the local Maven version irrelevant, which is why the wrapper is what gets pinned | n/a |
| **Spring Boot** | **`SPRING_BOOT_EXACT_PIN_PENDING`** — neither the patch nor the line is settled; see §8.1 | baseline says `3.x`; the *demonstrable floor* is 3.4.0: `content/lessons/day-28.json:145` *"@MockBean (hoặc @MockitoBean/@MockitoSpyBean từ Spring Boot 3.4 trở đi, do @MockBean/@SpyBean đã deprecated)"*; `content/lessons/day-29.json:120` *"Từ Spring Boot 3.4.0, có thể bật structured logging … logging.structured.format.console"*; `@ServiceConnection` needs 3.1+ (`day-29.json:319`). The only version-pinned Spring documentation anywhere in the corpus is Spring Security `6.5`/`6.5.x` (ships with Boot 3.5) — **but that is a documentation pin only, and does not evidence a 3.5 runtime: day-33's code compiles clean against Security 6.4.13 and every 6.5-only API is 0-hit** (pre-P0 sanity gate, 2026-09-05). The operative constraint is instead that both 3.4.x and 3.5.x are past OSS end-of-support as of 2026-09-05 | **UNRESOLVED — hard prerequisite of `task-spring-bootstrap` (V0.3), see §8.1** |
| Dependency management | `spring-boot-starter-parent` as `<parent>`; no explicit `<dependencyManagement>`; no per-starter versions | `spring-boot-starter-parent` 0, `dependencyManagement` 0, `<parent>` 0, `<properties>` 0, `start.spring.io` 0 — the corpus never shows a POM, so the Spring Boot default is adopted rather than invented | derived |
| **PostgreSQL** | **16**, container tag `postgres:16-alpine` | `postgres:16-alpine` at `content/lessons/day-29.json:297`, `day-30.json:96`, `day-30.json:204`, `production.json:609`; `postgres:16` at `day-36.json:219`. No server version in prose; no other tag anywhere. H2 is test-only and warned against (`day-28.json:239`) | strong |
| Redis | **optional**, `redis:7-alpine` when present | one hit, `content/lessons/day-30.json:334`, an exercise answer key; `day-30.json:204` says Redis is not required; Redis 6.2.0 named only as the GETEX/TTI floor (`day-25.json:567`) | weak — hence ADR-010 |
| Base image | **`eclipse-temurin:17-jre-alpine`** | day-30 uses `17-jre-alpine`, day-35 uses `17-jre` with a different layer list. Conflict resolved toward day-30 because day-30 is the production-readiness lab and carries the reference compose file | resolved conflict |
| Compose filename | **`compose.yml`** — a **project-side override**, not a corpus fact | **Bare `compose.yml` is 0 hits repo-wide.** Every one of the 39 tracked occurrences of the substring is inside **`docker-compose.yml`** — 22 of them in `content/`, across 5 files (`day-30.json` ×10, `source-manifest.json` ×5, `source-notes/production.json` ×3, `day-35.json` ×3 occurrences / 2 lines, `lesson-authoring-report.md` ×1). `compose.yaml` is also **0**, so the comparison this row originally cited was 0-vs-0. The corpus names the file explicitly and consistently: `content/lessons/day-30.json` title *"Dockerfile + docker-compose.yml"*, its code block opens `# docker-compose.yml`, and its `partialReason` reads *"docker-compose.yml, khong phai ma nguon Java bien dich duoc."* Spendwise adopts the modern Compose-Spec name instead | **decision — diverges from every lesson; must be disclosed to the learner** |
| **Root package** | **`com.spendwise`** | **0 hits in `content/`** — every occurrence in the repository is inside `docs/` Spendwise planning documents, this one included, so that count is self-referential and drifts as these documents are edited. The course teaches `com.example.ecommerce` (`day-31.json:74`) and `com.example.shop.api` (`day-29.json:75`), and **no snippet in the corpus declares a package at all** | **Spendwise-side decision** |
| `groupId` / `artifactId` | `com.spendwise` / `spendwise` | never stated in the corpus; chosen for consistency with the root package | decision |
| Jakarta Persistence | 3.1 is the operative floor | `content/lessons/day-19.json:172` names the JPA 3.1 `java.time` set | strong |
| Pinned library versions | only two exist in the whole corpus: **JMH 1.37** (`day-12.json:166`), **springdoc-openapi 2.6.0** (`day-29.json:75`) | Testcontainers (145 hits), JUnit 5 (22), Flyway (21), Hibernate, PostgreSQL JDBC: named everywhere, versioned nowhere → all inherit the Boot parent | strong |

**Six internal inconsistencies this freeze resolves**, each recorded so a mentor does not
rediscover them as bugs:

1. Temurin tag — `17-jre-alpine` (day-30) vs `17-jre` (day-35), with different layer lists. → day-30.
2. Postgres tag — `16-alpine` ×4 vs `16` (day-36). → `16-alpine`.
3. Compose filename — the corpus says **`docker-compose.yml`** (39 tracked occurrences, 22 of them in
   `content/`); bare `compose.yml` and `compose.yaml` are **both 0**. → `compose.yml` anyway, as a
   **project-side override** of the Compose-Spec name, *not* a resolved corpus conflict. It must be
   disclosed to the learner, because every lesson writes the old name.
4. Package root — `com.example.*` taught vs `com.spendwise` decided. → `com.spendwise`, labelled a
   project decision, not a corpus fact.
5. Spring Boot — baseline `"3.x"` vs a 3.4.0-dated feature floor. → **no exact patch is pinnable from
   this repository**; see the `SPRING_BOOT_EXACT_PIN_PENDING` block below.
6. JPA temporal advice — day-19 `OffsetDateTime` vs this blueprint's `Instant`. → `Instant` on
   Hibernate-6 grounds (D4/ADR-002), with the conflict stated rather than hidden.

**Upgrade policy.** Once the exact Spring Boot version is selected at initialization it is pinned in
the POM and recorded in the project README. **Any later change to it — patch, minor, or major —
requires an explicit toolchain/architecture decision recorded under §10.** It is never an
opportunistic AI upgrade, never a side effect of an unrelated task, and never justified by "a newer
version is available". Course compatibility and reproducibility outrank currency: a learner whose
build resolves different dependency versions than the lesson they are reading is debugging the
toolchain instead of learning. Java 17 is
not a floor to be raised: `tools/validate_lessons.py` lints Java-18+ syntax out of the corpus, so a
learner on Java 21 who uses a Java 21 feature diverges from every lesson they are reading.

### 8.1 `SPRING_BOOT_EXACT_PIN_PENDING`

```
SPRING_BOOT_EXACT_PIN_PENDING
```

**Added by the pre-P0 sanity gate, 2026-09-05.** An earlier revision of this section pinned Spring
Boot at `3.4.x`. That pin is withdrawn as unsupported, and the exact-patch question is escalated
from "choose one at initialization" to an explicit open decision, for three independent reasons —
**Reason 1** (no patch is derivable), **Reason 2** (the line was never evidenced either, and the
6.4-vs-6.5 argument that once seemed to settle it is refuted) and **Reason 3** (both candidate lines
are out of OSS support as of 2026-09-05, which is what actually forces the decision).

**Reason 1 — no exact patch is derivable from this repository.** Swept every URL in
`course-catalog.json`, `content/source-manifest.json`, `content/source-notes/*.json` and
`content/lessons/*.json`: 140 distinct URLs. Version-pinned paths, exhaustively:

| Pinned path | Count | What it pins |
|---|---|---|
| `docs.spring.io/spring-security/reference/6.5/…` | 4 | Spring Security **6.5** |
| `docs.spring.io/spring-security/reference/6.5.x/…` | 9 | Spring Security **6.5.x** |
| `javadoc.io/…/nimbus-jose-jwt/9.37.3/…MACSigner.html` | 1 | nimbus-jose-jwt **9.37.3** |

All **19** `docs.spring.io/spring-boot/…` URLs, all **5** `spring-framework` URLs and all **5**
`spring-data` URLs are **unversioned**, and each one's `check.finalUrl` equals its `requestedUrl` —
no redirect resolved them to a numbered path. In prose, `3.4.0` appears only as a *feature floor*
("từ Spring Boot 3.4 trở đi", "Từ Spring Boot 3.4.0"); the only other numbered Boot string in the
corpus is a `(v3.2.x)` banner at `content/lessons/day-13.json:79`, which contradicts a 3.4 floor
rather than supporting a pin. The two library versions that *are* pinned anywhere are JMH 1.37
(`day-12.json:166`) and springdoc-openapi 2.6.0 (`day-29.json:75`). No build file exists to enforce
anything: `pom.xml`, `mvnw`, `mvnw.cmd`, `gradlew`, `build.gradle`, `settings.gradle`, `.mvn/`,
`Dockerfile`, `compose.yml`, `docker-compose*` are all **0 files** in the working tree, and the 87
tracked files are 52 json / 17 py / 12 md / 2 html / 1 xlsx / 1 txt / 1 js / 1 gitignore.

**Reason 2 — the line choice was never evidenced (and the 6.4-vs-6.5 argument for it is refuted).**
Spring Boot manages Spring Security through its dependency BOM: **Boot 3.4.13 → Spring Security
6.4.13** (framework 6.2.15), **Boot 3.5.16 → Spring Security 6.5.11** (framework 6.2.19), verified from
the published `spring-boot-dependencies` POMs on Maven Central. The corpus cites Spring Security **6.5**
documentation 13 times across 69 `sourceRef` occurrences in day-22, day-33 and day-35, and
`content/lessons/day-33.json:196` and `:239` both write branch-scoped text: *"ở nhánh Spring Security
6.5 … chỉ có constructor nhận JWKSource được ghi nhận, CHƯA có các static builder (… chỉ xuất hiện từ
nhánh 7.0)."* So this document picked 3.4.x from a feature floor while the only version-pinned Spring
docs in the corpus point at 6.5, i.e. at 3.5.x. **That inference does not survive — see the
amendment immediately below; it is recorded here only because it was the gate's original argument.**

**Amended by adversarial verification, pre-P0 sanity gate, 2026-09-05.** The stronger claim this
section previously made — that the 6.5 citations *contradict* a 3.4 pin — is **refuted**:

- `day33-blk-29` (the `NimbusJwtEncoder` issuance block) and `day33-blk-10` (`SecurityConfig`) both
  compile under `javac --release 17` against a 6.4.13 classpath (Boot 3.4.13's exact managed set),
  **exit 0**, and **exit 0 with no warnings** under `-Xlint:deprecation,removal`.
- All **26** `org.springframework.security.*` types used anywhere in `content/` resolve on 6.4.13 —
  0 `Class.forName` misses.
- The repo's own probe under `.course-cache/jwt-probe/`, recompiled against 6.4.13, produces output
  **byte-for-byte identical** to the recorded 6.5.7 run: same `PROBE-RESULT: PASS`, same `length=191`,
  same `{"alg":"HS256"}`, same short-secret failure message.
- Every 6.5-only API that could force the line is **0 hits in `content/`**: `setJwkSelector`,
  `PathPatternRequestMatcher`, `oneTimeTokenLogin`, `AuthorizationManagerFactory`,
  `NimbusJwtEncoder.withSecretKey`, WebAuthn/passkey. `NimbusJwtEncoder(JWKSource)` and
  `JwsHeader.with/from` are all `@since 5.6`.

Note also that day-33's comment says what 6.5 **lacks**; reading it as a 6.5 *requirement* inverts its
logic. What survives is a **documentation-citation mismatch with no API consequence** — a hygiene
defect, not a compatibility one, and far too weak to decide a toolchain.

**Reason 3 — both candidate lines are out of OSS support today.** From
`api.spring.io/projects/spring-boot/generations`, fetched 2026-09-05:

| Generation | OSS support ends | Commercial ends | Status at 2026-09-05 |
|---|---|---|---|
| 3.4.x | **2025-12-31** | 2026-12-31 | expired |
| 3.5.x | **2026-06-30** | 2032-06-30 (`extended`) | expired |
| 4.0.x | 2026-12-31 | 2027-12-31 | current |
| 4.1.x | 2027-07-31 | 2028-07-31 | current, latest `v4.1.1` |

This reframes the decision entirely: it is not 3.4-vs-3.5, it is **pin an out-of-support line that
matches the corpus's Security 6.5 citations, or move to 4.x and accept that Security 7.0 falsifies
day-33's own comment** (7.0 introduces the static builders that comment says do not exist yet). There
is no free option, which is precisely why the verdict remains `SPRING_BOOT_EXACT_PIN_PENDING` rather
than a recommendation. Boot 4.0.0 manages Security 7.0.0 / framework 7.0.1 — a curriculum-breaking
jump, not a patch decision.

Two smaller corrections. Spring Boot does **not** manage `nimbus-jose-jwt` in any of these lines, but
that is misleading in effect: `spring-security-oauth2-jose` declares
`com.nimbusds:nimbus-jose-jwt:9.37.4` at compile scope **identically in 6.4.13 and 6.5.11**, so a
learner resolves 9.37.4 without writing a version, while the corpus cites the **9.37.3** javadoc in
five places (`content/source-manifest.json:4135,4154`,
`content/source-notes/project-final.json:860,867`, `content/supplemental-sources.json:131`). The real
defect is a 9.37.3-vs-9.37.4 **citation drift**. And `git log --all --diff-filter=A` confirms **no build
file has ever existed** in this repository's history — stronger than the working-tree count above.

**Status and blocking rules.**

> **Amended by the final planning reconciliation, 2026-09-05 — the blocker was attached to the wrong
> task.** The bullet below previously read: *"This is a **HARD prerequisite of
> `task-project-foundation`** (V0.1). That task creates the learner's Maven project, so it cannot be
> authored — let alone executed — without the exact `spring-boot-starter-parent` version, and
> `task-project-foundation`'s acceptance criterion (`mvnw test` green) is meaningless without it."*
> That is false, and Phase 2 §8 already contradicted it. V0.1 has **no Spring dependency at all**:
> `content/spendwise-project.json` states V0.1's acceptance criterion verbatim as **"No dependency on
> Spring, database, or REST"**, and Phase 2 §8's onboarding table records *"parent POM | added at
> **V0.3**, `spring-boot-starter-parent`, minor pinned then and frozen"*. A Maven project with a
> `main()` and JUnit tests needs no Boot version. The blocker moves to V0.3 accordingly.

- **Canonical V0.1 contract.** `task-project-foundation` = Java 17 + Maven with the Wrapper + root
  package `com.spendwise` + a runnable `main()` + `mvnw test` green + **no Spring Boot dependency**.
  Its POM is a plain Maven POM. No `spring-boot-starter-parent`, no starter, no Boot plugin.
- **`SPRING_BOOT_EXACT_PIN_PENDING` does NOT block `task-project-foundation`,** because that task
  writes no Spring version string. It also does not block V0.2, which is still plain Java.
- This is a **HARD prerequisite of `task-spring-bootstrap` (V0.3)** — the first task that adds
  `spring-boot-starter-parent`. It must be resolved **before the learner executes the first V0.3
  Spring task**, and V0.3 cannot be authored with a concrete version in its acceptance criteria
  until it is.
- It is **NOT a blocker for P0.** P0 touches `tools/validate_project.py`, `index.template.html` and
  the state migration only; it authors no build task content and writes no version string. P0 may
  proceed with this open.
- It is **not a blocker for P1's V0.1/V0.2 tasks** either — only for P1's V0.3 tasks and for any
  later task whose acceptance criteria name a version.
- It is not a blocker for P2–P4 either, except where a task's acceptance criteria name a version.
- **What resolving it requires:** a decision on the *line* first — **not** 3.4.x vs 3.5.x as this
  section originally framed it, since both are out of OSS support as of 2026-09-05, but *expired line
  matching the corpus's Security 6.5 citations* vs *4.x with a Security 7.0 break* — then the exact
  patch, sourced from the Spring Boot release notes at the time Spendwise is initialized, not from this
  document, which will be stale. Record the choice, the date, the Spring Security version it drags in,
  which of the two costs was accepted, and treat every later change as a §10 decision.

---

## 9. Recomputed scope

Everything below is derived from the corrected design and replaces the draft's and the Phase 2
plan's numbers. Nothing here was rounded to a pleasing total.

### Baseline, measured from the frozen artifact

| Dimension | Baseline | How measured |
|---|---|---|
| releases | **10** | `len(project["releases"])`; pinned by `EXPECTED_RELEASES` |
| features | **25** | `len(project["features"])` |
| buildTasks | **24** | `len(project["buildTasks"])`; V0.7–V1.0 all `buildTaskIds: []` |
| required tasks | **22** | `required: false` on exactly `task-config-profiles`, `task-optimistic-locking` |
| milestones | **4** | unchanged by this plan |
| architectureStages | **10** | unchanged |
| lessonMap entries | **38** | `day-01`…`day-38`; `day-39-64` and `day-65-66` unmapped |
| lessonMap distribution | **16 direct / 4 future / 18 theory** | measured: `direct` = day-01, 04, 10, 13, 14, 16, 17, 19, 20, 22, 23, 24, 25, 26, 29, 30; `future` = day-05, 07, 11, 12 |
| `direct` entries with **empty** `buildTaskIds` | **6** | day-01, 24, 25, 26, 29, 30 — the six that a task authoring pass must fill |

### Final target

| Dimension | Baseline | Final | Δ |
|---|---|---|---|
| releases | 10 | **10** | 0 — frozen spine |
| features | 25 | **31** | +6 |
| buildTasks | 24 | **64** | +40 net (+42 new, −2 retired ids not counted, 1 renamed slot reused) |
| required tasks | 22 | **56** | +34 |
| optional tasks | 2 | **8** | +6 |
| lessonMap entries | 38 | **38** | **0 — `day-33` already exists** |
| lessonMap distribution | 16/4/18 | **24 direct / 1 future / 13 theory** | +8 / −3 / −5 |
| buildSteps (new array) | 0 | **~229** | new |
| milestones / architectureStages | 4 / 10 | **4 / 10** | 0 |

### How 64 build tasks is reached

> **Amended by the final planning reconciliation, 2026-09-05 — the total row was arithmetically
> wrong.** Every earlier revision of this document printed a total of **58 / 50 / 8**. That total was
> never derived from the per-release rows: the rows as printed summed to **64 / 56 / 8**
> (6+5+4+5+7+6+8+8+9+6 = 64; required 6+5+3+5+6+5+7+7+8+4 = 56). The `58` was a bare addition error
> that then propagated into Phase 2 §2's heading, Phase 2 §18's P2 exit criterion, the pre-P0 sanity
> gate's quotations, and the planned `tests/test_build_site.py:81` target. It is now corrected against
> the id inventory rather than carried forward. Two further corrections land in the same pass and
> happen to cancel in the grand total — V0.3 loses one optional (Actuator, see below) and V0.4 gains
> one required (the split was mis-added) — which is itself proof that 58 never came from the ids.
> Full id-by-id inventory: `docs/report/2026-09-05-spendwise-final-reconciliation-report.md`.

Per-release, from §5's Evolution Contract:

| Release | Baseline | Final | Required | Optional |
|---|---|---|---|---|
| V0.1 | 5 | **6** | 6 | 0 |
| V0.2 | 5 | **5** | 5 | 0 |
| V0.3 | 3 | **3** | 2 | 1 |
| V0.4 | 4 | **6** | 6 | 0 |
| V0.5 | 5 | **7** | 6 | 1 |
| V0.6 | 2 | **6** | 5 | 1 |
| V0.7 | 0 | **8** | 7 | 1 |
| V0.8 | 0 | **8** | 7 | 1 |
| V0.9 | 0 | **9** | 8 | 1 |
| V1.0 | 0 | **6** | 4 | 2 |
| **total** | **24** | **64** | **56** | **8** |

Check: 6+5+3+6+7+6+8+8+9+6 = **64**; required 6+5+2+6+6+5+7+7+8+4 = **56**; optional 0+0+1+0+1+1+1+1+1+2 = **8**; 56 + 8 = **64**. Baseline column 5+5+3+4+5+2+0+0+0+0 = **24**, which matches the measured artifact.

The arithmetic of the delta:

- **+1 V0.1** — `task-project-foundation`, the empty-project onboarding task (repo, Maven project,
  `com.spendwise` root, `mvnw`, runnable `main()`). This exists because V0.1's project-artifact
  prerequisite list is empty and something must create the foundation; without it a mentor invents
  it. `task-category-enum` is also **renamed** to `task-category-model` (an enum at V0.1 becomes an
  entity at V0.5, so the id must not name the mechanism).
- **±0 V0.3** — **`task-actuator-baseline` is removed.** *Amended 2026-09-05:* an earlier revision
  added it here as an optional health-endpoint task. Actuator is **0-hit in day-13 and day-14**, the
  two lessons V0.3 rests on; its only pre-day-29 appearance in the corpus is as a *wrong answer* in a
  day-17 multiple-choice ("`spring-boot-starter-actuator` không phải starter mà phần Bean Validation
  yêu cầu"). It is taught at day-29 (25 hits, the only lesson with `management.endpoint`) and day-30
  (14 hits), and `content/spendwise-project.json` files it exclusively under release index 8 = V0.9
  (`/releases/8/learningDependencies/12`, `/releases/8/acceptanceCriteria/4` *"Health check and
  metrics exposed (Actuator/Micrometer)"*, `/features/22/description`,
  `/architectureStages/8/layers/6`). §6's Timing Matrix already places Actuator at day-29, so
  requiring it at V0.3 / day-13–14 contradicted this document's own row. Actuator now lives only in
  the existing V0.9 `task-production-packaging`, which Phase 2 §2 already defines as covering
  OpenAPI + MDC + Actuator + Compose — **no new V0.9 task is needed and the V0.9 count does not
  move.** V0.3 returns to its baseline 3 / 2 / 1.
- **+2 V0.4** — `task-rest-controllers` is **retired and split into 3**
  (`task-account-endpoints`, `task-transaction-endpoints`, `task-category-endpoints`); net +2 over
  the retired one, and `task-dto-mapping`/`task-bean-validation`/`task-error-handling-advice` remain
  → **6** (*amended 2026-09-05: this read "→ 5", the same mis-addition that produced the wrong
  header; 3 endpoint tasks + 3 kept tasks = 6, all required*). This is the split that forces the
  progress-migration strategy in Phase 2 §7.
- **+2 V0.5** — `task-flyway-baseline` (migration + `ddl-auto: validate`) and
  `task-balance-projection` (the `@Version`-guarded projection and its invariant). `task-atomic-
  transfer` is re-specified to R21 (linked pair + `transferRef`) without changing its id.
- **+4 V0.6** — `task-jwt-auth` is **retired**, replaced by `task-auth-foundation` (day-22),
  `task-token-lifecycle` (day-24: flow + `TokenIssuer` seam + logout revocation),
  `task-canonical-token-issuer` (**post-day-36**, the only place `NimbusJwtEncoder` appears),
  `task-ownership-checks` (kept), `task-user-migration` (`user_id` columns + scoped queries), and
  `task-auth-hardening-review` (optional; refresh rotation lives here and nowhere else).
- **+8 V0.7** — budget model, budget calculation, recurring model, recurring generation, rule model,
  rule engine, dashboard read model, + optional advanced-aggregation task.
- **+8 V0.8** — CSV parse, import batch model, per-row transaction handling, duplicate detection,
  rule application during import, import result reporting, CSV export, + optional async import.
- **+9 V0.9** — reference-data cache, scheduled reconciliation, recurring scheduler wiring, FX
  client with retry, invariant test suite, slice test suite, Testcontainers integration suite,
  observability (OpenAPI + MDC + Actuator), Docker Compose, + optional Redis cache backend. (Nine
  required-or-optional slots: the Redis upgrade is the optional one, and the two scheduler tasks
  count as one wiring task plus one reconciliation task.)
- **+6 V1.0** — hardening/reconciliation-proof, portfolio README, final demo, defense-question
  audit, + optional AI category suggestion, + optional AI insight.

Retired ids: `task-jwt-auth`, `task-rest-controllers`, and the *rename* of `task-category-enum` →
`task-category-model`. All three are progress-migration events (Phase 2 §7).

### How 31 features is reached

+6 over the artifact's 25, all of them capabilities the ten releases already promise but no feature
names:

| New feature | Introduced in | Why it must exist |
|---|---|---|
| `feat-project-foundation` | v0-1 | the repo/build/package baseline is real work with acceptance criteria |
| `feat-schema-migration` | v0-5 | Flyway + `ddl-auto: validate` is a capability, not a side effect of JPA |
| `feat-dashboard` | v0-7 | V0.7 promises a dashboard; no feature covered it |
| `feat-csv-export` | v0-8 | V0.8's acceptance criteria say *"CSV export is available"* verbatim |
| `feat-testing` | v0-9 | V1.0's `learningDependencies` include `"test coverage"`; V0.9's include Testcontainers |
| `feat-deployment` | v0-9 | V0.9 promises a Dockerized run; `feat-observability` is not deployment |

`feat-hardening` from the draft's list is **dropped** — V1.0 hardening is a task under existing
features, not a feature of its own. The Phase 2 plan's proposed `Release`/`Class` columns on the
feature objects are also dropped: `FEATURE_KEYS` is a closed five-key schema
(`tools/validate_project.py:87`) and adding presentational columns to the data model would fail
validation for no gain.

### How lessonMap stays at 38 entries and reaches 24/1/13

**Correction (pre-P0 sanity gate, 2026-09-05).** An earlier revision of this section claimed the
lessonMap grows to 39 entries by adding `day-33`. That was false. Re-measured directly from
`content/spendwise-project.json`: `lessonMap` is a JSON **object** with **38** keys, `day-01` …
`day-38`, and **`day-33` is already one of them**. It currently reads:

```json
"day-33": {
  "applicationType": "theory",
  "context": "Sprint 1 của dự án capstone e-commerce: hiện thực entity, quan hệ cascade, cấu hình JWT Resource Server và Category CRUD — áp dụng lại kiến thức đã học vào một dự án riêng, không xây tính năng Spendwise."
}
```

So the day-33 change is a **MODIFICATION of an existing entry**, not an addition, and the entry count
does **not** change. `day-39-64` and `day-65-66` stay unmapped and are **not** added — §15's
self-study roadmap is document-level prose, and the four `future`→`direct` conversions all point at
lessons that are actually taught.

- **entry count 38 → 38:** no key is added or removed. `day-33` is retyped and its five missing keys
  are filled in (it carries only `applicationType` and `context` today — the 2-key shape shared by
  all 18 `theory` entries).
- **`future` 4 → 1:** day-07 → `direct v0-2` (it already carries `task-repository-interface`), day-11
  → `direct v0-8`, day-12 → `direct v0-8`. Only day-05 stays `future` (Strategy at day-05, rules at
  V0.7 — genuinely a later release).
- **`direct` 16 → 24:** +3 from the `future` conversions, +5 from `theory` → `direct`
  (day-08 → v0-2, day-21 → v0-5, day-27 → v0-7, day-28 → v0-9, **day-33 → v0-6**). Each of the first
  four currently teaches a technique a Spendwise release requires: day-08 generics/collections/
  exceptions for the V0.2 repository, day-21 Flyway/`UNIQUE`/`SUM` for V0.5, day-27 async-after-commit
  ordering for V0.7's scheduler, day-28 the unit + slice suites for V0.9. Day-33 is the fifth and is
  **different in kind** — it is a knowledge unlock, not project work; see the
  KNOWLEDGE-UNLOCK-vs-PROJECT-EXECUTION rule in §7.
- **`theory` 18 → 13:** −5 for the five `theory` → `direct` conversions above (day-08, day-21, day-27,
  day-28, day-33). The earlier "18 → 14, −4" arithmetic double-counted day-33 as a new entry instead
  of as a conversion out of `theory`.
- Check: 24 + 1 + 13 = **38** = the baseline count. The earlier 24 + 1 + 14 = 39 only balanced
  because of the phantom entry.
- The six `direct`-with-empty-`buildTaskIds` entries (day-01, 24, 25, 26, 29, 30) all gain tasks.
  **day-33 deliberately joins that shape rather than leaving it** — see below.

**Validator consequence, verified:** `_validate_lesson_map` requires a resolvable `releaseId`,
a **nonempty** `featureIds`, a string `projectProblem` and a string `application` for every `direct`
entry (`tools/validate_project.py:410-418`), and enforces
`task.releaseId == entry.releaseId` (`:428`) plus `entry.featureIds ⊇ task.featureIds` (`:434`). Each
of the eight new `direct` entries must therefore be authored with all four fields, not just
retyped. `buildTaskIds` may be empty for a `direct` entry — `_require_str_list` is called without
`nonempty_list` at `:415` — so a lesson can be `direct` without owning a task, which is what makes
day-08 and day-21 convertible.

### buildSteps ≈ 229

> **Amended by the final planning reconciliation, 2026-09-05.** This heading read `≈ 205`, derived
> from the wrong required-task count (50). Recomputed from 56.

56 required tasks × ~4 steps ≈ 224, plus ~5 for the two multi-step optional tasks that need them
(async import, Redis backend) ≈ **229**. At the draft's measured ~600 bytes/step this is ~137 KB. The
40 new build-task objects add a further ~23 KB at the measured 568 bytes/object (24 baseline objects,
min 470, max 694) and the 6 new features ~1.6 KB at 266 bytes/object, taking
`content/spendwise-project.json` from its measured 65,050 bytes to roughly **220–260 KB** and
`index.html` from its measured 1,578,405 bytes to roughly **1.75–1.8 MB**. No size gate exists in
`tools/build_site.py` or the tests, so this
is a performance note, not a constraint.

### Exact test and self-test impact

Four assertions break, and one of them breaks in a way that hides itself. A fifth row is listed
because an earlier revision of this document wrongly called it a breakage.

| Location | Current | Becomes |
|---|---|---|
| `tests/test_build_site.py:80` | `assertEqual(len(project["features"]), 25)` | `31` |
| `tests/test_build_site.py:81` | `assertEqual(len(project["buildTasks"]), 24)` | **`64`** — *amended 2026-09-05 from `58`, which was an addition error in §9's total row* |
| `tests/test_validate_project.py:174` | `assertEqual(len(project["lessonMap"]), 38)` | **`38` — unchanged.** This row was previously listed as a breakage changing to `39`. It is **not** a breakage: `day-33` already exists, so the entry count never moves. Editing this assertion to `39` would take a currently-passing test and make it fail |
| `index.template.html:4792` | `…querySelectorAll('[data-action="toggle-build-task"]').length === 3` (self-test #37, day-20) | day-20's task count after V0.5 gains two tasks → **5** |
| `index.template.html:5120-5122` | self-test **#53** finds a release with `buildTaskIds.length === 0` and navigates to it | **no such release will exist.** `emptyRelease` becomes `undefined`, `emptyRelease.id` throws `TypeError`, and the throw is caught by the outer `catch` at `:5209`, which pushes `"self-test crashed: …"` — so the failure presents as *whole-harness* failure, not as "#53 failed" |

Verified counts behind that table: the in-page harness runs **49 numbered blocks** and **61
`assert(` call sites** — `assert(` appears 62 times in `index.template.html`, but one of those is the
helper's own definition at `:4231` (`function assert(name, cond) {`), so the call-site count is 61.
The highest numbered block is **#57** (`index.template.html:5194`), and the
tally line at `:5226` requires `passed === results.length && results.length >= 15`. The
implementation-plan claim that the project checks stop at #32
(`docs/build-while-you-learn-implementation-plan.md:745`) is **stale**; #53 and #57 are both project
checks. That discrepancy is now resolved in favour of the file.

**Four assertions break, not five.** The `tests/test_validate_project.py:174` row above is a
non-breakage; the real breakages are `test_build_site.py:80`, `test_build_site.py:81`,
`index.template.html:4792` and self-test #53, plus `tests/site_core.test.js:161` when
`STATE_VERSION` bumps.

`tests/site_core.test.js:161` asserts `core.STATE_VERSION === 2`; a bump to 3 breaks it, so the
progress-migration wave must edit that assertion in the same commit as `index.template.html:1714`.

---

## 10. Architecture change protocol

Thirteen triggers. A mentor — human or AI — asked to do any of the following **stops before
writing code**:

1. changing the **Money** strategy (type, scale, storage mechanism, rounding, comparison)
2. changing the **transaction effect model** (positive amounts, the four signed effects)
3. changing the **financial source of truth** (transactions as truth, balance as projection, derived
   budget/report figures)
4. changing the **domain/JPA strategy** (one class per concept, annotations in place, the import
   whitelist)
5. changing the **package structure** (root, package-by-feature, `imports` spelling)
6. changing the **repository strategy** (hand-written subset → `JpaRepository`, in-memory impl
   deleted)
7. changing the **transaction creation path** (the canonical service, `sourceRef` provenance, the
   production/test distinction)
8. changing the **transfer ledger model** (one transaction, linked pair, shared `transferRef`, no
   aggregate)
9. changing the **ownership model** (service-layer enforcement, single `SecurityContextHolder`
   reader, 404-not-403, `user_id` per table)
10. changing the **transaction boundary policy** (`@Transactional` placement, no I/O inside)
11. introducing an **event architecture** or replacing a direct call with a published event
12. changing the **security architecture** (token contents, filter chain, what is required vs
    optional)
13. changing **toolchain versions** (Java, Maven/Wrapper, Spring Boot — line *or* patch, once §8.1's
    `SPRING_BOOT_EXACT_PIN_PENDING` is resolved — PostgreSQL, base image)

Required output shape, exactly:

```
ARCHITECTURE_CHANGE_REQUIRED
Trigger: <which of the 13>
Current rule: <the Constitution rule id and its text>
Proposed change: <what would have to change>
Course support: <lesson ids that teach the replacement, or NONE>
Blast radius: <files, migrations, tests, docs, learner progress data>
Cheapest alternative preserving current architecture: <the smallest change that keeps every rule>
```

Then **STOP**. Do not implement the change, do not implement the alternative, do not implement a
partial version of either. The mentor is not permitted to optimize the architecture according to its
own preferences, and "this is the modern best practice" is not a course-support citation.

---

## 11. Known gaps

Stated plainly, unresolved.

1. **`BigDecimal.divide` is never taught.** V0.7's budget percentage needs it, and an unguarded
   `divide` throws `ArithmeticException` on a non-terminating result. `setScale` and `RoundingMode`
   are both **0-hit corpus-wide**. The V0.7 task must carry the rounding contract in its own
   `constraints`, because no lesson supplies it. This is the one genuine knowledge gap the
   architecture cannot route around.
2. **`openingBalance` is an invention.** 0 corpus hits. The whole signed-effect invariant rests on a
   field the course never mentions. Defensible, but not evidenced.
3. **The toolchain freeze is unenforced, and the Spring Boot version is not settled at all.** No POM
   exists to pin. Until `task-spring-bootstrap` runs, §8's Spring Boot row is prose (*amended
   2026-09-05: this read "until `task-project-foundation` runs"; V0.1 writes no Spring version, so the
   Boot pin is first exercised at V0.3 — see §8.1*). Worse than unenforced: §8.1
   records `SPRING_BOOT_EXACT_PIN_PENDING` — neither the patch nor the *line* is derivable from this
   repository, and the two arguments that once looked decisive have both failed. The corpus's only
   version-pinned Spring documentation is Spring Security `6.5`/`6.5.x`, which ships with Boot 3.5 —
   but that is a docs pin, not a runtime one, and day-33 compiles clean on 6.4.13 (pre-P0 sanity gate,
   2026-09-05). What remains is an external, time-bound constraint that this repository cannot settle:
   **both 3.4.x and 3.5.x are past OSS end-of-support as of 2026-09-05**, so any pin either accepts an
   unsupported line or moves to 4.x and falsifies day-33's own comment about static builders.
   **Related and newly recorded (final planning reconciliation, 2026-09-05): Maven itself is 0-hit in
   day-01 – day-11 and in day-13/day-14.** The only early `pom.xml` in the corpus is a JMH snippet in
   day-12, and `mvnw` first appears at day-35. `task-project-foundation` therefore requires a build
   tool that no lesson in its own window teaches — a **labelled structural exception**, not a hidden
   one: the task must supply the Maven commands it needs in its own `constraints`, exactly as the V0.7
   rounding contract must (gap 1).
4. **Day-06 contradicts R1.** `content/lessons/day-06.json` uses `double baseSalary` in an employee
   exercise. It is not Spendwise, and day-01 teaches the opposite, but a learner reading day-06 sees
   `double` money in a graded assignment. Unresolvable without editing frozen content.
5. **Defense-question count disagrees across three sources.** `docs/build-while-you-learn-plan.md`
   §45 has **13** portfolio/defense questions; `docs/SPENDWISE_ARCHITECTURE_RESEARCH.md` PART 15 has
   **15**; the Phase 2 plan's matrix has **15 rows**. This blueprint does not adjudicate; Phase 2 §12
   uses 15 and flags the discrepancy.
6. **Redis's evidentiary base is one answer key.** ADR-010 now treats Redis as optional for exactly
   this reason, but a reviewer who reads day-25 alone will see a lesson that teaches Redis in depth
   and may reasonably conclude the opposite.
7. **`ImportBatch` and `ExchangeRate` are 0-hit** as names. Both are named in the frozen artifact's
   feature descriptions, so they are authorized products of the plan — but no lesson shows their
   shape, and the V0.8/V0.9 tasks must specify them entirely from this document.
8. **`day-39-64` and `day-65-66` stay unmapped.** Both are internal framework records with no
   external `resourceId` (`content/lessons/ojt-evaluation.json`) — day-39-64 is *"khung tổ chức nội
   bộ"*, day-65-66 is *"khung đánh giá nội bộ, không đặt ra thang điểm chính thức"*. Self-test #37
   asserts `day-39-64` renders **no** project composition
   (`index.template.html:4807-4812`), so mapping either one would break the harness. The
   `SPENDWISE_SELF_STUDY_ROADMAP` (Phase 2 §10) is how the OJT window is addressed instead.

9. **The lessonMap count in this document was wrong until the pre-P0 sanity gate.** §9 claimed 39
   entries and a 24/1/14 distribution; the artifact has 38 entries and the correct target is
   24/1/13, because `day-33` already exists as a `theory` entry. Corrected in §9 and §7.1. The
   general lesson for a reviewer: **every count in this document that was not re-measured on
   2026-09-05 should be treated as suspect.** The ones that *were* re-measured and are now correct:
   lessonMap 38 and its distribution, the 39-files/40-records `baseline` string, the 61 `assert(`
   call sites, `mvnw` 5 occurrences, 87 tracked files, and the 0-file count for every build file.
   The `compose.yml` count is the cautionary case: it was re-measured *twice* — 25 → 22 → and only on
   the third pass was the **basis** found to be wrong. Bare `compose.yml` is 0 hits; all 22 in
   `content/` are `docker-compose.yml`. Re-measuring a number does not validate what the number
   counts.
10. **The buildTask total in this document was an addition error until the final planning
    reconciliation** (2026-09-05). §9 printed **58 / 50 / 8** in a total row whose own per-release
    rows summed to **64 / 56 / 8**. The wrong total had already propagated into Phase 2 §2's heading,
    Phase 2 §18's P2 exit criterion, the pre-P0 sanity gate's quotations and the planned
    `tests/test_build_site.py:81` value. Corrected to **64 / 56 / 8**, verified by summing the column
    and cross-checked against the id inventory (22 surviving baseline slots + 42 new ids = 64; the two
    retired ids are not counted and the one renamed id reuses its slot). This is the second count
    family in this document to have been wrong, after the lessonMap count in gap 9 — the same lesson
    applies with more force: **a total row is not evidence; the column sum is.**
11. **Import identity was unstable across re-import until the final planning reconciliation**
    (2026-09-05). `sourceRef = IMPORT:<batchId>:<rowNo>` could never trigger the `UNIQUE` guard on a
    second upload, because `batchId` is generated per upload. Replaced by the content fingerprint in
    **D10.1**. The replacement carries three acknowledged gaps of its own, none of them closed by this
    pass: composite `UNIQUE (a, b)` is **0-hit** in the corpus (only single-column inline `UNIQUE` at
    `day21-blk-10`), `DataIntegrityViolationException` is **0-hit**, and a content fingerprint
    **collides** on two genuinely distinct same-account/same-day/same-amount/same-description
    transactions. The collision is surfaced to the learner in the import report rather than silently
    absorbed; see D10.1 for the accepted trade.

    > **Amended 2026-09-05 by the final import-identity correction.** The last two sentences are
    > **overturned.** Surfacing the collision in a report is not an adequate answer for a finance
    > ledger: the second legitimate transaction is still not created. D10.1 now defines a **two-level**
    > identity — a stable source-provided reference where the file has one, otherwise
    > `IMPORT:<baseFingerprint>|OCC:<occurrenceIndex>` — so two identical legitimate rows in one
    > statement become two transactions. The two *corpus* gaps in this item (composite `UNIQUE (a, b)`
    > 0-hit, `DataIntegrityViolationException` 0-hit) **still stand unchanged**. The collision gap is
    > replaced by the reordering limitation in **gap 13**.
12. **Maven is 0-hit in day-01 – day-11 and day-13/day-14** (measured 2026-09-05). The only early
    `pom.xml` in the corpus is a JMH snippet in day-12 and `mvnw` first appears at day-35, yet
    `task-project-foundation` requires a Maven project at day-01. This is a **labelled structural
    exception**: the task must carry its own Maven instructions in `constraints`, because no lesson in
    its window supplies them. It is recorded here so that TASK 7's "no task requires a technique before
    its earliest lesson" check passes *explicitly*, by disclosure, rather than silently.
    **Clarified 2026-09-05 (final import-identity correction):** the disclosure is that Maven at V0.1
    is **project/tooling scaffolding the mentor may guide**, not a Day-01 learning objective the
    learner derives from theory — see the §8 opening. The gap is unchanged; its framing is now
    explicit.
13. **The fallback identity is order-sensitive, and this is not universal bank-file dedup**
    (new 2026-09-05, final import-identity correction). `IMPORT:<baseFingerprint>|OCC:<n>` is stable
    for re-importing the **same logical statement ordering**. If a file is arbitrarily reordered,
    filtered or reconstructed and carries **no** source-provided reference, occurrence indices may be
    assigned differently and identities may change — producing an apparent duplicate or an apparent
    loss, visible in the import report but not prevented. A source-supplied stable transaction id
    (D10.1 Level 1) removes the limitation, which is why it is the preferred tier. What is
    **unverified**: no reordered-file scenario has been executed, because nothing is implemented; and
    `referenceId` / `externalId` / `OCC:` / `occurrenceIndex` are **all 0-hit in `content/`**, so both
    the preferred tier's field name and the fallback's counter are Spendwise inventions the V0.8 task
    must define from scratch. The mechanism they need (`Map.merge` / `computeIfAbsent` /
    `getOrDefault`) **is** taught, in one block: `day08-blk-27` (`content/lessons/day-08.json:211`).

---

## Verdict

`SPENDWISE_ARCHITECTURE_BLUEPRINT_FINAL`

**Amended 2026-09-05 by the pre-P0 sanity gate.** Six factual corrections and two additions were
applied to this file after it was first finalized; every one is marked in place. The corrections:
the lessonMap target (39 → **38**, and `day-33` reclassified from an addition to a **modification**),
the distribution (`14 theory` → **13**, delta −4 → **−5**), the
`tests/test_validate_project.py:174` row (a breakage → **not** a breakage), the `baseline` string
count (38 files → **39 files / 40 records**), the `assert(` count (62 → **61** call sites), and the
`compose.yml` count (25 → **22** occurrences in `content/`). The additions: **§7.1 R-DAY33**, which
binds the knowledge-unlock/project-execution separation to the data shape rather than to prose, and
**§8.1 `SPRING_BOOT_EXACT_PIN_PENDING`**, which withdraws the 3.4.x pin. Detail and evidence:
`docs/report/2026-09-05-spendwise-pre-p0-sanity-gate.md`.

**Further amended 2026-09-05, same gate, after adversarial verification.** Two of the gate's own
supporting arguments were refuted by an independent verifier and have been rewritten in place rather
than left standing:

1. **§8.1's "the corpus's 6.5 citations mean the line should be 3.5.x" is withdrawn as refuted.**
   Day-33's authentication code compiles clean and deprecation-free against Spring Security
   **6.4.13** (Boot 3.4.13); all 26 security types resolve; every 6.5-only API is 0-hit in the
   corpus. No line is preferred on compile grounds. §8.1 now argues from support lifecycle instead
   (new **Reason 3**), which is external, dated, and the weakest link in the section.
2. **§7.1's "R-DAY33 is the only route that suppresses the CTA" is withdrawn as overstated.**
   `applicationType: future` + `buildTaskIds: []` suppresses it too and already ships on **three**
   lessons (day-05, day-11, day-12). §7.1's rendering table is now **6 rows**, and it records that
   `theory` is not a safety mechanism — a `theory` entry carrying an `application` key renders the
   full required CTA and validates clean, because the guard at `index.template.html:2895` is on the
   *field*, not the type.

**Further amended 2026-09-05 by the final import-identity correction (fourth amending pass).** The
import identity model in **D10.1** was replaced a second time, and four smaller sites were reconciled
to it. What changed:

1. **The bare content fingerprint is withdrawn.** Its documented behaviour — two legitimate
   transactions with the same account, date, direction, amount and description collapse into one, and
   the loss is *reported* to the learner rather than prevented — is not acceptable for a finance
   ledger. Replaced by a **two-level** identity: `IMPORT:SRC:<sourceKey>:<accountId>:<sourceTxnId>`
   when the file carries a stable source reference, otherwise
   `IMPORT:<baseFingerprint>|OCC:<occurrenceIndex>`. Two byte-identical data rows in one statement now
   import as **two** transactions (`OCC:1`, `OCC:2`), and re-importing that same file adds **0** and
   reports **2** `DUPLICATE` rows. `IMPORT:<batchId>:<rowNo>` remains rejected: a fresh `ImportBatch`
   PK on re-upload can never collide, so it cannot be idempotent.
2. **A new order-dependence constraint** was added as a **second clause of R22** — not a new rule id,
   because `buildSteps.architectureRules` is validated against `^R\d{1,2}$` and the rule set stays at
   **26**. The occurrence counter is only reproducible if the parser walks the file **sequentially in
   source-file order**; `parallelStream` (**12** corpus hits) would break it.
3. **A limitation replaced a claim.** The fingerprint's "accepted collision cost" is gone; in its
   place, gap **13** states that the fallback is stable for re-importing the *same logical statement
   ordering* only, and that this is **not** universal bank-file deduplication.
4. **R-CAPSTONE-GUARD** was added to §7.1 — *Day 31–36 must not expose a required Spendwise
   build-task CTA* — as a **test/self-test requirement that changes no UI**, closing the pre-P0
   gate's finding that R-DAY33 was an authoring convention with **zero** mechanical guards.
5. **§8's Maven wording** was clarified: Maven + Wrapper at V0.1 is project/tooling **scaffolding the
   mentor may guide**, not a Day-01 learning objective the learner derives from theory.

**No count moved in this pass.** 64 buildTasks / 56 required / 8 optional / 31 features / 38 lessonMap
entries / ≈229 buildSteps are all unchanged, and no implementation file was touched.

**What to challenge**, in order: **the fallback identity's order-dependence (gap 13)** — the whole
idempotency guarantee rests on the assumption that a re-uploaded statement presents the same rows in
the same order, which is *asserted from the shape of the format and never tested*, because nothing is
implemented; **the invention of both identity tiers' vocabulary** — `referenceId`, `externalId`,
`OCC:`, `occurrenceIndex` and `occurrence` are **all 0-hit in `content/`**, so the V0.8 task must
define field names and a counter the corpus never names (the *mechanism* is taught, once, at
`day08-blk-27`); **the judgement that `OCC:` is better than surfacing a collision**, which buys
correctness for identical legitimate rows at the price of a reordering failure mode that is harder for
a learner to reason about than a duplicate report;
the signed-effect ledger and its invented `openingBalance`; the
withdrawal of the framework-purity claim; **§8.1's Reason 3 — that the Spring Boot decision is now an
out-of-support-line choice** rather than a corpus-derivable pin, which rests entirely on external
lifecycle data fetched on 2026-09-05 and on the judgement that shipping an unsupported line to
learners is worse than falsifying one lesson comment (note that §8.1's *earlier* argument, that the
`6.5` doc citations imply the 3.5.x line, has been **withdrawn as refuted** — day-33 compiles clean
on Security 6.4.13, so no line is preferred on compile grounds);
**§7.1's decision to leave `lessonMap["day-33"].buildTaskIds` permanently empty**, which trades
day-33 → task discoverability for CTA suppression — and note that the empty *list* is what is legal,
the *key* is mandatory, and the live alternative `future` + `[]` (day-05/11/12) suppresses the CTA
too, so `direct` is a preference and not a forced move; the demotion of refresh-token rotation to
optional; the post-day-36 placement of the required `TokenIssuer` task; and the derived 64/56 task
counts (**amended 2026-09-05 from 58/50 by the final planning reconciliation — the total row was an
addition error against its own per-release rows**).

**Repository state.** Baseline `e97c13a`, unchanged. Three files written across the two sessions,
all untracked planning documents: this file, `docs/spendwise-alignment-phase2-plan.md`, and
`docs/report/2026-09-05-spendwise-pre-p0-sanity-gate.md`. **Nothing was implemented.**
`content/spendwise-project.json`, `content/lessons/*`, `tools/*`, `tests/*`,
`index.template.html` and `index.html` are all untouched — re-verified on 2026-09-05 by
`git status --short`, which reports zero modified tracked files. **Nothing was committed. Nothing was
pushed. No report was `git add`ed.**

> *Amended 2026-09-05 (fourth pass).* Two further untracked reports now exist —
> `docs/report/2026-09-05-spendwise-final-reconciliation-report.md` and
> `docs/report/2026-09-05-spendwise-import-identity-finalization-report.md` — and this file plus
> `docs/spendwise-alignment-phase2-plan.md` were edited again. The implementation statement is
> **unchanged and re-verified**: zero modified tracked files, nothing staged, nothing committed,
> nothing pushed.

**What happens next if approved.** Phase 2's P0 wave becomes executable: the schema extensions
(`buildSteps`, `alsoUsedIn`) and their validator support land first, together with the
`STATE_VERSION` 2→3 migration and self-test #53's `emptyRelease` premise — **P0 is plumbing only and
adds no route and no learner-visible rendering** (*amended 2026-09-05: the `#/task/:taskId` route and
the task detail view were moved out of P0 to P3, restoring "Data first. UI second."*). Then the
artifact rewrite to **64** tasks / 31 features / **38** lessonMap entries and the two
`tests/test_build_site.py:80-81` assertions, then the `#/task/:taskId` route and the mentor-prompt UI
in P3. The order is fixed by one constraint: `tools/build_site.py` validates before it embeds, so an
artifact that outruns its validator fails the build instead of shipping.
`SPRING_BOOT_EXACT_PIN_PENDING` does **not** block P0, and — *amended 2026-09-05* — it does **not**
block `task-project-foundation` either: V0.1 is pure Java with no Spring dependency. It is a hard
prerequisite of **`task-spring-bootstrap` (V0.3)**, the first task that adds
`spring-boot-starter-parent`. See §8.1.

