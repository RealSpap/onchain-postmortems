#!/usr/bin/env python3
"""
NuNet remediation closure and the NTX sale window, re-derived live.

Answers two questions the 2026-09-21 reconstruction could not yet answer:
  1. when the compromised key actually lost MINTER_ROLE and PAUSER_ROLE
  2. where the minted NTX was by the time the token was paused

Everything printed here is read from Ethereum mainnet at run time.
Usage:  python3 verif_remediation.py
"""
import json, time, urllib.request

RPC      = "https://gateway.tenderly.co/public/mainnet"
NTX      = "0xf0d33beda4d734c72684b5f9abbebf715d0a7935"
MINTKEY  = "0x863f13e5b505f1eb17803b94ec9d3daf80092165"
CASHOUT  = "0x2dcc1085fdcf418b421e45e86e4e54637cc21dfe"
NEWADMIN = "0x78a60de4fbf1f1c2daf8c94b5e40f877032cef00"
MMSWAP   = "0x881d40237659c251811cec9c364ef91dc08d300c"

MINTER_ROLE  = "0x9f2df0fed2c77648de5860a4cc508cd0818c85b8b8a1ab4ceeef8d981c8956a6"
PAUSER_ROLE  = "0x65d7a28e3265b37a6474929f336521b332c1681b933f6cb9f3376673440d862a"
ROLE_REVOKED = "0xf6391f5c32d9c69d2a47ea670b442974b53935d1edc7fd64eb21e047a839171b"
TRANSFER     = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

B_NTX_MINT   = 26014055   # the mint
B_DRAFT_HEAD = 26025495   # head when this entry was first written, 2026-09-21 11:09:35 UTC
B_LAST_SALE  = 26015677   # last NTX out of the cash-out wallet
B_PAUSE      = 26017641   # pause


def rpc(method, params, tries=6):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                RPC, data=json.dumps({"jsonrpc": "2.0", "id": 1,
                                      "method": method, "params": params}).encode(),
                headers={"Content-Type": "application/json", "Accept-Encoding": "identity"})
            with urllib.request.urlopen(req, timeout=180) as r:
                out = json.loads(r.read().decode())
            if "error" in out:
                raise RuntimeError(out["error"])
            return out["result"]
        except Exception as e:
            last = e
            time.sleep(1.0 * (i + 1))
    raise last


def blk(b):
    return b if isinstance(b, str) else hex(b)


def has_role(role, who, b="latest"):
    return int(rpc("eth_call", [{"to": NTX,
                                 "data": "0x91d14854" + role[2:] + "0" * 24 + who[2:]}, blk(b)]), 16) == 1


def ts(b):
    return int(rpc("eth_getBlockByNumber", [blk(b), False])["timestamp"], 16)


def iso(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t)) + " UTC"


print("=" * 70)
print("ROLE STATE ON THE COMPROMISED KEY %s" % MINTKEY)
print("=" * 70)
for name, role in (("MINTER_ROLE", MINTER_ROLE), ("PAUSER_ROLE", PAUSER_ROLE)):
    print("  %-12s at draft head %d : %s" % (name, B_DRAFT_HEAD, has_role(role, MINTKEY, B_DRAFT_HEAD)))
    print("  %-12s at latest            : %s" % (name, has_role(role, MINTKEY)))

logs = rpc("eth_getLogs", [{"address": NTX, "fromBlock": hex(B_NTX_MINT), "toBlock": "latest",
                            "topics": [ROLE_REVOKED, None, "0x" + "0" * 24 + MINTKEY[2:]]}])
print("\nRoleRevoked events naming that key: %d" % len(logs))
names = {MINTER_ROLE: "MINTER_ROLE", PAUSER_ROLE: "PAUSER_ROLE", "0x" + "00" * 32: "DEFAULT_ADMIN_ROLE"}
for l in logs:
    b = int(l["blockNumber"], 16)
    print("  block %d  %s  %-18s sender 0x%s" % (
        b, iso(ts(b)), names.get(l["topics"][1], l["topics"][1]), l["topics"][3][-40:]))
    print("    tx %s" % l["transactionHash"])

print("\n  revocation sender matches the new admin %s : %s" % (
    NEWADMIN, all("0x" + l["topics"][3][-40:] == NEWADMIN for l in logs)))

print("\nhours from the mint to the MINTER_ROLE revocation : %.2f" % ((ts(26025859) - ts(B_NTX_MINT)) / 3600.0))

print("\nwhat the compromised key can do now:")
for label, data in (("unpause()", "0x3f4ba83a"),
                    ("mint(cashout,1)", "0x40c10f19" + "0" * 24 + CASHOUT[2:] + "%064x" % 1)):
    try:
        rpc("eth_call", [{"from": MINTKEY, "to": NTX, "data": data}, "latest"], tries=1)
        print("    %-16s SUCCEEDS" % label)
    except Exception as e:
        msg = str(e)
        msg = msg[msg.find("execution reverted"):][:80] if "execution reverted" in msg else msg[:80]
        print("    %-16s reverts: %s" % (label, msg))

print("\n" + "=" * 70)
print("WHERE THE MINTED NTX WAS WHEN THE TOKEN WAS PAUSED")
print("=" * 70)
bal = int(rpc("eth_call", [{"to": NTX, "data": "0x70a08231" + "0" * 24 + CASHOUT[2:]}, "latest"]), 16)
print("  cash-out wallet NTX balance at latest : %.6f" % (bal / 1e6))
print("  cash-out wallet NTX balance at the pause block %d : %.6f" % (
    B_PAUSE, int(rpc("eth_call", [{"to": NTX, "data": "0x70a08231" + "0" * 24 + CASHOUT[2:]},
                                  hex(B_PAUSE)]), 16) / 1e6))

tx = "0x7831ac650481e446c065a241e40def85131cc1145ac7979c61392e18560d08fb"
t = rpc("eth_getTransactionByHash", [tx])
rc = rpc("eth_getTransactionReceipt", [tx])
print("\n  last NTX to leave the wallet, tx %s" % tx)
print("    from %s" % t["from"])
print("    to   %s  (MetaMask Swap Router: %s)" % (t["to"], t["to"].lower() == MMSWAP))
print("    status %s, block %d, %s" % (rc["status"], int(t["blockNumber"], 16), iso(ts(B_LAST_SALE))))
for l in rc["logs"]:
    if l["address"].lower() == NTX and l["topics"][0] == TRANSFER \
            and "0x" + l["topics"][1][-40:] == CASHOUT:
        print("    NTX out of the wallet in this tx : %.6f" % (int(l["data"], 16) / 1e6))

gap = ts(B_PAUSE) - ts(B_LAST_SALE)
print("\n  pause at %s" % iso(ts(B_PAUSE)))
print("  the wallet's last NTX left %d seconds (%dh%02dm%02ds) BEFORE the pause" % (
    gap, gap // 3600, (gap % 3600) // 60, gap % 60))
