# Aquifer (Sweeper Arbitrary Call) Postmortem

Independent reconstruction of the Aquifer exploit: an attacker got a
verified cross-chain "Sweeper" contract used in Aquifer's settlement flow
to execute an attacker-supplied call that redirected swept funds to their
own address instead of its legitimate destination, draining roughly 1,000
ETH-equivalent across Solana and Ethereum. Hours later, Aquifer's own
Solana upgrade authority signed and published an on-chain whitehat offer
directly to the attacker's wallets. This reconstruction starts from that
on-chain message, independently verifies its signer really is Aquifer's
real on-chain upgrade authority (not an impersonator), and reconstructs
the drain itself from the attacker's own receipts, live against Solana and
Ethereum mainnet.

## At a glance

| | |
|---|---|
| Incident | Arbitrary external call on a verified "Sweeper" settlement contract let the attacker redirect swept funds to their own address, on both Solana and Ethereum |
| Window | 2026-08-31 04:16:11 to 04:31:59 UTC (the drain); 16:43:27 UTC the same day (the on-chain whitehat offer); 2026-09-01 20:37:23 UTC (attacker consolidates and moves everything out) |
| Press/DefiLlama figure | DefiLlama: "Aquifer", $2,469,729, Solana, classification "Access Control", technique "Arbitrary External Call". Press (crypto.news via a secondary write-up) cites "roughly $2.5 million" |
| Verified independently | Attacker's Ethereum address received 1000.7955696018159 ETH across 3 transactions matching the exploit window to the second, then moved 1000.7955471888082 ETH out in one final transaction the next day. At CoinGecko's own 2026-08-31 (theft-day) price, that is $2,418,164 |
| A primary-source signer independently checked | The on-chain whitehat offer claims to come "from the upgrade authority of AQU1FRd7papthgdrwPTTq5JacJh8YtwEXaBfKU3bTz45"; querying that Solana program's real ProgramData account live confirms its actual upgrade authority is the exact address that signed the offer |

## The method

```bash
python3 reconstruct_exploit.py
```

No hardcoded press figures: every number below is read live from Solana
mainnet (`api.mainnet-beta.solana.com`), Ethereum mainnet
(`eth.drpc.org`, chosen because it serves historical `eth_getBalance` /
`eth_getBlockByNumber` without an API key, unlike most free-tier
providers), Blockscout's public indexer (used only to fetch a contract's
verified source and to look up indexed internal transactions, both
independently checked against a raw `eth_call` in Step 2 and against raw
`eth_getTransactionByHash`/`eth_getTransactionReceipt` in Steps 4 and 6),
and CoinGecko's public historical-price API.

1. **The starting anchor is on-chain, not a press address.** Aquifer's own
   Solana upgrade authority signed a Squads `VaultTransactionExecute`
   transaction carrying an `spl-memo` instruction: "AQUIFER WHITEHAT
   OFFER... From the upgrade authority of AQU1FRd7papthgdrwPTTq5JacJh8
   YtwEXaBfKU3bTz45, to the controller of [attacker's Solana and Ethereum
   addresses]... Return >=80% of exploited value... by 3 Sep 2026, 14:00
   UTC." This reconstruction starts from that transaction
   (`u1hoSUTzhe3hhnGiUiwvjtzd9Ji8EQPxjnTSKtW2hHDqY9ukYySftNp9eMHsBHsYezBKFcNyoZapYHYu4XaaZbQ`),
   not from any address a press article supplied.
2. **The claimed signer is checked against the program's real authority.**
   `AQU1FRd7papthgdrwPTTq5JacJh8YtwEXaBfKU3bTz45`'s own `programData`
   account (`GrHYWjuGETV5pZgUZLfzvvQEugYk6SutwHUPxFjrHda6`) is queried
   live; its `authority` field is `8pJhHxPQRiUGdtVSCNPyP9AH994zeyYEBGb5yZ
   RzheSA`, byte-for-byte the same address the memo names as its signer.
   The offer is authentic.
3. **The attacker's Solana wallet's full history** (379 signatures,
   paginated to its genesis) is read live and confined to a single
   calendar day, 2026-08-31, confirming a purpose-built exploit wallet.
4. **The Ethereum-side drain** is read from the attacker's own address's
   indexed internal transactions, cross-checked against
   `eth_getTransactionByHash`/`eth_getTransactionReceipt` for the
   top-level calls, not assumed from any summary.
5. **The exploited call is decoded from a verified contract's real ABI**,
   fetched from Blockscout and independently cross-checked with a live
   `eth_call` to the contract's own `executor()` getter.

## What it found

### The whitehat offer, and why it can be trusted

Aquifer's real on-chain upgrade authority genuinely signed the memo
addressed to the attacker. That is not something a press article can
assert; it is something anyone can check the same way this reconstruction
did, by reading the program's own `programData` account. This is the same
kind of check this repo already runs for a multisig's `getOwners()`,
applied to a Solana program's upgrade authority instead.

### The drain: three transactions, one attacker address

| Tx | Block time (UTC) | Amount received |
|---|---|---|
| `0x5085bbe5…d91396b` | 2026-08-31 04:16:11 | 871.860173070678342810 ETH |
| `0x3a3465bf…5fe4cb16` | 2026-08-31 04:22:35 | 122.509397867786333336 ETH |
| `0xad8e66e1…ce32964097` | 2026-08-31 04:31:59 | 6.425998663351236928 ETH |

