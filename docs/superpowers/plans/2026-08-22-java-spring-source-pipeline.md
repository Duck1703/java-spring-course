# Java Spring Source Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trích xuất nguyên vẹn curriculum từ workbook, thử truy cập đủ 111 URL duy nhất, lưu bằng chứng truy cập/đọc và tạo source notes có thể truy vết cho quá trình biên soạn.

**Architecture:** Python 3.13 standard library đọc trực tiếp định dạng XLSX/Open XML, chuẩn hóa dữ liệu vào một catalog duy nhất, sau đó GET từng URL với giới hạn tải và cache nội bộ. Source-note batches đọc nội dung thực tế đã tải hoặc dùng WebFetch làm fallback, nhưng chỉ được đánh dấu `read` khi có tiêu đề/locator và synthesis facts lấy từ body trang.

**Tech Stack:** Python 3.13 standard library (`zipfile`, `xml.etree.ElementTree`, `urllib`, `html.parser`, `unittest`), JSON, Markdown, WebFetch fallback.

## Global Constraints

- Workbook gốc `GST.CEN_Syllabus_JavaSpring_Dev2-3_v3.xlsx` và sheet `JavaSpring_Schedule` là nguồn curriculum có thẩm quyền; không chỉnh sửa workbook.
- Tổ chức theo Day; giữ Day 1–38 riêng lẻ và hai range đúng như syllabus: Day 39–64, Day 65–66.
- Giữ nguyên outline, objectives và assignment/lab; mọi giá trị phải có `sourceRows` để truy vết.
- Deduplicate URL trong từng Day; kiểm tra mỗi URL duy nhất toàn khóa đúng một lần rồi tái sử dụng kết quả.
- Thử truy cập mọi URL duy nhất và ghi `requestedUrl`, `finalUrl`, HTTP/access status, timestamp và lỗi nếu có.
- Chỉ `read.status = "read"` khi nội dung body thực tế đã được truy xuất và đọc; link lỗi/bị chặn không được dùng làm citation.
- Không lưu hoặc xuất bản bản sao toàn văn dài từ website nguồn; cache raw chỉ phục vụ xử lý cục bộ, source notes phải là diễn giải ngắn.
- Không thêm dependency bên thứ ba.
- Workspace hiện không phải Git repository; mỗi task kết thúc bằng validation checkpoint thay vì commit. Không tự khởi tạo Git.

---

## File Structure

- Create: `tools/course_model.py` — kiểu dữ liệu, Open XML parsing, URL normalization và catalog serialization.
- Create: `tools/extract_catalog.py` — CLI tạo `course-catalog.json`, `course-catalog.md`, `content/source-manifest.json`.
- Create: `tools/check_sources.py` — GET/link check, HTML-to-text extraction, cache và update catalog/manifest.
- Create: `tools/validate_sources.py` — kiểm tra coverage, read evidence, source-note schema và uniqueness.
- Create: `tests/test_course_model.py` — unit tests cho workbook/day/resource extraction.
- Create: `tests/test_check_sources.py` — unit tests qua local HTTP server, không gọi Internet.
- Create: `tests/test_validate_sources.py` — unit tests cho source-note validation.
- Create: `course-catalog.json` — machine-readable source of truth.
- Create: `course-catalog.md` — bản tổng hợp tên bài và link theo Day cho người đọc.
- Create: `content/source-manifest.json` — 111 resource records, assignments theo batch và lesson linkage.
- Create: `content/source-notes/java-foundations.json` — nguồn có first-use ở Units 1–2.
- Create: `content/source-notes/java-advanced.json` — nguồn có first-use ở Units 3–4.
- Create: `content/source-notes/spring-core-web.json` — nguồn có first-use ở Units 5–6.
- Create: `content/source-notes/data-security.json` — nguồn có first-use ở Units 7–8.
- Create: `content/source-notes/production.json` — nguồn có first-use ở Units 9–10.
- Create: `content/source-notes/project-final.json` — nguồn có first-use ở Units 11–13.
- Create (generated, not published): `.course-cache/resources/res-0123456789ab.txt` and `res-0123456789ab.meta.json` naming pattern — bounded local retrieval evidence keyed by the real resource ID.

## Shared Interfaces

`course-catalog.json` top-level shape:

