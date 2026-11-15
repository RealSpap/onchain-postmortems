# Notional Finance V1 Escrow Exploit Postmortem

Independent on-chain reconstruction of the integer-overflow exploit against Notional Finance's legacy V1 Escrow contract (Ethereum mainnet, 2026-09-03/04). Six press sources (SlowMist, CryptoRank, BeInCrypto, Blockfence, shattered.io, Cryptotimes) described the mechanism in real detail, but none of them published a contract address, a transaction hash, or the attacker's wallet. Every fact below was independently re-derived from Notional's own committed deployment records and two block numbers already public in the press coverage, then logged in a hypothesis register (`registre_hypotheses.csv`) that records, for each claim, exactly where its supporting evidence lives and what would falsify it.

## At a glance

| | |
|---|---|
| Incident | Integer-overflow exploit against Notional Finance's legacy V1 Escrow contract, Ethereum mainnet |
| Window | 2026-09-03 23:58:47 UTC to 2026-09-04 00:01:35 UTC (2 minutes 48 seconds) |
| Press figure | ~$1.73M (69,257 DAI + 1,658,524 USDC), swapped to ETH and reportedly routed through Tornado Cash |
| Verified independently | Exact same amounts to 4 decimal places, exact same block numbers, exact attacker and exploit-contract addresses, none published anywhere else found |
| A real naming discrepancy | DefiLlama's own hacks feed labels this incident "Notional V2"; every press source, and Notional's own GitHub organization structure, identifies the exploited contracts as V1 |
| What's still open | The reported Tornado Cash routing was not independently confirmed; the destination address found is an EIP-7702 delegated EOA (23-byte delegation designator), not a recognizable Tornado Cash pool |

## The method

```bash
pip install web3
python3 reconstruct_exploit.py
```

Notional Finance runs three parallel, independently-repo'd contract generations (`notional-finance/contracts` for V1, `contracts-v2`, `contracts-v3`). The V1 repo commits its own mainnet deployment addresses directly in `mainnet.json`, including the `Escrow` contract this exploit targeted; this project reads that file straight from GitHub rather than guessing an address from a block explorer search. The press's own reporting already narrowed the incident to two exact block numbers (one for the "preparatory" transaction, one for the extraction, three minutes apart); both were checked directly against `eth_getBlockByNumber` before anything else, and both timestamps match the press's own cited times to the second.

Concretely:

1. **The exploited contract addresses come from Notional's own GitHub, not a block explorer guess.** `mainnet.json` in `notional-finance/contracts` (fetched live from `raw.githubusercontent.com`) commits the full V1 address set, including a `startBlock`, well before this incident.
2. **Neither press-cited block number was taken on faith.** Both were re-read directly via `eth_getBlockByNumber` and their own timestamps compared to the articles' claimed times.
3. **No press source publishes a transaction hash, so both incident transactions were located from the blocks' own contents**, not copied from an article: the preparatory block was scanned for a contract-creation transaction that also touches the `ERC1155Trade` address, and the extraction block for the `Escrow` contract's own event log.
4. **The attacker wallet's full transaction history was pulled independently**, from Blockscout's public API (`eth.blockscout.com/api/v2`, no key), rather than assumed from the press's own laundering narrative.
5. One public RPC (`gateway.tenderly.co/public/mainnet`) was used throughout; no paid RPC or API key anywhere in this project.

## What it found

### Notional's own V1 deployment record, read live, not copied from a press screenshot

`mainnet.json` on `notional-finance/contracts`, committed well before this incident, names the full V1 address set:

| Contract | Address |
|---|---|
| escrow | `0x9abd0b8868546105F6F48298eaDC1D9c82f7f683` |
| portfolios | `0x0A4721117040ABF319b954aBF13F654505C34920` |
| erc1155 | `0x3a31b8121D810B1D7b3004f94f205E6DFC1bf8d9` |
| erc1155trade | `0xBbA899578bd3fA3DAa863A340f5600797993eF08` |
| proxyAdmin | `0x09DbA4Fa1826f7d0E284513333FE71867b324261` |
| directory | `0xdce848258dFB1bBf34C346Fbe40F10F8a42d2526` |
| startBlock | `11003692` |

`notional-finance/contracts` is the repository Notional itself treats as V1, distinct from its separate `notional-finance/contracts-v2` and `notional-finance/contracts-v3` repositories. That separation is what settles the naming question below, independently of the press.

### Both press-cited blocks check out to the second

