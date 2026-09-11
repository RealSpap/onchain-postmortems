# Coinsbuy (Hot Wallet Drain) Postmortem

On 9 August 2026, named Coinsbuy hot wallets on Ethereum and Tron sent
unauthorized withdrawals to attacker-controlled addresses within under an
hour. Coinsbuy is a centralized crypto payment processor and hosted
wallet provider, so unlike almost every other entry in this repo there is
no smart contract to decode: this is a custodial-key-style incident, and
Coinsbuy's own official statement deliberately withholds the mechanism
("we are not sharing technical details at this stage"). This
reconstruction does not attempt to guess the root cause; it independently
re-verifies the fund flow itself, live, against both chains.

The Tron leg is confirmed in full: this project's own independent sum of
every TRC20-USDT transfer landing on the attacker's Tron collector
address on 9 August 2026 totals exactly 6,037,005.00 USDT, matching
rekt.news's own figure to the cent. The Ethereum leg is confirmed only in
part: one direct 77 ETH transfer from a Coinsbuy-tagged hot wallet to the
attacker's Ethereum collector is confirmed via raw JSON-RPC, but
rekt.news's fuller claim (210.8 ETH cashed out through FixedFloat, 150
ETH through ChangeNOW) routes through an unlabeled intermediary address
this project could not independently tie back to a named Coinsbuy wallet
(see Caveats). The loss figure below is therefore reported as a floor,
not a complete total.

This project first found this candidate via rekt.news's own published
account, which itself names BlockWatchdog, PeckShield, GoPlus Security and
Specter as its sources. That article is treated here as a place to find
addresses to go re-check, not as facts to repeat: every hard number below
is independently re-fetched live from Ethereum mainnet or Tron, or
computed fresh from a live sum of the attacker's own on-chain receipts,
not copied from the article's count.

## At a glance

| | |
|---|---|
| Incident | Unauthorized withdrawals drained named Coinsbuy hot wallets on Ethereum and Tron within under an hour; Coinsbuy's own statement confirms the incident and reimburses users from its own reserves, but withholds the root-cause mechanism |
| Window | 2026-08-09, roughly 12:43-18:09 UTC on the Tron leg (first inbound sweep to last outbound forward); the one independently-confirmed Ethereum transfer lands at 13:19:23 UTC |
| Press figure | rekt.news: "$8.07 million across two blockchains" -- 6,037,005 USDT (Tron) + 210.8 ETH via FixedFloat + 150 ETH via ChangeNOW; DefiLlama tracks this incident as "Coinsbuy", $7,900,000, "Access Control" / "Improper Access Control", dated 2026-08-09 |
| Verified independently | The full Tron leg, live-summed to the cent (6,037,005.00 USDT); one direct 77 ETH Ethereum transfer, confirmed via raw JSON-RPC on 2 independent endpoints, plus its receipt status and block timestamp; a representative Tron transaction, cross-checked via TronGrid's raw transaction-info endpoint independently of the transfer-list endpoint used for the sum; Coinsbuy's own official statement, fetched live, confirms the date, the reimbursement, and that no technical detail was disclosed |
| Not independently confirmed | The root-cause mechanism (Coinsbuy discloses none); the remaining ~283.8 ETH of rekt.news's claimed Ethereum-side total, which this project traced only as far as an unlabeled intermediary address, not back to a specific named Coinsbuy wallet; whether the 7 additional Tron source addresses feeding the attacker's collector (beyond the one address rekt.news itself names) are Coinsbuy-controlled or victim/counterparty wallets |

## The method

```bash
python3 reconstruct_exploit.py
```

No hardcoded press figures beyond the starting anchor's own addresses and
one representative transaction hash. Every number below is read live from
Ethereum mainnet (`ethereum-rpc.publicnode.com`, cross-checked against
`eth-mainnet.public.blastapi.io`) or from Tron (`api.trongrid.io`, both
its trc20-transfer list and, as an independent cross-check, its raw
`gettransactioninfobyid` endpoint), plus Coinsbuy's own statement page and
a single CoinGecko historical-price lookup.

1. **Coinsbuy has no public GitHub org** (confirmed live via 3 case
   variants against the GitHub API), consistent with it being a
   centralized custodial service, not open-source smart-contract
   infrastructure. There is no deployment registry to anchor to the way
   almost every other entry in this repo does.
2. **Coinsbuy's own official statement** (`coinsbuy.com/news/official-...`)
   is fetched live and checked for 4 specific claims (the date, the
   reimbursement-from-reserves commitment, the withheld-technical-detail
   line, and the $100,000 reward), rather than trusted from a press
   paraphrase.
3. **The named Ethereum hot wallet's public tag** ("Coinsbuy 1" /
   "Exchange") is confirmed live from Blockscout's community-maintained
   labels, a corroborating signal, not proof on its own.
