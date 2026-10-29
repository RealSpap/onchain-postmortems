# Truebit Purchase Price Overflow, Post-Mortem

On January 8, 2026, at 16:02:35 UTC, one transaction on Ethereum took 8,535.453576519732789359 ETH out of the Truebit contract that sells and buys back TRU on a bonding curve, for 0.01 ETH of its own. BlockSec's write-up says the contract's price function adds two large terms with no overflow check. The attacker's contract bought TRU from the contract at prices from 0 to 5.11 ETH, sold the same TRU back to it, taking 5,105.07 ETH in the first of five rounds, and did the same four more times with other amounts in the same transaction. The contract held 8,539.45 ETH before and 3.999 ETH after. The EOA that sent the transaction received 8,535.36 ETH, 0.1 ETH went to the block's fee recipient, and within two days all of it was sent on to three addresses, one of which started making 100 ETH deposits into the Tornado Cash router.

DefiLlama lists $26,400,000 for "Truebit" on 2026-01-08 and classes it "Token & Share Accounting" / "Arithmetic Error"; BlockSec's write-up gives the transaction and says the cause is an addition that overflows in `_getPurchasePrice()`. This entry re-derives what the chain shows: the state one block before, the receipt's logs, the balances, the call trace, and where the ETH went. It does not read the implementation's source (it is not verified anywhere) and does not re-derive the cause, which is BlockSec's reading of the bytecode. The contract has not been fixed and may still be exploitable, which was not tested, so this entry gives no price formula, no amounts that make the sum wrap and no way to find them. It does not examine the second attacker some press reports mention.

The registry `registre_hypotheses.csv` states each fact as a falsifiable claim with its locator; `reconstruct_exploit.py` re-derives every on-chain number here live, check by check.

## At a glance

| | |
|---|---|
| Victim | The Truebit purchase contract, a proxy at `0x764c64b2a09b09acb100b80d8c505aa6a0302ef2` with the unverified implementation `0xc186e6f0163e21be057e95aa135edd52508d14d3`, which sells TRU (`0xf65b5c5104c4fafd4b709d9d60a185eae063276c`) against ETH on a bonding curve |
| Chain | Ethereum |
| Date | 2026-01-08, 16:02:35 UTC, block 24191019, transaction index 3, tx `0xcd4755645595094a8ab984d0db7e3b4aabde72a5c87c4f176a030629c47fb014` |
| Mechanism | Per BlockSec, `_getPurchasePrice()` adds two large terms with no overflow check, so for some amounts the price comes out far too low. The receipt shows five purchases from the contract, the first at a price of 0, each sold back to the same contract. The arithmetic is not re-derived or given here |
| Attacker | EOA `0x6c8ec8f14be7c01672d31cfa5f2cefeab2562b50`, which had sent nine transactions before (the first on 2025-12-06) and sent four plain transfers after; the transaction before this one, in the same block, created the attack contract `0x1de399967b206e446b4e9aeeb3cb0a0991bf11b8` |
| Loss | 8,535.453576519732789359 ETH (the contract's balance fell from 8,539.452648748044247863 to 3.999072228311458504), about $26,490,309 at DefiLlama's ETH price of 3,103.56 at the block time |
| Funds | The EOA received 8,535.363576519732789359 ETH and 0.1 ETH went to the block's fee recipient. The EOA sent 0.1 + 4,267 ETH to one address, 4,001 ETH to a second and 267.714966732018310674 ETH to a third, between 2026-01-08 16:09 and 2026-01-10 19:52 UTC; it holds 1.000000001e-9 ETH now. The third address made its first four transactions 100 ETH deposits through the Tornado Cash router. No return of funds was looked for |
| Press figures | DefiLlama: $26,400,000 (Truebit, Ethereum, "Token & Share Accounting" / "Arithmetic Error", source empty), 0.34% under the value found here. BlockSec: the transaction, an overflow in `_getPurchasePrice()`, an implementation whose source is not public |

## The contracts

The purchase contract is an upgradeable proxy: one block before the attack, its EIP-1967 implementation slot holds `0xc186e6f0...14d3`. The proxy and the TRU token are verified on Sourcify; the implementation and the attack contract are not. One block before the transaction (block 24191018) the purchase contract's ETH balance was 8,539.452648748044247863 and the TRU supply was 161,753,242.367424992669183203.

## The exploit, from the receipt

The attacker's EOA created the attack contract (nonce 9, transaction index 2) and called it in the next transaction (nonce 10, index 3) with 0.01 ETH and the argument 10^17 (0.1 ETH in wei). The attack contract then ran five rounds against the purchase contract; by the call trace each round is a `getPurchasePrice` call, a `buyTRU` at that price, and a `sellTRU` of everything just bought. The receipt's 32 logs show five mints of TRU to the attack contract, five transfers of the same amounts to the purchase contract and five burns by it; the TRU supply is the same before and after.

| Round | Price paid | ETH received |
|---|---|---|
| 1 | 0 | 5,105.06862519801295139 |
| 2 | 6 wei | 2,512.725519441713511752 |
| 3 | 0.000319134474904345 | 789.982659124501396402 |
| 4 | 0.015168571520541215 | 124.467568270275031182 |
| 5 | 5.114995545275641043 | 8.339687736500985242 |

The sales add up to 8,540.584059771003875968 ETH and the prices paid to 5.130483251271086609, so the contract lost 8,535.453576519732789359 ETH, as the attack contract's last event also states.

The call trace, read from one node, shows the attack contract sending 0.1 ETH to the block's fee recipient (`0x4838b106fce9647bdf1e7877bf73ce8b0bad5f97`, the block's `miner` field) and then 8,535.363576519732789359 ETH to the EOA. Without the trace, the same split follows from the balances: the EOA's balance rose by 8,535.348497836391626573 ETH, to which add its fees (0.005078683341162786 ETH) and the 0.01 ETH it sent, and the remainder of what the contract lost is 0.1 ETH, the argument of the call.

