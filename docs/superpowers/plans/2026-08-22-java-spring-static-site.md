# Java Spring Static Learning Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xuất bản 40 lesson/activity packages thành một `index.html` tự chứa, có giao diện documentation chuyên nghiệp, responsive, search/navigation/practice/copy/progress hoạt động và được kiểm thử trên Chrome desktop/mobile.

**Architecture:** `index.html` chứa toàn bộ HTML, CSS, JavaScript và một `<script type="application/json">` nhúng publication model. Một Python builder kiểm tra lesson corpus rồi thay duy nhất payload JSON; client app render dashboard/lesson/resource views từ dữ liệu nhúng và dùng versioned `localStorage` với fallback an toàn.

**Tech Stack:** Semantic HTML5, inline CSS, vanilla JavaScript ES2022, Python 3.13 standard library, Node 22 built-in test runner, Chrome Headless.

## Global Constraints

- REQUIRED: invoke the installed `frontend-design` skill before editing `index.html`, and follow its current instructions.
- Final frontend has exactly one deployable file: `index.html`; no framework, npm package, CDN, backend, database, authentication or runtime AI.
- CSS and JavaScript are inline; approved course data is embedded in the file and core lessons work offline.
- Use real curriculum/lesson packages only; no replacement curriculum or fake demo lessons.
- Header name is `Java Spring Boot Course`; header is sticky and includes search, overall progress and mobile hamburger.
- Desktop has persistent left curriculum sidebar and readable content; mobile has full-width content and accessible drawer.
- Primary groups are Java and Spring / Spring Boot; Completion is a concluding group for Units 13–15.
- Java accent `#F89820`; Spring accent `#6DB33F`; modern, clean, professional, developer-focused documentation style, not a marketing landing page.
- Every lesson shows 2–4 practices with Hint and hidden Solution, plus original assignments where present.
- Persist completion, last lesson, exercise/quiz state, module collapse state and theme in localStorage; support safe reset and JSON export/import.
- Respect keyboard navigation, visible focus, semantic structure, color contrast and `prefers-reduced-motion`.
- The user authorized a local Git repository on 2026-08-22 for worktree/diff review; each task commits locally after tests/inspection and nothing is pushed without separate authorization.

---

## File Structure

- Create: `index.html` — only deployable frontend artifact; complete shell, styles, inline course data and application script.
- Create: `tools/build_site.py` — validates and embeds catalog, lesson packages and source status into an existing `index.html` marker atomically.
- Create: `tests/test_build_site.py` — builder/publication-model tests.
- Create: `tests/site_core.test.js` — Node tests for extracted pure browser logic.
- Create: `tools/ui_smoke_test.py` — serves the site locally, runs Chrome self-test at desktop/mobile sizes and records output/screenshots.
- Generated/ignored test evidence: `.course-cache/ui/desktop.png`, `.course-cache/ui/mobile.png`, `.course-cache/ui/*-dom.html`.

## Embedded Publication Interface

`<script id="course-data" type="application/json">` contains:

```json
{
  "schemaVersion": 1,
  "builtAt": "ISO-8601 UTC",
  "course": {
    "title": "Java Spring Boot Course",
    "baseline": "Java 17 · Spring Boot 3.x",
    "groups": [
      {"id": "java", "label": "Java", "accent": "#F89820"},
      {"id": "spring", "label": "Spring / Spring Boot", "accent": "#6DB33F"},
      {"id": "completion", "label": "Hoàn tất khóa học", "accent": "#64748B"}
    ]
  },
  "units": [],
  "lessons": [],
  "resourceStatuses": []
}
```

Browser state key and exact shape:

```javascript
const STORAGE_KEY = "java-spring-course:v1";
const DEFAULT_STATE = Object.freeze({
  version: 1,
  completed: [],
  lastLessonId: null,
  practice: {},
  collapsedUnits: [],
  theme: "system"
});
```

Hash routes:

```text
#dashboard
#lesson/day-01
#resources
```

Pure functions exposed as `globalThis.CourseCore` for Node and self-tests:

