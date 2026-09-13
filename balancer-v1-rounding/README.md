# Balancer V1 Legacy Pools Rounding Exploit Postmortem

Independent on-chain reconstruction of a rounding-error exploit against legacy Balancer V1 pools (Ethereum mainnet, 2026-08-30/31). DefiLlama's hacks feed and roughly ten press outlets, most of them appearing to syndicate a single SlowMist writeup rather than reporting independently, all cover this as a single $234,000 incident against a single pool. This project traced the exploit from Balancer's own primary-source deployment addresses outward and found the same operator wallet drained **four separate pools**, not one, in a single overnight run, splitting the proceeds across four separate cash-out wallets, then decoded an on-chain negotiation message no press source quoted directly.

## At a glance

| | |
|---|---|
| Incident | Rounding-error exploit against legacy, unmaintained Balancer V1 BPools, Ethereum mainnet |
| Window | 2026-08-30 22:13 UTC (operator wallet's first attack-contract deployment) to 2026-08-31 06:31 UTC |
| Press figure | ~$234,000, one pool (DPI/USDC/WETH/WBTC), per DefiLlama and ~10 syndicated outlets |
| Verified independently | The same operator wallet drained **4 distinct Balancer V1 pools**, confirmed via `BFactory.isBPool()`, each swept to a different cash-out wallet - a scope no press source reported |
| A mechanism press got wrong | No flashloan-token transfers appear anywhere in the actual exploit transactions, and the main pool's WBTC balance had already been thin for at least 7 days - contradicting the "nested flash loans used to compress reserves" framing several outlets repeated |
| A genuine primary-source find | An on-chain message, decoded directly from calldata, from an address claiming to represent Balancer DAO: a bounty offer with a 2026-09-08 21:00 UTC deadline. No response or fund return found on-chain as of this research (2026-09-09) |

## The method

```bash
pip install web3
python3 reconstruct_exploit.py
```

No hardcoded press figures on the on-chain side: every address the committed script touches is either read from Balancer's own primary source or discovered by the script itself, working outward from that one anchor. No address in this project was taken from a press article without an independent on-chain check first.

1. **The pool factory address comes from Balancer's own GitHub, not a block explorer search.** `balancer/docs-v1`'s `smart-contracts/addresses.md` (still live) lists BFactory at `0x9424B1412450D0f8Fc2255FAf6046b98213B76Bd`. This project confirmed it on-chain first (bytecode length 24,407 bytes) before using it as the sole starting anchor for everything else. Separately, a GitHub API call confirmed `balancer/balancer-core` itself is archived and the `balancer-labs` org now holds only two repositories, independently corroborating press reports that Balancer Labs shut down in March 2026.
2. **The DefiLlama-tracked pool is confirmed, not assumed.** `BFactory.isBPool()` and `getCurrentTokens()` were called directly on the pool DefiLlama's feed points to, confirming both that it is a genuine Balancer V1 pool and that its token composition matches press's description.
3. **The exploit mechanism is read from decoded event logs, not summarized from an article.** The exploit transaction's `LOG_JOIN` and `LOG_EXIT` events were decoded directly, and net token flow to the attack contract was computed by aggregating the transaction's own `Transfer` logs, independently reproduced by two distinct calculation passes in this project (a wide-window scan, then a single-transaction scan), landing on the same figures each time.
4. **The wider scope came from following one wallet, not searching for more incidents.** The operator EOA's complete transaction history (via Blockscout's public API, `eth.blockscout.com`, no key) was paginated, and every contract it deployed was checked against `BFactory.isBPool()`, surfacing three further pools no press source this project found names.
5. **Two custom function selectors** (a generic `execute(bytes)` calldata executor and a `sweep(...)` cash-out call) were identified via the public 4byte.directory signature database, not guessed from context.
6. **The whitehat message was decoded from raw calldata**, byte for byte, not paraphrased from a press summary of it.
7. **The DefiLlama hacks feed itself was queried directly** (`api.llama.fi/hacks`), not taken from a screenshot or a secondary citation of it.
8. **Press coverage was searched, then spot-checked.** An initial press search was delegated to a research agent; the specific claim that one outlet names the exact attacker, attack-contract and pool addresses this project independently derived was then re-verified by directly re-fetching that article and, as a control, two other articles covering the same event, this time with an explicit instruction to quote any address verbatim or state that none exist.

