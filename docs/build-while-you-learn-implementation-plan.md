# Build While You Learn — Implementation Plan (Spendwise Project Track)

> **For agentic workers:** Đây là implementation plan cho việc tích hợp **Spendwise Project Track** vào learning site hiện tại. Master plan (source of truth về sản phẩm): [build-while-you-learn-plan.md](build-while-you-learn-plan.md). Plan này chỉ mô tả *cách làm*; không thay đổi các quyết định trong master plan. Các bước dùng checkbox `- [ ]` để theo dõi.

**Goal:** Biến site từ *Course Reader* thành *Build While You Learn* = **Java/Spring Learning Track** (giữ nguyên) **+ Spendwise Project Track** (thêm mới), với hai hệ tiến độ độc lập.

**Kiến trúc tiếp cận:** Data-first. Toàn bộ Spendwise được biểu diễn bằng **một artifact dữ liệu riêng** (`content/spendwise-project.json`) được build pipeline nhúng vào model dưới key `project`. Lesson↔project mapping tham chiếu **bằng ID** và sống trong file project (không sửa lesson JSON). UI sẽ thêm route/view mới trên đúng router hiện tại; lesson sẽ thêm 2 lớp *Project Context* / *Project Application* ở tầng composition, không đụng theory `sections`.

**Tech stack:** Static single-file SPA (vanilla JS, hash router, localStorage). Build bằng Python (`tools/build_site.py`). Test: `pytest` (Python) + `node --test` (JS core) + headless Chrome smoke (`tools/ui_smoke_test.py`).

**Implementation status — 2026-09-01:** P0-1 (canonical project data), P0-2 (validator), P0-3 (build integration), và P0-4 (independent project-progress state/core) đã được implement. Data Contract Alignment checkpoint hiện chỉ khóa contract + plan + validation trước P0-5. P0-5/P0-6/P0-7 UI chưa bắt đầu và không được implement trong checkpoint này.

## Global Constraints (bắt buộc, copy verbatim từ master plan)

- KHÔNG sửa syllabus: giữ `Unit → Day → Section`; không xóa/đổi thứ tự/ thêm hàng loạt Day; giữ đúng **40 lessons / 15 units / group counts java=12, spring=24, completion=4**.
- KHÔNG sửa trực tiếp `index.html` — nó là **build artifact**, luôn được regenerate từ `index.template.html`.
- KHÔNG hard-code nội dung Spendwise trong rendering function nếu biểu diễn được bằng data. Data first, UI second.
- Course Progress và Project Progress phải **độc lập**: hoàn thành lesson KHÔNG tự đánh dấu project task; và ngược lại.
- Theory vẫn là nội dung chính của lesson. Project chỉ là context/application layer. Build task là optional.
- Renderer phải xử lý gracefully lesson **không có** project mapping.
- Version: Java 17 / Spring Boot 3.x / Spring Framework 6 / Jakarta. Không introduce dependency ngoài (site phải `external_dependencies=0`).
- Không redesign visual lớn trước khi P0 data hoàn chỉnh. Hoàn thành P0 → P1 → P2 theo thứ tự.

---

# 1. Current Architecture

Single-file static SPA. Không framework, không network dependency, không backend.

- **`index.template.html`** (hiện 3199 dòng, 152.352 bytes) = source of truth cho markup + CSS + toàn bộ JS ứng dụng. Cấu trúc:
  - `<style id="app-styles">` (dòng ~8–1066): toàn bộ CSS (design tokens `:root`, dark override `html[data-theme="dark"]`, layout, components).
  - Pre-paint theme bootstrap `<script>` (1067–1082): đọc `localStorage["java-spring-course"].theme`, set `data-theme` trước khi paint (anti-FOUC).
  - `<div id="app">` (1086): mount point duy nhất; `<div id="toast-region" aria-live="polite">` (1087).
  - **`<script id="course-data" type="application/json">{}</script>`** (1088): điểm nhúng dữ liệu (ship với literal `{}`).
  - `<script id="app-script">` (1089–3197): ứng dụng, gồm 2 phần:
    - **CourseCore** (1091–1252, giữa `/* COURSE_CORE_START */`…`/* COURSE_CORE_END */`): pure logic, không DOM, `Object.freeze`d trên `globalThis.CourseCore`. Test bằng `tests/site_core.test.js` (node:vm).
    - **IIFE** (1258–3196): toàn bộ DOM/state/render trong scope private.
- **`tools/build_site.py`**: build pipeline. `build_publication_model()` chiếu corpus authored thành UI model, `embed_course_data()` nhúng JSON vào marker `#course-data`, ghi ra `index.html` (atomic temp-then-replace). Luôn build lại từ template (không đọc lại `index.html`).
- **`content/`**: corpus authored — `lessons/day-*.json` + `ojt-evaluation.json` (nội dung), `lesson-index.json` (thứ tự 40 lesson chuẩn), `lesson-schema.json` (schema tham chiếu, **closed**), `source-manifest.json` + `source-notes/*.json` (metadata reference).
- **`course-catalog.json`**: 15 units + 40 lessons + 111 resources, sinh từ file `.xlsx` bằng `tools/extract_catalog.py` + `tools/course_model.py`.
- **`tests/`**: `site_core.test.js` (JS core), `test_validate_project.py`, `test_build_site.py`, `test_validate_lessons.py`, `test_course_model.py`, `test_check_sources.py`, `test_validate_sources.py` (pytest). `tools/ui_smoke_test.py`: headless Chrome, yêu cầu in-browser self-test `PASS ≥13/13` ở cả desktop+mobile + static a11y/hygiene checks.

# 2. Current Data Flow

```
.xlsx  ──extract_catalog.py──▶  course-catalog.json  ─┐
content/lessons/*.json  ──────────────────────────────┤
content/lesson-index.json  ────────────────────────────┼─▶ build_site.py
content/source-manifest.json + source-notes/*.json  ──┘   build_publication_model()
                                                             │  (chiếu qua LESSON_FIELDS,
                                                             │   validate 40/15/12-24-4)
                                                             ▼
                       publication model (dict)  ──embed_course_data()──▶ index.template.html
                       { schemaVersion, app, builtAt,          (thay nội dung marker duy nhất
                         units[], lessons[], resources[],       #course-data)  ──▶ index.html
                         project }
```

Runtime (trình duyệt): `index.html` load → IIFE parse `#course-data` textContent một lần thành `courseData` → dựng `lessonsById`/`unitsById` Map, `LESSON_IDS`/`UNIT_IDS`/`PRACTICE_IDS` Set → `loadState()` (đọc localStorage + `sanitizeState`) → init render: `renderApp()` → `syncThemeButton()` → `renderSidebar()` → `updateProgress()` → `routeRender()`. Điều hướng qua `hashchange`.

# 3. Source of Truth

**Kết luận quan trọng nhất của audit:**

| Thứ | Source of truth | Ghi chú |
|---|---|---|
| Markup / CSS / JS ứng dụng | **`index.template.html`** | Sửa ở đây. |
| Dữ liệu course (units/lessons/resources) | `course-catalog.json` + `content/lessons/*.json` + `content/lesson-index.json` + `content/source-*` | Nguồn cho model. |
| **`index.html`** | **KHÔNG phải source** — là **build artifact** | `build_site.py` dòng 416–420 nói rõ: luôn rebuild từ template; đọc lại index.html sẽ tích lũy state cũ và che mất edit template. **Không bao giờ sửa tay `index.html`.** Nó có được commit vào git (là site đã publish) → sau khi build phải commit lại. |
| Dữ liệu Spendwise | **`content/spendwise-project.json`** (đã có, canonical) | Nhúng vào model dưới key `project`. |

**Khối canonical (agent coding phải đọc trước khi sửa bất cứ gì):**

```
SOURCE OF TRUTH (sửa ở đây):
- index.template.html — markup + CSS + toàn bộ JS ứng dụng; ship #course-data là literal `{}` (index.template.html dòng 1088).
- course-catalog.json, content/lessons/*.json, content/lesson-index.json,
  content/source-manifest.json, content/source-notes/*.json — corpus course authored.
- content/spendwise-project.json — nguồn dữ liệu Spendwise canonical.

GENERATED OUTPUT (không bao giờ sửa tay):
- index.html — build artifact sinh bởi `python tools/build_site.py`. CHỈ nội dung (textContent)
  của marker `<script id="course-data">` (dòng ~1088) bị thay bằng embedded JSON model; phần còn
  lại của file giữ NGUYÊN cấu trúc 3199 dòng của template (index.html KHÔNG phải một dòng duy nhất).
  Được version trong git (là site đã publish) → regenerate + commit lại sau mỗi thay đổi.

FILES SAFE TO EDIT:
- index.template.html; content/spendwise-project.json; tools/validate_project.py;
  tools/build_site.py; tests/* (test_build_site.py, site_core.test.js, test_validate_project.py, …).

FILES SHOULD NOT BE EDITED DIRECTLY:
- index.html — chỉ regenerate qua `python tools/build_site.py`, KHÔNG sửa tay.
- content/lessons/*.json, content/lesson-index.json, content/lesson-schema.json (closed schema),
  course-catalog.json, content/source-*, tools/course_model.py, tools/extract_catalog.py.
```

> **Lưu ý số dòng:** mọi số dòng trong plan này là dòng trong **`index.template.html`** (không phải `index.html`). Vì course-data embed thành đúng một nội dung marker nên số dòng của `index.template.html` và `index.html` gần trùng nhau ⇒ rất dễ mở nhầm `index.html` rồi sửa artifact. Luôn mở `index.template.html` để sửa. Sau build, chạy `git diff --stat index.html` để xác nhận chỉ dòng #course-data thay đổi; nếu có diff khác nghĩa là bạn đã sửa artifact thay vì template.

Điểm nhúng dữ liệu **duy nhất**: `embed_course_data()` bắt buộc **đúng một** marker `<script id="course-data" type="application/json">` (`if len(markers) != 1: raise ValueError`). ⇒ **Không** thêm marker thứ hai; project data đi cùng model course trong marker này.

# 4. Reusable Components (giữ nguyên hoặc mở rộng — không rewrite)

Toàn bộ những phần sau được **reuse**, chỉ *mở rộng* chứ không viết lại:

- **CourseCore (pure logic, đã có test):** `normalizeSearch`, `parseRoute`, `calculateProgress(lessons, completedIds, group)`, `nextLessonId`, `sanitizeState`, `searchLessons`, `defaultState`, `escapeHtml`, `safeExternalUrl`, `calculateReleaseProgress`, `calculateFeatureProgress`. P0-4 đã mở rộng `sanitizeState`/`defaultState` và thêm hai helper project-progress trong cùng block; P0-7 sau này chỉ mở rộng `parseRoute`.
- **Routing:** hash router `parseRoute()` + dispatcher `routeRender()` (1414–1424) + `hashchange` listener (1425–1442, có passthrough cho in-page anchor). → thêm route/view mới bằng đúng pattern này.
- **Renderer:** mọi view là `render*(container, …)` độc lập; helper an toàn `el(tag,class,text)` (dùng `textContent`). `renderFullLesson` (2210–2222) compose theo thứ tự cứng: header → sections → practices → assignments → references → nav. → chèn Project Context/Application ở tầng compose này.
- **State & persistence:** `STORAGE_KEY='java-spring-course'`, `defaultState()`/`sanitizeState()`/`loadState()`/`saveState()`, `STATE_VERSION=2`. Course progress = `state.completed[]`; Project Progress = `state.projectProgress.buildTasks[]` và hai primitive độc lập.
- **Import/Export:** `downloadProgress()` xuất `{app,schemaVersion,exportedAt,state}` nên đã tự bao gồm project progress; `importProgressText()` khớp `APP_SCHEMA`, nhận version 1/2, sanitize rồi preview/confirm swap; reset dùng `defaultState()`.
- **Search / Theme / Sidebar / Prev-next / Progress meter / Responsive layout / References / Resources view / Accessibility hooks / self-test harness:** giữ nguyên; chỉ thêm, không phá.
- **Data schema course:** giữ nguyên hoàn toàn (units/lessons/resources). Lesson schema là **closed** (validator từ chối key lạ) ⇒ **không** thêm field vào lesson JSON.

