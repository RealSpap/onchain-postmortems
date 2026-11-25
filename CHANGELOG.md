# Changelog

Additions and corrections to this repository, most recent first. Each
incident's own README carries the full detail and supersedes any earlier
wording; this file is a short log. New incidents are also announced as
GitHub releases.

## 2026-11-25

- BonfireSwap: the README said twice that the attacker's EOA had sent nothing since the exploit ("has sent none since" in the table row of the attacker, "has sent nothing since" in the paragraph on the attack contract). That was true when I read it on 2026-10-22; on BSC (chain ID 56) the EOA sent one transaction of 0 BNB on 2026-11-02 at 02:51:13 UTC (block 131164020, nonce 10, no code at the recipient, a 220-byte plain-text message as input), and its nonce was 11 when I read it at 19:05Z on 2026-11-25 on three nodes. The README says so now in both places, hypothesis H20 of the registry reads the nonce at block 131164019 and a new H20b names the transaction, and the script reads the nonce at that block instead of the latest block. The output of the run is in `incidents/bonfireswap-router-arbitrary-from-forced-sell/preuves/resultats_reconstruction_2026-11-25.txt`. No figure changes.
- NEAR Intents: the owner of the wallet contract changed `verifyAddress` on 2026-10-23 (BNB Chain, chain ID 56, block 129297067, 09:22:00 UTC, transaction `0xb6f4cd2a6a60505de21dfb71ccab8e1d55fd966cf28a8ac82d17b6c8a61655a1`): `0xbcfd8381fa8148d01fd7d5cbb0efcc96ce68176c` at block 125050000, `0xa53fe80c49fc9e3f96c632b3909601681807b7c7` at block 135707822, as read at 19:06Z on 2026-11-25. My script read the contract at the latest block, so its checks H1 and H4 failed when I ran it again on 2026-11-25 although the entry's facts had not changed, and the registry rows H1 and H4 named the old signer without a block. The script reads the contract at block 125050000 now, a new check H9 reads the change itself, the account's nonce (H2) is read at the block of its last transaction, and the registry names the blocks. The run is in `incidents/near-intents-omni-metawallet-signed-withdrawals/preuves/resultats_reconstruction_2026-11-25.txt`: 10 of 10 checks pass. No figure changes.

## 2026-11-19

- Enjin: the opening paragraph of the entry gave $175,442 for the ENJ that reached the attacker without saying that the loss counted in the Index is the first transaction's $140,799. It now gives both and says which one is counted. I had described the price as the price "at the block time"; it is the point DefiLlama returns for the time of the first transaction, dated 2026-08-25 18:51:50 UTC, 591 seconds after the transaction. The README, the Index note and the data files say so now. The closing sentence of the Index note is replaced by what I read: none of the 47 holders had approved the attacker's contract through `isApprovedForAll`, and DefiLlama's listing describes the cause as a storage-slot collision and gives no source. I ran the entry's script again on 2026-11-19 (read at 19:06Z): every check passes (the output is in `incidents/enjin-legacy-erc1155-adapter-melt/preuves/resultats_reconstruction_2026-11-19.txt`). No figure changes.
- Sandbox: the README had no reading of the hijacked delegate after 2026-09-09. I ran the script again on 2026-11-16 and on 2026-11-19 (read at 19:05Z), and the README has a section with the result: the Base delegate was reset on 2026-09-18 by a new `approveAndCall` of the kind that started the incident, the BSC delegate did not change, neither is the owner, one SAND was burned on 2026-09-12, and the consolidation wallet sent 196.6 ETH on 2026-09-11. The decimals of the phantom supply that I had printed in the README (.6875 and .96875) were floating-point artefacts; the README is corrected and the script now prints the integer value; the registry rows for the delegate (H2) and the balance (H8) carry the new readings. Step 8 of the script printed a fixed sentence saying the balance matched the bounty offer; it now compares and lists the later transactions. The new runs are in `resultats_reconstruction_2026-11-16.txt` and `resultats_reconstruction_2026-11-19.txt`.
- Index: the month heading marked "(current month)" was the latest month with an incident, not the calendar month. The mark now reads "(latest month)" in the Index, in `add_new_entry.py` and in `check_readme_consistency.py`.

## 2026-11-15

