# Balancer V1 Legacy Pools Rounding Exploit Postmortem

Independent on-chain reconstruction of a rounding-error exploit against legacy Balancer V1 pools (Ethereum mainnet, 2026-08-30/31). DefiLlama's hacks feed and roughly ten press outlets all cover this as a single $234,000 incident against a single pool. This project traced the exploit from Balancer's own primary-source deployment addresses outward and found the same operator wallet drained **four separate pools**, not one, in a single overnight run, then decoded an on-chain negotiation message no press source quoted directly.

## At a glance

| | |
|---|---|
| Incident | Rounding-error exploit against legacy, unmaintained Balancer V1 BPools, Ethereum mainnet |
| Window | 2026-08-30 22:13 UTC (operator wallet's first attack-contract deployment) to 2026-08-31 06:31 UTC |
| Press figure | ~$234,000, one pool (DPI/USDC/WETH/WBTC), per DefiLlama and ~10 syndicated outlets |
| Verified independently | The same operator wallet drained **4 distinct Balancer V1 pools**, confirmed via `BFactory.isBPool()`, each swept to a different cash-out wallet - a scope no press source reported |
| A mechanism press got wrong | No flashloan-token transfers appear anywhere in the actual exploit transactions, and the main pool's WBTC balance had already been thin for at least 7 days - contradicting the "nested flash loans used to compress reserves" framing several outlets repeated |
| A genuine primary-source find | An on-chain message, decoded directly from calldata, from an address claiming to represent Balancer DAO: a bounty offer with a 2026-09-08 21:00 UTC deadline. No response or fund return found on-chain as of this research (2026-09-09) |

## The method

```bash
pip install web3
python3 reconstruct_exploit.py
```

Balancer Labs' GitHub organization now holds only two repositories, and `balancer/balancer-core` is archived, independently corroborating press reports that Balancer Labs shut down in March 2026. Its documentation repository, `balancer/docs-v1`, is still live and lists the real BFactory address directly; this project used that one address as its only starting anchor, confirmed it on-chain, then worked outward using `BFactory.isBPool()`, `eth_getLogs`, and full transaction-receipt decoding. No address in this project was taken from a press article without an independent on-chain check first.

One working public RPC (`gateway.tenderly.co/public/mainnet`) was used throughout, plus Blockscout's public API (`eth.blockscout.com`, no key) for wallet transaction histories, and the public 4byte.directory signature database to identify two custom function selectors.

## What it found

### The DefiLlama-tracked pool, confirmed and precisely quantified

`0x2257aaac34bcb27900291f7b84ee2565a6cbac57` confirms on-chain as a real Balancer V1 pool (`BFactory.isBPool() = true`) holding exactly DPI, USDC, WETH and WBTC, matching press's description. Its single exploit transaction (block 25,872,274, 2026-08-31 02:28:23 UTC) contains 100 `LOG_JOIN` events, every one of them joining with 1 raw unit (1 satoshi) of WBTC, exactly the "rounded down to 1 satoshi" mechanism press described, now shown directly from decoded events rather than taken from an article. Net extraction: 544.77 DPI, 27,714.72 USDC, 11.45 WETH, 0.357 WBTC, landing in the attack contract `0x9cAa8d0E44b22f50057d2F4ce0D1446529e11be3`.

### The same wallet drained three more pools no press coverage mentions

The transaction above came from operator wallet `0x338C7Ec9BefbB451d66Fd8A468c32184f5689a41`, whose transaction count was 0 before 2026-08-30 21:12:59 UTC (the same fresh-burner-wallet pattern as this research program's Ajna and Notional postmortems). Reading that wallet's complete transaction history shows it deployed **four** separate attack contracts that night, each confirmed against a different real Balancer V1 pool via `BFactory.isBPool()`:

| Pool | Attack contract | Notable tokens extracted |
|---|---|---|
| A | `0x0359E5006f83E8c2CaBDd434494354Be835f3450` | USDC, DAI, 2 Uniswap V2 LP tokens, renBTC, LINK, UNI, BLZ (126,987), WSTA (869,118), SNX, WBTC |
| B | `0x5d0583cB69df5C3602292263FcA6700Cf273E2c9` | DAI, USDC, MKR, UMA (23,294), LINK, SNX (40,539) |
| C | `0xed1A1379fDc6A7A0D2a6A3E290B059469825975e` | AMPL (18,892), WBTC |
| D | `0x9cAa8d0E44b22f50057d2F4ce0D1446529e11be3` | the DefiLlama-tracked pool above |

Every pool required dozens of `execute(bytes)` calls (a generic custom-calldata executor, confirmed via the public 4byte.directory signature database) followed by a `sweep(address)` or `sweep()` call, and every one of those transactions succeeded (`status: 1`) with 1,300 to 1,600 logs each, the same repeated-rounding pattern as pool D. This project reports exact token amounts rather than a single dollar total, since it has no independently-verified historical price feed for tokens like BLZ or WSTA, but the sheer token variety and volume make clear the real scope of this incident is a multiple of the $234,000 DefiLlama recorded for pool D alone.

### Each pool's proceeds went to a different wallet, not one

Pool A's loot was swept to `0x9d0d918644c057b29538eb5567f9b48befb65f33`. Pool B's went to `0xa86e7d84bf2d1de9497d0e8eb46a90f7e99551cc`. Pool C's went to `0x0437fa52a192590440f885cf8e596aaa5e697ce5`. Pool D's went to `0xade439ade910a20854d4270d645b8a982d8f273b`. All four are plain EOAs with pre-existing transaction history, not fresh wallets, and all four are distinct from each other and from the operator wallet that ran the exploits. Splitting proceeds across four separate destinations, one per pool, is a detail no press source this project found reported.

### No flashloan was found, and the thin reserves were not freshly engineered

Several press sources describe the attacker using "nested flash loans across Aave, Spark, Morpho and Uniswap V3" to compress the pool's WBTC reserves toward zero before the rounding exploit. This project checked both claims directly: the exploit transaction's own logs contain Transfer events for exactly five tokens (DPI, USDC, WETH, WBTC and the pool's own BPT share token), nothing else, so no flashloan-token movement appears anywhere in the transaction that actually executed the exploit. Separately, the pool's WBTC balance was already close to its post-exploit level roughly a week earlier (0.362 WBTC seven days before, versus 0.357 WBTC the block before the exploit), meaning this was a long-standing thin reserve in an unmaintained legacy pool, not something the attacker freshly compressed that same night. This project cannot rule out a flashloan-funded compression happening even earlier than the week-long window checked, but found no evidence for one in the window it did check.

### A whitehat negotiation message, decoded directly from the blockchain

On 2026-09-03 16:37:23 UTC, an address (`0x3877188e9e5DA25B11fDb7F5E8D4fDDDCE2d2270`, unlabeled in Blockscout, so its claimed identity is unconfirmed) sent a zero-value transaction to the operator wallet carrying 2,830 bytes of calldata. Decoded as UTF-8 directly by this project (not paraphrased from any article), it reads as a formal notice from "Balancer DAO," offering a bounty for the funds' return, a deadline of 2026-09-08 21:00 UTC to begin contact via Blockscan chat, and a warning that after that point the case would be escalated with SEAL911, Hypernative and Balancer's legal team. The full text is in `resultats_reconstruction_2026-09-09.txt`.

### As of this research, no resolution

The operator wallet's last-ever transaction is dated 2026-09-01 07:09:11 UTC, two full days before the message above was even sent, and nothing further was found from that wallet up to this project's research date, one day after the message's own deadline. None of the four cash-out wallets show a matching return transaction either. This project found no on-chain evidence that the attacker responded, cooperated, or returned any funds.

## Caveats

- This is independent research, not an audit, and not affiliated with Balancer, Balancer DAO, SEAL911, Hypernative, or any outlet cited above.
- No historical price feed was used, so no aggregate USD figure is given for the three additional pools; only exact on-chain token amounts are reported.
- The identity of the address that sent the whitehat negotiation message is unconfirmed beyond its own message text; this project found no independent label or attribution for it.
- Whether a flashloan-funded compression happened before the 7-day window this project checked was not ruled out, only that none was found within it or in the exploit transactions themselves.
- One token in Pool B's listed underlying assets did not respond to standard `symbol()`/`name()` calls (neither the string nor the older bytes32 ABI) and was not identified; it was not part of the tokens actually swept out, so this does not affect the reported amounts.
- One working public RPC (`gateway.tenderly.co/public/mainnet`) was used throughout, plus Blockscout's public API for wallet transaction histories and the public 4byte.directory for function-selector lookups; no paid RPC, archive-node subscription, or API key was used anywhere in this project.

## License

MIT
