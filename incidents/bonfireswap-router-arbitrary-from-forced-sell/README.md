# BonfireSwap Router Forced Sale, Post-Mortem

On September 15, 2026, at 09:15:32 UTC, one transaction on BNB Smart Chain pulled BONFIRE tokens out of 65 holders' wallets without any of them signing anything, and had them turned into 66.080052256436953636 BNB. The transaction created a contract and used its constructor to call the BonfireSwap router, whose `transfer(to, amountAIn, beneficiary, deadline)` moves `amountAIn` of the token from the address `to` into the Pancake pair, using the allowance `to` had once given the router, and never checks that the caller is `to`. The pair's excess then went to the attacker's contract (5,082.493249693713424971 BONFIRE in 61 transfers) and the router unwrapped 66.08 WBNB for it. The BNB is still there: the contract's code only reverts, so nothing can be sent out of it by calling it.

DefiLlama lists $47,400 for "Bonfire" on 2026-09-15 and classes it "Access Control" / "Improper Access Control"; a public proof of concept in the DeFiHackLabs repository gives the transaction and the addresses, and one press article puts the loss at about $50,000 and about 41 holders. This entry re-derives the sequence on the chain: the router's verified source, the receipt's logs, the holders' balances and allowances one block before, the proceeds and where they sit now. It does not trace the calls (no node serves the trace of this old block), and it does not read BonfireSwap's own statements, none was found.

The registry `registre_hypotheses.csv` states each fact as a falsifiable claim with its locator; `reconstruct_exploit.py` re-derives every on-chain number here live, check by check.

## At a glance

