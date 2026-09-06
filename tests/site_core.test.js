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

test("RENAME_MAP is empty at this wave, so the migration is a deliberate no-op for renames", () => {
  // The machinery ships and is tested while it has no entries: the first wave
  // that renames a task id meets already-working code. RENAME_MAP is frozen, so
  // the rename branch cannot be exercised from here — the wave that adds the
  // first entry must add a test alongside it asserting the old id's completion
  // survives, which only holds because the rename is applied BEFORE the
  // valid-id filter.
  assert.deepEqual(core.RENAME_MAP, {});
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
