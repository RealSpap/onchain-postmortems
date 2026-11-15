# MOKE Release Over-Mint, Post-Mortem

On August 2, 2026, at 20:50:11 UTC, one transaction on BNB Chain made a net 1,546.443215651996973049 BNB out of MOKE, a token that a `MokeRelease` contract releases to its participants. `MokeRelease` pays a participant's pending USDT quota out in MOKE at a price that anyone with an ordinary account can latch with `settle()`, and that price is read from the instantaneous reserves of two PancakeSwap pairs, one of them the BNB/USDT pair. The attacker's account borrowed 633,344.033277139890380685 WBNB, sold it all into the BNB/USDT pair to push the BNB price from 589.6 to 1.34 USDT, called `settle()` to latch a MOKE price of 0.000594 USDT instead of 0.261, and then claimed: its 24,766.2 USDT of pending quota minted 41,684,057.233944649146143063 MOKE instead of about 94,832. Three helper accounts claimed the same way, the 43,860,308.980417278429035188 MOKE went through the project's dividend vault into the MOKE/BNB pair for 1,664.616180024096154954 BNB, the crash was undone, every loan was repaid, and the BNB reached the attacker's account. All of it ran in one transaction that the attacker's account sent to itself, through an EIP-7702 delegation.

DefiLlama lists $907,000 for "MOKE" on 2026-08-02 and classes it "Oracle Manipulation" / "Spot Price Manipulation"; a public proof of concept in the DeFiHackLabs repository gives the transaction and the addresses. This entry re-derives it from the chain and from the verified source of the contracts: what `settle()` accepts, how the price is built, the pairs' reserves one block before, the receipt's 256 logs, the four claims to the wei, the crash and its reversal, the 65 dividend claims, the delegation of every account involved, and the value.

The registry `registre_hypotheses.csv` states each fact as a falsifiable claim with its locator; `reconstruct_exploit.py` re-derives every on-chain number here live, check by check.

## At a glance

| | |
|---|---|
| Victim | The MOKE release scheme: `MokeRelease` `0x684d722ebf8980f49492f631f56765dd4fb302a7`, the X/MOKE reserve pool `0x89715a0768e95942071ed52b37a90c6d53019b5a` its claims drain, and the liquidity providers of the MOKE/BNB pair `0xba6a49a97cc725b3c39d6c5ea6deffddb64fe6b8`, which paid out 1,664.62 of its 1,849.17 WBNB |
| Chain | BNB Chain |
| Date | 2026-08-02, 20:50:11 UTC, block 113652609, transaction index 26, tx `0x0776048b1b58064fb31b6513721811e7b44d6bdbe7bf5833158b241ca6756a8f` |
| Mechanism | `settle()` is callable by any externally owned account (`msg.sender == tx.origin`) and stores `settledMokePrice` from `getMokeUsdtPrice()`, the product of the MOKE/BNB and BNB/USDT pairs' instantaneous reserve ratios. `claim()` mints `pendingUsdt / settledMokePrice` MOKE and only checks that the live price is within 20% of the settled one, which a price latched in the same transaction satisfies |
| Attacker | EOA `0xe454a9bac1a44868e4a9cbe1a4b5ac231d0dcf8a` (nonce 163 in this transaction), delegated by EIP-7702 to code at `0xc7fdea027feb41c8f3a45ec284280ce68f4e6ff7`; the transaction is a call from the EOA to itself |
| Loss | 1,546.443215651996973049 BNB, the attacker's net gain in the logs (1,664.616180024096154954 of dividends plus 28.129086340978628606 of its own liquidity removed, minus 146.302050713077810511 lost undoing the crash), about $909,743 at DefiLlama's BNB price of 588.28 at the block time |
| Funds | The last log is the EOA unwrapping 1,546.536756665233062068 WBNB; the EOA's BNB balance rose by 1,546.442988374596912068 BNB across the block after paying 0.0003337624 BNB of gas. Where it went after that was not examined |
| Press figures | DefiLlama: $907,000 (MOKE, BSC, "Oracle Manipulation" / "Spot Price Manipulation", source empty), 0.3% under the value found here. DeFiHackLabs: about 1,546.54 BNB, 41.68M MOKE over-minted |

