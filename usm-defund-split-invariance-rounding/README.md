# USM (Minimalist USD) Redemption Split, Post-Mortem

On August 9, 2026, at 08:12:47 UTC, one transaction on Ethereum took 70.830977367697708372 ETH out of USM, the Minimalist USD stablecoin and its leveraged token FUM. USM pays out ETH for a redemption (`defund`) at a price that slides while the redemption runs, and it computes that slide with an approximation; the approximation is not the same for one big redemption as for many small ones. The attacker's contract borrowed 11,579.978354608392803524 WETH from Morpho, put all of it into USM with one `fund` call to receive 62,184,299.03 FUM, and redeemed that FUM in 64 equal slices instead of one call. The 64 slices paid back 11,650.809331976090511896 ETH. Redeemed in one call, the same FUM pays 5,825.405636077073924807 ETH, about half. The loan was repaid and the 70.83 ETH difference went to a single address.

DefiLlama lists $136,000 for "USM" on 2026-08-09 and classes it "Token & Share Accounting" / "Arithmetic Error"; a public proof of concept in the DeFiHackLabs repository gives the transaction, the addresses and the cause read from the call trace. This entry re-derives it: the receipt's 201 logs, the call trace, the pool's state one block before, and above all a replay on a fork of the chain at that block, with the real contracts, that redeems the same FUM once in one call and once in the attacker's 64 slices, in the same block with the same timestamp. The 64-slice replay pays the real transaction's amount to the wei.

The registry `registre_hypotheses.csv` states each fact as a falsifiable claim with its locator; `reconstruct_exploit.py` re-derives every on-chain number here live, check by check, and runs the fork replay when Foundry is installed.

## At a glance

| | |
|---|---|
| Victim | USM `0x2a7fff44c19f39468064ab5e5c304de01d591675` (the USM stablecoin and the ETH pool behind it) and its FUM token `0x86729873e3b88de2ab85ca292d6d6d69d548edf3`, that is, the FUM holders and USM holders whose collateral sits in the pool |
| Chain | Ethereum |
| Date | 2026-08-09, 08:12:47 UTC, block 25716150, transaction index 1193, tx `0xfae5e751b8ce01457cbb6b529839f24a0cff50faaabcbd0fd02ca0cf559b050e` |
| Mechanism | `defund` prices a redemption off a sliding FUM sell price computed by an approximation (`ethFromDefund`), and each call moves the stored price and bid-ask adjustment. One redemption of N FUM pays much less ETH than 64 redemptions of N/64, so funding the pool and redeeming in small slices returns more ETH than was put in. Both `fund` and `defund` are open to any caller |
| Attacker | EOA `0xb92b2e47680c89da8f951b8963ef469f461a50fc` (this was its transaction with nonce 43), through an unverified contract `0x5a5e29ba89663a3558273354e990426f3cac7de7` |
| Loss | 70.830977367697708372 ETH, what the pool paid out above what was paid in (11,650.809331976090511896 minus 11,579.978354608392803524), about $136,088 at DefiLlama's ETH price of 1,921.31 at the block time |
| Funds | The attack contract sent the 70.830977367697708372 ETH to one address, `0xe3c6346b...`, in the same transaction; where it went after that was not examined |
| Press figures | DefiLlama: $136,000 (USM, Ethereum, "Token & Share Accounting" / "Arithmetic Error", source empty), 0.06% under the value found here. DeFiHackLabs: about 70.8 ETH drained |

## What the receipt shows

The receipt has 201 logs. Morpho Blue sends the attack contract 11,579.978354608392803524 WETH; WETH unwraps exactly that amount; USM emits two events for each of 65 calls (one `fund` and 64 `defund`); the FUM token mints 62,184,299.031602985197125048 FUM to the attack contract once, and burns it from the attack contract 64 times, 8 times 971,629.672368796643705078 and 56 times 971,629.672368796643705079, which adds up to exactly the FUM minted; at the end WETH wraps the same 11,579.978354608392803524 and Morpho gets it back. The ETH movements are not in the logs; the call trace, read from one node, shows USM paying the attack contract in 64 calls totalling 11,650.809331976090511896 ETH, the attack contract paying USM 11,579.978354608392803524 ETH once (the `fund`), and sending the 70.830977367697708372 left to `0xe3c6346b...`.

