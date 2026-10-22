# NEAR Intents Omni MetaWallet Signed Withdrawals, Post-Mortem

Between 18:57 UTC on September 30, 2026 and 06:08 UTC on October 1, one account called `withdraw()` seven times on a BNB Chain wallet contract that holds users' USDT for the Omni bridge (the contract names itself "Omni Token Wallet"), and each call was paid because its signature came from the wallet's configured signer. The seven calls moved 3,865,021 USDT to the account itself: 10 and 11 USDT on the evening of September 30, then 800,000, 1,200,000, 1,500,000, 330,000 and 35,000. The account passed the money on within minutes; 1,500,000 of it went to CoW Protocol's settlement contract through a one-block delegation of the account's code.

According to The Block and crypto.news, NEAR Intents' co-founder put the loss at $3.8 million, all of it USDT on BSC, and blamed a bug in how its Omni deposit and withdrawal infrastructure interacted with the NEAR Intents smart contract; DefiLlama lists $3,800,000 and classes it as a bridge logic flaw. This entry shows what the chain can show: the contract did what its code says, and every signature it accepted was made by its signer. It does not show why the signer signed.

The registry `registre_hypotheses.csv` states each fact as a falsifiable claim with its locator; `reconstruct_exploit.py` re-derives every on-chain number here live, check by check.

## At a glance

| | |
|---|---|
| Victim | The USDT held by the contract `0x233c5370ccfb3cd7409d9a3fb98ab94de94cb4cd` on BNB Chain, that is, the users who deposited through it. One press report names it the "HOT Bridge Treasury" and not NEAR Intents' principal EVM treasury; NEAR Intents said all affected users would be compensated in full |
| Chain | BNB Chain (BSC) |
| Date | 2026-09-30 18:57:07 UTC (first withdrawal, 10 USDT; the first large one is at 23:54:30) to 2026-10-01 06:08:26 UTC (last); DefiLlama dates it 2026-10-01 |
| Mechanism | `withdraw(nonce, token, receiver, amount, signature)` pays any caller whose signature recovers to the contract's `verifyAddress` over the SHA-256 of an RLP message, if the nonce is unused. It does not look at what was deposited. The seven signatures recover to `0xbcfd8381fa8148d01fd7d5cbb0efcc96ce68176c`, as does a withdrawal by another account. Why that signer signed is not established |
| Account | `0x09fd1f5d9f185067a92493e43aa259ea4ab3ad37`, an EOA created on 2026-09-28 (77 transactions, nonce 78), named by one press report as the suspected theft address |
| Loss | At least 3,865,021 dollars: 3,865,021 USDT at face value (800,000 + 1,200,000 + 1,500,000 + 330,000 + 35,000 + 10 + 11) |
| Funds | Forwarded the same night to at least five addresses and not traced further: 1,500,000 USDT to CoW Protocol's settlement contract (a Sourcify match named GPv2Settlement), 1,070,031.76 to `0xc590175e458b83680867afd273527ff58f74c02b`, 930,000 to `0xde85b9599d8324ffa4ba2792ebd4d8298b576b1c`, 330,000 to `0x62eb7ae0afa102bc1252a7cd9677486bb8df98af`, 34,998.97 to `0x168f364cf8da2105b99407cf817660a8450cf3b7` (and 13.03 in small transfers to others). The press says the money went to KuCoin and was bridged to bitcoin; none of that is checked here. Nothing returned was found |
| Press figures | DefiLlama: $3,800,000 (NEAR Intents, "Bridge & Cross-Chain", "Bridge Logic Flaw", BSC, source empty). The Block and crypto.news (2026-10-01): $3.8 million, USDT on BSC, services paused and restored after a fix within an hour, compensation promised. A search-result snippet: a BNB Chain address that collected 3.87 million USDT, about 1.5 million of it sent to CoW Protocol's settlement |

## What the contract does

The contract is verified on Sourcify (a full match: contract `MetaWallet`, solc 0.8.27). Its source header says it was audited by Hacken on 2024-09-24; the audit link in the header is a placeholder (`example.com`) and the audit was not read. Its pieces that matter here:

- `deposit(...)` records `deposits[nonce] = hash` for a deposit, with a nonce of the form seconds times 10^12 plus a counter, and emits `NewTransfer`.
- `withdraw(nonce, contract_id, receiver_id, amount, signature)` (selector `0xd9e7c316`) requires the nonce unused and `ECDSA.recover(sha256(RLP(nonce, chainId, token, receiver, amount)), signature) == verifyAddress`, then sends the token. It does not read `deposits`. Authorizing a withdrawal is entirely the signer's job.
- The owner (`0x1affb938645fdf3d86f3f04f1d1d49d4e000ea16`) can change `verifyAddress`, withdraw tokens and change the owner.