```json
{
  "schemaVersion": 1,
  "generatedAt": "ISO-8601 UTC",
  "source": {
    "workbook": "GST.CEN_Syllabus_JavaSpring_Dev2-3_v3.xlsx",
    "sheet": "JavaSpring_Schedule"
  },
  "units": [],
  "lessons": [],
  "resources": []
}
```

Required normalized IDs and groups:

```text
unit-01 through unit-15
day-01 through day-38
day-39-64
day-65-66
group ∈ {java, spring, completion}
resource id = "res-" + first 12 lowercase hex chars of SHA-256(normalized URL)
```

A source-note record has this exact contract:

```json
{
  "resourceId": "res-0123456789ab",
  "requestedUrl": "https://example.org/page",
  "finalUrl": "https://example.org/page",
  "access": {
    "status": "ok",
    "httpStatus": 200,
    "checkedAt": "ISO-8601 UTC",
    "method": "pipeline-get",
    "contentSha256": "64 lowercase hex chars"
  },
  "read": {
    "status": "read",
    "method": "cache-text",
    "pageTitle": "Exact page title",
    "relevantHeadings": ["Heading read on page"],
    "topics": ["topic represented in linked lessons"],
    "facts": [
      {
        "topic": "specific concept",
        "summary": "Vietnamese paraphrase grounded in the page body.",
        "locator": "Heading > Subheading or fragment URL"
      }
    ],
    "limitation": null
  },
  "lessonIds": ["day-01"]
}
```

For inaccessible content, `read` must instead be explicit and contain no facts:

```json
{
  "status": "blocked",
  "method": "pipeline-get",
  "pageTitle": null,
  "relevantHeadings": [],
  "topics": [],
  "facts": [],
  "limitation": "HTTP 403; WebFetch fallback also unavailable"
}
```

---

### Task 1: Parse Workbook and Generate Catalog

**Files:**
- Create: `tools/course_model.py`
- Create: `tools/extract_catalog.py`
- Create: `tests/test_course_model.py`

**Interfaces:**
- Produces: `normalize_url(url: str) -> str`
- Produces: `resource_id(url: str) -> str`
- Produces: `parse_schedule(workbook: Path, sheet_name: str = "JavaSpring_Schedule") -> dict`
- Produces: `render_catalog_markdown(catalog: dict) -> str`
- Produces: CLI `python tools/extract_catalog.py --workbook PATH --json PATH --markdown PATH --manifest PATH`

- [ ] **Step 1: Write URL and ID tests**

```python
# tests/test_course_model.py
import unittest
from tools.course_model import normalize_url, resource_id

class UrlTests(unittest.TestCase):
    def test_normalize_url_removes_fragment_and_trailing_punctuation(self):
        url = "https://docs.oracle.com/javase/tutorial/java/data/index.html#top)."
        self.assertEqual(
            normalize_url(url),
            "https://docs.oracle.com/javase/tutorial/java/data/index.html",
        )

    def test_resource_id_is_stable(self):
        self.assertEqual(
            resource_id("https://example.com/a"),
            resource_id("https://example.com/a#section"),
        )
        self.assertRegex(resource_id("https://example.com/a"), r"^res-[0-9a-f]{12}$")
```

- [ ] **Step 2: Run the focused tests and confirm failure**

Run:

```bash
python -m unittest tests.test_course_model.UrlTests -v
```

Expected: `ImportError` or missing `normalize_url`/`resource_id`.

- [ ] **Step 3: Implement URL normalization and stable IDs**

```python
# tools/course_model.py
from hashlib import sha256
from urllib.parse import urlsplit, urlunsplit

TRAILING_URL_PUNCTUATION = ".,);]}>"

def normalize_url(url: str) -> str:
    cleaned = url.strip().rstrip(TRAILING_URL_PUNCTUATION)
    parts = urlsplit(cleaned)
    scheme = parts.scheme.lower()
    host = parts.netloc.lower()
    path = parts.path or "/"
    return urlunsplit((scheme, host, path, parts.query, ""))

def resource_id(url: str) -> str:
    digest = sha256(normalize_url(url).encode("utf-8")).hexdigest()[:12]
    return f"res-{digest}"
```

- [ ] **Step 4: Run URL tests and confirm pass**

Run: `python -m unittest tests.test_course_model.UrlTests -v`  
Expected: `OK` and 2 passing tests.

- [ ] **Step 5: Write an XLSX fixture test that proves merged-style forward fill and Day grouping**

