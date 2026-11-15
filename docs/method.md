# Method, falsifiable hypotheses and adding an incident

Back to the [README](../README.md).

## How an entry is built

Each entry has its own folder under [`incidents/`](../incidents/): a full write-up (`README.md`), the Python script that queries the chain live (`reconstruct_exploit.py`), the registry of falsifiable hypotheses (`registre_hypotheses.csv`) and the script's raw, unedited output (`resultats_*.txt`). Eight early entries were first published as standalone reports and later consolidated here; each still keeps its own script, hypothesis registry, and raw proof files.

## Falsifiable hypotheses, not just claims

Every subfolder keeps a `registre_hypotheses.csv`: each claim broken into
a falsifiable hypothesis, with a locator (usually file + line in that
entry's `resultats_*.txt`), a falsification test, and a confidence level.
Every claim has a row; rows rated Medium may rest on checks not
reproduced by the committed script, and say so.

One real row, from `incidents/drift-protocol-durable-nonce-admin-hijack/registre_hypotheses.csv`:

| Key | Hypothesis | Locator | Falsification test | Confidence |
|---|---|---|---|---|
| H8 | The fake collateral mint (`G84LEhbNMR1yYbHgHbnNYNSK8mpTKcazh5jcW5yMPQKo`), derived purely from another hypothesis's own transaction inner instructions, not press-supplied, has `decimals=9`, live supply ~750,000,000 (within 0.0000004% of press's "750 million" claim), `mintAuthority=null`, and its own live Metaplex metadata decodes to name "CarbonVote Token", symbol "CVT" | `resultats_reconstruction_2026-09-11.txt:68-77` | Re-run `reconstruct_exploit.py` steps 5-6 against a different Solana RPC; a different supply, decimals, or metadata name/symbol would invalidate this | High |

Anyone can re-run that test against a different RPC themselves; it's
trusted only because it hasn't broken yet, not because this project
wrote it.

## Adding a new incident

```bash
python3 tools/add_new_entry.py \
  --slug new-protocol-incident \
  --name "New Protocol" \
  --date 2026-10-01 \
  --loss-usd 1234567 \
  --chain "Ethereum" \
  --category "Bridge" \
  --mechanism "Reentrancy in the withdrawal path" \
  --readme-url "https://example.com/postmortem"
```

Scaffolds a stub README, `registre_hypotheses.csv`, and
`reconstruct_exploit.py`; inserts the row into `INDEX.md` in the right
year/month section; recomputes every subtotal, the cumulative total, and
the README's "At a glance" block straight from the Index data, never a
hardcoded number. `add_new_entry.py --help` for the full flag reference,
including `--loss-known-partial`, `--loss-sourced` and the controlled
`--category` tags. It never touches `CORRECTIONS.md` or the floor table
under [Limits](limits.md#limits): both stay a human judgment call. Run `python3 tools/check_readme_consistency.py` before every
push; the same check runs in CI.

## Scope

Covers DeFi incidents today, but the name is deliberately
`onchain-postmortems`, not `defi-postmortems`: a bridge hack, an L1/L2
infrastructure incident, or a compromised validator set belongs here just
as much, with the same treatment (an on-chain reconstruction, not a
summary of press coverage).
