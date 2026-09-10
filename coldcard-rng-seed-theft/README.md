# COLDCARD (Weak Seed RNG) Postmortem

Independent reconstruction of the first wave of the COLDCARD weak-seed-RNG
theft (Bitcoin, 2026-07-30): a build-flag and linker bug in Coldcard's own
open-source firmware silently swapped the hardware random number generator
for MicroPython's weak software PRNG during seed generation, for more than
five years, before an attacker who had apparently pre-computed the
resulting narrow keyspace swept hundreds of long-dormant wallets in a few
minutes. This reconstruction starts from Coinkite's own official GitHub
repository, not a press summary, to confirm the root cause commit-for-commit,
then independently traces one full, concrete theft chain end to end against
live Bitcoin mainnet data: from 505 victim addresses, through a first-hop
consolidation address, to a second address where, six weeks later, the
entire haul is confirmed still sitting completely untouched.

## At a glance

| | |
|---|---|
| Incident | A firmware build/link bug (`MICROPY_HW_ENABLE_RNG` set to 0, guarded by `#ifndef` instead of a value check) let MicroPython's software PRNG silently replace the hardware TRNG in seed generation from March 2021 onward, collapsing entropy to roughly 40-72 bits depending on model |
| Window (this entry) | 2026-07-30 01:36:08-01:51:26 UTC, 4 consecutive Bitcoin blocks (960188-960191); this is wave 1 of a reported 4-wave incident spanning into early August |
| DefiLlama / named-security-team figure | DefiLlama: "COLDCARD", $116,000,000, classification "Weak Key Generation". TRM Labs (named security team): "roughly 1,816 BTC (~$116 million) drained from more than 5,200 addresses" across 4 waves, explicitly stated as preliminary |
| Verified independently (wave 1 only) | 594.47728031 BTC swept from 505 distinct victim addresses (1,331 UTXOs, 506 transactions) into one consolidation address inside a 15-minute, 4-block window; $37,996,965.32 at CoinGecko's theft-day price |
| A primary-source root cause independently confirmed | Coinkite's own GitHub commit `ca724637` ("fixes rng", 2026-07-31) fixes exactly the bug Coinkite's own blog describes; the current live file still shows the original bad line, `mpconfigboard.h:77` |

## The method

```bash
python3 reconstruct_exploit.py
```

No `web3.py` here: Bitcoin is not an EVM chain. `reconstruct_exploit.py`
walks two independent public Bitcoin explorer REST APIs (`blockstream.info/api`
and `mempool.space/api`, cross-checked against each other throughout) and the
GitHub REST API against `Coldcard/firmware`, Coinkite's own official repo.
Every number below is read live by that script, not copied from a press
figure:

1. **The root cause is Coinkite's own GitHub repo, not press.** Commit
   `b18723dd` ("First pass w/ libNgU", 2021-03-01) introduced the bug; commit
   `ca724637` ("fixes rng", 2026-07-31, the day after Coinkite's public
   advisory) fixes it. Both are fetched live via the GitHub API, and the fix
   commit's own diff is read in full, not summarized from a blog post.
2. **The specific theft chain traced here starts from a lead, not a primary
   source, and is independently re-verified from scratch.** A third-party
   researcher's GitHub repo (`DK27ss/ColdCard-38M-PoC`, explicitly not cited
   as authoritative anywhere in this entry) names one consolidation address.
   Every figure this entry actually reports about that address, and the
   address it leads to next, is independently re-derived from raw Bitcoin
   data, not taken on that repo's word; see "What could not be independently
   confirmed" below for where this entry's own numbers differ from that
   lead's.
3. **Every BTC amount is cross-checked against two independent public
   explorers.** Blockstream's Esplora and mempool.space return byte-identical
   `chain_stats` for both addresses traced here.
4. **Block timestamps are read from each block's own header**, not from any
   article's stated time window.

## What it found

### The root cause, confirmed against Coinkite's own repository

`stm32/COLDCARD/mpconfigboard.h` line 77 reads
`#define MICROPY_HW_ENABLE_RNG       (0)`, intended to disable MicroPython's
own software PRNG so the board's hardware TRNG would be used instead. Per
Coinkite's own technical write-up, the guard checking that macro used
`#ifndef` (tests whether the macro is *defined*) rather than testing its
*value*, so setting it to `0` did not have the intended effect: libNgU's
`rng_get()` symbol silently resolved to MicroPython's built-in Yasmarang
PRNG, seeded from device state and timing rather than genuine hardware
entropy. This traces to commit `b18723dddb6d751c39978e4364b56b2414f68b47`
("First pass w/ libNgU"), authored 2021-03-01, independently confirmed live
against `Coldcard/firmware`'s own commit history.

The fix, commit `ca72463709f4e3f8964952039d5caf955f566a87` ("fixes rng"),
authored 2026-07-31, the day after Coinkite's public advisory, does three
things per its own diff, read live: adds a real `rng_get()` wrapper in each
board's `rng.c` that calls the genuine hardware-backed
`rng_get_or_fault()`; forces MicroPython's own fallback PRNG object to
compile empty (`-Dpyb_rng_yasmarang=error-do-not-want-this`); and adds a new
`rng-code-check` build target that runs `arm-none-eabi-nm` on the built
objects and fails the build unless the board's own `rng.o` defines the
global `rng_get` symbol and MicroPython's upstream object defines none. That
last piece directly matches Coinkite's own description of the bug as a
silent *symbol resolution* failure: the fix enforces the correct resolution
at build time via the linker, rather than trusting a preprocessor guard.

