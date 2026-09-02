from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tools.course_model import resource_id
from tools.validate_supplemental_sources import main, validate_supplemental_sources


def _catalog():
    existing_url = "https://example.test/existing-resource"
    existing_id = resource_id(existing_url)
    return {
        "lessons": [
            {"id": "day-01", "unitId": "unit-01", "outline": [], "resourceIds": [existing_id]},
            {"id": "day-02", "unitId": "unit-01", "outline": [], "resourceIds": []},
        ],
        "resources": [
            {
                "id": existing_id,
                "url": existing_url,
                "labels": ["Existing Resource"],
                "lessonIds": ["day-01"],
                "sourceRows": [],
                "occurrences": [],
            }
        ],
    }


def _entry(url="https://example.test/new-resource", title="New Resource",
           publisher="Example Publisher", lesson_ids=("day-02",),
           purpose="test fixture only"):
    return {
        "url": url,
        "title": title,
        "publisher": publisher,
        "lessonIds": list(lesson_ids),
        "purpose": purpose,
    }


def _write_registry(path, entries, schema_version=1):
    path.write_text(
        json.dumps({"schemaVersion": schema_version, "resources": entries}),
        encoding="utf-8",
    )


class ValidateSupplementalSourcesTests(unittest.TestCase):
    def test_accepts_a_valid_new_resource(self):
        catalog = _catalog()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplemental-sources.json"
            _write_registry(path, [_entry()])
            entries, errors = validate_supplemental_sources(path, catalog)

        self.assertEqual(errors, [])
        self.assertEqual(len(entries), 1)

    def test_accepts_an_empty_registry(self):
        catalog = _catalog()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplemental-sources.json"
            _write_registry(path, [])
            entries, errors = validate_supplemental_sources(path, catalog)

        self.assertEqual(errors, [])
        self.assertEqual(entries, [])

    def test_rejects_unsupported_schema_version(self):
        catalog = _catalog()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplemental-sources.json"
            _write_registry(path, [], schema_version=2)
            entries, errors = validate_supplemental_sources(path, catalog)

        self.assertEqual(entries, [])
        self.assertTrue(errors)

    def test_rejects_unknown_lesson_id(self):
        catalog = _catalog()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplemental-sources.json"
            _write_registry(path, [_entry(lesson_ids=("day-99",))])
            entries, errors = validate_supplemental_sources(path, catalog)

        self.assertEqual(entries, [])
        self.assertTrue(any("day-99" in error for error in errors))

    def test_rejects_conflicting_metadata_for_existing_resource(self):
        catalog = _catalog()
        existing_url = catalog["resources"][0]["url"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplemental-sources.json"
            _write_registry(
                path,
                [_entry(url=existing_url, title="A Totally Different Title", lesson_ids=("day-02",))],
            )
            entries, errors = validate_supplemental_sources(path, catalog)

        self.assertEqual(entries, [])
        self.assertTrue(errors)

    def test_rejects_duplicate_url_within_file(self):
        catalog = _catalog()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplemental-sources.json"
            _write_registry(
                path,
                [
                    _entry(url="https://example.test/dup#a", lesson_ids=("day-01",)),
                    _entry(url="https://example.test/dup#b", lesson_ids=("day-02",)),
                ],
            )
            entries, errors = validate_supplemental_sources(path, catalog)

        self.assertEqual(entries, [])
        self.assertTrue(errors)

    def test_does_not_mutate_the_catalog_it_is_given(self):
        catalog = _catalog()
        before = json.dumps(catalog, sort_keys=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "supplemental-sources.json"
            _write_registry(path, [_entry()])
            validate_supplemental_sources(path, catalog)

        self.assertEqual(json.dumps(catalog, sort_keys=True), before)


class CliTests(unittest.TestCase):
    def _write_catalog(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_catalog()), encoding="utf-8")

    def test_valid_registry_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "course-catalog.json"
            self._write_catalog(catalog_path)
            registry_path = root / "supplemental-sources.json"
            _write_registry(registry_path, [_entry()])

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--supplemental-sources", str(registry_path),
                    "--catalog", str(catalog_path),
                ])

        self.assertEqual(exit_code, 0)
        self.assertIn("PASS supplemental-sources resources=1", output.getvalue())

    def test_empty_production_registry_passes_with_zero_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "course-catalog.json"
            self._write_catalog(catalog_path)
            registry_path = root / "supplemental-sources.json"
            _write_registry(registry_path, [])

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--supplemental-sources", str(registry_path),
                    "--catalog", str(catalog_path),
                ])

        self.assertEqual(exit_code, 0)
        self.assertIn("PASS supplemental-sources resources=0", output.getvalue())

    def test_unknown_lesson_id_exits_nonzero_with_error_line(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "course-catalog.json"
            self._write_catalog(catalog_path)
            registry_path = root / "supplemental-sources.json"
            _write_registry(registry_path, [_entry(lesson_ids=("day-99",))])

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--supplemental-sources", str(registry_path),
                    "--catalog", str(catalog_path),
                ])

        self.assertEqual(exit_code, 1)
        lines = [line for line in output.getvalue().splitlines() if line]
        self.assertTrue(lines)
        self.assertTrue(all(line.startswith("ERROR ") for line in lines))
        self.assertTrue(any("day-99" in line for line in lines))

    def test_malformed_json_registry_reports_useful_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "course-catalog.json"
            self._write_catalog(catalog_path)
            registry_path = root / "supplemental-sources.json"
            registry_path.write_text("{not json", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--supplemental-sources", str(registry_path),
                    "--catalog", str(catalog_path),
                ])

        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR", output.getvalue())

    def test_missing_catalog_file_reports_useful_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry_path = root / "supplemental-sources.json"
            _write_registry(registry_path, [])

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--supplemental-sources", str(registry_path),
                    "--catalog", str(root / "course-catalog.json"),
                ])

        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR", output.getvalue())


if __name__ == "__main__":
    unittest.main()
