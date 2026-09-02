from __future__ import annotations

import json
import posixpath
import re
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from xml.etree import ElementTree
from zipfile import ZipFile


TRAILING_URL_PUNCTUATION = ".,);]}>"
REL_NAMESPACES = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "http://purl.oclc.org/ooxml/officeDocument/relationships",
)
URL_RE = re.compile(r"https?://[^\s<>]+", re.IGNORECASE)
DAY_RE = re.compile(r"^Day\s*(\d+)(?:\s*-\s*(?:Day\s*)?(\d+))?", re.IGNORECASE)
UNIT_RE = re.compile(r"\d+")

SUPPLEMENTAL_SCHEMA_VERSION = 1
SUPPLEMENTAL_REQUIRED_FIELDS = ("url", "title", "publisher", "lessonIds", "purpose")


def normalize_url(url: str) -> str:
    cleaned = url.strip().rstrip(TRAILING_URL_PUNCTUATION)
    parts = urlsplit(cleaned)
    scheme = parts.scheme.lower()
    host = parts.netloc.lower()
    path = parts.path or "/"
    return urlunsplit((scheme, host, path, parts.query, ""))


def resource_id(url: str) -> str:
    digest = sha256(normalize_url(url).encode("utf-8")).hexdigest()[:12]
    return f"res-{digest}"


class SupplementalSourceError(ValueError):
    """Raised when content/supplemental-sources.json is malformed, or a
    supplemental resource conflicts with an already-known resource identity
    (same normalized URL, incompatible metadata) or references an unknown
    lesson id. Callers must not write any generated output when this is
    raised — see tools/extract_catalog.py.
    """


def load_supplemental_sources(path: Path) -> list[dict]:
    """Parse and structurally validate an authored supplemental-sources file.

    Returns a list of normalized entry dicts (url, normalizedUrl, resourceId,
    title, publisher, lessonIds, purpose) ready to pass to
    `merge_supplemental_resources`. Raises `SupplementalSourceError` on any
    structural problem: unreadable/malformed JSON, unsupported
    schemaVersion, a missing/blank required field, a malformed URL, or two
    entries whose URL normalizes to the same value (one entry per distinct
    URL — list every lesson it serves in that one entry's lessonIds).

    This function never touches course-catalog.json; lesson id existence and
    cross-resource identity conflicts are checked by
    `merge_supplemental_resources`, which needs the catalog to check against.
    """
    path = Path(path)
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise SupplementalSourceError(f"{path}: cannot read supplemental sources file: {error}") from error
    try:
        payload = json.loads(raw_text)
    except ValueError as error:
        raise SupplementalSourceError(f"{path}: invalid JSON: {error}") from error

    if not isinstance(payload, dict):
        raise SupplementalSourceError(f"{path}: root must be a JSON object")
    if payload.get("schemaVersion") != SUPPLEMENTAL_SCHEMA_VERSION:
        raise SupplementalSourceError(
            f"{path}: unsupported schemaVersion {payload.get('schemaVersion')!r} "
            f"(expected {SUPPLEMENTAL_SCHEMA_VERSION})"
        )

    resources = payload.get("resources")
    if not isinstance(resources, list):
        raise SupplementalSourceError(f"{path}: 'resources' must be a list")

    entries = []
    seen_by_normalized_url = {}
    seen_by_resource_id = {}
    for index, raw in enumerate(resources):
        location = f"{path}: resources[{index}]"
        if not isinstance(raw, dict):
            raise SupplementalSourceError(f"{location}: entry must be an object")

        missing = [field for field in SUPPLEMENTAL_REQUIRED_FIELDS if not raw.get(field)]
        if missing:
            raise SupplementalSourceError(f"{location}: missing required field(s): {', '.join(missing)}")

        url = raw["url"]
        if not isinstance(url, str) or not _is_http_url(url):
            raise SupplementalSourceError(f"{location}: url must be an absolute http(s) URL, got {url!r}")

        title, publisher, purpose = raw["title"], raw["publisher"], raw["purpose"]
        if not all(isinstance(value, str) and value.strip() for value in (title, publisher, purpose)):
            raise SupplementalSourceError(f"{location}: title/publisher/purpose must be nonempty strings")

        lesson_ids = raw["lessonIds"]
        if (
            not isinstance(lesson_ids, list)
            or not lesson_ids
            or not all(isinstance(item, str) and item for item in lesson_ids)
        ):
            raise SupplementalSourceError(f"{location}: lessonIds must be a nonempty list of nonempty strings")

        normalized_url = normalize_url(url)
        item_id = resource_id(url)

        if normalized_url in seen_by_normalized_url:
            raise SupplementalSourceError(
                f"{location}: duplicate resource definition — url normalizes the same as "
                f"resources[{seen_by_normalized_url[normalized_url]}] ({normalized_url}); "
                f"one entry per distinct URL, list every lessonId on that one entry"
            )
        if item_id in seen_by_resource_id and seen_by_resource_id[item_id] != normalized_url:
            raise SupplementalSourceError(
                f"{location}: resourceId collision {item_id} between "
                f"{seen_by_resource_id[item_id]!r} and {normalized_url!r}"
            )
        seen_by_normalized_url[normalized_url] = index
        seen_by_resource_id[item_id] = normalized_url

        entries.append(
            {
                "url": url,
                "normalizedUrl": normalized_url,
                "resourceId": item_id,
                "title": title.strip(),
                "publisher": publisher.strip(),
                "lessonIds": list(dict.fromkeys(lesson_ids)),
                "purpose": purpose.strip(),
            }
        )

    return entries


