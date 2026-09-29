# Symbiosis syBTC Unbacked Mint Postmortem

Independent on-chain reconstruction of the 2026-09-11 unbacked mint of
Symbiosis's synthetic Bitcoin token syBTC. Press coverage and DefiLlama both
place this incident on two chains, Ethereum and BNB Chain, and count eight
bridge transactions. Reading Symbiosis's own deployment list rather than the
press's chain list turns up a third inflated chain, Rootstock, hit by the same
key with the same amount inside the same four minutes, and brings the count to
twelve mints and the unbacked total from 368.9 billion syBTC to 553.4 billion.

## At a glance

| | |
|---|---|
| Incident | Twelve unbacked mints of the Symbiosis synthetic Bitcoin token syBTC, each authorised by the bridge's own live MPC signing key, across Ethereum, BNB Chain and Rootstock |
| Window | 2026-09-11 04:28:40 UTC to 04:32:25 UTC for the mints, 04:35:23 UTC for the single cash-out (6 minutes 43 seconds end to end) |
| Press and DefiLlama figure | About $336,000, "approximately 4.39 WBTC", 368.9 billion syBTC over eight bridge transactions on Ethereum and BNB Chain, dated 2026-09-10 by DefiLlama |
| Verified independently | 4.38897292 WBTC out of one Uniswap V4 swap, worth $338,285 at the WBTC price of that exact second, reconciling DefiLlama's $336,000 to within 0.7% |
| A chain nobody reported | Rootstock also carries 184,467,440,737.09552 syBTC, exactly 2^64 raw units, from four mints signed by the same key from 04:28:56 to 04:32:25 UTC. Neither DefiLlama's chain list nor any press account found mentions it |
| A count nobody reported | Twelve successful mints, not eight, and 553,402,322,211.29 syBTC minted rather than 368.9 billion |
| The part the press garbled | "2^62 raw units, nominal value approximately 46.1 billion USD" is a token count, not a dollar figure. 46.1 billion is how many syBTC one mint creates |
| Root cause, on-chain part | None. The signature check in Symbiosis's BridgeV2 worked exactly as written, and the key it checked against was the correct one |
| What's still open | Whether that key was compromised or whether the off-chain validator was induced to sign a malformed amount cannot be settled from chain data. The evidence here leans to the second |

## The method

```bash
python3 reconstruct_exploit.py
```

Standard library only, no API key, no installed dependency. The script carries
its own keccak-256 and its own secp256k1 public-key recovery, and refuses to
report any recovered signer unless both primitives pass a round-trip self-test
first.

Two things about the starting point matter. First, the only external input is
the single Ethereum transaction hash that press coverage published; every
address, every other chain and every amount below was derived from it rather
than read from an article. Second, the list of chains examined comes from
Symbiosis's own committed SDK configuration
(`js-sdk/src/crosschain/config/cache/mainnet.json`), which names five chains
carrying a syBTC representation. That is the reason Rootstock shows up here:
the press's chain list has two entries, the protocol's own has five, and
checking all five is what surfaces the third inflated chain.

Rootstock's public node does not expose `eth_getLogs` at all, so the mints
there are located by bisecting `totalSupply()` block by block rather than by
reading events, then confirmed by pulling the bridge transactions out of the
blocks the bisection lands on.

## What it found

### Twelve mints, not eight, across three chains, not two

Every one of the twelve carries the identical amount, 4,611,686,018,427,388,234
raw units. That is 2^62 plus 330, and the `+330` survives on all three chains.

| Chain | Mints | Blocks | First mint UTC | Last mint UTC |
|---|---|---|---|---|
| BNB Chain | 4 | 121198105, 121198122, 121198134, 121198155 | 04:28:40 | 04:29:03 |
| Ethereum | 4 | 25951769, 25951770, 25951771, 25951773 | 04:28:47 | 04:29:35 |
| Rootstock | 4 | 9229602, 9229604, 9229606, 9229610 | 04:28:56 | 04:32:25 |

Total minted: 55,340,232,221,128,658,808 raw units, or 553,402,322,211.29
syBTC. Still outstanding at the time of writing: 553,402,058,355.75 syBTC,
spread almost exactly evenly across the three chains at roughly 184.47 billion
each. Press reporting that "roughly 184.5 billion syBTC still remains on BNB
Chain" is accurate for BNB Chain in isolation and understates the outstanding
total by a factor of three.

Rootstock's supply is a tidy confirmation on its own. It sat at 195,101,329 raw
units before the incident, took four mints, then a burn of 195,102,649 at block
9229612 left it at 18,446,744,073,709,551,616, which is 2^64 exactly.

Two of the five chains Symbiosis lists were untouched: zkSync still carries
0.051097 syBTC and Citrea 0.00510312.

### The bridge's own live key signed all of it

This is the part that changes how the incident reads. Symbiosis's BridgeV2
gates `receiveRequestV2Signed` behind `onlySignedByMPC`, and the hash it checks
covers the entire inner call data, the mint amount included:

```
keccak256(bytes.concat("receiveRequestV2", _callData, bytes20(_receiveSide),
    bytes32(block.chainid), bytes20(address(this))))
```

Recovering the signer from each of the four Ethereum mints returns the same
address every time, `0x855eeeae34d08597db031094efbd8b6d15f849f6`, and calling
`mpc()` on the bridge at each of those blocks returns that same address. The
same holds on Rootstock under chain id 30. The signature check did not fail,
was not bypassed, and was not fed a forged signature: the key the contract was
supposed to trust is the key that authorised the mints.

