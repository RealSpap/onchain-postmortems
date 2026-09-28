# Limit Break Payment Processor V2 Forwarder Spoof Post-Mortem

Between September 25 and September 28, 2026, 541.375935595563059375 WETH left 978 Ethereum wallets through Limit Break's Payment Processor V2, in 1,072 recorded fills that none of those wallets sent. Another 8,426.531308 USDC left 63 wallets, 548,722.897850195194444065 WILD left 11, and 12.934036415936827524 APE left 2, the same way. DefiLlama records the incident with no amount. Coverage describes it as legacy Magic Eden approvals being abused, and one outlet reports "$1.7 million in NFTs stolen across three transactions", a figure that mixes the NFT side with the WETH side.

The stale approvals were the fuel, not the flaw. What this reconstruction found is that Payment Processor mis-identifies the buyer when a call reaches it through a trusted forwarder. It reads the buyer from the tail of the calldata handed to its trading module, but it copies that calldata from an ABI offset the caller supplies, and the fills here all supply an offset that shifts the copy so the forwarder's honestly-appended address is dropped and a different 20 bytes take its place. Payment Processor then settles the attacker's listing of a worthless NFT against that mis-read wallet's approved tokens. The registry `registre_hypotheses.csv` states each of these facts as a falsifiable claim with its on-chain locator; `reconstruct_exploit.py` re-derives every number here live.

The drains were still ongoing at the end of the observation window: 1.004216962060165451 WETH moved this way on September 28 alone, up to block 26077995 at 19:18:23 UTC.

## At a glance

| | |
|---|---|
| Victim | Wallets that had approved Limit Break's Payment Processor V2 as an ERC-20 operator, many via Magic Eden's former EVM marketplace |
| Contract | Payment Processor V2 `0x9a1d00bed7cd04bcda516d721a596eb22aac6834`, its trading module `0x9a1d0059f5534e7a6c6c4dae390ebd3a731bd7dc`, verified source on Sourcify |
| Chain | Ethereum (press also reports Polygon, Base, ApeChain; this entry covers Ethereum only) |
| Date | First observed fill 2026-09-25 08:26:11 UTC (block 26053260); still active at 2026-09-28 19:18:23 UTC |
| Mechanism | A trusted-forwarder path lets the caller choose the calldata offset Payment Processor copies from, so the trading module reads an attacker-chosen wallet as the buyer instead of the forwarder's appended caller. The victim's standing token approval then funds the attacker's zero-value NFT listing |
| WETH taken | 541.375935595563059375 WETH from 978 wallets in 1,072 fills |
| Other tokens taken | 8,426.531308 USDC (63 wallets), 548,722.897850195194444065 WILD (11 wallets), 12.934036415936827524 APE (2 wallets) |
| Dollar value of the WETH | About $1,453,688 at the first drain's block (Chainlink ETH/USD 2685.17247359 at block 26053260); about $1,462,114 with the USDC added |
| By day (WETH) | 2026-09-25: 532.651363735049749148 in 981 fills; 26th: 4.289110204423406696 in 41; 27th: 3.431244694029738080 in 33; 28th: 1.004216962060165451 in 17 |
| Largest single transaction | `0xdd3ab342cfcf979ed67988321e5541589426a80c43d52bc4514ca969c1e7a96b`, block 26053260, 25 wallets, 281.656429171682959990 WETH to seller `0x860bb7ce155d0a14574ce10033bec2c981739c8d`, matched against raw WETH Transfer logs |
| Distinct senders | 32 externally-owned accounts sent the 232 drain transactions; not one victim sent the transaction that charged it |
| Forwarder used for the ERC-20 drains | Clone `0xb48d6af77c5e3b99876ea71b38e9c814ba5b1c8e`, a `TrustedForwarderFactory` (`0xff0000b6c4352714cce809000d0cd30a0e0c8dce`) clone with `signer()` == 0 (open mode), so it appends its caller with no signature required |
| Forwarder provenance | Created 2026-09-25 05:27:11 UTC by the rescue wallet `0x71cf3f5724bd2b72ef6464992acd26216de7fe33` (tx `0xfe776ec0ca4be969f4b50d6f137f4dd9fb2d47606526a2d7f1a4089d197525ba`); the factory clones are permissionless, so the forwarder identity is not itself the vulnerability |
| DefiLlama | `Limit Break Payment Processor`, amount null, classification Access Control / Token Approval Abuse, source field empty |
| Status | Ongoing at end of window. Blockaid and RevokeCash urged affected wallets to revoke Payment Processor approvals (Ethereum, Polygon, Base) |

## Fund flow

```mermaid
flowchart LR
    ATT["attacker EOA<br/>32 senders"]
    FAKE["fresh NFT contract<br/>119 deployed after the attack began"]
    FWD["open-mode forwarder<br/>0xb48d...1c8e"]
    PP["Payment Processor V2<br/>0x9a1d...6834"]
    VICT["approved wallet<br/>read as the buyer"]
    WETH["victim's WETH"]

    ATT -->|"deploy + list at zero"| FAKE
    ATT -->|"forwarded call, shifted offset"| FWD
    FWD -->|"buyer read as VICT, not the forwarder's caller"| PP
    PP -->|"pull approved tokens"| WETH
    WETH -->|"listing proceeds"| ATT
    VICT -.->|"standing operator approval"| PP
```

*Fig. 1: how one wallet's tokens are pulled. Addresses truncated for display.*

## The method

