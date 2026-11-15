# Contributing

This repository rebuilds past incidents from public chain data. Every way of helping ends in something anyone can re-read, not in an opinion. Replies are best effort, with no promised delay.

## 1. Report an error or ask for a correction

Open an issue, or write privately to contact@realspap.com (see [SECURITY.md](SECURITY.md)). Name the entry (its folder under `incidents/`), the statement you dispute and what supports your reading: a transaction hash, a block number, an address with the call to make, or a public document. Corrections are made in the open and recorded in [CHANGELOG.md](CHANGELOG.md).

## 2. Suggest an incident

Open an issue with the protocol, the date, the chain and, if you have it, a transaction hash or a block number. Those matter most. This is built and checked by one person, so not every suggestion becomes a folder.

## 3. Replay an entry

Each entry has a script that queries the chain and its saved output (`resultats_*.txt`, in its folder under `incidents/` or in `preuves/`). Most scripts need just Python and curl; a few need `pip install web3`.

```bash
pip install web3
python3 incidents/<entry-folder>/reconstruct_exploit.py
python3 tools/check_readme_consistency.py
python3 tools/check_structure.py
```

Historical figures should match the saved output. Balances and roles read today may differ, because chains keep moving. If a historical figure differs, say which command, which block and what you got: that is a finding, and a useful one.

## What we do not accept

- A change to a figure without evidence that anyone can re-read.
- An entry that rests on press coverage alone, with no on-chain reconstruction.
- Anything that includes a private key, a seed phrase, a password or private data.
- Statements about the character or intent of a named person.
- Requests to soften or remove a finding without evidence.
- Promotional entries.

## Pull requests

Keep them small and say what you ran. Run `python3 tools/check_readme_consistency.py` and `python3 tools/check_structure.py` before you open one; the same checks run in CI. To add an entry, `tools/add_new_entry.py` scaffolds it under `incidents/` (see [docs/method.md](docs/method.md)). A new incident goes in `incidents/<slug>/` and nowhere else; the structure check refuses anything else at the root. The maintainer decides what is included.
