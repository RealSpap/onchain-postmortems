# Changelog

One entry per addition or correction to this repo. Each incident added
with `add_new_entry.py` gets tagged as a matching GitHub release, see
"Get notified of new postmortems" in `README.md`.

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
