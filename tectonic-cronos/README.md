# Tectonic (Cronos) Exploit Post-Mortem

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**An attacker pushed one token's price up against thin DEX liquidity and borrowed $120.4M against it in about 10 minutes; Certora's analysis finds, by formal verification, that sending the token directly to the lending market raises its exchange rate, and says that such direct transfers were part of the attack. The chain rollback that followed erased more of the trail than the headline number suggests.**

Independent research into the August 30 2026 Tectonic Protocol exploit on Cronos. This entry combines two different kinds of verification, kept clearly separate: the protocol's current on-chain state (Tectonic's real pool structure, its price feed's key setup) is checked directly against contract state by this project itself, live, from a public RPC. The dollar figures, the halt and the restored block rest on Cronos's own report, published 2026-09-08, and the sequence of the attack on that report and on Certora's analysis of 2026-09-22 (the mechanism is detailed below, with who says what), because the chain rollback that followed the exploit discarded the very blocks that would let this project re-derive the attack independently the way every other entry in this repo does. That is a real limit on this entry's independence, disclosed here rather than worked around, and the two block numbers the report names for the rollback are read live below. A first reading of them, dated 2026-09-13, queried the wrong blocks; it is withdrawn and redone on 2026-10-23 (see CORRECTIONS.md).

## At a glance