Block 25,900,220 timestamps to 2026-09-03 23:58:47 UTC (283 transactions); block 25,900,234 timestamps to 2026-09-04 00:01:35 UTC (251 transactions), 2 minutes 48 seconds later. The press's own "three minutes later" framing is accurate to within rounding.

### One wallet, its first-ever transaction, deploys the exploit contract

The attacker EOA, `0xDaCC235a494750193695A111D715c2ca12b5Ce38`, had a transaction count of exactly 0 going into block 25,900,220: the contract-creation transaction found in this exact block, `0xe1589a19fe742f0d553889214abade69551fe944acffac014c28cc07b325d60a`, is this wallet's very first transaction ever. Its constructor itself calls Notional V1's `ERC1155Trade` contract (`0xBbA899578bd3fA3DAa863A340f5600797993eF08`, the address committed in Notional's own `mainnet.json`), deploying the exploit contract at `0xEc434A2f9B7b93AAD1beD77d6Bc512A75aE90d78` (6,425 bytes of bytecode) and setting up the two `mintfCashPair()` positions the press describes in a single, gas-efficient constructor call, not two separate top-level transactions.

### The extraction transaction, decoded directly, matches the press to four decimal places

Three minutes later, at block 25,900,234, the same attacker wallet's second-ever transaction (`0xc3f3e318f7ab2d0daaba59e6ec901d25d1fe8a89aafe2b2b62e3b9aee1a24efa`) calls the exploit contract again, sending 0.07 ETH along with the call (most likely gas or fee provisioning for an internal step, not itself part of the stolen funds; this project did not determine its exact purpose). That call triggers Notional V1's `Escrow` contract (`0x9abd0b8868546105F6F48298eaDC1D9c82f7f683`) to release funds through two intermediate addresses, one per token, before landing directly in the attacker's wallet, read straight from the transaction's own `Transfer` events:

| Token | Escrow releases to | Then forwards to attacker | Amount |
|---|---|---|---|
| DAI | `0x265ccff3673bcab03867988081cd51bfd919c03c` | `0xDaCC235a494750193695A111D715c2ca12b5Ce38` | **69,257.3727** |
| USDC | `0x4a3508c5ac0677325932f3bc786ae7a1c3e9caff` | `0xDaCC235a494750193695A111D715c2ca12b5Ce38` | **1,658,524.8641** |

Both figures match the press's rounded ~69,257 DAI and ~1,658,524 USDC exactly, now to four decimal places, read directly from the receipt rather than taken from any article. Immediately after (nonce check at block 25,900,234 returns 2), the wallet's transaction count confirms this extraction was only its second transaction ever.

### DefiLlama's own hacks feed mislabels this "V2"

DefiLlama's `api.llama.fi/hacks` record for this incident reads, in full:

```
{
  "date": 1788480000,
  "name": "Notional V2",
  "classification": "Token & Share Accounting",
  "technique": "Arithmetic Error",
  "amount": 1727782,
  "chain": ["Ethereum"],
  "bridgeHack": false,
  "targetType": "DeFi Protocol",
  "source": "",
  "returnedFunds": null,
  "defillamaId": "234",
  "parentProtocolId": "parent#notional",
  "language": "Solidity"
}
```

`"source"` is empty here, like the other DefiLlama records checked for this repository. Every press source found (SlowMist, CryptoRank, BeInCrypto, Blockfence, shattered.io, Cryptotimes) identifies the exploited contracts as V1; Blockfence's headline explicitly calls it "Notional Finance V1". This project's own on-chain trace settles it independently: the exploited `Escrow` address is committed in `notional-finance/contracts`, the repository Notional itself names V1, distinct from its separate `contracts-v2` and `contracts-v3` repositories. The most widely syndicated tracker for on-chain hacks has the version number wrong for this one.

### The attacker's entire on-chain history: five transactions, ever

Retrieved from Blockscout's public API (`eth.blockscout.com/api/v2`, no key), the attacker wallet's full transaction history, in order:

| # | Time (UTC) | Target | Block | Value | Description |
|---|---|---|---|---|---|
| 1 | 2026-09-03 23:58:47 | (contract creation) | 25,900,220 | 0 | Deploys exploit contract, calls `ERC1155Trade` in constructor |
| 2 | 2026-09-04 00:01:35 | `0xEc434A2f...90d78` | 25,900,234 | 0.07 ETH | Extraction call, selector `0xe5fca7b6` |
| 3 | 2026-09-04 00:03:35 | USDC token | 25,900,244 | 0 | `transfer` call |
| 4 | 2026-09-04 00:04:11 | DAI token | 25,900,247 | 0 | `transfer` call |
| 5 | 2026-09-04 00:04:35 | `0x8aaf01B6...E3be6` | 25,900,249 | 1.105701960350961564 ETH | Final send, last transaction found |

Transactions 3 and 4 are the attacker moving its own, already-received DAI and USDC balances, most likely consolidating or routing them onward toward the swap to ETH the press describes; this project did not decode their exact recipients or amounts. Five transactions total, and no sixth was found by this project as of the date this reconstruction was run.

### What this project could not confirm: the Tornado Cash laundering claim

The press reports the stolen funds were swapped into ~689 ETH and routed through Tornado Cash. The attacker wallet's fifth and final transaction sends only 1.105701960350961564 ETH, to `0x8aaf01B6F9AcC973274B8718BE4D1C1be10E3be6`, an address whose code is exactly 23 bytes, `0xef0100` followed by `0x63c0c19a282a1B52b07dD5a65b58948A07DAE32B`: an EIP-7702 delegation designator, meaning an externally-owned account that delegated its execution to that contract (the same delegate the Moonwell MAMO exploiter used in this repo), not a minimal proxy. It carries no name or metadata in Blockscout's index. That destination does not resolve to a named or recognizable Tornado Cash pool by any means this project checked, and the ~1.11 ETH transfer found does not by itself account for the full ~689 ETH the press claims was laundered. This project reports the press's Tornado Cash claim as unconfirmed rather than independently verified, and did not trace the funds' full path from the attacker's DAI/USDC balances through to their final destination.

## Caveats

- This is independent research, not an audit, and not affiliated with Notional Finance, SlowMist, or any outlet cited above.
- The exact Solidity mechanics of the `uint128` downcast are reported here as the press (specifically SlowMist and shattered.io) describe them; this project verified the transaction-level effect (the exact amounts moved, the exact addresses, the exact timing) but did not independently re-derive the vulnerable line of code from Notional V1's source.
- SlowMist's own write-up, the most technically detailed press source found, returned an HTTP 403 to automated requests; it is summarized here only via search-result excerpts, not fetched and read directly.
- The full path of the stolen DAI and USDC after they reached the attacker's wallet, including the claimed swap to ~689 ETH and any Tornado Cash deposit, was not independently traced; transactions 3 and 4 in the attacker's own history (its own USDC and DAI transfer calls) were not decoded for exact recipients or amounts.
- The V1-vs-V2 mislabeling is established here from the exploited contract's own address and Notional's own repository structure (the address is committed in the repo Notional itself calls V1), not from any deeper audit of DefiLlama's internal ID scheme.
- This project's own hypothesis register rates six of its eight logged hypotheses "High" evidence confidence; the claim that only 5 transactions exist for the attacker wallet is rated "Medium" (a sixth, undiscovered transaction would invalidate it), and the claim that the final 23-byte destination is not Tornado Cash is rated "Low" (this project could not check a third-party address-labeling service).
- One working public RPC (`gateway.tenderly.co/public/mainnet`) was used throughout, plus Blockscout's public API for the attacker wallet's short transaction history; no paid RPC or API key was used anywhere in this project.

## Files

- `README.md`, this document.
- `reconstruct_exploit.py`, the committed Python script (uses `web3.py` and `eth_abi`) that independently re-derives both block timestamps, locates the attacker's deployment and extraction transactions, and decodes the exact DAI/USDC amounts straight from Ethereum mainnet via a public RPC.
- `registre_hypotheses.csv`, the hypothesis register: eight claims (H1-H8), each with its own locator inside the `resultats_*.txt` files below, a falsification test, and an evidence-confidence rating.
- `resultats_attaquant_2026-09-09.txt`, the attacker wallet's full 5-transaction history, retrieved from Blockscout's public API on 2026-09-09.
- `resultats_reconstruction_2026-09-09.txt`, raw console output of `reconstruct_exploit.py`, run on 2026-09-09.
- `resultats_sources_2026-09-09.txt`, the DefiLlama hacks-feed record, the press sources found, and Notional's own `mainnet.json` deployment addresses, all queried on 2026-09-09.
- `LICENSE`, MIT license text.
- `.gitignore`, ignores the local Python virtual environment and bytecode cache.

## License

MIT