One working public RPC (`gateway.tenderly.co/public/mainnet`) was used throughout, plus Blockscout's public API for wallet transaction histories, and the public 4byte.directory signature database for function-selector lookups. No paid RPC, archive-node subscription, or API key was used anywhere in this project.

## What it found

### The DefiLlama record, and the pool it actually names

DefiLlama's hacks feed (`api.llama.fi/hacks`, queried 2026-09-09) carries this incident as:

```json
{
  "date": 1788048000,
  "name": "Balancer V1",
  "classification": "Token & Share Accounting",
  "technique": "Rounding Error",
  "amount": 234000,
  "chain": ["Ethereum"],
  "bridgeHack": false,
  "targetType": "DeFi Protocol",
  "source": "",
  "returnedFunds": null,
  "defillamaId": "116",
  "parentProtocolId": "parent#balancer",
  "language": "Solidity"
}
```

`date` 1788048000 converts to 2026-08-30. The `source` field is empty, the same pattern this research program has found on every other DefiLlama record it has checked.

The pool that single $234,000 figure describes, `0x2257aaac34bcb27900291f7b84ee2565a6cbac57`, confirms on-chain as a real Balancer V1 pool: `BFactory.isBPool()` returns `True`, and `getCurrentTokens()` returns exactly DPI, USDC, WETH and WBTC, matching press's description. Queried live by this project, the pool's current balances are now down to near-zero residuals: 0.02052270 DPI, 1.17778300 USDC, 0.00047190 WETH, 0.00001504 WBTC.

Its single exploit transaction (`0x72510b257cc09bde8435b83ac1636f9498ffc353583330600b5b8da43d0d1aff`, block 25,872,274, 2026-08-31 02:28:23 UTC, gasUsed 11,377,828, 1,496 total logs) contains 100 `LOG_JOIN` events, every sampled one of them joining with `amt_raw=1` on WBTC (1 satoshi), exactly the "rounded down to 1 satoshi" mechanism press described, now shown directly from decoded events rather than taken from an article, plus 108 `LOG_EXIT` events. Aggregating the transaction's own `Transfer` logs gives a net extraction to the attack contract, `0x9cAa8d0E44b22f50057d2F4ce0D1446529e11be3`, of 544.76510327 DPI, 27,714.72484500 USDC, 11.44838131 WETH and 0.35710736 WBTC, the same figures on both independent calculation passes this project ran.

### One operator wallet, four pools, a scope no press source reports

The transaction above came from operator wallet `0x338C7Ec9BefbB451d66Fd8A468c32184f5689a41`, whose transaction count was 0 (its first-ever transaction) at 2026-08-30 21:12:59 UTC, about 5 hours before the pool-D exploit transaction decoded above (already at nonce 6 by then): a fresh, single-purpose wallet, the same pattern this research program's Ajna and Notional postmortems found.

Paginating that wallet's complete transaction history via Blockscout shows it deployed four separate attack contracts between 2026-08-30 22:13 UTC and 2026-08-31 06:31 UTC, each confirmed against a distinct real Balancer V1 pool via `BFactory.isBPool() == True`:

| Pool | Pool address | Attack contract |
|---|---|---|
| A | `0x9b208194acc0a8ccb2a8dcafeacfbb7dcc093f81` | `0x0359E5006f83E8c2CaBDd434494354Be835f3450` |
| B | `0x1373e57f764a7944bdd7a4bd5ca3007d496934da` | `0x5d0583cB69df5C3602292263FcA6700Cf273E2c9` |
| C | `0xa751a143f8fe0a108800bfb915585e4255c2fe80` | `0xed1A1379fDc6A7A0D2a6A3E290B059469825975e` |
| D (the DefiLlama-tracked pool) | `0x2257aaac34bcb27900291f7b84ee2565a6cbac57` | `0x9cAa8d0E44b22f50057d2F4ce0D1446529e11be3` |

Every pool required dozens of `execute(bytes)` calls (identified via 4byte.directory as a generic custom-calldata executor) followed by a `sweep(...)` call, and every one of those transactions succeeded (`status: 1`) with 1,300 to 1,600 logs each, the same repeated-rounding pattern as pool D. No press source found by this project's search reports more than a single pool or a single $234,000 figure.

### Four sweeps, four separate destinations, full token detail

Each attack contract's proceeds were swept to its own destination wallet, an EOA with pre-existing transaction history, not a fresh wallet, and distinct from the operator wallet and from the other three destinations:

| Pool | Swept to | Tokens received |
|---|---|---|
| A | `0x9d0d918644c057b29538eb5567f9b48befb65f33` | 0.07554759 WBTC, 10,191.65740700 USDC, 13,445.88434193 DAI, 5,278.43210424 UNI-V2, 0.15373323 renBTC, 406.70901731 LINK, 457.52886055 UNI, 126,986.89671717 BLZ, 869,118.27720949 WSTA, 10,416.49994978 SNX |
| B | `0xa86e7d84bf2d1de9497d0e8eb46a90f7e99551cc` | 8,473.42023999 DAI, 8,496.58934300 USDC, 5.34635385 MKR, 23,293.50428481 UMA, 764.15104458 LINK, 40,539.03461042 SNX |
| C | `0x0437fa52a192590440f885cf8e596aaa5e697ce5` | 18,892.16598241 AMPL, 0.42845429 WBTC |
| D | `0xade439ade910a20854d4270d645b8a982d8f273b` | 544.76510327 DPI, 27,714.72484500 USDC, 0.35710736 WBTC |

This project reports exact token amounts rather than a single dollar total for pools A, B and C, since it has no independently verified historical price feed for tokens like BLZ or WSTA, but the sheer token variety and volume make clear the real scope of this incident is a multiple of the $234,000 DefiLlama recorded for pool D alone. Splitting proceeds across four separate destinations, one per pool, rather than consolidating to a single cash-out address, is a detail no press source this project found reported.

### No flashloan was found, and the thin reserves were not freshly engineered

Several press sources describe the attacker using "nested flash loans across Aave, Spark, Morpho and Uniswap V3" to compress the pool's WBTC reserves toward zero before the rounding exploit. This project checked both claims directly against the pool D exploit transaction: its own logs contain Transfer events for exactly five tokens (DPI, USDC, WETH, WBTC and the pool's own BPT share token), nothing else, so no flashloan-token movement appears anywhere in the transaction that actually executed the exploit. Separately, the pool's WBTC balance was already close to its post-exploit level roughly a week earlier (0.362 WBTC seven days before, versus 0.357 WBTC the block before the exploit), meaning this was a long-standing thin reserve in an unmaintained legacy pool, not something the attacker freshly compressed that same night. This project cannot rule out a flashloan-funded compression happening even earlier than the week-long window checked, but found no evidence for one in the window it did check.

### A whitehat negotiation message, decoded directly from the blockchain

On 2026-09-03 16:37:23 UTC (block 25,898,022), an address unlabeled in Blockscout, `0x3877188e9e5DA25B11fDb7F5E8D4fDDDCE2d2270`, sent a zero-value transaction (`0xd4858faf506dd7164b5fa84a244ebc3657dcf9c7af671ec1329d7d4d084ccd4f`) to the operator wallet carrying 2,830 bytes of calldata. Decoded as UTF-8 directly by this project (not paraphrased from any article), it reads as a formal notice from an entity identifying itself as "Balancer DAO":

```
Balancer DAO — Notice to wallet owner:

We understand this wallet is linked to the exploit of Balancer V1 on Aug 31st, 2026. We are treating this as an opportunity for cooperation and would prefer to resolve this without escalation.

If you are willing to cooperate, reply to this message and begin contact procedures before September 8th, 21:00 UTC. If we do not hear from you by that time, we will assume you are unwilling to help make the liquidity providers whole and will escalate our response.

We would like to extend you an offer: return the funds to the DAO multisig address in exchange for a bounty. The details of this offer shall be arranged privately. Upon verification that the returned funds meet the criterias, Balancer will not pursue legal action or investigative steps aimed at identifying or prosecuting the owner of the returning wallet that are based solely on the fact of the return.

If you do not accept this offer or do not respond in time, we will use all technical, on-chain, and legal measures to identify and pursue the attacker. In that case, any bounty will instead be used to reward verified informants who help identify and lead to prosecution of the attacker.

To proceed, respond to this message privately via Blockscan (https://chat.blockscan.com). After successful verification, all communications will be coordinated with SEAL911, Hypernative, and Balancer's legal team.
```

The sender's claimed "Balancer DAO" identity is not independently confirmed beyond the message's own text: Blockscout carries no label or public tag for this address.

### As of this research, no resolution

