# Drift Protocol Postmortem

Independent reconstruction of the largest DeFi hack of 2026: on 2026-04-01,
attackers social-engineered two Squads multisig signers on Drift Protocol
(Solana's largest perpetuals DEX at the time, ~$550M TVL) into pre-signing
durable-nonce transactions weeks earlier, then used those still-valid
signatures to hijack the protocol's own admin key, list a fabricated
collateral token, and disable withdrawal circuit breakers on real markets
before draining roughly $295.7M in user funds. Press coverage (Elliptic,
TRM Labs, Chainalysis, QuillAudits, Halborn, Merkle Science) describes the
social-engineering campaign and attributes the attack to DPRK-linked
actors, but none of those write-ups decode the actual on-chain admin-change
instruction, name a verifiable fake-token mint address, or show the
withdraw-guard-threshold changes. This reconstruction starts from Drift's
own GitHub program-ID record and, separately, from two transaction
signatures a QuillAudits blog post names (treated only as a lead, the same
way this repo's Aquifer entry treats a press-named address), and
independently re-derives the mechanism, the fake token's identity, and a
sample of the real-asset outflow straight from Solana mainnet.

## At a glance

| | |
|---|---|
| Incident | Two of five Squads multisig signers were social-engineered into pre-signing durable-nonce transactions; weeks later the attackers broadcast them to overwrite Drift's on-chain program admin, list a fake "CarbonVote" (CVT) token as collateral, and raise the withdraw guard on real markets before draining assets |
| Window | 2026-04-01 16:05:18 UTC (durable-nonce pre-sign broadcast) to 2026-04-01 16:05:19 UTC (admin overwritten) to 16:05:39-18:05:01 UTC (fake market setup + withdraw-guard changes across dozens of markets); real-asset outflow to a consolidation address runs from at least 16:52 to 17:14 UTC in the sampled transactions (the full outflow window was not exhaustively bounded, see Caveats) |
| Press/DefiLlama figure | DefiLlama: "Drift Trade", $295,000,000, Solana, classification "Access Control", technique "Proxy Upgrade Hijack". Drift's own official "Incident Recovery Update - April 16, 2026" (drift.trade) states $295,706,374.93 across 19 stolen assets, led by JLP ($159.3M) and USDC ($71.4M) |
| Verified independently | The admin-change instruction, its exact timestamp, and the durable-nonce pre-sign step, read directly from Drift's own program logs; the fake collateral mint independently derived (not press-supplied) and confirmed via live Metaplex metadata to be named "CarbonVote Token" / "CVT" with a ~750M supply; at least 23 separate withdraw-guard-threshold changes across roughly 2 hours; a representative sample of the real-asset outflow (USDT and USDS legs) matching Drift's own official per-asset figures to within 0.002% |

## The method

```bash
pip install requests
python3 reconstruct_exploit.py
```

No hardcoded press figures: every address and number below is read live,
either from Drift's own GitHub deployment record
(`raw.githubusercontent.com/drift-labs/protocol-v2`, the repo's `master`
branch still resolves under the pre-rebrand org name even though the
GitHub org itself was later renamed and archived to
`velocity-exchange/protocol-v2`, confirmed via a live GitHub API call, see
Caveats), from Solana's public RPC (`api.mainnet-beta.solana.com`), or from
Drift's own official recovery-update page.

1. **The program ID comes from Drift's own GitHub, not a block explorer
   search.** `Anchor.toml` on `drift-labs/protocol-v2` (fetched live)
   states `drift = "dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH"`.
2. **Two transaction signatures a QuillAudits write-up names are treated
   only as a starting lead**, the same way this repo's Aquifer entry
   treats a press-named address: everything claimed about them below is
   re-derived from their own on-chain data, not copied from that blog.
   Both are fetched live and decoded from their raw program logs.
3. **The fake collateral mint is not taken from any press source.** It is
   derived purely from the admin-hijack follow-up transaction's own
   `initializeAccount3` inner instructions (the token accounts Drift's own
   `InitializeSpotMarket` instruction just created), then independently
   checked two ways: its live mint-account supply/decimals, and its own
   Metaplex metadata account (found via a `getProgramAccounts` `memcmp`
   filter on the metadata program, not a hardcoded PDA).
4. **The real-asset identification is independently verified the same
   way.** The token the attacker wallet first received is identified by
   reading its own Metaplex metadata live, not assumed from its mint
   address looking familiar.
5. **The dollar total is Drift's own stated figure**, fetched live from
   its own recovery-update page, cross-checked against (not reconciled to
   match) a representative sample of the on-chain outflow this
   reconstruction independently found.

## What it found

### The hijack: a durable nonce, a multisig, and one log line

Solana's "durable nonce" feature lets a transaction be signed once and
stay valid indefinitely until someone actually broadcasts it (normal
transactions expire within ~1-2 minutes of signing). Per press, attackers
spent months building trust with two of Drift's five Squads multisig
signers, then had them sign transactions against a durable nonce weeks
before the attack, banking valid signatures for later use.

At **2026-04-01 16:05:18 UTC** (slot 410344005), a transaction
(`2HvMSgDEfKhNryYZKhjowrBY55rUx5MWtcWkG9hqxZCFBaTiahPwfynP1dxBSRk9s5UTVc8LFeS4Btvkm9pc2C4H`)
advances a durable-nonce account
(`7s7s6saC5LHZoLyBXLM3pCjpWaA7meyQdP8NiH9ktAeC`) and, in the same
transaction, calls Squads V4's own `VaultTransactionCreate`,
`ProposalCreate`, and `ProposalApprove` instructions, exactly the
"broadcast a pre-signed durable-nonce payload to bank one approval"
pattern press describes.

One second later, at **16:05:19 UTC** (slot 410344009), a second
transaction
(`4BKBmAJn6TdsENij7CsVbyMVLJU1tX27nfrMM1zgKv1bs2KJy6Am2NqdA3nJm4g9C6eC64UAf5sNs974ygB9RsN1`)
banks the second approval (`ProposalApprove`) and immediately executes
(`VaultTransactionExecute`), which in turn calls Drift's own program
(`dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH`) directly. Drift's own
program log for that inner call is unambiguous:

```
Program log: Instruction: UpdateAdmin
Program log: admin: AiLGdNitMjv8n5HMS7HAdV2kaeJZZFd4jdfn5xp1PKrW -> H7PiGqqUaanBovwKgEtreJbKmQe6dbq6VTrw6guy7ZgL
```

That line is emitted by Drift's own `UpdateAdmin` instruction handler,
reading its own prior admin value before overwriting it. It is not
something an attacker-controlled off-chain script could spoof; it is the
protocol's own code recording its own state transition. This is the
entire privilege-escalation step of the attack, independently confirmed
down to the exact program instruction and the exact second.

### Twenty seconds later: a fake market, and the circuit breakers come off

At **16:05:39 UTC**, signed directly by the newly-installed admin key
(no multisig needed any more), a single transaction
(`4a5962Rdqd9pkXtk9DMQ9ZYhdGb2k9gPw71GvukJgELhxbCY5gm1c1hhKdwuGefyqJ3XMvihUTDNDn3qbXnst82X`)
calls Drift's own `InitializeSpotMarket` ("initializing spot market 63" per
its own log) and then, in the same transaction, `UpdateWithdrawGuardThreshold`
five times on five different existing (real) spot markets (indices 19, 0,
27, 17, 4), each one raised to an identical ceiling:

| Market index | withdraw_guard_threshold before | after |
|---|---|---|
| 19 | 5,000,000,000 | 500,000,000,000,000 |
| 0 | 25,000,000,000,000 | 500,000,000,000,000 |
| 27 | 10,000,000,000 | 500,000,000,000,000 |
| 17 | 5,000,000,000,000 | 500,000,000,000,000 |
| 4 | 200,000,000,000 | 500,000,000,000,000 |

`withdraw_guard_threshold` is Drift's own circuit breaker limiting how
much can be withdrawn from a market's spot balance before the protocol's
own logic halts further withdrawals. Raising five different real markets'
thresholds to the same round ceiling, in the same transaction that also
created the fake market, is not something any of the press write-ups
reviewed describe at this level of detail; it was found here purely from
decoding the transaction's own logs.

This was not a one-off: continuing to paginate the newly-installed admin
key's own signature history through the same window surfaces **at least
23 separate `UpdateWithdrawGuardThreshold` instructions** between
16:05:39 and 18:05:01 UTC (five in the bundled transaction above, plus at
least 18 further standalone transactions, each touching one more market;
a handful of additional transactions in the same window could not be
decoded due to the public RPC's rate limiting, so the true count is at
least this high, not exactly this high). About 88.6 minutes after the
hijack, at 17:33:57 UTC, the admin key also set up a **second** spot
market using the same fake mint (transaction
`2zwpKAerW73YJjYRWzRLfMV27ZswM2nBYy5v9DsGqYdWamV4c7Ywf6LzKA6TazX9BqMRX6bgFxqaNtCd8fPzGVQy`),
followed minutes later by `UpdateSpotMarketPoolId` and
`UpdateSpotMarketStatus` calls, consistent with the attacker correcting or
re-parameterizing the first market's setup rather than deploying a second
distinct fake asset.

### The fake collateral: independently derived, not press-supplied

Press names the fake token "CarbonVote Token" / "CVT" with "a total
supply of 750 million" but no source of any of these write-ups supplies
its mint address. This reconstruction derives it a different way:
Drift's own `InitializeSpotMarket` instruction above creates two SPL
token accounts via inner `initializeAccount3` instructions, and both name
the same mint: `G84LEhbNMR1yYbHgHbnNYNSK8mpTKcazh5jcW5yMPQKo`.

Querying that mint live confirms: 9 decimals, supply
749,999,997.231082657 (~750,000,000, within 0.0000004% of press's "750
million" claim), mint authority `null` (already renounced, standard
practice to make a fake token look permanently fixed-supply and
legitimate). Its own Metaplex metadata account (found live via a
`getProgramAccounts` filter, not a hardcoded PDA) decodes to:

```
name:   CarbonVote Token
symbol: CVT
uri:    https://arweave.net/AtgGd3qImxJuKmE3Y3SEXBiHAR__VU10acsYol0pAXY
```

Independently arriving at "CarbonVote Token" / "CVT" purely from the
hijack transaction's own inner instructions, with no press-supplied
address as a starting point, is the strongest single confirmation in this
reconstruction that the press narrative describes a real, on-chain
mechanism rather than a hypothesized one.

### The real-asset outflow: JLP in, USDC/USDT/USDS out

The attacker wallet `HkGz4KmoZ7Zmk7HN6ndJ31UJ1qZ2qgwQxgVqQwovpZES` starts
receiving funds at 16:08:13 UTC, about 3 minutes after the hijack. Its
first transfer in is 100,000 units of mint
`27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4`. That mint's own Metaplex
metadata (checked the same way as CVT's above, not assumed from
recognizing the address) decodes to `name: Jupiter Perps LP, symbol:
JLP`, a real, widely-used Solana asset, not a fake one, and exactly
Drift's own #1 asset in its official stolen-asset breakdown ($159.3M).

Paginating this wallet's and the hijacked-admin wallet's full signature
history and filtering to 2026-04-01 finds 315 transactions combined (288
from the attacker wallet, 27 from the hijacked-admin wallet); 170 of
those (all 27 admin-key ones, plus the attacker wallet's 141 falling in
the 16:00-17:30 UTC sub-window where the bulk of the outflow happens)
were individually decoded during this reconstruction. That decode
surfaces a repeating pattern: JLP (and other real Drift collateral) gets
converted through Solana AMM pools into USDC, USDT, and USDS, which are
then swept in large chunks to a second address,
`8ubo4HbWJHKyFJYJc2Gh74dxCP7bN7Fu2Pi13KZ9rGxw`. A representative sample of
that sweep, re-verified live by this repository's committed script:

| Asset | Tx (truncated) | Amount reaching the consolidation address |
|---|---|---|
| USDT | `Z1vjtrziosTdP58u..` | 4,009,718.693543 |
| USDT | `5DjHKgBVv4XcEXnv..` | 1,638,691.548357 |
| USDS | `2tpnkJaXcPr7z3mf..` | 5,254,017.070394 |

Summed: **5,648,410.24 USDT** and **5,254,017.07 USDS**. Drift's own
official figures for the same two assets are $5,648,410.13 (5,648,410.15
tokens) and $5,254,126.13 (5,254,016.98 tokens) respectively, both
independently matched to within 0.002%, without this reconstruction
having reproduced Drift's own internal ledger transaction-by-transaction.
A separate, broader (unsampled) scan of just the USDC leg found over
$103M in USDC alone reaching the same consolidation address across the
full window, consistent with Drift's own $71.4M native-USDC figure plus
a large share of the $159.3M JLP figure having been swapped into USDC
before consolidation, though this reconstruction did not fully separate
the two (see Caveats).

### Drift's own $295.7M figure, fetched live

Drift's "Incident Recovery Update - April 16, 2026"
(https://www.drift.trade/updates/incident-recovery-update-april-16-2026-now),
fetched live by the committed script, states the total as
**$295,706,374.93** across 19 assets:

| # | Asset | Amount ($) |
|---|---|---|
| 1 | JLP | 159,329,898.68 |
| 2 | USDC | 71,415,648.65 |
| 3 | cbBTC | 11,321,165.24 |
| 4 | SOL | 10,426,959.98 |
| 5 | USDT | 5,648,410.13 |
| 6 | USDS | 5,254,126.13 |
| 7 | WETH | 4,684,896.11 |
| 8 | dSOL | 4,466,805.96 |
| 9 | WBTC | 4,359,399.64 |
| 10 | Fartcoin | 4,145,112.56 |
| 11-19 | jitoSOL, syrupUSDC, INF, mSOL, bSOL, EURC, zBTC, USDY, JUP | 429,820.12-3,598,696.98 each |

This reconstruction did not re-derive all 19 rows transaction-by-transaction
(see Caveats); it treats this table as the protocol's own primary-source
figure, cross-checked (not reconciled to match) against the independently
found USDT/USDS sample above and the independently confirmed JLP identity.

### A protocol that renamed itself after the hack

Drift's own GitHub organization no longer exists under that name: a live
GitHub API call for `drift-labs/protocol-v2` returns `301 Moved
Permanently` to repository ID `497045217`, which now resolves to
`velocity-exchange/protocol-v2`, archived, last pushed 2026-07-08. Press
(The Defiant, CryptoRank, BingX, Blockzeit, Gate, CryptoTimes,
TakeProfit, CoinGabbar) independently confirms Drift rebranded to
"Velocity DEX" on 2026-07-01 as part of its post-hack relaunch, migrating
its settlement layer from USDC to USDT and introducing "a new
community-governed multisig" with durable nonces disabled for all
signers, transaction content independently verified outside the primary
signing interface, and enforced timelocks, a remediation plan that maps
directly onto the mechanism this reconstruction independently found
on-chain (durable nonces, an unreviewed multisig approval, no timelock).
This script still fetches the program ID from the `master` branch of
`drift-labs/protocol-v2`'s raw content, which GitHub continues to resolve
correctly despite the rename.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Drift Protocol, Velocity DEX, Squads, or any outlet
  cited above.
- The $295,706,374.93 total and its 19-asset breakdown are Drift's own
  stated figures, fetched live from Drift's own page, not independently
  re-summed line by line here. This reconstruction independently verified
  the mechanism in full and a representative sample of the outflow (the
  USDT and USDS legs, matching to within 0.002%, plus confirming the JLP
  and USDC mints are real Solana assets, not fake ones), rather than
  reproducing Drift's entire internal ledger.
- The full JLP and USDC totals were not cleanly separated: JLP appears to
  have been substantially converted into USDC through on-chain swaps
  before reaching the consolidation address, so this reconstruction's
  broader (unsampled) ~$103M USDC figure at that address mixes native
  USDC with swapped-JLP proceeds rather than isolating Drift's own
  reported $71.4M USDC and $159.3M JLP figures separately.
- "At least 23" withdraw-guard-threshold changes is a floor, not an exact
  count: a handful of transactions in the admin key's signature history
  during this window could not be decoded due to the public RPC's rate
  limiting (HTTP 429) rather than because they were a different
  instruction.
- Whether `AiLGdNitMjv8n5HMS7HAdV2kaeJZZFd4jdfn5xp1PKrW` (the pre-hijack
  admin) was itself a Squads vault PDA or a plain multisig-controlled key
  was not independently determined beyond confirming it is a System
  Program-owned account with no program data of its own.
- The real-asset outflow's full time window was not exhaustively bounded:
  the earliest inbound transfer found was 16:08:13 UTC, and the sampled
  outflow transactions span 16:52-17:14 UTC, but whether outflow
  continued past 17:14 UTC (or into the further transactions in the
  315-found/170-decoded set not individually itemized above) was not
  determined.
- Checked live today (2026-09-11): the two attacker wallets and the
  consolidation address hold only small residual SOL balances
  (1.10, 2.97, and 0.10 SOL respectively), consistent with the bulk of
  funds already having moved on; where those funds went next was not
  traced here.
- As with every entry in this repo, this reflects a snapshot as of
  2026-09-11.

## License

MIT
