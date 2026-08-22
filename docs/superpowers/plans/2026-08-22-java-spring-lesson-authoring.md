# Java Spring Lesson Authoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Biên soạn đầy đủ 40 lesson/activity packages tiếng Việt từ outline thật và source notes đã đọc, giữ nguyên assignment gốc, thêm 2–4 bài Practice và tạo citation/source-usage map kiểm chứng được.

**Architecture:** Mỗi lesson là một JSON độc lập theo schema cố định để có thể biên soạn song song và validation tự động. Lesson technical chỉ được citation tới source-note facts có `read.status=read`; validator kiểm tra source coverage, assignment preservation, Java 17/Spring Boot 3.x, số lượng practice và mọi internal ID trước khi publisher sử dụng.

**Tech Stack:** JSON, Python 3.13 standard library, Java 17-compatible source snippets, Spring Boot 3.x/Spring Framework 6 conventions, `unittest`.

## Global Constraints

- Consumes the validated source corpus from `content/source-manifest.json` and `content/source-notes/*.json`; do not author technical lessons before source validation passes.
- Vietnamese explanations; retain English technical terms, API/annotation/class names and code.
- Java examples target Java 17 language/runtime behavior; Spring examples target Spring Boot 3.x and Spring Framework 6/Jakarta namespaces.
- Use actual accessible source-page facts; no source may be cited solely because its URL appears in the syllabus.
- Every theory section has nonempty `sourceUsage`; each resource ID must be readable and linked to the lesson.
- Preserve syllabus assignments verbatim in `syllabusAssignments`; enrichment is separate.
- Every lesson/activity has 2–4 practices, hints and hidden solutions/reference answers.
- Technical lessons have at least one code/config example; project/OJT/evaluation lessons instead have a concrete deliverable example or template.
- Never copy a source run longer than 300 characters; paraphrase and cite.
- No backend/runtime AI dependencies.
- The user authorized a local Git repository on 2026-08-22 for worktree/diff review; each task commits locally after validation and nothing is pushed without separate authorization.

---

## File Structure

- Create: `content/lesson-schema.json` — declarative schema/reference for lesson fields.
- Create: `tools/validate_lessons.py` — cross-file semantic validator.
- Create: `tests/test_validate_lessons.py` — validation fixtures and regression tests.
- Create: `content/lessons/day-01.json` through `content/lessons/day-38.json` — one file per detailed Day.
- Create: `content/lessons/ojt-evaluation.json` — contains `day-39-64` and `day-65-66` activity packages.
- Create: `content/lesson-index.json` — generated ordered list and module/group aggregates.
- Create: `content/lesson-authoring-report.md` — coverage, source use, practices and limitations.

## Shared Lesson Interface

All `day-XX.json` files follow this exact top-level shape:

```json
{
  "schemaVersion": 1,
  "id": "day-01",
  "catalogRef": "day-01",
  "unitId": "unit-01",
  "group": "java",
  "kind": "theory",
  "title": "JVM, JRE, JDK & Data Types",
  "summary": "Vietnamese lesson summary grounded in the outline.",
  "durationMinutes": 150,
  "objectives": ["LO1"],
  "prerequisites": [],
  "outcomes": ["Observable outcome in Vietnamese"],
  "sections": [],
  "commonMistakes": [],
  "practices": [],
  "syllabusAssignments": [],
  "enhancedExercises": [],
  "references": [],
  "sourceUsage": [],
  "authoring": {
    "baseline": "Java 17 / Spring Boot 3.x",
    "reviewStatus": "reviewed",
    "limitations": []
  }
}
```

Allowed `kind`: `theory|lab|project|exam|ojt|evaluation`.

A section:

