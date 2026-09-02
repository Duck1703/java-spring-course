# Supplemental Source Architecture — Design

Status: **approved and implemented** (production registry still empty — see
the Supplemental Source Architecture Implementation report). This document is
the output of the original design gate, kept as the historical design record.

> **Implementation correction (post-approval):** the design below proposed
> adding a new, additive `"origin"` field to every generated resource record
> in `course-catalog.json`/`content/source-manifest.json` (Merge Rule 7, Test
> Plan row B, the Risks entry about unknown-key consumers, and Implementation
> Step 1). During implementation, a stricter backward-compatibility
> requirement was set: generated output must be **byte-for-byte identical**
> to today's output whenever supplemental input is empty or omitted, and no
> new generated field should be added merely because this draft proposed one.
> The `"origin"` field was **not implemented**. Provenance is instead
> discoverable only by (a) cross-referencing `content/supplemental-sources.json`
> itself, and (b) `SUPPLEMENT ...` diagnostic lines printed by
> `merge_supplemental_resources()` during generation (new resource / lessonIds
> merged / no-op). Every other design decision below (two sources of truth,
> unchanged validators, deterministic resource IDs, fail-loud merge semantics)
> was implemented as designed. See [Implementation
> Steps](#implementation-steps) for the original build plan.

## Problem

`content/lessons/*.json` may only cite a `resourceId` that appears in that
lesson's `resourceIds` array inside `course-catalog.json` (enforced by
`_validate_sourceusage_entry` in `tools/validate_lessons.py:204-249`).
`course-catalog.json` is 100% generated from
`GST.CEN_Syllabus_JavaSpring_Dev2-3_v3.xlsx` by `tools/extract_catalog.py`
(confirmed by reading the script in full — `build_manifest()` and the catalog
JSON are built strictly from `parse_schedule(workbook)` output, with no merge
or override input anywhere in the tool). The workbook is the syllabus source
of truth and must stay immutable (global pipeline constraint, restated in the
SQL Sourcing Gate result: `SQL_SOURCING_GATE_BLOCKED`).

Net effect: **authoritative sources that were never listed in the workbook
(e.g. official PostgreSQL docs for the Day 19/20/32 SQL foundation) cannot be
cited by any lesson today**, because there is no path to add a resource to
`course-catalog.json` other than adding a row to the workbook.

## Current Pipeline

```
GST.CEN_Syllabus_JavaSpring_Dev2-3_v3.xlsx      (source of truth, immutable)
        │  tools/extract_catalog.py --workbook --json --markdown --manifest
        ▼
course-catalog.json / course-catalog.md          (generated, frozen — never hand-edited)
content/source-manifest.json                     (generated, 100% derived from catalog["resources"])
        │  tools/check_sources.py --manifest        (fetches URLs, records access evidence)
        │  tools/validate_sources.py --manifest --notes-dir
        ▼
content/source-notes/{batch}.json                (authored: read facts + locators, keyed by resourceId)
        │  cited via lesson.sourceUsage[].resourceId
        ▼
content/lessons/*.json
        │
        ▼
tools/validate_lessons.py                        (gate: resourceId ∈ catalog_lesson.resourceIds,
                                                    resourceId ∈ source_index with readStatus=="read",
                                                    locator ∈ source_index[resourceId].locators)
```

Key facts confirmed by reading the code (not assumed):

- `resource_id(url) = "res-" + sha256(normalize_url(url)).hexdigest()[:12]`
  (`tools/course_model.py:23-34`) — a pure function of the URL. `normalize_url`
  lowercases scheme/host, keeps path+query, drops fragment and trailing
  punctuation.
- `tools/validate_sources.py` validates `content/source-notes/*.json` purely
  against the **shape** of `content/source-manifest.json` — `resourceId`,
  `requestedUrl`, `lessonIds`, `assignedBatch`, `check{...}`. It has no
  knowledge of the workbook and does not care where a manifest resource came
  from.
- `tools/validate_lessons.py`'s `build_source_index()` (line 56) indexes
  `content/source-notes/*.json` purely by `resourceId`, and
  `_validate_sourceusage_entry` checks only `catalog_lesson.resourceIds` (from
  `course-catalog.json`) plus that index. Neither function has any concept of
  provenance.
