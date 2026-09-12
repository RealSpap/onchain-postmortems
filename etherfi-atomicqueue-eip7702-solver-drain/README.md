# ether.fi Liquid AtomicQueue Exploit Postmortem

Independent on-chain reconstruction of the access-control exploit against a legacy Veda-built `AtomicQueue` used by ether.fi's Liquid vaults (Ethereum mainnet, 2026-09-11). Press coverage (CryptoTimes, PANews, brinztech) got the headline right, about 15.45 ETH from 11 wallets, and one outlet published the transaction hash and block. What none of them established is why exactly those 11 wallets and no others, that the funds were already back in every victim's wallet on-chain hours before the coverage ran, or how small the surface that remained actually was. Every figure below was re-derived live from a public RPC and the queue's own verified source; nothing is taken from press on trust.

## At a glance

| | |
|---|---|
| Incident | Missing `msg.sender` check in a legacy Veda `AtomicQueue.solve()` let an attacker redirect victims' standing token approvals to themselves, ether.fi Liquid, Ethereum mainnet |
| When | 2026-09-11 07:20:11 UTC, one transaction, `0x7cbe0b43…95599b`, block 25952624 |
| Press / DefiLlama figure | ~$38,000 (press) / $43,260 (DefiLlama), 15.45 ETH, 11 wallets |
| Verified independently | 14.445541086626480620 liquidETH + 7.047848 USDC drained from 11 wallets, realized as 15.453645063 ETH (~$38,004 at the ETH price DefiLlama's own oracle reports for that minute); DefiLlama's $43,260 is ~14% high |
| The finding press missed | Every drained wallet has code; nine of the eleven are EIP-7702 delegated accounts. The `solve()` path calls `finishSolve()` on the named solver, which reverts on a code-less address, so plain EOAs are unreachable. The attacker skipped a code-less EOA holding 300 liquidETH to drain a 7702 account holding 0.0005 |
| The other finding press missed | All 11 wallets were reimbursed on-chain to within dust ~9 hours after the exploit, from a Gnosis Safe multisig; press reported only the CEO's pledge, and DefiLlama still records `returnedFunds: null` |
| What's still open | Whether the reimbursing Safe is provably ether.fi's treasury (no on-chain label); whether each of the ~243 code-bearing approvers still exposed would actually survive the `finishSolve` call |

## The method

```bash
pip install web3
python3 reconstruct_exploit.py
```

The one public anchor was the exploit transaction hash, published by CryptoTimes. From it, this reconstruction pulls the receipt and decodes every `Transfer` and `AtomicRequestFulfilled` log directly, reads the `AtomicQueue`'s verified source to locate the flaw, checks `eth_getCode` on every party, re-prices the loss against DefiLlama's own historical ETH oracle, and follows the money both backward (to the 11 victims) and forward (to the reimbursing multisig and to Tornado Cash). A single public RPC (`gateway.tenderly.co/public/mainnet`) was used throughout, plus `coins.llama.fi` for the historical ETH price and `eth.blockscout.com`'s public API for contract labels and the attacker's outbound transaction list.

## What it found

### The mechanism: `solve()` never checks who the solver is

`AtomicQueue.solve(offer, want, users[], runData, solver)` (verified source, Solidity 0.8.21) takes a `solver` address straight from the caller and never requires it to equal `msg.sender`. Its second loop runs `want.safeTransferFrom(solver, users[i], assetsToUser)`, pulling the *want* token out of whatever address was named as `solver`, using that address's standing approval to the queue. The attacker deployed a helper contract, had it place self-requests that offer a worthless placeholder token and want liquidETH (or USDC), then called `solve()` naming each victim as the `solver`. Each victim's stale approval to the queue was spent sending their own tokens to the attacker. The whole operation ran inside a single contract-creation constructor from a wallet whose nonce was 0.

### Only wallets with code could be reached, and that is why the victim set looks the way it does

Between its two loops, `solve()` calls `IAtomicSolver(solver).finishSolve(...)`. That is a high-level Solidity call, and it reverts against a code-less address. So a `solver` must have code. Every one of the 11 drained wallets does: nine are 23-byte EIP-7702 delegation designators (`0xef0100` + an implementation address), two are proxy contracts. This is the detail that explains the incident's shape. At the exploit block, the plain-EOA approver `0x0a807c66…` held 300.79 liquidETH with a 482 liquidETH allowance to the queue and was not touched, while the attacker drained an EIP-7702 account holding 0.000558 liquidETH. The attacker was not being selective for stealth; the path simply cannot reach a code-less EOA. The real victim class here is EIP-7702 smart accounts that had left an approval on the legacy queue.

### The loss is about $38,000, and DefiLlama's $43,260 is high

The attacker's own ETH balance rose by 15.452960135 ETH, plus 0.000684929 ETH of gas, for 15.453645063 ETH realized, matching the precise figure one press outlet cited to the wei. At $2,459.24/ETH, the price DefiLlama's own coins oracle reports for 2026-09-11 07:20 UTC, that is about $38,004, plus the 7.05 USDC leg. DefiLlama's hacks feed records $43,260, roughly 14% higher, which would require an ETH price near $2,799 that its own oracle does not support. Press's "~$38,000" reconciles with the chain; DefiLlama's dollar figure does not.

### Every victim was made whole on-chain, hours before the coverage

Nine hours after the exploit, between 16:28 and 16:36 UTC, a Gnosis Safe multisig (`0xf6c612c7…`, funded by EOA `0x46cba1e9…`) sent each of the 11 wallets back its exact drained token and amount, to within dust of round-number payments. Press coverage carried only the CEO's stated pledge to reimburse and noted that "transaction hashes remained outstanding at publication." The transactions existed; this reconstruction lists all three. DefiLlama's feed still shows `returnedFunds: null`.

### The residual surface is small, not the millions a naive scan suggests

A naive scan finds 1,983 addresses that still held both a live liquidETH approval to the queue and a balance at block 25962428, summing to 961 liquidETH (~$2.5M) of `min(allowance, balance)`. That number is misleading. Only 243 of those addresses have code (231 of them EIP-7702); the other 1,740 are plain EOAs the `solve()` path cannot reach. The realistic still-drainable-via-this-path surface is at most about 19.0 liquidETH (~$50,000), and even that assumes each code-bearing account's `finishSolve` call would not revert. The queue itself is immutable: a non-proxy with no `owner()` or pause function, so the flaw cannot be switched off, only defused by users revoking approvals.

### Cash-out through Tornado Cash

The attacker swapped the drained tokens to ETH inside the exploit transaction, then sent 15.5 ETH to a contract labelled `TornadoRouter` (`0xd90e2f92…`) across 11 deposits, one of 10 ETH, five of 1 ETH, five of 0.1 ETH, all within five minutes. This matches the press account exactly and is verifiable from the attacker EOA's own nonce-1-through-11 transaction list.

## Caveats

- The reimbursing address is a Gnosis Safe multisig with no public on-chain label tying it to ether.fi; the link to ether.fi rests on timing, the exact-match payments, and the CEO's public pledge, not on a labelled treasury address.
- "Only addresses with code can be drained" rests on Solidity's high-level-call semantics plus the strong behavioural evidence that the attacker left a 300-liquidETH code-less approver untouched. This reconstruction did not additionally simulate a `solve()` against a code-less solver, because reproducing it would require creating a fresh on-chain request.
- The ~19 liquidETH residual figure is a per-token snapshot (liquidETH only) at one block and an upper bound; it moves as approvals are created or revoked, and some code-bearing accounts may revert inside `finishSolve`.
- The dollar figures use DefiLlama's historical ETH oracle for one timestamp; a different price source would shift them by a few percent.

## Files

- `reconstruct_exploit.py` — live reconstruction; re-derives every figure above and ends with an adversarial self-check that recomputes the loss two independent ways.
- `registre_hypotheses.csv` — 11 falsifiable hypotheses, each with a precise locator and a falsification test (0 anomalies under the `hypotheses-falsifiables` guard-rail tool).
- `preuves/` — raw evidence: exploit tx and receipt, per-victim drain, code-type proof and the skipped-EOA counter-example, the verified `solve()` source, the reimbursement and Tornado Cash traces, the DefiLlama record and the price used, the residual-surface scan, and the captured self-check run.

## License

Released under the MIT License. See `LICENSE`.
