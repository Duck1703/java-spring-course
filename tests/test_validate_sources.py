from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_sources import BATCHES, main, validate_source_notes


CHECKED_AT = "2026-08-22T16:33:26.013701Z"
HASH_A = "a" * 64
HASH_B = "b" * 64
ROOT = Path(__file__).resolve().parents[1]


def _manifest(resources):
    return {
        "schemaVersion": 1,
        "generatedAt": CHECKED_AT,
        "source": {"workbook": "fixture.xlsx", "sheet": "JavaSpring_Schedule"},
        "resources": resources,
    }


def _check(status="ok", http_status=200, final_url=None, content_sha256=HASH_A,
           cache_text=None, error=None):
    return {
        "attempted": True,
        "checkedAt": CHECKED_AT,
        "status": status,
        "httpStatus": http_status,
        "finalUrl": final_url,
        "contentType": "text/html",
        "contentBytes": 100,
        "contentSha256": content_sha256,
        "cacheText": cache_text,
        "truncated": False,
        "error": error,
    }


def _manifest_resource(resource_id, url="https://example.test/a", batch="java-foundations",
                        lesson_ids=("day-01",), check=None):
    check = check if check is not None else _check(final_url=url)
    if check.get("finalUrl") is None:
        check = dict(check, finalUrl=url)
    return {
        "resourceId": resource_id,
        "requestedUrl": url,
        "labelVariants": ["Example label"],
        "lessonIds": list(lesson_ids),
        "unitIds": ["unit-01"],
        "relevantOutline": ["Outline topic"],
        "assignedBatch": batch,
        "check": check,
    }


def _access_from_check(check):
    return {
        "status": check["status"],
        "httpStatus": check["httpStatus"],
        "finalUrl": check["finalUrl"],
        "contentSha256": check["contentSha256"],
    }


def _read_note(resource_id, url="https://example.test/a", batch="java-foundations",
               lesson_ids=("day-01",), access=None, facts=None, method="cache",
               fallback_evidence=None):
    facts = facts if facts is not None else [
        {"topic": "Outline topic", "summary": "Tóm tắt ngắn gọn bằng tiếng Việt.",
         "locator": "Heading A"}
    ]
    return {
        "resourceId": resource_id,
        "batch": batch,
        "requestedUrl": url,
        "lessonIds": list(lesson_ids),
        "access": access if access is not None else _access_from_check(_check(final_url=url)),
        "read": {
            "status": "read",
            "method": method,
            "pageTitle": "Example Page",
            "relevantHeadings": ["Heading A"],
            "topics": ["Outline topic"],
            "facts": facts,
            "limitation": None,
        },
        "fallbackEvidence": fallback_evidence,
    }


def _unavailable_note(resource_id, url, batch, lesson_ids, access, limitation="not read"):
    return {
        "resourceId": resource_id,
        "batch": batch,
        "requestedUrl": url,
        "lessonIds": list(lesson_ids),
        "access": access,
        "read": {
            "status": "unavailable",
            "method": None,
            "pageTitle": None,
            "relevantHeadings": [],
            "topics": [],
            "facts": [],
            "limitation": limitation,
        },
        "fallbackEvidence": None,
    }