## What `settle()` and `claim()` do

`MokeRelease` is verified on Sourcify (exact match, solc 0.8.28), and so are `MokeToken`, the dividend vault `MokeLPDividend`, `TokenX` and `MokeLPManager`. A participant has a USDT release quota that vests over time; `claim()` pays the pending part of it in MOKE, taken from an X/MOKE reserve pool, at `settledMokePrice`.

`settle()` requires that the caller be an authorized settler, the owner, or `msg.sender == tx.origin`, that is, any externally owned account, plus a 600 second cooldown. It then stores `settledMokePrice = getMokeUsdtPrice()`. `getMokeUsdtPrice()` is the MOKE/BNB reserve ratio times the BNB/USDT reserve ratio, each read from `getReserves()` of a PancakeSwap pair at that instant; there is no time-weighted price, no external feed and no bound on how far it can move between two settles. The last settle before the attack was on 2026-07-22 at a price of 0.219155995135458644, 11 days earlier; the attacker's account was neither a settler nor the owner.

`claim()` computes `mokeAmount = pendingUsdt * 1e18 / settledMokePrice`, then compares the live price with the settled one and reverts only if they differ by more than `maxPriceDeviation`, 2000 basis points (20%). That check protects against the price moving between the settle and the claim; a price crashed and latched inside one transaction is both the live and the settled price. `claim()` also needs a release quota, which the attacker's account had: 45,000 USDT, of which 24,766.2 were pending at the claim.

## The exploit, from the receipt

The transaction is a call from the account to itself, which ran the delegated code; one block before and at the block, the account's code is the EIP-7702 designator `0xef0100c7fdea...6ff7`. Because the call comes from the account itself, `msg.sender` and `tx.origin` are the same address, and `settle()`'s `tx.origin` arm accepts it. The 256 logs show, in order:

1. **Its own liquidity out.** The account removes 1,334.183807563777105758 MOKE/BNB LP tokens through `MokeLPManager` and receives 28.129086340978628606 BNB and 63,507.190562122389710491 MOKE, which go to the dead address. The MOKE/BNB pair is left with 4,111,383.78 MOKE and 1,821.05 WBNB.
2. **The borrowing.** Moolah lends it 403,344.033277139890380685 WBNB and 3,169.548892541186802722 BTCB; the BTCB goes in as collateral on Venus and 230,000 BNB are borrowed against it. It holds 633,344.033277139890380685 borrowed WBNB.
3. **The crash.** All of it is sold into the BNB/USDT pair for 17,788,339.291766263678994131 USDT. The pair had 18,680,401.84 USDT against 31,681.99 WBNB one block before (589.6 USDT per WBNB); it ends with 892,062.55 USDT against 665,026.03 WBNB (1.34).
4. **The latch.** `settle()` emits `PriceSettled(594140821297791)`, 0.000594 USDT per MOKE against 0.261159872237343465 a block earlier, a fall by a factor of 439.6. Recomputing the price with `MokeRelease`'s own formula from the MOKE/BNB and BNB/USDT reserves as they stand in the logs gives that number exactly.
5. **Four claims.** The account claims 24,766.2 USDT of pending quota and receives 41,684,057.233944649146143063 MOKE; at the price of the block before the same quota would have bought about 94,832, so the mint is 439.6 times too large. Three helper accounts, each also delegated by EIP-7702, claim 660, 600 and 33 USDT and receive 1,110,847.759220367615397373, 1,009,861.599291243286724884 and 55,542.387961018380769868 MOKE. Each amount is `pendingUsdt * 1e18 // 594140821297791` to the wei, and each claim burns the matching X from the reserve pool. The four mints total 43,860,308.980417278429035188 MOKE.
6. **The sale.** The released MOKE is moved to the dividend vault `MokeLPDividend`, which sells all of it in one swap into the MOKE/BNB pair for 1,664.616180024096154954 WBNB (the pair goes from 1,821.05 to 156.43 WBNB), unwraps it and distributes it as a dividend. Sixty-five distinct accounts, the attacker's among them and every one carrying an EIP-7702 designator a block earlier, claim 1,664.616180024096093973 BNB, 60,981 wei less than was distributed.
7. **The undoing.** The account sends 17,791,328.590270968124537043 USDT back to the BNB/USDT pair and takes out 633,197.731226426812570174 WBNB: 146.302050713077810511 less than it put in, the cost of the crash. Moolah gets back the 403,344.033277139890380685 WBNB and 3,169.548892541186802722 BTCB, Venus the 230,000 BNB, and the last log is the account unwrapping 1,546.536756665233062068 WBNB.

