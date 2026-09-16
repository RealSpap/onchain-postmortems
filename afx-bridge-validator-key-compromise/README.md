# AFX Bridge Postmortem

Independent reconstruction of the AFX Bridge exploit: an attacker
compromised the signing keys of 5 of the bridge's 7 validators and used
them to authorize a fraudulent withdrawal of 24,150,000 USDC from the
bridge's Arbitrum custody, then moved the entire amount to Ethereum via
Circle's own CCTP and swapped it out. No AFX-owned GitHub repository or
deployment registry was found, so this reconstruction starts from a
transaction hash a press article cited, verifies live that it actually
resolves on-chain and matches every claimed figure, then goes further
than any source found: it decodes the bridge's own raw submission
calldata to independently recover the full 7-validator weight table and
reproduce the reported "7,142 of 10,000 voting units" figure from first
principles, and traces the entire 24.15M USDC, unit for unit, from the
bridge to a single Ethereum-side destination.

## At a glance

| | |
|---|---|
| Incident | Compromised signing keys for 5 of 7 bridge validators authorized a withdrawal request that should have needed all 7 (or at least a majority not concentrated in one compromise) to be trustworthy |
| Window | 2026-07-22T21:26:55 UTC (validator-signed submission) to 2026-07-22T21:30:25 UTC (finalization, 210 seconds later) |
| Press/DefiLlama figure | DefiLlama: "AFX Bridge", $24,150,000, Arbitrum, classification "Key Compromise", technique "Validator Key Compromised". Press (CoinDesk, KuCoin, crypto.news, Halborn) converges on "$24.15 million", "5 of 7 validators", "7,142 of 10,000 voting units", and roughly "12,467.5 ETH" bought with the proceeds |
| Verified independently | The finalization transaction moved exactly 24,150,000.000000 USDC from the bridge contract to one attacker address, at the exact second press reports. The submission transaction's raw calldata independently decodes to 5 signatures, a 7-validator address list, and a weight table summing to exactly 10,000, whose only three possible 5-of-7 signing totals are 7,142 / 7,143 / 7,144 - 7,142 being press's exact figure, reproduced here without reading it from press first |
| Fund flow, traced in full | All 24,150,000.000000 USDC left the attacker's Arbitrum address in 6 transactions to one contract, which forwarded it via Circle's CCTP (`cctp-forward`, decoded from the burn call's own event data); the same attacker address received 24,146,274.281809 USDC on Ethereum minutes later (a 0.0154% CCTP fee accounts for the gap), then forwarded all of it, in full, to a single Ethereum address. Neither the Arbitrum nor the Ethereum attacker address holds any USDC, WETH, or meaningful ETH today |

## The method

No primary source in this project's usual sense (a protocol's own GitHub
deployment registry) exists for AFX: `afx.trade` resolves to an unrelated
Venezuela-based exchange, and no AFX-branded GitHub organization was
found. The starting anchor is instead a transaction hash a CoinDesk
article cites for the finalization transaction. This project has twice
already found a fetch/search tool invent a plausible-looking hex string
that did not actually resolve on-chain (the Nesa and Enjin candidates
recorded elsewhere in this repo's issue tracker) - so Step 1 below is
exactly the check that would catch that, before anything else is trusted.

```bash
python3 reconstruct_exploit.py
```

Every number below is read live from Arbitrum's own public RPC
(`arb1.arbitrum.io/rpc`) and Ethereum's (`eth.drpc.org`, chosen because it
serves `eth_getLogs` over multi-thousand-block ranges with no API key;
`publicnode` rejects `eth_getLogs` outright for this project, and
`blastapi` caps ranges at 10 blocks).

1. **The press-cited transaction hash is checked, not trusted.** Its
   receipt is fetched live; its `status`, `to` address, block, timestamp,
   and its own `Transfer` event (amount and both addresses) are read
   directly from the raw receipt, not from any article's paraphrase.
2. **The token contract is identified live**, not assumed from the
   address alone: `name()` is called and decoded from the raw ABI output.
3. **The earlier submission transaction is found independently**, by
   scanning the bridge contract's own event log in the ~1,200 blocks
   before the finalization block for any other log it emitted, rather
   than being handed a second hash by any source.
