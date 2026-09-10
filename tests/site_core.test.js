"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadCore() {
  const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
  const start = html.indexOf("/* COURSE_CORE_START */");
  const end = html.indexOf("/* COURSE_CORE_END */");
  assert.ok(start !== -1 && end !== -1 && end > start, "core markers present");
  const scriptStart = html.lastIndexOf("<script", start);
  const scriptEnd = html.indexOf("</script>", end);
  const block = html.slice(start, end);
  const context = { console, URL };
  vm.createContext(context);
  vm.runInContext(block + "\nglobalThis.CourseCore = CourseCore;", context);
  // Wrap every member so object results are cloned into the host realm;
  // otherwise deepStrictEqual fails on cross-realm prototypes.
  const raw = context.CourseCore;
  const wrapped = {};
  for (const key of Object.keys(raw)) {
    const value = raw[key];
    wrapped[key] =
      typeof value === "function"
        ? (...args) => JSON.parse(JSON.stringify(value(...args)))
        : JSON.parse(JSON.stringify(value));
  }
  return wrapped;
}

const core = loadCore();

// ---- fixtures -------------------------------------------------------------
const lessons = [
  {
    id: "day-01", group: "java", unitId: "unit-01", title: "JVM, JRE, JDK & Data Types",
    summary: "Nền tảng JVM, kiểu dữ liệu.",
    outcomes: ["Phân biệt JVM/JRE/JDK"],
    sections: [{ id: "s1", title: "JVM là gì", blocks: [] }],
  },
  {
    id: "day-02", group: "java", unitId: "unit-01", title: "Kiểm thử và biến",
    summary: "Biến, kiểu, kiểm thử đơn giản.",
    outcomes: ["Viết kiểm thử cơ bản"],
    sections: [{ id: "s2", title: "Kiểm thử", blocks: [] }],
  },
];
const units = [
  { id: "unit-01", number: 1, title: "Java Platform & Language Basics", group: "java", lessonIds: ["day-01", "day-02"] },
];

test("normalizeSearch strips diacritics and collapses spaces", () => {
  assert.equal(core.normalizeSearch("  Cấu hình ĐẬU Bean "), "cau hinh dau bean");
});

test("parseRoute preserves existing dashboard, lesson, resources and fallback behavior", () => {
  assert.deepEqual(core.parseRoute(""), { view: "dashboard" });
  assert.deepEqual(core.parseRoute("#/dashboard"), { view: "dashboard" });
  assert.deepEqual(core.parseRoute("#lesson/day-13"), { view: "lesson", lessonId: "day-13" });
  assert.deepEqual(core.parseRoute("#lesson/not-real"), { view: "lesson", lessonId: "not-real" });
  assert.deepEqual(core.parseRoute("#resources"), { view: "resources" });
  assert.deepEqual(core.parseRoute("#/unknown"), { view: "dashboard" });
});

test("parseRoute recognizes every P0 project route", () => {
  assert.deepEqual(core.parseRoute("#/project"), { view: "project" });
  assert.deepEqual(core.parseRoute("#/roadmap"), { view: "roadmap" });
  assert.deepEqual(core.parseRoute("#/release/v0-1"), { view: "release", releaseId: "v0-1" });
  assert.deepEqual(core.parseRoute("#/map"), { view: "map" });
  assert.deepEqual(core.parseRoute("#/architecture"), { view: "architecture" });
});

test("selectCurrentRelease prefers building then the earliest planned release", () => {
  const releases = [
    { id: "v0-3", order: 3, status: "planned" },
    { id: "v0-2", order: 2, status: "building" },
    { id: "v0-1", order: 1, status: "planned" },
  ];
  assert.equal(core.selectCurrentRelease(releases).id, "v0-2");
  assert.equal(
    core.selectCurrentRelease(releases.map((release) => ({ ...release, status: "planned" }))).id,
    "v0-1",
  );
  assert.equal(core.selectCurrentRelease([]), null);
});

test("selectNextBuildTask follows release ordering and skips optional or completed tasks", () => {
  const release = { id: "v0-1", buildTaskIds: ["task-b", "task-optional", "task-a"] };
  const buildTasks = [
    { id: "task-a", releaseId: "v0-1", required: true },
    { id: "task-b", releaseId: "v0-1", required: true },
    { id: "task-optional", releaseId: "v0-1", required: false },
  ];
  assert.equal(core.selectNextBuildTask(release, buildTasks, []).id, "task-b");
  assert.equal(core.selectNextBuildTask(release, buildTasks, ["task-b"]).id, "task-a");
  assert.equal(core.selectNextBuildTask(release, buildTasks, ["task-b", "task-a"]), null);
  assert.equal(core.selectNextBuildTask(null, buildTasks, []), null);
});

test("calculateProgress intersects completion with group scope", () => {
  assert.deepEqual(
    core.calculateProgress(lessons, ["day-01"], "java"),
    { completed: 1, total: 2, percent: 50 },
  );
  assert.deepEqual(
    core.calculateProgress(lessons, ["day-01"], null),
    { completed: 1, total: 2, percent: 50 },
  );
  assert.deepEqual(core.calculateProgress([], [], "java"), { completed: 0, total: 0, percent: 0 });
});

test("nextLessonId walks publication order with bounds", () => {
  assert.equal(core.nextLessonId(lessons, "day-01", 1), "day-02");
  assert.equal(core.nextLessonId(lessons, "day-01", -1), null);
  assert.equal(core.nextLessonId(lessons, "day-02", 1), null);
});

