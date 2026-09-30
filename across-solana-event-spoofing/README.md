# Across Protocol (Solana Event Spoofing) Postmortem

Independent on-chain reconstruction of the Across Protocol Solana
event-spoofing incident (Solana + Ethereum, 2026-07-17). Press
(Cryptonomist, CryptoBriefing, crypto.news, Pluang, KuCoin, techflowpost)
widely reported that Risk Labs' own Solana-origin relayer lost roughly
$4.5M forging Across's own deposit events, with no user funds at risk,
but no outlet named the exploited program, the actual transaction, or the
GitHub fix. This project starts instead from Across's own GitHub
deployment record and its own merged pull request fixing the bug (a real
engineering artifact, not a press summary), fetches the one transaction
that PR names live from Solana mainnet, and decodes its raw instruction
bytes byte-for-byte, re-deriving both Anchor discriminators involved from
their own SHA-256 preimages rather than from anyone's comments about them.

## At a glance

| | |
|---|---|
| Incident | `SvmCpiEventsClient` (Across's own off-chain event reader) decoded any inner instruction CPI'd into its SpokePool program as a genuine deposit event once it saw the right program + event-authority PDA pair, without checking the 8-byte Anchor CPI event discriminator that actually marks a real emitted event. An attacker exploited this with a wrapper program that CPI'd into the SpokePool's own **read-only** `get_unsafe_deposit_id` instruction, appending a forged `FundsDeposited` payload after it, escrowing nothing |
| Window | 2026-07-17, 05:08:25 UTC (the named exploit tx) to 09:37:55 UTC (the merged fix), roughly 4.5 hours, matching press's "fixed within approximately five hours" |
| Press figure | Cryptonomist / crypto.news / CryptoBriefing: Risk Labs' own relayer absorbed roughly $4.5M gross forging 581 of 1,627 attempted deposits across 18 destination chains ($41.7M face value attempted); zero user funds lost or at risk |
| Verified independently | The named exploit transaction, live on Solana mainnet: the inner CPI's first 8 bytes exactly match `sha256("global:get_unsafe_deposit_id")[:8]`, independently computed here, not the genuine Anchor event tag `sha256("anchor:event")[:8]` (byte-reversed) also independently computed here; the forged payload's `outputToken` field is Ethereum's real USDC contract address and its `inputAmount` is 4,113,882.210137 (matching the fix PR's own "~$4.1M" description); the wrapper program is confirmed to be outside Across's own deployments |
| A separate, fully re-derived figure | One of 2 relayers left with legitimate, already-recognised Solana fills stranded by the same incident (a smaller side-effect from the main loss, not part of it) was compensated off-protocol: both legs independently re-fetched and matched to the microdollar and to the second against Across's own unmerged recovery-script description |

## The method

```bash
python3 reconstruct_exploit.py
```

Starting anchor: `across-protocol/contracts`' own GitHub deployment record
(`broadcast/deployed-addresses.json`, fetched live), which states the
mainnet SvmSpoke program address for Solana (Across's internal chain ID
`34268394551451`) and the Ethereum HubPool address directly, not assumed
from a block explorer label. From there:

- `across-protocol/sdk` PR #1486 ("fix(svm): reject forged CPI events
  missing the Anchor event discriminator"), fetched live via the GitHub
  API, confirms it is merged and names the mechanism in its own commit
  message; the regression test file that same commit adds is fetched
  separately and confirmed to name one specific "mainnet exploit
  transaction" in its own code comment.
- That transaction is independently fetched from a public Solana RPC
  (`api.mainnet-beta.solana.com`) and its inner-instruction bytes are
  decoded directly: the first 8 bytes are compared against
  `sha256("global:get_unsafe_deposit_id")[:8]`, computed in this script,
  not copied from the PR.
- The forged event payload's `outputToken` and `inputAmount` fields are
  decoded directly from those same raw bytes.
- The wrapper (outer) program from the transaction is checked against
  every string value in Across's own `deployed-addresses.json` to confirm
  it is not one of Across's own programs.
- A second, unrelated on-chain fact from the same incident, the CBG4
  relayer's off-protocol compensation, is independently re-fetched on
  both legs (Ethereum via `eth.drpc.org`, cross-checked against
  `ethereum.publicnode.com`; Solana via the same public RPC) against the
  description in `across-protocol/contracts` PR #1501, an unmerged but
  fully-detailed recovery-script PR from the same repository.
- DefiLlama's own tracked record (`api.llama.fi/hacks`) is queried live
  for a final cross-check of the widely-reported figure and
  classification.

