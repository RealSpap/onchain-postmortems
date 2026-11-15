# FH Token (Falcon Heavy) Pair Drain, Post-Mortem

On August 25, 2026, at 09:54:52 UTC, one transaction on BNB Chain took 19,999.018106552928530404 USDT out of the FH Token / USDT PancakeSwap V2 pair, 99.998% of the USDT it held. The token's own transfer code treats every transfer into the pair as a sale, and on a sale it burns 80% of the net amount and moves the other 20% out of the pair's own FH balance and calls `sync()` on the pair before it credits the seller's FH to the pair. For the router that prices the swap, the pair then holds far less FH than it really will, so each sale is paid at a price that is too high. An attacker's contract borrowed 25,999.35 USDT from a lending pool, bought FH through a router the token whitelists, and sold it back, 25 times in one transaction; the USDT it paid into the pair in its 25 purchases was 33,401.19 and the pair paid back 53,400.21. The loan was repaid and the difference went to the attacker's EOA.

DefiLlama lists $20,000 for "FH Token" on 2026-08-25 and classes it "Protocol Logic" / "Swap Logic Flaw"; a public proof of concept in the DeFiHackLabs repository gives the transaction and the addresses. This entry re-derives the sequence from the chain and from the token's verified source: the sale branch of the transfer function, the whitelist, the router's public `sweepToken`, the pair's reserves one block before and after, the receipt's 508 logs, the attacker's eight transactions, and the value. It does not trace the calls (no public node serves the trace of this block); with a verified token it does not need to.

The registry `registre_hypotheses.csv` states each fact as a falsifiable claim with its locator; `reconstruct_exploit.py` re-derives every on-chain number here live, check by check.

## At a glance

| | |
|---|---|
| Victim | The FH/USDT PancakeSwap V2 pair `0x8f2d1a3992856a860304f1b86534b6b129cc4df7` (token0 USDT, token1 FH Token `0xdcf0dfe0053677a67610c6d08ea1f5c78df8ca37`), that is, its liquidity providers |
| Chain | BNB Chain |
| Date | 2026-08-25, 09:54:52 UTC, block 117979402, transaction index 62, tx `0x7a3cadc2f33e000b0091307df62db2f5cc79ab8e0b022fd84de9e1c2c0745bd2` |
| Mechanism | In `FHToken._transfer`, a transfer whose recipient is the pair is a sale: it sends the fee to a wallet, burns 80% of the net amount out of the pair, sends the other 20% from the pair to the treasury, calls `sync()` on the pair, and only then credits the seller's net FH to the pair. Buying is gated by a whitelist that includes a public router, `0x1b81d678ffb9c0263b24a97847620c99d213eb14`, whose `sweepToken` hands its whole balance of a token to any address the caller names |
| Attacker | EOA `0x7fa3bc0d5667ffd14d7acd6ce5f2432ac13a6fda`, whose fifth transaction this was; it ran the contract `0x727fb666e3f2531e807e987532c6e2c22adc45ad` that it had created seven days earlier |
| Loss | 19,999.018106552928530404 USDT, the pair's USDT reserve one block before (19,999.5) minus after (0.481893447071469596), counted at face value |
| Funds | All of it went to the attacker's EOA in the last log. Five days later the EOA sent 100 and 19,899.018126552928530404 USDT, 19,999.018126552928530404 in all, to `0xb4e283f6f20e68bac259fe7a84154363b63b05db`, an address without Sourcify verification; the trail stops there |
| Press figures | DefiLlama: $20,000 (FH Token, BSC, "Protocol Logic" / "Swap Logic Flaw", source empty), 0.01% over the value found here. DeFiHackLabs: 19,999.018106552928530404 USDT (about $20K), with the date of the transaction written as 2026-08-23 in the comment of its proof of concept; the chain says 2026-08-25 |

## What the token does on a sale

The token is verified on Sourcify (exact match, `FHToken`, solc 0.8.34). Its `_transfer`, for a transfer to the pair from a sender that is not the pair and not excluded from fees, runs this sale branch (condensed; the comment is translated from the Chinese):

```solidity
} else if (isSell) {
    feeAmount = (amount * sellFee) / FEE_DENOMINATOR;
    uint256 netAmount = amount - feeAmount;
    if (!inSwap) {
        inSwap = true;
        if (feeAmount > 0) { super._transfer(sender, SLIPPAGE_WALLET, feeAmount); }
        // net sale: 80% burned, 20% to the treasury
        if (netAmount > 0 && totalSupply() > targetSupply) {
            uint256 burnAmount = (netAmount * 80) / 100;
            uint256 treasuryAmount = netAmount - burnAmount;
            if (burnAmount > 0) { _burn(pair, burnAmount); totalBurned += burnAmount; emit TokensBurned(sender, burnAmount); }
            if (treasuryAmount > 0) { super._transfer(pair, TREASURY_WALLET, treasuryAmount); }
            try IUniswapV2Pair(pair).sync() {} catch {}
        }
        super._transfer(sender, recipient, netAmount);
        inSwap = false;
    }
    ...
}
```

