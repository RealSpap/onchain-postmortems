#!/usr/bin/env python3
"""
Fetch.ai / NuNet: the read behind the 2026-10-13 correction.

The original README said the NTX token has no on-chain cap and that stopping at exactly 1,000,000,000 was a choice.
It does have one: `MAX_SUPPLY()` is 1,000,000,000 NTX, and `mint` refuses one unit more. The attacker minted the
largest amount the contract allowed. (The earlier note that `cap()` reverts is true, and beside the point: the cap is
exposed under another name.)

Usage:  python3 verify_correction_2026-10-13.py
Needs:  the standard library and a public RPC that serves archive state (gateway.tenderly.co/public/mainnet).
"""
import json
import sys
import time
import urllib.request

RPC = "https://gateway.tenderly.co/public/mainnet"
NTX = "0xf0d33beda4d734c72684b5f9abbebf715d0a7935"
MINTER = "0x863f13e5b505f1eb17803b94ec9d3daf80092165"       # the MINTER_ROLE key that signed the mint
STRANGER = "0x000000000000000000000000000000000000dead"
RECIPIENT = "0x2dcc1085fdcf418b421e45e86e4e54637cc21dfe"
BLOCK = 26_014_054                                          # the block BEFORE the attacker's mint (the mint is in block 26,014,055); eth_call reads the state at the end of this block
ATTACK_MINT = 408_532_878_133_452                           # 6 decimals: 408,532,878.133452 NTX


def rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for attempt in range(4):
        try:
            req = urllib.request.Request(RPC, body, {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:
            err = e
            time.sleep(1 + attempt)
    raise RuntimeError(f"UNREAD: {err}")


def sel(sig):
    return rpc("web3_sha3", ["0x" + sig.encode().hex()])["result"][:10]


def view(selector):
    out = rpc("eth_call", [{"to": NTX, "data": selector}, hex(BLOCK)])
    if "error" in out:
        return None
    return int(out["result"], 16)


def mint(amount, sender):
    """('OK', None) or ('REVERT', reason text) for mint(RECIPIENT, amount) simulated from `sender` at BLOCK."""
    data = sel("mint(address,uint256)") + RECIPIENT[2:].rjust(64, "0") + hex(amount)[2:].rjust(64, "0")
    out = rpc("eth_call", [{"from": sender, "to": NTX, "data": data}, hex(BLOCK)])
    if "error" not in out:
        return "OK", None
    msg = out["error"].get("message", "") + " " + str(out["error"].get("data", ""))
    return "REVERT", msg


fails = 0


def check(label, ok, detail):
    global fails
    fails += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}")


supply, cap, cap_old = view(sel("totalSupply()")), view(sel("MAX_SUPPLY()")), view(sel("cap()"))
print(f"INFO  block {BLOCK}: totalSupply {supply}, MAX_SUPPLY() {cap}, cap() {'reverts' if cap_old is None else cap_old}")
check("MAX_SUPPLY() is 1,000,000,000 NTX (6 decimals)", cap == 1_000_000_000_000_000, str(cap))
margin = cap - supply
check("the attacker's mint is exactly the headroom MAX_SUPPLY - totalSupply", margin == ATTACK_MINT, f"{margin} vs {ATTACK_MINT}")
ok_status, _ = mint(margin, MINTER)
check("mint(headroom) from the minter key passes", ok_status == "OK", ok_status)
over_status, reason = mint(margin + 1, MINTER)
check("mint(headroom + 1) from the minter key is refused", over_status == "REVERT" and "initial supply" in (reason or ""), f"{over_status}: {(reason or '')[:90]}")
stranger_status, _ = mint(margin, STRANGER)
check("mint(headroom) from a stranger is refused (the witness fails)", stranger_status == "REVERT", stranger_status)
sys.exit(1 if fails else 0)