```json
{
  "id": "jvm-architecture",
  "title": "JVM Architecture",
  "body": [
    {"type": "paragraph", "text": "Vietnamese paraphrase grounded in the cited source fact.", "citations": ["cite-day-01-01"]},
    {"type": "important", "title": "Điểm cần nhớ", "text": "A concise technical caution grounded in the cited source fact.", "citations": ["cite-day-01-01"]},
    {
      "type": "code",
      "language": "java",
      "caption": "Primitive và wrapper",
      "code": "int count = 42;\nInteger boxed = count;",
      "citations": ["cite-day-01-02"]
    }
  ],
  "sourceUsage": ["cite-day-01-01", "cite-day-01-02"]
}
```

A source-usage entry:

```json
{
  "id": "cite-day-01-01",
  "resourceId": "the matching res- ID from content/source-manifest.json",
  "sectionIds": ["jvm-architecture"],
  "sourceLocators": ["2.5 Run-Time Data Areas"],
  "usedFacts": ["JVM runtime areas and their roles"],
  "note": "Tổng hợp/diễn giải, không sao chép nguyên văn."
}
```

A practice:

```json
{
  "id": "day-01-practice-01",
  "type": "predict-output",
  "title": "String pool và toán tử ==",
  "prompt": "Dự đoán kết quả và giải thích.",
  "interaction": "self-check",
  "choices": [],
  "correctChoiceIds": [],
  "explanation": "`==` so sánh reference; hãy đối chiếu với lời giải sau khi tự trả lời.",
  "starterCode": "String a = \"java\";\nString b = new String(\"java\");\nSystem.out.println(a == b);",
  "hint": "So sánh reference trước khi so sánh nội dung.",
  "solution": "false — `a` trỏ vào pooled literal còn `b` trỏ vào object được tạo bằng `new`; `==` so sánh hai reference.",
  "rubric": [
    {"criterion": "Kết quả", "points": 1},
    {"criterion": "Giải thích", "points": 2}
  ],
  "sourceUsage": ["cite-day-01-03"]
}
```

Allowed practice types: `concept|predict-output|coding|applied`. Allowed interactions are `self-check|multiple-choice`. A `multiple-choice` practice has 2–6 `{id,text}` choices, one or more `correctChoiceIds`, and a nonempty `explanation`; a `self-check` practice uses empty choice arrays and reveals its explanation with the hidden solution.

---

### Task 1: Lesson Schema and Semantic Validator

**Files:**
- Create: `content/lesson-schema.json`
- Create: `tools/validate_lessons.py`
- Create: `tests/test_validate_lessons.py`

**Interfaces:**
- Consumes: catalog, manifest, source notes, lesson directory.
- Produces: `validate_lesson(lesson: dict, catalog_lesson: dict, source_index: dict) -> list[str]`.
- Produces: `validate_corpus(catalog: dict, lessons: list[dict], source_index: dict) -> list[str]`.
- Produces: CLI `python tools/validate_lessons.py --catalog course-catalog.json --manifest content/source-manifest.json --source-notes-dir content/source-notes --lessons-dir content/lessons`.

- [ ] **Step 1: Write failing tests for a minimal valid lesson and required rejections**

Tests must reject:

```text
- lesson ID not in catalog
- unit/group/title/objectives mismatch with catalog
- a technical section with empty sourceUsage
- citation to blocked/unread source
- citation to resource not linked to this lesson
- citation locator absent from the source note
- practice count outside 2–4
- practice without hint, solution or explanation
- multiple-choice practice with fewer than two choices, unknown correctChoiceIds or no correct answer
- self-check practice with nonempty choices/correctChoiceIds
- technical lesson without code/config block
- copied 301-character source run
- lost or changed syllabus assignment
- duplicate section/practice/citation IDs
- Java source with `record pattern`/string templates or other post-17-only syntax
- Spring source using `javax.persistence`/`javax.validation` instead of Jakarta
```

