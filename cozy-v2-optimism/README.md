# Cozy V2 Optimism Post-Mortem

On September 7, 2026, an attacker walked away with Cozy V2's collateral on Optimism by exploiting the five-day window UMA's Optimistic Oracle gives anyone to dispute a false answer, and nobody disputed it. Cozy Finance posted its own account of what happened within hours. This project checks that account against the chain directly, and along the way finds that the three numbers now circulating for this one theft, Cozy's own, DefiLlama's, and this project's own on-chain total, do not actually agree.

## At a glance

| | |
|---|---|
| Protocol | Cozy V2, a DeFi protection (insurance) market, on Optimism |
| Attack window | September 2 (false oracle answers submitted) to September 7 (claimed), 2026 |
| Mechanism | Undisputed false "YES" answers to the UMA Optimistic Oracle during its 5-day challenge period |
| Markets triggered | 3: Aave v2, Curve, Rabbithole Quests |
| Verified independently | 174,311.01 USDC.e |
| Cozy's own published figure | 170,186 USDC.e, about $4,125 less |
| DefiLlama's tracked figure | $163,326, which turns out to be exactly one of the two claim transactions alone |
| Attacker | `0x003FE7359A4E03C85Ac2f521eC699ED84C7c5ccB`, funded via a bridge relay, cashed out to a separate EOA |

## The method

```bash
pip install web3

python3 reconstruct_exploit.py
```

The script reads the two transactions that claimed the Sets' collateral directly from Optimism (`https://mainnet.optimism.io`), sums every USDC.e transfer that lands in the attacker's cash-out address from each transaction's own receipt, then cross-checks that total against an independent direct log filter on the destination address across the full block window (156,355,000 to 156,582,000). Every address involved is classified by `eth_getCode`, contract or plain wallet, rather than assumed from how it behaves.

Alongside the script, verification ran against a small registry of eight falsifiable hypotheses (`registre_hypotheses.csv`), each one pointed at a specific line range in the two `resultats_*.txt` files and rated for evidence confidence rather than just asserted:

1. The factory contract DefiLlama's own TVL adapter cites for Cozy V2 on Optimism is directly labeled "Cozy Protocol" by Optimistic Etherscan, not just named that in a GitHub config file.
2. Cozy's own account of the incident, read directly from its X post rather than from a secondary summary.
3. The attacker address's full 21-transaction history, read directly on Optimistic Etherscan and checked against Cozy's stated timeline rather than assumed to match it.
4. Both attacker-deployed contracts, confirmed as real contracts rather than EOAs via `eth_getCode`, with matching bytecode size.
5. The drained token contract's "Cozy Set" identity, read from Etherscan's own token-tracker label rather than from the exploit transaction alone.
6. The cash-out address's classification as a plain EOA, which corrected an initial wrong assumption in this project's own draft (see below).
7. The exact stolen total, computed two independent ways from the chain.
8. That total's disagreement with both of the public figures already circulating.

All eight came back rated "High" evidence confidence in the registry; none had to be downgraded or left unresolved.

## What it found

### The mechanism, confirmed independently down to the helper contracts

Cozy's own account (posted on X, `@cozyfinance`, within hours of the incident) is specific: on September 2, an attacker bought protection in three markets and, in the same transactions, submitted false "YES" answers to the UMA Optimistic Oracle requests those markets depend on. Nobody disputed the proposals during UMA's five-day challenge window, so early on September 7 they settled as true, the markets triggered, and the attacker claimed the collateral.

Before trusting that account, this project first checked that the product itself is real and long-lived, not a fresh or malicious redeploy. The factory contract DefiLlama's own maintained TVL adapter cites for Cozy V2 on Optimism, `0xdebe19b57e8b7eb6ea6ebea67b12153e011e6447`, is directly labeled "Cozy Protocol" on Optimistic Etherscan (no manual tag added by this project) and was deployed 3 years and 123 days before this check, well before the incident.

This project then traced the attacker's own 21-transaction history on Optimistic Etherscan and found a pattern that matches without needing to take Cozy's account on faith. The wallet was funded by "Relay: Solver," a bridge relay, then ran a handful of Uniswap V3 / Metamask swaps, then made two `Contract Creation` transactions, then, 6 days before this check (matching September 2), called two custom functions on those contracts (selectors `0x67a6b2c0` and `0xcf4afd0e`), then, 36 hours before this check (matching "early on September 7"), called a third function (`0xf0f529ff`), then issued a USDC.e `Approve` and finally sent a Metamask "Meta Bridge" transaction out.

