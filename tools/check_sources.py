from __future__ import annotations

import argparse
import copy
import json
import os
import re
import ssl
import sys
import tempfile
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPHandler,
    HTTPSHandler,
    Request,
    build_opener,
    urlopen,
)

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.course_model import normalize_url, render_catalog_markdown


MAX_BYTES = 5 * 1024 * 1024
USER_AGENT = "JavaSpringCourseBuilder/1.0 (educational source verification)"
TIMEOUT_SECONDS = 20
MAX_WORKERS = 4
DEFAULT_PER_HOST_DELAY = 0.5
ACCESS_STATUSES = (
    "ok",
    "redirected",
    "blocked",
    "not_found",
    "http_error",
    "network_error",
    "content_unreadable",
    "invalid",
)
CHECK_STATUSES = ("unchecked",) + ACCESS_STATUSES
IGNORED_HTML_TAGS = {"script", "style", "svg", "noscript"}
BLOCK_HTML_TAGS = {
    "title",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "li",
    "tr",
    "pre",
    "code",
}
SAFE_RESOURCE_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self._ignored_depth = 0
        self._capture = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in IGNORED_HTML_TAGS:
            self._ignored_depth += 1
            return
        if not self._ignored_depth and tag in BLOCK_HTML_TAGS and self._capture is None:
            self._capture = {"tag": tag, "parts": []}

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in IGNORED_HTML_TAGS:
            if self._ignored_depth:
                self._ignored_depth -= 1
            return
        if self._ignored_depth or self._capture is None:
            return
        if tag == self._capture["tag"]:
            text = _collapse_whitespace("".join(self._capture["parts"]))
            if text:
                self.blocks.append(text)
            self._capture = None

    def handle_data(self, data):
        if not self._ignored_depth and self._capture is not None:
            self._capture["parts"].append(data)

    def close(self):
        super().close()
        if self._capture is not None:
            text = _collapse_whitespace("".join(self._capture["parts"]))
            if text:
                self.blocks.append(text)
            self._capture = None


class _HostPacer:
    def __init__(self, delay_seconds: float):
        self.delay_seconds = delay_seconds
        self._registry_lock = threading.Lock()
        self._locks_by_host = {}
        self._last_request_by_host = {}

    @contextmanager
    def request_slot(self, url: str):
        host = _request_host(url)
        with self._registry_lock:
            host_lock = self._locks_by_host.setdefault(host, threading.RLock())
        with host_lock:
            with self._registry_lock:
                last_request = self._last_request_by_host.get(host)
            if last_request is not None:
                remaining = self.delay_seconds - (time.monotonic() - last_request)
                if remaining > 0:
                    time.sleep(remaining)
            with self._registry_lock:
                self._last_request_by_host[host] = time.monotonic()
            try:
                yield
            finally:
                with self._registry_lock:
                    self._last_request_by_host[host] = time.monotonic()


class _PacedResponse:
    def __init__(self, response, request_slot):
        self._response = response
        self._request_slot = request_slot

    def __getattr__(self, name):
        return getattr(self._response, name)

    def close(self):
        request_slot = self._request_slot
        self._request_slot = None
        try:
            return self._response.close()
        finally:
            if request_slot is not None:
                request_slot.__exit__(None, None, None)


class _PacedHTTPHandler(HTTPHandler):
    def __init__(self, pacer):
        super().__init__()
        self.pacer = pacer

    def http_open(self, request):
        return _open_paced_response(
            self.pacer,
            request.full_url,
            lambda: super(_PacedHTTPHandler, self).http_open(request),
        )


class _PacedHTTPSHandler(HTTPSHandler):
    def __init__(self, pacer):
        super().__init__()
        self.pacer = pacer

    def https_open(self, request):
        return _open_paced_response(
            self.pacer,
            request.full_url,
            lambda: super(_PacedHTTPSHandler, self).https_open(request),
        )


def _open_paced_response(pacer, url, open_response):
    request_slot = pacer.request_slot(url)
    request_slot.__enter__()
    try:
        return _PacedResponse(open_response(), request_slot)
    except BaseException:
        request_slot.__exit__(*sys.exc_info())
        raise


