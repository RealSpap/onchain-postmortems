# Arrakis V1 (G-UNI ENS/WETH) Spot-Price Mint and Burn, Post-Mortem

On August 23, 2026, at 12:50:11 UTC, one transaction on Ethereum made a net 2.94135035290003714 WETH out of the Arrakis V1 G-UNI ENS/WETH vault, a Uniswap V3 liquidity vault. The vault prices a deposit from the pool's current price (`slot0`), and its only protection against a manipulated price, a check against the pool's time-weighted average, sits in the manager's `rebalance()` and nowhere else. The attacker's contract borrowed 1,800 WETH from Morpho, pushed the pool's price with a swap, minted vault shares at that price, pushed the price back part of the way, burned the same shares for a different mix of tokens, sold the ENS it held, and repaid the loan. It paid a 0.05 ETH tip to the block's fee recipient and sent the rest, 2.89135035290003714 ETH, to its EOA.

DefiLlama lists $7,100 for "Arrakis V1" on 2026-08-23 and classes it "Oracle Manipulation" / "Spot Price Manipulation"; a public proof of concept in the DeFiHackLabs repository gives the transaction and the addresses. This entry re-derives the sequence from the chain and from the vault's verified source: where the vault reads the price and where it does not, the pool's tick before and after, the receipt's 33 logs, the attacker's five transactions, and the value. It does not decide who lost the 2.94 WETH: the vault holders lost value, but part of the attacker's gain comes from the pool swaps themselves.

The registry `registre_hypotheses.csv` states each fact as a falsifiable claim with its locator; `reconstruct_exploit.py` re-derives every on-chain number here live, check by check.

## At a glance

| | |
|---|---|
| Victim | The Arrakis V1 G-UNI ENS/WETH vault `0x7c687f775a3b73bbab0e15832f24caab5d53bdde` (an EIP-173 proxy, implementation `ArrakisVaultV1` `0xd68b055fb444d136e3ac4df023f4c42334f06395`), that is, its share holders, and the liquidity of the Uniswap V3 pool `0xb9c4a5522a2f8ba9e2ff7063df8c02ed443337a3` it sits in |
| Chain | Ethereum |
| Date | 2026-08-23, 12:50:11 UTC, block 25817966, transaction index 1, tx `0x6ae3af4b2f25a56594de99cfb31369150dd9ac059c49efe04b9e3e0163dbc672` |
| Mechanism | `mint()` takes the amounts to deposit from `getUnderlyingBalances()`, which reads the pool's `slot0` price; neither `mint()` nor `burn()` looks at the time-weighted price, which `_checkSlippage` reads and only `rebalance()` calls. One block before the transaction minting was open to any caller (`restrictedMintToggle()` was 100) |
| Attacker | EOA `0xa3b096e4df1247794599a37af8f5b8cb05d5eb44`, whose third transaction this was; the attack contract `0x028d9c17b1a097e7e115a6400203df86339baf4a` was created by its second transaction, in the same block, just before |
| Loss | 2.94135035290003714 WETH, the attack contract's net WETH after repaying the loan, about $7,133 at DefiLlama's ETH price of 2,425.21 at the block time. The vault ended the transaction 4.987405217658776899 WETH richer and 123.710861675477149658 ENS poorer in the flows of the logs |
| Funds | 0.05 ETH to the block's fee recipient, 2.89135035290003714 ETH to the attacker's EOA, which sent 2.98 ETH on to `0x01e38ad959da0ddc5e028d4b709bc0116087f37b` 16 blocks later (about three minutes) and 0.005 ETH to `0xb8abc9727aae7a971a73363df9b0603b38d802b2` on 2026-10-02 |
| Press figures | DefiLlama: $7,100 (Arrakis V1, Ethereum, "Oracle Manipulation" / "Spot Price Manipulation", source empty), 0.47% under the value found here. DeFiHackLabs: about 2.9414 WETH net |

## What the vault trusts

The vault implementation is verified on Sourcify (exact match, `ArrakisVaultV1`, solc 0.8.4). Its `mint(mintAmount, receiver)` reads `pool.slot0()` and, when the vault has shares, computes the amounts to pull from the caller as `getUnderlyingBalances()` times `mintAmount / totalSupply`; `getUnderlyingBalances()` itself calls `pool.slot0()` and values the position at that instantaneous price. `burn(burnAmount, receiver)` withdraws the matching share of the position's current liquidity and of the vault's idle balances. The only function that reads the pool's time-weighted price (`pool.observe`) is `_checkSlippage`, and it is called once, from the manager's `rebalance()`. Nothing in `mint()` or `burn()` calls it, and `mint()` only refuses a caller who is not the manager when `restrictedMintToggle` is 11111; it was 100.

A swap in the pool moves `slot0` for the next call in the same transaction. So a caller can move the price, mint at the moved price, move it back, and burn.