The operator wallet's current transaction count is 40; its last-ever outgoing transaction (nonce 39) is dated 2026-09-01 07:09:11 UTC, two full days before the message above was even sent, and nothing further was found from that wallet up to this project's research date (2026-09-09), one day after the message's own deadline. None of the four cash-out wallets show a matching return transaction either. This project found no on-chain evidence that the attacker responded, cooperated, or returned any funds.

### Press coverage: heavy syndication, and one address match this project could not confirm from readable text

Nine outlets found by this project's search (news.bitcoin.com, cryptobriefing.com, blockfence.io, crypto-economy.com, cryptotimes.io, KuCoin's news flash, PrimeXBT, ground.news, cryptoticker.io), plus coinedition.com, describe the same mechanism and appear to largely be syndicating a single SlowMist writeup rather than reporting independently. Nearly all of them attribute the underlying vulnerability class to the same bug family as the ~$116M Balancer V2 hack of November 2025, and report Balancer Labs having shut down in March 2026 following that earlier incident, which this project independently corroborated on-chain above via the archived GitHub repository. coinedition.com is the outlet reporting the 2026-09-08 21:00 UTC deadline for the attacker to return funds.

Only one outlet found, cryptotimes.io, names specific addresses: the attacker wallet, the pool-D attack contract, and the pool-D pool address, all three matching exactly what this project independently derived starting only from the BFactory anchor. Two other articles covering the identical event (blockfence.io, crypto-economy.com), re-fetched directly and asked explicitly to quote any address verbatim or state that none exist, returned no addresses at all, so this project could not confirm from readable primary text that cryptotimes.io's own article genuinely contains these values, as opposed to a fetch-tool fabrication (the same failure mode this research program's Term Finance postmortem flagged). All three addresses were nonetheless independently re-derived and confirmed correct by this project's own on-chain trace, before this project ever compared them back to the press-suggested values.

## Caveats

- This is independent research, not an audit, and not affiliated with Balancer, Balancer DAO, SEAL911, Hypernative, or any outlet cited above.
- No historical price feed was used, so no aggregate USD figure is given for the three additional pools; only exact on-chain token amounts are reported.
- The identity of the address that sent the whitehat negotiation message is unconfirmed beyond its own message text; this project found no independent label or attribution for it. This project's own hypothesis register rates that specific point Low confidence.
- Whether a flashloan-funded compression happened before the 7-day window this project checked was not ruled out, only that none was found within it or in the exploit transactions themselves.
- One token in Pool B's listed underlying assets did not respond to standard `symbol()`/`name()` calls (neither the string nor the older bytes32 ABI) and was not identified; it was not part of the tokens actually swept out, so this does not affect the reported amounts.
- The claim that cryptotimes.io's own article names the three addresses this project matched is rated Medium confidence in this project's hypothesis register, not High: this project could not independently confirm the article's raw text actually contains them (two control articles returned no addresses when asked to quote verbatim), only that the addresses themselves check out correct on-chain regardless of that specific source's reliability.
- DefiLlama's own hacks-feed record for this incident carries an empty `source` field, the same pattern this research program has found on every other record it has checked.
- One working public RPC (`gateway.tenderly.co/public/mainnet`) was used throughout, plus Blockscout's public API for wallet transaction histories and the public 4byte.directory for function-selector lookups; no paid RPC, archive-node subscription, or API key was used anywhere in this project.

## Files

- `README.md` : this file.
- `reconstruct_exploit.py` : the committed Python (web3.py) script that reproduces every on-chain check in this postmortem: the BFactory confirmation, the pool-D composition and balance checks, the pool-D exploit transaction decode (LOG_JOIN/LOG_EXIT counts, sample amt_raw values, net Transfer-log extraction), the operator wallet's four-pool deployment history, all four sweep-transaction decodes, and the whitehat message's UTF-8 decode.
- `resultats_reconstruction_2026-09-09.txt` : raw stdout from running `reconstruct_exploit.py`, the on-chain evidence behind every number in this README.
- `resultats_sources_2026-09-09.txt` : the DefiLlama hacks-feed record for this incident, the press-coverage research (which outlets were found, the SlowMist-syndication pattern, the cryptotimes.io address cross-check), and Balancer's own primary-source GitHub checks.
- `registre_hypotheses.csv` : this project's hypothesis register, one row per claim (H1 through H13), each with its locator in the result files above, a falsification test, and a confidence rating (High/Medium/Low).
- `LICENSE` : MIT license.
- `.gitignore` : standard Python ignore rules (`__pycache__/`, `*.pyc`, `.venv/`).

## License

MIT