The valid fixture must include two practices, one code block, one exact source-note locator and the catalog assignment.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m unittest tests.test_validate_lessons -v`  
Expected: missing `validate_lesson`/`validate_corpus`.

- [ ] **Step 3: Write the exact JSON schema reference**

`content/lesson-schema.json` must enumerate required keys, body/practice types, min/max practice count, source-usage fields and `additionalProperties: false` for structured objects. The Python validator remains authoritative because standard library has no JSON Schema engine.

- [ ] **Step 4: Implement structural and cross-source validation**

Build indices:

```python
source_index[resource_id] = {
    "readStatus": note["read"]["status"],
    "headings": set(note["read"]["relevantHeadings"]),
    "locators": {fact["locator"] for fact in note["read"]["facts"]},
    "lessonIds": set(note["lessonIds"]),
    "cacheText": note["access"].get("cacheText"),
}
```

`validate_lesson` checks exact IDs, allowed enum values, nonempty text, assignment deep equality, citation ownership/locators and source-backed body blocks. `validate_corpus` checks every catalog lesson appears exactly once, including range activities from `ojt-evaluation.json`.

- [ ] **Step 5: Implement baseline lint**

Reject these exact patterns in code/config blocks unless inside prose explaining a migration and the block has `language="text"`:

```python
JAVA_POST_17 = [r"STR\.\"", r"case\s+\w+\([^)]*\)\s+when\b", r"Thread\.ofVirtual\("]
SPRING_LEGACY = [r"\bjavax\.persistence\b", r"\bjavax\.validation\b", r"WebSecurityConfigurerAdapter"]
```

Also compile standalone Java snippets marked `compile=true` using:

```bash
javac --release 17 -d .course-cache/javac .course-cache/javac-src/Snippet_day_01_01.java
```

A snippet may set `compile=false` only when it is intentionally partial and must include `partialReason`.

- [ ] **Step 6: Add reporting and run tests**

Success line:

```text
PASS lessons=40 sections={observed integer} practices={observed integer} citations={observed integer} assignments={observed integer}
```

Run:

```bash
python -m unittest tests.test_validate_lessons -v
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected: all tests pass.

---

### Task 2: Author Days 1–6 — Java Language and OOP Foundations

**Files:**
- Create: `content/lessons/day-01.json`
- Create: `content/lessons/day-02.json`
- Create: `content/lessons/day-03.json`
- Create: `content/lessons/day-04.json`
- Create: `content/lessons/day-05.json`
- Create: `content/lessons/day-06.json`

**Interfaces:**
- Consumes: exact catalog records and readable source notes linked to Days 1–6.
- Produces: schema-valid lessons with citations resolvable by Task 1 validator.

- [ ] **Step 1: Generate an authoring packet limited to Days 1–6**

Run:

```bash
python tools/validate_lessons.py --catalog course-catalog.json \
  --manifest content/source-manifest.json \
  --source-notes-dir content/source-notes \
  --lessons-dir content/lessons \
  --list-requirements day-01:day-06
```

Expected: exact title/outline/objectives/assignments plus readable source facts/locators for each Day.

- [ ] **Step 2: Author Day 1–3 packages**

Coverage must follow, not replace, the syllabus:

- Day 1: JVM architecture; JRE/JDK; primitive/wrapper; String/string pool/immutability; arrays/varargs.
- Day 2: operators; control flow; switch expressions; pattern matching supported by Java 17; loops; introductory stream comparison.
- Day 3: preserve the complete `StringCalculator` lab; add setup, acceptance examples, edge cases and rubric.

Each file has 2–4 practices spanning at least two practice types. Every theory lesson includes at least one source-backed `multiple-choice` concept check with immediate explanation; lab/project/exam/OJT/evaluation packages may use only `self-check` when fixed choices would be misleading. Day 3 may use lab deliverables as one practice only if remaining practices are distinct supporting exercises.

- [ ] **Step 3: Author Day 4–6 packages**

- Day 4: class structure, objects, constructors, access modifiers, encapsulation, records, `this`/`super`.
- Day 5: inheritance, override vs overload, polymorphism and abstract classes.
- Day 6: preserve complete Employee Management System assignment and add guided decomposition/test cases/rubric without altering requirements.