## The exploit, from the receipt

The receipt has 33 logs, in this order:

1. **The loan.** Morpho sends the attack contract 1,800 WETH; the same amount goes back in the last transfer.
2. **Swap 1.** 145.416963504083295148 WETH into the pool for 13,292.512773372132065449 ENS out. The pool's tick, 60333 one block before, falls.
3. **The mint.** The attack contract pays the vault 1,253.394683838271695411 WETH and 13,159.587645638410744793 ENS and receives 4,486.619135659964587643 vault shares.
4. **Swap 2.** 132.925127733721320656 ENS in for 7.433166160431042707 WETH out, moving the price back part of the way.
5. **The burn.** The attack contract burns the same 4,486.619135659964587643 shares and receives 1,248.407278620612918512 WETH and 13,283.298507313887894451 ENS from the vault: 4.987405217658776899 WETH less and 123.710861675477149658 ENS more than it put in.
6. **Swap 3.** All 13,283.298507313887894451 ENS in for 145.91255291421106648 WETH out.
7. **The end.** The 1,800 WETH are repaid and the remaining 2.94135035290003714 WETH are unwrapped, which is also the sum of what the attack contract received in WETH minus what it paid, to the wei. The call trace, read from one node, shows 0.05 ETH sent to the block's fee recipient (`0xdadb0d80178819f2319190d340ce9a924f783711`; the proof of concept names another address) and 2.89135035290003714 ETH to the EOA.

The pool's tick is 60333 before the block and 59789 after it.

## Who lost

The vault's own flows in the receipt are 4.987405217658776899 WETH in and 123.710861675477149658 ENS out. At the pool's price before the attack (416.98 ENS per WETH) that is worth about 4.69 WETH to the vault, so the vault gains on those flows; but the vault's position is liquidity in the pool, whose amounts change with the price the attacker moved. Read from the vault at the blocks before and after, its underlying balances were 6.162572482440994 WETH and 9,294.764916212745 ENS, then 0.7747257685649493 WETH and 9,878.195412513836 ENS, for an unchanged supply of 324.7566472380339 shares: at the price before the attack that is 28.45 WETH, then 24.46 WETH, a fall of 3.99 WETH. That fall is the end-of-block state, which includes every transaction of the block after this one, and it is larger than the attacker's 2.94 WETH; this entry does not split it between the attacker and the others. DefiLlama's $7,100 and the figure counted here are the attacker's gain.

## What came before and after

The EOA has sent five transactions in all. It created a first contract at block 25817963 (2026-08-23 12:49:35 UTC), the attack contract at block 25817966 and ran the attack in the same block. After it, it sent 2.98 ETH at block 25817982 and 0.005 ETH on 2026-10-02. Nothing since. Why the first contract was created, and who the two recipients are, were not examined.

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, an Ethereum archive node list walked in order (the state at an old block needs an archive node; the nodes that refuse are skipped), one node that serves the call trace when available, Sourcify (for the vault's source), DefiLlama's hacks and coins APIs. The DeFiHackLabs proof of concept gave the transaction hash and the addresses; everything else follows from the receipt, the logs, the pool's price and the verified source. It takes under a minute.

1. **The exploit transaction** (H1, H2).
2. **The vault, its verified source and what guards what** (H3 to H6).
3. **The pool's price before and after** (H7).
4. **The receipt's logs**: loan, three swaps, mint, burn, profit (H8 to H14).
5. **The attacker's other transactions** (H15).
6. **Value** and **DefiLlama's record** (H16, H17).

Each is a numbered check printed as PASS or FAIL; `--tx <hash>` runs the script with another Ethereum transaction as the exploit and `--expect-weth <wei>` with another amount: the checks that read them fail, see `preuves/temoins_negatifs_2026-10-23.txt`.

## Caveats

- **The trace comes from one node.** One check (H14) depends on it and is skipped when no node serves it; the profit itself follows from the logs (H12).
- **The attack contract is not verified.** How it chooses the swap sizes is not read; the sizes are the receipt's own.
- **Who lost, and how much, is not settled here.** The vault's flows and the change in its underlying balances are given, but the end-of-block state includes later transactions, and the position's value depends on the price.
- **The proof of concept names a different recipient for the 0.05 ETH tip** (it says `0x4838...5f97`); the trace shows the block's own fee recipient, which is the address used here.
- **The pool's price was not restored:** the tick ends 544 ticks lower than it began, a drop of 5.3% in the ENS per WETH price; whether other traders closed the gap afterwards was not examined.
- **The recipients of the two later transfers were not looked into,** and whether Arrakis answered, paused the vault or compensated its holders was not examined.
- **The category is the nearest of the index's seven.** A vault that prices deposits from the pool's instantaneous price: Oracle, as for Float Protocol.

## License

MIT, see the repository root.