- Reorganised the repository. Every incident folder moved from the root into `incidents/` (history kept, content unchanged) and the scripts moved to `tools/`. INDEX.md, CORRECTIONS.md, CHANGELOG.md, SECURITY.md, CONTRIBUTING.md, CITATION.cff and LICENSE stay at the root.
- A link such as `https://github.com/RealSpap/onchain-postmortems/tree/main/cozy-v2-optimism/` now reads `.../tree/main/incidents/cozy-v2-optimism/`, in the Index, the corrections table, the digests and `data/incidents.json`. Links pinned to a commit are unchanged. Scripts are run from `tools/`, for example `python3 tools/check_readme_consistency.py`.
- The README is now one page. Its sections on falsifiable hypotheses, adding an incident, scope, limits, the disclaimer and the license moved, unchanged, to `docs/method.md` and `docs/limits.md`.
- The README now opens with one question and a sixty-second path: read one incident, replay it, see my own errors, find the incidents that look like your protocol. CORRECTIONS.md opens with my own errors, dated, taken from this changelog.
- Added an index by type of control failure, `docs/by-type.md`, and the matching table in the README. Both are generated by `tools/export_dataset.py` from `data/incidents.json`, with the date of the latest incident they cover, and checked in CI. Added `tools/find_incidents.py` to filter the incidents by type, chain or text.
- CONTRIBUTING.md lists five first tasks, and two issue forms were added: "A figure is wrong" and "Suggest an incident".
- Each old incident folder and script path at the root now holds a short redirect (a README.md that links to the new folder, or a short stub that runs the script from `tools/`), so a link or a command published before this date still lands somewhere. They are listed in `tools/structure.json`, capped there, and do not count towards the root ceiling.
- Added `tools/check_structure.py`, run in CI with its own tests. It refuses a file or folder at the root that `tools/structure.json` does not list, an incident folder outside `incidents/`, any file that fits none of the paths listed there (a hand-over or work file included), a symbolic link, and more than 14 visible entries at the root.

## 2026-11-02

- Added the October 2026 digest.
- The ERC-8107 coordinator tests now live only in the authority-risk-oracle showcase (research/erc-8107-coordinator-tests there); this repository no longer carries the folder and is MIT throughout.
- README: the author line described the multisig-overlap showcase with the defi-admin-key-risk showcase's subject; it now reads "signers shared between protocols" for multisig-overlap and "single-key admin cases" for defi-admin-key-risk.
- SECURITY.md now caps the withholding of unfixed-issue detail at 90 days from the date of the entry.
- Republished the August and September 2026 digests with the incidents added since their first edition (August: 26 incidents, September: 26), and corrected the two digest lines of the README to match the Index.
- 14 line locators in 7 hypothesis registries pointed one to four lines past the end of the file they cite; each range now stops at the last line (afx-bridge-validator-key-compromise, balancer-v1-rounding, coldcard-rng-seed-theft, etherfi-atomicqueue-eip7702-solver-drain, fetchai-nunet-dual-key-compromise, moonwell-mamo-oracle, symbiosis-sybtc-mpc-signed-mint).
- check_readme_consistency.py accepts "one of N rows in [Corrections" as well as "cases".
- README: the Structure block now lists every top-level file and folder; "one of 38 cases" reads "one of 38 rows", as the Corrections table counts them; the author line names the two other showcases.

## 2026-10-29

- Chainflip: the script now reads the vault's USDT transfers by account from TronGrid, not by windows of logs from a public node that no longer serves the vault's history. The new run is in `preuves/`, and its README says what was and was not compared with the old logs. The Index and the dataset are unchanged.
- research/erc-8107-coordinator-tests: a new folder that is not an incident entry (no row in the Index, no change to any count). Executable tests of a coordinator for ERC-8107 on a fork of Ethereum mainnet, with the raw output of the run: two ENS names that resolve to the same address, and one complete coordinator whose every step is switched off in turn. The folder has since moved to the authority-risk-oracle showcase; this repository keeps a four-line pointer and is MIT throughout.
- Added CashCowCoin (BSC, 2026-08-27).
- Added FH Token (BSC, 2026-08-25).
- Added Arrakis V1 G-UNI ENS/WETH vault (Ethereum, 2026-08-23).
- Added USM (Ethereum, 2026-08-09).
- Added Unistreet LaunchpadFactoryAuto (Ethereum, 2026-08-06).
- Added MOKE MokeRelease (BSC, 2026-08-02).
- Added LULA (BSC, 2026-07-28).
- Added Truebit purchase contract (Ethereum, 2026-01-08).

## 2026-10-23

