# Unistreet LaunchpadFactoryAuto Position Drain, Post-Mortem

On August 6, 2026, at 00:27:47 UTC, one transaction on Ethereum emptied seven Uniswap V4 liquidity positions held by the Unistreet launchpad factory and sent 17,743.907229 USDC, 0.007209570881911319 WETH and eight launch tokens to the attacker's EOA. The factory's public `launch()` function takes two byte strings from its caller and hands them, unchecked, to Uniswap V4's PositionManager as two calls made by the factory itself. The PositionManager runs them with the factory as the caller, and the factory is the owner of every launch's liquidity-position NFT. So the attacker's launch carried a call that made the factory approve the attacker's contract for all of the factory's positions, and the contract then burned seven of them and took what was inside. The whole attack runs in the constructor of a contract the attacker created in that one transaction.

DefiLlama lists $17,750 for "Unistreets" on 2026-08-05 and classes it "Access Control" / "Arbitrary External Call"; a public proof of concept in the DeFiHackLabs repository gives the transaction and the addresses. This entry re-derives it from the chain and from the factory's verified source: what `launch()` forwards, the approval the PositionManager records, the seven burned positions, the ownership of those positions one block before, the 42 logs, the attacker's 27 transactions, and the value.

The registry `registre_hypotheses.csv` states each fact as a falsifiable claim with its locator; `reconstruct_exploit.py` re-derives every on-chain number here live, check by check.

## At a glance

| | |
|---|---|
| Victim | The Unistreet `LaunchpadFactoryAuto` `0xfb60cd0b36ad4bd839b91767a6ad9055ab6ad825`, which custodies the Uniswap V4 liquidity positions of the tokens launched through it, that is, the holders and launchers of seven of those tokens |
| Chain | Ethereum |
| Date | 2026-08-06, 00:27:47 UTC, block 25692311, transaction index 0, tx `0x9583e95d5c88c7966e269197f4b09022f26b7a27ad2c13660dda6774e3136d14` |
| Mechanism | `launch(params, initCalldata, modifyCalldata, seedBuys)` is `external payable` with no access control and calls `POSITION_MANAGER.multicall([initCalldata, modifyCalldata])` with the caller's bytes. The PositionManager's `setApprovalForAll` then comes from the factory, which owns the position NFTs |
| Attacker | EOA `0xc94e23c58b9b2998edb7abc8f99393fead985076`, whose seventh transaction (nonce 6) was the contract creation `0xc7d8c70f4349acc55409800c8768e801b7556b77`; two earlier attempts the day before reverted |
| Loss | 17,743.907229 USDC and 0.007209570881911319 WETH, about $17,758 at DefiLlama's ETH price of 1,910.73 at the block time, plus seven launch tokens that were not priced |
| Funds | All of it went to the EOA in the same transaction. The EOA then made seven 1 ETH deposits into the Tornado Cash router between 2026-08-06 07:25 and 2026-08-07 07:39 UTC and has sent nothing since |
| Press figures | DefiLlama: $17,750 (Unistreets, Ethereum, "Access Control" / "Arbitrary External Call", source empty), 0.04% under the value found here. DeFiHackLabs: about 17,743.91 USDC and 0.0072 WETH (about $17.75K) |

## What `launch()` does

The factory is verified on Sourcify (exact match, `LaunchpadFactoryAuto`, solc 0.8.24). After creating a token and approving Permit2 and the PositionManager for the seed amount, `launch()` builds `bytes[] memory calls = new bytes[](2)`, sets `calls[0] = initCalldata` and `calls[1] = modifyCalldata`, and calls `IPositionManager(POSITION_MANAGER).multicall(calls)`. Both byte strings are the caller's. The function has no `onlyOwner`, no check that the calls target the new pool or token, and its only `require` is on the refund of leftover ETH at the end. Uniswap V4's PositionManager is also verified; its `multicall` runs each entry as a delegate call to itself, so the caller it sees is the factory.

## The exploit, from the receipt

The transaction is a contract creation, so everything happens in the constructor. The 42 logs show, in order: a throwaway token launched through the factory (1,000,000 units minted to the factory); a PositionManager `ApprovalForAll` event whose owner is the factory and whose operator is the new contract, approved; then seven Uniswap V4 position NFTs (ids 360162, 364347, 360385, 363137, 363145, 363678 and 364293) transferred from the factory to the zero address, each followed by a `ModifyLiquidity` on the PoolManager and the position's tokens sent to the new contract. The burns pay it 17,743.907229 USDC (17,685.8181 and 58.089129), 0.007209570881911319 WETH (3,721,675,186,263,759 and 3,487,895,695,647,560 wei) and seven launch tokens; the contract then forwards all of them, to the unit, to the EOA, with the throwaway token.

One block before, the factory owned all seven positions and the PositionManager had no approval from the factory to the attacker's contract; after the transaction it has. The factory held 15 positions at that point, so the attacker took 7 of them.

## What came before and after

The EOA has sent 27 transactions in all, every one read. The first, on 2026-07-12, sent 0.497 ETH to a contract verified on Sourcify as `RelayDepository`; it created a contract on 2026-07-23 and made two small transfers on 2026-07-25. On 2026-08-05 two contract creations sent with 0.001 ETH reverted. The exploit was its nonce 6. After it, in the hours that followed, it approved USDC and DAI, called one contract (`0xccc88a9d...`) six times with the same selector (one call reverted), and made seven 1 ETH deposits into the Tornado Cash router. Why the creations of 2026-08-05 reverted, what the call to `0xccc88a9d...` was, and whether the deposits come from this attack, were not examined.

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, an Ethereum archive node list walked in order (the state at an old block needs an archive node; the nodes that refuse are skipped), Sourcify (for the factory's source and the contracts' names), DefiLlama's hacks and coins APIs. The DeFiHackLabs proof of concept gave the transaction hash and the addresses; everything else follows from the receipt, the logs, the ownership and approval state, and the verified source. It takes under a minute.

1. **The exploit transaction** (H1, H2).
2. **The factory, its verified source and what `launch()` forwards** (H3, H4).
3. **The receipt's logs**: the approval, the seven burns, the transfers (H5 to H7).
4. **The state one block before and after** (H8).
5. **The attacker's other transactions** (H9, H10).
6. **Value** and **DefiLlama's record** (H11, H12).

Each is a numbered check printed as PASS or FAIL; `--tx <hash>` runs the script with another Ethereum transaction as the exploit and `--expect-usdc <units>` with another amount: the checks that read them fail, see `preuves/temoins_negatifs_2026-10-23.txt`.

## Caveats

- **The calls were not traced.** The approval being made through the injected call, not by some other path, is read from the `ApprovalForAll` event (owner the factory) together with the verified `launch()`; the exact bytes the attacker passed were not decoded from the constructor's input.
- **The attacker's contract is not verified.** Why it burned seven of the factory's fifteen positions and left eight was not examined.
- **The seven launch tokens were not priced.** The loss counted here is the USDC and the WETH; the proof of concept says the same and calls the launch tokens illiquid.
- **Who owned the positions** (the launchers, the holders, the protocol) and whether Unistreet answered, paused `launch()` or compensated anyone were not examined.
- **The deposits into the Tornado Cash router** are the EOA's own, read from its transactions; that they come from this attack is not shown.
- **The category is the nearest of the index's seven.** A public function that forwards arbitrary calls as the factory: Access-Control.

## License

MIT, see the repository root.
