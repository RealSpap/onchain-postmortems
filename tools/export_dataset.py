#!/usr/bin/env python3
"""Export INDEX.md to machine-readable files: data/incidents.json and data/incidents.csv.

INDEX.md stays the single source of truth; this script only reshapes it.
Run after every change to INDEX.md:   python3 export_dataset.py
Check that the committed files are current (exit 1 if not):   python3 export_dataset.py --check
"""
import csv
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "INDEX.md"
OUT_JSON = ROOT / "data" / "incidents.json"
OUT_CSV = ROOT / "data" / "incidents.csv"
REPO = "https://github.com/RealSpap/onchain-postmortems"
FIELDS = ["slug", "protocol", "date", "loss_usd", "floor", "approximate", "sourced",
          "chain", "category", "mechanism", "url", "note"]


def parse(text):
    notes = dict(re.findall(r"^\[\^([a-z0-9-]+)\]:\s*(.+)$", text, re.M))
    rows = []
    for line in text.splitlines():
        if not line.startswith("| ") or line.startswith("| Protocol |") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 7:
            continue
        protocol, date, loss, chain, category, mechanism, link = cells
        ref = re.search(r"\[\^([a-z0-9-]+)\]", loss)
        folder = re.search(r"\(([a-z0-9-]+)/\)", link)
        amount = re.search(r"([\d,]+)", re.sub(r"\[\^[^\]]+\]", "", loss))
        if not (ref and folder and amount):
            raise SystemExit(f"Unreadable INDEX.md row: {line[:80]}")
        rows.append({
            "slug": folder.group(1),
            "protocol": protocol,
            "date": date,
            "loss_usd": int(amount.group(1).replace(",", "")),
            "floor": "≥" in loss,
            "approximate": "≈" in loss,
            "sourced": "†" in loss,
            "chain": chain,
            "category": category,
            "mechanism": mechanism,
            "url": f"{REPO}/tree/main/{folder.group(1)}/",
            "note": notes.get(ref.group(1), ""),
        })
    return rows


def render(rows):
    js = json.dumps({"source": f"{REPO}/blob/main/INDEX.md", "license": "MIT",
                     "incidents": rows}, ensure_ascii=False, indent=1) + "\n"
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows({k: (str(v).lower() if isinstance(v, bool) else v) for k, v in r.items()} for r in rows)
    return js, buf.getvalue()


def self_check(rows, text):
    # The export must add up to the totals INDEX.md states for itself.
    years = re.findall(r"\*\*\d{4} total: \$([\d,]+)\*\* across (\d+) incidents", text)
    if not years:
        raise SystemExit("INDEX.md year total lines not found")
    count = sum(int(n) for _, n in years)
    usd = sum(int(v.replace(",", "")) for v, _ in years)
    assert len(rows) == count, f"{len(rows)} rows, INDEX says {count}"
    assert sum(r["loss_usd"] for r in rows) == usd, "loss total differs from INDEX.md"
    assert len({r["slug"] for r in rows}) == len(rows), "duplicate slug"
    for r in rows:
        assert (ROOT / r["slug"]).is_dir(), f"missing folder {r['slug']}"


def main():
    text = INDEX.read_text()
    rows = parse(text)
    self_check(rows, text)
    js, cs = render(rows)
    if sys.argv[1:] == ["--check"]:
        stale = [p.name for p, c in ((OUT_JSON, js), (OUT_CSV, cs)) if not p.exists() or p.read_text() != c]
        if stale:
            raise SystemExit(f"Stale export, rerun python3 export_dataset.py: {', '.join(stale)}")
        print(f"OK: {len(rows)} incidents, export current")
        return
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(js)
    OUT_CSV.write_text(cs)
    recomputed = sum(r["loss_usd"] for r in rows if not r["sourced"])
    print(f"Wrote {len(rows)} incidents; total ${sum(r['loss_usd'] for r in rows):,}; recomputed ${recomputed:,}")


if __name__ == "__main__":
    main()
