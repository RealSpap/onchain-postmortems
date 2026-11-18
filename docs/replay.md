# Replay every figure

Every figure in this repository is either computed from a file in the repository or read live from a chain. This page lists each family of figures, the file that generates it, and the one command that replays it. It holds no figure itself, so it cannot go stale. If a replay differs from what a page says, open an issue: the replay is right until it is shown wrong, and the correction is dated.

| Figures | Written in | Generated from | Replay (one command) | Network |
|---|---|---|---|---|
| Incident count, total loss and reconstructed share | README.md, docs/by-type.md | data/incidents.json, data/incidents.csv | `python3 tools/export_dataset.py --check` | no |
| Per-month and per-year subtotals, corrections count | INDEX.md, CORRECTIONS.md | data/incidents.csv | `python3 tools/check_readme_consistency.py` | no |
| Incident count badge | data/badge-incidents.json | data/incidents.json | `python3 tools/export_dataset.py --check` | no |
| Figures inside one incident | incidents/sandbox-oft-delegate-hijack/README.md | incidents/sandbox-oft-delegate-hijack/reconstruct_exploit.py | `python3 incidents/sandbox-oft-delegate-hijack/reconstruct_exploit.py` | live |
| Corrections to press figures | CORRECTIONS.md | - | not replayed (dated record) | no |

A command that needs the network reads public endpoints only and writes nothing. Before a replay, check that the file named in its row exists at the commit you cloned.
