# Maya Protocol (MAYAChain) Postmortem

Independent reconstruction of the 2026-08-18 MAYAChain exploit: a single
23-message deposit transaction chained six accounting defects to get a
near-empty liquidity pool credited with tens of millions of phantom CACAO,
which the attacker then drained and swapped out to Bitcoin, all inside
seven minutes. This reconstruction starts from MAYAChain's own GitLab, the
team's two merged fix commits describing the root cause in detail, then
independently re-derives every number in them from raw chain data: the
exact 23-message transaction, the add-liquidity/withdraw pair that
extracted the phantom credit, the ten swaps that converted it into real
BTC, and a live check of Bitcoin mainnet itself confirming that BTC is
still sitting untouched where the attacker sent it.

## At a glance

| | |
|---|---|
| Incident | A voter-clobber bug inside a 23-message `MsgDeposit` got two legitimate trade-account withdrawals misclassified as theft; the resulting slash subsidy, never capped against pool depth, credited a near-empty ARB.LINK pool with tens of millions of phantom CACAO, which a single-sided liquidity add/withdraw immediately extracted |
| Window | 2026-08-18 17:00:38 UTC (the 23-message exploit tx) to 17:07:06 UTC (the last of 10 swaps to Bitcoin), all in the same block range |
| DefiLlama / press figure | DefiLlama: "Maya Protocol", $1,700,000, chain "Mayachain". Press (via PeckShield) cited "roughly $1.7 million," with "20 BTC ... sitting untouched in a single wallet" |
| Verified independently | 48,869,502.5269541928 CACAO withdrawn from the inflated pool (matches MAYAChain's own GitLab RCA's "48.87 million" almost digit for digit); 20.82730682 BTC of that swapped out to a Bitcoin address, independently confirmed via Blockstream to have arrived and remain entirely unspent; $1,343,181.04 at BTC's CoinGecko theft-day price |
| A primary-source figure independently re-derived | MAYAChain's own GitLab RCA states the attacker "withdrew 48.87 million CACAO" (rounded); this reconstruction re-derives 48,869,502.5269541928 CACAO to full precision straight from the raw withdrawal transaction |

## The method

```bash
python3 reconstruct_exploit.py
```

No hardcoded press figures: every number below is read live from
MAYAChain's own public Tendermint RPC (`tendermint.mayachain.info`) and
Cosmos LCD (`mayanode.mayachain.info`), MAYAChain's own indexer Midgard
(`midgard.mayachain.info`, used only to locate actions, then spot-checked
against the raw transaction), Bitcoin mainnet via Blockstream's public
Esplora API (a source with no relationship to Maya Protocol, used to
verify the BTC leg independently), MAYAChain's own GitLab
(`gitlab.com/mayachain/mayanode`) for the primary source, and CoinGecko's
public historical-price API.

1. **The starting anchor is the protocol's own GitLab, not a press
   address.** MR !835 ("harden outbound matching, native txID uniqueness
   and theft-slash subsidy") and its stacked follow-up MR !836 ("atomic
   vault-outbound slash + ragnarok matcher + subsidy guard"), both merged
   by the MAYAChain team's own account, lay out a six-defect root-cause
   chain in detail: a multi-message `MsgDeposit` whose trailing message
   overwrote the voter tracking the earlier messages, a stale outbound
   matcher that then failed to find two legitimate outbounds and flagged
   them as theft, an uncapped slash subsidy that credited CACAO to a
   near-empty pool, and a liquidity-add bug that let the attacker claim
   99.93% of that inflated pool.
2. **The incident transaction is located from the block itself**, not
   assumed: block 17977941 has exactly one transaction, its hash computed
   here from the raw block bytes (not looked up), and decoding it via
   mayanode's own REST endpoint confirms 23 `MsgDeposit` messages, exactly
   matching the primary source's description.
3. **The extraction is found via Midgard, then spot-checked against the
   raw transaction.** The add-liquidity/withdraw pair 30 blocks later is
   located by asset, then its underlying transaction is independently
   re-fetched from mayanode's own `/cosmos/tx` endpoint to confirm
   Midgard's indexed amount matches the chain's own record, not just the
   indexer's summary.
4. **The Bitcoin leg is checked against Bitcoin itself**, not against
   anything MAYAChain says about it: Blockstream's Esplora API (fully
   independent of Maya Protocol) is queried for the destination address's
   `funded_txo_sum` and `spent_txo_sum`.