- [ ] **Step 4: Validate this range**

Run:

```bash
python tools/validate_lessons.py --catalog course-catalog.json \
  --manifest content/source-manifest.json --source-notes-dir content/source-notes \
  --lessons-dir content/lessons --only day-01:day-06
```

Expected: `PASS lessons=6` and no uncited technical sections.

- [ ] **Step 5: Compile marked Java snippets**

Run the validator with `--compile-java --only day-01:day-06`.  
Expected: all `compile=true` snippets compile under `javac --release 17`; partial snippets have explicit reasons.

---

### Task 3: Author Days 7–12 — Interfaces, Collections, Streams and Concurrency

**Files:** Create `content/lessons/day-07.json` through `day-12.json`.

**Interfaces:** Consumes exact Day 7–12 catalog records and readable source-note facts/locators linked to those lesson IDs. Produces six top-level lesson objects with the shared required fields (`schemaVersion`, IDs/group/kind/title, summary/duration/objectives/prerequisites/outcomes, sections, commonMistakes, practices, syllabusAssignments, enhancedExercises, references, sourceUsage, authoring); citations resolve to readable linked resources and practices use the declared interaction schema.

- [ ] **Step 1:** Generate the requirement packet with `--list-requirements day-07:day-12`.
- [ ] **Step 2:** Author Days 7–9 covering interface vs abstract class, inner classes, enums, SOLID, generics, List/Set/Map, exception hierarchy and try-with-resources; preserve the Custom Collection & Exception Framework lab on Day 9.
- [ ] **Step 3:** Author Days 10–12 covering functional interfaces/lambdas, stream pipelines/collectors/Optional/parallel streams, threads/synchronized/volatile/ExecutorService/NIO/serialization; preserve the 500K-row Data Processing Pipeline assignment and its benchmark/thread-safety requirements.
- [ ] **Step 4:** Add 2–4 practices per Day, including predict-output where meaningful and applied/concurrency safety questions for Days 11–12.
- [ ] **Step 5:** Run validator with `--only day-07:day-12 --compile-java`; expected `PASS lessons=6` and all marked snippets compile for release 17.

---

### Task 4: Author Days 13–18 — Spring Core and MVC

**Files:** Create `content/lessons/day-13.json` through `day-18.json`.

**Interfaces:** Consumes exact Day 13–18 catalog records and readable linked source facts/locators. Produces six complete lesson objects with all shared required fields, 2–4 declared-interaction practices each, exact preserved assignments, and readable-resource citations; all Spring code/config follows Spring Boot 3.x/Spring Framework 6 and Jakarta conventions.

- [ ] **Step 1:** Generate `--list-requirements day-13:day-18` and identify official Spring locators for each theory section.
- [ ] **Step 2:** Author Days 13–15: Spring Boot architecture, IoC, bean scopes/lifecycle, stereotype annotations, DI types/resolution, `@Configuration`, `@Bean`, `@ConfigurationProperties`, profiles; preserve Multi-module Notification Service assignment.
- [ ] **Step 3:** Author Days 16–18: annotated controllers, mapping and parameters, `ResponseEntity`, content negotiation, Bean Validation, custom validators, `@RestControllerAdvice`, RFC 9457 `ProblemDetail`; preserve User & Task Management API lab.
- [ ] **Step 4:** Ensure all imports use `jakarta.validation` and examples do not use `WebSecurityConfigurerAdapter` or pre-Boot-3 APIs.
- [ ] **Step 5:** Validate `--only day-13:day-18`; expected `PASS lessons=6`, no legacy namespace lint errors and exact assignments retained.

---

### Task 5: Author Days 19–24 — JPA, Security and Performance

**Files:** Create `content/lessons/day-19.json` through `day-24.json`.

