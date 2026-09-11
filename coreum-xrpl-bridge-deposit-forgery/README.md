# Coreum (XRPL Bridge) Postmortem

On 2026-08-09, the official `coreumbridge-xrpl` reserve account on the XRP
Ledger paid out 199,916.3 XRP to two attacker-controlled addresses across 94
multisig-authorized transactions in roughly 97 minutes. The relayer software
watching this bridge accepted a self-transfer of the bridge's own
already-issued wrapped-token IOU, carrying a forged bridge-deposit memo, as
proof of a real XRP deposit, without ever checking that the payment actually
reached the bridge's own reserve address. No private key was compromised and
the XRP Ledger's own consensus was never at fault: the relayers genuinely
signed real payouts, against evidence that was itself fake.

This reconstruction does not start from the account press names. It starts
from the bridge's OWN smart contract on Coreum's mainnet, queried live, which
is what actually names the correct XRPL custody address -- a necessary step,
because a first attempt this round anchored on a different, also
XRPSCAN-verified "Coreum"-branded XRPL account and hit a real dead end (see
Method and Caveats). Every material figure below -- the drained amount, the
per-attacker split, the 97-minute window, and the forged-memo mechanism
itself -- is then independently re-derived from raw XRP Ledger data, cross-
checked against a direct ledger-snapshot balance comparison that does not
depend on any transaction-list indexer's completeness at all.

## At a glance

| | |
|---|---|
| Incident | 199,916.3 XRP drained from the Coreum-XRPL bridge's reserve account via 94 relayer-signed payments, after the relayers credited a self-transfer of the bridge's own wrapped-token IOU (carrying a forged bridge-deposit memo) as a real deposit |
| Window | 2026-08-09, first attacker probe 19:16:42 UTC, first real drain 19:26:30 UTC, last real drain 20:53:50 UTC (94 payments, ~97 minutes end to end) |
| Press figure | CoinDesk / Decrypt: "nearly 200,000 XRP... ~199,916 XRP... bridge's reserve fell from ~200,410 XRP to just 493.5 XRP"; DefiLlama tracks this as "Coreum Bridge", $200,000, "Bridge & Cross-Chain" / "Bridge Logic Flaw" |
| Verified independently | The bridge's own XRPL custody address and its 17-of-28 relayer threshold, read live from the bridge contract's own config on Coreum mainnet; the exact 199,916.334320 XRP balance reduction, from a direct before/after ledger-snapshot comparison; the 94-payment, 2-destination breakdown (107,397.5 / 92,518.8 XRP, matching press to the exact XRP); the 17-signer multisig on every payout; the forged-deposit mechanism itself, decoded from one transaction's own raw memo bytes |
| Not independently confirmed | Downstream laundering (press: ETH via THORChain to Tornado Cash) -- not re-traced this round; no dedicated Coreum/TX blog postmortem was fetchable (docs.tx.org returned HTTP 403) |

## The method

```bash
python3 reconstruct_exploit.py
```

No hardcoded XRPL custody address and no press figures trusted at face
value. Every number below is read live from Coreum's own mainnet LCD
(`rest-coreum.ecostake.com`) or the XRP Ledger's own public JSON-RPC
(`s2.ripple.com:51234`), plus one CoinGecko historical-price lookup.

1. **The bridge contract address itself is not guessed.** It is the single
   Coreum-side issuer shared by all 10 mainnet XRPL-originated assets (XRP,
   SOLO, RLUSD, ELS, VGB, EQL, OXP, SIGMA, ROLL, bwif) in
   CoreumFoundation's own `token-registry` repo's `mainnet/assets.json`,
   fetched live.
2. **That contract's OWN live config** (a CosmWasm smart-query,
   `{"config":{}}`, against Coreum's public LCD) names
   `bridge_xrpl_address`, `bridge_state`, `evidence_threshold`, and the
   full list of 28 registered relayers -- the bridge's own primary source,
   not a press paraphrase.
3. **Why the first attempt this round was a dead end**: a different,
   independently XRPSCAN-verified "Coreum"/"Issuer" account
   (`rcoreNywaoz2ZCQ8Lg2EbSLnGuRBmun6D`) is checked live and shown to be
   blackholed (master key disabled, null `RegularKey`, zero owned ledger
   objects -- no `SignerList` at all), structurally incapable of signing
   the 94 multisig payments press describes. Querying the bridge CONTRACT
   itself (step 2), not a plausible-looking vanity address, is what
   actually resolves this.