def merge_supplemental_resources(catalog: dict, supplemental_entries: list[dict]) -> dict:
    """Merge authored supplemental resources into a workbook-parsed catalog.

    Mutates and returns `catalog`. Called with an empty/None `supplemental_entries`
    this is a no-op and returns `catalog` unchanged — that is what keeps
    generation backward compatible when no supplemental file is supplied.

    Identity rule: a supplemental entry names the SAME resource as an
    existing one iff `resource_id(entry["url"]) == existing["id"]` (the same
    deterministic, content-derived id used for every workbook resource — see
    `resource_id`). For a match:
      - if the entry's title is not among the existing resource's `labels`,
        this is a metadata conflict -> SupplementalSourceError (fail loudly,
        no partial merge of this entry).
      - otherwise, any lessonIds not already linked to the resource are
        added (resource.lessonIds and each newly linked lesson's
        resourceIds are both updated) and a "SUPPLEMENT ... merge" line is
        printed. If every lessonId was already linked, this is a no-op
        (still prints a line, for visibility, but changes nothing).
    A supplemental entry naming a resource id that doesn't exist yet creates
    a new resource record and prints a "SUPPLEMENT ... new resource" line.

    Any lessonId (new or merged) that doesn't exist in `catalog["lessons"]`
    fails the whole entry loudly before anything is mutated for that entry.
    """
    if not supplemental_entries:
        return catalog

    lessons_by_id = {lesson["id"]: lesson for lesson in catalog["lessons"]}
    resources_by_id = {resource["id"]: resource for resource in catalog["resources"]}

    for entry in supplemental_entries:
        unknown_lessons = [lid for lid in entry["lessonIds"] if lid not in lessons_by_id]
        if unknown_lessons:
            raise SupplementalSourceError(
                f"supplemental resource {entry['url']!r} references unknown lesson id(s): "
                f"{', '.join(unknown_lessons)}"
            )

        item_id = entry["resourceId"]
        existing = resources_by_id.get(item_id)

        if existing is None:
            resource = {
                "id": item_id,
                "url": entry["normalizedUrl"],
                "labels": [entry["title"]],
                "lessonIds": [],
                "sourceRows": [],
                "occurrences": [],
            }
            resources_by_id[item_id] = resource
            catalog["resources"].append(resource)
            print(
                f"SUPPLEMENT {item_id} new resource url={entry['normalizedUrl']} "
                f"lessonIds={entry['lessonIds']}"
            )
        else:
            if entry["title"] not in existing["labels"]:
                raise SupplementalSourceError(
                    f"supplemental resource {item_id} ({entry['normalizedUrl']}) title "
                    f"{entry['title']!r} conflicts with existing label(s) {existing['labels']!r} "
                    f"for the same normalized URL — fix the title to match exactly, or cite a "
                    f"different/more specific URL if this is really a distinct reference"
                )
            resource = existing

        newly_linked = []
        for lesson_id in entry["lessonIds"]:
            if lesson_id not in resource["lessonIds"]:
                resource["lessonIds"].append(lesson_id)
                newly_linked.append(lesson_id)
            lesson = lessons_by_id[lesson_id]
            if item_id not in lesson["resourceIds"]:
                lesson["resourceIds"].append(item_id)

        if existing is not None:
            if newly_linked:
                print(f"SUPPLEMENT {item_id} merge lessonIds+={newly_linked} -> {resource['lessonIds']}")
            else:
                print(f"SUPPLEMENT {item_id} no-op (already linked to {entry['lessonIds']})")

    return catalog