### Wave 1: 505 wallets, 15 minutes, one address

Address `bc1qnk4zh9qcnap2mycp56qjrgza3cc8ylrh8fecp0` received
**594.47728031 BTC** across 506 separate funding transactions, independently
summed here from every transaction touching the address (matching the
address's own `funded_txo_sum` exactly). Those 506 transactions swept 1,331
victim UTXOs from 505 distinct source addresses (1,191 P2WPKH, 134 P2PKH, 6
P2SH inputs), with 500 of the 506 transactions confirmed inside 4
consecutive blocks:

| Block | Timestamp (UTC), read from the block's own header | Funding txs |
|---|---|---|
| 960188 | 01:36:08 | 63 |
| 960189 | 01:37:21 | 110 |
| 960190 | 01:43:00 | 168 |
| 960191 | 01:51:26 | 159 |

That is a 15-minute-18-second, 4-block window summing to 594.47722484 BTC,
essentially the whole haul; the remaining 6 transactions (0.00005547 BTC
combined) trickled in as late as 2026-08-19, most likely additional
weak-entropy addresses found and swept afterward.

One sampled victim, the single largest input found
(`bc1qe85jr4em79p66fsszkvfhwjf6p6qst58a2ahlr`, 29.89251877 BTC), received
that balance across 3 deposits between 2025-07-18 and 2026-05-02, all well
before the disclosure, and never spent from itself before being swept in
block 960188: independent confirmation that this was a genuine long-dormant
wallet, not staged or test data.

### Where it went next, and where it still is

In the very same block as the last funding batch (960191, 01:51:26 UTC), a
single transaction spent exactly 341 of address A's 506 UTXOs
(56,202,666,941 sats, 562.02666941 BTC, paying a 704,640-sat fee) to one new
address, `bc1qq85v2c926eg6pgxhwp6q7lf6cnsz80qs3fcu9r`, with no change output.

Querying that second address live today (2026-09-10), across two independent
explorers that agree byte for byte: it has received 562.02148293 BTC total
and **spent none of it**. Address A itself still holds its own residual 165
unspent UTXOs, 32.45061090 BTC. Added together, 594.47209383 of the original
594.47728031 BTC (the roughly 0.005 BTC gap fully explained by the one
mining fee plus later dust deposits) is sitting completely untouched across
exactly these two addresses, more than six weeks after the theft. Neither
address shows up in TRM Labs' or Coinkite's own public statements, which
name no addresses at all.

### The dollar figure, and what it does and doesn't cover

594.47728031 BTC at CoinGecko's own 2026-07-30 (theft-day) daily price
($63,916.60) is **$37,996,965.32**, independently matching press's "close to
USD 38 million" description of wave 1 almost exactly. An hourly price check
brackets the actual 01:36-01:51 UTC sweep window ($63,620.89 at 01:00 UTC,
$64,196.00 at 02:00 UTC), within about 0.9% of the daily figure used, so the
day-level price is not materially off from the moment of the sweep.

This is the figure this entry reports, and it covers only wave 1. DefiLlama
and TRM Labs (a named blockchain-security firm) both track a larger,
explicitly preliminary total across 4 waves: "roughly 1,816 BTC (~$116
million)" from "more than 5,200 addresses," with TRM Labs' own report
stating a fourth wave was still moving through the mempool at the time of
its assessment and that its figures "should be treated as preliminary
rather than final." This entry's $37,996,965.32 covers about 32.8% of that
$116,000,000. Waves 2 through 4 were not independently re-traced here; see
Caveats.

### What could not be independently confirmed

- The consolidation address this entry traces was first identified via a
  third-party researcher's GitHub repo (`DK27ss/ColdCard-38M-PoC`), not a
  primary or named-security-team source; that repo is not cited as
  authoritative anywhere above. Every figure actually reported here was
  independently re-derived from raw chain data rather than taken on that
  repo's word, and this entry's own numbers differ from it in specifics:
  506 funding transactions from 505 distinct addresses summing 1,331
  swept UTXOs (that repo states 501 wallets / 1,324 UTXOs), and a
  block-confirmed window of 01:36:08-01:51:26 UTC (that repo states
  01:10-01:56 UTC, which may reflect mempool broadcast time rather than
  block-confirmation time; this entry reports only the latter, since it is
  what can be read directly from the chain itself).
- Waves 2 through 4 of the broader incident (the remaining roughly 1,220 BTC
  TRM Labs' preliminary count implies) rest on TRM Labs' own reporting
  alone; no addresses for those waves were identified or independently
  traced here.
- The identity behind either address traced here is unknown; TRM Labs
  itself states transaction construction differs across the four waves,
  suggesting more than one attacker may be involved, and does not name a
  suspect. This entry makes no attribution claim.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Coinkite, Coldcard, TRM Labs, or any outlet cited above.
- **The $37,996,965.32 figure is a floor, not the full incident.** It covers
  only the 2026-07-30 wave this entry independently traced end to end. The
  broader, still-preliminary ~$116,000,000 figure DefiLlama and TRM Labs
  track spans 3 additional waves this entry did not re-verify.
- The BTC still sitting in the two addresses traced here (594.47 BTC
  combined) is not "recovered" or frozen in any sense; it is simply unmoved
  as of this reconstruction's run, and could move at any time after
  publication.
- As with every entry in this repo, this reflects a snapshot as of
  2026-09-10. Whether either address has moved, or whether Coinkite or TRM
  Labs have published a fuller, non-preliminary accounting, was not
  re-checked after this reconstruction's run.

## License

MIT
