# Radix (Hyperlane Warp Routes) Postmortem

Independent on-chain reconstruction of the Radix mainnet vault-access
incident (Radix + Ethereum, 2026-08-31). Radix is a Scrypto/Radix-Engine
L1, not EVM, not Cosmos-SDK. A single actor published a Scrypto blueprint
that abused the Engine's own "boot reference" resolution, letting one
function call `take`/`lock_fee` on any internal vault whose blueprint type
matched, with no check that the caller actually owned that vault. One
atomic transaction with 61 such functions drained 59 accounts and
components; 25 more transactions the same afternoon drained the rest.
Every asset taken was a Hyperlane-bridged synthetic (hUSDC, hUSDT, hETH,
hWBTC, hSOL, hBNB), so burning them on Radix and dispatching a bridge
message is what would let the attacker claim the real, collateral-backed
asset on the other side. Radix validators halted mainnet consensus a few
hours later; it had been offline for 11 days as of this reconstruction
(2026-09-11).

This project first learned the incident existed from the community-run
RADIX Wiki's incident page
(`radix.wiki/contents/history/hyperlane-asset-drain-2026`), which is not a
primary source and is not relied on for any figure below. Every address
comes from Hyperlane's own official GitHub deployment registry
(`hyperlane-xyz/hyperlane-registry`); every supply and transaction figure
is read live from Radix's own public Gateway API; the single largest
hUSDC-draining transaction is found by this project's own filtering of
that API's transaction stream, not copied from any secondary source; and part
of the loss is independently cross-checked on a second chain entirely
(Ethereum mainnet, via the real USDC/USDT contracts' own event logs). The
official fix (Scrypto v1.4.0, babylon-node v1.4.0.0-RC1, the "Eagle Ray"
protocol update) is confirmed directly from `radixdlt`'s own GitHub repos.

## At a glance

| | |
|---|---|
| Incident | A missing owner check on direct vault references in the Radix Engine kernel let a published blueprint call `take`/`lock_fee` on arbitrary internal vaults with no badge, proof, or other authorization primitive. The largest of 26 attack transactions used 61 functions to drain 59 accounts/components of 442,985.632108 hUSDC in one atomic call, then dispatched it through Hyperlane's own warp-route component toward Ethereum. Across all 6 Hyperlane-bridged assets on Radix (hUSDC, hUSDT, hETH, hWBTC, hSOL, hBNB), this reconstruction independently measures a combined drop of ≈$1,251,369 at theft-day prices. Radix validators halted mainnet consensus the same evening; it was still halted on 2026-09-11 while a protocol fix was validated |
| Window | 2026-08-31, sweep 16:02-16:57 UTC (independently confirmed below); mainnet halt 21:19:06 UTC the same day, still ongoing as of this reconstruction (2026-09-11) |
| DefiLlama figure | $1,249,946, chain-level row "Radix", classification "Access Control" / "Improper Access Control" (no source URL attached in the feed) |
| Verified independently | The exact halt point (state_version/epoch/round/timestamp) is confirmed live against Radix's own Gateway API; per-asset supply drops during the sweep are independently measured from each resource's own `total_supply` before/after, not assumed from any report; the single largest hUSDC-draining transaction is found by this project's own live filtering of the transaction stream, and its `BurnFungibleResourceEvent`/`SendRemoteTransferEvent` are decoded directly, matching the summed vault withdrawals to the cent; the theft-day USD total this project independently computes (≈$1,251,369) lands within 0.11% of DefiLlama's tracked figure |
| What's still open | Cross-checking Ethereum mainnet for the recipient address named in the largest transaction's own `SendRemoteTransferEvent` finds no USDC delivery matching that message as of this reconstruction; the only USDC delivered matches a smaller, later hUSDC message (see below); this project did not trace the Solana- or BSC-side legs (hSOL, hBNB) at all, and prices 4 of the 6 assets using CoinGecko's daily historical close rather than a per-transaction spot rate |

## The method

```bash
python3 reconstruct_exploit.py
```

Starting anchor: `hyperlane-xyz/hyperlane-registry`, Hyperlane's own
official GitHub deployment registry, not a block explorer. Its
`deployments/warp_routes/<ASSET>/*.yaml` files name the Radix-side
component address for each of the 6 bridged assets directly. One of those
files (`ETH/ethereum-radix-deploy.yaml`) turns out to hold an address one
character shorter than its own `ethereum-radix-config.yaml` copy of the
same address (`...zm7pc` vs. the correct `...zm7pcq`), a real bug in the
registry's own data, caught here because the shorter string fails Radix's
Bech32m checksum outright when queried; the script uses the
`config.yaml` value instead and shows this check explicitly.

RPC/REST endpoints used, all public, no key:
`mainnet.radixdlt.com` (Radix's own official Gateway API), `eth.drpc.org`
(public Ethereum JSON-RPC), `raw.githubusercontent.com` and
`api.github.com` (official `hyperlane-xyz` and `radixdlt` GitHub repos),
`api.coingecko.com` (theft-day historical pricing), `api.llama.fi/hacks`
(DefiLlama's own tracked record, for comparison only).

## What it found

### The halt, confirmed live against Radix's own Gateway API

Radix's Gateway API refuses "current state" reads outright (a
`NotSyncedUpError`, since its indexer compares last-processed time
against wall-clock time and mainnet has produced nothing new in 11 days);
every read in this reconstruction instead passes an explicit
`at_ledger_state` (a `state_version` or `timestamp`), which the API
answers normally. Querying `/status/gateway-status` this way returns:

```
state_version: 557840622
epoch/round:   339896/102
proposer_round_timestamp: 2026-08-31T21:19:06.179Z
```

Live, unprompted, and matching the community wiki's own claimed halt
point exactly, an independent confirmation this project did not have to
take on faith.

### The sweep, measured from each resource's own total_supply, not assumed

For each of the 6 Hyperlane-bridged assets, this project reads the
resource's own `total_supply` at 16:01 UTC (just before the sweep, per
the community wiki's own claimed window) and at 17:00 UTC (just after),
both live against Radix's Gateway API:

| Asset | Supply 16:01 UTC | Supply 17:00 UTC | Drop |
|---|---|---|---|
| hUSDC | 460,006.679705 | 1,091.793964 | 458,914.885741 |
| hUSDT | 72,420.420768 | 0.036292 | 72,420.384476 |
| hETH | 62.088284 | 0.010278 | 62.078006 |
| hWBTC | 6.353842 | 0.005600 | 6.348243 |
| hSOL | 536.196143 | 0.036338 | 536.159806 |
| hBNB | 32.912210 | 0.002105 | 32.910105 |

These are burns, not transfers: each asset is a synthetic Hyperlane
"HypToken" minted 1:1 against real collateral locked on its origin chain,
so a real supply drop here means real vaults were emptied and the
proceeds burned to be re-minted (as the real underlying asset) elsewhere.

### The largest hUSDC-draining transaction, found by this project's own filtering, decoded byte for byte

"The single largest transaction of the whole incident" is not a
well-defined question here: several of the 26 attack transactions target
different assets with similarly-sized manifests and near-identical fees,
so fee alone is not a reliable way to single one out (an earlier pass of
this same script tried exactly that and it surfaced the wrong
transaction). Instead, filtering `/stream/transactions` by
`affected_global_entities_filter=[hUSDC resource address]` over the sweep
window returns exactly 3 transactions that touched hUSDC at all; fetching
each one's own `balance_changes` shows one of them withdrew far more
hUSDC than the other two combined (442,985.632108 vs. 384.810629 and
15,544.443004). That transaction,
`txid_rdx19lzunu3relu436dm9r4mnmvyjx3yzr2723gk7d7kv0tce8g9h4kqd60u5v` at
**2026-08-31T16:33:28.554Z** (fee 8.39329093338 XRD, touching 68 global
entities), is the one this project singles out as "the largest hUSDC
drain." Fetching its own committed details (`balance_changes` +
`receipt_events` opt-ins) shows:

- **59 distinct entities** with a negative hUSDC balance change, summing
  to exactly **442,985.632108 hUSDC** withdrawn.
- A **`BurnFungibleResourceEvent`** on the hUSDC resource itself for the
  identical amount, **442,985.632108**.
- A **`SendRemoteTransferEvent`** emitted by the hUSDC warp-route
  component: `destination_domain=1` (Ethereum), `application_recipient
  =0x67899664446ccfadf75e0d3f5668be262acd1069` (the exact Ethereum-side
  hUSDC collateral router address named in Hyperlane's own registry, an
  independent cross-check that this really is the USDC warp route and not
  a lookalike), `user_recipient=0x626d7be5c2f2b6e9baa542e25b6313ac91d47cd2`
  (the attacker's own Ethereum receiving address), `amount=442985.632108`.
- A matching **`DispatchEvent`** from the Hyperlane mailbox component
  (`destination=1`, `sequence=3880`), confirming the cross-chain message
  was genuinely queued, not merely logged.
- **61 `WithdrawEvent`s** in total (59 for hUSDC vaults plus 2 for the
  attacker's own XRD fee vault), and the transaction's own `LockFeeEvent`
  is for the attacker's own fee, self-funded from an account holding 500
  XRD, no authorization primitive of any kind appears against any of
  the 59 drained vaults themselves.

The withdrawn total, the burn amount, and the dispatched amount agree to
the microunit: an internally consistent, atomic drain-and-dispatch, not
three separate claims stitched together after the fact.

### Root cause, confirmed against `radixdlt`'s own merged fix, not the wiki's paraphrase

`radixdlt/radixdlt-scrypto` pull request **#2093** ("0xOmarA/vault
access"), opened **2026-09-02T12:26:45Z** and merged
**2026-09-07T17:33:31Z** into what became release **v1.4.0** (the "Eagle
Ray" protocol update, published 2026-09-07T17:35:11Z), adds a new
`should_check_method_receiver_access` gate to the kernel's invocation
path (`system_callback.rs`): for a `Direct`-method-type invocation (the
pattern the attacker's blueprint used to reach vault internals directly)
the kernel now requires the node's own visibility to already permit that
direct call; for a normal `Main`/`Module` method it now requires the
*opposite* (the node must NOT be reachable as a bare direct reference).
Before this version shipped, neither case was checked, exactly matching
the drain's own mechanism: a blueprint holding a raw vault address could
invoke `take`/`lock_fee` on it with no ownership proof at all. A companion
fix landed in `radixdlt/babylon-node` PR **#1076** (opened
2026-09-08T06:00:59Z, merged same day), shipping as node release
**v1.4.0.0-RC1** (2026-09-08T15:35:42Z). Both are read directly from
`api.github.com`, not from the community wiki's summary of them.

### Cross-chain check: how much of this one message actually landed as real USDC?

Independently searching Ethereum mainnet's real USDC contract
(`0xA0b86991c6218b36C1D19D4a2e9Eb0cE3606eB48`) for `Transfer` events to
the attacker's own recipient address
(`0x626d7be5c2f2b6e9baa542e25b6313ac91d47cd2`, taken directly from the
Radix-side `SendRemoteTransferEvent` above, not guessed) finds exactly
one matching transfer as of this reconstruction:

```
15,544.443004 USDC, from 0x67899664446ccfadf75e0d3f5668be262acd1069
(the same Hyperlane collateral router named above),
block 25,876,572, 2026-08-31T16:51:11Z, tx 0x2798497bc623...37e30
```

That amount is exactly the hUSDC withdrawn by a different, later Radix
transaction (`txid_rdx177qfu39...`, 2026-08-31T16:50:54Z, 15,544.443004
hUSDC, listed in Step 4 of the result file), and it arrived on Ethereum
17 seconds after it. It is therefore most plausibly the full delivery of
that third message, not a partial delivery of the largest one. The
442,985.632108 hUSDC message (sequence 3880) produced no USDC transfer to
this recipient in the Ethereum blocks searched, which run from the attack
to the chain head at the time of the run (about 11 days). Why that
message was not delivered is not explained by anything this project can
see on either chain: the Radix-side dispatch and burn are unambiguous and
atomic. A plausible explanation, not independently confirmed, is that
Hyperlane's relayer infrastructure for this warp route was paused once
the exploit was discovered, leaving that message unprocessed; this
project did not find an official Hyperlane statement to that effect, so
it is reported as an open question, not a conclusion. The same search against the real USDT
contract (`0xdAC17F958D2ee523a2206206994597C13D831ec7`) for the same
recipient address finds 3 transfers, from a different Hyperlane router
address, totaling 71,937.389621 USDT (99.3% of the 72,420.384476 hUSDT
this project separately measured leaving Radix across all 26 attack
transactions combined, not just the largest one), so this pattern is not
universal across assets.

### Pricing the full drop, and reconciling against DefiLlama

Applying CoinGecko's 2026-08-31 historical close price to the 4
non-stablecoin drops, and pricing hUSDC/hUSDT at face value, gives:

| Asset | Native drop | Theft-day price | USD |
|---|---|---|---|
| hUSDC | 458,914.885741 | $1.00 | $458,914.89 |
| hUSDT | 72,420.384476 | $1.00 | $72,420.38 |
| hETH | 62.078006 | $2,416.2418 | $149,995.47 |
| hWBTC | 6.348243 | $77,658.2313 | $492,993.29 |
| hSOL | 536.159806 | $101.6829 | $54,518.27 |
| hBNB | 32.910105 | $684.4779 | $22,526.24 |
| **Total** | | | **$1,251,368.54** |

This project's own, independently-derived total (**≈$1,251,369**) sits
**0.11%** above DefiLlama's tracked **$1,249,946** for the chain-level
"Radix" row, a very close match given the two figures were arrived at
by completely different methods (this project: live on-chain supply
deltas times CoinGecko daily closes; DefiLlama: unknown internal
methodology, no source URL attached to the row). This is reported as a
confirmation, not a correction.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Radix, RDX Works, the Radix Foundation, Hyperlane, or
  any outlet cited above.
- The community-run RADIX Wiki incident page is where this project first
  learned of the incident's existence, rough timeline, and per-asset
  amounts. No figure in this README is sourced from that page directly;
  every number above is this project's own, independent re-derivation
  from Radix's Gateway API, Hyperlane's registry, `radixdlt`'s GitHub
  repos, and (for the cross-chain check) Ethereum's own USDC/USDT
  contracts. Where this project's own figures land close to the wiki's,
  that is presented as agreement, not as validation of the wiki as a
  source.
- Only the Ethereum leg of the cross-chain check was performed. hSOL
  bridges to Solana mainnet and hBNB to BNB Smart Chain; this project did
  not query either chain for the corresponding delivered amounts, so
  whether those two legs show a similar delivered/dispatched gap to the
  hUSDC leg above is not known here.
- The finding that the largest hUSDC message was not delivered is
  specific to that one message and one recipient address; this project
  did not check whether the other attack transactions used the same
  recipient address or a different one on the Ethereum/Solana/BSC side,
  so it cannot be generalized to the incident as a whole. The separate
  USDT cross-check above (99.3% delivered) shows the delivered fraction
  is not constant across assets or messages.
- 4 of the 6 assets are priced using CoinGecko's daily historical close
  for 2026-08-31, not the exact spot price at the moment of the sweep
  (16:02-16:57 UTC); this is the same source and method other entries in
  this repo use for off-Ethereum assets, but it is not a per-transaction
  spot rate.
- Radix mainnet was still halted as of this reconstruction (2026-09-11).
  Every figure above reflects the chain's state as of the halt
  (state_version 557840622); nothing here reflects any recovery,
  clawback, or compensation action that may occur after mainnet resumes.
- Neither the Radix Foundation nor RDX Works had published a full,
  numbered incident report or technical postmortem as of this
  reconstruction; the only official technical record found is the two
  GitHub pull requests and two releases cited above, which fix the bug
  but do not themselves state a loss figure, an incident timeline, or a
  root-cause narrative in prose.

## License

MIT

<!-- external source: https://github.com/radixdlt/radixdlt-scrypto/releases/tag/v1.4.0 -->
<!-- external source: https://radix.wiki/contents/history/hyperlane-asset-drain-2026 -->