```javascript
normalizeSearch(value: string): string
parseRoute(hash: string): {view: "dashboard"|"lesson"|"resources", lessonId: string|null}
calculateProgress(lessons: object[], completedIds: string[], group?: string): {completed:number,total:number,percent:number}
nextLessonId(lessons: object[], currentId: string, direction: -1|1): string|null
sanitizeState(raw: unknown, validLessonIds: Set<string>, validUnitIds: Set<string>, validPracticeIds: Set<string>): object
searchLessons(lessons: object[], unitsById: Map<string,object>, query: string): object[]
```

---

### Task 1: Build and Validate the Embedded Publication Model

**Files:**
- Create: `tools/build_site.py`
- Create: `tests/test_build_site.py`
- Create: `index.html` with data marker and temporary minimal semantic shell only.

**Interfaces:**
- Consumes: validated `course-catalog.json`, `content/lesson-index.json`, `content/lessons/*.json`, `content/source-manifest.json`, `content/source-notes/*.json`.
- Produces: `build_publication_model(catalog_path: Path, lesson_index_path: Path, lessons_dir: Path, manifest_path: Path, source_notes_dir: Path, built_at: str) -> dict` and `embed_course_data(index_html: str, model: dict) -> str`.
- Produces CLI: `python tools/build_site.py --catalog course-catalog.json --lesson-index content/lesson-index.json --lessons-dir content/lessons --manifest content/source-manifest.json --source-notes-dir content/source-notes --output index.html`.

- [ ] **Step 1: Write publication-model tests**

```python
# tests/test_build_site.py
import json
import unittest
from tools.build_site import embed_course_data

class EmbedTests(unittest.TestCase):
    def test_embeds_json_without_closing_script_injection(self):
        html = '<script id="course-data" type="application/json">{}</script>'
        model = {"text": "</script><script>alert(1)</script>"}
        built = embed_course_data(html, model)
        self.assertEqual(built.count('id="course-data"'), 1)
        self.assertNotIn("</script><script>alert", built)
        payload = built.split('id="course-data" type="application/json">', 1)[1].split("</script>", 1)[0]
        self.assertEqual(json.loads(payload)["text"], "</script><script>alert(1)</script>")

    def test_requires_one_data_marker(self):
        with self.assertRaisesRegex(ValueError, "exactly one course-data marker"):
            embed_course_data("<html></html>", {})
```

Add fixtures that assert 40 ordered lessons, Units 1–15, Java/Spring/Completion counts 12/24/4, all references reduced to supplied status/read metadata, and no source-note full body is embedded.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m unittest tests.test_build_site -v`  
Expected: missing module/functions.

- [ ] **Step 3: Implement model assembly**

`build_publication_model` must:

```python
expected_ids = [f"day-{n:02d}" for n in range(1, 39)] + ["day-39-64", "day-65-66"]
```

- Load individual day files plus `ojt-evaluation.json`.
- Require exact ordered ID equality with `lesson-index.json`.
- Copy all authored lesson fields required by the UI.
- Join unit title/number/group from catalog without changing curriculum.
- For every lesson reference, attach only `resourceId`, requested/final URL, label, check/read status, page title and limitation.
- Never embed cached page text or source-note fact corpus not directly used by a lesson.
- Require every lesson citation resource to have `read.status="read"` and locator match.
- Require exactly 40 lesson records and group counts 12/24/4.

- [ ] **Step 4: Implement safe atomic embedding**

Use exact marker regex:

```python
DATA_RE = re.compile(
    r'(<script id="course-data" type="application/json">)(.*?)(</script>)',
    re.DOTALL,
)
```

Serialize with `ensure_ascii=False, separators=(",", ":")`, then replace `<` with `\u003c`, `>` with `\u003e`, `&` with `\u0026`. Require exactly one marker. Write to a sibling temporary file and `Path.replace()` output.

- [ ] **Step 5: Create the initial valid document shell**

`index.html` must begin with:

```html
<!doctype html>
<html lang="vi" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Khóa học Java 17 và Spring Boot 3.x theo lộ trình thực hành.">
  <title>Java Spring Boot Course</title>
  <style id="app-styles"></style>
