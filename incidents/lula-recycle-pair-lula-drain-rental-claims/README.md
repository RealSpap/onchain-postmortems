# LULA Pair Drain, Post-Mortem

On July 28, 2026, at 16:08:29 UTC, one transaction on BNB Chain took 578,295.907588061000526778 USDT out of the LULA/USDT PancakeSwap V2 pair, whose USDT reserve fell from 591,841.33 to 181.58. The LULA token has a function, `recycle()`, that its Rental contract calls to move up to a third of the pair's LULA to itself and then `sync()` the pair, so the pair's LULA reserve shrinks while no USDT leaves; Rental calls it every time a reward is claimed. The attacker's contract borrowed 197.05 million USDT from 15 sources, pushed it into the pair to buy LULA with the output sent to the token's fee-excluded owner (which skips the token's disabled-buying gate), then had five helper accounts claim rewards: 41 `recycle()` transfers cut the pair's LULA reserve from 24,022 to 0.004 while its USDT stayed at 197.64 million. It sold 4,999 LULA back into that pair for 197,642,080.528989494738422649 USDT, repaid every loan with 13,363.84 USDT of fees, and sent the rest to its EOA.

DefiLlama lists $578,000 for "LULA" on 2026-07-28 and classes it "Access Control" / "Improper Access Control"; a public proof of concept in the DeFiHackLabs repository gives the transaction and the addresses. This entry re-derives it from the chain and from the token's verified source: what `recycle()` does and who may call it, what the buy gate lets through, the pair's reserves one block before and at the block, the receipt's 243 logs to the wei (the loans, the buy, the 41 transfers, the nine payouts, the sale, the repayments), and the value.

The registry `registre_hypotheses.csv` states each fact as a falsifiable claim with its locator; `reconstruct_exploit.py` re-derives every on-chain number here live, check by check.

## At a glance

| | |
|---|---|
| Victim | The LULA/USDT PancakeSwap V2 pair `0xf0b36389a12a28be1280c0ec2a4bbc76889d6a96` (token0 USDT, token1 LULA `0xf5d7029eb6751d170dcf0bb1c87af6f93d5a2e9a`), that is, its liquidity providers: the pair's USDT fell by 591,659.751036620107104457, of which 13,363.84 went to the flash-loan sources as fees |
| Chain | BNB Chain |
| Date | 2026-07-28, 16:08:29 UTC, block 112655390, transaction index 49, tx `0xa219ab9d57e520e5235b15a8801f4ebac8cc45551be0430ce4e49caea0411d7c` |
| Mechanism | `LULA.recycle(amount)`, callable only by the Rental contract, moves min(amount, a third of the pair's LULA) from the pair to Rental and calls `sync()`; Rental pays rewards by calling it. Buying is disabled (`buyEnabled` false) but `_transfer` skips that check when the sender or recipient is fee-excluded, and the token's owner is. A pair swap whose output goes to the owner is a buy that works |
| Attacker | EOA `0x2677806d48325ced7533c54b86ed5e99b129a4ed` (its 551st transaction, nonce 550) calling the contract `0x5e506ba06fa6c61d1069b0e68d7013de35afa816`; five helper accounts, each carrying an EIP-7702 delegation one block before, claimed the rewards |
| Loss | 578,295.907588061000526778 USDT at face value, what the attack contract sent the EOA after repaying everything: the pair's take (197,642,430.758745416717169252 out, 197,050,771.007708796610064795 in) minus 13,363.843448559106577679 of fees |
| Funds | The last USDT log sends it to the EOA. About 17,930.61 LULA stayed in the attack contract. Where the USDT went after that was not examined |
| Press figures | DefiLlama: $578,000 (LULA, BSC, "Access Control" / "Improper Access Control", source empty), 0.05% under the value found here. DeFiHackLabs: 578,295.907588061000526778 USDT net |

## What the token does

The LULA token is verified on Sourcify (exact match, solc 0.8.28); the Rental contract, the token's owner, the attack contract and the pair are not.

`recycle(amount)` requires `msg.sender == rentalContract`, takes `maxTake = balanceOf[pair] / 3`, moves `min(amount, maxTake)` from the pair to Rental with a plain balance transfer, and calls `sync()` on the pair. Nothing is paid into the pair. The pair's LULA reserve therefore falls by the amount moved while its USDT reserve does not change, which for a constant-product pair multiplies the price of the remaining LULA.

`_transfer` runs a plain transfer, before any other rule, if the sender or the recipient is excluded from fees. Only afterwards does it handle a transfer out of the pair as a buy and require `buyEnabled`. One block before the attack `buyEnabled` was false, the token's owner `0x43721abc1d19378c6160abfda6f1dd488ebbb5c9` and Rental were fee-excluded, and the attack contract, the EOA and the pair were not. A buy cannot go to the attacker, but it can go to the owner, who is excluded.

## The exploit, from the receipt

The 243 logs show, in order:

1. **The loans.** The attack contract receives 197,050,420.777952874631318192 USDT in 15 transfers from 15 different sources, Moolah among them. Other transfers of WBNB and of lender tokens in the same logs belong to the loans' collateral and were not followed. None of the borrowed USDT has touched the pair yet.
2. **A small sale.** The EOA sent it 5,000 LULA; after the token's taxes, 4,750 LULA go into the pair and 350.229755921978746603 USDT come out. The USDT it now holds is exactly its loans plus that, 197,050,771.007708796610064795.
3. **The buy.** All of it goes into the pair; the pair sends 7,982,785.68743000315948181 LULA to the token's owner, not to the attacker. The pair now holds 197,642,262.105713614392627871 USDT against 24,022.137 LULA, a price per LULA of about 8,200 USDT against 0.074 before.
4. **The drain.** Rental moves LULA out of the pair 41 times, each time at most a third of what is left, 34 of them exactly a third, and each followed by a Sync that records the smaller LULA reserve against the same USDT reserve: 24,022.137 LULA falls to 0.004. Between those transfers Rental pays nine rewards, 23,607.995266800130898984 LULA in all, to five helper accounts, and each helper forwards the same amount to the attack contract; the attack contract itself sends Rental 392.634225895698522739 and 285.754430007355834460 LULA twice during the payouts.
5. **The sale.** The attack contract sells 4,999 LULA (4,749.05 after tax) into the pair and takes out 197,642,080.528989494738422649 USDT; the pair ends with 181.576724119654205222 USDT and 4,749.054352115435255586 LULA, as `getReserves()` confirms at the block.
6. **The end.** All 15 sources are repaid, each at least what it lent, 13,363.843448559106577679 USDT more than borrowed in total; the last USDT log sends 578,295.907588061000526778 USDT to the EOA, which is the pair's net take minus those fees to the wei.

## What came before and after

The EOA had no code one block before and at the exploit block and its nonce was 550; its code today is an EIP-7702 delegation designator, set after the attack, though the proof of concept describes it as delegated at the time. Each of the five helpers carried a delegation designator one block before; their pending referral rewards one block before, read from Rental by hand with the function name taken from the proof of concept (not part of the script), summed to 2,895.4 LULA, much less than the 23,607.99 LULA paid, and how Rental computes what it pays was not read (it is not verified). The EOA's other 550 transactions, the attack contract, the owner and the way the 5,000 LULA reached the EOA were not examined.

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, a BNB Chain node list walked in order (the state at an old block needs an archive node; of the public nodes tried, one served it, and it is often rate-limited: the script retries), Sourcify (for the token's source and the verification status), DefiLlama's hacks API. The DeFiHackLabs proof of concept gave the transaction hash and the addresses; everything else follows from the receipt, the logs, the reserves and the verified source. It takes a few minutes.

1. **The exploit transaction** (H1 to H3).
2. **The token, its verified source, `recycle()` and the buy gate** (H4 to H6).
3. **The state one block before, and the pair at the block** (H7, H8).
4. **The receipt's logs**: loans, sale, buy, drain, payouts, sale back, repayments, proceeds (H9 to H16).
5. **Value** and **DefiLlama's record** (H17, H18).

Each is a numbered check printed as PASS or FAIL; `--tx <hash>` runs the script with another BNB Chain transaction as the exploit and `--expect-usdt <wei>` with another amount: the checks that read them fail, see `preuves/temoins_negatifs_2026-10-23.txt`.

## Caveats

- **The calls were not traced.** No public node serves a call trace of this block. That the 41 transfers from the pair to Rental are `recycle()` calls is read from the verified function (a plain transfer from the pair to Rental followed at once by a Sync, with no Swap and no USDT moving, is what it does) and from Rental being the only address allowed to call it; the proof of concept's reading, that Rental calls it in a loop of up to ten rounds for each claim, was not re-derived.
- **Rental is not verified,** nor is the attack contract, the owner or the pair. What triggers the payouts, how their amount is computed and whose rewards the five helpers hold were not read.
- **The loans' sources are listed by address only;** Moolah is the only one identified here. The WBNB and other tokens in the loan logs were not followed.
- **About 17,930.61 LULA stayed in the attack contract,** not sold and not priced; the loss counted is the USDT at face value.
- **The proof of concept calls the EOA "EIP-7702 delegated";** at the exploit block it had no code, and today it carries a designator.
- **Why the owner address is fee-excluded and why buying was disabled** were not examined, nor whether the LULA team answered (the proof of concept mentions an on-chain bounty message, not read) or paused anything.
- **The category is the nearest of the index's seven.** A token function that shrinks the pair's reserve and syncs it without paying anything in: Rounding/Math-Bug, as for SKYDAO, CashCowCoin and FH Token. DefiLlama says "Access Control".

## License

MIT, see the repository root.
