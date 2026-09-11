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
[multisig-overlap-showcase](https://github.com/RealSpap/multisig-overlap-showcase),
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
| Incidents covered | 26, independently reconstructed on-chain, see the index for detail |
| Cumulative loss, recomputed | About $477.4M across the 26 incidents ($477,364,727 exactly, sum of the figures in the index below). At least one entry is a known floor, so the real total is higher. |
| Corrections made | 18 entries below correct, reconcile, or newly surface a press or DefiLlama figure, label, date, or classification (14 corrections, 3 reconciliations, 1 discovery not previously tracked by DefiLlama at all). See Corrections to press and DefiLlama below. |
| Method | Each subfolder keeps its original Python reconstruction script, its `registre_hypotheses.csv` falsification registry, and its script's raw output in `resultats_*.txt`, so every figure below can be checked against the file that produced it |
| License | MIT across all 26 entries, single author (s_pap, 2026) |

## Table of contents

- [Index](#index)
<!-- TOC:YEARS:START -->
  - [2026](#2026)
    - [September 2026 (current month)](#september-2026-current-month)
    - [August 2026](#august-2026)
    - [July 2026](#july-2026)
    - [June 2026](#june-2026)
    - [May 2026](#may-2026)
    - [April 2026](#april-2026)
<!-- TOC:YEARS:END -->
- [Corrections to press and DefiLlama](#corrections-to-press-and-defillama)
- [Structure](#structure)
- [Adding a new incident](#adding-a-new-incident)
- [Scope](#scope)
- [Suggest an incident](#suggest-an-incident)
- [Limits](#limits)
- [Disclaimer](#disclaimer)
- [License](#license)

## Index

Grouped by year, then by month, most recent first. Within each month,
sorted by recomputed loss, descending. Every year gets its own subtotal
(sum of its months), every month gets its own subtotal (sum of its rows),
and both roll up into the cumulative total stated in "At a glance" above.
The current month, the month the most recent incident falls in, is marked
below so recent activity is easy to tell apart from historical entries.

The "Type/Mechanism" column reflects what the on-chain reconstruction
actually found, not the incident's press label. The "Category" column is
this project's own classification, for scanning convenience, not a label
sourced from DefiLlama or press.

Loss ($) legend: **≥** confirmed floor, the real loss may be higher.
**≈** independently recomputed, not exact to the cent. No symbol,
exact figure decoded from source data.

### 2026

**2026 total: $477,364,727** across 26 incidents (6 months, April through September). At least one entry this year is a known floor, so the true total is higher.

#### September 2026 (current month)

| Protocol | Date | Loss ($) | Chain | Category | Type/Mechanism | Link |
|---|---|---|---|---|---|---|
| Liquid Network | 2026-09-06 / 09-07 | ≥ 46,568,719 [^liquid-rangeproof-cache] | Bitcoin + Liquid | Bridge | Range-proof cache-key collision in Elements let a peg-out register as fully backed; the federation's real multisig then genuinely signed the BTC release | [liquid-rangeproof-cache/](liquid-rangeproof-cache/) |
| Notional Finance (V1 Escrow) | 2026-09-03 / 09-04 | 1,727,782 [^notional] | Ethereum | Rounding/Math-Bug | uint128 overflow/downcast in the legacy V1 Escrow contract's collateral valuation | [notional-v1-escrow/](notional-v1-escrow/) |
| XRP Healthcare (XRPH Wallet) | 2026-09-03 / 09-04 | ≥ 445,198 [^xrph-wallet-key-compromise] | XRP Ledger + Ethereum | Key-Compromise | Mass wallet-side private-key compromise (not an XRPL protocol bug) swept thousands of externally-owned wallets to one collector, laundered via NEAR Intents into Ethereum and settled as DAI | [xrph-wallet-key-compromise/](xrph-wallet-key-compromise/) |
| Cozy V2 | 2026-09-02 / 09-07 | 174,311 [^cozy] | Optimism | Oracle | False answers to the UMA Optimistic Oracle left uncontested during its 5-day dispute window | [cozy-v2-optimism/](cozy-v2-optimism/) |

**September 2026 subtotal: $48,916,010** across 4 incidents. Includes 2 known floor figures (Liquid Network, XRP Healthcare (XRPH Wallet)), so the true total is higher.

#### August 2026

| Protocol | Date | Loss ($) | Chain | Category | Type/Mechanism | Link |
|---|---|---|---|---|---|---|
| Moonwell (MAMO market) | 2026-08-27 | ≈ 9,131,000 [^moonwell] | Base | Donation-Attack | Donation attack on an illiquid market's exchange rate, combined with collateral/oracle manipulation | [moonwell-mamo-oracle/](moonwell-mamo-oracle/) |
| Term Finance (Meta Vault) | 2026-08-17 / 08-23 | ≈ 8,500,000 [^termfinance] | Ethereum | Governance | Hijacked governance: a proposal self-voted by a fresh wallet through an attacker-deployed executor, normal 6-day delay elapsed with no veto | [termfinance-metavault-governance/](termfinance-metavault-governance/) |
| Tectonic | 2026-08-30 | ≈ 8,300,000 [^tectonic] | Cronos | Donation-Attack | Donation attack (recursive collateral minting then direct donations to the market contract) inflating an exchange rate, massive borrowing against the inflated collateral, followed by a chain rollback | [tectonic-cronos/](tectonic-cronos/) |
| Cosmos EVM (MANTRA / TAC / KiiChain) | 2026-08-20 / 08-22 | ≥ 5,720,000 [^cosmos-evm-vesting-underflow] | MANTRA + TAC + KiiChain (+ 3 unnamed Cosmos EVM chains) | Rounding/Math-Bug | Underflow then overflow of the native balance in a shared Cosmos EVM staking precompile | [cosmos-evm-vesting-underflow/](cosmos-evm-vesting-underflow/) |
| Aquifer | 2026-08-31 / 09-01 | ≈ 2,418,164 [^aquifer-sweeper-arbitrary-call] | Solana + Ethereum | Access-Control | Arbitrary external call on a verified cross-chain Sweeper contract redirected swept funds to the attacker's own address | [aquifer-sweeper-arbitrary-call/](aquifer-sweeper-arbitrary-call/) |
| Maya Protocol (MAYAChain) | 2026-08-18 | ≥ 1,343,181 [^mayachain-cacao-slash-drain] | MAYAChain + Bitcoin + Arbitrum | Access-Control | Voter-clobber misrouted a multi-message deposit, an uncapped theft-slash subsidy then credited phantom CACAO to a near-empty pool, drained by a single-sided add/withdraw and swapped out to Bitcoin | [mayachain-cacao-slash-drain/](mayachain-cacao-slash-drain/) |
| Virtue Protocol (VUSD CDP) | 2026-08-28 | ≈ 848,457 [^virtue-iota-switchboard-oracle] | IOTA | Oracle | All 14 Switchboard oracle signing keys for the IOTA price queue compromised, self-submitted a fake $10,000,000 IOTA price inside the same transaction that minted 4.94M VUSD against 1 IOTA of real collateral, then a crashed price triggered a real-user liquidation cascade | [virtue-iota-switchboard-oracle/](virtue-iota-switchboard-oracle/) |
| Ajna Finance | 2026-08-28 / 08-29 | ≈ 775,400 [^ajna] | Ethereum | Rounding/Math-Bug | Liquidation-math exploit (Kick) on pools deployed through a factory the protocol never documented | [ajna-liquidation/](ajna-liquidation/) |
| Sandbox (SAND / OFT) | 2026-08-21 / 08-22 | ≥ 675,000 [^sandbox] | Base + BSC + Ethereum | Bridge | LayerZero delegate hijack via a legacy approveAndCall primitive, a composition bug, not a compromised key | [sandbox-oft-delegate-hijack/](sandbox-oft-delegate-hijack/) |
| Avici (Rain Card Collateral) | 2026-08-28 | ≈ 500,859 [^avici-rain-collateral-withdraw] | Solana | Access-Control | Forged dual-signature authorization (Ed25519 instruction-offset reuse) on a shared Rain card-collateral program let one attacker-controlled signature satisfy a two-signer withdrawal check | [avici-rain-collateral-withdraw/](avici-rain-collateral-withdraw/) |
| MORE Markets (Ankr ankrFLOW E-Mode) | 2026-08-31 | ≈ 415,398 [^more-markets-ankrflow-emode] | Flow EVM | Access-Control | Ankr's ankrFLOW liquid-staking contract let unbacked ankrFLOW be minted via a recursive stake/restake loop, supplied as E-Mode collateral to drain MORE Markets' WFLOW reserve | [more-markets-ankrflow-emode/](more-markets-ankrflow-emode/) |
| Balancer V1 (legacy pools) | 2026-08-30 / 08-31 | ≥ 234,000 [^balancer] | Ethereum | Rounding/Math-Bug | Rounding error on unmaintained V1 pools, repeated 1-satoshi joins | [balancer-v1-rounding/](balancer-v1-rounding/) |

**August 2026 subtotal: $38,861,459** across 12 incidents. Includes 4 known floor figures (Cosmos EVM (MANTRA / TAC / KiiChain), Maya Protocol (MAYAChain), Sandbox (SAND / OFT), Balancer V1 (legacy pools)), so the true total is higher.

#### July 2026

| Protocol | Date | Loss ($) | Chain | Category | Type/Mechanism | Link |
|---|---|---|---|---|---|---|
| COLDCARD (Weak Seed RNG) | 2026-07-30 | ≥ 37,996,965 [^coldcard-rng-seed-theft] | Bitcoin | Key-Compromise | Build-flag/linker bug silently swapped the hardware RNG for a weak software PRNG in seed generation for 5+ years; resulting low-entropy wallets brute-forced and swept, first wave traced end to end | [coldcard-rng-seed-theft/](coldcard-rng-seed-theft/) |
| AFX Bridge | 2026-07-22 | ≈ 24,150,000 [^afx-bridge-validator-key-compromise] | Arbitrum + Ethereum | Bridge | 5-of-7 threshold bridge-validator signing keys compromised (social-engineering campaign attributed by Halborn to DPRK-linked UNC4899/TraderTraitor) authorized a fraudulent USDC withdrawal from the bridge's Arbitrum custody | [afx-bridge-validator-key-compromise/](afx-bridge-validator-key-compromise/) |
| Ostium (PrivatePriceUpKeep Compromise) | 2026-07-15 | ≈ 23,752,642 [^ostium-oracle-forwarder-compromise] | Arbitrum | Oracle | Compromised off-chain oracle-signer credential pushed self-authored BTC/USD price reports through a trusted PrivatePriceUpKeep forwarder, extracting real USDC from the counterparty vault | [ostium-oracle-forwarder-compromise/](ostium-oracle-forwarder-compromise/) |
| Lazy Summer Protocol | 2026-07-06 | ≈ 6,016,632 [^lazy-summer-stale-ark-donation] | Ethereum | Donation-Attack | Donation attack: a zeroed-cap Ark, still summed in totalAssets() despite being blocked from new deposits, was donated an over-valued token to inflate vault share price ~9.5%, redeemed after a flash-loan-funded deposit at the honest price | [lazy-summer-stale-ark-donation/](lazy-summer-stale-ark-donation/) |
| Across Protocol (Solana Event Spoofing) | 2026-07-17 | ≈ 4,500,000 [^across-solana-event-spoofing] | Solana + Ethereum | Bridge | Missing Anchor CPI event-discriminator check let a wrapper program forge FundsDeposited events via a read-only instruction, so the relayer paid real funds against Solana deposits that never escrowed anything | [across-solana-event-spoofing/](across-solana-event-spoofing/) |
| Allbridge (CCTP Forged Message) | 2026-07-25 / 08-19 | ≈ 190,156 [^allbridge-cctp-forged-message] | Polygon + Base | Bridge | Forged Circle CCTP message accepted without checking the mint recipient, unlocked with a self-funded Aave flash loan to match the fabricated credit | [allbridge-cctp-forged-message/](allbridge-cctp-forged-message/) |

**July 2026 subtotal: $96,606,395** across 6 incidents. Includes 1 known floor figure (COLDCARD (Weak Seed RNG)), so the true total is higher.

#### June 2026

| Protocol | Date | Loss ($) | Chain | Category | Type/Mechanism | Link |
|---|---|---|---|---|---|---|
| Nomic (nBTC / Osmosis allBTC) | 2026-06-25 | ≈ 2,429,809 [^nomic-nbtc-ibc-selfmint] | Bitcoin + Nomic + Osmosis | Bridge | Forged IBC sender field made a MsgTransfer appear to originate from the channel's own escrow account; a balance-map aliasing bug let the debit and credit resolve to the same key, so the escrow was never drawn down while Osmosis still minted real nBTC vouchers against the unconsumed packet | [nomic-nbtc-ibc-selfmint/](nomic-nbtc-ibc-selfmint/) |

**June 2026 subtotal: $2,429,809** across 1 incident.

#### May 2026

| Protocol | Date | Loss ($) | Chain | Category | Type/Mechanism | Link |
|---|---|---|---|---|---|---|
| Verus-Ethereum Bridge | 2026-05-17 | ≥ 11,775,898 [^verus-ethereum-bridge-forged-proof] | Ethereum + Verus | Bridge | Forged proof: an attacker-crafted output, provable by real Verus notarizations, was interpreted by the Ethereum bridge contract as a different output type than the Verus daemon intended, releasing funds with no matching real export | [verus-ethereum-bridge-forged-proof/](verus-ethereum-bridge-forged-proof/) |
| Gravity Bridge | 2026-05-30 | ≈ 5,397,931 [^gravity-bridge-denom-poisoning] | Ethereum + Osmosis + Gravity Chain | Bridge | Permissionless deployERC20() plus a missing registry collision check let a fabricated Cosmos denom string embed a real custody token address, poisoning the bridge's ERC20 lookup | [gravity-bridge-denom-poisoning/](gravity-bridge-denom-poisoning/) |

**May 2026 subtotal: $17,173,829** across 2 incidents. Includes 1 known floor figure (Verus-Ethereum Bridge), so the true total is higher.

#### April 2026

| Protocol | Date | Loss ($) | Chain | Category | Type/Mechanism | Link |
|---|---|---|---|---|---|---|
| Kelp DAO (rsETH / LayerZero DVN) | 2026-04-18 | ≈ 273,377,225 [^kelpdao-rseth-layerzero-rpc-spoofing] | Ethereum | Bridge | Compromised LayerZero RPC nodes plus a DDoS-forced DVN failover let a forged cross-chain message pass a 1-of-1 verifier, minting real rsETH against a burn that never happened on the claimed source chain (Unichain) | [kelpdao-rseth-layerzero-rpc-spoofing/](kelpdao-rseth-layerzero-rpc-spoofing/) |

**April 2026 subtotal: $273,377,225** across 1 incident.

[^liquid-rangeproof-cache]: A range-proof cache-key collision in Elements let a peg-out register as fully backed; the federation's real multisig then genuinely signed 4,007.82220180 BTC out of its reserve on 2026-09-06, 3,400.00000000 BTC came back the next day, and 598.50041569 BTC remains unrecovered as of this reconstruction, the floor reported here. Also catches a 2-hour timestamp error in Liquid Network's own incident report (block 4,050,336's real time is 13:53:10 UTC, not the stated 15:53:10 UTC). DefiLlama tracks this as $320,000,000, the gross pre-return figure. See `liquid-rangeproof-cache/README.md`.
[^notional]: 69,257.3727 DAI plus 1,658,524.8641 USDC, decoded directly from the extraction transaction's `Transfer` events, totaling $1,727,782.2368, matching DefiLlama's `amount` field exactly, even though that feed labels the incident "Notional V2" when the exploited contract is actually V1. See `notional-v1-escrow/README.md`.
[^xrph-wallet-key-compromise]: A mass wallet-side private-key compromise, not an XRPL protocol bug, swept thousands of externally-owned wallets to one collector; a full independent pagination of the collector account (10,936 transactions) totals 267,679.863641 XRP, within 0.006% of the source article's own figure, and the final 445,197.999216 DAI leg is confirmed still sitting untouched 6 days later. Not tracked in DefiLlama's hacks feed at all. See `xrph-wallet-key-compromise/README.md`.
[^cozy]: 174,311.006968 USDC.e, verified two independent ways, exceeds both Cozy's own published figure ($170,186) and DefiLlama's ($163,326, which matches exactly one of the two claim transactions). See `cozy-v2-optimism/README.md`.
[^moonwell]: Debt still unrecovered as of August 28, 2026 per Moonwell's own official postmortem (595 liquidations on $11.03M gross borrowed, $9.131M remained uncovered). Press (PeckShield/CertiK) reported about $8.7M. See `moonwell-mamo-oracle/README.md`.
[^termfinance]: Press figure, consistent with the amounts independently verified on-chain (2,841.7435 WETH plus 1,679,639.290442 USDC swept and converted to DAI). No dollar total was independently recomputed in the source repo. See `termfinance-metavault-governance/README.md`.
[^tectonic]: Loss confirmed unrecoverable after Cronos validators rolled back roughly 11,000 blocks; over $120M had been borrowed against the inflated collateral, but most of that debt was wiped out by the rollback itself. See `tectonic-cronos/README.md` and the linked Dune dashboard.
[^cosmos-evm-vesting-underflow]: Cosmos Labs' own post-mortem states $5.72M realized across 6 chains; independently reconstructed against each named chain's live RPC, matching the post-mortem's own figures to the block and second, and catching a citation error in the post-mortem itself (the KiiChain anchor transaction sits at block 9355107, not the 9355102 stated). DefiLlama tracks this as 3 separate rows summing to $17.2M, a real, disclosed gap against the primary source's own figure, not resolved here. See `cosmos-evm-vesting-underflow/README.md`.
[^aquifer-sweeper-arbitrary-call]: An arbitrary external call on a verified cross-chain Sweeper contract redirected 1000.7955696018159 ETH to the attacker; at theft-day price that is $2,418,164, about 2% below DefiLlama's tracked $2,469,729, and re-pricing the same amount one day later, when the attacker actually moved it, lands within 0.05% of DefiLlama's figure. See `aquifer-sweeper-arbitrary-call/README.md`. External source: https://api.llama.fi/hacks.
[^mayachain-cacao-slash-drain]: An uncapped theft-slash subsidy credited phantom CACAO to a near-empty pool after a voter-clobber bug; the independently re-derived, BTC-only loss is $1,343,181.04, about 21% below DefiLlama's tracked $1,700,000, a gap traced to a specific, still-unconverted 8.87M CACAO balance sitting in the attacker's own wallet. See `mayachain-cacao-slash-drain/README.md`. External source: https://gitlab.com/mayachain/mayanode/-/merge_requests/835.
[^ajna]: Press and DefiLlama figure for all 7 affected pools combined. Only one extraction is confirmed transaction-by-transaction (about $121,800 on the cbETH/WETH pool); the rest rests on a before/after balance delta, weaker evidence. See `ajna-liquidation/README.md`.
[^sandbox]: Press figure, Ethereum leg only. The independent reconstruction finds a real amount about 5.2x higher (405.828879423128923336 gross WETH across Base and Ethereum), but the source repo declines to assign a dollar total to that native-unit figure. See `sandbox-oft-delegate-hijack/README.md`.
[^avici-rain-collateral-withdraw]: A forged dual-signature check on a shared Rain-authored Solana card-collateral program let an attacker register as an extra collateral admin and withdraw held balances directly. The $500,859.22 total is Avici's own figure, matching DefiLlama's exactly; this project's own attempt to independently re-derive it was inconclusive (a reproducible sample over-estimated it by about 75%), so the total is reported as sourced, not re-derived. See `avici-rain-collateral-withdraw/README.md`. External source: https://crypto.news/rain-contract-exploit-drains-1-1m-from-card-users/.
[^more-markets-ankrflow-emode]: Ankr's ankrFLOW liquid-staking contract let unbacked ankrFLOW be minted via a recursive stake/restake loop, then supplied as E-Mode collateral to drain MORE Markets' WFLOW reserve. One transaction's Borrow events total $415,398.47, within 1.32% of DefiLlama's own tracked $410,000 (listed under "Ankr", not "MORE Markets"); Blockaid's initial "$9.3M" press estimate does not hold up against a full scan of the incident window. See `more-markets-ankrflow-emode/README.md`.
[^balancer]: DefiLlama and press figure for 1 pool only. The independent reconstruction finds the same wallet drained 4 separate pools the same night; the 3 additional pools are only quantified in kind, for lack of a reliable historical price feed for those tokens. See `balancer-v1-rounding/README.md`.
[^coldcard-rng-seed-theft]: A build-flag/linker bug silently swapped the hardware RNG for a weak software PRNG in seed generation for 5+ years. The first theft wave, independently reconstructed against Bitcoin mainnet, swept 594.47728031 BTC ($37,996,965.32 at theft-day price) from 505 victim addresses; DefiLlama and TRM Labs track a larger, explicitly preliminary total (about 1,816 BTC across 4 waves), of which only this first wave, about a third, is independently verified here. See `coldcard-rng-seed-theft/README.md`. External source: https://blog.coinkite.com/coldcard-mk3-seed-generation-warning/.
[^afx-bridge-validator-key-compromise]: 24,150,000.000000 USDC moved in one transaction, matching DefiLlama's tracked $24,150,000 exactly. See `afx-bridge-validator-key-compromise/README.md`.
[^ostium-oracle-forwarder-compromise]: A compromised off-chain oracle-signer credential pushed self-authored price reports through a trusted forwarder. 7 of 8 payout transactions sum to $23,752,641.68, within 0.0004% of Ostium's own final figure ($23,752,746), reconciling three earlier, conflicting press estimates ($18M, ~$22M, ~$24M) down to essentially Ostium's own number. See `ostium-oracle-forwarder-compromise/README.md`. External source: https://rekt.news/ostium-rekt.
[^lazy-summer-stale-ark-donation]: A zeroed-cap Ark, still summed in `totalAssets()` despite being blocked from new deposits, was donated an over-valued token to inflate vault share price; the attacker's realized payout is $6,016,632.02, within 0.39% of both Summer.fi's own and DefiLlama's combined figures. DefiLlama's own hacks feed dates this incident 2026-07-05T00:00:00Z, 29.3 hours before the transaction's own live block timestamp, a real date error the amount and classification don't share. See `lazy-summer-stale-ark-donation/README.md`. External source: https://blog.summer.fi/lazy-summer-usdc-vault-exploit-post-mortem-what-happened-and-what-comes-next/.
[^across-solana-event-spoofing]: A missing Anchor CPI event-discriminator check let a wrapper program forge deposit events via a read-only instruction; the forged payload matches Across's own merged-fix regression test's "about $4.1M" description. Press/DefiLlama's $4.5M gross-loss figure is reported as sourced, not independently re-derived fill-by-fill; a separate, smaller side effect (one stranded relayer's off-protocol compensation) is fully re-derived instead. See `across-solana-event-spoofing/README.md`.
[^allbridge-cctp-forged-message]: A forged Circle CCTP message, accepted without checking the mint recipient, unlocked with a self-funded Aave flash loan. The Router's real loss is 190,155.976393 USDC; DefiLlama tracks this incident at $191,000, a figure closer to the Router's gross pre-attack balance than to either the real loss or the attacker's net profit. Also catches a one-day date error in SlowMist's own published post-mortem. See `allbridge-cctp-forged-message/README.md`. External source: https://slowmist.medium.com/a-cross-chain-attack-spanning-one-month-analysis-of-the-allbridge-hack-32a6183bce08.
[^nomic-nbtc-ibc-selfmint]: A forged IBC sender field made a transfer appear to originate from the channel's own escrow account, so the escrow was never drawn down while Osmosis still minted real nBTC vouchers. DefiLlama dates this incident 2026-09-09 (the disclosure date), 76 days after the mint's own live-confirmed timestamp of 2026-06-25, and its $3,150,000 figure prices the full counterfeit mint at a current BTC rate rather than the theft-day rate this entry uses instead ($2,429,809.11 for the still-unbacked portion). See `nomic-nbtc-ibc-selfmint/README.md`.
[^verus-ethereum-bridge-forged-proof]: A forged output, provable by real Verus notarizations, was interpreted by the Ethereum bridge contract as a different output type than intended, releasing funds with no matching real export. One transaction moved $11,775,898.10 at theft-day prices, about 2.4% above DefiLlama's tracked $11,500,000. Also catches a press mechanism claim: VerusCoin's own official writeup states this and a second 2026-07-23 exploit against the same contract shared only a general bug category, not the same unpatched bug some press claimed. See `verus-ethereum-bridge-forged-proof/README.md`.
[^gravity-bridge-denom-poisoning]: A permissionless `deployERC20()` plus a missing registry collision check let a fabricated Cosmos denom string embed a real custody token address, poisoning the bridge's ERC20 lookup. $5,397,931.45 moved, within 0.04% of DefiLlama's tracked $5.4M, but this entry's own decode of the raw event data contradicts DefiLlama's "Key Compromise" classification: every validator signature on the payout batches was genuine, the registry was poisoned via a missing check, no key was compromised. See `gravity-bridge-denom-poisoning/README.md`. External source: https://rekt.news/gravity-bridge-rekt.
[^kelpdao-rseth-layerzero-rpc-spoofing]: Compromised LayerZero DVN RPC nodes plus a DDoS-forced failover let a forged cross-chain message pass a 1-of-1 verifier; the exploit transaction moved exactly 116,500 rsETH. At theft-day price that is $273,377,225, about 6.7% below DefiLlama's tracked $293,000,000; a second, independently-derived cross-check via Kelp's own on-chain oracle backing rate instead gives $301,716,067, bracketing both figures from the other side. See `kelpdao-rseth-layerzero-rpc-spoofing/README.md`. External sources: https://layerzero.network/blog/kelpdao-incident-statement, https://api.llama.fi/hacks.
[^virtue-iota-switchboard-oracle]: All 14 Switchboard oracle signing keys for Virtue's IOTA price queue were compromised and, in one atomic transaction, self-submitted a fake $10,000,000 IOTA price, minted 4,942,703.659474 VUSD against 1 IOTA of real collateral, and seeded the stability pool with 1,000,000 of it; the price was then crashed, triggering 47 real-user liquidations (45 distinct users) that cleared $455,102.94 of VUSD debt (matching Virtue's own $455,103 figure) against real-user collateral independently valued at ≈$848,457 at theft-day prices, closer to DefiLlama's tracked $894,500. See `virtue-iota-switchboard-oracle/README.md`. External source: https://cryptoslate.com/cross-chain-oracle-compromise-triggers-liquidations-and-frozen-vaults-across-multiple-defi-networks/.

## Corrections to press and DefiLlama

Every figure in the Index above is recomputed from each subfolder's own
source files, then checked against whatever press or DefiLlama already
published. The 18 rows below are the cases where that check turned up a
real gap: a wrong number, a wrong label, a wrong date, a wrong
classification, or (for Aquifer, Maya Protocol, and Virtue Protocol) a
reconciled gap neither side is really "wrong" about, or (for XRP
Healthcare) an incident DefiLlama does not track at all. Full detail,
including the exact transactions and event logs behind each figure, lives
in the linked subfolder; this table gives the headline gap only.

| Incident | What press/DefiLlama got wrong | What this repo found | Link |
|---|---|---|---|
| Sandbox (SAND / OFT) | Press figure covers the Ethereum leg only | Real amount is about 5.2x higher, 405.83 gross WETH across Base and Ethereum, though no dollar total is assigned for lack of a reliable native-unit conversion | [sandbox-oft-delegate-hijack/](sandbox-oft-delegate-hijack/) |
| Balancer V1 (legacy pools) | DefiLlama and press figure cover 1 pool only | The same wallet drained 4 pools the same night; the other 3 are quantified only in kind, for lack of a price feed | [balancer-v1-rounding/](balancer-v1-rounding/) |
| Notional Finance (V1 Escrow) | DefiLlama's own feed labels the exploited contract "V2" | The exploited contract is actually V1; the dollar amount itself matches DefiLlama exactly | [notional-v1-escrow/](notional-v1-escrow/) |
| Cozy V2 | Cozy's own figure ($170,186) and DefiLlama's ($163,326, exactly one of two claim transactions) both undercount | Verified on-chain total is $174,311.01, confirmed two independent ways | [cozy-v2-optimism/](cozy-v2-optimism/) |
| Cosmos EVM (MANTRA / TAC / KiiChain) | Cosmos Labs' own post-mortem cites the wrong block number for the KiiChain anchor transaction | The real block is 9355107, not 9355102, confirmed on two RPC endpoints | [cosmos-evm-vesting-underflow/](cosmos-evm-vesting-underflow/) |
| Allbridge (CCTP Forged Message) | SlowMist's own post-mortem states the wrong date (July 26); DefiLlama's $191,000 conflates 3 different figures into one | The exploit happened July 25; Router loss, attacker profit, and gross balance are 3 separate numbers ($190,156 real loss, $189,752 net profit, $191,000-ish gross balance) | [allbridge-cctp-forged-message/](allbridge-cctp-forged-message/) |
| Liquid Network | The project's own incident report cites 15:53:10 UTC for the exploit block | That block's own chain-recorded timestamp is 13:53:10 UTC, two hours earlier; this entry also reports the still-missing floor (598.50 BTC) rather than DefiLlama's pre-return gross figure | [liquid-rangeproof-cache/](liquid-rangeproof-cache/) |
| Aquifer | DefiLlama's $2,469,729 sits about 2% above this entry's theft-day figure | Re-pricing the identical on-chain amount one day later, when the attacker actually moved it, lands within 0.05% of DefiLlama's number, pinning down which moment DefiLlama priced it at (a reconciliation, not an error) | [aquifer-sweeper-arbitrary-call/](aquifer-sweeper-arbitrary-call/) |
| Maya Protocol (MAYAChain) | DefiLlama's $1,700,000 sits about 21% above this entry's BTC-only figure | The gap traces to a specific, still-unconverted 8.87M CACAO balance sitting in the attacker's own wallet (a reconciliation, not an error) | [mayachain-cacao-slash-drain/](mayachain-cacao-slash-drain/) |
| Gravity Bridge | DefiLlama classifies this "Key Compromise" / "Validator Key Compromised" | Every validator signature on the payout batches was genuine; the registry was poisoned via a permissionless function call with a missing collision check, not a compromised key | [gravity-bridge-denom-poisoning/](gravity-bridge-denom-poisoning/) |
| MORE Markets (Ankr ankrFLOW E-Mode) | Blockaid's initial "$9.3M" estimate was repeated across most outlets that covered it | A full scan of the Pool's own event log finds exactly one transaction, totaling $415,398.47, matching DefiLlama's separately-tracked $410,000 (listed under "Ankr") within 1.32% | [more-markets-ankrflow-emode/](more-markets-ankrflow-emode/) |
| Verus-Ethereum Bridge | Press (via Blockaid/cryptotimes.io) described 2 exploits as hitting the same contract through the same import route, implying one reused bug | VerusCoin's own writeup states the two exploits shared only a general bug category, not the same specific mechanism | [verus-ethereum-bridge-forged-proof/](verus-ethereum-bridge-forged-proof/) |
| Ostium (PrivatePriceUpKeep Compromise) | Press carried 3 conflicting estimates ($18M, ~$22M, ~$24M) before Ostium's own investigation settled on $23,752,746 | An independent scan of the Vault's event log lands on $23,752,641.68, within 0.0004% of Ostium's own final figure | [ostium-oracle-forwarder-compromise/](ostium-oracle-forwarder-compromise/) |
| Nomic (nBTC / Osmosis allBTC) | DefiLlama dates this incident 2026-09-09, the disclosure date | The mint itself happened 2026-06-25T21:49:59 UTC, 76 days earlier; DefiLlama's $3,150,000 also prices the full mint at a current BTC rate rather than the theft-day rate | [nomic-nbtc-ibc-selfmint/](nomic-nbtc-ibc-selfmint/) |
| XRP Healthcare (XRPH Wallet) | Not tracked in DefiLlama's hacks feed at all | Independently re-derived totals (267,679.863641 XRP; 445,197.999216 DAI) land within 0.006% and 1.5% of the two figures the source article itself gives (a discovery, not a correction) | [xrph-wallet-key-compromise/](xrph-wallet-key-compromise/) |
| Lazy Summer Protocol | DefiLlama dates this incident 2026-07-05T00:00:00Z | The exploit transaction's own block timestamp is 2026-07-06T05:17:59Z, 29.3 hours later; the amount and classification both check out independently | [lazy-summer-stale-ark-donation/](lazy-summer-stale-ark-donation/) |
| Kelp DAO (rsETH / LayerZero DVN) | DefiLlama tracks $293,000,000 and LayerZero's own statement says "approximately $290M" | This entry's own reconstruction confirms exactly 116,500 rsETH moved; priced at theft-day rate that is $273,377,225, while a second cross-check via Kelp's own oracle backing rate gives $301,716,067, bracketing both public figures from either side | [kelpdao-rseth-layerzero-rpc-spoofing/](kelpdao-rseth-layerzero-rpc-spoofing/) |
| Virtue Protocol (VUSD CDP) | Virtue's own press-relayed figure ($455,103) is the face-value VUSD debt cleared, well below DefiLlama's tracked $894,500 | The debt-cleared figure matches Virtue's own account almost exactly (independently re-derived: $455,102.94), but the real-user collateral actually seized during the crash-triggered liquidation cascade is worth roughly double that at theft-day prices (independently re-derived: ≈$848,457), much closer to DefiLlama's figure (a reconciliation, not an error) | [virtue-iota-switchboard-oracle/](virtue-iota-switchboard-oracle/) |

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
  --category "Bridge" \
  --mechanism "Reentrancy in the withdrawal path" \
  --readme-url "https://example.com/postmortem"
```

This scaffolds `new-protocol-incident/` with a stub README, an empty
`registre_hypotheses.csv`, and a stub `reconstruct_exploit.py`, then
inserts a new row into the Index above, under the year/month section that
matches `--date`'s own year and month (creating that year or month section
first if this is its first entry), sorted by loss within the month. It
then recomputes, from the Index itself and never from a hardcoded number:
that month's subtotal, that year's subtotal, the overall cumulative total
and incident count in "At a glance", and the table of contents' year/month
list. It also moves the "(current month)" label to whichever month is now
chronologically latest, and appends a placeholder footnote for the new
slug. See `add_new_entry.py --help` for the full list of options, and use
`--loss-known-partial` for an incident like Sandbox or Balancer V1 above,
where the real loss is known to exceed the figure that can actually be
sourced. `--category` must be one of the controlled tags already in use
(Bridge, Oracle, Governance, Key-Compromise, Donation-Attack,
Access-Control, Rounding/Math-Bug); the script rejects anything else. If
none genuinely fits a new incident, add the new tag to `VALID_CATEGORIES`
in `add_new_entry.py` by hand first, a deliberate decision, not a
free-text escape hatch.

The script doesn't touch the "Corrections made" and "License" lines in the
"at a glance" block, or the "Corrections to press and DefiLlama" section,
those are human judgment calls (does this new incident actually correct
the press, is it actually MIT), not mechanical totals. Update them
yourself if needed.

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
- Every dollar figure in the Index above is recomputed from each
  subfolder's source files (its README, its script's raw output in
  `resultats_*.txt`, or its `registre_hypotheses.csv`), never carried over
  from an old summary without checking it against those files. When a
  subfolder's source data doesn't support a full dollar total, the table
  says so in a footnote instead of inventing one.
- Five entries (Sandbox, Balancer V1, Liquid Network, Maya Protocol,
  COLDCARD) report a dollar figure that is a known floor, not a complete
  total, because their source repo found a wider scope than the press
  without converting every recovered amount to dollars, (Liquid Network)
  left some smaller destination addresses untraced, (Maya Protocol) found a
  real, still-unconverted balance sitting in the attacker's own wallet that
  this repo declined to price for lack of a sourceable historical rate, or
  (COLDCARD) independently traced only the first of a reported 4 theft
  waves, about a third of the named-security-team's own preliminary total.
  Read the linked subfolder for the full accounting in native units.
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
- The "Category" column in the Index is this project's own classification
  of an already-described mechanism, for scanning convenience, not a
  label sourced from DefiLlama, press, or the protocol itself. Several
  incidents plausibly fit more than one tag; each row carries the single
  tag judged most useful for finding it, the full "Type/Mechanism" column
  next to it carries the actual nuance.

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
