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

Moonwell's GitHub organization (`github.com/moonwell-fi`) publishes its full Base deployment registry directly in `moonwell-contracts-v2/chains/8453.json`. This project used that one file as its only starting anchor: the MAMO token (`0x7300B37DfdfAb110d83290A29DfB31B1740219fE`), the mMAMO market (`0x2F90Bb22eB3979f5FfAd31EA6C3F0792ca66dA32`), its comptroller (`0xfBb21d0380beE3312B33c4353c8936a0F13EF26C`), and the MAMO/USD oracle (`0xeF7541b388a77C1709a3d44BfBfC5c1ED3F0Ac94`) were all confirmed on-chain (`underlying()`, `comptroller()`, `description()`) before anything else was searched.

The incident-window block range was located by binary search against block timestamps rather than assumed: 2026-08-27 05:00 UTC resolves to block 50508727 and 11:00 UTC to block 50519527, a 10,800-block span at Base's roughly 2-second block time. From there, this project searched that window for `Mint` events on the mMAMO market and `Borrow` events on Moonwell's four other Core Markets (cbBTC `0xF877ACaFA28c19b96727966690b2f44d35aD5976`, WETH `0x628ff693426583D9a7FB391E54366292F509D457`, USDC `0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22`, wstETH `0x627Fe393Bc6EdDA28e99AE648fD6fF362514304b`), entirely independently of Moonwell's own account of the incident. Event topics were computed from their own signature hashes (`Borrow(address,uint256,uint256,uint256)`, `Mint(address,uint256,uint256)`), not copied from a block explorer's cached ABI.

One working public RPC (`gateway.tenderly.co/public/base`, no API key, no archive-node subscription, and capped at 1,000 blocks per `eth_getLogs` call, tighter than the Ethereum-mainnet gateway used elsewhere in this program, so the script chunks its log scans at 990 blocks) was used for all on-chain work, plus Moonwell's own governance forum (`forum.moonwell.fi`, fetched directly via its public Discourse JSON API at `t/post-mortem-mamo-market-incident-on-base/2208.json`) as a primary source for cross-checking, read only after this project's own numbers were already final.

Every claim below traces to one of nine falsifiable hypotheses (H1 through H9) recorded in this incident's own `registre_hypotheses.csv`, each row giving a locator into the raw result files and a concrete falsification test: the specific different result that would prove it wrong. Six of the nine, everything independently re-derived on-chain by this project itself (the DefiLlama third-strike count, the MAMO/mMAMO/oracle identity check, the blind Mint-event reconstruction, the exact borrow-total match, the EIP-7702 bytecode, and the fetch-tool fabrication test), are rated High confidence. The remaining three, everything drawn from Moonwell's own forum postmortem or from this project's own inconclusive Base-only transfer trace rather than independently re-derived on-chain (the donation-attack mechanism, the funding and cash-out chain, and the 403-transfer finding below), are rated Medium.

## What it found

### A blind reconstruction that matched the protocol's own forensics exactly

Starting only from the MAMO/mMAMO/oracle addresses, this project searched for `Mint` events on the mMAMO market in the incident window and found 8 events across 6 distinct addresses. Five of those six supplied trivial amounts (1,719.6762, 101.5, 69.1202, 50, and 1 MAMO respectively, addresses `0x396f0e55fa33513441d556f84a6ea5c6fd7d217b`, `0xcca0a99b94529493ddffe7c61a3ae454828cd3bb`, `0xdb0a05dc5e6377fe90b945123e5233f473e6cb5e`, `0x475d9a118b0dc931bb5411c2e5fa3a516bece681`, `0xbde1e1d731986c8030b15ad476d6831ada8d0b54`), unrelated background activity on the market. The sixth, `0x719eae70d4A83f35bF82A2740699F5db84BE919D`, accounts for three large deposits:

| Block | Time (UTC) | Tx | Amount |
|---|---|---|---|
| 50512452 | 07:04:11 | `a39954a6db8b7b5c94cb9b44f438767d23a88ef802953295d9ec788746632778` | 99,986.9214 MAMO |
| 50514959 | 08:27:45 | `f1af776b596e7adc1745df1ddf9ab20b5192ff7fc5ac08d9525d99302b272afd` | 7,889,608.3085 MAMO |
| 50516316 | 09:12:59 | `4cf9f1a10b416729fc55f264534efd170d2763cb114d6fa93d7023296b38cb55` | 7,100,000.0000 MAMO |

Total: **15,089,595.2298 MAMO**. Searching that same address's `Borrow` events across the other four markets gave:

| Market | Borrows | Total |
|---|---|---|
| cbBTC | 12 | 71.35549505 |
| WETH | 2 | 623.600287604679454542 |
| USDC | 3 | 2,560,000.00000000 |
| wstETH | 1 | 368.00000000 |