4. **The submission's calldata is decoded by hand**, word by word, no
   ABI file available: a signature-count word, that many `(r, s, v)`
   triples, a validator-address array, and a weight array, each length
   read from the calldata itself before being trusted.
5. **The weight table's own arithmetic is checked against press's
   figure** by enumerating every possible 5-of-7 exclusion (there are
   only `C(7,2) = 21` ways to exclude 2 of 7, collapsing to 3 distinct
   totals given the validators' actual weights) and reporting where
   press's 7,142 falls among them.
6. **The full downstream fund flow is traced** on both chains via
   `eth_getLogs` on the USDC contracts, address-scoped, confirming both
   that 100% of the stolen amount left the attacker's Arbitrum address to
   one destination, and that the same amount (net of an implied CCTP fee)
   arrived at the same attacker address on Ethereum before being forwarded
   again, in full, to one further address.

## What it found

### The theft itself, confirmed to the exact second and the exact cent

Transaction `0x50d0b3ec6c3f5fce0f10abf81540bbb508f421494aa2b3480c4a264b0436547b`
resolves on Arbitrum, status `0x1`, block 486,658,838, timestamp
**2026-07-22T21:30:25 UTC**. Its own `Transfer` event on
`0xaf88d065e77c8cc2239327c5edb3a432268e5831` (independently confirmed live
as real USD Coin, `name()` returns "USD Coin") shows exactly
**24,150,000.000000 USDC** moving from `0xcb3b9a3e5668afe84dc7a864b36b845dce062e67`
(the bridge contract, verified deployed with real code, not an EOA) to
`0x2f2974fabc54dba33442261211c06bd20e0feefc` (the attacker). Both the
amount and the timestamp match every press outlet checked, to the dollar
and to the second, independently derived from the raw receipt rather than
copied from any of them.

### The submission, 210 seconds earlier: 5 signatures, a 7-validator table, and a reproduced 7,142

Scanning the bridge contract's own logs in the blocks just before the
finalization block finds one other event, emitted by transaction
`0x217c45c1272550e0439e53243f2987b7fb3f58b1d33c222597bbb71851b93f74` at
block 486,657,995, timestamp **2026-07-22T21:26:55 UTC**, exactly 210
seconds before finalization (matching press's "200-second challenge
period" description within rounding). This is the submission that
carried the validator signatures.

Decoding its 1,412 bytes of calldata by hand, with no ABI file available,
word by word:

- A word holding `5`: the number of `(r, s, v)` ECDSA signature triples
  that follow, matching press's "five validator signatures" exactly.
- A word holding `7`, followed by 7 addresses: the bridge's full
  validator set, decoded directly from the transaction's own bytes.
- A second word holding `7`, followed by 7 numbers
  (`1428, 1429, 1429, 1428, 1428, 1429, 1429`) that **sum to exactly
  10,000** - independently reproducing press's "10,000 voting units"
  figure without reading it from press first.

With 5 of 7 validators signing, exactly 2 are excluded. Enumerating all
`C(7,2) = 21` possible excluded pairs against this specific weight
multiset collapses to only 3 distinct possible signing totals:
**7,142 / 7,143 / 7,144** out of 10,000, depending on which 2 validators
(by weight) are the excluded pair. **7,142 is press's exact reported
figure**, and it is one of the 3 values this independent decode produces
from the raw calldata alone. This reconstruction did not perform ECDSA
signer recovery against the exploited contract's specific message-hash
scheme (undocumented, no ABI available), so it cannot name which 2 of the
7 validators were the excluded pair, only that the weight table itself,
decoded from nothing but the transaction's own bytes, is consistent with
and reproduces press's specific number.

The finalization transaction's own sender, `0x5553ea7bda594ade7afe91d279779a42b2b84208`,
is independently confirmed to be one of the 7 decoded validator addresses
(weight 1,429); the submission transaction's sender,
`0x32e3200d6e944cd9bd1c8c9865293b07206e7a01`, is not among the 7,
consistent with a permissionless relayer submitting the signed request on
the validators' behalf and a validator itself executing the finalization
once the challenge window passed.

### The fund flow, traced unit for unit across two chains

The attacker's Arbitrum address sent out **24,150,000.000000 USDC**, to
the last unit the exact amount received, in 6 transactions, all to one
Arbitrum contract (`0xb3fa262d0fb521cc93be83d87b322b8a23daf3f0`). That
contract's own transaction logs carry a UTF-8 tag, `cctp-forward`, decoded
directly from raw event data, identifying the path as Circle's own CCTP
(Cross-Chain Transfer Protocol) rather than a bespoke or third-party
bridge.

Minutes later, the same attacker address (no new address, no obfuscation
at this hop) received **24,146,274.281809 USDC** on Ethereum, in 6
mint-from-zero-address transactions, the standard signature of a CCTP
mint. The 3,725.72 USDC gap (0.0154% of the amount sent) is consistent
with CCTP's own fee structure, not an accounting error.

That Ethereum-side balance was then forwarded again, in full (8
transactions, executed by two different high-nonce third-party addresses
pulling from the attacker's own approval rather than the attacker sending
these transactions directly, consistent with an intent/solver-style fill
rather than a plain DEX swap), to a single further address,
`0x225a38bc71102999dd13478bfabd7c4d53f2dc17`. Press reports this leg as
the attacker buying "approximately 12,467.5 ETH"; this reconstruction
independently confirms the full USDC amount moved to that one address but
did not itself identify what protocol that address belongs to or trace
the ETH-denominated proceeds further, see Caveats.

Both of the attacker's own addresses, checked live today (2026-09-10, 50
days after the incident), hold no USDC, no WETH, and no meaningful native
balance: 0 USDC and 0 WETH on Ethereum, 0 USDC on Arbitrum, and 0.0000243
ETH, all consistent with full, immediate pass-through rather than any
funds still resting at an address this reconstruction can check.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with AFX, Halborn, CoinDesk, or any other outlet cited above.
- No official GitHub repository or contract-verification registry from
  AFX itself was found, and AFX's own domain (`afx.trade`) resolves to an
  unrelated exchange, so the incident is reconstructed entirely from raw
  Arbitrum/Ethereum chain data plus a transaction hash a press article
  supplied, independently verified rather than trusted (see "The method").
  Update 2026-09-16: AFX did publish its own technical postmortem on
  2026-07-31 ("A Detailed Post-Mortem on the AFX Security Incident",
  medium.com/@AFXTrade), not found when this entry was first written. It
  gives no loss figure, validator count or voting-unit figure, so none of
  the numbers above change. Its stated co-signing time, "July 22 21:27"
  UTC, matches the submission transaction's on-chain timestamp
  (21:26:55 UTC, re-fetched 2026-09-16). See
  `resultats_sources_2026-09-16.txt`.
- Mechanism wording: AFX's own postmortem describes attacker malware
  running on a subset of validator nodes (reached through an internal
  Ansible operations bastion) that "interfered with consensus-message
  handling", causing those validators to co-sign the withdrawal. It does
  not state that signing keys were exfiltrated. "Compromised signing
  keys" above follows DefiLlama's "Validator Key Compromised" label; the
  on-chain evidence (5 valid validator signatures) is consistent with
  either reading and cannot distinguish them.
- The excluded 2-of-7 validators (the ones whose keys were *not* used,
  i.e., not necessarily the compromised set) were not individually
  identified; this would require ECDSA signer recovery against the
  bridge contract's specific message-hash/domain scheme, which was not
  reverse-engineered here for lack of a verified ABI or source.
- The attacker's social-engineering origin (a fake "Oddium Lab" recruiter
  approach on 2026-07-09, per AFX) and the UNC4899/TraderTraitor (DPRK)
  attribution are reported here as the claims of Halborn and of AFX's own
  postmortem, not independently confirmed; this project has no forensic
  method for attributing an exploit to a specific threat actor.
- The final destination address on Ethereum
  (`0x225a38bc71102999dd13478bfabd7c4d53f2dc17`) was not identified as
  belonging to any specific named protocol; this reconstruction confirms
  the USDC arrived there in full but does not independently verify press's
  "~12,467.5 ETH" resulting purchase figure, since that would require
  tracing that contract's own internal accounting or a further hop this
  round did not pursue.
- As with every entry in this repo, this reflects a snapshot as of
  2026-09-10; balances at any address named above may have changed since.

## License

MIT