Build a minimal XLSX ZIP in the test with `workbook.xml`, rels, shared strings and one worksheet containing:

```python
expected = {
    "unitId": "unit-01",
    "lessonIds": ["day-01", "day-02"],
    "dayOneRows": [3, 4],
    "dayOneResourceCount": 1,
    "dayOneAssignment": "Assignment: Calculate an expression",
}
```

Assertions must verify that row 4, which has blank Unit and Day cells, belongs to `day-01`, while row 5 starts `day-02`.

- [ ] **Step 6: Run the parser fixture test and confirm failure**

Run: `python -m unittest tests.test_course_model.ScheduleParserTests -v`  
Expected: FAIL because `parse_schedule` does not exist.

- [ ] **Step 7: Implement Open XML parsing and exact catalog fields**

`parse_schedule` must:

```python
catalog = {
    "schemaVersion": 1,
    "generatedAt": generated_at,
    "source": {"workbook": workbook.name, "sheet": sheet_name},
    "units": [
        {
            "id": "unit-01",
            "number": 1,
            "title": "Java Platform & Language Basics",
            "group": "java",
            "lessonIds": ["day-01", "day-02", "day-03"],
            "sourceRows": [3, 4, 5, 6, 7]
        }
    ],
    "lessons": [
        {
            "id": "day-01",
            "dayStart": 1,
            "dayEnd": 1,
            "label": "Day 1",
            "unitId": "unit-01",
            "group": "java",
            "title": "JVM, JRE, JDK & Data Types",
            "outline": [],
            "objectives": ["LO1"],
            "durationMinutes": 150,
            "activities": [],
            "syllabusAssignments": [],
            "resourceIds": [],
            "sourceRows": [3, 4]
        }
    ],
    "resources": []
}
```

Rules:

- Read `sharedStrings`, inline strings, numeric values and formulas safely.
- Forward-fill Unit from column A/B and Day from column C only for curriculum rows 3–63.
- Start a new lesson only when C begins with `Day`.
- Parse ranges `Day 39- Day 64` as `dayStart=39`, `dayEnd=64`, `id=day-39-64`; similarly 65–66.
- Split objectives on comma and trim.
- Sum numeric durations across grouped rows.
- Preserve every non-empty D activity with row, delivery type, duration, trainer, format and date.
- Treat D rows containing `Assignment` or `Lab` as syllabus assignments without deleting them from activities.
- Extract each bullet `label: URL` from K, preserve label and source row, normalize URL, and deduplicate by resource ID inside each lesson.
- Convert Excel date serials using epoch `1899-12-30`.
- Assign groups by Unit: 1–4 `java`, 5–12 `spring`, 13–15 `completion`.

- [ ] **Step 8: Implement deterministic Markdown rendering**

Each lesson section in `course-catalog.md` must have this shape:

```markdown
## Day 1 — JVM, JRE, JDK & Data Types

- **Unit:** Unit 1 — Java Platform & Language Basics
- **Nhóm:** Java
- **Mục tiêu:** LO1
- **Thời lượng:** 150 phút
- **Dòng nguồn:** 3, 4

### Nội dung và hoạt động
- JVM, JRE, JDK & Data Types / JVM Architecture / JRE vs JDK / Primitive Types & Wrappers
- Assignment

### Tài liệu
- [JVM Architecture](https://docs.oracle.com/javase/specs/jvms/se17/html/jvms-2.html) — stable `res-` ID generated from the normalized URL — chưa kiểm tra
```

Escape Markdown brackets in labels; preserve full URLs.

- [ ] **Step 9: Add the extraction CLI and manifest assignment**

`extract_catalog.py` must call `parse_schedule`, write UTF-8 JSON with `ensure_ascii=False, indent=2`, write Markdown, and generate `content/source-manifest.json`. Assign each globally unique resource to the batch determined by the first linked Unit:

```python
BATCH_BY_UNIT = {
    1: "java-foundations", 2: "java-foundations",
    3: "java-advanced", 4: "java-advanced",
    5: "spring-core-web", 6: "spring-core-web",
    7: "data-security", 8: "data-security",
    9: "production", 10: "production",
    11: "project-final", 12: "project-final", 13: "project-final",
}
```

Each manifest record includes `resourceId`, URL, label variants, lesson IDs, unit IDs, relevant outline text, assigned batch and empty check result.

