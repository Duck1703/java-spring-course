from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.course_model import (
    SupplementalSourceError,
    load_supplemental_sources,
    merge_supplemental_resources,
    normalize_url,
    parse_schedule,
    render_catalog_markdown,
)


BATCH_BY_UNIT = {
    1: "java-foundations",
    2: "java-foundations",
    3: "java-advanced",
    4: "java-advanced",
    5: "spring-core-web",
    6: "spring-core-web",
    7: "data-security",
    8: "data-security",
    9: "production",
    10: "production",
    11: "project-final",
    12: "project-final",
    13: "project-final",
}


def _index_previous_resources(previous_manifest: dict | None) -> dict:
    if previous_manifest is None:
        return {}
    if not isinstance(previous_manifest, dict):
        raise ValueError("previous manifest root must be an object")
    resources = previous_manifest.get("resources")
    if not isinstance(resources, list):
        raise ValueError("previous manifest must contain a resources list")

    by_id = {}
    for index, resource in enumerate(resources):
        location = f"previous manifest resources[{index}]"
        if not isinstance(resource, dict):
            raise ValueError(f"{location} must be an object")
        resource_id = resource.get("resourceId")
        if not isinstance(resource_id, str) or not resource_id:
            raise ValueError(f"{location} must contain a nonempty resourceId")
        if resource_id in by_id:
            raise ValueError(f"previous manifest contains duplicate resourceId: {resource_id}")
        requested_url = resource.get("requestedUrl")
        if not isinstance(requested_url, str) or not requested_url:
            raise ValueError(f"{location} must contain a nonempty requestedUrl")
        if not isinstance(resource.get("check"), dict):
            raise ValueError(f"{location} check must be an object")
        by_id[resource_id] = resource
    return by_id


def _load_previous_manifest(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read previous manifest {path}: {error}") from error


def build_manifest(catalog: dict, previous_manifest: dict | None = None) -> dict:
    lessons = {lesson["id"]: lesson for lesson in catalog["lessons"]}
    units = {unit["id"]: unit for unit in catalog["units"]}
    previous_by_id = _index_previous_resources(previous_manifest)
    records = []
    for resource in catalog["resources"]:
        lesson_ids = list(resource["lessonIds"])
        unit_ids = []
        outline = []
        for lesson_id in lesson_ids:
            lesson = lessons[lesson_id]
            if lesson["unitId"] not in unit_ids:
                unit_ids.append(lesson["unitId"])
            for text in lesson["outline"]:
                if text not in outline:
                    outline.append(text)
        first_unit_number = units[unit_ids[0]]["number"]
        previous = previous_by_id.get(resource["id"])
        check = {}
        if (
            previous is not None
            and normalize_url(previous["requestedUrl"]) == normalize_url(resource["url"])
        ):
            check = copy.deepcopy(previous["check"])
        if check:
            resource["check"] = copy.deepcopy(check)
        records.append(
            {
                "resourceId": resource["id"],
                "requestedUrl": resource["url"],
                "labelVariants": list(resource["labels"]),
                "lessonIds": lesson_ids,
                "unitIds": unit_ids,
                "relevantOutline": outline,
                "assignedBatch": BATCH_BY_UNIT[first_unit_number],
                "check": check,
            }
        )
    return {
        "schemaVersion": 1,
        "generatedAt": catalog["generatedAt"],
        "source": catalog["source"],
        "resources": records,
    }


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Extract the Java/Spring course catalog")
    parser.add_argument("--workbook", required=True, type=Path)
    parser.add_argument("--json", required=True, type=Path)
    parser.add_argument("--markdown", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument(
        "--supplemental-sources",
        type=Path,
        default=None,
        help=(
            "Optional content/supplemental-sources.json of authored, non-workbook "
            "resources to merge in. Omit for exact current behavior."
        ),
    )
    args = parser.parse_args(argv)

    catalog = parse_schedule(args.workbook)

    if args.supplemental_sources is not None:
        try:
            supplemental_entries = load_supplemental_sources(args.supplemental_sources)
            merge_supplemental_resources(catalog, supplemental_entries)
        except SupplementalSourceError as error:
            print(f"ERROR supplemental-sources: {error}")
            return 1

    try:
        previous_manifest = _load_previous_manifest(args.manifest)
        manifest = build_manifest(catalog, previous_manifest)
    except ValueError as error:
        print(f"ERROR previous manifest: {error}")
        return 1
    write_json(args.json, catalog)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(render_catalog_markdown(catalog), encoding="utf-8")
    write_json(args.manifest, manifest)

    day_resource_refs = sum(len(lesson["resourceIds"]) for lesson in catalog["lessons"])
    print(
        f"PASS units={len(catalog['units'])} lessons={len(catalog['lessons'])} "
        f"day_resource_refs={day_resource_refs} unique_resources={len(catalog['resources'])}"
    )
    print(f"PASS output={args.json}")
    print(f"PASS output={args.markdown}")
    print(f"PASS output={args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
