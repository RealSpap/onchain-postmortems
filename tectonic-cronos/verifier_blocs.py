#!/usr/bin/env python3
"""Reads the Cronos blocks this entry relies on from three public JSON-RPC endpoints (no key, no indexer) and prints hash and timestamp for each.
The hex form of every block number is computed with hex(n); it is never typed by hand. Standard library only.
Usage: python3 verifier_blocs.py [block ...]   (default: the blocks listed in BLOCKS)"""
import datetime, json, sys, time, urllib.request
NODES = ["https://evm.cronos.org", "https://cronos.drpc.org", "https://cronos-evm-rpc.publicnode.com"]
BLOCKS = [
    (90896188, "last block kept by the rollback, per Cronos's report"),
    (90896189, "the next block"),
    (90896190, "the block after that"),
    (90896206, "where Dune's index dates the start of the TONIC price rise (12:39:10 UTC)"),
    (90897073, "where Dune's index dates the price peak (12:49:13 UTC)"),
    (90907150, "the halt block, per Cronos's report"),
]
def rpc(url, method, params):
    last = None
    for _ in range(4):
        try:
            req = urllib.request.Request(url, json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                                         {"Content-Type": "application/json", "User-Agent": "curl/8"})
            r = json.load(urllib.request.urlopen(req, timeout=40))
            if "error" in r or r.get("result") is None: last = r.get("error", "null"); time.sleep(2); continue
            return r["result"]
        except Exception as e: last = e; time.sleep(2)
    return "ERROR " + str(last)[:80]
def utc(ts): return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
wanted = [(int(a), "") for a in sys.argv[1:]] or BLOCKS
for n, note in wanted:
    h = hex(n)
    print(f"--- block {n} ({h}){' - ' + note if note else ''}")
    for u in NODES:
        b = rpc(u, "eth_getBlockByNumber", [h, False])
        if isinstance(b, dict):
            assert int(b["number"], 16) == n, (u, b["number"])
            ts = int(b["timestamp"], 16)
            print(f"  {u.split('//')[1]:32s} hash {b['hash']}  timestamp {ts} ({utc(ts)})  transactions {len(b['transactions'])}")
        else: print(f"  {u.split('//')[1]:32s} {b}")
print("--- current height")
for u in NODES:
    r = rpc(u, "eth_blockNumber", [])
    print(f"  {u.split('//')[1]:32s} {int(r, 16) if r.startswith('0x') else r}")
