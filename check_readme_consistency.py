#!/usr/bin/env python3
"""
Deterministic self-consistency check across README.md, INDEX.md,
CORRECTIONS.md and the incident subfolders.

This is NOT a re-verification against raw blockchain data. It never touches
a chain or any external API. It only checks that the numbers and
cross-references these files make about EACH OTHER agree.

The Index is grouped by year (### <YYYY>), then by month
(#### <Month name> <YYYY>, optionally suffixed " (current month)"), each
month holding one markdown table of incident rows. Checks:

  1. Every month's stated subtotal equals the sum of its rows' Loss ($)
     figures, and the stated incident count matches the row count.
  2. Every year's stated total and count equal the sum of its months'.
  3. The cumulative total, the recomputed share (rows not marked †) and the
     incident count in README's "At a glance" equal the Index's.
  4. Exactly one month is marked "(current month)", the latest one.
  5. The number of Index rows equals the number of incident subfolders
     (a subfolder counts only if it has its own README.md), and every row's
     Link cell points to an existing subfolder.
  6. Every footnote marker has a definition and vice versa.
  7. The opening bold headline (total, count, recomputed share) matches the
     Index.
  8. The Corrections row count agrees across README and CORRECTIONS.md and
     with the table itself, and the per-type breakdown sums to it.
  9. The number of known floors (≥) stated in README equals the Index's ≥
     cells and the rows of README's floor table.
 10. Every subfolder's registre_hypotheses.csv has the standard header and
     exactly 5 ';'-separated fields per row.

Exit code 0 means everything checked is internally consistent; non-zero
means a disagreement, and stderr says which check failed and the two
disagreeing values.
"""

import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
README_PATH = REPO_ROOT / "README.md"
INDEX_PATH = REPO_ROOT / "INDEX.md"
CORRECTIONS_PATH = REPO_ROOT / "CORRECTIONS.md"

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


