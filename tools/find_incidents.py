#!/usr/bin/env python3
"""Find the incidents that look like your protocol, from data/incidents.csv.

    python3 tools/find_incidents.py --category Bridge --chain Ethereum
    python3 tools/find_incidents.py --text vault

Filters are case-insensitive and combine with AND; --text looks in the protocol, mechanism and note.
Types and their questions: docs/by-type.md. Loss marks as in the Index: ≥ known floor, ≈ recomputed, † sourced, not recomputed.
"""
import argparse
import csv
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "incidents.csv"


def find(rows, category="", chain="", text=""):
    out = []
    for r in rows:
        if category and category.lower() not in r["category"].lower():
            continue
        if chain and chain.lower() not in r["chain"].lower():
            continue
        if text and text.lower() not in " ".join((r["protocol"], r["mechanism"], r["note"])).lower():
            continue
        out.append(r)
    return sorted(out, key=lambda r: r["date"], reverse=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--category", default="")
    ap.add_argument("--chain", default="")
    ap.add_argument("--text", default="")
    ap.add_argument("--data", default=str(DATA))
    a = ap.parse_args(argv)
    with open(a.data, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    hits = find(rows, a.category, a.chain, a.text)
    for r in hits:
        mark = ("≥ " if r["floor"] == "true" else "") + ("≈ " if r["approximate"] == "true" else "") + ("† " if r["sourced"] == "true" else "")
        print(f"{r['date']} | {r['protocol']} | {mark}{int(r['loss_usd']):,} | {r['chain']} | {r['category']} | {r['url']}")
    print(f"{len(hits)} of {len(rows)} incidents", file=sys.stderr)
    return 0 if hits else 1


if __name__ == "__main__":
    sys.exit(main())
