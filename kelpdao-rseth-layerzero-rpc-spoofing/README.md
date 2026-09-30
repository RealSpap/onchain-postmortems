# Kelp DAO (rsETH / LayerZero DVN) Postmortem

Independent reconstruction of the second-largest incident this repo covers,
after Drift Protocol: on 2026-04-18, a forged LayerZero cross-chain message
minted 116,500 real rsETH on Ethereum against a burn that never happened
on the message's claimed source chain, Unichain. The forgery was possible
because Kelp DAO's rsETH bridge ran a 1-of-1 DVN (Decentralized Verifier
Network) setup, LayerZero Labs as the sole verifier, and because
attackers, per LayerZero's own account, compromised two of that verifier's
RPC nodes and then DDoS'd the uncompromised ones to force a failover onto
the poisoned pair. This reconstruction starts from LayerZero's own
official incident statement and a named security-research firm's
technical writeup, then independently re-derives every on-chain fact
(transaction, amounts, addresses, contract identities, and the source-EID
decode) from raw receipts and live contract calls across multiple
unrelated RPC providers, none of it assumed from either source.

## At a glance

| | |
|---|---|
| Incident | A forged LayerZero cross-chain message, verified by a compromised 1-of-1 DVN, minted 116,500 rsETH on Ethereum with no matching burn on the claimed source chain (Unichain) |
| Window | 2026-04-18, block 24,908,285, timestamp 17:35:35 UTC (confirmed live, byte-identical, on 3 independent RPC providers); falls inside LayerZero's own stated attack window, "10:20a and 11:40a PT" (17:20-18:40 UTC) |
| DefiLlama figure | "Kelp", $293,000,000, chains Ethereum + Arbitrum, classification "Bridge & Cross-Chain", technique "Cross-Chain Message Spoofing" |
| LayerZero's own stated figure | "approximately $290M" (its own official incident statement) |
| Verified independently | Exactly 116,500.000000000000000000 rsETH (raw wei: 116500000000000000000000), decoded from the exploit transaction's own Transfer log, transferred from the verified `RSETH_OFTAdapter` contract straight to the attacker's address. At CoinGecko's own 2026-04-18 daily rsETH price, that is $273,377,225 |
| Root cause, per LayerZero's own account | RPC infrastructure poisoning, not a protocol bug, a stolen key, or a compromised validator set: two independent LayerZero-Labs DVN RPC nodes were compromised, a DDoS against the remaining clean nodes forced failover onto the poisoned pair, and a forged message was accepted because Kelp DAO ran a 1-of-1 (single-verifier) configuration with no independent DVN to catch it |

## The method

```bash
python3 reconstruct_exploit.py
```

No hardcoded press figures beyond what is explicitly labeled as sourced
from LayerZero or DefiLlama for comparison; every other number below is
read live from Ethereum mainnet (`eth.drpc.org`, cross-checked against
`ethereum-rpc.publicnode.com` and, for one call, `eth-mainnet.public.blastapi.io`),
Sourcify's public contract-verification API, DefiLlama's own
`dimension-adapters` GitHub repo, LayerZero-Labs' own official
`lz-address-book` GitHub repo, and CoinGecko's public historical-price API.

1. **The starting anchor is a named security firm's own technical
   writeup, not a press paraphrase.** DarkNavy (darknavy.org), an
   established blockchain-security research outfit, names the exploit
   transaction hash and every contract/attacker address directly. Its raw
   HTML (fetched directly with `curl`) was grepped
   to confirm every address/hash actually appears on the page, before any
   of them were trusted as a starting point.
2. **Every one of those addresses is then independently re-derived from
   the raw transaction receipt**, fetched live via `eth_getTransactionReceipt`
   on two unrelated RPC providers that return byte-identical results, not
   assumed from DarkNavy's own claims.
3. **Every contract identity is checked against its own live bytecode/state**,
   not against a label: the LayerZero EndpointV2 contract is confirmed by
   calling its own `eid()` function live (returns 30101, LayerZero's
   documented Ethereum-mainnet EID); the OFTAdapter contract is confirmed
   via Sourcify's independent, decentralized source-verification API
   (exact bytecode match against Solidity source named `RSETH_OFTAdapter`,
   verified more than a year before the exploit); the rsETH token address
   is cross-checked against DefiLlama's own `dimension-adapters` fee
   adapter for Kelp DAO, not against a press-quoted address.
