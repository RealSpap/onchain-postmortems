# Virtue Protocol (VUSD CDP) Postmortem

Independent on-chain reconstruction of the Virtue Protocol exploit (IOTA,
2026-08-28). Virtue is a decentralized, over-collateralized stablecoin
(VUSD) protocol built on IOTA's Move-based ledger ("IOTA Rebased"). Press
(CryptoSlate, CryptoBriefing, PrimeXBT and others) reported that
Switchboard, the price oracle Virtue depends on, was compromised across
its Move-based deployments (Aptos, Sui, IOTA, Movement) on 2026-08-28/29,
and that an attacker used a fake price to mint VUSD against next to no
real collateral, then crashed the price to trigger a liquidation cascade
against real borrowers. None of that is taken on faith here: every
package address below is read live from Virtue's own GitHub SDK
repository, the exploit transaction is found by scanning the CDP
package's own on-chain event log (not copied from any article), and its
own PTB commands and events independently confirm the mechanism byte for
byte, down to the exact 14 compromised oracle signers acting inside the
same atomic transaction as the mint.

## At a glance

| | |
|---|---|
| Incident | All 14 Switchboard oracle signing keys for Virtue's IOTA price queue were compromised; in one atomic transaction the attacker self-submitted a fake $10,000,000 IOTA price through all 14 of them, opened a CDP position with 1 real IOTA of collateral, minted 4,942,703.659474 VUSD against it, and deposited 1,000,000 VUSD of that into Virtue's own stability pool. The price was then crashed toward zero, triggering a cascade of 47 liquidations against 45 real, honestly-collateralized users |
| Window | 2026-08-28, exploit mint at 21:53:10 UTC; liquidation cascade 21:52:12-22:45:02 UTC (the first liquidation, a small wash/test cycle, is 58 seconds BEFORE the mint; see What it found) |
| Press figures | Virtue's own account (per press paraphrase of its X posts, X itself not independently fetchable by this project): 47 liquidations / 45 users, 455,103 VUSD debt cleared against 23,215,117 IOTA-equivalent seized. DefiLlama tracks $894,500, "Oracle Manipulation" / "Oracle Misconfiguration" |
| Verified independently | The exploit transaction, its 14 compromised-oracle submissions, the mint, and the stability-pool deposit, all decoded directly from the transaction's own commands and events; the 47/45 liquidation count matches Virtue's account exactly once the attacker's own 1 wash-test liquidation is identified and excluded from the raw 48; the VUSD debt-cleared figure independently reconstructs to $455,102.94, within 7 cents of Virtue's own number; a second, independent figure -- the real-user collateral's value at theft-day prices, ≈$848,457 -- sits much closer to DefiLlama's $894,500 than to the face-value debt figure |
| What's still open | The stIOTA/vIOTA-to-IOTA exchange-rate conversion behind the ≈$848,457 figure is this project's own approximation of Virtue's internal accounting, not a byte-for-byte replication of it (6.8% below Virtue's own stated IOTA-equivalent). The attacker's own 4.94M-VUSD position is never seen being liquidated in this project's own capture of the event log. See Caveats |

## The method

```bash
python3 reconstruct_exploit.py
```

Starting anchor: `Virtue-CDP/virtue-sdk`, Virtue's own GitHub SDK
repository, `src/constants/object.ts`, fetched live from
`raw.githubusercontent.com`. This file is the SDK's own mainnet
deployment config: the CDP, Oracle, Switchboard and VUSD package IDs, and
the Switchboard aggregator object ID Virtue itself uses for pricing IOTA.
Every one of those addresses is confirmed live on IOTA mainnet before
being used, the exploit transaction is found by paginating the CDP
package's own event log (not by searching a block explorer or copying a
hash from press), and every liquidation in the cascade is read the same
way.