class ValidateSourceNotesTests(unittest.TestCase):
    def test_accepts_a_complete_valid_read_record(self):
        resource = _manifest_resource("res-a")
        manifest = _manifest([resource])
        note = _read_note("res-a")

        errors = validate_source_notes(manifest, [note])

        self.assertEqual(errors, [])

    def test_rejects_read_status_without_facts(self):
        resource = _manifest_resource("res-a")
        manifest = _manifest([resource])
        note = _read_note("res-a", facts=[])
        note["read"]["relevantHeadings"] = []
        note["read"]["topics"] = []

        errors = validate_source_notes(manifest, [note])

        self.assertTrue(any("res-a" in error and "fact" in error for error in errors))

    def test_rejects_read_claim_for_blocked_access_without_fallback_evidence(self):
        check = _check(status="blocked", http_status=403, final_url="https://example.test/a",
                        content_sha256=None)
        resource = _manifest_resource("res-a", check=check)
        manifest = _manifest([resource])
        note = _read_note(
            "res-a",
            access=_access_from_check(check),
            facts=[{"topic": "x", "summary": "x", "locator": "x"}],
        )

        errors = validate_source_notes(manifest, [note])

        self.assertTrue(any("res-a" in error for error in errors))

    def test_rejects_duplicate_resource_note_across_batches(self):
        resource = _manifest_resource("res-a")
        manifest = _manifest([resource])
        note_1 = _read_note("res-a")
        note_2 = _read_note("res-a")

        errors = validate_source_notes(manifest, [note_1, note_2])

        self.assertTrue(any("res-a" in error and "duplicate" in error for error in errors))

    def test_rejects_missing_resource_note(self):
        manifest = _manifest(
            [_manifest_resource("res-a"), _manifest_resource("res-b")]
        )
        note = _read_note("res-a")

        errors = validate_source_notes(manifest, [note])

        self.assertTrue(any("res-b" in error for error in errors))

    def test_rejects_resource_id_absent_from_manifest(self):
        manifest = _manifest([_manifest_resource("res-a")])
        note = _read_note("res-a")
        unknown_note = _read_note("res-unknown")

        errors = validate_source_notes(manifest, [note, unknown_note])

        self.assertTrue(any("res-unknown" in error for error in errors))

    def test_rejects_requested_url_mismatch(self):
        resource = _manifest_resource("res-a", url="https://example.test/a")
        manifest = _manifest([resource])
        note = _read_note("res-a", url="https://example.test/different")

        errors = validate_source_notes(manifest, [note])

        self.assertTrue(any("res-a" in error and "requestedUrl" in error for error in errors))

    def test_rejects_access_metadata_mismatch_without_fallback(self):
        check = _check(final_url="https://example.test/a")
        resource = _manifest_resource("res-a", check=check)
        manifest = _manifest([resource])
        note = _read_note("res-a")
        note["access"]["contentSha256"] = HASH_B

        errors = validate_source_notes(manifest, [note])

        self.assertTrue(any("res-a" in error and "access" in error for error in errors))

    def test_accepts_access_metadata_mismatch_with_webfetch_fallback_evidence(self):
        check = _check(status="blocked", http_status=403, final_url="https://example.test/a",
                        content_sha256=None)
        resource = _manifest_resource("res-a", check=check)
        manifest = _manifest([resource])
        note = _read_note(
            "res-a",
            access={"status": "blocked", "httpStatus": 403,
                    "finalUrl": "https://example.test/a", "contentSha256": None},
            method="webfetch-fallback",
            fallback_evidence={
                "requestedUrl": "https://example.test/a",
                "finalUrl": "https://example.test/a",
                "retrievedAt": CHECKED_AT,
                "contentSha256": HASH_B,
            },
        )

        errors = validate_source_notes(manifest, [note])

        self.assertEqual(errors, [])

    def test_rejects_incomplete_webfetch_fallback_evidence(self):
        check = _check(status="blocked", http_status=403, final_url="https://example.test/a",
                        content_sha256=None)
        resource = _manifest_resource("res-a", check=check)
        manifest = _manifest([resource])
        note = _read_note(
            "res-a",
            access={"status": "blocked", "httpStatus": 403,
                    "finalUrl": "https://example.test/a", "contentSha256": None},
            method="webfetch-fallback",
            fallback_evidence={
                "requestedUrl": "https://example.test/a",
                "finalUrl": "https://example.test/a",
                "retrievedAt": CHECKED_AT,
                "contentSha256": "not-a-hash",
            },
        )

        errors = validate_source_notes(manifest, [note])

        self.assertTrue(any("res-a" in error and "sha256" in error for error in errors))

    def test_rejects_non_read_status_with_facts_present(self):
        resource = _manifest_resource("res-a")
        manifest = _manifest([resource])
        note = _unavailable_note(
            "res-a", "https://example.test/a", "java-foundations", ["day-01"],
            _access_from_check(_check(final_url="https://example.test/a")),
        )
        note["read"]["facts"] = [{"topic": "x", "summary": "x", "locator": "x"}]

        errors = validate_source_notes(manifest, [note])

        self.assertTrue(any("res-a" in error and "facts" in error for error in errors))

    def test_accepts_honest_unavailable_record(self):
        check = _check(status="not_found", http_status=404,
                        final_url="https://example.test/a", content_sha256=None)
        resource = _manifest_resource("res-a", check=check)
        manifest = _manifest([resource])
        note = _unavailable_note(
            "res-a", "https://example.test/a", "java-foundations", ["day-01"],
            _access_from_check(check), limitation="HTTP 404: not found",
        )

        errors = validate_source_notes(manifest, [note])

        self.assertEqual(errors, [])

    def test_rejects_lesson_id_set_mismatch(self):
        resource = _manifest_resource("res-a", lesson_ids=("day-01", "day-02"))
        manifest = _manifest([resource])
        note = _read_note("res-a", lesson_ids=("day-01",))

        errors = validate_source_notes(manifest, [note])

        self.assertTrue(any("res-a" in error and "lessonIds" in error for error in errors))

    def test_rejects_batch_missing_assigned_manifest_resource(self):
        manifest = _manifest([
            _manifest_resource("res-a", batch="java-foundations"),
            _manifest_resource("res-b", batch="java-foundations", url="https://example.test/b"),
        ])
        note = _read_note("res-a")

        errors = validate_source_notes(manifest, [note], batch="java-foundations")

        self.assertTrue(any("res-b" in error for error in errors))

    def test_batch_scope_ignores_other_batches_missing_notes(self):
        manifest = _manifest([
            _manifest_resource("res-a", batch="java-foundations"),
            _manifest_resource("res-b", batch="java-advanced", url="https://example.test/b"),
        ])
        note = _read_note("res-a")

        errors = validate_source_notes(manifest, [note], batch="java-foundations")

        self.assertEqual(errors, [])

    def test_rejects_copied_run_over_300_characters(self):
        cached_sentence = "Đây là một đoạn văn bản mẫu rất dài được sao chép nguyên văn. " * 6
        with tempfile.TemporaryDirectory() as directory:
            cache_path = Path(directory) / "res-a.txt"
            cache_path.write_text(cached_sentence, encoding="utf-8")
            check = _check(final_url="https://example.test/a", cache_text=str(cache_path))
            resource = _manifest_resource("res-a", check=check)
            manifest = _manifest([resource])
            note = _read_note(
                "res-a",
                access=_access_from_check(check),
                facts=[{"topic": "Outline topic", "summary": cached_sentence[:400],
                        "locator": "Heading A"}],
            )

            errors = validate_source_notes(manifest, [note])

        self.assertTrue(any("res-a" in error and "300" in error for error in errors))

    def test_accepts_concise_paraphrase_even_with_matching_cache(self):
        cached_sentence = "Đây là một đoạn văn bản mẫu rất dài được sao chép nguyên văn. " * 6
        with tempfile.TemporaryDirectory() as directory:
            cache_path = Path(directory) / "res-a.txt"
            cache_path.write_text(cached_sentence, encoding="utf-8")
            check = _check(final_url="https://example.test/a", cache_text=str(cache_path))
            resource = _manifest_resource("res-a", check=check)
            manifest = _manifest([resource])
            note = _read_note(
                "res-a",
                access=_access_from_check(check),
                facts=[{"topic": "Outline topic", "summary": "Tóm tắt ngắn gọn, diễn giải lại.",
                        "locator": "Heading A"}],
            )

            errors = validate_source_notes(manifest, [note])

        self.assertEqual(errors, [])

    def test_missing_cache_for_unavailable_resource_is_not_an_error(self):
        check = _check(status="network_error", http_status=None,
                        final_url="https://example.test/a", content_sha256=None,
                        cache_text=None, error="URLError: refused")
        resource = _manifest_resource("res-a", check=check)
        manifest = _manifest([resource])
        note = _unavailable_note(
            "res-a", "https://example.test/a", "java-foundations", ["day-01"],
            _access_from_check(check), limitation="network_error: URLError: refused",
        )

        errors = validate_source_notes(manifest, [note])

        self.assertEqual(errors, [])

    def test_malformed_record_does_not_crash_and_becomes_an_error(self):
        manifest = _manifest([_manifest_resource("res-a")])

        errors = validate_source_notes(manifest, ["not-a-dict", {"batch": "java-foundations"}])

        self.assertTrue(all(isinstance(error, str) for error in errors))
        self.assertTrue(len(errors) >= 2)

    def test_rejects_unknown_read_status_value(self):
        resource = _manifest_resource("res-a")
        manifest = _manifest([resource])
        note = _read_note("res-a")
        note["read"]["status"] = "skimmed"
        note["read"]["facts"] = []

        errors = validate_source_notes(manifest, [note])

        self.assertTrue(any("res-a" in error and "status" in error for error in errors))

    def test_errors_are_sorted_and_deterministic(self):
        manifest = _manifest([
            _manifest_resource("res-a"),
            _manifest_resource("res-b", url="https://example.test/b"),
        ])

        errors = validate_source_notes(manifest, [])

        self.assertEqual(errors, sorted(errors))
        self.assertEqual(len(errors), 2)