## The seven withdrawals

| Time (UTC) | Block | Amount (USDT) | Signature issued (the nonce's seconds) |
|---|---|---|---|
| 2026-09-30 18:57:07 | 124960379 | 10 | 3.2 hours before |
| 2026-09-30 20:05:24 | 124969481 | 11 | 49 minutes before |
| 2026-09-30 23:54:30 | 125000023 | 800,000 | 238 seconds before |
| 2026-10-01 00:24:02 | 125003957 | 1,200,000 | 213 seconds before |
| 2026-10-01 00:50:42 | 125007511 | 1,500,000 | 237 seconds before |
| 2026-10-01 01:46:20 | 125014927 | 330,000 | 350 seconds before |
| 2026-10-01 06:08:26 | 125049861 | 35,000 | 256 seconds before |

Each call names the sender as receiver and USDT as token. For each, I rebuilt the message the way the contract does (and the contract's own `getMessageRaw` returns the same bytes), hashed it and recovered the signer with secp256k1 in plain Python: all seven are `verifyAddress`. So is a withdrawal of 83,150.68 USDT sent by another account at about 02:20 UTC, and the same signature with one wei added to the amount recovers a different address; the check discriminates, and the contract's acceptance was right under its own rule.

The counters in the nonces are the sequence of one signer: 1814475, 1815187, 1815791, 1815831, 1815863 and 1815949 for the first six calls, 1816013 for the other account's call, 1816530 for the last. The seven withdrawals and the ordinary one come from one pipeline.

## Where the USDT went

The account's own 77 transactions received 3,865,043.757177 USDT (the seven withdrawals and 22.757177 USDT of other transfers) and sent 2,365,043.757703 USDT on: 2,365,030.73 to the four addresses above and 13.03 in small transfers to others. The other 1,500,000 left in four transfers of 300,000, 300,000, 300,000 and 600,000 to CoW Protocol's settlement contract, between 00:51 and 00:52 UTC. Those four transactions were sent by other accounts: the account's own transaction of nonce 44 (block 125007596, type 4) set an EIP-7702 delegation on it, and its code from that block is `0xef0100...`; the transfers ran through that code. Its other transactions send BNB, mostly 100 to 350 at a time, to many other addresses and approve and swap tokens through a router; they were not examined.

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, BNB Chain RPC with archive state (`bsc.rpc.sentio.xyz`, `bsc-mainnet.public.blastapi.io`), Sourcify's API and DefiLlama. DefiLlama gave a date and an amount; the press gave the contract's and the account's addresses; the account's transactions were found by bisecting its nonce against archive state. The script includes keccak256 and secp256k1 written for this purpose, with a self-test against the selector of `withdraw`.

1. **The contract**: verified source, owner, signer, chain id.
2. **The account's 77 transactions** and their blocks.
3. **The seven withdrawals** and their sum.
4. **The signatures**: message, hash and recovered signer, plus a control and an altered copy.
5. **The nonces' counters** and their timing.
6. **Where the USDT went**, and the delegated transfers to CoW.
7. **DefiLlama's record.**

Each is a numbered check (H0 to H8) printed as PASS or FAIL; `--account <address>` runs the script with another account and the checks that read it fail, see `preuves/temoins_negatifs_2026-10-22.txt`.

## Caveats

- **Why the signer signed is not established.** The team's explanation, a bug in how the Omni infrastructure interacted with the contract, fits a signer that signed withdrawals nobody was owed, but the chain shows only valid signatures. Whether the signer was fed false deposits on another chain, its key was used by someone else, or something else happened is not shown; the other chains and the signer's own system were not examined.
- **The loss rests on the account's seven calls.** It is a floor: other accounts may have received signed withdrawals, and tokens other than USDT may have been taken. It matches the press figure of about $3.87 million. DefiLlama's $3,800,000 is lower by 65,021.
- **The audit claim in the source header is not checked.** The header says Hacken audited the contract on 2024-09-24, with a placeholder link; no audit report was read.
- **Which product is the victim is unsettled.** DefiLlama and NEAR Intents' statement say NEAR Intents; one press report says the address is the HOT Bridge Treasury, a different wallet from NEAR Intents' principal EVM treasury. This entry reports the contract and the account, not who owns the funds.
- **The account is not an identified actor.** The press names it as the suspected theft address; it is tied here only by the transactions. Four of the five addresses it paid were not examined.
- **Funds to KuCoin and bitcoin are the press's claim**, not checked here. CoW Protocol's contract receiving 1,500,000 USDT proves a swap venue, not a final holder.
- **Compensation is not a recovery.** NEAR Intents said it would compensate affected users in full; no return of funds to the contract was looked for.

## License

MIT, see the repository root.
