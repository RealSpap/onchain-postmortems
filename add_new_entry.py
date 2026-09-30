#!/usr/bin/env python3
"""
Scaffold a new incident subfolder in onchain-postmortems and update
INDEX.md's Index (year -> month grouped) and README.md's "at a glance"
block plus its opening headline sentence to match.

Inspired by SunWeb3Sec/DeFiHackLabs's add_new_entry.py, adapted for this
repo's actual layout: one subfolder per incident, each holding a Python
reconstruction script, a registre_hypotheses.csv falsification registry,
and raw resultats_*.txt script output, rather than DeFiHackLabs's
Foundry-POC-per-year layout.

The Index groups incidents by year, then by month (the incident's primary,
i.e. earliest, date if --date is a range), each month holding its own
table sorted by loss, descending. Every number this script writes, a
month's subtotal, a year's total, and the overall cumulative total and
incident count (in README.md's "at a glance" block AND its opening
headline sentence), is recomputed from the Index itself every time this
script runs, never from a stored counter, so nothing can drift out of sync
with the table data. The script also keeps the "(current month)" label on
whichever month is chronologically latest after the new incident is
inserted.

ADDED 2026-09-29: the Index moved out of README.md into INDEX.md (a
compaction pass, README.md was 459 lines, half of it this table) -- this
script now reads/writes INDEX.md for everything Index-shaped, and
README.md only for "at a glance" + the headline sentence, in two separate
file writes. It never touches CORRECTIONS.md or the "Corrections made"
line, both stay a human judgment call.

Usage:
    python3 add_new_entry.py \\
        --slug new-protocol-incident \\
        --name "New Protocol" \\
        --date 2026-10-01 \\
        --loss-usd 1234567 \\
        --chain "Ethereum" \\
        --category "Bridge" \\
        --mechanism "Reentrancy in the withdraw path" \\
        --readme-url "https://example.com/postmortem"

Use --loss-known-partial when the true loss is known to exceed the number
you can actually source (the same situation as the Sandbox and Balancer V1
entries already in this repo): the table then shows "≥" instead of "≈"
and the combined-loss total is flagged as a floor, matching how those two
existing entries are already handled.
"""
import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
README_PATH = REPO_ROOT / "README.md"
# ADDED 2026-09-29: the Index (year/month tables + footnotes) moved out of
# README.md into its own file, part of a compaction pass (README.md was 459
# lines, half of it this table). This script now writes INDEX.md for
# everything Index-shaped, and only touches README.md for the "At a glance"
# block, which stays there.
INDEX_PATH = REPO_ROOT / "INDEX.md"

MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]
MONTH_INDEX = {name: i + 1 for i, name in enumerate(MONTH_NAMES)}

VALID_CATEGORIES = [
    "Bridge", "Oracle", "Governance", "Key-Compromise",
    "Donation-Attack", "Access-Control", "Rounding/Math-Bug",
]

TABLE_HEADER = "| Protocol | Date | Loss ($) | Chain | Category | Type/Mechanism | Link |"
TABLE_SEPARATOR = "|---|---|---|---|---|---|---|"

ROW_RE = re.compile(
    r"^\|\s*(?P<name>.+?)\s*\|\s*(?P<date>.+?)\s*\|\s*(?P<loss_cell>.+?)\s*\|\s*"
    r"(?P<chain>.+?)\s*\|\s*(?P<category>.+?)\s*\|\s*(?P<mechanism>.+?)\s*\|\s*(?P<link>.+?)\s*\|\s*$"
)

YEAR_HEADING_RE = re.compile(r"^### (\d{4})\s*$")
MONTH_HEADING_RE = re.compile(
    r"^#### (" + "|".join(MONTH_NAMES) + r") (\d{4})(?: \(current month\))?\s*$"
)
YEAR_TOTAL_RE = re.compile(r"^\*\*(\d{4}) total: \$([\d,]+)\*\* across (\d+) incidents?\b(.*)$")
MONTH_SUBTOTAL_RE = re.compile(
    r"^\*\*(" + "|".join(MONTH_NAMES) + r") (\d{4}) subtotal: \$([\d,]+)\*\* across (\d+) incidents?\b(.*)$"
)

LOSS_NUM_RE = re.compile(r"([≈≥]?)\s*([\d][\d\s,]*)")


def parse_loss_cell(cell: str):
    """Returns (float_amount, is_floor) for sorting/summing a loss cell."""
    m = LOSS_NUM_RE.search(cell)
    if not m:
        return 0.0, False
    digits = m.group(2).replace(" ", "").replace(",", "")
    try:
        amount = float(digits)
    except ValueError:
        amount = 0.0
    return amount, m.group(1) == "≥"


