# Ajna Finance Liquidation Exploit Postmortem

Independent on-chain reconstruction of the Ajna Finance liquidation-math exploit on Ethereum mainnet (2026-08-28/29). Every press report on this incident (Defimon Alerts, cryptoticker.io, cryptotimes.io, Cryptopolitan) named a dollar total and a technique, but not one of them published a single on-chain address. This project starts where they stopped: the actual pool contracts, the attacker's wallet and exploit contracts, the flashloan it used, and the exact transaction that moved the bulk of the money.

## At a glance

| | |
|---|---|
| Incident | Liquidation-math exploit against Ajna Finance's oracleless lending pools, Ethereum mainnet |
| Window | 2026-08-28 15:15 UTC to 2026-08-29 16:02 UTC |
| Press figure | ~$775,400 across "seven Ethereum pools" (Defimon Alerts), no addresses published anywhere |
| Verified independently | The exploited pools live on a second, undocumented Ajna factory, not the one on Ajna's own docs page |
| Headline transaction | A single Balancer V2 flashloan-funded call drained 49.32 WETH (~$121,800) from the cbETH/WETH pool in one transaction, block 25,854,888, exactly matching the press's own cited block |
| What's still open | A clean, single attacker for all seven pools could not be confirmed; two other addresses active on the remaining six pools may be copycats or unrelated liquidation bots, named honestly rather than guessed at |

## The method

```bash
pip install web3
python3 reconstruct_exploit.py
```

Ajna's own official address list (`faqs.ajna.finance/info/deployment-addresses-and-bridges`) gives one `ERC20PoolFactory` address for Ethereum mainnet. Every pool it has ever deployed is enumerable directly: the factory emits a `PoolCreated(address,bytes32)` event with neither parameter indexed, so a single `eth_getLogs` call for the event's topic0 across full mainnet history returns all of them, no archive-tier RPC or pagination required. Each pool then exposes its own `collateralAddress()`/`quoteTokenAddress()` getters directly, so its token pair is read on-chain, not guessed from a name.

The press's own cited timestamp for "first extraction" (August 28, 16:19 UTC) resolves to an exact, checkable block number, 25,854,888. Checking that block for any log from any pool of the documented factory returns zero: the pool actually hit was never deployed by the address Ajna's own docs list. The fix was a broader, address-unfiltered search: Ajna's `Kick` and `AuctionSettle` events (the start and end of a liquidation auction) have well-known signatures regardless of which factory deployed the pool emitting them. Searching mainnet for those two signatures alone, no address filter, in the exact block window around the incident, surfaces every pool actually active that day, from either factory at once.

## What it found

### A second, undocumented Ajna factory deployed the pool that was actually hit

Searching Ajna's documented `ERC20PoolFactory` (`0x6146DD43C5622bB6D12A5240ab9CF4de14eDC625`) turns up 224 real pools, none of which have any activity in block 25,854,888. The broad, factory-agnostic `Kick`/`AuctionSettle` search instead surfaces a second set of pools, from a completely different, undocumented factory, whose token pairs line up closely with the press's list: WETH/USDC, wstETH/WETH, rETH/WETH, rETH/DAI, cbETH/WETH, WBTC/DAI, and sDAI/USDC. One more pool from the *documented* factory, syrupUSDC/USDC, also shows matching activity in the same window, accounting for the seventh pool in the press's count. Ajna is an open-source, permissionlessly-deployable protocol; nothing about a second factory existing is itself suspicious, but no public source this project found documents it, and it is the one that mattered here.

### One transaction, one flashloan, 49.32 WETH

The cbETH/WETH pool (`0xad24FC773e125Edb223C38a39657cB64bc7C178e`) is the one the press's own timeline points to by exact block. Its WETH balance is confirmed, by a direct `balanceOf` call at blocks straddling the incident, to drop from 49.34 to 0.44 WETH, a loss the transaction-level trace accounts for almost entirely in a single call:

- **2026-08-28 15:17:47 UTC**: a fresh externally-owned account, `0x6F2f5236b10FE7162Da077A2779f8b5f04b7827e` (nonce 10 at the time, not a long-running bot), calls a contract it had deployed roughly 90 seconds earlier, `0x80AD419C4783A09252Ad6a576ce059f51Cc53D47` (24,328 bytes of bytecode, its second-ever transaction).
- That call borrows a 105 WETH flashloan from the canonical Balancer V2 Vault (`0xBA12222222228d8Ba445958a75a0704d566BF2C8`), uses it to interact with the cbETH/WETH pool's `Kick` function (the call that initiates a liquidation auction), and the pool pays out 49.3437 WETH as part of processing that call. After a short chain of internal transfers, the exploit contract nets 49.3191 WETH and repays the 105 WETH flashloan in the same transaction, at essentially zero net cost beyond gas and the flashloan fee.
- At roughly $2,470/ETH (the same rate this research program's other work independently confirmed for late August 2026), that single transfer alone is worth **~$121,800**.

### The attacker came back for smaller amounts over the next 13 hours

The same EOA sent 25 transactions in total between 2026-08-28 15:15 UTC and 2026-08-29 16:02 UTC, deploying at least three separate exploit-contract instances in sequence (`0x80AD419C...`, then `0xF0D1Bf3C09dB0bAfFa6ff638579Fef44056C68Ce`, then `0x112616Fe7209FEA053D2d558F2Ba76ae651ff7B9`) and reusing the same handful of function selectors (`0x84aef632`, `0x01681a62`, `0x9a325b22`, `0xf1cd0d25`) against each new instance. These follow-up rounds moved much smaller amounts (single-digit WETH or fractions of one per round, based on WETH `Transfer` events decoded directly from each transaction's receipt), consistent with the attacker repeatedly extracting whatever smaller residual the pool's broken accounting still exposed after the first, much larger extraction. The trail ends at 2026-08-29 15:59 UTC with a WETH-to-ETH `withdraw` call, followed two minutes later by a transfer to `0xA60e1a120D076F650e7E3F5f79A8fEd18b05bb48`, the closest thing this project found to a cash-out destination; it was not traced further.

### The other six pools: a consistent pattern, not a cleanly single-attributed one

All seven pools (the cbETH/WETH one above, plus WETH/USDC, wstETH/WETH, rETH/WETH, rETH/DAI, WBTC/DAI, sDAI/USDC, and syrupUSDC/USDC) show the same signature when checked directly: a severe quote-token balance drop between blocks 25,850,000 and 25,870,000, all in the same ~20,000-block window as the confirmed cbETH attack. That much is independently confirmed for every pool named in the press coverage, not assumed from it.

What this project could not cleanly resolve is a single attacker across all seven. The `Kick` transactions on the other six pools come from two addresses distinct from the confirmed cbETH attacker: `0xcccc640018f8c2b00fa45F456017AD2378Eb3447` (a 23-byte contract, likely a minimal proxy, with 242 transactions to its name by the time of the incident) and `0xc213145EF56c0f162E0c3d79e6E107b25Cb8c453` (a plain EOA with 103 prior transactions). Both profiles are ambiguous on their own: a high transaction count and a minimal-proxy pattern are exactly what a long-running, unrelated liquidation-keeper bot would look like, but they are just as consistent with a second and third opportunist who saw the first pool's public liquidation event, recognized the same broken math, and moved fast on other pools before Ajna's team could react. This project reports both readings rather than picking the more dramatic one without evidence to back it.

### The independently-measured numbers land in the same range as the press, not on the same total

Net WETH captured in the single confirmed cbETH transaction (49.32 WETH, ~$121,800) is already close to a fifth of the press's ~$775,400 total for all seven pools combined, and the balance-drop pattern on the other six pools is of a broadly similar order of magnitude per pool. This project's own rough, balance-based estimate across all seven pools comes in lower than the press figure, most likely because a simple before/after balance check measures net flow over a fixed window, not the gross amount extracted, and would understate the true drain if any legitimate deposits landed in the same pools during the same volatile hours. The press's $775,400 and this project's own on-chain measurements are treated as two independent, imperfectly-reconciled estimates of the same real event, not forced to agree.

## Caveats

- This is independent research, not an audit, and not affiliated with Ajna Finance, Defimon Alerts, or any outlet cited above.
- The exact root-cause line of Solidity is not identified here. The press's own description ("how the protocol books the residual quantities that arise in the process") is reported as their claim, not independently re-derived from Ajna's source code line by line.
- The single, cleanly-attributed finding in this project is the cbETH/WETH pool's initial 49.32 WETH extraction. The other six pools' figures rest on a balance-delta check over a fixed block window, a weaker form of evidence than a fully-traced transaction, and are reported at that lower confidence level.
- The two addresses active on the other six pools are not confirmed as either copycat attackers or unrelated bots; both readings are stated, neither is asserted as fact.
- ETH was priced at ~$2,470 for the one USD conversion in this project (the WETH figure on the cbETH pool), the same rate independently used elsewhere in this research program for the same window; it is an approximation, not a trade-level price.
- The final destination address (`0xA60e1a120D076F650e7E3F5f79A8fEd18b05bb48`) was identified but not traced further; whether it is a personal wallet, an exchange, or a mixer entry point is not established here.
- Two working, full-history-capable public RPC endpoints were used throughout (`gateway.tenderly.co/public/mainnet` and, for one cross-check, Blockscout's public API); no paid RPC or API key was used anywhere in this project.

## License

MIT
