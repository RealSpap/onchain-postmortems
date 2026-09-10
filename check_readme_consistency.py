#!/usr/bin/env python3
"""
Deterministic self-consistency check for README.md.

This is NOT a re-verification against raw blockchain data. It never touches
a chain, a protocol contract, or any external API. It only checks that the
numbers and cross-references README.md makes about ITSELF actually agree
with each other.

The Index is grouped by year (### <YYYY>), then by month
(#### <Month name> <YYYY>, optionally suffixed " (current month)"), each
month holding one markdown table of incident rows. This script walks that
structure and checks:

  1. Every month's stated subtotal equals the sum of its own rows' Loss ($)
     figures, and the stated per-month incident count matches the row count.
  2. Every year's stated total equals the sum of its months' STATED
     subtotals (not recomputed independently, so this specifically checks
     the month -> year rollup), and the stated per-year incident count
     matches the sum of its months' counts.
  3. The overall cumulative total and incident count stated in "At a
     glance" equal the sum of the years' STATED totals and counts (the
     year -> overall rollup).
  4. Exactly one month is marked "(current month)", and it is the
     chronologically latest month that actually has a section.
  5. The number of incident rows across the whole Index matches the number
     of incident subfolders that actually exist in the repo (a subfolder
     counts only if it has its own README.md; root-level files don't
     count).
  6. Every footnote marker referenced anywhere in the Index has a matching
     footnote definition, and every footnote definition is referenced by
     at least one row (no orphans in either direction).

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

MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]
MONTH_INDEX = {name: i + 1 for i, name in enumerate(MONTH_NAMES)}

YEAR_HEADING_RE = re.compile(r"^### (\d{4})\s*$")
MONTH_HEADING_RE = re.compile(
    r"^#### (" + "|".join(MONTH_NAMES) + r") (\d{4})(?: \(current month\))?\s*$"
)
YEAR_TOTAL_RE = re.compile(
    r"^\*\*(\d{4}) total: \$([\d,]+)\*\* across (\d+) incidents?\b"
)
MONTH_SUBTOTAL_RE = re.compile(
    r"^\*\*(" + "|".join(MONTH_NAMES) + r") (\d{4}) subtotal: \$([\d,]+)\*\* across (\d+) incidents?\b"
)


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


def parse_table_row(line: str):
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    return [c.strip() for c in stripped.strip("|").split("|")]


class MonthSection:
    def __init__(self, year: int, month_num: int, is_current: bool):
        self.year = year
        self.month_num = month_num
        self.is_current = is_current
        self.rows = []  # list of cell-lists
        self.stated_subtotal = None
        self.stated_count = None

    @property
    def key(self):
        return (self.year, self.month_num)


def parse_index(index_text: str):
    """
    Walk the Index section line by line, returning:
      years: dict[int -> {"stated_total": int, "stated_count": int, "months": [MonthSection,...]}]
      current_month_keys: list of (year, month_num) marked "(current month)"
    """
    lines = index_text.splitlines()
    years = {}
    current_year = None
    current_month_section = None
    current_month_keys = []
    i = 0
    n = len(lines)
    header_marker = "Loss ($)"

    while i < n:
        line = lines[i]

        ym = YEAR_HEADING_RE.match(line)
        if ym:
            current_year = int(ym.group(1))
            if current_year in years:
                fail(f"Year heading '### {current_year}' appears more than once in the Index.")
            years[current_year] = {"stated_total": None, "stated_count": None, "months": []}
            current_month_section = None
            i += 1
            continue

        mm = MONTH_HEADING_RE.match(line)
        if mm:
            if current_year is None:
                fail(f"Month heading {line!r} appears before any '### <year>' heading.")
            month_name, year_in_heading = mm.group(1), int(mm.group(2))
            if year_in_heading != current_year:
                fail(
                    f"Month heading {line!r} states year {year_in_heading}, "
                    f"but it sits under the '### {current_year}' section."
                )
            month_num = MONTH_INDEX[month_name]
            is_current = line.rstrip().endswith("(current month)")
            current_month_section = MonthSection(current_year, month_num, is_current)
            years[current_year]["months"].append(current_month_section)
            if is_current:
                current_month_keys.append((current_year, month_num))
            i += 1
            continue

        # Table header row for a month's incident table.
        if line.strip().startswith("|") and header_marker in line:
            if current_month_section is None:
                fail(f"Found an incident table (header {line!r}) before any month heading.")
            sep_i = i + 1
            if sep_i >= n or not re.match(r"^\|[\s:-]+\|", lines[sep_i].strip()):
                fail(
                    f"Expected a '|---|---|' separator line right after the table "
                    f"header {line!r}, did not find one."
                )
            j = sep_i + 1
            while j < n and lines[j].strip().startswith("|"):
                row = parse_table_row(lines[j])
                if row is not None:
                    current_month_section.rows.append(row)
                j += 1
            i = j
            continue

        ytot = YEAR_TOTAL_RE.match(line)
        if ytot:
            y = int(ytot.group(1))
            if y != current_year:
                fail(
                    f"Line {line!r} states a total for year {y}, but it appears "
                    f"under the '### {current_year}' section."
                )
            years[y]["stated_total"] = int(ytot.group(2).replace(",", ""))
            years[y]["stated_count"] = int(ytot.group(3))
            i += 1
            continue

        msub = MONTH_SUBTOTAL_RE.match(line)
        if msub:
            month_name, y = msub.group(1), int(msub.group(2))
            if current_month_section is None or current_month_section.year != y or \
                    current_month_section.month_num != MONTH_INDEX[month_name]:
                fail(f"Subtotal line {line!r} does not follow its matching month heading.")
            current_month_section.stated_subtotal = int(msub.group(3).replace(",", ""))
            current_month_section.stated_count = int(msub.group(4))
            i += 1
            continue

        i += 1

    if not years:
        fail("Found no '### <year>' sections in the Index. The year/month structure may be missing.")

    return years, current_month_keys


def check_month_subtotals(years: dict) -> list:
    """Returns the flat list of all row cell-lists across every month, for later checks."""
    all_rows = []
    loss_col = 2  # Protocol | Date | Loss ($) | Chain | Category | Type/Mechanism | Link
    for year, ydata in years.items():
        for month in ydata["months"]:
            if month.stated_subtotal is None:
                fail(
                    f"No '**<Month> {year} subtotal: ...**' line found for month "
                    f"{MONTH_NAMES[month.month_num - 1]} {year}."
                )
            if not month.rows:
                fail(f"{MONTH_NAMES[month.month_num - 1]} {year} has a heading but zero incident rows.")
            computed = 0.0
            for row in month.rows:
                if len(row) <= loss_col:
                    fail(
                        f"A row in {MONTH_NAMES[month.month_num - 1]} {year} does not have a "
                        f"Loss ($) column at the expected position: {row!r}"
                    )
                computed += parse_loss_cell(row[loss_col])
            computed_int = int(round(computed))
            if computed_int != month.stated_subtotal:
                fail(
                    f"Month subtotal mismatch for {MONTH_NAMES[month.month_num - 1]} {year}: "
                    f"stated ${month.stated_subtotal:,}, but summing its {len(month.rows)} "
                    f"row(s) gives ${computed_int:,}."
                )
            if len(month.rows) != month.stated_count:
                fail(
                    f"Month incident-count mismatch for {MONTH_NAMES[month.month_num - 1]} {year}: "
                    f"stated {month.stated_count}, but the table has {len(month.rows)} row(s)."
                )
            all_rows.extend(month.rows)
    return all_rows


def check_year_totals(years: dict) -> None:
    for year, ydata in years.items():
        if ydata["stated_total"] is None:
            fail(f"No '**{year} total: ...**' line found for the '### {year}' section.")
        month_sum = sum(m.stated_subtotal for m in ydata["months"])
        month_count_sum = sum(m.stated_count for m in ydata["months"])
        if month_sum != ydata["stated_total"]:
            fail(
                f"Year total mismatch for {year}: stated ${ydata['stated_total']:,}, "
                f"but summing its {len(ydata['months'])} month subtotal(s) gives ${month_sum:,}."
            )
        if month_count_sum != ydata["stated_count"]:
            fail(
                f"Year incident-count mismatch for {year}: stated {ydata['stated_count']}, "
                f"but summing its months' counts gives {month_count_sum}."
            )


def check_overall_total(full_text: str, years: dict) -> None:
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

    m = re.match(r"^(\d+)", incidents_value.strip())
    if not m:
        fail(f"Could not parse a leading integer out of the 'Incidents "
             f"covered' cell: {incidents_value!r}")
    stated_overall_count = int(m.group(1))
    year_count_sum = sum(y["stated_count"] for y in years.values())
    if stated_overall_count != year_count_sum:
        fail(
            "Incident count mismatch: 'At a glance' states "
            f"{stated_overall_count} incident(s), but summing every year's stated "
            f"count gives {year_count_sum}."
        )

    m = re.search(r"\$([\d,]+)\s+exactly", loss_value_text)
    if not m:
        fail(
            "Could not find an exact dollar figure of the form "
            "'$<number> exactly' in the 'Cumulative loss, recomputed' cell: "
            f"{loss_value_text!r}"
        )
    stated_overall_sum = int(m.group(1).replace(",", ""))
    year_sum = sum(y["stated_total"] for y in years.values())
    if stated_overall_sum != year_sum:
        fail(
            "Cumulative loss mismatch: 'At a glance' states the exact figure "
            f"${stated_overall_sum:,}, but summing every year's stated total gives "
            f"${year_sum:,}."
        )


def check_current_month(years: dict, current_month_keys: list) -> None:
    all_keys = [m.key for y in years.values() for m in y["months"]]
    latest = max(all_keys)
    if len(current_month_keys) == 0:
        fail(
            "No month heading is marked '(current month)'. The month "
            f"{MONTH_NAMES[latest[1]-1]} {latest[0]} (the chronologically latest "
            "with a section) should be."
        )
    if len(current_month_keys) > 1:
        fail(
            "More than one month heading is marked '(current month)': "
            f"{[f'{MONTH_NAMES[m-1]} {y}' for (y, m) in current_month_keys]}."
        )
    marked = current_month_keys[0]
    if marked != latest:
        fail(
            f"'(current month)' is on {MONTH_NAMES[marked[1]-1]} {marked[0]}, but the "
            f"chronologically latest month with a section is {MONTH_NAMES[latest[1]-1]} {latest[0]}."
        )


def check_table_rows_match_subfolders(all_rows: list) -> None:
    actual_row_count = len(all_rows)

    subfolders = []
    for entry in sorted(REPO_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        if any(entry.name.startswith(prefix) for prefix in NON_INCIDENT_DIR_PREFIXES):
            continue
        if (entry / "README.md").is_file():
            subfolders.append(entry.name)

    if actual_row_count != len(subfolders):
        fail(
            "Incident subfolder count mismatch: the Index has "
            f"{actual_row_count} row(s) total, but {len(subfolders)} incident "
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
                f"referenced in a table but never defined as a footnote: "
                f"{orphaned_references}"
            )
        if unused_definitions:
            parts.append(
                f"defined as a footnote but never referenced in any table: "
                f"{unused_definitions}"
            )
        fail("Footnote mismatch: " + "; and ".join(parts) + ".")


def main() -> int:
    try:
        full_text = read_readme()
        index_section = extract_section(full_text, "Index")
        years, current_month_keys = parse_index(index_section)
        all_rows = check_month_subtotals(years)
        check_year_totals(years)
        check_overall_total(full_text, years)
        check_current_month(years, current_month_keys)
        check_table_rows_match_subfolders(all_rows)
        check_footnotes(full_text)
    except ConsistencyError as exc:
        print(f"README self-consistency check FAILED: {exc}", file=sys.stderr)
        return 1

    total_months = sum(len(y["months"]) for y in years.values())
    print(
        f"README self-consistency check passed ({len(all_rows)} incidents across "
        f"{len(years)} year(s) and {total_months} month(s); month/year/overall totals, "
        f"current-month label, subfolder count, and footnotes all consistent)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