test("sanitizeState drops unknown ids, keys and properties", () => {
  const cleaned = core.sanitizeState(
    {
      version: 999,
      completed: ["day-01", "fake", "day-01"],
      lastLessonId: "fake",
      practice: { "day-01-practice-01": { attempted: true }, evil: "x" },
      collapsedUnits: ["unit-01", "fake"],
      theme: "neon",
      projectProgress: { buildTasks: ["task-real", "task-fake", "task-real"] },
      extra: "discard",
    },
    new Set(["day-01"]),
    new Set(["unit-01"]),
    new Set(["day-01-practice-01"]),
    new Set(["task-real"]),
  );
  assert.deepEqual(cleaned.completed, ["day-01"]);
  assert.equal(cleaned.lastLessonId, null);
  assert.equal(cleaned.theme, "system");
  assert.equal("extra" in cleaned, false);
  assert.deepEqual(Object.keys(cleaned.practice), ["day-01-practice-01"]);
  assert.deepEqual(cleaned.projectProgress.buildTasks, ["task-real"]);
});

test("sanitizeState returns fresh defaults on invalid input", () => {
  const fresh = core.sanitizeState(null, new Set(), new Set(), new Set());
  assert.equal(fresh.theme, "system");
  assert.deepEqual(fresh.completed, []);
  assert.deepEqual(fresh.projectProgress, { buildTasks: [], legacyCompleted: [] });
});

test("sanitizeState migrates a v1 state forward, preserving course progress", () => {
  const migrated = core.sanitizeState(
    { version: 1, completed: ["day-01"], theme: "dark" },
    new Set(["day-01"]),
    new Set(["unit-01"]),
    new Set(["day-01-practice-01"]),
    new Set(["task-real"]),
  );
  assert.equal(core.STATE_VERSION, 3);
  assert.equal(migrated.version, core.STATE_VERSION);
  assert.deepEqual(migrated.completed, ["day-01"]);
  assert.equal(migrated.theme, "dark");
  assert.deepEqual(migrated.projectProgress, { buildTasks: [], legacyCompleted: [] });
});

test("sanitizeState drops unknown build task ids and defaults missing project progress", () => {
  const cleaned = core.sanitizeState(
    { projectProgress: { buildTasks: ["task-a", "ghost", "task-b", "task-a"] } },
    new Set(), new Set(), new Set(), new Set(["task-a", "task-b"]),
  );
  assert.deepEqual(cleaned.projectProgress.buildTasks, ["task-a", "task-b"]);
  // "ghost" is no longer known to the artifact, so it becomes history rather
  // than vanishing: a v2 state whose task was retired keeps the evidence.
  assert.deepEqual(cleaned.projectProgress.legacyCompleted, ["ghost"]);

  // A 4-arg caller (no validBuildTaskIds) still gets a well-formed track; with
  // nothing valid to match, every id is retired.
  const legacy = core.sanitizeState(
    { projectProgress: { buildTasks: ["task-a"] } }, new Set(), new Set(), new Set(),
  );
  assert.deepEqual(legacy.projectProgress, { buildTasks: [], legacyCompleted: ["task-a"] });
});

test("migrateProjectProgress partitions ids into current and retired without synthesizing", () => {
  const known = new Set(["task-a", "task-b"]);
  const migrated = core.migrateProjectProgress(
    { buildTasks: ["task-a", "task-retired", "task-a"] },
    known,
  );
  assert.deepEqual(migrated.buildTasks, ["task-a"]);
  assert.deepEqual(migrated.legacyCompleted, ["task-retired"]);
  // A split task's successors are never auto-completed: only the retired id is
  // recorded, and task-b (a hypothetical successor) stays untouched.
  assert.equal(migrated.buildTasks.includes("task-b"), false);
});

test("migrateProjectProgress is total on malformed input and never returns a shared shape", () => {
  const empty = { buildTasks: [], legacyCompleted: [] };
  for (const input of [null, undefined, [], "x", 7, {}, { buildTasks: "nope" }]) {
    assert.deepEqual(core.migrateProjectProgress(input, new Set(["task-a"])), empty);
  }
  // Non-string and empty-string entries are discarded, not coerced.
  assert.deepEqual(
    core.migrateProjectProgress({ buildTasks: [1, "", null, "task-a"] }, new Set(["task-a"])),
    { buildTasks: ["task-a"], legacyCompleted: [] },
  );
  // Called with no id set at all, everything is retired rather than dropped.
  assert.deepEqual(
    core.migrateProjectProgress({ buildTasks: ["task-a"] }),
    { buildTasks: [], legacyCompleted: ["task-a"] },
  );
});

test("migrateProjectProgress carries an existing legacyCompleted forward and never overlaps", () => {
  const migrated = core.migrateProjectProgress(
    { buildTasks: ["task-a"], legacyCompleted: ["task-gone", "task-gone", "task-a"] },
    new Set(["task-a"]),
  );
  // A previously-retired id that the artifact has since RE-introduced returns to
  // buildTasks; the two lists are a partition, so nothing appears in both.
  assert.deepEqual(migrated.buildTasks, ["task-a"]);
  assert.deepEqual(migrated.legacyCompleted, ["task-gone"]);
  const overlap = migrated.buildTasks.filter((id) => migrated.legacyCompleted.includes(id));
  assert.deepEqual(overlap, []);
});

test("RENAME_MAP carries exactly the P1 rename, and renamed completion survives migration", () => {
  // P1's Case A rename: task-category-enum became task-category-model (it
  // gains JPA mapping at V0.5, so the id no longer names the mechanism). The
  // map is frozen, so the rename branch is exercised through
  // migrateProjectProgress, which applies it BEFORE the valid-id filter — the
  // old id's completion must survive as the new id.
  assert.deepEqual(core.RENAME_MAP, { "task-category-enum": "task-category-model" });
  const known = new Set(["task-category-model", "task-a"]);
  const migrated = core.migrateProjectProgress(
    { buildTasks: ["task-category-enum", "task-a"] },
    known,
  );
  // renamed id lands under its NEW identity in buildTasks
  assert.ok(migrated.buildTasks.includes("task-category-model"));
  assert.ok(migrated.buildTasks.includes("task-a"));
  assert.equal(migrated.buildTasks.length, 2);
  assert.deepEqual(migrated.legacyCompleted, []);
});

