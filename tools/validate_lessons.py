from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from hashlib import sha256
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


GROUPS = {"java", "spring", "completion"}
KINDS = {"theory", "lab", "project", "exam", "ojt", "evaluation"}
BLOCK_TYPES = {
    "paragraph", "note", "important", "warning", "code", "table",
    "deliverable", "template",
}
TECHNICAL_BLOCK_TYPES = {"code", "table"}
TEXT_BLOCK_TYPES = {"paragraph", "note", "important", "warning", "deliverable", "template"}
PRACTICE_TYPES = {"concept", "predict-output", "coding", "applied"}
INTERACTIONS = {"self-check", "multiple-choice"}
REFERENCE_TYPES = {"external", "internal"}
REVIEW_STATUSES = {"draft", "reviewed"}
MIN_PRACTICES = 2
MAX_PRACTICES = 4
COPIED_RUN_THRESHOLD = 300

JAVA_POST_17_PATTERNS = [
    (re.compile(r'STR\."'), 'STR."'),
    (re.compile(r"case\s+\w+\([^)]*\)\s+when\b"), "record pattern switch guard (case X(...) when)"),
    (re.compile(r"Thread\.ofVirtual\("), "Thread.ofVirtual("),
]
SPRING_LEGACY_PATTERNS = [
    (re.compile(r"\bjavax\.persistence\b"), "javax.persistence"),
    (re.compile(r"\bjavax\.validation\b"), "javax.validation"),
    (re.compile(r"WebSecurityConfigurerAdapter"), "WebSecurityConfigurerAdapter"),
]
BASELINE_LABELS = {
    "post-17": "Java post-17-only syntax",
    "legacy": "Spring legacy javax namespace",
}

DEFAULT_COURSE_CACHE_DIR = Path(".course-cache")


def build_source_index(notes: list) -> dict:
    """Index source-note records by resourceId for cross-source validation.

    Matches the shape documented in the Task 1 brief: readStatus, the set of
    relevant headings, the set of fact locators, the lessonIds the note is
    linked to, and the cache text path (if any) for copied-run detection.
    """
    index = {}
    for note in notes:
        if not isinstance(note, dict):
            continue
        resource_id = note.get("resourceId")
        if not isinstance(resource_id, str) or not resource_id:
            continue
        read = note.get("read") if isinstance(note.get("read"), dict) else {}
        facts = read.get("facts") if isinstance(read.get("facts"), list) else []
        headings = read.get("relevantHeadings") if isinstance(read.get("relevantHeadings"), list) else []
        lesson_ids = note.get("lessonIds") if isinstance(note.get("lessonIds"), list) else []
        access = note.get("access") if isinstance(note.get("access"), dict) else {}
        index[resource_id] = {
            "readStatus": read.get("status"),
            "headings": {h for h in headings if isinstance(h, str)},
            "locators": {
                fact.get("locator") for fact in facts
                if isinstance(fact, dict) and isinstance(fact.get("locator"), str)
            },
            "lessonIds": {lid for lid in lesson_ids if isinstance(lid, str)},
            "cacheText": access.get("cacheText"),
        }
    return index


def validate_lesson(lesson: dict, catalog_lesson: dict | None, source_index: dict) -> list[str]:
    """Validate one lesson package against its catalog record and source index.

    Returns a sorted-free list of "ERROR ..." strings (callers sort/merge as
    needed); an empty list means the lesson is valid.
    """
    errors = _validate_lesson_structure(lesson, catalog_lesson, source_index)
    if isinstance(lesson, dict):
        lesson_id = lesson.get("id") if isinstance(lesson.get("id"), str) else "unknown"
        errors.extend(_validate_lesson_copy_check(lesson, source_index, lesson_id))
    return errors