- `content/lesson-schema.json` documents the same contract in plain text
  (`resourceIds`: "res-* ids the catalog links to this lesson"; `sourceUsage.resourceId`:
  "res-* id linked to this lesson in course-catalog.json with read.status == read").
  Nothing in the schema is workbook-specific.

**This is the central design leverage point: three of the four downstream
tools (`validate_sources.py`, `validate_lessons.py`, `content/lesson-schema.json`'s
contract) are already fully agnostic to where a resource came from.** Only
`tools/extract_catalog.py` (the generation step) is workbook-only. A
supplemental architecture only needs to teach the generation step about a
second, authored input — nothing downstream needs to change.

## Proposed Pipeline

```
GST.CEN_Syllabus_JavaSpring_Dev2-3_v3.xlsx      content/supplemental-sources.json
   (syllabus source of truth, immutable)          (supplemental authoring source of truth)
        │                                                  │
        │  parse_schedule(workbook)                        │  load + validate (structural)
        ▼                                                  ▼
   catalog (workbook-only)  ────────────────────►  merge_supplemental_resources()
                                                              │
                                                              ▼
                                          catalog (workbook ∪ supplemental, fail-loud on conflict)
                                                              │
                                            tools/extract_catalog.py writes, unchanged shape:
                                                              ▼
                              course-catalog.json / course-catalog.md / content/source-manifest.json
                                                              │
                                     (everything below this line: byte-for-byte unchanged code path)
                                                              ▼
                        check_sources.py → source-notes → lesson sourceUsage → validate_lessons.py
```

