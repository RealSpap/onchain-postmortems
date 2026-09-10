# Lazy Summer Protocol (Stale-Ark Donation) Postmortem

Independent on-chain reconstruction of the Lazy Summer Protocol (Summer.fi)
exploit (Ethereum, 2026-07-06). Lazy Summer is an ERC-4626-style yield
vault system (FleetCommander vaults routing capital across sub-strategies
called "Arks"). Summer.fi's own blog post-mortem and its own GitHub
deployment-governance commits describe an Ark that had been capped for
offboarding, but not removed, still counting toward the vault's share
price at a stale, pre-November-2025 valuation; an attacker donated an
over-valued token into that Ark to inflate the share price about 9.5%,
then redeemed at the inflated price after a flash-loan-funded deposit at
the honest price. Press (Bankless, CoinDesk, Bitget) and DefiLlama both
carry a "~$6.04M" / "$6,040,000" headline figure. None of it is taken on
faith here: the attacker addresses and the exploit transaction are read
directly out of Summer.fi's own blog post's raw HTML, the two affected
vault addresses are independently recovered in full from the transaction's
own event log (the blog itself only ever prints them truncated), one of
the two is independently cross-confirmed a second way from Summer.fi's own
GitHub governance JSON, and the dollar figure is independently recomputed
from the attacker's own realized DAI payout, decoded straight from the
transaction's own log, landing within 0.39% of Summer.fi's and DefiLlama's
figure.

## At a glance

