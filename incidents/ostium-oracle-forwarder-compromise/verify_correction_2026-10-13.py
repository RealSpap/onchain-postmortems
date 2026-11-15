#!/usr/bin/env python3
"""
Ostium: the reads behind the 2026-10-13 correction.

The original README described the 231-byte contract the attack was sent through (0xfe12...bd2e) as "a purpose-built
batching contract used only to execute the attack". It is not. It had been registered as a forwarder on the
PrivatePriceUpKeep contract on 2026-05-30, about 46 days before the attack, in the same transaction as three other
forwarders, and its owner() just before the attack was the externally owned account that sent the attack.

Usage:  python3 verify_correction_2026-10-13.py
Needs:  the standard library and a public RPC that serves Arbitrum archive state (gateway.tenderly.co/public/arbitrum).
"""
import datetime
import json
import sys
import time
import urllib.request

RPC = "https://gateway.tenderly.co/public/arbitrum"
KEEPER = "0xb71ec9ebd8145dacacf6724363143cb5667a3d36"     # PrivatePriceUpKeep
FORWARDER = "0xfe12f6360000de49d5506d52ee5ac4bc9dd5bd2e"  # the 231-byte contract
SENDER = "0xd1794196f0fc99c7f27970e661597d77d9a85869"     # the EOA that sent the attack
REG_TX = "0x56e36ae77eb7de9ff9129af7422794bbabe287f2bcd109b95b141e57f008f24e"
REG_BLOCK, ATTACK_BLOCK = 468_285_055, 484_137_015


def rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for attempt in range(4):
        try:
            req = urllib.request.Request(RPC, body, {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
            out = json.load(urllib.request.urlopen(req, timeout=60))
            if "error" in out:
                raise RuntimeError(out["error"])
            return out["result"]
        except Exception as e:
            err = e
            time.sleep(1 + attempt)
    raise RuntimeError(f"UNREAD: {err}")


def sel(sig):
    return rpc("web3_sha3", ["0x" + sig.encode().hex()])[:10]


def call(to, data, block):
    return rpc("eth_call", [{"to": to, "data": data}, hex(block)])


fails = 0


def check(label, ok, detail):
    global fails
    fails += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}")


before = ATTACK_BLOCK - 1
code = rpc("eth_getCode", [FORWARDER, hex(before)])
check("the forwarder is 231 bytes of code just before the attack", (len(code) - 2) // 2 == 231, str((len(code) - 2) // 2))

owner = "0x" + call(FORWARDER, sel("owner()"), before)[-40:]
check("owner() of the forwarder just before the attack is the attack's sender", owner == SENDER, owner)

is_fw = int(call(KEEPER, sel("isForwarder(address)") + FORWARDER[2:].rjust(64, "0"), before), 16)
is_fw_sender = int(call(KEEPER, sel("isForwarder(address)") + SENDER[2:].rjust(64, "0"), before), 16)
check("the keeper lists the forwarder as registered just before the attack", is_fw == 1, str(is_fw))
check("the sender account itself is not a registered forwarder (the witness)", is_fw_sender == 0, str(is_fw_sender))

receipt = rpc("eth_getTransactionReceipt", [REG_TX])
check("the registration transaction succeeded in the block the log search gave", receipt["status"] == "0x1" and int(receipt["blockNumber"], 16) == REG_BLOCK, f"status {receipt['status']}, block {int(receipt['blockNumber'], 16)}")
mentions = [l for l in receipt["logs"] if l["address"].lower() == KEEPER and FORWARDER[2:] in (l["data"] + "".join(l["topics"])).lower()]
check("the keeper emitted a log naming the forwarder in that transaction", len(mentions) >= 1, f"{len(mentions)} log(s)")

ts = {b: int(rpc("eth_getBlockByNumber", [hex(b), False])["timestamp"], 16) for b in (REG_BLOCK, ATTACK_BLOCK)}
days = (ts[ATTACK_BLOCK] - ts[REG_BLOCK]) / 86400
fmt = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
print(f"INFO  registered {fmt(ts[REG_BLOCK])}, attack block {fmt(ts[ATTACK_BLOCK])}: {days:.1f} days apart")
check("the registration came about 46 days before the attack", 45 <= days <= 47, f"{days:.1f}")
sys.exit(1 if fails else 0)
