# Cosmos EVM Vesting-Account Underflow Postmortem

Between August 20 and 25, 2026, an attacker used a single chained bug in
`cosmos/evm`, the shared module dozens of Cosmos SDK chains use for EVM
compatibility, to drain native-token balances on at least six blockchains.
Cosmos Labs itself named only three in its own post-mortem: MANTRA, TAC,
and KiiChain. This project re-fetches all three chains' own cited
transactions directly from each chain's own public RPC (not from the
post-mortem's prose, not from a block explorer search), and in doing so
finds two things nobody else appears to have published: DefiLlama's own
tracked dollar figures for this incident, summed across just three of the
six chains, are about 3x Cosmos Labs' own total realized figure for all
six combined; and Cosmos Labs' own post-mortem misattributes a block
number to the wrong transaction hash on the KiiChain leg, citing a
downstream "sweep" call with zero events as if it were the delegate call
that actually triggers the underflow, which is a different, unremarked
transaction five blocks earlier.

## At a glance

| | |
|---|---|
| Incident | Shared `cosmos/evm` staking-precompile underflow/overflow, GHSA-7g4w-cg88-2cq2 |
| Window | 2026-08-20 19:06 UTC (MANTRA, first hit) to 2026-08-25 15:20 UTC (per Cosmos Labs) |
| Chains named by Cosmos Labs | MANTRA, TAC, KiiChain (3 more chains confirmed exploited, not named) |
| Cosmos Labs' own total (realized) | ~$5.72M across all 6 chains (2.87M DEX + 2.85M CEX), stated "not independently audited" |
| DefiLlama's tracked total | $17.2M for MANTRA + TAC + KiiChain alone ($0 + $7.5M + $9.7M) |
| Verified independently | Block height + timestamp for all 3 named chains' cited transactions; the exact TAC drain amount from a self-derived pool address; a block/tx-hash mismatch in Cosmos Labs' own post-mortem for KiiChain |

## The method

Starting anchor: Cosmos Labs' own post-mortem, published on its GitHub
security org (`cosmos/security`), not a press summary or a block explorer
search:
https://github.com/cosmos/security/blob/main/communications/cosmos_evm_GHSA-7g4w-cg88-2cq2_post_mortem.md

That document names three transaction hashes (MANTRA's two attacks, TAC's
one, KiiChain's one) with block heights and UTC timestamps. Every one of
those is re-fetched here from the chain's own RPC:

```bash
pip install web3
python3 reconstruct_exploit.py
```

RPC endpoints used: `https://rpc.tac.build` (TAC), `https://evm.archive.mantrachain.io`
(MANTRA archive node; MANTRA's regular RPC prunes history past a few
thousand blocks), and `https://json-rpc.kiivalidator.com` (KiiChain).

The `bonded_tokens_pool` address used on TAC is not looked up anywhere: it
is computed as `SHA256("bonded_tokens_pool")[:20]`, the standard Cosmos SDK
module-account derivation, which is identical on every Cosmos SDK chain
regardless of denom, decimals, or chain ID.

## What it found

### TAC: the exact drained amount, from a self-derived address, not a lookup

Cosmos Labs' post-mortem states TAC's `bonded_tokens_pool` lost
2,985,651,403.40 TAC at block 24662148. This project computed that pool's
address independently (it is not chain-specific, see above), queried its
balance on TAC's own public RPC at the block immediately before and at the
exploit block itself, and found: 2,985,651,403.404713 TAC before, exactly
0 TAC after. That matches the post-mortem's figure to the two decimal
places it published, and adds a digit of precision the post-mortem does
not give. The block height (24662148) and block timestamp
(2026-08-22T19:46:37+00:00) both match the post-mortem exactly. The
attacker's own EOA gained 2,985,651,402.729713 TAC in the same transaction
 - about 0.68 TAC less than the pool lost, consistent with gas paid in the
same call.

### MANTRA: both attacks confirmed second-for-second, and a rough price check on the $3.6M figure

Both of MANTRA's cited attack transactions were re-fetched from MANTRA's
archive RPC (its regular RPC only retains a few thousand recent blocks,
too short a window to reach back to August 20). Both the block height and
the UTC timestamp, to the second, match the post-mortem exactly:
block 17444928 at 19:06:00 UTC for attack #1, block 17449159 at 22:59:01
UTC for attack #2.

Measuring the attacker's own EVM balance immediately before and after each
transaction (isolating each attack to its own single-transaction block)
gives a net gain of 600,000,035.50 OM from attack #1 alone, and a further
120,923,932.38 OM from attack #2. MANTRA's own reported loss, as relayed
by crypto.news, is 720.9 million OM "then valued at about $3.6 million",
taken from two addresses. The two measured gains sum to 720,923,967.89 OM,
which matches that token count, so the $3.6M covers both attacks, not
attack #1 alone (an earlier version of this check divided by attack #1
only and got $0.0060/OM). On both attacks it implies about $0.0050/OM, in
the same order of magnitude as OM's price when this was first written
($0.004418, per CoinGecko, after OM continued falling post-exploit). This
is reported as a cross-check, not as independent confirmation of a
historical price feed. It is also not in tension with Cosmos Labs'
$5.72M six-chain total below: $3.6M values the OM taken, while $5.72M is
what was actually converted into other assets. See
`resultats_sources_2026-09-14.txt`.

