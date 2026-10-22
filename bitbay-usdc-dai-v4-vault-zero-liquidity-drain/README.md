# BitBay UsdcDaiV4Vault Zero-Liquidity Drain, Post-Mortem

On October 9, 2026, at 02:23:42 UTC, one transaction on Polygon took 14,838.466608989135865711 DAI, the whole content of a Uniswap v4 liquidity vault that the press calls BitBay's, by redeeming a single share. The attacker's contract borrowed 107,865 DAI in two flash loans, deposited 1 wei of DAI to hold one share, pushed the pool's price out of the vault's three-tick range with swaps, called the vault's public `reposition`, which removed the vault's position and re-minted none (liquidity 0), and then withdrew its one share. The vault's `_withdraw` has a branch for `liquidity == 0` that sends the caller-named recipient the vault's entire DAI and USDC balance, whatever the share amount. The loans were repaid in the same transaction and the attacker kept 14,813.548248 USDC.

DefiLlama lists $14,838.47 for "BitBay" on 2026-10-08 and classes it as "Protocol Logic" / "Withdrawal Logic Flaw"; the press says about $14,000 to $14,838 and gives the same mechanism. This entry confirms it on the chain and in the vault's verified source: the zero-liquidity branch, the unrestricted `reposition` and the exact sequence. It does not read BitBay's own statements (none was found), the other holders' balances, or the second burst of transactions the same account made an hour later.

The registry `registre_hypotheses.csv` states each fact as a falsifiable claim with its locator; `reconstruct_exploit.py` re-derives every on-chain number here live, check by check.

## At a glance

| | |
|---|---|
| Victim | The holders of the 14,837.644859066499448843 shares of the vault `0x048e88311ca84876aea086125825492e2af2e5a0` (`UsdcDaiV4Vault`), a Uniswap v4 DAI/USDC liquidity vault; the holders were not itemized |
| Chain | Polygon |
| Date | 2026-10-09, 02:23:42 UTC, block 95204942, tx `0x5b795dc5c5e1665b712c7ccf478c1d8c59a162d698f4e0bfb40bd303e04a7ff2` (DefiLlama dates it 2026-10-08) |
| Mechanism | `_withdraw` sends the whole DAI and USDC balance to the recipient when `liquidity == 0`, whatever the share amount; `reposition` is callable by any account once the pool's price is outside the vault's range and 129,600 s have passed since the last one; the attacker pushed the price out of range, repositioned (the vault re-minted nothing, liquidity 0) and withdrew one share |
| Attacker | EOA `0x59ae3c8dd50063429d86bdaebbc350fb64e9884b` (15 transactions, 02:15:12 to 03:43:51 UTC), which deployed the contract `0xc2c6f4f7e1425be1dcb996175cf7852bf53c23e2` at 02:18:45 UTC (code not published) |
| Loss | 14,838.466608989135865711 DAI, about $14,837 at DefiLlama's DAI price of 0.99988 at the block time: the vault's whole balance after its position was removed |
| Funds | The attacker's contract repaid its loans in the same transaction and sent 14,813.548248 USDC to the EOA; 39 seconds later the EOA sent it to `0xfb7c...b025`, which passed 14,683.929701 USDC to `0xc1d1...a1b5` and 129.618547 to `0xf244...8616`; not traced further. Nothing returned was found |
| Press figures | DefiLlama: $14,838.47 (BitBay, Polygon, "Protocol Logic", "Withdrawal Logic Flaw", source empty). SlowMist's alert of 2026-10-09 as relayed by Crypto Times and Tokenpost: about 14,838.47 DAI, the `_withdraw()` zero-liquidity payout, `reposition()` used to force liquidity to zero, one share unit redeemed |

## What the vault does

The contract is verified on Sourcify (exact match, `UsdcDaiV4Vault` in `StableVault.sol`, solc 0.8.30). It holds one Uniswap v4 position in the DAI/USDC pool through the PoolManager `0x67366782805870060151383f4bbff9dab53e5cd6` and keeps shares equal to the DAI deposited. Two functions matter:

- `_withdraw(shareAmount, recipient, addDust)`: `if (liquidity == 0) { ... transfer(recipient, DAI balance) ... transfer(recipient, USDC balance) ... return; }`. The branch ignores `shareAmount`.
- `reposition(deadline)`: `if (msg.sender != minter) { ... if (ct >= tickLower && ct < tickUpper) revert PositionInRange(); }`, so anyone can call it when the pool's current tick is outside the vault's range; it also requires `block.timestamp > lastReposition + POSITION_TIMELOCK` (129,600 s). It removes the position, computes a new range around the current tick and re-mints from the vault's balances.

One block before the exploit the vault held a position of liquidity 98,869,777,365,041,977,456 on ticks 276323 to 276326 (three ticks wide), the pool's current tick was 276324 (inside), the vault had 8.390192804782497678 DAI idle, `mintThis` was false, the minter was neither the attacker's account nor its contract, and the last reposition was 7.3 days earlier.

