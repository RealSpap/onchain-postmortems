# Reddio (RedSonic Vault) Postmortem

Independent reconstruction of a share-registration exploit on Reddio's
RedSonic Vault (rsvETH), a Diamond-proxy (EIP-2535) staking vault on
Ethereum mainnet. An attacker flash-loaned 1,139.6 WETH, then immediately
called an unprivileged function to register Lido's stETH as a second,
brand-new share class inside the vault, before ever depositing anything
into the vault's existing rsvETH product. Only after that registration
did the attacker deposit ~1,130 ETH to mint almost all of the vault's
rsvETH shares; redeeming that same position moments later paid out about
9.25 ETH more than it was ever deposited for. That single unprivileged
call, made from a plain, freshly created contract with no special role on
the vault, is what let the redemption pay out more than it was worth,
netting roughly $22,700 before repaying the flash loan. This
reconstruction starts from Reddio's own official documentation (not a
press address), decodes the exploit transaction's own calldata and event
log directly, and confirms live, today, that the exploited function
still has no caller restriction.

## At a glance

| | |
|---|---|
| Incident | Permissionless `registerErc20(address)` on the RedSonic Vault's Diamond proxy let an unprivileged caller register a second share class (stETH-backed `rsvstETH`) drawing on the same pooled collateral as the existing rsvETH shares |
| Window | 2026-09-05 16:03:11 UTC, one transaction, one block (25,912,201) |
| Press/DefiLlama figure | DefiLlama: "Reddio RedSonic", $22,800, Ethereum, classification "Token & Share Accounting" / technique "Incorrect Share Accounting", dated 2026-09-05 (no source URL attached in the feed). Press (via ExVulSec's analysis, republished by several outlets) describes "9.25 ETH" net profit from a flash-loan attack exploiting a "permissionless" `registerErc20` function |
| Verified independently | The attacker's own Ethereum address, whose nonce was 0 before this transaction (its first ever), held exactly 9.261768945208 ETH the moment the block closed. At CoinGecko's own 2026-09-05 historical price, that is **$22,747.69**, within 0.23% of DefiLlama's figure |
| Confirmed live, today | A read-only simulation of `registerErc20(WETH)` from an arbitrary, unprivileged address still succeeds against the real, currently-deployed vault; the same call against an already-registered asset (stETH) correctly reverts with `"Vaults: vToken already registered"`, proving the function is real, live, and still has no caller check |

## The method

```bash
pip install eth_abi pycryptodome
python3 reconstruct_exploit.py
```

No hardcoded press figures: every number below is read live from Ethereum
mainnet (`ethereum-rpc.publicnode.com` for everything except one
historical `eth_getBalance`, which that provider rejects as "archive" and
`1rpc.io/eth` serves instead) and CoinGecko's public historical-price API.

The starting anchor is not a press-supplied address. DefiLlama's own
hacks feed (`api.llama.fi/hacks`) surfaces the incident by name ("Reddio
RedSonic", $22,800, no source URL); Reddio's own official documentation
(`docs.reddio.com/zkevm/staking`) independently names
`0x4315990D9eeAFFdFAfD49958b4851F203FA1126f` as the "Deposit Smart
Contract" behind rsvETH/rsvUSDT, and `0xCA9de1F80Df74331c5fcb7Eee2D05E7
46d47BFb2` as rsvETH itself, before any transaction hash is looked up.
The exploit transaction hash was then located from security-firm
write-ups (ExVulSec's analysis, as republished by coin-turk.com and
others) and independently re-derived from there on: fetched directly from
the chain, decoded log by log, and cross-checked against a live Diamond
Loupe (`facets()`) call and two live `eth_call` simulations against the
vault's real, currently-deployed bytecode, none of which any press
write-up could have supplied.

1. **The vault is a Diamond proxy (EIP-2535)**, not a single monolithic
   contract. A live `facets()` call lists 7 facets, one of them
   unverified on Blockscout, which is exactly the facet whose selector
   list includes `0xa4a3c9ef`, i.e. `keccak256("registerErc20(address)")`
   computed independently and matched against the facet's own live
   selector list, not assumed from the function's name in a press quote.
2. **The exploit's own raw creation bytecode contains that exact
   selector**, immediately followed in the same contiguous byte window by
   Lido stETH's own mainnet address, and by the vault's own address (the
   call's target) -- decoded directly from `tx.input`, not from a
   decompiler or a third-party trace API.
3. **The vault's own emitted event (not a guess about function names)
   confirms the registration.** Log index 4 in the exploit transaction's
   receipt is emitted by the vault itself, with two indexed (ABI-safe,
   not offset-guessed) topics: the asset registered
   (`0xae7ab96520De3A18E5e111B5EaAb095312D7fe84`, Lido's real stETH
   contract) and the new share token created
   (`0xf65e1ec6093642Ba9D439aC25AF1b767054e1558`).
4. **That new token's own live state is queried directly**: `name()`
   returns "RedSonic Vault Liquid staked Ether 2.0", `symbol()` returns
   "rsvstETH", `owner()` returns the vault's own address, and
   `totalSupply()` today is exactly 0.
5. **The caller had no privilege on the vault.** A live `owner()` call on
   the vault's OwnershipFacet returns `0x3786540Ec316f2383FAb2d5Cfc816C1A
   BDfEEf44`; the address that actually drove the exploit (the contract
   that unwrapped the flash-loaned WETH and called `registerErc20`,
   `0x39a2Aee44bd9eF106917D94880a9f8F7CfAf09d5`) is not that address.
6. **The realized profit is read off the attacker's own balance, not
   assumed from a press figure.** The attacker's EOA
   (`0x70f2333d21Ed7E7D105F6578227A9A747687982C`) sent this transaction at
   nonce 0, its first ever; a live `eth_getBalance` at the exploit block
   shows it holding 9.261768945208 ETH immediately afterward.
7. **The exploited function's current state is checked live, today**,
   with two read-only `eth_call` simulations (nothing broadcast, no
   mainnet state touched): registering a genuine, not-yet-registered
   ERC20 (WETH) from an arbitrary unprivileged address still succeeds;
   registering an already-registered one (stETH) correctly reverts with
   the facet's own real error string.

## What it found

### The flash loan, and the registration -- before any real deposit

The attacker's contract (`0x39a2...f09d5`) flash-loaned
**1,139.615952950658083864 WETH** from Balancer's Vault
(`0xBA12222222228d8Ba445958a75a0704d566BF2C8`) and unwrapped essentially
all of it to native ETH (a standard WETH `Withdrawal` event for the same
amount). The very next thing it did, before depositing a single wei into
the vault's existing rsvETH product, was call `registerErc20(address)`
(selector `0xa4a3c9ef`) directly on the vault, naming Lido's real stETH
contract as the argument. The vault's own emitted events confirm this
succeeded and in what order: a brand-new ERC20, **rsvstETH** ("RedSonic
Vault Liquid staked Ether 2.0"), was deployed at `0xf65e1ec6...4e1558`
with its ownership immediately transferred to the vault
(`OwnershipTransferred`, `0x0` to the vault); the vault's own next event
(log index 3, data = the new token's own address) records that token as
created, and the one after that (log index 4, two ABI-indexed topics)
records the pairing: asset `0xae7ab96520De3A18E5e111B5EaAb095312D7fe84`
(stETH) to share token `0xf65e1ec6...4e1558`. Nothing about the calling
contract required any role, allowance, or prior relationship with the
vault; it is a plain contract, freshly created in the same transaction,
with no elevated privilege confirmed against the vault's own `owner()`.

### The real deposit, made into an already-corrupted vault

Only after the new share class existed did the attacker's contract
deposit ETH into the vault's ordinary rsvETH product: the vault's own
`Deposited`-shaped event (log index 6, indexed depositor = the attacker's
contract) records **1,130.259297504314263299 ETH** deposited, minting
**1,118.002170814811506716 rsvETH** (`0xCA9de1...47BFb2`, mint from
`0x0`) in the same call. Considered alone this looks like an ordinary
deposit; it is the vault's own combined share-price math, already
carrying the freshly registered but still-empty stETH share class, that
this deposit is made against.

### Seeding the new share class, then cashing both out

The attacker's contract then staked a small amount of ETH into Lido
directly (a fresh stETH mint, `Transfer` from `0x0`,
9.356655446343745908 stETH), approved the vault for it, and deposited
**9.336655446343746334 stETH** into the newly registered share class
(the vault's own `Deposited`-shaped event, log index 14, indexed asset =
stETH, records the same amount against the attacker's address), minting
the same amount of rsvstETH 1:1. It then, in the same transaction:

- Burned the *entire* 1,118.002170814811506716 rsvETH position (the exact
  amount minted above) and the vault's own `Withdrawn`-shaped event (log
  index 16, indexed withdrawer = the attacker's contract) records
  **1,139.513928645387002525 ETH** paid out for it -- **9.254631141072739
  ETH more than the 1,130.259297504314263299 ETH that position was ever
  deposited for**, decoded directly from the vault's own two events for
  the same position, not inferred. This is the exploit's core mechanism,
  isolated to the cent (well, the attogram): the freshly registered,
  still-tiny stETH share class let the pre-existing rsvETH share class be
  redeemed for value it never actually held.
- Burned the rsvstETH position too, and the vault's own matching
  `Withdrawn`-shaped event (log index 20, indexed asset = stETH) records
  9.336655446343746250 stETH paid back out -- the same amount deposited,
  confirming the stETH side of the position broke exactly even; none of
  the 9.25 ETH gain above came at the direct expense of the stETH the
  attacker put in.

### Unwinding and repaying

The attacker's contract swapped the reclaimed stETH back to ETH through a
real Curve stETH/ETH pool (`0xDC24316b9AE028F1497c275eB9192A3eA0F67022`,
confirmed live: `coins(0)` is the native-ETH placeholder address,
`coins(1)` is Lido's real stETH contract), wrapped the result back to
WETH, and repaid the Balancer flash loan in full
(1,139.615952950658083864 WETH transferred back to the Balancer Vault,
exactly matching the amount borrowed -- Balancer's flash loans carry no
fee, so the entire spread the share-registration bug created was pure
profit).

### The realized profit

The attacker's EOA (`0x70f2333d21Ed7E7D105F6578227A9A747687982C`) sent
this transaction at nonce 0: its first-ever transaction. A live
`eth_getBalance` at the exploit block shows it holding
**9.261768945208000758 ETH** the moment the block closed. Since the
transaction itself paid only 0.00071931438106165 ETH in gas, and this
address had sent nothing before it, this balance is the attacker's
realized take-home profit, give or take at most that gas amount of
pre-funding this reconstruction could not separately net out (see
Caveats). At CoinGecko's own 2026-09-05 historical daily price
($2,456.085066364875), that is **$22,747.69**, within 0.23% of
DefiLlama's own tracked $22,800 for this incident -- a confirmation, not
a correction. That total-realized-profit figure agrees closely with the
9.254631141072739 ETH the vault's own `Deposited`/`Withdrawn` events show
being extracted from the rsvETH position alone (above); the small
~0.0071 ETH gap between the two is consistent with the leftover
9.356655446343745908 − 9.336655446343746334 ≈ 0.02 stETH the attacker
staked but did not deposit into the new share class, also swapped out via
Curve.

### Still live today

A read-only `eth_call` simulation (nothing broadcast; no mainnet state
touched) of `registerErc20(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2)`
(real WETH, not yet registered on this vault) from a completely arbitrary
address (`0x1111...1111`, holding no role or balance on the vault)
succeeds without reverting against the vault's actual, currently-deployed
bytecode. The same call against stETH, already registered, correctly
reverts with the facet's own real error string, `"Vaults: vToken already
registered"` -- proving both that the function is genuinely live and
stateful (it is not a dead code path) and that it still carries no
caller restriction, as of this reconstruction's run.

## Caveats

- This is independent research, not a security audit, and is not
  affiliated with Reddio, Balancer, Lido, Curve, or any outlet cited
  above.
- The facet implementing `registerErc20` (`0x92ecC5DEacB14937867686Ca8
  b85dd8a65b74704`) is not verified on Blockscout. This entry confirms
  the function's selector, its live behavior (via the two `eth_call`
  simulations in Step 7), and its actual effect (via the vault's own
  emitted event and the new token's own queried state) independently of
  any source-code read, but cannot independently confirm every internal
  accounting detail of *why* the combined share-price math breaks, beyond
  what the balanced stETH in/out and the rsvETH burn/mint the event log
  itself shows.
- The exact address that deployed the top-level exploit contract from the
  attacker's EOA, versus the nested contract
  (`0x39a2aee44bd9ef106917d94880a9f8f7cfaf09d5`) that actually executed
  the flash loan and the vault calls, was not independently disambiguated
  beyond confirming the latter is not the vault's owner; the transaction
  is a single, atomic contract-creation call and both addresses belong to
  the same attacker.
- The $22,747.69 realized-profit figure equals the attacker EOA's full
  balance immediately after the exploit block, which slightly overstates
  the true profit by whatever amount, if any, funded that address's gas
  before this, its first transaction. That amount is bounded above by the
  0.00071931438106165 ETH the transaction itself paid in gas (about $1.77
  at the same price), and this reconstruction could not query the
  address's exact pre-transaction balance because every public archive
  RPC endpoint tried for the one block immediately prior either required
  a paid API key or reported the state as unavailable.
- DefiLlama dates this incident 2026-09-05T00:00:00Z (midnight UTC); the
  actual exploit transaction's own block timestamp is 16:03:11 UTC the
  same calendar day, not a cross-day discrepancy like some other entries
  in this repo, just less precise.
- Step 7's live `registerErc20` simulations are read-only `eth_call`s;
  nothing was broadcast to mainnet, and no state was changed by running
  this reconstruction. Whether Reddio has since been notified or has a
  fix in progress was not determined; this entry reports only what the
  live bytecode does today, at the time it was run (2026-09-11).

## License

MIT
