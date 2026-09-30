# Avici (Rain Card Collateral) Exploit Postmortem

Independent on-chain reconstruction of the Avici / Rain card-collateral
exploit (Solana, 2026-08-28). Press (crypto.news, bleap.finance, CoinDesk)
named an attacker wallet and described a 3-step instruction pattern, but
no outlet found named a Solana program address, a transaction hash, or the
patch's own timing. None of that is taken on faith here: every claim below
starts from the attacker wallet address itself, read directly off Solana's
own ledger, and the vulnerable programs' own on-chain upgrade history, not
from Rain's or Avici's unverified claim that a fix shipped "following the
attack."

## At a glance

| | |
|---|---|
| Incident | A signature-verification bypass in a Rain-authored Solana card-collateral contract, shared across Avici and other Rain-integrated apps, let an attacker register as an extra collateral admin on victim accounts and withdraw their held balances directly |
| Window | 2026-08-28, 13:40:41 UTC (attacker wallet's first on-chain activity) to 19:26:34 UTC (its last) |
| Press figure | Avici's own X statement, matching DefiLlama exactly: $500,859.22 across 1,685 users |
| Verified independently | The attacker wallet is real and active in exactly the reported window; the exact `WithdrawCollateralAsset` / `AddCollateralAdmin` / `SubmitSignatures` instruction sequence, decoded from raw program logs, not copied from press; 3 separately-deployed program addresses running the same code; all 3 independently confirmed patched within a 4.5-minute window, about 55-60 minutes after the attacker's last transaction |
| What's not independently confirmed | The $500,859.22 total itself (see Caveats) and the exact Ed25519 signature-offset-reuse mechanism press describes |

## The method

```bash
python3 reconstruct_exploit.py
python3 sample_withdrawal_amounts.py
```

Starting anchor: the attacker wallet address named by press
(`FVNFzqAny8spWdPmYw6RQ9TkYa29ueFFiqCFD1gQnCEj`). From there, this project
walks that wallet's complete on-chain signature history, decodes the raw
logs of its transactions, derives the Solana programs those logs actually
name, and reads each program's own on-chain `ProgramData` account (the
upgradeable-loader's own bookkeeping of when a program's live bytecode was
last deployed), the same primary-source pattern this repo's Aquifer entry
uses for a Solana program's upgrade authority, applied here to 3 programs
instead of 1.

RPC endpoint used: `https://api.mainnet-beta.solana.com`, public, no key.
Every step below succeeded against it; no retry or second endpoint was
needed anywhere in this reconstruction.

## What it found

### The attacker wallet, independently timed against press's own claims

bleap.finance's article states the attacker wallet's first funding (via
the deBridge cross-chain bridge) landed "at 13:40 UTC" and, separately,
that its first actual exploit call happened "at 16:49:48 UTC". Neither
claim is taken on faith: this project's own live enumeration of
`FVNFzqAny8spWdPmYw6RQ9TkYa29ueFFiqCFD1gQnCEj`'s full signature history
finds its earliest transaction at **2026-08-28T13:40:41Z** (inside the
stated 13:40 UTC minute), and, filtering to only the transactions that
touch the attacker's own USDC token account
(`A5fBB5sLNMiF6NGz8JPpeKM2Ke6tCvmmAZ7PZVsp6rZy`, itself derived live via
`getTokenAccountsByOwner`, not assumed), its earliest transaction lands at
**2026-08-28T16:49:48Z**, an exact match, to the second, against the
article's separately-stated figure.

One press claim does not hold up under this project's own count, however:
this project's live enumeration finds **21,405** total signatures sent by
the attacker wallet, not the 14,672 bleap.finance's article states. This
is reported as an open discrepancy, not resolved either way; a different
counting methodology (e.g. unique victim accounts probed, rather than raw
transaction signatures, which includes retries) could explain the gap
without either figure being wrong. See `registre_hypotheses.csv` (H2).

### The mechanism, decoded from raw program logs, not copied from press

A representative transaction from the attacker's own loot account's
transaction list, decoded directly (each Solana program invocation is
paired with the instruction name its own log line names at that same call
depth, not guessed from instruction position):

```
Program CWgkFB7ngUc9cGD1LryyhP7h6xYWtwrAjhSKKCoR1gkz invoke [1]
Program log: Instruction: WithdrawCollateralAsset
Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA invoke [2]
...
Program CWgkFB7ngUc9cGD1LryyhP7h6xYWtwrAjhSKKCoR1gkz success
```

This matches the instruction name bleap.finance's article states
("WithdrawCollateralAsset"), independently confirmed here from the raw
log rather than repeated from the article. Widening the search across
more of the attacker's transactions surfaces the other 2 named
instructions, `SubmitSignatures` and `AddCollateralAdmin`, completing the
3-step pattern press describes: submit a forged dual signature, register
as an extra collateral admin on the strength of it, then withdraw.

### 3 programs, not 1: a correction to this project's own first-pass reading