RPC endpoints used, all public, no key: `api.mainnet-beta.solana.com`
(Solana), `eth.drpc.org` and `ethereum.publicnode.com` (Ethereum, cross-
checked against each other), `raw.githubusercontent.com` + `api.github.com`
(Across's own repositories), `api.llama.fi/hacks` (DefiLlama).

## What it found

### The mechanism, confirmed from Across's own merged fix, not press

`across-protocol/sdk` PR #1486 (merged 2026-07-17T09:37:55Z) describes the
bug directly: `SvmCpiEventsClient.processEventFromTx` treated any inner
instruction into the SpokePool whose sole account was the
`__event_authority` PDA as an emitted event, decoding whatever bytes
followed as a `FundsDeposited`/`FilledRelay` event, without ever checking
that those bytes actually began with Anchor's 8-byte CPI event
discriminator. A genuine Anchor `emit_cpi!` self-invocation carries that
prefix; nothing else that merely touches the program and its event-
authority PDA is required to.

### The named exploit transaction, independently fetched and decoded

The commit's own regression test
(`test/Solana.SvmCpiEventsClient.ForgedEvent.unit.test.ts`) names one
transaction as its real-world source:
`3rLkGVvyYL2LTuDzbo8MBYNwjhYaKo1pEoqd24HCPQJEhNgyVnKZeNFsFrStKYY6cVizBfLpa2RMiB8dxHPzGHMV`.
Fetched live from Solana mainnet (slot 433417931, block time
2026-07-17T05:08:25Z):

- Program `4ACJMgcm2s1q7GCGefKXatniBRtWqosMZDX7QV2c3Cut` (a separate,
  independently deployed BPF program, confirmed absent from every address
  in Across's own `deployed-addresses.json`) CPI'd into
  `DLv3NggMiSaef97YCkew5xKUHDh13tVGZ7tydt3ZeAru`, Across's own SvmSpoke
  program per its own deployment record, passing
  `F3SDf1r4Abt4ZQ9zDwo2Vd2We9e3Xo6fhfMM2iH23soh` (the program's own
  `__event_authority` PDA) as the inner instruction's sole account.
- That inner instruction's first 8 bytes are `760a8700a8f3df75`. This
  project independently computed `sha256(b"global:get_unsafe_deposit_id")
  [:8]` and got the same value: this is Anchor's standard instruction
  discriminator for SvmSpoke's own **read-only** `get_unsafe_deposit_id`
  instruction, not an event at all.
- This project also independently computed
  `sha256(b"anchor:event")[:8]`, byte-reversed (`e445a52e51cb9a1d`), the
  genuine Anchor CPI event tag the fix now requires. The exploit
  transaction's instruction prefix is confirmably not that value.
- The next 256 bytes are the forged event payload. Decoded directly: an
  `outputToken` field whose last 20 bytes read as
  `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`, Ethereum's own real USDC
  contract address, and an `inputAmount` field of `4113882210137` raw
  units, i.e. 4,113,882.210137 at 6 decimals, matching PR #1485's (an
  earlier, unmerged version of the same fix) own description of this
  transaction as forging "a ~$4.1M USDC→mainnet deposit" almost exactly.

Because the client stripped what it assumed was the standard 8-byte
prefix and Borsh-decoded the rest as a real deposit, Across's own indexer
recorded this (and hundreds of similar forgeries) as genuine, and the
relayer filled a subset of them on real destination chains against
origin escrow that was never actually locked on Solana.

### The reported financial total: independently consistent, not independently re-derived in full

Press reports 1,627 forged deposits attempted across 18 destination
chains ($41.7M in attempted face value), of which the relayer filled 581
before the fix landed, for a reported gross loss to Risk Labs' own
relayer capital of roughly $4.5M (net under $4M and falling as recovery
continues), with zero user funds lost, matching DefiLlama's own tracked
$4,500,000 for "Across" (classification "Bridge & Cross-Chain", technique
"Spoofed Event Log"), queried live here. Reconstructing all 581 filled
deposits across 18 chains from raw logs was outside the scope of what
this project could complete; what is independently confirmed
above is the mechanism itself, one specific ~$4.1M forged deposit
matching the incident's own scale, and (below) a fully re-derived, much
smaller figure from a documented side-effect of the same incident. The
headline $4.5M figure is reported as sourced to press and DefiLlama, not
as independently recomputed from a complete fill-by-fill ledger.

### A separate, fully re-derived figure: the CBG4 stranded-relayer compensation

`across-protocol/contracts` PR #1501, an unmerged but extensively
documented recovery-script PR from Across's own repository, describes a
distinct side-effect of the same incident: 2 legitimate relayers (E4bX
and CBG4) had valid, protocol-recognised Solana fills stranded when the
2 bundles covering them were abandoned outright because their accounting
had been poisoned by roughly 36.69M USDC of the same phantom deposit
inflows. The PR states CBG4 was compensated off-protocol on the incident
afternoon by a Council Safe signer, via Mayan, before its own proposed
on-chain repayment leaf ever executed. Both legs, independently
re-fetched here from public RPCs, match that description exactly:

- **Ethereum leg**: tx
  `0xed75fc80ac1793e308449f51609162f3f90b73fca09b88d070e004bb3ecfb76e`,
  block 25552651, timestamp **2026-07-17T13:17:11Z** (matching the PR's
  "13:17 UTC" to the second), sender
  `0x837219D7a9C666F5542c4559Bf17D7B804E5c5fe`. Its own USDC `Transfer`
  logs move exactly **735.500000 USDC** through each hop of a swap-
  aggregator route.
- **Solana leg**: tx
  `2VNwQpsQGnEGLtq6FdXQWs8Qs3zopxK5niQjytXWCr85ZASLm6oyavh6eTSQ5GG3uYd3Gt9BE8dbpXF3gvJ4hxeU`,
  slot 433488475, timestamp **2026-07-17T13:17:40Z**. CBG4's own USDC
  associated token account balance moves by exactly **+735.159139 USDC**
  in this transaction, matching the PR's stated delivered amount exactly.

This is a real, fully independently-verified dollar figure ($735.159139),
but it is a separate accounting side-effect of the incident (compensation
to a third-party relayer for stranded legitimate fills), not part of the
attacker's own $4.5M haul. The PR also states E4bX's own larger
stranded entitlement (64,153.191307 USDC, of which 13,832.309134 was
proposed to be repaid directly from the SpokePool vault) remained an open
claim against the HubPool as of the PR; this project did not find
evidence the specific proposed repayment leaf was ever executed (the PR
itself is closed, not merged), so E4bX's status is reported here as
last documented, not confirmed resolved.

### The 2 poisoned bundle-proposal transactions, confirmed real

The same PR names 2 Ethereum `ProposedRootBundle` transactions whose
Solana-side refund leaves were poisoned by the phantom inflows and never
executed. Both are independently confirmed live as real, successful
transactions sent to `0xc186fA914353c44b2E33eBE05f21846F1048bEda`,
Across's own HubPool address per its own deployment record: tx
`0x46f5926a5cb691cdf604fda01a16eff05158318c09e8830aef8d23c2ed2210bb`
(block 25550386) and tx
`0xd9361db63d710a96de1af115037af6432ed3cb6a745c0956ba55b77758b806f5`
(block 25550543).

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Across Protocol, Risk Labs, or any outlet cited above.
- The headline $4.5M loss figure is press- and DefiLlama-sourced, not
  independently recomputed from a complete reconstruction of all 581
  filled deposits across 18 destination chains; see "The reported
  financial total" above for exactly what was and was not independently
  confirmed.
- `across-protocol/contracts` PR #1501 (the E4bX/CBG4 recovery script) is
  closed without being merged. The CBG4 compensation it describes is
  independently confirmed above as a real, already-executed transaction
  pair, but E4bX's larger stranded entitlement (64,153.191307 USDC per
  that PR) is not confirmed resolved by this project: PR #1501 itself
  proposes, but this project found no independent evidence the specific
  repayment leaf it describes was ever executed on-chain. This is
  reported as an open item, not asserted as either paid or unpaid.
- The forged event payload's full field layout (fields beyond
  `outputToken`/`inputAmount`, such as the destination chain ID and
  recipient) was not fully decoded: without Across's own IDL, a byte-level
  guess at the remaining Borsh struct produced internally inconsistent
  results (e.g. an apparent destination chain ID of 0) past the first two
  fields, so this project stopped at the two fields it could decode with
  confidence and cross-check against an external anchor (a real USDC
  contract address, a dollar figure matching the primary source's own
  description), rather than publish a guessed decode of the rest.
- Across's own Asymmetric Research bug-bounty disclosure blog post
  (published 2026-04-22, well before this incident) describes a
  different, separately-disclosed missing-check bug in the same general
  area of the Solana event client (a missing transaction-success check,
  not a missing discriminator check) that was fixed before any funds were
  lost. It is unrelated to the 2026-07-17 incident this entry covers and
  is not cited as evidence for it.

## License

MIT

<!-- external source: https://github.com/across-protocol/sdk/pull/1486 -->