4. **The forged message's claimed source chain is decoded from the raw
   Endpoint log itself** (a source-EID field of 30320), then checked
   against LayerZero-Labs' own official `lz-address-book` GitHub repo,
   which maps EID 30320 to `unichain-mainnet` in its own generated
   Solidity source.
5. **The dollar figure is computed two independent ways**: directly, from
   CoinGecko's own historical rsETH price on the theft date, and as a
   cross-check, from Kelp DAO's own on-chain `LRTOracle.rsETHPrice()`
   backing rate (read live at the block immediately before the exploit)
   multiplied by CoinGecko's ETH price the same day. Both are reported;
   see "The dollar figure" below for why they differ from DefiLlama's and
   LayerZero's own numbers.

## What it found

### The exploit transaction, confirmed on 3 independent RPC providers

Transaction `0x1ae232da212c45f35c1525f851e4c41d529bf18af862d9ce9fd40bf709db4222`,
block **24,908,285**, timestamp **2026-04-18T17:35:35Z**. `eth.drpc.org`,
`ethereum-rpc.publicnode.com`, and `eth-mainnet.public.blastapi.io` all
return the exact same block hash
(`0x48cbf7328277c6a4c57479b25574f5e052c9f4f22d5ea59b65fb8293ac0a0630`)
and timestamp, and the first two return byte-identical transaction
receipts. `to` is `0x1a44076050125825900e736c501f859c50fe728c`, LayerZero's
Ethereum-mainnet EndpointV2, independently confirmed live: calling its own
`eid()` function returns `30101`, LayerZero's documented Ethereum-mainnet
endpoint ID.

The receipt carries exactly 3 logs:

| Contract | Event |
|---|---|
| `0xa1290d69...cb99e5a7` (rsETH token) | `Transfer` |
| `0x85d456b2...00e98ef3` (`RSETH_OFTAdapter`, Sourcify-verified) | an OFT-receive event |
| `0x1a440760...c50fe728c` (LayerZero EndpointV2) | a packet-delivery event, encoding source EID `30320` |

The `Transfer` log decodes to exactly
**116,500.000000000000000000 rsETH** (raw value
`116500000000000000000000` wei), moving from the `RSETH_OFTAdapter`
contract directly to `0x8b1b6c9a6db1304000412dd21ae6a70a82d60d3b`, a
recipient Etherscan's own public tag independently labels "Kelp DAO
Exploiter 13" (confirmed by fetching the raw Etherscan page directly).
This is Kelp DAO's largest single incident.

### Why this is a genuine forgery, not a legitimate mint

The Endpoint log's own source-EID field reads **30320**. LayerZero-Labs'
own official `lz-address-book` GitHub repo (`src/generated/LZWorkers.sol`)
independently maps EID 30320 to `unichain-mainnet` in its own generated
source, matching DarkNavy's claim that the forged message purported to
originate from Unichain. LayerZero's own official incident statement
confirms, in its own words, that no real burn backed this mint: "the
LayerZero Labs-operated DVN instance confirmed transactions that never in
fact took place," and states plainly that this was not a protocol bug:
"It was not done through an exploit to the protocol, DVN, key management
or other means... Rather, the attacker was able to gain access to the
list of RPCs our DVN uses, compromise two of them... and swap out
binaries running the op-geth nodes... they used this pivot point to
execute an RPC-spoofing attack." A DDoS against the DVN's remaining clean
RPC nodes forced a failover onto the two poisoned ones: "In order to
complete the attack they performed DDoS attacks on the uncompromised
RPCs. The DDoS triggered the failover to the poisoned RPCs."

LayerZero's own statement is explicit that the configuration, not the
protocol, is what let this succeed: rsETH's "OApp configuration at the
time of this incident relied on a 1-of-1 DVN setup, with LayerZero Labs
as the sole verifier... Operating a single-point-of-failure configuration
meant there was no independent verifier to catch and reject a forged
message." Kelp DAO has separately disputed how much warning it had about
that configuration's risk (per press coverage, not independently
adjudicated here); this entry reports only what both LayerZero's own
statement and the raw chain data independently confirm: the 1-of-1
setup was real, and it is what a second, independent DVN would have
caught.

