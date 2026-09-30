# Full Sail (Sui Vaults) Postmortem

Independent on-chain reconstruction of the Full Sail exploit (Sui,
2026-08-29). Full Sail is a concentrated-liquidity DEX on Sui whose
"Vaults" ("Ports" on-chain) take user deposits and manage them as
delegated CLMM liquidity positions, priced through Full Sail's own
`port_oracle` module reading Switchboard's oracle. Press (Yellow,
CryptoTimes, Cointelegraph, and others) reported that Switchboard's
oracle-signing infrastructure was compromised across its Move-based
deployments (Aptos, Sui, IOTA, Movement) on 2026-08-28/29, the same
broader compromise this repo already covers for Virtue Protocol on IOTA
(see [`../virtue-iota-switchboard-oracle/`](../virtue-iota-switchboard-oracle/)),
and that an attacker used a forged key to push a Full Sail price feed
to "roughly 100x below market", deposited, restored the price, and
withdrew for a profit across three vaults, for a total press reports as
"roughly $91,000". No press account this project found names an attacker
address, a transaction hash, or which three vaults were hit, and
DefiLlama's own hacks feed tracks this incident with **no dollar figure
at all**.

None of that is taken on faith here. Every package/object address below
is read live from Full Sail's own published npm SDK package
(`@fullsailfinance/sdk`, its own mainnet deployment config, not a block
explorer or a press screenshot). The attacker address and the three
affected vaults are not assumed from press; they are found by
paginating the vault package's own on-chain event log for the incident
window and clustering by sender. The "100x" manipulation is decoded
directly from the attacker's own transactions' Programmable Transaction
Block (PTB) commands and emitted events.

## At a glance