4. **The exploit-window ledger range is located live** via binary search
   on XRP Ledger close-times, not hardcoded from any press timestamp.
5. **A direct ledger-snapshot ground truth**: `account_info` for the
   bridge's own XRP balance is queried at the ledger index bracketing the
   window's start and end. The difference is cryptographically committed
   in each ledger's own `AccountRoot` state -- true regardless of whether
   any transaction-list indexer is complete.
6. **`account_tx` is fetched and retried against that ground truth.** This
   project found the public `account_tx` endpoint genuinely unreliable
   within this session: 4 separate fetches of the identical ledger range
   returned 4112, 4000, 4111, and 4088 raw records (see Caveats). Rather
   than trust any single fetch, the script retries until the resulting
   balance-changing subset sums to exactly the step-5 ground truth --
   which it did, on the first attempt, on the run that produced this
   entry.
7. **The 94 real payments are summed independently by destination**, and
   every one is checked for exactly 17 `Signers`, matching step 2's
   `evidence_threshold`.
8. **The forged-deposit mechanism is decoded directly**, not assumed: one
   representative attacker self-transfer's raw memo bytes are hex-decoded
   and checked against the bridge's own real deposit-tag JSON format.
9. **A single CoinGecko historical-price lookup** (2026-08-09 XRP/USD)
   converts the confirmed 199,916.3 XRP to dollars.
10. **Live state today**: whether the bridge is still halted, and whether
    its reserve balance has moved since.

## What it found

### The bridge's own contract names the right account