### Where the funds went, and what remains

As of this reconstruction's run (2026-09-10, 5 months later), the
attacker's receiving address (`0x8b1b6c9a...a82d60d3b`) holds **0 rsETH**
and 0.0975260878903386 ETH, confirmed live on two RPC providers, an
essentially empty wallet consistent with press reporting that the
attacker swapped the rsETH for wstETH and used it as collateral to borrow
against on Aave V3, Compound V3, and Euler, spread across several branch
addresses. This reconstruction does not independently re-trace that
downstream laundering trail; see Caveats.

### The dollar figure, and why it differs from DefiLlama's and LayerZero's

The exact token amount moved on-chain, 116,500 rsETH, is not in dispute
between any source checked here. The dollar figure depends entirely on
which price snapshot is used, and three independently-computed figures
give three different answers:

- **This entry's headline figure**: 116,500 rsETH at CoinGecko's own
  2026-04-18 daily historical price for `kelp-dao-restaked-eth`
  ($2,346.5856193419986) is **$273,377,224.65**, reported in the index
  table rounded to $273,377,225.
- **A cross-check via Kelp's own on-chain oracle**: `LRTOracle.rsETHPrice()`,
  read live at block 24,908,284 (immediately before the exploit), returns
  1.069610361882844 ETH per rsETH; 116,500 rsETH at that backing rate is
  124,609.607 ETH-equivalent, which at CoinGecko's 2026-04-18 ETH price
  ($2,421.2905710664027) is **$301,716,066.88**.
- **DefiLlama tracks $293,000,000**; **LayerZero's own statement says
  "approximately $290M"**.

All four figures (this entry's two, DefiLlama's, and LayerZero's) sit
within about 10% of each other, and none of them is treated here as
"the" correct number over another: the gap most likely reflects that
CoinGecko's daily snapshot is not pinned to the exact 17:35:35 UTC theft
moment, that rsETH's own market price and its oracle-stated backing rate
can diverge slightly during a same-day de-peg event, and that LayerZero's
and DefiLlama's own figures are not sourced to a stated methodology this
entry could check against. The one number every source, including this
one, agrees on exactly is the 116,500 rsETH itself.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Kelp DAO, LayerZero Labs, DarkNavy, or any outlet cited
  above.
- This entry does not independently re-trace the attacker's downstream
  laundering (the swap to wstETH, the Aave V3/Compound V3/Euler borrows,
  or the movement across the several additional "Kelp DAO Exploiter"
  addresses Etherscan's own tags separately enumerate). It verifies only
  the single forged-mint transaction and the current, now-empty state of
  the address that transaction paid out to.
- LayerZero and Kelp DAO have publicly disputed, in the weeks after this
  incident (per press coverage, not independently checked here), whether
  Kelp DAO was adequately warned about the risk of its 1-of-1 DVN
  configuration before the exploit. This entry takes no position on that
  dispute; it reports only what LayerZero's own statement says about the
  configuration and the RPC-compromise mechanism, both independently
  corroborated by the raw on-chain data.
- Kelp DAO's own GitHub org (`Kelp-DAO`) does not appear to host the
  `RSETH_OFTAdapter` contract's source directly in its main `LRT-rsETH`
  repo (that repo's `contracts/bridges` and `contracts/cross-chain`
  folders cover other bridges, not the LayerZero OFT integration); this
  entry relies on Sourcify's independent verification of the deployed
  bytecode instead of a Kelp-DAO-controlled source repo for that specific
  contract.
- DefiLlama's chain tag for this incident lists both "Ethereum" and
  "Arbitrum". This reconstruction found and independently confirmed only
  a single forged-mint transaction, on Ethereum; no corresponding
  Arbitrum-side transaction was identified or checked here, and this
  entry's chain field reports only what was independently verified.
- As with every entry in this repo, this reflects a snapshot as of
  2026-09-10. The attacker's other addresses and the frozen/recovered
  status of any downstream funds were not re-checked after this run.

## License

MIT

<!-- external source: https://layerzero.network/blog/kelpdao-incident-statement -->
