from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


BATCHES = (
    "java-foundations",
    "java-advanced",
    "spring-core-web",
    "data-security",
    "production",
    "project-final",
)

READ_STATUSES = {"read", "unavailable"}
SUCCESSFUL_ACCESS_STATUSES = {"ok", "redirected"}
ACCESS_MIRROR_FIELDS = ("status", "httpStatus", "finalUrl", "contentSha256")
COPIED_RUN_THRESHOLD = 300
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def validate_source_notes(manifest: dict, notes: list, batch: str | None = None) -> list[str]:
    """Validate source-note records against manifest/check evidence.

    `manifest` is the Task 2 resource manifest (access/check truth). `notes`
    is the flattened list of source-note records loaded from one or more
    batch files. `batch`, when given, scopes the required-coverage check to
    only the manifest resources assigned to that batch; other loaded notes
    are still structurally validated.
    """
    errors = []
    manifest_by_id = _index_manifest(manifest)

    seen_ids = set()
    notes_by_id = {}
    for note in notes:
        if not isinstance(note, dict):
            errors.append(_error("unknown", batch or "unknown", "source note record must be an object"))
            continue

        resource_id = note.get("resourceId")
        note_batch = note.get("batch")
        label_batch = note_batch if isinstance(note_batch, str) and note_batch else "unknown"

        if not isinstance(resource_id, str) or not resource_id:
            errors.append(_error("unknown", label_batch, "source note record is missing resourceId"))
            continue

        if resource_id in seen_ids:
            errors.append(_error(resource_id, label_batch, "duplicate source note for resource"))
            continue
        seen_ids.add(resource_id)

        manifest_resource = manifest_by_id.get(resource_id)
        if manifest_resource is None:
            errors.append(_error(resource_id, label_batch, "resource is not present in manifest"))
            continue

        notes_by_id[resource_id] = note
        errors.extend(_validate_note(note, manifest_resource, label_batch))

    errors.extend(_validate_coverage(manifest_by_id, notes_by_id, batch))

    return sorted(errors)


def _index_manifest(manifest: dict) -> dict:
    resources = manifest.get("resources") if isinstance(manifest, dict) else None
    by_id = {}
    if not isinstance(resources, list):
        return by_id
    for resource in resources:
        if not isinstance(resource, dict):
            continue
        resource_id = resource.get("resourceId")
        if isinstance(resource_id, str) and resource_id:
            by_id[resource_id] = resource
    return by_id


def _validate_note(note: dict, manifest_resource: dict, batch: str) -> list[str]:
    errors = []
    resource_id = manifest_resource["resourceId"]
    assigned_batch = manifest_resource.get("assignedBatch")

    if batch != assigned_batch:
        errors.append(
            _error(resource_id, batch,
                   f"batch does not match manifest assignedBatch {assigned_batch!r}")
        )

    if note.get("requestedUrl") != manifest_resource.get("requestedUrl"):
        errors.append(_error(resource_id, batch, "requestedUrl does not match manifest"))

    lesson_ids = note.get("lessonIds")
    manifest_lesson_ids = manifest_resource.get("lessonIds") or []
    if not isinstance(lesson_ids, list) or set(lesson_ids) != set(manifest_lesson_ids):
        errors.append(_error(resource_id, batch, "lessonIds do not match manifest lesson ID set"))

    check = manifest_resource.get("check") or {}

    access = note.get("access")
    if not isinstance(access, dict):
        errors.append(_error(resource_id, batch, "access metadata is missing"))
        access = {}

    read = note.get("read")
    if not isinstance(read, dict):
        errors.append(_error(resource_id, batch, "read record is missing"))
        read = {}

    method = read.get("method")
    is_fallback = method == "webfetch-fallback"

    if not is_fallback:
        mismatched = [
            field for field in ACCESS_MIRROR_FIELDS if access.get(field) != check.get(field)
        ]
        if mismatched:
            errors.append(
                _error(resource_id, batch,
                       f"access metadata does not match latest check: {', '.join(mismatched)}")
            )

    read_status = read.get("status")
    if read_status not in READ_STATUSES:
        errors.append(_error(resource_id, batch, "read status must be 'read' or 'unavailable'"))

    facts = read.get("facts")
    facts = facts if isinstance(facts, list) else None

    if read_status == "read":
        errors.extend(_validate_read_completeness(read, facts, resource_id, batch))

        check_status = check.get("status")
        if check_status not in SUCCESSFUL_ACCESS_STATUSES and not is_fallback:
            errors.append(
                _error(resource_id, batch,
                       "read status=read for failed access requires webfetch-fallback evidence")
            )

        if is_fallback:
            errors.extend(
                _validate_fallback_evidence(note.get("fallbackEvidence"), resource_id, batch)
            )

        if facts:
            cache_text = _load_cache_text(check.get("cacheText"))
            if cache_text is not None:
                errors.extend(_validate_copied_runs(facts, cache_text, resource_id, batch))
    else:
        if facts:
            errors.append(_error(resource_id, batch, "non-read status must not include facts"))

    return errors