# 5. Canonical Data Architecture

**Nguyên tắc:** ID ổn định · reference bằng ID · không duplicate · lesson không có mapping vẫn render tốt · backward compatible · mở rộng dễ.

**Vị trí lưu:** artifact riêng `content/spendwise-project.json` (source of truth cho Spendwise). Build nhúng nguyên vẹn (sau validate) vào `model["project"]`. **Không** chạm lesson JSON, **không** chạm `LESSON_FIELDS`. Client đọc `courseData.project`.

**Vì sao KHÔNG nhét mapping vào lesson JSON:** lesson schema là *closed* (`tools/validate_lessons.py` từ chối key ngoài `properties`); nhiều field lesson phải `deep-equal` với `catalogRef`; sửa 40 file authored = rủi ro cao cho theory. Mapping keyed-by-lesson-id trong file project = một nguồn, không đụng nội dung học.

## 5.1 Schema `content/spendwise-project.json`

```jsonc
{
  "schemaVersion": 1,
  "product": {
    "id": "spendwise",
    "name": "Spendwise",
    "type": "Personal Expense & Budget Tracker",
    "vision": "…",                       // ngắn, plain text
    // Canonical contract: outOfScope là mảng trực tiếp trên product; KHÔNG có product.scope.
    // Danh sách phải khớp ĐẦY ĐỦ và đúng thứ tự với Finance Lite trong master plan §9:
    "outOfScope": [
      "full double-entry accounting","general ledger","tax","stock trading",
      "investment portfolio","cryptocurrency","bank synchronization","Open Banking",
      "OCR receipt","family/shared finance","financial advisor","loan system",
      "payment gateway","microservices","Kafka","Kubernetes","mobile app","blockchain",
      "complex accounting reconciliation","support for every bank file format",
      "full multi-currency accounting engine"
    ]
    // KHÔNG có product.capabilities: danh sách năng lực suy ra từ features[].name (tránh trùng registry).
  },

  "releases": [                          // V0.1 → V1.0, đúng 10 release theo master plan §11
    {
      "id": "v0-1",                      // ID ổn định (kebab, không dấu chấm cho URL-safe)
      "version": "V0.1",
      "title": "Java Domain",             // canonical release display field (không dùng release.name)
      "order": 1,
      // enum: released | building | planned — AUTHORED, không suy ra từ course progress.
      // MẶC ĐỊNH tất cả "planned"; đặt "building" cho ĐÚNG release đang xây thật;
      // "released" CHỈ khi có artifact Spendwise verify được (master plan §20 "không dùng status giả").
      "status": "planned",
      "problem": "…",                   // "Spendwise đang gặp vấn đề gì"
      "goal": "…",
      "featureIds": ["feat-money","feat-account","feat-transaction","feat-category"],
      "learningDependencies": ["Class","Encapsulation","Enum","Exception"],  // text, để hiển thị
      "acceptanceCriteria": ["Tạo được Account","Business invariants cơ bản được bảo vệ","…"],
      "buildTaskIds": ["task-money-vo","task-account-entity"]   // THỨ TỰ task trong release (ordering authority)
    }
    // … v0-2 … v1-0
  ],

  "features": [                          // đơn vị năng lực sản phẩm, tái dùng bởi nhiều release
    {
      "id": "feat-account",
      "name": "Account Management",
      "description": "Tạo/sửa/đóng account, nhiều loại (cash, bank, card), số dư.",
      "domainEntities": ["Account","Money"],
      "introducedInReleaseId": "v0-1"    // release đầu tiên feature xuất hiện (không suy ra status)
    }
    // Canonical artifact hiện có 25 feature, gồm feat-statistics, feat-cache và feat-exchange-rate;
    // không dùng proxy cho ba năng lực này.
  ],

  "milestones": [                        // mốc lớn xuyên nhiều release (hiển thị roadmap)
    { "id": "ms-domain-solid", "name": "Domain vững", "releaseIds": ["v0-1","v0-2"], "summary": "…" },
    { "id": "ms-api-live",     "name": "API chạy",   "releaseIds": ["v0-4","v0-5"], "summary": "…" }
  ],

  "architectureStages": [                // tiến hóa kiến trúc theo release
    {
      "id": "arch-v0-1",
      "releaseId": "v0-1",
      "title": "Pure Java domain, in-memory",
      "layers": ["Domain (POJO/Value Object)"],
      "diagram": "Console → InMemoryStore → Domain",   // ASCII 1 dòng, render <pre>
      "changesFromPrev": "Khởi tạo domain model",
      "rationale": "…"
    }
    // … arch-v0-3 thêm Spring context, arch-v0-4 thêm REST, arch-v0-5 thêm JPA/DB …
  ],

  "buildTasks": [                        // đơn vị NHỎ NHẤT của project progress (primitive)
    {
      "id": "task-money-vo",
      "title": "Money value object (BigDecimal + Currency)",
      "releaseId": "v0-1",
      "featureIds": ["feat-money"],
      "problem": "Dùng double cho tiền gây sai số.",
      "goal": "Money immutable, BigDecimal, phép cộng/trừ an toàn.",
      "constraints": ["BigDecimal, không double","immutable","equals/hashCode theo amount+currency"],
      "acceptanceCriteria": ["add/subtract đúng","không mất precision","reject currency lệch"],
      "relevantLessonIds": ["day-04","day-08"],   // bằng chứng từ nội dung lesson thật
      "required": true                             // required !== false tính vào % release; false = stretch
    }
    // … task-account-entity, task-transaction-entity, …
  ],

  "lessonMap": {                         // keyed BY LESSON ID (ổn định) — lesson thiếu key = graceful
    "day-01": {
      "applicationType": "direct",       // enum: direct | future | theory
      "releaseId": "v0-1",
      "featureIds": ["feat-money"],
      "buildTaskIds": [],
      "projectProblem": "Spendwise phải biểu diễn tiền mà không mất độ chính xác.",
      "context": "Kiểu số là nền tảng kỹ thuật của Money value object.",
      "application": "Dùng BigDecimal thay vì double khi xây Money ở V0.1."
    },
    "day-04": {
      "applicationType": "direct",
      "releaseId": "v0-1",
      "featureIds": ["feat-account","feat-money","feat-transaction"],
      "buildTaskIds": [
        "task-money-vo","task-account-entity","task-transaction-entity","task-domain-validation"
      ],
      "projectProblem": "Domain object phải tự bảo vệ invariant.",
      "context": "Encapsulation là kỹ thuật dựng Account, Money và Transaction hợp lệ.",
      "application": "Dùng field private, constructor validation và hành vi domain có nghĩa."
    },
    "day-10": {
      "applicationType": "direct",
      "releaseId": "v0-2",
      "featureIds": ["feat-statistics","feat-repository","feat-transaction"],
      "buildTaskIds": ["task-transaction-service","task-statistics-aggregation"],
      "projectProblem": "Spendwise cần group và sum transaction theo category.",
      "context": "Stream + Collectors là engine cho thống kê chi tiêu.",
      "application": "Dùng groupingBy và collector tổng hợp cho statistics V0.2."
    },
    "day-20": {
      "applicationType": "direct",
      "releaseId": "v0-5",
      "featureIds": ["feat-persistence","feat-atomic-transfer"],
      "buildTaskIds": ["task-spring-data-repositories","task-atomic-transfer","task-optimistic-locking"],
      "projectProblem": "Truy vấn phải phân trang an toàn và thao tác tiền phải commit/rollback nguyên tử.",
      "context": "Repository nâng cao và transaction bảo vệ dữ liệu Spendwise.",
      "application": "Dùng pagination/sorting và @Transactional; @Version là optional hardening."
    }
    // Canonical P0 data có 38 entry day-01..day-38. Hai lesson tổng hợp day-39-64 và day-65-66
    // được chủ ý để unmapped; renderer phải xử lý graceful. Không có field lessonMap.concept.
  }
}
```

### 5.1.1 Canonical release status và task ordering

Cả 10 release hiện authored `status: "planned"`; không release nào được suy thành `building`/`released` từ course progress. `release.buildTaskIds` là ordering authority, còn `buildTask.releaseId` là ownership pointer. Hai chiều phải khớp:

| Release | Ordered `buildTaskIds` |
|---|---|
| V0.1 (`v0-1`) | `task-money-vo`, `task-account-entity`, `task-transaction-entity`, `task-category-enum`, `task-domain-validation` |
| V0.2 (`v0-2`) | `task-repository-interface`, `task-inmemory-repository`, `task-transaction-service`, `task-statistics-aggregation`, `task-csv-read-write` |
| V0.3 (`v0-3`) | `task-spring-bootstrap`, `task-di-service-beans`, `task-config-profiles` |
| V0.4 (`v0-4`) | `task-rest-controllers`, `task-dto-mapping`, `task-bean-validation`, `task-error-handling-advice` |
| V0.5 (`v0-5`) | `task-jpa-entities`, `task-jpa-relationships`, `task-spring-data-repositories`, `task-atomic-transfer`, `task-optimistic-locking` |
| V0.6 (`v0-6`) | `task-jwt-auth`, `task-ownership-checks` |
| V0.7 (`v0-7`) | `[]` |
| V0.8 (`v0-8`) | `[]` |
| V0.9 (`v0-9`) | `[]` |
| V1.0 (`v1-0`) | `[]` |

Empty arrays ở V0.7–V1.0 là intentional. Không invent task chỉ để làm mảng non-empty. Mỗi task authored phải xuất hiện đúng một lần trong ordered array của owner release.

**Ghi chú field theo `applicationType`:**
- Mọi loại bắt buộc có `applicationType` + `context`.
- `direct`: bắt buộc thêm `releaseId`, `featureIds` không rỗng, `buildTaskIds` (được phép rỗng), `projectProblem`, `application`. Lesson này trực tiếp dựng/áp dụng một phần Spendwise.
- `future`: bắt buộc thêm `releaseId`, `featureIds` không rỗng, `buildTaskIds` (được phép rỗng), `application`; `projectProblem` là optional nhưng nếu có phải là chuỗi không rỗng.
- `theory`: chỉ cần hai field chung; canonical theory entry không có release/feature/task/application. Renderer chỉ hiện ngữ cảnh nhẹ hoặc bỏ qua.
- Lesson **không có** key trong `lessonMap`: renderer bỏ hoàn toàn phần project (graceful) — hợp lệ.

## 5.2 Referential integrity (validator bắt buộc)

Validator canonical `tools/validate_project.py` kiểm tra `content/spendwise-project.json` — build **fail** nếu vi phạm (fail-fast, không nhúng data hỏng):

