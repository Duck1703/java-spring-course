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
)


def validate_supplemental_sources(supplemental_path: Path, catalog: dict) -> tuple[list, list[str]]:
    """Structurally validate an authored supplemental-sources file and dry-run
    its merge against `catalog` (a loaded course-catalog.json).

    Reuses `load_supplemental_sources` (structural checks: schema, required
    fields, well-formed URLs, no duplicate URL/resourceId within the file)
    and `merge_supplemental_resources` (identity checks: unknown lesson ids,
    metadata conflicts with an existing same-URL resource) against a deep
    copy of `catalog`, so this validator never mutates its input and never
    reimplements either check.

    Returns `(entries, errors)`. `errors` is a single-item list of the
    formatted failure message on any problem; empty on success.
    """
    try:
        entries = load_supplemental_sources(supplemental_path)
        merge_supplemental_resources(copy.deepcopy(catalog), entries)
    except SupplementalSourceError as error:
        return [], [f"ERROR {error}"]
    return entries, []


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate content/supplemental-sources.json structurally and against course-catalog.json"
    )
    parser.add_argument("--supplemental-sources", required=True, type=Path)
    parser.add_argument("--catalog", required=True, type=Path)
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    try:
        catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"ERROR cannot read catalog {args.catalog}: {error}")
        return 1

    entries, errors = validate_supplemental_sources(args.supplemental_sources, catalog)
    if errors:
        for error in errors:
            print(error)
        return 1

    print(f"PASS supplemental-sources resources={len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