def _validate_read_completeness(read: dict, facts, resource_id: str, batch: str) -> list[str]:
    errors = []
    page_title = read.get("pageTitle")
    headings = read.get("relevantHeadings")
    topics = read.get("topics")

    if not isinstance(page_title, str) or not page_title:
        errors.append(_error(resource_id, batch, "read status requires a nonempty page title"))
    if not isinstance(headings, list) or not headings:
        errors.append(_error(resource_id, batch, "read status requires at least one relevant heading"))
    if not isinstance(topics, list) or not topics:
        errors.append(_error(resource_id, batch, "read status requires at least one topic"))

    if not facts:
        errors.append(_error(resource_id, batch, "read status requires at least one fact"))
        return errors

    for fact in facts:
        if not isinstance(fact, dict) or not fact.get("summary"):
            errors.append(_error(resource_id, batch, "read status requires a nonempty fact summary"))
            continue
        if not fact.get("locator"):
            errors.append(_error(resource_id, batch, "read status requires at least one fact locator"))
        if not fact.get("topic"):
            errors.append(_error(resource_id, batch, "read status requires a fact topic"))

    return errors


def _validate_fallback_evidence(evidence, resource_id: str, batch: str) -> list[str]:
    errors = []
    if not isinstance(evidence, dict):
        errors.append(_error(resource_id, batch, "webfetch-fallback requires fallbackEvidence"))
        return errors

    for field in ("requestedUrl", "finalUrl", "retrievedAt"):
        value = evidence.get(field)
        if not isinstance(value, str) or not value:
            errors.append(_error(resource_id, batch, f"webfetch-fallback evidence missing {field}"))

    content_hash = evidence.get("contentSha256")
    if not isinstance(content_hash, str) or not HEX64_RE.fullmatch(content_hash):
        errors.append(
            _error(resource_id, batch,
                   "webfetch-fallback evidence requires a 64-character lowercase sha256 hash")
        )

    return errors


def _validate_copied_runs(facts, cache_text: str, resource_id: str, batch: str) -> list[str]:
    errors = []
    for fact in facts:
        if not isinstance(fact, dict):
            continue
        summary = fact.get("summary")
        if isinstance(summary, str) and _contains_copied_run(summary, cache_text):
            errors.append(
                _error(resource_id, batch,
                       "fact summary copies more than 300 characters from cached source text")
            )
    return errors


def _validate_coverage(manifest_by_id: dict, notes_by_id: dict, batch: str | None) -> list[str]:
    errors = []
    target_batches = {batch} if batch else set(BATCHES)
    for resource_id in sorted(manifest_by_id):
        resource = manifest_by_id[resource_id]
        assigned_batch = resource.get("assignedBatch")
        if assigned_batch not in target_batches:
            continue
        if resource_id not in notes_by_id:
            errors.append(_error(resource_id, assigned_batch, "missing source note for assigned batch"))
    return errors


def _contains_copied_run(summary: str, cache_text: str, threshold: int = COPIED_RUN_THRESHOLD) -> bool:
    normalized_summary = _normalize_for_copy_check(summary)
    window = threshold + 1
    if len(normalized_summary) < window:
        return False
    normalized_cache = _normalize_for_copy_check(cache_text)
    if len(normalized_cache) < window:
        return False
    for start in range(0, len(normalized_summary) - window + 1):
        if normalized_summary[start:start + window] in normalized_cache:
            return True
    return False