**Total received: 1000.7955696018159 ETH.** The first two arrived as
internal transactions (value moved inside another transaction's
execution, invisible to a plain `eth_getTransactionByHash` "value" field
and read here from Blockscout's indexed internal-transaction view
instead, the same category of data this repo has used before for
contract-mediated transfers); the third is a plain top-level transfer,
read directly from the RPC.

The first two both trace back to a call on
`0x8d04cc7e86e687854eb41d9d43512b655b93184b`, a contract Blockscout's own
indexer labels "Sweeper" and whose Solidity source was verified there on
2026-09-08 (8 days after the exploit). Its method, decoded against that
verified ABI: **`sweepAndExecute`**, with an `execution` parameter naming
real mainnet USDC (`0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`), an
amount of `2119478923113` (2,119,478.923113 USDC at 6 decimals), and a
recipient field set to the attacker's own Ethereum address. Calling
`executor()` live on the Sweeper contract returns
`0x067cb62f4dcc0a45edcb6b7c018d4077abd10c67`, confirming this is the
contract's own designated (and, on this call, apparently
attacker-redirectable) settlement target, not an unrelated third
contract. This matches DefiLlama's own classification of the incident
("Access Control" / "Arbitrary External Call") with an actual decoded
call, not just the label.

Neither the Sweeper contract nor its designated executor ever shows a
resting native-ETH or USDC balance at any block boundary queried here
(before the first drain, after each drain, and today): both operate as
pass-through settlement contracts that pull, convert, and forward within
a single transaction rather than holding custody between blocks, which is
why this entry verifies the drain from the attacker's own receiving
address instead of a vault's before/after balance, the same substitute
this repo's Allbridge entry already used when a router, not a resting
vault, was what moved the funds.

### The consolidation, and the deadline that passed

On 2026-09-01 at 20:37:23 UTC, the attacker's Ethereum address sent
**1000.7955471888082 ETH** in a single, successful transaction
(`0x728294f756bf1f2f35fb32d9c5a18b5f65f9e78cdc2fae72544a64ffb8004800`,
status `0x1`) to `0x200e52350fbc579c96bad87b6ef782c1f962dffd`. That
destination address's prefix/suffix pattern (`0x200e…DFfD`) matches a
cluster of clearly fake, zero-value "poisoning" tokens this same
reconstruction found littering the attacker's own transaction history
(fake "ETH" and "Ether.." tokens all carrying the identical bogus value
`1000795547188808275967`); this entry does not claim to know whether that
destination is a second wallet the attacker actually controls or an
address-poisoning trap the attacker fell for while moving their own
funds, and reports the transaction only as what it verifiably is: the
attacker's real, successful, final move of the entire drained amount.

Checked live today (2026-09-10, a week after the 2026-09-03 14:00 UTC
whitehat deadline): the designated recovery addresses hold 0.980001878
SOL and 0.001550501933366716 ETH, respectively, neither remotely close to
80% of 1000.8 ETH. The whitehat deal was not honored.

### The dollar figure, and a same-day price gap that explains the press number

1000.7955696018159 ETH at CoinGecko's own 2026-08-31 (theft-day) daily
price ($2,416.24) is **$2,418,164**, the figure this entry reports as
independently verified. At CoinGecko's 2026-09-01 price ($2,466.57), the
same ETH amount is $2,468,528, within 0.05% of DefiLlama's own tracked
$2,469,729 for this incident. The two prices bracket DefiLlama's figure
because the attacker did not move the stolen ETH out as one lump until a
day after the actual drain; whichever exact hour DefiLlama's own pipeline
priced this at, it lands inside that one-day gap, not on the theft
timestamp itself. This entry uses the theft-day price because that is
when the loss actually happened, not when the attacker later chose to
move it.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Aquifer or any outlet cited above.
- The Sweeper contract's source was verified on Blockscout only after the
  exploit (2026-09-08); this entry cannot confirm what the contract's
  source looked like, or whether it had already been patched, at the
  exact moment of the 2026-08-31 04:16 UTC drain, only what the verified
  bytecode now deployed at that address decodes to.
- 2,119,478.923113 USDC appears as the `execution.amount` parameter inside
  the exploited call, but this entry does not independently trace where
  that USDC itself came from (a specific Aquifer pool address was not
  identified, since neither the Sweeper nor its executor ever rests with
  a balance), nor does it reconcile that USDC figure precisely against
  the final 1000.8 ETH figure; some of the drained value may also reflect
  WETH or other assets swept in the same call. The 1000.8 ETH figure this
  entry reports as the verified loss is what the attacker's own address
  actually received and moved, independent of how that value was
  assembled inside the exploited call.
- Whether the attacker's Solana-side activity (379 transactions on
  2026-08-31) caused a separate, additional dollar loss on top of the
  1000.8 ETH figure above, or was itself the mechanism that fed value
  into this same Ethereum-side total (the article's own framing, "wallets
  on Solana and Ethereum," describes one combined figure, not two), was
  not independently separated here.
- The identity or intent behind `0x200e52350fbc579c96bad87b6ef782c1f962dffd`
  (the final destination of the swept ETH) was not determined; see above.
- As with every entry in this repo, this reflects a snapshot as of
  2026-09-10. The recovery-address balances and whether the swept funds
  move again after this reconstruction's run were not re-checked after
  it.

## License

MIT