One block before, the pool held 132.588942983107019337 ETH against 329,463.502710697641576863 FUM. The attacker's `fund` of 11,579.98 ETH is 87 times the pool.

## The replay: one call against 64 slices

The USM source is verified on Sourcify (exact match, solc 0.8.9). `fund(to, minFumOut)` and `defund(to, fumToBurn, minEthOut)` are public and have no role check of their own. `ethFromDefund` prices a redemption with a sliding FUM sell price and, in its own comments, with approximations built from a "pessimistic" bound on the ending pool; `_defundFum` then multiplies the stored price and the bid-ask adjustment by a shrink factor after each call. Nothing in the source says redeeming in pieces is equivalent to redeeming in one go, and the chain says it is not.

`fork/src/Fork.t.sol` is a Foundry test that forks the chain at block 25716149, the block before the attack, gives its own contract the 11,579.978354608392803524 ETH of the loan, and calls the real USM:

| Step | Result |
|---|---|
| `fund` with the whole loan | 62,184,299.031602985197125048 FUM, exactly what the real transaction minted |
| `defund` of all of it in ONE call | 5,825.405636077073924807 ETH |
| the same `fund`, then `defund` in the attacker's 64 slices (same block, same timestamp) | 11,650.809331976090511896 ETH |

The 64 slices pay exactly what the real transaction was paid by USM (its trace total), so the replay is the transaction and the one call is the same transaction with the same FUM redeemed at once. The loan is 11,579.978354608392803524: one call loses 5,754.57 ETH of it, 64 slices win 70.83. The proof of concept's claim that this is a pricing and rounding flaw and not price manipulation is consistent with this: the fork does not touch any oracle or price, it only changes how the same FUM is split.

## What came before and after

The EOA's transaction was its 44th (nonce 43). The attack contract is not verified; when it was created and what the EOA's other 43 transactions were were not examined. After the attack, the attack contract sent the profit to `0xe3c6346b...` in the same transaction; that address was not followed.

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, plus Foundry (`forge`) for the fork replay (H10, H11, skipped when it is missing); an Ethereum archive node list walked in order; one node that serves the call trace when available; Sourcify; DefiLlama's hacks and coins APIs. The DeFiHackLabs proof of concept gave the transaction hash and the addresses; everything else follows from the receipt, the verified source, the trace and the fork. It takes about a minute.

1. **The exploit transaction** (H1, H2).
2. **The contracts and their source** (H3, H4).
3. **The receipt's logs**: loan, one fund, 64 slices, repayment (H5 to H7).
4. **The pool one block before, and the trace** (H8, H9).
5. **The fork replay**: one call against 64 slices (H10, H11).
6. **Value** and **DefiLlama's record** (H12, H13).

Each is a numbered check printed as PASS or FAIL; `--tx <hash>` runs the script with another Ethereum transaction as the exploit and `--expect-eth <wei>` with another amount: the checks that read them fail, see `preuves/temoins_negatifs_2026-10-23.txt`. The raw output of the fork test is `preuves/resultats_fork_2026-10-23.txt`.

## Caveats

- **The fork replay uses the state of the block before the attack,** not of the transaction's position in its block (index 1193). That the replay equals the real transaction to the wei says no earlier transaction of the block changed what matters here.
- **The mechanism is shown by its effect,** the same FUM paying 5,825 ETH in one call and 11,651 ETH in 64; the exact line of arithmetic in `ethFromDefund` that makes the difference was not isolated, and the proof of concept's explanation (averaging the current and the estimated final sell price, plus the per-call state contraction and rounding) is not re-derived here.
- **Whether 64 is the best split, and whether other splits or other sizes pay more,** was not examined; the attacker's split is the only one replayed.
- **The attack contract is not verified,** and the trace comes from one node; the fork replay needs Foundry and an archive node that allows it.
- **Who holds the loss was not examined:** the pool's ETH was paid out of the collateral behind USM and FUM; what happened to USM's peg or to its holders after the attack, and whether the team answered, was not looked into.
- **Where the 70.83 ETH went after `0xe3c6346b...` was not followed.**
- **The category is the nearest of the index's seven.** A pricing approximation that is not invariant to how a redemption is split: Rounding/Math-Bug.

## License

MIT, see the repository root.