Payment Processor V2 is a monolithic router that `delegatecall`s into four modules. Its own comments say it is "designed to work both via direct calls and calls from a trusted forwarder that preserves the original msg.sender by appending an extra 20 bytes to the calldata." The trading module builds its trade context with `taker: appendedDataLength == 20 ? _msgSender() : msg.sender`, and `_msgSender()`, from Limit Break's own `TrustedForwarderERC2771Context`, returns the last 20 bytes of the calldata when the immediate caller is a factory-registered forwarder.

The reconstruction traced the transactions that moved the tokens and read the exact bytes at each hop. In the largest transaction, the call that entered Payment Processor was a `buyListing(bytes)` (selector `0xc32dacae`) whose `bytes` argument declared an offset of 0 rather than the ABI-correct 32. Payment Processor copies `calldatasize - 68` bytes from that offset into the module. With the offset short by 32 bytes, the copy begins 32 bytes early and ends 32 bytes early: the 20 bytes the forwarder honestly appended (the attacker's own contract) fall past the end of the copied region, and a 20-byte value sitting 32 bytes earlier in the buffer lands in the taker slot instead. In that transaction the forwarder appended `0x860bb7ce...739c8d`, but the module read `0xede4e6d7...95a2373`, which is exactly the wallet the first fill then charged. So Payment Processor validated the attacker's maker signature on a listing of a worthless NFT, treated a victim who signed nothing as the buyer, and pulled that victim's approved WETH to pay for it.

Three checks confirm this is the whole story and not a coincidence of one transaction:

- **The buyer never sent the transaction.** Across all 1,150 token fills on freshly-deployed NFT contracts, the wallet charged (the fill's buyer) is never the account that sent the transaction. 32 attacker EOAs sent the 232 transactions; the 978 drained WETH wallets sent none of them.
- **The NFTs are worthless props.** 119 of the 121 NFT contracts involved had no code at block 26047000, before the first theft: they were deployed during the attack. The two pre-existing contracts account for 0.16 WETH total and are excluded from the headline figure.
- **Every drain took the shifted-offset path.** Of the ERC-20 drains, 499 of the sampled module entries came through the same open-mode forwarder with a declared offset of 0; the module read a different address as taker than the forwarder appended, in every one checked.

The 2026-09-24 NFT-side transactions (the ones press first noticed) use the same primitive from a different forwarder: the earliest, `0x9050e28e...`, entered Payment Processor 70 times through forwarder `0xb233e360...` with the same zero offset, moving approved NFTs to attacker addresses instead of WETH.

## What it found

**The approvals are old, but the read is the bug.** Coverage frames this as Magic Eden's expired approvals catching up with users, which is why the funds were reachable at all. But an expired-approval story alone would have the approved operator spend on its own behalf. Here the operator is made to act as if a victim initiated a purchase they never signed. The defect is that Payment Processor trusts a caller-supplied calldata offset to locate the bytes it then treats as the authenticated caller, so a trusted forwarder's integrity guarantee (it appends the real caller, unforgeably) is bypassed downstream by shifting where those appended bytes are read from.

**The forwarder is not the villain, and neither is the rescue wallet.** The open-mode forwarder used for the WETH drains was created by `0x71cf3f57...`, the same address press names as the white-hat rescue wallet, three hours before the first WETH drain. The `TrustedForwarderFactory` clones forwarders permissionlessly and marks them trusted, so any forwarder, whoever deployed it, is a valid entry point for this. This entry does not attribute the WETH drains to the rescuer: 32 distinct EOAs sent the transactions, and the forwarder is a shared, open utility. It is noted only because it shows the "trusted" set is open by construction.

**DefiLlama has no dollar figure and press figures conflict.** DefiLlama logs the incident with `amount: null`. The Block reports 23,155 NFTs rescued (> $5.7M) and about 660 WETH at risk. CryptoTicker gives 530.7 to 537.5 WETH from 911 to 949 wallets. This reconstruction's 541.375935595563059375 WETH from 978 wallets is the sum of every zero-NFT ERC-20 fill in the window, which is a slightly wider count than a single-day snapshot and explains the gap. The "$1.7 million in NFTs" figure (Phemex, citing Blockaid) is the WETH side valued in dollars, not NFTs.

## What this does not establish

The reconstruction covers the Ethereum WETH/USDC/WILD/APE drains and the NFT-side primitive. It does not measure the Polygon, Base or ApeChain losses, and does not value or count the NFTs moved. The dollar figure applies Chainlink ETH/USD at the first drain's block to the whole WETH total; it is not re-priced per block. Fund flow past each attacker EOA (the cash-out) is not traced. Whether Limit Break has since paused or patched Payment Processor V2 is not asserted here; the drains were still landing at the end of the window. No Limit Break technical post-mortem was found as of 2026-09-28; if one appears it should be checked against the four facts this entry rests on: the buyer never sent the transaction, the NFTs are freshly-deployed props, the module reads a different taker than the forwarder appended, and the declared calldata offset is 0.

## Caveats

The dollar figure in the index is the WETH quantity valued once, at the first drain's block, and is not a claim about realized proceeds. The block window is 26040000 to 26078000; fills after block 26077995 are outside it and the total is a floor, not a final tally. The largest-transaction cross-check confirms the event sums against raw WETH Transfer logs for that one transaction only. Two RPC providers are rotated with silent fallback on the wide `eth_getLogs` scans, so those queries are only as independent as the fallback allowed. Section 7 of the script samples the first drain transaction of each sender for the trace-level offset check rather than tracing all 232.

## License

MIT, same as the rest of this repository. The evidence files in `preuves/` are raw tool output and are reproduced as generated.