</head>
<body>
  <a class="skip-link" href="#main-content">Bỏ qua đến nội dung</a>
  <div id="app" aria-live="off"></div>
  <div id="toast-region" role="status" aria-live="polite" aria-atomic="true"></div>
  <script id="course-data" type="application/json">{}</script>
  <script id="app-script"></script>
</body>
</html>
```

No external script, stylesheet, font or image request.

- [ ] **Step 6: Run tests and full content validation**

Run:

```bash
python -m unittest tests.test_build_site -v
python tools/validate_lessons.py --catalog course-catalog.json --manifest content/source-manifest.json --source-notes-dir content/source-notes --lessons-dir content/lessons
```

Expected: all tests and lesson validation pass.

- [ ] **Step 7: Build the real publication payload**

Run:

```bash
python tools/build_site.py \
  --catalog course-catalog.json \
  --lesson-index content/lesson-index.json \
  --lessons-dir content/lessons \
  --manifest content/source-manifest.json \
  --source-notes-dir content/source-notes \
  --output index.html
```

Expected: `PASS output=index.html units=15 lessons=40` followed by the observed published resource count and `external_dependencies=0`.

---

### Task 2: Establish the Frontend Design System and Responsive Shell

**Files:**
- Modify: `index.html` (`#app-styles`, shell-rendering portion of `#app-script`)

**Interfaces:**
- Consumes: embedded course data and approved design spec.
- Produces: CSS custom properties, semantic shell and stable DOM hooks used by later tasks.

- [ ] **Step 1: Invoke the installed frontend design skill before editing**

Invoke `frontend-design` with this exact brief:

```text
Design the implementation for the approved Java Spring Boot Course static documentation/learning app. One index.html, inline CSS/JS, no dependencies. Sticky header, desktop curriculum rail, mobile accessible drawer, dashboard and long-form lesson view. Developer-focused, editorial/technical rather than marketing. Java #F89820 and Spring #6DB33F are restrained semantic accents. Use real course titles/data. Ensure long-study readability, keyboard focus, light/dark themes, reduced motion and mobile code overflow. Do not add features outside the spec.
```

Read and follow the skill output; preserve all global constraints in this plan.

- [ ] **Step 2: Implement the visual token system**

Define at minimum:

```css
:root {
  --java: #f89820;
  --spring: #6db33f;
  --completion: #64748b;
  --ink: #172033;
  --muted: #667085;
  --canvas: #f5f7f8;
  --surface: #ffffff;
  --surface-raised: #ffffff;
  --line: #dfe4e8;
  --code-bg: #111827;
  --code-ink: #e5edf7;
  --focus: #2563eb;
  --header-h: 4rem;
  --sidebar-w: 19rem;
  --content-max: 48rem;
  --radius-sm: .5rem;
  --radius-md: .875rem;
  --shadow-float: 0 18px 50px rgb(15 23 42 / .12);
  color-scheme: light;
}
html[data-theme="dark"] {
  --ink: #edf2f7;
  --muted: #a8b3c2;
  --canvas: #0d1117;
  --surface: #121922;
  --surface-raised: #17202b;
  --line: #2a3543;
  --code-bg: #080c12;
  --code-ink: #e6edf3;
  color-scheme: dark;
}
```

Use a local system stack led by `"Segoe UI Variable Text"` for prose and `"Cascadia Code"` for code. No network fonts.

- [ ] **Step 3: Implement semantic shell HTML through JavaScript**

The app root renders these stable hooks:

```html
<header class="app-header" data-testid="header"><button class="menu-button" aria-controls="course-sidebar">Mở nội dung khóa học</button><a href="#dashboard">Java Spring Boot Course</a><div id="header-search"></div><div id="header-progress"></div></header>
<div class="app-frame">
  <aside id="course-sidebar" class="course-sidebar" aria-label="Nội dung khóa học"><nav id="curriculum-nav" aria-label="Lộ trình học"></nav></aside>
  <main id="main-content" tabindex="-1"><section id="route-view"></section></main>
</div>
<div class="drawer-backdrop" data-action="close-drawer" hidden></div>
```