def _validate_lesson_structure(lesson: dict, catalog_lesson: dict | None, source_index: dict) -> list[str]:
    errors = []
    if not isinstance(lesson, dict):
        return [_error("unknown", "lesson record must be an object")]

    lesson_id = lesson.get("id") if isinstance(lesson.get("id"), str) else "unknown"

    if catalog_lesson is None:
        errors.append(_error(lesson_id, "lesson id is not present in course-catalog.json"))
        catalog_lesson = {}

    errors.extend(_validate_catalog_mirror(lesson, catalog_lesson, lesson_id))
    errors.extend(_validate_enums(lesson, lesson_id))

    seen_ids: dict[str, str] = {}
    citation_ids: set[str] = set()

    source_usage = lesson.get("sourceUsage")
    if isinstance(source_usage, list):
        for entry in source_usage:
            if not isinstance(entry, dict):
                errors.append(_error(lesson_id, "sourceUsage entry must be an object"))
                continue
            entry_id = entry.get("id")
            if not isinstance(entry_id, str) or not entry_id:
                errors.append(_error(lesson_id, "sourceUsage entry is missing id"))
                continue
            errors.extend(_register_id(seen_ids, entry_id, lesson_id))
            citation_ids.add(entry_id)
            errors.extend(
                _validate_sourceusage_entry(entry, entry_id, catalog_lesson, source_index, lesson_id)
            )
    else:
        errors.append(_error(lesson_id, "sourceUsage must be a list"))

    sections = lesson.get("sections")
    has_technical_block = False
    if isinstance(sections, list) and sections:
        for section in sections:
            section_errors, _section_used, section_has_technical = _validate_section(
                section, seen_ids, citation_ids, lesson_id
            )
            errors.extend(section_errors)
            has_technical_block = has_technical_block or section_has_technical
    else:
        errors.append(_error(lesson_id, "sections must be a nonempty list"))

    kind = lesson.get("kind")
    if kind in {"theory", "lab", "exam"} and isinstance(sections, list) and sections and not has_technical_block:
        errors.append(_error(lesson_id, "technical lesson requires at least one code or table block"))

    practices = lesson.get("practices")
    if isinstance(practices, list):
        errors.extend(_validate_practices(practices, seen_ids, citation_ids, kind, lesson_id))
    else:
        errors.append(_error(lesson_id, "practices must be a list"))

    errors.extend(_validate_references(lesson, citation_ids, lesson_id))
    errors.extend(_validate_baseline_lint(sections, lesson_id))
    errors.extend(_validate_authoring(lesson.get("authoring"), lesson_id))

    return errors


def _validate_catalog_mirror(lesson: dict, catalog_lesson: dict, lesson_id: str) -> list[str]:
    errors = []
    mirror_fields = ("unitId", "group", "title", "durationMinutes")
    for field in mirror_fields:
        if field in catalog_lesson and lesson.get(field) != catalog_lesson.get(field):
            errors.append(_error(lesson_id, f"{field} does not match catalog"))

    if "objectives" in catalog_lesson:
        if lesson.get("objectives") != catalog_lesson.get("objectives"):
            errors.append(_error(lesson_id, "objectives do not deep-equal catalog objectives"))

    if "syllabusAssignments" in catalog_lesson:
        if lesson.get("syllabusAssignments") != catalog_lesson.get("syllabusAssignments"):
            errors.append(
                _error(lesson_id, "syllabusAssignments do not deep-equal catalog syllabusAssignments")
            )

    return errors


def _validate_enums(lesson: dict, lesson_id: str) -> list[str]:
    errors = []
    if lesson.get("group") not in GROUPS:
        errors.append(_error(lesson_id, f"group must be one of {sorted(GROUPS)}"))
    if lesson.get("kind") not in KINDS:
        errors.append(_error(lesson_id, f"kind must be one of {sorted(KINDS)}"))
    for field in ("title", "summary"):
        if not isinstance(lesson.get(field), str) or not lesson.get(field):
            errors.append(_error(lesson_id, f"{field} must be a nonempty string"))
    return errors


def _register_id(seen_ids: dict, object_id: str, lesson_id: str) -> list[str]:
    if object_id in seen_ids:
        return [_error(lesson_id, f"duplicate id {object_id!r} (already used in {seen_ids[object_id]})")]
    seen_ids[object_id] = lesson_id
    return []


