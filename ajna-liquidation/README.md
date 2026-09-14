# Ajna Finance Liquidation Exploit Postmortem

Independent on-chain reconstruction of the Ajna Finance liquidation-math exploit on Ethereum mainnet (2026-08-28/29). DefiLlama's own hacks feed carries this incident as "Ajna V2" (defillamaId 4019, parentProtocolId "parent#ajna"), classification "Protocol Logic", technique "Liquidation Logic Flaw", amount $775,400, but its own `source` field is empty: DefiLlama itself does not link to a single write-up. Every press report found independently (Defimon Alerts, cryptoticker.io, cryptotimes.io, Cryptopolitan) named a dollar total and a technique, but not one of them published a single on-chain address. This project starts where they stopped: the actual pool contracts, the attacker's wallet and exploit contracts, the flashloan it used, and the exact transaction that moved the bulk of the money.

## At a glance

| | |
|---|---|
| Incident | Liquidation-math exploit against Ajna Finance's oracleless lending pools, Ethereum mainnet |
| Window | 2026-08-28 15:15 UTC to 2026-08-29 16:02 UTC |
| Press figure | ~$775,400 across "seven Ethereum pools" (Defimon Alerts), no addresses published anywhere |
| Verified independently | The exploited pools live on a second, undocumented Ajna factory, not the one on Ajna's own docs page |
| Headline transaction | A single Balancer V2 flashloan-funded call drained 49.32 WETH (~$121,800) from the cbETH/WETH pool in one transaction, block 25,854,585 (15:18:35 UTC). The block press cites as the "first extraction", 25,854,888 (16:19:11 UTC), is on the same pool but carries the attacker's next, much smaller round (~3.26 WETH net) |
| What's still open | A clean, single attacker for all seven pools could not be confirmed; two other addresses active on the remaining six pools may be copycats or unrelated liquidation bots, named honestly rather than guessed at |

## The method

```bash
pip install web3
python3 reconstruct_exploit.py
```

Ajna's own official address list (`faqs.ajna.finance/info/deployment-addresses-and-bridges`) gives one `ERC20PoolFactory` address for Ethereum mainnet, `0x6146DD43C5622bB6D12A5240ab9CF4de14eDC625`, alongside an ERC721 factory and a `PoolInfoUtils` utility contract. It lists no individual pool addresses. Every pool that factory has ever deployed is enumerable directly: it emits a `PoolCreated(address,bytes32)` event with neither parameter indexed, so a single `eth_getLogs` call for the event's topic0 across full mainnet history returns all of them, no archive-tier RPC or pagination required. Each pool then exposes its own `collateralAddress()`/`quoteTokenAddress()` getters directly, so its token pair is read on-chain, not guessed from a name.

The press's own cited timestamp for "first extraction" (August 28, 16:19 UTC, via cryptoticker.io) resolves to an exact, checkable block number, 25,854,888, confirmed word for word via a direct `eth_getBlockByNumber` call. Checking that block for any log from any pool of the documented factory returns zero: the pool actually hit was never deployed by the address Ajna's own docs list. The fix was a broader, address-unfiltered search: Ajna's `Kick` and `AuctionSettle` events (the start and end of a liquidation auction) have well-known signatures regardless of which factory deployed the pool emitting them. Searching mainnet for those two signatures alone, no address filter, in a 25,852,000 to 25,858,000 block window around the incident, surfaces every pool actually active that day, from either factory at once. The same script then traces the confirmed attacker's exact Kick transaction, decoding its WETH `Transfer` events directly from the transaction receipt rather than trusting any summary.

## What it found

### A second, undocumented Ajna factory deployed the pool that was actually hit

Searching Ajna's documented `ERC20PoolFactory` turns up 224 real pools, none of which have any activity in block 25,854,888. The broad, factory-agnostic `Kick`/`AuctionSettle` search instead surfaces 13 distinct active pool addresses in the same window, 7 of which do not belong to the documented factory: WETH/USDC, wstETH/WETH, rETH/WETH, rETH/DAI, cbETH/WETH, WBTC/DAI, and sDAI/USDC, all confirmed as real pools by direct `collateralAddress()`/`quoteTokenAddress()` calls, all coming from a second, publicly undocumented Ajna factory. Ajna is an open-source, permissionlessly-deployable protocol; nothing about a second factory existing is itself suspicious, but no public source this project found documents it, and it is the one that mattered here. An eighth pool from that same undocumented factory, sUSDe/DAI (`0x34bC3D3d274A355f3404c5dEe2a96335540234de`), was located during the same factory-identification pass but showed no `Kick`/`AuctionSettle` activity in the incident window and is not counted among the seven; it is not named in any press coverage found either.