- Text fixes after review: the opening line of the README no longer calls `tectonic_risk_snapshot.py` the only script of tectonic-cronos (`verifier_blocs.py` was added the same day), and with the headline, the At a glance row and the August digest it now says that the rollback is per Cronos's report. The Corrections count now says 38 rows for 36 entries (Tectonic and Ostium have two rows each) and that 3 of the rows correct this repository's own earlier text, where it said 38 entries; the Ostium row no longer says Ostium settled on $23,752,746. In the Coinsbuy README the swap address is said to have sent 551 ETH to the collector, not to have received them, and the three figures of the article are no longer written as one sum; its registry no longer says "to the cent" of a whole-number press figure. Printed lines were edited by hand, without replaying the script, in the recorded outputs dated 2026-09-11 (Coinsbuy, one line) and 2026-09-10 (Ostium, two lines), to match the changed print statements of those scripts. No figure changed.
- README and the August digest: "each reconstructed from raw chain data" (the headline), "each reconstructed on-chain" (the At a glance row) and the digest's "each mechanism reconstructed on-chain" and "Every entry's mechanism is reconstructed" were not true of tectonic-cronos, whose chain was rolled back; they now count 63 of 64 (18 of 19 in August) and name the exception. The generator add_new_entry.py writes the new wording. The digest's Tectonic line no longer calls the mechanism "recursive collateral minting then direct donations", which was the wording corrected in the entry on 2026-10-22. No figure changed.
- Ostium: the figure $23,752,746 was written as "Ostium's own final figure". Among the pages read only Odaily (2026-07-19) gives it, as the loss in an Ostium update; The Block and rekt.news give 23.75 million, and Ostium's own post was not read. The wording, the registry (H5, one new row), the script's printed line, the Index note and the Corrections table (one new row, 38 rows, 26 corrections) now say so. No figure changed.
- Tectonic: corrected the block readings. The results file of 2026-09-13 labelled two blocks "90896188 (0x56AB1FC)" and "90907150 (0x56ADCAE)"; the hexadecimal numbers were wrong (0x56AB1FC is block 90878460, 0x56ADCAE is block 90889390), so the hashes and timestamps published (10:07:02 and 11:38:53 UTC) belonged to two other blocks. Read again on three nodes with the hexadecimal computed by a script now in the entry: block 90896188 is timestamped 12:38:52 UTC, four seconds before the 12:38:56 UTC of Cronos's report, and block 90907150 is dated 2026-08-31 05:59:27 UTC, after the restart. The clock conflict with Dune's index that the README drew from the wrong reading is withdrawn, and "both boundary blocks independently re-confirmed live on 2026-09-13" is replaced by the new reading. Corrections table: one row added (37 rows, 25 corrections).

## 2026-10-22

- README: the opening line and the Disclaimer now name tectonic-cronos as the one entry whose attack sequence is not rebuilt from the chain (the chain was rolled back past it); every other entry has a reconstruction script. No figure changed.
- Ostium: a compromised signer key was written as a fact. Ostium's statement of 2026-07-18 (as rekt.news quotes it) says compromised off-chain infrastructure, its post-mortem (as The Block reports it) says unauthorized access to its off-chain infrastructure, and Halborn says, reportedly, a compromised oracle private key; none says which credential was used, and Ostium's own posts were not read. README (four places and the sources caveat), registry (H6, one new row), Index row and note, and the script header now say so. No figure changed.
- Full Sail: the 63 deposit and 63 withdraw calls are now stated as successful calls, and the attacker address's failed transactions are listed: inside the attack window (02:33:24 to 05:28:07 UTC) 1 deposit and 2 withdrawals failed at their call; 6 more transactions containing a deposit failed, 4 before the window (from 01:52:14 UTC) and 2 after it; 1 swap ran out of gas. New script `verifier_appels_graphql.py` and its output. No figure changed.
- Tectonic: corrected the attribution of the mechanism. The entry put "recursive minting and direct donations" on Cronos's report, which speaks of manipulated collateral values and TONIC's price pushed up against thin DEX liquidity and does not mention a donation; the direct transfers into tTONIC are in Certora's analysis of 2026-09-22 (its Prover found that a direct transfer raises the exchange rate; its text says the transfers were part of the attack) and the 98-iteration loop is in the timeline section of the same article, which names no source for it. The word "auditor" is gone, and the 147x price move is qualified: 196x against the starting price BlockSec gives. Category unchanged; Corrections table: Tectonic added (36 rows, 24 corrections). No figure changed.
- Coinsbuy: corrected the sentence that explained the gap to the press totals. The unattributed Ethereum-side flow (about $1.06M) cannot close a gap of $1.7M to $1.9M, and the figures in rekt.news's article add up to about $6.6M to $7.3M depending on what is counted, not to its $8.07M. Also: "to the cent" became "a whole number" (rekt.news writes 6,037,005), and the press quote is now the article's own wording. The address 0x66790b54...4b17 is no longer called unlabeled: rekt.news lists it as an attacker-side swap address; what this project could not do is attribute it to Coinsbuy. Corrections table: Coinsbuy added as a reconciliation (35 rows, 9 reconciliations). No figure of the entry changed.
- `check_readme_consistency.py` now also compares the incident count written in the License row and in the line above the largest losses with the Index, so a stale count fails the check.
- Added a replay block at the top of the README, `CONTRIBUTING.md`, and a new `SECURITY.md` and `CITATION.cff` (author name `RealSpap`).
- Added GoldPesa GPXHooks (Base, 2026-10-02).
- Added EtherVista (Ethereum, 2026-10-09).
- Added Enjin (Ethereum, 2026-08-25).
- Added NEAR Intents, Omni MetaWallet on BNB Chain (2026-09-30 and 2026-10-01).
- Added BitBay UsdcDaiV4Vault (Polygon, 2026-10-09).
- Added DoinGud Diamond (Polygon, 2026-09-21).
- Added BonfireSwap router (BSC, 2026-09-15).