def _validate_sourceusage_entry(entry, entry_id, catalog_lesson, source_index, lesson_id):
    errors = []
    resource_id = entry.get("resourceId")
    locator = entry.get("locator")
    topic = entry.get("topic")

    if not isinstance(resource_id, str) or not resource_id:
        errors.append(_error(lesson_id, f"sourceUsage {entry_id} is missing resourceId"))
        return errors
    if not isinstance(topic, str) or not topic:
        errors.append(_error(lesson_id, f"sourceUsage {entry_id} is missing topic"))
    if not isinstance(locator, str) or not locator:
        errors.append(_error(lesson_id, f"sourceUsage {entry_id} is missing locator"))
        locator = None

    catalog_resource_ids = catalog_lesson.get("resourceIds") or []
    if resource_id not in catalog_resource_ids:
        errors.append(
            _error(
                lesson_id,
                f"sourceUsage {entry_id} cites {resource_id} which is not linked to this lesson",
            )
        )

    source = source_index.get(resource_id)
    if source is None:
        errors.append(_error(lesson_id, f"sourceUsage {entry_id} cites unknown resource {resource_id}"))
        return errors

    if source.get("readStatus") != "read":
        errors.append(
            _error(
                lesson_id,
                f"sourceUsage {entry_id} cites {resource_id} which is not read (status={source.get('readStatus')})",
            )
        )

    if locator is not None and locator not in source.get("locators", set()):
        errors.append(
            _error(
                lesson_id,
                f"sourceUsage {entry_id} locator {locator!r} is absent from the source note for {resource_id}",
            )
        )

    return errors


def _validate_section(section, seen_ids, citation_ids, lesson_id):
    errors = []
    used_citations = set()
    has_technical_block = False

    if not isinstance(section, dict):
        return [_error(lesson_id, "section must be an object")], used_citations, has_technical_block

    section_id = section.get("id")
    if isinstance(section_id, str) and section_id:
        errors.extend(_register_id(seen_ids, section_id, lesson_id))
    else:
        errors.append(_error(lesson_id, "section is missing id"))

    if not isinstance(section.get("title"), str) or not section.get("title"):
        errors.append(_error(lesson_id, f"section {section_id} is missing title"))

    blocks = section.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        errors.append(_error(lesson_id, f"section {section_id} must have a nonempty blocks list"))
        return errors, used_citations, has_technical_block

    for block in blocks:
        block_errors, block_used, is_technical = _validate_block(
            block, seen_ids, citation_ids, lesson_id, section_id
        )
        errors.extend(block_errors)
        used_citations |= block_used
        has_technical_block = has_technical_block or is_technical

    return errors, used_citations, has_technical_block