test("split-task ids (retired, never renamed) are preserved as legacyCompleted and no successor auto-completes", () => {
  // P1's Case B splits: task-rest-controllers -> 3 endpoint tasks;
  // task-jwt-auth -> 4+1 auth tasks. The old ids have NO rename entry, so they
  // partition to legacyCompleted (history preserved) and none of the
  // successors is marked complete — auto-completing them would claim work the
  // learner never did (the JWT split in particular contains a post-capstone
  // task).
  const known = new Set([
    "task-account-endpoints", "task-transaction-endpoints", "task-category-endpoints",
    "task-auth-foundation", "task-user-migration", "task-ownership-checks",
    "task-token-lifecycle", "task-canonical-token-issuer", "task-auth-hardening-review",
  ]);
  const migrated = core.migrateProjectProgress(
    { buildTasks: ["task-rest-controllers", "task-jwt-auth"] },
    known,
  );
  assert.deepEqual(migrated.buildTasks, []);
  assert.equal(migrated.legacyCompleted.length, 2);
  assert.ok(migrated.legacyCompleted.includes("task-rest-controllers"));
  assert.ok(migrated.legacyCompleted.includes("task-jwt-auth"));
});

test("unchanged P1 ids keep their completion and legacyCompleted stays a partition", () => {
  // Ids the P1 artifact kept (e.g. task-money-vo, task-atomic-transfer) must
  // still migrate into buildTasks, and a previously-retired id never
  // re-overlaps with the kept set.
  const known = new Set(["task-money-vo", "task-atomic-transfer"]);
  const migrated = core.migrateProjectProgress(
    { buildTasks: ["task-money-vo"], legacyCompleted: ["task-rest-controllers"] },
    known,
  );
  assert.deepEqual(migrated.buildTasks, ["task-money-vo"]);
  assert.deepEqual(migrated.legacyCompleted, ["task-rest-controllers"]);
  const overlap = migrated.buildTasks.filter((id) => migrated.legacyCompleted.includes(id));
  assert.deepEqual(overlap, []);
});

test("calculateReleaseProgress counts only required tasks for the release", () => {
  const buildTasks = [
    { id: "t1", releaseId: "v0-1", featureIds: ["f1"], required: true },
    { id: "t2", releaseId: "v0-1", featureIds: ["f1"], required: true },
    { id: "t3", releaseId: "v0-1", featureIds: ["f1"], required: false },
    { id: "t4", releaseId: "v0-2", featureIds: ["f2"], required: true },
  ];
  assert.deepEqual(
    core.calculateReleaseProgress(buildTasks, ["t1"], "v0-1"),
    { completed: 1, total: 2, percent: 50 },
  );
  // Completing every required task reaches 100% even with an optional task open.
  assert.deepEqual(
    core.calculateReleaseProgress(buildTasks, ["t1", "t2", "t3"], "v0-1"),
    { completed: 2, total: 2, percent: 100 },
  );
  assert.deepEqual(core.calculateReleaseProgress([], [], "v0-1"), { completed: 0, total: 0, percent: 0 });
});

test("calculateFeatureProgress counts only required tasks for the feature", () => {
  const buildTasks = [
    { id: "t1", releaseId: "v0-1", featureIds: ["f1"], required: true },
    { id: "t2", releaseId: "v0-1", featureIds: ["f1", "f2"], required: true },
    { id: "t3", releaseId: "v0-1", featureIds: ["f1"], required: false },
  ];
  assert.deepEqual(
    core.calculateFeatureProgress(buildTasks, ["t2"], "f1"),
    { completed: 1, total: 2, percent: 50 },
  );
  assert.deepEqual(
    core.calculateFeatureProgress(buildTasks, ["t2"], "f2"),
    { completed: 1, total: 1, percent: 100 },
  );
});

test("deriveMapRows classifies every lesson as direct/future/theory/unmapped without mutating inputs", () => {
  const mapLessons = [
    { id: "day-01", group: "java", unitId: "unit-01", title: "Money" },
    { id: "day-02", group: "java", unitId: "unit-01", title: "Operators" },
    { id: "day-39-64", group: "ojt", unitId: "unit-99", title: "OJT aggregate" },
  ];
  const lessonMap = {
    "day-01": { applicationType: "direct", releaseId: "v0-1", featureIds: ["feat-money"] },
    "day-02": { applicationType: "theory" },
    // day-39-64 intentionally absent — aggregated lesson, never authored a mapping entry.
  };
  const rows = core.deriveMapRows(mapLessons, lessonMap);
  assert.deepEqual(rows, [
    { id: "day-01", title: "Money", group: "java", unitId: "unit-01", applicationType: "direct", releaseId: "v0-1", featureIds: ["feat-money"] },
    { id: "day-02", title: "Operators", group: "java", unitId: "unit-01", applicationType: "theory", releaseId: null, featureIds: [] },
    { id: "day-39-64", title: "OJT aggregate", group: "ojt", unitId: "unit-99", applicationType: "unmapped", releaseId: null, featureIds: [] },
  ]);
  // Pure: source arrays/objects are untouched.
  assert.deepEqual(mapLessons[0], { id: "day-01", group: "java", unitId: "unit-01", title: "Money" });
  assert.deepEqual(Object.keys(lessonMap), ["day-01", "day-02"]);
});

test("deriveMapRows treats a future-application lesson as its own category", () => {
  const rows = core.deriveMapRows(
    [{ id: "day-05", group: "java", unitId: "unit-02", title: "Inheritance" }],
    { "day-05": { applicationType: "future", releaseId: "v0-3", featureIds: [] } },
  );
  assert.equal(rows[0].applicationType, "future");
  assert.equal(rows[0].releaseId, "v0-3");
});

