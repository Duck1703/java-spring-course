"""Chrome headless UI smoke test for the built index.html.

Serves the workspace over localhost, loads the app with ?selftest=1 at
desktop and mobile viewports, requires a passing in-browser self-test
(`PASS 13/13`), captures screenshots, and runs static accessibility /
hygiene checks against the built HTML.

Usage:
    python tools/ui_smoke_test.py --file index.html --output-dir .course-cache/ui
"""
from __future__ import annotations

import argparse
import http.server
import re
import shutil
import socket
import socketserver
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHROME_CANDIDATES = [
    r"C:/Program Files/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
    r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    r"C:/Program Files/Microsoft/Edge/Application/msedge.exe",
]


def find_browser() -> str:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    found = shutil.which("chrome") or shutil.which("msedge")
    if found:
        return found
    raise SystemExit("ERROR: no Chrome/Edge executable found")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:  # silence per-request logging
        pass


def serve_root_free_port() -> tuple[socketserver.TCPServer, int]:
    """ThreadingHTTPServer rooted at the workspace on an ephemeral port."""
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), QuietHandler)
    return server, port


def run_browser(browser: str, args: list[str], url: str, timeout: int = 90) -> str:
    cmd = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--virtual-time-budget=6000", "--dump-dom", url] + args
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"browser exited {proc.returncode}: {proc.stderr[:500]}")
    return proc.stdout


SCREENSHOT_ARGS = {
    "desktop": ["--window-size=1440,1000"],
    "mobile": ["--window-size=390,844"],
}

STATIC_REQUIREMENTS = [
    ('lang="vi"', 'html lang="vi"'),
    ('name="viewport"', "viewport meta"),
    ("skip-link", "skip-link"),
    ('"#main-content"', "main-content anchor/element reference"),
    ('aria-live', "aria-live toast region"),
    ("prefers-reduced-motion", "prefers-reduced-motion support"),
    ("focus-visible", "focus-visible styling"),
]


def static_checks(html: str) -> list[str]:
    problems: list[str] = []
    for needle, label in STATIC_REQUIREMENTS:
        if needle not in html:
            problems.append(f"missing {label} ({needle})")

    # Runtime-created hooks live in the app script — check they are created.
    runtime_labels = [
        "'main-content'",
        "'Danh mục khóa học'",
        "'Tìm kiếm bài học'",
        "Tiến độ khóa học",
        '"Sao chép mã mẫu vào clipboard"',
        "'Mở danh mục'",
    ]
    for needle in runtime_labels:
        if needle not in html:
            problems.append(f"missing runtime control label {needle}")

    # Inline event handlers must not appear in static markup
    for handler in re.finditer(r'\son[a-z]+\s*=', html):
        ctx = html[max(0, handler.start() - 40):handler.end() + 40]
        # Allow JS string content inside <script> bodies
        before = html[:handler.start()]
        last_script_open = before.rfind("<script")
        last_script_close = before.rfind("</script>")
        if last_script_open > last_script_close:
            continue  # inside script body — fine
        problems.append(f"inline event handler in markup: ...{ctx!r}...")

    # Duplicate static IDs
    ids = re.findall(r'id="([^"]+)"', html)
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        problems.append(f"duplicate static IDs: {sorted(dupes)[:8]}")

    # External stylesheets/scripts
    for m in re.finditer(r'<(link|script)\b[^>]*\b(src|href)="(https?:)?//[^"]*"', html):
        problems.append(f"external dependency tag: {m.group(0)[:80]}")

    # Mixed content (http:// subresources)
    for m in re.finditer(r'(src|href)="http://[^"]*"', html):
        problems.append(f"insecure http:// URL in chrome: {m.group(0)[:80]}")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", default="index.html")
    parser.add_argument("--output-dir", default=".course-cache/ui")
    parser.add_argument("--skip-screenshots", action="store_true")
    args = parser.parse_args()

    page_path = ROOT / args.file
    if not page_path.exists():
        print(f"ERROR: {page_path} not found — run tools/build_site.py first")
        return 2
    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    html = page_path.read_text(encoding="utf-8")
    problems = static_checks(html)

    browser = find_browser()
    server, port = serve_root_free_port()
    rel = "/" + str(page_path.relative_to(ROOT)).replace("\\", "/")
    base_url = f"http://127.0.0.1:{port}{rel}"
    server_thread_ready = True

    failures: list[str] = []
    try:
        import threading
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        with tempfile.TemporaryDirectory(prefix="ui-smoke-profile-") as profile:
            profile_arg = f"--user-data-dir={profile}"

            for name, extra in SCREENSHOT_ARGS.items():
                url = f"{base_url}?selftest=1"
                dom = run_browser(browser, [profile_arg] + extra, url)
                ok_results = 'id="self-test-results" data-status="pass"' in dom
                count_ok = re.search(r'id="self-test-results"[^>]*>PASS (\d+)/(\d+)<', dom)
                counts = f"{count_ok.group(1)}/{count_ok.group(2)}" if count_ok else "?/?"
                label = "desktop" if name == "desktop" else "mobile"
                total = int(count_ok.group(2)) if count_ok else 0
                passed_n = int(count_ok.group(1)) if count_ok else 0
                # The spec requires at least the 13 listed assertions; the
                # suite may include extra structural guards (e.g. hint panel
                # existence) — all must pass.
                if ok_results and total >= 13 and passed_n == total:
                    print(f"PASS {label} selftest={counts} viewport={extra[0].split('=')[1]}")
                else:
                    failures.append(f"{label}: self-test results bad (status tag present={ok_results}, counts={counts})")
                    snippet = re.search(r'id="self-test-results"[^>]*>([^<]*)<', dom)
                    if snippet:
                        failures.append(f"  got: {snippet.group(1)!r}")
                    for err in re.findall(r'SELFTEST #\d+ FAILED: [^<]*', dom):
                        failures.append(f"  {err}")

                if not args.skip_screenshots:
                    shot = output_dir / f"{name}.png"
                    shot_cmd = [browser, "--headless=new", "--disable-gpu",
                                "--virtual-time-budget=6000", profile_arg]
                    shot_cmd += extra[:-1] + [f"--screenshot={shot}", url]
                    proc = subprocess.run(shot_cmd, capture_output=True, text=True, timeout=90)
                    if proc.returncode != 0 or not shot.exists():
                        failures.append(f"{label}: screenshot failed ({proc.stderr[:200]})")
        print(f"PASS screenshots={output_dir / 'desktop.png'},{output_dir / 'mobile.png'}"
              if not failures and not args.skip_screenshots else
              ("" if args.skip_screenshots or failures else ""))
    except Exception as exc:  # noqa: BLE001
        failures.append(f"harness error: {exc}")
    finally:
        server.shutdown()
        server.server_close()

    if problems:
        print("\nStatic checks failed:")
        for p in problems:
            print(f"  - {p}")
    if failures:
        print("\nBrowser checks failed:")
        for f in failures:
            print(f"  - {f}")
    if problems or failures:
        return 1
    print("PASS static accessibility + hygiene checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
