# Weft Finance (Weft V2) Postmortem

Independent on-chain reconstruction of the Weft Finance (Weft V2) incident
(Radix, 2026-08-30). Weft is a lending/borrowing protocol on Radix; "Weft
V2" is its current live deployment, with CDP-based (Wefty NFT) positions
that let a user post one asset as collateral and borrow another against
it, priced through Weft's own on-chain price-feed components.

DefiLlama's hacks feed lists this incident: "Weft V2", Radix, 2026-08-30,
$47,200, "Oracle Manipulation" / "Spot Price Manipulation" -- with an
**empty source field**. No article, no tx hash, no attacker address, no
protocol statement. Direct web search (several query variants, including
searching specifically for a Weft/Radix rekt.news entry) found no press
coverage of this incident anywhere. The only two Weft-related security
stories that exist publicly are unrelated: a 2025 Hacken ethical-hacking
case study (a private, disclosed-and-fixed audit finding on a test copy of
the ledger, not a live exploit) and the separate, well-documented Aug 2026
Switchboard oracle-signing-key compromise that hit Sui/Aptos/IOTA/Movement
(already covered in this repo for Virtue Protocol and Full Sail) -- which
does not include Radix at all.

This entry is therefore built entirely from the chain, the same way
WealthManagementV2 and Oraichain were in this project: an official,
primary-source starting anchor (Weft's own PR into DefiLlama's own
TVL-adapter repository, not a block explorer search), then every address,
amount, and price below decoded live from Radix's own Gateway API.

## At a glance