def _validate_block(block, seen_ids, citation_ids, lesson_id, section_id):
    errors = []
    used_citations = set()

    if not isinstance(block, dict):
        return [_error(lesson_id, f"section {section_id} block must be an object")], used_citations, False

    block_id = block.get("id")
    if isinstance(block_id, str) and block_id:
        errors.extend(_register_id(seen_ids, block_id, lesson_id))
    else:
        errors.append(_error(lesson_id, f"section {section_id} has a block missing id"))
        block_id = block_id or "unknown"

    block_type = block.get("type")
    if block_type not in BLOCK_TYPES:
        errors.append(_error(lesson_id, f"block {block_id} has invalid type {block_type!r}"))

    citations = block.get("citations")
    if not isinstance(citations, list):
        errors.append(_error(lesson_id, f"block {block_id} citations must be a list"))
        citations = []
    for citation_id in citations:
        if citation_id not in citation_ids:
            errors.append(
                _error(lesson_id, f"block {block_id} citations references unknown citation {citation_id!r}")
            )
        else:
            used_citations.add(citation_id)

    is_technical = block_type in TECHNICAL_BLOCK_TYPES

    if block_type in TEXT_BLOCK_TYPES:
        if not isinstance(block.get("text"), str) or not block.get("text"):
            errors.append(_error(lesson_id, f"block {block_id} requires nonempty text"))
        if block_type in {"important", "warning"} and not citations:
            errors.append(
                _error(lesson_id, f"block {block_id} ({block_type}) has empty citations for a technical claim")
            )

    if block_type == "code":
        if not isinstance(block.get("language"), str) or not block.get("language"):
            errors.append(_error(lesson_id, f"block {block_id} (code) requires language"))
        if not isinstance(block.get("code"), str) or not block.get("code"):
            errors.append(_error(lesson_id, f"block {block_id} (code) requires nonempty code"))
        compile_flag = block.get("compile")
        if not isinstance(compile_flag, bool):
            errors.append(_error(lesson_id, f"block {block_id} (code) requires boolean compile"))
        else:
            if compile_flag and block.get("language") != "java":
                errors.append(
                    _error(lesson_id, f"block {block_id} (code) compile=true is only allowed for language=java")
                )
            if not compile_flag:
                partial_reason = block.get("partialReason")
                if not isinstance(partial_reason, str) or not partial_reason:
                    errors.append(
                        _error(lesson_id, f"block {block_id} (code) compile=false requires nonempty partialReason")
                    )
        if not citations and block.get("language") != "text":
            errors.append(_error(lesson_id, f"block {block_id} (code) has empty citations for a technical claim"))

    if block_type == "table":
        columns = block.get("columns")
        rows = block.get("rows")
        if not isinstance(columns, list) or not columns:
            errors.append(_error(lesson_id, f"block {block_id} (table) requires nonempty columns"))
        if not isinstance(rows, list) or not rows:
            errors.append(_error(lesson_id, f"block {block_id} (table) requires nonempty rows"))
        if not citations:
            errors.append(_error(lesson_id, f"block {block_id} (table) has empty citations for a technical claim"))

    return errors, used_citations, is_technical


def _validate_practices(practices, seen_ids, citation_ids, kind, lesson_id):
    errors = []
    if not (MIN_PRACTICES <= len(practices) <= MAX_PRACTICES):
        errors.append(
            _error(lesson_id, f"practices count {len(practices)} must be between {MIN_PRACTICES} and {MAX_PRACTICES}")
        )

    for practice in practices:
        errors.extend(_validate_practice(practice, seen_ids, citation_ids, lesson_id))

    return errors


def _validate_practice(practice, seen_ids, citation_ids, lesson_id):
    errors = []
    if not isinstance(practice, dict):
        return [_error(lesson_id, "practice must be an object")]

    practice_id = practice.get("id")
    if isinstance(practice_id, str) and practice_id:
        errors.extend(_register_id(seen_ids, practice_id, lesson_id))
    else:
        errors.append(_error(lesson_id, "practice is missing id"))
        practice_id = practice_id or "unknown"

    if practice.get("type") not in PRACTICE_TYPES:
        errors.append(_error(lesson_id, f"practice {practice_id} has invalid type {practice.get('type')!r}"))

    interaction = practice.get("interaction")
    if interaction not in INTERACTIONS:
        errors.append(_error(lesson_id, f"practice {practice_id} has invalid interaction {interaction!r}"))

    for field in ("prompt", "hint", "solution", "explanation", "rubric"):
        if not isinstance(practice.get(field), str) or not practice.get(field):
            errors.append(_error(lesson_id, f"practice {practice_id} requires nonempty {field}"))

    choices = practice.get("choices")
    correct_ids = practice.get("correctChoiceIds")
    choices = choices if isinstance(choices, list) else []
    correct_ids = correct_ids if isinstance(correct_ids, list) else []

    choice_ids = set()
    for choice in choices:
        if not isinstance(choice, dict) or not isinstance(choice.get("id"), str) or not choice.get("id"):
            errors.append(_error(lesson_id, f"practice {practice_id} has a choice missing id"))
            continue
        if not isinstance(choice.get("text"), str) or not choice.get("text"):
            errors.append(_error(lesson_id, f"practice {practice_id} choice {choice['id']} requires nonempty text"))
        choice_ids.add(choice["id"])

    if interaction == "multiple-choice":
        if len(choices) < 2:
            errors.append(_error(lesson_id, f"practice {practice_id} (multiple-choice) requires at least two choices"))
        unknown = [cid for cid in correct_ids if cid not in choice_ids]
        if unknown:
            errors.append(
                _error(lesson_id, f"practice {practice_id} correctChoiceIds references unknown choice(s) {unknown}")
            )
        if not correct_ids:
            errors.append(
                _error(lesson_id, f"practice {practice_id} (multiple-choice) correctChoiceIds must name at least one correct answer")
            )
    elif interaction == "self-check":
        if choices:
            errors.append(_error(lesson_id, f"practice {practice_id} (self-check) must have empty choices"))
        if correct_ids:
            errors.append(_error(lesson_id, f"practice {practice_id} (self-check) must have empty correctChoiceIds"))

    source_usage = practice.get("sourceUsage")
    if not isinstance(source_usage, list):
        errors.append(_error(lesson_id, f"practice {practice_id} sourceUsage must be a list"))
    else:
        for citation_id in source_usage:
            if citation_id not in citation_ids:
                errors.append(
                    _error(lesson_id, f"practice {practice_id} sourceUsage references unknown citation {citation_id!r}")
                )

    return errors


