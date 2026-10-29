# CashCowCoin Pair Drain, Post-Mortem

On August 27, 2026, at 12:31:31 UTC, one transaction on BNB Chain took 165.471928251512413319 WBNB out of the CashCowCoin (CCC) / WBNB PancakeSwap V2 pair, 99.99% of the WBNB it held. The token's trading contract lets any caller sell CCC through the pair; after each sale the pair sends to the dead address the very CCC it has just received and syncs its reserves, so the pair keeps its CCC and keeps losing WBNB. The attacker's contract borrowed 416,831.49 WBNB from a lending pool, put 13,999.89 WBNB of it into the pair, bought CCC with 402,831.60 WBNB, and then sold it back in 80 equal-looking steps; at each step the pair paid out WBNB and burned the CCC it was paid in. The WBNB reserve went from 165.49 to 0.0179, the loan was repaid to the wei, and the profit equals the pair's loss to the wei.

DefiLlama lists $117,000 for "CCC" on 2026-08-27 and classes it "Protocol Logic" / "Swap Logic Flaw"; a public proof of concept in the DeFiHackLabs repository gives the transaction, the addresses and a reading of the cause from the call trace. This entry re-derives the sequence from the chain: the pair's reserves one block before and after, the receipt's 1,572 logs, the attacker's ten transactions, and the value. It does not trace the calls (no public node serves the trace of this block) and none of the contracts involved is verified anywhere, so the code that does the burning is not read here.

The registry `registre_hypotheses.csv` states each fact as a falsifiable claim with its locator; `reconstruct_exploit.py` re-derives every on-chain number here live, check by check.

## At a glance

| | |
|---|---|
| Victim | The CCC/WBNB PancakeSwap V2 pair `0x1dbe9458a6840784d5defd62c6b71386100097c0` (token0 CCC `0xb9b845f718c32f37e8af8b887ae4eec816c93ccc`, token1 WBNB), that is, its liquidity providers. The CCC trading contract is a proxy at `0xf523224c6171f81c54b93f474ed4c78de91241c7` with the unverified implementation `0x4287742e50fad6d3351000fd31632412ab29a9ac` |
| Chain | BNB Chain |
| Date | 2026-08-27, 12:31:31 UTC, block 118384061, transaction index 86, tx `0x89d8050641019a5a75fa3dafb4f64fb153e4dd30c0f1f51d06a6cc206d3ead43` |
| Mechanism | One purchase, then 80 sales through the trading proxy. After each swap the pair sends the CCC it just received to `0x...dEaD` and syncs: the 80 burns remove 6,209,331.84 CCC from the pair, the pair's CCC reserve stays between 326,767.61 and 431,336.96, and its WBNB reserve goes from 14,165.38 (after a donation) to 0.0179 |
| Attacker | EOA `0x7977bdeee3a79dc85cc18739692e796b5d2513c4`, whose ninth transaction this was; it ran a helper contract `0x7738b4d7c25e9a7092ae1ab402343b20340daeaf` that it had created 135 blocks earlier, and a call to a first contract of its own had reverted 151 seconds before |
| Loss | 165.471928251512413319 WBNB, the pair's WBNB reserve one block before (165.489861516856566016) minus after (0.017933265344152697), about $117,005 at DefiLlama's BNB price of 707.10 at the block time |
| Funds | The 165.47 WBNB stayed with a 1,424-byte contract `0xbabf70e515ae71a2177e624994a68d10c61d7a9f` that also returned the loan; it holds nothing now and where the WBNB went was not traced. The EOA sent one more transaction, on 2026-08-31, 0.162901688552397264 BNB into a verified RelayDepository contract |
| Press figures | DefiLlama: $117,000 (CCC, BSC, "Protocol Logic" / "Swap Logic Flaw", source empty), 0.00% under the value found here. DeFiHackLabs: "~165.47 WBNB (~$117.4K)" |

## What the logs show

The receipt has 1,572 logs. In order:

1. **The loan.** The lending pool Moolah (verified on Sourcify) sends the attack contract 416,831.487011304318246517 WBNB; the same amount goes back to Moolah in the last log.
2. **The donation.** The attack contract sends 13,999.890970633457505314 WBNB straight to the pair, and the pair's first Sync shows its WBNB reserve raised by exactly that amount, from 165.489861516856566016 to 14,165.38083215031407133.
3. **The purchase.** 402,831.596040670860741203 WBNB, unwrapped from the loan by WBNB and sent through the router, buy 8,805,839.807721103467515041 CCC out of the pair, sent to the trading proxy; this is the pair's first Swap of 81.
4. **Eighty cycles.** In each one the proxy sends CCC into the pair, the pair swaps it and pays out WBNB, WBNB unwraps it to BNB for the caller, then the pair sends to the dead address exactly the CCC it was just sent and a Sync follows. All 80 cycles match: the amount sent into the pair equals the amount burned out of it right after, 6,209,331.84177536332138734 CCC in total. The pair's WBNB reserve at the last Sync of each cycle never rises and ends at 0.017933265344152697.
5. **The proceeds.** The 80 sales unwrap 416,996.958939555830659836 BNB, wrapped again in one deposit and sent to `0xbabf...7a9f`, which sends the 416,831.487011304318246517 WBNB of the loan back, and the helper repays Moolah. What is left, 165.471928251512413319 WBNB, is the pair's whole fall in WBNB, to the wei.