The two contracts created by the attacker, `0x9E47C805587362eF36F2cAB9d1E4E7D546f953d4` and `0xeF9886f4C8823Dc9457267A7b76A55Db2C2f5F8d`, are both unverified but both exactly 6,703 bytes, consistent with two deployments of the same purpose built code, and `0x9E47C805...` lists the attacker's own address as its `CONTRACTCREATOR` directly on Etherscan. Reading their raw, unverified bytecode directly (not decoding it function by function, see Caveats) found the attacker's own address and the Set address below present as literal 32 byte constants pushed in the disassembly, consistent with purpose built exploit/claim helpers rather than generic contract code.

One of the contracts these helpers call, `0x17705474203F7ff7ba8a940c433AB43D1F58E249`, carries Etherscan's own token tracker label "ERC-20: Cozy Set (CSET)", independent confirmation this really is one of the Sets Cozy's account refers to. It was deployed the same 3 years and 123 days before this check as the factory, and its own token holdings now sit at $4,167.84, a small residual left behind after the drain.

### Three published numbers for one theft, and they don't agree

Summing every USDC.e transfer that reaches the attacker's cash-out address, directly from the two claim transactions' own receipts, gives 174,311.006968 USDC.e. The two claim transactions themselves are `0xf7a270480f9d457bddc2c8cb4f16669ef01f185cf6bda338351a71e704c79b4b` (10,984.663268 USDC.e) and `0x8761164b8947a0690b57896a8e7370dd69fe8e9137ce61e0b21ff08581a2ce60` (163,326.3437 USDC.e), both in block 156,580,507.

The script reports "3 distinct USDC.e source addresses touched" for each of these two transactions, and that count is worth stating precisely, because it describes the whole transaction rather than the leg that reaches the cash-out wallet. Re-read on 2026-09-20, each transaction has exactly one transfer landing on the cash-out address, and in both cases the sender is one of the attacker's own helper contracts: `0xeF9886f4C8823Dc9457267A7b76A55Db2C2f5F8d` forwards the full 10,984.663268, and `0x9E47C805587362eF36F2cAB9d1E4E7D546f953d4` forwards the full 163,326.3437. The third of each transaction's three USDC.e senders is that helper itself; the other two are the Cozy-side sources feeding it, `0x255483434aBA5a75dc60c1391bB162bcd9De2882` and `0x426713C9E9522bd840b8506bc14a3Fe761a5fbd8` in the first transaction (1,525.00 and 9,409.663229), and `0x255483434aBA5a75dc60c1391bB162bcd9De2882` and the confirmed Cozy Set `0x17705474203F7ff7ba8a940c433AB43D1F58E249` in the second (2,050.00 and 160,776.340904). Each helper forwards slightly more than it receives in its own transaction, by 50.000039 and 500.002796 USDC.e respectively, and those two figures are exactly what each helper already held at block 156,580,506, the block before the claims. Both helpers hold 0 USDC.e today. The totals are unaffected: what reaches the cash-out address is still 10,984.663268 and 163,326.3437.

An independent, wider log filter on the same destination address across the full block window returns the identical two transactions and the identical total, so this isn't an artifact of which two transactions were picked by hand.

That number does not match either public figure. Cozy's own account states 170,186 USDC.e, about $4,125 less than what this project finds actually reached the attacker on-chain. DefiLlama's hacks API record for this incident (defillamaId "2964", parent "cozy-finance") reads:

```json
{
  "date": 1788739200,
  "name": "Cozy V2",
  "classification": "Protocol Logic",
  "technique": "Unknown",
  "amount": 163326,
  "chain": ["Optimism"],
  "bridgeHack": false,
  "targetType": "DeFi Protocol",
  "source": "",
  "returnedFunds": null
}
```

`date` 1788739200 is 2026-09-07 UTC, the classification is the generic "Protocol Logic," the technique field is "Unknown" despite Cozy's own account naming the exact oracle mechanism, and the `source` field is empty: DefiLlama cites nothing for its own $163,326 figure. That figure turns out to correspond exactly to the second of the two claim transactions alone (163,326.3437 USDC.e), meaning the widely cited public number for this hack is missing the first claim transaction (10,984.66 USDC.e) entirely, undercounting the true loss by about 6.7%.

Worth flagging so it isn't confused with this incident: DefiLlama's hacks feed carries a second, older, separate entry for the same parent protocol, dated 2025-08-30, technique "Missing Input Validation," amount $427,000, also on Optimism. That is a distinct, earlier incident and not the subject of this project.

