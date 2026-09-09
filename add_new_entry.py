#!/usr/bin/env python3
"""
Scaffold a new incident subfolder in onchain-postmortems and update the
root README's index table and "at a glance" block to match.

Inspired by SunWeb3Sec/DeFiHackLabs's add_new_entry.py, adapted for this
repo's actual layout: one subfolder per incident, each holding a Python
reconstruction script, a registre_hypotheses.csv falsification registry,
and raw resultats_*.txt script output, rather than DeFiHackLabs's
Foundry-POC-per-year layout.

The "at a glance" incident count and combined-loss line are recomputed
from the index table itself every time this script runs, not from a
stored counter, so they cannot drift out of sync with the table.

Usage:
    python3 add_new_entry.py \\
        --slug new-protocol-incident \\
        --name "New Protocol" \\
        --date 2026-10-01 \\
        --loss-usd 1234567 \\
        --chain "Ethereum" \\
        --mechanism "Reentrancy in the withdraw path" \\
        --readme-url "https://example.com/postmortem"

Use --loss-known-partial when the true loss is known to exceed the number
you can actually source (the same situation as the Sandbox and Balancer V1
entries already in this repo): the table then shows "≥" instead of "≈" and
the combined-loss total is flagged as a floor, matching how those two
existing entries are already handled.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
README_PATH = REPO_ROOT / "README.md"

INDEX_HEADER = "| Protocole | Date | Perte ($) | Chaîne | Type/Mécanisme | Lien |"
INDEX_SEPARATOR = "|---|---|---|---|---|---|"

ROW_RE = re.compile(
    r"^\|\s*(?P<name>.+?)\s*\|\s*(?P<date>.+?)\s*\|\s*(?P<loss_cell>.+?)\s*\|\s*"
    r"(?P<chain>.+?)\s*\|\s*(?P<mechanism>.+?)\s*\|\s*(?P<link>.+?)\s*\|\s*$"
)

# Pulls the leading numeric amount out of a loss cell like
# "≈ 9 131 000 [^moonwell]" or "≥ 675 000 [^sandbox]" or "174 311 [^cozy]".
LOSS_NUM_RE = re.compile(r"([≈≥]?)\s*([\d][\d\s,]*)")


def parse_loss_cell(cell: str) -> float:
    """Best-effort numeric value of a loss cell, for sorting and summing."""
    m = LOSS_NUM_RE.search(cell)
    if not m:
        return 0.0
    digits = m.group(2).replace(" ", "").replace(",", "")
    try:
        return float(digits)
    except ValueError:
        return 0.0


def format_loss_cell(loss_usd: float, slug: str, partial: bool) -> str:
    prefix = "≥" if partial else "≈"
    return f"{prefix} {loss_usd:,.0f}".replace(",", " ") + f" [^{slug}]"


def read_readme() -> str:
    if not README_PATH.exists():
        sys.exit(f"README introuvable a {README_PATH}, ce script doit tourner a la racine du repo.")
    return README_PATH.read_text(encoding="utf-8")


def find_index_table(content: str):
    lines = content.splitlines()
    try:
        header_i = lines.index(INDEX_HEADER)
    except ValueError:
        sys.exit(
            "Impossible de trouver l'en-tete du tableau d'index dans README.md. "
            "Le format attendu est:\n" + INDEX_HEADER
        )
    sep_i = header_i + 1
    if lines[sep_i] != INDEX_SEPARATOR:
        sys.exit("La ligne separatrice du tableau d'index ne correspond pas au format attendu.")
    row_start = sep_i + 1
    row_end = row_start
    while row_end < len(lines) and lines[row_end].startswith("|"):
        row_end += 1
    return lines, header_i, row_start, row_end


def insert_row_sorted(lines, row_start, row_end, new_row: str, new_loss: float):
    rows = lines[row_start:row_end]
    parsed = []
    for row in rows:
        m = ROW_RE.match(row)
        loss = parse_loss_cell(m.group("loss_cell")) if m else 0.0
        parsed.append((loss, row))
    parsed.append((new_loss, new_row))
    parsed.sort(key=lambda pair: pair[0], reverse=True)
    new_rows = [row for _, row in parsed]
    return lines[:row_start] + new_rows + lines[row_end:]


def update_at_a_glance(lines, total_incidents: int, total_loss: float, has_partial: bool):
    total_str = f"{total_loss:,.0f}".replace(",", " ")
    total_m = round(total_loss / 100_000) / 10  # nearest 0.1M
    floor_note = (
        " Au moins une entree est un plancher connu, le vrai cumul est donc plus eleve."
        if has_partial
        else ""
    )
    new_incidents_line = (
        f"| Incidents couverts | {total_incidents}, reconstruit independamment on-chain, "
        f"voir le tableau d'index pour le detail |"
    )
    new_loss_line = (
        f"| Perte cumulee, recalculee | Environ {total_m:.1f} M$ sur les {total_incidents} "
        f"incidents ({total_str} $ exactement, somme des chiffres du tableau ci-dessous)."
        f"{floor_note} |"
    )
    out = []
    for line in lines:
        if line.startswith("| Incidents couverts |"):
            out.append(new_incidents_line)
        elif line.startswith("| Perte cumulée, recalculée |") or line.startswith("| Perte cumulee, recalculee |"):
            out.append(new_loss_line)
        else:
            out.append(line)
    return out


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

REGISTRE_HEADER = "cle;hypothese;locator;test_falsification;confiance_preuve\n"


def scaffold_subfolder(slug: str, name: str, date: str, chain: str):
    folder = REPO_ROOT / slug
    if folder.exists():
        sys.exit(f"{folder} existe deja, choisis un autre --slug ou complete-le a la main.")
    folder.mkdir(parents=True)
    (folder / "README.md").write_text(
        README_STUB.format(name=name, chain=chain, date=date), encoding="utf-8"
    )
    (folder / "reconstruct_exploit.py").write_text(
        SCRIPT_STUB.format(name=name, chain=chain, date=date), encoding="utf-8"
    )
    (folder / "registre_hypotheses.csv").write_text(REGISTRE_HEADER, encoding="utf-8")
    (folder / ".gitignore").write_text("__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n.DS_Store\n", encoding="utf-8")
    print(f"Scaffold cree dans {folder}")
    return folder


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--slug", required=True, help="nom de dossier, ex. new-protocol-incident")
    p.add_argument("--name", required=True, help="nom lisible du protocole, ex. 'New Protocol'")
    p.add_argument("--date", required=True, help="date ISO ou plage, ex. 2026-10-01 ou 2026-10-01/02")
    p.add_argument("--loss-usd", required=True, type=float, help="perte en dollars, chiffre nu, ex. 1234567")
    p.add_argument("--chain", required=True, help="chaine, ex. Ethereum, Base, 'Ethereum + Base'")
    p.add_argument("--mechanism", required=True, help="type/mecanisme reel, pas le nom de l'incident")
    p.add_argument("--link", help="lien du sous-dossier dans le tableau, par defaut '<slug>/'")
    p.add_argument("--readme-url", default="", help="URL externe optionnelle a noter dans le stub de README")
    p.add_argument(
        "--loss-known-partial",
        action="store_true",
        help="la vraie perte depasse ce chiffre mais la source ne permet pas d'en affirmer plus (comme Sandbox, Balancer V1)",
    )
    p.add_argument("--skip-scaffold", action="store_true", help="ne cree pas le sous-dossier, met seulement a jour le README")
    args = p.parse_args()

    link = args.link or f"{args.slug}/"

    if not args.skip_scaffold:
        scaffold_subfolder(args.slug, args.name, args.date, args.chain)
        if args.readme_url:
            readme_path = REPO_ROOT / args.slug / "README.md"
            text = readme_path.read_text(encoding="utf-8")
            text += f"\n<!-- source externe: {args.readme_url} -->\n"
            readme_path.write_text(text, encoding="utf-8")

    content = read_readme()
    lines, header_i, row_start, row_end = find_index_table(content)

    loss_cell = format_loss_cell(args.loss_usd, args.slug, args.loss_known_partial)
    new_row = f"| {args.name} | {args.date} | {loss_cell} | {args.chain} | {args.mechanism} | [{link}]({link}) |"

    lines = insert_row_sorted(lines, row_start, row_end, new_row, args.loss_usd)

    # Recompute totals from every row now in the table (including the new one).
    _, _, row_start2, row_end2 = find_index_table("\n".join(lines))
    all_rows = lines[row_start2:row_end2]
    total_loss = 0.0
    has_partial = False
    for row in all_rows:
        m = ROW_RE.match(row)
        if not m:
            continue
        total_loss += parse_loss_cell(m.group("loss_cell"))
        if "≥" in m.group("loss_cell"):
            has_partial = True
    total_incidents = len(all_rows)

    lines = update_at_a_glance(lines, total_incidents, total_loss, has_partial)

    # Add a placeholder footnote for the new entry if one doesn't already exist.
    footnote_marker = f"[^{args.slug}]:"
    if footnote_marker not in "\n".join(lines):
        insertion_point = row_end2
        # Footnotes live directly after the table; find the last existing
        # footnote line (if any) to append after it, else insert right after
        # the table.
        i = insertion_point
        while i < len(lines) and lines[i].startswith("[^"):
            i += 1
        footnote_text = f"[^{args.slug}]: TODO, cite the exact source file and figure behind {args.loss_usd:,.0f} dollars."
        if args.readme_url:
            footnote_text += f" External source: {args.readme_url}."
        lines = lines[:i] + [footnote_text] + lines[i:]

    README_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"README.md mis a jour: {total_incidents} incidents, perte cumulee {total_loss:,.0f} $.")
    print(f"Complete le TODO dans {args.slug}/README.md, {args.slug}/reconstruct_exploit.py et la note de bas de page [^{args.slug}] avant de publier.")


if __name__ == "__main__":
    main()