_FETCH_STATE = threading.local()


def fetch_resource(resource: dict, cache_dir: Path, checked_at: str) -> dict:
    resource_id = str(resource.get("resourceId", ""))
    requested_url = str(resource.get("requestedUrl", ""))
    result = {
        "attempted": True,
        "checkedAt": checked_at,
        "status": "invalid",
        "httpStatus": None,
        "finalUrl": None,
        "contentType": None,
        "contentBytes": None,
        "contentSha256": None,
        "cacheText": None,
        "truncated": False,
        "error": None,
    }
    headers = {}
    metadata_path = None

    try:
        cache_dir = Path(cache_dir)
        cache_stem = _cache_stem(resource_id)
        text_path = cache_dir / f"{cache_stem}.txt"
        metadata_path = cache_dir / f"{cache_stem}.meta.json"
        cache_dir.mkdir(parents=True, exist_ok=True)
        text_path.unlink(missing_ok=True)
    except Exception as error:
        result["status"] = "content_unreadable"
        _record_local_error(result, error)
        return _finish_fetch_result(
            metadata_path, resource_id, requested_url, headers, result
        )

    try:
        _validate_http_url(requested_url)
        request = Request(requested_url, headers={"User-Agent": USER_AGENT}, method="GET")
        response_error = None
        try:
            opener = getattr(_FETCH_STATE, "opener", None)
            if opener is None:
                response = urlopen(request, timeout=TIMEOUT_SECONDS)
            else:
                response = opener.open(request, timeout=TIMEOUT_SECONDS)
        except HTTPError as error:
            response = error
            response_error = error
        except (URLError, TimeoutError, ssl.SSLError, OSError) as error:
            result["status"] = "network_error"
            result["error"] = _format_error(error)
            return _finish_fetch_result(
                metadata_path, resource_id, requested_url, headers, result
            )
        except Exception as error:
            result["status"] = "network_error"
            result["error"] = _format_error(error)
            return _finish_fetch_result(
                metadata_path, resource_id, requested_url, headers, result
            )

        with closing(response):
            status_code = response.getcode()
            final_url = response.geturl()
            headers = {key: value for key, value in response.headers.items()}
            content_type = response.headers.get("Content-Type")
            body, truncated = _read_bounded(response)

        result.update(
            {
                "httpStatus": status_code,
                "finalUrl": final_url,
                "contentType": content_type,
                "contentBytes": len(body),
                "contentSha256": sha256(body).hexdigest(),
                "truncated": truncated,
            }
        )
        if response_error is not None:
            result["error"] = _format_error(response_error)
        result["status"] = _classify_status(
            status_code, requested_url, final_url
        )

        if _is_text_content(content_type):
            try:
                extracted_text = _extract_text(body, content_type)
                _atomic_write_text(text_path, extracted_text)
                result["cacheText"] = text_path.as_posix()
            except Exception as error:
                result["error"] = _join_errors(result["error"], error)
                if result["status"] in {"ok", "redirected"}:
                    result["status"] = "content_unreadable"
        elif result["status"] in {"ok", "redirected"}:
            result["status"] = "content_unreadable"
            media_type = _media_type(content_type) or "unknown"
            result["error"] = f"UnsupportedContentType: {media_type}"
    except (TypeError, ValueError) as error:
        result["status"] = "invalid"
        result["error"] = _format_error(error)
    except Exception as error:
        result["status"] = "network_error"
        result["error"] = _format_error(error)

    return _finish_fetch_result(
        metadata_path, resource_id, requested_url, headers, result
    )


def _finish_fetch_result(
    metadata_path, resource_id, requested_url, headers, result
):
    if metadata_path is not None:
        try:
            _write_metadata(
                metadata_path, resource_id, requested_url, headers, result
            )
        except Exception as error:
            _record_local_error(result, error)
    return result