def _is_http_url(url: str) -> bool:
    parts = urlsplit(url.strip())
    return parts.scheme.lower() in {"http", "https"} and bool(parts.netloc)


def parse_schedule(
    workbook: Path, sheet_name: str = "JavaSpring_Schedule"
) -> dict:
    workbook = Path(workbook)
    with ZipFile(workbook) as archive:
        shared_strings = _read_shared_strings(archive)
        sheet_path = _find_sheet_path(archive, sheet_name)
        rows = _read_rows(archive, sheet_path, shared_strings)

    units_by_id = {}
    lessons = []
    resources_by_id = {}
    current_unit_number = None
    current_unit_title = None
    current_lesson = None

    for row_number in range(3, 64):
        cells = rows.get(row_number, {})
        unit_number = _parse_unit_number(cells.get("A"))
        unit_title = _text(cells.get("B"))
        day_value = _text(cells.get("C"))

        if unit_number is not None:
            current_unit_number = unit_number
        if unit_title:
            current_unit_title = unit_title
        if not any(_text(value) for value in cells.values()):
            continue
        if not day_value.lower().startswith("day") and current_lesson is None:
            continue
        if current_unit_number is None or not current_unit_title:
            continue

        unit_id = f"unit-{current_unit_number:02d}"
        group = _unit_group(current_unit_number)
        unit = units_by_id.setdefault(
            unit_id,
            {
                "id": unit_id,
                "number": current_unit_number,
                "title": current_unit_title,
                "group": group,
                "lessonIds": [],
                "sourceRows": [],
            },
        )
        if unit["title"] != current_unit_title:
            unit["title"] = current_unit_title

        if day_value.lower().startswith("day"):
            day_start, day_end = _parse_day(day_value)
            lesson_id = (
                f"day-{day_start:02d}"
                if day_start == day_end
                else f"day-{day_start}-{day_end}"
            )
            current_lesson = {
                "id": lesson_id,
                "dayStart": day_start,
                "dayEnd": day_end,
                "label": _canonical_day_label(day_start, day_end),
                "unitId": unit_id,
                "group": group,
                "title": "",
                "outline": [],
                "objectives": [],
                "durationMinutes": 0,
                "activities": [],
                "syllabusAssignments": [],
                "resourceIds": [],
                "sourceRows": [],
            }
            lessons.append(current_lesson)
            unit["lessonIds"].append(lesson_id)

        if current_lesson is None:
            continue
        lesson_unit = units_by_id[current_lesson["unitId"]]
        _append_unique(lesson_unit["sourceRows"], row_number)
        _append_unique(current_lesson["sourceRows"], row_number)
        _add_row_to_lesson(current_lesson, cells, row_number)
        _add_resources(
            current_lesson,
            resources_by_id,
            cells.get("K"),
            row_number,
        )

    resources = sorted(resources_by_id.values(), key=lambda item: item["id"])
    return {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {"workbook": workbook.name, "sheet": sheet_name},
        "units": list(units_by_id.values()),
        "lessons": lessons,
        "resources": resources,
    }