| | |
|---|---|
| Protocol | Tectonic, a Compound v2 fork |
| Chain | Cronos |
| Date | 30 August 2026 |
| Loss | $120.4M borrowed against inflated collateral (Cronos's report); $111.2M reversed by the rollback, $9.19M (7.6% of affected value) had already left Cronos before the halt and remains unrecovered |
| Technique | TONIC oracle price pumped about 147x against the baseline in Dune's retained historical index, which this project read (about 196x against the $1.06e-8 price BlockSec gives for 12:19 UTC, as quoted by Certora; both series reach about $2.08e-6 at the top and differ on the baseline, see below; the wall-clock timing of the pump is not reconciled). Cronos's report speaks of "manipulation of collateral values" and of "pushing TONIC's price up against thin DEX liquidity", then $120.4M borrowed against the inflated collateral. Certora's analysis (2026-09-22) reports that its Prover found the tTONIC exchange rate can be raised by sending TONIC directly to the market, says that direct TONIC transfers to the market were part of the attack, and, in its "Tectonic exploit timeline" section, that the main transaction contained 98 iterations of a borrowing and collateral inflation loop; that section names no source for the statement. This project independently verified only the oracle-price leg; the transfers, the exchange rate and the loop are Certora's and not re-derived here. Recursive minting, which an earlier version of this entry attributed to Cronos, is in neither source |
| Response | Cronos validators halted at block 90,907,150 and rolled back to block 90,896,188, discarding 10,961 blocks; both block numbers read live by this project on 2026-10-23 (the first reading, of 2026-09-13, queried the wrong blocks and is withdrawn) |
| Status | Mixed: pool/price-feed structure independently verified live; attack sequence and dollar figures sourced from Cronos's report |

## What it found

### Three pools, not one

Tectonic actually runs three separate lending pools. The address commonly cited as "Tectonic: Core" on CronoScan has never held a single market, confirmed by calling `getAllMarkets()` on all three pools directly. TONIC's collateral factor (20%) hasn't changed since before the exploit either, verified directly against the live Comptroller on-chain, so nothing was quietly tightened after the fact.

### A price feed with no safeguards and two single-owner keys

The price feed pulls from two sources, VVS Finance and the Crypto.com Exchange, with no circuit breaker and no smoothing, as read on 2026-09-13. It is under single-key admin control: two separate single-owner keys, neither a multisig nor a timelock. Current configuration not re-verified since.

### The price pump: about 147x (196x on BlockSec's baseline), not 100x

Cronos validators rolled the chain back past the attack window, so today's live RPC can no longer read the pump transactions directly. But Dune's own indexer had already recorded the raw `PriceUpdated` events from TONIC's sub-oracle before the rollback happened, and that historical record still exists, independently of live chain state. Decoded directly from it: TONIC's price sat stable around $0.0000000141-0.0000000142, then began rising at block 90,896,206 and peaked at block 90,897,073 (tx `0x5699cfbd590483965d7a20346c2ec692921a6ca01441f020e2defef7af3620c6`) at $0.000002076321. That is a 147x move from the stable baseline in that index, not the roughly 100x figure this project's own earlier draft and some press coverage used. The ratio depends on the baseline: Dune's index puts the stable price at about $1.41e-8, while BlockSec, as quoted by Certora, puts it at about $1.06e-8 at 12:19 UTC; against that baseline the price BlockSec gives for 12:49 UTC (about $2.08e-6, which is also what Dune's maximum rounds to) is a move of about 196x. BlockSec, as quoted, does not say that this is the peak. The two series give the same figure at the top and differ on where it started; this project did not determine which baseline is right. A long, gradual decline follows as the price reverts, consistent with the position being unwound rather than the peak holding.

The wall-clock times attached to those indexed records are the index's; this project did not read them from the chain and does not rely on them. They can be set against the live chain at one point only: the index dates the start of the rise at 12:39:10 UTC, at block 90,896,206, and block 90,896,188, 18 blocks earlier and the last block Cronos's report says was kept, is timestamped 12:38:52 UTC on 2026-08-30 on three nodes (read on 2026-10-23), 18 seconds before. Cronos's report puts the start of the price push at 12:38:56 UTC. The live blocks at the two heights the index gives, 90,896,206 and 90,897,073, are dated 23:49:35 UTC on 2026-08-30 and 00:08:11 UTC on 2026-08-31, after the restart, so the index's times at those heights cannot be checked against the live chain. An earlier version of this entry reported a clock conflict between the index's times and block 90,896,188, which it read as 10:07:02 UTC; that came from a reading of the wrong block (see CORRECTIONS.md) and is withdrawn, and the conflict does not exist. The earlier "exactly 10 minutes 3 seconds" pump duration, taken from the index's times, stays withdrawn, since those times are not re-derived here.

According to Cronos's report, the attacker borrowed against the inflated TONIC collateral across nine markets roughly 10 minutes into the attack, for $120.4M total. This project's own on-chain checks cover the price-pump mechanism above and Tectonic's current pool/price-feed structure (both sections on this page); the specific borrow transactions across those nine markets are not independently re-derived here, because the rollback removed them from live-queryable state and this project did not locate an indexed historical record for them the way it did for the price-oracle events.

### Who says what about the mechanism

- **Cronos's report** (https://x.com/CronosNetwork/status/2097131718948094299, text pasted by the maintainer on 2026-10-22, read in full, dated 2026-08-30 for the events): the attacker "deploys contracts and begins pushing TONIC's price up against thin DEX liquidity" at 12:38:56 UTC, and "One transaction borrows $120.4 million across nine markets" at 12:49:39 UTC. The report speaks of "manipulation of collateral values". It does not mention a donation, an exchange rate, minting or recursion.
- **Certora's analysis** (Mooly Sagiv, 2026-09-22, https://www.certora.com/blog/tectonic-exploit-120million-collateral-inflation-attack, read on 2026-10-22 and again on 2026-10-23): its Prover run found that the tTONIC exchange rate could be increased through direct token transfers, and a later section says that the on-chain reconstruction shows that "direct TONIC transfers to the tTONIC market were actually part of the attack" (it does not say whose reconstruction). Its "Tectonic exploit timeline" section for August 30, 2026 says that the main transaction "contained 98 iterations of the loop" and that during it TONIC "was also transferred directly into the tTONIC market"; that section names no source for these statements. It does not describe recursive minting ("No tTONIC needs to be minted"). Elsewhere it credits BlockSec with a price path and with about $6.29M traced to Ethereum, and Bitquery with one call that emptied the nine markets; it gives no transaction hash for the transfer.
- **This project**: the price series from Dune's index (about 147x, peak 0.000002076321) and, from BlockSec through Certora, a price of about 0.00000208 by 12:49 UTC are the same to three digits; the transfer into tTONIC, the exchange rate and the loop are not in any record this project could read, since the blocks were rolled back and Dune needs an account to query. DefiLlama classes the incident "Donation Attack" ($124,470,000), which is where this Index's category comes from; this project did not re-derive a transfer.
- **The category**: the Index category, Donation-Attack, is DefiLlama's label ("Donation Attack", "Token & Share Accounting"). Certora titles its article "Collateral Inflation Attack", describes two mechanisms (a direct transfer of TONIC into the market that raises its exchange rate, and a price manipulation through DEX purchases) and uses the word donation for the first only. The category is defensible, not established by Certora alone; it is kept as DefiLlama's.

### What the rollback actually erased, and what it didn't

Read directly on three independent Cronos RPC endpoints on 2026-10-23, with `verifier_blocs.py`, which computes each hexadecimal block number with `hex(n)`: block 90,896,188, the block Cronos's report gives as the last pre-attack block, exists with an identical hash (`0x53c11afc...`) on all three, timestamped 2026-08-30 12:38:52 UTC, four seconds before the 12:38:56 UTC at which Cronos's report places the start of the price push. The next block, 90,896,189, is timestamped 12:38:55 UTC; the one after it, 90,896,190, is timestamped 23:49:01 UTC the same day, more than 11 hours later, and the blocks that follow are timestamped from there on (90,896,206: 23:49:35 UTC). Block 90,907,150, the halt height in the report, is timestamped 2026-08-31 05:59:27 UTC (hash `0x6bd5dc6d...`, same on all three), after the restart; this project has no record of what the discarded block at that height contained. The jump in the timestamps right after block 90,896,189 and the dates of block 90,907,150 are consistent with the report's account of a rollback at about these heights; they do not show it by themselves. The gap between the two numbers, 10,962, matches the report's own stated "10,961 blocks discarded" to within one block, consistent with an inclusive/exclusive counting difference. A first reading of these blocks, dated 2026-09-13, queried two other blocks because of wrong hexadecimal numbers; it is withdrawn (see `resultats_verification_2026-09-13.txt` and CORRECTIONS.md).

What the rollback erased: the entire attack sequence, not just the borrow itself, is gone from today's live chain state, both by this project's own direct check above and by Cronos's own account. What it didn't erase: Dune's independently-retained indexed record of the price-oracle events (see above), and whatever funds had already left Cronos before the rollback's cutoff, an official $9.19M (7.6% of the $120.4M affected), remain unrecovered regardless of the rollback.

## The method

`tectonic_risk_snapshot.py` connects directly to a Cronos RPC endpoint and reads Tectonic's live on-chain state: all 18 markets in the real (unlabeled) Pool 1, their prices, collateral factors, borrows, and utilization. No API keys, no indexer, just the contracts.

```bash
pip install web3
python3 tectonic_risk_snapshot.py --rpc https://evm.cronos.org
```

The script's own docstring documents the verified contract addresses and known quirks, for example that Tectonic's native-asset market reverts on a standard `underlying()` call instead of returning the zero-address sentinel most Compound forks use.

## Caveats

This is independent research, not an official Tectonic or Cronos post-mortem. Cronos published its own report on 2026-09-08, after this entry's original draft; the dollar figures and block numbers above have been updated to match it, and are cited to it directly rather than to this project's own chain reads for the parts a rolled-back chain makes impossible to re-derive independently. The price-pump mechanism and Tectonic's current pool/price-feed structure remain this project's own direct, live verification. This project did not independently re-derive the specific borrow transactions across the nine markets Cronos's report describes, and did not locate an indexed historical record for them the way it did for the price-oracle events. Cronos's report does not mention a donation; Certora's analysis does, in its own words, and names BlockSec, Bitquery and Cronos as the source of some of its figures, without quoting their reports. Every claim above is stated at the confidence level the underlying evidence actually supports; see `registre_hypotheses.csv` for the exact locator and confidence level behind each one.

## Files

- `README.md`: this file.
- `tectonic_risk_snapshot.py`: connects directly to a Cronos RPC endpoint and reads Tectonic's current, post-rollback on-chain state (all 18 markets in the real Pool 1, their prices, collateral factors, borrows, and utilization). Does not replay the attack; the attack blocks no longer exist via live RPC after the rollback.
- `registre_hypotheses.csv`: every claim in this README, broken into 11 individually falsifiable hypotheses, each with its exact source locator (a press citation, a live RPC result, or a Dune query over the public `cronos.logs` table), a falsification test, and a confidence level.
- `verifier_blocs.py`: reads the two block numbers Cronos's report names and the blocks around them from 3 public Cronos RPC endpoints, computing each hexadecimal block number with `hex(n)`.
- `resultats_verification_2026-10-23.txt`: its raw output, run on 2026-10-23.
- `resultats_verification_2026-09-13.txt`: a notice withdrawing the first reading of these blocks, which queried the wrong blocks because of wrong hexadecimal numbers, with the blocks it actually read.
- `resultats_sources_2026-09-13.txt`: the press sources checked, including Cronos's report, and what each one was and was not used for.
- `LICENSE`: MIT.

## License

MIT (`LICENSE`). Anyone may copy, modify, and redistribute this code and analysis, the only obligation being to keep the copyright notice.
