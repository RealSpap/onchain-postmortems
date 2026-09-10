# Liquid Network (Range-Proof Cache) Postmortem

Independent reconstruction of the Liquid Network exploit: a range-proof
verification cache collision in Elements, the Liquid sidechain's own
open-source software, let a peg-out request that the federation's nodes
should have rejected get treated as fully backed instead. The federation's
own 11-of-15 multisig, using real functionary signatures rather than a
stolen key, then correctly signed off on releasing real Bitcoin against
that forged backing. Every address, transaction, and dollar figure below
was found and verified independently, live against Bitcoin mainnet and the
Liquid sidechain, starting only from the federation's own reserve address
(located by decoding its own witness script, not from a press-supplied
address) and Elements' own GitHub repository.

## At a glance

| | |
|---|---|
| Incident | A range-proof cache key collision in Elements let a peg-out get accepted as fully backed when it was not; the federation's real multisig then genuinely authorized releasing BTC against it |
| Window | 2026-09-06 14:28:56 to 16:48:45 UTC (3 outflow transactions, Bitcoin mainnet); partial return 2026-09-07 16:09:25 UTC |
| Press/DefiLlama figure | DefiLlama and press both cite about $320,000,000 gross, "~4,000 BTC" |
| Verified independently | 4,007.82220180 BTC net left the federation's own reserve address across 3 transactions on 2026-09-06, each spent with 11 valid signatures against the federation's real multisig script. 3,400.00000000 BTC came back on 2026-09-07. 598.50041569 BTC remains at the same source address, live, as of this reconstruction |
| A primary-source citation caught | Liquid Network's own incident report states the exploit happened at "15:53:10 UTC" in block 4,050,336; that block's own chain-recorded timestamp, read live, is 13:53:10 UTC, two hours earlier |

## The method

```bash
python3 reconstruct_exploit.py
```

No `web3.py` here: Bitcoin and the Liquid sidechain are not EVM chains.
`reconstruct_exploit.py` instead walks Blockstream's public Esplora REST API
(`blockstream.info/api` for Bitcoin mainnet, `blockstream.info/liquid/api`
for the Liquid sidechain) and the GitHub REST API against
`ElementsProject/elements`, the sidechain's own official repo. Every number
below is read live by that script, not copied from a press figure:

1. **The root cause** comes straight from Elements' own GitHub repo: pull
   request #1600, "sigcache: harden range proof cache keys and add
   `-norangeproofcache` option," merged 2026-09-08 and tagged as release
   `elements-23.3.4` the next day. The PR's own body names the bug: the
   range-proof and surjection-proof caches hashed their arguments by raw
   `CSHA256` concatenation instead of a length-prefixed `CHashWriter`, so
   "distinct argument tuples with byte-identical raw concatenations" could
   collide to the same cache key.
2. **The federation's reserve address** was not taken from any article. It
   was found the same way every other entry in this repo starts from a
   primary source: its witness script, decoded live, is an 11-of-15
   `OP_CHECKMULTISIG` with a timelocked 2-of-3 emergency-backup branch,
   which is exactly the structure Blockstream's own Help Center documents
   for the Liquid Federation's multisig.
3. **Every BTC amount** below is read directly from that address's own
   transaction history and each transaction's own receipt, via
   `blockstream.info/api`, not summed from a press table.
4. **The Liquid-side block** the incident report cites was queried
   directly against the Liquid sidechain's own explorer API, independent of
   any figure the report itself states about it.

## What it found

### The federation's reserve address, and what actually left it

Address `bc1qdlld6antmv4xug242ed83q7k4rqw50cwfns38szx4qu2f4jwaxxsuhwxxr` is
the current Liquid Federation Bitcoin reserve. Three transactions moved
BTC out of it on 2026-09-06:

| Tx | Block | Time (UTC) | Net outflow |
|---|---|---|---|
| `8db751a6…8a7b140` | 965783 | 14:28:56 | 4,002.66609035 BTC |
| `1e5c0fbb…176b3998d` | 965799 | 16:01:28 | 4.14039943 BTC |
| `cb1a2b59…f87e403e` | 965804 | 16:48:45 | 1.01571202 BTC |

**Total: 4,007.82220180 BTC.** Each of the three spent input 0 with 11 valid
signatures against the federation's own real multisig script, decoded
directly from the transaction's own witness data. No private key was
stolen; the federation's own functionary nodes genuinely signed these
releases, because their own Elements software had genuinely (and wrongly)
verified the peg-out as backed.