def _normalize_for_copy_check(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _load_cache_text(cache_path):
    if not cache_path:
        return None
    path = Path(cache_path)
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _error(resource_id: str, batch: str, message: str) -> str:
    return f"ERROR {resource_id} [{batch}] {message}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate source notes against manifest access/check evidence"
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--notes-dir", required=True, type=Path)
    parser.add_argument("--batch", choices=BATCHES)
    parser.add_argument("--list-required", action="store_true")
    parser.add_argument("--write-report", type=Path)
    args = parser.parse_args(argv)

    if args.list_required and args.write_report:
        parser.error("--list-required and --write-report cannot be combined")
    if args.batch and args.write_report:
        parser.error("--batch cannot be combined with --write-report")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    manifest = _read_json(args.manifest)

    if args.list_required:
        _print_required(manifest, args.batch)
        return 0

    notes, loader_errors = _load_notes_dir(args.notes_dir)
    errors = sorted(loader_errors + validate_source_notes(manifest, notes, args.batch))

    if errors:
        for error in errors:
            print(error)
        return 1

    _print_summary(manifest, notes, args.batch)

    if args.write_report:
        _write_report(args.write_report, manifest, notes)

    return 0


def _load_notes_dir(notes_dir: Path):
    notes = []
    errors = []
    notes_dir = Path(notes_dir)
    for batch in BATCHES:
        path = notes_dir / f"{batch}.json"
        if not path.is_file():
            continue
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"ERROR - [{batch}] malformed notes file {path.name}: {error}")
            continue
        if not isinstance(content, list):
            errors.append(f"ERROR - [{batch}] notes file {path.name} must contain a JSON array")
            continue
        for record in content:
            if isinstance(record, dict) and record.get("batch") != batch:
                errors.append(
                    _error(record.get("resourceId") or "unknown", batch,
                           f"note batch does not match containing file {path.name}")
                )
            notes.append(record)
    return notes, errors


def _print_required(manifest: dict, batch: str | None) -> None:
    resources = manifest.get("resources", [])
    selected = [
        resource for resource in resources
        if batch is None or resource.get("assignedBatch") == batch
    ]
    selected.sort(key=lambda resource: resource.get("resourceId") or "")
    print("resourceId\trequestedUrl\tlessonIds\trelevantOutline\tcheckStatus\tcacheText\terror")
    for resource in selected:
        check = resource.get("check") or {}
        values = (
            resource.get("resourceId"),
            resource.get("requestedUrl"),
            ";".join(resource.get("lessonIds") or []),
            " | ".join(resource.get("relevantOutline") or []),
            check.get("status"),
            check.get("cacheText"),
            check.get("error"),
        )
        print("\t".join(_table_cell(value) for value in values))
    print(f"count={len(selected)}")


def _print_summary(manifest: dict, notes: list, batch: str | None) -> None:
    if batch is None:
        total = len(manifest.get("resources", []))
        read_count = sum(
            1 for note in notes
            if isinstance(note, dict) and note.get("read", {}).get("status") == "read"
        )
        unavailable = len(notes) - read_count
        print(
            f"PASS source-notes resources={total} read={read_count} "
            f"unavailable={unavailable} batches={len(BATCHES)}"
        )
        return

    scoped_notes = [
        note for note in notes if isinstance(note, dict) and note.get("batch") == batch
    ]
    scoped_read = sum(
        1 for note in scoped_notes if note.get("read", {}).get("status") == "read"
    )
    unavailable = len(scoped_notes) - scoped_read
    print(
        f"PASS source-notes batch={batch} resources={len(scoped_notes)} "
        f"read={scoped_read} unavailable={unavailable}"
    )


def _write_report(path: Path, manifest: dict, notes: list) -> None:
    notes_by_id = {
        note.get("resourceId"): note
        for note in notes
        if isinstance(note, dict) and isinstance(note.get("resourceId"), str)
    }
    resources = sorted(
        manifest.get("resources", []), key=lambda resource: resource.get("resourceId") or ""
    )
    lines = [
        "# Source Reading Report",
        "",
        "| Resource | URL | Access | Read | Method | Lessons | Limitation |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for resource in resources:
        resource_id = resource.get("resourceId", "")
        note = notes_by_id.get(resource_id, {})
        check = resource.get("check") or {}
        read = note.get("read") or {}
        lessons = ", ".join(resource.get("lessonIds") or [])
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} |".format(
                _escape_table_cell(resource_id),
                _escape_table_cell(resource.get("requestedUrl") or ""),
                _escape_table_cell(check.get("status") or ""),
                _escape_table_cell(read.get("status") or "unavailable"),
                _escape_table_cell(read.get("method") or ""),
                _escape_table_cell(lessons),
                _escape_table_cell(read.get("limitation") or ""),
            )
        )
    content = "\n".join(lines) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _escape_table_cell(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _table_cell(value) -> str:
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")


def _read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
