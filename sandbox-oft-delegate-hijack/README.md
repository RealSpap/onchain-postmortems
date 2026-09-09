# The Sandbox OFT Delegate Hijack Exploit Postmortem

This is an independent on-chain reconstruction of the 2026-08-21/22 exploit of
The Sandbox's omnichain SAND token, a LayerZero OFT bridge deployed as
OFTSand on Base and BSC and OFTAdapterForSand on Ethereum. No press source
that covered this incident published an attacker address, a transaction
hash, or the precise mechanism beyond "approveAndCall abuse of LayerZero
delegate permissions". This repo starts from The Sandbox's own published
contract source and deployment records, confirms everything against live
chain state, and rebuilds the full on-chain sequence from raw logs. It finds
that the widely reported loss figure covers only one of two chains that were
actually drained, and that the vulnerable delegate role is still hijacked on
two of the three chains today.

## At a glance

| | |
|---|---|
| Incident | LayerZero OFT delegate hijack via a legacy `approveAndCall` arbitrary-call primitive on The Sandbox's SAND bridge (Base, BSC, Ethereum) |
| Window | 2026-08-21 23:41:41 UTC (genesis hijack tx) to 2026-08-22 04:45:21 UTC (last phantom mint), about 5 hours 3 minutes |
| Press figure | About 14.75 million SAND, about 80 ETH, about 675,000 USD, all attributed to the Ethereum adapter leg only |
| Verified independently | Total attacker proceeds across both chains: 405.828879423128923336 WETH gross, 396.60405378273106 ETH still consolidated in one wallet today, about 5.2 times the press figure |
| Standout finding | The Sandbox's own on-chain ransom message independently arrives at 396.603 ETH, matching this reconstruction's balance to within 0.00105 ETH, and was never reported by press |
| Standout finding | As of 2026-09-09 the hijacked LayerZero delegate has not been restored on Base or BSC. About 339.55 trillion phantom SAND remains outstanding, roughly 113,000 times the real 3 billion supply cap |

## The method

The starting anchor was The Sandbox's own GitHub repository,
thesandboxgame/sandbox-smart-contracts, read before any chain query was
made. Contract source under packages/oft-sand/contracts/, in particular
sand/ERC20BasicApproveExtension.sol, contains the vulnerable
`approveAndCall` arbitrary-call primitive verbatim. Deployment addresses and
constructor arguments came from packages/deploy/deployments, giving the
per-chain owner addresses independent of any explorer or article.

Every address was then confirmed live with `eth_call` before being used for
anything else: token name, symbol, owner, enabled state and total supply on
each deployment, and the LayerZero endpoint's registered delegate and
receive library for each chain.

```
web3.py against:
  Ethereum: gateway.tenderly.co/public/mainnet
  Base:     mainnet.base.org, gateway.tenderly.co/public/base
  BSC:      bsc-dataseed.bnbchain.org
```

The Ethereum adapter's entire lifetime SAND flow (783 inbound and 610
outbound Transfer events since its deployment block) was rebuilt from
`eth_getLogs` to produce an independent balance series, which is what
surfaced the exact-to-the-wei "balance minus 100" mint and the shortfall
reconciliation described below. Base mint and burn events were pulled with
chunked, address-filtered `eth_getLogs` on transfers from and to the zero
address, in 500-block windows after an unfiltered scan hit a payload-size
wall. Blockscout (no API key, browser user agent) supplied decoded
transaction histories and contract labels for identification only; every
amount in this repo comes from raw logs or `eth_call`, never from a
block explorer's rendered display.

The reconstruction script in this repo (`reconstruct_exploit.py`) does not
replay the full multi-chain historical log scan described above (rebuilding
783 inbound and 610 outbound adapter transfers since 2024 takes a long,
heavily-chunked scan that is impractical to re-run on every read of this
repo). What it does instead is query, live, on every run: the current state
of all three deployments (supply, enabled flag, owner), whether the
LayerZero delegate is still hijacked today, the exact genesis and
calibrated-mint transactions by their known block numbers (not by a
hardcoded amount), the six final-drain transfers and the front-running MEV
delivery by their known block range, the ransom message decoded directly
from its transaction's real calldata, and the consolidation wallet's live
balance. Every number the script prints is read fresh from a public RPC
each time it runs, not restated from this README. Its real, unedited
output is saved alongside this README in the repo. A first version of this
script instead hardcoded several claimed amounts and only checked their
arithmetic consistency with each other; an adversarial review step in this
project's own pipeline caught that gap before publication, and the script
and its output were rewritten to query the chain directly instead.