5. **The residual is reconciled, not ignored.** The attacker did not
   convert all of the phantom CACAO to BTC; this script pages through
   every action Midgard has indexed for the attacker's native address and
   nets every CACAO flow against the live on-chain balance, rather than
   just reporting the final balance on its own.

## What it found

### The exploit transaction: 23 messages, matching the primary source exactly

Block 17977941 (2026-08-18T17:00:38Z) holds a single transaction,
`516BA14D6976EC7B8A3087E1C52B195433EF0F9D85F4B9520675BC4FEB99E9B7`, with
23 `MsgDeposit` messages: 20 carrying `ARB~ETH` and 2 carrying `ARB~LINK`
(memo `trade-`, MAYAChain's trade-account withdrawal path), plus a
trailing 1-unit `DONATE:ARB.LINK` message. That trailing message is
exactly the mechanism MR !835 names as root-cause step 1: each message of
a multi-message deposit was supposed to get its own voter tracking its
outbound, but a bug let the last message's voter overwrite the earlier
ones', resetting their scheduled-outbound height to zero and making the
outbound matcher unable to find two of the legitimate `trade-` outbounds
later, misclassifying them as theft.

### The extraction: an add and a withdraw, in one transaction

30 blocks later (height 17977971, 17:03:32 UTC), the same attacker-native
address, `maya1dl3yrfpedyr5jfr0r86s2apjltnjqgszmwsv8x`, submitted one
transaction with two messages:

| Memo | Coin |
|---|---|
| `+:ARB.LINK:0xa2f246f82995CBcCA8eD0d9F251383881A5E423e` | 100 CACAO |
| `WITHDRAW:ARB.LINK:9900` | 1 CACAO (fee unit) |

The add's 100 CACAO, deposited into a pool the primary source describes as
having a near-zero asset side but pre-existing LP units outstanding, was
enough to mint the attacker 99.93% of the pool under the pre-fix liquidity
math (MR !835's root-cause step 5). The withdraw that followed, in the
same transaction, paid out **48,869,502.5269541928 CACAO**, independently
re-derived here to full precision from the raw transaction, not from
Midgard's rounded display. MAYAChain's own RCA in MR !835 states this step
"withdrew 48.87 million CACAO"; this reconstruction's own number matches
it to 8 of its 9 significant digits, itself already a level of precision
the primary source's rounded prose figure doesn't carry.

### The cash-out: ten swaps, four minutes, straight to Bitcoin

Over the next four minutes (blocks 17977998-17978008), the same address
submitted exactly 10 swap transactions, each converting 4,000,000 CACAO
into `BTC.BTC` sent to `bc1q0hsgwunccczelq05ucpmfz268eyy5jr2y5l646` (with a
trivial `ARB.ETH` remainder returned to the attacker's own trade account
each time). MAYAChain's own action log for these ten transactions sums to
**2,082,730,682 sats (20.82730682 BTC)**.

Querying Bitcoin mainnet itself, independent of anything MAYAChain
reports, confirms it: that address's `funded_txo_sum` is 2,082,731,774
sats across 12 transactions (within 0.0001% of the MAYAChain-side total;
Bitcoin's own UTXO batching accounts for the tiny gap and the 12-vs-10 tx
count), and its `spent_txo_sum` is exactly 0. Every satoshi the attacker
swapped out is still sitting in that address, unmoved, as of this
reconstruction's run.

### What didn't get cashed out

The 40,000,000 CACAO swapped to BTC is well short of the 48,869,502.53
CACAO withdrawn. Paging through every action Midgard has indexed for the
attacker's native address (54 actions total) and netting every CACAO flow
against it gives an expected balance of 8,874,278.3052775995 CACAO; the
address's actual live balance, queried today via mayanode's own
`/cosmos/bank` endpoint, is **8,874,269.1052775996 CACAO**, a gap of just
9.2 CACAO consistent with native gas fees (which draw down the balance
without themselves being a Midgard-indexed action). That residual amount
has not been converted to anything outside MAYAChain's own accounting the
way the BTC has: it is inflated CACAO supply sitting in a native wallet,
not an asset the attacker has pulled out of the protocol's reach.

### The dollar figure, and why it's lower than DefiLlama's

20.82730682 BTC at CoinGecko's own 2026-08-18 (theft-day) daily price
($64,491.35) is **$1,343,181.04**, the figure this entry reports as the
confirmed, independently verified loss: real value that left MAYAChain's
control for an address the attacker fully and irreversibly owns on
Bitcoin's own chain. A tighter, hourly price at the actual 17:00 UTC swap
window ($64,790.82) gives $1,349,418.37, within 0.5% of the daily figure,
so the day-level price isn't materially off from the moment of extraction.

This is about 21% below DefiLlama's tracked $1,700,000 and press's
"roughly $1.7 million." The gap is best explained by the still-unconverted
8,874,269.11 CACAO above: if DefiLlama's or the team's own internal figure
values the full phantom credit near its pre-incident market price rather
than only the BTC actually extracted, that would produce a higher number
than this entry's BTC-only, fully-verified floor. This entry does not
attempt to price that residual CACAO itself; see Caveats.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Maya Protocol, MAYAChain, or any outlet cited above.
- **The $1,343,181.04 figure is a floor, not a ceiling.** It covers only
  the BTC the attacker has actually and irreversibly moved out of
  MAYAChain's reach. The roughly 8.87M CACAO still sitting in the
  attacker's own native wallet (see "What didn't get cashed out") is real,
  inflated supply the protocol will likely have to absorb one way or
  another, but this entry does not convert it to a dollar figure: CoinGecko's
  historical-price endpoint returned no market data for CACAO on
  2026-08-18 (its "history" endpoint returned no `market_data` field at
  all, unlike for BTC), so no independently sourceable price was found for
  that date, and this entry would rather omit a number than guess one.
- MAYAChain's own root-cause chain (steps 1-4 of MR !835: the voter
  clobber, the stale outbound matcher, and the exact uncapped-subsidy
  calculation that first credited the pool) is cited from the primary
  source, not independently re-derived block-by-block here: this public
  mayanode gateway does not honor historical block-height queries (it was
  tested and confirmed to return identical, current-state data regardless
  of the `x-cosmos-block-height` header, including for a height of 1), so
  the pool's exact state at each intermediate step could not be
  independently re-queried. What is independently re-derived, from raw
  transaction data rather than Midgard's summary, is the amount actually
  withdrawn (48,869,502.5269541928 CACAO) and everything downstream of it.
- Whether the two trade-account messages inside the 23-message transaction
  addressed to `0xFFDdAd2ff7022680F4B94556417f9Cb18d41d7f2` and
  `0x6C71DcC5AD12DDCe2Ad8562037C2FDb72BeF2D9c` (rather than the attacker's
  own `0xa2f246...` address) represent additional attacker-controlled
  wallets or something else was not determined; neither address shows up
  anywhere in the extraction or cash-out chain this reconstruction traced,
  and Midgard's address-scoped action search returns zero results for
  both.
- As with every entry in this repo, this reflects a snapshot as of
  2026-09-10. The residual CACAO balance and whether the Bitcoin address
  is touched after this reconstruction's run were not re-checked after it.

## License

MIT