| | |
|---|---|
| Victim | The holders of BONFIRE (`0x5e90253fbae4dab78aa351f4e6fed08a64ab5590`) who had approved the BonfireSwap router `0x17e801e17cefc6334059189c178d4783830e03d3`: 65 holders other than the attack contract and the token contract were pulled into the pair in the transaction, 5,420.900973001337074887 BONFIRE in all; they were not itemized |
| Chain | BNB Smart Chain |
| Date | 2026-09-15, 09:15:32 UTC, block 122003954, tx `0xb4c00e8f3ba815b6c70f45026f8794d2c1f079646a89919077688ce60692193f` |
| Mechanism | `transfer(address to, uint amountAIn, address beneficiary, uint deadline)` pulls the tokens from `to` with `transferFrom` and never compares `msg.sender` with `to`; `loggedTransfer` does the same. Any caller can name any holder who has an allowance to the router; the pair's excess goes to the caller's `beneficiary`, and the router's `sell` turns it into BNB |
| Attacker | EOA `0x2b5bf7d9d9dc1eec68f40c6b7a8f197e65f9731a`, which had sent nine transactions before this one, from 2026-05-04 (four contract creations, a WBNB transfer call, a WBNB withdrawal and three plain BNB transfers of 0.046790558, 0.5 and 0.4 BNB) and has sent none since; this transaction created the contract `0x28e976ea7b83553d6d1d45ce81334156a2632127` (its code is a 63-byte stub that reverts on every call) |
| Loss | 66.080052256436953636 BNB, about $47,364 at DefiLlama's BNB price of 716.77 at the block time: the BNB the attack contract holds, from two WBNB withdrawals by the router |
| Funds | All of it is still in the attack contract (same amount at the exploit's block and at block 129,187,030); it cannot be withdrawn by calling it. Nothing returned was found |
| Press figures | DefiLlama: $47,400 (Bonfire, BSC, "Access Control" / "Improper Access Control", source empty), 0.08% under the value found here. DeFiHackLabs: "~66 BNB (~$47-50K)". A Coinfomania article citing one SlowMist post on X: about $50,000, about 41 holders, largest loss "over 5,289 TOKEN" |

## What the router does

The router `BonfireSwap` is verified on Sourcify (match, solc 0.8.7). Its `transfer` is:

```solidity
function transfer(address to, uint amountAIn, address beneficiary, uint deadline) public ensure(deadline) returns (uint amountAOut, uint amountBOut) {
    _safeTransferFrom(tokenAddress, to, pancakePair, amountAIn);
    (amountAOut, amountBOut) = skimPools(beneficiary);
}
```

`_safeTransferFrom(token, from, to, amount)` calls the token's `transferFrom(from, to, amount)` and checks only that the call succeeded. Nothing compares `msg.sender` with `to`, nor asks whether the caller owns the tokens: the pull succeeds as long as `to` once gave the router an allowance. `loggedTransfer` has the same two lines. `skimPools(beneficiary)` then hands the excess in the pools to `beneficiary`.

## The exploit, from the receipt

The transaction is a contract creation (`to` is null, the receipt gives the created address), so everything happens in the constructor. Its 346 logs show:

1. **The pull.** BONFIRE transfers into the pair come from 67 distinct addresses: 65 holders, the attack contract and the token contract. The largest holder, `0xeff2fc4e3145f58f534d68a36bcd3085be6a4096`, loses 5,289.104767128481849088 BONFIRE in two transfers of 2,644.176000944142651753 and 2,644.928766184339197335 (the token caps a transfer at 5,000, per the proof of concept, which is why it takes two). One block before, that holder had 5,875.946668764761448339 BONFIRE and an allowance to the router above 2^128; the other four of the five largest holders also had a balance and an allowance to the router at least as large as what was pulled, and lost about 90% of their balance each.
2. **The refunds.** The pair sends the attack contract 61 transfers of BONFIRE, 5,082.493249693713424971 in all. The 5,420.9 pulled and the 5,082.49 received differ by 338.407723307623649916 BONFIRE, which is not explained here (the token takes a fee on transfers; not examined).
3. **The sales.** The router withdraws WBNB twice, 33.223195564710982431 and 32.856856691725971205, and the attack contract ends the transaction holding exactly their sum, 66.080052256436953636 BNB. The creation code contains the router's selectors for `transfer` (`0x335a9406`, once), `sell` (`0x8a038a54`, twice) and `skimPool` (`0x8757c3ab`, once).

## What came after

Nothing left the attack contract. Its code, `0x6080604052600080fd...`, is `PUSH1 0x80 PUSH1 0x40 MSTORE PUSH1 0 DUP1 REVERT` followed by a metadata hash: any call reverts, there is no `selfdestruct` and no function, so the BNB can neither be sent nor withdrawn by anyone. The same amount sits there at block 129,187,030. The EOA's balance fell by the gas it paid in this transaction (0.0003794891 BNB) and it has sent nothing since (its nine earlier transactions are the ones the script lists under H21). Why the proceeds were left in the contract was not examined.

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, a BNB Smart Chain node list walked in order (the state at old blocks needs an archive node; the public nodes that do not serve it are skipped), Sourcify, DefiLlama's hacks and coins APIs. The DeFiHackLabs proof of concept gave the transaction hash and the addresses; everything else follows from the receipt, the logs, the balances and the code. It takes under a minute.

1. **The exploit transaction** (H1 to H3).
2. **The router's verified source**: the pull, the helper, `loggedTransfer`, and the selectors in the creation code (H4 to H9).
3. **The pull, holder by holder**, from the receipt's logs (H10 to H12).
4. **The allowances** one block before (H13, H14).
5. **The proceeds** and where they are now, the attack contract's code, the sender's balance and nonce (H15 to H21).
6. **Value** and **DefiLlama's record** (H22 to H24).

Each is a numbered check printed as PASS or FAIL; `--tx <hash>` runs the script with another BSC transaction as the exploit and `--expect-bnb <wei>` with another amount: the checks that read them fail, see `preuves/temoins_negatifs_2026-10-22.txt`.

## Caveats

- **The calls were not traced.** No public node serves a call trace of this block (`debug_traceTransaction` is unavailable or reports "missing trie node"). The order of events is read from the receipt's logs and the creation code's selectors; the function names `transfer`, `sell` and `skimPool` are the router's, the way the attack contract used them is the proof of concept's account, matched here to the logs.
- **The counts and amounts are the receipt's own.** The 65 holders and the amounts are decoded from the receipt; the press count of about 41 holders is not reproduced here (27 holders lost at least 1 BONFIRE and 57 at least 0.01).
- **Who the holders are, and whether anyone was compensated, were not examined.** BonfireSwap's own statements were not found; the press article rests on one X post that was not read.
- **The loss is the BNB at one price.** About $47,364 at 716.77; the holders' own loss in BONFIRE (5,420.9 pulled) was not priced, and the token's market value was not examined. DefiLlama's $47,400 matches the proceeds, not the tokens.
- **The pull's fee** (338.41 BONFIRE between what was pulled and what the attack contract received) **is not explained.**
- **The attacker's contract holds the funds, but the attacker's intent was not examined**: whether the stub was meant, and what the EOA's nine earlier transactions and the four contracts it created before were for, were not looked into.
- **The category is the nearest of the index's seven.** The flaw is a missing caller check on a function that spends other people's allowances, an access-control error.

## License

MIT, see the repository root.