- `schemaVersion == 1`; `product.id` cùng mọi `id` của release/feature/buildTask/milestone/architectureStage dùng **một registry global**: không ID nào được trùng với bất kỳ object nào khác trong toàn artifact.
- Mọi ID trên phải URL-safe: `^[a-z0-9][a-z0-9-]*$` (không dấu chấm — release ID dùng làm route `#/release/<id>`).
- `releases`: đúng spine 10 release V0.1→V1.0, `order` chính xác 1..10; `status ∈ {released,building,planned}` và hiện cả 10 đều authored là `planned`.
- Mọi tham chiếu ID resolve được: `release.featureIds`→features, `release.buildTaskIds`→buildTasks; `buildTask.releaseId`→releases, `buildTask.featureIds`→features; `feature.introducedInReleaseId`→releases; `milestone.releaseIds`→releases; `architectureStage.releaseId`→releases. *(Bỏ `release.architectureStageId` — quan hệ release↔stage 1:1 tra bằng `architectureStage.releaseId`, không cần con trỏ hai chiều — §5.3.)*
- **Ràng buộc chéo release↔task (FAIL, không chỉ cảnh báo):** `release.buildTaskIds` là ordering authority; mọi ID phải resolve, không được duplicate/list dưới nhiều release, và `buildTasks[taskId].releaseId` **phải bằng** release chứa nó. Ngược lại, **mỗi buildTask phải xuất hiện đúng một lần** trong `buildTaskIds` của release mà `task.releaseId` sở hữu; task bị bỏ sót cũng fail.
- **Ràng buộc lessonMap entry ↔ task (FAIL):** nếu entry có `buildTaskIds`, thì mọi task được trỏ phải có `releaseId == entry.releaseId`, và `entry.featureIds` phải **là superset** của hợp các `featureIds` của các task đó. `entry.releaseId` là *display authority* cho lesson (dùng ở dashboard/map).
- `lessonMap`: **mọi key phải là lesson id hợp lệ** (nằm trong canonical `LESSON_IDS`); `applicationType ∈ {direct,future,theory}`; mọi entry có `context`; `direct`/`future` đều cần valid `releaseId`, non-empty `featureIds`, `buildTaskIds` list và `application`; `direct` còn cần `projectProblem`, còn `future` chỉ validate field này nếu authored; `theory` không cần các field project-specific. Mọi reference resolve được. Canonical artifact hiện có đúng 38 entry; `day-39-64` và `day-65-66` chủ ý unmapped.
- **Closed schema theo TỪNG object (không chỉ top-level)** — khớp `content/lesson-schema.json` ("every object kind is closed"): định nghĩa tập key cho phép cho *mỗi* loại object (`product`, `release`, `feature`, `milestone`, `architectureStage`, `buildTask`, và mỗi entry trong `lessonMap`) và báo lỗi với bất kỳ key ngoài tập đó (chống typo như `realeaseId`/`aplication` lọt qua rồi render rỗng). Top-level cũng closed: `{schemaVersion,product,releases,features,milestones,architectureStages,buildTasks,lessonMap}`. Thêm test tương ứng (vd `test_unknown_key_in_release_rejected`) cạnh `test_unknown_top_key_rejected`.
- `product.outOfScope` là canonical shape trực tiếp (không có `product.scope`), phải khớp chính xác danh sách Finance Lite đầy đủ trong master plan §9; thiếu/thừa/đổi thứ tự/duplicate đều fail.

## 5.3 Tích hợp build (`tools/build_site.py`)

- CLI hiện có arg `--project` với default `content/spendwise-project.json`.
- `build_publication_model()` hiện load JSON project → gọi validator (raise nếu lỗi) → gắn `model["project"] = project_data` **nguyên vẹn** (đã là JSON-safe). `LESSON_FIELDS` không đổi, lesson không có field project mới, và không có marker thứ hai.
- Cross-check hai nguồn (fail build nếu lệch): `build_site.py` giữ `EXPECTED_LESSON_IDS` làm publication sequence; validator standalone giữ canonical `LESSON_IDS`. Trong build thật, `_load_project_model()` truyền tập ID của chính `lessons_out` vào `validate_project(..., valid_lesson_ids=...)`, nên project validation dùng corpus vừa build và không thể trỏ tới lesson không được publish.
- `embed_course_data()` giữ nguyên: vẫn đúng một marker `#course-data`; `_json_escape_for_script()` thay ba ký tự `<`, `>`, `&` bằng các Unicode escape sequence tương ứng U+003C, U+003E, U+0026 trước khi nhúng. Project data đi *chung* trong marker này ⇒ ràng buộc "đúng một marker" không đổi.
- Kích thước: project.json nhỏ (vài chục KB) so với corpus lessons ⇒ không lo ngại payload.

**Client đọc:** IIFE parse `#course-data` → `courseData`, rồi đặt `projectData = courseData.project || null` (null-safe: nếu build cũ chưa có `project`, course vẫn chạy). Runtime dựng `releasesById`, `featuresById`, `buildTasksById`, `archStageByReleaseId` và **`projectByLessonId` đều là `Map`**. Riêng lesson mapping được nạp bằng `Object.keys(projectData.lessonMap || {}).forEach(k => projectByLessonId.set(k, lessonMap[k]))`, nên mọi call-site tra bằng `projectByLessonId.get(lessonId)`; không mô tả nó như object lookup.

# 6. Project Progress State (độc lập hoàn toàn với Course Progress)

**Bất biến quan trọng:** hoàn thành lesson KHÔNG tự tick build task, và tick build task KHÔNG tự complete lesson. Hai hệ chỉ *hiển thị cạnh nhau*, không bao giờ đồng bộ trạng thái.

## 6.1 Hình dạng state (bump `STATE_VERSION` 1 → 2)

`defaultState()` hiện tại:

```js
{
  version: 2,               // STATE_VERSION = 2
  completed: [],            // COURSE progress — giữ nguyên tên/ý nghĩa
  lastLessonId: null,
  practice: {},
  collapsedUnits: [],
  theme: "system",
  projectProgress: {        // PROJECT progress, độc lập
    buildTasks: []          // primitive = mảng buildTask id đã hoàn thành
  }
}
```