Reading Moonwell's own forum postmortem afterward, its independently-published figures for the same address are "15,089,595 MAMO" supplied, and gross borrows of "71.35549505" cbBTC, "623.600287604679454542" WETH, "2,560,000" USDC, and "368" wstETH: an exact match on every figure, across four separate markets, computed by two completely independent methods before comparison.

### Market context: an illiquid asset listed ten months before it was exploited

MAMO was listed as Moonwell collateral via governance proposal MIP-B48 on 15 October 2025, roughly ten months before the exploit, with a 50% collateral factor, a 20,000,000 MAMO supply cap, a 3,000,000 MAMO borrow cap, and a 30% reserve factor (per Moonwell's own forum postmortem). The principal account's own minted collateral, 15,089,595.2298 MAMO across the three deposits above, stayed under that 20,000,000 MAMO supply cap throughout. The much larger 53,393,290.31 MAMO donation described below, by contrast, never went through the `mint` path at all, so it was never checked against that cap, which is exactly why it worked as an exchange-rate manipulation rather than tripping a supply-cap limit.

### The price move behind the manipulation

Moonwell's own postmortem records the MAMO/USD price sequence directly: $0.01059700 at 09:06:11 UTC, rising to a peak of $0.43127363 at 09:28:43 UTC, a roughly 40.7x move in 22 minutes 32 seconds. Moonwell's own highest-accepted oracle price during the incident was $0.40248571, while the Aerodrome MAMO/USDC pool's own transaction VWAP ran even higher, at $0.458621073364. This price-sequence data is reported here from Moonwell's own forum postmortem, not independently re-derived by this project (see Caveats).

### The exploiter's account was a MetaMask smart account, not a custom contract

This project checked the principal account's bytecode directly: `0xef010063c0c19a282a1b52b07dd5a65b58948a07dae32b`, exactly 23 bytes. The `0xef0100` prefix is the EIP-7702 delegation designator (an EOA that has authorized its code to be a thin pointer to another contract's logic); the 20 bytes after it, `0x63c0c19a282a1B52b07dD5a65b58948A07DAE32B`, resolve to MetaMask's own official EIP-7702 Delegator contract (an 11,185-byte implementation, confirmed via Etherscan's public label for that same address). The account that ran this exploit was, mechanically, an ordinary MetaMask wallet using MetaMask's built-in smart-account upgrade feature, not a purpose-built attack contract. This project did not find this detail mentioned in the portion of Moonwell's own forum postmortem it read.

### What Moonwell's own postmortem adds beyond this project's independent search

Moonwell's forensics go further than what this project searched for on its own, and are reported here as their findings, clearly separated from this project's own independent numbers above:

- **A second, distinct exploit layered on top of the price manipulation.** The principal account separately transferred 53,393,290.31 MAMO directly into the mMAMO contract's balance without ever calling `mint`, in two transactions (09:19:59 and 09:21:09 UTC). Because the market's exchange rate is computed from the contract's real token balance, not just minted shares, this alone raised the mMAMO exchange rate by roughly 3.68x while never touching the market's 20,000,000 MAMO mint-path supply cap. This is a donation-style accounting exploit, the same general family as the "Donation Attack" this research program already saw on Tectonic (Cronos, a separate and unrelated incident).
- **The funding and cash-out path.** 800.098 ETH received from Tornado Cash on 21 and 23 August 2026. Part of it, 99 ETH, was routed through Stargate/LayerZero to Cronos and back; 700 ETH plus that same 99 ETH (799 ETH total) were then sold via CoW Swap for 1,947,391.33 USDC as the exploit's seed capital. On the way out: borrowed assets converted and consolidated, then 8,729,454 USDC burned on Base through Circle's CCTP V2 (via Wormhole's Executor helper), 8,728,319 USDC received on Ethereum, converted through Velora into DAI, and sent to the "linked operational account" (`0xD71d...C384`, per Moonwell's own naming).
- **A fast liquidation response.** 595 liquidation events across 594 transactions, the first just 32 seconds after the principal account's final successful borrow, leaving approximately $9.131 million of the $11.03 million gross borrowed still outstanding as of Moonwell's own 28 August evidence cutoff.

### An independent Base-only trace hit an unrelated wall

Before reading Moonwell's own postmortem, this project separately tried to trace the principal account's outgoing transfers directly on Base: a `Transfer`-event scan for USDC, WETH, cbBTC, and wstETH with the principal account as sender, across the post-borrow portion of the incident window (blocks 50516500-50519527). It surfaced a single transaction (block 50516508, 2026-08-27 09:19:23 UTC, `0xb11122d2932e811aabbaab1f29f11a8c1c471072194d9af13558de5471dd3776`) containing 403 separate USDC transfers to over 100 distinct recipients, in small, irregular amounts (tens to thousands of USDC each). That block falls before this project's own confirmed exploit-specific borrows for this address, and the per-recipient amounts and destinations do not match any obvious exploit-proceeds distribution pattern. Read alongside the EIP-7702 finding above, this is consistent with the principal account already being a busy, general-purpose actor on Base, not a purpose-built exploit contract, before and independently of this incident. This project did not further separate that routine activity from any exploit-specific fund movement on Base; Moonwell's own postmortem resolves the real cash-out path as a cross-chain bridge to Ethereum (see above), which a Base-only search such as this one would not have found regardless.

