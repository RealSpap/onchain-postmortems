# BarnBridge Dormant-DAO Controller Swap Postmortem

Independent on-chain reconstruction of the governance takeover of BarnBridge
SMART Yield (Ethereum mainnet, 2026-07-06 to 2026-07-23). Press and DefiLlama
both price this incident at about $776K in USDC, drawn from one transaction
against one pool. Reading the governance contract's own event log instead of
the coverage turns up **five proposals, three of them executed, seventeen
extraction transactions, three attacker wallets and ten pools**, for
**$1,931,365.22** of stablecoins pulled out of user wallets, 2.49x the
reported figure. Every contract address below was resolved from BarnBridge's
own committed deployment registry or from an execution receipt on chain,
never from a block-explorer name search.

## At a glance

| | |
|---|---|
| Incident | Governance takeover of an abandoned DAO, used to swap the Controller of every SMART Yield provider and drain live ERC-20 approvals, Ethereum mainnet |
| Window | 2026-07-06 08:08:11 UTC (first BOND stake) to 2026-07-23 17:34:35 UTC (last extraction), 17 days 9 hours |
| Press figure | ~$776K in USDC, ~50 users, one transaction (BlockSec); DefiLlama: $776,000, dated 2026-07-14; ~$777,000 across two sweeps (Blockaid, published after this entry, see 2026-09-18 note below) |
| Verified independently | **$1,931,365.22**: 1,877,869.183182 USDC + 51,759.121322 USDT + 1,736.920247 DAI, across 17 extraction transactions |
| Correction to press | The published figure is at most two transactions out of seventeen. BlockSec and DefiLlama price the incident from `0xd191fead…` alone (774,943.379409 USDC, and its "50 users" is exactly right: 50 distinct source wallets, counted leg by leg); Blockaid additionally names `0x7d722637…` (1,632.168524 USDC). The two together are 776,575.547933 USDC, 40.2% of the total |
| Note on DefiLlama's date | The feed dates the incident 2026-07-14 (timestamp 00:00:00 UTC). The first extraction is at block 25,535,120, 2026-07-15 02:39:47 UTC, which is still the evening of July 14 in US time zones, so the feed's date may reflect a non-UTC calendar day rather than an error. In UTC, BlockSec's July 15 matches the chain |
| Discovery not in any source found | Proposals 15 and 16 were also executed. Proposal 16 transferred `owner`/`dao` of **ten** core BarnBridge contracts, including the Barn staking contract itself, to the attacker EOA |
| State at block 25,955,104 | At block 25,955,104 (2026-09-11 15:37:47 UTC) all ten proposal-16 targets still returned the attacker EOA as owner, and the SmartYield *token* contracts still pointed at an attacker-installed Controller. The bb_cUSDC *pool* contract itself (the fund-custody address, same one H11 traces the theft to) pointed at a third, unattributed Controller instead (see 'What's still open' below). Current status not re-verified since that block |
| What's still open | 3,001,678.69 USDC left the bb_cUSDC provider between 2026-08-22 and 2026-08-31 through a *third* Controller, installed after the attack, which is also the address bb_cUSDC's pool contract pointed to at block 25,955,104. This project could not attribute it and excludes it from the figure above |

## The method

```bash
python3 reconstruct_exploit.py
```

BarnBridge publishes its own mainnet addresses in `barnbridge-subgraph-2.0`,
one `subgraph.yaml` per deployed pool. This project reads that repository
straight from GitHub to enumerate the SMART Yield universe, then resolves
each pool's `pool()` and `controller()` by live `eth_call`, so the set of
affected contracts is derived from BarnBridge's own records rather than
guessed.

That registry turned out to be incomplete, which is itself worth stating.
Nine pools carry an address in their manifest; a tenth provider, bb_cUSDT
(`0x6ac048ee380cbf0cb22c30401e710c28d91eb94d`), has none, and a scan built
only from the repo silently misses the 22.171476 USDT taken from it. The
tenth was recovered from proposal 15's own execution receipt, where each
pool whose Controller actually changed hands emits an `Approval` pair whose
owner is the provider. The script unions both sources rather than trusting
either alone (the first run of it, before that union existed, produced
1,931,343.05 instead of 1,931,365.22).

The Governance contract's entire log history for 2026 was then
pulled with `eth_getLogs`, every event topic recomputed from its signature
rather than looked up, and every proposal's payload decoded from
`getActions(uint256)`. Fund movement was reconstructed from raw `Transfer`
topics only. One free archive endpoint (`gateway.tenderly.co/public/mainnet`)
was used throughout, plus Blockscout's public API for contract-creation
metadata; no paid RPC and no API key anywhere.

The order matters and was kept strictly: the chain was read first, the press
second. The `$776K`-is-one-transaction finding is a consequence of that
order, not of a hunch about the coverage.

## What it found

BarnBridge stopped operating as a going concern years before 2026, but it
never turned its machinery off. Three things were left running at once: a
Governance contract that could still pass and execute proposals, a Barn
staking contract that still minted voting power to whoever deposited BOND,
and (the part that turned a dead protocol into $1.9M) thousands of ERC-20
approvals that users had granted to SMART Yield providers years earlier and
never revoked.

An attacker bought BOND on the open market, staked it at the maximum lock
multiplier, and voted itself the right to replace the Controller on every
pool. A Controller in BarnBridge can call the provider's internal
`_takeUnderlying(from, amount)` / `_sendUnderlying(to, amount)` pair. Point
those at a wallet that still has a live approval and the funds move with no
new signature from the victim.

### Voting power was bought, and the multiplier did the work

Three wallets staked BOND into the Barn (`0x10e138877df69ca44fdc68655f86c88cde142d7f`,
the address BarnBridge's own `barnbridge-governance-staking` subgraph names):

| Wallet | BOND deposited | Block / time | Voting power used |
|---|---|---|---|
| `0xf908610e9174c7cd6e9dfd371e238be4511297a1` | 32,000 | 25,472,195 (2026-07-06 08:08:11 UTC) | 63,824.1715 |
| `0xa8ce49a57400445c6a4118ae3460ed4e46c815b8` | 2,000 + 65,838 | 25,493,943 / 25,507,818 | 135,659.3524 |
| `0x2f6be6ac5af4af7ce7d618006ebd8d5137f2de11` | 150,781 (+ 39,550.28 after its vote) | 25,553,413 / 25,575,679 | 301,504.2857 (vote at block 25,560,921) |

Every one of the three votes with almost exactly **twice** the BOND it
had deposited at the time of its vote (the third wallet's second deposit of
39,550.28 BOND, at block 25,575,679, came after its proposal-16 vote at block
25,560,921). That is the Barn's lock multiplier at its ceiling: all three
wallets locked for the maximum term, the cheapest way to turn a given number
of tokens into governance weight. The Barn held 146,010.8951 BOND in total
before any of this started, so 32,000 BOND at 2x was already decisive on its
own, and BlockSec's independently published "approximately 43% of the total
voting power" is consistent with that.

The first stake landed at 08:08:11 UTC on 2026-07-06 and the first proposal
went up at 08:15:23 UTC, **seven minutes and twelve seconds later**. Nothing
about the sequence was opportunistic.

### Five proposals, three executed

Decoded from `getActions(uint256)` on the Governance contract
`0x4cAE362D7F227e3d306f70ce4878E245563F3069`:

| # | Created | Executed | Payload |
|---|---|---|---|
| 14 | 2026-07-06 08:15:23 | 2026-07-15 02:35:11 | `yieldControllTo(0x66c6f3b4…)` on one target: hands the bb_cUSDC pool to a contract the attacker deployed |
| 15 | 2026-07-09 09:23:59 | 2026-07-16 09:28:59 | `yieldControllTo(0x851e47f3…)` on **ten** targets: hands every remaining pool to a second attacker contract |
| 16 | 2026-07-15 19:11:11 | 2026-07-23 14:59:47 | `transferOwnership` on 5 contracts + `transferDAO` on 5 contracts, all to `0xf908610e…` |
| 17 | 2026-07-16 01:37:23 | never | `yieldControllTo(0x35a0a685…)` on 2 targets, **voted down** |
| 18 | 2026-07-16 10:52:11 | never | `transferDAO`/`transferOwnership` to `0x01c3dbd9…`, **voted down** |

Proposals 17 and 18 are the detail no source found mentions. They were
created by two *different* wallets (`0x01c3dbd90a0d639ca6c9f6a11928056168d72c89`,
which staked 100,000 BOND, and `0xb971770cd53b839004fdfcaf4cd2f5b39342cd9a`,
which staked 50,000) and they tried to redirect the same pools and the same
ownership to *their* addresses. All three of the original attacker's wallets
voted `support=false` on both, within six blocks of each other, and both
proposals died. A second party turned up to contest the takeover and was
outvoted. Whether that party was a rival attacker or a late rescue attempt
cannot be settled from the chain alone, but 0x01c3dbd9's own proposal 17
would have moved the pools to an address it controlled, not back to the DAO.

Proposals 14 and 16 were executed by contracts the attacker deployed
specifically for it: the `ProposalExecuted` events name callers
`0x8b5f73544e50f18791682d1bcb4bb5011ca81b00` and
`0xa5df767a55f11d5f89ede46dcb685880036ea5a4`, both created in the same
transaction that executed the proposal (the constructor calls `execute()`).

Each queued proposal was also followed, within one or two blocks and by the
same wallet, by `AbrogationProposalStarted`. The attacker opened the
abrogation window on its own proposals. In BarnBridge's design an abrogation
proposal that fails to reach quorum simply expires and clears the way; the
attacker started the clock itself rather than wait for someone else to.

### The extraction

The Controller contracts are the exploit. `0x66c6f3b4b4b458e6d764759ecf122484ebef7580`
was deployed by `0xf908610e…` and `0x851e47f37e20712407990556376a7124de5c3d4a`
by `0xa8ce49a5…`; neither is verified source, and both are **upgradeable
proxies**: `implementation()` and `admin()` both answer, and
`0x66c6f3b4…`'s `admin()` returns the attacker EOA itself. A backdoor that
can be re-pointed after installation.

Seventeen transactions moved funds. Every one of them has the same shape and
none of them burns a single SMART Yield share, which is what separates them
from an ordinary redemption:

```
victim wallet --(stale approval, transferFrom)--> provider --> attacker wallet
```

| Block | Time (UTC) | Pool | Amount | To |
|---|---|---|---|---|
| 25,535,120 | 2026-07-15 02:39:47 | bb_cUSDC | 774,943.379409 USDC | `0xf908610e…` |
| 25,535,160 | 2026-07-15 02:47:47 | bb_cUSDC | 1,632.168524 USDC | `0xf908610e…` |
| 25,542,518 | 2026-07-16 03:24:23 | bb_cUSDC | 500.000000 USDC | `0xf908610e…` |
| 25,544,358 | 2026-07-16 09:33:35 | aDAI/aUSDC/aUSDT/cDAI/cUSDT | 1,736.920247 DAI + 32,246.539372 USDC + 51,759.121322 USDT | `0xa8ce49a5…` |
| 25,546,439 | 2026-07-16 16:31:23 | bb_cUSDC | 118,030.000000 USDC | `0xf908610e…` |
| 25,561,666 | 2026-07-18 19:25:23 | bb_cUSDC | 6,082.879952 USDC | `0xf908610e…` |
| 25,567,102 | 2026-07-19 13:37:59 | bb_cUSDC | 5,004.794465 USDC | `0xf908610e…` |
| 25,573,294 | 2026-07-20 10:21:35 | bb_cUSDC | 63,753.681156 USDC | `0xf908610e…` |
| 25,586,832 to 25,586,837 | 2026-07-22 07:38:47 | bb_cUSDC | 6 × 0.000001 USDC to 6 addresses | probe |
| 25,589,161 | 2026-07-22 15:27:59 | bb_cUSDC | 94,629.874042 USDC (62 legs, one tx) | `0xf908610e…` |
| 25,596,937 | 2026-07-23 17:31:23 | bb_cUSDC | 524,353.111656 USDC | `0x5051da1c…` |
| 25,596,953 | 2026-07-23 17:34:35 | bb_cUSDC | 256,692.754600 USDC | `0x5051da1c…` |

**1,877,869.183182 USDC + 51,759.121322 USDT + 1,736.920247 DAI =
$1,931,365.22** at the $1 peg. The press's $776K is the first row.

Two details inside that table are worth separating out.

The six dust transfers at blocks 25,586,832 to 25,586,837 send exactly one
micro-USDC each, to six different addresses, one per block, six blocks in a
row, through a different function selector (`0x33bfd4b6`) than every other
extraction (`0xe321fa05`). That is an approval scanner: the cheapest possible
probe of whether a given victim's allowance is still live before committing
gas to a real pull.

The last two rows are the reason the attack ran for another eight days after
the press wrote it up. Victim `0x71f12a5b0e60d2ff8a87fd34e7dcff3c10c914b0`
had already lost 85,660 USDC in the first extraction. On 2026-07-23 the same
wallet was hit twice more, for 524,353.111656 and 256,692.754600 USDC, more
than the entire reported loss, from a single address that had by then had
eight days' public warning to revoke.

### The reported $776K, checked leg by leg

BlockSec's "approximately 50 users" is exactly right and this project can
confirm the exact number rather than the approximation. Transaction
`0xd191fead…` contains **50 distinct source wallets**, counted from the
`Transfer` legs into the provider, totalling 774,943.379409 USDC. The largest
single victim is `0x20c76d4203bf7490615804fe4fe9b132ee3e0935` at
125,628.402942 USDC; the smallest is
`0x1dd01835e0eb26abe597e2e69ffac1a6cd00283a` at 160.787907 USDC. The full
list is in `preuves/06_victim_legs_per_theft_tx.txt`.

Across all extraction transactions the distinct victim wallets number **87**
(65 in USDC, 13 in DAI, 11 in USDT, with overlap between tokens).

## Status at block 25,955,104 (2026-09-11 15:37:47 UTC)

At that block, fifty days after the last extraction, nothing had been
recovered or unwound:

- All five `transferOwnership` targets from proposal 16 returned
  `owner() == 0xf908610e9174c7cd6e9dfd371e238be4511297a1`, including the Barn
  staking contract `0x10e138877df69ca44fdc68655f86c88cde142d7f` that holds
  504,180.1751 BOND of other people's stake.
- All five `transferDAO` targets returned
  `dao() == 0xf908610e9174c7cd6e9dfd371e238be4511297a1`.
- Eight of the nine registry-listed SMART Yield pools routed through
  `0x851e47f37e20712407990556376a7124de5c3d4a`.
- bb_cUSDC's token contract named `0x66c6f3b4…` as its Controller.

Current status not re-verified since that block; details on open approvals
are withheld here.

## What this project could not attribute

Between 2026-08-22 and 2026-08-31, five transactions moved **3,001,678.69
USDC** out of the bb_cUSDC provider to `0xe4ed3720d16802dfaac61183b0ec3fe13520b908`,
including 2,468,514.560863 USDC in a single transaction at block 25,852,942.
The shape is identical to the July extractions: funds pulled from a wallet
via a stale approval, forwarded straight out, no share burned.

What is different is the entry point. The provider's `controller()` is no
longer either July Controller; it is now
`0xfd04775ef1c7e0486951f3431bc9bcd3dc6a90b8`, an unverified proxy whose
admin/dao slot holds `0x3588A1de656398e1336329A8194f2be8d80AF53a`, an
address with no observed link to the July wallets. And both the source and
the destination behave like high-frequency DEX routers: the 2.47M USDC was
split across Uniswap V4 and two Uniswap V3 USDC/WETH pools within two blocks
of arriving, and the source address has 511 token transfers including CoW
Protocol settlements.

Three readings fit: a continuation of the same theft under new infrastructure,
a third party that noticed the pool was ownerless and took it, or a
consensual arrangement between two trading addresses. This project cannot
choose between them from chain data alone, so the 3,001,678.69 USDC is
reported here and **excluded from the $1,931,365.22 figure**. If it turns out
to be theft, the real total is closer to $4.9M.

## Why a dormant DAO is an ownership problem

Much of the risk in DeFi sits with whoever holds a protocol's admin keys.
This incident is what happens when the answer is *nobody*: when a protocol winds
down and the keys are left with a smart contract that will hand them to
whoever shows up with enough tokens. A dormant DAO is not an unowned
protocol; it is a protocol whose owner is for sale at the market price of its
governance token. BlockSec's own figure for that price here is 0.335 ETH for
about 32,795 BOND; Blockaid, writing later, prices the 32,000 BOND the
attacker locked at about $600. Neither figure was re-derived here and the two
measure slightly different things, but on either of them the consideration
that bought $1.9M of other people's money was a few hundred to about a
thousand dollars.

It also sits next to `termfinance-metavault-governance` already in this repo,
which is the same class of bug on live governance rather than abandoned
governance.

## Caveats

- This is independent research, not an audit, and not affiliated with
  BarnBridge, BlockSec, GoPlus, Blockaid or DefiLlama.
- The `$1,931,365.22` total is stated in stablecoin face value at the $1 peg,
  not marked to the exact spot price of USDC, USDT and DAI at each block. The
  non-USDC part is 2.7% of the total, so this choice cannot move the headline.
- The extraction/redemption distinction rests on two signals: the entry
  point being an attacker-deployed Controller, and no SMART Yield share being
  burned in the transaction. Both were checked on every transaction in the
  table. Neither is a substitute for reading the Controllers' source, which
  is not verified on any explorer checked and was not decompiled here.
- BarnBridge's own subgraph registry is missing one provider (bb_cUSDT). The
  affected set stated here is nine registry-listed pools plus that tenth
  provider, recovered from an execution receipt. If a further pool exists
  that appears in neither source, this reconstruction would miss it too.
- The 2x lock multiplier is inferred from the ratio of voting power used to
  BOND deposited before each vote (63,824/32,000, 135,659/67,838,
  301,504/150,781; the third wallet's further 39,550.28 BOND arrived after
  its vote), not read out of the Barn's storage. The ratio is consistent across all three wallets
  but the exact lock parameters were not queried.
- BlockSec's "approximately 43% of the total voting power" and "0.335 ETH for
  about 32,795 BOND" are reported here as BlockSec states them; this project
  confirmed the 32,000 BOND deposit on-chain but did not re-derive the
  percentage or the purchase price.
- No official BarnBridge post-mortem was found (38 repositories enumerated on
  their GitHub organisation, plus a targeted search). Absence of a finding is
  not proof of absence. Re-checked 2026-09-18: still none.
- Source review, 2026-09-18. Blockaid has since published a full write-up
  ("Governance Takeovers: How $22M Was Drained and How to Stop Them"), where
  on 2026-09-11 this project had only their pre-drain approval alert on X.
  It is the first source found here to publish the *second* transaction hash,
  `0x7d722637a58a7117dbca0182ec26d74e2be0c1052ac319f0150bc056e528d238`, and it
  prices the incident at "$777,000" / "approximately $776,600 across two
  sweeps". That transaction was already in this project's own evidence
  (`preuves/05_outflow_tx_classification.txt`, row 2 of the extraction table)
  and was re-fetched and re-confirmed independently on 2026-09-18; see
  `resultats_sources_2026-09-18.txt`. The headline correction is unchanged:
  two of seventeen transactions, 40.2% of the verified total. DefiLlama's
  record was re-fetched the same day and is byte-identical to
  `preuves/12_defillama_hacks_record.json` (still $776,000, still
  `source: ""`).
- The August-September flows are explicitly unattributed. See above.

## Files

| File | What it is |
|---|---|
| `reconstruct_exploit.py` | Re-derives every figure in this README from RPC and GitHub |
| `registre_hypotheses.csv` | Falsification registry: one row per claim, with locator and test |
| `resultats_reconstruction_2026-09-11.txt` | Full console output of that script, the run every figure above was checked against |
| `preuves/` | Raw evidence: unmodified `eth_getLogs` output, decoded proposal payloads, full receipts, per-victim legs, current-state reads, verbatim press extracts |

## License

MIT