class ProductionIntegrationTests(unittest.TestCase):
    def test_canonical_manifest_and_source_notes_pass_strict_validation(self):
        from tools.validate_sources import _load_notes_dir

        manifest = json.loads(
            (ROOT / "content" / "source-manifest.json").read_text(encoding="utf-8")
        )
        notes, loader_errors = _load_notes_dir(ROOT / "content" / "source-notes")

        errors = loader_errors + validate_source_notes(manifest, notes)

        self.assertEqual(len(manifest["resources"]), 133)
        self.assertEqual(errors, [])


class CliTests(unittest.TestCase):
    def test_list_required_works_without_any_notes_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            manifest = _manifest([
                _manifest_resource("res-a", batch="java-foundations"),
                _manifest_resource("res-b", batch="java-advanced", url="https://example.test/b"),
            ])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            notes_dir = root / "source-notes"

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--manifest", str(manifest_path),
                    "--notes-dir", str(notes_dir),
                    "--batch", "java-foundations",
                    "--list-required",
                ])

        self.assertEqual(exit_code, 0)
        self.assertFalse(notes_dir.exists())
        report = output.getvalue()
        self.assertIn("res-a", report)
        self.assertNotIn("res-b", report)
        self.assertIn("count=1", report)

    def test_invalid_notes_exit_nonzero_with_one_line_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            manifest = _manifest([_manifest_resource("res-a")])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            notes_dir = root / "source-notes"
            notes_dir.mkdir()
            (notes_dir / "java-foundations.json").write_text(
                json.dumps([_read_note("res-a", facts=[])]), encoding="utf-8"
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--manifest", str(manifest_path),
                    "--notes-dir", str(notes_dir),
                ])

        self.assertEqual(exit_code, 1)
        lines = [line for line in output.getvalue().splitlines() if line]
        self.assertTrue(lines)
        self.assertTrue(all(line.startswith("ERROR ") for line in lines))

    def test_malformed_json_notes_file_reports_useful_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            manifest = _manifest([_manifest_resource("res-a")])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            notes_dir = root / "source-notes"
            notes_dir.mkdir()
            (notes_dir / "java-foundations.json").write_text("{not json", encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--manifest", str(manifest_path),
                    "--notes-dir", str(notes_dir),
                ])

        self.assertEqual(exit_code, 1)
        self.assertIn("java-foundations", output.getvalue())

    def test_notes_file_batch_mismatch_with_containing_file_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            manifest = _manifest([_manifest_resource("res-a", batch="java-foundations")])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            notes_dir = root / "source-notes"
            notes_dir.mkdir()
            misplaced_note = _read_note("res-a", batch="java-advanced")
            (notes_dir / "java-foundations.json").write_text(
                json.dumps([misplaced_note]), encoding="utf-8"
            )

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--manifest", str(manifest_path),
                    "--notes-dir", str(notes_dir),
                ])

        self.assertEqual(exit_code, 1)
        report = output.getvalue()
        self.assertIn("res-a", report)
        self.assertIn("java-foundations.json", report)

    def test_complete_six_batch_fixtures_print_expected_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            resources = []
            notes_by_batch = {batch: [] for batch in BATCHES}
            for index, batch in enumerate(BATCHES):
                resource_id = f"res-{index}"
                url = f"https://example.test/{index}"
                resource = _manifest_resource(resource_id, url=url, batch=batch)
                resources.append(resource)
                notes_by_batch[batch].append(_read_note(resource_id, url=url, batch=batch))
            manifest = _manifest(resources)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            notes_dir = root / "source-notes"
            notes_dir.mkdir()
            for batch, records in notes_by_batch.items():
                (notes_dir / f"{batch}.json").write_text(json.dumps(records), encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--manifest", str(manifest_path),
                    "--notes-dir", str(notes_dir),
                ])

        self.assertEqual(exit_code, 0)
        self.assertIn(
            f"PASS source-notes resources={len(BATCHES)} read={len(BATCHES)} "
            f"unavailable=0 batches={len(BATCHES)}",
            output.getvalue(),
        )

    def test_list_required_survives_non_utf8_stdout_encoding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            resource = _manifest_resource("res-a", batch="java-foundations")
            resource["relevantOutline"] = ["Operators → Control Flow ≥ threshold"]
            manifest = _manifest([resource])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            notes_dir = root / "source-notes"

            raw = io.BytesIO()
            wrapper = io.TextIOWrapper(raw, encoding="cp1252", errors="strict", newline="")
            with contextlib.redirect_stdout(wrapper):
                exit_code = main([
                    "--manifest", str(manifest_path),
                    "--notes-dir", str(notes_dir),
                    "--batch", "java-foundations",
                    "--list-required",
                ])
            wrapper.flush()

        self.assertEqual(exit_code, 0)

    def test_write_report_includes_every_resource_once_and_labels_honestly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            ok_check = _check(final_url="https://example.test/a")
            blocked_check = _check(status="blocked", http_status=403,
                                    final_url="https://example.test/b", content_sha256=None)
            resources = []
            notes_by_batch = {batch: [] for batch in BATCHES}
            resources.append(_manifest_resource("res-a", url="https://example.test/a",
                                                  batch="java-foundations", check=ok_check))
            notes_by_batch["java-foundations"].append(
                _read_note("res-a", url="https://example.test/a",
                           batch="java-foundations", access=_access_from_check(ok_check))
            )
            resources.append(_manifest_resource("res-b", url="https://example.test/b",
                                                  batch="java-advanced", check=blocked_check))
            notes_by_batch["java-advanced"].append(
                _unavailable_note("res-b", "https://example.test/b", "java-advanced",
                                   ["day-01"], _access_from_check(blocked_check),
                                   limitation="HTTP 403: blocked")
            )
            for index, batch in enumerate(BATCHES):
                if batch in {"java-foundations", "java-advanced"}:
                    continue
                resource_id = f"res-extra-{index}"
                url = f"https://example.test/extra-{index}"
                resources.append(_manifest_resource(resource_id, url=url, batch=batch))
                notes_by_batch[batch].append(_read_note(resource_id, url=url, batch=batch))

            manifest = _manifest(resources)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            notes_dir = root / "source-notes"
            notes_dir.mkdir()
            for batch, records in notes_by_batch.items():
                (notes_dir / f"{batch}.json").write_text(json.dumps(records), encoding="utf-8")
            report_path = root / "report.md"

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([
                    "--manifest", str(manifest_path),
                    "--notes-dir", str(notes_dir),
                    "--write-report", str(report_path),
                ])

            report = report_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(report.count("res-a"), 1)
        self.assertEqual(report.count("res-b"), 1)
        self.assertIn("| res-a |", report)
        self.assertIn("read |", report)
        self.assertIn("| res-b |", report)
        self.assertIn("unavailable |", report)
        self.assertNotIn("| res-b | https://example.test/b | blocked | read |", report)


if __name__ == "__main__":
    unittest.main()
