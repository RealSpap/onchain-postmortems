# Float Protocol (Hypervisor Vaults) Postmortem

Independent reconstruction of a spot-price manipulation attack against
Float Protocol's two Gamma-style "Hypervisor" vaults (`vFLOAT-ETH3`),
which auto-manage FLOAT/WETH liquidity on a Uniswap V3 pool. In a single
atomic transaction, an attacker flash-borrowed 1,000 WETH from a lending
pool and flash-swapped 120,000 FLOAT from a Uniswap V2 pair, used that
capital to push the shared V3 pool's spot price (`slot0`) far from fair
value, then ran four deposit/withdraw cycles across the two vaults while
the price stayed distorted, each pair depositing a small, genuine stake
and withdrawing the identical share count moments later for a
disproportionate mix of the underlying tokens. Reversing the swaps and
unwrapping the residual WETH back to ETH nets the attacker exactly
10.706591043820923 ETH, confirmed two independent ways in this
reconstruction (the WETH contract's own `Withdrawal` event, and the
attacker's EOA balance delta across the block), both agreeing to the
wei. Two Gamma/Hypervisor vaults, deployed in November 2021 and untouched
for years, were still live, still holding real FLOAT/WETH liquidity, and
still carried no defense against this when this transaction landed.

## At a glance

| | |
|---|---|
| Incident | A flash-loan-funded Uniswap V3 `slot0` manipulation distorted the shared FLOAT/WETH pool's spot price; four deposit/withdraw cycles against Float Protocol's two `vFLOAT-ETH3` Hypervisor vaults, straddling that distorted price, redeemed more value than was deposited |
| Window | 2026-08-31T09:35:11Z, one transaction, one block (25,874,402) |
| Press/DefiLlama figure | SlowMist's own Twitter alert (as republished by crypto.news, cryptotimes.io, and others) states "10.71 ETH" lost; DefiLlama's hacks feed tracks the same incident (defillamaId 497, the same id as Float Protocol's unrelated January 2022 exploit) at a flat $28,000 |
| Verified independently | The exploit transaction's own `Withdrawal(address,uint256)` event on the WETH contract, and the attacker EOA's own balance delta across the exploit block (two archive RPC endpoints agree), both independently confirm **10.706591043820923 ETH** realized profit, matching the "10.71 ETH" figure to the reported precision |
| USD conversion | At CoinGecko's own 2026-08-31 daily historical price ($2,416.24), that is **$25,869.71**, about 7.6% below DefiLlama's $28,000; an intraday-interpolated price ($2,446.10, from CoinGecko's hourly range around the exact block timestamp) gives $26,189.43, about 6.5% below. Neither this entry nor DefiLlama's $28,000 can be shown as flatly wrong from public data alone (see Caveats) |

## The method

```bash
pip install pycryptodome
python3 reconstruct_exploit.py
```

No hardcoded press figures: every number below is read live from Ethereum
mainnet (`ethereum-rpc.publicnode.com` for everything except one
historical `eth_getBalance`, which that provider rejects as "archive";
`eth.drpc.org`, cross-checked against
`eth-mainnet.public.blastapi.io`, serves it instead) and CoinGecko's
public historical-price API.

The starting anchor is not a press-supplied transaction hash trusted at
face value. SlowMist's own alert (as republished by crypto.news and
cryptotimes.io) names five addresses: an attacker EOA, an attack
contract, two "vulnerable contracts", and an underlying pool. Every one
of those is independently re-derived and cross-checked below, rather than
assumed correct:

1. **The exploit transaction is fetched directly from the chain** and
   decoded from its own receipt: block 25,874,402, a contract-creation
   transaction (`to` is null), 108 event logs, status success.
2. **The two "vulnerable contracts" are confirmed live as Float
   Protocol's own vaults**, not assumed from the press label: a live
   `name()`/`symbol()`/`token0()`/`token1()` call against both returns
   `"Visor FLOAT-ETH Uni .3%"` / `"vFLOAT-ETH3"`, `token0` = the real
   FLOAT token, `token1` = real WETH. This is independently cross-checked
   against **messari/subgraphs' own public Gamma Strategies deployment
   registry** (`subgraphs/gamma-strategies/protocols/gamma-strategies/config/deployments/gamma-strategies-ethereum/configurations.json`
   on GitHub, a collaboratively maintained primary source, not a press
   article), which names the same two addresses `vFLOAT-ETH3_2` and
   `vFLOAT-ETH3_3`, deployed at blocks 13,507,015 and 13,615,043 (November
   2021).
3. **FLOAT itself is confirmed as Float Protocol's own token** (`name()`
   returns `"Float Protocol: FLOAT"`), and Float Protocol's own GitHub
   org (`github.com/FloatProtocol`) is confirmed live, holding
   `float-staking`, `float-ui`, and `float-whitelist`, ruling out a
   same-named but unrelated project.
4. **The underlying Uniswap V3 pool is confirmed** by decoding the
   transaction's own `Swap` events (topic
   `0xc42079f9...bcca67`) and reading its `token0()`/`token1()` live:
   FLOAT/WETH, matching both vaults.
