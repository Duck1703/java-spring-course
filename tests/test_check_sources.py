from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from tools.check_sources import fetch_resource, main


CHECKED_AT = "2026-08-22T16:30:00Z"
OK_BODY = b"""<!doctype html>
<html><head><title>Testing Beans</title><style>hidden style</style></head>
<body><h1>Spring Testing</h1><p>First paragraph.</p><p>Second <strong>paragraph</strong>.</p>
<ul><li>List item</li></ul><table><tr><th>Key</th><td>Value</td></tr></table>
<pre>assert bean != null</pre><script>hidden script</script></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def do_GET(self):
        self.server.requests.append((self.path, time.monotonic()))
        if self.path == "/moved":
            self.send_response(302)
            self.send_header("Location", "/ok")
            self.end_headers()
            return
        if self.path == "/cross":
            self.server.cross_barrier.wait()
            self.send_response(302)
            self.send_header("Location", self.server.cross_redirect_url)
            self.end_headers()
            return
        if self.path == "/missing":
            self._send(404, b"Missing", "text/plain; charset=utf-8")
            return
        if self.path == "/forbidden":
            self._send(403, b"Forbidden", "text/plain; charset=utf-8")
            return
        if self.path == "/error":
            self._send(500, b"Failure", "text/plain; charset=utf-8")
            return
        if self.path == "/binary":
            self._send(200, b"%PDF-1.7\x00binary", "application/pdf")
            return
        if self.path == "/large":
            self._send(200, b"x" * 100, "text/plain; charset=utf-8")
            return
        if self.path.startswith("/pace/"):
            self._send(200, self.path.encode(), "text/plain; charset=utf-8")
            return
        self._send(200, OK_BODY, "text/html; charset=utf-8")

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


class LocalServer:
    def __enter__(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.server.requests = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


class FetchTests(unittest.TestCase):
    def test_fetches_html_extracts_blocks_and_writes_atomic_evidence(self):
        with LocalServer() as server, tempfile.TemporaryDirectory() as directory:
            cache_dir = Path(directory) / ".course-cache" / "resources"
            result = fetch_resource(
                {
                    "resourceId": "res-ok",
                    "requestedUrl": f"{server.base_url}/ok",
                },
                cache_dir,
                CHECKED_AT,
            )

            cache_path = cache_dir / "res-ok.txt"
            cache_text = cache_path.read_text(encoding="utf-8")
            metadata = json.loads(
                (cache_dir / "res-ok.meta.json").read_text(encoding="utf-8")
            )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["httpStatus"], 200)
        self.assertEqual(result["checkedAt"], CHECKED_AT)
        self.assertEqual(result["contentSha256"], sha256(OK_BODY).hexdigest())
        self.assertIn("Testing Beans", cache_text)
        self.assertIn("Spring Testing", cache_text)
        self.assertIn("First paragraph.", cache_text)
        self.assertIn("List item", cache_text)
        self.assertIn("Key", cache_text)
        self.assertIn("assert bean != null", cache_text)
        self.assertNotIn("hidden script", cache_text)
        self.assertNotIn("hidden style", cache_text)
        self.assertEqual(metadata["check"], result)
        self.assertEqual(metadata["contentBytes"], result["contentBytes"])
        self.assertIn("Content-Type", metadata["headers"])
        self.assertFalse(list(cache_dir.glob("*.tmp")))

    def test_classifies_redirect_and_records_actual_final_url(self):
        with LocalServer() as server, tempfile.TemporaryDirectory() as directory:
            result = fetch_resource(
                {
                    "resourceId": "res-moved",
                    "requestedUrl": f"{server.base_url}/moved",
                },
                Path(directory),
                CHECKED_AT,
            )

        self.assertEqual(result["status"], "redirected")
        self.assertEqual(result["httpStatus"], 200)
        self.assertTrue(result["finalUrl"].endswith("/ok"))

    def test_maps_http_failures_and_writes_metadata_for_each_attempt(self):
        cases = [
            ("missing", "not_found", 404),
            ("forbidden", "blocked", 403),
            ("error", "http_error", 500),
        ]
        with LocalServer() as server, tempfile.TemporaryDirectory() as directory:
            cache_dir = Path(directory)
            for route, expected_status, expected_http_status in cases:
                with self.subTest(route=route):
                    result = fetch_resource(
                        {
                            "resourceId": f"res-{route}",
                            "requestedUrl": f"{server.base_url}/{route}",
                        },
                        cache_dir,
                        CHECKED_AT,
                    )
                    self.assertEqual(result["status"], expected_status)
                    self.assertEqual(result["httpStatus"], expected_http_status)
                    self.assertTrue(result["attempted"])
                    self.assertTrue((cache_dir / f"res-{route}.meta.json").is_file())

    def test_marks_binary_content_unreadable_without_text_cache(self):
        with LocalServer() as server, tempfile.TemporaryDirectory() as directory:
            cache_dir = Path(directory)
            stale_text_path = cache_dir / "res-binary.txt"
            stale_text_path.write_text("stale readable body", encoding="utf-8")
            result = fetch_resource(
                {
                    "resourceId": "res-binary",
                    "requestedUrl": f"{server.base_url}/binary",
                },
                cache_dir,
                CHECKED_AT,
            )
            text_cache_exists = stale_text_path.exists()
            metadata_exists = (cache_dir / "res-binary.meta.json").exists()

        self.assertEqual(result["status"], "content_unreadable")
        self.assertEqual(result["httpStatus"], 200)
        self.assertIsNone(result["cacheText"])
        self.assertFalse(text_cache_exists)
        self.assertTrue(metadata_exists)

    def test_bounds_body_and_records_truncation(self):
        with LocalServer() as server, tempfile.TemporaryDirectory() as directory:
            with patch("tools.check_sources.MAX_BYTES", 32):
                result = fetch_resource(
                    {
                        "resourceId": "res-large",
                        "requestedUrl": f"{server.base_url}/large",
                    },
                    Path(directory),
                    CHECKED_AT,
                )

        self.assertEqual(result["contentBytes"], 32)
        self.assertTrue(result["truncated"])

    def test_invalid_url_records_error_and_metadata_without_request(self):
        with tempfile.TemporaryDirectory() as directory:
            cache_dir = Path(directory)
            result = fetch_resource(
                {"resourceId": "res-invalid", "requestedUrl": "not a URL"},
                cache_dir,
                CHECKED_AT,
            )
            metadata_exists = (cache_dir / "res-invalid.meta.json").exists()

        self.assertEqual(result["status"], "invalid")
        self.assertIn("ValueError", result["error"])
        self.assertTrue(metadata_exists)

    def test_network_exception_is_recorded(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        host, port = server.server_address
        server.server_close()
        with tempfile.TemporaryDirectory() as directory:
            result = fetch_resource(
                {
                    "resourceId": "res-network",
                    "requestedUrl": f"http://{host}:{port}/ok",
                },
                Path(directory),
                CHECKED_AT,
            )

        self.assertEqual(result["status"], "network_error")
        self.assertIsNotNone(result["error"])
        self.assertIn("Error", result["error"])


class CliTests(unittest.TestCase):
    def test_real_mode_updates_both_json_files_and_renders_vietnamese_status(self):
        with LocalServer() as server, tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "course-catalog.json"
            manifest_path = root / "content" / "source-manifest.json"
            markdown_path = root / "course-catalog.md"
            cache_dir = root / ".course-cache" / "resources"
            catalog = _catalog(f"{server.base_url}/ok")
            manifest = _manifest(f"{server.base_url}/ok")
            _write_json(catalog_path, catalog)
            _write_json(manifest_path, manifest)

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "--catalog",
                        str(catalog_path),
                        "--manifest",
                        str(manifest_path),
                        "--markdown",
                        str(markdown_path),
                        "--cache-dir",
                        str(cache_dir),
                        "--max-workers",
                        "8",
                        "--per-host-delay",
                        "0",
                    ]
                )

            updated_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            updated_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")

        catalog_resource = updated_catalog["resources"][0]
        manifest_resource = updated_manifest["resources"][0]
        self.assertEqual(exit_code, 0)
        self.assertEqual(updated_catalog["generatedAt"], "2026-08-22T15:55:10Z")
        self.assertEqual(updated_manifest["generatedAt"], "2026-08-22T15:55:10Z")
        self.assertEqual(catalog_resource["labels"], ["Testing reference"])
        self.assertEqual(catalog_resource["check"], manifest_resource["check"])
        self.assertTrue(catalog_resource["check"]["attempted"])
        self.assertIn("truy xuất được (HTTP 200)", markdown)
        self.assertNotIn("đã đọc", markdown)
        self.assertIn("attempted=1", output.getvalue())
        self.assertEqual([path for path, _ in server.server.requests], ["/ok"])

    def test_same_host_requests_are_serialized_and_paced(self):
        with LocalServer() as server, tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            urls = [f"{server.base_url}/pace/{index}" for index in range(3)]
            catalog = _catalog_without_lessons(urls)
            manifest = _manifest_for_urls(urls)
            catalog_path = root / "catalog.json"
            manifest_path = root / "manifest.json"
            _write_json(catalog_path, catalog)
            _write_json(manifest_path, manifest)

            main(
                [
                    "--catalog",
                    str(catalog_path),
                    "--manifest",
                    str(manifest_path),
                    "--markdown",
                    str(root / "catalog.md"),
                    "--cache-dir",
                    str(root / "cache"),
                    "--max-workers",
                    "4",
                    "--per-host-delay",
                    "0.05",
                ]
            )

            starts = sorted(stamp for path, stamp in server.server.requests if path.startswith("/pace/"))

        self.assertEqual(len(starts), 3)
        self.assertTrue(
            all(later - earlier >= 0.04 for earlier, later in zip(starts, starts[1:])),
            starts,
        )

    def test_redirect_follow_up_get_obeys_same_host_pacing(self):
        with LocalServer() as server, tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            urls = [
                f"{server.base_url}/moved",
                f"{server.base_url}/pace/after-redirect",
            ]
            catalog_path = root / "catalog.json"
            manifest_path = root / "manifest.json"
            _write_json(catalog_path, _catalog_without_lessons(urls))
            _write_json(manifest_path, _manifest_for_urls(urls))

            main(
                [
                    "--catalog",
                    str(catalog_path),
                    "--manifest",
                    str(manifest_path),
                    "--markdown",
                    str(root / "catalog.md"),
                    "--cache-dir",
                    str(root / "cache"),
                    "--max-workers",
                    "4",
                    "--per-host-delay",
                    "0.05",
                ]
            )

            starts = sorted(stamp for _, stamp in server.server.requests)

        self.assertEqual(len(starts), 3)
        self.assertTrue(
            all(later - earlier >= 0.04 for earlier, later in zip(starts, starts[1:])),
            starts,
        )

    def test_cross_host_redirects_do_not_deadlock_workers(self):
        with (
            LocalServer() as first,
            LocalServer() as second,
            tempfile.TemporaryDirectory() as directory,
        ):
            barrier = threading.Barrier(2)
            first.server.cross_barrier = barrier
            second.server.cross_barrier = barrier
            first.server.cross_redirect_url = f"{second.base_url}/ok"
            second.server.cross_redirect_url = f"{first.base_url}/ok"
            urls = [f"{first.base_url}/cross", f"{second.base_url}/cross"]
            root = Path(directory)
            catalog_path = root / "catalog.json"
            manifest_path = root / "manifest.json"
            _write_json(catalog_path, _catalog_without_lessons(urls))
            _write_json(manifest_path, _manifest_for_urls(urls))
            command = [
                sys.executable,
                str(Path(__file__).resolve().parents[1] / "tools" / "check_sources.py"),
                "--catalog",
                str(catalog_path),
                "--manifest",
                str(manifest_path),
                "--markdown",
                str(root / "catalog.md"),
                "--cache-dir",
                str(root / "cache"),
                "--max-workers",
                "2",
                "--per-host-delay",
                "0.05",
            ]

            try:
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=3,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                self.fail("cross-host redirects deadlocked worker host locks")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PASS attempted=2", completed.stdout)

    def test_report_only_prints_complete_filtered_table_without_fetching(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            manifest = _manifest("https://invalid.example/never-requested")
            manifest["resources"][0]["check"] = {
                "attempted": True,
                "status": "blocked",
                "error": "HTTPError: blocked",
            }
            _write_json(manifest_path, manifest)
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                exit_code = main(
                    [
                        "--report-only",
                        "--manifest",
                        str(manifest_path),
                        "--status",
                        "blocked,not_found",
                    ]
                )

        report = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("resourceId\trequestedUrl\tstatus\terror", report)
        self.assertIn("res-test", report)
        self.assertIn("https://invalid.example/never-requested", report)
        self.assertIn("blocked", report)
        self.assertIn("count=1", report)


def _catalog(url):
    return {
        "schemaVersion": 1,
        "generatedAt": "2026-08-22T15:55:10Z",
        "source": {"workbook": "fixture.xlsx", "sheet": "JavaSpring_Schedule"},
        "units": [
            {
                "id": "unit-01",
                "number": 1,
                "title": "Testing",
                "group": "java",
                "lessonIds": ["day-01"],
                "sourceRows": [3],
            }
        ],
        "lessons": [
            {
                "id": "day-01",
                "label": "Day 1",
                "unitId": "unit-01",
                "group": "java",
                "title": "Testing",
                "outline": [],
                "objectives": [],
                "durationMinutes": 60,
                "activities": [],
                "resourceIds": ["res-test"],
                "sourceRows": [3],
            }
        ],
        "resources": [
            {
                "id": "res-test",
                "url": url,
                "labels": ["Testing reference"],
                "lessonIds": ["day-01"],
                "sourceRows": [3],
                "occurrences": [
                    {"lessonId": "day-01", "row": 3, "label": "Testing reference"}
                ],
            }
        ],
    }


def _manifest(url):
    return {
        "schemaVersion": 1,
        "generatedAt": "2026-08-22T15:55:10Z",
        "source": {"workbook": "fixture.xlsx", "sheet": "JavaSpring_Schedule"},
        "resources": [
            {
                "resourceId": "res-test",
                "requestedUrl": url,
                "labelVariants": ["Testing reference"],
                "lessonIds": ["day-01"],
                "unitIds": ["unit-01"],
                "relevantOutline": [],
                "assignedBatch": "java-foundations",
                "check": {},
            }
        ],
    }


def _catalog_without_lessons(urls):
    catalog = _catalog(urls[0])
    catalog["units"] = []
    catalog["lessons"] = []
    catalog["resources"] = [
        {
            "id": f"res-{index}",
            "url": url,
            "labels": [f"Resource {index}"],
            "lessonIds": [],
            "sourceRows": [],
            "occurrences": [],
        }
        for index, url in enumerate(urls)
    ]
    return catalog


def _manifest_for_urls(urls):
    manifest = _manifest(urls[0])
    manifest["resources"] = [
        {
            "resourceId": f"res-{index}",
            "requestedUrl": url,
            "labelVariants": [f"Resource {index}"],
            "lessonIds": [],
            "unitIds": [],
            "relevantOutline": [],
            "assignedBatch": "java-foundations",
            "check": {},
        }
        for index, url in enumerate(urls)
    ]
    return manifest


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