Unlike TAC, MANTRA's `bonded_tokens_pool` was not the victim: its balance
moved by only 1 wei across attack #1's block, confirming the post-mortem's
statement that victim accounts varied per chain ("arbitrary accounts with
high balances, such as the 0x00 address or a multisignature wallet created
during chain genesis").

### KiiChain: the post-mortem cites the wrong transaction for its own anchor

This is the part of the reconstruction that turned up something the
post-mortem itself gets wrong. Cosmos Labs' document reads: "KiiChain is
exploited via the identified vulnerability (tx `0xf45c07e94a4d4474220c96b1fff5f798bf22f4a4adf159d8f3e28c52caf1e840`,
block 9355102)." Fetching that exact transaction hash from KiiChain's own RPC,
by two independent methods (`eth_getTransactionReceipt` and
`eth_getTransactionByHash`), returns block **9355107**, not 9355102, a
five-block, roughly eleven-second gap. This is not fixable by rounding:
block 9355102 is a real, populated block, five blocks earlier, containing
a *different* transaction entirely.

That other transaction, `0xaf0ac52bbef9996ef0c22a93cba5f55a71de79d1799175c6d8bcc35988d7ae9b`,
genuinely at block 9355102, is the one that actually matches the
mechanism the post-mortem describes: it carries a log at the staking
precompile address (`0x0000000000000000000000000000000000000800`), the
same event signature (`topic0`) seen on both the TAC and MANTRA exploit
transactions, decoding to a delegation of exactly
2,000,000,000,000,000,001 akii (2 KII plus 1 wei). That is the same "2 KII
+ 1 wei" delegate pattern rekt.news documented independently (by different
means) for a different one of KiiChain's 18 repeated exploit iterations.

The transaction the post-mortem actually cites by hash
(really at block 9355107, not 9355102) carries **zero** event logs and
calls a helper contract with function selector `0x01681a62` and the
attacker's own address as its sole parameter, consistent with a
downstream "sweep to attacker" call, not the underflow-triggering
delegation itself. In short: Cosmos Labs' own post-mortem paired the right
block number with the wrong transaction hash for its single KiiChain
anchor, and the hash it did cite documents a later step in the same
18-iteration sequence, not "the" exploit moment.

### DefiLlama's tracked dollar figures run about 3x the primary source's own realized total

DefiLlama's hacks feed (`api.llama.fi/hacks`, fetched 2026-09-10) carries
this incident as three separate rows: MANTRA Chain ($0), TAC ($7.5M), and
KiiChain ($9.7M, the only one of the three without a registered
`defillamaId`). Summed, that is $17.2M for three of the six chains Cosmos
Labs says were exploited. Cosmos Labs' own post-mortem states a combined
realized total, across **all six** chains, of only about $5.72M (2.87M
sold on DEXes + 2.85M sold on centralized exchanges), explicitly flagged
by Cosmos Labs itself as "not independently audited."

Dividing each DefiLlama dollar figure by the *full* amount extracted on
that chain gives an implied price of $0.0654/KII and $0.00251/TAC.
Dividing the post-mortem's own cited swap outputs (1,607,323.41 USDT for
64.6M KII sold via PancakeSwap; roughly $1,005,293 for about 1.2085B TAC
sold via KyberSwap plus a smaller STON.fi leg) by the amount actually sold
gives a realized price of $0.0249/KII and $0.00083/TAC, 2.6x and 3.0x
lower, respectively. DefiLlama's figures track much closer to the full
amount an attacker *extracted* than to what the post-mortem says was
actually turned into stablecoins. This project could not trace DefiLlama's
exact price source (its own `source` field is empty for all three rows),
so this is reported as a directional finding, not a reproduction of
DefiLlama's exact arithmetic (see `registre_hypotheses.csv` H10).

MANTRA's own DefiLlama row, meanwhile, shows $0, even though the
widely-reported $3.6M figure is independently plausible from this
project's own on-chain balance-delta reconstruction above. DefiLlama
overstates two of the three named chains and, on the same incident, shows
nothing at all for the third.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Cosmos Labs, MANTRA, TAC, KiiChain, DefiLlama, or any
  outlet cited above.
- Three of the six chains Cosmos Labs says were exploited are not named in
  its post-mortem ("three other chains... we are not including their full
  details in this timeline for brevity"). Nothing here can speak to them;
  the loss figure in the root README's index is marked as a floor (≥) for
  this reason, and because the $5.72M total this entry leans on is itself
  "not independently audited" per its own source.
- The ~$0.0050/OM and $0.0654/KII / $0.00251/TAC price points in this
  README are implied prices solved backward from other reported dollar
  figures, not independently sourced historical price-feed lookups. They
  are reported as order-of-magnitude cross-checks, explicitly flagged as
  weaker evidence in `registre_hypotheses.csv` (confidence "Medium"),
  not as confirmed facts.
- The KiiChain tx-hash/block mismatch found here is about Cosmos Labs' own
  document, not about the underlying facts of the exploit: the actual
  drain (block 9355102, tx `0xaf0ac52b...`) is real and independently
  confirmed by this project, matching the mechanism described everywhere
  else in the same document. This is a citation error in an otherwise
  detailed and unusually transparent primary source, not evidence the
  incident didn't happen as described.
- This project did not attempt to independently verify MANTRA's or TAC's
  cited USDT/ETH/TON/USDC/OSMO totals sold on DEXes beyond the specific
  KII (PancakeSwap) and TAC (KyberSwap) legs the post-mortem itself
  breaks out by number; the combined $2.87M DEX figure is taken from the
  post-mortem as reported.
- The 3 other chains' RPC endpoints, if any are public, were not located
  or queried for this project.

## License

MIT

<!-- external source: https://github.com/cosmos/security/blob/main/communications/cosmos_evm_GHSA-7g4w-cg88-2cq2_post_mortem.md -->