- [ ] **Step 10: Run all extractor tests**

Run:

```bash
python -m unittest tests.test_course_model -v
```

Expected: all tests pass.

- [ ] **Step 11: Validation checkpoint**

Run:

```bash
python tools/extract_catalog.py \
  --workbook GST.CEN_Syllabus_JavaSpring_Dev2-3_v3.xlsx \
  --json course-catalog.json \
  --markdown course-catalog.md \
  --manifest content/source-manifest.json
```

Expected summary:

```text
PASS units=15 lessons=40 day_resource_refs=165 unique_resources=111
PASS output=course-catalog.json
PASS output=course-catalog.md
PASS output=content/source-manifest.json
```

Inspect Day 1, Day 38, Day 39–64 and Day 65–66 in both catalog formats before continuing.

---

### Task 2: Fetch Every Unique Source and Record Access Evidence

**Files:**
- Create: `tools/check_sources.py`
- Create: `tests/test_check_sources.py`
- Modify: `course-catalog.json`
- Modify: `course-catalog.md`
- Modify: `content/source-manifest.json`
- Create: `.course-cache/resources/*`

**Interfaces:**
- Consumes: `course-catalog.json` and `content/source-manifest.json` from Task 1.
- Produces: `fetch_resource(resource: dict, cache_dir: Path, checked_at: str) -> dict`
- Produces: access status enum `ok|redirected|blocked|not_found|http_error|network_error|content_unreadable|invalid`.
- Produces: CLI `python tools/check_sources.py --catalog course-catalog.json --manifest content/source-manifest.json --markdown course-catalog.md --cache-dir .course-cache/resources --max-workers 4 --per-host-delay 0.5`.

- [ ] **Step 1: Write local-server tests for 200, redirect, 404 and HTML extraction**

Use `http.server.ThreadingHTTPServer` on `127.0.0.1` with routes:

```text
/ok       -> 200 text/html; title "Testing Beans"; h1 and two paragraphs
/moved    -> 302 Location: /ok
/missing  -> 404
```

Assert:

```python
self.assertEqual(result_ok["status"], "ok")
self.assertEqual(result_ok["httpStatus"], 200)
self.assertIn("Testing Beans", cache_text)
self.assertEqual(result_redirect["status"], "redirected")
self.assertTrue(result_redirect["finalUrl"].endswith("/ok"))
self.assertEqual(result_missing["status"], "not_found")
```

- [ ] **Step 2: Run the focused tests and confirm failure**

Run: `python -m unittest tests.test_check_sources.FetchTests -v`  
Expected: missing `fetch_resource`.

- [ ] **Step 3: Implement bounded GET, status classification and text cache**

Implementation requirements:

```python
MAX_BYTES = 5 * 1024 * 1024
USER_AGENT = "JavaSpringCourseBuilder/1.0 (educational source verification)"
TIMEOUT_SECONDS = 20
```

- Use GET because the body must be available for reading; do not claim a HEAD request proves content was read.
- Follow standard redirects and compare normalized requested/final URLs.
- Read at most `MAX_BYTES`; record `truncated: true` if more data exists.
- Accept HTML and plain text. For PDF/binary, record `content_unreadable` unless a later WebFetch fallback can read it.
- Extract title, headings, paragraphs, list items, table text and code/pre text using a small `HTMLParser`; ignore `script`, `style`, `svg`, `noscript`.
- Collapse whitespace but preserve one logical block per line.
- Write `.txt` atomically and `.meta.json` containing headers, byte count, SHA-256 and access result.
- Map 401/403/429 to `blocked`, 404/410 to `not_found`, other 4xx/5xx to `http_error`.
- Catch DNS, TLS and timeout failures as `network_error` with error class/message.
- Never suppress an exception without recording it in the result.

- [ ] **Step 4: Add per-host pacing and a maximum of four workers**

Maintain a lock-protected `last_request_by_host`; sleep until at least `--per-host-delay` seconds have elapsed for the same host. Parallelize across hosts only. The default must be four workers and 0.5 seconds between same-host requests.

- [ ] **Step 5: Update manifest, catalog and Markdown deterministically**

For every resource, write:

```json
"check": {
  "attempted": true,
  "checkedAt": "ISO-8601 UTC",
  "status": "redirected",
  "httpStatus": 200,
  "finalUrl": "https://final.example/page",
  "contentType": "text/html; charset=utf-8",
  "contentBytes": 42810,
  "contentSha256": "64 lowercase hexadecimal characters computed from the fetched body",
  "cacheText": ".course-cache/resources/{the record's resourceId}.txt",
  "error": null
}
```

Markdown resource suffixes must become readable Vietnamese status text such as `đã đọc được (HTTP 200)`, `chuyển hướng và đọc được`, `bị chặn (HTTP 403)`, or `không tìm thấy (HTTP 404)`.

- [ ] **Step 6: Run tests and confirm pass**

Run:

```bash
python -m unittest tests.test_check_sources -v
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected: all tests pass and no Internet is contacted by tests.

- [ ] **Step 7: Execute the real 111-URL access pass**

Run:

```bash
python tools/check_sources.py \
  --catalog course-catalog.json \
  --manifest content/source-manifest.json \
  --markdown course-catalog.md \
  --cache-dir .course-cache/resources \
  --max-workers 4 \
  --per-host-delay 0.5
```

Expected final line must report exactly `attempted=111`. Counts by status are observed results, not hard-coded expectations.

- [ ] **Step 8: Inspect all non-readable results before source authoring**

Run:

```bash
python tools/check_sources.py \
  --report-only \
  --manifest content/source-manifest.json \
  --status blocked,not_found,http_error,network_error,content_unreadable,invalid
