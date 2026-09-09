# Notional Finance V1 Escrow Exploit Postmortem

Independent on-chain reconstruction of the integer-overflow exploit against Notional Finance's legacy V1 Escrow contract (Ethereum mainnet, 2026-09-03/04). Six press sources (SlowMist, CryptoRank, BeInCrypto, Blockfence, shattered.io, Cryptotimes) described the mechanism in real detail, but none of them published a contract address, a transaction hash, or the attacker's wallet. Every fact below was independently re-derived from Notional's own committed deployment records and two block numbers already public in the press coverage.

## At a glance

| | |
|---|---|
| Incident | Integer-overflow exploit against Notional Finance's legacy V1 Escrow contract, Ethereum mainnet |
| Window | 2026-09-03 23:58:47 UTC to 2026-09-04 00:01:35 UTC (2 minutes 48 seconds) |
| Press figure | ~$1.73M (69,257 DAI + 1,658,524 USDC), swapped to ETH and reportedly routed through Tornado Cash |
| Verified independently | Exact same amounts to 4 decimal places, exact same block numbers, exact attacker and exploit-contract addresses, none published anywhere else found |
| A real naming discrepancy | DefiLlama's own hacks feed labels this incident "Notional V2"; every press source, and Notional's own GitHub organization structure, identifies the exploited contracts as V1 |
| What's still open | The reported Tornado Cash routing was not independently confirmed; the destination address found is an unlabeled 23-byte minimal-proxy contract, not a recognizable Tornado Cash pool |

## The method

```bash
pip install web3
python3 reconstruct_exploit.py
```

Notional Finance runs three parallel, independently-repo'd contract generations (`notional-finance/contracts` for V1, `contracts-v2`, `contracts-v3`). The V1 repo commits its own mainnet deployment addresses directly in `mainnet.json`, including the `Escrow` contract this exploit targeted; this project reads that file straight from GitHub rather than guessing an address from a block explorer search. The press's own reporting already narrowed the incident to two exact block numbers (one for the "preparatory" transaction, one for the extraction, three minutes apart); both were checked directly against `eth_getBlockByNumber` before anything else, and both timestamps match the press's own cited times to the second.

## What it found

### Both press-cited blocks check out to the second

Block 25,900,220 timestamps to 2026-09-03 23:58:47 UTC; block 25,900,234 timestamps to 2026-09-04 00:01:35 UTC, 2 minutes 48 seconds later. The press's own "three minutes later" framing is accurate to within rounding.

### One wallet, its first-ever transaction, deploys the exploit contract

The attacker EOA, `0xDaCC235a494750193695A111D715c2ca12b5Ce38`, had a transaction count of exactly 0 going into block 25,900,220: the block containing the "preparatory" transaction the press describes is this wallet's very first transaction ever. That single transaction is a contract creation whose constructor itself calls Notional V1's `ERC1155Trade` contract (`0xBbA899578bd3fA3DAa863A340f5600797993eF08`, the address committed in Notional's own `mainnet.json`), deploying the exploit contract at `0xEc434A2f9B7b93AAD1beD77d6Bc512A75aE90d78` and setting up the two `mintfCashPair()` positions the press describes in a single, gas-efficient step, not two separate transactions.

### The extraction transaction, decoded directly, matches the press to four decimal places

Three minutes later, the same attacker wallet's second-ever transaction calls the exploit contract again. That call triggers Notional V1's `Escrow` contract (`0x9abd0b8868546105F6F48298eaDC1D9c82f7f683`) to release funds through two intermediate addresses before landing directly in the attacker's wallet:

- **69,257.3727 DAI**
- **1,658,524.8641 USDC**

Both figures match the press's rounded ~69,257 DAI and ~1,658,524 USDC exactly, now to four decimal places, read directly from the `Transfer` events in the transaction's own receipt rather than taken from any article.

### DefiLlama's own hacks feed mislabels this "V2"

DefiLlama's `api.llama.fi/hacks` record for this incident (`defillamaId: "234"`, `parentProtocolId: "parent#notional"`) names it `"Notional V2"`. Every press source found (SlowMist, CryptoRank, BeInCrypto, Blockfence, shattered.io) identifies the exploited contracts as V1, specifically the legacy Escrow left live after Notional wound down that generation following an unrelated November 2025 Balancer-driven cascade. This project's own on-chain trace settles it independently: the exploited `Escrow` address is committed in `notional-finance/contracts`, the repository Notional itself names as V1, distinct from its separate `contracts-v2` and `contracts-v3` repositories. The most widely syndicated tracker for on-chain hacks has the version number wrong for this one.

### What this project could not confirm: the Tornado Cash laundering claim

The press reports the stolen funds were swapped into ~689 ETH and routed through Tornado Cash. The attacker wallet sent only 5 transactions in total, the last of which forwards roughly 1.11 ETH to an unlabeled contract, 23 bytes of bytecode (small enough to be a minimal proxy, structurally similar to a pattern already seen in this research program's other work on unrelated liquidation-bot infrastructure). That destination does not resolve to a named or recognizable Tornado Cash pool by any means this project checked, and the ~1.11 ETH transfer found does not by itself account for the full ~689 ETH the press claims was laundered. This project reports the press's Tornado Cash claim as unconfirmed rather than independently verified, and did not trace the funds' full path from the attacker's DAI/USDC balances through to their final destination.

## Caveats

- This is independent research, not an audit, and not affiliated with Notional Finance, SlowMist, or any outlet cited above.
- The exact Solidity mechanics of the `uint128` downcast are reported here as the press (specifically SlowMist and shattered.io) describe them; this project verified the transaction-level effect (the exact amounts moved, the exact addresses, the exact timing) but did not independently re-derive the vulnerable line of code from Notional V1's source.
- The full path of the stolen DAI and USDC after they reached the attacker's wallet, including the claimed swap to ~689 ETH and any Tornado Cash deposit, was not independently traced; see above.
- The V1-vs-V2 mislabeling is established here from the exploited contract's own address and Notional's own repository structure (the address is committed in the repo Notional itself calls V1), not from any deeper audit of DefiLlama's internal ID scheme.
- One working public RPC (`gateway.tenderly.co/public/mainnet`) was used throughout, plus Blockscout's public API for the attacker wallet's short transaction history; no paid RPC or API key was used anywhere in this project.

## License

MIT