def _record_local_error(result, error):
    result["error"] = _join_errors(result["error"], error)
    if result["status"] in {"ok", "redirected"}:
        result["status"] = "content_unreadable"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch course sources and record access evidence"
    )
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--max-workers", type=int, default=MAX_WORKERS)
    parser.add_argument(
        "--per-host-delay", type=float, default=DEFAULT_PER_HOST_DELAY
    )
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument(
        "--status",
        help=(
            "Comma-separated check statuses to fetch or report. Real mode defaults "
            "to unchecked; use an explicit status to retry previously checked resources."
        ),
    )
    args = parser.parse_args(argv)

    manifest = _read_json(args.manifest)
    selected_statuses = _parse_statuses(
        args.status,
        CHECK_STATUSES,
        parser,
        default=ACCESS_STATUSES if args.report_only else ("unchecked",),
    )
    if args.report_only:
        return _report_only(manifest, selected_statuses)

    missing = [
        name
        for name, value in (
            ("--catalog", args.catalog),
            ("--markdown", args.markdown),
            ("--cache-dir", args.cache_dir),
        )
        if value is None
    ]
    if missing:
        parser.error(f"the following arguments are required: {', '.join(missing)}")
    if args.max_workers < 1:
        parser.error("--max-workers must be at least 1")
    if args.per_host_delay < 0:
        parser.error("--per-host-delay must not be negative")

    catalog = _read_json(args.catalog)
    catalog_by_id = _validate_inputs(catalog, manifest)
    all_resources = manifest["resources"]
    resources = [
        resource for resource in all_resources
        if _resource_check_status(resource) in selected_statuses
    ]
    checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    pacer = _HostPacer(args.per_host_delay)
    worker_count = min(args.max_workers, MAX_WORKERS)

    def fetch_with_pacing(resource):
        _FETCH_STATE.opener = build_opener(
            _PacedHTTPHandler(pacer),
            _PacedHTTPSHandler(pacer),
        )
        try:
            return fetch_resource(resource, args.cache_dir, checked_at)
        finally:
            del _FETCH_STATE.opener

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        checks = list(executor.map(fetch_with_pacing, resources))

    for resource, check in zip(resources, checks):
        resource["check"] = check

    for resource in all_resources:
        catalog_by_id[resource["resourceId"]]["check"] = copy.deepcopy(
            resource.get("check") or {}
        )

    _atomic_write_json(args.manifest, manifest)
    _atomic_write_json(args.catalog, catalog)
    _atomic_write_text(args.markdown, render_catalog_markdown(catalog))

    counts = Counter(check["status"] for check in checks)
    status_summary = ",".join(
        f"{status}={counts[status]}" for status in ACCESS_STATUSES
    )
    print(
        f"PASS attempted={len(checks)} skipped={len(all_resources) - len(checks)} "
        f"status_counts={status_summary}"
    )
    return 0


def _resource_check_status(resource):
    status = (resource.get("check") or {}).get("status")
    return status if status in ACCESS_STATUSES else "unchecked"


def _parse_statuses(raw_statuses, allowed_statuses, parser, default):
    if raw_statuses:
        statuses = [status.strip() for status in raw_statuses.split(",") if status.strip()]
    else:
        statuses = list(default)
    unknown = [status for status in statuses if status not in allowed_statuses]
    if unknown:
        parser.error(f"unknown status: {', '.join(unknown)}")
    return set(statuses)


def _report_only(manifest, statuses):
    selected = [
        resource
        for resource in manifest.get("resources", [])
        if _resource_check_status(resource) in statuses
    ]
    print("resourceId\trequestedUrl\tstatus\terror")
    for resource in selected:
        check = resource.get("check", {})
        values = (
            resource.get("resourceId"),
            resource.get("requestedUrl"),
            _resource_check_status(resource),
            check.get("error"),
        )
        print("\t".join(_table_cell(value) for value in values))
    print(f"count={len(selected)}")
    return 0


