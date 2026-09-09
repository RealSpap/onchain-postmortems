# Moonwell MAMO Oracle Exploit Postmortem

Independent on-chain reconstruction of the MAMO market exploit against Moonwell's lending protocol on Base (2026-08-27). Unlike the other postmortems in this research program, Moonwell itself published an excellent, detailed forensic postmortem on its own governance forum. This project did its own independent on-chain reconstruction first, from Moonwell's own primary-source deployment registry, and only read Moonwell's forum postmortem afterward to cross-check. The numbers matched exactly, down to the last decimal, across four separate markets. This project also found one detail, the exploiter account's use of EIP-7702, that Moonwell's own postmortem does not mention.

## At a glance

| | |
|---|---|
| Incident | Collateral and oracle price manipulation of Moonwell's illiquid MAMO market, Base mainnet |
| Window | 2026-08-27, 06:09-09:46 UTC (per Moonwell's own postmortem) |
| Press figure | ~$8.7M, per PeckShield/CertiK, syndicated across 15+ outlets |
| Verified independently | This project's own blind on-chain reconstruction (done before reading Moonwell's forum post) matched Moonwell's own official per-market borrow totals exactly: 71.35549505 cbBTC, 623.600287604679454542 WETH, 2,560,000 USDC, 368 wstETH |
| A detail beyond Moonwell's own report | The exploiter's "principal account" is a plain EOA that upgraded itself via EIP-7702 to MetaMask's own official Delegator contract, not a bespoke exploit contract - found from this project's own bytecode inspection |
| Third strike | DefiLlama's own hacks feed lists two EARLIER oracle-related incidents against the same protocol ID (Nov 2025, $1M; Feb 2026, $1.78M) before this $8.7M one, independently confirming press's "third failure in 11 months" framing |

## The method

```bash
pip install web3
python3 reconstruct_exploit.py
```

Moonwell's GitHub organization (`github.com/moonwell-fi`) publishes its full Base deployment registry directly in `moonwell-contracts-v2/chains/8453.json`. This project used that one file as its only starting anchor: the MAMO token, the mMAMO market, and the MAMO/USD oracle addresses were all confirmed on-chain (`underlying()`, `description()`) before anything else was searched. From there, this project searched Base directly for `Mint` events on the mMAMO market and `Borrow` events on Moonwell's four other Core Markets (cbBTC, WETH, USDC, wstETH) in the incident window, entirely independently of Moonwell's own account of the incident.

One working public RPC (`gateway.tenderly.co/public/base`, capped at 1,000 blocks per `eth_getLogs` call, tighter than the Ethereum-mainnet gateway used elsewhere in this program) was used for all on-chain work, plus Moonwell's own governance forum (`forum.moonwell.fi`, fetched directly via its public Discourse JSON API) as a primary source for cross-checking, read only after this project's own numbers were already final.

## What it found

### A blind reconstruction that matched the protocol's own forensics exactly

Starting only from the MAMO/mMAMO/oracle addresses, this project searched for `Mint` events on the mMAMO market in the incident window and found one address, `0x719eae70d4A83f35bF82A2740699F5db84BE919D`, responsible for three large deposits (99,986.92, 7,889,608.31 and 7,100,000.00 MAMO) totaling **15,089,595.23 MAMO**. Searching that same address's `Borrow` events across the other four markets gave:

| Market | Borrows | Total |
|---|---|---|
| cbBTC | 12 | 71.35549505 |
| WETH | 2 | 623.600287604679454542 |
| USDC | 3 | 2,560,000.00000000 |
| wstETH | 1 | 368.00000000 |

Reading Moonwell's own forum postmortem afterward, its independently-published figures for the same address are "15,089,595 MAMO" supplied, and gross borrows of "71.35549505" cbBTC, "623.600287604679454542" WETH, "2,560,000" USDC, and "368" wstETH: an exact match on every figure, across four separate markets, computed by two completely independent methods before comparison.

### The exploiter's account was a MetaMask smart account, not a custom contract