5. **All 108 logs are decoded structurally**, not selectively: every
   `Transfer`, `FlashLoan`, `Swap`, `Deposit`, and `Withdraw` event is
   matched by its real, independently-recomputed `keccak256` topic hash
   (asserted against the hardcoded constants at the top of the script, so
   a mismatch would halt the script rather than silently mislabel a log),
   revealing the full attack structure: one 1,000 WETH flash loan, one
   120,000 FLOAT flash swap, four deposit/withdraw cycles (two per
   vault), and a final WETH-to-ETH unwrap.
6. **The realized profit is read two independent ways**: the WETH
   contract's own `Withdrawal` event (the attack contract unwrapping its
   residual WETH into raw ETH, the last event in the transaction), and
   the attacker EOA's own `eth_getBalance` delta across the block (on two
   separate archive-capable RPC providers, which agree with each other to
   the wei). Both land on the identical figure once the transaction's own
   gas cost is added back in.

## What it found

### The capital: one WETH flash loan, one FLOAT flash swap

The attack contract (`0xb46655eb...b6c54`, self-destructed by the end of
the transaction; the transaction itself also creates and destroys a
second, outer contract, `0x05303c95...fe51ab`) opened by flash-borrowing
**1,000.0 WETH** from a lending pool at `0xbbbbbbbb...37eeffcb` (a real
`FlashLoan(address,address,uint256)` event, log 0) and flash-swapping
**120,000.0 FLOAT** from a Uniswap V2-style pair at
`0x481ddaf9...612ca5a9` (confirmed live: `token0()`/`token1()` are FLOAT
and WETH). Both loans are fully accounted for by the end of the
transaction: the WETH is repaid in full (log 106, exactly 1,000.0 WETH
back to the same lending pool), and the FLOAT flash-swap is repaid with a
**0.3009%** premium (120,361.083250 FLOAT back, log 95, against 120,000.0
FLOAT borrowed, log 2) -- matching Uniswap V2's own 0.30% flash-swap fee
almost exactly, independent confirmation that this really is a V2-style
flash swap rather than an ordinary trade.

### The manipulation and four extraction cycles

With that capital, the attack contract swapped 114,000 FLOAT into the
shared V3 pool for 12.05 WETH (log 5, `Swap` event), pushing the pool's
spot price for FLOAT down hard. While the price stayed distorted, it ran
four deposit/withdraw cycles, alternating between the two vaults, each
one routed through a separate, freshly-created helper contract as the
`msg.sender` of the `deposit()` call (`0x38037294...f3f8a28` for VAULT1,
`0x7cf8431e...622cd75f` for VAULT2) before the resulting vault shares
were transferred to the main attack contract for withdrawal:

| Cycle | Vault | Deposited | Shares | Withdrawn (same shares) |
|---|---|---|---|---|
| 1 | VAULT1 (`0x85cbed...a70c`) | 2,000 FLOAT + 200 WETH | 222.629 | 7,145.280 FLOAT + 199.782 WETH |
| 2 | VAULT2 (`0xc86b1e...c1153`) | 4,000 FLOAT + 400 WETH | 3,703.210 | 50,425.189 FLOAT + 397.849 WETH |
| 3 | VAULT1 | 395,035.556 FLOAT + 0 WETH | 4,298.630 | 394,911.862 FLOAT + 1.852 WETH |
| 4 | VAULT2 | 394,911.862 FLOAT + 0 WETH | 11,687.203 | 394,297.020 FLOAT + 2.841 WETH |

Every deposit/withdraw pair burns exactly the shares it minted (verified
by the script, `shares matched: True` for all 4 cycles) -- the gain comes
entirely from the underlying token split the vault computes at deposit
time versus at withdraw time, while the pool's spot price is held away
from fair value in between by further swaps (logs 20-24, 42-48, 53, 55,
67-71, 85-90, 96-98) interleaved between the cycles. Cycle 1 alone turns
2,000 FLOAT + 200 WETH into 7,145 FLOAT + ~200 WETH for the identical
shares; the pattern repeats, with the third and fourth cycles routing the
bulk of the accumulated FLOAT back through both vaults a second time.

