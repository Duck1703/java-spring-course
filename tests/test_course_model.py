import json
import tempfile
import unittest
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

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
                    "outline": ["JVM Architecture"],
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
        self.assertIn("- **Nhóm:** Java", markdown)
        self.assertIn("[JVM \\[Architecture\\]](https://example.com/a_(b))", markdown)
        self.assertIn("chưa kiểm tra", markdown)

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
