# Gravity Bridge Denom-Poisoning Exploit Postmortem

Independent on-chain reconstruction of the Gravity Bridge exploit (Ethereum
+ Osmosis + Gravity Chain, 2026-05-30). rekt.news published the most
detailed account found, naming all 8 Ethereum transaction hashes and the
Cosmos-side setup narrative, but it was security-research journalism, not
a document from Gravity Bridge itself: the team's own public response was
two short halt notices, no technical postmortem. Every Ethereum-side claim
below was independently re-derived from raw chain data starting from
Gravity Bridge's own GitHub deployment record, not copied from the
article, and the Cosmos-side minting claim is independently corroborated
by a live cross-chain match against Osmosis's own tokenfactory state,
rather than simply repeated.

## At a glance

| | |
|---|---|
| Incident | Permissionless `deployERC20()` plus a missing registry collision check in Gravity Bridge's Ethereum contract let an attacker register a fabricated Cosmos denom string embedding a real custody-token address, poisoning the bridge's token registry |
| Window | 2026-05-30 01:52:35 UTC to 02:31:11 UTC (the 8 Ethereum transactions); Cosmos-side setup reported by rekt.news as starting weeks earlier with a minimal validator self-delegation |
| Press figure | rekt.news / PeckShield: ~$5.4M ($4.3M USDC, $434K USDT, 274.34 WETH, 14.16 PAXG) |
| Verified independently | Exact same 4 assets, to 6 decimals, read directly from the bridge contract's own `Transfer` and `TransactionBatchExecutedEvent` logs; total $5,397,931.45 at CoinGecko's theft-day prices, within 0.04% of DefiLlama's own tracked $5,400,000 |
| A real correction | DefiLlama's own hacks feed classifies this "Key Compromise" / "Validator Key Compromised". Every validator signature on the 4 outgoing batches was genuine; the registry itself was poisoned via a permissionless function call with no collision check, not a compromised key |
| What's still open | The Gravity Chain (Cosmos-side) validator-registration transaction and validator address rekt.news names could not be independently re-confirmed; see Caveats |

## The method

```bash
pip install web3
python3 reconstruct_exploit.py
```

Starting anchor: `Gravity-Bridge/Gravity-Docs`, the project's own GitHub
docs repository, states the "Gravity.sol Contract Address" directly in
`docs/resources.md`. This script fetches that file live and asserts the
address it contains matches the contract used in every transaction below,
rather than trusting rekt.news's label or Etherscan's tag alone. From
there, all 8 Ethereum transaction hashes rekt.news names are fetched and
their logs decoded directly (no ABI needed beyond the standard ERC20
`Transfer` topic and the two custom event topics observed on the bridge
contract itself), and the Osmosis-side claim is checked against a live
query to Osmosis's own tokenfactory module, independent of anything
Ethereum-side.