Header contains hamburger, brand mark/name, `<label>`-backed search input, progress meter with text, and theme control. The brand mark uses CSS shapes/letterforms, not an external logo asset.

- [ ] **Step 4: Implement responsive breakpoints and durable reading measure**

```css
@media (min-width: 64rem) {
  .menu-button { display: none; }
  .course-sidebar { position: sticky; top: var(--header-h); height: calc(100dvh - var(--header-h)); }
  .app-frame { grid-template-columns: var(--sidebar-w) minmax(0, 1fr); }
}
@media (max-width: 63.999rem) {
  .course-sidebar { position: fixed; inset: var(--header-h) auto 0 0; transform: translateX(-105%); }
  body.drawer-open .course-sidebar { transform: translateX(0); }
  .lesson-shell { padding-inline: clamp(1rem, 4vw, 2rem); }
}
pre { max-width: 100%; overflow-x: auto; }
```

At ≤30rem, compact progress text without removing its accessible label. Never hide lesson navigation or Practice controls.

- [ ] **Step 5: Add accessible state styles and reduced motion**

Include `:focus-visible`, selected/completed/current states that do not rely on color alone, skip-link behavior, `@media (prefers-reduced-motion: reduce)` and print styles that hide navigation/buttons while printing lesson content and expanded source URLs.

- [ ] **Step 6: Static checkpoint**

Run:

```bash
python - <<'PY'
from pathlib import Path
h=Path('index.html').read_text(encoding='utf-8')
for token in ['--java: #f89820','--spring: #6db33f','course-sidebar','main-content','prefers-reduced-motion','overflow-x: auto']:
    assert token in h, token
assert 'https://fonts.' not in h and '<link rel="stylesheet"' not in h
print('PASS design-shell dependencies=0')
PY
```

Expected: `PASS design-shell dependencies=0`.

---

### Task 3: Pure Client Logic, Routing, Search and Curriculum Navigation

**Files:**
- Modify: `index.html` (`#app-script`)
- Create: `tests/site_core.test.js`

**Interfaces:**
- Produces the `CourseCore` functions listed in the shared interface.
- Produces UI functions: `renderApp()`, `renderHeader()`, `renderSidebar()`, `renderDashboard()`, `renderLesson(id)`, `renderResources()`.

- [ ] **Step 1: Write pure-logic Node tests**

The test reads `index.html`, extracts `#app-script`, evaluates only the block between `/* COURSE_CORE_START */` and `/* COURSE_CORE_END */` in `node:vm`, then asserts:

```javascript
assert.equal(core.normalizeSearch("  Cấu hình ĐẬU Bean "), "cau hinh dau bean");
assert.deepEqual(core.parseRoute("#lesson/day-13"), {view:"lesson", lessonId:"day-13"});
assert.deepEqual(core.parseRoute("#lesson/not-real"), {view:"lesson", lessonId:"not-real"});
assert.deepEqual(core.calculateProgress(lessons, ["day-01"], "java"), {completed:1,total:2,percent:50});
assert.equal(core.nextLessonId(lessons, "day-01", 1), "day-02");
assert.equal(core.nextLessonId(lessons, "day-01", -1), null);
assert.deepEqual(core.searchLessons(lessons, units, "kiem thu"), [lessons[1]]);
```

- [ ] **Step 2: Run Node tests and confirm failure**

Run: `node --test tests/site_core.test.js`  
Expected: missing core markers/functions.

- [ ] **Step 3: Implement pure core functions without DOM dependencies**

Requirements:

```javascript
function normalizeSearch(value) {
  return String(value ?? "").normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d").replace(/Đ/g, "D")
    .toLowerCase().trim().replace(/\s+/g, " ");
}
```