Nor did the attacker install that key. `mpc()` rotates on a fixed daily
schedule, driven by the same relayer account that submits ordinary bridge
traffic:

| Block | UTC | New mpc() |
|---|---|---|
| 25931022 | 2026-09-08 07:01:35 | 0xed44d13dbfe160bff53d89932294a7fce4a5b385 |
| 25938188 | 2026-09-09 07:01:35 | 0x91a614e561fe6c8e054f207eab7e66eb7693b884 |
| 25945362 | 2026-09-10 07:01:23 | 0x855eeeae34d08597db031094efbd8b6d15f849f6 |
| 25952529 | 2026-09-11 07:01:11 | 0xd890729b7ed7724fbe6e1f1804ac93114e3abb28 |

The exploit key arrived at its scheduled hour on 2026-09-10 and left at its
scheduled hour on 2026-09-11, two and a half hours after the mints. Six
ordinary user mints sampled in the hours before the incident, for everyday
amounts between 0.00350506 and 0.49948230 syBTC, all recover to that same key.
It was the bridge's live operating key doing its normal job, and it signed
these twelve payloads alongside that normal traffic.

So the failure is not in the contract and not in the key rotation. It is in
what the off-chain validator agreed to put its signature on.

### The amount looks like a real deposit with one bit flipped

4,611,686,018,427,388,234 is 0x400000000000014A. Strip bit 62 and 330 remains,
which at eight decimals is 0.0000033 BTC, a dust deposit. The payload's
`chainIdFrom` is 3652501241, which is 0xD9B4BEF9, the Bitcoin mainnet message
magic that Symbiosis uses as its Bitcoin chain identifier, and each of the four
Ethereum payloads carries a different 32-byte origin reference, consistent with
four distinct claimed Bitcoin deposits. Every payload names the same
beneficiary, `0x025122b60470eee9e7947fbd922fe0d35f5d3ba2`.

That reading, a genuine dust deposit whose amount reached the signer with bit
62 set, is inference from the arithmetic rather than proof. It is recorded as
such in the hypothesis registry.

### The whole thing converted to 4.39 WBTC and left in four blocks

One Uniswap V4 swap, Ethereum block 25951802 at 04:35:23 UTC, pushed
18,446,744,072,845,450,682 raw syBTC into the pool and took 438,897,292 raw
WBTC out, which is 4.38897292 WBTC. At the WBTC price DefiLlama records for
that exact second, $77,076.12, that is $338,285. DefiLlama's $336,000 is within
0.7%, so this is a reconciliation and not a correction.

The beneficiary had already taken 0.00049605 WBTC out of the same venue at
block 25951357, 03:06:23 UTC, an hour and twenty-two minutes before the first
mint, which looks like a route test. The combined 4.38946897 WBTC left the
beneficiary at block 25951806, 04:36:11 UTC, forty-eight seconds after the
swap, to a contract at `0x666fedd4cdd4e890a5ad20e7b60975409435a64a` that holds
no WBTC today.

Set against the 553.4 billion syBTC created, 4.39 WBTC realised is a ratio of
about 1.26e+11 to one. The mint was effectively unbounded and the cash-out was
bounded by whatever WBTC one Uniswap V4 pool happened to hold.

### DefiLlama's record

DefiLlama carries this as id 1594, amount 336000, chains `["BSC","Ethereum"]`,
classification "Bridge & Cross-Chain", technique "Unbacked Cross-Chain Mint",
dated 1788998400, which decodes to 2026-09-10 00:00:00 UTC. The technique label
is right about the effect. The chain list is missing Rootstock, and the date is
a day early against the mints' own block timestamps of 2026-09-11 04:28 to
04:32 UTC.

## Caveats

Whether the MPC key was compromised or the off-chain validator was tricked into
signing a malformed amount cannot be decided from chain data, and this write-up
does not decide it. Three observations point away from a stolen key and none of
them is conclusive: the same key signed ordinary user traffic in the same
window, the attacker never touched the rotation schedule, and the amount
carries a `+330` remainder that a freely-chosen number would not need. A
compromised key used carefully would look much the same.

The `+330` as a genuine Bitcoin dust deposit is an inference from the
arithmetic. No Bitcoin-side transaction was examined, so the claimed deposits
were not checked against the Bitcoin chain at all.

The count of four mints on Rootstock rests on per-block `totalSupply()` deltas
rather than on Transfer events, because the public Rootstock endpoint does not
serve `eth_getLogs`. A mint exactly offset by a burn inside one block would be
invisible to that method.

BNB Chain's legitimate syBTC float immediately before the incident could not be
read: the one free BNB Chain endpoint that serves archive `eth_getLogs` refuses
archive `eth_call`. Ethereum's was 693,250,174 raw units, 6.93250174 syBTC, and
Rootstock's 195,101,329, or 1.95101329 syBTC.

The loss figure here is the realised extraction only. Holders of the small
legitimately-backed float on three chains are left holding a token whose supply
is now unbacked by a factor of about 2.6e+10, and whether they are made whole
is not something chain data answers. The figure should be read as a floor.

No official Symbiosis postmortem existed when this reconstruction was done. The
team's public statements at the time said the Bitcoin swap route was disabled,
an update was being deployed, and non-Bitcoin routes plus ETH and stablecoin
pools were unaffected. Nothing here contradicts those statements; the point of
difference is scope, not substance.

## License

MIT, Spap, 2026.