test("filterMapRows groups theory+unmapped under one filter bucket while keeping row-level types distinct", () => {
  const rows = [
    { id: "a", applicationType: "direct", releaseId: "v0-1" },
    { id: "b", applicationType: "future", releaseId: "v0-3" },
    { id: "c", applicationType: "theory", releaseId: null },
    { id: "d", applicationType: "unmapped", releaseId: null },
  ];
  assert.deepEqual(core.filterMapRows(rows, "all", "all").map((r) => r.id), ["a", "b", "c", "d"]);
  assert.deepEqual(core.filterMapRows(rows, "direct", "all").map((r) => r.id), ["a"]);
  assert.deepEqual(core.filterMapRows(rows, "future", "all").map((r) => r.id), ["b"]);
  assert.deepEqual(core.filterMapRows(rows, "theory-unmapped", "all").map((r) => r.id), ["c", "d"]);
  // Each row keeps its own precise applicationType — the filter only groups, never merges data.
  const theoryUnmapped = core.filterMapRows(rows, "theory-unmapped", "all");
  assert.deepEqual(theoryUnmapped.map((r) => r.applicationType), ["theory", "unmapped"]);
});

test("filterMapRows narrows by release on top of the type filter", () => {
  const rows = [
    { id: "a", applicationType: "direct", releaseId: "v0-1" },
    { id: "b", applicationType: "direct", releaseId: "v0-2" },
    { id: "c", applicationType: "future", releaseId: "v0-1" },
  ];
  assert.deepEqual(core.filterMapRows(rows, "all", "v0-1").map((r) => r.id), ["a", "c"]);
  assert.deepEqual(core.filterMapRows(rows, "direct", "v0-1").map((r) => r.id), ["a"]);
  assert.deepEqual(core.filterMapRows(rows, "direct", "v0-9"), []);
});

test("deriveDomainEntities unions and dedups features[].domainEntities, alphabetically ordered", () => {
  const features = [
    { id: "feat-money", name: "Money Value Object", domainEntities: ["Money"] },
    { id: "feat-account", name: "Account", domainEntities: ["Account", "Money"] },
    { id: "feat-category", name: "Category", domainEntities: [] },
  ];
  assert.deepEqual(core.deriveDomainEntities(features), [
    { entity: "Account", featureIds: ["feat-account"] },
    { entity: "Money", featureIds: ["feat-money", "feat-account"] },
  ]);
});

test("deriveDomainEntities never hardcodes entity names — empty input yields empty output", () => {
  assert.deepEqual(core.deriveDomainEntities([]), []);
  assert.deepEqual(core.deriveDomainEntities([{ id: "f1", domainEntities: [] }]), []);
});

test("orderArchitectureStages joins releases to their stage and sorts by release.order", () => {
  const releases = [
    { id: "v0-2", order: 2, status: "planned" },
    { id: "v0-1", order: 1, status: "planned" },
    { id: "v0-3", order: 3, status: "planned" },
  ];
  const stages = [
    { id: "arch-v0-2", releaseId: "v0-2", title: "Spring App" },
    { id: "arch-v0-1", releaseId: "v0-1", title: "Java Domain" },
    // v0-3 has no authored stage — must be omitted, not synthesized.
  ];
  assert.deepEqual(
    core.orderArchitectureStages(releases, stages).map((pair) => [pair.release.id, pair.stage.id]),
    [["v0-1", "arch-v0-1"], ["v0-2", "arch-v0-2"]],
  );
  assert.deepEqual(core.orderArchitectureStages([], []), []);
});

test("groupReleasesByMilestone derives groups from milestone.releaseIds in release order", () => {
  const releases = [
    { id: "v0-1", order: 1 },
    { id: "v0-2", order: 2 },
    { id: "v0-3", order: 3 },
  ];
  const milestones = [
    { id: "ms-1", name: "Java Foundation", releaseIds: ["v0-2", "v0-1"] },
    { id: "ms-2", name: "Spring App", releaseIds: ["v0-3"] },
  ];
  const groups = core.groupReleasesByMilestone(releases, milestones);
  assert.deepEqual(groups.map((g) => g.milestone.id), ["ms-1", "ms-2"]);
  // Releases within a group are release-order sorted regardless of authored releaseIds order.
  assert.deepEqual(groups[0].releases.map((r) => r.id), ["v0-1", "v0-2"]);
  assert.deepEqual(groups[1].releases.map((r) => r.id), ["v0-3"]);
});

test("groupReleasesByMilestone puts releases uncovered by any milestone in a trailing ungrouped bucket", () => {
  const releases = [{ id: "v0-1", order: 1 }, { id: "v0-2", order: 2 }];
  const milestones = [{ id: "ms-1", name: "Java Foundation", releaseIds: ["v0-1"] }];
  const groups = core.groupReleasesByMilestone(releases, milestones);
  assert.equal(groups.length, 2);
  assert.equal(groups[0].milestone.id, "ms-1");
  assert.equal(groups[1].milestone, null);
  assert.deepEqual(groups[1].releases.map((r) => r.id), ["v0-2"]);
});

test("searchLessons matches title/summary/outcome/unit text normalized", () => {
  const hits = core.searchLessons(lessons, units, "kiem thu");
  assert.deepEqual(hits, [lessons[1]]);
  const hits2 = core.searchLessons(lessons, units, "JVM");
  assert.deepEqual(hits2, [lessons[0]]);
  assert.deepEqual(core.searchLessons(lessons, units, ""), []);
});

test("escapeHtml neutralizes markup and quotes", () => {
  assert.equal(core.escapeHtml('<img src=x onerror=alert(1)>'), '&lt;img src=x onerror=alert(1)&gt;');
  assert.equal(core.escapeHtml('a & b "c" \'d\''), 'a &amp; b &quot;c&quot; &#39;d&#39;');
  assert.equal(core.escapeHtml(null), "");
});

test("safeExternalUrl allows only absolute http(s)/mailto", () => {
  assert.equal(core.safeExternalUrl('javascript:alert(1)'), null);
  assert.equal(core.safeExternalUrl('data:text/html,<script>x</script>'), null);
  assert.equal(core.safeExternalUrl('https://docs.spring.io/a'), 'https://docs.spring.io/a');
  assert.equal(core.safeExternalUrl('http://example.com/x?y=1'), 'http://example.com/x?y=1');
  assert.equal(core.safeExternalUrl('not a url'), null);
  assert.equal(core.safeExternalUrl(null), null);
});

