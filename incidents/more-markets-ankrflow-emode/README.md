# MORE Markets (Ankr ankrFLOW E-Mode) Postmortem

Independent on-chain reconstruction of the MORE Markets exploit (Flow EVM,
2026-08-31). Blockaid's initial estimate, repeated across most crypto
press that week, put the loss at "$9.3M". Several outlets later carried a
correction naming the real vulnerable component as Ankr's own ankrFLOW
liquid-staking contract, with a real loss near $410,000, but no outlet
found published a transaction hash, a block number, or an attacker
address in full. Neither figure is taken on faith here: every claim below
starts from MORE Markets' own GitHub deployment registry and is decoded
directly from raw Flow EVM chain data.

## At a glance

| | |
|---|---|
| Incident | Ankr's ankrFLOW liquid-staking contract let an attacker mint unbacked ankrFLOW through a recursive stake/restake loop inside a single transaction, then supplied it as E-Mode collateral on MORE Markets (an Aave V3 fork) to borrow out its entire WFLOW reserve |
| Window | 2026-08-31 06:18:52 UTC, a single transaction |
| Press figure | Blockaid's initial estimate: "$9.3M" (widely repeated); a later, uncredited correction: "~$410,000" / "~$246,000 realized after slippage" |
| Verified independently | 15,488,124.145039 WFLOW borrowed out of the Pool's WFLOW reserve in one transaction, decoded from the Pool's own `Borrow` event and cross-checked against the underlying WFLOW token's own `Transfer` events; $415,398.47 at CoinGecko's theft-day price, within 1.32% of DefiLlama's own tracked $410,000 |
| Figure reconciliation | The widely-repeated Blockaid "$9.3M" figure is not found in the part of the Pool this reconstruction scanned: the only Pool activity touching the WFLOW or ankrFLOW reserve in the 2026-08-30/09-01 window is this one transaction, and its WFLOW-reserve Borrow events total $415,398.47. Other reserves of the Pool were not scanned |
| What's still open | The exact internal mechanism inside Ankr's own (unverified, not open-source as far as this project found) staking contract that let the recursive loop inflate ankrFLOW is characterized at the level press described, not independently decoded opcode-by-opcode; the attacker's downstream conversion of the borrowed WFLOW into whatever they ultimately kept happened after this transaction and was not traced here. See Caveats |

## The method

```bash
python3 reconstruct_exploit.py
```

Starting anchor: `MOREProtocol/MORE-Markets`, the protocol's own GitHub
repository, states every deployed contract address for its Flow EVM
mainnet market in `docs/DEPLOYED_CONTRACTS.md` and
`docs/MARKETS_CONFIGURATION.md`, fetched live below, not assumed from a
block explorer label or a press screenshot. From there, every address is
confirmed live (bytecode present, `symbol()` matches) against Flow EVM
mainnet before being used, the exploit block is located by binary
search on live block timestamps (not by copying a date from an article),
and the exploit transaction is located by scanning the Pool's own event
log for the one transaction whose Borrow event on the WFLOW reserve is
far larger than routine market activity.

RPC endpoints used, all public, no key: `mainnet.evm.nodes.onflow.org`
(Flow EVM, chain ID 747), `raw.githubusercontent.com` (MORE Markets' own
deployment docs), `api.coingecko.com` (theft-day pricing),
`api.llama.fi/hacks` (DefiLlama's own tracked record).

## What it found

### The drain: one transaction, decoded directly from the Pool's own event log

MORE Markets' own GitHub deployment docs name its Flow EVM mainnet Pool
proxy as `0xbC92aaC2DBBF42215248B5688eB3D3d2b32F2c8d`, its WFLOW market's
underlying token as `0xd3bF53DAC106A0290B0483EcBC89d40FcC961f3e`, and its
ankrFLOW market's underlying token as
`0x1b97100eA1D7126C4d60027e231EA4CB25314bdb`. All three carry live
bytecode on Flow EVM mainnet (chain ID 747, confirmed via `eth_chainId`),
and `WFLOW.symbol()` / `ankrFLOW.symbol()` read live as `"WFLOW"` and
`"ankrFLOWEVM"`, matching the docs.

Scanning the Pool contract's own event log across the entire
2026-08-30T00:00:00Z to 2026-09-01T00:00:00Z window (located by binary
search on live block timestamps, not assumed) for any event whose
indexed `reserve` parameter is WFLOW or ankrFLOW turns up 7 transactions,
6 of them routine Supply/Borrow/Withdraw activity in the tens or hundreds
of WFLOW. One transaction,
`0x2b2e6ea6cc7dabeec83941abfdc22dd7fa53a58f327af0fccb73a0ed8a3f66c9` at
block 76,986,328 (timestamp **2026-08-31 06:18:52 UTC**, live-read, not
copied from any article), stands far apart: it alone carries 2 `Borrow`
events on the WFLOW reserve, for 5,668,483.096790 and 9,819,641.048249
WFLOW, **15,488,124.145039 WFLOW total**, both paid out to the same
attacker contract, `0xa0c2fe72ad9b640994a9c4252f25fb058ddb3702`, called
by EOA `0xa1e4b05f9a0425136045d8fc8a4978b25bb6a7cc`.

This total is independently cross-checked a second way: Aave-style pools
pay out a `Borrow` by having the WFLOW aToken
(`0x02BF4bd075c1b7C8D85F54777eaAA3638135c059`, also from MORE Markets'
own docs) call `transfer()` on the underlying WFLOW token directly, so
the same transaction's WFLOW `Transfer` events (aToken to attacker
contract) total exactly the same 15,488,124.145039 WFLOW, decoded from a
completely different event on a different contract than the Borrow event
above.