def _validate_references(lesson, citation_ids, lesson_id):
    errors = []
    references = lesson.get("references")
    if not isinstance(references, list):
        errors.append(_error(lesson_id, "references must be a list"))
        return errors

    catalog_resource_ids = {
        entry.get("resourceId")
        for entry in (lesson.get("sourceUsage") or [])
        if isinstance(entry, dict)
    }
    seen_reference_ids: set[str] = set()

    for reference in references:
        if not isinstance(reference, dict):
            errors.append(_error(lesson_id, "reference must be an object"))
            continue
        reference_id = reference.get("id")
        if not isinstance(reference_id, str) or not reference_id:
            errors.append(_error(lesson_id, "reference is missing id"))
            continue
        if reference_id in seen_reference_ids:
            errors.append(_error(lesson_id, f"duplicate reference id {reference_id!r}"))
        seen_reference_ids.add(reference_id)

        reference_type = reference.get("type")
        if reference_type not in REFERENCE_TYPES:
            errors.append(_error(lesson_id, f"reference {reference_id} has invalid type {reference_type!r}"))
            continue

        if reference_type == "external":
            resource_id = reference.get("resourceId")
            citation_id = reference.get("citationId")
            if resource_id not in catalog_resource_ids:
                errors.append(
                    _error(lesson_id, f"reference {reference_id} resourceId {resource_id!r} has no matching sourceUsage entry")
                )
            if citation_id not in citation_ids:
                errors.append(
                    _error(lesson_id, f"reference {reference_id} citationId {citation_id!r} has no matching sourceUsage id")
                )
        else:
            if not isinstance(reference.get("description"), str) or not reference.get("description"):
                errors.append(_error(lesson_id, f"reference {reference_id} (internal) requires nonempty description"))

    return errors


def _validate_authoring(authoring, lesson_id):
    errors = []
    if not isinstance(authoring, dict):
        return [_error(lesson_id, "authoring must be an object")]
    if not isinstance(authoring.get("baseline"), str) or not authoring.get("baseline"):
        errors.append(_error(lesson_id, "authoring.baseline must be a nonempty string"))
    if authoring.get("reviewStatus") not in REVIEW_STATUSES:
        errors.append(_error(lesson_id, f"authoring.reviewStatus must be one of {sorted(REVIEW_STATUSES)}"))
    if not isinstance(authoring.get("limitations"), list):
        errors.append(_error(lesson_id, "authoring.limitations must be a list"))
    return errors