Querying `core1zhs909jp9yktml6qqx9f0ptcq2xnhhj99cja03j3lfcsp2pgm86studdrz`
(the Coreum-side issuer shared by every mainnet XRPL-originated asset in
CoreumFoundation's own token registry) live returns:

| | |
|---|---|
| `bridge_xrpl_address` | `rxXXXeMX8Gy5YvibvGLnQJ1XKKD7UswM1` |
| `bridge_state` | `halted` |
| `evidence_threshold` | 17 |
| Registered relayers | 28 |

This matches press's own "17 of 28 relayer keys" description exactly, from
the contract's own live state, independent of any article. A different,
also-plausible XRPL account tried first this round
(`rcoreNywaoz2ZCQ8Lg2EbSLnGuRBmun6D`, tagged "Coreum" / "Issuer" and
verified on XRPSCAN) turned out to be a blackholed legacy issuer: master
key disabled, `RegularKey` set to the null placeholder
(`rrrrrrrrrrrrrrrrrrrrBZbvji`), and zero owned ledger objects, meaning no
`SignerList` exists on it at all. That account's balance has sat flat at
472.89 XRP for the entire year sampled -- it cannot have signed anything,
let alone 94 multisig payments. It is a real, verified Coreum-branded
address; it is simply not the bridge.

### The drain, confirmed twice over

A direct comparison of the bridge's own XRP balance at the ledger closest
to 2026-08-09 19:00 UTC against the ledger closest to 21:30 UTC --
independent of any transaction list -- gives:

| | |
|---|---|
| Balance before | 200,409.878544 XRP |
| Balance after | 493.544224 XRP |
| Reduction | **199,916.334320 XRP** |

Enumerating the actual transactions behind that reduction (retried until
the sum matched the figure above exactly) finds 104 balance-changing
transactions: 10 fee-only multisig probe/setup entries, and 94 real
payouts, split:

| Destination | XRP received | Payments |
|---|---|---|
| `rfXSfH2q4zhGWdw45nYcWfjvFN5ZfwE1U6` | 107,397.500000 | 47 |
| `rwt8PJhyXWgW8uwmTjmQ7Rw89tJHELFgb5` | 92,518.800000 | 47 |
| **Total delivered** | **199,916.300000** | **94** |

Both the destination split and the total match press's own "~107,397.5 and
~92,518.8 XRP respectively" and "199,916.3 XRP" figures to the exact XRP.
Every one of the 94 payments carries exactly 17 `Signers`, matching the
contract's own `evidence_threshold`. The first real drain lands at
19:26:30 UTC and the last at 20:53:50 UTC (87.3 minutes); counting from the
first attacker probe transaction at 19:16:42 UTC to the last drain gives
97.1 minutes, matching press's "94 payments... 97 minutes" almost exactly.

### The mechanism, decoded from the attacker's own memo

The earliest self-transfer between the two attacker addresses in this
window carries a memo whose raw hex bytes decode to:

```json
{"type":"coreumbridge-xrpl-v1","coreum_recipient":"core1e7y6qwktg7l6ajr8e2eal5j4dnc2jyceftnjce"}
```

That is the bridge's own real deposit-tag format -- attached to a transfer
of 100 units of `coreum7c8eb29e07`, a currency the bridge itself already
issues (an XRPL-side wrapped-token IOU), sent from one attacker wallet to
the other and never touching the bridge's own reserve address at all. This
directly confirms the mechanism press describes: the relayers' deposit
detector matched on the memo tag and the fact that a bridge-issued
currency moved, not on whether XRP was actually paid to the bridge.

### Is the bridge back?

As of this reconstruction, the contract's own live config still reports
`bridge_state: halted`, and the reserve account's balance
(763.543911 XRP) sits only a little above the immediate post-drain
493.544224 XRP -- some small residual inflow since the halt, nowhere near
restored.

### The independently-confirmed total

199,916.3 XRP x CoinGecko's 2026-08-09 historical XRP/USD price
($1.0389339261257766) = **$207,699.83**, about 3.8% above DefiLlama's own
tracked $200,000 for this incident. That gap is ordinary daily-price/
headline-rounding variance, not a mechanism or classification error --
DefiLlama's own "Bridge & Cross-Chain" / "Bridge Logic Flaw" tag already
matches what this reconstruction independently found -- so this entry is
not listed under Corrections to press and DefiLlama below.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Coreum, TX (the rebranded Coreum/Sologenic brand),
  CoinDesk, Decrypt, or DefiLlama.
- **`account_tx` against the public `s2.ripple.com` endpoint proved
  genuinely unreliable within this session.** Four separate fetches of the
  identical 2026-08-09 19:00-21:30 UTC ledger range for the bridge account
  returned 4112, 4000, 4111, and 4088 raw transaction records respectively
  -- none of that variance touched the bridge's own XRP balance itself
  (it is noise from other users' trust-line and DEX-path activity on this
  heavily-used, multi-currency-issuing account), but it meant a single
  `account_tx` fetch could not be trusted on its own. `reconstruct_exploit.py`
  handles this by retrying the fetch until the resulting balance-changing
  subset sums to exactly the independent ledger-snapshot ground truth
  (Step 5 above) rather than trusting any one fetch or asserting
  reproducibility of the full, flaky dataset; on the run that produced
  this entry, the first attempt already matched.
- **Downstream laundering is not independently re-traced.** Press
  (Decrypt) states the stolen XRP was converted to ETH, moved through
  THORChain, and sent to Tornado Cash. This project did not independently
  trace the two attacker XRPL addresses onward into a THORChain swap or an
  Ethereum-side Tornado Cash deposit this round; that claim is reported as
  sourced from press, not independently verified here.
- **No official Coreum/TX blog postmortem was fetchable.** `docs.tx.org`
  returned HTTP 403 to this project's tooling, and the public
  `coreumbridge-xrpl` GitHub repo's own commit and release history shows
  no activity since 2025-09-10, over a year before this incident -- so no
  patched, post-incident version of the relayer code was checked. This
  entry's sourcing rests on CoinDesk's and Decrypt's own published
  articles (mainstream outlets, both independently fetched live) plus this
  project's own on-chain reconstruction, not on a Coreum-authored
  incident report.
- The dollar figure ($207,699.83) uses CoinGecko's daily-snapshot XRP/USD
  price for 2026-08-09, not an intraday price at the exact drain window;
  DefiLlama's $200,000 sits about 3.8% below it, within ordinary
  headline-rounding variance for this kind of conversion.

## License

MIT

<!-- external sources: https://www.coindesk.com/tech/2026/08/12/xrp-bridge-drained-for-usd200-000-after-software-mistook-fake-deposits-for-real-ones, https://decrypt.co/375441/xrp-drained-tx-bridge, https://github.com/CoreumFoundation/coreumbridge-xrpl, https://github.com/CoreumFoundation/token-registry, https://api.llama.fi/hacks -->
