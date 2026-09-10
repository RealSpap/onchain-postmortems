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

The script reads the two transactions that claimed the Sets' collateral directly from Optimism (`https://mainnet.optimism.io`), sums every USDC.e transfer that lands in the attacker's cash-out address from each transaction's own receipt, then cross-checks that total against an independent direct log filter on the destination address across the full block window. Every address involved is classified by `eth_getCode`, contract or plain wallet, rather than assumed from how it behaves.

## What it found

### The mechanism, confirmed independently down to the helper contracts

Cozy's own account (posted on X, `@cozyfinance`, within hours of the incident) is specific: on September 2, an attacker bought protection in three markets and, in the same transactions, submitted false "YES" answers to the UMA Optimistic Oracle requests those markets depend on. Nobody disputed the proposals during UMA's five-day challenge window, so early on September 7 they settled as true, the markets triggered, and the attacker claimed the collateral.

This project traced the attacker's own 21-transaction history on Optimistic Etherscan and found a pattern that matches without needing to take the account on faith: funding via a bridge relay, then two `Contract Creation` transactions 6 days before this check (matching September 2), followed by two custom function calls that day, then two more calls roughly 36 hours before this check (matching "early on September 7"), then a USDC.e approval and a bridge transaction out. The two contracts created by the attacker are both unverified but both exactly 6,703 bytes, consistent with two deployments of the same purpose-built code, and one of them lists the attacker's own address as its `CONTRACTCREATOR` directly on Etherscan. One of the contracts these helpers call, `0x17705474203F7ff7ba8a940c433AB43D1F58E249`, carries Etherscan's own token-tracker label "ERC-20: Cozy Set (CSET)", independent confirmation this really is one of the Sets Cozy's account refers to.

### Three published numbers for one theft, and they don't agree

Summing every USDC.e transfer that reaches the attacker's cash-out address, directly from the two claim transactions' own receipts, gives 174,311.006968 USDC.e. An independent, wider log filter on the same destination address across the full block window returns the identical two transactions and the identical total, so this isn't an artifact of which two transactions were picked by hand.

That number does not match either public figure. Cozy's own account states 170,186 USDC.e, about $4,125 less than what this project finds actually reached the attacker on-chain. DefiLlama's hacks tracker records $163,326 for this incident, technique listed as "Unknown", source field empty. That figure turns out to correspond exactly to the second of the two claim transactions alone (163,326.3437 USDC.e), meaning the widely-cited public number for this hack is missing the first claim transaction (10,984.66 USDC.e) entirely, undercounting the true loss by about 6.7%.

### One correction made to this project's own draft before publishing

An earlier pass through this same investigation assumed the cash-out address was a third attacker-deployed helper contract, by analogy with the two confirmed ones. Running `eth_getCode` on it directly returned 0 bytes: it is a plain EOA, not a contract. The same address separately received an ETH transfer from the attacker's own wallet on Ethereum mainnet, consistent with being a cash-out wallet reused across chains rather than a third piece of exploit infrastructure. Corrected in the script and in this README rather than left in.

## Caveats

- This project could not independently confirm the specific claim that the funds were deposited into Tornado Cash. Cozy's account states this happened within about 90 minutes of bridging; no native USDC arrival matching the bridged amount was found at the attacker's or the cash-out address on Ethereum mainnet in the window checked, which may mean the bridge delivered a different asset, routed through an intermediate address not checked here, or simply that the specific token/window searched was wrong. Reported as unconfirmed, not as false.
- Both attacker-deployed contracts are unverified on Etherscan. This project read their raw bytecode far enough to confirm hardcoded addresses and matching sizes, not far enough to decode the exact function-by-function mechanics of the UMA oracle interaction.
- At least one press summary (via Blockaid's monitoring, cited by KuCoin/RootData) describes this as a "reentrancy attack", which does not match Cozy's own, far more specific account of an oracle-dispute-window exploit. This project weights Cozy's account higher, since it is the affected party's own detailed post-incident finding with exact addresses and amounts, not a preliminary automated classification, but the discrepancy is real and unresolved here.
- Cozy stated a full account would be posted by September 10, 2026, 18:00 UTC. This project was written and published before that date; it may be superseded by Cozy's own fuller account once available.
- One incident, one protocol, checked from public RPC endpoints. This is independent research, not an audit. Everything above is stated at the confidence level the on-chain data actually supports.

## License

MIT