// ---- P3: Task Detail / mentor prompt --------------------------------------

test("parseRoute resolves task routes with a guarded decode", () => {
  assert.deepEqual(core.parseRoute("#/task/task-money-vo"), { view: "task", taskId: "task-money-vo" });
  assert.deepEqual(core.parseRoute("#task/day-01"), { view: "task", taskId: "day-01" });
  // Encoded id decodes to the real task id.
  assert.deepEqual(core.parseRoute("#/task/task%2Dmoney%2Dvo"), { view: "task", taskId: "task-money-vo" });
  // A decodable escape that matches no task still parses as a task route —
  // the not-found decision belongs to the renderer, not the parser.
  assert.deepEqual(core.parseRoute("#/task/%20"), { view: "task", taskId: " " });
  // A MALFORMED escape must not throw a URIError: fall back to the raw segment.
  assert.deepEqual(core.parseRoute("#/task/%"), { view: "task", taskId: "%" });
  assert.deepEqual(core.parseRoute("#/task/%E0%A4%A"), { view: "task", taskId: "%E0%A4%A" });
  // No segment → not a task route at all.
  assert.deepEqual(core.parseRoute("#/task/"), { view: "dashboard" });
  // Extra segments stay part of the id (deterministic not-found downstream).
  assert.deepEqual(core.parseRoute("#/task/task-money-vo/extra"), { view: "task", taskId: "task-money-vo/extra" });
});

test("orderAllTasks orders by release order then release.buildTaskIds, deduping and skipping unknown ids", () => {
  const releases = [
    { id: "r2", order: 2, buildTaskIds: ["t3", "t2", "t-ghost"] },
    { id: "r1", order: 1, buildTaskIds: ["t1", "t3"] }, // t3 duplicates across releases
  ];
  const buildTasks = [
    { id: "t3", releaseId: "r2" },
    { id: "t2", releaseId: "r2" },
    { id: "t1", releaseId: "r1" },
    { id: "t-orphan" }, // in no release list → never ordered
  ];
  const releasesCopy = JSON.parse(JSON.stringify(releases));
  const ordered = core.orderAllTasks(releases, buildTasks);
  assert.deepEqual(ordered.map((t) => t.id), ["t1", "t3", "t2"]);
  assert.deepEqual(releases, releasesCopy); // inputs never mutated
  assert.deepEqual(core.orderAllTasks([], buildTasks), []);
  assert.deepEqual(core.orderAllTasks(releases, []), []);
});

test("stepsForTask filters by taskId and sorts by order without mutating the source", () => {
  const buildSteps = [
    { id: "s-b", taskId: "t1", order: 2 },
    { id: "s-a", taskId: "t1", order: 1 },
    { id: "s-other", taskId: "t2", order: 1 },
    { id: "s-c", taskId: "t1", order: 3 },
  ];
  const steps = core.stepsForTask(buildSteps, "t1");
  assert.deepEqual(steps.map((s) => s.id), ["s-a", "s-b", "s-c"]);
  // Source array order untouched (raw JSON order is never an authority).
  assert.deepEqual(buildSteps.map((s) => s.id), ["s-b", "s-a", "s-other", "s-c"]);
  assert.deepEqual(core.stepsForTask([], "t1"), []);
  assert.deepEqual(core.stepsForTask(null, "t1"), []);
});

test("estimateTaskMinutes sums only when EVERY step has a finite non-negative estimatedMinutes", () => {
  assert.equal(core.estimateTaskMinutes([{ estimatedMinutes: 20 }, { estimatedMinutes: 45 }]), 65);
  assert.equal(core.estimateTaskMinutes([{ estimatedMinutes: 20 }, {}]), null); // partial sum would understate
  assert.equal(core.estimateTaskMinutes([{ estimatedMinutes: -5 }]), null);
  assert.equal(core.estimateTaskMinutes([]), null);
  assert.equal(core.estimateTaskMinutes(null), null);
});