**Interfaces:** Consumes exact Day 19–24 catalog records and readable linked source facts/locators. Produces six complete lesson objects with all shared required fields, 2–4 declared-interaction practices each, exact preserved assignments, and readable-resource citations; every security caveat has explicit sourceUsage and locator evidence.

- [ ] **Step 1:** Generate `--list-requirements day-19:day-24`.
- [ ] **Step 2:** Author Days 19–21 for entity mapping, relationships, `@ManyToMany`, cascades/orphan removal, fetch strategies, repositories, pagination/sort/projection, transactions and auditing; preserve E-Commerce Data Layer assignment/Flyway deliverables.
- [ ] **Step 3:** Author Days 22–24 for Spring Security architecture, JWT structure/flow, stateless sessions, password encoding, method security, CORS/CSRF, N+1, batch fetching and soft delete; preserve Auth Service + Performance Optimization lab.
- [ ] **Step 4:** Include warnings that explain token validation, password hashing and context-dependent CSRF rather than presenting insecure tutorial shortcuts as production recommendations.
- [ ] **Step 5:** Validate `--only day-19:day-24`; expected `PASS lessons=6`, Jakarta imports only, exact assignments retained and every security warning cited.

---

### Task 6: Author Days 25–30 — Caching, Integration, Testing and Operations

**Files:** Create `content/lessons/day-25.json` through `day-30.json`.

**Interfaces:** Consumes exact Day 25–30 catalog records and readable linked source facts/locators. Produces six complete lesson objects with all shared required fields, 2–4 declared-interaction practices each, exact preserved assignments, technical code/config blocks, and citations restricted to readable linked resources.

- [ ] **Step 1:** Generate `--list-requirements day-25:day-30`.
- [ ] **Step 2:** Author Days 25–27 for Spring Cache/Redis, cache patterns/eviction, `@Async`, `@Scheduled`, multipart upload/download, WebClient, resilience and CSV/Excel export; preserve Product & Order Features assignment.
- [ ] **Step 3:** Author Days 28–30 for unit/slice/integration tests, Testcontainers, OpenAPI/SpringDoc, structured logging, Actuator/Micrometer concepts, Docker and Compose; preserve Production Readiness lab including ≥75% JaCoCo, trace ID and metrics requirements.
- [ ] **Step 4:** Include environment/config examples as technical blocks and 2–4 practices per Day; avoid pretending the browser can execute them.
- [ ] **Step 5:** Validate `--only day-25:day-30`; expected `PASS lessons=6` and exact assignments retained.

---

### Task 7: Author Days 31–38 — Project Sprints, Defense and Final Tests

**Files:** Create `content/lessons/day-31.json` through `day-38.json`.

**Interfaces:** Kinds are `project` for Days 31–36 and `exam` for Days 37–38.

- [ ] **Step 1:** Generate `--list-requirements day-31:day-38`.
- [ ] **Step 2:** Author Days 31–32 as system-design/kickoff packages with architecture overview, API contract template, database design checklist, error strategy and development workflow. Keep their distinct source rows/deliverables even though titles match.
- [ ] **Step 3:** Author Days 33–35 as Sprint 1–3 packages preserving every entity/module/API/caching/async/export/Docker/CI deliverable and adding Definition of Done, review checklist and daily progress template.
- [ ] **Step 4:** Author Day 36 Final Defense with presentation structure, demo checklist, evidence checklist, question bank and rubric; source citations only where actual linked testing/OpenAPI/Docker pages were read.
- [ ] **Step 5:** Author Day 37 Final Theory as a cited review map across LO1–LO10 and Day 38 Final Practice as an exam-readiness package. Day 38 has no source links, so derive only from prior validated lesson IDs and label references as internal curriculum review rather than external citations.
- [ ] **Step 6:** Validate `--only day-31:day-38`; expected `PASS lessons=8`. Technical config examples are source-backed; deliverable templates satisfy the non-code example requirement.

---

