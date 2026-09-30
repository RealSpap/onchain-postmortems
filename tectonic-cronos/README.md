# Tectonic (Cronos) Exploit Post-Mortem

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**A single wallet inflated one token's exchange rate through a direct donation, borrowed $120.4M against it in about 10 minutes, and the chain rollback that followed erased more of the trail than the headline number suggests.**

Independent research into the August 30 2026 Tectonic Protocol exploit on Cronos. This entry combines two different kinds of verification, kept clearly separate: the protocol's current on-chain state (Tectonic's real pool structure, its price feed's key setup) is checked directly against contract state by this project itself, live, from a public RPC. The attack sequence and dollar figures rest on Cronos's own official post-mortem, published 2026-09-08, because the chain rollback that followed the exploit discarded the very blocks that would let this project re-derive the attack independently the way every other entry in this repo does. That is a real limit on this entry's independence, disclosed here rather than worked around, and the rollback's own boundary blocks are independently re-confirmed live below.

## At a glance

| | |
|---|---|
| Protocol | Tectonic, a Compound v2 fork |
| Chain | Cronos |
| Date | 30 August 2026 |
| Loss | $120.4M borrowed against inflated collateral (Cronos's own post-mortem); $111.2M reversed by the rollback, $9.19M (7.6% of affected value) had already left Cronos before the halt and remains unrecovered |
| Technique | TONIC oracle price pumped about 147x (independently confirmed by this project via Dune's retained historical index, see below; the wall-clock timing of the pump is not reconciled); separately, per Cronos's official post-mortem, TONIC collateral was recursively minted and donated directly into the tTONIC contract, inflating its internal exchange rate outside the normal deposit path, before borrowing $120.4M against the combined effect. This project independently verified the oracle-price leg; the minting/donation/borrow sequence is sourced to the official post-mortem, not re-derived here |
| Response | Cronos validators halted at block 90,907,150 and rolled back to block 90,896,188, discarding 10,961 blocks; both boundary blocks independently re-confirmed live by this project on 2026-09-13 |
| Status | Mixed: pool/price-feed structure independently verified live; attack sequence and dollar figures sourced from Cronos's own official post-mortem |

## What it found

### Three pools, not one

Tectonic actually runs three separate lending pools. The address commonly cited as "Tectonic: Core" on CronoScan has never held a single market, confirmed by calling `getAllMarkets()` on all three pools directly. TONIC's collateral factor (20%) hasn't changed since before the exploit either, verified directly against the live Comptroller on-chain, so nothing was quietly tightened after the fact.

### A price feed with no safeguards and two single-owner keys

The price feed pulls from two sources, VVS Finance and the Crypto.com Exchange, with no circuit breaker and no smoothing, as read on 2026-09-13. It is under single-key admin control: two separate single-owner keys, neither a multisig nor a timelock. Current configuration not re-verified since.

### The price pump: about 147x, not 100x

Cronos validators rolled the chain back past the attack window, so today's live RPC can no longer read the pump transactions directly. But Dune's own indexer had already recorded the raw `PriceUpdated` events from TONIC's sub-oracle before the rollback happened, and that historical record still exists, independently of live chain state. Decoded directly from it: TONIC's price sat stable around $0.0000000141-0.0000000142, then began rising at block 90,896,206 and peaked at block 90,897,073 (tx `0x5699cfbd590483965d7a20346c2ec692921a6ca01441f020e2defef7af3620c6`) at $0.000002076321. That is a 147x move from the stable baseline, not the roughly 100x figure this project's own earlier draft and some press coverage used. A long, gradual decline follows as the price reverts, consistent with the position being unwound rather than the peak holding.

The wall-clock times attached to those indexed records are not reconciled and are not relied on here. The index dates the start of the rise at 12:39:10 UTC and the peak at 12:49:13 UTC, but block 90,896,188, read live, is timestamped 10:07:02 UTC, only 18 blocks before the start of the rise, and the rollback span of about 10,962 blocks took about 1 hour 32 minutes. Either the indexed times are offset or they are attached to the wrong blocks; the cause was not determined. An earlier version of this entry reported a pump duration of "exactly 10 minutes 3 seconds" from those times; that precision is withdrawn.

According to Cronos's official post-mortem, the attacker borrowed against the inflated TONIC collateral across nine markets roughly 10 minutes into the attack, for $120.4M total. This project's own on-chain checks cover the price-pump mechanism above and Tectonic's current pool/price-feed structure (both sections on this page); the specific borrow transactions across those nine markets are not independently re-derived here, because the rollback removed them from live-queryable state and this project did not locate an indexed historical record for them the way it did for the price-oracle events.

### What the rollback actually erased, and what it didn't

Checked directly against three independent Cronos RPC endpoints on 2026-09-13: block 90,896,188, the official post-mortem's stated last pre-attack block, still exists with an identical hash (`0x3115d7bc...`) on all three, timestamped 2026-08-30 10:07:02 UTC. Block 90,907,150, the stated halt block, now holds different, legitimate post-rollback content on all three (hash `0xc4773eb7...`, timestamped 2026-08-30 11:38:53 UTC, about 1h32m after the pre-attack block), confirming a real reorg happened at approximately the height the post-mortem describes, rather than this project simply repeating an unverified press number. The gap between the two blocks, 10,962, matches the post-mortem's own stated "10,961 blocks discarded" to within one block, consistent with an inclusive/exclusive counting difference.

What the rollback erased: the entire attack sequence, not just the borrow itself, is gone from today's live chain state, both by this project's own direct check above and by Cronos's own account. What it didn't erase: Dune's independently-retained indexed record of the price-oracle events (see above), and whatever funds had already left Cronos before the rollback's cutoff, an official $9.19M (7.6% of the $120.4M affected), remain unrecovered regardless of the rollback.

## The method

`tectonic_risk_snapshot.py` connects directly to a Cronos RPC endpoint and reads Tectonic's live on-chain state: all 18 markets in the real (unlabeled) Pool 1, their prices, collateral factors, borrows, and utilization. No API keys, no indexer, just the contracts.

```bash
pip install web3
python3 tectonic_risk_snapshot.py --rpc https://evm.cronos.org
```

The script's own docstring documents the verified contract addresses and known quirks, for example that Tectonic's native-asset market reverts on a standard `underlying()` call instead of returning the zero-address sentinel most Compound forks use.

## Caveats

This is independent research, not an official Tectonic or Cronos post-mortem. Cronos published its own official post-mortem on 2026-09-08, after this entry's original draft; the dollar figures and block numbers above have been updated to match it, and are cited to it directly rather than to this project's own chain reads for the parts a rolled-back chain makes impossible to re-derive independently. The price-pump mechanism and Tectonic's current pool/price-feed structure remain this project's own direct, live verification. This project did not independently re-derive the specific borrow transactions across the nine markets the official post-mortem describes, and did not locate an indexed historical record for them the way it did for the price-oracle events. Every claim above is stated at the confidence level the underlying evidence actually supports; see `registre_hypotheses.csv` for the exact locator and confidence level behind each one.

## Files

- `README.md`: this file.
- `tectonic_risk_snapshot.py`: connects directly to a Cronos RPC endpoint and reads Tectonic's current, post-rollback on-chain state (all 18 markets in the real Pool 1, their prices, collateral factors, borrows, and utilization). Does not replay the attack; the attack blocks no longer exist via live RPC after the rollback.
- `registre_hypotheses.csv`: every claim in this README, broken into 8 individually falsifiable hypotheses, each with its exact source locator (a press citation, a live RPC result, or a Dune query over the public `cronos.logs` table), a falsification test, and a confidence level.
- `resultats_verification_2026-09-13.txt`: raw output of this project's own live RPC checks confirming the rollback's two boundary blocks, run against 3 independent Cronos endpoints.
- `resultats_sources_2026-09-13.txt`: the press sources checked, including Cronos's own official post-mortem, and what each one was and was not used for.
- `LICENSE`: MIT.

## License

MIT (`LICENSE`). Anyone may copy, modify, and redistribute this code and analysis, the only obligation being to keep the copyright notice.