An earlier, smaller sample taken during this reconstruction seemed to show
one fixed "collateral" program (`WithdrawCollateralAsset`) and one fixed
"authorization" program (`SubmitSignatures` / `AddCollateralAdmin`).
Widening the sample overturned that: all 3 named instructions actually
appear, in different sampled transactions, on **3 different program
addresses**:
`26DkA98jjctzPkBEteUsN935CR4dsKx3XvjrtE7MeL4a`,
`CWgkFB7ngUc9cGD1LryyhP7h6xYWtwrAjhSKKCoR1gkz`, and
`3zVB27Gap6fbxpAcV2hsBBUcV3vRjkCikBXREiyBzDuc`. That is not a
contradiction of press, it is consistent with what crypto.news's own
reporting says: Rain's vulnerable contract version was shared across
"Avici and a small number of other programs", i.e. separately deployed
instances of the same code, one per partner or market, rather than one
shared collateral program and one shared authorization program. This
project's own first-pass 2-program reading is corrected here rather than
carried into the final entry uncorrected. See `registre_hypotheses.csv`
(H5).

### The patch, timed from each program's own on-chain upgrade record

crypto.news reports that Rain "upgraded" every program running the
vulnerable contract version "following the August attack", without a
timestamp. Rather than taking that claim on faith, this project read each
of the 3 programs' own `ProgramData` account directly (Solana's own
upgradeable-loader bookkeeping of when a program's live bytecode was last
deployed, not a claim from Rain, Avici, or press):

| Program | Last deployed (live-queried) |
|---|---|
| `26DkA98jjctzPkBEteUsN935CR4dsKx3XvjrtE7MeL4a` | 2026-08-28T20:22:02Z |
| `CWgkFB7ngUc9cGD1LryyhP7h6xYWtwrAjhSKKCoR1gkz` | 2026-08-28T20:22:21Z |
| `3zVB27Gap6fbxpAcV2hsBBUcV3vRjkCikBXREiyBzDuc` | 2026-08-28T20:26:29Z |

All 3 within a 4.5-minute window, about 55-60 minutes after the attacker
wallet's own last transaction (19:26:34Z). This independently confirms a
coordinated, same-day emergency patch across all 3 instances, with a
precision press's own reporting does not give.

### Current status of the attacker's funds

Live-queried on 2026-09-10: the attacker wallet holds 0 SOL, and its USDC
loot account holds 0 USDC. Consistent with, though not direct proof of,
funds having already been moved on (Blockaid, cited by crypto.news,
reports the broader multi-protocol proceeds later reaching Tornado Cash on
Ethereum, a claim this project did not independently trace).

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Avici, Rain, or any outlet cited above.
- **The $500,859.22 total is not independently re-derived here, only
  sourced.** This project attempted an independent recomputation: a fixed,
  reproducible random sample (seed=42) of 35 of the 5,392 transactions
  that touch the attacker's own USDC loot account. Only 29% of the sample
  moved any USDC; the amounts that did range from single digits to several
  thousand dollars, too skewed a distribution for 35 transactions to
  extrapolate reliably. A naive extrapolation from the sample's own mean
  gives $875,983.55, about 75% above the reported figure. Rather than
  present that extrapolation as a finding, or silently adopt the reported
  figure as if it had been re-derived, this project reports the
  $500,859.22 total as sourced to Avici's own X statement (matching
  DefiLlama's independently tracked figure for this incident exactly) and
  reports its own recomputation attempt as inconclusive. See
  `resultats_sampling_2026-09-10.txt` and `registre_hypotheses.csv` (H8).
  A full, exhaustive (non-sampled) sum over all 5,392 transactions would
  settle this, and was not done here for time. One point of scale when
  reading that gap: the attacker's transactions touch all 3 program
  deployments described above, not Avici's alone, so the loot account is
  not necessarily an Avici-only figure. Press puts the loss across the
  affected Rain-powered programs at roughly $1.1 million (CoinDesk,
  2026-08-29, citing Avici's $500,800 and Tria's over $430,000 as parts of
  it), which the $875,983.55 extrapolation undershoots rather than
  exceeds. This is context for the sampling gap, not a re-derived total.
  See `resultats_sources_2026-09-17.txt`.
- **The Ed25519 signature-offset-reuse mechanism is reported as sourced,
  not independently confirmed.** crypto.news and Blockaid describe the
  root cause as the attacker manipulating a second Ed25519 verification
  instruction so its offsets pointed back into the first, letting one
  signature satisfy what should have been 2 independent authorizations.
  This project saw 2 `Ed25519SigVerify` precompile calls ahead of
  `WithdrawCollateralAsset` in the transactions it inspected, consistent
  with that description, but did not decode the raw instruction bytes
  (message/public-key/signature offset fields) to independently confirm
  offset reuse. See `registre_hypotheses.csv` (H9).
- Whether DefiLlama's own classification for this incident ("Protocol
  Logic" / "Withdrawal Logic Flaw") is the most precise label is left as
  an open question rather than asserted as wrong: given the above, the
  root cause reads more like an access-control/authentication bypass, but
  this project did not independently confirm that mechanism to the level
  this repo's Gravity Bridge entry confirmed its own reclassification.
- Only the `Avici` row of this incident is covered here. Separate press
  coverage describes a similarly-patterned, separate loss at a second
  Rain-integrated app (`Tria`, reported at $431,945 / 636 users); that
  loss is not independently reconstructed or counted in this entry's
  total, and is not currently a separate DefiLlama-tracked row this
  project could cross-check.
- One public RPC (`api.mainnet-beta.solana.com`) was used for the entire
  reconstruction; no paid RPC or API key was used anywhere in this
  project.

## License

MIT

<!-- external source: https://crypto.news/rain-contract-exploit-drains-1-1m-from-card-users/ -->