- `parseRoute` defaults to dashboard; preserves requested lesson ID so renderer can show not-found/reset rather than silently selecting another lesson.
- `calculateProgress` intersects completion IDs with valid lessons/group and rounds percent; zero total gives zero percent.
- `sanitizeState` strips unknown lesson/unit IDs, invalid practice keys and unknown properties; invalid input returns a fresh default state.
- `searchLessons` searches title, summary, outcomes, outline text, Unit title and technical keywords, all normalized.

Expose with:

```javascript
globalThis.CourseCore = Object.freeze({ normalizeSearch, parseRoute, calculateProgress, nextLessonId, sanitizeState, searchLessons });
```

- [ ] **Step 4: Run pure tests and confirm pass**

Run: `node --test tests/site_core.test.js`  
Expected: all tests pass.

- [ ] **Step 5: Parse embedded data safely and build indices**

```javascript
const courseData = JSON.parse(document.getElementById("course-data").textContent);
const lessonsById = new Map(courseData.lessons.map(lesson => [lesson.id, lesson]));
const unitsById = new Map(courseData.units.map(unit => [unit.id, unit]));
```

On parse/model failure, replace app content with a semantic error panel and do not throw an uncaught loop.

- [ ] **Step 6: Render collapsible curriculum from real data**

Group order is `java`, `spring`, `completion`; sort Units by number and lessons by publication order. A module button uses:

```html
<button class="module-toggle" aria-expanded="true" aria-controls="lessons-unit-01" data-unit-id="unit-01">
```

Lesson links include current `aria-current="page"` and visible completed indicator plus screen-reader text.

- [ ] **Step 7: Implement hash routing and search behavior**

- `hashchange` renders route and moves focus to `#main-content` only after intentional navigation, not initial load.
- Unknown lesson renders “Không tìm thấy bài học” with Dashboard and clear-search actions.
- Search opens a keyboard-navigable result panel; results show group, Unit and lesson title.
- Arrow Down/Up moves active option; Enter routes; Escape closes and restores input focus.
- Empty query closes results; no result state has a “Xóa tìm kiếm” button.
- Selecting a result updates `lastLessonId` and closes the mobile drawer.

- [ ] **Step 8: Render dashboard with real aggregates**

Dashboard includes total progress, completed/total, Continue Learning, Java progress, Spring progress and Unit overview. Continue Learning chooses `lastLessonId` when valid and unfinished, otherwise the first unfinished lesson, otherwise Day 1 with “Ôn tập lại”.

- [ ] **Step 9: Routing/search checkpoint**

Run:

```bash
node --test tests/site_core.test.js
python tools/build_site.py --catalog course-catalog.json --lesson-index content/lesson-index.json --lessons-dir content/lessons --manifest content/source-manifest.json --source-notes-dir content/source-notes --output index.html
```

Expected: tests pass; builder preserves CSS/JS and reports 40 lessons.

---

### Task 4: Documentation Lesson Renderer and Practice Experience

**Files:**
- Modify: `index.html`
- Modify: `tests/site_core.test.js`

**Interfaces:**
- Consumes the lesson body/practice/source interfaces.
- Produces safe renderer helpers and delegated actions.

- [ ] **Step 1: Add escaping and content-render tests**

Test pure helpers:

```javascript
assert.equal(core.escapeHtml('<img src=x onerror=alert(1)>'), '&lt;img src=x onerror=alert(1)&gt;');
assert.equal(core.safeExternalUrl('javascript:alert(1)'), null);
assert.equal(core.safeExternalUrl('https://docs.spring.io/a'), 'https://docs.spring.io/a');
```

Add these functions to the core markers and run tests; expected initial failure, then pass.

- [ ] **Step 2: Implement lesson header and breadcrumb**

Render group / Unit / Day breadcrumb, title, summary, duration, objective chips, prerequisites and outcomes. Use one page `<h1>` and logical `<h2>/<h3>` sequence.

- [ ] **Step 3: Render typed body blocks safely**

Map only allowed types:

```text
paragraph -> <p>
list -> <ul>/<ol>
note|important|warning -> <aside class="callout callout--note|callout--important|callout--warning">
code -> <figure class="code-sample"><figcaption>{escaped caption}<button data-action="copy-code">Sao chép mã</button></figcaption><pre><code>{escaped code}</code></pre></figure>
table -> accessible <table> with caption
```