```

Expected: a complete table of resource ID, requested URL, status and error. Do not edit these statuses to `ok` manually.

- [ ] **Step 9: Validation checkpoint**

Run:

```bash
python - <<'PY'
import json
m=json.load(open('content/source-manifest.json',encoding='utf-8'))
r=m['resources']
assert len(r)==111
assert all(x['check']['attempted'] for x in r)
assert len({x['resourceId'] for x in r})==111
assert len({x['requestedUrl'] for x in r})==111
print('PASS attempted=111 unique=111')
PY
```

Expected: `PASS attempted=111 unique=111`.

---

### Task 3: Validate Source Notes and Prevent False “Read” Claims

**Files:**
- Create: `tools/validate_sources.py`
- Create: `tests/test_validate_sources.py`

**Interfaces:**
- Consumes: manifest resource/check records and `content/source-notes/*.json`.
- Produces: `validate_source_notes(manifest: dict, notes: list[dict], batch: str | None = None) -> list[str]`.
- Produces: CLI with `--manifest`, `--notes-dir`, optional `--batch`, and nonzero exit on errors.

- [ ] **Step 1: Write failing validation tests**

Tests must prove that validation rejects:

```python
# read without facts
{"read": {"status": "read", "relevantHeadings": [], "facts": []}}

# citation-like note for blocked access
{"access": {"status": "blocked"}, "read": {"status": "read", "facts": [{"summary": "x"}]}}

# duplicate resource in two batch files
[record_for("res-a"), record_for("res-a")]

# missing resource note
manifest_has_two_resources_but_notes_have_one
```

It must accept a read record containing nonempty page title, heading, topics, facts with locators, matching URL/hash/access metadata and lesson IDs.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m unittest tests.test_validate_sources -v`  
Expected: missing validator.

- [ ] **Step 3: Implement exact invariants**

Reject when any of these are true:

- resource ID is absent from manifest or duplicated;
- requested URL differs from manifest;
- note access status/HTTP/final URL/hash differs from the latest check unless method is explicitly `webfetch-fallback`;
- `read.status=read` but page title, at least one heading, topic, fact summary or locator is empty;
- `read.status=read` for a failed pipeline access without `webfetch-fallback` evidence;
- `read.status!=read` but facts are present;
- note lesson IDs are not the same set as manifest lesson IDs;
- summary contains a copied run longer than 300 characters from cached source text;
- a batch is missing any assigned manifest resource.

- [ ] **Step 4: Implement report output**

Success output:

```text
PASS source-notes resources=111 read={observed integer} unavailable={observed integer} batches=6
```

Failure output is one line per resource, for example:

```text
ERROR res-abc123 [java-foundations] read status requires at least one fact locator
```

- [ ] **Step 5: Run validator tests and full regression**

Run:

```bash
python -m unittest tests.test_validate_sources -v
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected: all tests pass.

---

### Task 4: Read and Summarize Java Foundations Sources

**Files:**
- Create: `content/source-notes/java-foundations.json`

**Interfaces:**
- Consumes: manifest records with `assignedBatch="java-foundations"`, linked lesson outlines and matching cache files.
- Produces: one valid source-note record per assigned resource, no duplicates.

- [ ] **Step 1: List the exact assigned sources and linked lesson topics**

Run:

```bash
python tools/validate_sources.py --manifest content/source-manifest.json \
  --notes-dir content/source-notes --batch java-foundations --list-required
```

Expected: every first-use source from Units 1–2 with resource ID, URL, lesson IDs and outline topics.

- [ ] **Step 2: Read every accessible cached page and use WebFetch only as fallback**

For each resource:

1. Open its `.meta.json` and confirm requested URL, final URL and hash.
2. Read the relevant heading/section in `.txt`, not only the title or first paragraph.
3. Cover every linked outline topic for which the page is supplied.
4. If cache is blocked/unreadable, call WebFetch on the exact requested URL; mark `method=webfetch-fallback` only when body content is returned.
5. If both fail, record the actual limitation and zero facts.

- [ ] **Step 3: Write grounded notes**

Write one top-level object:

```json
{
  "schemaVersion": 1,
  "batch": "java-foundations",
  "resources": []
}
```

Each readable resource needs 2–8 concise facts, exact heading locators and topics relevant to JVM/JRE/JDK, primitives/wrappers, strings, arrays/varargs, operators/control flow, classes, encapsulation, records, inheritance, polymorphism and abstract classes as linked by the manifest. Do not introduce facts unrelated to linked outlines merely because they are on the page.

- [ ] **Step 4: Validate the batch**

Run:

```bash
python tools/validate_sources.py --manifest content/source-manifest.json \
  --notes-dir content/source-notes --batch java-foundations
```

Expected: a PASS with `required` and `present` showing the same observed integer and no errors.

---

### Task 5: Read and Summarize Java Advanced Sources

**Files:**
- Create: `content/source-notes/java-advanced.json`

**Interfaces:** Consumes manifest records assigned to `java-advanced`, their linked lesson IDs/outlines, and matching cache evidence. Produces `content/source-notes/java-advanced.json` with `{schemaVersion: 1, batch: "java-advanced", resources: [...]}`; every resource record contains exact manifest URL/access metadata, `read.status/method/pageTitle/relevantHeadings/topics/facts/limitation`, and the exact manifest lesson-ID set.

- [ ] **Step 1:** Run `python tools/validate_sources.py --manifest content/source-manifest.json --notes-dir content/source-notes --batch java-advanced --list-required`.
- [ ] **Step 2:** Read each actual page section linked to Units 3–4, using matching cache text/hash or WebFetch fallback; never promote a failed URL to `read` without returned body content.
- [ ] **Step 3:** Write 2–8 grounded facts per readable source covering interfaces, inner classes, enums, SOLID, generics, collections, exceptions, lambdas, streams, Optional, concurrency, synchronization, executors, NIO/file I/O and serialization according to each manifest record.
- [ ] **Step 4:** Run `python tools/validate_sources.py --manifest content/source-manifest.json --notes-dir content/source-notes --batch java-advanced` and require a PASS with exact required/present equality.

---

### Task 6: Read and Summarize Spring Core and MVC Sources

**Files:**
- Create: `content/source-notes/spring-core-web.json`

**Interfaces:** Consumes manifest records assigned to `spring-core-web`, linked lesson IDs/outlines, and cache evidence. Produces `content/source-notes/spring-core-web.json` with `{schemaVersion: 1, batch: "spring-core-web", resources: [...]}`; every resource records exact URL/access metadata plus `read.status/method/pageTitle/relevantHeadings/topics/facts/limitation` and exact lesson IDs.

- [ ] **Step 1:** List required records with `--batch spring-core-web --list-required`.
- [ ] **Step 2:** Read actual linked sections for IoC container, bean scopes/lifecycle, stereotypes, DI resolution, configuration, profiles, request mapping, parameter binding, `ResponseEntity`, validation, custom validators and `ProblemDetail`.
- [ ] **Step 3:** Record precise Spring reference heading locators and Spring Boot 3/Spring Framework 6 implications; do not treat older Baeldung snippets as baseline until cross-checked against supplied official sources.
- [ ] **Step 4:** Validate with `--batch spring-core-web`; expected exact coverage and no blocked source used as `read`.

---

### Task 7: Read and Summarize JPA and Security Sources

**Files:**
- Create: `content/source-notes/data-security.json`

**Interfaces:** Consumes manifest records assigned to `data-security`, linked lesson IDs/outlines, and cache evidence. Produces `content/source-notes/data-security.json` with `{schemaVersion: 1, batch: "data-security", resources: [...]}`; every resource records exact URL/access metadata plus `read.status/method/pageTitle/relevantHeadings/topics/facts/limitation` and exact lesson IDs.

- [ ] **Step 1:** List required records with `--batch data-security --list-required`.
- [ ] **Step 2:** Read actual sections for entity mapping, associations, cascades, fetch strategies, repositories, pagination, transactions, auditing, JWT resource server, password storage, stateless security, method security, CSRF/CORS, N+1, batch fetching and soft delete.
- [ ] **Step 3:** Preserve security caveats in facts, especially password encoding, token validation and CSRF context; distinguish official behavior from tutorial implementation choices.
- [ ] **Step 4:** Validate with `--batch data-security`; expected exact coverage.

---

### Task 8: Read and Summarize Production Sources

**Files:**
- Create: `content/source-notes/production.json`

**Interfaces:** Consumes manifest records assigned to `production`, linked lesson IDs/outlines, and cache evidence. Produces `content/source-notes/production.json` with `{schemaVersion: 1, batch: "production", resources: [...]}`; every resource records exact URL/access metadata plus `read.status/method/pageTitle/relevantHeadings/topics/facts/limitation` and exact lesson IDs.

- [ ] **Step 1:** List required records with `--batch production --list-required`.
- [ ] **Step 2:** Read actual sections for Spring Cache/Redis, async/scheduled work, file upload/download, WebClient, resilience, CSV/Excel export, Spring tests, JUnit, integration testing, Testcontainers, OpenAPI, logging, Actuator/metrics and Docker Compose.
- [ ] **Step 3:** Record configuration/API locators compatible with Spring Boot 3.x and note source-version limitations explicitly.
- [ ] **Step 4:** Validate with `--batch production`; expected exact coverage.

---

### Task 9: Read and Summarize Project and Final Sources

**Files:**
- Create: `content/source-notes/project-final.json`

**Interfaces:** Consumes manifest records assigned to `project-final`, linked lesson IDs/outlines, and cache evidence. Produces `content/source-notes/project-final.json` with `{schemaVersion: 1, batch: "project-final", resources: [...]}`; every resource records exact URL/access metadata plus `read.status/method/pageTitle/relevantHeadings/topics/facts/limitation` and exact lesson IDs.

- [ ] **Step 1:** List required records with `--batch project-final --list-required`.
- [ ] **Step 2:** Read actual linked sections for project structuring, MVC/API design, repositories/entity persistence, exception handling, security/JWT, pagination, uploads, caching, transactions, async, Docker, testing, Testcontainers, OpenAPI and the Java/Spring references used for final theory.
- [ ] **Step 3:** Notes must identify which source sections support each sprint deliverable or final-review topic; do not summarize an entire reference manual as though every chapter was read.
- [ ] **Step 4:** Validate with `--batch project-final`; expected exact coverage.

---

### Task 10: Full Source Audit

**Files:**
- Modify only source-note records that fail validation.

**Interfaces:** Produces a source corpus that downstream lesson citations may rely on.

- [ ] **Step 1: Run complete coverage validation**

```bash
python tools/validate_sources.py \
  --manifest content/source-manifest.json \
  --notes-dir content/source-notes
```

Expected: exactly 111 resource records, six batches, no duplicate/missing records.

- [ ] **Step 2: Generate a transparent status report**

```bash
python tools/validate_sources.py \
  --manifest content/source-manifest.json \
  --notes-dir content/source-notes \
  --write-report content/source-reading-report.md
```

The report must list URL, check status, read status, fallback method, linked lessons and limitation. It must not label unavailable resources as read.

- [ ] **Step 3: Spot-check at least one source in every batch**

Compare note title, heading locator and one fact to the cached body or WebFetch result. If a locator cannot be found, correct or downgrade the note.

- [ ] **Step 4: Final regression checkpoint**

Run:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python tools/validate_sources.py --manifest content/source-manifest.json --notes-dir content/source-notes
```

Expected: all tests pass and source validation reports `resources=111`.
