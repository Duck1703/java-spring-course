import contextlib
import copy
import io
import json
import re
import tempfile
import unittest
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from tools.course_model import normalize_url, resource_id

_GENERATED_AT_RE = re.compile(rb'"generatedAt": "[^"]*"')
ROOT = Path(__file__).resolve().parents[1]


def _bytes_ignoring_generated_at(path: Path) -> bytes:
    """Read a generated JSON file's bytes with its `generatedAt` timestamp
    value blanked out.

    `generatedAt` is `datetime.now(timezone.utc)` captured fresh on every
    parse_schedule() call (tools/course_model.py), so it necessarily differs
    between any two separate CLI invocations -- including two runs with
    identical supplemental-sources input. Byte-for-byte backward-compat
    comparisons must ignore this one field; every other byte is compared
    exactly as written.
    """
    return _GENERATED_AT_RE.sub(b'"generatedAt": "IGNORED"', path.read_bytes())


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


class ScheduleParserTests(unittest.TestCase):
    def test_forward_fills_merged_style_cells_and_groups_days(self):
        from tools.course_model import parse_schedule

        with tempfile.TemporaryDirectory() as directory:
            workbook = Path(directory) / "fixture.xlsx"
            self._write_workbook(workbook)

            catalog = parse_schedule(workbook)

        unit = catalog["units"][0]
        day_one = catalog["lessons"][0]
        expected = {
            "unitId": "unit-01",
            "lessonIds": ["day-01", "day-02"],
            "dayOneRows": [3, 4],
            "dayOneResourceCount": 1,
            "dayOneAssignment": "Assignment: Calculate an expression",
        }
        self.assertEqual(unit["id"], expected["unitId"])
        self.assertEqual(unit["lessonIds"], expected["lessonIds"])
        self.assertEqual(day_one["sourceRows"], expected["dayOneRows"])
        self.assertEqual(len(day_one["resourceIds"]), expected["dayOneResourceCount"])
        self.assertEqual(
            day_one["syllabusAssignments"][0]["text"],
            expected["dayOneAssignment"],
        )
        multiline_activity = (
            "JVM, JRE, JDK & Data Types\nJVM Architecture / Primitive Types"
        )
        self.assertEqual(day_one["title"], "JVM, JRE, JDK & Data Types")
        self.assertEqual(day_one["outline"][0], multiline_activity)
        self.assertEqual(day_one["activities"][0]["text"], multiline_activity)
        self.assertEqual(day_one["durationMinutes"], 150)
        self.assertEqual(day_one["objectives"], ["LO1", "LO2"])
        self.assertEqual(day_one["activities"][1]["row"], 4)
        self.assertEqual(day_one["activities"][0]["date"], "2026-08-22")
        self.assertEqual(catalog["resources"][0]["sourceRows"], [3, 4])

    def test_renders_deterministic_markdown_and_escapes_resource_labels(self):
        from tools.course_model import render_catalog_markdown

        catalog = {
            "source": {"workbook": "fixture.xlsx", "sheet": "JavaSpring_Schedule"},
            "units": [
                {
                    "id": "unit-01",
                    "number": 1,
                    "title": "Java Platform & Language Basics",
                    "group": "java",
                    "lessonIds": ["day-01"],
                    "sourceRows": [3],
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
                    "outline": ["JVM Architecture\n  - Primitive Types "],
                    "objectives": ["LO1"],
                    "durationMinutes": 150,
                    "activities": [{"row": 3, "text": "Assignment", "deliveryType": "Lecture", "durationMinutes": 150, "trainer": "A", "format": "Online", "date": "2026-08-22"}],
                    "syllabusAssignments": [{"row": 3, "text": "Assignment"}],
                    "resourceIds": ["res-abc123456789"],
                    "sourceRows": [3],
                }
            ],
            "resources": [
                {
                    "id": "res-abc123456789",
                    "url": "https://example.com/a_(b)",
                    "labels": ["JVM [Architecture]"],
                    "lessonIds": ["day-01"],
                    "sourceRows": [3],
                    "occurrences": [
                        {
                            "lessonId": "day-01",
                            "row": 3,
                            "label": "JVM [Architecture]",
                        }
                    ],
                }
            ],
        }

        markdown = render_catalog_markdown(catalog)

        self.assertIn("## Day 1 — JVM, JRE, JDK & Data Types", markdown)
        heading = next(line for line in markdown.splitlines() if line.startswith("## Day"))
        self.assertNotIn("\n", heading)
        self.assertTrue(
            all(line == line.rstrip() for line in markdown.splitlines()),
            "rendered Markdown must not contain trailing whitespace",
        )
        self.assertIn("- **Nhóm:** Java", markdown)
        self.assertIn("[JVM \\[Architecture\\]](https://example.com/a_(b))", markdown)
        self.assertIn("chưa kiểm tra", markdown)

        catalog["resources"][0]["check"] = {
            "status": "redirected",
            "httpStatus": 200,
        }
        markdown = render_catalog_markdown(catalog)
        self.assertIn("chuyển hướng và truy xuất được (HTTP 200)", markdown)
        self.assertNotIn("đã đọc", markdown)

    def test_manifest_assigns_first_linked_unit_batch_and_empty_check(self):
        from tools.extract_catalog import build_manifest

        catalog = {
            "generatedAt": "2026-08-22T00:00:00Z",
            "source": {"workbook": "fixture.xlsx", "sheet": "JavaSpring_Schedule"},
            "units": [
                {"id": "unit-02", "number": 2},
                {"id": "unit-03", "number": 3},
            ],
            "lessons": [
                {
                    "id": "day-02",
                    "unitId": "unit-02",
                    "outline": ["Classes", "Inheritance"],
                },
                {
                    "id": "day-03",
                    "unitId": "unit-03",
                    "outline": ["Inheritance", "Interfaces"],
                },
            ],
            "resources": [
                {
                    "id": "res-abc123456789",
                    "url": "https://example.com/a",
                    "labels": ["A", "A reference"],
                    "lessonIds": ["day-02", "day-03"],
                }
            ],
        }

        record = build_manifest(catalog)["resources"][0]

        self.assertEqual(record["assignedBatch"], "java-foundations")
        self.assertEqual(record["unitIds"], ["unit-02", "unit-03"])
        self.assertEqual(
            record["relevantOutline"], ["Classes", "Inheritance", "Interfaces"]
        )
        self.assertEqual(record["check"], {})

    def test_cli_writes_utf8_catalog_markdown_and_manifest(self):
        from tools.extract_catalog import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = root / "fixture.xlsx"
            catalog_path = root / "course-catalog.json"
            markdown_path = root / "course-catalog.md"
            manifest_path = root / "content" / "source-manifest.json"
            self._write_workbook(workbook)

            exit_code = main(
                [
                    "--workbook",
                    str(workbook),
                    "--json",
                    str(catalog_path),
                    "--markdown",
                    str(markdown_path),
                    "--manifest",
                    str(manifest_path),
                ]
            )

            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")
        self.assertEqual(exit_code, 0)
        self.assertEqual(catalog["lessons"][0]["label"], "Day 1")
        self.assertIn("Java/Spring Course Catalog", markdown)
        self.assertEqual(manifest["resources"][0]["check"], {})

    def test_cli_adding_supplemental_resource_preserves_existing_check(self):
        from tools.extract_catalog import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = root / "fixture.xlsx"
            catalog_path = root / "course-catalog.json"
            markdown_path = root / "course-catalog.md"
            manifest_path = root / "content" / "source-manifest.json"
            self._write_workbook(workbook)

            self.assertEqual(
                main(
                    [
                        "--workbook", str(workbook),
                        "--json", str(catalog_path),
                        "--markdown", str(markdown_path),
                        "--manifest", str(manifest_path),
                    ]
                ),
                0,
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            existing_resource = manifest["resources"][0]
            existing_check = {
                "attempted": True,
                "checkedAt": "2026-08-22T16:30:00Z",
                "status": "ok",
                "httpStatus": 200,
                "finalUrl": existing_resource["requestedUrl"],
                "contentType": "text/html",
                "contentBytes": 123,
                "contentSha256": "a" * 64,
                "cacheText": ".course-cache/resources/existing.txt",
                "truncated": False,
                "error": None,
            }
            existing_resource["check"] = existing_check
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            supplemental_url = "https://example.test/new-source"
            registry = root / "supplemental-sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "resources": [
                            {
                                "url": supplemental_url,
                                "title": "New Source",
                                "publisher": "Example Publisher",
                                "lessonIds": ["day-02"],
                                "purpose": "Regression fixture for state preservation.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                main(
                    [
                        "--workbook", str(workbook),
                        "--json", str(catalog_path),
                        "--markdown", str(markdown_path),
                        "--manifest", str(manifest_path),
                        "--supplemental-sources", str(registry),
                    ]
                ),
                0,
            )
            regenerated = json.loads(manifest_path.read_text(encoding="utf-8"))

        resources = {resource["resourceId"]: resource for resource in regenerated["resources"]}
        self.assertEqual(resources[existing_resource["resourceId"]]["check"], existing_check)
        self.assertEqual(resources[resource_id(supplemental_url)]["check"], {})

    def test_manifest_preserves_check_when_only_lesson_ids_change(self):
        from tools.extract_catalog import build_manifest

        catalog = _fixture_catalog()
        existing = catalog["resources"][0]
        previous_check = {"status": "ok", "contentSha256": "a" * 64}
        previous_manifest = {
            "resources": [
                {
                    "resourceId": existing["id"],
                    "requestedUrl": existing["url"],
                    "check": previous_check,
                }
            ]
        }
        merge_supplemental = _supplemental_entry(
            url=existing["url"],
            title="Existing Resource",
            lesson_ids=("day-20",),
        )
        from tools.course_model import merge_supplemental_resources
        merge_supplemental_resources(catalog, [merge_supplemental])

        resource = build_manifest(catalog, previous_manifest)["resources"][0]

        self.assertEqual(resource["lessonIds"], ["day-19", "day-20"])
        self.assertEqual(resource["check"], previous_check)

    def test_manifest_does_not_inherit_check_for_same_id_with_changed_url(self):
        from tools.extract_catalog import build_manifest

        catalog = _fixture_catalog()
        current = catalog["resources"][0]
        previous_manifest = {
            "resources": [
                {
                    "resourceId": current["id"],
                    "requestedUrl": "https://example.test/different-resource",
                    "check": {"status": "ok", "contentSha256": "a" * 64},
                }
            ]
        }

        resource = build_manifest(catalog, previous_manifest)["resources"][0]

        self.assertEqual(resource["check"], {})

    def test_manifest_does_not_retain_removed_resource(self):
        from tools.extract_catalog import build_manifest

        catalog = _fixture_catalog()
        current = catalog["resources"][0]
        removed = {
            "resourceId": "res-removed",
            "requestedUrl": "https://example.test/removed",
            "check": {"status": "ok", "contentSha256": "b" * 64},
        }
        previous_manifest = {
            "resources": [
                {
                    "resourceId": current["id"],
                    "requestedUrl": current["url"],
                    "check": {"status": "ok", "contentSha256": "a" * 64},
                },
                removed,
            ]
        }

        regenerated = build_manifest(catalog, previous_manifest)

        self.assertNotIn("res-removed", {resource["resourceId"] for resource in regenerated["resources"]})

    def test_cli_rejects_duplicate_previous_resource_ids_before_writing(self):
        from tools.extract_catalog import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = root / "fixture.xlsx"
            catalog_path = root / "course-catalog.json"
            markdown_path = root / "course-catalog.md"
            manifest_path = root / "source-manifest.json"
            self._write_workbook(workbook)
            sentinel = b"catalog must remain untouched"
            catalog_path.write_bytes(sentinel)
            duplicate = {
                "resourceId": "res-duplicate",
                "requestedUrl": "https://example.test/a",
                "check": {},
            }
            manifest_path.write_text(
                json.dumps({"resources": [duplicate, duplicate]}), encoding="utf-8"
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "--workbook", str(workbook),
                        "--json", str(catalog_path),
                        "--markdown", str(markdown_path),
                        "--manifest", str(manifest_path),
                    ]
                )

            self.assertEqual(exit_code, 1)
            self.assertEqual(catalog_path.read_bytes(), sentinel)
            self.assertIn("previous manifest", output.getvalue())

    def test_cli_rejects_malformed_previous_check_before_writing(self):
        from tools.extract_catalog import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = root / "fixture.xlsx"
            catalog_path = root / "course-catalog.json"
            markdown_path = root / "course-catalog.md"
            manifest_path = root / "source-manifest.json"
            self._write_workbook(workbook)
            sentinel = b"catalog must remain untouched"
            catalog_path.write_bytes(sentinel)
            manifest_path.write_text(
                json.dumps(
                    {
                        "resources": [
                            {
                                "resourceId": "res-bad",
                                "requestedUrl": "https://example.test/a",
                                "check": "not-an-object",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "--workbook", str(workbook),
                        "--json", str(catalog_path),
                        "--markdown", str(markdown_path),
                        "--manifest", str(manifest_path),
                    ]
                )

            self.assertEqual(exit_code, 1)
            self.assertEqual(catalog_path.read_bytes(), sentinel)
            self.assertIn("previous manifest", output.getvalue())

    def test_cli_omitting_supplemental_sources_matches_baseline_output(self):
        """Test A: no --supplemental-sources flag -> output identical to a
        plain run (proves the flag is purely additive/backward compatible).
        """
        from tools.extract_catalog import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = root / "fixture.xlsx"
            self._write_workbook(workbook)

            baseline_dir = root / "baseline"
            without_flag_dir = root / "without-flag"
            for target in (baseline_dir, without_flag_dir):
                exit_code = main(
                    [
                        "--workbook", str(workbook),
                        "--json", str(target / "course-catalog.json"),
                        "--markdown", str(target / "course-catalog.md"),
                        "--manifest", str(target / "content" / "source-manifest.json"),
                    ]
                )
                self.assertEqual(exit_code, 0)

            self.assertEqual(
                _bytes_ignoring_generated_at(baseline_dir / "course-catalog.json"),
                _bytes_ignoring_generated_at(without_flag_dir / "course-catalog.json"),
            )
            self.assertEqual(
                (baseline_dir / "course-catalog.md").read_bytes(),
                (without_flag_dir / "course-catalog.md").read_bytes(),
            )
            self.assertEqual(
                _bytes_ignoring_generated_at(baseline_dir / "content" / "source-manifest.json"),
                _bytes_ignoring_generated_at(without_flag_dir / "content" / "source-manifest.json"),
            )

    def test_cli_empty_supplemental_registry_matches_baseline_output(self):
        """Test B: an empty content/supplemental-sources.json -> output
        identical to a plain run (byte-for-byte, not just semantically equal).
        """
        from tools.extract_catalog import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = root / "fixture.xlsx"
            self._write_workbook(workbook)
            empty_registry = root / "supplemental-sources.json"
            empty_registry.write_text(
                json.dumps({"schemaVersion": 1, "resources": []}), encoding="utf-8"
            )

            baseline_dir = root / "baseline"
            with_empty_dir = root / "with-empty"
            self.assertEqual(
                main(
                    [
                        "--workbook", str(workbook),
                        "--json", str(baseline_dir / "course-catalog.json"),
                        "--markdown", str(baseline_dir / "course-catalog.md"),
                        "--manifest", str(baseline_dir / "content" / "source-manifest.json"),
                    ]
                ),
                0,
            )
            self.assertEqual(
                main(
                    [
                        "--workbook", str(workbook),
                        "--json", str(with_empty_dir / "course-catalog.json"),
                        "--markdown", str(with_empty_dir / "course-catalog.md"),
                        "--manifest", str(with_empty_dir / "content" / "source-manifest.json"),
                        "--supplemental-sources", str(empty_registry),
                    ]
                ),
                0,
            )

            self.assertEqual(
                _bytes_ignoring_generated_at(baseline_dir / "course-catalog.json"),
                _bytes_ignoring_generated_at(with_empty_dir / "course-catalog.json"),
            )
            self.assertEqual(
                (baseline_dir / "course-catalog.md").read_bytes(),
                (with_empty_dir / "course-catalog.md").read_bytes(),
            )
            self.assertEqual(
                _bytes_ignoring_generated_at(baseline_dir / "content" / "source-manifest.json"),
                _bytes_ignoring_generated_at(with_empty_dir / "content" / "source-manifest.json"),
            )

    def test_cli_one_supplemental_source_appears_in_catalog_and_manifest(self):
        """Test C + D: a new supplemental resource mapped to day-01 appears
        in both course-catalog.json's lesson resourceIds and the manifest.
        """
        from tools.course_model import resource_id
        from tools.extract_catalog import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = root / "fixture.xlsx"
            self._write_workbook(workbook)
            registry = root / "supplemental-sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "resources": [
                            {
                                "url": "https://www.postgresql.org/docs/current/queries-table-expressions.html",
                                "title": "7.2.1.1. Joined Tables",
                                "publisher": "PostgreSQL Global Development Group",
                                "lessonIds": ["day-01"],
                                "purpose": "test fixture only",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            catalog_path = root / "course-catalog.json"
            manifest_path = root / "content" / "source-manifest.json"

            exit_code = main(
                [
                    "--workbook", str(workbook),
                    "--json", str(catalog_path),
                    "--markdown", str(root / "course-catalog.md"),
                    "--manifest", str(manifest_path),
                    "--supplemental-sources", str(registry),
                ]
            )
            self.assertEqual(exit_code, 0)
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        new_id = resource_id("https://www.postgresql.org/docs/current/queries-table-expressions.html")
        day01 = next(lesson for lesson in catalog["lessons"] if lesson["id"] == "day-01")
        self.assertIn(new_id, day01["resourceIds"])
        self.assertIn(new_id, {resource["id"] for resource in catalog["resources"]})
        self.assertIn(new_id, {resource["resourceId"] for resource in manifest["resources"]})

    def test_cli_unknown_lesson_id_fails_loudly_and_writes_nothing(self):
        from tools.extract_catalog import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = root / "fixture.xlsx"
            self._write_workbook(workbook)
            registry = root / "supplemental-sources.json"
            registry.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "resources": [
                            {
                                "url": "https://example.com/nowhere",
                                "title": "Nowhere",
                                "publisher": "Example",
                                "lessonIds": ["day-99"],
                                "purpose": "test fixture only",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            catalog_path = root / "course-catalog.json"

            exit_code = main(
                [
                    "--workbook", str(workbook),
                    "--json", str(catalog_path),
                    "--markdown", str(root / "course-catalog.md"),
                    "--manifest", str(root / "content" / "source-manifest.json"),
                    "--supplemental-sources", str(registry),
                ]
            )
            self.assertEqual(exit_code, 1)
            self.assertFalse(catalog_path.exists())

    @staticmethod
    def _write_workbook(path):
        shared_strings = [
            "Java Platform & Language Basics",
            "Day 1",
            "JVM, JRE, JDK & Data Types\nJVM Architecture / Primitive Types",
            "LO1, LO2",
            "Lecture",
            "Trainer A",
            "Online",
            "• JVM Architecture: https://example.com/jvm#top).\n"
            "• JVM Architecture duplicate: https://example.com/jvm",
            "Assignment: Calculate an expression",
            "Day 2",
            "Operators & Control Flow",
            "LO3",
        ]
        sst = "".join(f"<si><t>{escape(value)}</t></si>" for value in shared_strings)
        worksheet = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="3">
      <c r="A3"><v>1</v></c><c r="B3" t="s"><v>0</v></c>
      <c r="C3" t="s"><v>1</v></c><c r="D3" t="s"><v>2</v></c>
      <c r="E3" t="s"><v>3</v></c><c r="F3" t="s"><v>4</v></c>
      <c r="G3"><f>45+45</f><v>90</v></c><c r="H3" t="s"><v>5</v></c>
      <c r="I3" t="s"><v>6</v></c><c r="J3"><v>46256</v></c>
      <c r="K3" t="s"><v>7</v></c>
    </row>
    <row r="4">
      <c r="D4" t="s"><v>8</v></c><c r="G4"><v>60</v></c>
      <c r="K4" t="s"><v>7</v></c>
    </row>
    <row r="5">
      <c r="C5" t="s"><v>9</v></c><c r="D5" t="inlineStr"><is><t>Operators &amp; Control Flow</t></is></c>
      <c r="E5" t="s"><v>11</v></c><c r="G5"><v>120</v></c>
    </row>
  </sheetData>
</worksheet>"""
        workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="JavaSpring_Schedule" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
        relationships = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>"""
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", workbook)
            archive.writestr("xl/_rels/workbook.xml.rels", relationships)
            archive.writestr(
                "xl/sharedStrings.xml",
                f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">{sst}</sst>',
            )
            archive.writestr("xl/worksheets/sheet1.xml", worksheet)


def _fixture_catalog():
    """Small in-memory catalog shaped like a real parse_schedule() result,
    with one workbook-derived resource already linked to day-19.
    """
    existing_url = "https://example.com/existing-resource"
    existing_id = resource_id(existing_url)
    return {
        "generatedAt": "2026-08-22T00:00:00Z",
        "source": {"workbook": "fixture.xlsx", "sheet": "JavaSpring_Schedule"},
        "units": [{"id": "unit-07", "number": 7, "title": "Unit 7", "group": "spring", "lessonIds": ["day-19", "day-20"], "sourceRows": []}],
        "lessons": [
            {"id": "day-19", "unitId": "unit-07", "outline": [], "resourceIds": [existing_id]},
            {"id": "day-20", "unitId": "unit-07", "outline": [], "resourceIds": []},
        ],
        "resources": [
            {
                "id": existing_id,
                "url": normalize_url(existing_url),
                "labels": ["Existing Resource"],
                "lessonIds": ["day-19"],
                "sourceRows": [],
                "occurrences": [],
            }
        ],
    }


def _supplemental_entry(url="https://example.com/new-resource", title="New Resource",
                         publisher="Example Publisher", lesson_ids=("day-20",),
                         purpose="test fixture only"):
    """Build an entry shaped exactly like load_supplemental_sources()'s output
    -- merge_supplemental_resources() only ever receives already-normalized
    entries (normalizedUrl/resourceId precomputed), never raw authored JSON.
    """
    return {
        "url": url,
        "normalizedUrl": normalize_url(url),
        "resourceId": resource_id(url),
        "title": title,
        "publisher": publisher,
        "lessonIds": list(lesson_ids),
        "purpose": purpose,
    }


def _write_supplemental_file(path, entries):
    path.write_text(
        json.dumps({"schemaVersion": 1, "resources": entries}), encoding="utf-8"
    )


class ProductionStateStabilityTests(unittest.TestCase):
    def test_real_workbook_resources_keep_checks_when_supplemental_sources_are_added(self):
        from tools.course_model import (
            load_supplemental_sources,
            merge_supplemental_resources,
            parse_schedule,
        )
        from tools.extract_catalog import build_manifest

        catalog = parse_schedule(ROOT / "GST.CEN_Syllabus_JavaSpring_Dev2-3_v3.xlsx")
        workbook_ids = {resource["id"] for resource in catalog["resources"]}
        self.assertEqual(len(workbook_ids), 111)
        previous_checks = {
            resource["id"]: {
                "status": "ok",
                "contentSha256": f"{index:064x}",
            }
            for index, resource in enumerate(catalog["resources"], start=1)
        }
        previous_manifest = {
            "resources": [
                {
                    "resourceId": resource["id"],
                    "requestedUrl": resource["url"],
                    "check": previous_checks[resource["id"]],
                }
                for resource in catalog["resources"]
            ]
        }
        entries = load_supplemental_sources(
            ROOT / "content" / "supplemental-sources.json"
        )

        merge_supplemental_resources(catalog, entries)
        manifest = build_manifest(catalog, previous_manifest)
        by_id = {resource["resourceId"]: resource for resource in manifest["resources"]}
        all_ids = set(by_id)
        supplemental_ids = {entry["resourceId"] for entry in entries}
        # One authored entry deliberately targets a URL the workbook already ships
        # (a shared source reused by a second lesson), so it merges instead of
        # introducing a resource; only genuinely new resources start unchecked.
        merged_ids = supplemental_ids & workbook_ids
        new_ids = supplemental_ids - workbook_ids

        self.assertEqual(len(entries), 23)
        self.assertEqual(len(all_ids), 133)
        self.assertEqual(workbook_ids | supplemental_ids, all_ids)
        self.assertEqual(len(merged_ids), 1)
        self.assertEqual(len(new_ids), 22)
        self.assertEqual(
            {resource_id: by_id[resource_id]["check"] for resource_id in workbook_ids},
            previous_checks,
        )
        self.assertTrue(
            all(by_id[resource_id]["check"] == {} for resource_id in new_ids)
        )

    def test_repeated_real_generation_preserves_all_existing_checks(self):
        from tools.extract_catalog import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "course-catalog.json"
            markdown_path = root / "course-catalog.md"
            manifest_path = root / "source-manifest.json"
            args = [
                "--workbook", str(ROOT / "GST.CEN_Syllabus_JavaSpring_Dev2-3_v3.xlsx"),
                "--json", str(catalog_path),
                "--markdown", str(markdown_path),
                "--manifest", str(manifest_path),
                "--supplemental-sources", str(ROOT / "content" / "supplemental-sources.json"),
            ]
            self.assertEqual(main(args), 0)
            first = json.loads(manifest_path.read_text(encoding="utf-8"))
            expected_checks = {}
            for index, resource in enumerate(first["resources"], start=1):
                resource["check"] = {
                    "status": "ok",
                    "contentSha256": f"{index:064x}",
                }
                expected_checks[resource["resourceId"]] = resource["check"]
            manifest_path.write_text(json.dumps(first), encoding="utf-8")

            self.assertEqual(main(args), 0)
            second = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(len(second["resources"]), 133)
        self.assertEqual(
            {
                resource["resourceId"]: resource["check"]
                for resource in second["resources"]
            },
            expected_checks,
        )


class SupplementalSourceLoadTests(unittest.TestCase):
    """load_supplemental_sources: structural validation of the authored file."""

    def test_rejects_unsupported_schema_version(self):
        from tools.course_model import SupplementalSourceError, load_supplemental_sources

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplemental-sources.json"
            path.write_text(json.dumps({"schemaVersion": 2, "resources": []}), encoding="utf-8")
            with self.assertRaises(SupplementalSourceError):
                load_supplemental_sources(path)

    def test_rejects_missing_required_field(self):
        from tools.course_model import SupplementalSourceError, load_supplemental_sources

        entry = _supplemental_entry()
        del entry["publisher"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplemental-sources.json"
            _write_supplemental_file(path, [entry])
            with self.assertRaises(SupplementalSourceError):
                load_supplemental_sources(path)

    def test_rejects_malformed_url(self):
        from tools.course_model import SupplementalSourceError, load_supplemental_sources

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplemental-sources.json"
            _write_supplemental_file(path, [_supplemental_entry(url="not-a-url")])
            with self.assertRaises(SupplementalSourceError):
                load_supplemental_sources(path)

    def test_rejects_duplicate_url_within_file(self):
        """Test G: two entries whose URL normalizes the same must fail as an
        authoring error, not be silently deduplicated.
        """
        from tools.course_model import SupplementalSourceError, load_supplemental_sources

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplemental-sources.json"
            _write_supplemental_file(
                path,
                [
                    _supplemental_entry(url="https://example.com/dup#a", lesson_ids=("day-19",)),
                    _supplemental_entry(url="https://example.com/dup#b", lesson_ids=("day-20",)),
                ],
            )
            with self.assertRaises(SupplementalSourceError):
                load_supplemental_sources(path)

    def test_returns_normalized_entry_with_deterministic_resource_id(self):
        from tools.course_model import load_supplemental_sources

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplemental-sources.json"
            _write_supplemental_file(path, [_supplemental_entry(url="https://example.com/x#frag")])
            entries = load_supplemental_sources(path)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["resourceId"], resource_id("https://example.com/x#frag"))
        self.assertEqual(entries[0]["resourceId"], resource_id("https://example.com/x"))

    def test_empty_registry_returns_empty_list(self):
        """Test B (unit level): an empty resources array parses to []."""
        from tools.course_model import load_supplemental_sources

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplemental-sources.json"
            _write_supplemental_file(path, [])
            self.assertEqual(load_supplemental_sources(path), [])


class SupplementalSourceMergeTests(unittest.TestCase):
    """merge_supplemental_resources: identity/merge rules against a catalog."""

    def test_no_entries_is_a_no_op(self):
        """Test A (unit level): omitted/empty entries leave the catalog untouched."""
        from tools.course_model import merge_supplemental_resources

        catalog = _fixture_catalog()
        before = json.dumps(catalog, sort_keys=True)
        merge_supplemental_resources(catalog, [])
        after = json.dumps(catalog, sort_keys=True)
        self.assertEqual(before, after)

    def test_new_resource_is_added_and_linked_to_lesson(self):
        """Test C + D: a brand-new resource is created and its lessonId is
        added to both the resource and the lesson's resourceIds.
        """
        from tools.course_model import merge_supplemental_resources, resource_id

        catalog = _fixture_catalog()
        entry_url = "https://www.postgresql.org/docs/current/queries-table-expressions.html"
        entries = [_supplemental_entry(url=entry_url, lesson_ids=("day-20",))]

        merge_supplemental_resources(catalog, entries)

        new_id = resource_id(entry_url)
        day20 = next(lesson for lesson in catalog["lessons"] if lesson["id"] == "day-20")
        self.assertIn(new_id, day20["resourceIds"])
        new_resource = next(r for r in catalog["resources"] if r["id"] == new_id)
        self.assertEqual(new_resource["lessonIds"], ["day-20"])

    def test_existing_resource_new_lesson_id_merges_under_same_resource_id(self):
        """Test E: same normalized resource + new lessonId -> lessonIds are
        unioned, resourceId is unchanged, no second resource is created.
        """
        from tools.course_model import merge_supplemental_resources

        catalog = _fixture_catalog()
        existing_id = catalog["resources"][0]["id"]
        existing_url = catalog["resources"][0]["url"]
        entries = [
            _supplemental_entry(
                url=existing_url, title="Existing Resource", lesson_ids=("day-20",)
            )
        ]

        merge_supplemental_resources(catalog, entries)

        self.assertEqual(len(catalog["resources"]), 1, "must not create a second resource")
        resource = catalog["resources"][0]
        self.assertEqual(resource["id"], existing_id, "resourceId must not change")
        self.assertEqual(sorted(resource["lessonIds"]), ["day-19", "day-20"])
        day20 = next(lesson for lesson in catalog["lessons"] if lesson["id"] == "day-20")
        self.assertIn(existing_id, day20["resourceIds"])
        day19 = next(lesson for lesson in catalog["lessons"] if lesson["id"] == "day-19")
        self.assertIn(existing_id, day19["resourceIds"])

    def test_existing_resource_identical_lesson_id_is_idempotent(self):
        """Test E variant: re-merging the same (resource, lessonId) pair is a no-op."""
        from tools.course_model import merge_supplemental_resources

        catalog = _fixture_catalog()
        existing_url = catalog["resources"][0]["url"]
        entries = [
            _supplemental_entry(url=existing_url, title="Existing Resource", lesson_ids=("day-19",))
        ]

        merge_supplemental_resources(catalog, entries)

        self.assertEqual(len(catalog["resources"]), 1)
        self.assertEqual(catalog["resources"][0]["lessonIds"], ["day-19"])

    def test_conflicting_metadata_for_existing_resource_fails_loudly(self):
        """Test F: same normalized URL, but a title that doesn't match any
        existing label -> SupplementalSourceError, nothing is merged.
        """
        from tools.course_model import SupplementalSourceError, merge_supplemental_resources

        catalog = _fixture_catalog()
        existing_url = catalog["resources"][0]["url"]
        entries = [
            _supplemental_entry(
                url=existing_url, title="A Completely Different Title", lesson_ids=("day-20",)
            )
        ]

        with self.assertRaises(SupplementalSourceError):
            merge_supplemental_resources(catalog, entries)

        # nothing was merged: day-20 must not have picked up the resource
        day20 = next(lesson for lesson in catalog["lessons"] if lesson["id"] == "day-20")
        self.assertEqual(day20["resourceIds"], [])

    def test_unknown_lesson_id_fails_loudly(self):
        """Test H: a lessonId that doesn't exist in the catalog fails,
        without mutating the catalog.
        """
        from tools.course_model import SupplementalSourceError, merge_supplemental_resources

        catalog = _fixture_catalog()
        before = json.dumps(catalog, sort_keys=True)
        entries = [_supplemental_entry(lesson_ids=("day-99",))]

        with self.assertRaises(SupplementalSourceError):
            merge_supplemental_resources(catalog, entries)

        self.assertEqual(json.dumps(catalog, sort_keys=True), before)

    def test_existing_workbook_resource_id_is_never_changed_by_merge(self):
        """Test I (unit-level proxy): merging in an unrelated new resource
        must not touch the id or fields of a pre-existing resource.
        """
        from tools.course_model import merge_supplemental_resources

        catalog = _fixture_catalog()
        existing_before = copy.deepcopy(catalog["resources"][0])
        entries = [_supplemental_entry(url="https://example.com/unrelated", lesson_ids=("day-20",))]

        merge_supplemental_resources(catalog, entries)

        self.assertEqual(catalog["resources"][0], existing_before)
