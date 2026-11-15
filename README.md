# On-Chain Postmortems

**$954.3M in DeFi and on-chain losses across 72 incidents, 71 of them reconstructed from raw chain data (the exception, tectonic-cronos, is not: per Cronos's report the chain was rolled back past it); $617.4M of it independently recomputed, the rest sourced from the protocol, press or DefiLlama.**

Forensic reconstructions done on-chain. Each entry rebuilds the exploit
from raw chain data (`eth_getLogs`, decoded transaction receipts,
`eth_call` reads) rather than from press summaries. When press or
DefiLlama gets a number, scope, or label wrong, this repo shows the
on-chain proof; when a dollar figure could not be recomputed, the Index
says so and marks it †.

**Don't trust us. Redo it.** Every entry but one rebuilds one incident from public chain data, and its script reads the chain live. The exception is tectonic-cronos: per Cronos's report the chain was rolled back past that attack, so its attack sequence cannot be rebuilt from the chain, and its README says which parts rest on Cronos's report and Certora's analysis. Try one against a public RPC:

```bash
pip install web3
python3 incidents/sandbox-oft-delegate-hijack/reconstruct_exploit.py
```

The historical figures should match `incidents/sandbox-oft-delegate-hijack/resultats_reconstruction_2026-09-09.txt`; balances and roles read today may have moved since. A difference is useful: see [CONTRIBUTING.md](CONTRIBUTING.md).

Example: press reported only the Ethereum leg of the Sandbox bridge
exploit; the reconstruction finds 405.83 WETH gross across Base and
Ethereum, about 5.2 times the press figure, one of 38 rows
in [Corrections to press and DefiLlama](CORRECTIONS.md).

## At a glance

| | |
|---|---|
| Incidents covered | 72, 71 of them reconstructed on-chain (tectonic-cronos is the exception: per Cronos's report the chain was rolled back past the attack), see [the full index](INDEX.md) for detail |
| Cumulative loss | About $954.3M across the 72 incidents ($954,321,548 exactly, sum of the figures in the index); $617,353,390 of it independently recomputed, the rest (marked † in the index) sourced from the protocol, press or DefiLlama. At least one entry is a known floor, so the real total is higher. |
| Corrections made | 38 rows for 36 entries correct, reconcile, or newly surface a press or DefiLlama figure, label, date, or classification (26 corrections, 9 reconciliations, 3 discoveries not previously priced by DefiLlama at all); 3 of the 26 correction rows correct this repository's own earlier text, not the press or DefiLlama. See [Corrections to press and DefiLlama](CORRECTIONS.md). |
| Machine-readable data | [`data/incidents.json`](data/incidents.json) and [`data/incidents.csv`](data/incidents.csv), one row per incident, regenerated from INDEX.md; cite via [`CITATION.cff`](CITATION.cff) |
| License | MIT across all 72 entries, single author (RealSpap, 2026) |

## The 5 biggest losses

Full history is 72 incidents across 8 months with an incident; these are the largest, by
loss. Full table, sortable by month: [INDEX.md](INDEX.md).

| Protocol | Loss ($) | Chain | Mechanism | Link |
|---|---|---|---|---|
| Drift Protocol | † 295,706,375 | Solana | Pre-signed durable-nonce Squads multisig approvals hijacked the program's admin key | [drift-protocol-durable-nonce-admin-hijack/](incidents/drift-protocol-durable-nonce-admin-hijack/) |
| Kelp DAO (rsETH / LayerZero DVN) | ≈ 273,377,225 | Ethereum | Compromised LayerZero RPC nodes plus a DDoS-forced DVN failover passed a forged message through a 1-of-1 verifier | [kelpdao-rseth-layerzero-rpc-spoofing/](incidents/kelpdao-rseth-layerzero-rpc-spoofing/) |
| Bitget hot wallet drain (Ethereum leg) | ≥ 126,417,066 | Ethereum | Spoofed withdrawal requests signed by Bitget's own hot wallets; the Ethereum leg of a $387.5M four-chain theft | [bitget-hot-wallet-spoofed-withdrawals/](incidents/bitget-hot-wallet-spoofed-withdrawals/) |
| Liquid Network | ≥ 46,568,719 | Bitcoin + Liquid | Range-proof cache-key collision let a peg-out register as fully backed | [liquid-rangeproof-cache/](incidents/liquid-rangeproof-cache/) |
| COLDCARD (Weak Seed RNG) | ≥ 37,996,965 | Bitcoin | Build-flag bug silently swapped the hardware RNG for a weak software PRNG for 5+ years | [coldcard-rng-seed-theft/](incidents/coldcard-rng-seed-theft/) |

Drift's figure is Drift's own stated total; a sample of the outflow
(USDT and USDS legs) matches Drift's per-asset figures to within 0.002%,
but the total is not fully recomputed here.

## How to read an incident

1. Start with [INDEX.md](INDEX.md): every incident by year and month, with its loss, chain, category and mechanism.
2. Open the incident folder under [`incidents/`](incidents/). Its `README.md` is the write-up: an "at a glance" block, the method, the caveats.
3. Check the numbers yourself: `reconstruct_exploit.py` re-queries the chain, `resultats_*.txt` is the saved output it should match, and `registre_hypotheses.csv` lists every claim with the test that would falsify it.
4. Where press or DefiLlama got a figure, label or date wrong, the gap is one row in [CORRECTIONS.md](CORRECTIONS.md). The marks in the Index: **≥** known floor, **≈** recomputed, **†** sourced, not recomputed. More in [docs/method.md](docs/method.md) and [docs/limits.md](docs/limits.md).

## Contribute

- **Report an error or ask for a correction:** open an issue, or write privately (see [SECURITY.md](SECURITY.md)).
- **Suggest an incident:** open an issue with the protocol, date, chain and, if you have it, a transaction hash.
- **Replay an entry or send a fix:** see [CONTRIBUTING.md](CONTRIBUTING.md). `python3 tools/check_readme_consistency.py` and `python3 tools/check_structure.py` must pass before a pull request.

New incidents are announced as GitHub releases (Watch, then Custom, then Releases), or through the plain [Atom feed](https://github.com/RealSpap/onchain-postmortems/releases.atom), no account needed.

## Monthly digests

One file per month, published once the month closes: headline loss
total, breakdown by root-cause technique, the three biggest incidents,
and a full linked table.

- [October 2026](digests/2026-10.md): 6 incidents, at least $1.1M
- [September 2026](digests/2026-09.md): 26 incidents, at least $190.0M
- [August 2026](digests/2026-08.md): first edition, 26 incidents, at least $48.9M

Full history: [`digests/`](digests/)

## Structure

```
README.md  INDEX.md  CORRECTIONS.md  CHANGELOG.md   the pitch, every incident, the corrections, the log
SECURITY.md  CONTRIBUTING.md  CITATION.cff  LICENSE   reporting, helping, citing, MIT
incidents/<slug>/                                    one folder per incident: write-up, script, registry, raw output
tools/                                               add_new_entry.py, check_readme_consistency.py, check_structure.py, export_dataset.py
data/  digests/  docs/                               machine-readable data, monthly roundups, method and limits
```

Same author: [@RealSpap on X](https://x.com/RealSpap),
[multisig-overlap-showcase](https://github.com/RealSpap/multisig-overlap-showcase)
(signers shared between protocols),
[defi-admin-key-risk-showcase](https://github.com/RealSpap/defi-admin-key-risk-showcase)
(single-key admin cases, checked by hand) and
[authority-risk-oracle-showcase](https://github.com/RealSpap/authority-risk-oracle-showcase)
(who can change a contract and how fast; testnet).

Independent research, not a security audit, not advice, not affiliated with any protocol named. MIT: see [LICENSE](LICENSE), and [docs/limits.md](docs/limits.md) for the full limits and disclaimer.
