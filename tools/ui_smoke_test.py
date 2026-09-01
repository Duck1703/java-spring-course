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
import base64
import http.server
import json
import os
import re
import shutil
import socket
import socketserver
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request
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


def ws_build_frame(payload: bytes, mask: bytes) -> bytes:
    """Build a single unfragmented, masked WebSocket text frame (RFC 6455).

    Client-to-server frames must be masked. `mask` is taken as a parameter
    (rather than generated internally) so this stays a pure, unit-testable
    function; callers pass `os.urandom(4)` in production.
    """
    length = len(payload)
    header = bytearray([0x81])  # FIN=1, opcode=1 (text)
    if length <= 125:
        header.append(0x80 | length)
    elif length <= 65535:
        header.append(0x80 | 126)
        header += struct.pack(">H", length)
    else:
        header.append(0x80 | 127)
        header += struct.pack(">Q", length)
    header += mask
    masked_payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return bytes(header) + masked_payload


def ws_parse_frame(data: bytes) -> tuple[int, bytes]:
    """Parse one complete WebSocket frame already assembled in memory.

    Returns (opcode, payload). Handles both masked (client) and unmasked
    (server) frames with 7-bit, 16-bit, or 64-bit length encodings. Does not
    handle fragmentation across multiple frames — CDP responses in practice
    fit in a single frame for the calls this tool makes.
    """
    b1, b2 = data[0], data[1]
    opcode = b1 & 0x0F
    masked = bool(b2 & 0x80)
    length = b2 & 0x7F
    offset = 2
    if length == 126:
        length = struct.unpack(">H", data[offset:offset + 2])[0]
        offset += 2
    elif length == 127:
        length = struct.unpack(">Q", data[offset:offset + 8])[0]
        offset += 8
    if masked:
        mask = data[offset:offset + 4]
        offset += 4
        raw = data[offset:offset + length]
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(raw))
    else:
        payload = data[offset:offset + length]
    return opcode, payload