## 2026-10-16

- Added UNCX Vesting V2, Ethereum leg (Ethereum, 2026-10-14), counted net of the 82,143,476 X tokens and 8.10335 ETH returned.

## 2026-10-13

- Added MakerDAO ETH-A dormant keeper (Ethereum, 2026-10-06).
- Term Finance: corrected the mechanism. The Delay module's cooldown went from 608,400 s to 0 in the execution block (it did not elapse), the 6 days 1 hour was the vote, and the votes came from a wrapper of the ETH Meta Vault, not from TERM. No figure changed.
- Fetch.ai and NuNet: corrected the cap claim. The NTX token has a cap, exposed as `MAX_SUPPLY()` (1,000,000,000 NTX); the attacker minted the headroom to it. No figure changed.
- Ostium: corrected the description of the 231-byte contract. It had been registered as a forwarder on 2026-05-30, 46 days before the attack; it was not built for the attack. No figure changed.
- Each of the three entries has a `verify_correction_2026-10-13.py` and its output.

## 2026-10-07

- Secured Finance: corrected to $27,860 (was $45,445). JPYC had been priced with the CoinGecko id of an older JPYC contract; CoinGecko maps the drained contract to `jpycoin`. The figure now agrees within 2% with the attacker's own realized proceeds. 2026 total: $921,128,104.

## 2026-10-05

- Added SKYDAO pair drain (BSC, 2026-09-30).
- Bitget: noted that the roughly $318K frozen by Circle and Tether on 2026-09-25 sits on an address outside the Ethereum leg traced here (no figure changed).
- README: incident count in the License row and above the 5 biggest losses brought up to date (55 incidents, 7 months).

## 2026-10-04

- Added FlashLoopAdapter Safe module (Ethereum, 2026-10-01).
- Oraichain: noted Oraichain's statement that about 3.9M unauthorized ORAI were deposited at MEXC and KuCoin (no figure changed).

## 2026-10-01

- Added Duelbits hot wallet drain, Ethereum leg (Ethereum, 2026-09-24).
- Added the September 2026 digest.

## 2026-09-30

- Loss figures now distinguish recomputed from sourced: a new † marker in
  the Index flags dollar figures taken from the protocol's own
  post-mortem, press or DefiLlama and not independently recomputed
  (Drift, Moonwell, Term Finance, Tectonic, Cosmos EVM, Across, Ajna,
  Sandbox, Avici, Balancer V1, Fetch.ai and NuNet, The Internet Token,
  WealthManagementV2). The headline now states both: $917.6M across 52
  incidents, $580.7M of it independently recomputed.
- One counting rule for the Index, written into its legend: funds
  returned by the attacker or reversed on-chain are deducted. Safe LP
  Module now counts the 83.63 rsETH actually kept (≈ $225,762), not the
  $8,006,577 gross drain.
- Tectonic: $9.19M unrecovered, sourced from Cronos's official
  post-mortem (was $8.3M); the dead dashboard link is removed.
- WealthManagementV2: where the USDT held by the attacker's proxy came
  from was not traced, so the Index carries DefiLlama's $26,414 (was
  ≥ $422,251) and the earlier claim that DefiLlama's "Key Compromise"
  classification is contradicted is withdrawn, with its Corrections row.
- ether.fi: priced at the 07:20 UTC oracle point ($38,151, was $38,004);
  7 of the 11 drained wallets are EIP-7702 accounts (was 9).
- Virtue Protocol: $848,190, matching the script output (was $848,457).
- Limit Break Payment Processor V2 marked as a floor, as its own note
  already said.