All prose/code passes `escapeHtml`; citations become numbered superscript links to source cards. Unknown block types render a visible authoring warning, never execute raw HTML.

- [ ] **Step 4: Render Practice with independent disclosure state**

Each Practice card includes type label, prompt, optional starter code, Hint button, Show Solution button and rubric. Use buttons with `aria-expanded`/`aria-controls`; solution starts hidden. For `multiple-choice`, render labeled checkbox/radio controls plus “Kiểm tra đáp án”; show correct/incorrect status and the authored explanation only after checking. For `self-check`, keep the learner's response external and reveal the explanation with Solution. Save selected choice IDs and checked/attempted state only under the stable practice ID.

- [ ] **Step 5: Render assignments and distinguish enrichment**

Original syllabus assignments appear under “Bài tập trong syllabus” with an “Nội dung gốc” label and preserved requirement text. Enhanced exercises appear under “Luyện tập bổ sung”. Do not merge or rewrite them in the UI.

- [ ] **Step 6: Render references and transparent status**

Every used source card shows label/title, domain, external URL, page heading locators, `đã đọc` badge and section backlinks. Supplied but inaccessible resources appear in a separate “Nguồn được cung cấp nhưng không truy cập được” disclosure with status/limitation and no `đã đọc` badge.

- [ ] **Step 7: Implement Copy Code with fallback and toast**

```javascript
async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return "clipboard";
  }
  const area = Object.assign(document.createElement("textarea"), {value: text});
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.append(area);
  area.select();
  const ok = document.execCommand("copy");
  area.remove();
  if (!ok) throw new Error("copy unavailable");
  return "fallback";
}
```

On success announce “Đã sao chép mã”; on failure announce “Không thể sao chép tự động — hãy chọn mã và sao chép thủ công.”

- [ ] **Step 8: Render previous/completion/next navigation**

At lesson end, Previous/Next use actual ordered lesson IDs and show destination title. Center button toggles completion, reflects state with text/icon and never advances automatically.

- [ ] **Step 9: Lesson-render checkpoint**

Run Node tests and build. Open `#lesson/day-01`, `#lesson/day-15`, `#lesson/day-30`, `#lesson/day-39-64` manually and verify each typed block, Practice disclosure, source status and navigation.

---

### Task 5: Durable Progress, Theme, Drawer and Data Portability

**Files:**
- Modify: `index.html`
- Modify: `tests/site_core.test.js`

**Interfaces:**
- Uses `STORAGE_KEY`/`DEFAULT_STATE` and `sanitizeState`.
- Produces safe storage wrapper, progress updates, drawer focus lifecycle, export/import.

- [ ] **Step 1: Add state-sanitization tests**

Assert that:

```javascript
const cleaned = core.sanitizeState({
  version: 999,
  completed: ["day-01", "fake", "day-01"],
  lastLessonId: "fake",
  practice: {"day-01-practice-01": {attempted: true}, "evil": "x"},
  collapsedUnits: ["unit-01", "fake"],
  theme: "neon",
  extra: "discard"
}, new Set(["day-01"]), new Set(["unit-01"]), new Set(["day-01-practice-01"]));
assert.deepEqual(cleaned.completed, ["day-01"]);
assert.equal(cleaned.lastLessonId, null);
assert.equal(cleaned.theme, "system");
assert.equal("extra" in cleaned, false);
```

- [ ] **Step 2: Implement safe storage read/write**

- `loadState` catches parse/security/quota errors, sanitizes and returns defaults with a one-time warning.
- `saveState` catches errors and keeps in-memory state functional.
- Never put authored lesson content into localStorage.
- Recompute progress from completion IDs; do not store a stale percentage.

- [ ] **Step 3: Wire completion and last-lesson state**

Visiting a lesson updates `lastLessonId`. Completion toggle updates header, dashboard/sidebar and button without full page reload, then persists. Unknown/removed IDs are cleaned on next load.

- [ ] **Step 4: Wire module collapse and theme**