### DefiLlama's own dataset independently confirms "third failure"

DefiLlama's hacks feed (`api.llama.fi/hacks`) lists three separate incidents under the same `defillamaId` ("1853", `parentProtocolId` "parent#moonwell"): this one (2026-08-27, "Moonwell Lending", classification "Oracle Manipulation", technique "Spot Price Manipulation", $8.7M, chain Base), an earlier one on 2025-11-04 ($1M, chains Base and Optimism, technique "Spot Price Manipulation"), and another on 2026-02-15 ($1.78M, chain Base, technique "Oracle Misconfiguration"). This confirms press's "third failure in 11 months" framing straight from DefiLlama's own dataset, independent of the press claim itself.

### Press coverage: wide syndication, one attributed figure

Web search (delegated to a research agent, then independently re-verified) found 15+ outlets covering the incident: The Block, Crowdfund Insider, crypto.news, Cryptopolitan, KuCoin News, TechTimes, Yahoo Finance/wire, News.Bitcoin.com, ForkLog, Cryptonomist, Blockonomi, CryptoTimes, CryptoDaily, shattered.io, cryptoticker.io, and bitcoinethereumnews.com. All describe the same mechanism (MAMO, an illiquid Base collateral asset, price-pumped then borrowed against) and the same ~$8.7M headline figure attributed to PeckShield/CertiK, none independently decoding the on-chain mechanism itself.

### A fourth confirmed instance of the same methodology lesson

A research agent checking press coverage for this project re-fetched Moonwell's own forum post twice with an explicit "quote verbatim or say none exist" instruction and got two different sets of transaction hashes back, one containing a character that isn't valid hex: a demonstrated fabrication, not a theoretical risk. The same two addresses that fetch also surfaced (the principal account and the linked operational account), however, turned out to be exactly right once this project re-derived them independently on-chain, starting only from Moonwell's own primary-source registry. This is the fourth time in this research program (after Term Finance and Balancer V1) that a specific-looking detail from a summarization tool turned out correct on independent verification. The lesson stands as stated before: verify independently every time, but a precise-looking claim from such a tool is not automatically false either.

## Caveats

- This is independent research, not an audit, and not affiliated with Moonwell, MetaMask, PeckShield, CertiK, or any outlet cited above.
- The exchange-rate donation attack, the price sequence, the Tornado Cash funding chain, the CCTP/Velora cash-out path, and the exact liquidation count are reported here from Moonwell's own governance-forum postmortem, not independently re-derived by this project; only the collateral-supply and cross-market borrow totals above were computed independently before that source was read.
- This project's own attempt to trace the principal account's outgoing transfers directly on Base (see "An independent Base-only trace hit an unrelated wall" above) ran into 403 unrelated USDC micro-transfers rather than a clean exploit-proceeds trail, and did not on its own find the real cash-out path, which Moonwell's own postmortem shows left Base entirely via a cross-chain bridge.
- The precise on-chain mechanism behind the MAMO/USD price feed itself (whether a push oracle, a wrapped DEX price, or something else) was not independently determined; an `AnswerUpdated`-style search on the feed contract returned no events, suggesting a different update mechanism than a classic Chainlink push feed, not investigated further.
- One working public RPC (`gateway.tenderly.co/public/base`) was used for all on-chain work; no paid RPC, archive-node subscription, or API key was used anywhere in this project.

## Files

- `README.md`: this file.
- `reconstruct_exploit.py`: the committed Python script performing this project's independent on-chain reconstruction (contract-identity confirmation, incident-window block search via binary search on timestamps, chunked `Mint`/`Borrow` event scans across all five markets, and the EIP-7702 bytecode check on the principal account), runnable end to end with `pip install web3`.
- `registre_hypotheses.csv`: the falsifiable-hypothesis register (H1 through H9), one row per hypothesis with its own locator in the result files below, a concrete falsification test, and an evidence-confidence rating.
- `resultats_reconstruction_2026-09-09.txt`: raw console output of `reconstruct_exploit.py`'s on-chain run, steps 1 through 5.
- `resultats_sources_2026-09-09.txt`: DefiLlama hacks-feed query results, the press-coverage survey, and the cross-check against Moonwell's own governance-forum postmortem, including the fetch-tool fabrication test.
- `resultats_transferts_2026-09-09.txt`: raw output of this project's attempt to trace the principal account's outgoing transfers directly on Base.
- `LICENSE`: MIT license.
- `.gitignore`: standard Python ignores (`__pycache__/`, `*.pyc`, `.venv/`).

## License

MIT