The pair held 9,596,072.668666131466478257 CCC and 165.489861516856566016 WBNB one block before the transaction, and 326,767.607907075184883477 CCC and 0.017933265344152697 WBNB after.

## What the contracts are

None of the CCC token, the trading proxy, its implementation, the pair or the attack contract is verified on Sourcify. One block before the attack the proxy's EIP-1967 implementation slot holds `0x4287...a9ac`, whose code contains the selectors of `buy(uint256,uint256,uint256)`, `sell(uint256,uint256,uint256)` and `0xb20a0b6f`; the CCC token's code contains `0xb20a0b6f` too. The DeFiHackLabs proof of concept, from the call trace, reads `0xb20a0b6f` as a privileged function of the token that burns CCC out of the pair, which only the proxy may call, and says the proxy's public `sell` calls it after each swap and then calls `sync()`. This entry did not read that trace and cannot confirm the call chain; what it confirms is the effect, in the logs of all 80 cycles, and that a contract the EOA created about a minute earlier, and had called once before, could run the cycle 80 times.

## What came before and after

The EOA's ten transactions are all read. At block 117800020 it approved USDT and made one 1,861-byte call to a contract. At blocks 118381838 to 118383725 it created a first contract (7,716 bytes of creation code) and called it three times; the third call, selector `0x36b3d4df`, the one it later used for the attack, reverted. It created the helper at block 118383926, called it once with `0x18cb85bd` (68 bytes), and ran the attack with `0x36b3d4df`. After it, on 2026-08-31 at 08:23 UTC, it sent 0.162901688552397264 BNB to a contract verified on Sourcify as `RelayDepository`, calling `depositNative(address,bytes32)`. Nothing since. Why the first call reverted, and what the Relay deposit was for, were not examined.

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, a BNB Chain node list walked in order (the state at old blocks needs an archive node; of the public nodes tried, one served it, and it is often rate-limited: the script retries), Sourcify, DefiLlama's hacks and coins APIs. The DeFiHackLabs proof of concept gave the transaction hash and the addresses; everything else follows from the receipt, the logs, the reserves and the code. It takes about a minute.

1. **The exploit transaction and the helper's creation** (H1 to H3).
2. **The contracts and what is verified** (H4 to H6).
3. **The pair's reserves before and after** (H7, H8).
4. **The receipt's logs**: loan, donation, purchase, 80 cycles, proceeds (H9 to H16).
5. **The attacker's other transactions** (H17, H18).
6. **Value** and **DefiLlama's record** (H19, H20).

Each is a numbered check printed as PASS or FAIL; `--tx <hash>` runs the script with another BNB Chain transaction as the exploit and `--expect-wbnb <wei>` with another amount: the checks that read them fail, see `preuves/temoins_negatifs_2026-10-23.txt`.

## Caveats

- **The calls were not traced.** No public node serves a call trace of this block. The order of events is read from the receipt's logs; that the burn is made by a privileged token function called through the proxy's `sell` is the proof of concept's reading of the trace, not re-derived here.
- **No source was read.** None of the contracts involved is verified. The selectors found in the bytecode show that `buy`, `sell` and `0xb20a0b6f` exist; what they do is inferred from their effects in the logs.
- **Whether `sell` needs no permission is inferred,** from a fresh contract with no history running it 80 times, not from the code.
- **Where the 165.47 WBNB went is not traced.** The contract that kept it is empty now; the log queries that would show its later transfers were refused by the nodes available.
- **The loss is the WBNB at one price.** About $117,005 at 707.10; the DeFiHackLabs figure of about $117.4K comes from another price. The pair's liquidity providers also lost their CCC to the burns in a sense the pair's accounting does not price: the CCC reserve fell from 9.6 million to 0.33 million, of which the purchase and sales moved most; this entry prices only the WBNB.
- **Why the attacker's first attempt reverted, and what the Relay deposit was for, were not examined.**
- **The category is the nearest of the index's seven.** A pair whose reserve is burned and synced after each swap: Rounding/Math-Bug, as for SKYDAO.

## License

MIT, see the repository root.