class CDPSession:
    """A minimal Chrome DevTools Protocol client over a raw WebSocket.

    No selenium/playwright/websocket-client is available in this
    environment, so the handshake and frame (de)serialization are
    implemented directly against `socket` using only the stdlib. This is
    enough to drive `Emulation.setDeviceMetricsOverride`, which is the only
    reliable way to get an exact 390x844 CSS viewport on this platform:
    headless Chrome/Edge's `--window-size` flag is subject to an OS/window
    manager minimum window size that inflates small requested sizes (~390px
    floors around ~500-520px here), silently invalidating "mobile" checks.
    """

    def __init__(self, debug_port: int, connect_timeout: float = 10.0):
        with urllib.request.urlopen(
            f"http://127.0.0.1:{debug_port}/json/list", timeout=connect_timeout
        ) as resp:
            targets = json.loads(resp.read().decode())
        page_target = next(t for t in targets if t.get("type") == "page")
        ws_url = page_target["webSocketDebuggerUrl"]
        # ws://127.0.0.1:<port>/devtools/page/<id> -> just need host/path.
        path = ws_url.split(f":{debug_port}", 1)[1]

        self._sock = socket.create_connection(("127.0.0.1", debug_port), timeout=connect_timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        handshake = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: 127.0.0.1:{debug_port}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self._sock.sendall(handshake.encode())
        resp_bytes = b""
        while b"\r\n\r\n" not in resp_bytes:
            resp_bytes += self._sock.recv(4096)
        self._next_id = 0

    def _recv_n(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("CDP WebSocket closed unexpectedly")
            buf += chunk
        return buf

    def _recv_frame(self) -> tuple[int, bytes]:
        head = self._recv_n(2)
        length = head[1] & 0x7F
        extra = 0
        if length == 126:
            extra = 2
        elif length == 127:
            extra = 8
        rest_len_bytes = self._recv_n(extra) if extra else b""
        if extra == 2:
            length = struct.unpack(">H", rest_len_bytes)[0]
        elif extra == 8:
            length = struct.unpack(">Q", rest_len_bytes)[0]
        masked = bool(head[1] & 0x80)
        mask = self._recv_n(4) if masked else b""
        raw = self._recv_n(length)
        full_frame = bytes(head) + rest_len_bytes + mask + raw
        return ws_parse_frame(full_frame)

    def call(self, method: str, params: dict | None = None, timeout: float = 15.0) -> dict:
        self._next_id += 1
        msg_id = self._next_id
        payload = json.dumps({"id": msg_id, "method": method, "params": params or {}}).encode()
        self._sock.sendall(ws_build_frame(payload, os.urandom(4)))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            opcode, frame_payload = self._recv_frame()
            if opcode != 1:
                continue
            msg = json.loads(frame_payload.decode())
            if msg.get("id") == msg_id:
                return msg
        raise TimeoutError(f"CDP call {method} timed out")

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass


def capture_mobile_via_cdp(
    browser: str,
    profile_arg: str,
    url: str,
    screenshot: str | Path | None,
    width: int = 390,
    height: int = 844,
    timeout: float = 30.0,
) -> tuple[str, str]:
    """Load `url` at a *true* 390x844 CSS viewport via CDP device-metrics
    override, returning (self_test_status_text, self_test_data_status).

    `--window-size` alone cannot be trusted at this width on this platform
    (see CDPSession docstring), so this drives Emulation directly instead of
    reusing the desktop `--window-size` + `--dump-dom` path.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        debug_port = probe.getsockname()[1]

    cmd = [
        browser, "--headless=new", "--disable-gpu",
        f"--remote-debugging-port={debug_port}", profile_arg,
        "--window-size=1024,900", "about:blank",
    ]
    proc = subprocess.Popen(cmd)
    try:
        deadline = time.monotonic() + timeout
        session = None
        last_error: Exception | None = None
        while time.monotonic() < deadline and session is None:
            try:
                session = CDPSession(debug_port)
            except (OSError, StopIteration, ConnectionError) as exc:
                last_error = exc
                time.sleep(0.2)
        if session is None:
            raise RuntimeError(f"could not open CDP session: {last_error}")

        try:
            session.call("Page.enable")
            session.call("Emulation.setDeviceMetricsOverride", {
                "width": width, "height": height, "deviceScaleFactor": 1,
                "mobile": True, "screenWidth": width, "screenHeight": height,
            })
            session.call("Page.navigate", {"url": url})

            status_text = ""
            data_status = ""
            poll_deadline = time.monotonic() + timeout
            while time.monotonic() < poll_deadline:
                result = session.call("Runtime.evaluate", {
                    "expression": (
                        "(function(){var el = document.getElementById('self-test-results');"
                        "return el ? JSON.stringify({text: el.textContent, "
                        "status: el.getAttribute('data-status')}) : '';})()"
                    ),
                    "returnByValue": True,
                })
                value = result.get("result", {}).get("result", {}).get("value") or ""
                if value:
                    parsed = json.loads(value)
                    if parsed.get("status"):
                        status_text = parsed.get("text") or ""
                        data_status = parsed.get("status") or ""
                        break
                time.sleep(0.2)

            if screenshot is not None:
                shot = session.call("Page.captureScreenshot", {"format": "png"})
                data = shot.get("result", {}).get("data")
                if data:
                    Path(screenshot).write_bytes(base64.b64decode(data))

            return status_text, data_status
        finally:
            session.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def run_browser(browser: str, args: list[str], url: str, timeout: int = 90) -> str:
    cmd = [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
           "--virtual-time-budget=6000", "--dump-dom", url] + args
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"browser exited {proc.returncode}: {proc.stderr[:500]}")
    return proc.stdout


def build_screenshot_command(
    browser: str,
    profile_arg: str,
    viewport_args: list[str],
    screenshot: str | Path,
    url: str,
) -> list[str]:
    return [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--virtual-time-budget=6000",
        profile_arg,
        *viewport_args,
        f"--screenshot={screenshot}",
        url,
    ]


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
                label = "desktop" if name == "desktop" else "mobile"
                shot = None if args.skip_screenshots else output_dir / f"{name}.png"

                if name == "mobile":
                    # Plain --window-size cannot be trusted at ~390px on this
                    # platform (OS/window-manager floor inflates it to
                    # ~500-520px CSS px — see CDPSession docstring), so drive
                    # a true 390x844 CSS viewport via CDP device emulation
                    # instead of the desktop dump-dom + --window-size path.
                    status_text, data_status = capture_mobile_via_cdp(
                        browser, profile_arg, url, shot, width=390, height=844,
                    )
                    ok_results = data_status == "pass"
                    count_ok = re.match(r'PASS (\d+)/(\d+)', status_text or "")
                    counts = f"{count_ok.group(1)}/{count_ok.group(2)}" if count_ok else "?/?"
                    total = int(count_ok.group(2)) if count_ok else 0
                    passed_n = int(count_ok.group(1)) if count_ok else 0
                    viewport_label = "390,844"
                    screenshot_ok = shot is None or (shot.exists())
                    if not screenshot_ok:
                        failures.append(f"{label}: screenshot failed (no CDP screenshot data)")
                else:
                    dom = run_browser(browser, [profile_arg] + extra, url)
                    ok_results = 'id="self-test-results" data-status="pass"' in dom
                    count_ok = re.search(r'id="self-test-results"[^>]*>PASS (\d+)/(\d+)<', dom)
                    counts = f"{count_ok.group(1)}/{count_ok.group(2)}" if count_ok else "?/?"
                    total = int(count_ok.group(2)) if count_ok else 0
                    passed_n = int(count_ok.group(1)) if count_ok else 0
                    viewport_label = extra[0].split('=')[1]

                # The spec requires at least the 13 listed assertions; the
                # suite may include extra structural guards (e.g. hint panel
                # existence) — all must pass.
                if ok_results and total >= 13 and passed_n == total:
                    print(f"PASS {label} selftest={counts} viewport={viewport_label}")
                else:
                    failures.append(f"{label}: self-test results bad (status tag present={ok_results}, counts={counts})")
                    if name == "mobile":
                        if status_text:
                            failures.append(f"  got: {status_text!r}")
                    else:
                        snippet = re.search(r'id="self-test-results"[^>]*>([^<]*)<', dom)
                        if snippet:
                            failures.append(f"  got: {snippet.group(1)!r}")
                        for err in re.findall(r'SELFTEST #\d+ FAILED: [^<]*', dom):
                            failures.append(f"  {err}")

                if name != "mobile" and not args.skip_screenshots:
                    shot_cmd = build_screenshot_command(
                        browser, profile_arg, extra, shot, url
                    )
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
