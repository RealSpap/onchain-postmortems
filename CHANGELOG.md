# Changelog

One entry per addition or correction to this repo. Each incident added
with `add_new_entry.py` gets tagged as a matching GitHub release, see
"Get notified of new postmortems" in `README.md`.

## 2026-09-11 (21)

- Added a 35th incident: Drift Protocol durable-nonce admin hijack,
  Solana, 2026-04-01, the largest DeFi hack this repo has covered to
  date. Found via DefiLlama's hacks feed (a "Drift Trade" row, $295M,
  "Access Control" / "Proxy Upgrade Hijack", distinct from an older 2022
  $14.5M "Drift Trade" row already resolved via a whitehat return, not
  this incident) and cross-checked against extensive press coverage
  (Elliptic, TRM Labs, Chainalysis, QuillAudits, Halborn, Merkle Science),
  none of which decodes the actual on-chain admin-change instruction,
  names a verifiable fake-token mint address, or shows the
  withdraw-guard-threshold manipulation. Started from Drift's own GitHub
  deployment record (`drift-labs/protocol-v2`'s `Anchor.toml`, fetched
  live) for the program ID, and, separately, from two transaction
  signatures a QuillAudits write-up names, treated only as a lead (the
  same way this repo's Aquifer entry treats a press-named address), not
  taken on faith. Independently decoded the admin-hijack transaction's
  own program log ("Instruction: UpdateAdmin" / "admin: X -> Y"),
  confirming two Squads-multisig-signer approvals bundled with a
  durable-nonce `advanceNonce` instruction (Solana's mechanism for a
  transaction signed once and broadcast much later) overwrote Drift's own
  on-chain admin key at 2026-04-01 16:05:19 UTC, one second after a
  matching pre-sign transaction. Twenty seconds later the new admin key
  created a new fake spot market and, in the same transaction, raised the
  withdraw-guard circuit breaker on five real markets to an identical
  ceiling; continuing to paginate the admin key's own transaction history
  finds at least 23 such changes across roughly 2 hours, a level of
  mechanism detail none of the press write-ups reviewed show. The fake
  collateral mint itself was not taken from any press source: derived
  purely from the hijack transaction's own inner SPL-Token instructions,
  then independently confirmed via live Metaplex metadata to be named
  "CarbonVote Token" / "CVT" with a live supply of 749,999,997.23 (within
  0.0000004% of press's "750 million" claim) and a renounced mint
  authority. The real asset the attacker wallet first received was
  likewise identified via its own live metadata ("Jupiter Perps LP" /
  "JLP", not a fake token), and a representative sample of the downstream
  outflow (USDT and USDS legs reaching a consolidation address) matches
  Drift's own official per-asset figures, published on its own
  "Incident Recovery Update" page and fetched live by the committed
  script, to within 0.002%. Also independently confirmed, via a live
  GitHub API call, that Drift's own GitHub organization no longer exists
  under its original name (`drift-labs/protocol-v2` now redirects to
  `velocity-exchange/protocol-v2`, archived), consistent with widely
  reported press coverage of Drift's July 2026 rebrand to "Velocity DEX"
  as part of its post-hack relaunch. This entry treats the $295,706,374.93
  total as Drift's own primary-source figure, cross-checked against (not
  fully re-derived from) the independently verified mechanism and sample
  outflow, rather than reproducing all 19 stolen-asset rows
  transaction-by-transaction.

## 2026-09-11 (20)

- Added a 34th incident: Full Sail (Sui Vaults) Switchboard-oracle vault
  drain, Sui, 2026-08-29. Found via DefiLlama's hacks feed (tracked as
  "Full Sail", Sui, "Oracle Manipulation" / "Oracle Misconfiguration",
  with **no dollar amount at all** -- `amount: null`) and cross-checked
  against press (Yellow, CryptoTimes, Cointelegraph), which reports
  "roughly $91,000" across "three vaults" but names no attacker address,
  transaction hash, or which three vaults, attributing the root cause to
  the same broader Switchboard oracle-signing compromise this repo
  already covers for Virtue Protocol on IOTA
  (`virtue-iota-switchboard-oracle/`). None of the press claims were
  taken on faith. Started from Full Sail's own published npm SDK package
  (`@fullsailfinance/sdk`, fetched live as a tarball from
  registry.npmjs.org, not a block explorer), whose minified bundle
  embeds three network configs; the script specifically locates the
  `mainnet-production` block (a naive first-match regex would silently
  grab `mainnet-dev`'s addresses instead) to extract the vault package ID
  and five config object IDs, all confirmed live on Sui mainnet via a
  third-party public JSON-RPC node (Mysten Labs' own public fullnode has
  deprecated JSON-RPC in favor of GraphQL/gRPC). Found the attacker
  address and all three affected vaults independently, not from press:
  paginated the vault package's own `WithdrawEvent` log for 2026-08-29
  and clustered by sender, surfacing one address responsible for 63 of
  the day's withdraw calls across exactly 3 distinct Port objects (USDC/
  ETH, IKA/SUI, USDC/SUI), matching press's "three vaults" count exactly.
  Decoded one of the attacker's own deposit transactions byte-for-byte:
  a single atomic PTB submits a forged Switchboard price for SUI (100x
  below real, $0.007405 vs $0.740500), calls Full Sail's own
  `port::calculate_aum` and `port::deposit` while that fake price is
  live, then restores the real price in the same transaction -- and
  independently confirmed the same exact ~100x pattern for ETH
  ($24.41 vs $2,440.63) and, pair-by-pair, for IKA too, while USDC (the
  untouched quote asset) shows only ordinary sub-1% feed noise, ruling
  out a blanket "whole feed compromised" reading in favor of "exactly the
  asset each vault needed skewed." Summed the attacker's own
  `WithdrawEvent` minus `IncreaseLiquidityEvent` amounts per vault across
  the full attack window (this nets out each vault's own repeated
  deposit/withdraw recycling automatically) and converted at the chain's
  own restored oracle price, landing on $91,605.56 total, 0.67% above
  press's unsourced $91,000 estimate, independently computed rather than
  reconciled to match it. Cross-checked the ETH leg a second, entirely
  separate way: a swap-out transaction found by scanning the attacker's
  own follow-up activity shows a balance change of exactly -77345418 raw
  ETH through Full Sail's own DEX-aggregation router, matching this
  project's own ledger-summed net ETH figure to the last wei. Also
  confirmed the attacker's wallet currently holds only dust and zero ETH/
  IKA (funds moved out), and read Full Sail's own live
  `vault_config::GlobalConfig.max_price_deviation_bps` (currently 200 bps
  / 2%), flagged as an open question rather than a resolved root cause
  since whether that guard existed or was wired into the exploited code
  path at attack time was not established. This entry is a genuine
  discovery/quantification, not a correction of an existing DefiLlama
  number, since DefiLlama tracks the incident with no dollar figure to
  correct.