| | |
|---|---|
| Incident | A single atomic transaction swaps a trivial 70.6 XRD into 539,703.17 units of an obscure meme token ("Hug", HUG) via one thin CaviarNine pool, posts the HUG as CDP collateral, borrows 47,280,000 LSULP (a real, correctly-priced liquid-staking token) and 13,100,500 XRD against it, then removes the HUG collateral again -- all in the same transaction |
| Window | 2026-08-30T18:02:58Z (the attack), 2026-08-30T23:45:57Z (the one partial liquidation that followed) |
| DefiLlama figure | $47,200, "Oracle Manipulation" / "Spot Price Manipulation", empty source field. No press, rekt.news entry, or protocol statement found anywhere |
| Verified independently | The two live Weft V2 component addresses (from Weft's own DefiLlama adapter PR), the attack transaction (found by ranking the Gateway's own transaction stream, not assumed), both resources' identities (HUG vs. LSULP, via their own on-chain metadata), LSULP's own un-manipulated theft-day price (via Weft's own price-feed component), the CDP's own current bad-debt state (via its own non-fungible data, 6 days later), and the one partial liquidation that followed -- net independently reconstructed loss: **$61,592.84**, about 30.5% above DefiLlama's figure |

## The method

```bash
python3 reconstruct_exploit.py
```

Starting anchor: `projects/weft-finance-v2/index.js` in
`github.com/DefiLlama/DefiLlama-Adapters`, Weft's own pull request into
DefiLlama's TVL-adapter repository (not a block explorer guess), which
names the two live "Weft V2" components directly:

```js
const lendingPool = 'component_rdx1czmr02yl4da709ceftnm9dnmag7rthu0tu78wmtsn5us9j02d9d0xn'
const lendingMarket = 'component_rdx1cpy6putj5p7937clqgcgutza7k53zpha039n9u5hkk0ahh4stdmq4w'
```

From there the script: (1) confirms live, via the Gateway's own
`/status/gateway-status`, that Radix mainnet has produced no new state
since state_version 557840622 -- a separate, unrelated halt caused by the
Hyperlane-vault-access incident this project already covers in
[`../radix-hyperlane-vault-access-drain/`](../radix-hyperlane-vault-access-drain/),
not by this incident -- and pins every later query to that state_version;
(2) finds the attack transaction itself by filtering the Gateway's own
`/stream/transactions` for every committed transaction touching
`lendingMarket` across 2026-08-29 through 08-31 (73 transactions) and
ranking by total absolute fungible balance-change volume, rather than
assuming a tx hash from anywhere; (3) decodes that transaction's own
receipt events directly; (4) confirms both resources' real identities via
`/state/entity/details`; (5) reads Weft's own on-chain price-feed
component (the same address listed as LSULP's `priceFeed` in the sibling
Weft V1 adapter file) for LSULP's theft-day price; (6) reads the CDP's own
current non-fungible data to confirm the aftermath; (7) finds and nets out
the one partial liquidation that followed; (8) prices the net loss at
CoinGecko's theft-day XRD rate and compares to DefiLlama's tracked figure.

RPC/REST endpoints used, all public, no key:
`https://mainnet.radixdlt.com` (Radix Gateway API, official),
`https://raw.githubusercontent.com/DefiLlama/DefiLlama-Adapters` (Weft's
own PR), `https://api.coingecko.com` (theft-day XRD price),
`https://api.llama.fi/hacks` (comparison only).

## What it found

### The attack transaction, found by ranking the chain, not assumed

Filtering the Gateway's own transaction stream to every transaction that
touched `lendingMarket` between 2026-08-29 and 2026-08-31 (73 committed
transactions) and ranking by total absolute balance-change volume surfaces
one transaction an order of magnitude larger than anything else in the
window:

```
    121,840,406.34  2026-08-30T18:02:58.28Z  txid_rdx12lsyuggs587xt7m9uxjedtkdtz0lcnzh85g2w4x6wwdq3cuyhccs8ls3kc
      7,742,124.08  2026-08-31T05:34:29.576Z  txid_rdx1zu37yejre74k6mea7pp4ehex3dcqzhtn2jt52g60w5dstc0g3lzqxldhuz
      2,437,632.22  2026-08-31T00:17:57.187Z  txid_rdx1yrrxsya3ezlm0300w9f4le8x76fusu6j4j3xeaj578wq52t0zw9qgadde8
```

`2026-08-30` matches DefiLlama's own dated entry exactly, arrived at
independently of that date rather than searched around it.

### The mechanism, decoded from the transaction's own receipt events

One atomic manifest, in order:

1. **Swap**: 70.6 XRD in, 539,703.171057886068001932 units of an unknown
   resource out, through a single CaviarNine pool -- a rate of
   0.0001308126 XRD per unit. A swap this lopsided against a thin pool
   necessarily leaves that pool's own spot price badly skewed for whatever
   reads it next.
2. **Mint**: a fresh Weft CDP, Wefty V2 NFT `#1138`.
3. **Deposit**: the 539,703.17 units just acquired are posted as `#1138`'s
   collateral.
4. **Borrow**: two `BorrowEvent`s against `#1138`, in the same
   transaction, for 47,280,000 units of one resource and 13,100,500 XRD,
   both withdrawn straight to the attacker's own account.
5. **`FlashRemoveCollateralEvent`**: the posted collateral is removed
   again, before the transaction ends.

### The two resources, identified live, not assumed

| Resource | Role | Name / symbol (on-chain metadata) | Total supply |
|---|---|---|---|
| `resource_rdx1t5kmyj54jt85malva7fxdrnpvgfgs623yt7ywdaval25vrdlmnwe97` | Collateral posted (from the swap) | "Hug" / HUG, description "Hug The World" | 100,000,000,000 |
| `resource_rdx1thksg5ng70g9mmy9ne7wz0sc7auzrrwy7fmgcxzel2gvp8pj0xxfmf` | Asset borrowed | "LSU Pool LP" / LSULP, CaviarNine's own liquid-staking pool token | 217,144,821.60 |

HUG is an obscure, 100-billion-supply meme token with no obvious real
value; LSULP is a real, actively used Radix liquid-staking derivative.
The attacker paid 70.6 XRD (worth about $0.06 at theft-day prices) for
collateral that then unlocked a borrow of real assets worth tens of
thousands of dollars.

### LSULP's own price was never manipulated -- only the collateral was

Reading Weft's own on-chain price-feed component
(`component_rdx1cptmek76m0xuw3etvdqttvgtcu99lvz84jh9q8zleaj3vc5elk4epc`, a
`CaviarLsuPriceFeedProxy` -- the same address listed as LSULP's own
`priceFeed` in the sibling Weft V1 DefiLlama adapter file) at the ledger
state at/just before the attack gives **1 LSULP = 1.224027421309258
XRD**, a normal liquid-staking premium consistent with the days around it.
The asset borrowed was priced correctly the whole time; the exploit works
entirely on the collateral side, where Weft's own accounting apparently
accepted the just-manipulated HUG valuation to size the borrow.

### The aftermath, read directly from the CDP's own current on-chain state

As of the last update before Radix mainnet halted (state_version
557445107, 2026-08-30T23:46:01.7Z, about 5h43m after the attack), CDP
`#1138` is still open (`is_burned: false`) and its own stored data shows:

| | Amount |
|---|---|
| LSULP still owed (loan units) | 47,202,009.98 |
| XRD still owed (loan units) | 11,877,595.35 |
| HUG collateral remaining | 0.000000000000016501 |

Functionally zero collateral against real, still-outstanding debt in both
borrowed assets -- read straight from the protocol's own CDP data, not
inferred from the attack transaction alone.

### One partial liquidation followed, but recovered almost nothing

A separate transaction 5h43m later
(`txid_rdx1kt5f3vfq47thgnh49ykzffqd7243w6z6dw23dfwygqrphj7yafjquxp7hz`,
2026-08-30T23:45:57Z) liquidates part of `#1138`: a
`CDPRepayForLiquidationEvent` repays only **51.127952505660406764 LSULP**
(0.0001% of the 47,280,000 owed) in exchange for a
`CDPRemoveCollateralForLiquidation` seizing essentially all the remaining
HUG (539,703.17 units) -- a liquidation that closes out the collateral
side formally but recovers almost none of the real debt, consistent with
the seized HUG itself being worth only a few dollars.

### Net loss, priced at theft-day rates

| | Amount |
|---|---|
| LSULP borrowed | 47,280,000.000000 |
| LSULP repaid at liquidation | -51.127953 |
| LSULP net still owed | 47,279,948.872047 |
| x LSULP/XRD rate (Weft's own oracle) | 1.224027421309258 |
| = XRD-equivalent (LSULP leg) | 57,871,953.897486 |
| + XRD borrowed (fully unrepaid) | 13,100,500.000000 |
| **Total XRD-equivalent net loss** | **70,972,453.897486** |
| x CoinGecko XRD/USD, 2026-08-30 | $0.0008678415160464539 |
| **Total independently reconstructed net loss** | **$61,592.84** |

DefiLlama tracks this incident at $47,200 with an empty source field.
This project's independently reconstructed figure is about **30.5%
higher** -- a real, quantified gap, not reconciled here for lack of any
DefiLlama methodology to check against (the source field is empty, so
there is nothing published explaining how DefiLlama's own $47,200 was
derived).

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Weft Finance, CaviarNine, Radix, or DefiLlama.
- No press, rekt.news entry, security-firm writeup, or official Weft
  Finance statement about this incident was found anywhere. If one
  surfaces later with its own figure or attacker attribution, it should
  be checked against the independent reconstruction above rather than
  simply adopted.
- The theft-day LSULP/XRD rate used above (1.224027421309258) is read
  from Weft's own price-feed component at the ledger state resolved by
  the Gateway for the attack transaction's own timestamp; this component
  is itself fed by a CaviarNine-side process this project did not
  independently audit, only cross-checked for plausibility against the
  days around it.
- Radix mainnet has been offline since 2026-08-31 (a separate, unrelated
  incident -- see `../radix-hyperlane-vault-access-drain/`), so every
  query above is pinned to the last real state before that halt
  (state_version 557840622); whether any further liquidation or recovery
  action against CDP `#1138` was queued but not yet executed cannot be
  observed until mainnet resumes.
- The attacker's own account made 8 further transactions in the 45
  minutes after the attack (staking a large XRD amount to a validator,
  and routing part of the borrowed LSULP through several DEX pools); this
  project did not fully trace every downstream hop of where the borrowed
  funds ultimately ended up, only confirmed the amounts that left Weft's
  lending pool itself.
- Whether HUG was a Weft-team-approved isolated collateral market or was
  listed some other way (e.g. a permissionless listing path) was not
  established here -- only that it was a live, borrowable-against
  collateral option at the time of the attack.

## License

MIT

<!-- external source: https://api.llama.fi/hacks -->