RPC endpoints used, all public, no key: `eth.drpc.org` (Ethereum),
`rest.cosmos.directory/osmosis` (Osmosis LCD), `api.coingecko.com` (theft-day
pricing), `api.llama.fi/hacks` (DefiLlama's own tracked record).

## What it found

### The poisoning: 4 fabricated denom strings, decoded directly from on-chain event data

The bridge contract's `deployERC20()` function is permissionless by
design. On 2026-05-30 between 01:52:35 and 01:53:23 UTC, an attacker
address (`0x73e95ae5f3b87e02d4547afe86d0d466e9450d6b`) called it 4 times.
Decoding the `ERC20DeployedEvent` each call emits, straight from the raw
log data rather than from the article, shows the `_cosmosDenom` argument
passed each time:

```
ibc/C92D312D79D9C44B6C6F94AF40FFCB30A334D87F08952D6ED9904E3E83A9F50C/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48/transfer/channel-10/factory/osmo1m9athjzah02f2mnrgtcke7e5ya3zpvw8lccuss
```

That string embeds USDC's real Ethereum contract address
(`0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`) as a path segment inside
what is supposed to be an opaque Cosmos IBC denom identifier. The same
pattern repeats for USDT, WETH, and PAXG in the other 3 calls. Each call
deploys a fresh wrapper contract and writes this fabricated string into
the bridge's own denom-to-ERC20 registry, with no cross-check against the
registry's existing, legitimate entries for those same 4 real tokens.

### Independently cross-checked against Osmosis, not just repeated from the article

rekt.news's account has the attacker first minting 4 worthless tokens on
Osmosis via its `tokenfactory` module, then IBC-transferring them to
Gravity Chain to obtain the predictable metadata the deploy calls above
rely on. Rather than taking that on faith, this project queried Osmosis's
own `tokenfactory` module live for every denom the named attacker address
(`osmo1m9athjzah02f2mnrgtcke7e5ya3zpvw8lccuss`) has ever created. It
returns exactly 4, and every one embeds, as its own final path segment,
one of the 4 wrapper-contract addresses independently decoded from the
Ethereum side above:

| Osmosis tokenfactory denom (live query) | Matches Ethereum wrapper for |
|---|---|
| `.../0x9a280B869A73b6fF812a599E40ABd8dbdFB738c2/x` | USDC |
| `.../0xC4E01e1Bf95f218e97303FA59D21240A93f27c37/x` | USDT |
| `.../0x198930Ca72F1ed2399FDAe362D3AC6e0b2bCae20/x` | WETH |
| `.../0x899C7b3A16ad95DB1aF5EBE17ceF9eDeF5b87cdb/x` | PAXG |

4 of 4, obtained from two independent, unrelated public endpoints. This is
the strongest evidence this project has for the Cosmos-side half of the
mechanism.

### The drain: exact amounts, sequential batch nonces, all independently decoded

35 minutes later, 4 `submitBatch` outputs (Gravity's normal, legitimately
validator-signed withdrawal path) released real assets from the bridge
contract to the attacker's wallet (`0x7b582033061b96cc3f9421e73a749ed7c62da1f9`),
tagged with 4 sequential `TransactionBatchExecutedEvent` nonces:

| Asset | Batch nonce | Amount (decoded, 6dp) |
|---|---|---|
| USDC | 41572 | 4,349,701.311883 |
| USDT | 41573 | 434,072.402068 |
| WETH | 41574 | 274.345940 |
| PAXG | 41575 | 14.163836 |

All 4 match rekt.news's own reporting to the precision it gave, now taken
several decimals further, read directly from the `Transfer` events in
each transaction's own receipt.

### DefiLlama's own classification is wrong, independently shown

DefiLlama's `api.llama.fi/hacks` record for this incident (`defillamaId:
"3293"`) labels it `"Key Compromise"` / `"Validator Key Compromised"`.
That is contradicted by the reconstruction above: the 4 outgoing batches
carry genuine validator signatures over a checkpoint that was, at the
time of signing, already corrupted by the poisoned registry. The
validators did nothing wrong and no signing key was compromised; the
failure is a missing collision check in `handleErc20Deployed` against a
permissionless `deployERC20()` input. This project's own independent
decode of the raw event data, not merely rekt.news's narrative framing,
is what supports calling DefiLlama's classification wrong here. Worth
noting: DefiLlama's own $5.4M figure and 2026-05-30 date are both
accurate; only the technique/classification fields are wrong.

### A minor date note

All 8 on-chain transaction timestamps read 2026-05-30 UTC (01:52:35 to
02:31:11). rekt.news's own article text says the bridge "was drained on
May 29th". DefiLlama's own tracked date (2026-05-30) agrees with this
project's on-chain reading rather than with the article's prose; this may
simply be a timezone framing in the article rather than an outright date
error (the same UTC window falls on the evening of May 29th in North
American time zones), so it is reported here as a discrepancy, not
asserted as a clear-cut mistake the way the Allbridge or MAYAChain
entries in this repo report theirs.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Gravity Bridge, rekt.news, or any outlet it credits.
- The Gravity Chain (Cosmos-side) validator-registration transaction hash
  and validator address rekt.news names could not be independently
  re-confirmed: the tx hash returns "tx not found" on 2 different public
  Gravity Chain nodes (both live and synced, checked 2026-09-10), and the
  named validator address fails bech32 checksum validation on both. This
  is most likely public nodes not retaining tx history back to the
  2026-06-25/07-17 window the article describes, or a transcription
  artifact somewhere upstream of this project, not evidence the claim is
  false. It is reported as unconfirmed rather than silently repeated or
  silently dropped. See `resultats_sources_2026-09-10.txt` for the full
  detail of what was tried.
- The Ethereum-side reconstruction (the actual dollar loss, the exact
  mechanism, the DefiLlama classification correction) does not depend on
  that unconfirmed Cosmos-side detail; it is anchored entirely in
  Gravity Bridge's own GitHub-documented contract address and decoded
  directly from that contract's own event logs.
- "Not fully swept" (H9 in the hypothesis registry) reflects wallet
  balances as queried on 2026-09-10; both attacker wallets have been
  actively moving funds toward Tornado Cash per rekt.news's own tracing,
  and these balances will likely continue to change after this snapshot.
- One working public RPC (`eth.drpc.org`) was used for the entire
  Ethereum-side reconstruction, plus `rest.cosmos.directory/osmosis` for
  Osmosis and `api.coingecko.com` / `api.llama.fi` for pricing and the
  DefiLlama comparison; no paid RPC or API key was used anywhere in this
  project.

## License

MIT

<!-- external source: https://rekt.news/gravity-bridge-rekt -->