def render_catalog_markdown(catalog: dict) -> str:
    units = {unit["id"]: unit for unit in catalog["units"]}
    resources = {resource["id"]: resource for resource in catalog["resources"]}
    lines = ["# Java/Spring Course Catalog", ""]
    for lesson in catalog["lessons"]:
        unit = units[lesson["unitId"]]
        objectives = ", ".join(lesson["objectives"]) or "—"
        rows = ", ".join(str(row) for row in lesson["sourceRows"])
        lines.extend(
            [
                f"## {lesson['label']} — {lesson['title']}",
                "",
                f"- **Unit:** Unit {unit['number']} — {unit['title']}",
                f"- **Nhóm:** {lesson['group'].title()}",
                f"- **Mục tiêu:** {objectives}",
                f"- **Thời lượng:** {lesson['durationMinutes']} phút",
                f"- **Dòng nguồn:** {rows}",
                "",
                "### Nội dung và hoạt động",
            ]
        )
        content_items = list(lesson["outline"])
        for activity in lesson["activities"]:
            _append_unique(content_items, activity["text"])
        if content_items:
            for item in content_items:
                lines.extend(line.rstrip() for line in f"- {item}".splitlines())
        else:
            lines.append("- —")
        lines.extend(["", "### Tài liệu"])
        if lesson["resourceIds"]:
            for item_id in lesson["resourceIds"]:
                resource = resources[item_id]
                label = _escape_markdown_label(
                    _resource_label_for_lesson(resource, lesson["id"])
                )
                lines.append(
                    f"- [{label}]({resource['url']}) — stable `{item_id}` ID generated "
                    f"from the normalized URL — {_resource_check_label(resource)}"
                )
        else:
            lines.append("- —")
        lines.append("")
    return "\n".join(lines)


def _read_shared_strings(archive: ZipFile) -> list[str]:
    try:
        root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    namespace = _namespace(root)
    return ["".join(node.itertext()) for node in root.findall(f"{{{namespace}}}si")]


def _find_sheet_path(archive: ZipFile, sheet_name: str) -> str:
    workbook_root = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    sheet_namespace = _namespace(workbook_root)
    sheet = next(
        (
            node
            for node in workbook_root.findall(
                f"{{{sheet_namespace}}}sheets/{{{sheet_namespace}}}sheet"
            )
            if node.get("name") == sheet_name
        ),
        None,
    )
    if sheet is None:
        raise ValueError(f"Sheet not found: {sheet_name}")
    relationship_id = next(
        (
            sheet.get(f"{{{namespace}}}id")
            for namespace in REL_NAMESPACES
            if sheet.get(f"{{{namespace}}}id")
        ),
        None,
    )
    relationships = ElementTree.fromstring(
        archive.read("xl/_rels/workbook.xml.rels")
    )
    relationship_namespace = _namespace(relationships)
    relationship = next(
        (
            node
            for node in relationships.findall(
                f"{{{relationship_namespace}}}Relationship"
            )
            if node.get("Id") == relationship_id
        ),
        None,
    )
    if relationship is None:
        raise ValueError(f"Relationship not found for sheet: {sheet_name}")
    target = relationship.get("Target", "")
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    return posixpath.normpath(posixpath.join("xl", target))


def _read_rows(archive: ZipFile, sheet_path: str, shared_strings: list[str]):
    root = ElementTree.fromstring(archive.read(sheet_path))
    namespace = _namespace(root)
    rows = {}
    for row in root.findall(
        f"{{{namespace}}}sheetData/{{{namespace}}}row"
    ):
        row_number = int(row.get("r", "0"))
        values = {}
        for cell in row.findall(f"{{{namespace}}}c"):
            reference = cell.get("r", "")
            column_match = re.match(r"[A-Z]+", reference)
            if column_match:
                values[column_match.group(0)] = _cell_value(
                    cell, shared_strings, namespace
                )
        rows[row_number] = values
    return rows


def _cell_value(cell, shared_strings, namespace):
    cell_type = cell.get("t")
    if cell_type == "inlineStr":
        inline = cell.find(f"{{{namespace}}}is")
        return "" if inline is None else "".join(inline.itertext())
    value_node = cell.find(f"{{{namespace}}}v")
    if value_node is None:
        formula = cell.find(f"{{{namespace}}}f")
        return "" if formula is None else "".join(formula.itertext())
    value = value_node.text or ""
    if cell_type == "s":
        try:
            return shared_strings[int(value)]
        except (IndexError, ValueError):
            return value
    if cell_type == "b":
        return value == "1"
    return value


def _namespace(element):
    match = re.match(r"\{([^}]+)\}", element.tag)
    if match is None:
        raise ValueError(f"Open XML element has no namespace: {element.tag}")
    return match.group(1)


def _parse_unit_number(value):
    text = _text(value)
    match = UNIT_RE.search(text)
    return int(match.group()) if match else None


def _parse_day(label):
    match = DAY_RE.match(label.strip())
    if match is None:
        raise ValueError(f"Invalid Day label: {label}")
    day_start = int(match.group(1))
    day_end = int(match.group(2) or day_start)
    return day_start, day_end


