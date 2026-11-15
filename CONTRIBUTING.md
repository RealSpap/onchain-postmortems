# Contributing

This repository rebuilds past incidents from public chain data. Every way of helping ends in something anyone can re-read, not in an opinion. Replies are best effort, with no promised delay.

## Five first tasks

Each takes about an hour, needs only Python and a public RPC, and ends in something anyone can re-read. All of them defend: they check what we published.

1. **Replay one script on another RPC.** Pick any folder under [`incidents/`](incidents/), run its `reconstruct_exploit.py` against a different public endpoint than the one it names, and say whether the historical figures match its saved `resultats_*.txt`. A match is useful; a difference is a finding.
2. **Re-derive one correction.** Take a row of [CORRECTIONS.md](CORRECTIONS.md), for example Cozy V2 (an on-chain total of $174,311.01, reached two ways), and rebuild its "found" figure from the transactions in its folder.
3. **Try to falsify a Medium row.** Open any `registre_hypotheses.csv` and pick a hypothesis rated Medium. Its falsification test says what would break it; run it and report.
4. **Extend one floor.** [docs/limits.md](docs/limits.md) lists the entries whose figure is a known floor, for example Enjin (594 later transactions, $34,643, are not counted). Read one leg the entry leaves out and tell us what it adds.
5. **Fix a small thing.** A broken link, a typo, a missing block number in an incident README: a small pull request, with `python3 tools/check_readme_consistency.py` and `python3 tools/check_structure.py` passing.

For a figure you think is wrong or an incident you think is missing, use the issue forms: "A figure is wrong" and "Suggest an incident". This repository studies past incidents so that teams can protect themselves; it does not accept requests that aim to harm a live system.

## 1. Report an error or ask for a correction

Open an issue, or write privately to contact@realspap.com (see [SECURITY.md](SECURITY.md)). Name the entry (its folder under `incidents/`), the statement you dispute and what supports your reading: a transaction hash, a block number, an address with the call to make, or a public document. Corrections are made in the open and recorded in [CHANGELOG.md](CHANGELOG.md).

## 2. Suggest an incident

Open an issue with the protocol, the date, the chain and, if you have it, a transaction hash or a block number. Those matter most. This is built and checked by one person, so not every suggestion becomes a folder.

## 3. Replay an entry

Each entry has a script that queries the chain and its saved output (`resultats_*.txt`, in its folder under `incidents/` or in `preuves/`). Most scripts need just Python and curl; a few need `pip install web3`.

```bash
pip install web3
python3 incidents/sandbox-oft-delegate-hijack/reconstruct_exploit.py
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

Keep them small and say what you ran. Run `python3 tools/check_readme_consistency.py` and `python3 tools/check_structure.py` before you open one; the same checks run in CI. To add an entry, `tools/add_new_entry.py` scaffolds it under `incidents/` (see [docs/method.md](docs/method.md)). A new incident goes in its own folder under `incidents/` and nowhere else; the structure check refuses anything else at the root. The maintainer decides what is included.