def read_file(path: Path) -> str:
    if not path.is_file():
        fail(f"{path.name} not found at expected path: {path}")
    return path.read_text(encoding="utf-8")


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
    Parse a Loss ($) table cell like '≈ 9,131,000 [^moonwell]',
    '≥ † 234,000 [^balancer]' or a plain '174,311 [^cozy]' into a number.
    Handles the approx (≈), at-least (≥) and sourced (†) prefix symbols, and
    strips thousands-separator commas.
    """
    original = cell
    text = re.sub(r"\[\^[^\]]+\]", "", cell)  # drop footnote marker(s)
    text = re.sub(r"^[≈≥†\s]+", "", text.strip())  # drop prefix symbols
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


def loss_prefix(cell: str) -> str:
    return re.match(r"^[≈≥†\s]*", cell.strip()).group(0)


def recomputed_total(all_rows: list) -> int:
    """Sum of the rows NOT marked † (sourced, not recomputed)."""
    return int(round(sum(parse_loss_cell(r[2]) for r in all_rows if "†" not in loss_prefix(r[2]))))


def check_overall_total(full_text: str, years: dict, all_rows: list) -> None:
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
        fail("Could not find the 'Cumulative loss' row in the "
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
            "'$<number> exactly' in the 'Cumulative loss' cell: "
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
    m = re.search(r"\$([\d,]+) of it independently recomputed", loss_value_text)
    if not m:
        fail("Could not find '$<number> of it independently recomputed' in the 'Cumulative loss' cell.")
    stated_recomputed = int(m.group(1).replace(",", ""))
    if stated_recomputed != recomputed_total(all_rows):
        fail(
            f"Recomputed-share mismatch: 'At a glance' states ${stated_recomputed:,}, but the Index "
            f"rows not marked † sum to ${recomputed_total(all_rows):,}."
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
    for row in all_rows:
        m = re.match(r"^\[([^\]]+)\]\(([^)]+)\)$", row[-1])
        target = m.group(2).rstrip("/") if m else None
        if not m or target not in subfolders:
            fail(f"Index row {row[0]!r} links to {row[-1]!r}, not to one of the incident subfolders.")


def check_footnotes(index_text: str) -> None:
    referenced = set(re.findall(r"\[\^([A-Za-z0-9_-]+)\](?!:)", index_text))
    defined = set(re.findall(r"^\[\^([A-Za-z0-9_-]+)\]:", index_text, re.MULTILINE))

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


# Deliberately loose on wording: only the three numbers are pinned, so a prose
# edit of the headline does not break CI (it did on 2026-09-29).
HEADLINE_RE = re.compile(
    r"^\*\*\$([\d.]+)M\b.*?\bacross (\d+) incidents\b.*?\$([\d.]+)M of it independently recomputed",
    re.MULTILINE,
)


def check_headline(full_text: str, years: dict, all_rows: list) -> None:
    """The opening bold sentence restates the total, the incident count and the
    recomputed share in rounded form; checked against the Index."""
    m = HEADLINE_RE.search(full_text)
    if not m:
        fail(
            "Could not find the opening bold headline with '$X.YM ... across N incidents "
            "... $Z.WM of it independently recomputed' at the top of README.md."
        )
    headline_millions, headline_count = m.group(1), int(m.group(2))
    year_count_sum = sum(y["stated_count"] for y in years.values())
    if headline_count != year_count_sum:
        fail(
            f"Headline incident count mismatch: the opening sentence says "
            f"{headline_count}, but summing every year's stated count gives "
            f"{year_count_sum}."
        )
    year_sum = sum(y["stated_total"] for y in years.values())
    expected_millions = f"{year_sum / 1_000_000:.1f}"
    if headline_millions != expected_millions:
        fail(
            f"Headline loss figure mismatch: the opening sentence says "
            f"${headline_millions}M, but the year totals sum to ${year_sum:,} "
            f"(${expected_millions}M rounded to the same precision)."
        )
    expected_recomputed = f"{recomputed_total(all_rows) / 1_000_000:.1f}"
    if m.group(3) != expected_recomputed:
        fail(
            f"Headline recomputed-share mismatch: the opening sentence says ${m.group(3)}M, "
            f"but the Index rows not marked † sum to ${expected_recomputed}M."
        )


CORRECTIONS_INLINE_RE = re.compile(r"one of (\d+) cases\s+in \[Corrections")
CORRECTIONS_GLANCE_RE = re.compile(
    r"^(\d+) entries correct, reconcile.*?\((\d+) corrections, (\d+) reconciliations, (\d+) discoveries"
)
CORRECTIONS_SECTION_ROWS_RE = re.compile(r"The (\d+) rows below\s+are (?:the cases|where)")


def check_corrections_count(readme_text: str, corrections_text: str) -> None:
    """README's intro, README's 'At a glance' row and CORRECTIONS.md's lead
    sentence each state the Corrections row count; the table is a fourth
    source. The per-type breakdown in 'At a glance' must sum to it."""
    inline_m = CORRECTIONS_INLINE_RE.search(readme_text)
    if not inline_m:
        fail("Could not find the 'one of N cases in [Corrections ...' sentence near the top of README.md.")
    glance_section = extract_section(readme_text, "At a glance")
    glance_m = None
    for line in glance_section.splitlines():
        row = parse_table_row(line)
        if row and len(row) >= 2:
            glance_m = CORRECTIONS_GLANCE_RE.search(row[1])
            if glance_m:
                break
    if not glance_m:
        fail("Could not find the 'N entries correct, reconcile ...' row in README.md's 'At a glance' block.")
    section_m = CORRECTIONS_SECTION_ROWS_RE.search(corrections_text)
    if not section_m:
        fail("Could not find 'The N rows below are the cases ...' in CORRECTIONS.md's lead paragraph.")

    table_rows = [
        line for line in corrections_text.splitlines()
        if line.strip().startswith("|") and "Incident" not in line and not re.match(r"^\|[\s:-]+\|", line.strip())
    ]
    stated = {"readme intro": int(inline_m.group(1)), "readme at a glance": int(glance_m.group(1)),
              "corrections.md lead sentence": int(section_m.group(1)), "actual table rows": len(table_rows)}
    if len(set(stated.values())) != 1:
        fail("Corrections row-count mismatch across the repo: " +
             ", ".join(f"{k} says {v}" for k, v in stated.items()) + ".")
    by_type = sum(int(glance_m.group(i)) for i in (2, 3, 4))
    if by_type != stated["actual table rows"]:
        fail(f"Corrections breakdown in 'At a glance' sums to {by_type}, "
             f"but the table has {stated['actual table rows']} rows.")


FLOOR_COUNT_RE = re.compile(r"^- (\d+) entries report a dollar figure that is a known floor", re.MULTILINE)


def check_floors(readme_text: str, all_rows: list) -> None:
    index_floors = sum(1 for r in all_rows if "≥" in loss_prefix(r[2]))
    m = FLOOR_COUNT_RE.search(readme_text)
    if not m:
        fail("Could not find '- N entries report a dollar figure that is a known floor' in README.md.")
    lines = readme_text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith("| Protocol | Why it's a floor |"))
    except StopIteration:
        fail("Could not find README.md's floor table ('| Protocol | Why it's a floor |').")
    table_rows = 0
    for l in lines[start + 2:]:
        if not l.startswith("|"):
            break
        table_rows += 1
    if not int(m.group(1)) == index_floors == table_rows:
        fail(f"Floor count mismatch: README says {m.group(1)}, the Index has {index_floors} '≥' "
             f"cells, README's floor table has {table_rows} rows.")


REGISTRY_HEADER = ["key", "hypothesis", "locator", "falsification_test", "evidence_confidence"]


def check_registries() -> None:
    for path in sorted(REPO_ROOT.glob("*/registre_hypotheses.csv")):
        with path.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh, delimiter=";"))
        if not rows or rows[0] != REGISTRY_HEADER:
            fail(f"{path.parent.name}/registre_hypotheses.csv: header is {rows[0] if rows else None!r}, "
                 f"expected {';'.join(REGISTRY_HEADER)!r}.")
        for n, row in enumerate(rows[1:], start=2):
            if any(c.strip() for c in row) and len(row) != 5:
                fail(f"{path.parent.name}/registre_hypotheses.csv line {n}: {len(row)} fields, expected 5 "
                     f"(a ';' or quote inside a field is probably unquoted).")


def main() -> int:
    try:
        readme_text = read_file(README_PATH)
        index_text = read_file(INDEX_PATH)
        corrections_text = read_file(CORRECTIONS_PATH)
        years, current_month_keys = parse_index(index_text)
        all_rows = check_month_subtotals(years)
        check_year_totals(years)
        check_overall_total(readme_text, years, all_rows)
        check_current_month(years, current_month_keys)
        check_table_rows_match_subfolders(all_rows)
        check_footnotes(index_text)
        check_headline(readme_text, years, all_rows)
        check_corrections_count(readme_text, corrections_text)
        check_floors(readme_text, all_rows)
        check_registries()
    except ConsistencyError as exc:
        print(f"README self-consistency check FAILED: {exc}", file=sys.stderr)
        return 1

    total_months = sum(len(y["months"]) for y in years.values())
    print(
        f"README/INDEX/CORRECTIONS self-consistency check passed ({len(all_rows)} incidents "
        f"across {len(years)} year(s) and {total_months} month(s); month/year/overall totals, "
        f"current-month label, subfolders and links, footnotes, headline, corrections, floors and registries all consistent)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