4. **The one transaction this project could fully, independently confirm**
   -- 77 ETH from that tagged wallet straight to the attacker's named
   Ethereum collector -- is re-fetched via raw `eth_getTransactionByHash`
   / `eth_getTransactionReceipt` / `eth_getBlockByNumber` on 2 separate
   RPC endpoints, not assumed from an indexer.
5. **The incident-day UTC block window is located live** via binary
   search on block timestamps, not hardcoded.
6. **A best-effort scan** of the 3 named Ethereum hot wallets' full-day
   transaction lists (Blockscout's indexer) looks for any other direct
   transfer to the attacker's addresses; this step is wrapped to degrade
   gracefully and say so if the indexer rate-limits the request during a
   given run, rather than silently omitting the check (see `resultats_*`
   and Caveats for what happened on the run that produced this entry).
7. **The Tron leg is summed independently**: every TRC20-USDT transfer
   landing on the attacker's Tron collector address on 2026-08-09 is
   pulled live from TronGrid and summed by source address, not trusted
   from rekt.news's own total.
8. **One representative Tron transaction is cross-checked** via
   TronGrid's raw `gettransactioninfobyid` endpoint and its own decoded
   `Transfer` event log, independent of the transfer-list endpoint used
   for the sum in step 7.
9. **Live state today**: both attacker collector addresses' current
   balances, to see whether the funds are still sitting there.
10. **A single CoinGecko historical-price lookup** (2026-08-09 ETH/USD)
    converts the one independently-confirmed 77 ETH transfer to dollars.

## What it found

### The Ethereum leg: one transaction, fully confirmed

| | |
|---|---|
| From | `0xc6acbee42e9e323140c1ed060c2f6ea9cc3b4b75` (tagged "Coinsbuy 1" / "Exchange" on Blockscout) |
| To | `0x4d1bef2fe998b3e3c4029ef9ea6a0534d95661d3` (rekt.news's named "Attacker Collector") |
| Amount | 77.0 ETH |
| Block | 25,717,677 |
| Time (live block header) | 2026-08-09T13:19:23Z |
| Status | success, confirmed on 2 independent RPC endpoints |

On the run that produced this entry, Blockscout's public indexer
rate-limited every one of the 3 attempted per-wallet queries for this
step (see `resultats_reconstruction_2026-09-11.txt` and Caveats), so this
project could not independently confirm or rule out a further direct
transfer from the 2 wallets other than the one already confirmed above by
raw RPC. This entry therefore relies solely on the one transaction
confirmed in Step 3, not on a completed scan. The attacker's collector
address separately received 551 ETH that same day across 4 transfers
from an unlabeled address
(`0x66790b54b891e2ebdef58a15b969ff6fb4374b17`), which itself cycles
through 1inch's router and dozens of single-use-looking destination
addresses -- a pattern consistent with active cash-out laundering, and
plausibly the path rekt.news's FixedFloat/ChangeNOW figures describe, but
this project could not independently tie that intermediary address back
to a specific named Coinsbuy wallet, so it is not counted in the total
below.

### The Tron leg: summed in full, matching rekt.news to the cent

Every TRC20-USDT transfer landing on the attacker's Tron collector
(`TVpX9xCzrj6KHeNhhDJoqjzEqFMxdgubGR`) on 2026-08-09, pulled live from
TronGrid and summed independently of any press count:

| Source address | USDT received |
|---|---|
| `TCEEJKaAT4mF3AsjqwUUHmHvosq67x3FTz` (rekt.news's own named Coinsbuy hot wallet) | 3,492,005.00 |
| `TEauiNEmQo9WimV5zQHpVVbU4kwuy3ktfc` | 1,010,000.00 |
| `TSriRu1sN8ishVpLqXYc1tnmvpzvVTMNW3` | 480,000.00 |
| `TEjBLgyLmjexV1MLuFWpdudpMeXBNuXevc` | 400,000.00 |
| `THH76A5EgVqFYzDB6LuC5yt3UjmHSGWBDM` | 309,000.00 |
| `TBk8Z9nLQau7zUNpfC2iP6vgAF9eqWbvkf` | 138,000.00 |
| `TJNvhYEgSbsK3Rnf5KJUEcAAc3Dxov76Km` | 115,000.00 |
| `THgWGuFFTDRX6SvWp6ZqgoK2YCUSXgRFN7` | 93,000.00 |
| **Total** | **6,037,005.00** |

That total matches rekt.news's own "6,037,005 USDT (per BlockWatchdog)"
figure exactly. Only the first address is the one rekt.news's own article
names as a Coinsbuy hot wallet; the other 7 are not individually
attributed by any source this project checked, so whether they are
additional Coinsbuy-controlled wallets or victim/counterparty addresses
that separately paid into the same collector is not independently
established here (see Caveats).

One representative transaction (1,460,000 USDT, from the named Coinsbuy
wallet, at 12:57:03 UTC) is cross-checked via TronGrid's raw
`gettransactioninfobyid` endpoint: its own decoded `Transfer` event log
(topic0 matching the standard ERC20/TRC20 `Transfer` signature) confirms
the identical amount, independent of the transfer-list endpoint used for
the table above.

### Is the money still there?

As of this reconstruction, the Tron collector's own live USDT balance is
at or near zero: essentially all 6,037,005 USDT was forwarded onward the
same day (outbound transfers from the collector on 2026-08-09 sum to
6,036,994.37 USDT, within a few dollars of the inbound total), consistent
with rekt.news's account that "refills began within 10-12 hours" as the
attacker moved to cash out rather than let funds sit. The Ethereum
attacker collector's live balance is checked the same way in
`resultats_*.txt`.

### The independently-confirmed floor

- Tron leg (exact): 6,037,005.00 USDT = **$6,037,005.00**
- Ethereum leg (exact, one transaction): 77 ETH x CoinGecko's 2026-08-09
  historical price ($1,915.45) = **$147,489.48**
- **Combined floor: $6,184,494.48**, reported in the Index above as
  `≥ 6,184,494`.

rekt.news's own total is $8.07 million; DefiLlama tracks $7,900,000. The
gap to both is the unattributed Ethereum-side laundering flow through
`0x66790b54...4b17` described above, which this project observed but
could not independently price or attribute to a specific Coinsbuy source
wallet.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Coinsbuy, rekt.news, BlockWatchdog, PeckShield, GoPlus
  Security, Specter, or any outlet cited above.
- **The root-cause mechanism is not independently confirmed here, and is
  not disclosed by Coinsbuy itself.** rekt.news's own article states
  explicitly that no confirmed intrusion path was disclosed by any source
  it checked, listing compromised keys, leaked API credentials,
  privileged internal accounts, and a compromised approval workflow as
  possibilities "compatible with the observed pattern," none established.
  This project did not independently investigate Coinsbuy's internal
  systems (it has none exposed on-chain to investigate) and does not
  adopt any of these as fact. DefiLlama's own classification, "Access
  Control" / "Improper Access Control," is used for this entry's Category
  column on that basis, as the closest controlled tag to a genuinely
  undetermined mechanism, not as an independently confirmed finding.
- **The Ethereum-side total is a partial reconstruction, not a complete
  one.** Only 77 of the roughly 360.8 ETH rekt.news's own account
  describes (210.8 ETH via FixedFloat, 150 ETH via ChangeNOW) is directly,
  independently traced back to a named Coinsbuy hot wallet. The remainder
  plausibly routes through the unlabeled intermediary address noted above,
  which received 551 ETH from elsewhere that same day and forwarded
  comparable amounts onward through what looks like an automated,
  1inch-integrated cash-out flow -- but this project could not
  independently confirm that intermediary is Coinsbuy-attributable rather
  than a general-purpose swap bot the attacker merely used, so none of
  that 551 ETH is counted in this entry's loss figure.
- **The Blockscout indexer scan for additional direct transfers (method
  step 6) is best-effort, not exhaustive, and did not complete on the run
  that produced this entry.** Blockscout's free public API rate-limited
  all 3 per-wallet queries during this research round (a real, transient
  infrastructure limit from heavy prior use this session, not a data
  gap); `resultats_reconstruction_2026-09-11.txt` shows exactly this
  (`Wallets successfully scanned this run: []`). The script is written to
  report which wallets it actually managed to scan rather than fail
  silently or claim a completeness it doesn't have. This entry's "no
  other direct transfer found" claim is therefore limited to what raw
  RPC alone could confirm (the one transaction in Step 3); re-running the
  script later, once the rate limit clears, may reach the other 2
  wallets.
- **Only 1 of the 8 Tron addresses feeding the attacker's collector is
  individually named by any source this project checked.** The other 7,
  totaling 2,545,000 of the 6,037,005 USDT total, are not independently
  attributed to Coinsbuy; they are counted in the total above only because
  they paid directly into the same attacker collector address on the same
  day as the confirmed drain, which this project treats as strong but not
  certain evidence they are part of the same incident.
- Coinsbuy's own statements beyond its official-statement page exist only
  on X, which is not independently fetchable from this project's tooling
  (consistent with every other entry in this repo that has tried); this
  entry relies on rekt.news's own account of what Coinsbuy and named
  investigators found, not on independently fetching Coinsbuy's X posts.
- Whether any of the 7 unattributed Tron source addresses, or the
  unlabeled Ethereum intermediary, will ever be identified is outside
  this project's scope.

## License

MIT

<!-- external sources: https://rekt.news/coinsbuy-rekt/, https://coinsbuy.com/news/official-statement-on-the-august-9-security-incident/, https://api.llama.fi/hacks -->
