# Verus-Ethereum Bridge (Forged Proof) Postmortem

Independent on-chain reconstruction of the first of two 2026 exploits
against the Verus-Ethereum Bridge: an attacker forged a cross-chain proof
root and got the bridge's own Ethereum contract to release funds against
an export that never existed on the Verus chain, draining tBTC, USDC, and
ETH from the contract in a single transaction. Starting from a contract
address VerusCoin's own mobile-wallet repo hardcodes (not a press-supplied
address), this reconstruction independently confirms the drain from raw
transaction logs and an internal ETH transfer, cross-checked against 3
public RPC endpoints, and lands within 2.4% of DefiLlama's own tracked
figure. VerusCoin's own GitHub release notes independently corroborate
the date and the roughly 26.6% loss of bridge reserves. A second,
technically distinct exploit hit the same contract in July; this entry
confirms that transaction happened and itemizes what it drained, but does
not re-price it to a dollar total (see Caveats).

## At a glance

| | |
|---|---|
| Incident | A forged notarization proof root passed the Ethereum bridge contract's verification, letting the attacker claim an "import" backed by an export that was never actually sent from the Verus chain |
| Window | 2026-05-17T23:55:23 UTC, one transaction |
| Press/DefiLlama figure | DefiLlama tracks this as "Verus-Ethereum Bridge", $11,500,000, dated 2026-05-17, classification "Bridge & Cross-Chain" / "Forged Proof". Press (CoinDesk, crypto.news, etc.) cites "$11 million" to "$11.6 million" depending on outlet and which day's price they used |
| Verified independently | One transaction (`0x6990f01...eb321`) moved 103.567660170000000000 tBTC, 147,658.836798 USDC, and 1,625.366886490000000000 ETH from the bridge contract to one attacker address. At CoinGecko's own 2026-05-17 (theft-day) prices, that totals **$11,775,898.10** |
| Official acknowledgment | VerusCoin's own GitHub release (Verus-Desktop v1.2.17, 2026-07-03) states the network lost "about 26.6% of the ETH and tBTC held in the Ethereum contract" after "the May 17th exploit" |
| Second exploit (context only) | A technically distinct exploit hit the same contract on 2026-07-23T03:45:59 UTC (confirmed live), draining 7 tokens to a different address. DefiLlama tracks it separately at $7,530,000. Not re-priced here |

## The method

```bash
python3 reconstruct_exploit.py
```

No hardcoded press figures beyond what is explicitly labeled as press
context. Every number in "What it found" is read live from:
- Ethereum mainnet, via 3 independent public JSON-RPC endpoints
  (`ethereum.publicnode.com`, `eth.merkle.io`, `eth.drpc.org`), used to
  cross-check the exploit transaction's own receipt and logs, not assumed
  from any one provider.
- Blockscout's public API (`eth.blockscout.com/api/v2`), used only to
  fetch a contract's verified source/metadata and one address's indexed
  internal-transaction view, both cross-checked against raw
  `eth_getTransactionReceipt` data.
- GitHub's own Releases API and raw file content
  (`raw.githubusercontent.com`), used to read VerusCoin's own
  primary-source files directly, not a scraped changelog page.
- CoinGecko's public historical-price API, for the USD conversion.

**The starting anchor is not a press-supplied contract address.**
VerusCoin's own `Verus-Mobile` wallet repo
(`github.com/VerusCoin/Verus-Mobile`,
`src/utils/constants/web3Constants.js`) hardcodes:

```js
export const VERUS_BRIDGE_DELEGATOR_MAINNET_CONTRACT = "0x71518580f36FeCEFfE0721F06bA4703218cD7F63"
```

found via a GitHub code search scoped to `org:VerusCoin` for the exact
address, not the other way around. That address is independently
confirmed as a verified Ethereum contract (Blockscout), named
"Delegator", **verified 2024-12-01**, well over a year before either 2026
exploit, so its published source was not backfilled after the fact. That
source imports `../Storage/StorageMaster.sol` and
`../VerusBridge/Token.sol`, matching the folder layout of VerusCoin's own
public `Verus-Ethereum-Contracts` repo exactly.

## What it found

### The drain: one transaction, three assets, one attacker

Transaction
[`0x6990f01720f57fc515d0e976a0c4f8157e0a9529194c4c15d190e98d087eb321`](https://etherscan.io/tx/0x6990f01720f57fc515d0e976a0c4f8157e0a9529194c4c15d190e98d087eb321),
block 25,118,335, timestamp **2026-05-17T23:55:23 UTC** (read from
`eth.merkle.io`'s receipt-embedded `blockTimestamp` field and
cross-checked against Blockscout's own reported timestamp for the same
block), status success, called by a plain EOA
(`0x5abb91b9c01a5ed3ae762d32b236595b459d5777`, no contract code) against
the bridge's Delegator contract. All 3 RPC endpoints queried return
byte-identical receipts.

Two ERC20 `Transfer` events, decoded directly from the raw log
topics/data, both moving funds from the bridge contract to
`0x65Cb8b128Bf6e690761044CCECA422bb239C25F9` (also a plain EOA):

| Token | Address | Amount |
|---|---|---|
| tBTC | `0x18084FBA666a33d37592FA2633fD49a74DD93A88` | 103.567660170000000000 |
| USDC | `0xA0b86991c6218b36c1d19D4A2e9Eb0cE3606eB48` | 147,658.836798 |

The tBTC leg's token contract is independently confirmed via a live
`eth_call`: `symbol()` returns `"tBTC"`, `name()` returns `"tBTC v2"`,
matching press's description of Threshold Network's tokenized bitcoin.
The USDC address is Ethereum's canonical USDC contract.

A third leg, **1,625.366886490000000000 ETH**, does not appear in the
transaction's logs at all, because native ETH transfers never emit an
ERC20 `Transfer` event. It is confirmed instead as an internal transfer
inside the same transaction, read from Blockscout's indexed
internal-transactions view for the attacker's own address and filtered to
this exact transaction hash: same source (the bridge contract), same
destination (the attacker), same transaction hash.

### The dollar figure

At CoinGecko's own 2026-05-17 historical daily prices (ETH $2,180.0891,
tBTC $78,063.3137, USDC $0.99973):