`tools/extract_catalog.py` gains one new optional argument,
`--supplemental-sources content/supplemental-sources.json`. When omitted, the
tool's behavior is identical to today (this is the backward-compatibility
guarantee — see [Backward Compatibility](#backward-compatibility)).

## Sources of Truth

Two sources of truth from now on, each owning a disjoint concern:

| | Syllabus Source of Truth | Supplemental Authoring Source of Truth |
|---|---|---|
| File | `GST.CEN_Syllabus_JavaSpring_Dev2-3_v3.xlsx` | `content/supplemental-sources.json` |
| Owns | units, days, syllabus structure, original course resources | authoritative references identified *during* authoring that were never in the workbook |
| Mutability | immutable (existing global constraint, unchanged) | hand-authored, reviewed like any other content PR |
| Format | binary workbook | JSON, versioned in git, human-diffable |
| Feeds | `tools/extract_catalog.py --workbook` | `tools/extract_catalog.py --supplemental-sources` |

Neither source of truth is generated. `course-catalog.json` and
`content/source-manifest.json` remain the **only** generated artifacts, now
derived from two inputs instead of one. This preserves the existing rule that
a generated file is never hand-edited to add a citation.

## Supplemental Registry Contract

`content/supplemental-sources.json` — authored, one entry per distinct
(normalized) URL:

```json
{
  "schemaVersion": 1,
  "resources": [
    {
      "url": "https://www.postgresql.org/docs/current/queries-table-expressions.html",
      "title": "7.2.1.1. Joined Tables",
      "publisher": "PostgreSQL Global Development Group",
      "lessonIds": ["day-20"],
      "purpose": "Authoritative INNER/LEFT JOIN semantics for the SQL foundation section."
    }
  ]
}
```

Deliberately **not** authored:

- `id` / `resourceId` — always computed at generation time via the existing
  `tools.course_model.resource_id(url)`. Authors never hand-pick an ID, so a
  typo or copy-paste ID can never collide with or shadow one of the 111
  existing IDs (requirement: deterministic/stable IDs, requirement: existing
  IDs never change).
- `check` / access evidence — populated later by `tools/check_sources.py`
  against the merged manifest, exactly as it is today for workbook resources.
  A supplemental entry is inert (uncitable) until it has gone through
  `check_sources.py` → `content/source-notes/*.json`, same as any workbook
  resource.

Required fields: `url`, `title`, `publisher`, `lessonIds` (non-empty array),
`purpose` (free text, review aid only — not written into the generated
catalog). `sourceType` is intentionally omitted from the schema. **As
implemented** (see the correction note above), provenance is *not* recorded
anywhere in the generated catalog/manifest at all — `content/supplemental-sources.json`
itself is the only durable record of which resources are supplemental, plus
the `SUPPLEMENT ...` lines `tools/extract_catalog.py` prints to stdout on
every generation run that touches a supplemental resource.

## Merge Rules

Executed inside `tools/course_model.py` as a new pure function,
`merge_supplemental_resources(catalog: dict, supplemental: dict) -> dict`,
called from `tools/extract_catalog.py main()` immediately after
`parse_schedule(workbook)` returns and before `build_manifest()` / any file is
written.

1. **Order:** workbook resources are parsed and materialized into `catalog`
   first, exactly as today. Supplemental resources are merged in as a second,
   additive pass on top of the already-built `catalog` dict. If
   `--supplemental-sources` is omitted, or the file's `resources` array is
   empty, this pass is a no-op and `catalog` is byte-for-byte what
   `parse_schedule` produced — this is what makes the change backward
   compatible.
2. **Lesson ID validation timing:** each supplemental entry's `lessonIds` is
   checked against `catalog["lessons"]` (i.e. the just-parsed workbook lesson
   set) **during the merge pass, before any output file is written**. An
   unknown lesson ID fails the whole generation run — nothing is written
   (atomic: no partial catalog/manifest is ever produced).
3. **Duplicate URL within the supplemental file:** two entries whose
   `normalize_url(url)` match is a hard error. One entry per distinct URL —
   if a resource serves two lessons, list both in that one entry's
   `lessonIds`, don't repeat the entry.
4. **Duplicate resourceId across two different supplemental URLs:** a
   `sha256` collision at 12 hex chars is not practically expected, but is
   still treated as a hard error rather than silently keeping one and
   dropping the other (defensive; matches "duplicate resourceId phải fail
   loudly").
5. **Same resource, workbook vs. supplemental (URL normalizes to an ID
   already present in `catalog["resources"]` from the workbook pass):**
   - If title/publisher metadata *conflicts* with what's derivable from the
     existing resource's labels → **hard error.** The author must resolve
     this by hand (fix the supplemental entry or drop it if the workbook
     already covers it); merge never silently prefers one side.
   - If metadata is compatible and only `lessonIds` differ → **merge, not
     silent overwrite.** The resource's `lessonIds` becomes the union, and
     `extract_catalog.py` prints a visible, non-error log line, e.g.
     `SUPPLEMENT res-xxxxxxxxxxxx merge lessonIds+=[day-20] -> [day-19,day-20]`
     (as implemented — see `tools/course_model.py`'s
     `merge_supplemental_resources`), to stdout on every run that touches it
     (mirrors the existing `PASS ...` summary line convention in
     `extract_catalog.py main()`). This satisfies "merge cùng resource nhưng
     lessonIds khác nhau" while keeping it loud and reviewable rather than
     swallowed — this diagnostic line is also the only place provenance is
     visible, since (per the correction note above) no `origin` field is
     written to generated output.
6. **No whole-course attach:** a supplemental entry's `lessonIds` is exactly
   the lessons the resource is linked to — never expanded, inferred, or
   defaulted to "all lessons in a unit". This directly satisfies "không được
   silently attach một source vào toàn course."
7. **No provenance field in generated output (corrected — see note at top):**
   the original draft proposed a new, additive `"origin"` field on each
   `course-catalog.json` / `content/source-manifest.json` resource record.
   **As implemented, this field does not exist.** The stricter requirement
   set during implementation was that generated output be byte-for-byte
   identical to today's output whenever supplemental input is empty or
   absent — and more generally, that no new generated field be added merely
   because this draft proposed one, since downstream code does not currently
   need provenance. An eventual audit ("which resources came from the
   workbook vs. were added during authoring") is still possible — it just
   requires cross-referencing `content/supplemental-sources.json` (the
   authored file itself) or the stdout `SUPPLEMENT ...` lines from the
   generation run, rather than reading a field off the generated record.
8. **`assignedBatch` subtlety authors must know:** `build_manifest()` assigns
   a resource's batch from `units[unit_ids[0]]["number"]`, where
   `unit_ids[0]` is the unit of the **first** `lessonIds` entry. For a
   resource shared across units (e.g. the PostgreSQL Indexes source spanning
   Day 20, unit-07 → `data-security`, and Day 32, unit-11 → `project-final`),
   list the primary/first-introduced lesson first in `lessonIds`. This is an
   existing mechanism, not new — supplemental entries inherit it unchanged.

## Resource ID Rules

- Reuse `tools.course_model.resource_id` / `normalize_url` verbatim — do not
  reimplement URL normalization or hashing for supplemental sources. This
  guarantees requirement 7 ("same normalized resource → same ID") for free,
  and is exactly how rule 5 above detects a workbook/supplemental collision:
  it's the same function computing the same ID, not a heuristic URL compare.
- No random/UUID IDs anywhere in the registry — the whole point of a
  content-derived ID is that duplicate detection and workbook-collision
  detection fall out of the ID function itself.
- The 111 existing resource IDs are untouched by construction: the merge pass
  only ever *adds* to `catalog["resources"]` / lesson `resourceIds`; it never
  rewrites or renumbers anything the workbook pass produced. No migration of
  existing IDs is needed or performed.

## Validation Rules

Two validators, one new and small, one existing and unmodified:

**New — `tools/validate_supplemental_sources.py`** (structural gate on the
*authored* file, mirroring the CLI conventions of `validate_sources.py`:
`argparse`, `_error(...)` formatted lines, sorted output, exit 1 on any
error):

- `content/supplemental-sources.json` parses and matches the schema
  (`schemaVersion`, `resources[]` with all required fields present and
  non-empty).
- `url` is a well-formed absolute `http(s)` URL.
- No duplicate normalized URLs within the file.
- Every `lessonIds` entry exists in `course-catalog.json`'s current
  `lessons[]` (this validator can be run standalone, any time, against the
  already-generated catalog — same pattern as `validate_sources.py --manifest
  ... --notes-dir ...` being independently re-runnable after generation).
- No two entries produce the same `resourceId` unless their normalized URLs
  are identical (defensive collision check, same rule as merge rule 4).

**Unchanged — `tools/validate_sources.py` and `tools/validate_lessons.py`.**
Both already validate purely against the generated `course-catalog.json` /
`content/source-manifest.json` shape and `content/source-notes/*.json`,
without caring about provenance (confirmed by reading both in full — see
[Current Pipeline](#current-pipeline)). Once a supplemental resource is
merged into the manifest and has a matching source-note, it is
indistinguishable from a workbook resource to these two validators. No code
change is required in either file. This is why the design proposes a small
*dedicated* validator rather than extending `validate_sources.py`:
`validate_sources.py`'s job is read-completeness/access-evidence checking
against manifest `check` data, a different concern from authored-file
structural integrity; keeping them separate matches the existing
one-validator-per-concern pattern in `tools/`.

## CLI / Build Integration

```
tools/extract_catalog.py
  --workbook PATH              (required, unchanged)
  --json PATH                  (required, unchanged)
  --markdown PATH               (required, unchanged)
  --manifest PATH               (required, unchanged)
  --supplemental-sources PATH   (NEW, optional; default: none → no-op)

tools/validate_supplemental_sources.py   (NEW)
  --supplemental-sources PATH   (required)
  --catalog PATH                 (required — cross-checks lessonIds exist)
```

No change to `tools/check_sources.py` or `tools/validate_sources.py`
invocations — they already take `--manifest`, and the manifest now simply
contains more resources on the runs where `--supplemental-sources` was used
during generation.

## Backward Compatibility

- Running `extract_catalog.py` with today's exact arguments (no
  `--supplemental-sources`) produces byte-for-byte identical
  `course-catalog.json` / `course-catalog.md` / `content/source-manifest.json`
  to what exists today — this is Test Plan item A, and is the mechanism that
  makes the change safe to land before any SQL source is actually added.
- An empty or absent `content/supplemental-sources.json` is equivalent to
  omitting the flag.
- The 111 existing resource IDs, all existing lessons' `resourceIds`, and all
  existing `content/source-notes/*.json` entries are untouched.
- `content/lesson-schema.json` needs no change — its `resourceIds` /
  `sourceUsage.resourceId` contract is already provenance-agnostic wording.

## Test Plan

New/updated test files, following the existing 1:1 `tools/x.py` ↔
`tests/test_x.py` convention and the existing in-process `main([...])` CLI
test style (see `tests/test_course_model.py:179`,
`test_cli_writes_utf8_catalog_markdown_and_manifest`):

| # | Case | Where |
|---|---|---|
| A | No `--supplemental-sources` flag (or empty file) → generated output identical to current behavior | `tests/test_course_model.py` (extend `test_cli_writes_utf8_catalog_markdown_and_manifest`-style fixture) |
| B | One supplemental resource, one new lesson mapping → appears in `catalog["resources"]` and `content/source-manifest.json` (as implemented: with no `origin` field — see correction note at top) | `tests/test_course_model.py` (new `SupplementalSourceMergeTests` class) |
| C | Supplemental resource attached to `day-19`/`day-20` → `tools/validate_lessons.py` accepts a `sourceUsage` entry citing it once a matching source-note exists | `tests/test_validate_lessons.py` (extend with a fixture catalog/source-index built from a merged-shape resource — no code change needed in `validate_lessons.py` itself, this test documents/locks in that fact) |
| D | Supplemental entry with a `lessonIds` value that doesn't exist → merge fails loudly, no output written | `tests/test_course_model.py` + `tests/test_validate_supplemental_sources.py` (new) |
| E | Two supplemental entries, same normalized URL (duplicate), or same URL as an existing workbook resource with conflicting title/publisher → fails loudly | `tests/test_course_model.py` (merge) + `tests/test_validate_supplemental_sources.py` (structural) |
| F | After B, the 111 pre-existing resource IDs are byte-identical to a run without `--supplemental-sources` | `tests/test_course_model.py` (assert workbook-only resource IDs unchanged pre/post merge) |
| G | `tools/validate_sources.py` and source-note locator rules (`tools/validate_lessons.py`'s `build_source_index`/`_validate_sourceusage_entry`) require zero code changes — a supplemental-origin resource with a normal source-note passes exactly like a workbook one | `tests/test_validate_sources.py`, `tests/test_validate_lessons.py` (new fixture-based regression test, not a behavior change) |

## Migration

None required. `content/supplemental-sources.json` starts absent (or with an
empty `resources: []`), which is a pure no-op per the merge rules. The 111
existing resources need no ID changes, no re-checking, and no re-authored
source notes.

## SQL Gate Integration

This section explains how the six PostgreSQL sources already verified in the
`SQL_SOURCING_GATE_BLOCKED` report would enter the course **after** this
architecture is implemented and approved — not now.

| Source (verified locator) | `lessonIds` (order matters — see merge rule 8) | Resulting `assignedBatch` |
|---|---|---|
| PostgreSQL Docs §5.5.4/5.5.5 (Primary/Foreign Keys) | `["day-19"]` | `data-security` (unit-07) |
| PostgreSQL Docs §7.2.1.1 (Joined Tables — INNER/LEFT JOIN) | `["day-20"]` | `data-security` (unit-07) |
| PostgreSQL Docs §3.4 (Transactions, ACID, BEGIN/COMMIT/ROLLBACK) | `["day-20"]` | `data-security` (unit-07) |
| PostgreSQL Docs §13.2 (Transaction Isolation levels) | `["day-20"]` | `data-security` (unit-07) |
| PostgreSQL Docs §13.3 (Explicit Locking) | `["day-20"]` | `data-security` (unit-07) |
| PostgreSQL Docs §11.1 (Indexes — Introduction) | `["day-20", "day-32"]` | `data-security` (day-20 listed first, unit-07) — **correction applied per your instruction:** this source must support both Day 20 (learners get the index mental model before Day 24) and Day 32 (deepening only), not Day 32 alone |

Open question flagged, not resolved here: whether Day 19 needs an additional,
more introductory source for bare table/row/column vocabulary rather than
leaning on the Primary/Foreign Key subsections alone. A plausible candidate
is the PostgreSQL Tutorial's own "Concepts" section (part of the tutorial
chapter that precedes DDL/DML), but **this locator has not been fetched or
verified** — unlike the six above, it must go through the same
WebFetch-verification step before being treated as citable, at SQL-sourcing
time, not in this design task.

Mechanically, once implemented, adding these would be:
1. Author six entries in `content/supplemental-sources.json`.
2. `python tools/validate_supplemental_sources.py --supplemental-sources content/supplemental-sources.json --catalog course-catalog.json`
3. `python tools/extract_catalog.py --workbook GST.CEN_Syllabus_JavaSpring_Dev2-3_v3.xlsx --json course-catalog.json --markdown course-catalog.md --manifest content/source-manifest.json --supplemental-sources content/supplemental-sources.json`
4. `python tools/check_sources.py --manifest content/source-manifest.json` (populates `check` evidence for the 6 new URLs only — existing 111 are already checked and idempotent)
5. Author matching entries in `content/source-notes/data-security.json` (the batch all six resolve to)
6. `python tools/validate_sources.py --manifest content/source-manifest.json --notes-dir content/source-notes`
7. Only then can Day 19/20/32 lesson JSON cite these `resourceId`s via `sourceUsage`, validated by the unmodified `tools/validate_lessons.py`.

This remains out of scope for the current task — explicitly not performed here.

## Risks

- ~~**Unverified assumption:** no consumer of `course-catalog.json` /
  `content/source-manifest.json` does strict schema validation (rejecting
  unknown keys) that would break on the new additive `origin` field.~~
  **Moot as implemented** (see correction note at top): no `origin` field
  was added, so this risk does not apply. `tools/build_site.py` and the two
  JS test suites (`tests/site_core.test.js`, `tests/test_ui_smoke_test.py`)
  were run as part of the implementation's validation pass regardless, and
  pass unchanged since their inputs (production `course-catalog.json` /
  `content/source-manifest.json` / `content/lessons/*.json`) are byte-for-byte
  unchanged while the production supplemental registry stays empty.
- **`assignedBatch` first-lessonId ordering** (merge rule 8) is a sharp edge:
  an author who lists `lessonIds` in the "wrong" order silently gets the
  resource routed to a different source-notes batch file than intended. The
  merge log line (rule 5) and the new validator's cross-check make this
  visible, but it's still easy to get wrong on the first attempt — worth a
  short comment in the schema/tooling itself once implemented.
- **Workbook/supplemental collision handling (merge rule 5) adds real
  branching complexity** to what is currently a straightforward
  parse-and-write script. This is inherent to the requirement ("cùng
  resource nhưng lessonIds khác nhau merge thế nào") and not avoidable, but
  it's the single largest chunk of new logic and deserves its own focused
  code review pass.
- **`content/supplemental-sources.json` could grow into a second, informally
  governed workbook** if review discipline lapses (e.g., someone adds a
  resource with `lessonIds` pointing at many lessons "just in case"). Merge
  rule 6 (no whole-course attach) and requiring a `purpose` string per entry
  are process guardrails, not enforced by any validator — worth a note in
  CONTRIBUTING/authoring docs at implementation time.

## Implementation Steps

Small, independently reviewable steps, each with its own tests:

1. ~~Read `tools/build_site.py` end-to-end for resource-record consumption
   patterns; confirm the new `origin` field is safe to add (resolves the Risk
   above).~~ **Superseded as implemented:** no `origin` field was added (see
   correction note at top), so this step was not needed. No code change.
2. Add `merge_supplemental_resources()` to `tools/course_model.py` + unit
   tests (Test Plan B, D, E, F) against in-memory fixture catalogs — no
   `extract_catalog.py` change yet, no real workbook/network involved.
3. Wire `--supplemental-sources` into `tools/extract_catalog.py main()`,
   calling the new function; add the CLI-level test (Test Plan A, C-adjacent)
   using the existing `_write_workbook` fixture pattern.
4. Add `tools/validate_supplemental_sources.py` + `tests/test_validate_supplemental_sources.py`.
5. Add the "already provenance-agnostic" regression tests to
   `tests/test_validate_sources.py` / `tests/test_validate_lessons.py` (Test
   Plan G) — these should pass with **zero** changes to the two files under
   test, proving the claim in [Validation Rules](#validation-rules) rather
   than asserting it.
6. Create an empty `content/supplemental-sources.json` (`{"schemaVersion": 1,
   "resources": []}`) and run the full existing validation suite
   (`validate_lessons.py --compile-java`, `validate_sources.py`,
   `build_site.py`, `pytest tests/`, `node --test tests/site_core.test.js`)
   to confirm zero regressions before any real source is added.
7. Only after step 6 is green: a separate, explicit task adds the six
   PostgreSQL sources per [SQL Gate Integration](#sql-gate-integration).
