# DoinGud Diamond Double Payout, Post-Mortem

On September 21, 2026, at 03:27:25 UTC, one transaction on Polygon emptied the marketplace escrow of DoinGud, an NFT platform, of 35,486.935717 USDC.e, all it held. The attacker's contract took a flash swap of exactly that amount, put it into the escrow as an offer from itself on token id 1, then called the Diamond's accept function twice with the identical four arguments. Both calls paid the full price out of the escrow and neither was refused, so the escrow paid twice what had been put in; the second payout was the funds that were already there. The flash swap was repaid with its 0.3 % fee and the attacker's account received 35,380.154566 USDC.e.

DefiLlama lists $35,486 for "DoinGud" on 2026-09-21 and classes it as a "Swap Logic Flaw" ("Protocol Logic"); a public proof of concept in the DeFiHackLabs repository describes the same double accept and attributes it to an offer record that is never deleted. This entry reconstructs the sequence on the chain: the loans, the three calls, the payouts, the balances before and after. It does not read the code that failed: the facet that handles the calls is not published.

The registry `registre_hypotheses.csv` states each fact as a falsifiable claim with its locator; `reconstruct_exploit.py` re-derives every on-chain number here live, check by check.

## At a glance

| | |
|---|---|
| Victim | The users whose USDC.e sat in the escrow of the Diamond `0xe3a161edd679fc5ce2db2316a4b6f7ab33a8ed6a` (`DoinGudDiamond`), 35,486.935717 USDC.e in all; they were not itemized. A search result describes the platform as a dormant NFT marketplace whose contracts stayed deployed and funded; that page was not opened |
| Chain | Polygon |
| Date | 2026-09-21, 03:27:25 UTC, block 94170781, index 0, tx `0x56818a63077f5ba8bfc0bc0877ac33502a5d65cc79dbf5dfaac2a0b8545216a8` |
| Mechanism | An offer from the attacker's own contract at a price equal to the escrow's whole balance, then the accept call (selector `0x5c924960`) twice with identical arguments: each pays the price from the escrow and neither is refused or consumed differently. The calls reach a facet `0x123aafc8d0a07ce1a146e53aa899e77f21a2dde1` that is not published |
| Attacker | EOA `0xb8c717239bcace558c3a8dc471c16e07bf57a1eb` (943 transactions before this one), which deployed the contract `0xe588834aa3161a0720e8f6bf223748d6098a4b76` on 2026-05-03, 141 days earlier (code not published) |
| Loss | 35,486.935717 USDC.e, about $35,477 at DefiLlama's USDC.e price of 0.99972 at the block time: the escrow's whole balance before the transaction |
| Funds | 35,380.154566 USDC.e to the EOA; not traced further. Nothing returned was found |
| Press figures | DefiLlama: $35,486 (DoinGud, Polygon, "Protocol Logic" / "Swap Logic Flaw", target type NFTfi, source empty). The DeFiHackLabs pull request (merged 2026-09-26): offer price 35,486.935717 USDC, flash-swap repayment 35,593.716868 USDC, net profit 35,380.154566 USDC, matching the figures here |

## The exploit, call by call

Read from the call trace and the logs (`preuves/`):
1. The attacker's contract (selector `0xa6588745`) takes a flash swap of 35,486.935717 USDC.e from the pair `0x160532d2536175d65c03b97b0630a9802c274dad`.
2. It calls the Diamond with selector `0xf6dbe82d` (an offer: itself as offerer, token id 1, price 35,486.935717 USDC.e) and sends the same amount of USDC.e to the Diamond.
3. It calls the Diamond with selector `0x5c924960`, which a public proof of concept names `acceptOffer(offerer, tokenId, price, amount)`, with arguments (itself, 1, 35,486.935717, 0). The Diamond sends 35,486.935717 USDC.e to the attacker's contract and emits three events: a transfer of 0 units of token id 1 from the attacker's contract to itself, one carrying the price, one naming the contract.
4. It makes the same call again with the same four arguments. The Diamond again sends 35,486.935717 USDC.e to the attacker's contract and emits the same three events, identical except one counter word that goes from `0x39fc` to `0x39fd`.
5. It repays the pair 35,593.716868 USDC.e (the loan and a fee of 106.781151, 0.3009 %) and sends the remaining 35,380.154566 to the EOA.

Each call goes through the Diamond to the same facet by `delegatecall`, and none reverts. One block before the transaction the Diamond held exactly 35,486.935717 USDC.e; after the attacker's deposit it held 70,973.871434, paid out twice 35,486.935717 and ended at 0 (and holds 0 now). The loss to others is therefore the 35,486.935717 that was there before.

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, Polygon RPC with archive state (Tenderly's public gateway, `polygon-bor-rpc.publicnode.com`, `polygon.drpc.org`; the call trace comes from drpc, `--trace-file` reads a saved one), Sourcify's API and DefiLlama. DefiLlama gave a date and an amount; a public proof of concept gave the transaction hash and the facet address; everything else follows from the receipt, logs, balances and trace. It takes under a minute.

1. **The exploit transaction**, the attacker's contract (created 141 days before) and account (H1 to H3).
2. **The Diamond**: its balance before and after, the verified proxy and the unpublished facet (H4).
3. **The call trace** (H5) and **the money flows** (H6).
4. **The events** of the two accepts (H7) and **the arithmetic of the escrow** (H8).
5. **Value** and **DefiLlama's record** (H9, H10).

Each is a numbered check printed as PASS or FAIL; `--tx <hash>` runs the script with another Polygon transaction as the exploit and `--expect-price <units>` with another price: the checks that read them fail, see `preuves/temoins_negatifs_2026-10-22.txt`.

## Caveats

- **The failing code was not read.** The facet that handles the offer and accept calls is not published (Sourcify has only the proxy). That the accept does not consume the offer, that it ignores the offerer being the caller and that a non-zero amount reverts are the proof-of-concept author's reading from a fork and from disassembly, not established here; what the chain shows is the three calls, the two identical payouts and the balances.
- **The function names are the proof of concept's.** Only the selectors are on the chain; `acceptOffer` is the name that proof of concept gives to `0x5c924960`, and the offer call's name is not known.
- **Whose funds, and how many holders, is not itemized.** The escrow held 35,486.935717 USDC.e before; who put it there, whether it was all owed to users and whether DoinGud or anyone compensated them were not examined, and no statement from DoinGud was found.
- **The attacker's contract and earlier activity are not examined.** Its code is not published; the EOA had sent 943 transactions before and 1,050 by now, and whether other incidents are linked to it was not looked into. The destination of the 35,380.154566 USDC.e was not traced.
- **The category is the nearest of the index's seven, not an exact fit.** The flaw is an accept that pays without consuming, a state and accounting error; the index has no logic category, so the entry sits under Rounding/Math-Bug with the other share-accounting entries.
- **The loss is the escrow's balance at one price.** About $35,477 at DefiLlama's price of 0.99972; DefiLlama's $35,486 is the USDC.e count truncated to the dollar. The attacker's take (35,380.154566) is smaller by the flash-swap fee and is not the loss.

## License

MIT, see the repository root.