This project checked the principal account's bytecode directly: `0xef010063c0c19a282a1b52b07dd5a65b58948a07dae32b`, exactly 23 bytes. The `0xef0100` prefix is the EIP-7702 delegation designator (an EOA that has authorized its code to be a thin pointer to another contract's logic); the 20 bytes after it, `0x63c0c19a282a1B52b07dD5a65b58948A07DAE32B`, resolve to MetaMask's own official EIP-7702 Delegator contract (confirmed via Etherscan's public label for that same address). The account that ran this exploit was, mechanically, an ordinary MetaMask wallet using MetaMask's built-in smart-account upgrade feature, not a purpose-built attack contract. This project did not find this detail mentioned in the portion of Moonwell's own forum postmortem it read.

### What Moonwell's own postmortem adds beyond this project's independent search

Moonwell's forensics go further than what this project searched for on its own, and are reported here as their findings, clearly separated from this project's own independent numbers above:

- **A second, distinct exploit layered on top of the price manipulation.** The principal account separately transferred 53,393,290.31 MAMO directly into the mMAMO contract's balance without ever calling `mint`, in two transactions (09:19:59 and 09:21:09 UTC). Because the market's exchange rate is computed from the contract's real token balance, not just minted shares, this alone raised the mMAMO exchange rate by roughly 3.68x while never touching the market's 20,000,000 MAMO mint-path supply cap. This is a donation-style accounting exploit, the same general family as the "Donation Attack" this research program already saw on Tectonic (Cronos, a separate and unrelated incident).
- **The funding and cash-out path.** 800.098 ETH received from Tornado Cash on 21 and 23 August 2026, partly routed through Stargate/LayerZero to Cronos and back, then 799 ETH sold via CoW Swap for 1,947,391.33 USDC as the exploit's seed capital. On the way out: borrowed assets converted and consolidated, then 8,729,454 USDC burned on Base through Circle's CCTP V2 (via Wormhole's Executor helper), 8,728,319 USDC received on Ethereum, converted through Velora into DAI, and sent to the "linked operational account."
- **A fast liquidation response.** 595 liquidation events across 594 transactions, the first just 32 seconds after the principal account's final successful borrow, leaving approximately $9.131 million of the $11.03 million gross borrowed still outstanding as of Moonwell's own 28 August evidence cutoff.

### A fourth confirmed instance of the same methodology lesson

A research agent checking press coverage for this project re-fetched Moonwell's own forum post twice with an explicit "quote verbatim or say none exist" instruction and got two different sets of transaction hashes back, one containing a character that isn't valid hex: a demonstrated fabrication, not a theoretical risk. The same two addresses that fetch also surfaced, however, turned out to be exactly right once this project re-derived them independently on-chain, starting only from Moonwell's own primary-source registry. This is the fourth time in this research program (after Term Finance and Balancer V1) that a specific-looking detail from a summarization tool turned out correct on independent verification. The lesson stands as stated before: verify independently every time, but a precise-looking claim from such a tool is not automatically false either.

## Caveats

- This is independent research, not an audit, and not affiliated with Moonwell, MetaMask, PeckShield, CertiK, or any outlet cited above.
- The exchange-rate donation attack, the Tornado Cash funding chain, the CCTP/Velora cash-out path, and the exact liquidation count are reported here from Moonwell's own governance-forum postmortem, not independently re-derived by this project; only the collateral-supply and cross-market borrow totals above were computed independently before that source was read.
- This project's own attempt to trace the principal account's outgoing transfers on Base directly ran into 403 unrelated USDC micro-transfers from the same address in a single transaction, evidence that this EIP-7702 account was already a busy, multi-purpose actor on Base; Moonwell's own postmortem resolves this by showing the real cash-out path left Base entirely via a cross-chain bridge, which this project's Base-only search would not have found on its own.
- The precise on-chain mechanism behind the MAMO/USD price feed itself (whether a push oracle, a wrapped DEX price, or something else) was not independently determined; an `AnswerUpdated`-style search on the feed contract returned no events, suggesting a different update mechanism than a classic Chainlink push feed, not investigated further.
- One working public RPC (`gateway.tenderly.co/public/base`) was used for all on-chain work; no paid RPC, archive-node subscription, or API key was used anywhere in this project.

## License

MIT
