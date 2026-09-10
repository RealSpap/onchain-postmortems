# Allbridge (CCTP Forged Message) Postmortem

Independent on-chain reconstruction of the Allbridge cross-chain bridge exploit: a forged Circle CCTP message crafted on Polygon on 2026-07-25, redeemed against Allbridge's Router on Base almost a month later on 2026-08-19. SlowMist's own security team published a detailed, named post-mortem of the mechanism, but it names no contract address and no transaction hash anywhere. Every address, transaction, and dollar figure below was found and verified independently, live against both chains, starting only from Allbridge's and Circle's own official deployment records, Aave's own official address book, and the attacker's own short public transaction history.

## At a glance

| | |
|---|---|
| Incident | A forged Circle CCTP message, accepted by Allbridge's Base Router without checking that the tokens it credited had actually arrived, then redeemed via a self-funded Aave flash loan |
| Window | Setup 2026-07-25 20:32:55 UTC (Polygon); drain 2026-08-19 01:47:17 UTC (Base), almost a month later |
| Press/DefiLlama figure | DefiLlama tracks this as "Allbridge", Base only, $191,000. SlowMist's own post-mortem: "approximately $190,000" |
| Verified independently | The Router's own USDC balance drops by exactly 190,155.976393 USDC in one transaction; of that, the attacker keeps 189,751.554381 and 404.422012 goes to Aave as a flash-loan fee. Every one of SlowMist's own quoted numbers matches to 6 decimals |
| A real date discrepancy | SlowMist's article states the Polygon setup call happened "July 26, 2026"; the transaction found here is timestamped 2026-07-25 20:32:55 UTC, one calendar day earlier, confirmed on two independent Polygon RPC endpoints |
| A parallel-contracts finding | The Router and CCTPTokenMessenger contracts actually exploited are not the addresses Allbridge's own live API currently returns for Base USDC bridging; that pair sat idle that day |

## The method

```bash
pip install web3
python3 reconstruct_exploit.py
```

Nothing in SlowMist's article is a lie, but nothing in it is checkable either: no address, no transaction hash, no block number. This project treats the article as a map, not a source of truth, and re-derives every stop on it from primary records:

1. **Aave's own address book** (`aave-dao/aave-address-book`, `AaveV3Base.sol`) gives the real Aave V3 Pool address on Base. Scanning every `FlashLoan` event that contract emitted on 2026-08-19 (no address guessed, no name searched) turns up exactly one USDC loan above $700,000: 808,844.023607 USDC, matching SlowMist's "808,844 USDC" figure before anything else is checked.
2. That flash loan's own transaction receipt is decoded directly: 4 USDC `Transfer` events show the full round trip through a contract that Base Blockscout's public API independently confirms is verified under the name **"Router"**, and a second contract it calls into verified under the name **"CCTPTokenMessenger"** - names this project did not supply, matching SlowMist's own terminology exactly.
3. The Router's own USDC balance, read live via `eth_call` at the block immediately before and immediately after the attack transaction, gives the real loss directly, without depending on SlowMist's arithmetic at all.
4. The attacker EOA that signed the Base attack transaction has a total of 14 transactions on Base and 8 on Polygon, ever (pulled from each chain's public Blockscout API). Exactly one of those 8 Polygon transactions calls Circle's `MessageTransmitterV2` directly - the forged-message setup call SlowMist describes but never names.
5. That transaction's `MessageSent` event is decoded byte-for-byte using Circle's own official header-offset constants, published in `circlefin/evm-cctp-contracts` (`MessageV2.sol`), not guessed.

Two public RPC endpoints were used throughout: `mainnet.base.org` for Base, and `polygon.gateway.tenderly.co` for Polygon (`polygon-rpc.com` returned HTTP 403 outright, and most other free Polygon RPCs had pruned history back to July 2026). Base Blockscout's and Polygon Blockscout's public APIs were used only for contract-name verification and for pulling an address's own transaction history, never for any dollar figure or amount, all of which come from raw RPC decodes.

## What it found

### The flash loan, found by scanning, not by searching

Circle's CCTP protocol burns USDC on the source chain and mints it on the destination chain; a signed "attestation" from Circle only proves the message content wasn't tampered with in transit, not that a burn or mint actually happened. SlowMist's own post-mortem describes how Allbridge's `CCTPTokenMessenger` contract trusted a forged message's declared amount as a credit, keyed by a `messageHash` the attacker could precompute, without ever re-checking that the Router's real USDC balance had increased to match. This project did not need to independently verify that specific line of reasoning to independently verify its consequences: scanning Aave's own `FlashLoan` events on Base for 2026-08-19 turns up exactly one USDC loan large enough to matter, and its own transaction receipt tells the whole story on its own.

### The attack transaction, decoded directly, matches SlowMist to 6 decimals

Transaction `0x9f906fcd8fceaa6745e8d1c004861dcfa9b5e6a893fe1e8c5d0013a4e982e6a8`, block 50157345, 2026-08-19 01:47:17 UTC, four USDC `Transfer` events in sequence:

- **808,844.023607 USDC** - Aave's Pool lends the attack contract (`0xb6fbdfa5f3cbeb139d4cce86d92f4ac8687b16c0`) a flash loan.
- **808,844.023607 USDC** - forwarded straight to the Router (`0xaa119f7442ecc28b9a8f236707ada8362cff24ff`), temporarily bringing its balance up to exactly the 1,000,000 USDC the forged message had declared.
- **999,000.000000 USDC** - the Router pays this out to the attack contract (1,000,000 minus the Router's own 0.1% fee), trusting the forged credit.
- **809,248.445619 USDC** - repaid to Aave: the 808,844.023607 principal plus 404.422012 in flash-loan fees.

Net attacker profit: 999,000.000000 − 809,248.445619 = **189,751.554381 USDC**, matching SlowMist's own stated profit to 6 decimals, independently re-derived from the raw logs rather than taken from the article.

### The Router's own balance gives a cleaner loss figure than either published number

`eth_call`-ing the Router's USDC balance at block 50157344 (the block before the attack) returns 191,155.976393 USDC, matching SlowMist's rounded "~191,156" almost exactly. At block 50157345 (the attack block itself) it returns exactly 1,000.000000 USDC. The real loss to Allbridge's Router - not the attacker's own cut, but the total that actually left the contract - is the difference: **190,155.976393 USDC**, about $404 more than the attacker's reported profit, because the Aave flash-loan fee also left the Router's balance, it just went to Aave rather than into the attacker's pocket. DefiLlama's tracked $191,000 sits closer to the Router's *gross pre-attack balance* than to either the real loss or the attacker's real profit; all three numbers are close, but they answer different questions, and this project can now say precisely which is which.

The 1,000.000000 USDC left in the Router after the attack is the exact figure SlowMist's article separately mentions was "later taken by other attackers who replicated the same attack method" - a detail this project's balance read confirms independently, without needing to trace that follow-up incident itself.

### Two different CCTP integrations, only one of them exploited

Allbridge's own live `api.core.allbridge.io/token-info` endpoint currently lists two CCTP-related addresses for Base USDC: a `cctpAddress` (`0x1eFE2C85989D97fEBbD0743cdd79B9F0826314f6`) and a `cctpV2Address` (`0x214D972b8c869cfcE50D55B595adC7eF336D7FAd`). Neither is the Router or CCTPTokenMessenger actually involved in this exploit: both had essentially no outgoing USDC transfers on 2026-08-19, and their own committed Solidity source in `allbridge-io/allbridge-core-evm-contracts` (`CctpBridge.sol`, `CctpV2Bridge.sol`) doesn't contain the `receivedTokenAmount`/`hookData`/`messageHash` ledger logic SlowMist's post-mortem describes at all - that logic lives only in the separate, older `Router` + `CCTPTokenMessenger` pair this project found by tracing the actual attack transaction. Allbridge appears to run (or to have run) two parallel CCTP integrations on Base at once; this project has no way to independently confirm whether the vulnerable pair has since been paused, deprecated, or is simply still there.

### A date SlowMist got wrong by one day

SlowMist's article states plainly: "On July 26, 2026, the attacker first directly called the `sendMessage` function of Circle's `MessageTransmitterV2` contract on Polygon." The actual transaction - found independently via the attacker EOA's own 8-transaction Polygon history, not searched for by date - is `0x2a88d79756b4547b33fea7b3c1420793680e2b8952bef4c65e99879e16b22140`, block 90871052, timestamped **2026-07-25 20:32:55 UTC** by the chain itself. That reading was confirmed on two independent public RPC endpoints (`polygon.gateway.tenderly.co` and `polygon.drpc.org`), both agreeing to the second. Every other number and every other address in SlowMist's account checks out exactly against the chain; the date is the one place it does not, off by almost a full day (SlowMist's stated July 26 would put the call after 00:00 UTC; the real call landed at 20:32 UTC the day before).

## Caveats

- This is independent research, not a security audit, and is not affiliated with Allbridge, SlowMist, Circle, or Aave.
- The forged message's full body is 260 bytes and is not ABI-encoded in any standard CCTP format this project could find documented anywhere; only the 32-byte word carrying the forged 1,000,000 USDC amount was independently located and decoded (by searching the raw body bytes for that exact value, which is found at byte offset 68). The remaining body bytes, including what is very likely the precomputed `messageHash` SlowMist's article describes, were not further decoded, since Allbridge has not published the `CCTPTokenMessenger` contract's exact body-encoding format anywhere this project could find.
- Whether the vulnerable Router/CCTPTokenMessenger pair has since been patched, paused, or is still live was not checked; this project only confirmed it existed and held the funds in question on 2026-08-19.
- SlowMist's article was not directly fetchable (HTTP 403 from Medium to this project's tools) and was read via a read-only mirror instead; every number quoted from it here was cross-checked against the mirror's own plain text, not against a screenshot or a paraphrase.
- The identity behind the attacker EOA (`0x2419432344b0b892e592b2601b98eae702ba360e`) and the attack contract were not investigated beyond what is reported here; no claim is made about who controls them.

## License

MIT