### Task 8: Author OJT and Evaluation Activities

**Files:**
- Create: `content/lessons/ojt-evaluation.json`

**Interfaces:** Produces a JSON object with `schemaVersion` and `lessons` containing exactly `day-39-64` and `day-65-66`.

- [ ] **Step 1: Extract exact source constraints**

From catalog, preserve:

```text
Day 39–64: Learners work with project tasks in FSU Project; mentor support during OJT; LO6–LO12.
Day 65–66: Evaluate learners after training and OJT phase; LO10–LO12.
```

- [ ] **Step 2: Author Day 39–64 as `kind="ojt"`**

Include:

- onboarding/goal-setting checklist;
- weekly work-log template with date, task, evidence, blocker, next action;
- mentor check-in template;
- code-review/evidence checklist tied to LO6–LO12;
- incident/reflection practice and applied delivery practice;
- no invented FSU project policy, stack or proprietary process.

Set `authoring.limitations` to explain that the syllabus supplies no external URLs for this range.

- [ ] **Step 3: Author Day 65–66 as `kind="evaluation"`**

Include:

- evidence portfolio template;
- learner self-assessment;
- evaluator rubric mapped to LO10–LO12;
- defense/reflection questions and improvement-plan practice;
- no invented score thresholds unless explicitly labeled as a suggested template.

- [ ] **Step 4: Validate the two range activities**

Run with `--only day-39-64,day-65-66`.  
Expected: `PASS lessons=2`, each has 2–4 practices, concrete templates and explicit source limitations.

---

### Task 9: Generate Lesson Index and Full Authoring Report

**Files:**
- Modify: `tools/validate_lessons.py`
- Create: `content/lesson-index.json`
- Create: `content/lesson-authoring-report.md`

**Interfaces:**
- Produces ordered index consumed by the static-site build plan.

- [ ] **Step 1: Write failing index-generation test**

Assert exact ordered IDs:

```python
expected = [f"day-{n:02d}" for n in range(1, 39)] + ["day-39-64", "day-65-66"]
self.assertEqual([x["id"] for x in index["lessons"]], expected)
```

Also assert group totals: Java 12, Spring 24 (Days 13–36), Completion 4 (Days 37–38 plus two range activities). Unit 13–15 remain Completion; Unit 11–12 remain Spring as specified.

- [ ] **Step 2: Run test and confirm failure**

Run: `python -m unittest tests.test_validate_lessons.LessonIndexTests -v`.

- [ ] **Step 3: Implement index/report generation**

Each index entry includes:

```json
{
  "id": "day-01",
  "unitId": "unit-01",
  "group": "java",
  "kind": "theory",
  "title": "JVM, JRE, JDK & Data Types",
  "durationMinutes": 150,
  "objectiveCount": 1,
  "practiceCount": 3,
  "citationCount": 6,
  "sourceLimitations": 0
}
```

Report one section per lesson with source resources actually used, inaccessible supplied links, practice inventory, assignment preservation and baseline lint result.

- [ ] **Step 4: Run full corpus validation and generation**

```bash
python tools/validate_lessons.py \
  --catalog course-catalog.json \
  --manifest content/source-manifest.json \
  --source-notes-dir content/source-notes \
  --lessons-dir content/lessons \
  --compile-java \
  --write-index content/lesson-index.json \
  --write-report content/lesson-authoring-report.md
```

Expected: `PASS lessons=40` and generated index/report.

- [ ] **Step 5: Final content audit**

Run:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python tools/validate_sources.py --manifest content/source-manifest.json --notes-dir content/source-notes
python tools/validate_lessons.py --catalog course-catalog.json --manifest content/source-manifest.json --source-notes-dir content/source-notes --lessons-dir content/lessons --compile-java
```

Expected: every command passes. Manually inspect one Java theory lesson, one Java lab, one Spring theory lesson, one Spring lab, one project sprint and both range activities for readable Vietnamese and honest citations.
