# On-Chain Postmortems

**$924.9M in DeFi and on-chain losses, independently recomputed from raw chain data across 52 incidents.**

Forensic reconstructions done entirely on-chain. Each entry starts from a
primary source (the protocol's own deployment registries, never a press
article) and rebuilds the exploit from raw chain data: `eth_getLogs`,
decoded transaction receipts, live `eth_call` reads. When press or
DefiLlama gets a number, scope, or label wrong, this repo shows the
on-chain proof.

Example: DefiLlama logged WealthManagementV2 as a $26,414 "private key
compromise"; the real drain was $422,251.40, 16x higher — one of 34 cases
in [Corrections to press and DefiLlama](CORRECTIONS.md).

Same author: [@RealSpap on X](https://x.com/RealSpap), [Dune
profile](https://dune.com/s_pap),
[multisig-overlap-showcase](https://github.com/RealSpap/multisig-overlap-showcase)
(who actually controls DeFi admin keys).

New postmortems land as GitHub releases — Watch → Custom → Releases, or
the plain [Atom feed](https://github.com/RealSpap/onchain-postmortems/releases.atom),
no account needed.

8 incidents here used to be 8 separate repos, merged so incident count
doesn't become repo count (mapping in [Structure](#structure) below);
each still keeps its own script, hypothesis registry, and raw proof
files.

## At a glance

| | |
|---|---|
| Incidents covered | 52, independently reconstructed on-chain, see [the full index](INDEX.md) for detail |
| Cumulative loss, recomputed | About $924.9M across the 52 incidents ($924,918,283 exactly, sum of the figures in the index). At least one entry is a known floor, so the real total is higher. |
| Corrections made | 34 entries correct, reconcile, or newly surface a press or DefiLlama figure, label, date, or classification (26 corrections, 5 reconciliations, 3 discoveries not previously priced by DefiLlama at all). See [Corrections to press and DefiLlama](CORRECTIONS.md). |
| Method | Each subfolder keeps its original Python reconstruction script, its `registre_hypotheses.csv` falsification registry, and its script's raw output in `resultats_*.txt`, so every figure below can be checked against the file that produced it |
| License | MIT across all 52 entries, single author (Spap, 2026) |

## The 5 biggest losses

Full history is 52 incidents across 6 months; these are the largest, by
recomputed loss. Full table, sortable by month: [INDEX.md](INDEX.md).

| Protocol | Loss ($) | Chain | Mechanism | Link |
|---|---|---|---|---|
| Drift Protocol | ≈ 295,706,375 | Solana | Pre-signed durable-nonce Squads multisig approvals hijacked the program's admin key | [drift-protocol-durable-nonce-admin-hijack/](drift-protocol-durable-nonce-admin-hijack/) |
| Kelp DAO (rsETH / LayerZero DVN) | ≈ 273,377,225 | Ethereum | Compromised LayerZero RPC nodes plus a DDoS-forced DVN failover passed a forged message through a 1-of-1 verifier | [kelpdao-rseth-layerzero-rpc-spoofing/](kelpdao-rseth-layerzero-rpc-spoofing/) |
| Bitget hot wallet drain (Ethereum leg) | ≥ 126,417,066 | Ethereum | Spoofed withdrawal requests signed by Bitget's own hot wallets; the Ethereum leg of a $387.5M four-chain theft | [bitget-hot-wallet-spoofed-withdrawals/](bitget-hot-wallet-spoofed-withdrawals/) |
| Liquid Network | ≥ 46,568,719 | Bitcoin + Liquid | Range-proof cache-key collision let a peg-out register as fully backed | [liquid-rangeproof-cache/](liquid-rangeproof-cache/) |
| COLDCARD (Weak Seed RNG) | ≥ 37,996,965 | Bitcoin | Build-flag bug silently swapped the hardware RNG for a weak software PRNG for 5+ years | [coldcard-rng-seed-theft/](coldcard-rng-seed-theft/) |

## Full index

Grouped by year and month, sorted by loss within each month, 52 rows in
total: **[INDEX.md](INDEX.md)**. Corrections against press and DefiLlama,
34 rows: **[CORRECTIONS.md](CORRECTIONS.md)**.

## Monthly digests

One file per month, published once the month closes: headline loss
total, breakdown by root-cause technique, the three biggest incidents,
and a full linked table. Same discipline as every individual entry, just
aggregated.

- [August 2026](digests/2026-08.md): first edition, 19 incidents, at least $46.7M

Full history: [`digests/`](digests/)

## Falsifiable hypotheses, not just claims

Every subfolder keeps a `registre_hypotheses.csv`: each claim broken into
a falsifiable hypothesis, with an exact locator (file + line in that
entry's `resultats_*.txt`), a falsification test, and a confidence level.
Nothing above is asserted without a row backing it.

One real row, from `drift-protocol-durable-nonce-admin-hijack/registre_hypotheses.csv`:

| Key | Hypothesis | Locator | Falsification test | Confidence |
|---|---|---|---|---|
| H8 | The fake collateral mint (`G84LEhbNMR1yYbHgHbnNYNSK8mpTKcazh5jcW5yMPQKo`), derived purely from another hypothesis's own transaction inner instructions, not press-supplied, has `decimals=9`, live supply ~750,000,000 (within 0.0000004% of press's "750 million" claim), `mintAuthority=null`, and its own live Metaplex metadata decodes to name "CarbonVote Token", symbol "CVT" | `resultats_reconstruction_2026-09-11.txt:68-77` | Re-run `reconstruct_exploit.py` steps 5-6 against a different Solana RPC; a different supply, decimals, or metadata name/symbol would invalidate this | High |

Anyone can re-run that test against a different RPC themselves; it's
trusted only because it hasn't broken yet, not because this project
wrote it.

## Structure

```
onchain-postmortems/
  README.md                          this file (pitch + at-a-glance)
  INDEX.md                           full year/month incident index, 52 rows
  CORRECTIONS.md                     full press/DefiLlama corrections table, 34 rows
  add_new_entry.py                   scaffolds a new subfolder and updates INDEX.md
  digests/                            one monthly roundup file per month (2026-08.md, ...)
  LICENSE                            MIT, Spap 2026
  <incident-slug>/
    README.md                        full writeup, "at a glance", method, caveats
    reconstruct_exploit.py           script that queries the chain live
    registre_hypotheses.csv          every hypothesis with its falsification test and evidence level
    resultats_*.txt                  raw, unedited output from the script
    LICENSE, .gitignore              kept as-is from the source repo
```

Each of the 8 subfolders above used to be, before being folded into this
repo, its own public GitHub repo under the `RealSpap` account. That account is
no longer publicly reachable (migrated to `RealSpap` in September 2026); none
of these 8 old repo names resolve anywhere anymore, and no attempt is made to
recreate them under the new account -- their canonical content already lives
here, in full.

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
  --category "Bridge" \
  --mechanism "Reentrancy in the withdrawal path" \
  --readme-url "https://example.com/postmortem"
```

Scaffolds a stub README, `registre_hypotheses.csv`, and
`reconstruct_exploit.py`; inserts the row into `INDEX.md` in the right
year/month section; recomputes every subtotal, the cumulative total, and
this README's "At a glance" block straight from the Index data, never a
hardcoded number. `add_new_entry.py --help` for the full flag reference,
including `--loss-known-partial` and the controlled `--category` tags. It
never touches `CORRECTIONS.md` — that stays a human judgment call.

## Scope

Covers DeFi incidents today, but the name is deliberately
`onchain-postmortems`, not `defi-postmortems`: a bridge hack, an L1/L2
infrastructure incident, or a compromised validator set belongs here just
as much, same treatment — an independent on-chain reconstruction from a
primary source, not a summary of press coverage.

## Suggest an incident

Open a GitHub issue with the protocol name, date, and chain, or reach out
on X ([@RealSpap](https://x.com/RealSpap)). Built and verified by one
person, so not every suggestion becomes a subfolder, but tips with a tx
hash or block number attached get looked at first.

## Limits

- Independent research, not a security audit; not affiliated with any
  protocol, auditor, or outlet cited in a subfolder.
- Every dollar figure in [the Index](INDEX.md) is recomputed from each
  subfolder's own source files (its README, its script's raw output in
  `resultats_*.txt`, or its `registre_hypotheses.csv`), never carried over
  from an old summary unchecked. When a subfolder's source data doesn't
  support a full dollar total, the table footnotes it instead of
  inventing one.
- 12 entries report a dollar figure that is a known floor, not a complete
  total. Read the linked subfolder for the full accounting in native
  units.

| Protocol | Why it's a floor | Link |
|---|---|---|
| Sandbox | Wider scope found than press; not all converted to dollars | [sandbox-oft-delegate-hijack/](sandbox-oft-delegate-hijack/) |
| Balancer V1 (legacy pools) | Same: wider scope than press, not fully priced | [balancer-v1-rounding/](balancer-v1-rounding/) |
| Liquid Network | Some smaller destination addresses left untraced | [liquid-rangeproof-cache/](liquid-rangeproof-cache/) |
| Maya Protocol (MAYAChain) | Unconverted CACAO balance in attacker's wallet, no rate | [mayachain-cacao-slash-drain/](mayachain-cacao-slash-drain/) |
| COLDCARD (Weak Seed RNG) | Only 1st of 4 theft waves traced, about a third | [coldcard-rng-seed-theft/](coldcard-rng-seed-theft/) |
| Coinsbuy | Tron leg full; only one Ethereum tx attributable | [coinsbuy-wallet-drain/](coinsbuy-wallet-drain/) |
| WealthManagementV2 | Only nonces 0-41 of 252 lifetime txns decoded | [wealthmanagementv2-selfowned-proxy-drain/](wealthmanagementv2-selfowned-proxy-drain/) |
| XRP Healthcare (XRPH Wallet) | Covers 3,630 of 4,011 wallets XRP Healthcare counted | [xrph-wallet-key-compromise/](xrph-wallet-key-compromise/) |
| Symbiosis | Prices only the realized cash-out; syBTC float unresolved | [symbiosis-sybtc-mpc-signed-mint/](symbiosis-sybtc-mpc-signed-mint/) |
| Cosmos EVM (MANTRA / TAC / KiiChain) | Source itself withholds 3 of the 6 chains hit | [cosmos-evm-vesting-underflow/](cosmos-evm-vesting-underflow/) |
| Oraichain (ICS-20 EVM Precompile) | Prices only 2 legs; excludes Injective-bridged/locked ORAI | [oraichain-ics20-precompile-selfmint/](oraichain-ics20-precompile-selfmint/) |
| Verus-Ethereum Bridge | 2nd exploit (2026-07-23, $7,530,000 per DefiLlama) not priced | [verus-ethereum-bridge-forged-proof/](verus-ethereum-bridge-forged-proof/) |

- Tectonic, Moonwell, and Liquid Network report the confirmed
  unrecoverable or still-uncovered figure, not the higher gross amount —
  see each entry's own footnote for both readings.
- `tectonic-cronos/` is the only subfolder without a `resultats_*.txt` or
  a `registre_hypotheses.csv`: its script reads the chain's current state
  (`tectonic_risk_snapshot.py`), not a replay of the incident, and its
  loss figures ($120M+ borrowed, $8.3M unrecoverable) rest on its README
  and the Dune dashboard it links, not a locally reproducible output file
  in this repo. Flagged here rather than hidden.
- The "Category" column in the Index is this project's own classification
  of an already-described mechanism, for scanning convenience, not a
  label sourced from DefiLlama, press, or the protocol itself. Several
  incidents plausibly fit more than one tag; each row carries the single
  tag judged most useful for finding it, the "Type/Mechanism" column next
  to it carries the actual nuance.

## Disclaimer

Every entry in this repo is an independent, factual reconstruction of
publicly available on-chain data (transaction receipts, decoded logs,
live contract reads) as of the date noted per entry, not a security
audit, and not affiliated with, commissioned by, or endorsed by any
protocol, auditor, or outlet named in a subfolder.

- **No claim beyond the data.** Who sent, received, or drained funds is
  based solely on on-chain records and publicly disclosed information
  cited inline — no claim of wrongdoing beyond what that data shows is
  made or implied against any named address or entity.
- **Not advice.** Nothing in this repo is legal, financial, or investment
  advice.
- **A snapshot, not a live feed.** Balances, labels, and follow-up
  transactions can and do change after publication; entries are not
  updated automatically to reflect such changes.
- **Corrections welcome.** Any individual or entity named who believes a
  fact about them is inaccurate is invited to contact the author with
  supporting evidence for a prompt, transparent correction.

Readers should independently verify all cited addresses, transactions,
and figures before relying on them.

## License

MIT. See `LICENSE`. Deliberately open, including every reconstruction
script: each is wired to one already-public historical incident, so
publishing it costs nothing competitively and buys real reproducibility —
anyone can rerun the same query against the same public chain data and
get the same number, which is what makes the corrections to press and
DefiLlama in this repo checkable rather than just asserted.