def _validate_baseline_lint(sections, lesson_id):
    errors = []
    if not isinstance(sections, list):
        return errors
    for section in sections:
        if not isinstance(section, dict):
            continue
        for block in section.get("blocks") or []:
            if not isinstance(block, dict) or block.get("type") != "code":
                continue
            if block.get("language") == "text":
                continue
            code = block.get("code")
            if not isinstance(code, str):
                continue
            block_id = block.get("id", "unknown")
            for pattern, label in JAVA_POST_17_PATTERNS:
                if pattern.search(code):
                    errors.append(
                        _error(lesson_id, f"block {block_id} contains {BASELINE_LABELS['post-17']}: {label}")
                    )
            for pattern, label in SPRING_LEGACY_PATTERNS:
                if pattern.search(code):
                    errors.append(
                        _error(lesson_id, f"block {block_id} contains {BASELINE_LABELS['legacy']}: {label}")
                    )
    return errors


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


def _normalize_for_copy_check(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


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


def _error(lesson_id: str, message: str) -> str:
    return f"ERROR {lesson_id} {message}"


def _validate_lesson_copy_check(lesson, source_index, lesson_id):
    errors = []
    sourceusage_by_id = {
        entry.get("id"): entry
        for entry in (lesson.get("sourceUsage") or [])
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    sections = lesson.get("sections")
    if not isinstance(sections, list):
        return errors
    for section in sections:
        if not isinstance(section, dict):
            continue
        for block in section.get("blocks") or []:
            if not isinstance(block, dict):
                continue
            text = block.get("text") if block.get("type") in TEXT_BLOCK_TYPES else None
            if not isinstance(text, str) or not text:
                continue
            for citation_id in block.get("citations") or []:
                entry = sourceusage_by_id.get(citation_id)
                if not entry:
                    continue
                resource_id = entry.get("resourceId")
                source = source_index.get(resource_id)
                if not source:
                    continue
                cache_text = _load_cache_text(source.get("cacheText"))
                if cache_text is None:
                    continue
                if _contains_copied_run(text, cache_text):
                    errors.append(
                        _error(
                            lesson_id,
                            f"block {block.get('id')} copies more than 300 characters from cached source text for {resource_id}",
                        )
                    )
    return errors


def validate_corpus(catalog: dict, lessons: list[dict], source_index: dict,
                     required_ids: set[str] | None = None) -> list[str]:
    """Validate a set of lesson packages together against the catalog.

    Runs `validate_lesson` on each lesson (against its own catalog record),
    checks that every lesson id in `required_ids` (defaulting to every
    catalog lesson id) is present exactly once, and enforces global id
    uniqueness (sections/practices/citations) across the whole corpus.
    """
    errors = []
    catalog_lessons = catalog.get("lessons") if isinstance(catalog, dict) else None
    catalog_lessons = catalog_lessons if isinstance(catalog_lessons, list) else []
    catalog_by_id = {
        lesson.get("id"): lesson for lesson in catalog_lessons
        if isinstance(lesson, dict) and isinstance(lesson.get("id"), str)
    }

    if required_ids is None:
        required_ids = set(catalog_by_id)

    seen_lesson_ids: dict[str, int] = {}
    global_seen_ids: dict[str, str] = {}

    for lesson in lessons:
        lesson_id = lesson.get("id") if isinstance(lesson, dict) and isinstance(lesson.get("id"), str) else None
        if lesson_id is None:
            errors.append(_error("unknown", "lesson record is missing id"))
            continue
        seen_lesson_ids[lesson_id] = seen_lesson_ids.get(lesson_id, 0) + 1
        if seen_lesson_ids[lesson_id] > 1:
            errors.append(_error(lesson_id, "duplicate lesson file for this id"))
            continue

        catalog_lesson = catalog_by_id.get(lesson_id)
        errors.extend(validate_lesson(lesson, catalog_lesson, source_index))
        errors.extend(_merge_global_ids(lesson, lesson_id, global_seen_ids))

    for lesson_id in sorted(required_ids - set(seen_lesson_ids)):
        errors.append(_error(lesson_id, "missing lesson file for required catalog entry"))

    return errors


def _merge_global_ids(lesson, lesson_id, global_seen_ids):
    errors = []
    local_ids = []
    for section in lesson.get("sections") or []:
        if isinstance(section, dict):
            if isinstance(section.get("id"), str):
                local_ids.append(section["id"])
            for block in section.get("blocks") or []:
                if isinstance(block, dict) and isinstance(block.get("id"), str):
                    local_ids.append(block["id"])
    for practice in lesson.get("practices") or []:
        if isinstance(practice, dict) and isinstance(practice.get("id"), str):
            local_ids.append(practice["id"])
    for entry in lesson.get("sourceUsage") or []:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str):
            local_ids.append(entry["id"])

    for object_id in local_ids:
        owner = global_seen_ids.get(object_id)
        if owner is not None and owner != lesson_id:
            errors.append(_error(lesson_id, f"duplicate id {object_id!r} (already used in {owner})"))
        else:
            global_seen_ids[object_id] = lesson_id
    return errors


def _select_lesson_ids(catalog: dict, selector: str | None) -> set[str] | None:
    if not selector:
        return None
    all_ids = [
        lesson.get("id") for lesson in catalog.get("lessons", [])
        if isinstance(lesson, dict) and isinstance(lesson.get("id"), str)
    ]
    if ":" in selector and "," not in selector:
        start, end = selector.split(":", 1)
        try:
            start_index = all_ids.index(start)
            end_index = all_ids.index(end)
        except ValueError as error:
            raise ValueError(f"unknown lesson id in range {selector!r}: {error}") from error
        if start_index > end_index:
            raise ValueError(f"range {selector!r} is inverted")
        return set(all_ids[start_index:end_index + 1])
    selected = {item.strip() for item in selector.split(",") if item.strip()}
    unknown = selected - set(all_ids)
    if unknown:
        raise ValueError(f"unknown lesson id(s): {sorted(unknown)}")
    return selected


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate lesson packages against the catalog and source notes"
    )
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source-notes-dir", required=True, type=Path)
    parser.add_argument("--lessons-dir", required=True, type=Path)
    parser.add_argument("--list-requirements")
    parser.add_argument("--only")
    parser.add_argument("--compile-java", action="store_true")
    parser.add_argument("--course-cache-dir", type=Path, default=DEFAULT_COURSE_CACHE_DIR)
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    catalog = _read_json(args.catalog)

    if args.list_requirements:
        try:
            selected = _select_lesson_ids(catalog, args.list_requirements)
        except ValueError as error:
            parser.error(str(error))
        _print_requirements(catalog, _load_all_notes(args.source_notes_dir), selected)
        return 0

    notes = _load_all_notes(args.source_notes_dir)
    source_index = build_source_index(notes)

    try:
        required_ids = _select_lesson_ids(catalog, args.only)
    except ValueError as error:
        parser.error(str(error))

    lessons, load_errors = _load_lessons_dir(args.lessons_dir, required_ids)

    errors = load_errors + validate_corpus(catalog, lessons, source_index, required_ids)

    if not errors and args.compile_java:
        errors = _compile_java_snippets(lessons, args.course_cache_dir)

    errors = sorted(errors)
    if errors:
        for error in errors:
            print(error)
        return 1

    sections = sum(len(lesson.get("sections") or []) for lesson in lessons)
    practices = sum(len(lesson.get("practices") or []) for lesson in lessons)
    citations = sum(len(lesson.get("sourceUsage") or []) for lesson in lessons)
    assignments = sum(len(lesson.get("syllabusAssignments") or []) for lesson in lessons)
    print(
        f"PASS lessons={len(lessons)} sections={sections} practices={practices} "
        f"citations={citations} assignments={assignments}"
    )
    return 0