The main transaction's own receipt shows 4,019.44426085 BTC in from 83
inputs, with 3,996.01834922 BTC going to a single address
(`bc1qgslsydz56d0ed6827hdemfmk5w2f6ldyc6wt7p`) and two smaller amounts
(2.65138358 and 3.99601658 BTC) going to two other addresses this
reconstruction did not trace further.

### A message, then a partial return

At 18:30:10 UTC the same day, a 0.00001 BTC transaction carrying an
`OP_RETURN` payload was sent to the federation address
(`c103de95…2b3e69a19`, block 965818) - a contact attempt, consistent with
press reporting that whoever held the funds identified themselves as
white-hat researchers and opened a channel with the federation on-chain.

At 16:09:25 UTC the next day, transaction
`a6d697a25266ce3c78774fd1d75f896b7af522ada209b0f6228ea497bc49a46d` (block
965950) sent exactly **3,400.00000000 BTC** back to the federation address,
from a single source address, `bc1ql4mfu6aundtkksxklfajs2h3t9nzcd6gyqjlte`,
with **598.49955894 BTC** returned to that same source address as change.
Querying that source address again live, three days later on 2026-09-10,
its balance is **598.50041569 BTC** - essentially unchanged, only
dust-level probe transactions since. That is the figure this entry reports
as the still-unrecovered loss: a floor, not a ceiling, since the two other,
smaller destination addresses from the original drain (6.64740016 BTC
combined) are not accounted for in it.

### A primary source's own citation checked against the chain it describes

Liquid Network's own incident report (posted by its own X account,
`@Liquid_BTC`, "LIQUID NETWORK UPDATE: INCIDENT REPORT," status as of
2026-09-08 19:10 UTC) states: "On September 6, 2026 at 15:53:10 UTC (Liquid
block 4,050,336), a vulnerability in the open-source Elements software
related to how Liquid nodes cache range proof verifications..." Querying
Liquid block 4,050,336 directly gives a chain-recorded timestamp of
2026-09-06 **13:53:10 UTC** - two hours earlier than what the incident
report itself states for the very block it cites. This does not change any
BTC amount in this entry (all of those come from Bitcoin mainnet, not from
this timestamp), but it is a real, checkable discrepancy in the primary
source's own account of its own incident, independently found the same way
this repo's Cosmos EVM and Allbridge entries each caught a different
primary source's own citation error.

### What could not be independently confirmed

Liquid transactions are Confidential Transactions: their amounts are
blinded by default, and public explorer access does not unblind them. Block
4,050,336 contains 7 transactions; this reconstruction could not determine
which one (if any single one) is "the" fraudulent mint, or decode its true
amount, from public data alone. This entry does not name a specific
Liquid-side transaction as the exploit transaction. Press and named
security-team coverage (Halborn, CertiK) additionally attributes the
peg-out to SideSwap, a Liquid Federation member holding a peg-out
authorization key; that attribution was not independently re-derived here
and rests on that press and security-team coverage alone.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Blockstream, the Liquid Federation, SideSwap, or any
  outlet cited above.
- Liquid Network's own incident report was not directly fetchable (HTTP 402
  from the tool available in this session). Its quoted text above rests on
  two independently-worded search queries both returning the identical
  indexed page-title text for that report's URL, not on a direct fetch of
  the page itself. See `resultats_sources_2026-09-10.txt` for the full
  access trail, including a suspicious third-party gist surfaced by one of
  those searches (containing a specific transaction hash that does check
  out on-chain, and an unrelated "clock skew" theory, whose own numbers do
  not reconcile with the actual 2-hour gap found here) that this entry
  deliberately does not rely on.
- The two smaller destination addresses from the main drain transaction
  (2.65138358 and 3.99601658 BTC) were not traced further; the
  598.50041569 BTC figure this entry reports as "still unrecovered" is a
  floor, not the full unrecovered total.
- As with every entry in this repo, this reflects a snapshot: as of
  2026-09-10, the network remains paused and recovery is described by press
  as still in progress. The still-unrecovered balance and the BTC/USD price
  used here can both change after publication.
- Whether more has been returned, or whether the two smaller untraced
  outputs mentioned above have moved, was not re-checked after this
  reconstruction's run.

## License

MIT
