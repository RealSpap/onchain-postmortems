# Changelog

Additions and corrections to this repository, most recent first. Each
incident's own README carries the full detail and supersedes any earlier
wording; this file is a short log. New incidents are also announced as
GitHub releases.

## 2026-10-04

- Added FlashLoopAdapter Safe module (Ethereum, 2026-10-01).

## 2026-10-01

- Added Duelbits hot wallet drain, Ethereum leg (Ethereum, 2026-09-24).
- Added the September 2026 digest.

## 2026-09-30

- Loss figures now distinguish recomputed from sourced: a new † marker in
  the Index flags dollar figures taken from the protocol's own
  post-mortem, press or DefiLlama and not independently recomputed
  (Drift, Moonwell, Term Finance, Tectonic, Cosmos EVM, Across, Ajna,
  Sandbox, Avici, Balancer V1, Fetch.ai and NuNet, The Internet Token,
  WealthManagementV2). The headline now states both: $917.6M across 52
  incidents, $580.7M of it independently recomputed.
- One counting rule for the Index, written into its legend: funds
  returned by the attacker or reversed on-chain are deducted. Safe LP
  Module now counts the 83.63 rsETH actually kept (≈ $225,762), not the
  $8,006,577 gross drain.
- Tectonic: $9.19M unrecovered, sourced from Cronos's official
  post-mortem (was $8.3M); the dead dashboard link is removed.
- WealthManagementV2: where the USDT held by the attacker's proxy came
  from was not traced, so the Index carries DefiLlama's $26,414 (was
  ≥ $422,251) and the earlier claim that DefiLlama's "Key Compromise"
  classification is contradicted is withdrawn, with its Corrections row.
- ether.fi: priced at the 07:20 UTC oracle point ($38,151, was $38,004);
  7 of the 11 drained wallets are EIP-7702 accounts (was 9).
- Virtue Protocol: $848,190, matching the script output (was $848,457).
- Limit Break Payment Processor V2 marked as a floor, as its own note
  already said.
- Corrections table: BarnBridge SMART Yield added; Allbridge, Liquid
  Network and MORE Markets reclassified as reconciliations; Cosmos EVM,
  BeatSwap, Maya Protocol and Float Protocol rows made more precise. 34
  rows: 23 corrections, 8 reconciliations, 3 discoveries.
- Reddio, Secured Finance, Limit Break, ether.fi and Nimiq: current patch
  status not re-verified; exploitation detail withheld pending disclosure
  to the teams.
- Added SECURITY.md (how to report an error or request a correction).
- The consistency check now also covers the recomputed share, the floor
  count, Index links, and the format of every hypothesis registry.
- Releases are now created only for new incidents, after the consistency
  check passes, at most one per day.
- Added Bitget hot wallet drain, Ethereum leg (Ethereum, 2026-09-24).

## 2026-09-29

- Index and Corrections tables moved out of the README into INDEX.md and
  CORRECTIONS.md.
- Headline figures re-aligned with the Index; the consistency check
  extended to the headline and the Corrections row count.
- Corrections table: Nimiq, Fetch.ai and NuNet, and The Internet Token
  added.
- Added Limit Break Payment Processor V2 forwarder spoof (Ethereum,
  2026-09-25).

## 2026-09-26

- Added Payy Network rollup zero-hash burn (Ethereum, 2026-09-24).

## 2026-09-24

- Added The Internet Token LiquidityUnifier fake-pool mint (Base,
  2026-09-21).
- Added Fetch.ai and NuNet dual key compromise (Ethereum, 2026-09-19).

## 2026-09-21

- Added Nimiq GSN forwarder unsigned execute (Polygon, 2026-09-16).
- Dream Health Chain: day counts updated and live state re-verified.

## 2026-09-20

- Added Safe LP Module unauthenticated executor (Ethereum, 2026-09-15).
- Added Chainflip Tron vault double payout (Tron, 2026-09-12).
- Cozy V2: clarified the "3 distinct source addresses" count.

## 2026-09-19

- BeatSwap: V2 depositors are being repaid after the pause, V1's are
  not; corrects the previous day's note.
- COLDCARD and Coinsbuy re-checked; the COLDCARD attacker's BTC is still
  unmoved.

## 2026-09-18

- Added Flamincome VaultYUSDT share inflation (Ethereum, 2026-09-16).
- BeatSwap: the 2026-09-15 pause recorded. BarnBridge: Blockaid's later
  figure added.

## 2026-09-17

- Added Dream Health Chain award re-claim (BNB Chain, 2026-09-05).
- Zentra Finance: the 2026-09-16 patch recorded. Avici: the scope of the
  sampling estimate clarified.

## 2026-09-16

- AFX Bridge: cites AFX's own 2026-07-31 postmortem (malware on
  validator nodes) next to DefiLlama's "key compromise" label.

## 2026-09-15

- Ajna: the 49.32 WETH extraction is at block 25,854,585, not the block
  cited by press. Balancer V1 re-checked.

## 2026-09-14

- Added BeatSwap vesting slot0 reserve drain (BNB Chain, 2026-09-09).
- Cosmos EVM: MANTRA's $3.6M covers both attacks, not the first alone.

## 2026-09-13

- Added Zentra Finance aToken burn clamp (Citrea, 2026-09-09).
- Monthly digest format, starting with August 2026.
- Fund-flow diagrams added to 8 entries; Tectonic's verification files
  added; older consolidated entries rewritten to the current format.

## 2026-09-12

- Added ether.fi Liquid AtomicQueue (Ethereum, 2026-09-11).

## 2026-09-11

- Added Virtue Protocol, Radix (Hyperlane Warp Routes), Reddio (RedSonic
  Vault), Float Protocol, Coinsbuy, Coreum (XRPL Bridge), Oraichain,
  Secured Finance, Full Sail, Drift Protocol, WealthManagementV2, Weft
  Finance, BarnBridge SMART Yield and Symbiosis.

## 2026-09-10

- Added Cosmos EVM, Allbridge, Liquid Network, Aquifer, Maya Protocol,
  COLDCARD, Gravity Bridge, Avici, MORE Markets, Verus-Ethereum Bridge,
  Across Protocol, Ostium, Nomic, XRP Healthcare, AFX Bridge, Lazy Summer
  and Kelp DAO.
- Index grouped by year and month; consistency check added to CI.

## 2026-09-09

- Eight earlier standalone reports consolidated into this repository:
  Sandbox, Moonwell, Balancer V1, Term Finance, Notional, Ajna, Cozy V2
  and Tectonic.