The net gain from the logs, dividends plus liquidity removed minus the cost of undoing the crash, is 1,546.443215651996973049 BNB. The account's balance rose by 1,546.442988374596912068 BNB across the block, which with the 0.0003337624 BNB of gas is within 0.0002 BNB of it. The difference between that gain and the last log's 1,546.54 is 0.0935 BNB, the account's own opening balance, wrapped in the same transaction.

## What came before and after

The account's code was already delegated one block before, and it had sent 163 transactions; none of them, and none after this one, were read. When the delegations were installed, who controls the three helpers and the 64 other dividend recipients, and where the BNB went after the unwrap were not examined. The 45,000 USDT quota is the account's own release allocation; how it came to hold it was not examined.

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, a BNB Chain node list walked in order (the state at an old block needs an archive node; of the public nodes tried, one served it, and it is often rate-limited: the script retries), Sourcify (for the contracts' source and names), DefiLlama's hacks and coin-price APIs. The DeFiHackLabs proof of concept gave the transaction hash and the main addresses; everything else follows from the receipt, the logs, the state one block before and the verified source. It takes a few minutes.

1. **The exploit transaction and the delegation** (H1 to H3).
2. **The contracts and what `settle()`, the price and `claim()` do** (H4 to H7).
3. **The state one block before** (H8 to H10).
4. **The receipt's logs**: borrowing, crash, latch, four claims, sale, dividends, undoing, repayments, net gain (H11 to H23).
5. **Value** and **DefiLlama's record** (H24, H25).

Each is a numbered check printed as PASS or FAIL; `--tx <hash>` runs the script with another BNB Chain transaction as the exploit and `--expect-moke <wei>` with another amount: the checks that read them fail, see `preuves/temoins_negatifs_2026-10-23.txt`.

## Caveats

- **The calls were not traced.** No public node serves a call trace of this block. The order of events is read from the receipt's logs; native BNB movements (the dividends reaching the account, the 64 other accounts' shares) do not appear in them, so how the 65 recipients' BNB reached the account is not shown. The gain is reconciled with the account's balance, not followed transfer by transfer.
- **"Attacker-controlled" is an inference** for the three helpers and the 64 other dividend recipients: they all carry EIP-7702 delegations and the BNB ended at the account, but nothing shows who signed for them.
- **The proof of concept says the real attack made a single claim.** The receipt has four `claim()` calls; the account's own is the 41.68M MOKE one, the helpers' three add 2.18M.
- **The gain includes 28.129 BNB of the attacker's own liquidity,** removed in the same transaction; its cost was not examined. Without it the gain is 1,518.314 BNB. About 0.0001 BNB of the gap between the logs' gain and the balance change plus gas is not explained.
- **Why the released MOKE had to go through the dividend vault** (the PoC says released MOKE is transfer-locked to whitelisted handlers) was not read in `MokeToken`; the path is the receipt's.
- **Who lost** is the MOKE/BNB pair's liquidity providers (BNB paid out, 90% of the pair's WBNB), and the X/MOKE reserve pool that supplied 43.86M MOKE; the owners of those positions, the team's answer, whether `settle()` was changed, and the state of the BNB/USDT pair afterwards (it was restored by the attacker's own swap back) were not examined.
- **One line of each of two output files was edited by hand after the run.** The label of check H25 read "about $909,744" while the value measured on the same line, $909,743, is what the run printed. The label was changed to $909,743 in the script, in the register and in the lines of `preuves/resultats_reconstruction_2026-10-23.txt` and `preuves/temoins_negatifs_2026-10-23.txt`; the script was not run again, and nothing else in those files was touched.
- **The category is the nearest of the index's seven.** A release price latched from instantaneous pair reserves: Oracle, as for Float Protocol.

## License

MIT, see the repository root.