test("buildMentorPrompt emits all ten Phase-2 §14 fields for a task-level prompt", () => {
  const task = {
    id: "task-money-vo",
    title: "Money Value Object",
    problem: "Số tiền lưu bằng double sẽ mất chính xác.",
    goal: "Tạo Money VO bất biến.",
    acceptanceCriteria: ["MoneyTest pass với các case làm tròn", "Không dùng double cho tiền"],
    constraints: ["Không thêm dependency mới"],
    featureIds: ["feat-money"],
  };
  const release = { id: "v0-1", version: "V0.1", title: "Domain foundation", status: "planned" };
  const steps = [
    { id: "s1", taskId: "task-money-vo", order: 1, title: "Viết MoneyTest trước", doneWhen: "Test compile", verifyCommand: "mvn test" },
    { id: "s2", taskId: "task-money-vo", order: 2, title: "Cài Money", doneWhen: "Test pass", verifyCommand: "mvn test" },
  ];
  const lessons = [
    { id: "day-01", title: "JVM & Data Types", done: true },
    { id: "day-02", title: "Kiểm thử", done: false },
  ];
  const prereqTasks = [{ id: "task-0", title: "Scaffold repo", done: true }];
  const ctx = {
    task, release, steps, lessons, prereqTasks,
    features: ["Money Value Object"],
    ruleIds: ["R3", "R7"],
  };
  const ctxCopy = JSON.parse(JSON.stringify(ctx));
  const text = core.buildMentorPrompt(ctx);

  // 1. Role line
  assert.ok(text.includes("mentor lap trinh"), "role line present");
  assert.ok(text.includes("Spendwise"), "project named in role");
  // 2. Current task section with verbatim AC
  assert.ok(text.includes("## Task hiện tại"));
  assert.ok(text.includes("- Task id: task-money-vo"));
  assert.ok(text.includes("MoneyTest pass với các case làm tròn"), "AC quoted verbatim");
  assert.ok(text.includes("Không thêm dependency mới"), "constraints quoted verbatim");
  // 3. Steps in order with doneWhen + verify
  assert.ok(text.includes("## Các bước của task (theo thứ tự)"));
  assert.ok(text.includes("- Bước 1: Viết MoneyTest trước — done when: Test compile | verify: mvn test"));
  assert.ok(text.includes("- Bước 2: Cài Money"));
  // 4. Knowledge boundary + the boundary instruction line
  assert.ok(text.includes("## Kiến thức đã học (boundary)"));
  assert.ok(text.includes("JVM & Data Types (day-01)"));
  // Regression (adversarial review): the boundary is the task's DECLARED
  // knowledge list — a not-yet-ticked relevant lesson must stay listed even
  // when another lesson is marked done, or the boundary clause would forbid
  // knowledge the task page itself lists as relevant.
  assert.ok(text.includes("Kiểm thử (day-02)"), "not-done relevant lesson stays in the boundary");
  assert.ok(text.includes("KHONG su dung ky thuat tu bai hoc sau"));
  // 5. Artifact prerequisites
  assert.ok(text.includes("## Artifact prerequisites trong repo nguoi hoc"));
  assert.ok(text.includes("Scaffold repo (task-0)"));
  // 6. Architecture rules — ids only, never invented text
  assert.ok(text.includes("## Architecture rules in force"));
  assert.ok(text.includes("R3, R7"));
  // 7. Toolchain: Java 17 pinned, Boot pin explicitly PENDING, no invented version
  assert.ok(text.includes("## Toolchain"));
  assert.ok(text.includes("Java 17"));
  assert.ok(text.includes("SPRING_BOOT_EXACT_PIN_PENDING"));
  // A version suggestion would look like "Spring Boot 3.x" — "Spring Boot 40
  // bai" (the lesson count in the role line) must not trip this.
  assert.ok(!/Spring Boot\s+v?[0-9]+\.[0-9]/.test(text), "no Spring Boot version is ever suggested");
  // 8. Repository truth
  assert.ok(text.includes("## Repository truth"));
  // 9+10. Teaching contract with convention + stop clause verbatim
  assert.ok(text.includes(core.MENTOR_CONVENTION_CLAUSE));
  assert.equal(core.MENTOR_CONVENTION_CLAUSE, "Prefer the established Spendwise convention over your own preference, even where your preference is defensible.");
  // The whole stop clause must appear verbatim (§14 field 9), not just fragments.
  assert.ok(text.includes(core.MENTOR_STOP_CLAUSE));
  // Field 10 non-goals line is mandatory — the test title promises all ten fields.
  assert.ok(text.includes("Khong refactor code khong lien quan, khong them dependency, khong doi build, khong tao package moi"), "non-goals line present");
  // Field 2 release sub-line renders because the fixture supplies a release.
  assert.ok(text.includes("Release hien tai trong prompt nay: V0.1 — Domain foundation"), "release sub-line present");
  // Never leaks template artifacts
  assert.ok(!text.includes("undefined"));
  assert.ok(!text.includes("[object Object]"));
  // Purity: input object untouched
  assert.deepEqual(ctx, ctxCopy);
});

test("buildMentorPrompt step scope quotes the focused step without dropping sibling steps", () => {
  const task = { id: "task-money-vo", title: "Money VO", acceptanceCriteria: ["AC1"], constraints: [], featureIds: [] };
  const steps = [
    { id: "s1", taskId: "task-money-vo", order: 1, title: "Viết test trước", intent: "TDD", doneWhen: "Test compile", verifyCommand: "mvn test" },
    { id: "s2", taskId: "task-money-vo", order: 2, title: "Cài Money", doneWhen: "Test pass" },
  ];
  const text = core.buildMentorPrompt({ task, step: steps[0], steps });
  assert.ok(text.includes("## Bước đang làm (focus)"));
  assert.ok(text.includes("- Step 1: Viết test trước (id: s1)"));
  assert.ok(text.includes("- Intent: TDD"));
  // Siblings still listed so the mentor sees the sequence.
  assert.ok(text.includes("- Bước 2: Cài Money"));
  assert.ok(!text.includes("undefined"));
  // Task-level prompt omits the focus section entirely.
  const taskText = core.buildMentorPrompt({ task, steps });
  assert.ok(!taskText.includes("## Bước đang làm (focus)"));
  // Empty optional sections never render as empty headings.
  const minimal = core.buildMentorPrompt({ task: { id: "t", title: "T" } });
  assert.ok(minimal.includes("- Task id: t"));
  assert.ok(!minimal.includes("undefined"));
  // Total on hostile input: no task → empty string, never a throw.
  assert.equal(core.buildMentorPrompt({}), "");
  assert.equal(core.buildMentorPrompt(null), "");
});

test("built stylesheet pairs the step-picker display:flex with a [hidden] override", () => {
  // Author display beats the UA [hidden] rule. The picker must carry its own
  // .task-prompt-step-picker[hidden] companion or it stays visible (and
  // keyboard-focusable) in task scope where its change handler no-ops.
  const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
  assert.ok(/\.task-prompt-step-picker\s*\{[^}]*display:\s*flex/.test(html), "base rule sets display:flex");
  assert.ok(/\.task-prompt-step-picker\[hidden\]\s*\{[^}]*display:\s*none/.test(html), "companion [hidden] rule present");
});

// ---- P4: Architecture Constitution + defense matrix + rule traceability ----

test("CourseCore exports the P4 constitution data with exactly R1-R26, no duplicates, non-empty canonical text", () => {
  const rules = core.ARCHITECTURE_CONSTITUTION;
  assert.equal(rules.length, 26);
  const ids = rules.map((r) => r.id);
  assert.deepEqual(ids, Array.from({ length: 26 }, (_, i) => `R${i + 1}`));
  for (const rule of rules) {
    assert.ok(rule.text && rule.text.length > 20, `${rule.id} carries canonical text`);
    assert.ok(rule.group, `${rule.id} has a group`);
    assert.ok(rule.title, `${rule.id} has a title`);
  }
  const groupKeys = new Set(core.CONSTITUTION_GROUPS.map((g) => g.key));
  assert.equal(core.CONSTITUTION_GROUPS.length, 7);
  for (const rule of rules) assert.ok(groupKeys.has(rule.group), `${rule.id} group is one of the 7`);
  // ids() mirrors the data
  assert.deepEqual(core.constitutionRuleIds(), ids);
});

