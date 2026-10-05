# On-Chain Postmortems

**$921.1M in DeFi and on-chain losses across 55 incidents, each reconstructed from raw chain data; $584.2M of it independently recomputed, the rest sourced from the protocol, press or DefiLlama.**

Forensic reconstructions done on-chain. Each entry rebuilds the exploit
from raw chain data (`eth_getLogs`, decoded transaction receipts,
`eth_call` reads) rather than from press summaries. When press or
DefiLlama gets a number, scope, or label wrong, this repo shows the
on-chain proof; when a dollar figure could not be recomputed, the Index
says so and marks it †.

Example: press reported only the Ethereum leg of the Sandbox bridge
exploit; the reconstruction finds 405.83 WETH gross across Base and
Ethereum, about 5.2 times the press figure, one of 34 cases
in [Corrections to press and DefiLlama](CORRECTIONS.md).

Same author: [@RealSpap on X](https://x.com/RealSpap),
[multisig-overlap-showcase](https://github.com/RealSpap/multisig-overlap-showcase)
(who actually controls DeFi admin keys).

New incidents are announced as GitHub releases (Watch, then Custom, then
Releases), or through the plain [Atom
feed](https://github.com/RealSpap/onchain-postmortems/releases.atom), no
account needed.

Eight early entries were first published as standalone reports and later
consolidated here; each still keeps its own script, hypothesis registry,
and raw proof files.

## At a glance

| | |
|---|---|
| Incidents covered | 55, each reconstructed on-chain, see [the full index](INDEX.md) for detail |
| Cumulative loss | About $921.1M across the 55 incidents ($921,145,689 exactly, sum of the figures in the index); $584,177,531 of it independently recomputed, the rest (marked † in the index) sourced from the protocol, press or DefiLlama. At least one entry is a known floor, so the real total is higher. |
| Corrections made | 34 entries correct, reconcile, or newly surface a press or DefiLlama figure, label, date, or classification (23 corrections, 8 reconciliations, 3 discoveries not previously priced by DefiLlama at all). See [Corrections to press and DefiLlama](CORRECTIONS.md). |
| Method | Each subfolder keeps its Python reconstruction script, its `registre_hypotheses.csv` falsification registry, and its script's raw output in `resultats_*.txt`, so each recomputed figure can be checked against the file that produced it |
| License | MIT across all 52 entries, single author (Spap, 2026) |

## The 5 biggest losses

Full history is 52 incidents across 6 months; these are the largest, by
loss. Full table, sortable by month: [INDEX.md](INDEX.md).

| Protocol | Loss ($) | Chain | Mechanism | Link |
|---|---|---|---|---|
| Drift Protocol | † 295,706,375 | Solana | Pre-signed durable-nonce Squads multisig approvals hijacked the program's admin key | [drift-protocol-durable-nonce-admin-hijack/](drift-protocol-durable-nonce-admin-hijack/) |
| Kelp DAO (rsETH / LayerZero DVN) | ≈ 273,377,225 | Ethereum | Compromised LayerZero RPC nodes plus a DDoS-forced DVN failover passed a forged message through a 1-of-1 verifier | [kelpdao-rseth-layerzero-rpc-spoofing/](kelpdao-rseth-layerzero-rpc-spoofing/) |
| Bitget hot wallet drain (Ethereum leg) | ≥ 126,417,066 | Ethereum | Spoofed withdrawal requests signed by Bitget's own hot wallets; the Ethereum leg of a $387.5M four-chain theft | [bitget-hot-wallet-spoofed-withdrawals/](bitget-hot-wallet-spoofed-withdrawals/) |
| Liquid Network | ≥ 46,568,719 | Bitcoin + Liquid | Range-proof cache-key collision let a peg-out register as fully backed | [liquid-rangeproof-cache/](liquid-rangeproof-cache/) |
| COLDCARD (Weak Seed RNG) | ≥ 37,996,965 | Bitcoin | Build-flag bug silently swapped the hardware RNG for a weak software PRNG for 5+ years | [coldcard-rng-seed-theft/](coldcard-rng-seed-theft/) |

Drift's figure is Drift's own stated total; a sample of the outflow
(USDT and USDS legs) matches Drift's per-asset figures to within 0.002%,
but the total is not fully recomputed here.

## Full index

Grouped by year and month, sorted by loss within each month:
**[INDEX.md](INDEX.md)**. Corrections against press and DefiLlama:
**[CORRECTIONS.md](CORRECTIONS.md)**.

## Monthly digests

One file per month, published once the month closes: headline loss
total, breakdown by root-cause technique, the three biggest incidents,
and a full linked table.

- [September 2026](digests/2026-09.md): 22 incidents, at least $185.8M
- [August 2026](digests/2026-08.md): first edition, 19 incidents, at least $47.6M

Full history: [`digests/`](digests/)

## Falsifiable hypotheses, not just claims

Every subfolder keeps a `registre_hypotheses.csv`: each claim broken into
a falsifiable hypothesis, with a locator (usually file + line in that
entry's `resultats_*.txt`), a falsification test, and a confidence level.
Every claim has a row; rows rated Medium may rest on checks not
reproduced by the committed script, and say so.

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
  INDEX.md                           full year/month incident index
  CORRECTIONS.md                     press/DefiLlama corrections table
  CHANGELOG.md                       short log of additions and corrections
  SECURITY.md                        how to report an error or request a correction
  add_new_entry.py                   scaffolds a new subfolder and updates INDEX.md
  check_readme_consistency.py        checks totals, counts and links across these files
  digests/                           one monthly roundup file per month (2026-08.md, ...)
  LICENSE                            MIT, Spap 2026
  <incident-slug>/
    README.md                        full writeup, "at a glance", method, caveats
    reconstruct_exploit.py           script that queries the chain live
    registre_hypotheses.csv          every hypothesis with its falsification test and evidence level
    resultats_*.txt                  raw, unedited output from the script
```

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
including `--loss-known-partial`, `--loss-sourced` and the controlled
`--category` tags. It never touches `CORRECTIONS.md` or the floor table
under [Limits](#limits): both stay a human judgment call. Run `python3 check_readme_consistency.py` before every
push; the same check runs in CI.

## Scope

Covers DeFi incidents today, but the name is deliberately
`onchain-postmortems`, not `defi-postmortems`: a bridge hack, an L1/L2
infrastructure incident, or a compromised validator set belongs here just
as much, with the same treatment (an on-chain reconstruction, not a
summary of press coverage).

## Suggest an incident, report an error

Open a GitHub issue with the protocol name, date, and chain, or reach out
on X ([@RealSpap](https://x.com/RealSpap)). Built and verified by one
person, so not every suggestion becomes a subfolder, but tips with a tx
hash or block number attached get looked at first. To report an error or
request a correction privately, see [SECURITY.md](SECURITY.md).

## Limits

- Independent research, not a security audit; not affiliated with any
  protocol, auditor, or outlet cited in a subfolder.
- Every dollar figure in [the Index](INDEX.md) is taken from each
  subfolder's own source files (its README, its script's raw output in
  `resultats_*.txt`, or its `registre_hypotheses.csv`), never carried over
  from an old summary unchecked. Figures marked † come from the
  protocol's own post-mortem, press or DefiLlama and are not
  independently recomputed; each footnote names the source.
- 14 entries report a dollar figure that is a known floor, not a complete
  total. Read the linked subfolder for the full accounting in native
  units.

| Protocol | Why it's a floor | Link |
|---|---|---|
| Bitget hot wallet drain (Ethereum leg) | Ethereum leg only; XRPL, Tron and a probable Zcash leg not reconstructed | [bitget-hot-wallet-spoofed-withdrawals/](bitget-hot-wallet-spoofed-withdrawals/) |
| Duelbits hot wallet drain (Ethereum leg) | Ethereum leg only; BNB Chain, Tron and Bitcoin legs not reconstructed | [duelbits-hot-wallet-drain/](duelbits-hot-wallet-drain/) |
| Limit Break Payment Processor V2 | Drains observed until the end of the window (2026-09-28); WILD and APE not priced | [limit-break-payment-processor-forwarder-spoof/](limit-break-payment-processor-forwarder-spoof/) |
| Symbiosis | Prices only the realized cash-out; syBTC float unresolved | [symbiosis-sybtc-mpc-signed-mint/](symbiosis-sybtc-mpc-signed-mint/) |
| Liquid Network | Some smaller destination addresses left untraced | [liquid-rangeproof-cache/](liquid-rangeproof-cache/) |
| XRP Healthcare (XRPH Wallet) | Covers 3,630 of 4,011 wallets XRP Healthcare counted | [xrph-wallet-key-compromise/](xrph-wallet-key-compromise/) |
| Sandbox | Wider scope found than press; not all converted to dollars | [sandbox-oft-delegate-hijack/](sandbox-oft-delegate-hijack/) |
| Balancer V1 (legacy pools) | Same: wider scope than press, not fully priced | [balancer-v1-rounding/](balancer-v1-rounding/) |
| Maya Protocol (MAYAChain) | Unconverted CACAO balance in attacker's wallet, no rate | [mayachain-cacao-slash-drain/](mayachain-cacao-slash-drain/) |
| Coinsbuy | Tron leg full; only one Ethereum tx attributable | [coinsbuy-wallet-drain/](coinsbuy-wallet-drain/) |
| Cosmos EVM (MANTRA / TAC / KiiChain) | Source itself withholds 3 of the 6 chains hit | [cosmos-evm-vesting-underflow/](cosmos-evm-vesting-underflow/) |
| Oraichain (ICS-20 EVM Precompile) | Prices only 2 legs; excludes Injective-bridged/locked ORAI | [oraichain-ics20-precompile-selfmint/](oraichain-ics20-precompile-selfmint/) |
| COLDCARD (Weak Seed RNG) | Only 1st of 4 theft waves traced, about a third | [coldcard-rng-seed-theft/](coldcard-rng-seed-theft/) |
| Verus-Ethereum Bridge | 2nd exploit (2026-07-23, $7,530,000 per DefiLlama) not priced | [verus-ethereum-bridge-forged-proof/](verus-ethereum-bridge-forged-proof/) |

- Counting rule: funds returned by the attacker or reversed on-chain are
  deducted, so Liquid Network, Tectonic, Oraichain and the Safe LP Module
  report the unrecovered figure, and Moonwell its uncovered debt, not the
  higher gross amount (each footnote gives both readings).
  Reimbursements a protocol paid from its own reserves are not deducted.
- `tectonic-cronos/`'s script reads the chain's current state
  (`tectonic_risk_snapshot.py`), not a replay of the incident (the
  rollback erased the attack blocks), and its loss figures ($120.4M
  borrowed, $9.19M unrecovered) are sourced from Cronos's official
  post-mortem, not recomputed. Flagged here rather than hidden.
- The "Category" column in the Index is this project's own classification
  of an already-described mechanism, for scanning convenience, not a
  label sourced from DefiLlama, press, or the protocol itself. Several
  incidents plausibly fit more than one tag; each row carries the single
  tag judged most useful for finding it, the "Type/Mechanism" column next
  to it carries the actual nuance.

## Disclaimer

Every entry in this repo is an independent, factual reconstruction of
publicly available on-chain data (transaction receipts, decoded logs,
contract reads) as of the date noted per entry, not a security audit,
and not affiliated with, commissioned by, or endorsed by any protocol,
auditor, or outlet named in a subfolder.

- **No claim beyond the data.** Who sent, received, or drained funds is
  based solely on on-chain records and publicly disclosed information
  cited inline; no claim of wrongdoing beyond what that data shows is
  made or implied against any named address or entity.
- **Not advice.** Nothing in this repo is legal, financial, or investment
  advice.
- **A snapshot, not a live feed.** Balances, labels, and follow-up
  transactions can and do change after publication; entries are not
  updated automatically to reflect such changes.
- **Corrections welcome.** Any individual or entity named who believes a
  fact about them is inaccurate is invited to get in touch, privately if
  they prefer (see [SECURITY.md](SECURITY.md)), with supporting evidence
  for a prompt, public correction.

Readers should independently verify all cited addresses, transactions,
and figures before relying on them.

## License

MIT. See `LICENSE`. Deliberately open, including every reconstruction
script: each is wired to one already-public historical incident, so
anyone can rerun the same query against the same public chain data and
get the same number, which is what makes the corrections to press and
DefiLlama in this repo checkable rather than just asserted.