The burn and the treasury transfer take FH out of the pair's balance, `sync()` records that smaller balance as the reserve, and the seller's net amount arrives after. The pair's recorded FH reserve is cut by the burned and treasury FH while the FH being sold arrives only after, so the swap is priced against a pair that looks nearly empty of FH: in the first cycle the attack contract pays 19,799.505 USDT in and gets 35,460.85159856576 USDT back for the FH it sells. The exact pricing arithmetic of the swap was not re-derived here. Nothing in this branch looks at who the seller is.

The buy side is gated: a transfer out of the pair needs the sender and the recipient on `isBuyerWhitelist`. The constructor whitelists, among others, `0x1b81D678ffb9C0263b24A97847620C99d213eB14`, which is verified on Sourcify as a `SwapRouter` (built from the Uniswap V3 periphery code, solc 0.7.6); its `sweepToken(token, amountMinimum, recipient)` is `public payable` and sends its whole balance of the token to the recipient the caller gives, with no check on the caller. One block before the attack the router is on the whitelist on chain and the attacker's contract is not. So the attacker's contract has the pair send each purchase to the router and then asks the router to sweep the FH back to itself.

## The exploit, from the receipt

The receipt has 508 logs. In order: the lending pool Moolah (verified) sends the attack contract 25,999.35 USDT; then 25 times the attack contract buys with a USDT amount that shrinks from 19,799.505 to 0.697 (the same 25 sizes as in the public proof of concept) and sells all the FH it got. In each of the 25 sales the logs show, in this order, 80% of the net amount burned out of the pair, the other 20% moved from the pair to the treasury wallet, a Sync of the pair, and only then the net FH credited to the pair: 25 of 25, and the burn is exactly `net * 80 // 100` each time. The pair emits 50 Swap events. The attack contract paid 33,401.193110175201444095 USDT into the pair in its 25 purchases and received 53,400.211216728129974499 USDT from it in its 25 sales; the difference, 19,999.018106552928530404, is the pair's whole USDT fall, to the wei. The loan goes back to Moolah, and the last log sends the 19,999.018106552928530404 USDT to the EOA.

The pair held 19,999.5 USDT and 200,000 FH one block before the transaction and 0.481893447071469596 USDT and 0.006969714567965646 FH after.

## What came before and after

The EOA has sent eight transactions in all, every one read. On 2026-08-10 it created a contract (`0x3f10...7f84`) and called it once; on 2026-08-17 it created a second (`0x2e52...eccb`); on 2026-08-18 at 05:18 UTC it created the attack contract, with 3,577 bytes of code, seven days before the exploit. After the exploit, on 2026-08-30 at about 09:01 UTC, it sent 100 USDT, then 0.024514079162607298 BNB, then 19,899.018126552928530404 USDT, all to `0xb4e2...05Db`. Nothing since. Why the attacker waited seven days after creating the contract, and whose address `0xb4e2...05Db` is, were not examined.

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, a BNB Chain node list walked in order (the state at old blocks needs an archive node; of the public nodes tried, one served it, and it is often rate-limited: the script retries), Sourcify (for the token's and the router's source), DefiLlama's hacks API. The DeFiHackLabs proof of concept gave the transaction hash and the addresses; everything else follows from the receipt, the logs, the reserves and the verified source. It takes about a minute.

1. **The exploit transaction** (H1, H2).
2. **The contracts and their source**: the sale branch, the whitelist, the router's `sweepToken` (H3 to H7).
3. **The pair's reserves before and after** (H8, H9).
4. **The receipt's logs**: loan, 25 cycles, proceeds (H10 to H14).
5. **The attacker's other transactions** (H15, H16).
6. **Value** and **DefiLlama's record** (H17, H18).

Each is a numbered check printed as PASS or FAIL; `--tx <hash>` runs the script with another BNB Chain transaction as the exploit and `--expect-usdt <wei>` with another amount: the checks that read them fail, see `preuves/temoins_negatifs_2026-10-23.txt`.

## Caveats

- **The calls were not traced.** No public node serves a call trace of this block. The order of events is read from the receipt's logs, which the verified source explains line by line.
- **The attacker's contract is not verified**, so how it chooses the 25 purchase sizes is not read; the sizes are the receipt's own, and the public proof of concept reuses them.
- **Why this amount of FH was in the pair and who owns the liquidity** were not examined; the loss is the pair's USDT, counted at face value, not a price in dollars read from a feed (USDT was not priced).
- **The token's owner and its other wallets were not examined**, nor whether the team knew of the flaw, answered, or changed the contract.
- **Where the USDT went stops at one address.** `0xb4e2...05Db` has no verified source; it was not followed.
- **The date written in the proof of concept's comment (2026-08-23) is wrong;** the chain's block time is 2026-08-25 09:54:52 UTC, which is also DefiLlama's date.
- **The category is the nearest of the index's seven.** A token whose transfer code resyncs the pair's reserves before the sale is credited: Rounding/Math-Bug, as for SKYDAO and CashCowCoin.

## License

MIT, see the repository root.