## 2026-09-11 (19)

- Added a 33rd incident: Secured Finance (JPYC Lending Market) TokenVault
  self-lend, Ethereum, 2026-09-05/09-06. Found via DefiLlama's hacks feed
  (tracked as "Secured Finance Lending", $104,000, "Oracle Manipulation" /
  "Spot Price Manipulation", empty source field); no press writeup,
  security-firm postmortem, or official protocol statement was found
  anywhere for it. Started from Secured Finance's own GitHub deployment
  registry (`deployments/mainnet/LendingMarketController.json` and
  `TokenVault.json`), confirmed both proxies live on Ethereum mainnet, and
  read the JPYC currency's own token address live from TokenVault's own
  `getTokenAddress("JPYC")` state rather than assuming it. Scanned both
  contracts' own event logs across a full 72-hour window (not the
  narrower 24-hour window a previously-parked attempt at this same
  candidate used) and found exactly 2 transactions, 58 minutes apart,
  where TokenVault paid out materially more JPYC than it received in the
  same transaction, both sent by the same near-fresh EOA (nonce 10,
  matching its full Blockscout-fetched transaction history exactly), both
  `to: null` (a contract-creation transaction running the exploit in its
  own constructor). Confirmed neither transaction carries a
  LiquidationExecuted or ForcedRepaymentExecuted event (independently
  computed topic hashes checked against every transaction in the window,
  zero matches), ruling out ordinary liquidation profit. Decoded both
  transactions' full JPYC Transfer sequence directly: each opens with a
  flash loan from Uniswap V4's PoolManager and closes with that exact
  same amount repaid, with 4,360,902.135130 JPYC landing on the attacker's
  EOA in between ($45,444.97 at CoinGecko's theft-day price), cross-checked
  a second way against TokenVault's own Deposit/Withdraw event totals
  (both methods agree to the last decimal). Read Secured Finance's own
  currently-live `DepositManagementLogic.sol` from GitHub (last touched
  2026-02-09, seven months before this incident, still the most recent
  commit on that file) and quoted the exact `_calculateCollateral`/
  `getWithdrawableCollateral` functions whose structure is consistent
  with the exploit's observed same-block deposit-then-over-withdraw
  pattern, an improvement over a previously-parked attempt at this
  candidate that could only offer this project's own unsourced inference.
  Traced the attacker's complete 10-transaction lifetime history (not
  just the 2 exploit transactions) and found 91% of the realized ETH
  proceeds (10.1 of 11.125698746898514 ETH total, the total independently
  cross-checked 3 ways: 1inch swap decode, WETH's own Withdrawal event,
  and an attacker-EOA balance-delta check net of gas) routed into Tornado
  Cash's own router contract, a genuinely new finding beyond what the
  parked candidate issue had found, and itself independent evidence
  against any legitimate or white-hat explanation. This project's own
  figure ($45,444.97) sits at 0.44x DefiLlama's tracked $104,000, an
  unreconciled gap explicitly disclosed rather than papered over, and
  this entry corrects DefiLlama's classification outright: neither
  transaction reads any price oracle anywhere, so "Oracle Manipulation" /
  "Spot Price Manipulation" does not hold up; this is a TokenVault
  collateral-accounting / access-control bug. 8 other transactions active
  on the same two contracts in the same 72-hour window are neither
  counted nor cleared: 2 addresses among them show a superficially similar
  same-transaction deposit-then-withdraw pattern on USDC or WBTC, but
  unlike the confirmed attacker, neither creates a fresh contract in the
  same transaction and every counterparty carries a long prior
  transaction history (nonces from 264 up to 222,969), so this
  reconstruction reports them as an open question rather than asserting
  either "routine" or "exploit" without stronger per-transaction evidence.

## 2026-09-11 (18)

