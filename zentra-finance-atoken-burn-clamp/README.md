# Zentra Finance ctUSD Reserve Exploit Postmortem

Independent on-chain reconstruction of the exploit against Zentra Finance, an Aave v3 fork on Citrea mainnet (2026-09-09). Press coverage (CryptoTimes, Crypto Economy, PANews) reported about $143,000 drained from the ctUSD reserve, published the transaction hash, and said the attack vector had not been disclosed; later summaries of Zentra's own post-mortem described "an edge case" in `repayWithATokens`. What none of them showed is the exact line responsible, when it went live, that a second reserve was hit in the same transaction, or where the money sits now. Every figure below was re-derived live from public RPCs and the protocol's own verified source. Zentra's post-mortem document itself was not read.

## At a glance

| | |
|---|---|
| Incident | `repayWithATokens` cleared a borrower's debt without burning any aTokens, Zentra Finance (Aave v3 fork), Citrea mainnet |
| When | 2026-09-09 12:59:37 UTC, one transaction, `0x9ac5df7e…3074aa1`, block 12428145 |
| Press / DefiLlama figure | ~$143,000 from the ctUSD reserve (press) / $140,030, "Rounding Error" (DefiLlama) |
| Verified independently | 139,999.999999 ctUSD + 29.999999 USDC.e left the two reserves = 140,029.999998 stablecoin units, derived two independent ways that agree to the unit. DefiLlama's $140,030 matches to the dollar; the press's $143K does not reproduce |
| The finding press missed | The flaw is a "safety guard" in the aToken's `_burnScaled`: after the non-zero check, the scaled burn is capped to the caller's scaled balance. With a balance of zero, the burn becomes zero, the debt is still cleared, and the `Burn` event still reports the full amount. The cap arrived with an aToken upgrade on 2026-06-25; the implementation it replaced has no cap, and by its source the same repay would have reverted |
| The other finding press missed | The USDC.e reserve was hit by the same path in the same transaction (small, 29.999999 USDC.e), so the flaw was never ctUSD-specific. The proceeds, 55.18 ETH, went to the Ethereum wallet that funded the attacker the evening before; 55.12 ETH of it was still there on 2026-09-17 |
| What's still open | Where the $143K figure comes from; why the attacker stopped at 140,000 ctUSD and 30 USDC.e; whether any funds come back (Zentra's recovery deadline, 2026-09-14 12:00 UTC, passed with nothing visible at its recovery address as of 2026-09-17) |

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only. The single public anchor was the exploit transaction hash, published by CryptoTimes and Crypto Economy. From it, the script pulls the receipt from Citrea's public RPC (`rpc.mainnet.citrea.xyz`, chainId 4114), decodes the Aave v3 `Supply` / `Borrow` / `Repay` / `Withdraw` and aToken `Burn` events, reads aToken scaled supplies and balances on either side of the block, pulls the verified source of both aToken implementations from Citrea's Blockscout, finds the proxy `Upgraded` logs, and measures what left each reserve. It then follows the money across LayerZero to Ethereum (`gateway.tenderly.co/public/mainnet`, `eth.blockscout.com`) and reads Zentra's own on-chain messages. It closes by recomputing the loss a second way from the attack contract's own transfers and asserting both methods agree.

## What it found

### The sequence: borrow, "repay with aTokens" you do not have, withdraw collateral

The attacker's EOA (`0xa73d72d6a858df742fe756da5cb61c2288a95c17`, the same address on Citrea and Ethereum) deployed an attack contract (`0x8d85840f4c05a5d7385498f2a75daa54c6507b4b`) and called it in the same block, which holds only those two transactions. The contract flash-borrowed 200,000 USDC.e from a ctUSD/USDC.e pool, supplied it to Zentra as collateral, and borrowed 140,000 ctUSD. It then called `repayWithATokens` for 140,000.000001 ctUSD, paying with zctUSD, the ctUSD aToken, of which it held none; no zctUSD reached the contract earlier in the transaction. The debt cleared. With no debt left, it withdrew 199,999.999999 USDC.e of collateral and repaid the flash loan plus a 20 USDC.e fee. It ran the same loop once more in miniature on the USDC.e reserve: supply 50 ctUSD, borrow 30 USDC.e, repay 30.000001 with zUSDC it did not hold (the preceding withdrawal had burned its scaled balance to exactly zero), withdraw 49.999999 ctUSD. Net: 139,999.999999 ctUSD and 9.999999 USDC.e sent to the EOA.

