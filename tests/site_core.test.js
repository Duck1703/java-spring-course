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
  const context = { console };
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

test("parseRoute handles dashboard, lesson and raw lesson ids", () => {
  assert.deepEqual(core.parseRoute(""), { view: "dashboard" });
  assert.deepEqual(core.parseRoute("#lesson/day-13"), { view: "lesson", lessonId: "day-13" });
  assert.deepEqual(core.parseRoute("#lesson/not-real"), { view: "lesson", lessonId: "not-real" });
  assert.deepEqual(core.parseRoute("#resources"), { view: "resources" });
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
      extra: "discard",
    },
    new Set(["day-01"]),
    new Set(["unit-01"]),
    new Set(["day-01-practice-01"]),
  );
  assert.deepEqual(cleaned.completed, ["day-01"]);
  assert.equal(cleaned.lastLessonId, null);
  assert.equal(cleaned.theme, "system");
  assert.equal("extra" in cleaned, false);
  assert.deepEqual(Object.keys(cleaned.practice), ["day-01-practice-01"]);
});

test("sanitizeState returns fresh defaults on invalid input", () => {
  const fresh = core.sanitizeState(null, new Set(), new Set(), new Set());
  assert.equal(fresh.theme, "system");
  assert.deepEqual(fresh.completed, []);
});

test("searchLessons matches title/summary/outcome/unit text normalized", () => {
  const hits = core.searchLessons(lessons, units, "kiem thu");
  assert.deepEqual(hits, [lessons[1]]);
  const hits2 = core.searchLessons(lessons, units, "JVM");
  assert.deepEqual(hits2, [lessons[0]]);
  assert.deepEqual(core.searchLessons(lessons, units, ""), []);
});