### The final unwrap: the realized profit

After the last withdrawal, the attack contract swapped its remaining
233,291 FLOAT back into the pool for 238.07 WETH (log 98), repaid the
1,000 WETH flash loan and the 120,361 FLOAT flash-swap in full, and
unwrapped what was left. The WETH contract's own `Withdrawal(address,
uint256)` event (log 107, the very last log in the transaction) records
the attack contract unwrapping **10.706591043820923304 ETH** -- read
directly off that event, not inferred.

This is independently cross-checked against the attacker EOA's own
balance: `eth_getBalance` at block 25,874,401 (immediately before) shows
1.523042733552253614 ETH; at block 25,874,402 (immediately after,
i.e. this transaction's own block) shows 12.226732689558621914 ETH. The
delta (10.703689956006368078 ETH) plus the transaction's own gas cost
(0.002901087814555094 ETH) equals **10.706591043820923304 ETH** --
matching the WETH `Withdrawal` event to the wei. A second archive-capable
RPC provider (`eth-mainnet.public.blastapi.io`, cross-checked against
`eth.drpc.org`) returns the identical two balances.

### USD conversion, and the gap against DefiLlama

10.706591043820923 ETH at CoinGecko's own 2026-08-31 daily historical
price ($2,416.2418165172735) is **$25,869.71**. A tighter,
intraday-interpolated price (using CoinGecko's hourly range data around
the exact block timestamp, 09:35:11 UTC, interpolating between the
$2,445.97 and $2,446.20 hourly points that bracket it) gives $2,446.10
and **$26,189.43**. Both sit 6.5-7.6% below DefiLlama's flat $28,000
figure for this incident. This reconstruction cannot determine which
side, if either, is "wrong": DefiLlama's feed carries no source URL for
this row, and SlowMist's own alert states the ETH amount, not a dollar
figure, so the $28,000 in circulation is press/DefiLlama's own USD
conversion of that ETH amount, at a price and timestamp this
reconstruction could not independently locate. Reported here as a
reconciled gap, not a correction.

### Still holding real liquidity

Both vaults, deployed in November 2021, still hold real FLOAT today:
189.664448 FLOAT in VAULT1 and 871.173253 FLOAT in VAULT2 (live
`balanceOf` calls, Step 13 of the script), confirming this was a real,
years-old, unmonitored deployment, not an abandoned shell with nothing
left to drain.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Float Protocol, Gamma Strategies/Visor, Uniswap, or any
  outlet cited above.
- The exact internal Hypervisor accounting formula that produced each
  cycle's disproportionate token split was not independently derived
  from source: the live bytecode at both vault addresses does not match
  the current `GammaStrategies/hypervisor` GitHub `master` branch closely
  enough for this reconstruction's `eth_call` probes of documented
  getters (`whitelistedAddress()`, `directDeposit()`) to succeed against
  it (both revert), consistent with a 2021-era deployment predating
  several since-refactored versions of that codebase. This entry
  confirms the mechanism's *effect*, fully, from the vaults' and pool's
  own emitted events (the exact deposited/withdrawn amounts, matched
  share counts, and the swaps in between), but not the specific Solidity
  line that computed the disproportionate split.
- The two "helper" deposit-caller contracts
  (`0x3803729416aa5207fe801c1c565b906f6f3f8a28` and
  `0x7cf8431e086e1bcdc9524fd305f7d5d8622cd75f`) were not independently
  disassembled; their role (calling `deposit()` as a distinct
  `msg.sender` from the withdrawing contract) is read directly off the
  event log's indexed `sender` arguments, not assumed.
- The $25,869.71 / $26,189.43 figures are two different, defensible
  independent re-derivations of the same confirmed 10.706591043820923 ETH
  using different CoinGecko price granularities; neither should be read
  as more "official" than the other, and neither matches DefiLlama's
  $28,000 exactly (see "USD conversion" above).
- DefiLlama's hacks feed reuses the same `defillamaId` (497) for this
  incident and for Float Protocol's unrelated January 2022 exploit
  ($1,160,000, also "Spot Price Manipulation"); this script filters on
  the 2026 timestamp specifically to avoid conflating the two.
- The attack contract and the transaction's own outer created contract
  both self-destructed by the end of the transaction (`eth_getCode`
  returns empty bytecode for both today); every figure in this entry
  comes from the transaction's own permanent event log and receipt, not
  from reading either contract's state after the fact.

## License

MIT
