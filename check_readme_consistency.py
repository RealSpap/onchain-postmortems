#!/usr/bin/env python3
"""
Deterministic self-consistency check for README.md.

This is NOT a re-verification against raw blockchain data. It never touches
a chain, a protocol contract, or any external API. It only checks that the
numbers and cross-references README.md makes about ITSELF actually agree
with each other:

  1. The Loss ($) figures in the index table sum to the "cumulative loss,
     recomputed" figure stated in the "At a glance" block.
  2. The incident count stated in "At a glance" matches the number of rows
     in the index table.
  3. The number of rows in the index table matches the number of incident
     subfolders that actually exist in the repo (a subfolder counts only if
     it has its own README.md; root-level files don't count).
  4. Every footnote marker referenced in the index table has a matching
     footnote definition, and every footnote definition is referenced by at
     least one row (no orphans in either direction).

No LLM call, no network access, no API key. Exit code 0 means everything
that was checked is internally consistent; non-zero means it found a
disagreement, and stderr says exactly which check failed and what the two
disagreeing values were.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
README_PATH = REPO_ROOT / "README.md"

# Directories that are never incident subfolders even though they live at
# repo root, e.g. VCS/CI metadata.
NON_INCIDENT_DIR_PREFIXES = (".",)


class ConsistencyError(Exception):
    """Raised with a message that already states both disagreeing values."""


def fail(message: str) -> None:
    raise ConsistencyError(message)


def read_readme() -> str:
    if not README_PATH.is_file():
        fail(f"README.md not found at expected path: {README_PATH}")
    return README_PATH.read_text(encoding="utf-8")


def extract_section(text: str, heading: str) -> str:
    """Return the text between a '## <heading>' line and the next '## ' line."""
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    if not m:
        fail(f"Could not find a '## {heading}' section in README.md at all. "
             f"The heading may have been renamed or removed.")
    return m.group(1)


def parse_table_rows(section_text: str, header_marker: str) -> list[list[str]]:
    """
    Find the markdown table whose header row contains `header_marker`, skip
    the '|---|...' separator line, and return each subsequent data row as a
    list of trimmed cell strings. Stops at the first line that is not a
    table row.
    """
    lines = section_text.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and header_marker in line:
            header_idx = i
            break
    if header_idx is None:
        fail(f"Could not find a markdown table with header containing "
             f"{header_marker!r} in this section of README.md.")

    # Line after the header must be the '|---|---|...' separator.
    sep_idx = header_idx + 1
    if sep_idx >= len(lines) or not re.match(r"^\|[\s:-]+\|", lines[sep_idx].strip()):
        fail(f"Expected a '|---|---|' separator line right after the table "
             f"header containing {header_marker!r}, did not find one. "
             f"Line was: {lines[sep_idx] if sep_idx < len(lines) else '<EOF>'!r}")

    rows = []
    for line in lines[sep_idx + 1:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        rows.append(cells)
    return rows


def parse_loss_cell(cell: str) -> float:
    """
    Parse a Loss ($) table cell like '≈ 9,131,000 [^moonwell]' or
    '≥ 234,000 [^balancer]' or a plain '174,311 [^cozy]' into a number.
    Handles the approx (≈) and at-least (≥) prefix symbols, and strips
    thousands-separator commas.
    """
    original = cell
    text = re.sub(r"\[\^[^\]]+\]", "", cell)  # drop footnote marker(s)
    text = text.strip()
    text = text.lstrip("≈≥~").strip()          # drop approx/at-least symbols
    text = re.sub(r"^(about|approximately|at least)\s+", "", text, flags=re.IGNORECASE)
    text = text.lstrip("$").strip()
    text = text.replace(",", "")
    m = re.match(r"^(\d+(?:\.\d+)?)", text)
    if not m:
        fail(f"Could not parse a numeric loss figure out of table cell "
             f"{original!r} (Loss ($) column).")
    return float(m.group(1))


def get_index_table_rows(full_text: str) -> list[list[str]]:
    index_section = extract_section(full_text, "Index")
    rows = parse_table_rows(index_section, "Loss ($)")
    if not rows:
        fail("The index table in README.md has a header but zero data rows.")
    return rows


def check_table_sum_matches_glance(full_text: str, table_rows: list[list[str]]) -> None:
    # Expected column order: Protocol | Date | Loss ($) | Chain | Type/Mechanism | Link
    loss_col = 2
    computed_sum = 0.0
    for row in table_rows:
        if len(row) <= loss_col:
            fail(f"Index table row does not have a Loss ($) column at the "
                 f"expected position: {row!r}")
        computed_sum += parse_loss_cell(row[loss_col])
    computed_sum_int = int(round(computed_sum))

    # The "At a glance" table has no distinguishing header text (its header
    # row is just "| | |"), so scan every '| key | value |' row directly
    # instead of relying on parse_table_rows()'s header-marker search.
    glance_section = extract_section(full_text, "At a glance")
    glance_rows = []
    for line in glance_section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and set(cells[0]) != {"-"}:
            glance_rows.append(cells)

    incidents_value = None
    loss_value_text = None
    for cells in glance_rows:
        key = cells[0].strip().lower()
        if key.startswith("incidents covered"):
            incidents_value = cells[1]
        elif key.startswith("cumulative loss"):
            loss_value_text = cells[1]

    if incidents_value is None:
        fail("Could not find the 'Incidents covered' row in the 'At a glance' block.")
    if loss_value_text is None:
        fail("Could not find the 'Cumulative loss, recomputed' row in the "
             "'At a glance' block.")

    # --- incident count: stated vs. table row count ---
    m = re.match(r"^(\d+)", incidents_value.strip())
    if not m:
        fail(f"Could not parse a leading integer out of the 'Incidents "
             f"covered' cell: {incidents_value!r}")
    stated_count = int(m.group(1))
    actual_table_rows = len(table_rows)
    if stated_count != actual_table_rows:
        fail(
            "Incident count mismatch: 'At a glance' states "
            f"{stated_count} incident(s), but the index table has "
            f"{actual_table_rows} row(s)."
        )

    # --- cumulative loss: stated exact figure vs. sum computed from table ---
    m = re.search(r"\$([\d,]+)\s+exactly", loss_value_text)
    if not m:
        fail(
            "Could not find an exact dollar figure of the form "
            "'$<number> exactly' in the 'Cumulative loss, recomputed' cell: "
            f"{loss_value_text!r}"
        )
    stated_sum = int(m.group(1).replace(",", ""))
    if stated_sum != computed_sum_int:
        fail(
            "Cumulative loss mismatch: 'At a glance' states the exact figure "
            f"${stated_sum:,}, but summing the Loss ($) column of the index "
            f"table gives ${computed_sum_int:,}."
        )


def check_table_rows_match_subfolders(table_rows: list[list[str]]) -> None:
    actual_table_rows = len(table_rows)

    subfolders = []
    for entry in sorted(REPO_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        if any(entry.name.startswith(prefix) for prefix in NON_INCIDENT_DIR_PREFIXES):
            continue
        if (entry / "README.md").is_file():
            subfolders.append(entry.name)

    if actual_table_rows != len(subfolders):
        fail(
            "Incident subfolder count mismatch: the index table has "
            f"{actual_table_rows} row(s), but {len(subfolders)} incident "
            f"subfolder(s) with their own README.md exist in the repo: "
            f"{sorted(subfolders)}."
        )


def check_footnotes(full_text: str) -> None:
    index_section = extract_section(full_text, "Index")

    referenced = set(re.findall(r"\[\^([A-Za-z0-9_-]+)\](?!:)", index_section))
    defined = set(re.findall(r"^\[\^([A-Za-z0-9_-]+)\]:", index_section, re.MULTILINE))

    orphaned_references = sorted(referenced - defined)  # used in table, never defined
    unused_definitions = sorted(defined - referenced)   # defined, never used in table

    if orphaned_references or unused_definitions:
        parts = []
        if orphaned_references:
            parts.append(
                f"referenced in the table but never defined as a footnote: "
                f"{orphaned_references}"
            )
        if unused_definitions:
            parts.append(
                f"defined as a footnote but never referenced in the table: "
                f"{unused_definitions}"
            )
        fail("Footnote mismatch: " + "; and ".join(parts) + ".")


def main() -> int:
    try:
        full_text = read_readme()
        table_rows = get_index_table_rows(full_text)
        check_table_sum_matches_glance(full_text, table_rows)
        check_table_rows_match_subfolders(table_rows)
        check_footnotes(full_text)
    except ConsistencyError as exc:
        print(f"README self-consistency check FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"README self-consistency check passed ({len(table_rows)} incidents, "
          f"table sum matches 'At a glance', footnotes balanced).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
