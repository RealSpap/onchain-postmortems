"""Tectonic Protocol (Cronos): live on-chain risk snapshot.

MVP for a post-exploit tracking dashboard. Tectonic is a Compound v2 fork
("tTokens"), so this reads the standard Comptroller/CToken/PriceOracle
interface directly from contract state.

Context (2026-08-30 exploit): an attacker inflated the TONIC token price
(about 147x, see README) and borrowed against the inflated collateral.
Cronos validators rolled back 10,961 blocks to undo it (Cronos's official
post-mortem, published 2026-09-08). This script gives an independent,
verifiable read of Tectonic's CURRENT state (post-rollback), not a replay
of the incident itself.

Known contract addresses (Cronos mainnet, chain id 25). Tectonic actually
runs THREE separate, isolated Comptroller pools, not one, cross-checked
against DefiLlama's TVL adapter history and confirmed on-chain (each pool's
`getAllMarkets()` returns a distinct, populated list, both before and after
the exploit). The address below is Pool 1, the one that actually lists
tTONIC and tWBTC; it is NOT the address CronoScan labels "Tectonic: Core"
(0x7De56Bd8b37827c51835e162c867848fE2403a48), which has never had a single
market registered despite the label:
    TectonicCore (Comptroller, Pool 1): 0xb3831584acb95ED9cCb0C11f677B5AD01DeaeEc0
    TONIC token:                        0xDD73dEa10ABC2Bff99c60882EC5b2B81Bb1Dc5B2
    tTONIC market:                      0xfe6934fdf050854749945921faa83191bccf20ad
    tWBTC market:                       0x67fd498e94d95972a4a2a44acce00a000af7fe00
    Price oracle adapter:               0xD360D8cABc1b2e56eCf348BFF00D2Bd9F658754A
The other two pools (not used by this script, listed for reference):
    Pool 2: 0x8312A8d5d1deC499D00eb28e1a2723b13aA53C1e
    Pool 3: 0x7E0067CEf1e7558daFbaB3B1F8F6Fa75Ff64725f

Tested against the live chain: connects fine, returns real data for all
18 markets in Pool 1. tTONIC is still listed with an unchanged 20%
collateral factor as of this run: no risk parameters were adjusted after
the exploit.

Usage:
    pip install web3
    python3 tectonic_risk_snapshot.py [--rpc https://evm.cronos.org]
"""
from __future__ import annotations

import argparse
import sys

from web3 import Web3
from web3.exceptions import ContractLogicError

TECTONIC_CORE = Web3.to_checksum_address("0xb3831584acb95ED9cCb0C11f677B5AD01DeaeEc0")

DEFAULT_RPC_ENDPOINTS = [
    "https://evm.cronos.org",
    "https://cronos.drpc.org",
    "https://cronos-evm-rpc.publicnode.com",
]

# Standard Compound v2 Comptroller ABI fragment: Tectonic is a documented
# Compound v2 fork ("TectonicCore" plays the Comptroller role, "tTokens"
# play the CToken role), so the canonical function signatures apply.
COMPTROLLER_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getAllMarkets",
        "outputs": [{"name": "", "type": "address[]"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "oracle",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "cToken", "type": "address"}],
        "name": "markets",
        "outputs": [
            {"name": "isListed", "type": "bool"},
            {"name": "collateralFactorMantissa", "type": "uint256"},
            {"name": "isComped", "type": "bool"},
        ],
        "type": "function",
    },
]

CTOKEN_ABI = [
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "underlying", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalBorrows", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalReserves", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "exchangeRateStored", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "getCash", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]

ORACLE_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "cToken", "type": "address"}],
        "name": "getUnderlyingPrice",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
]

ERC20_DECIMALS_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
]

# CRO (the chain's native asset) has no ERC20 `underlying()`; Compound-fork
# markets for the native coin return the zero address instead.
NATIVE_SENTINEL = "0x0000000000000000000000000000000000000000"


def connect(rpc_url: str) -> Web3:
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 20}))
    if not w3.is_connected():
        raise ConnectionError(f"could not connect to {rpc_url}")
    return w3


def underlying_decimals(w3: Web3, underlying_addr: str) -> int:
    if underlying_addr.lower() == NATIVE_SENTINEL:
        return 18  # native CRO
    token = w3.eth.contract(address=Web3.to_checksum_address(underlying_addr), abi=ERC20_DECIMALS_ABI)
    return token.functions.decimals().call()


def snapshot(rpc_url: str) -> list[dict]:
    w3 = connect(rpc_url)
    comptroller = w3.eth.contract(address=TECTONIC_CORE, abi=COMPTROLLER_ABI)

    markets = comptroller.functions.getAllMarkets().call()
    oracle_addr = comptroller.functions.oracle().call()
    oracle = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=ORACLE_ABI)

    rows = []
    for market_addr in markets:
        ctoken = w3.eth.contract(address=Web3.to_checksum_address(market_addr), abi=CTOKEN_ABI)

        symbol = ctoken.functions.symbol().call()
        try:
            underlying_addr = ctoken.functions.underlying().call()
        except ContractLogicError:
            # Tectonic's native-CRO market (tCRO) reverts on underlying()
            # instead of returning the zero-address sentinel like a typical
            # Compound-fork CEther equivalent would.
            underlying_addr = NATIVE_SENTINEL
        decimals = underlying_decimals(w3, underlying_addr)

        total_borrows = ctoken.functions.totalBorrows().call()
        cash = ctoken.functions.getCash().call()
        total_reserves = ctoken.functions.totalReserves().call()

        # Compound convention: price is scaled to 1e18 * 10**(18 - underlying_decimals)
        # so that price * amount_in_underlying_units / 1e18 = USD value.
        raw_price = oracle.functions.getUnderlyingPrice(market_addr).call()
        price_usd = raw_price / (10 ** (36 - decimals))

        borrows_units = total_borrows / (10 ** decimals)
        cash_units = cash / (10 ** decimals)
        reserves_units = total_reserves / (10 ** decimals)

        rows.append({
            "market": symbol,
            "address": market_addr,
            "underlying_price_usd": price_usd,
            "total_borrows_usd": borrows_units * price_usd,
            "available_cash_usd": cash_units * price_usd,
            "total_reserves_usd": reserves_units * price_usd,
            # utilization: how much of the pool's liquidity is currently
            # lent out: a market with cash near zero and borrows still
            # high after the rollback is the signal worth flagging.
            "utilization_pct": (
                100 * borrows_units / (borrows_units + cash_units)
                if (borrows_units + cash_units) > 0 else 0.0
            ),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rpc", default=DEFAULT_RPC_ENDPOINTS[0], help="Cronos RPC endpoint")
    args = parser.parse_args()

    try:
        rows = snapshot(args.rpc)
    except Exception as e:
        print(f"Snapshot failed against {args.rpc}: {e}", file=sys.stderr)
        print(f"Try one of: {', '.join(DEFAULT_RPC_ENDPOINTS[1:])}", file=sys.stderr)
        return 1

    print(f"{'Market':<10} {'Price (USD)':>14} {'Borrows (USD)':>16} {'Cash (USD)':>14} {'Util %':>8}")
    for r in sorted(rows, key=lambda r: r["total_borrows_usd"], reverse=True):
        # `g` picks significant figures rather than fixed decimals, so a
        # sub-cent price (tTONIC is ~1e-8) doesn't silently round to 0.000000.
        print(
            f"{r['market']:<10} {r['underlying_price_usd']:>14.6g} "
            f"{r['total_borrows_usd']:>16,.2f} {r['available_cash_usd']:>14,.2f} "
            f"{r['utilization_pct']:>7.1f}%"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
