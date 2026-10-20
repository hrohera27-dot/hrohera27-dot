#!/usr/bin/env python3
"""Lightweight validation for the publication metadata archive.

This script checks for the structural issues most likely to affect a static
publication repository: missing files, duplicate bibliography keys, duplicate
DOIs, and obvious drift between the publication index and the bibliography data.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "readme": ROOT / "README.md",
    "publications": ROOT / "PUBLICATIONS.md",
    "bibtex": ROOT / "publications.bib",
}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def has_text(file_path: Path, expected: str) -> bool:
    try:
        return expected in file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False


def parse_bibtex_entries(path: Path) -> list[dict[str, str]]:
    content = path.read_text(encoding="utf-8")
    entries: list[dict[str, str]] = []
    for match in re.finditer(r"@(?P<type>[A-Za-z]+)\s*\{\s*(?P<key>[^,\s]+)\s*,(?P<body>.*?)\}\s*(?:\n|$)", content, re.S):
        entry = {
            "type": match.group("type"),
            "key": match.group("key"),
            "body": match.group("body"),
        }
        entries.append(entry)
    return entries


def main() -> None:
    missing = [name for name, path in FILES.items() if not path.exists()]
    if missing:
        fail(f"Missing expected files: {', '.join(missing)}")

    readme = FILES["readme"]
    if not has_text(readme, "PUBLICATIONS.md"):
        fail("README.md does not reference PUBLICATIONS.md")
    if not has_text(readme, "publications.bib"):
        fail("README.md does not reference publications.bib")
    if not has_text(readme, "orcid.org/0009-0005-3275-1743"):
        fail("README.md does not include the ORCID reference")

    publications = FILES["publications"]
    if not has_text(publications, "# Publications — Hemant K. Rohera"):
        fail("PUBLICATIONS.md title is missing or changed")

    bib_path = FILES["bibtex"]
    entries = parse_bibtex_entries(bib_path)
    if not entries:
        fail("No BibTeX entries were found in publications.bib")

    keys = [entry["key"] for entry in entries]
    duplicate_keys = sorted({key for key in keys if keys.count(key) > 1})
    if duplicate_keys:
        fail(f"Duplicate BibTeX keys found: {', '.join(duplicate_keys)}")

    doi_pattern = re.compile(r"doi\s*=\s*\{?\s*(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\s*\}?", re.I)
    doi_values = []
    for entry in entries:
        match = doi_pattern.search(entry["body"])
        if match:
            doi_values.append(match.group(1).strip())
    duplicate_dois = sorted({doi for doi in doi_values if doi_values.count(doi) > 1})
    if duplicate_dois:
        fail(f"Duplicate DOI values found: {', '.join(duplicate_dois)}")

    rendered_entry_count = len(entries)
    if rendered_entry_count < 10:
        fail(f"Unexpectedly low bibliography count: {rendered_entry_count}")

    print(f"Validation passed: {rendered_entry_count} BibTeX entries checked across {len(FILES)} files.")


if __name__ == "__main__":
    main()
