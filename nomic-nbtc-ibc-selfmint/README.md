# Nomic (nBTC / Osmosis allBTC) Postmortem

On 25 June 2026, one Nomic transaction forged 25 identical IBC transfer
packets, each claiming to come from the bridge's own escrow account, and
minted 40.650602 BTC of nBTC on Osmosis with no real Bitcoin behind it. No
IBC rule was broken: two separate bugs in Nomic's own code let a
`MsgTransfer` name the channel's escrow account as its sender, then let
that same escrow's debit and credit resolve to the same in-memory value,
so the escrow balance never actually dropped while Osmosis, trusting a
perfectly valid packet proof, minted real vouchers anyway. It went
undisclosed for 74 days until Nomic's own chain halted on 7 September on
an unrelated bug, prompting a check of Bitcoin backing that exposed the
shortfall. Osmosis's own governance forum carries the incident's first
public writeup, posted the same day as this reconstruction (10 September
2026). This project treats that forum post and its linked forensic report
as a starting anchor only: every hard number below (the exploit
transaction, the escrow-address derivation, the live pool composition,
the frozen balance, the Bitcoin reserve, the halt's real root cause) is
independently re-fetched here from the chain itself or from a primary
source unrelated to that report, not copied from it.

## At a glance

| | |
|---|---|
| Incident | Forged IBC sender + escrow self-transfer aliasing bug in Nomic's `nomic`/`orga` stack (no public CVE/GHSA id found) |
| Window | Mint: 2026-06-25T21:49:59 UTC (1 Nomic block, verified live). Disclosed/halted: 2026-09-07. This entry's own governance-forum anchor: 2026-09-10 |
| DefiLlama's tracked figure | "Nomic", $3,150,000, dated 2026-09-09 (the disclosure date, not the exploit date) |
| Verified independently | The exploit tx byte-for-byte on Nomic's own RPC; the escrow-account address by independent SHA256/bech32 re-derivation; the allBTC pool's live composition and backing ratio on 2 Osmosis LCD endpoints; the attacker's frozen Osmosis balance; Nomic's own BTC reserve address balance (Blockstream); the attacker's Ethereum wallet's live dust balance and nonce; the halt's real root cause via a still-open Nomic GitHub issue |

## The method

Starting anchor: Osmosis's own governance forum, posted by an Osmosis
admin account (`JohnnyWyles`), not a press summary:
https://forum.osmosis.zone/t/alloyed-btc-restore-backing-after-the-nbtc-incident/4122
("Alloyed BTC: Restore backing after the nBTC incident", 2026-09-10). That
post links a "Full forensic report"
(https://hackmd.io/optjLjTdTKadPNmMc60gJg) with a detailed technical
account; this reconstruction treats the forum post and that report as the
place to find transaction hashes, block heights and addresses to go
re-check, not as facts to repeat. Every claim below that matters is
re-derived independently.

```bash
python3 reconstruct_exploit.py
```

No `web3` dependency: every chain involved here (Nomic, Osmosis) is a
plain Cosmos SDK / Tendermint chain queried over its own public RPC/LCD
via `curl`, plus a plain Ethereum JSON-RPC call for the attacker's ETH
wallet and a plain Bitcoin Esplora call for Nomic's own reserve address.

RPC/API endpoints used: `rpc.nomic.basementnodes.ca` (Nomic - the only one
of 5 Nomic endpoints in the Cosmos chain registry that actually answered;
the other 4, including Nomic's own `stakenet-rpc.nomic.io`, all failed to
connect, consistent with the chain still being halted), `osmosis-rest.publicnode.com`
and `osmosis-api.polkachu.com` (Osmosis, 2 independent operators),
`blockstream.info/api` (Bitcoin), `ethereum-rpc.publicnode.com`
(Ethereum), `api.github.com` (Nomic's own GitHub), `api.coingecko.com`
(historical BTC price).

## What it found

### The escrow-account forgery, independently re-derived, not copied

Every one of the 25 fraudulent packets names `nomic1kq2rzz6fq2q7fsu75a9g7cpzjeanmk685ak9g7`
as its sender. That is not a normal user account: it is Nomic's own
ADR-028 escrow address for `transfer/channel-1`, the standard IBC
derivation `SHA256("ics20-1" + 0x00 + "transfer/channel-1")[:20]`,
bech32-encoded. This project re-implements that derivation from scratch
(no IBC library) and gets the exact same address. An honest transfer can
never carry the escrow account as its own sender; naming it as one is
only possible through the sender-authorization gap the forensic report
describes in Nomic's `ibc_deliver` path.

### The exploit transaction, byte-for-byte, from Nomic's own live RPC

Nomic block 33137470, tx `BEE54496B351A018D092779FE6C833238E1CDF965FE9761A572934F37932E028`,
re-fetched live from `rpc.nomic.basementnodes.ca` (the block's own
chain-recorded timestamp: 2026-06-25T21:49:59.960727999Z): `code: 0`,
`gas_wanted: 0`, `gas_used: 0`, exactly 25 occurrences of `"success:
packet send"`, 25 identical amounts of 162,602,409,537,873 usat (1.626024
BTC) each, a single sender (the escrow account above) and a single
recipient (`osmo1wq76r2mhqsa9yaygghuwyq4wy6dcsgf8vtzltn`), and 101 raw
events total. Every one of those figures matches what the linked
forensic report describes, now confirmed directly against the chain
rather than trusted from the report's prose.

### Osmosis's allBTC pool: the current backing shortfall, read live on 2 independent endpoints

The allBTC transmuter (pool 1868, contract
`osmo1z6r6qdknhgsc0zeracktgpcxf43j6sekq07nw8sxduc9lg0qjjlqfu25e3`) is
queried live via its own `get_total_pool_liquidity` CosmWasm smart query
on two independently operated Osmosis LCD nodes (publicnode.com,
Polkachu), which return byte-identical results. Decoding all 5 pool
denoms (the nBTC IBC denom plus 4 separate WBTC/cbBTC bridge routes) gives
**39.83974592 BTC of nBTC still inside the alloy** against **70.73128010
BTC of real WBTC/cbBTC collateral**, a **63.97% backing ratio** - matching
the forum post's own table (39.839746 / 70.731198 / 63.97%) to 5-6
significant figures, independently, not by re-reading the same table.

### The frozen attacker balance and the Bitcoin reserve, both confirmed live

The attacker's Osmosis address holds, right now, exactly 2,265,060,846
(= 22.65060846 allBTC) and 703,055,696 uosmo (= 703.055696 OSMO) - matching
the forum post's stated frozen amounts exactly. Nomic's own Bitcoin
reserve address (`bc1q9e3d4nca68wzh8j3gme7z7gatnrzrpgcflsu5tgeuh6g7svqykssqzxyfe`),
checked independently via Blockstream (a Bitcoin explorer with no
relationship to Nomic or Osmosis), holds 0.74599951 BTC, matching the
report's stated 0.746 BTC. Both readings are today's live state, 3 days
after the freeze, showing the position genuinely has not moved.

### The halt's root cause, confirmed from Nomic's own GitHub, not from the forum post

Nomic's own GitHub carries a still-open issue, `nomic-io/nomic#340` ("Fix:
prevent advancing checkpoints that cannot cover outputs and fees"), filed
2026-09-07T17:00:45Z by a contributor (`Cordtus`): an insolvent-checkpoint
panic with no solvency check, which halts the chain rather than pushing a
checkpoint it cannot actually cover. This independently corroborates the
forensic report's account of why the chain stopped on 7 September, from a
Nomic-side source the report itself is not. Its open state also confirms
the chain remains halted as of this writing: no merged fix exists yet.
Separately, of the 5 Nomic RPC endpoints the Cosmos chain registry lists,
only 1 (`rpc.nomic.basementnodes.ca`) answered; the other 4, including
Nomic's own `stakenet-rpc.nomic.io`, all failed to connect - consistent
with, though not proof of, a chain that is still not producing new
blocks.

### DefiLlama's date is the disclosure date, not the exploit date, and its dollar figure follows a different BTC price

DefiLlama's hacks feed carries this incident as "Nomic", $3,150,000,
dated 2026-09-09 - the day the halt became public, not the day the mint
actually happened (2026-06-25, independently timestamped above from
Nomic's own chain, 76 days earlier). Dividing DefiLlama's $3,150,000 by
the full counterfeit mint (40.650602 BTC) implies a price near $77,500,
close to BTC's price at the time DefiLlama's entry was made (CoinGecko:
~$77,000 on 2026-09-10), not the $60,989.57/BTC CoinGecko's historical
API gives for 2026-06-25, the actual mint date. This entry instead prices
the portion still unbacked today (39.83974592 BTC, from the live pool
read above) at the 2026-06-25 rate: **$2,429,809.11**, the figure carried
in the root README's index table.

### The Ethereum-side laundering trail: consistent, not independently re-derived in full

The attacker's Ethereum wallet (`0x8f36fd9ffc0a8ca373aa7a4787292536a489d2b5`)
holds, live, 0.5753708194 ETH and an outgoing nonce of 35 - consistent
with the forensic report's "0.575 ETH dust" figure and its account of 33
Tornado Cash deposits plus a handful of other transactions (the report's
own total of "39 transactions" counts both incoming and outgoing; this
project only independently confirms the outgoing count and the live
balance, not the full incoming/outgoing transaction-by-transaction
ledger). Of the 39.83974592 BTC shortfall confirmed live above, 22.650608
BTC (56.9%) sits frozen and pending a governance vote (proposed the same
day as this reconstruction, not yet executed); the remaining 17.189137
BTC is reported by the forensic account as already swapped to ETH and
sent through Tornado Cash, which this project did not independently
retrace hop-by-hop through the mixer.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Nomic, Osmosis, or any outlet cited above.
- No Nomic-side technical postmortem (a GitHub commit fixing the
  sender-authorization or escrow-aliasing bugs themselves, as opposed to
  issue #340's unrelated checkpoint-solvency bug) was found as of this
  writing; `nomic-io/nomic`'s most recent tagged release is still v9.0.0
  (2024-09-19) and its most recent default-branch commit dates to
  2024-11-19, so the exact code fix for the escrow-forgery bug itself
  could not be independently located and is not claimed here beyond what
  the linked forensic report describes.
- The Ethereum-side laundering trail (the Axelar/Squid and Noble CCTP
  routes into the attacker's wallet, the 33 individual Tornado Cash
  deposits, and the exact 39-transaction count) is reported as described
  in the linked forensic report; this project independently confirmed
  only the wallet's current balance and outgoing transaction count, not
  every individual hop.
- The 22.650608 BTC frozen on Osmosis is recoverable only if a future
  governance proposal to reassign it actually passes and a corresponding
  software upgrade ships; as of this writing that proposal has only just
  been posted, not voted on or executed. Nothing here should be read as
  confirming that recovery will happen.
- Authorship of the linked "Full forensic report" (hackmd.io) is not
  independently established beyond its being the reference Osmosis's own
  governance forum post links; it may be written by Osmosis itself, a
  contracted security firm, or a third party. Every figure from it that
  this entry relies on has been independently re-verified against the
  actual chains above rather than trusted on the report's authority
  alone.

## License

MIT

<!-- external sources: https://forum.osmosis.zone/t/alloyed-btc-restore-backing-after-the-nbtc-incident/4122, https://hackmd.io/optjLjTdTKadPNmMc60gJg -->