Persist collapsed Unit IDs. Theme control cycles or selects `system|light|dark`; `system` follows `matchMedia('(prefers-color-scheme: dark)')`. Update `data-theme`, accessible label and `color-scheme` without flash by running a tiny theme bootstrap before first paint.

- [ ] **Step 5: Implement mobile drawer focus behavior**

- Hamburger sets `body.drawer-open`, `aria-expanded=true`, unhides backdrop and focuses the close/current item.
- Escape closes; backdrop closes; selecting a lesson closes.
- Tab/Shift+Tab cycle among visible drawer focusables while open.
- Closing restores focus to hamburger.
- At desktop breakpoint, clear drawer state and remove focus trap.

- [ ] **Step 6: Implement reset, export and import**

Dashboard settings disclosure contains:

```text
Tải tiến độ (.json)
Nhập tiến độ (.json)
Đặt lại tiến độ
```

Export exact shape `{app:"java-spring-course", schemaVersion:1, exportedAt, state}`. Import requires app/schema match, parses text, sanitizes IDs and shows a confirmation preview with completed count before replacing current state. Reset uses a confirm dialog, clears only `STORAGE_KEY`, then rerenders.

- [ ] **Step 7: Run Node and manual persistence checks**

Run Node tests. In browser: complete Day 1, collapse Unit 2, select dark theme, reload and verify; export, reset, import and verify restored state. Test with localStorage manually disabled and ensure reading/navigation still work.

---

### Task 6: Resource View, Accessibility and Browser Self-Test

**Files:**
- Modify: `index.html`
- Create: `tools/ui_smoke_test.py`

**Interfaces:**
- Produces `#resources` route and `?selftest=1` automated in-browser assertions.
- `ui_smoke_test.py` serves localhost and launches installed Chrome Headless.

- [ ] **Step 1: Implement resource view**

Show every supplied resource referenced by the published curriculum with filters `all|read|unavailable` and normalized search. Each card includes URL, linked lessons, latest check/read status and limitation. Totals must derive from embedded data.

- [ ] **Step 2: Add in-browser self-test mode**

When `new URLSearchParams(location.search).get("selftest") === "1"`, run after app initialization and append:

```html
<pre id="self-test-results" data-status="pass">PASS 13/13</pre>
```

The 13 assertions must exercise actual DOM/actions:

```text
1 course data has 40 lessons
2 dashboard renders total progress
3 search “dependency injection” returns Day 14
4 search “kiem thu” returns Day 28 or relevant testing lesson
5 Unit collapse toggles aria-expanded
6 navigating to Day 1 updates route and lesson h1
7 Hint starts hidden and toggles visible
8 Solution starts hidden and toggles visible
9 Mark Completed updates header progress
10 Previous/Next destination matches ordered data
11 mobile drawer open/close state changes when viewport is mobile
12 a multiple-choice check shows authored correct/incorrect feedback and explanation only after checking
13 inaccessible-resource cards never display “đã đọc”
```

Use an in-memory storage adapter in self-test mode so tests never alter the learner’s real localStorage.

- [ ] **Step 3: Write the Chrome smoke runner**

`tools/ui_smoke_test.py` must:

1. Start `ThreadingHTTPServer` rooted at workspace on a free localhost port.
2. Locate Chrome at `C:/Program Files/Google/Chrome/Application/chrome.exe` with Edge fallback.
3. Run twice:

```text
--headless=new --disable-gpu --hide-scrollbars --virtual-time-budget=3000
--window-size=1440,1000 --dump-dom URL?selftest=1
--window-size=390,844 --dump-dom URL?selftest=1&viewport=mobile
```

4. Require `id="self-test-results" data-status="pass"` and `PASS 13/13` in both DOM dumps.
5. Capture screenshots with matching sizes to `.course-cache/ui/desktop.png` and `mobile.png`.
6. Always stop the server in `finally`.

- [ ] **Step 4: Add static accessibility checks to the runner**

Parse built HTML and fail unless it contains:

```text
lang="vi"
viewport meta
skip-link
main-content
aria-live toast region
prefers-reduced-motion
focus-visible
button labels for menu/search/theme/copy/disclosures
```

