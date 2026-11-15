#!/usr/bin/env python3
"""
Term Finance Meta Vault: the reads behind the 2026-10-13 correction.

Three claims of the original README were wrong and are replaced by what this script reads:
  1. The execution delay did not run its course: the Zodiac Delay module's txCooldown was 608,400 s one block
     before execution and 0 in the execution block, where seven queued transactions were also executed.
  2. The 6 days 1 hour between propose() and executeProposal() is the length of the vote, not an elapsed delay.
  3. The voting power was not TERM: the plugin's voting token wraps the ETH Meta Vault itself, and the
     attacker's deposit into the vault, a few blocks before propose(), made it the holder of almost every vote.

Usage:  python3 verify_correction_2026-10-13.py
Needs:  the standard library and a public RPC that serves archive state (gateway.tenderly.co/public/mainnet).
A read that fails prints UNREAD, never 0.
"""
import json
import sys
import time
import urllib.request

RPC = "https://gateway.tenderly.co/public/mainnet"
DELAY = "0x35c99cf4a5df2d9bcd822bee32676d9590229e33"      # Zodiac Delay module on the vault's Safe
VOTE_TOKEN = "0x5b96c5bbdcb361e1e9944baa071b237e27829be0"  # the voting plugin's token
VAULT = "0x26fcb50eec367ddab060ccf5e7394cecd95f7db2"       # ETH Meta Vault
EXECUTOR = "0x64e477800051efb06ae4086f4b258b270668b4df"    # the 145-byte contract the attacker deployed
EXEC_TX = "0xd354a15b15cb73d30908f411aee3f795ec86737a4d080e9a818ac4d6d3014129"
B_BEFORE_PROPOSAL, B_PROPOSE, B_EXEC_MINUS_1, B_EXEC = 25_772_680, 25_772_694, 25_816_048, 25_816_049


def rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for attempt in range(4):
        try:
            req = urllib.request.Request(RPC, body, {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
            out = json.load(urllib.request.urlopen(req, timeout=60))
            if "error" in out:
                raise RuntimeError(out["error"])
            return out["result"]
        except Exception as e:  # 429 or a transient failure: retry, then give up loudly
            err = e
            time.sleep(1 + attempt)
    raise RuntimeError(f"UNREAD: {err}")


def call(to, data, block):
    return rpc("eth_call", [{"to": to, "data": data}, hex(block)])


def uint(to, selector, block):
    return int(call(to, selector, block), 16)


def keccak(sig):
    """Full keccak256 of a signature, asked of the node itself (web3_sha3) so no extra package is needed."""
    return rpc("web3_sha3", ["0x" + sig.encode().hex()])


def keccak4(sig):
    return keccak(sig)[:10]


fails = 0


def check(label, ok, detail):
    global fails
    fails += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'}  {label}: {detail}")


# 1. the delay cooldown, one block before and in the execution block
SEL_COOLDOWN = keccak4("txCooldown()")
SEL_EXPIRATION = keccak4("txExpiration()")
for name, selector in (("txCooldown", SEL_COOLDOWN), ("txExpiration", SEL_EXPIRATION)):
    b, a = uint(DELAY, selector, B_EXEC_MINUS_1), uint(DELAY, selector, B_EXEC)
    print(f"INFO  Delay {name} one block before execution -> in the execution block: {b} -> {a}")
cool_before, cool_after = uint(DELAY, SEL_COOLDOWN, B_EXEC_MINUS_1), uint(DELAY, SEL_COOLDOWN, B_EXEC)
check("the cooldown was 7 days 1 hour (608,400 s) and became 0", (cool_before, cool_after) == (608_400, 0), f"{cool_before} -> {cool_after}")

# 2. the execution transaction queued and ran seven transactions through the Delay module
receipt = rpc("eth_getTransactionReceipt", [EXEC_TX])
full_added = keccak("TransactionAdded(uint256,bytes32,address,uint256,bytes,uint8)")
n_added = sum(1 for l in receipt["logs"] if l["address"].lower() == DELAY and l["topics"][0] == full_added)
check("TransactionAdded events from the Delay module inside the execution transaction", n_added == 7, str(n_added))
check("execution block", int(receipt["blockNumber"], 16) == B_EXEC, str(int(receipt["blockNumber"], 16)))

# 3. the vote
underlying = "0x" + call(VOTE_TOKEN, keccak4("underlying()"), B_EXEC_MINUS_1)[-40:]
check("the voting token's underlying() is the ETH Meta Vault, not TERM", underlying == VAULT, underlying)
supply = {b: uint(VOTE_TOKEN, keccak4("totalSupply()"), b) for b in (B_BEFORE_PROPOSAL, B_PROPOSE, B_EXEC_MINUS_1)}
print("INFO  voting token totalSupply (raw, 18 decimals) before the attacker's deposit / at propose() / one block before execution:", supply)
try:
    votes = int(call(VOTE_TOKEN, keccak4("getVotes(address)") + EXECUTOR[2:].rjust(64, "0"), B_EXEC_MINUS_1), 16)
    share = 100 * votes / supply[B_EXEC_MINUS_1]
    check("the attacker's executor held most of the votes one block before execution", share > 50, f"{votes} of {supply[B_EXEC_MINUS_1]} = {share:.2f}%")
except Exception as e:
    print("UNREAD  getVotes(executor):", e)
sys.exit(1 if fails else 0)
