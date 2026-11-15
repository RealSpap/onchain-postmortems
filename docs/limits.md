# Limits, disclaimer and license

Back to the [README](../README.md).

## Limits

- Independent research, not a security audit; not affiliated with any
  protocol, auditor, or outlet cited in a subfolder.
- Every dollar figure in [the Index](../INDEX.md) is taken from each
  subfolder's own source files (its README, its script's raw output in
  `resultats_*.txt`, or its `registre_hypotheses.csv`), never carried over
  from an old summary unchecked. Figures marked † come from the
  protocol's own post-mortem, press or DefiLlama and are not
  independently recomputed; each footnote names the source.
- 18 entries report a dollar figure that is a known floor, not a complete
  total. Read the linked subfolder for the full accounting in native
  units.

| Protocol | Why it's a floor | Link |
|---|---|---|
| Bitget hot wallet drain (Ethereum leg) | Ethereum leg only; XRPL, Tron and a probable Zcash leg not reconstructed | [bitget-hot-wallet-spoofed-withdrawals/](../incidents/bitget-hot-wallet-spoofed-withdrawals/) |
| Duelbits hot wallet drain (Ethereum leg) | Ethereum leg only; BNB Chain, Tron and Bitcoin legs not reconstructed | [duelbits-hot-wallet-drain/](../incidents/duelbits-hot-wallet-drain/) |
| Limit Break Payment Processor V2 | Drains observed until the end of the window (2026-09-28); WILD and APE not priced | [limit-break-payment-processor-forwarder-spoof/](../incidents/limit-break-payment-processor-forwarder-spoof/) |
| Symbiosis | Prices only the realized cash-out; syBTC float unresolved | [symbiosis-sybtc-mpc-signed-mint/](../incidents/symbiosis-sybtc-mpc-signed-mint/) |
| Liquid Network | Some smaller destination addresses left untraced | [liquid-rangeproof-cache/](../incidents/liquid-rangeproof-cache/) |
| XRP Healthcare (XRPH Wallet) | Covers 3,630 of 4,011 wallets XRP Healthcare counted | [xrph-wallet-key-compromise/](../incidents/xrph-wallet-key-compromise/) |
| Sandbox | Wider scope found than press; not all converted to dollars | [sandbox-oft-delegate-hijack/](../incidents/sandbox-oft-delegate-hijack/) |
| Balancer V1 (legacy pools) | Same: wider scope than press, not fully priced | [balancer-v1-rounding/](../incidents/balancer-v1-rounding/) |
| Maya Protocol (MAYAChain) | Unconverted CACAO balance in attacker's wallet, no rate | [mayachain-cacao-slash-drain/](../incidents/mayachain-cacao-slash-drain/) |
| Coinsbuy | Tron leg full; only one Ethereum tx attributable | [coinsbuy-wallet-drain/](../incidents/coinsbuy-wallet-drain/) |
| Cosmos EVM (MANTRA / TAC / KiiChain) | Source itself withholds 3 of the 6 chains hit | [cosmos-evm-vesting-underflow/](../incidents/cosmos-evm-vesting-underflow/) |
| Oraichain (ICS-20 EVM Precompile) | Prices only 2 legs; excludes Injective-bridged/locked ORAI | [oraichain-ics20-precompile-selfmint/](../incidents/oraichain-ics20-precompile-selfmint/) |
| COLDCARD (Weak Seed RNG) | Only 1st of 4 theft waves traced, about a third | [coldcard-rng-seed-theft/](../incidents/coldcard-rng-seed-theft/) |
| Verus-Ethereum Bridge | 2nd exploit (2026-07-23, $7,530,000 per DefiLlama) not priced | [verus-ethereum-bridge-forged-proof/](../incidents/verus-ethereum-bridge-forged-proof/) |
| UNCX Vesting V2 (Ethereum leg) | Ethereum leg only; Base, BNB Chain and Robinhood Chain legs not reconstructed | [uncx-vesting-v2-share-accounting/](../incidents/uncx-vesting-v2-share-accounting/) |
| EtherVista | Only the WETH leg is valued; the 43,855.9 VISTA taken at the same time are not | [ethervista-pair-k-check-uint112-overflow/](../incidents/ethervista-pair-k-check-uint112-overflow/) |
| Enjin | Counted on the first transaction only; the ENJ taken by 594 later transactions ($34,643) is not counted; neither Enjin's contracts nor its report were read | [enjin-legacy-erc1155-adapter-melt/](../incidents/enjin-legacy-erc1155-adapter-melt/) |
| NEAR Intents (Omni MetaWallet, BNB Chain) | The seven withdrawals of one account only; why the signer signed, other accounts and other tokens were not examined; funds not traced beyond five addresses | [near-intents-omni-metawallet-signed-withdrawals/](../incidents/near-intents-omni-metawallet-signed-withdrawals/) |

- Counting rule: funds returned by the attacker or reversed on-chain are
  deducted, so Liquid Network, Tectonic, Oraichain, the Safe LP Module and UNCX
  Vesting V2 report the unrecovered figure, and Moonwell its uncovered debt, not the
  higher gross amount (each footnote gives both readings).
  Reimbursements a protocol paid from its own reserves are not deducted.
- `tectonic-cronos/`'s script reads the chain's current state
  (`tectonic_risk_snapshot.py`), not a replay of the incident (the
  rollback erased the attack blocks), and its loss figures ($120.4M
  borrowed, $9.19M unrecovered) are sourced from Cronos's official
  post-mortem, not recomputed. Flagged here rather than hidden.
- The "Category" column in the Index is this project's own classification
  of an already-described mechanism, for scanning convenience, not a
  label sourced from DefiLlama, press, or the protocol itself. Several
  incidents plausibly fit more than one tag; each row carries the single
  tag judged most useful for finding it, the "Type/Mechanism" column next
  to it carries the actual nuance.

## Disclaimer

Every entry in this repo is an independent, factual reconstruction of
publicly available on-chain data (transaction receipts, decoded logs,
contract reads) as of the date noted per entry (for tectonic-cronos, part of
the attack sequence rests on Cronos's report and Certora's analysis, as its
README says), not a security audit,
and not affiliated with, commissioned by, or endorsed by any protocol,
auditor, or outlet named in a subfolder.

- **No claim beyond the data.** Who sent, received, or drained funds is
  based solely on on-chain records and publicly disclosed information
  cited inline; no claim of wrongdoing beyond what that data shows is
  made or implied against any named address or entity.
- **Not advice.** Nothing in this repo is legal, financial, or investment
  advice.
- **A snapshot, not a live feed.** Balances, labels, and follow-up
  transactions can and do change after publication; entries are not
  updated automatically to reflect such changes.
- **Corrections welcome.** Any individual or entity named who believes a
  fact about them is inaccurate is invited to get in touch, privately if
  they prefer (see [SECURITY.md](../SECURITY.md)), with supporting evidence
  for a prompt, public correction.

Readers should independently verify all cited addresses, transactions,
and figures before relying on them.

## License

MIT. See `LICENSE`. Deliberately open, including every reconstruction
script: each is wired to one already-public historical incident, so
anyone can rerun the same query against the same public chain data and
get the same number, which is what makes the corrections to press and
DefiLlama in this repo checkable rather than just asserted.