| | |
|---|---|
| Incident | A compromised Switchboard oracle signing key let an attacker submit a forged price, inside a Full Sail transaction that also legitimately updates the same feed and calls `port::deposit`, pushing SUI/ETH/IKA to almost exactly 100x below their real price, depositing while the fake price is active (fooling the vault's `calculate_aum` price-gated capacity check), then restoring the real price and withdrawing the resulting oversized position across three vaults (Ports) |
| Window | 2026-08-29, first attacker deposit 02:33:25 UTC, last withdraw 05:28:07 UTC (63 withdraw calls, 63 deposit calls, all by one address) |
| Press figures | ~$91,000 total, "three vaults", no address, tx hash, or per-vault breakdown published (Yellow, CryptoTimes, Cointelegraph). DefiLlama tracks this as "Full Sail" / Sui / "Oracle Manipulation" / "Oracle Misconfiguration" with **no dollar amount at all** |
| Verified independently | Attacker address, the 3 exact Port objects, the exact ~100x price ratio for each of SUI/ETH/IKA (all decoded from the attacker's own transactions), and a per-port net (withdrawn minus deposited) figure in native units, converted to USD at the chain's own restored (real) oracle price at the time: **$91,605.56 total** with the small IKA leg at the day's high (an upper bound; $91,149.73 at a matched real/fake pair price), 0.67% above the press estimate, computed independently of it |
| What's still open | Whether Full Sail's `vault_config::GlobalConfig.max_price_deviation_bps` guard (currently 200 bps / 2%) existed and was wired into this code path at exploit time is not established here; the attack succeeded regardless. See Caveats |

## The method

```bash
python3 reconstruct_exploit.py
```

Starting anchor: `@fullsailfinance/sdk`, Full Sail's own npm-published SDK
package, fetched live from `registry.npmjs.org` (its published tarball,
not a GitHub search or a docs screenshot). The bundle's minified
`dist/index.js` embeds three network configs (`mainnet-dev`,
`mainnet-prediction`, `mainnet-production`); the script locates the
`mainnet-production` block specifically (naively grabbing the first
match in the file would silently pull `mainnet-dev`'s addresses instead)
and extracts the vault package ID and five config object IDs from it.
Every one of those is confirmed live on Sui mainnet before being used.
The attacker address is not taken from press (no press account names
one): it is found by paginating the vault package's own `WithdrawEvent`
log for 2026-08-29 and picking the sender with the most withdraw calls
across the most distinct Ports. The three Port objects are the ones that
same sender actually touched that day, each independently read on-chain
for its underlying vault's `coin_a`/`coin_b` pair.

RPC endpoint used, public, no key: `https://sui-rpc.publicnode.com`.
Mysten Labs' own public Sui fullnode has deprecated JSON-RPC in favor of
GraphQL/gRPC (`sui_getObject` and friends now return
`"Method not found... migrate to gRPC or GraphQL"` there); this
third-party node still serves the same JSON-RPC surface this repo's other
Move-chain entries use, confirmed live via `sui_getChainIdentifier`
(`35834a8a`) before anything else runs. Also used: `registry.npmjs.org`
(Full Sail's own SDK), `api.llama.fi/hacks` (DefiLlama's own record).

## What it found

### The attacker and the three vaults, found from the chain, not press

Paginating the vault package's own `port::WithdrawEvent` log (150 events,
back through 2026-07-27) and filtering to 2026-08-29 shows one sender,
**`0x9104d073e1fdfd76a6b756f61c5684e4affa0b3d124d383afc64aabbd87934cc`**,
responsible for 63 of the day's withdraw calls across exactly 3 distinct
Port objects; the next most active sender that day made only 3 calls
across 3 Ports (routine user activity, not a drain). Reading each of the
3 Ports' own `vault.coin_a`/`vault.coin_b` fields live gives:

| Port object | Pair |
|---|---|
| `0x320ca75b93419d306bfc5db266952e52fb5c81b5ad05372039123a7822b1d0ea` | USDC / ETH |
| `0x8c8a0203bb4ecb49b7ea3b96822826408eb7a5d27a232f630dc04f08f6bc45c3` | IKA / SUI |
| `0x9787a95e76530f80ff8e8dd4a851a2a266b3eadcca4e6503c6d6fa18d8129ccc` | USDC / SUI |

This matches press's "three vaults" claim exactly, arrived at
independently.

### The mechanism, decoded from one of the attacker's own transactions

Transaction `EUcJWv6ZpMA1C3WmyrbrTbRQ8DRXj1TyqCrqJUVRoenJ`
(2026-08-29T04:57:27.497Z), a single atomic PTB, 16 commands:

1. `aggregator_submit_result_action::run` (Switchboard) followed by Full
   Sail's own `port_oracle::external_update_price_from_switchboard`:
   this submission sets SUI's tracked price to **74050000** raw
   (scale 1e10 => **$0.007405**).
2. A second pair of the same two calls updates USDC's price (a routine,
   undisturbed ~$1.00 read).
3. Reward/AUM bookkeeping (`update_pool_reward_v2` x3,
   `update_position_reward`), then `port::calculate_aum`, computed
   while SUI's tracked price is still the fake, 100x-low value.
4. `port::deposit`: the attacker deposits 2,786.123876 USDC
   (`IncreaseLiquidityEvent`: `amount_a: "2786123876"`,
   `before_aum: "70713262037"`), sized against the artificially
   depressed AUM figure.
5. A third `aggregator_submit_result_action::run` +
   `external_update_price_from_switchboard` pair, in the **same**
   transaction, restores SUI's price to **7405000000** raw
   (**$0.740500**), exactly **100.00x** the fake value submitted two
   commands earlier.

The deposit is sized and accepted while the price is fake; by the time
the transaction ends, the price is back to normal, so nothing about the
deposit itself looks abnormal to a later observer; only decoding the
transaction's own internal event sequence shows the price was ever wrong.
Separate, later transactions (2 seconds to several minutes afterward,
same sender) call `port::withdraw_v2` against the now-oversized position
at the real, restored price, realizing the profit.

### Independently confirming ~100x for all three assets, not just SUI

Paginating `port_oracle::UpdatePriceEvent` for the full day (500 events
across 10 pages) and isolating the 315 submitted by the attacker address
gives, per asset (raw price, scale 1e10):

| Asset | Real (high) | Fake (low) | Ratio |
|---|---|---|---|
| SUI | $0.740500 | $0.007405 | **100.00x** |
| ETH | $2,440.630000 | $24.406300 | **100.00x** |
| IKA | $0.002145 (day's high) | $0.000020 (day's low) | 106.86x (day-wide high/low, not one matched pair; every individual matched pair this project sampled, e.g. 20072969 vs 200729, is itself exactly 100.00x; the day-wide ratio differs slightly because the real IKA price also drifted normally across the ~3-hour attack) |
| USDC | $1.002195 | $0.997358 | 1.00x (never manipulated; only ever the routine, sub-1% price-feed noise expected of a real crank) |

USDC, the quote asset in two of the three vaults, was never touched,
consistent with the attack manipulating exactly the one price a given
Port needed skewed (SUI for two vaults, IKA for the third; ETH for the
USDC/ETH vault), never the whole feed set at once.

### Net realized profit per vault, in native units, then USD at the chain's own restored price

For each Port, summing the attacker's own `WithdrawEvent` amounts minus
their own `IncreaseLiquidityEvent` (deposit) amounts across the full
attack window gives a net native-unit change per coin; this nets out
each vault's repeated deposit/withdraw recycling automatically, leaving
only what the attacker actually extracted:

| Port (pair) | Net coin_a | Net coin_b | USD (at real, restored on-chain price) |
|---|---|---|---|
| USDC/ETH | -18.861463 USDC | +0.773454 ETH | **$1,868.85** |
| IKA/SUI | +3,310,237.387089 IKA | -100.462349 SUI | **$7,026.07** |
| USDC/SUI | -802.061839 USDC | +112,778.798369 SUI | **$82,710.64** |
| **Total** | | | **$91,605.56** (IKA leg at the day's high; $91,149.73 at a matched-pair IKA price) |

USD conversion uses the *real* (restored, post-correction) price read
directly from the chain's own `UpdatePriceEvent` log at the time of the
attack ($0.7405/SUI, $2,440.63/ETH, $0.002145/IKA, ~$1.00/USDC), not
an external price feed and not the manipulated figures. For IKA that is
the day's high real price, so the IKA leg ($7,026.07) is an upper bound:
at the real price of one matched real/fake pair the attacker submitted
(20072969 raw, $0.0020072969) it is $6,570.24, and the total $91,149.73.

### Cross-check: the ETH leg matches the attacker's own swap-out transaction to the last raw unit

Minutes after the last withdraw, transaction
`Da67fbc4CrTiAESEtKHxwqWNKsyFNSvF2PxKgwNKWZ6r` (2026-08-29T05:42:32.810Z)
routes through Full Sail's own multi-DEX swap router (momentum/cetus/
turbos/bluefin aggregation) with a balance change of exactly **-77345418
raw ETH**. This project's own independently-computed net ETH figure for
the USDC/ETH Port above is **77345418 raw**, an exact match, to the
last raw unit (8 decimals), found by re-deriving both numbers separately rather than
computing one from the other.

### Funds no longer sit at the exploit address

As of this reconstruction, `0x9104d073e1...87934cc` holds 0.00098083 SUI
and 0.040284 USDC (dust), and zero ETH or IKA; the realized profit has
been moved out via the swap above and further transfers, not left
sitting at the exploit address.

## Root cause: the same broader Switchboard compromise, a different chain and protocol

Press attributes this to the same Switchboard oracle-signing compromise
already covered in this repo for Virtue Protocol on IOTA (see
[`../virtue-iota-switchboard-oracle/`](../virtue-iota-switchboard-oracle/)),
disclosed by Switchboard as affecting its Aptos/Sui/IOTA/Movement
deployments together on 2026-08-28/29. This project did not independently
re-verify Switchboard's own signing-key compromise itself (that would
require access to Switchboard's own infrastructure/logs, not public chain
data); what is independently confirmed here is the on-chain consequence
on Sui specifically: an oracle submission accepted by Full Sail's own
`port_oracle` module carrying a price both Switchboard's `min_responses`
threshold and Full Sail's own logic should not have accepted from a
single legitimate reporting round, given the coincident, same-transaction
"real, then fake, then real again" pattern. Full Sail's own
`vault_config::GlobalConfig` carries a `max_price_deviation_bps` field
(currently 200, i.e. 2%) that, at face value, should reject a ~9,900%
single-step move; this project did not establish whether that field
existed, or was wired into the `port_oracle`/`calculate_aum` path used by
the exploit, at the time of the attack, nor whether Switchboard's own
per-aggregator `max_variance`/`min_responses` checks were bypassed via
the same compromised signer(s) implicated in the IOTA incident. Both are
open questions, not asserted either way; see Caveats.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Full Sail, Switchboard, Sui, or any outlet cited above.
- The IKA "100x" figure in the table above is a day-wide high/low across
  all of the attacker's IKA submissions, not one matched real/fake pair
  (unlike SUI and ETH, where the highest real value and lowest fake value
  happened to be a single matched pair). Every individual matched pair
  this project sampled by hand for IKA (e.g. 20072969 vs 200729) is
  itself exactly 100.00x; the day-wide figure (106.86x) differs slightly
  because IKA's real price also drifted normally, independent of the
  attack, across the roughly 3-hour window.