## What came after

Nine transactions earlier, from 2025-12-06, the EOA had made two 0.50015 ETH calls to a swap contract, created and called a contract, and on 2025-12-27 made five 1 ETH deposits through the Tornado Cash router (verified on Sourcify as `TornadoRouter`, selector `deposit(address,bytes32,bytes)`). After the attack it sent four plain transfers and nothing else:

| Nonce | When (UTC) | To | ETH |
|---|---|---|---|
| 11 | 2026-01-08 16:09 | `0x3b58192943ee6f9ae92d54dd1ef378cfd519862a` | 0.1 |
| 12 | 2026-01-08 16:11 | `0x3b58192943ee6f9ae92d54dd1ef378cfd519862a` | 4,267 |
| 13 | 2026-01-08 18:29 | `0x273589ca3713e7becf42069f9fb3f0c164ce850a` | 4,001 |
| 14 | 2026-01-10 19:52 | `0xd841c52b68c5db133078aba039bd9eaf19b0b135` | 267.714966732018310674 |

The first address sent 0.1 and 4,266.99 ETH on to `0x62afdd1bd84f6b152572404be90679ae58eb4862` and holds 0.0099 ETH. The second sent 0.1 and 4,000.900562100975 ETH to the third address. The third made its first four transactions 100 ETH deposits through the Tornado Cash router, and has sent 61 transactions in all. All five addresses are accounts without code. None of them is labelled here, and the trail was not followed past these hops.

## The hours after the first transaction

The same contract kept being used. From block 24191080 to block 24192373 TRU's logs show 6,711 mints to 21 addresses and 105 transfers of TRU into the purchase contract from 6 addresses, the last in block 24192339; there is none of either kind from block 24195001 to block 24300000. The contract's ETH balance was 3.999072228311458504 right after the first transaction and 16.441259438635460491 at block 24192400, where it stayed at block 24195000: higher, not lower. The traces I read show payouts to those callers adding up to about 4.18 ETH, 4.04 of them to one address, but they do not reconcile with the balance changes to within 0.24 ETH, so no total is claimed. The press figure of a second wallet taking about $224,000 is not reproduced on this contract.

## The contract today

At the time of writing the proxy still points to the same implementation, `0xc186e6f0...14d3`: the contract has not been fixed by an upgrade. It is possibly still exploitable; this was not tested. Its `reserve()` reads 0.091011059533144807 ETH and its ETH balance is 16.451259438635460491 ETH. This entry does not give the price formula, the amounts that make the sum wrap, or a method for finding them.

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, an Ethereum archive node list walked in order (the state at an old block needs an archive node; the nodes that refuse are skipped), one node that serves the call trace when available, Sourcify, DefiLlama's hacks and coins APIs. The transaction hash came from BlockSec's write-up; everything else follows from the chain. The script does not call the price function. It takes about a minute.

1. **The exploit transaction and the attack contract's creation** (H1 to H3).
2. **The contracts and what is verified** (H4, H5).
3. **The state one block before** (H6).
4. **The receipt's logs**: five purchases and sales, the amount taken (H7 to H9).
5. **Who got the ETH**, with the trace when a node serves it (H10 to H13).
6. **The attacker's earlier and later transactions** and where the ETH went first (H14 to H19).
7. **Value** and **DefiLlama's record** (H20, H21).
8. **The hours after the first transaction**: who kept using the contract, and its ETH balance (H22, H23).
9. **The contract today** (H24).

Each is a numbered check printed as PASS or FAIL; `--tx <hash>` runs the script with another Ethereum transaction as the exploit and `--expect-eth <wei>` with another amount: the checks that read them fail, see `preuves/temoins_negatifs_2026-10-23.txt`.

## Caveats

- **The cause is BlockSec's, not re-derived.** The implementation's source is not verified anywhere; "the final addition is unchecked" is BlockSec's reading of the bytecode, which was not redone here, and this entry does not model the contract's arithmetic.
- **The call trace comes from one node.** Two checks (H12, H13) depend on it and are skipped when no node serves it; the same split follows from balances (H10, H11).
- **How the attacker found the amounts was not examined,** and this entry does not suggest a way: what the nine earlier transactions were for (a swap contract, a created contract, five test deposits into a mixer router) was not looked into.
- **The later use of the contract is counted, not analysed.** Who the 21 addresses are, whether they were attackers, bots or ordinary buyers, and what each took was not examined; the press figure of about $224,000 for a second wallet was not read and is not reproduced here; the trace sums of what the contract paid out afterwards are not reconciled with its balance and are not claimed.
- **Where the ETH went stops at the first hops.** Five addresses are named, none is labelled, and the Tornado Cash deposits of the third are seen only in its first four transactions.
- **Truebit's own statements were not found or read,** and whether anyone was compensated was not examined; that the contract is unchanged is read from its implementation slot only. BlockSec's page is the only analysis opened; SlowMist, CertiK, Verichains, Cantina, Halborn, QuillAudits and Rekt appeared in a search and were not opened.
- **The loss is the ETH at one price.** About $26,490,309 at 3,103.56; the attacker's net proceeds are 8,535.36 ETH after the 0.1 ETH paid to the block's fee recipient.
- **The category is the nearest of the index's seven.** An arithmetic overflow in a price function: Rounding/Math-Bug.

## License

MIT, see the repository root.
