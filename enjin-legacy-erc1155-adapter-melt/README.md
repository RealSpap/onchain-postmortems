# Enjin Legacy ERC-1155 Melt Drain, Post-Mortem

On August 25, 2026, at 18:41:59 UTC, one transaction on Ethereum moved 54 batches of ERC-1155 items from 47 wallets to a contract the attacker had deployed in the previous transaction of the same block, burned them there, and so released 5,238,353 ENJ from Enjin's platform contract: 5,231,353 ENJ reached the attacker's address and 7,000 went to a third address. The same address then ran the same contract 594 more times over the following three hours, taking another 1,287,165.5545533333 ENJ. All 6,518,518.554553 ENJ it received, worth $175,442 at DefiLlama's price, went on to one contract.

DefiLlama lists $162,000 for "Enjin" and classes it as an ownership takeover under access control; the press figure I saw, about $142K for 5.24M ENJ, matches the first transaction alone. This entry reconstructs the sequence of calls and events of that first transaction and counts the later ones; it does not explain why the legacy ERC-1155 contract and the platform contract allowed any of it, because neither was read.

The registry `registre_hypotheses.csv` states each fact as a falsifiable claim with its locator; `reconstruct_exploit.py` re-derives every on-chain number here live, check by check.

## At a glance

| | |
|---|---|
| Victim | The ENJ held by Enjin's platform contract `0x4e643a25a64952895f553f20252861258727174e` against ERC-1155 items of the legacy contract `0xfaafdc07907ff5120a76b34b731b278c38d6043c`, that is, the holders of those items: 47 wallets in the first transaction; the later ones were not itemized |
| Chain | Ethereum |
| Date | 2026-08-25, 18:41:59 UTC, block 25834071, tx `0xd4a382da03c99ce3084661b913b50b525a4b283f66f510bcf1040152830b2a7e` (DefiLlama dates it 2026-08-25) |
| Mechanism | A contract with no approval from the item holders (`isApprovedForAll` is false for all 47) is operator of 108 `TransferSingle` events: 54 moving items from the holders to itself, 54 burning them. It first has the legacy contract create 6 adapter contracts and register each on the platform contract, then calls the legacy contract's `0xf6089e12` 54 times, and the platform sends ENJ to the contract in 54 transfers. Which check fails, and why anyone could create and register adapters, is not established here |
| Attacker | EOA `0x5ec1ba7892d11059c39557b762a97dd695778ca5`, whose first transaction, in the same block, deployed the contract `0x7083ddece38216c7741fa76c75326bea744ed321` (9,786 bytes, unverified) |
| Loss | At least 140,799 dollars: the 5,231,353 ENJ of the first transaction, whose 47 holders are all checked, at DefiLlama's price of 0.02691447 at the exploit's block time. With the 594 later transactions of the same address to the same contract (holders checked on a sample of 5), the total is 6,518,518.554553 ENJ, 175,442 dollars; that larger figure is not counted |
| Funds | The EOA sent all 6,518,518.554553 ENJ in 32 transfers, from block 25834083 (18:41:59 UTC plus 12 blocks) to block 25837514 (2026-08-26 06:12:23 UTC), to one contract, `0x8f10b468b06c6fd214b65f87778827f7d113f996` (13,529 bytes, unverified, not read). What it did with the ENJ is not established. No return was found |
| Press figures | DefiLlama: $162,000 (Enjin, "Access Control", "Ownership Takeover", Ethereum, source empty). A search-result snippet citing Defimon: about $142K, 5.24M ENJ; one attributed to SlowMist (not verified) describes storage slots, managerial control and a malicious adapter. The pages were not opened; Enjin's own report (dated 2026-08-27 in the results) returned HTTP 403 |

## Timeline (2026-08-25, UTC)

| Time | Block | Event |
|---|---|---|
| 18:41:59 | 25834071, index 0 | The EOA's first transaction (nonce 0) deploys `0x7083...d321` |
| 18:41:59 | 25834071, index 1 | Exploit transaction (nonce 1): 54 item moves and 54 burns, 62 ENJ transfers |
| 18:41:59 + 12 blocks | 25834083 | The EOA sends its first 100,000 ENJ to `0x8f10...f996` |
| 19:44:23 | 25834382 | First of 594 transactions from the EOA to its contract (selector `0xf7d9430e`), 62 minutes after the exploit; the last is in block 25834993 |
| 19:44:23 + 1 block | 25834383 | First sweep (selector `0x35faa416`): 3,070 ENJ from the contract to the EOA |
| 21:46:47 | 25834994 | Third and last sweep: 537,616.5554533333 ENJ (the second, 746,478.9991, is in block 25834623) |
| 2026-08-26 06:12:23 | 25837514 | The EOA's last ENJ transfer to `0x8f10...f996` |

## The first transaction, step by step

Read from the call trace, the receipt's events and the ENJ balance of the platform contract, not from source code:

1. The attacker's contract creates 3 contracts.
2. It calls selector `0x33d332ab` on the legacy ERC-1155 contract six times. Each call creates a contract, which I call an adapter, and the legacy contract then calls selector `0x7b129b06` on the platform contract, with an address that the attacker's contract goes on to call (selector `0x6453dcf6`).
3. For each of the 54 melts it calls selector `0xf6089e12` on the legacy contract. The legacy contract logs a `TransferSingle` with the attacker's contract as operator moving the item from its holder to the attacker's contract, then another burning it from there. In all, the legacy contract calls selector `0x7843e5dd` on the platform contract 61 times and each is followed by an ENJ transfer by the platform, 54 to the attacker's contract and 7 to a third address (below).
4. In all, 2,149 item units over 12 item ids are moved and burned, from 47 wallets; the platform contract sends 5,231,353 ENJ to the attacker's contract in 54 transfers and 7,000 ENJ to `0x862e4dc54eceaada8a2574e0d5d5d730f692466f` in 7 transfers of 1,000, and its ENJ balance goes from 9,852,235.680835 to 4,613,882.680835.
5. The attacker's contract passes 5,231,353 ENJ to the EOA in one transfer.