## The exploit, call by call

The attacker's contract (selector `0xde463630`) does the following in one transaction, in this order (call trace and logs, `preuves/`):
1. A Uniswap v3 pool `0x5645dcb6...a8cf` (`flash`) lends 106,411.492456133328096283 DAI and the Balancer vault lends 1,453.569001525582433698 DAI.
2. `deposit(1, deadline)` on the vault: 1 wei of DAI, one share.
3. A swap in the PoolManager: 107,865.061456658704649884 DAI in, 107,843.364597 USDC out. The pool's price leaves the vault's range. The vault's `reposition` then passes its in-range check.
4. `reposition(deadline)`: the vault collects fees, removes its position (the PoolManager sends 14,838.464613705392149247 DAI to the vault) and emits `Repositioned(276324, 276327, 0)`: the new range, liquidity 0. The vault holds its DAI idle.
5. `withdraw(1, deadline, false)`: `liquidity == 0`, so the vault sends 14,838.466608989135865711 DAI, its whole balance, to the attacker's contract and emits `Withdrawn(attacker contract, 1, 14838466608989135865711, 0)`.
6. The Balancer loan is repaid; a swap back (93,029.816349 USDC in, 93,037.235996915182116984 DAI out); the Uniswap v3 loan is repaid with 106,422.133605378941429093 DAI (a fee of 10.641149245613332752 DAI); the remaining 14,813.548248 USDC goes to the EOA.

At the exploit's block the vault has liquidity 0, ticks 276324 and 276327, no DAI and no USDC, and the same 14,837.644859066499448843 total shares: the other holders' shares stand on an empty vault.

## What came after

39 seconds later the EOA sends the 14,813.548248 USDC to `0xfb7c...b025` in one transaction (block 95204968), which splits it as above. Between 03:36:48 and 03:43:51 UTC the EOA sends ten more transactions, deploys a third contract and calls it several times; in them the PoolManager sends 4,156.374927 USDC to the EOA. None of those transactions emits a log from this vault, so that burst is not counted here and its target was not identified.

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, Polygon RPC with archive state (Tenderly's public gateway, `polygon-bor-rpc.publicnode.com`, `polygon.drpc.org`; the call trace comes from drpc, `--trace-file` reads a saved one), Sourcify's API, and DefiLlama. DefiLlama gave a date and an amount; the press gave the attacker's abbreviated address and the mechanism; everything else follows from the receipts, logs, balances and trace. It takes about a minute.

1. **The exploit transaction** and the attacker's contract and account (H1 to H3).
2. **The vault's verified source** and its state one block before (H4, H5).
3. **The call trace and the vault's events** (H6, H7), then the vault at the exploit's block (H8).
4. **The money flows**: loans, payout, proceeds (H9 to H12).
5. **The second burst** (H13).
6. **Value** and **DefiLlama's record** (H14, H15).

Each is a numbered check printed as PASS or FAIL; `--tx <hash>` runs the script with another Polygon transaction as the exploit and `--expect-payout <wei>` with another payout: the checks that read them fail, see `preuves/temoins_negatifs_2026-10-22.txt`.

## Caveats

- **The vault is BitBay's according to the press only.** The press quotes the vault by its abbreviated address (`0x048..F2e5A0`) and the attacker by `0x59A..884B`, both of which match the addresses found here; the name BitBay comes from the press and DefiLlama. BitBay's own statements were not found.
- **Only the two functions above were read.** The vault's other functions, its `_reposition` arithmetic that gave liquidity 0 at the pushed price, its admin functions (minter, price bounds, timelocks) and the Uniswap v4 pool were not audited; the reason the re-mint came out as zero was not worked out.
- **The price push is read from the flows, not derived.** The swap amounts and the vault's state before and after show the price leaving the range; the pool's tick during the transaction was not read.
- **Who bears the loss is not itemized.** The vault's shares sum to 14,837.644859066499448843; the holders and their balances were not examined, and whether anyone was compensated is not known.
- **The loss is the DAI at one price.** About $14,837 at DefiLlama's DAI price of 0.99988; DefiLlama's $14,838.47 is the DAI count taken as dollars. The attacker's own take (14,813.548248 USDC) is smaller by loan fees and swap costs and is not the loss.
- **The attacker's contract is not published** and was not decompiled; its steps are read from the trace and logs. The destination of the proceeds past the first hop was not traced, and the identity of the account is unknown.
- **The second burst** (ten transactions, 4,156.374927 USDC from the PoolManager) is not attributed to this vault or to any protocol.
- **The category is the nearest of the index's seven, not an exact fit.** The flaw is a withdrawal branch that pays out a balance instead of a share, a logic and accounting error; the index has no logic category, so the entry sits under Rounding/Math-Bug with the other share-accounting entries.

## License

MIT, see the repository root.