| Leg | Amount | USD |
|---|---|---|
| ETH | 1,625.36688649 | $3,543,444.65 |
| tBTC | 103.56766017 | $8,084,834.74 |
| USDC | 147,658.84 | $147,618.71 |
| **Total** | | **$11,775,898.10** |

This is about 2.4% above DefiLlama's own tracked $11,500,000 for the same
date, a gap consistent with which exact hour's price DefiLlama's own
pipeline used versus this entry's own daily-close snapshot; both figures
agree closely on the underlying native-unit amounts (~103.6 tBTC, ~1,625
ETH, ~147,000-148,000 USDC), which press independently reported.

### The mechanism, in VerusCoin's own words

VerusCoin did not just quietly patch this and move on. Their GitHub
release v1.2.17 (2026-07-03) is an unusually detailed public accounting,
explicitly naming "the May 17th exploit" and stating the network lost
"about 26.6% of the ETH and tBTC held in the Ethereum contract" (after
some asset recovery), leaving the vETH/tBTC.vETH currencies "only 73.4%"
backed. A separate, longer official writeup (a Google Doc linked directly
from release v1.2.17-3) explains the actual root cause: the Verus
PBaaS daemon and the Ethereum contract disagreed on how to interpret a
cross-chain notarization, letting the attacker's forged output be
"interpreted by the contract as a completely different output type than
what the daemon considered it to be" without ever proving a real export
existed on the Verus chain, which is exactly what DefiLlama's own
"Forged Proof" technique label captures.

### The second exploit (2026-07-23): confirmed, not re-priced

The same bridge contract was hit again on **2026-07-23T03:45:59 UTC**
(transaction
[`0xa1f1e65c1cea4dba4ae439cd4dcdba6cc2dbda0ed1228e61f29ae9c9324eb099`](https://etherscan.io/tx/0xa1f1e65c1cea4dba4ae439cd4dcdba6cc2dbda0ed1228e61f29ae9c9324eb099),
block 25,592,836, status success on 2 independent RPC endpoints). Direct
`Transfer` events from the bridge contract to a different loot wallet
(`0xCFd0A20703cD11E0b9f665e1C3F1Ef989C142D54`), decoded and identified
live via `eth_call symbol()` for each token:

| Token | Raw amount |
|---|---|
| tBTC | 71,504,591,500,000,000,000 |
| MKR | 59,429,543,840,000,000,000 |
| USDC | 149,275,074,098 |
| USDT | 78,300,537,681 |
| EURC | 31,475,664,323 |
| scrvUSD | 92,784,360,277,250,000,000,000 |
| DAI (minted, not transferred from an existing balance) | 220,357,027,072,980,000,000,001 |

VerusCoin's own writeup states, unambiguously, that this was a
**different zero-day** from the first exploit (a map-deserialization
asymmetry, not the same output-type confusion), contradicting a press
claim (Blockaid, via a July 2026 cryptotimes.io article) that "both
attacks targeted the same contract through the same import route,"
implying an unpatched, reused bug. Press separately reports the attacker
also consolidated the drained basket into roughly 3,916 ETH via DEX
routes over the following ~15 minutes; this reconstruction independently
confirms native ETH did move into the loot wallet afterward (via
Blockscout's internal-transactions view) but did not sum that
consolidation to a total, for the reasons in Caveats below.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with VerusCoin, Threshold Network, or any outlet cited
  above.
- The 3 asset legs of the first exploit (tBTC, USDC, ETH) are each
  individually verified from raw on-chain data. The combined $11,775,898
  figure depends on CoinGecko's historical daily-close prices, which are
  a snapshot, not the exact price at block 25,118,335's timestamp; this
  is the same convention every other USD figure in this repo uses.
- The second exploit (2026-07-23) is confirmed to have happened, hit the
  same contract, and drained exactly the 7 tokens listed above, all
  independently decoded from raw log data. It is deliberately **not**
  converted to a dollar total here: unlike the first exploit's clean,
  single-transaction, 3-asset drain, the second exploit's proceeds were
  swapped and consolidated across roughly a dozen further transactions
  before landing as ETH in the loot wallet, and fully and correctly
  reconstructing that consolidation (avoiding double-counting swap legs,
  correctly attributing DEX fees/slippage) was judged to need more
  verification than this round's time allowed. DefiLlama's own tracked
  figure for that date ($7,530,000) is reported above as sourced, not
  independently re-derived.
- The DAI amount in the second exploit's table (`220,357,027,072,980,000,
  000,001`, i.e. ending in a stray `1` at 18-decimal precision) is
  reported exactly as decoded from the raw log data; this entry does not
  speculate on why that trailing unit exists.
- The caller EOA for the first exploit
  (`0x5abb91b9c01a5ed3ae762d32b236595b459d5777`) and the beneficiary EOA
  that received the funds (`0x65Cb8b128Bf6e690761044CCECA422bb239C25F9`)
  are different addresses; this entry does not trace any further
  relationship between them beyond what the transaction itself shows.
- As with every entry in this repo, this reflects a snapshot as of
  2026-09-10. Neither attacker address's current balance or subsequent
  fund movement was re-checked after this reconstruction's run.

## License

MIT
