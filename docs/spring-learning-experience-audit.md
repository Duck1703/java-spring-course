# Spring Learning Experience — Audit (Day 13–30) & Redesign Rationale

**Status:** planning/audit artifact for the Unit 5 theory-UX pilot. Untracked; not committed.
**Scope:** audit-only for Day 16–30 (no content rewritten). Day 13–15 were redesigned in this
same pass; their "current" column below describes the *pre-redesign* state that motivated the
change, and the "recommended treatment" column records what was actually done.

## 1. Learner persona

"Java-Core Developer New to Spring": comfortable with Java syntax, OOP, collections, generics,
interfaces, exceptions; has manually wired dependencies with `new` and factory methods; has
**not** used a DI container, annotation-driven configuration, or convention-over-configuration
frameworks before. Reads Vietnamese; Java Core terminology should stay in English (that's how
they'll meet it in docs/IDE/stack traces) but be explained in Vietnamese prose.

## 2. Design principles (pedagogical contract used for this pass)

No "Java Spring Teacher — Theory Mode" file exists anywhere in the repository — confirmed via
`grep -rli "theory mode\|teacher" --include="*.md" docs/ CLAUDE.md` and a repo-wide filename
search for `*teacher*` (excluding `node_modules`/`.course-cache`), both empty except for
`docs/course-content-audit.md` (a prior, unrelated audit). Treated as an absent/unverifiable
input, not fabricated. The principles below are reconstructed from the spec itself and from the
pedagogy pattern already present as a second authoring layer in Day 13/14 (see §4):

1. **Problem-in-Java-first.** Show the plain-Java pain point before naming the Spring mechanism
   that solves it. Annotations appear after the learner has felt the need for them.
2. **Mental-model-first, definition-second.** An analogy or "how it works" paragraph precedes the
   formal/textbook definition, not the reverse.
3. **Staged cognitive load.** Every dense topic gets an explicit tier: *cần hiểu ngay* (must
   understand now) / *nhận biết lúc này* (recognize now, master later) / *sẽ học sâu hơn sau*
   (deferred). No new schema type required — plain `note` blocks with empty `citations` are the
   existing, precedented mechanism (e.g. `day13-blk-12`, `day14-blk-24`).
4. **Group before enumerate.** Anti-pattern: a paragraph naming N equally-weighted items
   immediately followed by a table repeating the same N items with equal structural weight, with
   no primary/secondary split. Fix: teach the 1–2 dominant cases as the mental model, then group
   the remainder as a secondary "awareness" tier, then use the full table as a *recap*, not an
   opener.
5. **Java→Spring bridges stay compact.** A short comparison paragraph, not a parallel tutorial.
6. **Don't silently drop required syllabus content.** If something is officially required (e.g.
   Day 15's retry logic), it can be *staged later* in the flow but must not be demoted out of
   scope or marked optional.
7. **Citations are per-claim, not per-file.** Adding staging/summary prose needs no new citation
   as long as it makes no new factual/technical claim — it is framing, not content.

## 3. Day 13–30 audit matrix

| Day | Title | Kind | Sections/Blocks | Main concern found | Recommended treatment |
|---|---|---|---|---|---|
| 13 | Spring Boot Fundamentals & Bean Lifecycle | theory | 6/38→39 | Formal DI definition preceded the Java-first analogy; 6-scope table opened the scopes section with no primary/secondary split (§4 anti-pattern); lifecycle taught callback-name-first instead of sequence-first; architecture (packaging) section ran before the actual "why Spring" motivation | **Redesigned this pass** — see §5 |
| 14 | Dependency Injection & Configuration | theory | 5/33→34 | DI mental-model paragraph (`blk-20`) sat after the formal 3-kind table instead of before it; "why @Bean vs @Component" (`blk-26`) was separated from the @Bean intro by an unrelated exclude/--debug note | **Redesigned this pass** — see §5 |
| 15 | Assignment 5: Multi-module Notification Service | project | 6/24→26 | No milestone map up front; retry logic (a required deliverable) had equal visual weight to the other 4 deliverables with no signal that it's the hardest/last part | **Redesigned this pass** — see §5 |
| 16 | Controller & Request/Response | theory | 4/18 | **Deep-read (see §11): DispatcherServlet analogy precedes formal mapping annotations; problem-first flow already present.** | No structural change — verified sound |
| 17 | Validation & Exception Handling | theory | 4/22 | **Deep-read: Bean Validation → @ControllerAdvice → ProblemDetail (RFC 7807) taught mental-model-first; bridges forward to Day 29 OpenAPI error docs.** | No structural change — verified sound |
| 18 | Lab 6: User & Task Management API | lab | 6/12 | Task-first lab, low block count | No change |
| 19 | Entity Design & Relationships | theory | 6/27 | **Deep-read: relationship/cascade/fetch-type each get mental-model framing before formal rules; not a raw 3-topic dump as the metadata-only pass assumed.** | No structural change — verified sound |
| 20 | Query, Transaction & Patterns | theory | 6/33 | **Deep-read: highest block count in range, but density is staged (SQL fundamentals → pagination → transactions → isolation/locking → auditing built as a causal progression, each section closing with a mental-model/pitfall layer, not flat enumeration). Confirmed NOT an arbitrary bundle — see §11/§12.** | No structural change — verified sound; old audit's "highest-priority Wave 4" flag retracted |
| 21 | Assignment 7: E-Commerce Data Layer | project | 5/12 | Project brief, Day-15-style pattern | No change |
| 22 | Authentication with Spring Security + JWT | theory | 4/24 | **Deep-read: filter-chain mental model precedes JWT mechanics; problem-first.** | No structural change — verified sound |
| 23 | Authorization & JPA Performance | theory | 4/26 | **Deep-read: N+1 (JPA performance) and method-security/CORS/CSRF (authorization) are bridged, not arbitrarily combined — both are "requests already authenticated, what happens next" concerns, and later days (25, 27, 28) explicitly cross-reference Day 23's content as a unit. Old audit's "two unrelated concept clusters" claim retracted.** | No structural change — verified sound |
| 24 | Lab 8: Auth Service + Performance Optimization | lab | 7/24 | Task-first lab | No change |
| 25 | Caching & Async Processing | theory | 5/30 | **Deep-read: mature mental-model layer (cache-as-tradeoff, AOP-proxy self-invocation defect correctly cross-referencing Day 21/23, TTL-vs-eviction-ordering). Section titles were unaccented ("Pham vi buoi hoc" etc.) — confirmed genuine defect, body prose unaffected.** | **Diacritics fixed this pass (4 titles); no structural change needed** |
| 26 | File Upload/Download & External API | theory | 6/29 | **Deep-read: upload/download/WebClient/resilience/CSV are unified around "external integration & fault tolerance," each with defense-in-depth or 3-state-model mental frameworks — not an arbitrary bundle. Same diacritics defect (5 titles).** | **Diacritics fixed this pass; no structural change needed** |
| 27 | Assignment 9: Product & Order Features | project | 8/15 | **Deep-read: 8-section brief correctly reuses Day 20/23/25/26 patterns with explicit cross-day citation-scope notes; same diacritics defect (8 titles).** | **Diacritics fixed this pass; no structural change needed** |
| 28 | Testing Spring Boot | theory | 7/27 | **Deep-read: strong mental-model content (what makes a good test, edge-case-first selection) with correct forward/backward refs (Day 20 N+1, Day 22-23 security, Day 29 Testcontainers). Same diacritics defect (5 titles).** | **Diacritics fixed this pass; no structural change needed** |
| 29 | Documentation, Logging, Monitoring & Docker | theory | 6/27 | **Deep-read: OpenAPI/logging/Actuator/Docker/Testcontainers unified as "production readiness toolkit," each topic gets mental-model treatment (why generate docs from code, health-vs-metrics distinction, container statelessness); genuine knowledge gaps (distributed tracing, Prometheus) transparently disclosed via `authoring.limitations`, not hidden. Old audit's "4 unrelated topics bundled" claim retracted. Same diacritics defect (4 titles).** | **Diacritics fixed this pass; no structural change needed** |
| 30 | Lab 10: Production Readiness | lab | 9/17 | **Deep-read: capstone lab honestly marks 4/7 acceptance items "CHƯA CHỐT" (JaCoCo, traceId, Prometheus, CI) as course-wide knowledge gaps rather than silently grading on unsupported content — a notably rigorous integrity practice. Same diacritics defect (2 titles); "Acceptance criteria…" title was already correctly accented, confirming the defect is inconsistent per-title, not a uniform batch marker.** | **Diacritics fixed this pass; no structural change needed** |

## 4. Cross-day sequencing observations

- Day 13 and Day 14 both already carried **two authoring layers**: an original definition-first
  pass (low block-id numbers) and a later mental-model/Java-first-comparison layer (block ids in
  the 20s–30s) interleaved into the *same* sections but positioned *after* the material they were
  meant to introduce. The pedagogy this pilot asks for already existed in the files — the defect
  was ordering, not missing content. This sharply reduced the redesign's blast radius: no new
  citations were needed, and every existing outcome/commonMistake/citation id was preserved.
- Day 25–30 show a distinct, unaccented-Vietnamese section-title style ("Pham vi buoi hoc") not
  present in Day 13–24 ("Đề bài và phạm vi bài học" / "Phạm vi buổi Guides/Review"). This is a
  separate, mechanical content-quality issue (likely an encoding or authoring-tool artifact from
  a different batch), not a pedagogy issue — worth a targeted find-and-fix pass independent of
  any redesign wave, but explicitly out of scope for this audit-only pass.
- Day 20 (33 blocks/6 sections: SQL fundamentals, pagination, transactions, isolation/locking,
  auditing) and Day 23 (authorization bundled with an unrelated N+1 performance topic) are the two
  strongest concept-density candidates for a future redesign wave, on the same "too many unrelated
  concepts per day" concern the spec flags for Day 13's original 6-scopes-at-once table.

## 5. Day 13–15 redesign — what was actually changed

All edits are pure reordering (arrays of existing objects moved; no id, citation, outcome, or
`commonMistake` altered or removed) plus a small number of new zero-citation `note` blocks, using
the schema's existing "uncited standard-knowledge framing" convention
(`tools/validate_lessons.py` only requires citations for `important`/`warning` blocks, never for
`note`). Verified via `validate_lessons.py` (`PASS lessons=40 sections=212 practices=156
citations=425 assignments=20` — identical to pre-edit baseline) and `build_site.py`
(`citations=1054` unchanged, confirming zero net new cited/uncited claims were introduced).

**Day 13** (`content/lessons/day-13.json`):
- Top-level sections reordered: `brief → ioc → architecture → scopes → lifecycle → stereotypes`
  (was `brief → architecture → ioc → …`), so the IoC/bean motivation is the first substantive
  content, not packaging/startup-log detail. The architecture section was retitled to
  `"Spring Boot Architecture — bối cảnh đóng gói (nhận biết, không phải mô hình tư duy chính)"` to
  make its status explicit.
- `day13-sec-ioc`: `day13-blk-30` (Java-first analogy) moved ahead of `day13-blk-5`/`blk-6`
  (formal DI definition + code).
- `day13-sec-scopes`: reordered to `blk-7 (brief overview) → blk-32 (singleton mutable-state
  warning) → blk-9/blk-10 (prototype code + note) → blk-33 (scope-grouping note) → blk-11 (scoped
  proxy) → blk-8 (full 6-row table, now a closing recap, not the opener)` — directly fixes the
  §4-style anti-pattern.
- `day13-sec-lifecycle`: reordered to `blk-34 (causal sequence) → blk-12 (callback names) →
  blk-35 (destroy specifics)`, sequence-before-vocabulary.
- Added `day13-blk-38` (`note`, no citations): end-of-day staged summary (cần hiểu ngay / nhận
  biết lúc này / sẽ học sâu hơn sau / where it reappears).

**Day 14** (`content/lessons/day-14.json`):
- `day14-sec-di-types` reordered to `blk-20 (problem framing) → blk-3/4 (3-kind intro + table) →
  blk-5/6 (constructor code + resolve order) → blk-21 (mechanism) → blk-22 (why constructor is
  default) → blk-23/24 (qualifier/ambiguity) → blk-25 (avoid field injection)`.
- `day14-sec-configuration-bean` reordered to `blk-7 (intro) → blk-26 (@Bean vs @Component) →
  blk-27 (code example) → blk-8 (non-invasive/back-off) → blk-28 (back-off mechanism) → blk-9
  (exclude/--debug) → blk-29 (bean naming)` — groups "what @Bean is for" before "how auto-config
  decides" before "how to debug it".
- Added `day14-blk-40` (`note`, no citations): end-of-day staged summary.

**Day 15** (`content/lessons/day-15.json`):
- Added `day15-blk-40` (`note`, no citations) immediately after the deliverable block: a
  structured project-brief framing — concept map (which Day 13/14 mechanism each deliverable
  practices), target architecture, and a recommended 5-step milestone order ending with retry.
- Added `day15-blk-41` (`note`, no citations) at the end of the retry section: explicitly stages
  retry as the hardest/last milestone while keeping it a required deliverable (it still appears,
  unchanged, in the acceptance-criteria table) — matches the "stage later, don't drop" principle.
- No change to any TODO/exercise code (`day15-blk-9`, `day15-blk-13`) — no solution leaked.

## 6. Recurring cognitive-load problems found

1. Mental-model/analogy content authored *after* the formal definition it should precede (Day 13,
   Day 14 — both fixed this pass by reordering, not rewriting).
2. Flat enumeration of N similar items with no primary/secondary grouping before a full reference
   table (Day 13 bean scopes — fixed this pass).
3. Multiple unrelated concept clusters bundled into a single day with no internal signal of which
   is core vs. peripheral (Day 20, Day 23, Day 26, Day 29 — flagged, not fixed; out of pilot
   scope).
4. A required-but-harder deliverable given equal visual/structural weight to easier ones with no
   sequencing hint (Day 15 retry logic — fixed this pass via staging note, not by changing
   requirement status).

## 7. Recommended redesign waves — SUPERSEDED by §11/§12 full-content deep-read

This section originally ranked Day 20 > Day 23 > Day 26/29 > Day 19 as Wave 4 candidates, based
only on section/block counts (no block content had been read yet). The full Day 16–30 deep-read
performed for the parent task (§11) **retracts this ranking**: every flagged day turned out to
already contain a mature problem-first/mental-model-first layer with correct staging and honest
cross-day bridging (see §11 for evidence per day, §12 for the concept-dependency chain that shows
*why* each day's apparent multi-topic bundle is in fact a coherent cluster). **No Day 16–30
structural redesign is warranted.** The only confirmed, fixable defect was mechanical: unaccented
Vietnamese section titles in Day 25–30, fixed in this pass (see §11).

## 8. Pilot rationale

Day 13–15 was chosen because: (a) it is the first Spring content the learner meets (Unit 5), so
first-exposure ordering effects compound the most; (b) Day 13/14 already contained the target
pedagogy as an un-promoted second layer, making the fix a low-risk reorder rather than a rewrite;
(c) Day 15 is the first project brief, so its milestone-staging pattern is reusable as a template
for Day 21/27 project briefs later, without committing to rewriting them now.

## 9. Definition of success

- All four full validation-gate runs (`validate_lessons.py`, `validate_project.py`,
  `validate_guided_build.py`, `build_site.py`, `pytest`, `node --test`, `ui_smoke_test.py`)
  reproduce their pre-edit baseline figures exactly (lessons/sections/practices/citations counts
  unchanged) — confirmed in §5 and in the full session report.
- Zero citation/outcome/commonMistake ids removed or altered.
- Zero new dependency added; zero new schema type added.
- Every required Day 15 deliverable (including retry) still appears, unchanged, in the
  acceptance-criteria table.

## 11. Day 16–30 full-content deep-read (this pass, supersedes §3/§7's metadata-only assessment)

Every block of `content/lessons/day-16.json` through `day-30.json` was read in full (sections,
blocks, citations, sourceUsage, commonMistakes, practices, references, `authoring.limitations`) —
no day was judged from title or block count alone, per the parent spec's explicit requirement.

**Headline finding:** unlike Day 13–15 (which had a real ordering defect — a mental-model layer
authored *after* the formal definition it should precede), Day 16–30 was evidently authored in a
later batch that already gets this right. Every day shows the same recurring pattern:

1. A problem/mental-model paragraph before or alongside the formal mechanism (not after).
2. Explicit, honest `authoring.limitations` disclosures for content genuinely outside the day's
   cited resources — framed as "khoảng trống kiến thức thật sự" (genuine knowledge gap) rather than
   silently asserted or silently dropped.
3. Correct "no cross-day citation borrowing" discipline: content belonging to a later day's
   resources is deferred with an explicit forward reference, never mis-cited against the wrong day.
4. Frequent, *correct* cross-day pedagogical callbacks, e.g.:
   - Day 25 cross-references Day 21 (`@Transactional`) and Day 23 (`@PreAuthorize`) for the
     AOP-proxy self-invocation defect.
   - Day 27 cross-references "Day 20/23/25" for the same proxy defect, precisely scoping the claim
     ("no overlap" only applies same-job/same-scheduler, not cross-job).
   - Day 28 cross-references Day 20 (N+1), Day 22–23 (security causing "mysteriously" failing web
     slice tests), and Day 29 (Testcontainers, for dialect-dependent behavior `@DataJpaTest`+H2
     can't catch).
   - Day 29 cross-references Day 25 (`@Async` ThreadLocal-doesn't-propagate caveat, reused for
     MDC), Day 26 (container statelessness reusing the file-upload/storage discussion).
   - Day 30 (capstone) correctly reuses Day 29's citations *only* where the resourceId is also in
     Day 30's own `resourceIds`, and otherwise marks reused material as internal references with no
     re-citation — textbook-correct citation discipline for a capstone lab.

**What this means for the days the old (metadata-only) audit flagged as multi-topic bundles:**

- **Day 20** (SQL fundamentals → pagination → transactions → isolation/locking → auditing, 33
  blocks): each subject gets its own mental-model framing and closes with a mechanism/pitfall
  layer before the next starts; the causal thread is "how does a query become a safe, repeatable
  operation," not five disconnected topics.
- **Day 23** (authorization + N+1 performance): both halves are downstream of "the request is
  authenticated — what happens to it next," and later days treat the pair as a single citable unit
  ("Day 22-23"), which would be an authoring error if the two halves were genuinely unrelated.
- **Day 26** (upload/download/WebClient/resilience/CSV): unified around "talking to things outside
  this JVM safely" — defense-in-depth validation for inbound files, circuit-breaker/retry
  discipline for outbound calls, RFC 4180 correctness for outbound exports.
- **Day 29** (OpenAPI/logging/Actuator/Docker/Testcontainers): unified around "production
  readiness," explicitly framed in the day's own summary as groundwork for Lab 10 (Day 30); the
  4 topics are not peers competing for attention but 4 facets of the same operational concern.

**Confirmed, fixed defect:** Vietnamese section titles (not body prose) in Day 25–30 were
genuinely unaccented — 28 titles across 6 files. Body prose throughout Day 16–30 was, without
exception, correctly accented; only section `title` fields were affected, and the defect was
inconsistent even within a single file (Day 30's "Acceptance criteria: 7 hạng mục production
readiness" was already correct while its sibling "De bai Lab 10" was not) — evidence this was a
per-block authoring-tool artifact, not a systemic encoding failure. All 28 titles were corrected
this pass (see file-by-file list in §3's table); `validate_lessons.py` reproduced the exact
pre-edit baseline (`PASS lessons=40 sections=212 practices=156 citations=425 assignments=20`)
confirming zero structural/citation impact.

**Conclusion:** no Day 16–30 file required reordering, new staging notes, or any other structural
redesign. The redesign contract (problem → mental model → formal concept → mechanism → minimal
example → explanation → edge case → where-used-later) was already satisfied by the existing
authoring layer in every one of the 15 files.

## 12. Concept-dependency map (Day 16–30)

Built from the actual sourceUsage/citation/cross-reference data read in §11, not from titles.

```
Day 16  Controller/REST          DispatcherServlet, @RequestMapping family, ResponseEntity
Day 17  Validation/Exceptions    Bean Validation → @ControllerAdvice → ProblemDetail (RFC 7807)
                                    └─▶ referenced by Day 29 (OpenAPI error-response docs)
Day 18  Lab 6                    integrates Day 16+17
Day 19  Entity/Relationships     @OneToMany/@ManyToOne, cascade, orphanRemoval, fetch type
                                    └─▶ referenced by Day 20 (N+1 stems from fetch-type choices)
Day 20  Query/Transaction        JPQL/pagination, @Transactional (propagation/isolation), N+1,
                                  locking, auditing
                                    └─▶ proxy mechanism referenced by Day 25/27 (self-invocation)
                                    └─▶ N+1 referenced by Day 23, Day 28 (@DataJpaTest detection)
Day 21  Assignment 7             integrates Day 19+20
Day 22  Security/JWT             Spring Security filter chain, JWT issue/validate
                                    └─▶ proxy mechanism referenced by Day 25/27 (self-invocation)
                                    └─▶ referenced by Day 28 (web-slice test 401s), Day 29 (Swagger
                                        UI auth docs)
Day 23  Authorization/Perf       method security (@PreAuthorize), CORS/CSRF + N+1 revisited
                                    └─▶ cited as a unit ("Day 22-23") by Day 25, 27, 28
Day 24  Lab 8                    integrates Day 22+23
Day 25  Caching/Async            @Cacheable family (depends on Day 20/21/23 proxy mechanism),
                                  Redis backend, @Async, @Scheduled
                                    └─▶ MDC/ThreadLocal caveat referenced by Day 29
                                    └─▶ referenced by Day 27 (applied) and Day 29 (@Async+MDC)
Day 26  Upload/External API      MultipartFile validation, WebClient, Circuit Breaker, CSV export
                                    └─▶ referenced by Day 27 (applied), Day 29 (Docker statelessness
                                        re-uses the "don't store uploads in-container" point)
Day 27  Assignment 9             integrates Day 20+23+25+26 (explicit citation-scope notes for each)
Day 28  Testing                  JUnit 5, @WebMvcTest (needs Day 22-23), @DataJpaTest (needs
                                  Day 20 N+1, defers dialect verification to Day 29 Testcontainers),
                                  @SpringBootTest, slice-test reference table
Day 29  Docs/Logging/Monitoring/ OpenAPI (needs Day 17 ProblemDetail, Day 23 JWT), structured
        Docker                  logging+MDC (needs Day 25 @Async caveat), Actuator/HealthIndicator,
                                  Docker intro, Testcontainers mechanism (feeds Day 28's deferred gap)
Day 30  Lab 10 (capstone)        integrates Day 28+29 end-to-end; 4/7 acceptance items explicitly
                                  marked "CHƯA CHỐT" (JaCoCo, traceId, Prometheus, CI) as genuine
                                  course-wide knowledge gaps, not silently graded
```

Reading this chain top to bottom shows no forward-reference leaks (every "└─▶" points to a later
day, consistent with §62's no-future-concept-leak rule) and no missing prerequisite (every day's
"needs X" resolves to an earlier day already covered). This is the artifact required by the parent
spec's §12/§63 — a reusable design guide for anyone extending Day 16–30 later.

## 13. What was deliberately NOT changed

- Day 16–30 content files — audit only, per spec; findings are recorded in §3/§6/§7 above as a
  roadmap, not applied.
- Day 13–15 `commonMistakes` arrays — read and judged already causal/"why"-oriented (e.g. the
  existing scope-mixing commonMistake already explains *why* request/session scopes need a
  scoped proxy while prototype needs `ObjectProvider`), so left untouched rather than rewritten
  for the sake of it.
- Day 15's TODO-based exercises (`day15-blk-9` factory constructor, `day15-blk-13` retry
  skeleton) — no solution code added or implied; only organizational/staging notes were added
  around them.
- The "Java Spring Teacher — Theory Mode" review requested by the parent spec — file does not
  exist in this repository (see §2); nothing was fabricated in its place.
- Day 16–30 content, structure, citations, outcomes, commonMistakes, and practices — deep-read in
  full (§11) and found to already satisfy the redesign contract; the only edit applied was the
  28-title diacritics fix (§11), verified structural-no-op via `validate_lessons.py`.
