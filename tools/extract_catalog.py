from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.course_model import parse_schedule, render_catalog_markdown


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


def build_manifest(catalog: dict) -> dict:
    lessons = {lesson["id"]: lesson for lesson in catalog["lessons"]}
    units = {unit["id"]: unit for unit in catalog["units"]}
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
        records.append(
            {
                "resourceId": resource["id"],
                "requestedUrl": resource["url"],
                "labelVariants": list(resource["labels"]),
                "lessonIds": lesson_ids,
                "unitIds": unit_ids,
                "relevantOutline": outline,
                "assignedBatch": BATCH_BY_UNIT[first_unit_number],
                "check": {},
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
    args = parser.parse_args(argv)

    catalog = parse_schedule(args.workbook)
    manifest = build_manifest(catalog)
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
