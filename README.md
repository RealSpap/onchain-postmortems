# On-Chain Postmortems

Independent forensic reconstructions, done entirely on-chain, of DeFi
security incidents and on-chain incidents more broadly. Each entry starts
from a primary source of the protocol involved (its own GitHub deployment
registries, never a press article) and reconstructs the exploit from raw
chain data: `eth_getLogs`, decoded transaction receipts, live `eth_call`
reads. When press coverage or DefiLlama gets a number, a scope, or a label
wrong, this repo says so and shows the on-chain proof.

By the same author: [@RealSpap on X](https://x.com/RealSpap), [Dune
profile](https://dune.com/s_pap), and
[[private-repo-name-redacted]](https://github.com/RealSpap/[private-repo-name-redacted]),
on-chain research into who actually controls DeFi admin keys.

Get notified of new postmortems: click Watch, then Custom, then Releases
only, on this repo's GitHub page. Every new incident gets tagged as a
release.

This repo brings together 8 postmortems that used to live in 8 separate
GitHub repos. The merge is justified because one repo per incident doesn't
scale: 8 repos today and 50 tomorrow would mean 50 places to search instead
of one. Each incident keeps its own subfolder with its script, its
hypothesis registry, and its raw proof files. Nothing was summarized or
lost in the merge.

## At a glance

| | |
|---|---|
| Incidents covered | 8, from August 21 to September 7, 2026, each independently reconstructed on-chain |
| Cumulative loss, recomputed | About $29.5M across the 8 incidents ($29,517,493 exactly, sum of the figures in the table below). Two entries, Sandbox and Balancer V1, are known floors: their source repo explicitly declines to state an aggregate dollar total, so the real cumulative figure is higher than $29.5M |
| Corrections made to press or DefiLlama | 4 of the 8 incidents published at merge time correct at least one already-published figure or label: Sandbox (real loss about 5.2x the reported figure), Balancer V1 (4 pools drained, not the single one reported), Notional V1 (DefiLlama's own feed labels the exploited contract "V2" when it's actually V1), Cozy V2 Optimism (both Cozy's own figure and DefiLlama's undercount the verified on-chain total). This count is updated by hand each time a new correction is found, `add_new_entry.py` doesn't touch it |
| Method | Each subfolder keeps its original Python reconstruction script, its `registre_hypotheses.csv` falsification registry, and its script's raw output in `resultats_*.txt`, so every figure below can be checked against the file that produced it |
| License | MIT across all 8 entries, single author (s_pap, 2026) |

## Index

Sorted by recomputed loss, descending. The "Type/Mechanism" column reflects
what the on-chain reconstruction actually found, not the incident's press
label.

| Protocol | Date | Loss ($) | Chain | Type/Mechanism | Link |
|---|---|---|---|---|---|
| Moonwell (MAMO market) | 2026-08-27 | ≈ 9,131,000 [^moonwell] | Base | Donation attack on an illiquid market's exchange rate, combined with collateral/oracle manipulation | [moonwell-mamo-oracle/](moonwell-mamo-oracle/) |
| Term Finance (Meta Vault) | 2026-08-17 / 08-23 | ≈ 8,500,000 [^termfinance] | Ethereum | Hijacked governance: a proposal self-voted by a fresh wallet through an attacker-deployed executor, normal 6-day delay elapsed with no veto | [termfinance-metavault-governance/](termfinance-metavault-governance/) |
| Tectonic | 2026-08-30 | ≈ 8,300,000 [^tectonic] | Cronos | Donation attack (recursive collateral minting then direct donations to the market contract) inflating an exchange rate, massive borrowing against the inflated collateral, followed by a chain rollback | [tectonic-cronos/](tectonic-cronos/) |
| Notional Finance (V1 Escrow) | 2026-09-03 / 09-04 | 1,727,782 [^notional] | Ethereum | `uint128` overflow/downcast in the legacy V1 Escrow contract's collateral valuation | [notional-v1-escrow/](notional-v1-escrow/) |
| Ajna Finance | 2026-08-28 / 08-29 | ≈ 775,400 [^ajna] | Ethereum | Liquidation-math exploit (`Kick`) on pools deployed through a factory the protocol never documented | [ajna-liquidation/](ajna-liquidation/) |
| The Sandbox (SAND / OFT) | 2026-08-21 / 08-22 | ≥ 675,000 [^sandbox] | Base + BSC + Ethereum | LayerZero delegate hijack via a legacy `approveAndCall` primitive, a composition bug, not a compromised key | [sandbox-oft-delegate-hijack/](sandbox-oft-delegate-hijack/) |
| Balancer V1 (legacy pools) | 2026-08-30 / 08-31 | ≥ 234,000 [^balancer] | Ethereum | Rounding error on unmaintained V1 pools, repeated 1-satoshi joins | [balancer-v1-rounding/](balancer-v1-rounding/) |
| Cozy V2 | 2026-09-02 / 09-07 | 174,311 [^cozy] | Optimism | False answers to the UMA Optimistic Oracle left uncontested during its 5-day dispute window | [cozy-v2-optimism/](cozy-v2-optimism/) |

[^moonwell]: Debt still unrecovered as of August 28, 2026 per Moonwell's own official postmortem (595 liquidations on $11.03M gross borrowed, $9.131M remained uncovered at that date). Press coverage (PeckShield/CertiK) reported about $8.7M. See `moonwell-mamo-oracle/README.md`.
[^termfinance]: Press figure, consistent with the amounts independently verified on-chain (2,841.7435 WETH drained from the ETH Meta Vault, plus 1,679,639.290442 USDC swept then converted to 1,679,642.454089 DAI). No dollar total was independently recomputed in the source repo. See `termfinance-metavault-governance/README.md`.
[^tectonic]: Loss confirmed unrecoverable after Cronos validators rolled back roughly 11,000 blocks. Over $120M had been borrowed against the inflated collateral, but most of that debt was wiped out by the rollback itself. See `tectonic-cronos/README.md` and the linked Dune dashboard.
[^notional]: 69,257.3727 DAI plus 1,658,524.8641 USDC, decoded directly from the extraction transaction's `Transfer` events, totaling $1,727,782.2368. This figure matches DefiLlama's public feed `amount` field for this incident exactly, even though that feed labels the incident "Notional V2" when the exploited contract is actually V1. See `notional-v1-escrow/README.md`.
[^ajna]: Press and DefiLlama figure for all 7 affected pools combined. Only one extraction is confirmed transaction-by-transaction (49.32 WETH on the cbETH/WETH pool, about $121,800 at $2,470/ETH). The rest rests on a before/after balance delta, weaker evidence, and the source project doesn't force this figure to match the press one. See `ajna-liquidation/README.md`.
[^sandbox]: Press figure, Ethereum leg only. The independent reconstruction finds a real amount about 5.2x higher (405.828879423128923336 gross WETH across the 2 chains actually drained, Base and Ethereum), but the source repo explicitly declines to assign any dollar total to this native-unit figure. See `sandbox-oft-delegate-hijack/README.md`.
[^balancer]: DefiLlama and press figure for 1 pool only. The independent reconstruction finds the same wallet drained 4 separate pools the same night. The 3 additional pools are only quantified in kind (DAI, USDC, MKR, UMA, LINK, SNX, AMPL, WBTC, BLZ, WSTA and others): the source repo doesn't aggregate a dollar total, for lack of a reliable historical price feed for these tokens. See `balancer-v1-rounding/README.md`.
[^cozy]: 174,311.006968 USDC.e, verified by two independent methods that land on the same total (sum of transfers across each claim transaction, then an independent log filter on the destination address). This figure exceeds both the one Cozy itself published ($170,186) and the one DefiLlama tracks ($163,326, which matches exactly one of the two claim transactions). See `cozy-v2-optimism/README.md`.

## Structure

```
onchain-postmortems/
  README.md                          this file
  add_new_entry.py                   scaffolds a new subfolder and updates the index
  LICENSE                            MIT, s_pap 2026
  <incident-slug>/
    README.md                        full writeup, "at a glance", method, caveats
    reconstruct_exploit.py           script that queries the chain live
    registre_hypotheses.csv          every hypothesis with its falsification test and evidence level
    resultats_*.txt                  raw, unedited output from the script
    LICENSE, .gitignore              kept as-is from the source repo
```

Each of the 8 subfolders above used to be, before being folded into this
repo, its own public GitHub repo under the `RealSpap` account. Those 8 repos
aren't deleted, kept archived and private now that their canonical content
lives here.

| Old repo | Subfolder here |
|---|---|
| `RealSpap/sandbox-oft-delegate-hijack-exploit-postmortem` | `sandbox-oft-delegate-hijack/` |
| `RealSpap/moonwell-mamo-oracle-exploit-postmortem` | `moonwell-mamo-oracle/` |
| `RealSpap/balancer-v1-legacy-pools-rounding-exploit-postmortem` | `balancer-v1-rounding/` |
| `RealSpap/termfinance-metavault-governance-exploit-postmortem` | `termfinance-metavault-governance/` |
| `RealSpap/notional-v1-escrow-exploit-postmortem` | `notional-v1-escrow/` |
| `RealSpap/ajna-liquidation-exploit-postmortem` | `ajna-liquidation/` |
| `RealSpap/cozy-v2-optimism-postmortem` | `cozy-v2-optimism/` |
| `RealSpap/tectonic-cronos-postmortem` | `tectonic-cronos/` |

## Adding a new incident

```bash
python3 add_new_entry.py \
  --slug new-protocol-incident \
  --name "New Protocol" \
  --date 2026-10-01 \
  --loss-usd 1234567 \
  --chain "Ethereum" \
  --mechanism "Reentrancy in the withdrawal path" \
  --readme-url "https://example.com/postmortem"
```

This scaffolds `new-protocol-incident/` with a stub README, an empty
`registre_hypotheses.csv`, and a stub `reconstruct_exploit.py`, then
inserts a new row into the index table above, sorted by loss, and
recomputes the incident-count and cumulative-loss line in the "at a
glance" block from the table itself, never from a hardcoded number. See
`add_new_entry.py --help` for the full list of options, and use
`--loss-known-partial` for an incident like Sandbox or Balancer V1 above,
where the real loss is known to exceed the figure that can actually be
sourced.

The script doesn't touch the "Corrections made" and "License" lines in the
"at a glance" block, those are human judgment calls (does this new
incident actually correct the press, is it actually MIT), not mechanical
totals. Update them yourself if needed.

## Scope

This program covers DeFi incidents today, but the name is deliberately
`onchain-postmortems`, not `defi-postmortems`: a future entry doesn't need
to be a lending or AMM protocol. A bridge hack, an L1/L2 infrastructure
incident, or a compromised validator set all belong here just as much, as
long as they get the same treatment: an independent on-chain reconstruction
from a primary source, not a summary of press coverage.

## Suggest an incident

Know of an on-chain incident that fits this program's scope, an
independent, primary-source reconstruction, not a summary of press? Open
a GitHub issue with the protocol name, date, and chain, or reach out on X
([@RealSpap](https://x.com/RealSpap)). Every entry is still built and
verified by one person, so not every suggestion becomes a subfolder, but
tips with a tx hash or block number attached get looked at first.

## Limits

- This is independent research, not a security audit, and isn't
  affiliated with any protocol, auditor, or outlet cited in a subfolder.
- Every dollar figure in the index table above is recomputed from each
  subfolder's source files (its README, its script's raw output in
  `resultats_*.txt`, or its `registre_hypotheses.csv`), never carried over
  from an old summary without checking it against those files. When a
  subfolder's source data doesn't support a full dollar total, the table
  says so in a footnote instead of inventing one.
- Two entries (Sandbox, Balancer V1) report a dollar figure that is a
  known floor, not a complete total, because their source repo found a
  wider scope than the press without converting every recovered amount to
  dollars. Read the linked subfolder for the full accounting in native
  units.
- The Tectonic and Moonwell entries report the confirmed unrecoverable or
  still-uncovered figure, not the higher, gross amount borrowed or
  extracted before liquidations and, for Tectonic, a chain rollback
  recovered part of it. Both readings are given in the footnote and in the
  linked subfolder.
- `tectonic-cronos/` is the only subfolder without a `resultats_*.txt` or
  a `registre_hypotheses.csv`: its script is a tool for reading the
  chain's current state (`tectonic_risk_snapshot.py`), not a replay of the
  incident, and its loss figures ($120M+ borrowed, $8.3M unrecoverable)
  rest on its README and the Dune dashboard it links, not on a locally
  reproducible output file in this repo. Flagged here rather than hidden.

## Disclaimer

Every entry in this repo is an independent, factual reconstruction of
publicly available on-chain data (transaction receipts, decoded logs,
live contract reads) as of the date noted per entry, not a security
audit, and not affiliated with, commissioned by, or endorsed by any
protocol, auditor, or outlet named in a subfolder. Statements about who
sent, received, or drained funds are based solely on on-chain records and
publicly disclosed information cited inline, so no claim of wrongdoing
beyond what that cited on-chain data shows is made or implied against any
named address or entity. Nothing in this repo is legal, financial, or
investment advice. Each entry reflects a snapshot in time: on-chain
balances, labels, and follow-up transactions can and do change after
publication, and entries are not updated automatically to reflect such
changes. Any individual or entity named in an entry who believes a fact
about them is inaccurate is invited to contact the author with supporting
evidence for a prompt, transparent correction. Readers should
independently verify all cited addresses, transactions, and figures
before relying on them.

## License

MIT. See `LICENSE`.
