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
| Incidents covered | 13, independently reconstructed on-chain, see the index table for detail |
| Cumulative loss, recomputed | About $85.8M across the 13 incidents ($85,757,713 exactly, sum of the figures in the table below). At least one entry is a known floor, so the real total is higher. |
| Corrections made | 4 of the first 8 incidents correct at least one already-published press or DefiLlama figure or label: Sandbox (real loss about 5.2x the reported figure), Balancer V1 (4 pools drained, not the single one reported), Notional V1 (DefiLlama's own feed labels the exploited contract "V2" when it's actually V1), Cozy V2 Optimism (both Cozy's own figure and DefiLlama's undercount the verified on-chain total). A 5th, different kind of correction: Cosmos EVM catches a citation error in a primary source itself (Cosmos Labs' own official post-mortem), not just press or DefiLlama. A 6th, same kind: the Allbridge CCTP entry catches SlowMist's own published post-mortem stating the wrong date (July 26) for a transaction independently found and timestamped July 25, confirmed on two RPC endpoints; it also separates the Router's real loss, the attacker's net profit, and DefiLlama's gross-balance figure, three different numbers DefiLlama's single tracked total conflates. A 7th, same kind again: the Liquid Network entry catches the project's own incident report citing 15:53:10 UTC for the block where the exploit happened, when that block's own chain-recorded timestamp, read live, is 13:53:10 UTC; it also reports the still-unrecovered floor (598.50 BTC) rather than DefiLlama's pre-return gross figure ($320,000,000), since most of the drained BTC was returned the next day. An 8th entry, a reconciliation rather than an error: Aquifer's independently-derived loss ($2,418,164, priced at the moment of the actual theft) sits about 2% below DefiLlama's tracked $2,469,729, and re-pricing the exact same on-chain amount one day later, when the attacker actually consolidated it, lands within 0.05% of DefiLlama's figure, pinning down which moment DefiLlama's own pipeline priced this at without needing to call either number wrong. A 9th entry, another reconciliation: the Maya Protocol (MAYAChain) entry's independently-derived, BTC-only loss ($1,343,181.04) sits about 21% below DefiLlama's tracked $1,700,000; rather than calling DefiLlama wrong, this entry traces the gap to a specific, still-unconverted 8.87M CACAO balance sitting in the attacker's own wallet, reconciled live against every CACAO flow found for that address. This count is updated by hand each time a new correction is found, `add_new_entry.py` doesn't touch it |
| Method | Each subfolder keeps its original Python reconstruction script, its `registre_hypotheses.csv` falsification registry, and its script's raw output in `resultats_*.txt`, so every figure below can be checked against the file that produced it |
| License | MIT across all 13 entries, single author (s_pap, 2026) |

## Index

Sorted by recomputed loss, descending. The "Type/Mechanism" column reflects
what the on-chain reconstruction actually found, not the incident's press
label.

| Protocol | Date | Loss ($) | Chain | Type/Mechanism | Link |
|---|---|---|---|---|---|
| Liquid Network | 2026-09-06 / 09-07 | ≥ 46,568,719 [^liquid-rangeproof-cache] | Bitcoin + Liquid | Range-proof cache-key collision in Elements let a peg-out register as fully backed; the federation's real multisig then genuinely signed the BTC release | [liquid-rangeproof-cache/](liquid-rangeproof-cache/) |
| Moonwell (MAMO market) | 2026-08-27 | ≈ 9,131,000 [^moonwell] | Base | Donation attack on an illiquid market's exchange rate, combined with collateral/oracle manipulation | [moonwell-mamo-oracle/](moonwell-mamo-oracle/) |
| Term Finance (Meta Vault) | 2026-08-17 / 08-23 | ≈ 8,500,000 [^termfinance] | Ethereum | Hijacked governance: a proposal self-voted by a fresh wallet through an attacker-deployed executor, normal 6-day delay elapsed with no veto | [termfinance-metavault-governance/](termfinance-metavault-governance/) |
| Tectonic | 2026-08-30 | ≈ 8,300,000 [^tectonic] | Cronos | Donation attack (recursive collateral minting then direct donations to the market contract) inflating an exchange rate, massive borrowing against the inflated collateral, followed by a chain rollback | [tectonic-cronos/](tectonic-cronos/) |
| Cosmos EVM (MANTRA / TAC / KiiChain) | 2026-08-20/08-22 | ≥ 5,720,000 [^cosmos-evm-vesting-underflow] | MANTRA + TAC + KiiChain (+ 3 unnamed Cosmos EVM chains) | Underflow then overflow of the native balance in a shared Cosmos EVM staking precompile | [cosmos-evm-vesting-underflow/](cosmos-evm-vesting-underflow/) |
| Aquifer | 2026-08-31 / 09-01 | ≈ 2,418,164 [^aquifer-sweeper-arbitrary-call] | Solana + Ethereum | Arbitrary external call on a verified cross-chain Sweeper contract redirected swept funds to the attacker's own address | [aquifer-sweeper-arbitrary-call/](aquifer-sweeper-arbitrary-call/) |
| Notional Finance (V1 Escrow) | 2026-09-03 / 09-04 | 1,727,782 [^notional] | Ethereum | `uint128` overflow/downcast in the legacy V1 Escrow contract's collateral valuation | [notional-v1-escrow/](notional-v1-escrow/) |
| Maya Protocol (MAYAChain) | 2026-08-18 | ≥ 1,343,181 [^mayachain-cacao-slash-drain] | MAYAChain + Bitcoin + Arbitrum | Voter-clobber misrouted a multi-message deposit, an uncapped theft-slash subsidy then credited phantom CACAO to a near-empty pool, drained by a single-sided add/withdraw and swapped out to Bitcoin | [mayachain-cacao-slash-drain/](mayachain-cacao-slash-drain/) |
| Ajna Finance | 2026-08-28 / 08-29 | ≈ 775,400 [^ajna] | Ethereum | Liquidation-math exploit (`Kick`) on pools deployed through a factory the protocol never documented | [ajna-liquidation/](ajna-liquidation/) |
| The Sandbox (SAND / OFT) | 2026-08-21 / 08-22 | ≥ 675,000 [^sandbox] | Base + BSC + Ethereum | LayerZero delegate hijack via a legacy `approveAndCall` primitive, a composition bug, not a compromised key | [sandbox-oft-delegate-hijack/](sandbox-oft-delegate-hijack/) |
| Balancer V1 (legacy pools) | 2026-08-30 / 08-31 | ≥ 234,000 [^balancer] | Ethereum | Rounding error on unmaintained V1 pools, repeated 1-satoshi joins | [balancer-v1-rounding/](balancer-v1-rounding/) |
| Allbridge (CCTP Forged Message) | 2026-07-25 / 08-19 | ≈ 190,156 [^allbridge-cctp-forged-message] | Polygon + Base | Forged Circle CCTP message accepted without checking the mint recipient, unlocked with a self-funded Aave flash loan to match the fabricated credit | [allbridge-cctp-forged-message/](allbridge-cctp-forged-message/) |
| Cozy V2 | 2026-09-02 / 09-07 | 174,311 [^cozy] | Optimism | False answers to the UMA Optimistic Oracle left uncontested during its 5-day dispute window | [cozy-v2-optimism/](cozy-v2-optimism/) |
[^cosmos-evm-vesting-underflow]: Cosmos Labs' own post-mortem (github.com/cosmos/security, 2026-08-28) states $5.72M realized across all 6 exploited chains ($2.87M DEX-sold, $2.85M CEX-frozen), explicitly "not independently audited", with 3 of the 6 chains left unnamed. Independently reconstructed against each named chain's live RPC: TAC's exact drain (2,985,651,403.40 TAC, from a self-derived bonded_tokens_pool address, not looked up anywhere) and MANTRA's two attack transactions both matched the post-mortem's own cited figures to the block and second. KiiChain's reconstruction caught a citation error in the post-mortem itself: the transaction hash it cites for the KiiChain anchor sits at block 9355107, not the 9355102 stated, confirmed independently via two separate RPC calls. DefiLlama tracks this as 3 separate rows summing to $17.2M, a real, disclosed gap against the primary source's own $5.72M, not resolved either way here. See `cosmos-evm-vesting-underflow/README.md`.
[^allbridge-cctp-forged-message]: Allbridge's Router (0xaa119f7442ecc28b9a8f236707ada8362cff24ff, verified as "Router" on Base Blockscout) held 191,155.976393 USDC one block before the attack and exactly 1,000.000000 USDC one block after (read live via `eth_call`), a real Router loss of 190,155.976393 USDC. Of that, the attacker's own transaction receipt shows a kept profit of 189,751.554381 USDC and a 404.422012 USDC flash-loan fee paid to Aave, matching SlowMist's own published post-mortem to 6 decimals throughout. DefiLlama tracks this incident as "Allbridge", $191,000, Base only; that figure sits closer to the Router's gross pre-attack balance than to either the real loss or the attacker's profit. This reconstruction also independently found the Polygon setup transaction SlowMist's article never names, and caught a one-day date error in that same article (see `allbridge-cctp-forged-message/README.md`). External source: https://slowmist.medium.com/a-cross-chain-attack-spanning-one-month-analysis-of-the-allbridge-hack-32a6183bce08.
[^liquid-rangeproof-cache]: A range-proof cache-key collision in Elements (ElementsProject/elements PR #1600, merged 2026-09-08, released as elements-23.3.4) let a peg-out register as fully backed when it was not; the federation's real 11-of-15 multisig, decoded live from its own witness script, then genuinely signed 3 transactions releasing 4,007.82220180 BTC from its Bitcoin reserve on 2026-09-06 (read live via the public Esplora API, not a stolen key). A single return transaction sent 3,400.00000000 BTC back on 2026-09-07; the source address's own live balance, queried again 2026-09-10, is 598.50041569 BTC, essentially unchanged since, which is the still-unrecovered floor reported here (two smaller untraced destination addresses, 6.65 BTC combined, are excluded from it). DefiLlama tracks this as "Liquid Network", $320,000,000, dated 2026-09-06, the gross figure before the return. This reconstruction also caught Liquid Network's own incident report citing 15:53:10 UTC for block 4,050,336, when that block's own chain-recorded timestamp is 13:53:10 UTC. See `liquid-rangeproof-cache/README.md`.
[^aquifer-sweeper-arbitrary-call]: Aquifer's own Solana upgrade authority (8pJhHxPQRiUGdtVSCNPyP9AH994zeyYEBGb5yZRzheSA, confirmed live against the program's own programData account, not just claimed by the message itself) signed an on-chain whitehat offer to the attacker's wallets. The attacker's Ethereum address received 1000.7955696018159 ETH across 3 transactions on 2026-08-31 (two from a decoded `sweepAndExecute` call on a verified "Sweeper" settlement contract, one a plain transfer), then moved 1000.7955471888082 ETH out in one transaction the next day. At CoinGecko's 2026-08-31 (theft-day) price this is $2,418,164; at CoinGecko's 2026-09-01 (the day the attacker actually moved it) price it is $2,468,528, within 0.05% of DefiLlama's own tracked $2,469,729 for this incident, suggesting DefiLlama priced the loss nearer the later date. The 2026-09-03 14:00 UTC whitehat deadline passed with the designated recovery addresses still holding, checked live 2026-09-10, less than 1 SOL and less than 0.002 ETH between them. See `aquifer-sweeper-arbitrary-call/README.md`. External source: https://api.llama.fi/hacks.
[^mayachain-cacao-slash-drain]: MAYAChain's own GitLab (MR !835/!836, merged by the team's account) describes a 6-defect chain: a 23-message `MsgDeposit`'s trailing message clobbered the voter tracking the earlier ones, the stale outbound matcher then misclassified 2 legitimate withdrawals as theft, and the resulting uncapped slash subsidy credited a near-empty ARB.LINK pool with phantom CACAO, extracted moments later by a single-sided liquidity add/withdraw the primary source states "withdrew 48.87 million CACAO". Independently re-derived from the raw withdrawal transaction to full precision: 48,869,502.5269541928 CACAO. Of that, 20.82730682 BTC was swapped out to a Bitcoin address; queried live against Bitcoin mainnet itself (Blockstream, independent of MAYAChain), that address's `spent_txo_sum` is 0, confirming the BTC arrived and is still untouched. At CoinGecko's 2026-08-18 (theft-day) price, that is $1,343,181.04, reported here as a confirmed floor. DefiLlama tracks this incident as "Maya Protocol", $1,700,000; the roughly 21% gap is most likely explained by the remaining 8,874,269.11 CACAO (reconciled live against every CACAO flow this reconstruction found for the attacker's wallet) still sitting unconverted in the attacker's own native address, not yet turned into an asset outside MAYAChain's own accounting the way the BTC has. See `mayachain-cacao-slash-drain/README.md`. External source: https://gitlab.com/mayachain/mayanode/-/merge_requests/835.

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
- Four entries (Sandbox, Balancer V1, Liquid Network, Maya Protocol) report
  a dollar figure that is a known floor, not a complete total, because
  their source repo found a wider scope than the press without converting
  every recovered amount to dollars, (Liquid Network) left some smaller
  destination addresses untraced, or (Maya Protocol) found a real,
  still-unconverted balance sitting in the attacker's own wallet that this
  repo declined to price for lack of a sourceable historical rate. Read the
  linked subfolder for the full accounting in native units.
- The Tectonic, Moonwell, and Liquid Network entries report the confirmed
  unrecoverable or still-uncovered figure, not the higher, gross amount
  borrowed or extracted before liquidations or, for Tectonic, a chain
  rollback, and for Liquid Network, a large partial return the next day.
  Both readings are given in the footnote and in the linked subfolder.
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

MIT. See `LICENSE`. Deliberately open, including every reconstruction script: unlike a reusable cross-protocol screening tool, each script here is wired to one already-public historical incident, so publishing it costs nothing competitively and buys real reproducibility, anyone can rerun the same query against the same public chain data and get the same number, which is what makes the corrections to press and DefiLlama in this repo checkable rather than just asserted.
