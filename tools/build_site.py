"""Build the single-file course site: assemble a publication model from
validated content artifacts and embed it into index.html as JSON.

The publication model is a UI-facing projection of the authored corpus:
- every lesson record keeps only fields the interface needs;
- every external reference is reduced to resolved URL/label/status metadata;
- no source-note fact corpus, page text or fallback evidence is embedded.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

EXPECTED_LESSON_IDS = [f"day-{n:02d}" for n in range(1, 39)] + ["day-39-64", "day-65-66"]
GROUP_ORDER = ["java", "spring", "completion"]
EXPECTED_GROUP_COUNTS = {"java": 12, "spring": 24, "completion": 4}

DATA_RE = re.compile(
    r'(<script id="course-data" type="application/json">)(.*?)(</script>)',
    re.DOTALL,
)

LESSON_FIELDS = (
    "id", "unitId", "group", "kind", "title", "summary", "durationMinutes",
    "objectives", "prerequisites", "outcomes", "sections", "commonMistakes",
    "practices", "syllabusAssignments", "enhancedExercises", "references",
)

OJT_EVAL_IDS = {"day-39-64", "day-65-66"}


def _load_lesson_record(lessons_dir: Path, lesson_id: str):
    """Load an authored lesson package, or return None when not yet authored.

    Day files are individual JSON documents; the OJT/Evaluation ranges share
    one combined package per the authoring pipeline.
    """
    if lesson_id in OJT_EVAL_IDS:
        combined = lessons_dir / "ojt-evaluation.json"
        if not combined.exists():
            return None
        payload = _load_json(combined)
        records = payload if isinstance(payload, list) else payload.get("lessons", [])
        return next((r for r in records if r.get("id") == lesson_id), None)
    path = lessons_dir / f"{lesson_id}.json"
    if not path.exists():
        return None
    return _load_json(path)


def _placeholder_lesson(catalog_lessons: dict, lesson_id: str) -> dict:
    entry = catalog_lessons[lesson_id]
    return {
        "id": lesson_id,
        "unitId": entry["unitId"],
        "group": entry["group"],
        "kind": "pending",
        "title": entry["title"],
        "summary": "",
        "durationMinutes": entry.get("durationMinutes"),
        "objectives": [],
        "prerequisites": [],
        "outcomes": [],
        "sections": [],
        "commonMistakes": [],
        "practices": [],
        "syllabusAssignments": [],
        "enhancedExercises": [],
        "references": [],
    }


def _normalize_heading(text: str) -> str:
    """Reduce a heading/locator to comparable ASCII letters+digits only.

    Strips Vietnamese diacritics (NFD decomposition) so 'mục lục' matches
    'muc luc' and heading text compares regardless of tone-mark variance.
    """
    decomposed = unicodedata.normalize("NFD", text.lower())
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    stripped = stripped.replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", "", stripped)


def _citation_locator_matches(record: dict, ref: dict, read: dict) -> bool:
    """A citation is publishable when its sourceUsage entry carries a locator
    that corresponds to a heading recorded in the source's read notes.

    Locators use a leading '§' plus the heading text (e.g. '§2. JVM'); the
    read notes list the page headings verbatim. Punctuation/spacing vary, so
    compare on letters-and-digits-only forms.
    """
    headings = [_normalize_heading(h) for h in read.get("relevantHeadings") or []]
    headings = [h for h in headings if h]
    if not headings:
        return False
    for su in record.get("sourceUsage", []):
        if su.get("id") != ref.get("citationId"):
            continue
        raw_locator = (su.get("locator") or "").strip()
        locator = _normalize_heading(raw_locator)
        if not locator:
            continue
        # Series/TOC pages: the locator explicitly declares the whole page's
        # table of contents ('mục lục'), which the read headings enumerate.
        if "mucluc" in locator or "toc" == locator:
            return True
        for heading in headings:
            if (
                locator == heading
                or heading.endswith(locator)
                or locator.startswith(heading)
            ):
                return True
    return False


def _slim_authored_lesson(
    record: dict,
    catalog_lessons: dict,
    resources_by_id: dict,
    read_by_id: dict,
    limitations: dict,
    published_resources: set,
) -> dict:
    """Project one authored lesson package onto the UI-facing shape."""
    lesson_id = record["id"]
    catalog_ref = record.get("catalogRef", {})
    group = (
        record.get("group")
        or catalog_ref.get("group")
        or catalog_lessons[lesson_id]["group"]
    )

    slim_refs = []
    for ref in record.get("references", []):
        slim = {
            "id": ref["id"],
            "type": ref["type"],
            "resourceId": ref.get("resourceId"),
            "citationId": ref.get("citationId"),
        }
        if ref["type"] == "external":
            rid = ref["resourceId"]
            manifest_rec = resources_by_id.get(rid)
            if manifest_rec is None:
                raise KeyError(f"reference {ref['id']} cites unknown resource {rid}")
            check = manifest_rec.get("check", {})
            read = read_by_id.get(rid, {})
            if read.get("status") != "read":
                raise ValueError(
                    f"reference {ref['id']} ({rid}) is not marked read; "
                    "published citations must come from read sources"
                )
            locator_ok = _citation_locator_matches(record, ref, read)
            if not locator_ok:
                raise ValueError(
                    f"citation {ref['id']} has no locator matched to its read headings"
                )
            published_resources.add(rid)
            slim.update({
                "url": check.get("finalUrl") or manifest_rec.get("requestedUrl"),
                "label": (manifest_rec.get("labelVariants") or [""])[0],
                "checkStatus": check.get("status"),
                "readStatus": read.get("status"),
                "pageTitle": read.get("pageTitle"),
                "limitation": limitations.get(rid),
            })
        slim_refs.append(slim)

    slim_lesson = {field: record[field] for field in LESSON_FIELDS if field in record}
    slim_lesson["group"] = group
    slim_lesson["references"] = slim_refs
    return slim_lesson


def _load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def build_publication_model(
    catalog_path: Path,
    lesson_index_path: Path,
    lessons_dir: Path,
    manifest_path: Path,
    source_notes_dir: Path,
    built_at: str,
) -> dict:
    catalog = _load_json(catalog_path)
    lesson_index = _load_json(lesson_index_path)
    manifest = _load_json(manifest_path)

    catalog_lessons = {lesson["id"]: lesson for lesson in catalog["lessons"]}
    catalog_units = {unit["id"]: unit for unit in catalog["units"]}
    index_ids = [entry["id"] if isinstance(entry, dict) else entry for entry in lesson_index]
    if index_ids != EXPECTED_LESSON_IDS:
        raise ValueError(
            "lesson-index.json order does not match the expected 40-lesson sequence"
        )

    # Resource metadata joined from the manifest (requested/final URL + check)
    # and the per-resource read notes (read status, page title, limitation).
    resources_by_id = {res["resourceId"]: res for res in manifest["resources"]}
    read_by_id: dict[str, dict] = {}
    limitations: dict[str, str] = {}
    for notes_file in sorted(Path(source_notes_dir).glob("*.json")):
        for note in _load_json(notes_file):
            rid = note["resourceId"]
            read = note.get("read", {})
            read_by_id.setdefault(rid, read)
            lim = read.get("limitation") or note.get("fallbackEvidence")
            if isinstance(lim, dict):
                lim = lim.get("limitation") or lim.get("note")
            if lim:
                limitations[rid] = lim

    lessons_out = []
    group_counts = {group: 0 for group in GROUP_ORDER}
    published_resources: set[str] = set()

    for lesson_id in EXPECTED_LESSON_IDS:
        record = _load_lesson_record(lessons_dir, lesson_id)
        if record is None:
            slim_lesson = _placeholder_lesson(catalog_lessons, lesson_id)
        else:
            slim_lesson = _slim_authored_lesson(
                record, catalog_lessons, resources_by_id,
                read_by_id, limitations, published_resources,
            )

        unit = catalog_units.get(slim_lesson.get("unitId"))
        if unit:
            slim_lesson["unitNumber"] = unit["number"]
            slim_lesson["unitTitle"] = unit["title"]
        group_counts[slim_lesson["group"]] += 1
        lessons_out.append(slim_lesson)

    if group_counts != EXPECTED_GROUP_COUNTS:
        raise ValueError(f"group counts {group_counts} != {EXPECTED_GROUP_COUNTS}")

    units_out = [
        {
            "id": unit["id"],
            "number": unit["number"],
            "title": unit["title"],
            "group": unit["group"],
            "lessonIds": unit["lessonIds"],
        }
        for unit in sorted(catalog["units"], key=lambda u: u["number"])
    ]

    resource_cards = []
    for rid in sorted(published_resources):
        rec = resources_by_id[rid]
        check = rec.get("check", {})
        read = read_by_id.get(rid, {})
        resource_cards.append({
            "id": rid,
            "url": check.get("finalUrl") or rec.get("requestedUrl"),
            "label": (rec.get("labelVariants") or [""])[0],
            "checkStatus": check.get("status"),
            "httpStatus": check.get("httpStatus"),
            "readStatus": read.get("status"),
            "pageTitle": read.get("pageTitle"),
            "lessonIds": rec.get("lessonIds", []),
            "limitation": limitations.get(rid),
        })

    return {
        "schemaVersion": 1,
        "app": "java-spring-course",
        "builtAt": built_at,
        "units": units_out,
        "lessons": lessons_out,
        "resources": resource_cards,
    }


def _json_escape_for_script(payload: str) -> str:
    return (
        payload.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def embed_course_data(index_html: str, model: dict) -> str:
    markers = DATA_RE.findall(index_html)
    if len(markers) != 1:
        raise ValueError(
            f"expected exactly one course-data marker, found {len(markers)}"
        )
    payload = json.dumps(model, ensure_ascii=False, separators=(",", ":"))
    payload = _json_escape_for_script(payload)
    return DATA_RE.sub(lambda m: m.group(1) + payload + m.group(3), index_html, count=1)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Embed the course model into index.html")
    parser.add_argument("--catalog", default="course-catalog.json")
    parser.add_argument("--lesson-index", default="content/lesson-index.json")
    parser.add_argument("--lessons-dir", default="content/lessons")
    parser.add_argument("--manifest", default="content/source-manifest.json")
    parser.add_argument("--source-notes-dir", default="content/source-notes")
    parser.add_argument("--output", default="index.html")
    args = parser.parse_args(argv)

    import datetime

    model = build_publication_model(
        catalog_path=Path(args.catalog),
        lesson_index_path=Path(args.lesson_index),
        lessons_dir=Path(args.lessons_dir),
        manifest_path=Path(args.manifest),
        source_notes_dir=Path(args.source_notes_dir),
        built_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )

    output = Path(args.output)
    if output.exists():
        html = output.read_text(encoding="utf-8")
    else:
        shell = Path(__file__).resolve().parents[1] / "index.template.html"
        if not shell.exists():
            print(f"ERROR output {output} does not exist and no index.template.html found", file=sys.stderr)
            return 2
        html = shell.read_text(encoding="utf-8")

    try:
        built = embed_course_data(html, model)
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    fd, tmp_name = tempfile.mkstemp(dir=str(output.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(built)
    Path(tmp_name).replace(output)

    n_practices = sum(len(l.get("practices", [])) for l in model["lessons"])
    n_citations = sum(
        1 for l in model["lessons"] for sec in l.get("sections", [])
        for blk in sec.get("blocks", []) if blk.get("citations")
    ) + sum(len(l.get("references", [])) for l in model["lessons"])
    print(
        f"PASS output={output.name} units={len(model['units'])} "
        f"lessons={len(model['lessons'])} practices={n_practices} "
        f"citations={n_citations} resources={len(model['resources'])} "
        f"external_dependencies=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