- **Primitive duy nhất của project = `projectProgress.buildTasks[]`** (danh sách task done). Không lưu % — mọi mức cao hơn là *derived*.
- **Derived (tính lúc render, không lưu):**
  - Feature progress = (#required buildTasks của feature đã done) / (#required buildTasks của feature).
  - Release progress = (#required buildTasks của release đã done) / (#required buildTasks của release) — khớp master plan §24 (chỉ đếm `required:true`).
  - `stretch` (`required:false`) hiển thị nhưng không tính mẫu số.
- **KHÔNG lưu** release.status theo user; `status` là authored trong data (released/building/planned) và độc lập với việc user tick task.

## 6.2 Sanitize & migration

`sanitizeState(input, validLessonIds, validUnitIds, validPracticeKeys, validBuildTaskIds = new Set())` — API canonical có tham số thứ 5:

- Luôn khởi tạo từ `defaultState()` rồi copy các key hợp lệ (pattern hiện có) ⇒ **tự migrate**: state v1 (không có `projectProgress`) nạp vào → nhận `projectProgress` mặc định `{buildTasks:[]}`, `completed[]` cũ **được giữ nguyên** (không mất tiến độ học).
- `projectProgress.buildTasks`: lọc chỉ giữ id ∈ `validBuildTaskIds` (drop id lạ / task đã bị xóa khỏi data), unique, giữ thứ tự.
- **Phòng thủ (đã có):** tham số thứ 5 có default `validBuildTaskIds = new Set()`, nên call-site cũ không truyền arg này vẫn không ném `TypeError`. Hai call-site runtime hiện đều truyền đủ: `loadState` dòng 1303 và `importProgressText` dòng 1579.
- Sau sanitize, `state.version = STATE_VERSION` (2). Không có nhánh migration thủ công nào khác — rebuild-from-default là migration.
- `validBuildTaskIds` = `new Set((courseData.project?.buildTasks||[]).map(t=>t.id))`; nếu không có project data → Set rỗng → `buildTasks` luôn sạch.

## 6.3 Toggle handlers (hai hệ riêng biệt)

- Course completion **không** có hàm tên `toggleLessonComplete`; nó là **delegated handler** gắn vào `data-action="toggle-completion"` đọc `data-lesson-id` (`index.template.html:2542-2552`), chỉ mutate `state.completed` rồi `saveState()`. Giữ nguyên cơ chế này.
- Handler `toggleBuildTask(taskId)` hiện chỉ đụng `state.projectProgress.buildTasks` rồi `saveState()`. P0-5/P0-6 sẽ gọi handler này khi có UI; handler **không** gọi tới `completed`, và course completion handler không gọi tới project progress.
- Hai helper thuần trong CourseCore (test được) theo API thực tế: `calculateReleaseProgress(buildTasks, completedTaskIds, releaseId)` và `calculateFeatureProgress(buildTasks, completedTaskIds, featureId)` → trả `{completed, total, percent}` và chỉ đếm task không có `required:false`. Đặt cạnh `calculateProgress` trong block `COURSE_CORE`.

**Reset semantics (P0 UI follow-up, không thuộc data-contract checkpoint này):** nút "Đặt lại **toàn bộ** tiến độ" hiện chạy `state = CourseCore.defaultState()` (`index.template.html:1645-1654`), nên đã **có chủ đích xóa CẢ HAI hệ** (course `completed[]` + `projectProgress.buildTasks[]`) cùng `lastLessonId/practice/collapsedUnits/theme`. Đây là hành vi mong muốn; bất biến độc lập chỉ cấm đồng bộ theo toggle, không cấm một nút reset tất cả cố ý.
- Text confirm hiện chỉ nêu trạng thái hoàn thành/bài đang học/theme, chưa nói rõ project progress. **Giữ đây là việc P0 UI phải làm sau checkpoint**, không sửa template trong Data Contract Alignment: đổi text thành *"Đặt lại toàn bộ tiến độ? Hành động này xóa trạng thái hoàn thành khóa học, tiến độ build project, bài đang học và cài đặt giao diện đã lưu trên máy bạn."*
- **KHÔNG** tách thành hai nút `resetCourseProgress()`/`resetProjectProgress()`: không có yêu cầu nào trong master plan đòi "reset một hệ không đụng hệ kia".

## 6.4 Import / Export backward-compatible

- `downloadProgress()`: giữ format `{app, schemaVersion, exportedAt, state}`. Vì `state` có `projectProgress`, export tự động bao gồm project progress; `APP_SCHEMA.schemaVersion` hiện là 2.
- `importProgressText()` hiện đã **chấp nhận `{1, 2}`** qua `SUPPORTED_IMPORT_VERSIONS`:
  - file v2 → nạp `state` qua `sanitizeState` như thường (có `projectProgress`).
  - file v1 (cũ, người dùng đã export trước đây) → vẫn nhận; thiếu `projectProgress` ⇒ sanitize thêm default `{buildTasks:[]}`; `completed[]` giữ nguyên. **Không vỡ file cũ.**
  - `app` vẫn phải khớp `"java-spring-course"`.
  - **Cả hai call-site hiện truyền đủ 5 tham số:** `loadState` (`index.template.html:1303`) và `importProgressText` (`:1579`) đều truyền `BUILD_TASK_IDS`, nên task ID lạ bị lọc khi load lẫn import. Default ở §6.2 vẫn bảo vệ tương thích với call-site cũ.
- Filename export giữ nguyên `java-spring-course-tien-do.json` (không đổi để không gây bất ngờ).

---

# 7. Curriculum → Spendwise Mapping Strategy (dựa trên NỘI DUNG THẬT)

**Quy tắc phân loại** (đọc `outcomes` + `sections` của từng lesson, KHÔNG chỉ đọc tiêu đề Day):

| Loại | Điều kiện | Bắt buộc field trong `lessonMap` | Có build task? |
|---|---|---|---|
| **direct** | Khái niệm của lesson *trực tiếp* dựng hoặc áp dụng một phần Spendwise | `applicationType`, `context`, `projectProblem`, `application`, `releaseId`, non-empty `featureIds`, `buildTaskIds` list | Có thể có; list được phép rỗng |
| **future** | Khái niệm sẽ dùng cho Spendwise nhưng ở release xa; giờ chưa build | `applicationType`, `context`, `application`, `releaseId`, non-empty `featureIds`, `buildTaskIds` list; `projectProblem` optional | Thường không; list vẫn phải có và được phép rỗng |
| **theory** | Nền tảng/tooling/kiến thức chung, không map thẳng vào feature nào | `applicationType`, `context` | KHÔNG |

**Không ép buộc:** lesson thuần lý thuyết (vd. canonical `day-02`, các exam `day-37`/`day-38`) có thể là `theory`; lesson không thuộc Spendwise (canonical `day-39-64`/`day-65-66`) có thể không có entry — đó là hợp lệ, không phải thiếu sót. `day-01` không phải ví dụ theory: canonical mapping của nó là `direct` cho `feat-money` ở V0.1.

## 7.1 Canonical authored mapping (khớp `content/spendwise-project.json`)

> Bảng này là snapshot **đã chốt** của 38 entry `day-01`…`day-38`, không còn là candidate seed. `content/spendwise-project.json` là authority thực thi; validator bảo đảm mọi release/feature/task reference resolve và mọi task reference khớp release + feature set của entry. Hai aggregate lesson `day-39-64` và `day-65-66` chủ ý không có entry.

| Lesson | Authored type | Release | Feature IDs | Ordered task references |
|---|---|---|---|---|
| day-01 | direct | v0-1 | feat-money | — |
| day-02 | theory | — | — | — |
| day-03 | theory | — | — | — |
| day-04 | direct | v0-1 | feat-account, feat-money, feat-transaction | task-money-vo, task-account-entity, task-transaction-entity, task-domain-validation |
| day-05 | future | v0-7 | feat-rule | — |
| day-06 | theory | — | — | — |
| day-07 | future | v0-2 | feat-repository | task-repository-interface |
| day-08 | theory | — | — | — |
| day-09 | theory | — | — | — |
| day-10 | direct | v0-2 | feat-statistics, feat-repository, feat-transaction | task-transaction-service, task-statistics-aggregation |
| day-11 | future | v0-8 | feat-import | — |
| day-12 | future | v0-8 | feat-import | — |
| day-13 | direct | v0-3 | feat-spring-migration | task-spring-bootstrap |
| day-14 | direct | v0-3 | feat-spring-migration | task-di-service-beans, task-config-profiles |
| day-15 | theory | — | — | — |
| day-16 | direct | v0-4 | feat-api | task-rest-controllers, task-dto-mapping |
| day-17 | direct | v0-4 | feat-api | task-bean-validation, task-error-handling-advice |
| day-18 | theory | — | — | — |
| day-19 | direct | v0-5 | feat-persistence | task-jpa-entities, task-jpa-relationships, task-spring-data-repositories |
| day-20 | direct | v0-5 | feat-persistence, feat-atomic-transfer | task-spring-data-repositories, task-atomic-transfer, task-optimistic-locking |
| day-21 | theory | — | — | — |
| day-22 | direct | v0-6 | feat-auth | task-jwt-auth |
| day-23 | direct | v0-6 | feat-ownership, feat-auth | task-ownership-checks |
| day-24 | direct | v0-6 | feat-auth, feat-ownership | — |
| day-25 | direct | v0-9 | feat-cache, feat-async-import, feat-scheduler | — |
| day-26 | direct | v0-8 | feat-import, feat-exchange-rate | — |
| day-27 | theory | — | — | — |
| day-28 | theory | — | — | — |
| day-29 | direct | v0-9 | feat-observability | — |
| day-30 | direct | v0-9 | feat-observability | — |
| day-31 | theory | — | — | — |
| day-32 | theory | — | — | — |
| day-33 | theory | — | — | — |
| day-34 | theory | — | — | — |
| day-35 | theory | — | — | — |
| day-36 | theory | — | — | — |
| day-37 | theory | — | — | — |
| day-38 | theory | — | — | — |

**Feature decision đã đóng:** canonical artifact có 25 features. `feat-statistics`, `feat-cache` và `feat-exchange-rate` đều là feature thật; không dùng `feat-report` hoặc feature gần nhất làm proxy. Validator từ chối mọi feature reference dangling.

## 7.2 Quy trình bảo trì mapping sau P0

Canonical mapping đã authored; không reclassify khi làm UI. Khi master plan hoặc lesson content được thay đổi có chủ đích:

1. Đọc lại lesson thật (`outcomes` + `sections`) và master roadmap trước khi sửa entry.
2. Giữ đúng semantics `direct`/`future`/`theory`; không tạo mapping chỉ để đạt số lượng.
3. Nếu entry trỏ task, giữ `entry.releaseId == task.releaseId` và `entry.featureIds` bao phủ toàn bộ `task.featureIds`.
4. Phân biệt task core (`required:true`) với optional hardening (`required:false`); không đổi chỉ để làm đẹp phần trăm.
5. Chạy `python tools/validate_project.py` và full build validation sau mọi thay đổi contract.

# 8. Route / View Architecture (mở rộng router hiện tại, KHÔNG đụng route cũ)

## 8.1 Route hiện có (giữ nguyên hành vi)

`parseRoute(hash)` (template ~1106–1113): `""`/`dashboard`→`{view:"dashboard"}`; `resources`→`{view:"resources"}`; `lesson/(.+)`→`{view:"lesson", lessonId}`; còn lại→`dashboard`. `routeRender()` (~1414–1424) dispatch theo `view`.

## 8.2 Route MỚI (thêm nhánh, không sửa nhánh cũ)

| Hash | view | Params | Mục đích |
|---|---|---|---|
| `#/project` | `project` | — | Project Overview (Spendwise là gì, release hiện tại, progress tổng) |
| `#/roadmap` | `roadmap` | — | Spendwise Roadmap V0.1→V1.0 (list release + status + progress) |
| `#/release/<id>` | `release` | `releaseId` | Release Detail (problem/goal/features/tasks/acceptance/architecture stage) |
| `#/map` | `map` | — | Course ↔ Project Map (lesson → release/feature, lọc theo loại) |
| `#/architecture` | `architecture` | — | Architecture Evolution (các `architectureStages` theo release) |

**Mở rộng `parseRoute`** (thêm case, giữ default an toàn). Lưu ý: hàm hiện có dùng biến tên **`raw`** (không phải `clean`) cho phần hash đã strip — snippet dưới đây khớp tên biến thật:

```js
if (raw === "project") return { view: "project" };
if (raw === "roadmap") return { view: "roadmap" };
if (raw === "map") return { view: "map" };
if (raw === "architecture") return { view: "architecture" };
const rel = raw.match(/^release\/(.+)$/);
if (rel) return { view: "release", releaseId: rel[1] };
```

(giữ `dashboard`/`resources`/`lesson` y nguyên; fallthrough vẫn `dashboard`). **Không đổi** regex `lesson/(.+)`. Test `parseRoute` mới trong `site_core.test.js`.

**Mở rộng `routeRender`** — hàm thật là **chuỗi `if/else if` trên `route.view`** (KHÔNG phải `switch`), và render vào container **`#route-view`** (KHÔNG phải biến `main`). Thêm nhánh **mới** đúng phong cách hiện có, không đổi các nhánh cũ (`dashboard`/`lesson`/`resources`); nếu `!projectData` thì các nhánh project render empty-state "Project track chưa sẵn sàng":

```js
} else if (view === "project") {
  renderProjectOverview(routeView);
} else if (view === "roadmap") {
  renderRoadmap(routeView);
} else if (view === "release") {
  renderReleaseDetail(routeView, route.releaseId);   // id sai → not-found panel + link roadmap
} else if (view === "map") {
  renderCourseProjectMap(routeView);
} else if (view === "architecture") {
  renderArchitecture(routeView);
}
```

> `routeView`/`view` ở trên là chính các biến hàm đang dùng (lấy `#route-view` và `route.view`); khớp tên thật khi implement, đừng tạo biến `main` mới.

## 8.3 Nav affordance (bắt buộc — hiện header KHÔNG có nav; `#resources` hiện không có link UI)

- Thêm **một** primary nav vào `renderApp()` header (chưa có view-switcher). **P0 chỉ ship các link đã có view thật:** **Học** (`#/dashboard`), **Dự án** (`#/project`), **Lộ trình** (`#/roadmap`), **Tài nguyên** (`#/resources`). Đây cũng vá luôn việc `#resources` trước đây không reachable.
- **Link Bản đồ (`#/map`) và Kiến trúc (`#/architecture`) hoãn sang P1** — các view đó chỉ có stub ở P0; ĐỪNG thêm link nav trỏ tới view rỗng (tránh dead-end cho người dùng). Thêm hai link này vào nav khi P1 hoàn thiện `renderCourseProjectMap`/`renderArchitecture`.
- Nav là `<a href="#/…">` thuần (không inline `onclick` — smoke test cấm handler inline trong markup). Mỗi link mang thuộc tính `data-view="dashboard|project|roadmap|resources"` để đánh dấu active không phụ thuộc parse href.
- **Đánh dấu active cần helper MỚI `updateNavActive(view)`** — KHÔNG tái dùng `setAriaCurrent` hiện có (hàm đó chỉ quét `.lesson-link` để highlight lesson trong sidebar, không biết tới nav header). `updateNavActive(view)`: xóa `aria-current` khỏi mọi `[data-view]` rồi set `aria-current="page"` cho link có `data-view===view`. **Gọi từ trong `routeRender`** (sau khi đã xác định `view`) để nav luôn khớp route hiện tại — kể cả khi điều hướng bằng gõ hash trực tiếp.
- Nav keyboard-focusable; responsive (collapse ở mobile 390px — tái dùng pattern menu/`prefers-reduced-motion` hiện có).
- **Không** đổi cấu trúc `#main-content`, skip-link, `aria-live` (smoke test static checks phụ thuộc).

## 8.4 Không đụng runtime hooks smoke-test yêu cầu

Giữ nguyên mọi label runtime mà `ui_smoke_test.py` kiểm: `'main-content'`, `'Danh mục khóa học'`, `'Tìm kiếm bài học'`, `Tiến độ khóa học`, `"Sao chép mã mẫu vào clipboard"`, `'Mở danh mục'`. Nav mới chỉ *thêm* nhãn, không xóa nhãn cũ.

---

# 9. P0 Implementation Plan (Core — P0-1..P0-4 đã implement; P0-5..P0-7 còn pending)

**Mục tiêu hoàn chỉnh của P0:** canonical project data + validator + build integration; state có `projectProgress` (migration an toàn); dashboard trả lời 4 câu hỏi; lesson có Project Context/Application ở tầng compose; Project Overview + Roadmap tối thiểu; nav mới; toàn bộ test xanh; rebuild `index.html`. Data Contract Alignment checkpoint hiện dừng trước phần UI P0-5.

## 9.0 Dashboard data requirements (nguồn dữ liệu từng widget — làm ở Task P0-5)

| Widget | Câu hỏi trả lời | Nguồn dữ liệu | Ghi chú |
|---|---|---|---|
| Current Lesson | "Đang học gì?" | `state.lastLessonId` → `lessonsById` (fallback: lesson đầu chưa completed) | đã có sẵn logic gần giống |
| Learning Progress | "Học tới đâu?" | `calculateProgress(lessons, state.completed)` | reuse nguyên |
| Current Spendwise Release | "Đang xây release nào?" | release có `status==="building"` (nếu không có → release `planned` có `order` nhỏ nhất) | AUTHORED, không suy từ course |
| Current Milestone | "Đang ở mốc nào?" | `milestones[]` chứa `currentReleaseId` trong `releaseIds` (nếu không có → ẩn) | derived từ current release; null-safe |
| Project Progress | "Xây tới đâu?" | `calculateReleaseProgress(projectData.buildTasks, state.projectProgress.buildTasks, currentReleaseId)` | derived, chỉ `required` |
| Today's Project Impact | "Bài hôm nay góp gì cho Spendwise?" | `projectByLessonId.get(currentLessonId)` → `application`/`featureIds` | rỗng nếu theory/không map |
| Next Learning Step | "Học gì tiếp?" | resolve `currentId = state.lastLessonId ?? lesson đầu chưa completed`, rồi `nextLessonId(lessons, currentId, 1)` | **signature thật là `nextLessonId(lessons, currentId, delta)`** — KHÔNG phải `(lessons, completed, lastLessonId)`; null-safe (trả `null` nếu đã ở lesson cuối → ẩn) |
| Next Build Step | "Xây gì tiếp?" | buildTask `required:true` **đầu tiên chưa done** theo **thứ tự trong `release.buildTaskIds`** của current release | buildTask **không có** field `order`; thứ tự lấy từ mảng `release.buildTaskIds` (ordering authority — §5.1); rỗng → ẩn |

Tất cả widget project **null-safe**: `projectData==null` hoặc lesson không map → widget tự ẩn / hiện empty-state, dashboard course vẫn nguyên.

## 9.1 Task P0-1 — Canonical `content/spendwise-project.json` (implemented)

**File:** `content/spendwise-project.json`

**Implemented contract:**
- [x] `schemaVersion:1`, canonical `product`, và đúng **10 releases** V0.1→V1.0 (`id` `v0-1`..`v1-0`, `order` 1..10). Canonical release field là `title` (không dùng `name`). Mỗi release có authored `status` + ordered `buildTaskIds`; hiện cả 10 là `"planned"` vì chưa có Spendwise artifact thật được verify. V0.7→V1.0 có mảng task rỗng có chủ đích; không tạo task giả.
- [x] `product.outOfScope` là mảng trực tiếp trên `product` (không có `product.scope`), khớp đầy đủ và đúng thứ tự 21 mục Finance Lite của master §9. Không có `product.capabilities` hoặc `scope.lite`.
- [x] Canonical `features[]` có 25 entries, gồm `feat-statistics`, `feat-cache`, `feat-exchange-rate` là feature riêng; không dùng proxy.
- [x] Có 10 `architectureStages[]`, mỗi release một stage.
- [x] Có 24 `buildTasks[]` authored cho V0.1–V0.6. `required:true` là task cốt lõi; `required:false` là hardening/portfolio tùy chọn (vd optimistic locking `@Version`).
- [x] `lessonMap{}` có đúng **38 entries day-01..day-38** theo table §7.1; `day-39-64` và `day-65-66` chủ ý unmapped.
- [x] Có 4 `milestones[]` authored.

## 9.2 Task P0-2 — Validator `tools/validate_project.py` (implemented bằng TDD)

**Files:**
- Implemented: `tools/validate_project.py`
- Tests: `tests/test_validate_project.py`

**Interfaces:** `validate_project(data: dict, *, valid_lesson_ids: set | None = None) -> list[str]` (list lỗi; rỗng = hợp lệ); CLI `main(argv=None) -> int`. Build integration gọi `validate_project` trực tiếp với lesson ids thực tế rồi raise `ValueError` nếu có lỗi; không có wrapper `load_and_validate`.

> Các bước RED/GREEN dưới đây là implementation record của P0-2, không phải công việc còn pending.

- [ ] **Step 1 — test fail trước:** viết `tests/test_validate_project.py`:
```python
import json, pathlib
from tools.validate_project import main, validate_project
FIX = json.loads(pathlib.Path("content/spendwise-project.json").read_text("utf-8"))
def test_real_file_is_valid():
    assert validate_project(FIX) == []
def test_dangling_feature_ref_detected():
    bad = json.loads(json.dumps(FIX)); bad["releases"][0]["featureIds"].append("feat-nope")
    assert any("feat-nope" in e for e in validate_project(bad))
def test_bad_lessonmap_key_detected():
    bad = json.loads(json.dumps(FIX)); bad["lessonMap"]["day-99"] = {"applicationType":"theory"}
    assert any("day-99" in e for e in validate_project(bad))
def test_unknown_top_key_rejected():
    bad = json.loads(json.dumps(FIX)); bad["surprise"] = 1
    assert any("surprise" in e for e in validate_project(bad))
```
- [ ] **Step 2 — chạy, xác nhận FAIL** (`python -m pytest tests/test_validate_project.py -q` → import error / fail).
- [ ] **Step 3 — implement** `validate_project` theo đúng ràng buộc §5.2: closed top-level + per-object keys; id unique + regex `^[a-z0-9][a-z0-9-]*$`; spine/order 1..10; `status` enum; release `buildTaskIds` bắt buộc và là ordering authority; kiểm tra hai chiều task↔release; resolve mọi ID ref; `lessonMap` key ∈ canonical `LESSON_IDS` (hoặc `valid_lesson_ids` do build truyền), `applicationType` enum và required fields theo loại; exact `product.outOfScope`. Trả list message rõ ràng (kèm id vi phạm).
- [ ] **Step 4 — chạy, xác nhận PASS.**
- [ ] **Step 5 — commit** (`test: add spendwise project validator`).

## 9.3 Task P0-3 — Build integration (`tools/build_site.py`) (implemented bằng TDD)

**Files:**
- Implemented: `tools/build_site.py` (`--project`; load+validate; `model["project"]=...`; cross-check lessonMap⊆lessons)
- Tests: `tests/test_build_site.py`

> Các bước RED/GREEN dưới đây là implementation record của P0-3, không phải công việc còn pending.

- [ ] **Step 1 — test:** `tests/test_build_site.py` **dùng `unittest`, KHÔNG có pytest fixture** — có `class PublicationModelTests(unittest.TestCase)` với `setUpClass` build sẵn `cls.model = build_publication_model(...)`. Thêm **method** vào class đó (không viết hàm `def test_x(built_model)` — fixture `built_model`/`built_html` KHÔNG tồn tại):
```python
def test_model_has_project_and_lessonmap_subset(self):
    proj = self.model["project"]
    self.assertEqual(proj["schemaVersion"], 1)
    self.assertIn("releases", proj)
    lesson_ids = {l["id"] for l in self.model["lessons"]}
    self.assertTrue(set(proj["lessonMap"]).issubset(lesson_ids))

def test_still_single_course_data_marker(self):
    # embed vào template rồi đếm marker (giống đường build thật)
    template = pathlib.Path("index.template.html").read_text("utf-8")
    html = embed_course_data(template, self.model)   # tên hàm/kiểu tham số khớp module
    self.assertEqual(html.count('id="course-data"'), 1)
```
> Nếu `setUpClass` hiện chưa truyền `--project`/project path, cập nhật nó để `build_publication_model` nhận project (giữ default trỏ `content/spendwise-project.json`). Import `embed_course_data`, `pathlib` ở đầu file nếu chưa có.
- [ ] **Step 2 — chạy, FAIL** (chưa có `project`).
- [ ] **Step 3 — implement:** thêm arg `--project` (default `content/spendwise-project.json`); trong `build_publication_model()` load JSON, gọi `validate_project(project, valid_lesson_ids=lesson_ids)`, raise `ValueError` nếu có lỗi; `model["project"]=project`. KHÔNG đổi `LESSON_FIELDS`, KHÔNG đổi `embed_course_data()`.
- [ ] **Step 4 — chạy pytest + build thật** (`python tools/build_site.py`) → PASS, `index.html` regenerated.
- [ ] **Step 5 — commit** (`feat: embed spendwise project data into build model`).

## 9.4 Task P0-4 — State migration + project progress core (implemented bằng TDD, JS)

**Files:**
- Implemented: `index.template.html` (CourseCore: `STATE_VERSION=2`, `defaultState`, `sanitizeState` arg 5, `calculateReleaseProgress`/`calculateFeatureProgress`; IIFE: `toggleBuildTask`, `BUILD_TASK_IDS`, import v1&v2)
- Tests: `tests/site_core.test.js`

> Các bước RED/GREEN dưới đây là implementation record của P0-4, không phải công việc còn pending.

- [ ] **Step 1 — test:** thêm vào `site_core.test.js`:
```js
test("sanitizeState migrates v1 (no projectProgress) keeping completed", () => {
  const s = CourseCore.sanitizeState(
    {version:1, completed:["day-01"]},
    new Set(["day-01"]), new Set(), new Set(), new Set(["task-a"]));
  assert.equal(s.version, 2);
  assert.deepEqual(s.completed, ["day-01"]);
  assert.deepEqual(s.projectProgress.buildTasks, []);
});
test("sanitizeState drops unknown build task ids", () => {
  const s = CourseCore.sanitizeState(
    {version:2, projectProgress:{buildTasks:["task-a","ghost"]}},
    new Set(), new Set(), new Set(), new Set(["task-a"]));
  assert.deepEqual(s.projectProgress.buildTasks, ["task-a"]);
});
test("calculateReleaseProgress counts only required tasks", () => {
  const buildTasks = [
    {id:"t1",releaseId:"r",required:true},{id:"t2",releaseId:"r",required:true},
    {id:"t3",releaseId:"r",required:false}];
  assert.deepEqual(CourseCore.calculateReleaseProgress(buildTasks,["t1","t3"],"r"),
                   {completed:1,total:2,percent:50});
});
```
- [ ] **Step 2 — chạy `node --test tests/site_core.test.js` → FAIL.** (Lưu ý: `site_core.test.js` đọc **`index.html` đã build**, không đọc `index.template.html` — bản build cũ chưa có hàm mới nên test đỏ đúng như mong đợi.)
- [ ] **Step 3 — implement** trong block `COURSE_CORE` (trong `index.template.html`): bump version; `defaultState` thêm `projectProgress:{buildTasks:[]}`; `sanitizeState` thêm tham số 5 + lọc buildTasks (default `new Set()` — §6.2); thêm hai hàm progress (đếm task có `required !== false`); export chúng trong object freeze. IIFE: `toggleBuildTask`, dựng `BUILD_TASK_IDS`, cập nhật **cả hai** call-site `sanitizeState` truyền đủ 5 tham số (`loadState` :1303 **và** `importProgressText` :1579 — §6.4), import chấp nhận schemaVersion∈{1,2}, `APP_SCHEMA.schemaVersion=2`.
- [ ] **Step 4 — BUILD trước, rồi test:** `python tools/build_site.py` (regenerate `index.html` từ template) **→ sau đó** `node --test tests/site_core.test.js` → PASS. **Bắt buộc build trước** vì test đọc `index.html` đã build; quên build = test vẫn chạy trên code cũ (đỏ giả hoặc xanh giả).
- [ ] **Step 5 — commit** (`feat: add independent project progress state (STATE_VERSION 2)`).

## 9.5 Task P0-5 — Dashboard tích hợp widget Spendwise (null-safe)

**Files:**
- Modify: `index.template.html` (`renderDashboard`, ~1445–1536 — *thêm* block project, không xóa block course)

**Steps:**
- [ ] Trong `renderDashboard`, sau phần course hiện có, thêm section “Spendwise” chỉ khi `projectData`:
  - Current Spendwise Release + Project Progress (dùng `calculateReleaseProgress`), reuse progress-meter markup hiện có.
  - Current Milestone: milestone chứa current release trong `releaseIds` (ẩn nếu không có).
  - Today's Project Impact: từ `projectByLessonId.get(currentLessonId)?.application` (ẩn nếu theory/không map).
  - Next Build Step: buildTask `required:true` **đầu tiên chưa done** theo thứ tự `release.buildTaskIds` của current release (KHÔNG có field `order`); ẩn nếu rỗng.
- [ ] Dùng `el(tag,class,text)` (textContent-safe) cho mọi text động; link release/roadmap là `<a href=”#/…”>`.
- [ ] Không đổi các widget course cũ (Current Lesson / Learning Progress / Next Learning Step giữ nguyên).
- [ ] Build (`python tools/build_site.py`) **trước**, rồi `node --test` + mở `?selftest=1` thủ công xem dashboard không vỡ.
- [ ] **Commit** (`feat: add spendwise widgets to dashboard`).

## 9.6 Task P0-6 — Lesson Project Context / Application (tầng compose, KHÔNG đụng sections)

**Files:**
- Modify: `index.template.html` (`renderFullLesson` compose ~2210–2222; thêm `renderProjectContext`/`renderProjectApplication`)

**Steps:**
- [ ] Thêm 2 render nhỏ đọc `projectByLessonId.get(lesson.id)`:
  - `renderProjectContext(container, lessonId)` → chèn **sau** `renderLessonHeader`, **trước** `renderSections`. Hiện `context` (+ badge loại direct/future/theory). Không có map → **không chèn gì** (early return).
  - `renderProjectApplication(container, lessonId)` → chèn ở **CUỐI lesson: sau `renderPractices` + `renderAssignments`, TRƯỚC `renderReferences`** (master §13/§15: "Project Application" là bước áp dụng ở cuối bài, sau khi đã học lý thuyết + luyện tập). Hiện `application`, `featureIds`→tên feature, link release; nếu có `buildTaskIds` hiện checklist build task với `toggleBuildTask` (event gắn bằng `addEventListener`, KHÔNG inline onclick).
- [ ] **Bất biến:** không sửa `renderSections` và dữ liệu `sections` (theory nguyên vẹn). Thứ tự compose mới: header → **projectContext?** → sections → practices → assignments → **projectApplication?** → references → nav.
- [ ] Build + mở một lesson `direct` (day-20), một `theory` (day-02), một lesson **không** có entry (day-39-64) → cả ba render đúng (graceful).
- [ ] **Commit** (`feat: render project context/application in lessons`).

## 9.7 Task P0-7 — Project Overview + Roadmap views + Nav (tối thiểu)

**Files:**
- Modify: `index.template.html` (`parseRoute`, `routeRender`, `renderApp` header nav; thêm `renderProjectOverview`, `renderRoadmap`, `renderReleaseDetail` tối thiểu)
- Test: `tests/site_core.test.js` (parseRoute cases mới)

**Steps:**
- [ ] **Test trước:** thêm case `parseRoute("#/project")→{view:"project"}`, `parseRoute("#/release/v0-1")→{view:"release",releaseId:"v0-1"}`, `parseRoute("#/roadmap")`, `#/map`, `#/architecture`; xác nhận `#/dashboard`, `#/lesson/day-01`, `#/resources` **không đổi**. Chạy → FAIL.
- [ ] Mở rộng `parseRoute` (§8.2) → node test PASS.
- [ ] `renderProjectOverview`: product summary + current release + **Current Milestone** (milestone chứa current release) + link roadmap. `renderRoadmap`: list 10 release (version, title, status badge, release progress bar), mỗi cái link `#/release/<id>`. `renderReleaseDetail(routeView,id)`: releaseById → problem/goal/features/acceptance/build tasks (+toggle)/architecture stage; id sai → not-found panel + link roadmap.
- [ ] Thêm nav vào `renderApp` header (§8.3): **P0 chỉ 4 link** Học/Dự án/Lộ trình/Tài nguyên, `<a href=”#/…” data-view=”…”>`, đánh dấu active bằng **helper mới `updateNavActive(view)` gọi từ `routeRender`** (KHÔNG tái dùng `setAriaCurrent` — hàm đó chỉ cho `.lesson-link`). **KHÔNG** thêm link Bản đồ/Kiến trúc ở P0 (view còn stub → hoãn sang P1 để tránh dead-end). Nhánh `map`/`architecture` trong `routeRender` render stub “đang cập nhật”.
- [ ] Build + smoke test (`python tools/ui_smoke_test.py`) → PASS N/N (N≥13) desktop+mobile + static checks.
- [ ] **Commit** (`feat: add project overview/roadmap views and primary nav`).

---

# 10. P1 Implementation Plan (Project Workspace — sau khi P0 xanh)

Điều kiện tiên quyết: toàn bộ P0 pass (data+state+dashboard+lesson+overview/roadmap+nav). P1 làm dày các view và chi tiết, vẫn data-first, vẫn hai hệ tiến độ độc lập.

- [ ] **P1-1 — Release Detail đầy đủ:** mở rộng `renderReleaseDetail` — hiển thị đủ `features` (mô tả + domainEntities), `buildTasks` nhóm theo feature với problem/goal/constraints/acceptanceCriteria (accordion tái dùng `collapsedUnits`-style), `learningDependencies`, link tới các lesson `relevantLessonIds`, và `architectureStage` (diagram `<pre>`). Progress bar release + per-feature. Test render với release có/không build task.
- [ ] **P1-2 — Course ↔ Project Map (`renderCourseProjectMap`):** bảng/nhóm 40 lesson → (loại direct/future/theory, release, feature). Bộ lọc theo loại + theo release (client-side, không thêm dep). Mỗi hàng link tới lesson và tới release. Lesson không map → nhóm “Theory / chưa map” (không lỗi). Đọc `projectByLessonId` + `lessonsById` (đã có).
- [ ] **P1-3 — Architecture Evolution (`renderArchitecture`):** liệt kê `architectureStages` theo `order` release; mỗi stage: title, layers, diagram `<pre>`, `changesFromPrev`, `rationale`; đánh dấu stage của current release. Điều hướng prev/next stage.
- [ ] **P1-4 — Domain Overview:** trong Project Overview thêm khối domain (danh sách entity **suy ra từ hợp `features[].domainEntities`** — KHÔNG dùng `product.capabilities`, field đó đã bỏ ở §5.1), out-of-scope (`product.outOfScope`). Thuần data, không hard-code.
- [ ] **P1-5 — Build Tasks workspace:** trang/section tổng hợp mọi buildTask của current release với toggle + % ; đồng bộ hai chiều hiển thị với checklist trong lesson (cùng `state.projectProgress.buildTasks`, cùng `toggleBuildTask`).
- [ ] **P1-6 — Roadmap giàu hơn:** thêm milestones (dải mốc), trạng thái released/building/planned rõ ràng, progress mỗi release, filter “chỉ current”.
- [ ] **P1-7 — Before/After architecture:** ở Release Detail thêm so sánh `changesFromPrev` (stage n-1 → n) dạng hai cột.

Mỗi P1 task: TDD cho phần có logic thuần (thêm vào `site_core.test.js` nếu có hàm mới trong CourseCore) → build → `ui_smoke_test.py` xanh → commit riêng.

---

# 11. P2 Implementation Plan (UX Polish — sau P1)

- [ ] **P2-1 — Responsive & visual polish:** nav collapse mobile mượt, spacing/typography cho các view mới; kiểm 390×844 và 1440×1000 (đúng viewport smoke test).
- [ ] **P2-2 — Micro-interactions:** transition tôn trọng `prefers-reduced-motion` (đã có hook); toast khi tick build task; progress bar animate.
- [ ] **P2-3 — Filters & search mở rộng:** cân nhắc cho phép search chạm project (feature/release title) — **tùy chọn**, nếu làm phải giữ `searchLessons` cũ nguyên si (thêm hàm mới, không sửa hành vi cũ để không regress test).
- [ ] **P2-4 — Progress visualization tốt hơn:** overview kép course% vs project% (hai vòng/thanh tách biệt, nhấn mạnh tính độc lập), timeline release.
- [ ] **P2-5 — Empty/te states:** trau chuốt empty-state khi `projectData==null` hoặc lesson theory (thông điệp rõ, không giống lỗi).

P2 không được phá bất biến P0/P1: 40/15/12-24-4, hai hệ độc lập, external_dependencies=0, smoke test ≥13/13.

---

# 12. Migration Strategy

**Schema data (build model):** thêm key `project` là *additive* — model cũ vẫn hợp lệ. Không đổi `schemaVersion` của course model (giữ 1) vì cấu trúc course không đổi; project có `schemaVersion` riêng (1). Client dùng `courseData.project || null` ⇒ nếu chạy `index.html` build cũ (không có project), app vẫn chạy, view project hiện empty-state.

**localStorage state (v1 → v2):**
- Migration = **rebuild-from-default**: `sanitizeState` luôn bắt đầu từ `defaultState()` (đã có `projectProgress`) rồi copy các key hợp lệ từ input. State v1 cũ trong máy người dùng → `completed/lastLessonId/practice/collapsedUnits/theme` được giữ; `projectProgress` nhận default `{buildTasks:[]}`; `version` set = 2. **Không mất tiến độ học.**
- Không cần script migration ngoài; không cần đọc `version` để rẽ nhánh (default-then-copy đã idempotent). Nếu sau này cần rẽ theo version, chèn trước bước copy — nhưng P0 không cần.
- **Downgrade là LOSSY (không an toàn hoàn toàn) — nêu rõ để không hứa sai:** nếu người dùng mở lại **bản build cũ** sau khi đã có state v2, code cũ đọc state — `completed`/`lastLessonId`/… vẫn đúng, nhưng `sanitizeState` cũ (4 tham số, `defaultState` cũ **không** có `projectProgress`) dựng lại state từ default rồi chỉ copy các key nó biết ⇒ **lần `saveState()` kế tiếp của bản cũ sẽ GHI ĐÈ localStorage và xóa mất `projectProgress`**. Vì app tự `saveState` khá thường xuyên (toggle lesson, đổi theme, đánh dấu…), thực tế `projectProgress` sẽ mất ngay trong phiên dùng bản cũ. `completed` (course) không mất. Đây là rủi ro **chấp nhận được** (downgrade là kịch bản hiếm, và ta không có cơ chế chống downgrade cho một site tĩnh) — nhưng KHÔNG được mô tả là "an toàn". Course progress luôn được bảo toàn; project progress có thể mất khi hạ cấp.

# 13. Backward Compatibility Strategy

| Bề mặt | Rủi ro | Biện pháp |
|---|---|---|
| Course data model | thêm `project` phá parse cũ | additive; client null-safe `courseData.project||null` |
| localStorage v1 | mất `completed` | default-then-copy giữ nguyên completed (§12); có test |
| Export file cũ (schemaVersion 1) | import từ chối | `importProgressText` chấp nhận `{1,2}`; thiếu `projectProgress`→default |
| Export file mới (2) mở ở app cũ | app cũ không hiểu | ban đầu key lạ bị bỏ qua, nhưng lần save kế tiếp của app cũ có thể ghi đè và làm mất `projectProgress` (§12); downgrade là lossy |
| Route cũ (`dashboard/lesson/resources`) | thêm route phá cũ | chỉ *thêm* case; regex `lesson/(.+)` không đổi; test giữ nguyên |
| `searchLessons` | regress | không sửa; nếu mở rộng ở P2 thì thêm hàm mới |
| Smoke-test hooks/labels | thiếu nhãn cũ | nav chỉ thêm; giữ toàn bộ label trong `STATIC_REQUIREMENTS`/runtime_labels |
| Lesson JSON (closed schema) | validator từ chối | KHÔNG sửa lesson JSON; mapping ở file riêng |
| `LESSON_FIELDS` | rớt field | KHÔNG đụng; project data đi qua `model["project"]` |
| Self-test count | rớt PASS | chỉ *thêm* assertion (total tăng, passed==total vẫn xanh); không xóa assertion cũ |

# 14. Validation / Test Strategy

**Bậc test (đều phải xanh trước khi commit `index.html`):**

1. **Python — data & build:**
   - `tests/test_validate_project.py` (mới): file thật hợp lệ; phát hiện dangling ref, key lessonMap sai, top-key lạ, order sai, id trùng, id không URL-safe, direct thiếu field.
   - `tests/test_build_site.py` (mở rộng): `model["project"]` tồn tại + `schemaVersion==1`; `lessonMap ⊆ lesson ids`; **vẫn đúng một** marker `#course-data`; 40/15/12-24-4 và no-script-injection giữ nguyên.
   - Chạy: `python -m pytest -q`.
2. **JS — CourseCore:** `tests/site_core.test.js` (mở rộng): `parseRoute` route mới + route cũ không đổi; `sanitizeState` migration v1→v2 giữ completed + drop task lạ (arg thứ 5); `calculateReleaseProgress`/`calculateFeatureProgress` chỉ đếm `required`. Chạy: `node --test tests/site_core.test.js`.
3. **In-browser self-test (`?selftest=1`):** thêm assertion **mới** (không xóa cũ) — VD: `courseData.project` tồn tại; `projectProgress` có trong state sau load; toggle build task không đổi `completed`. Cổng của smoke test yêu cầu ngưỡng sàn và `passed == total`; suite template hiện có các kiểm tra project đến mục #32. Chỉ *thêm* assertion nên `total` tăng, luôn phải giữ `passed == total`. Assertion #1 (`lessons.length===40`) giữ nguyên.
4. **Headless smoke (`tools/ui_smoke_test.py`):** PASS desktop(1440×1000)+mobile(390×844), `PASS N/N` với N≥13; static checks: `lang="vi"`, viewport, skip-link, `#main-content`, aria-live, prefers-reduced-motion, focus-visible, **không** inline handler trong markup, **không** duplicate static IDs, **không** external dep / http:// subresource. Nav mới phải tuân (dùng `<a>`, gắn event bằng `addEventListener`).
5. **Rebuild + commit artifact:** sau khi mọi test xanh → `python tools/build_site.py` → `git add index.html` cùng các file nguồn → commit. `index.html` là artifact nhưng được version ⇒ **bắt buộc** commit lại sau thay đổi.

**Thứ tự chạy khuyến nghị mỗi task:** `pytest -q` → **`python tools/build_site.py` (build TRƯỚC)** → `node --test tests/site_core.test.js` → `python tools/ui_smoke_test.py` (smoke) → `git diff --stat index.html`.
- **Vì sao build trước `node --test`:** `site_core.test.js` đọc **`index.html` đã build** (không đọc `index.template.html`); chạy `node --test` trước khi rebuild = test chạy trên code cũ (đỏ giả hoặc, tệ hơn, xanh giả sau khi đã sửa template mà chưa build).
- **`git diff --stat index.html`** sau build phải cho thấy diff **chỉ tập trung ở vùng marker `#course-data`** (payload JSON). Nếu thấy `index.html` đổi ở vùng markup/CSS/JS mà bạn không cố ý sửa template tương ứng ⇒ dấu hiệu ai đó đã sửa tay artifact — dừng và điều tra.

---

# 15. Risks (ánh xạ đúng danh sách rủi ro người dùng nêu + phát hiện audit)

| # | Rủi ro | Phát hiện / mức | Phòng ngừa |
|---|---|---|---|
| R1 | **Nhầm source of truth** | `index.html` là artifact, `index.template.html` là nguồn (build_site.py 416–420) | §3 nêu rõ; mọi task “Modify” chỉ trỏ template; không bao giờ Edit `index.html` tay |
| R2 | **Sửa nhầm file generated** | cao nếu agent mở `index.html` | Chỉ sửa template; sau build mới `git add index.html`; review diff template vs artifact |
| R3 | **Schema migration** | state v1→v2 | default-then-copy trong `sanitizeState` (§12); có test migration |
| R4 | **localStorage không tương thích** | key `java-spring-course` giữ nguyên | không đổi `STORAGE_KEY`; thêm key con `projectProgress` additive |
| R5 | **Mất tiến độ học cũ** | `completed[]` | test khẳng định completed giữ nguyên sau migrate; import v1 vẫn nhận |
| R6 | **Duplicate dữ liệu project** | nếu copy release/feature vào nhiều nơi | một nguồn `spendwise-project.json`; reference bằng ID; validator chặn dangling |
| R7 | **Hard-code nội dung project trong render** | dễ xảy ra khi vội | cấm; render đọc `courseData.project`; DoD kiểm không có literal Spendwise trong render |
| R8 | **Renderer coupling** | `renderFullLesson` compose cứng | chèn project ở tầng compose, early-return nếu không map; không sửa `renderSections` |
| R9 | **Route collision** | thêm route | prefix mới (project/roadmap/release/map/architecture) khác route cũ; regex `lesson/(.+)` giữ nguyên; test route cũ |
| R10 | **Search regression** | `searchLessons` | không sửa ở P0/P1; mở rộng (nếu có) là hàm mới ở P2 |
| R11 | **Mobile regression** | nav mới | smoke test 390×844; nav collapse; `<a>` + addEventListener |
| R12 | **Project progress bị buộc vào lesson progress** | bất biến cốt lõi | hai handler tách biệt (delegated `data-action="toggle-completion"` cho course :2542-2552 vs `toggleBuildTask` cho project); test toggle build task không đụng `completed`; status release là authored |
| R13 | **Syllabus bị đổi ngoài ý muốn** | 40/15/12-24-4 | không đụng lesson-index/catalog/lessons; test build_site giữ counts; validator lessonMap ⊆ lesson ids (không tạo lesson mới) |
| R14 | **Vỡ ràng buộc “đúng một marker”** | `embed_course_data` raise nếu ≠1 | không thêm marker; project đi chung marker; test đếm marker==1 |
| R15 | **external_dependencies ≠ 0** | smoke test cấm | không thêm CDN/font/script ngoài; tất cả inline |
| R16 | **Rớt PASS self-test count** | smoke yêu cầu passed==total, total≥13 | chỉ thêm assertion, không xóa; giữ #1 lessons===40 |
| R17 | **Lesson không map gây lỗi render** | graceful | early-return; test render lesson không có entry |
| R18 | **Data project hỏng lọt vào build** | fail-fast | `validate_project` raise trong build → build dừng, không sinh `index.html` hỏng |

---

# 16. Exact files to modify per phase

## 16.0 FILE CHANGE MAP (anchor đã verify trong `index.template.html`)

> Mọi số dòng là dòng **`index.template.html`** (nguồn), KHÔNG phải `index.html`. `index.html` chỉ *regenerate*.

| Phase | File / vị trí | Thay đổi | Lý do | Rủi ro |
|---|---|---|---|---|
| P0-1 | `content/spendwise-project.json` | **Author/maintain** | Nguồn dữ liệu Spendwise (data-first) | Thấp — artifact riêng |
| P0-2 | `tools/validate_project.py` | **Implemented/maintain** | Referential integrity, fail-fast | Thấp — artifact riêng |
| P0-2 | `tests/test_validate_project.py` | **Implemented/maintain** | Test validator (TDD) | Thấp |
| P0-3 | `tools/build_site.py` `build_publication_model()` | **Implemented:** arg `--project`, load+validate, `model["project"]=…`, cross-check lessonMap⊆lessons | Nhúng project vào model | Trung — `embed_course_data`/`LESSON_FIELDS` không đổi |
| P0-3 | `tests/test_build_site.py` `PublicationModelTests` | **Implemented:** project + marker coverage | Assert project + đúng 1 marker | Thấp |
| P0-4 | `index.template.html` CourseCore (1091–1252) | **Implemented:** `STATE_VERSION=2`; `defaultState`+`projectProgress`; `sanitizeState`+arg5; `calculateReleaseProgress`/`calculateFeatureProgress`; exports | State độc lập + progress derived | Trung — có test node:vm |
| P0-4 | `index.template.html` IIFE | **Implemented:** project maps; `toggleBuildTask`; hai call-site `sanitizeState` truyền `BUILD_TASK_IDS`; import `{1,2}`; `APP_SCHEMA.schemaVersion=2` | Wiring runtime | Trung |
| P0-4/7 | `index.template.html` self-test block | P0-4 project-state assertions đã có; P0-7 route/UI assertions còn pending | Giữ `passed==total` | Thấp |
| P0-5 | `index.template.html` `renderDashboard` (~1445–1536) | +block Spendwise null-safe (release/milestone/impact/next build) | Trả 4 câu hỏi + impact | Trung — không xóa widget course |
| P0-6 | `index.template.html` `renderFullLesson` compose (2210–2222) | chèn `renderProjectContext` (sau header, trước sections) + `renderProjectApplication` (sau assignments, **trước** references) | Context/Application layer | Trung — KHÔNG đụng `renderSections`/`sections` |
| P0-7 | `index.template.html` `parseRoute` (1106–1113) | +case project/roadmap/release/map/architecture (biến `raw`) | Route mới | Thấp — regex `lesson/(.+)` không đổi |
| P0-7 | `index.template.html` `routeRender` (1414–1424, `#route-view`) | +nhánh `else if` view mới; gọi `updateNavActive(view)` | Dispatch view mới | Thấp — không đụng nhánh cũ |
| P0-7 | `index.template.html` `renderApp` header (~2555) | +nav 4 link (`data-view`, `<a>`); helper mới `updateNavActive` | Nav + `#resources` reachable | Trung — giữ `#main-content`/skip-link/aria-live |
| P0-7 | `index.template.html` | +`renderProjectOverview`/`renderRoadmap`/`renderReleaseDetail` (tối thiểu); `map`/`architecture`=stub | View project tối thiểu | Thấp |
| P0-7 | `tests/site_core.test.js` | +parseRoute cases, sanitizeState migration, progress helpers | TDD core (đọc `index.html` đã build) | Thấp |
| P0 (mọi task chạm template) | `index.html` | **Regenerate** qua `python tools/build_site.py` + commit | Artifact versioned | **Cao nếu sửa tay** — chỉ build |
| P1 | `index.template.html` | `renderReleaseDetail` đầy đủ, `renderCourseProjectMap`, `renderArchitecture`, nav +Bản đồ/Kiến trúc, domain overview, build-tasks workspace | Làm dày view | Trung |
| P1 | `content/spendwise-project.json` | (tùy) bổ sung buildTasks/stages | Nội dung sâu hơn | Thấp — qua validator |
| P2 | `index.template.html` `<style id="app-styles">` + render polish | CSS/UX polish; nếu chạm search → hàm mới | Polish | Trung — tránh regress core |

**P0 status:**
- **Implemented P0-1:** `content/spendwise-project.json` — canonical Spendwise data.
- **Implemented P0-2:** `tools/validate_project.py` + `tests/test_validate_project.py` — closed-schema/referential-integrity validation.
- **Implemented P0-3:** `tools/build_site.py` + `tests/test_build_site.py` — project load/validate/embed through the single marker.
- **Implemented P0-4:** `index.template.html` CourseCore/state wiring + `tests/site_core.test.js` — `STATE_VERSION=2`, independent `projectProgress`, migration/import compatibility, project maps/toggle, derived progress helpers, self-test assertions.
- **Pending P0-5:** `renderDashboard` — Spendwise widgets.
- **Pending P0-6:** `renderFullLesson` compose + `renderProjectContext`/`renderProjectApplication`.
- **Pending P0-7:** `parseRoute`, `routeRender`, header nav, project/roadmap/release views, route/UI tests and self-test additions.
- `index.html` is regenerated by the build after source/data changes; commit only when explicitly requested.

**P1:** chỉ `index.template.html` (mở rộng `renderReleaseDetail`, thêm `renderCourseProjectMap`, `renderArchitecture`, domain overview, build-tasks workspace) + `tests/site_core.test.js` (nếu thêm hàm CourseCore) + có thể bổ sung `content/spendwise-project.json` (thêm buildTasks/stages) + regenerate `index.html`. **Không** đụng file course/catalog/lessons.

**P2:** `index.template.html` (CSS `<style id="app-styles">` + render polish) + regenerate `index.html`. Tránh đụng logic core; nếu chạm search thì thêm hàm mới + test mới.

**Tuyệt đối KHÔNG sửa (mọi phase):** `content/lessons/*.json`, `content/lesson-index.json`, `content/lesson-schema.json`, `course-catalog.json`, `content/source-*`, `tools/course_model.py`/`extract_catalog.py` (trừ khi có lý do độc lập với task này). `index.html` chỉ được *regenerate*, không sửa tay.

# 17. Definition of Done — P0

- [ ] `content/spendwise-project.json` tồn tại, hợp lệ; `lessonMap` có đúng **38 entry day-01..day-38**, còn `day-39-64`/`day-65-66` chủ ý unmapped; 10 release V0.1→V1.0 có status authored và `buildTaskIds`; features/architectureStages/buildTasks/milestones có mặt; mọi ID reference resolve (validator xanh).
- [ ] `tools/validate_project.py` + `tests/test_validate_project.py`: `python -m pytest -q` xanh.
- [ ] `tools/build_site.py` gắn `model["project"]`; `tests/test_build_site.py` xanh; build vẫn **đúng một** marker `#course-data`; 40/15/12-24-4 giữ nguyên; `LESSON_FIELDS` không đổi.
- [ ] State: `STATE_VERSION=2`, `projectProgress.buildTasks[]` độc lập; `node --test tests/site_core.test.js` xanh gồm test migration (giữ `completed`), drop task lạ, progress chỉ đếm `required`.
- [ ] Hai hệ tiến độ **độc lập**: tick lesson KHÔNG đổi build tasks; tick build task KHÔNG đổi completed (có test).
- [ ] Import chấp nhận export cũ (schemaVersion 1) và mới (2); export mới bao gồm `projectProgress`.
- [ ] Dashboard trả lời 4 câu (đang học gì / học tới đâu / đang xây release nào / xây tới đâu) + Today's Project Impact + Next Learning/Build Step; null-safe khi không có project/không map.
- [ ] Lesson `direct` (vd day-20) hiện Project Context (đầu bài, sau header) + Project Application (**cuối bài: sau practices/assignments, trước references** — master §13/§15) + build-task checklist; lesson `theory` (vd canonical day-02) và lesson không map (vd day-39-64) render KHÔNG lỗi (graceful); `sections` theory không đổi.
- [ ] **Reset semantics đúng & trung thực:** nút "Đặt lại toàn bộ tiến độ" (`state = CourseCore.defaultState()`, :1645-1654) xóa **cả** course `completed[]` **lẫn** `projectProgress.buildTasks[]`; trong P0 UI, cập nhật text confirm (:1646) để nêu rõ có xóa "tiến độ build project". Data Contract Alignment không sửa UI text này. KHÔNG tách thành hai nút reset ở P0.
- [ ] Route mới `#/project` `#/roadmap` `#/release/<id>` hoạt động; route cũ không đổi; nav header xuất hiện với `aria-current`, `#/resources` giờ reachable.
- [ ] Không hard-code nội dung Spendwise trong render (chỉ đọc `courseData.project`).
- [ ] `python tools/ui_smoke_test.py`: PASS desktop+mobile, `PASS N/N` (N≥13, passed==total); static a11y/hygiene xanh; external_dependencies=0; không inline handler trong markup; không duplicate static ID.
- [ ] `index.html` được regenerate và commit cùng nguồn; không sửa tay artifact.

---

*Hết implementation plan. Thực thi tuần tự P0 → P1 → P2; mỗi task theo TDD (test đỏ → code → test xanh → build → smoke → commit). Master plan là source of truth sản phẩm; plan này là source of truth cách làm.*

---

# Original Review Gate (historical; superseded by Data Contract Alignment)

*Cổng này được viết trước khi implementation bắt đầu. P0-1..P0-4 đã được implement sau đó; status vận hành hiện tại nằm ở đầu tài liệu và §9/§16. Các quyết định kỹ thuật bên dưới vẫn là record/normative constraints, nhưng verdict pre-implementation cũ không phải readiness verdict cho P0-5.*

## Historical Verdict

**SUPERSEDED — P0-1..P0-4 IMPLEMENTED; DATA CONTRACT ALIGNMENT REQUIRED BEFORE P0-5**

Plan giữ master plan làm product-scope source of truth: Learning + Project đều first-class, hai hệ tiến độ độc lập, theory vẫn là nội dung chính, dữ liệu không hard-code trong renderer, và thứ tự DATA→STATE→DASHBOARD/LESSON→UI được giữ. Readiness cho P0-5 chỉ được kết luận sau fresh full validation của Data Contract Alignment checkpoint.

## Critical Decisions

- **CD-1 — Source of truth (đã sửa cho ĐÚNG):** `index.html` là **build artifact giữ cấu trúc 3199 dòng của template**; build chỉ thay `textContent` của **đúng một** marker `<script id="course-data">`. Bác bỏ khẳng định sai của vòng review rằng "index.html là một dòng ~876KB". Vẫn giữ 4 nhãn bắt buộc (SOURCE OF TRUTH / GENERATED OUTPUT / FILES SAFE TO EDIT / FILES SHOULD NOT BE EDITED DIRECTLY) ở §3, nội dung factual. Không bao giờ để coding agent sửa tay `index.html`.
- **CD-2 — Dữ liệu ở artifact riêng:** toàn bộ Spendwise sống trong `content/spendwise-project.json` → `model["project"]`; **không** đụng lesson JSON (schema *closed*), không đụng `LESSON_FIELDS`. Mapping keyed-by-lesson-id, tham chiếu bằng ID, lesson không map render graceful.
- **CD-3 — Hai hệ tiến độ độc lập:** course = `state.completed[]`; project = `state.projectProgress.buildTasks[]`. `STATE_VERSION` 1→2 bằng rebuild-from-default (không mất `completed`); `APP_SCHEMA.schemaVersion` 1→2. Bất biến = **không đồng bộ theo toggle** (không phải "reset một hệ chừa hệ kia").
- **CD-4 — Reset semantics:** nút "Đặt lại toàn bộ" cố ý xóa **cả hai** track. Text confirm còn thiếu nhắc tới project progress và là follow-up trong P0 UI; Data Contract Alignment không sửa UI. **Không** tách hai nút reset ở P0.
- **CD-5 — Anchor code đúng thực tế:** course toggle là delegated `data-action="toggle-completion"` (:2542-2552), **không** có hàm `toggleLessonComplete`; `nextLessonId(lessons, currentId, delta)`; `routeRender` là `if/else if` trên `route.view` vào `#route-view` (không `switch`/`main`); `parseRoute` dùng biến `raw`; đánh dấu nav active bằng helper **mới** `updateNavActive(view)` (vì `setAriaCurrent` chỉ cho `.lesson-link`).
- **CD-6 — Vị trí Project Application:** render ở **CUỐI lesson** (sau practices/assignments, trước references) theo master §13/§15 — không phải ngay sau sections. Project Context vẫn ở đầu (sau header).
- **CD-7 — Release status là AUTHORED, mặc định `planned`:** chỉ `building` cho release đang xây thật, `released` chỉ khi có artifact verify được (master §20). Không suy status từ course progress. Không đánh `released` cho V0.1–V0.2 chỉ vì "coi domain đã xong".
- **CD-8 — Mapping theo NỘI DUNG THẬT:** dùng tiêu đề verbatim từ `lesson-index.json`. Abstract dạy ở **day-05**; day-06/15/21/27 là **Assignment**; Day 10 Stream map trực tiếp V0.2 statistics; day-25 map V0.9 với `feat-cache`/`feat-async-import`/`feat-scheduler`; day-26 map V0.8 với `feat-import` + `feat-exchange-rate`; `day-39-64` và `day-65-66` chủ ý **unmapped** vì không thuộc Spendwise.
- **CD-9 — Bắt buộc vs tùy chọn:** optimistic locking `@Version` (day-20) và các hardening/portfolio là `required:false` (master §42/§45); chỉ `required:true` tính vào % release (master §24). App bắt buộc của day-20 = @Transactional atomicity + rollback.
- **CD-10 — Validator chặt (fail-fast):** closed schema **theo từng loại object**; release↔task cross-check **FAIL** (không chỉ cảnh báo); lessonMap entry↔task **FAIL**; `outOfScope` liệt kê đầy đủ master §9; id URL-safe. Build cross-check thêm `lessonMap ⊆ model["lessons"]` (defense-in-depth). Data hỏng → build dừng, không sinh `index.html` hỏng.
- **CD-11 — Thứ tự thực thi & test:** DATA (P0-1..3) → STATE (P0-4) → DASHBOARD/LESSON (P0-5,6) → UI tối thiểu (P0-7); CSS/polish hoãn tới P2 (không "CSS trước"). **Build phải chạy TRƯỚC `node --test`** vì `site_core.test.js` đọc `index.html` đã build. Nav P0 chỉ 4 link; Bản đồ/Kiến trúc (stub) hoãn P1.

## Risks Accepted

- **RA-1 — Downgrade là LOSSY cho project progress:** nếu mở lại bản build cũ sau khi có state v2, `saveState()` của bản cũ sẽ ghi đè và **mất `projectProgress`** (course `completed` được giữ). Chấp nhận: downgrade hiếm, site tĩnh không có cơ chế chống downgrade. Không mô tả là "an toàn".
- **RA-2 — Mapping đã chốt nhưng vẫn cần bảo trì có kiểm chứng:** §7.1 phản ánh canonical artifact hiện tại. Nếu lesson/master roadmap thay đổi, sửa theo quy trình §7.2 và validator; không reclassify ad hoc trong UI task.
- **RA-3 — Feature registry đã chốt:** artifact hiện có 25 feature, gồm `feat-statistics`/`feat-cache`/`feat-exchange-rate`; không còn quyết định proxy đang treo. Rủi ro còn lại là dangling ref và đã được validator chặn.
- **RA-4 — Quan hệ release↔architectureStage 1:1 một chiều:** chỉ giữ `architectureStage.releaseId` (client dựng `archStageByReleaseId`), bỏ con trỏ hai chiều `release.architectureStageId`. Chấp nhận để tránh drift.

## Blockers

**Không có.** Mọi phát hiện HIGH của vòng review đã được xử lý: source-of-truth bị bác bỏ vì sai sự thật (CD-1) nhưng vẫn thêm 4 nhãn bắt buộc với nội dung đúng; các finding còn lại đã hạ cấp thành chỉnh sửa in-plan và **đã áp dụng** ở các mục §3–§17.

## Historical P0 Entry Criteria (pre-P0-1; no longer active)

Các tiêu chí dưới đây ghi lại gate đã dùng trước P0-1. Chúng không thay thế fresh validation gate trước P0-5:

- [ ] **Baseline xanh:** chạy `python -m pytest -q` + `python tools/build_site.py` + `node --test tests/site_core.test.js` + `python tools/ui_smoke_test.py` trên nhánh hiện tại **trước mọi thay đổi** → tất cả PASS (40/15/12-24-4, `PASS N/N`). Thiết lập mốc sạch để so sánh.
- [ ] **Môi trường đủ:** Python, Node.js, headless Chrome sẵn sàng (cả 3 bậc test chạy được).
- [ ] **Có mục master plan để author data:** §9 (outOfScope), §11/§12 (10 release + status), §20 (không dùng status giả), §23 (Day 10 Stream→Statistics→V0.2), §24 (release % chỉ đếm required), §13/§15 (vị trí Project Application), §42/§45 (hardening tùy chọn).
- [x] **Tập feature-id đã chốt:** canonical artifact có 25 feature; `feat-statistics`/`feat-cache`/`feat-exchange-rate` là feature thật, không map proxy (RA-3).
- [x] **Mapping per-lesson đã authored:** §7.1 phản ánh 38 entry canonical; mọi thay đổi sau này theo quy trình bảo trì §7.2, không chép/đổi mù.
- [ ] **Xác nhận không sửa file cấm:** đọc §3 + §16.0 FILE CHANGE MAP; chỉ sửa `index.template.html`/`content/spendwise-project.json`/`tools/*`/`tests/*`; `index.html` chỉ regenerate.

*Kết thúc historical Review Gate. P0-1..P0-4 đã được implement. Data Contract Alignment phải xác nhận readiness rồi dừng; KHÔNG tự bắt đầu P0-5.*