test("every buildSteps architectureRules token resolves to a defined Constitution rule (0 dangling)", () => {
  const fs2 = fs;
  const project = JSON.parse(
    fs2.readFileSync(path.join(__dirname, "..", "content", "spendwise-project.json"), "utf8")
  );
  const steps = project.buildSteps || [];
  assert.equal(steps.length, 161);
  // 295 total refs across 161 steps after the P4 source-guidance repair (was 306), tokens only R1..R26
  let refs = 0;
  const tokens = new Set();
  for (const step of steps) {
    for (const token of step.architectureRules || []) {
      refs += 1;
      tokens.add(token);
      assert.match(token, /^R\d{1,2}$/);
    }
  }
  assert.equal(refs, 295);
  assert.equal(tokens.size, 26);
  // resolveRuleTokens reports dangles by suffixing :DANGLING
  const resolved = core.resolveRuleTokens(steps);
  assert.equal(resolved.filter((t) => t.endsWith(":DANGLING")).length, 0, "0 dangling rule references");
  assert.deepEqual(resolved, Array.from(tokens));
  // sanity: resolveRuleTokens flags a fabricated token
  const probe = core.resolveRuleTokens([{ architectureRules: ["R27"] }]);
  assert.ok(probe.includes("R27:DANGLING"));
});

test("defense matrix has 15 rows and every answer anchor resolves to a Constitution rule", () => {
  const matrix = core.DEFENSE_MATRIX;
  assert.equal(matrix.length, 15);
  const defined = new Set(core.constitutionRuleIds());
  matrix.forEach((row, i) => {
    assert.ok(row.q, `row ${i + 1} has a question`);
    assert.ok(defined.has(row.a), `row ${i + 1} anchor ${row.a} is a defined rule`);
    assert.ok(row.why, `row ${i + 1} has an evidence note`);
  });
});

test("evolution narrative covers exactly the ten authored releases in order", () => {
  const project = JSON.parse(
    fs.readFileSync(path.join(__dirname, "..", "content", "spendwise-project.json"), "utf8")
  );
  const narrative = core.EVOLUTION_NARRATIVE;
  assert.equal(narrative.length, 10);
  const releaseIds = project.releases.map((r) => r.id);
  assert.deepEqual(narrative.map((n) => n.releaseId), releaseIds);
  for (const entry of narrative) assert.ok(entry.why && entry.why.length > 40, `${entry.releaseId} has a WHY paragraph`);
});

test("built stylesheet pairs .lesson-list display:grid with a [hidden] override (P4 sidebar-collapse fix)", () => {
  const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
  assert.ok(/\.lesson-list\s*\{[^}]*display:\s*grid/.test(html), "base rule sets display:grid");
  assert.ok(/\.lesson-list\[hidden\]\s*\{[^}]*display:\s*none/.test(html), "companion [hidden] rule present");
});

// ---- P4 QA: content-fidelity pins (2026-09-09 audit) -----------------------

test("R22 text carries the full two-tier identity contract, not a condensed overclaim", () => {
  const rules = new Map(core.ARCHITECTURE_CONSTITUTION.map((r) => [r.id, r]));
  const r22 = rules.get("R22").text;
  // Preferred tier normalizes the source txn id (Blueprint §3 / D10.1 pseudocode).
  assert.ok(r22.includes("normalize(sourceTxnId)"), "preferred tier normalizes sourceTxnId");
  // Fingerprint fields are enumerated (accountId | occurredOn | direction | amount | description).
  assert.ok(r22.includes("occurredOn") && r22.includes("direction"), "fingerprint fields enumerated");
  // Determinism is same-order qualified, and the limitation + non-goal are stated.
  assert.ok(r22.includes("same logical order"), "determinism is same-order qualified");
  assert.ok(r22.includes("NOT guaranteed"), "reordering limitation stated");
  assert.ok(r22.includes("not universal bank-file deduplication"), "non-goal stated");
});

test("R26 note discloses the unresolved Spring Boot pin instead of claiming a full freeze", () => {
  const rules = new Map(core.ARCHITECTURE_CONSTITUTION.map((r) => [r.id, r]));
  const note = rules.get("R26").note || "";
  assert.ok(note.includes("SPRING_BOOT_EXACT_PIN_PENDING"), "Boot pin disclosed in the reader note");
  assert.ok(note.includes("ADR-017"), "pin authority named");
});

test("defense row 15 attributes testing tiers to ADR-014, not to R26", () => {
  const row = core.DEFENSE_MATRIX[14];
  assert.equal(row.q, "Why is there no coverage percentage?");
  assert.ok(row.why.includes("ADR-014"), "ADR-014 named as the tier owner");
  assert.ok(row.why.includes("does not fix the tiers"), "R26's role bounded to knowledge timing");
});

test("evolution and course-boundary narratives carry required qualifications", () => {
  const template = fs.readFileSync(path.join(__dirname, "..", "index.template.html"), "utf8");
  // V0.2 changes Transaction only to add sourceRef; unchanged-domain belongs to V0.3.
  assert.ok(template.includes("Transaction chỉ nhận thêm sourceRef"), "V0.2 narrative names its domain-model change");
  assert.ok(!template.includes("xung quanh domain mà không đổi domain"), "V0.2 narrative does not claim an unchanged domain");
  // V0.1-V0.6 is "mandatory" except the one post-Day-36 TokenIssuer execution.
  assert.ok(template.includes("thực hiện sau Day 36"), "boundary names the post-Day-36 TokenIssuer exception");
  // V0.8 re-import determinism holds only for the same logical statement ordering.
  assert.ok(template.includes("cùng thứ tự nguồn trở nên deterministic"), "V0.8 narrative qualifies same-order determinism");
  assert.ok(template.includes("không phải dedup ngân hàng phổ quát"), "V0.8 narrative disclaims universal dedup");
});