def _validate_inputs(catalog, manifest):
    catalog_resources = catalog.get("resources")
    manifest_resources = manifest.get("resources")
    if not isinstance(catalog_resources, list) or not isinstance(
        manifest_resources, list
    ):
        raise ValueError("catalog and manifest must contain resource lists")
    catalog_by_id = _unique_records(catalog_resources, "id", "catalog")
    manifest_by_id = _unique_records(manifest_resources, "resourceId", "manifest")
    if set(catalog_by_id) != set(manifest_by_id):
        raise ValueError("catalog and manifest resource IDs do not match")
    requested_urls = []
    for resource_id, manifest_resource in manifest_by_id.items():
        requested_url = manifest_resource.get("requestedUrl")
        catalog_url = catalog_by_id[resource_id].get("url")
        if requested_url != catalog_url:
            raise ValueError(f"URL mismatch for resource {resource_id}")
        requested_urls.append(requested_url)
    if len(set(requested_urls)) != len(requested_urls):
        raise ValueError("manifest requested URLs must be globally unique")
    return catalog_by_id


def _unique_records(records, key, label):
    by_id = {}
    for record in records:
        record_id = record.get(key)
        if not record_id:
            raise ValueError(f"{label} resource is missing {key}")
        if record_id in by_id:
            raise ValueError(f"duplicate {label} resource ID: {record_id}")
        by_id[record_id] = record
    return by_id


def _read_bounded(response):
    body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        return body[:MAX_BYTES], True
    content_length = response.headers.get("Content-Length")
    try:
        truncated = content_length is not None and int(content_length) > len(body)
    except ValueError:
        truncated = False
    return body, truncated


def _classify_status(http_status, requested_url, final_url):
    if http_status in {401, 403, 429}:
        return "blocked"
    if http_status in {404, 410}:
        return "not_found"
    if http_status is None or not 200 <= http_status < 300:
        return "http_error"
    if normalize_url(requested_url) != normalize_url(final_url):
        return "redirected"
    return "ok"


def _is_text_content(content_type):
    return _media_type(content_type) in {
        "text/html",
        "application/xhtml+xml",
        "text/plain",
    }


def _media_type(content_type):
    if not content_type:
        return None
    return content_type.split(";", 1)[0].strip().lower()


def _extract_text(body, content_type):
    charset = "utf-8"
    charset_match = re.search(
        r"(?:^|;)\s*charset\s*=\s*[\"']?([^;\"']+)",
        content_type or "",
        re.IGNORECASE,
    )
    if charset_match:
        charset = charset_match.group(1).strip()
    text = body.decode(charset, errors="replace")
    if _media_type(content_type) in {"text/html", "application/xhtml+xml"}:
        parser = _TextExtractor()
        parser.feed(text)
        parser.close()
        return "\n".join(parser.blocks) + ("\n" if parser.blocks else "")
    lines = [_collapse_whitespace(line) for line in text.splitlines()]
    blocks = [line for line in lines if line]
    return "\n".join(blocks) + ("\n" if blocks else "")


def _collapse_whitespace(value):
    return re.sub(r"\s+", " ", value).strip()


def _validate_http_url(url):
    parts = urlsplit(url)
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("requestedUrl must be an absolute HTTP(S) URL")


def _request_host(url):
    parts = urlsplit(url)
    if parts.hostname:
        return f"{parts.hostname.lower()}:{parts.port or _default_port(parts.scheme)}"
    return normalize_url(url)


def _default_port(scheme):
    return 443 if scheme.lower() == "https" else 80


def _cache_stem(resource_id):
    if resource_id and SAFE_RESOURCE_ID_RE.fullmatch(resource_id):
        return resource_id
    digest = sha256(resource_id.encode("utf-8")).hexdigest()[:12]
    return f"invalid-{digest}"


def _format_error(error):
    message = str(error).strip()
    return f"{error.__class__.__name__}: {message}" if message else error.__class__.__name__


def _join_errors(existing, error):
    formatted = _format_error(error)
    return f"{existing}; {formatted}" if existing else formatted


def _write_metadata(path, resource_id, requested_url, headers, result):
    metadata = {
        "resourceId": resource_id,
        "requestedUrl": requested_url,
        "headers": headers,
        "contentBytes": result["contentBytes"],
        "contentSha256": result["contentSha256"],
        "truncated": result["truncated"],
        "check": result,
    }
    _atomic_write_json(path, metadata)


def _atomic_write_json(path, value):
    content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    _atomic_write_text(path, content)


def _atomic_write_text(path, content):
    _atomic_write_bytes(Path(path), content.encode("utf-8"))


def _atomic_write_bytes(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _table_cell(value):
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