None of the 47 wallets had approved the attacker's contract through `isApprovedForAll`, at the end of the block or of the next one. While building this entry that function never returned true for any of five addresses I tried (the platform contract, the legacy contract and three others from the trace), so this shows the answer, not that no other permission mechanism existed. The 7,000 ENJ went to an address with no code that is not one of the 47 wallets; why the platform paid it is not established, and it is not counted in the loss.

## The later transactions

From block 25834382 (19:44:23 UTC) to block 25834993, 594 more transactions went from the same EOA to the same contract with selector `0xf7d9430e`, each taking ENJ from the platform contract to the contract: 1,287,165.5545533333 ENJ in 594 transfers, typically 500 to 5,000 ENJ each. A second reading of the EOA's transaction list (Blockscout, 2026-10-22, not run by the script) finds 604 transactions with that selector in that range: these 594, 4 that reverted and 6 that succeeded without moving ENJ from the platform to the contract; those ten were not examined here. Three more, with selector `0x35faa416`, in blocks 25834383, 25834623 and 25834994, sent the same total from the contract to the EOA (3,070, then 746,478.9991, then 537,616.5554533333); the contract held no ENJ at block 25835500.

I read the trace of the first of them and the item events of five (the 1st, 2nd, 101st, 301st and last): 126 distinct wallets had items moved to the attacker's contract, 3 of them among the first 47, the EOA not among them, and none had approved the contract. The first one moves 600 `TransferSingle` events (299 units from one wallet, 1 from another, burned from the contract) in 300 loops of the same call sequence. The other 589 were not itemized. The EOA's nonce was 707 at the time of reading: 108 of its other transactions (nonces 2 to 32, a dozen between 33 and 641, and 642 to 706) were not examined.

## Where the ENJ went

The EOA forwarded everything it was given: 32 transfers of 100,000 to 631,353 ENJ each to one contract, `0x8f10...f996`, in blocks 25834083 to 25837514, summing to 6,518,518.554553 ENJ, exactly what it had received from the contract. At block 25838000 it held no ENJ. The recipient is a contract with 13,529 bytes of code, unverified on Blockscout, that I did not read.

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, Ethereum RPC (`eth.drpc.org`, then Tenderly's public gateway), the node's `debug_traceTransaction` for the call trace (or `--trace-file` with a saved callTracer result), DefiLlama's price API. DefiLlama gave a date and an amount only; the transaction was found from the large ENJ transfers out of the platform contract on that day; the rest follows from its receipt and trace.

1. **The exploit transaction** and **the deployment** that precedes it in the same block.
2. **The ENJ flows** of the receipt and the platform contract's balance over the block.
3. **The item events**, and **the approvals** of the 47 wallets.
4. **The call trace**: contracts created, selectors and counts.
5. **The later transactions**: senders, selectors, ENJ in and out, and a sample of their item events.
6. **Where the ENJ went**, and the recipient of the 7,000.
7. **Value**: DefiLlama's price, and its record.

Each is a numbered check (H1 to H12) printed as PASS or FAIL; `--tx <hash>` runs the script with another transaction as the exploit and the checks that read it fail, see `preuves/temoins_negatifs_2026-10-22.txt`.

## Caveats

- **Why this was possible is not established.** The facts are the order of calls, the events and the absence of approvals through `isApprovedForAll`. Neither Enjin's contracts nor the attacker's contract is verified or was read. A search-result snippet quoted SlowMist as describing storage slots, managerial control and a malicious adapter; I did not check it, and Enjin's own report was not readable (HTTP 403). The selectors in this entry are not named because no source was read for them.
- **The loss is what left the platform contract for the attacker, not an audited count of what holders lost.** It rests on ENJ transfers and on the item events of one transaction and a sample of the others. The platform contract's ENJ balance is also affected by other users; between the two blocks around the exploit its fall equals the 5,238,353 ENJ of the transfers, but over the whole episode I did not reconcile it (read outside the script: the balance fell by 1,341,274 ENJ between the end of the exploit block and block 25835000, against 1,287,165 ENJ taken by the later transactions; the difference of about 54,109 ENJ was not examined).
- **The figure counts the first transaction only.** $140,799 is close to the press's $142K and below DefiLlama's $162,000. The 594 later transactions would bring it to $175,442; they are on-chain facts, but their holders were checked on a sample of 5 transactions only, so they are left out of the floor. Price: one point, DefiLlama's ENJ price at the exploit's block time; it is not applied to the 7,000 ENJ.
- **One address is not one actor.** The EOA, its contract and the sink contract are tied by transactions and transfers; who controls the sink contract, and whether anyone else took funds, are not established.
- **The sink contract's behaviour is unknown.** Its code was not read; the ENJ may have been swapped, bridged or held.
- **The 7,000 ENJ** sent to `0x862e...466f` are not counted as the attacker's; it may be a fee or another party's share.

## License

MIT, see the repository root.