def _load_all_notes(notes_dir: Path) -> list:
    notes = []
    notes_dir = Path(notes_dir)
    if not notes_dir.is_dir():
        return notes
    for path in sorted(notes_dir.glob("*.json")):
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(content, list):
            notes.extend(content)
    return notes


def _load_lessons_dir(lessons_dir: Path, required_ids: set[str] | None):
    lessons = []
    errors = []
    lessons_dir = Path(lessons_dir)
    if not lessons_dir.is_dir():
        return lessons, errors
    for path in sorted(lessons_dir.glob("*.json")):
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"ERROR - malformed lesson file {path.name}: {error}")
            continue
        if isinstance(content, list):
            candidates = content
        else:
            candidates = [content]
        for lesson in candidates:
            if not isinstance(lesson, dict):
                errors.append(f"ERROR - {path.name} lesson record must be an object")
                continue
            lesson_id = lesson.get("id")
            if required_ids is not None and lesson_id not in required_ids:
                continue
            lessons.append(lesson)
    return lessons, errors


def _print_requirements(catalog, notes, selected):
    notes_by_resource = {}
    for note in notes:
        if isinstance(note, dict) and isinstance(note.get("resourceId"), str):
            notes_by_resource[note["resourceId"]] = note

    lessons = [
        lesson for lesson in catalog.get("lessons", [])
        if isinstance(lesson, dict) and (selected is None or lesson.get("id") in selected)
    ]
    lessons.sort(key=lambda lesson: lesson.get("id") or "")

    for lesson in lessons:
        print(f"=== {lesson.get('id')} ===")
        print(f"title\t{lesson.get('title')}")
        print(f"unitId\t{lesson.get('unitId')}\tgroup\t{lesson.get('group')}")
        print(f"durationMinutes\t{lesson.get('durationMinutes')}")
        print(f"objectives\t{'; '.join(lesson.get('objectives') or [])}")
        print(f"outline\t{' | '.join(lesson.get('outline') or [])}")
        for activity in lesson.get("activities") or []:
            print(f"activity[row={activity.get('row')}]\t{activity.get('text')}")
        for assignment in lesson.get("syllabusAssignments") or []:
            print(f"syllabusAssignment[row={assignment.get('row')}]\t{assignment.get('text')}")
        print(f"sourceRows\t{lesson.get('sourceRows')}")
        for resource_id in lesson.get("resourceIds") or []:
            note = notes_by_resource.get(resource_id)
            if note is None:
                print(f"resource\t{resource_id}\tstatus=no-note")
                continue
            read = note.get("read") or {}
            status = read.get("status")
            if status == "read":
                print(
                    f"resource\t{resource_id}\tstatus=read\theadings={'; '.join(read.get('relevantHeadings') or [])}"
                    f"\ttopics={'; '.join(read.get('topics') or [])}"
                )
                for fact in read.get("facts") or []:
                    print(
                        f"  fact\ttopic={fact.get('topic')}\tlocator={fact.get('locator')}\tsummary={fact.get('summary')}"
                    )
            else:
                print(f"resource\t{resource_id}\tstatus=unavailable\tlimitation={read.get('limitation')}")
        print("")