def _canonical_day_label(day_start, day_end):
    return f"Day {day_start}" if day_start == day_end else f"Day {day_start}–{day_end}"


def _unit_group(unit_number):
    if unit_number <= 4:
        return "java"
    if unit_number <= 12:
        return "spring"
    return "completion"


def _add_row_to_lesson(lesson, cells, row_number):
    activity_text = _text(cells.get("D"))
    if activity_text:
        if not lesson["title"]:
            lesson["title"] = next(
                line.strip() for line in activity_text.splitlines() if line.strip()
            )
        _append_unique(lesson["outline"], activity_text)
        duration = _numeric(cells.get("G"))
        activity = {
            "row": row_number,
            "text": activity_text,
            "deliveryType": _text(cells.get("F")) or None,
            "durationMinutes": _duration_value(duration),
            "trainer": _text(cells.get("H")) or None,
            "format": _text(cells.get("I")) or None,
            "date": _excel_date(cells.get("J")),
        }
        lesson["activities"].append(activity)
        if re.search(r"\b(?:Assignment|Lab)\b", activity_text, re.IGNORECASE):
            lesson["syllabusAssignments"].append(
                {"row": row_number, "text": activity_text}
            )
    duration = _numeric(cells.get("G"))
    if duration is not None:
        lesson["durationMinutes"] += duration
    objectives = _text(cells.get("E"))
    for objective in objectives.split(","):
        if objective.strip():
            _append_unique(lesson["objectives"], objective.strip())


def _add_resources(lesson, resources_by_id, raw_value, row_number):
    for label, url in _extract_resources(_text(raw_value)):
        normalized = normalize_url(url)
        item_id = resource_id(normalized)
        _append_unique(lesson["resourceIds"], item_id)
        resource = resources_by_id.setdefault(
            item_id,
            {
                "id": item_id,
                "url": normalized,
                "labels": [],
                "lessonIds": [],
                "sourceRows": [],
                "occurrences": [],
            },
        )
        _append_unique(resource["labels"], label)
        _append_unique(resource["lessonIds"], lesson["id"])
        _append_unique(resource["sourceRows"], row_number)
        occurrence = {"lessonId": lesson["id"], "row": row_number, "label": label}
        if occurrence not in resource["occurrences"]:
            resource["occurrences"].append(occurrence)


def _extract_resources(value):
    resources = []
    matches = list(URL_RE.finditer(value))
    for index, match in enumerate(matches):
        start = matches[index - 1].end() if index else 0
        label_text = value[start : match.start()]
        label = re.split(r"[\r\n•]", label_text)[-1].strip().lstrip("-* ")
        label = label.rstrip(":").strip()
        url = match.group(0)
        if not label:
            label = normalize_url(url)
        resources.append((label, url))
    return resources


def _resource_label_for_lesson(resource, lesson_id):
    occurrence = next(
        (
            item
            for item in resource.get("occurrences", [])
            if item["lessonId"] == lesson_id
        ),
        None,
    )
    if occurrence:
        return occurrence["label"]
    return resource["labels"][0]


def _escape_markdown_label(label):
    return label.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def _resource_check_label(resource):
    check = resource.get("check", {})
    status = check.get("status")
    http_status = check.get("httpStatus")
    http_suffix = f" (HTTP {http_status})" if http_status is not None else ""
    labels = {
        "ok": f"truy xuất được{http_suffix}",
        "redirected": f"chuyển hướng và truy xuất được{http_suffix}",
        "blocked": f"bị chặn{http_suffix}",
        "not_found": f"không tìm thấy{http_suffix}",
        "http_error": f"lỗi HTTP{http_suffix}",
        "network_error": "lỗi mạng",
        "content_unreadable": f"truy xuất được nhưng nội dung không thể trích xuất{http_suffix}",
        "invalid": "URL không hợp lệ",
    }
    return labels.get(status, "chưa kiểm tra")


def _excel_date(value):
    serial = _numeric(value)
    if serial is None:
        text = _text(value)
        return text or None
    return (datetime(1899, 12, 30) + timedelta(days=serial)).date().isoformat()


def _duration_value(value):
    if value is None:
        return None
    return int(value) if float(value).is_integer() else value


def _numeric(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _text(value):
    return "" if value is None else str(value).strip()


def _append_unique(items, value):
    if value not in items:
        items.append(value)