- Corrections table: BarnBridge SMART Yield added; Allbridge, Liquid
  Network and MORE Markets reclassified as reconciliations; Cosmos EVM,
  BeatSwap, Maya Protocol and Float Protocol rows made more precise. 34
  rows: 23 corrections, 8 reconciliations, 3 discoveries.
- Reddio, Secured Finance, Limit Break, ether.fi and Nimiq: current patch
  status not re-verified; exploitation detail withheld pending disclosure
  to the teams.
- Added SECURITY.md (how to report an error or request a correction).
- The consistency check now also covers the recomputed share, the floor
  count, Index links, and the format of every hypothesis registry.
- Releases are now created only for new incidents, after the consistency
  check passes, at most one per day.
- Added Bitget hot wallet drain, Ethereum leg (Ethereum, 2026-09-24).

## 2026-09-29

- Index and Corrections tables moved out of the README into INDEX.md and
  CORRECTIONS.md.
- Headline figures re-aligned with the Index; the consistency check
  extended to the headline and the Corrections row count.
- Corrections table: Nimiq, Fetch.ai and NuNet, and The Internet Token
  added.
- Added Limit Break Payment Processor V2 forwarder spoof (Ethereum,
  2026-09-25).

## 2026-09-26

- Added Payy Network rollup zero-hash burn (Ethereum, 2026-09-24).

## 2026-09-24

- Added The Internet Token LiquidityUnifier fake-pool mint (Base,
  2026-09-21).
- Added Fetch.ai and NuNet dual key compromise (Ethereum, 2026-09-19).

## 2026-09-21

- Added Nimiq GSN forwarder unsigned execute (Polygon, 2026-09-16).
- Dream Health Chain: day counts updated and live state re-verified.

## 2026-09-20

- Added Safe LP Module unauthenticated executor (Ethereum, 2026-09-15).
- Added Chainflip Tron vault double payout (Tron, 2026-09-12).
- Cozy V2: clarified the "3 distinct source addresses" count.

## 2026-09-19

- BeatSwap: V2 depositors are being repaid after the pause, V1's are
  not; corrects the previous day's note.
- COLDCARD and Coinsbuy re-checked; the COLDCARD attacker's BTC is still
  unmoved.

## 2026-09-18

- Added Flamincome VaultYUSDT share inflation (Ethereum, 2026-09-16).
- BeatSwap: the 2026-09-15 pause recorded. BarnBridge: Blockaid's later
  figure added.

## 2026-09-17

- Added Dream Health Chain award re-claim (BNB Chain, 2026-09-05).
- Zentra Finance: the 2026-09-16 patch recorded. Avici: the scope of the
  sampling estimate clarified.

## 2026-09-16

- AFX Bridge: cites AFX's own 2026-07-31 postmortem (malware on
  validator nodes) next to DefiLlama's "key compromise" label.

## 2026-09-15

- Ajna: the 49.32 WETH extraction is at block 25,854,585, not the block
  cited by press. Balancer V1 re-checked.

## 2026-09-14

- Added BeatSwap vesting slot0 reserve drain (BNB Chain, 2026-09-09).
- Cosmos EVM: MANTRA's $3.6M covers both attacks, not the first alone.

## 2026-09-13

- Added Zentra Finance aToken burn clamp (Citrea, 2026-09-09).
- Monthly digest format, starting with August 2026.
- Fund-flow diagrams added to 8 entries; Tectonic's verification files
  added; older consolidated entries rewritten to the current format.

## 2026-09-12

- Added ether.fi Liquid AtomicQueue (Ethereum, 2026-09-11).

## 2026-09-11

- Added Virtue Protocol, Radix (Hyperlane Warp Routes), Reddio (RedSonic
  Vault), Float Protocol, Coinsbuy, Coreum (XRPL Bridge), Oraichain,
  Secured Finance, Full Sail, Drift Protocol, WealthManagementV2, Weft
  Finance, BarnBridge SMART Yield and Symbiosis.

## 2026-09-10

- Added Cosmos EVM, Allbridge, Liquid Network, Aquifer, Maya Protocol,
  COLDCARD, Gravity Bridge, Avici, MORE Markets, Verus-Ethereum Bridge,
  Across Protocol, Ostium, Nomic, XRP Healthcare, AFX Bridge, Lazy Summer
  and Kelp DAO.
- Index grouped by year and month; consistency check added to CI.

## 2026-09-09

- Eight earlier standalone reports consolidated into this repository:
  Sandbox, Moonwell, Balancer V1, Term Finance, Notional, Ajna, Cozy V2
  and Tectonic.