Fail on inline event handler attributes (`onclick=`, etc.), duplicate static IDs, external stylesheet/script tags and HTTP mixed-content URLs in app chrome.

- [ ] **Step 5: Run browser functional smoke tests**

Run:

```bash
python tools/ui_smoke_test.py --file index.html --output-dir .course-cache/ui
```

Expected:

```text
PASS desktop selftest=13/13 viewport=1440x1000
PASS mobile selftest=13/13 viewport=390x844
PASS screenshots=.course-cache/ui/desktop.png,.course-cache/ui/mobile.png
```

- [ ] **Step 6: Inspect desktop screenshot**

Open `.course-cache/ui/desktop.png` with the image viewer. Verify sticky header, persistent sidebar, readable measure, visual hierarchy, real title/content, accents, current/completed states and no clipping. Correct CSS and rerun if any issue appears.

- [ ] **Step 7: Inspect mobile screenshot**

Open `.course-cache/ui/mobile.png`. Verify full-width content, compact header, hamburger, no page horizontal overflow, code horizontal scroll, touch target spacing and no content hidden by sticky header. Correct CSS and rerun if needed.

---

### Task 7: Final End-to-End Verification and Delivery Audit

**Files:**
- Modify only files implicated by failed verification.

**Interfaces:** Produces final self-contained `index.html` plus verified content artifacts.

- [ ] **Step 1: Run all unit tests**

```bash
python -m unittest discover -s tests -p "test_*.py" -v
node --test tests/site_core.test.js
```

Expected: all tests pass.

- [ ] **Step 2: Revalidate sources and lessons**

```bash
python tools/validate_sources.py --manifest content/source-manifest.json --notes-dir content/source-notes
python tools/validate_lessons.py --catalog course-catalog.json --manifest content/source-manifest.json --source-notes-dir content/source-notes --lessons-dir content/lessons --compile-java
```

Expected: 111 source records accounted for and 40 lesson packages valid.

- [ ] **Step 3: Rebuild and prove single-file deployment**

```bash
python tools/build_site.py --catalog course-catalog.json --lesson-index content/lesson-index.json --lessons-dir content/lessons --manifest content/source-manifest.json --source-notes-dir content/source-notes --output index.html
python - <<'PY'
from pathlib import Path
h=Path('index.html').read_text(encoding='utf-8')
assert '<script id="course-data" type="application/json">' in h
assert '<style id="app-styles">' in h
assert '<script id="app-script">' in h
assert '<script src=' not in h and '<link rel="stylesheet"' not in h
print('PASS self-contained index.html')
PY
```

Expected: `PASS self-contained index.html`.

- [ ] **Step 4: Run Chrome desktop/mobile smoke test after final build**

Run: `python tools/ui_smoke_test.py --file index.html --output-dir .course-cache/ui`  
Expected: both viewports PASS 13/13.

- [ ] **Step 5: Manual interaction checklist**

Open the local site and verify:

```text
[ ] Search with accents and without accents
[ ] Collapse/expand a Java and a Spring module
[ ] Select lessons from every group
[ ] Copy one Java and one configuration block
[ ] Toggle Hint/Solution in two different practices
[ ] Previous/Next around Day 12→13 and Day 36→37 boundaries
[ ] Mark/unmark, reload and Continue Learning
[ ] Theme follows system and explicit choice
[ ] Export/reset/import progress
[ ] Mobile drawer keyboard Escape/focus restoration
[ ] Resources view distinguishes read and inaccessible links
```

- [ ] **Step 6: Report outcomes without overclaiming**

Delivery summary must state:

- paths to `index.html`, `course-catalog.md`, `course-catalog.json`, source-reading report and lesson-authoring report;
- exact source counts by access/read status;
- exact lessons/practices/citations counts;
- test commands and observed pass/fail output;
- desktop/mobile screenshots inspected;
- inaccessible links and content limitations;
- no claim that a blocked page was read and no claim that every section of a long manual was read when only relevant sections were used.