def format_loss_cell(loss_usd: float, slug: str, partial: bool) -> str:
    prefix = "≥" if partial else "≈"
    return f"{prefix} {loss_usd:,.0f}" + f" [^{slug}]"


def slugify_heading(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text


def read_readme() -> str:
    if not README_PATH.exists():
        sys.exit(f"README not found at {README_PATH}, this script must run from the repo root.")
    return README_PATH.read_text(encoding="utf-8")


def read_index() -> str:
    if not INDEX_PATH.exists():
        sys.exit(f"INDEX.md not found at {INDEX_PATH}, this script must run from the repo root.")
    return INDEX_PATH.read_text(encoding="utf-8")


def parse_primary_date(date_str: str):
    """--date accepts 'YYYY-MM-DD' or a range like 'YYYY-MM-DD/MM-DD' or
    'YYYY-MM-DD / MM-DD'; the primary (earliest) date is what's used for
    year/month placement."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", date_str.strip())
    if not m:
        sys.exit(f"--date {date_str!r} doesn't start with YYYY-MM-DD.")
    return int(m.group(1)), int(m.group(2))


class MonthBlock:
    def __init__(self, year, month_num, heading_line_idx, rows_start, rows_end,
                 subtotal_line_idx, note_suffix):
        self.year = year
        self.month_num = month_num
        self.heading_line_idx = heading_line_idx
        self.rows_start = rows_start  # index of first table data row
        self.rows_end = rows_end      # exclusive
        self.subtotal_line_idx = subtotal_line_idx
        self.note_suffix = note_suffix  # trailing text after "across N incidents" on subtotal line

    @property
    def key(self):
        return (self.year, self.month_num)


def find_index_bounds(lines):
    """Returns (index_start_idx, index_end_idx) spanning the whole Index
    body in INDEX.md: from its first '### <year>' heading (skipping the
    file's own title + backlink preamble) to EOF -- INDEX.md's entire
    content IS the Index now, there's no wrapping '## Index' heading or a
    trailing '## ' section to stop at (both moved to README.md, unrelated
    file, 2026-09-29)."""
    start = None
    for i, line in enumerate(lines):
        if YEAR_HEADING_RE.match(line):
            start = i
            break
    if start is None:
        sys.exit("Could not find a '### <year>' heading in INDEX.md.")
    return start, len(lines)


def parse_index_structure(lines, index_start, index_end):
    """
    Walks lines[index_start:index_end] and returns a list of MonthBlock in
    document order, plus a dict year -> (year_heading_idx, year_total_line_idx,
    year_note_suffix).
    """
    months = []
    years = {}
    i = index_start
    current_year = None
    while i < index_end:
        line = lines[i]
        ym = YEAR_HEADING_RE.match(line)
        if ym:
            current_year = int(ym.group(1))
            years[current_year] = {"heading_idx": i, "total_idx": None, "note": ""}
            i += 1
            continue
        mm = MONTH_HEADING_RE.match(line)
        if mm:
            month_num = MONTH_INDEX[mm.group(1)]
            heading_idx = i
            j = i + 1
            # find table header
            while j < index_end and lines[j].strip() != TABLE_HEADER:
                if MONTH_HEADING_RE.match(lines[j]) or YEAR_HEADING_RE.match(lines[j]):
                    sys.exit(f"Month section at line {heading_idx+1} has no incident table before the next heading.")
                j += 1
            if j >= index_end:
                sys.exit(f"Month section at line {heading_idx+1} has no incident table.")
            rows_start = j + 2  # skip header + separator
            k = rows_start
            while k < index_end and lines[k].startswith("|"):
                k += 1
            rows_end = k
            # find subtotal line
            m2 = k
            while m2 < index_end and MONTH_SUBTOTAL_RE.match(lines[m2]) is None:
                if MONTH_HEADING_RE.match(lines[m2]) or YEAR_HEADING_RE.match(lines[m2]):
                    sys.exit(f"Month section at line {heading_idx+1} has no subtotal line.")
                m2 += 1
            if m2 >= index_end:
                sys.exit(f"Month section at line {heading_idx+1} has no subtotal line.")
            sub_m = MONTH_SUBTOTAL_RE.match(lines[m2])
            note_suffix = sub_m.group(5)
            months.append(MonthBlock(current_year, month_num, heading_idx, rows_start, rows_end, m2, note_suffix))
            i = m2 + 1
            continue
        ytot = YEAR_TOTAL_RE.match(line)
        if ytot:
            y = int(ytot.group(1))
            years[y]["total_idx"] = i
            years[y]["note"] = ytot.group(4)
            i += 1
            continue
        i += 1
    return months, years


def rows_in_block(lines, block: MonthBlock):
    rows = []
    for idx in range(block.rows_start, block.rows_end):
        m = ROW_RE.match(lines[idx])
        if m:
            rows.append((idx, m))
    return rows


def month_sum_and_floor(lines, block: MonthBlock):
    total = 0.0
    floor_names = []
    for idx, m in rows_in_block(lines, block):
        amount, is_floor = parse_loss_cell(m.group("loss_cell"))
        total += amount
        if is_floor:
            floor_names.append(m.group("name"))
    return total, floor_names


def build_note(floor_names):
    if not floor_names:
        return ""
    plural = "figure" if len(floor_names) == 1 else "figures"
    return f" Includes {len(floor_names)} known floor {plural} ({', '.join(floor_names)}), so the true total is higher."


def build_year_note(has_floor):
    if not has_floor:
        return ""
    return " At least one entry this year is a known floor, so the true total is higher."


def scaffold_subfolder(slug: str, name: str, date: str, chain: str):
    folder = REPO_ROOT / slug
    if folder.exists():
        sys.exit(f"{folder} already exists, pick a different --slug or edit it by hand.")
    folder.mkdir(parents=True)
    (folder / "README.md").write_text(README_STUB.format(name=name, chain=chain, date=date), encoding="utf-8")
    (folder / "reconstruct_exploit.py").write_text(SCRIPT_STUB.format(name=name, chain=chain, date=date), encoding="utf-8")
    (folder / "registre_hypotheses.csv").write_text(REGISTRE_HEADER, encoding="utf-8")
    (folder / ".gitignore").write_text("__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n.DS_Store\n", encoding="utf-8")
    print(f"Scaffold created in {folder}")
    return folder


README_STUB = """# {name} Postmortem

Independent on-chain reconstruction of the {name} incident ({chain}, {date}).
TODO: one paragraph, what happened, and what this reconstruction adds beyond
whatever press or the protocol itself already published.

## At a glance

| | |
|---|---|
| Incident | TODO |
| Window | {date} |
| Press figure | TODO, cite the outlet |
| Verified independently | TODO |

## The method

TODO: starting anchor (the protocol's own GitHub deployment records, not a
block explorer search), RPC endpoints used, how the incident window was
located.

```bash
pip install web3
python3 reconstruct_exploit.py
```

## What it found

TODO.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with {name} or any outlet cited above.
- TODO: anything not independently confirmed.

## License

MIT
"""

SCRIPT_STUB = '''"""
Independent on-chain reconstruction of the {name} incident ({chain}, {date}).
TODO: fill in the starting anchor (a primary-source deployment address or
registry file), the RPC endpoint(s) used, and the steps that follow it.
Every number this script prints should be read live from the chain, not
hardcoded from a press figure.
"""
from web3 import Web3

RPC = "TODO"
w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={{"timeout": 30}}))

if __name__ == "__main__":
    print("=== Step 1: TODO ===")
'''

REGISTRE_HEADER = "key;hypothesis;locator;falsification_test;evidence_confidence\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--slug", required=True, help="folder name, e.g. new-protocol-incident")
    p.add_argument("--name", required=True, help="human-readable protocol name, e.g. 'New Protocol'")
    p.add_argument("--date", required=True, help="ISO date or range, e.g. 2026-10-01 or 2026-10-01/02")
    p.add_argument("--loss-usd", required=True, type=float, help="loss in dollars, bare number, e.g. 1234567")
    p.add_argument("--chain", required=True, help="chain, e.g. Ethereum, Base, 'Ethereum + Base'")
    p.add_argument("--category", required=True, choices=VALID_CATEGORIES,
                    help="controlled tag for the Index's Category column")
    p.add_argument("--mechanism", required=True, help="real type/mechanism, not the incident's name")
    p.add_argument("--link", help="subfolder link in the table, defaults to '<slug>/'")
    p.add_argument("--readme-url", default="", help="optional external URL to note in the README stub")
    p.add_argument(
        "--loss-known-partial",
        action="store_true",
        help="the real loss exceeds this figure but the source doesn't support claiming more (like Sandbox, Balancer V1)",
    )
    p.add_argument("--skip-scaffold", action="store_true", help="don't create the subfolder, only update the README")
    args = p.parse_args()

    link = args.link or f"{args.slug}/"
    target_year, target_month = parse_primary_date(args.date)

    if not args.skip_scaffold:
        scaffold_subfolder(args.slug, args.name, args.date, args.chain)
        if args.readme_url:
            readme_path = REPO_ROOT / args.slug / "README.md"
            text = readme_path.read_text(encoding="utf-8")
            text += f"\n<!-- external source: {args.readme_url} -->\n"
            readme_path.write_text(text, encoding="utf-8")

    content = read_index()
    lines = content.splitlines()
    index_start, index_end = find_index_bounds(lines)
    months, years = parse_index_structure(lines, index_start, index_end)

    loss_cell = format_loss_cell(args.loss_usd, args.slug, args.loss_known_partial)
    new_row = (f"| {args.name} | {args.date} | {loss_cell} | {args.chain} | "
               f"{args.category} | {args.mechanism} | [{link}]({link}) |")

    target = None
    for block in months:
        if block.key == (target_year, target_month):
            target = block
            break

    if target is not None:
        # Insert into the existing month's table, sorted by loss descending.
        existing_rows = rows_in_block(lines, target)
        parsed = []
        for idx, m in existing_rows:
            amount, _ = parse_loss_cell(m.group("loss_cell"))
            parsed.append((amount, lines[idx]))
        parsed.append((args.loss_usd, new_row))
        parsed.sort(key=lambda pair: pair[0], reverse=True)
        new_table_rows = [row for _, row in parsed]
        lines = lines[:target.rows_start] + new_table_rows + lines[target.rows_end:]
    else:
        # Need a new month section, possibly inside an existing year, possibly a new year too.
        month_heading_text = f"{MONTH_NAMES[target_month - 1]} {target_year}"
        new_block_lines = [
            f"#### {month_heading_text}",
            "",
            TABLE_HEADER,
            TABLE_SEPARATOR,
            new_row,
            "",
            f"**{month_heading_text} subtotal: ${args.loss_usd:,.0f}** across 1 incident.",
            "",
        ]
        if target_year in years:
            # Insert in descending-month order within the year.
            year_months = [b for b in months if b.year == target_year]
            insert_before = None
            for b in year_months:
                if b.month_num < target_month:
                    insert_before = b
                    break
            if insert_before is not None:
                insert_at = insert_before.heading_line_idx
            else:
                # goes after the last month of this year (or right after the
                # year total line if that's the only thing there)
                last_month = year_months[-1]
                insert_at = last_month.subtotal_line_idx + 2  # after blank line following subtotal
            lines = lines[:insert_at] + new_block_lines + lines[insert_at:]
        else:
            # Brand new year section. Insert in descending-year order.
            all_years_sorted = sorted(years.keys(), reverse=True)
            insert_at = None
            for y in all_years_sorted:
                if y < target_year:
                    insert_at = years[y]["heading_idx"]
                    break
            if insert_at is None:
                insert_at = index_end
            year_block_lines = [
                f"### {target_year}",
                "",
                f"**{target_year} total: ${args.loss_usd:,.0f}** across 1 incident "
                f"(1 month, {month_heading_text.split()[0]} through {month_heading_text.split()[0]}).",
                "",
            ] + new_block_lines
            lines = lines[:insert_at] + year_block_lines + lines[insert_at:]

    # Re-parse from scratch now that the table/structure changed, then
    # recompute every subtotal/total purely from the row data.
    index_start, index_end = find_index_bounds(lines)
    months, years = parse_index_structure(lines, index_start, index_end)

    # Recompute month subtotals (in place, iterating in reverse document
    # order so earlier line indices stay valid as we rewrite lines).
    for block in sorted(months, key=lambda b: b.subtotal_line_idx, reverse=True):
        total, floor_names = month_sum_and_floor(lines, block)
        month_name = MONTH_NAMES[block.month_num - 1]
        count = len(rows_in_block(lines, block))
        note = build_note(floor_names)
        lines[block.subtotal_line_idx] = (
            f"**{month_name} {block.year} subtotal: ${total:,.0f}** across "
            f"{count} incident{'s' if count != 1 else ''}.{note}"
        )

    # Recompute year totals from their months' (just-recomputed) subtotals.
    for year, ydata in years.items():
        year_months = [b for b in months if b.year == year]
        year_total = 0.0
        year_count = 0
        has_floor = False
        for b in year_months:
            total, floor_names = month_sum_and_floor(lines, b)
            year_total += total
            year_count += len(rows_in_block(lines, b))
            has_floor = has_floor or bool(floor_names)
        month_span = sorted({b.month_num for b in year_months})
        span_text = f"{len(month_span)} month{'s' if len(month_span)!=1 else ''}, {MONTH_NAMES[month_span[0]-1]} through {MONTH_NAMES[month_span[-1]-1]}"
        note = build_year_note(has_floor)
        lines[ydata["total_idx"]] = (
            f"**{year} total: ${year_total:,.0f}** across {year_count} incidents ({span_text}).{note}"
        )

    # Move the "(current month)" label to whichever month is now latest.
    index_start, index_end = find_index_bounds(lines)
    months, years = parse_index_structure(lines, index_start, index_end)
    latest_key = max(b.key for b in months)
    for block in months:
        heading_line = lines[block.heading_line_idx]
        mm = MONTH_HEADING_RE.match(heading_line)
        month_heading_text = f"{mm.group(1)} {mm.group(2)}"
        is_current = block.key == latest_key
        lines[block.heading_line_idx] = f"#### {month_heading_text}" + (" (current month)" if is_current else "")

    # Recompute overall totals from the years' stated totals -- these now feed
    # README.md's "At a glance" block AND its opening headline sentence
    # (ADDED 2026-09-29: both moved/added when the Index moved out to its own
    # file; neither is INDEX.md's own content, so update README.md separately
    # below instead of writing these into `lines`, which is INDEX.md's).
    index_start, index_end = find_index_bounds(lines)
    months, years = parse_index_structure(lines, index_start, index_end)
    overall_total = sum(month_sum_and_floor(lines, b)[0] for b in months)
    overall_count = sum(len(rows_in_block(lines, b)) for b in months)
    overall_has_floor = any(month_sum_and_floor(lines, b)[1] for b in months)
    total_str = f"{overall_total:,.0f}"
    total_m = round(overall_total / 100_000) / 10  # nearest 0.1M
    floor_note = (
        " At least one entry is a known floor, so the real total is higher."
        if overall_has_floor else ""
    )

    # Add a placeholder footnote for the new entry if one doesn't already exist.
    joined = "\n".join(lines)
    footnote_marker = f"[^{args.slug}]:"
    if footnote_marker not in joined:
        index_start, index_end = find_index_bounds(lines)
        i = index_end
        while i > index_start and not lines[i - 1].startswith("[^"):
            i -= 1
        insertion_point = i
        j = insertion_point
        while j < index_end and lines[j].startswith("[^"):
            j += 1
        footnote_text = f"[^{args.slug}]: TODO, cite the exact source file and figure behind {args.loss_usd:,.0f} dollars."
        if args.readme_url:
            footnote_text += f" External source: {args.readme_url}."
        lines = lines[:j] + [footnote_text] + lines[j:]

    INDEX_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # README.md: "At a glance" table (Incidents covered / Cumulative loss rows)
    # and the opening headline sentence, both recomputed from the same
    # overall_total/overall_count just derived from INDEX.md -- kept as two
    # separate writes to two separate files, never both baked into one.
    readme_lines = read_readme().splitlines()
    new_incidents_line = f"| Incidents covered | {overall_count}, independently reconstructed on-chain, see [the full index](INDEX.md) for detail |"
    new_loss_line = (
        f"| Cumulative loss, recomputed | About ${total_m:.1f}M across the {overall_count} "
        f"incidents (${total_str} exactly, sum of the figures in the index)."
        f"{floor_note} |"
    )
    new_headline = (
        f"**${total_m:.1f}M in DeFi and on-chain losses, "
        f"independently recomputed from raw chain data across {overall_count} "
        f"incidents.**"
    )
    for idx, line in enumerate(readme_lines):
        if line.startswith("| Incidents covered |"):
            readme_lines[idx] = new_incidents_line
        elif line.startswith("| Cumulative loss, recomputed |"):
            readme_lines[idx] = new_loss_line
        elif line.startswith("**$") and "in DeFi and on-chain losses" in line:
            readme_lines[idx] = new_headline
    README_PATH.write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

    index_start, index_end = find_index_bounds(lines)
    months, years = parse_index_structure(lines, index_start, index_end)
    final_count = sum(len(rows_in_block(lines, b)) for b in months)
    final_total = sum(month_sum_and_floor(lines, b)[0] for b in months)
    print(f"INDEX.md and README.md updated: {final_count} incidents, cumulative loss ${final_total:,.0f}.")
    print(f"Fill in the TODO in {args.slug}/README.md, {args.slug}/reconstruct_exploit.py, and the [^{args.slug}] footnote before publishing.")


if __name__ == "__main__":
    main()