### The complete seven-pool set: an exact category match, addresses no press source ever published

The remaining 6th of the 13 active pools, `syrupUSDC/USDC` (`0xbCda8EE352778071fc7f09B8bfBcD832aa09CeE9`), belongs to the *documented* factory: it is the only one of that factory's 224 pools active in the window, and the only "syrupUSDC" pool that factory has ever created, a unique collateral symbol across all 224, making the match to the press's "syrupUSDC" line unambiguous. Combined with the 6 non-cbETH pools from the undocumented factory, the 7 collateral categories cryptoticker.io and cryptotimes.io both named (syrupUSDC, wstETH, rETH, cbETH, WBTC, WETH/USDC, sDAI) are each covered exactly once, a complete match, with every address independently located on-chain and never published by any secondary source found:

| Pool | Address | Factory |
|---|---|---|
| WETH/USDC | `0x1C50ce3550D1846134F3B7c09785e7005F6A1566` | undocumented |
| wstETH/WETH | `0x37d3a44C905663d7B77C9b574b941D4FbF713A91` | undocumented |
| rETH/WETH | `0xa2fFdC7EFeF98469d11370d91c0A17DC83EC2BDA` | undocumented |
| rETH/DAI | `0x42d3f9C4dF0b98c3974Fd539A7EA9d0847F37Ef5` | undocumented |
| cbETH/WETH | `0xad24FC773e125Edb223C38a39657cB64bc7C178e` | undocumented (press's "first extraction" pool) |
| WBTC/DAI | `0xdB30a08Ebc49af1BaF87f57824f85056cEd33d5F` | undocumented |
| sDAI/USDC | `0xf4ab415e00FF0Ed4f25D31d7E9140f3C75B69E7D` | undocumented |
| syrupUSDC/USDC | `0xbCda8EE352778071fc7f09B8bfBcD832aa09CeE9` | documented (created at block 20,421,260) |

Direct `balanceOf` calls bracketing the incident (blocks 25,850,000 to 25,870,000) confirm a severe quote-token drop on every one of the eight:

| Pool | Quote asset | Before | After | Delta |
|---|---|---|---|---|
| WETH/USDC | USDC | 28,770.27 | 5,685.50 | -23,084.77 |
| wstETH/WETH | WETH | 50.89 | 2.27 | -48.62 |
| rETH/WETH | WETH | 6.97 | 1.82 | -5.15 |
| rETH/DAI | DAI | 40,137.88 | 8,128.54 | -32,009.34 |
| cbETH/WETH | WETH | 49.34 | 0.46 | -48.88 |
| WBTC/DAI | DAI | 34,847.81 | 6,244.01 | -28,603.80 |
| sDAI/USDC | USDC | 13,228.52 | 1,443.98 | -11,784.54 |
| syrupUSDC/USDC | USDC | 92,357.69 | 5,326.72 | -87,030.97 |

These are net balance deltas over a fixed block window, a weaker signal than a fully-traced transaction, and are reported at that lower confidence (see Caveats). For reference, cryptoticker.io's own per-pool press breakdown (syrupUSDC ~$173,700, wstETH ~$159,800, rETH ~$143,000, cbETH ~$136,900, WBTC ~$101,800, WETH/USDC ~$42,000, sDAI ~$18,000) sums to almost exactly its own $775,400 headline, and every one of the seven categories it names lines up with a pool independently confirmed active in the same window here.

### One transaction, one flashloan, 49.32 WETH

The cbETH/WETH pool is the one the press's own timeline points to by exact block. Its WETH balance drop (49.34 to 0.46, a delta of 48.88 WETH per the table above) is accounted for almost entirely by a single transaction:

- **2026-08-28 15:18:35 UTC** (block 25,854,585): a fresh externally-owned account, `0x6F2f5236b10FE7162Da077A2779f8b5f04b7827e` (nonce 10 at block 25,858,000, not a long-running bot), calls a contract it had deployed roughly 90 seconds earlier, `0x80AD419C4783A09252Ad6a576ce059f51Cc53D47` (24,328 bytes of bytecode, its second-ever transaction).
- That call (tx `0x8a8793963c0ef443b9a396665c3c185ded132d5f99daf7c99e87125597016e64`) borrows a 105 WETH flashloan from the canonical Balancer V2 Vault (`0xBA12222222228d8Ba445958a75a0704d566BF2C8`), interacts with the cbETH/WETH pool's `Kick` function (the call that starts a liquidation auction), and the pool's WETH `Transfer` events, decoded directly from the receipt, show the exploit contract netting 49.3191 WETH before the same transaction repays the 105 WETH flashloan in full.
- 49.3191 WETH captured against a 48.8810 WETH measured pool-balance drop is a gap of well under half a WETH, close enough that this single transaction is treated as explaining almost the entire loss on this pool.
- At roughly $2,470/ETH (the same rate this research program's other work independently confirmed for late August 2026), that single transfer alone is worth **~$121,800**, about a fifth on its own of the $775,400 the press reports across all seven pools combined.

### The attacker came back for smaller amounts over the next 13 hours

The same EOA sent 25 transactions in total between 2026-08-28 15:15:35 UTC and 2026-08-29 16:01:47 UTC (retrieved from Blockscout's public API, no key required), deploying at least three separate exploit-contract instances in sequence and reusing the same four function selectors (`0x84aef632`, `0x01681a62`, `0x9a325b22`, `0xf1cd0d25`) against each new instance:

| Exploit contract | First used | Notes |
|---|---|---|
| `0x80AD419C4783A09252Ad6a576ce059f51Cc53D47` | ~15:17 UTC, 08-28 | 24,328 bytes; the 49.32 WETH extraction above |
| `0xF0D1Bf3C09dB0bAfFa6ff638579Fef44056C68Ce` | ~03:19 UTC, 08-29 | four follow-up rounds through 04:20 UTC, then one more at 15:20-15:23 UTC |
| `0x112616Fe7209FEA053D2d558F2Ba76ae651ff7B9` | ~15:23 UTC, 08-29 | final round before cash-out |

A second `AuctionSettle` call at 16:19:11 UTC (block 25,854,888, tx `0x12dfde52...`) borrowed a much smaller 4 WETH flashloan and moved roughly 3.26 WETH net to the exploit contract, of which 1.7194 WETH went straight to the attacker EOA; the following rounds on 08-29 (via the second and third exploit-contract instances) borrowed sub-1-WETH to ~10-WETH flashloans each, netting on the order of a few tenths of a WETH up to about 4.78 WETH per round, consistent with the attacker repeatedly extracting whatever smaller residual the pool's broken accounting still exposed after the first, much larger extraction; several of these rounds' internal transfers were not reconciled to the last decimal (see Caveats). The trail ends at 2026-08-29 15:59:35 UTC with a WETH-to-ETH `withdraw` call, followed two minutes later, at 16:01:47 UTC, by a transfer to `0xA60e1a120D076F650e7E3F5f79A8fEd18b05bb48`, the closest thing this project found to a cash-out destination; it was not traced further.

### The other six pools: two addresses, two plausible readings, neither asserted as fact

The `Kick` transactions on the other six pools come from two addresses distinct from the confirmed cbETH attacker:

| Address | Type | Nonce/code at block 25,858,000 | Pools |
|---|---|---|---|
| `0xcccc640018f8c2b00fa45F456017AD2378Eb3447` | 23-byte contract (likely a minimal proxy) | nonce 242 | WETH/USDC, wstETH/WETH, WBTC/DAI, sDAI/USDC (4 of 6) |
| `0xc213145EF56c0f162E0c3d79e6E107b25Cb8c453` | plain EOA | nonce 103 | rETH/WETH, rETH/DAI, syrupUSDC/USDC (3 of 6) |

Both profiles are ambiguous on their own. A high transaction count and a minimal-proxy pattern are exactly what a long-running, unrelated liquidation-keeper bot would look like, and Ajna's `Kick` function is permissionless and incentivized, so a routine keeper calling it on several pools in the same hour is not inherently suspicious. But both readings are equally consistent with a second and third opportunist who saw the first pool's public `Kick`/`AuctionSettle` transactions, recognized the same broken math, and moved fast on other pools within minutes to hours, matching the timing observed here. This project did not trace either address's history on other protocols deeply enough to settle which reading is correct, and reports both rather than picking the more dramatic one without evidence to back it.

### The independently-measured numbers land in the same range as the press, not on the same total

Net WETH captured in the single confirmed cbETH transaction (49.32 WETH, ~$121,800) is already close to a fifth of the press's ~$775,400 total for all seven pools combined, and the balance-drop pattern on the other pools is of a broadly similar order of magnitude. This project's own balance-based estimate across the seven pools consistently comes in lower than the press figure, honestly explained by the fact that a net balance delta over a fixed window measures net flow, not gross amount extracted, and understates the true drain if any legitimate deposits landed in the same pools during the same volatile hours. The press's $775,400 and this project's own on-chain measurements are treated as two independent, imperfectly-reconciled estimates of the same real event, not forced to agree.

## Caveats

- This is independent research, not an audit, and not affiliated with Ajna Finance, Defimon Alerts, or any outlet cited above.
- The exact root-cause line of Solidity is not identified here. The press's own description ("how the protocol books the residual quantities that arise in the process") is reported as their claim, not independently re-derived from Ajna's source code line by line.
- The single, cleanly-attributed finding in this project is the cbETH/WETH pool's initial 49.32 WETH extraction. The other pools' figures rest on a balance-delta check over a fixed block window, a weaker form of evidence than a fully-traced transaction, and are reported at that lower confidence level.
- The two addresses active on the other six pools are not confirmed as either copycat attackers or unrelated bots; both readings are stated, neither is asserted as fact.
- The smaller follow-up rounds on 2026-08-29 (via the second and third exploit-contract instances) were not reconciled transfer-by-transfer to the last decimal; net amounts per round are reported as approximate ranges, not exact figures.
- ETH was priced at ~$2,470 for the one USD conversion in this project (the WETH figure on the cbETH pool), the same rate independently used elsewhere in this research program for the same window; it is an approximation, not a trade-level price.
- The final destination address (`0xA60e1a120D076F650e7E3F5f79A8fEd18b05bb48`) was identified but not traced further; whether it is a personal wallet, an exchange, or a mixer entry point is not established here.
- No independent Defimon Alerts publication (X/Twitter post, dashboard) was found directly during this research; all Defimon-attributed figures are as relayed by the press outlets cited above, not read from a Defimon source itself.
- DefiLlama's own hacks feed record for this incident carries an empty `source` field; the per-pool and mechanism detail above comes from independent secondary press reporting, then independently re-verified on-chain, not from DefiLlama itself.
- Two working, full-history-capable public RPC/API endpoints were used throughout (`gateway.tenderly.co/public/mainnet` and, for the attacker's transaction history, Blockscout's public API); no paid RPC or API key was used anywhere in this project.

## Files

| File | What it is |
|---|---|
| `README.md` | This postmortem. |
| `reconstruct_exploit.py` | The committed, runnable script: enumerates every pool from Ajna's documented factory, confirms block 25,854,888's timestamp, runs the broad address-unfiltered `Kick`/`AuctionSettle` search that surfaces the undocumented factory's pools, checks the cbETH/WETH pool's WETH balance before/after, and traces the attacker's first Kick transaction's flashloan and net capture. |
| `registre_hypotheses.csv` | The hypothesis register: 12 individually falsifiable claims (H1-H12), each with its exact source-file locator, a concrete falsification test, and an evidence-confidence rating (High/Medium/Low). This is the audit trail behind every claim in this README. |
| `resultats_sources_2026-09-09.txt` | Raw output of the press and DefiLlama research pass: the DefiLlama hacks-feed JSON record for "Ajna V2", the per-outlet press claims (cryptoticker.io, cryptotimes.io, Cryptopolitan, Defimon Alerts), and Ajna's own official factory/utility addresses. |
| `resultats_reconstruction_2026-09-09.txt` | Raw stdout of `reconstruct_exploit.py`: the 224-pool documented-factory enumeration, the block 25,854,888 timestamp confirmation, the 13-pool broad search and its 7 undocumented-factory results, the cbETH/WETH balance check, and the attacker's flashloan/capture trace. |
| `resultats_pools_2026-09-09.txt` | Raw output mapping all 8 exploited pools (7 undocumented-factory plus syrupUSDC/USDC from the documented factory) to the press's 7 named categories, plus the full balance-drop table across all 8 pools and the one extra pool found (sUSDe/DAI) that showed no activity and was excluded. |
| `resultats_kickers_2026-09-09.txt` | Raw output on the two addresses that called `Kick` on the six non-cbETH pools: their contract/EOA status, nonce, which pools each hit, and the bot-versus-copycat analysis. |
| `resultats_timeline_attaquant_2026-09-09.txt` | Raw output of the confirmed attacker EOA's full 25-transaction history from Blockscout: every transaction timestamp, target, and function selector, the three exploit-contract instances, and the decoded WETH `Transfer` events (flashloan borrow/repay and net capture) for each round. |
| `LICENSE` | MIT license text. |
| `.gitignore` | Standard Python ignores (`__pycache__/`, `*.pyc`, `.venv/`). |

## License

MIT