### One correction made to this project's own draft before publishing

An earlier pass through this same investigation assumed the cash-out address, `0xeb2d41bcb3c3Be8Be5D74942Fa2deB601448E240`, was a third attacker-deployed helper contract, by analogy with the two confirmed ones. Running `eth_getCode` on it directly returned 0 bytes: it is a plain EOA, not a contract. The same address separately received a 0.08894469 ETH transfer from the attacker's own wallet on Ethereum mainnet, about 36 hours before this check, consistent with being a cash-out wallet reused across chains rather than a third piece of exploit infrastructure. Corrected in the script and in this README rather than left in.

## Caveats

- This project could not independently confirm the specific claim that the funds were deposited into Tornado Cash. Cozy's account states this happened within about 90 minutes of bridging; no native USDC arrival matching the bridged amount was found at the attacker's or the cash-out address on Ethereum mainnet in the window checked, which may mean the bridge delivered a different asset, routed through an intermediate address not checked here, or simply that the specific token/window searched was wrong. Reported as unconfirmed, not as false.
- Both attacker-deployed contracts are unverified on Etherscan. This project read their raw bytecode far enough to confirm hardcoded addresses and matching sizes, not far enough to decode the exact function-by-function mechanics of the UMA oracle interaction.
- At least one press summary (via Blockaid's monitoring, cited by KuCoin/RootData) describes this as a "reentrancy attack", which does not match Cozy's own, far more specific account of an oracle-dispute-window exploit. This project weights Cozy's account higher, since it is the affected party's own detailed post-incident finding with exact addresses and amounts, not a preliminary automated classification, but the discrepancy is real and unresolved here.
- Cozy's own two X posts don't use identical vocabulary. An earlier, same-day post said only that funds were drained from "the Cozy v2 Main Set and the Rabbithole Set," naming two Sets; the later, detailed account instead names three protection markets, Aave v2, Curve, and Rabbithole Quests. This project did not independently verify which Set backs which market(s), so it cannot confirm whether that is a clean one Set to two markets mapping or a genuine inconsistency between Cozy's own two statements.
- Cozy stated a full account would be posted by September 10, 2026, 18:00 UTC. This project was written and published before that date; it may be superseded by Cozy's own fuller account once available.
- One incident, one protocol, checked from public RPC endpoints and Etherscan on 2026-09-08. This is independent research, not an audit. Everything above is stated at the confidence level the on-chain data actually supports.

## Files

- `README.md`: this file.
- `reconstruct_exploit.py`: the web3.py script that reads the two claim transactions directly from Optimism, classifies the cash-out address via `eth_getCode`, sums the USDC.e that reaches it from each transaction's own receipt, and cross-checks that total against an independent log filter on the destination address across the full block window.
- `example_output.txt`: captured stdout from running `reconstruct_exploit.py`, including the per-transaction and total USDC.e figures, the `eth_getCode` classification of the cash-out address, the wide-window cross-check, and the comparison against Cozy's and DefiLlama's published figures.
- `registre_hypotheses.csv`: the registry of 11 falsifiable hypotheses (H1-H11) behind this write-up, each with a locator into the `resultats_*.txt` files below, a stated falsification test, and an evidence-confidence rating (all 11 rated High). H1-H8 date from the original 2026-09-08 pass; H9-H11 were added by the 2026-09-20 re-check.
- `resultats_sources_2026-09-08.txt`: the primary sources collected on 2026-09-08, DefiLlama's hacks API record for this incident (and the separate, older 2025 entry), Cozy Finance's own two X posts, the DefiLlama-Adapters GitHub factory address, and the news coverage found via web search.
- `resultats_verification_2026-09-08.txt`: the on-chain and Etherscan checks run independently of those sources on 2026-09-08, the factory's label and age, the attacker's full transaction history, the two helper contracts, the Cozy Set token-tracker label, the cash-out EOA's classification, and the recomputed stolen total.
- `resultats_sources_2026-09-20.txt`: the rotating figure-freshness re-check run on 2026-09-20, which re-derived both claim transactions' USDC.e flows live, established that the leg reaching the cash-out wallet is a single transfer in each case, traced each helper contract's forwarding shortfall to its own pre-claim balance, and re-confirmed that neither DefiLlama's record nor Cozy's published figure has changed.
- `LICENSE`: MIT license.
- `.gitignore`: standard Python ignore rules (`__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `.env`, `.DS_Store`).

## License

MIT