def _compile_java_snippets(lessons, cache_dir: Path) -> list[str]:
    errors = []
    javac = shutil.which("javac")
    if javac is None:
        return [_error("unknown", "javac is not available on PATH; --compile-java requires a JDK")]

    src_dir = Path(cache_dir) / "javac-src"
    out_dir = Path(cache_dir) / "javac"
    src_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    for lesson in lessons:
        lesson_id = lesson.get("id", "unknown")
        for section in lesson.get("sections") or []:
            if not isinstance(section, dict):
                continue
            for block in section.get("blocks") or []:
                if not isinstance(block, dict) or block.get("type") != "code":
                    continue
                if block.get("language") != "java" or block.get("compile") is not True:
                    continue
                block_id = block.get("id", "unknown")
                snippet_name = f"Snippet_{_safe_component(lesson_id)}_{_safe_component(block_id)}.java"
                snippet_path = src_dir / snippet_name
                snippet_path.write_text(block.get("code") or "", encoding="utf-8")
                result = subprocess.run(
                    [javac, "--release", "17", "-d", str(out_dir), str(snippet_path)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    detail = (result.stderr or result.stdout or "").strip().splitlines()
                    detail_line = detail[0] if detail else "javac failed"
                    errors.append(
                        _error(lesson_id, f"block {block_id} failed javac --release 17: {detail_line}")
                    )
    return errors


def _safe_component(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", str(value))


def _read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