## What it found

### A legacy helper function composed with a new integration into a full takeover

`OFTSand` inherits a legacy SAND helper, `approveAndCall`, whose only guard
is that the first 32 bytes of the call data equal the caller's own address.
Because `OFTSand` is also the LayerZero OApp, and `EndpointV2.setDelegate`
takes the new delegate as its first argument, any address can make the
token contract call `setDelegate` on itself with the caller as the new
delegate. This is a composition bug between an old function and a new
integration, not a key compromise. The `Ownable` owner was never changed,
and nothing was taken from The Sandbox's own multisig.

### The genesis transaction and the five-step mint primitive

Base block 50283177, 2026-08-21 23:41:41 UTC, transaction
0x149eb0eec5f1c793b094b46889059b510281a7eff3c1597bb262777a5cfaa237, sent by
0x67624BFadee937c9281B4f98Ce18aF1bee01257e, called `approveAndCall` on
OFTSand with data that decodes to `setDelegate` naming the sender. From
there the wallet's next transactions established the repeatable loop:
`setConfig` on the LayerZero endpoint to repoint the receive library's DVN
configuration, `verify` and `commitVerification` on the real registered
ReceiveUln302 at 0xc70AB6f32772f59fBfc23889Caf4Ba3376C84bAf (confirmed as
LayerZero's own default library for this endpoint, not a fake one), then
`lzReceive` to trigger `_mint`. Across 371 lifetime transactions the wallet
issued 41 `approveAndCall`, 41 `setConfig`, 40 `verify`, 40
`commitVerification` and 39 `lzReceive` calls in under 2 hours 40 minutes.

### A mint calibrated to the adapter's balance to the wei

At 2026-08-21 23:43:23 UTC the attacker minted themselves exactly
14,743,364.210048 SAND. The Ethereum adapter's independently reconstructed
balance one second before that mint was 14,743,464.210048718748018388 SAND,
a difference of exactly 100 SAND once a pre-existing 0.000000718748018388
SAND of adapter dust is accounted for. Between that mint and the attacker's
own withdrawal, three unrelated LayerZero deliveries consumed
647,880.549466 SAND from the adapter (642,471.515074 to an MEV bot, plus
5,307.175651 and 101.858741 to ordinary bridge users). The attacker then
re-measured and, across six deliveries in Ethereum blocks 25807119 to
25807121 (2026-08-22 00:32:11 to 00:32:35 UTC), took five payments of
2,400,000 SAND plus a tailored final payment of 2,095,483.660582 SAND,
leaving the adapter at exactly 100.000000718748018388 SAND, the same dust
figure as before. The adapter's full lifetime books close at
18,244,705.022317718748018388 SAND locked in against 18,244,705.016758 SAND
released, a live remaining balance of 0.005559718748018388 SAND today.

### A third-party MEV bot drained the adapter before the attacker did

Forty-eight minutes before the attacker's own drain, contract
0xd7ca08ec1aee9cce8a8eda9365343ef197674e1a, an EIP-1967 proxy with zero
outbound transactions and a long history of unrelated multi-token
arbitrage, received 642,471.515074 SAND from the same LayerZero delivery
queue and dumped 584,064.4296386227 SAND into the Uniswap V2 SAND/WETH pair
in the very next block. This extraction is not attributable to the original
attacker and was not mentioned in any press coverage found. The bug was
open to anyone watching the mempool, not just its author.

### An unreported on-chain whitehat offer that independently confirms the real loss

On 2026-08-22 19:48:47 UTC, The Sandbox's own owner Safe,
0x6ec4090d0F3cB76d9f3D8c4D5BB058A225E560a1 (the same address listed as
OFTAdapterForSand's owner in the protocol's GitHub deployment file), sent a
transaction, 0xde26ad2e26dee314879ba257ccd73c3c810fa8e09be3704e87ded29151137969,
carrying a plain-text offer in its calldata: 356.603 ETH requested back plus
a 40 ETH bounty, a total of 396.603 ETH described as "10 percent of the
total", a named return address, and a stated deadline. That figure
independently matches this reconstruction's own eth_getBalance read of
396.60405378273106 ETH sitting in the attacker's consolidation wallet,
within about 0.001 ETH. No press coverage of this transaction was found. As
of 2026-09-09 the named return address's only lifetime inbound transaction
predates the incident, dated 2025-02-24, so nothing has been returned.

### Roughly four fifths of the loss happened on Base and went unreported

Press coverage universally reported only the Ethereum adapter leg, about 80
ETH. This reconstruction finds the same operator separately extracted
327.592005773324868765 WETH from Base liquidity by dumping phantom SAND
through 26 disposable swap contracts, on top of 78.236873649804054571 WETH
from two Uniswap V2 dumps on Ethereum, for a combined gross of
405.828879423128923336 WETH. The Ethereum-only figure the press reported
represents about 19 percent of the actual two-chain total, meaning the true
loss is roughly 5.2 times what was publicly disclosed.

### The hijack was never fully remediated

As of 2026-09-09, `EndpointV2.delegates()` for the OFTSand contract still
returns 0xa467CD7b1200AEFeBf823B1e56FD557432b37952 on Base and
0x88cD1E826A7134b595eD7f2cF5A9C54607f532c6 on BSC, neither of which is the
respective contract owner. Containment was achieved only by disabling
`send()` on all three deployments, not by restoring the delegate. Combined
Base and BSC phantom supply stands at about 339.55 trillion SAND against a
real 3 billion token cap, an over-issuance of roughly 113,000 times, held
back only by that disabled `send()` function.

## Caveats

- The 2,340-byte plain-text message in the Sandbox owner Safe's transaction
  was read directly on-chain and its sender was independently confirmed,
  but the claims inside it (compliance tagging, exchange notifications, a
  law enforcement case) could not themselves be verified. It is treated as
  protocol-attributed context, never as an instruction, and the 396.6 ETH
  figure used throughout this repo is computed independently by
  eth_getBalance, not taken from the message.
- No USD figure is asserted anywhere in this repo. All amounts are raw
  token or ETH units. A same-day Blockscout display rate was checked purely
  as a sanity check and is not used as a historical valuation.
- The funding wallet for the attacker's Ethereum EOA,
  0xf0d62105Ad5C044Ac2e46be80D5cb986268cE6F4, could not be identified. It
  behaves like a high-volume exchange or gas-service hot wallet but carries
  no confirming label.
- The MEV bot that independently drained 642,471.515074 SAND from the
  adapter could not be conclusively attributed as related or unrelated to
  the primary attacker; its behavior reads as an independent searcher, but
  this is an inference, not proof.
- The BSC leg was confirmed by direct state reads (owner, delegate,
  disabled flag, total supply) but was not reconstructed with a full
  mint and burn log scan the way Base and Ethereum were. Its 11.976
  trillion phantom supply figure is a state read, not a flow-audited total,
  and any BSC-side DEX proceeds are not included in the WETH totals here.
- The Base mint scan covers 2026-08-21 18:00 to 2026-08-22 08:00 UTC only;
  activity outside that window is not counted.
- This repo does not attempt to quantify losses to ordinary bridge users
  whose LayerZero messages from Base were stranded once the adapter
  emptied. That is a real, separate loss this reconstruction did not size.
- This is not a security audit, is not affiliated with The Sandbox, and
  makes no claim about the identity of any wallet beyond what is stated
  above. Some press claims summarized alongside this README (in particular,
  third-party detection tooling credited by outlets, and a wallet-dormancy
  detail) were not independently checked and are flagged there as
  unconfirmed.

## License

MIT