| | |
|---|---|
| Incident | An Ark (Silo "Varlamore USDC Growth") had its deposit cap zeroed as part of an offboarding, which blocks new deposits but does not remove it from the vault's active-Ark set; `totalAssets()`/`withdrawableTotalAssets()` kept summing over it at a stale valuation. An attacker who had spent months quietly accumulating that Ark's receipt tokens flash-borrowed over 65M in stablecoins, deposited at the honest price into two USDC vaults (LowerRisk and HigherRisk), donated the stale position directly into the capped Ark to inflate NAV about 9.5%, redeemed at the inflated price, repaid the flash loan, and swapped the proceeds to DAI |
| Window | 2026-07-06T05:17:59Z, one transaction (block 25,471,348), live-timestamped; Summer.fi's own blog states "05:17 AM UTC", matching to the second |
| Press/primary figures | Summer.fi's own blog: LowerRisk vault "≈5.64M USDC", HigherRisk vault "≈0.40M USDC" (≈$6.04M combined); DefiLlama: $6,040,000, dated 2026-07-05 |
| Verified independently | The attacker's own final realized payout, decoded directly from the exploit transaction's own DAI `Transfer` events: **6,016,754.998121 DAI**, landing on the beneficiary EOA named in Summer.fi's own blog. At CoinGecko's own 2026-07-06 DAI/USD rate (0.999979560645277): **$6,016,632.02**, within **0.39%** of both Summer.fi's own and DefiLlama's figures |
| What's still open | The exact Solidity path inside `totalAssets()`/`withdrawableTotalAssets()` that sums a zero-cap Ark is reported here as Summer.fi's own stated root cause, not independently re-derived from decompiled bytecode or a public source repo (the FleetCommander/Ark contracts' source was not found in a public GitHub repo at the time of this reconstruction). See Caveats |

## The method

```bash
python3 reconstruct_exploit.py
```

Starting anchor: `blog.summer.fi`'s own post-mortem article, fetched live
as raw HTML and regex-parsed directly (not an AI-summarized paraphrase of
it), cross-checked against `github.com/OasisDEX/summer-earn-protocol`
(Summer.fi's own GitHub org and repo, its deployment-governance commit
history), neither a press screenshot nor a block-explorer label. From
there, every address is confirmed against the live transaction's own
receipt and event log on Ethereum mainnet, and the dollar total is summed
from the beneficiary's own realized payout, not copied from the blog or
DefiLlama.

RPC/API endpoints used, all public, no key: `eth.drpc.org` and
`ethereum-rpc.publicnode.com` (Ethereum mainnet, chain ID 1),
`blog.summer.fi` (Summer.fi's own post-mortem), `api.github.com` and
`raw.githubusercontent.com` (Summer.fi's own `OasisDEX` GitHub org),
`api.coingecko.com` (theft-day DAI pricing), `api.llama.fi/hacks`
(DefiLlama's own tracked record).

## What it found

### Contract and transaction identity, from Summer.fi's own blog, not a block explorer

Summer.fi's own post-mortem names the two attacker-controlled addresses
directly, linking each straight to Etherscan: "the funder/beneficiary EOA
(`0x7BF7…BDCa`) and the executor contract (`0x0514…FC61`)... These are
already public across security-firm reporting; we are publishing them
here so the community and exchanges can flag associated activity." The
full addresses, `0x7BF716167B48CF527725722C6d79494b45B3BDCa` and
`0x0514F827C129C16418a0933E03C99A6AF982FC61`, are regex-extracted directly
from the blog's own HTML (its `<a href="etherscan.io/address/...">` link
targets), not paraphrased. The blog also links the exploit transaction
itself directly, in the sentence describing the redemption: "...redeems
at the inflated price, repays the loans, and exits with ~$6.04M in DAI."
→ `0x0db528c44f23fc7fa4544684a2fab81096450a14aae8bc89f42cd0592d43da12`.

One caution recorded during this reconstruction: the same blog page links
**six** different transactions with an `#eventlog` Etherscan anchor
(pre-funding, pre-positioning, the exploit itself, three separate Guardian
response actions). An earlier, less careful regex pass on this
reconstruction matched the *first* such link, a pre-funding transaction
from months before the exploit, not the exploit transaction, and would
have silently produced a wrong receipt (a real transaction, but the wrong
one, with a different `from`/`to`). Anchoring the regex to the specific
sentence describing the redemption fixed this. Recorded here as a
methodology note, not a finding about Summer.fi's blog.

Live on Ethereum mainnet (chain ID 1, confirmed via `eth_chainId`), the
named transaction's own receipt confirms: status success, block
25,471,348, `from` = the beneficiary EOA exactly, `to` = the executor
contract exactly, 305 logs, block timestamp **2026-07-06T05:17:59Z**,
matching the blog's own "[05:17 AM]: Exploit transaction" timeline entry
to the second.

### The two vault addresses, recovered in full, not copied truncated from the blog

Summer.fi's own blog only ever prints the two affected vault addresses
truncated: `LazyVault_LowerRisk_USDC (0x98C49e13…EcF17)` and
`LazyVault_HigherRisk_USDC (0xE9cDA459…cB06)`. This reconstruction
recovers both addresses **in full** directly from the exploit
transaction's own USDC `Transfer` log: scanning for counterparties the
executor contract both deposited into and redeemed from (for amounts over
$1M) inside this single transaction finds exactly two such addresses,
`0x98c49e13bf99d7cad8069faa2a370933ec9ecf17` (executor deposited
64,828,534.992005 USDC, redeemed 70,959,584.459769 USDC) and
`0xe9cda459bed6dcfb8ac61cd8ce08e2d52370cb06` (deposited
29,517,258.144045 USDC, redeemed 29,916,430.381787 USDC), each matching
the blog's truncated prefix and suffix exactly.

The HigherRisk vault address is independently cross-confirmed a **second,
completely separate** way: Summer.fi's own GitHub org (`OasisDEX`)
committed `b77fe629cc`
("chore(deployment): Safe batches to sweep + remove Term_Summer_USDC ark
from LazyVault_HigherRisk_USDC (mainnet)") 6 hours after the exploit,
adding a governance-proposal JSON file
(`packages/deployment/proposals/prod_remove_arks_phase1_sweep_mainnet_2026-07-06T13-45-17-049Z.json`,
fetched live) whose own `grantCuratorRole` call names
`fleetCommanderAddress: 0xE9cDA459bED6dcfb8AC61CD8cE08E2D52370cB06`
directly, byte for byte the same address this reconstruction independently
recovered from the transaction log. A companion commit in the same push,
`124733c076` ("feat(deployment): add gov:remove-arks Safe batch script
(sweep stuck assets via socializeLosses, then removeArk)"), and a live
`eth_getCode` check confirm both vault addresses carry real contract
bytecode (24,544 bytes each, on Ethereum mainnet).

### Root cause, in Summer.fi's own words

Summer.fi's own post-mortem states the mechanism directly, not paraphrased
by press: "the attacker donated an over-valued token into an Ark that had
been capped for offboarding but was still counted in the vault's share
price, then redeemed at the inflated price... The Ark was in that state
because its per-Ark deposit cap (`depositCap`, zeroed via
`setArkDepositCap`) had been set to 0 as part of offboarding. Zeroing the
cap blocks new inflows... but it does not remove the Ark from the
FleetCommander's active set (`getActiveArks()`), and both `totalAssets()`
and `withdrawableTotalAssets()` are summed over that active set." The same
post-mortem is explicit that this was not a pure flash-loan trick: "the
stale external valuation combined with incomplete offboarding, not a
single flash-loan trick, was the load-bearing condition," consistent with
a separate blog timeline entry describing the attacker accumulating the
donated Ark's receipt tokens over the preceding months, well before the
same-block flash-loan-funded extraction.

### The attacker's own realized payout, decoded from the transaction's own log

The transaction's own DAI `Transfer` events (7 total, decoded live) show
the executor contract's USDC proceeds routed through a swap
(`0xbebc4478...` → `0x45312ea0...`) into **6,016,754.998121 DAI**, all of
which is then forwarded in one final transfer to the beneficiary EOA named
in Summer.fi's own blog. At CoinGecko's own historical 2026-07-06 DAI/USD
rate (0.999979560645277, fetched live), that is **$6,016,632.02**, within
$23,368 (0.39%) of DefiLlama's tracked $6,040,000 and Summer.fi's own
combined "≈5.64M + ≈0.40M ≈ $6.04M" figure. This reconstruction reports
its own independently-decoded $6,016,632 as the headline figure, on the
same basis this repo uses elsewhere (the attacker's own realized cash-out,
not a gross or intermediate figure), while recording both readings.

### DefiLlama also mis-dates this incident by more than a day

DefiLlama's own hacks feed (`api.llama.fi/hacks`, queried live) tracks
exactly one "Lazy Summer Protocol" entry: chain Ethereum, amount
$6,040,000, classification "Token & Share Accounting" / "Donation Attack",
dated **2026-07-05T00:00:00Z**. The exploit transaction's own live block
timestamp is **2026-07-06T05:17:59Z**, 29.3 hours later. DefiLlama's
classification and amount are both accurate; only the date is off, by
more than a full day.

### Current state of the beneficiary address

As of block 25,948,898 (2026-09-10, live-queried), the beneficiary EOA
holds **0.000000 DAI** and **0.000087 ETH**, essentially dust, confirming
the drained funds no longer sit at that address. Summer.fi's own
post-mortem states the attacker "swapped a portion of the proceeds and
routed them through Tornado Cash... via an intermediary wallet
(`0x46e0…eBa7`)"; that downstream laundering route is not independently
retraced hop by hop in this reconstruction, only the beneficiary's own
current near-zero balance is independently confirmed.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Summer.fi, Lazy Summer Protocol, or any outlet cited
  above.
- The Solidity-level detail of how `totalAssets()`/`withdrawableTotalAssets()`
  sum a zero-cap Ark is reported here as Summer.fi's own stated
  explanation (quoted above), not independently re-derived from a public
  source repo: the FleetCommander/Ark contract source was not found in a
  public GitHub repository at the time of this reconstruction (the
  `OasisDEX/lazy-summer-protocol` repo's own last push predates this
  incident by over a year, and `OasisDEX/summer-earn-protocol`, actively
  maintained through the incident, holds deployment/governance tooling,
  not the vault contracts' own Solidity source).
- The per-vault split (LowerRisk ≈5.64M vs HigherRisk ≈0.40M USDC, per
  Summer.fi's own blog) is not independently re-derived here. A
  redemption-minus-deposit delta computed directly from this
  reconstruction's own transaction-log scan gives a different split
  (≈6.13M / ≈0.40M USDC, summing to more than the attacker's own realized
  DAI payout), most likely because that raw delta double-counts USDC that
  passed back through the vaults again later in the same multi-step
  transaction (e.g. a separate ≈490,637 USDC ark-sweep flow visible in the
  same log) rather than reflecting the attacker's own net extraction. The
  attacker's own final DAI receipt, used as this entry's headline figure,
  sidesteps that ambiguity by measuring the one number that cannot be
  double-counted: what actually left the transaction and landed on the
  beneficiary's own address.
- The attacker's downstream laundering (a swap, then Tornado Cash via an
  intermediary wallet, per Summer.fi's own blog) happened after the
  transaction this reconstruction covers and was not independently
  retraced hop by hop; only the beneficiary address's own current
  near-zero balance is independently confirmed.
- Summer.fi's own blog states a fuller, DAO-level accounting ("a full
  onchain snapshot of vault positions is being conducted to establish,
  precisely and per-depositor, who was affected... No final per-user
  figure will be published until that reconciliation is complete") was
  still pending at the time the post-mortem was published; this
  reconstruction does not attempt to anticipate that per-depositor figure.

## License

MIT

<!-- external source: https://blog.summer.fi/lazy-summer-usdc-vault-exploit-post-mortem-what-happened-and-what-comes-next/ -->