### The mechanism, as far as this reconstruction independently confirms it

The same single transaction contains 613 logs. Before the two large
`Borrow` calls, the attacker's contract and two other addresses
(`0xfe8189a3016cb6a3668b8ccdac520ce572d4287a` and
`0xd6fd021662b83bb1aabc2006583a62ad2efb8d4a`, both undocumented in
MORE Markets' own repo, most likely Ankr's own staking contracts) exchange
ankrFLOW and WFLOW in a geometric series, each step roughly 1.2x the last,
starting near 5,000 tokens and ending near 6,245,328 tokens, before two
final chunks (7,639,125.76 and 5,668,483.10 ankrFLOW) are supplied to the
Pool as collateral. This matches the shape of what press describes as
"inflating a position roughly 200x": a recursive mint/stake loop inside
Ankr's own contract that grows the attacker's ankrFLOW balance without a
matching real deposit each round. This reconstruction independently
confirms the loop happened (the geometric Transfer amounts, decoded
directly from raw event data) and confirms its end state (the exact
ankrFLOW collateral supplied and the exact WFLOW borrowed against it), but
does not independently decode the opcode-level logic inside Ankr's own
staking contracts that makes each round profitable, since neither
contract is verified open-source in a location this project found. That
narrower claim is reported here as press-sourced, not independently
re-derived.

### USD total, independently priced, not copied from either press figure

15,488,124.145039 WFLOW at CoinGecko's own 2026-08-31 historical price
($0.0268204505) is **$415,398.47**. DefiLlama's own hacks feed
(`api.llama.fi/hacks`) tracks this incident as `"Ankr"`, chain `Flow`,
dated 2026-08-31, amount **$410,000**, classification "Token & Share
Accounting" / "Unbacked Mint" (not "MORE Markets", and not the $9.3M
figure Blockaid's initial report carried). This project's own
independently-derived total sits within **1.32%** of DefiLlama's tracked
figure, obtained from a completely different starting point (the native
WFLOW amount actually borrowed, priced independently) than whatever
DefiLlama's own pipeline used.

### The widely-repeated $9.3M figure is not found in the WFLOW reserve

Blockaid's initial estimate of "$9.3M" was carried by essentially every
outlet that covered this incident in the days immediately after. This
project's own reconstruction, anchored in the Pool's own event log across
the full incident window, finds exactly one transaction touching the
WFLOW or ankrFLOW reserve that could plausibly be the exploit, and its
WFLOW-reserve Borrow events total $415,398.47, roughly 22x less than
$9.3M. Borrow and Withdraw events on the Pool's other reserves were not
scanned, so a loss outside the WFLOW reserve is not excluded by this
reconstruction; the figure is consistent with DefiLlama's $410,000 and
with the later press figure.
Some outlets later carried a walked-back figure closer to $410,000
without a byline explaining the revision or citing a transaction hash;
this project's own independent number was derived before finding those
later articles and matches them within 1.32%, which is evidence for the
corrected figure, not merely a repetition of it.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with MORE Markets, Ankr, Blockaid, Flow Foundation, or any
  outlet cited above.
- The two undocumented addresses driving the geometric loop
  (`0xfe8189a3016cb6a3668b8ccdac520ce572d4287a` and
  `0xd6fd021662b83bb1aabc2006583a62ad2efb8d4a`) are almost certainly part
  of Ankr's own ankrFLOW staking infrastructure, given they appear
  exclusively alongside ankrFLOW and WFLOW transfers throughout this
  transaction, but neither is named in MORE Markets' own repo (naturally,
  since they belong to Ankr, not MORE Markets) and this project found no
  verified source code for either, so the precise internal call sequence
  that lets the loop compound is reported as press-characterized, not
  independently decoded.
- The attacker's downstream handling of the 15,488,124.145039 WFLOW after
  this transaction (press: "extreme slippage" reducing the realized
  amount to roughly $246,000) is not traced here. Both attacker addresses
  currently hold 0 WFLOW and negligible native FLOW (101.2 and 0,
  live-queried 2026-09-10), confirming the funds did leave these two
  addresses, but the specific swaps or transfers that moved them out are
  a separate matter from the Pool-level loss this entry reconstructs, and
  were not independently retraced.
- [The spendnode.io article](https://www.spendnode.io/blog/more-markets-flow-evm-lending-exploit-9-3-million-august-2026/)
  is one of several outlets covering this incident; none found published the transaction hash, block number, or
  full attacker address independently confirmed here.

## License

MIT

<!-- external source: https://www.spendnode.io/blog/more-markets-flow-evm-lending-exploit-9-3-million-august-2026/ -->