// ---- P4 source-guidance repair pins (2026-09-09) ---------------------------
// Pins for the migration-ownership and rule-membership repairs in
// content/spendwise-project.json. These are semantic pins for the CONFIRMED_FIX
// set only - the full 161-step membership is audited, not hardcoded here.

function repairedSteps() {
  const project = JSON.parse(
    fs.readFileSync(path.join(__dirname, "..", "content", "spendwise-project.json"), "utf8")
  );
  return project.buildSteps || [];
}

test("source_ref timeline: column persists from V1__init; V9 adds only the UNIQUE constraint", () => {
  const steps = new Map(repairedSteps().map((s) => [s.id, s]));
  // The constraint migration is V9 and ALTERs, not CREATEs: source_ref has existed since V1__init.
  const dw = steps.get("step-duplicate-detection-03").doneWhen;
  assert.ok(dw.includes("V9__transaction_source_ref.sql"), "constraint migration is V9");
  assert.ok(dw.includes("UNIQUE (user_id, source_ref)"), "two-column constraint named");
  assert.ok(dw.includes("persisted since V1__init.sql"), "column timeline: source_ref exists from V1__init");
  assert.ok(!dw.includes("adds source_ref VARCHAR"), "V9 does not claim first creation of the source_ref column");
  const hint = steps.get("step-duplicate-detection-03").mentorHint;
  assert.ok(hint.includes("V9 alters the table V1__init.sql already created"), "hint says V9 ALTERs the V1 table");
  // Every other migration mention carries the renumbered names (V2/V3 inserted; old V2-V7 shifted to V4-V9).
  const blob = JSON.stringify(repairedSteps());
  assert.ok(blob.includes("V2__balance_projection.sql"), "M2 migration file exists");
  assert.ok(blob.includes("V3__transfer_ref.sql"), "M1 migration file exists");
  for (const gone of ["V2__user_identity", "V3__budget.sql", "V4__recurring.sql", "V5__rules.sql", "V6__import_batch", "V7__transaction_source_ref"]) {
    assert.ok(!blob.includes(gone), `stale migration name absent: ${gone}`);
  }
});

test("transfer_ref and @Version columns are owned by post-baseline migrations, not V1__init", () => {
  const steps = new Map(repairedSteps().map((s) => [s.id, s]));
  // M1: the transfer step owns V3__transfer_ref.sql (the transfer pair postdates the V1 baseline).
  const at1 = steps.get("step-atomic-transfer-01");
  assert.ok(at1.filesTouched.some((f) => f.includes("V3__transfer_ref.sql")), "atomic-transfer-01 owns V3__transfer_ref.sql");
  assert.ok(at1.doneWhen.includes("postdates V1__init.sql"), "transfer_ref timeline stated");
  assert.ok(at1.architectureRules.includes("R26"), "migration-creating step carries R26");
  // M2: the balance-projection step owns V2__balance_projection.sql (version + balance columns).
  const bp1 = steps.get("step-balance-projection-01");
  assert.ok(bp1.filesTouched.some((f) => f.includes("V2__balance_projection.sql")), "balance-projection-01 owns V2__balance_projection.sql");
  assert.ok(bp1.doneWhen.includes("V2__balance_projection.sql"), "version/balance column timeline stated");
  assert.ok(bp1.architectureRules.includes("R26") && bp1.architectureRules.includes("R3"), "carries R26 + R3 (money DDL)");
});

test("rule-membership repairs: mis-tags removed, missing tags added", () => {
  const steps = new Map(repairedSteps().map((s) => [s.id, s]));
  const rules = (id) => steps.get(id).architectureRules;
  // R23 narrowed to the 5 claim-shaping/issuing steps (QA mis-tags removed).
  const r23 = repairedSteps().filter((s) => s.architectureRules.includes("R23")).map((s) => s.id).sort();
  assert.deepEqual(r23, [
    "step-auth-hardening-01",
    "step-canonical-token-issuer-02",
    "step-canonical-token-issuer-04",
    "step-token-lifecycle-01",
    "step-token-lifecycle-02",
  ]);
  // R21 is transfer semantics only: recurring-generation and reconciliation jobs lose it.
  assert.ok(!rules("step-recurring-generation-03").includes("R21"), "R21 off recurring-generation-03");
  assert.ok(!rules("step-scheduled-reconciliation-01").includes("R21"), "R21 off scheduled-reconciliation-01");
  assert.ok(rules("step-recurring-generation-03").includes("R20"), "canonical path pinned on recurring-generation-03");
  // Missing tags added.
  assert.ok(rules("step-transaction-endpoints-01").includes("R16"), "R16 on transaction-endpoints-01");
  assert.ok(rules("step-slice-test-suite-02").includes("R22"), "R22 on slice-test-suite-02");
  // Over-tags removed.
  assert.ok(!rules("step-hardening-reconciliation-01").includes("R22"), "R22 off hardening-reconciliation-01");
  assert.ok(!rules("step-budget-model-01").includes("R26"), "R26 off budget-model-01 (domain-only step)");
  assert.ok(!rules("step-slice-test-suite-02").includes("R26"), "R26 off slice-test-suite-02 (test-only step)");
  assert.ok(!rules("step-redis-cache-backend-02").includes("R26"), "R26 off redis-cache-backend-02");
  // Refuted adds stay refuted: R11/R24/R14 must not appear where they never belonged.
  assert.ok(!rules("step-duplicate-detection-01").includes("R11"), "R11 not resurrected on duplicate-detection-01");
  assert.ok(!rules("step-production-packaging-02").includes("R13"), "R13 off production-packaging-02");
});
