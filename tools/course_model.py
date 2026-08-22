from __future__ import annotations

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