### The zero burn is visible on-chain, and the event log hides it

The zctUSD `Burn` event in the exploit transaction reports 140,000.000001. The aToken's scaled total supply says otherwise: 1,357,533,941,399 before the block, 1,357,533,941,399 after, delta exactly zero, and the attack contract's scaled balance afterward is zero. The zUSDC scaled supply is likewise unchanged. Nothing was burned. Any indexer or dashboard that trusts `Burn` events would record this as a normal repayment.

### The cause is one clamp, added in a June upgrade

In the current aToken implementation (`0x62ff719a…bdda694`, verified, Solidity 0.8.19), `ScaledBalanceTokenBase._burnScaled` computes `amountScaled`, requires it to be non-zero, then caps it: `if (amountScaled > scaledBalance) { amountScaled = scaledBalance; }`. The code comment says the cap exists to absorb a 1-wei overshoot from ceil-rounded burns on `withdraw(max)` and full liquidations. It runs after the non-zero check, and it does not care how large the overshoot is. For a caller with a scaled balance of zero, the burn silently becomes zero. On the Pool side, `BorrowLogic.executeRepay` only reads the aToken balance when the amount is `type(uint256).max`; for an explicit amount it burns the debt first, then asks the aToken to burn `paybackAmount`, trusting that call to revert if the caller cannot pay. After the clamp, it no longer does.

Both the zctUSD and zUSDC proxies were upgraded to this implementation on 2026-06-25 at 22:01 UTC (blocks 9161296 and 9161294). The implementation they replaced (`0x2ec995d5…c63f7`, verified) has no cap: `_burnScaled` passes the full `amountScaled` to `_burn`, whose checked `balance - amount` subtraction reverts when the balance is zero. The flaw was live for about 75 days. DefiLlama's "Rounding Error" label is understandable, since the clamp was written to handle rounding, but no rounding error was exploited: the attacker simply held nothing.

### What it cost the ctUSD reserve