- The attacker's own current wallet holds dust and no ETH/IKA, meaning
  the funds were moved out; this project traced only the one swap-out
  transaction cited above (the ETH leg), not every hop of every asset's
  full downstream path (e.g. exactly which address ultimately received
  the SUI or IKA proceeds, or whether any of it left Sui entirely).
- Full Sail has said (per press paraphrase) it plans to publish "a
  detailed incident report"; as of this reconstruction, no such report,
  and no official statement with an attacker address, transaction hash,
  or per-vault breakdown, was found published anywhere. The independent
  reconstruction above does not depend on one existing.
- Switchboard's own root-cause statement for the broader 4-chain
  compromise was not published as of this reconstruction (see
  `../virtue-iota-switchboard-oracle/README.md` Caveats for the same
  point in more detail); this entry independently confirms the
  Sui/Full-Sail-specific mechanism from the attacker's own transactions,
  not from any Switchboard statement.
- Whether `vault_config::GlobalConfig.max_price_deviation_bps` (200 bps,
  read live and current as of this reconstruction) existed, at what
  value, and was actually enforced on the `port_oracle`/`calculate_aum`
  path at exploit time is not established here; only that the attack
  succeeded regardless of whatever guard, if any, was live that day.
- DefiLlama's own hacks feed tracks this incident with no dollar amount
  at all (`amount: null`), so the $91,605.56 figure above cannot be
  cross-checked against a DefiLlama number, only against the press
  estimate (~$91,000, itself unsourced to any on-chain data in the
  articles this project found).

## License

MIT

<!-- external source: https://yellow.com/news/full-sail-91k-sui-hack -->
<!-- external source: https://www.cryptotimes.io/2026/08/30/full-sail-confirms-sui-vault-losses-as-switchboard-halts-4-chains/ -->