RPC endpoints used, all public, no key: `api.mainnet.iota.cafe` (IOTA
mainnet full node), `indexer.mainnet.iota.cafe` (IOTA mainnet indexer,
needed for `iotax_queryEvents`), `raw.githubusercontent.com` (Virtue's own
SDK repo), `api.github.com` (a supporting commit lookup, see Caveats),
`api.coingecko.com` (theft-day IOTA/USD pricing), `api.llama.fi/hacks`
(DefiLlama's own tracked record).

## What it found

### Contract identity, from Virtue's own SDK repo, not a block explorer

`Virtue-CDP/virtue-sdk`'s own `src/constants/object.ts` (fetched live)
names the mainnet package IDs directly, including:

- **CDP package**: `0xb0ca01917f84a07774397395467fc2d56de377fab9d603cb79b82f062d1f6e9a`
- **Oracle package**: `0x7eebbee92f64ba2912bdbfba1864a362c463879fc5b3eacc735c1dcb255cc2cf`
- **Switchboard package**: `0x8650249db8ffcffe8eb08b0696a8cb71e325f2afb9abc646f45344077b073ba1`
- **Switchboard IOTA aggregator**: `0x7c16ffdac553a4816db57e5e2cfbba8245337f2983b4ffb4dd944493a530c556`

All 3 packages are confirmed live via `iota_getObject` on IOTA mainnet
(chain identifier `6364aad5`), and VUSD/IOTA coin decimals (6 and 9) are
read live via `iotax_getCoinMetadata`, not assumed. This is the same file
the SDK's own upgrade history shows being edited less than 24 hours before
the exploit (see the root-cause section below), so the addresses used
here are the exact ones live on-chain at the time of the incident, not a
later, patched deployment.

### The exploit mint: one atomic transaction, 14 compromised oracle signers, a fake $10,000,000 price

Paginating the CDP package's own event log (`iotax_queryEvents`,
descending) and scanning every `manage`-memo `PositionUpdated` event for
the single largest `borrow` value surfaces exactly one transaction:

**`CaAD9SRJjuvEbNiHQcgT176kg4F8jKUTM1EneeYsd3Gd`**, 2026-08-28T21:53:10.246Z
(live block timestamp). Sender/debtor
`0x381d5b5fa3ae0ba5b3d0ce3421a43d48397cf6eb2a87e624d56dec5e68e7c7e9`
deposits exactly 1.000000000 IOTA and immediately borrows
**4,942,703.659474 VUSD**, matching press's "about 4.94 million VUSD
against 1 IOTA" account.

Decoding this single transaction's own Programmable Transaction Block (48
commands total) shows the entire attack was atomic:

1. **14 separate calls** to Switchboard's own
   `aggregator_submit_result_action::run` (package
   `0x8650249d...`, matching the SDK's own config above), each preceded by
   a `SplitCoins` (paying that oracle's own submission fee). Each of the
   14 calls carries a **distinct `oracle_id`** -- 14 distinct signers in
   total -- and each emits an `AggregatorUpdated` event with the
   **identical** raw value `10000000000000000000000000`. Fourteen
   distinct legitimate oracles do not independently agree on the same
   manipulated price by chance; this is 14 compromised keys submitting
   from a single controlling party inside one transaction, matching
   press's "compromised the signing keys used by all 14 oracles on
   Switchboard's IOTA mainnet queue" account exactly, and going further:
   this project confirms it from the raw submission events themselves,
   not from Virtue's or Switchboard's own paraphrase of what happened.
2. Virtue's own Oracle package (`aggregater::aggregate`) resolves that
   poisoned submission to a `PriceAggregated<IOTA>` event with
   `result: "10000000000000000"`. At this Oracle's own 9-decimal price
   convention (independently confirmed below against a normal price for
   the same coin type), that is **exactly $10,000,000.00 per IOTA** --
   not just "a very large number", but the specific figure press
   reports, decoded from the raw event data.
3. The CDP package (`request::debtor_request`, `vault::update_position`)
   opens the position and mints VUSD against it, using that poisoned
   price. Its own `vusd::Mint` event records `amount: 4942703659474`
   (4,942,703.659474 VUSD) with `total_supply` immediately after the mint
   at **5,592,035.484667 VUSD** -- meaning this single fraudulent mint was
   about **88.4%** of the entire VUSD supply the instant after it
   happened, a detail no press account this project found states.
4. In the **same transaction**, a `stability_pool::Deposit` event shows
   the attacker depositing exactly **1,000,000.000000 VUSD** of that
   freshly-minted, essentially unbacked stablecoin into Virtue's own
   stability pool -- the pool whose depositors absorb the collateral from
   liquidations that follow, in exchange for having their own VUSD
   burned. This directly connects the mint to the liquidation cascade
   below: positioning fake VUSD in the stability pool before crashing the
   price is how a share of real, honestly-collateralized users' seized
   collateral converts into value for the attacker.

**Cross-checking the price-decimal convention** (so "$10,000,000.00" is
not an assumed reading): the most recent `PriceAggregated<IOTA>` event
on-chain as of this reconstruction, timestamped 2026-08-28T23:13:51Z
(after Virtue's own freeze, still Switchboard-sourced), carries
`result: "39260630"`. At the same 9-decimal convention that is
$0.039261/IOTA, matching CoinGecko's independently-sourced theft-window
spot price (mean $0.039188 across 3 samples, 21:00-23:00 UTC 2026-08-28)
to within 0.2%. The same decimal convention applied to the exploit
transaction's own `result: "10000000000000000"` gives exactly
$10,000,000.00.

### Root cause, one layer deeper than press: a real-time-verifiable dependency Virtue's own team had already flagged

Virtue's own GitHub SDK repository shows commit `b1ba8f80b3`, merged
**2026-08-27T03:13:38Z -- less than 24 hours before the exploit** --
titled "remove Pyth and iBTC; Switchboard is now the only price source".
Its own commit message states verbatim: Pyth's Hermes endpoint had been
"answering `401 unauthorized`... to us and to anyone... persistently,"
so the team removed Pyth's client-side integration entirely rather than
leave it failing silently, explicitly noting the tradeoff in writing:
"That leaves IOTA priced by Switchboard... there is no second opinion
left, so crossbar going down means no price at all."

Separately, this project independently confirms (via
`iota_tryGetPastObject` against the price-aggregator config object at the
exact version the exploit transaction itself used, `0x052c40b4...`
version `759082917`) that the **on-chain** config still listed BOTH
`PythRule` and `SwitchboardRule` as valid sources, `weight_threshold: 1`
-- meaning a single source alone was always sufficient by the contract's
own design. Removing Pyth client-side did not change that on-chain
threshold; it meant that, in practice, only Switchboard was ever going to
be the source any normal caller actually fed in, since a broken upstream
Pyth feed left nothing else worth calling. The team's own commit message
already named the risk ("no second opinion left") one day before it was
realized through a different failure mode than the one they had in mind
(a compromised signer, not a downed feed).

### The liquidation cascade: 47 events, 45 users, matching Virtue's own account exactly

Of the 48 `liquidate`-memo events found on the CDP package across the
incident window (2026-08-28T21:52:12Z-22:45:02Z), **exactly 1** belongs
to the same debtor address as the exploit-mint transaction above: a small
wash/test cycle (2 IOTA deposited, 0.066941 VUSD borrowed, then
immediately closed) 58 seconds **before** the main exploit, at the real,
pre-manipulation price. Excluding it leaves **exactly 47 liquidation
events across 45 distinct debtor addresses** -- matching Virtue's own
press-relayed account ("47 liquidation events had affected 45 users")
exactly on both counts, independently arrived at from the raw event log,
not copied from that account.

Summing the `repay` field across those 47 real-user events gives
**455,102.938610 VUSD** of debt cleared, within **7 cents** of Virtue's
own stated 455,103 VUSD (summing all 48, including the attacker's own
dust test, gives 455,103.005552 VUSD, closer still). This face-value
figure is independently, exactly reconstructable from the CDP package's
own raw event log.

Collateral seized across those same 47 events (`withdraw` field, by coin
type):

| Coin | Raw units withdrawn | Native units |
|---|---|---|
| IOTA | 3,611,650,830,680,175 | 3,611,650.830680 |
| stIOTA (liquid-staked IOTA) | 16,911,443,633,889,400 | 16,911,443.633889 |
| vIOTA | 54,017,069,548,773 | 54,017.069549 |

Converting stIOTA and vIOTA to IOTA-equivalent using each token's OWN
exchange rate (`total_staked / total_supply`, read via
`iota_tryGetPastObject` at the exact object version each liquidation
transaction itself used, not today's rate) gives:

- stIOTA rate at exploit time: 1.063108479 IOTA/stIOTA -> 17,978,699.12 IOTA-equivalent
- vIOTA rate at exploit time: 0.999136720 IOTA/vIOTA -> 53,970.44 IOTA-equivalent
- native IOTA: 3,611,650.83 (1:1)

**Total: 21,644,320.39 IOTA-equivalent**, about 6.8% below Virtue's own
stated 23,215,117 IOTA-equivalent. At the independently-sourced
theft-window mean spot price ($0.039188/IOTA), that is **≈$848,457** --
much closer to DefiLlama's tracked **$894,500** ("Oracle Manipulation" /
"Oracle Misconfiguration") than to the $455,103 face-value debt figure
Virtue's own account (and, by extension, most press paraphrasing it)
emphasizes. The gap is not a case of either side being "wrong": debt
cleared and collateral seized are two different numbers by construction
whenever a liquidation happens at a manipulated, crashed price -- exactly
what happened here. DefiLlama's classification and figure track the real
economic value taken from the 45 real users; Virtue's own $455,103
statement tracks the smaller, nominal VUSD amount that was technically
"repaid."

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Virtue Protocol, Switchboard, IOTA, or any outlet cited
  above.
- The stIOTA/vIOTA exchange-rate conversion behind the ≈$848,457 figure is
  this project's own reconstruction (raw `total_staked`/`total_supply`
  read at the exact historical object version each liquidation
  transaction used), not a byte-for-byte replication of however Virtue's
  own systems computed the 23,215,117 IOTA-equivalent figure it reported;
  the two land within 6.8% of each other, not exactly.
- The attacker's own original exploit position (1 IOTA collateral against
  the 4,942,703.66 VUSD mint) is never seen being liquidated anywhere in
  this project's own capture of the CDP package's event log, which runs
  through the package's own last recorded event
  (2026-08-29T03:20:11Z, evidently when Virtue froze the protocol). The
  address instead shows a series of tiny (0.001 IOTA) top-up `manage`
  calls from 22:06 through 22:58 UTC, then nothing. What ultimately
  happened to this specific position (a later, unrecorded on-chain
  liquidation after a freeze, an off-chain/social resolution, or
  something else) is not independently confirmed here.
- Virtue's own fuller statement of the incident, including its
  compensation plan, was published to X, which this project could not
  fetch directly (X returns errors to automated fetches); its 455,103
  VUSD / 23,215,117 IOTA-equivalent figures and narrative are reported
  here via press paraphrase (CryptoSlate, CryptoBriefing, PrimeXBT,
  kryptorevolution.de), not read from the primary post itself. The
  independent, transaction-level reconstruction above does not depend on
  that paraphrase being accurate for its own headline figures (the
  exploit transaction, the mint, the 47/45 liquidation count, and the
  $455,102.94 debt-cleared figure); it is offered as a cross-check, and
  lands within 7 cents of it.
- The GitHub commit lookup behind the root-cause section (commit
  `b1ba8f80b3`) and the historical price-aggregator config read (both
  described in the README above) are live checks made during this
  reconstruction; neither is saved to a `resultats_*.txt` file in this
  repo, since `reconstruct_exploit.py` focuses on the chain-side
  reconstruction. Both are independently re-checkable: the commit via
  `api.github.com/repos/Virtue-CDP/virtue-sdk/commits/b1ba8f80b3`, and the
  config via `iota_tryGetPastObject` against
  `0x052c40b4e8f16df5238457f3a7b3b0eeaa49c6bc8acc22f6a7790ab32495b2c6`
  at version `759082917`.
- Switchboard's own root-cause statement for the broader, 4-chain
  (Aptos/Sui/IOTA/Movement) compromise was not published as of this
  reconstruction (press: "Switchboard has not confirmed a link... no root
  cause or technical postmortem has been published"); this entry
  independently confirms the IOTA-specific mechanism from Virtue's own
  exploited transaction, not from any Switchboard statement.

## License

MIT

<!-- external source: https://cryptoslate.com/cross-chain-oracle-compromise-triggers-liquidations-and-frozen-vaults-across-multiple-defi-networks/ -->