The ctUSD held by the zctUSD contract fell from 147,152.479895 to 7,152.479896. Before the block, supplier claims (1,374,132.29 zctUSD) were covered by cash plus outstanding variable debt, with a 38.6 ctUSD surplus. After it, the same claims face 1,234,170.90 of cash plus debt: a backing gap of 139,961.39 ctUSD, 10.19% of every ctUSD supplier's claim, with only 7,152 ctUSD of cash left to withdraw against. All four reserves (USDC.e, WCBTC, ctUSD, sUSN) were paused at block 12428650, 13:16:27 UTC, 17 minutes after the exploit and under 4 minutes after the attacker's cash-out on Citrea. As of block 12596082 (2026-09-13) both aToken proxies still pointed at the clamped implementation, with the pause the only thing standing in front of it. On 2026-09-16 at 21:50:29 UTC (block 12746471, tx `0x372509f0…0b369`, sent by `0x76be77a1…c2f860`, the same address that sent Zentra's on-chain messages) both proxies were upgraded to a new verified implementation, `0x41b70b89…811f8`. It keeps the cap but requires the overshoot to be at most one scaled unit and rejects any burn that clamps to zero; its own source comment names "repayWithATokens holding no aTokens, the 2026-09-09 drain" as the case it must revert. The ctUSD and USDC.e reserves were still paused when this was re-checked on 2026-09-17.

### The money went back to where the attacker's gas came from

On Citrea the attacker swapped the 139,999.999999 ctUSD for 139,940.792477 USDC.e (13:12:51 UTC) and sent 139,959.692499 USDC.e over LayerZero to the same address on Ethereum. There, at 13:15:59 UTC, it swapped the USDC through MetaMask Swaps for 55.160465780922437311 ETH, and one minute later sent 55.182876157279836053 ETH to `0x4eb55301d7848750059300e5ca62ec8de3b4f56a`. That wallet is the one that sent the attacker EOA its very first ETH, 0.004249243687652093 ETH on 2026-09-08 at 21:16:23 UTC, under 16 hours before the exploit. The attacker used it to buy 8.9 USDC and bridge that to Citrea over LayerZero, together with a 0.0001 cBTC native-gas drop, minutes before the attack. As of Ethereum block 25967899 it held 55.182877225991682053 ETH and had sent nothing since 2026-09-08 (nonce 9). It moved a small amount soon after: three transfers totalling 0.064010153703968582 ETH on 2026-09-13 and 2026-09-14 to `0x62c98e0c42c3f86f0e95520394ae054894a5bc93`, which forwarded them to `0x994bbf684a13c7f74be25e35a5a2fb83d948470d`. As of Ethereum block 25996322 it holds 55.118876951619856472 ETH (nonce 12). Since then, lookalike `0x62c9…bc93` addresses have sent it dust and fake-token transfers, a common address-poisoning pattern. The press described the funds as traced to "a specific wallet" without naming it. Zentra's own on-chain message, sent 2026-09-11 14:12:47 UTC, went to this address first and to the attacker EOA ten blocks later. No return is visible at Zentra's stated recovery address as of this reconstruction (0 ctUSD and 0 USDC.e on Citrea, 0.0009 ETH on Ethereum), unchanged on 2026-09-17.

### What this adds to Zentra's account, as summarised by press

Zentra's post-mortem, as relayed by press, describes an inconsistent accounting result between Pool, aToken and debt token in `repayWithATokens`, where "in a specific edge case" the debt path completed while the aToken burn was reduced to zero. The chain agrees with that description. It adds that the edge case is an aToken balance of zero, not a rounding boundary; that the responsible line was introduced by the protocol's own upgrade on 2026-06-25; that the USDC.e reserve was also hit; that the `Burn` event misreports the burn; and where the proceeds are parked.

## Caveats

- Dollar figures treat ctUSD and USDC.e as $1. The attacker's own swap realised 0.99958 USDC.e per ctUSD.
- "The previous implementation would have reverted" rests on its verified source (no cap in `_burnScaled`, checked subtraction in `_burn`). A counterfactual `eth_call` replay with state overrides was attempted and reverted inside the attacker's own contract even without any implementation change, so it proves nothing either way; see `preuves/11_counterfactual_replay_attempt.txt`.
- Calling `0x4eb55301…f56a` the attacker's own wallet is an inference from the seed-then-return pattern, not an on-chain label. It has older activity back to 2026-07-02 that was not investigated.
- Zentra's post-mortem was not opened; its wording is known only through press summaries read after the reconstruction was complete. The $143K figure appears in those summaries and could include something this reconstruction does not see, such as off-chain valuation or costs.
- The pause state, implementation slots and funder balance are snapshots as of 2026-09-13, re-checked on 2026-09-17 (see `preuves/13_*` to `preuves/15_*`), and can change. What `0x994bbf68…470d` is was not investigated.

## Files

- `reconstruct_exploit.py`: live reconstruction; re-derives every figure above and ends with an adversarial self-check that recomputes the loss two independent ways.
- `registre_hypotheses.csv`: 12 falsifiable hypotheses, each with a precise locator and a falsification test (0 anomalies under the `hypotheses-falsifiables` guard-rail tool).
- `resultats_reconstruction_2026-09-13.txt`: raw, unedited output of the reconstruction run (identical to `preuves/09_reconstruction_output.txt`).
- `preuves/`: raw evidence, including the exploit receipt, the attacker's Citrea and Ethereum transaction lists, verified source of both aToken implementations and of `BorrowLogic`, the proxy `Upgraded` and `ReservePaused` logs, the funder wallet's history, Zentra's on-chain messages, the DefiLlama record, a claim-by-claim check of press coverage, the failed replay attempt, the captured reconstruction run, and the separate adversarial verification pass (different RPCs and data sources).

## License

Released under the MIT License. See `LICENSE`.