- Added a 32nd incident: Oraichain (ICS-20 EVM Precompile) self-mint,
  Oraichain + Cosmos Hub + Osmosis + Injective, 2026-08-08/08-09. Found via
  DefiLlama's hacks feed (tracked as "Oraichain", a flat $1,000,000 with an
  empty source field), cross-checked against the only public writeup
  found, a short radar note on 0xposed.io that states plainly it has no
  attacker address, no transaction hash, and no official post-mortem as of
  2026-08-20 -- treated here as a rough time-window anchor only, not a
  source of any hard number. Every address, transaction, and figure below
  was independently found and re-derived from the chain. Binary search
  against a live archive RPC (mainnet-orai-rpc.konsortech.xyz, the only
  one of Oraichain's 7 registered RPC endpoints whose retained history
  reaches back before 2026-08-08) located the incident window; a
  `message.sender` tx_search on the address found calling the chain's own
  ICS-20 EVM precompile (0x0000...0802, independently confirmed as
  `ICS20PrecompileAddress` from `cosmos/evm`'s own GitHub source, not
  assumed from the address alone) returned that address's entire
  31-transaction history: 24 self-referential IBC-transfer calls, each of
  which correctly escrowed the sender's balance for an outbound packet and
  then also erroneously minted the identical amount straight back to the
  same sender, roughly doubling the balance every call over 10 minutes
  (89.999995 ORAI to 754,974,669.602687 ORAI), followed by one final
  native-EVM consolidation transfer of 1,509,949,343.000000 ORAI (decoded
  directly from its own `coinbase` event) to a second, cash-out address.
  That address's own complete 17-transaction history was likewise fully
  decoded: 600,000,000 ORAI IBC'd to Injective; a 9-way OraiDEX swap chain
  draining, among other assets, two CW20 stablecoins independently
  identified via their own live `token_info` query (not assumed from a
  swap-log symbol) as USDT and USDC; two of those swap outputs further
  bridged onward to Cosmos Hub and Osmosis as 3,161.082810 ATOM and
  5,438.198605 OSMO, with both IBC voucher denoms independently decoded via
  Oraichain's own live `denom_traces` endpoint (not trusted from the
  packet's self-reported memo); 59,255,027.19 ORAI locked as lending-market
  collateral with no matching borrow event found; and a small leg toward
  Ethereum mainnet via the legacy bridge, not independently re-traced.
  Oraichain's own `supply/by_denom` endpoint, queried at specific
  historical block heights via the `x-cosmos-block-height` header, pins
  the reversal to one single block: total supply was 1,525,538,652.019679
  ORAI (78.00x the post-incident baseline) at block 118018794
  (2026-08-09T03:56:51.007Z) and 19,558,484.847626 ORAI one block later,
  118018795 (2026-08-09T03:56:51.608Z), about 3 minutes after the
  officially reported 04:00 UTC halt time -- consistent with a coordinated
  state-surgery reversal, not a gradual burn. Live balance checks today
  confirm which legs actually stayed reachable: both Oraichain-side
  addresses are now empty (the attacker's holds 1.205373 dust ORAI; the
  cash-out address holds nothing at all, in any denom), while the
  attacker's own Cosmos Hub and Osmosis addresses hold only 1.081869 ATOM
  and 0.543356 OSMO today, a small fraction of what was bridged in,
  meaning the attacker moved almost all of it onward well beyond
  Oraichain's own reach. Loss figure: this entry prices only the ATOM and
  OSMO confirmed, via those live cross-chain balance checks, to have left
  Oraichain and been further dispersed: $4,461.73 at CoinGecko's
  2026-08-08 historical prices, two orders of magnitude below DefiLlama's
  flat $1,000,000 and far below the true nominal mint. The roughly $6,383
  in USDT/USDC also drained from OraiDEX pools is not added to that floor:
  both now sit at a zero balance with no on-chain trace of having left any
  other way, consistent with (though not proven to be) the same reversal.
  Not independently re-traced this round: the 600,000,000 ORAI sitting on
  Injective (its status there was not checked on Injective's own chain),
  whether the lending-market collateral was ever borrowed against or
  separately seized, and whether this is the exact same defect `cosmos/evm`'s
  own security advisory ASA-2026-002 (patched in v0.6.0, published March
  2026, describing an unrelated ~$7M incident on a different, unnamed
  chain on 2026-01-21) already documents, a later recurrence of it on
  Oraichain specifically, or an independently discovered variant -- flagged
  as an open question rather than asserted either way, since Oraichain's
  own public GitHub has not been pushed since November 2024 and its
  `master` branch shows no `cosmos/evm` dependency at all, meaning it is
  not the code the live chain actually runs.

## 2026-09-11 (17)

- Added a 31st incident: Coreum (XRPL Bridge) deposit forgery, XRP Ledger +
  Coreum, 2026-08-09. Found via a web search for recent security-firm
  writeups (CoinDesk and Decrypt both carry independent, mainstream
  coverage); DefiLlama separately tracks the same incident as "Coreum
  Bridge", $200,000, "Bridge & Cross-Chain" / "Bridge Logic Flaw". A first
  attempt this round anchored on a different, also XRPSCAN-verified
  "Coreum"/"Issuer" XRPL account (rcoreNywaoz2ZCQ8Lg2EbSLnGuRBmun6D) and
  was a genuine dead end: that account's balance sat flat at 472.89 XRP
  for the entire year sampled, and it turned out to be blackholed (master
  key disabled, null RegularKey, zero owned ledger objects -- no
  SignerList at all), structurally incapable of signing anything. The
  second, genuinely different on-chain angle that resolved it: querying
  the bridge's OWN smart contract on Coreum's mainnet (a live CosmWasm
  `{"config":{}}` query, cross-checked against CoreumFoundation's own
  `token-registry` GitHub repo to confirm the contract address itself is
  the shared issuer for all 10 mainnet XRPL-originated assets) returned
  the bridge's own `bridge_xrpl_address`
  (rxXXXeMX8Gy5YvibvGLnQJ1XKKD7UswM1), a 17-of-28 `evidence_threshold`,
  and `bridge_state: halted` -- matching press's own "17 of 28 relayer
  keys" description independently, from the bridge's own primary source.
  A direct before/after ledger-snapshot balance comparison (independent
  of any transaction-list indexer's completeness) confirms the bridge's
  own reserve fell by exactly 199,916.334320 XRP over the incident
  window. `account_tx` against the public s2.ripple.com endpoint proved
  genuinely unreliable within this session (4 separate fetches of the
  identical ledger range returned 4112, 4000, 4111, and 4088 raw records);
  `reconstruct_exploit.py` handles this by retrying the fetch until the
  resulting balance-changing subset sums to exactly that ground-truth
  figure rather than trusting any single fetch, which matched on the
  first attempt on the run that produced this entry: 94 real payouts
  (each carrying exactly 17 Signers), split 107,397.5 XRP to one attacker
  address and 92,518.8 XRP to a second, 199,916.300000 XRP delivered in
  total -- matching press's own per-destination and total figures to the
  exact XRP. The forged-deposit mechanism itself is decoded directly from
  one representative transaction's own raw memo bytes: a self-transfer of
  the bridge's own already-issued wrapped-token IOU between the two
  attacker addresses, carrying the bridge's own real deposit-tag JSON
  format, that never touched the bridge's reserve address at all. Loss
  figure: $207,699.83 at CoinGecko's 2026-08-09 historical XRP price,
  about 3.8% above DefiLlama's tracked $200,000 (ordinary daily-price
  variance, not a mechanism or classification error, so not listed as a
  correction). Not independently re-traced this round: the downstream
  laundering path press describes (ETH via THORChain to Tornado Cash), and
  no official Coreum/TX blog postmortem, since docs.tx.org returned HTTP
  403 to this project's tooling.

## 2026-09-11 (16)

- Added a 30th incident: Coinsbuy (hot-wallet drain), Ethereum + Tron,
  2026-08-09. Found via rekt.news's own published account (not DefiLlama's
  hacks feed, though DefiLlama separately tracks the same incident at
  $7,900,000, "Access Control" / "Improper Access Control", with an empty
  source field). Unlike almost every other entry in this repo, this is a
  custodial-wallet incident, not a smart-contract exploit: Coinsbuy has no
  public GitHub org (checked live across 3 case variants) and its own
  official statement, fetched live from coinsbuy.com rather than trusted
  from a press paraphrase, confirms the date and a full reimbursement from
  its own reserves but explicitly withholds every technical detail ("we
  are not sharing technical details at this stage"). The Tron leg is
  independently confirmed in full: every TRC20-USDT transfer landing on
  the attacker's Tron collector on 2026-08-09, summed live from TronGrid
  across 126 transfer records from 8 source addresses, totals exactly
  6,037,005.00 USDT, matching rekt.news's own figure to the cent, with one
  representative transaction separately cross-checked via TronGrid's raw
  transaction-info endpoint and its own decoded Transfer event log,
  independent of the list endpoint used for the sum. The Ethereum leg is
  confirmed only in part: one direct 77 ETH transfer from a
  Blockscout-tagged "Coinsbuy 1" / "Exchange" wallet to the attacker's
  named Ethereum collector is confirmed via raw eth_getTransactionByHash /
  eth_getTransactionReceipt / eth_getBlockByNumber on 2 independent RPC
  endpoints, but rekt.news's fuller claim (210.8 ETH via FixedFloat, 150
  ETH via ChangeNOW) routes through an unlabeled intermediary address that
  itself cycles hundreds of ETH through 1inch's router and dozens of
  single-use-looking destinations -- a pattern consistent with active
  cash-out laundering, but not independently attributable to a specific
  named Coinsbuy wallet, so it is not counted. A best-effort scan of the 3
  named Ethereum hot wallets for any other direct transfer to the
  attacker (method step 6) hit Blockscout's public rate limit on all 3
  wallets during this run (8 retries with growing backoff each, still
  refused); the script is written to report exactly which wallets it
  could and could not reach on a given run rather than claim a
  completeness it doesn't have, and this entry's Caveats say so plainly.
  Combined independently-confirmed floor: $6,184,494.48 (6,037,005.00 USDT
  + 77 ETH at CoinGecko's 2026-08-09 price of $1,915.45), reported as a
  known floor (`≥`) against rekt.news's own $8.07M total and DefiLlama's
  tracked $7,900,000. Live state check: the Tron collector's own balance
  today is near-zero (10.63 USDT), and its own outbound transfers on
  2026-08-09 sum to 6,036,994.37 USDT, confirming the funds were forwarded
  onward the same day rather than left sitting, matching rekt.news's
  "refills began within 10-12 hours" account.

## 2026-09-11 (15)

- Added a 29th incident: Float Protocol (Hypervisor Vaults), Ethereum,
  2026-08-31. Found via DefiLlama's hacks feed (a "Float Protocol" row,
  $28,000, "Oracle Manipulation" / "Spot Price Manipulation", reusing
  defillamaId 497, the same id as Float Protocol's unrelated January 2022
  exploit). The starting anchor was not a press address: SlowMist's own
  alert (as republished by crypto.news and cryptotimes.io) named 5
  addresses, and every one of them was independently re-derived rather
  than trusted. The two "vulnerable contracts" it named
  (`0x85cbed523459b7f6f81c11e710df969703a8a70c` and
  `0xc86b1e7fa86834cac1468937cdd53ba3ccbc1153`) are confirmed live as
  Float Protocol's own Gamma-style Hypervisor vaults
  (`name()`="Visor FLOAT-ETH Uni .3%", `token0()`=FLOAT, `token1()`=WETH),
  cross-checked against messari/subgraphs' own public Gamma Strategies
  deployment registry on GitHub (a primary source, not a press write-up),
  which independently names the same two addresses `vFLOAT-ETH3_2` and
  `vFLOAT-ETH3_3`, deployed November 2021. All 108 event logs in the
  single exploit transaction
  (`0x3d7549db65344da2a41067e17791b17fac16ec6b8e5132e82e243f6541de5cff`,
  block 25,874,402) were decoded against independently recomputed
  `keccak256` topic hashes, asserted at runtime rather than assumed:
  a 1,000 WETH flash loan (fully repaid) and a 120,000 FLOAT Uniswap V2
  flash swap (repaid with a 0.3009% premium, matching V2's own 0.30% fee)
  funded four deposit/withdraw cycles straddling a Uniswap V3 `slot0`
  price the attacker pushed away from fair value, alternating between the
  two vaults, each pair burning and minting the identical share count for
  a disproportionate token split. The realized profit is confirmed two
  independent ways, agreeing to the wei: the WETH contract's own
  `Withdrawal` event (the attack contract's final unwrap, log 107) and
  the attacker EOA's own `eth_getBalance` delta across the exploit block
  (cross-checked on two separate archive-capable RPC providers,
  `eth.drpc.org` and `eth-mainnet.public.blastapi.io`), both landing on
  exactly 10.706591043820923 ETH, matching SlowMist's own reported
  "10.71 ETH" to the stated precision. Converting that at CoinGecko's
  2026-08-31 daily price gives $25,869.71, and at an intraday-interpolated
  price (from CoinGecko's hourly range data bracketing the exact block
  timestamp) gives $26,189.43 -- both 6.5-7.6% below DefiLlama's tracked
  $28,000, a gap this reconstruction could not attribute to either side
  being wrong (DefiLlama's row carries no source URL; SlowMist's own
  alert states only the ETH amount), so it is recorded as a reconciliation
  in the "Corrections to press and DefiLlama" table, not a correction.
  A live probe also found the deployed vault bytecode does not match
  several documented getters on the current `GammaStrategies/hypervisor`
  GitHub `master` branch (both revert), consistent with a 2021-era
  version predating later refactors -- flagged honestly in the entry's
  Caveats rather than asserting a specific Solidity mechanism this
  reconstruction could not confirm against the actual deployed bytecode.
  Both vaults, untouched for nearly 5 years, still hold real FLOAT
  balances today (189.66 and 871.17 FLOAT), confirming this was a live,
  unmonitored deployment, not an abandoned shell.

## 2026-09-11 (14)

- Added a 28th incident: Reddio (RedSonic Vault), Ethereum, 2026-09-05.
  Found via DefiLlama's hacks feed ("Reddio RedSonic", $22,800, "Token &
  Share Accounting" / "Incorrect Share Accounting", no source URL
  attached). The starting anchor was not a press address: Reddio's own
  official documentation (`docs.reddio.com/zkevm/staking`) independently
  names `0x4315990D9eeAFFdFAfD49958b4851F203FA1126f` as the "Deposit
  Smart Contract" behind rsvETH/rsvUSDT, and
  `0xCA9de1F80Df74331c5fcb7Eee2D05E746d47BFb2` as rsvETH itself, matching
  the vault address security-firm write-ups (ExVulSec, republished by
  coin-turk.com and others) separately named. From there this entry
  worked entirely from the chain: the exploit transaction
  (`0xe3cba90e865c6cba950ebce36a52607f51f1fd33cd9fb920c78803f19b57791a`,
  block 25,912,201) is a single contract-creation call whose raw
  bytecode itself contains `keccak256("registerErc20(address)")`
  (`0xa4a3c9ef`, computed independently, not assumed from a press quote)
  next to Lido stETH's real address and the vault's own address in the
  same byte window. A live Diamond `facets()` (EIP-2535 Loupe) call
  confirms that exact selector is a real, currently-installed function on
  one of the vault's 7 facets, one of which (the one owning this
  selector) is unverified on Blockscout. The vault's own emitted event
  (receipt log index 4, two ABI-indexed topics, no offset-guessing)
  independently confirms the asset registered was Lido stETH and names
  the new share token created,
  `0xf65e1ec6093642Ba9D439aC25AF1b767054e1558`; querying that token live
  today returns `name()` "RedSonic Vault Liquid staked Ether 2.0",
  `symbol()` "rsvstETH", `owner()` the vault itself, and `totalSupply()`
  0 (the attacker's own position was fully unwound). The vault's real
  `owner()` (`0x3786540Ec316f2383FAb2d5Cfc816C1ABDfEEf44`) does not match
  the address that actually called `registerErc20`
  (`0x39a2aee44bd9ef106917d94880a9f8f7cfaf09d5`), confirming the caller
  held no special privilege. Log order also shows the registration happened
  before the attacker's own ETH deposit into rsvETH, not after: the vault's
  own paired `Deposited`/`Withdrawn`-shaped events for that one rsvETH
  position (1,130.259297504314190519 ETH in, 1,139.513928645387068173 ETH
  out for the identical shares minted and burned) show a gain of exactly
  9.254631141072739098 ETH attributable purely to the vault's share-price
  math once stETH was registered, independent of and closely matching the
  attacker's own total realized profit below. The attacker's own EOA sent
  this transaction at nonce 0 (its first ever) and held 9.261768945208 ETH
  the instant the
  block closed, read live via `eth_getBalance` against an archive-capable
  public endpoint after `ethereum-rpc.publicnode.com` rejected that
  specific historical query as "archive"; at CoinGecko's own 2026-09-05
  historical price that is $22,747.69, within 0.23% of DefiLlama's
  tracked $22,800, a confirmation rather than a correction, so this entry
  was not added to the "Corrections to press and DefiLlama" table. Two
  read-only `eth_call` simulations, run today and touching no mainnet
  state, go beyond what any write-up reported: calling
  `registerErc20(WETH)` from a completely arbitrary, unprivileged address
  still succeeds against the vault's real, currently-deployed bytecode,
  while the identical call against an already-registered asset (stETH)
  correctly reverts with the facet's own real error string, `"Vaults:
  vToken already registered"` -- proving the bug is still live and
  unpatched as of this reconstruction, not merely a historical curiosity.

## 2026-09-11 (13)

- Added a 27th incident: Radix (Hyperlane Warp Routes), Radix + Ethereum,
  2026-08-31. This project first learned the incident existed from the
  community-run RADIX Wiki's incident page
  (`radix.wiki/contents/history/hyperlane-asset-drain-2026`), which is not
  a primary source and is not relied on for any figure in the entry. Every
  address instead comes from Hyperlane's own official GitHub deployment
  registry (`hyperlane-xyz/hyperlane-registry`, fetched live), which also
  surfaced a real bug in that registry: `ETH/ethereum-radix-deploy.yaml`'s
  own hETH component address is one Bech32m character short of the correct
  one in its own `ethereum-radix-config.yaml`, caught because the shorter
  string fails a live address check outright. Radix's own public Gateway
  API refuses ordinary "current state" reads with a `NotSyncedUpError`
  once the ledger has gone static for too long, itself an independent,
  unprompted confirmation that mainnet is still halted (state_version
  557840622 / epoch 339896 / round 102, unchanged for 10+ days), matching
  every read in this entry passing an explicit `at_ledger_state` instead.
  Per-asset supply drops for all 6 Hyperlane-bridged assets (hUSDC, hUSDT,
  hETH, hWBTC, hSOL, hBNB) are independently measured from each resource's
  own `total_supply` immediately before/after the sweep, not assumed from
  any report. The single largest hUSDC-draining transaction was found by
  filtering the Gateway API's own transaction stream by
  `affected_global_entities_filter` on the hUSDC resource address (fee
  alone turned out not to be a reliable way to single it out: several
  attack transactions carry near-identical fees, and an earlier pass of
  this project's own script ranked by fee and surfaced the wrong
  transaction before this was caught and fixed) and its own
  `BurnFungibleResourceEvent`/`SendRemoteTransferEvent`/`DispatchEvent`
  were decoded directly: 59 vaults drained of 442,985.632108 hUSDC in one
  atomic call, dispatched toward Ethereum with no authorization badge or
  proof against any of the 59 vaults. Independently cross-checking
  Ethereum mainnet's own real USDC contract for the attacker's own
  recipient address (named directly in that `SendRemoteTransferEvent`,
  never guessed) finds only 15,544.443004 USDC actually delivered so far
  -- 3.5% of what was dispatched -- while the equivalent USDT check on the
  same recipient finds 99.3% delivered, an inconsistency this project
  cannot explain from either chain's own data and reports as an open
  question rather than a conclusion. Pricing all 6 assets' drops at
  CoinGecko's 2026-08-31 historical close gives an independently
  reconstructed total of $1,251,368.54, within 0.11% of DefiLlama's
  tracked $1,249,946 for the chain-level "Radix" row, reported as a
  confirmation rather than a correction. The official fix (`radixdlt`'s
  own GitHub repos, not the wiki's paraphrase of them: `radixdlt-scrypto`
  PR #2093 / release v1.4.0, `radixdlt/babylon-node` PR #1076 / release
  v1.4.0.0-RC1) adds a kernel-level ownership check on direct method
  invocations that did not exist before, matching the drain's own
  mechanism exactly.

## 2026-09-11 (12)

- Added a 26th incident: Virtue Protocol (VUSD CDP), IOTA, 2026-08-28.
  Found via DefiLlama's hacks feed ("Virtue", $894,500, "Oracle
  Manipulation" / "Oracle Misconfiguration"), cross-checked against press
  coverage of a broader Switchboard oracle compromise affecting Aptos,
  Sui, IOTA and Movement the same day. Every package address was read
  live from Virtue's own GitHub SDK repo (`Virtue-CDP/virtue-sdk`,
  `src/constants/object.ts`), not a block explorer. The exploit
  transaction (`CaAD9SRJjuvEbNiHQcgT176kg4F8jKUTM1EneeYsd3Gd`) was found
  by paginating the CDP package's own on-chain event log for the single
  largest mint, not copied from any article: a single atomic transaction
  shows 14 distinct Switchboard oracle signers self-submitting an
  identical fake price (independently decoded to exactly $10,000,000.00
  per IOTA at the Oracle's own 9-decimal convention), a mint of
  4,942,703.659474 VUSD against 1 IOTA of real collateral (about 88.4% of
  the entire VUSD supply the instant after), and a 1,000,000 VUSD
  stability-pool deposit inside the same transaction. The subsequent
  liquidation cascade (48 raw events on-chain) resolves to exactly 47
  events / 45 distinct real users once the attacker's own 1
  wash-test liquidation is identified and excluded, matching Virtue's own
  press-relayed account on both counts exactly; the VUSD debt-cleared
  total independently reconstructs to $455,102.94, within 7 cents of
  Virtue's own 455,103 figure. A second figure, the real-user collateral's
  value at theft-day prices (≈$848,457, using each cert token's own
  historical exchange rate read at the exact object version each
  liquidation transaction used), sits much closer to DefiLlama's tracked
  $894,500 than to the face-value debt figure -- a reconciliation, not an
  error, logged in "Corrections to press and DefiLlama". Also surfaces a
  root-cause detail from Virtue's own GitHub commit history not stated in
  any press account found: a commit merged less than 24 hours before the
  exploit removed Pyth as a price source (its own Hermes endpoint had
  been persistently returning 401 Unauthorized), with the commit message
  itself stating "there is no second opinion left, so crossbar going down
  means no price at all" -- a risk the team had already named in writing
  one day before it was realized through a compromised signer rather than
  a downed feed.

## 2026-09-10 (11)

- Backfilled 8 entries that were missing despite this changelog's own
  opening line above: the 10th, 11th, 12th, 13th, 14th, 23rd, 24th, and
  25th incidents each already have a subfolder and an Index row, just
  never got a changelog line when added. One line each below, headline
  fact only, not a full retroactive narrative, since this entry is written
  well after the fact.
  - 10th: Allbridge (CCTP Forged Message), Polygon + Base, 2026-07-25 /
    08-19. Router's real loss 190,155.976393 USDC; also catches a one-day
    date error in SlowMist's own post-mortem.
  - 11th: Liquid Network, Bitcoin + Liquid, 2026-09-06 / 09-07. Range-proof
    cache-key collision in Elements; 598.50 BTC still unrecovered as of
    this reconstruction.
  - 12th: Aquifer, Solana + Ethereum, 2026-08-31 / 09-01. Arbitrary
    external call on a verified Sweeper contract; $2,418,164 at theft-day
    price.
  - 13th: Maya Protocol (MAYAChain), MAYAChain + Bitcoin + Arbitrum,
    2026-08-18. Voter-clobber bug plus an uncapped slash subsidy;
    $1,343,181.04 BTC-only floor.
  - 14th: COLDCARD (Weak Seed RNG), Bitcoin, 2026-07-30. Hardware RNG
    silently replaced by a weak software PRNG for 5+ years; first theft
    wave, $37,996,965.32, independently traced.
  - 23rd: AFX Bridge, Arbitrum + Ethereum, 2026-07-22. 5-of-7 bridge
    validator signing keys compromised; $24,150,000, matching DefiLlama
    exactly.
  - 24th: Lazy Summer Protocol, Ethereum, 2026-07-06. Donation attack on a
    zeroed-cap Ark; $6,016,632.02, DefiLlama's date is off by 29.3 hours.
  - 25th: Kelp DAO (rsETH / LayerZero DVN), Ethereum, 2026-04-18. Forged
    cross-chain message via compromised LayerZero DVN RPC nodes; this
    repo's largest incident, $273,377,225 at theft-day price against
    DefiLlama's tracked $293,000,000.
- Restructured `README.md`'s Index from a single flat table sorted by loss
  into year, then month sections, each with its own subtotal, plus a table
  of contents and a "Corrections to press and DefiLlama" section pulled out
  of the "At a glance" block. Rewrote `add_new_entry.py` and
  `check_readme_consistency.py` to match. No incident, footnote, or section
  was dropped in the restructuring.

## 2026-09-10 (10)

- Added a 22nd incident: XRP Healthcare (XRPH Wallet), XRP Ledger +
  Ethereum, 2026-09-03/09-04. Not a DeFi protocol hack in the usual
  sense: every wallet signed an ordinary, validly-signed payment of its
  own balance, and XRP Healthcare's own investigation states the XRP
  Ledger itself was not at fault. Found via xrpl.to's own published
  forensic article (an XRPL-native analytics platform, independent of
  XRP Healthcare and of any press outlet), treated only as a place to
  find addresses and transaction hashes to independently re-check, not
  as facts to repeat. Every hop of the fund flow was independently
  re-fetched live and matches the article's stated timestamps to the
  second: the collector account's own genesis transaction; its first and
  largest sweep (97,829.051309 XRP); a two-hop handoff through a NEAR
  Intents deposit address to a second XRPL wallet 9 seconds later; the
  resulting ETH landing on the attacker's Ethereum address 18 seconds
  after that (twice, for two separate legs); and the final 178 ETH to
  445,197.999216 DAI swap, confirmed via that transaction's own DAI
  Transfer event log rather than assumed from the ETH side alone. A live
  balance check today shows that exact DAI amount, to the wei, still
  sitting untouched 6 days later. This entry goes beyond the source
  article by independently paginating the collector account's entire
  transaction history from genesis (10,936 transactions), which
  independently totals 267,679.863641 XRP swept from 3,630 distinct
  addresses (within 0.006% of the article's own count) and exactly
  reproduces its "five trustlines" and "forty-five deleted accounts"
  claims. This incident is not tracked in DefiLlama's hacks feed at all.
  The underlying root-cause mechanism (the wallet app's own private-key
  generation, per the source article's unreproduced decompilation of it)
  is reported as the article's claim, not independently confirmed: no
  XRP Healthcare GitHub source repo was found to check it against
  directly (the XRPHealthcare org holds exactly one public repo,
  `.github`, not the wallet-source repo a web search's own synthesized
  answer had claimed exists).

## 2026-09-10 (9)

- Added a 21st incident: Nomic (nBTC / Osmosis allBTC), Bitcoin + Nomic +
  Osmosis, mint 2026-06-25, disclosed/halted 2026-09-07. Parked in an
  earlier round for lack of a primary source; reconsidered this round
  after Osmosis's own governance forum posted "Alloyed BTC: Restore
  backing after the nBTC incident" (an admin account, forum.osmosis.zone/t/4122)
  the same day, naming the exploit transaction, block, and frozen attacker
  address directly. Every hard number was independently re-verified
  live: the exploit transaction byte-for-byte on Nomic's own public RPC
  (25 identical forged IBC packets, code 0, gas 0, 101 events); the
  forged packet sender independently re-derived as Nomic's own ADR-028
  escrow account for transfer/channel-1 via SHA256/bech32, not copied
  from any report; the allBTC transmuter's live pool composition on 2
  independent Osmosis LCD endpoints (39.83974592 BTC of nBTC against
  70.73128010 BTC of real WBTC/cbBTC collateral, 63.97% backing,
  matching the forum post's own table); the attacker's frozen Osmosis
  balance and Nomic's own BTC reserve address balance, both confirmed
  live; and the halt's real root cause independently corroborated via a
  still-open Nomic GitHub issue (#340) unrelated to the forum post or its
  linked forensic report. Also catches a DefiLlama date/price gap:
  DefiLlama dates this incident 2026-09-09 (the disclosure date), 76 days
  after the mint's own live-confirmed timestamp of 2026-06-25, and its
  $3,150,000 figure tracks the full counterfeit mint at a current BTC
  price rather than the theft-day rate this entry uses instead for the
  still-unbacked portion ($2,429,809.11).

## 2026-09-10 (8)

- Added a 20th incident: Ostium (PrivatePriceUpKeep Compromise), Arbitrum,
  2026-07-15. Started from Ostium's own Immunefi bug-bounty scope page
  (immunefi.com/bug-bounty/ostium/scope/), whose embedded, self-maintained
  contract registry names the Vault and PrivatePriceUpKeep addresses
  directly and states verbatim that registered keepers/forwarders are
  "assumed to be trusted and operating correctly", independently
  confirming the trust model a compromised forwarder signer defeated. One
  candidate address from a secondary Ostium documentation page (with a
  single wrong hex digit) was caught and discarded after `eth_getCode`
  showed it had no bytecode, a caution about AI-assisted page
  summarization inventing plausible-looking hex strings. Scanning the
  Vault's own USDC Transfer log across the full incident window
  (block range located by binary search on live timestamps) independently
  found the same 8 transactions a third-party forensic writeup (rekt.news)
  separately names, spanning exactly 329 seconds, matching that writeup's
  stated duration to the second. 7 of the 8 (excluding a small "test"
  cycle) sum to $23,752,641.68, within 0.0004% of Ostium's own final
  $23,752,746 figure, reconciling three earlier, conflicting press
  estimates ("$18M", "~$22M", "~$24M") down to essentially Ostium's own
  number, independently derived from the Vault's own event log, not
  copied from any of them.

## 2026-09-10 (7)

- Added a 19th incident: Across Protocol (Solana Event Spoofing), Solana +
  Ethereum, 2026-07-17. Started from Across's own merged GitHub fix
  (across-protocol/sdk PR #1486), whose regression test names one
  "mainnet exploit transaction" in its own code comment. Independently
  fetched that transaction live from Solana mainnet and decoded its raw
  instruction bytes: the first 8 bytes exactly match
  sha256("global:get_unsafe_deposit_id")[:8], independently computed here,
  proving the exploit abused the SpokePool's own read-only
  get_unsafe_deposit_id instruction, not a genuine emitted event (whose
  real Anchor CPI tag, sha256("anchor:event")[:8] byte-reversed, was also
  independently computed and confirmed absent). The forged payload
  decodes to an outputToken of Ethereum's real USDC contract address and
  an inputAmount of 4,113,882.210137, matching the fix's own "~$4.1M"
  description. Press/DefiLlama's $4.5M gross-loss figure (zero user funds
  lost, Risk Labs' own relayer absorbed it) is reported as sourced, not
  independently re-derived fill-by-fill. A separate, smaller side-effect
  of the same incident is fully re-derived instead: a stranded relayer's
  (CBG4) off-protocol compensation, both legs (Ethereum + Solana)
  independently matched to the microdollar and to the second against an
  unmerged but fully-detailed recovery-script PR from Across's own
  contracts repo.

## 2026-09-10 (6)

- Added an 18th incident: Verus-Ethereum Bridge (Forged Proof), Ethereum +
  Verus, 2026-05-17. Started from VerusCoin's own Verus-Mobile wallet repo
  (github.com/VerusCoin/Verus-Mobile), which hardcodes the bridge's
  mainnet Delegator contract address, independently confirmed as a
  verified Ethereum contract whose own source (verified 2024-12-01, over
  a year before the exploit) matches VerusCoin's public
  Verus-Ethereum-Contracts repo structure. One transaction, cross-checked
  byte-for-byte across 3 independent RPC endpoints, moved 103.5677 tBTC,
  147,658.84 USDC, and 1,625.3669 ETH from that contract to one attacker
  address; at CoinGecko's theft-day prices that totals $11,775,898.10,
  about 2.4% above DefiLlama's own tracked $11,500,000 for the same date.
  VerusCoin's own GitHub release notes (v1.2.17, 2026-07-03) independently
  corroborate the date and scope, stating the network lost "about 26.6%"
  of its ETH/tBTC bridge reserves. Also confirms and itemizes (without
  re-pricing) a second, technically distinct exploit against the same
  contract on 2026-07-23, and catches a press claim (Blockaid, via
  cryptotimes.io) that both exploits reused the same unpatched bug: per
  VerusCoin's own official writeup, they were two different root causes.

## 2026-09-10 (5)

- Added a 17th incident: MORE Markets (Ankr ankrFLOW E-Mode), Flow EVM,
  2026-08-31. Started from MORE Markets' own GitHub deployment docs
  (Pool, WFLOW, and ankrFLOW addresses), confirmed all three live on Flow
  EVM mainnet, then located the exploit by scanning the Pool's own event
  log for the WFLOW/ankrFLOW reserve across the full incident window
  rather than starting from a transaction hash found in press. Found
  exactly one transaction standing apart from routine activity: 2 Borrow
  events on the WFLOW reserve totaling 15,488,124.145039 WFLOW,
  independently cross-checked against the underlying token's own Transfer
  events (a different event on a different contract, same total to the
  wei). At CoinGecko's own theft-day price this is $415,398.47, within
  1.32% of DefiLlama's own tracked $410,000 for this incident (tracked as
  "Ankr", not "MORE Markets"). This also corrects a widely-repeated
  Blockaid "$9.3M" press estimate: no other Pool activity on either
  reserve anywhere in the full incident window comes close to that
  figure, roughly 22x the reconstructed total.

## 2026-09-10 (4)

- Added a 16th incident: Avici (Rain Card Collateral), Solana, 2026-08-28.
  Started from the attacker wallet press named and independently
  confirmed it live: its earliest on-chain activity (13:40:41 UTC) and the
  earliest transaction touching its own USDC loot account (16:49:48 UTC)
  both match press's separately-stated timestamps to the second. Decoded
  the `WithdrawCollateralAsset` / `AddCollateralAdmin` / `SubmitSignatures`
  instruction sequence directly from raw program logs and found 3
  separately-deployed program addresses running the same code, not the 1
  fixed collateral program and 1 fixed authorization program an initial,
  smaller sample first suggested; all 3 programs' own on-chain upgrade
  records show a coordinated patch within a 4.5-minute window, about
  55-60 minutes after the attacker's last transaction, independently
  timing a fix press only described as happening "following the attack".
  One press figure did not hold up: this project's own live count found
  21,405 signatures sent by the attacker wallet, not the 14,672 the
  press figure states, left as an open discrepancy. The $500,859.22 loss
  total is reported as sourced (Avici's own figure, matching DefiLlama
  exactly), not independently re-derived: a reproducible 35-transaction
  sample attempt over-estimated it by about 75%, too high a variance to
  trust, reported as an inconclusive recomputation rather than adopted
  silently.

## 2026-09-10 (3)

- Added a 15th incident: Gravity Bridge denom-poisoning (Ethereum +
  Osmosis + Gravity Chain, 2026-05-30). Independently reconstructed from
  Gravity Bridge's own GitHub-documented contract address; decoded the
  fabricated Cosmos denom string directly from the exploit's own
  on-chain event data and cross-checked it live against Osmosis's own
  tokenfactory state (4-of-4 match across two unrelated chains).
  Independently derived loss ($5,397,931.45) lands within 0.04% of
  DefiLlama's tracked $5.4M, but this entry's own decode of the raw
  event data contradicts DefiLlama's "Key Compromise" classification for
  this incident: every validator signature was genuine, the registry was
  poisoned via a permissionless function call, not a compromised key.

## 2026-09-10 (2)

- Added a 9th incident: Cosmos EVM shared staking-precompile
  underflow/overflow (MANTRA/TAC/KiiChain, plus 3 unnamed chains).
  Independently reconstructed against each named chain's live RPC,
  catching a citation error in Cosmos Labs' own official post-mortem
  along the way (wrong block number cited for the KiiChain anchor
  transaction). Cumulative loss across all 9 incidents: $35,237,493.

## 2026-09-10

- Automated review pass: translated the remaining French
  `registre_hypotheses.csv` files (all 7 subfolders that have one) to
  English, fixed `add_new_entry.py`'s `REGISTRE_HEADER` so newly
  scaffolded entries use the same English header, added a "Suggest an
  incident" note, an author cross-linking line, a root-level Disclaimer
  section, and this changelog with the accompanying Watch/Releases
  guidance in `README.md`.
- Translated `README.md` and `add_new_entry.py` to English.

## 2026-09-09

- Consolidated 8 previously separate postmortem repos into this single
  indexed repo: sandbox-oft-delegate-hijack, moonwell-mamo-oracle,
  balancer-v1-rounding, termfinance-metavault-governance,
  notional-v1-escrow, ajna-liquidation, cozy-v2-optimism, tectonic-cronos.
