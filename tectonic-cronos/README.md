# Tectonic (Cronos) Exploit Post-Mortem

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**A single wallet inflated one token's exchange rate through a direct donation, borrowed $120M+ against it in about 11 minutes, and the chain rollback that followed erased more of the trail than the headline number suggests.**

Independent, on-chain verified analysis of the August 30 2026 Tectonic Protocol exploit on Cronos. No official post-mortem from Tectonic or Cronos existed as of this writing, so every claim below is checked directly against contract state and cross-checked against independent nodes, not taken from a press release.

**Live dashboard: [dune.com/s_pap/tectonic-cronos-exploit-postmortem](https://dune.com/s_pap/tectonic-cronos-exploit-postmortem)**, every query behind every number is public and re-runnable. This repo holds the source for the risk-snapshot script behind that dashboard, so the numbers can be checked by anyone, not just trusted.

## At a glance

| | |
|---|---|
| Protocol | Tectonic, a Compound v2 fork |
| Chain | Cronos |
| Date | 30 August 2026 |
| Loss | $120M+ borrowed against inflated collateral; an estimated $8.3M confirmed unrecoverable after the rollback |
| Technique | Recursive TONIC minting (98x), then two direct donations into the tTONIC contract that inflated its exchange rate outside the normal deposit path |
| Response | Cronos validators rolled back roughly 11,000 blocks |
| Status | Independent research, verifiable from a public RPC, no API key required |

## What it found

### Three pools, not one

Tectonic actually runs three separate lending pools. The address commonly cited as "Tectonic: Core" on CronoScan has never held a single market, confirmed by calling `getAllMarkets()` on all three pools directly. TONIC's collateral factor (20%) hasn't changed since before the exploit either, verified directly against the live Comptroller on-chain, so nothing was quietly tightened after the fact.

### A price feed with no safeguards and two single-owner keys

The price feed pulls from two sources, VVS Finance and the Crypto.com Exchange, with no circuit breaker and no smoothing. Two separate single-owner keys control it end to end, neither a multisig nor a timelock, so a single compromised key on either side is enough to move the price the protocol lends against.

### The attack: one wallet, three steps, eleven minutes

A contract deployed by a single wallet recursively minted TONIC collateral 98 times, then donated TONIC directly into the tTONIC contract twice, inflating its exchange rate outside the normal deposit path, then borrowed $120M+ against the combined effect. The entire sequence ran in about 11 minutes.

### What the rollback actually erased

Checked directly against three independent nodes: the entire attack sequence, not just the drain, is gone from today's chain, not only the transactions that moved funds. Only funds that had already left Cronos before the rollback's cutoff block remain unrecoverable, an estimated $8.3M.

Full write-up, sources, and the live queries are on the Dune dashboard linked above.

## The method

`tectonic_risk_snapshot.py` connects directly to a Cronos RPC endpoint and reads Tectonic's live on-chain state: all 18 markets in the real (unlabeled) Pool 1, their prices, collateral factors, borrows, and utilization. No API keys, no indexer, just the contracts.

```bash
pip install web3
python3 tectonic_risk_snapshot.py --rpc https://evm.cronos.org
```

The script's own docstring documents the verified contract addresses and known quirks, for example that Tectonic's native-asset market reverts on a standard `underlying()` call instead of returning the zero-address sentinel most Compound forks use.

## Caveats

This is independent research, not an official Tectonic or Cronos post-mortem, neither of which had been published as of this writing. Every claim above is stated at the confidence level the on-chain data actually supports; where something is inference rather than direct observation, the dashboard says so explicitly.

## License

MIT (`LICENSE`). Anyone may copy, modify, and redistribute this code and analysis, the only obligation being to keep the copyright notice.
