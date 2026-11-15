#!/usr/bin/env python3
"""UNCX VestingManager v2, Ethereum leg: funds returned after the window of reconstruct_exploit.py (which stops at block 26204197).

Reads, live and read-only: the receipts of the two transactions that carried the returned X tokens (on three independent public nodes, which must agree), the path of
those tokens from the second drain, every X token transfer of the original depositor since the incident, the contract's balances at block 26204197 and now, and the
value of the returned tokens at DefiLlama's price for the time of the first drain (the same price reconstruct_exploit.py uses).
Also (added 2026-10-21): the 8.10335 ETH sent by the same holder to the same Safe and handed on to the same depositor, and an exhaustive list of what moved in and out of the Safe and out
of the holder towards the Safe, the depositor or the contract since the first drain.
Usage: python3 verifier_retours.py
"""
import calendar, json, subprocess, time

NODES = ["https://gateway.tenderly.co/public/mainnet", "https://eth.drpc.org", "https://eth-mainnet.public.blastapi.io"]
BS = "https://eth.blockscout.com/api/v2"
VM = "0xA98F06312b7614523d0f5e725e15fd20fB1b99F5"
X = "0x140007c65535AA9C3801eA3bBd3F83C378C7F457"           # X token, 9 decimals
DEPOSITOR = "0x81EDADbe4a5BaaD8cd5d321547584cB48Fe1d265"    # the only address that ever deposited X in the contract (3 deposits, 150,150,150.15 X)
HOLDER = "0xC70f00CD7E461686b04B0E912E309becA8b80ea0"      # received X in the second drain transaction
SAFE = "0x32f0eB068fD804195629A2CBEE30A7e9CE58c4cb"
DRAIN2 = "0xbf7e5182694d0703051951520c176135dac63d772b328468ce783b37dd7a8a7c"
RET1 = "0xf0ae2cd77698882e35437500891907327765f4e36f33c7dcd88683be7c757301"   # HOLDER -> SAFE
RET2 = "0x686c704e402fa9d531e87afaec20d36d6ce53851cbac7f4365e5b46823bd753b"   # SAFE -> DEPOSITOR
ETH1 = "0x07614e32f26762ef90d3010f8f4460302a6689ab4444c62015fb04cb2edc02d2"   # HOLDER -> SAFE, native ETH
ETH2 = "0xf7cccf72387813d6ecacdb31c05e544ead2b43b50942d2373d790222c3300749"   # SAFE -> DEPOSITOR, native ETH (an execTransaction sent by a Safe owner)
SINCE = "2026-10-14T00:00"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
WINDOW_END = 26204197
FIRST_TX_TIME = "2026-10-14T15:49:35"
TOKENS = {"ZC": ("0x4E67DB19044549fF420860834c91b45BaD298722", 18), "X": (X, 9), "PAAL": ("0x14feE680690900BA0ccCfC76AD70Fd1b95D10e16", 9),
          "LO0P": ("0x00000000000050806673B532D7486ac114c1De3F", 18), "PEPECOIN": ("0xA9E8aCf069C58aEc8825542845Fd754e41a9489A", 18),
          "EDGEN": ("0xAa9806c938836627Ed1a41Ae871c7E1889AE02Ca", 18)}


def curl_json(url, data=None):
    cmd = ["curl", "-s", "-m", "60", url] if data is None else ["curl", "-s", "-m", "60", "-X", "POST", "-H", "content-type: application/json", "--data", json.dumps(data), url]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)


def rpc(node, method, params):
    for _ in range(6):
        r = curl_json(node, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        if r.get("result") is not None:
            return r["result"]
        time.sleep(2)
    raise RuntimeError(f"RPC error from {node}: {r}")


def x9(raw):
    return f"{raw // 10**9:,}.{raw % 10**9:09d}"   # exact, 9 decimals


def addr(topic):
    return "0x" + topic[-40:]


def recent(path, since=SINCE, maxp=40):
    out, nxt, sep = [], "", "&" if "?" in path else "?"
    for _ in range(maxp):
        d = curl_json(f"{BS}/{path}{nxt}")
        it = d.get("items", [])
        out += [t for t in it if t["timestamp"] >= since]
        n = d.get("next_page_params")
        if not it or min(t["timestamp"] for t in it) < since or not n:
            break
        nxt = sep + "&".join(f"{k}={v}" for k, v in n.items())
    return out


def x_transfers(receipt):
    return [(addr(l["topics"][1]), addr(l["topics"][2]), int(l["data"], 16)) for l in receipt["logs"]
            if l["address"].lower() == X.lower() and l["topics"] and l["topics"][0] == TRANSFER and len(l["topics"]) == 3]


def main():
    print("1) The two transactions, on three nodes (they must agree)")
    seen = {}
    for name, h in (("return 1", RET1), ("return 2", RET2)):
        per_node = []
        for n in NODES:
            rc = rpc(n, "eth_getTransactionReceipt", [h])
            blk = rpc(n, "eth_getBlockByNumber", [rc["blockNumber"], False])
            per_node.append((int(rc["status"], 16), int(rc["blockNumber"], 16), int(blk["timestamp"], 16), x_transfers(rc)))
        assert all(p == per_node[0] for p in per_node), f"nodes disagree on {h}"
        status, block, ts, tr = per_node[0]
        seen[name] = tr
        for f, t, v in tr:
            print(f"  {name} {h}\n    status {status} block {block} {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts))} UTC: X {x9(v)} from {f} to {t}")
    amount = seen["return 1"][0][2]
    assert seen["return 1"][0][:2] == (HOLDER.lower(), SAFE.lower()) and seen["return 2"][0][:2] == (SAFE.lower(), DEPOSITOR.lower()) and seen["return 2"][0][2] == amount
    print(f"  same amount in both transactions: {amount} raw units = {x9(amount)} X")

    print("\n2) Where the holder got them: the second drain transaction")
    rc = rpc(NODES[0], "eth_getTransactionReceipt", [DRAIN2])
    got = [v for f, t, v in x_transfers(rc) if t == HOLDER.lower()]
    print(f"  {DRAIN2}: X received by {HOLDER} in that transaction: {x9(sum(got))} X (returned: {x9(amount)} X, {amount/sum(got):.1%} of it)")

    print("\n3) The original depositor: deposits into the contract, and the return")
    items, nxt = [], ""
    for _ in range(20):
        d = curl_json(f"{BS}/addresses/{DEPOSITOR}/token-transfers?type=ERC-20&token={X}{nxt.replace('?', '&')}")
        items += d["items"]
        n = d.get("next_page_params")
        if not n:
            break
        nxt = "?" + "&".join(f"{k}={v}" for k, v in n.items())
    dep = sorted((t for t in items if t["to"]["hash"].lower() == VM.lower()), key=lambda t: t["timestamp"])
    for t in dep:
        print(f"  deposit {t['timestamp']} {int(t['total']['value'])/1e9:,.2f} X tx {t['transaction_hash']}")
    print(f"  total deposited by this address: {sum(int(t['total']['value']) for t in dep)/1e9:,.2f} X")
    after = sorted((t for t in items if t["timestamp"] >= "2026-10-15"), key=lambda t: t["timestamp"])
    for t in after:
        print(f"  since the incident {t['timestamp']} block {t['block_number']} {x9(int(t['total']['value']))} X {t['from']['hash']} -> {t['to']['hash']} tx {t['transaction_hash']}")

    print(f"\n4) The contract: balances at block {WINDOW_END} (end of the 16/10 reconstruction) and now")
    head = int(rpc(NODES[0], "eth_blockNumber", []), 16)
    for s, (a, d) in TOKENS.items():
        data = "0x70a08231" + VM[2:].lower().rjust(64, "0")
        b0 = int(rpc(NODES[0], "eth_call", [{"to": a, "data": data}, hex(WINDOW_END)]), 16)
        b1 = int(rpc(NODES[0], "eth_call", [{"to": a, "data": data}, hex(head)]), 16)
        print(f"  {s:9s} at {WINDOW_END}: {b0/10**d:,.4f}   now (block {head}): {b1/10**d:,.4f}")
    print("  transfers of the contract since 2026-10-15 (Blockscout):")
    rows, nxt = [], ""
    for _ in range(40):
        d = curl_json(f"{BS}/addresses/{VM}/token-transfers{nxt}")
        rows += d["items"]
        n = d.get("next_page_params")
        if not n:
            break
        nxt = "?" + "&".join(f"{k}={v}" for k, v in n.items())
    for t in sorted((t for t in rows if t["timestamp"] >= "2026-10-15"), key=lambda t: t["timestamp"]):
        v = int(t["total"]["value"] or 0) / 10 ** int(t["token"].get("decimals") or 0)
        print(f"    {t['timestamp']} {t['token'].get('symbol')} {v:,.4f} {t['from']['hash']} -> {t['to']['hash']}")

    print("\n5) Native ETH: the same holder sent ETH to the same Safe, which handed it to the same depositor (three nodes must agree)")
    eth = None
    for n in NODES:
        a = rpc(n, "eth_getTransactionByHash", [ETH1]); r = rpc(n, "eth_getTransactionReceipt", [ETH1])
        b2 = rpc(n, "eth_getTransactionByHash", [ETH2]); r2 = rpc(n, "eth_getTransactionReceipt", [ETH2])
        blk2 = int(r2["blockNumber"], 16)
        sb = [int(rpc(n, "eth_getBalance", [SAFE, hex(x)]), 16) for x in (blk2 - 1, blk2)]
        db = [int(rpc(n, "eth_getBalance", [DEPOSITOR, hex(x)]), 16) for x in (blk2 - 1, blk2)]
        row = (a["from"].lower(), a["to"].lower(), int(a["value"], 16), int(r["status"], 16), int(r["blockNumber"], 16), b2["to"].lower(), int(r2["status"], 16), blk2, sb, db)
        eth = eth or row
        assert row == eth, f"nodes disagree on the ETH transactions ({n})"
    f1, t1, v1, s1, bl1, to2, s2, bl2, sb, db = eth
    ts1 = int(rpc(NODES[0], "eth_getBlockByNumber", [hex(bl1), False])["timestamp"], 16); ts2 = int(rpc(NODES[0], "eth_getBlockByNumber", [hex(bl2), False])["timestamp"], 16)
    print(f"  {ETH1}\n    status {s1} block {bl1} {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts1))} UTC: {v1/1e18:.5f} ETH from {f1} to {t1}")
    print(f"  {ETH2}\n    status {s2} block {bl2} {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts2))} UTC, sent to the Safe {to2} (an execTransaction); Safe balance before/after: {sb[0]/1e18:.5f} / {sb[1]/1e18:.5f} ETH; depositor balance gain in that block: {(db[1]-db[0])/1e18:.5f} ETH")
    assert f1 == HOLDER.lower() and t1 == SAFE.lower() and v1 == sb[0] and sb[1] == 0 and db[1] - db[0] == v1, "the ETH did not go holder -> Safe -> depositor as read"
    eth_wei = v1
    print(f"  same amount in and out: {eth_wei/1e18:.5f} ETH; Safe balance now: " + ", ".join(f"{int(rpc(n, 'eth_getBalance', [SAFE, 'latest']), 16)/1e18:.5f}" for n in NODES) + " ETH on the three nodes")

    print(f"\n6) Everything that moved at the Safe since the first drain (Blockscout; the Safe was created on 2026-10-15 08:32 UTC)")
    for t in sorted(recent(f"addresses/{SAFE}/transactions"), key=lambda t: t["timestamp"]):
        print(f"  tx {t['timestamp'][:19]} block {t['block_number']} {t['hash']} from {t['from']['hash']} to {(t['to'] or {}).get('hash')} value {int(t['value'])/1e18:.5f} ETH")
    for t in sorted(recent(f"addresses/{SAFE}/internal-transactions"), key=lambda t: t["timestamp"]):
        if int(t["value"]):
            print(f"  internal {t['timestamp'][:19]} block {t['block_number']} {t['transaction_hash']} {t['type']} {t['from']['hash']} -> {(t['to'] or {}).get('hash')} {int(t['value'])/1e18:.5f} ETH")
    for t in sorted(recent(f"addresses/{SAFE}/token-transfers"), key=lambda t: t["timestamp"]):
        print(f"  token {t['timestamp'][:19]} block {t['block_number']} {t['transaction_hash']} {t['token'].get('symbol')} {x9(int(t['total']['value']))} {t['from']['hash']} -> {t['to']['hash']}")

    print(f"\n7) Transfers from the holder since {SINCE} whose recipient is exactly the Safe, the depositor or the contract")
    want = {SAFE.lower(), DEPOSITOR.lower(), VM.lower()}
    hits = []
    for t in recent(f"addresses/{HOLDER}/token-transfers"):
        if t["from"]["hash"].lower() == HOLDER.lower() and t["to"]["hash"].lower() in want:
            hits.append(("token", t["timestamp"], t["transaction_hash"], t["token"].get("symbol"), x9(int(t["total"]["value"])), t["to"]["hash"]))
    for t in recent(f"addresses/{HOLDER}/transactions"):
        if t["from"]["hash"].lower() == HOLDER.lower() and (t["to"] or {}).get("hash", "").lower() in want:
            hits.append(("native", t["timestamp"], t["hash"], "ETH", f"{int(t['value'])/1e18:.5f}", t["to"]["hash"]))
    for t in recent(f"addresses/{HOLDER}/internal-transactions"):
        if t["from"]["hash"].lower() == HOLDER.lower() and (t["to"] or {}).get("hash", "").lower() in want and int(t["value"]):
            hits.append(("internal", t["timestamp"], t["transaction_hash"], "ETH", f"{int(t['value'])/1e18:.5f}", t["to"]["hash"]))
    for h in sorted(hits, key=lambda h: h[1]):
        print(f"  {h[0]} {h[1][:19]} {h[2]} {h[3]} {h[4]} -> {h[5]}")
    assert {(h[3], h[2]) for h in hits} == {("X", RET1), ("ETH", ETH1)}, "unexpected transfer from the holder to the Safe, the depositor or the contract"
    fake = [t for t in recent(f"addresses/{HOLDER}/token-transfers") if t["from"]["hash"].lower() == HOLDER.lower() and t["to"]["hash"].lower() not in want
            and t["to"]["hash"][:6].lower() == SAFE[:6].lower() and t["to"]["hash"][-3:].lower() == SAFE[-3:].lower()]
    print(f"  not counted: {len(fake)} ERC-20 Transfer events naming the holder as sender, for tokens listed as 'ETH' or lookalikes of it, each for 8.10335 and each to a DIFFERENT address that starts with 0x32f0 and ends with 4cb (never the Safe): they repeat the amount of the real ETH transfer and mimic the Safe's address, and none reaches the Safe, the depositor or the contract")

    print("\n8) Value of the returns, at DefiLlama's price for the time of the first drain (as in reconstruct_exploit.py)")
    ts = calendar.timegm(time.strptime(FIRST_TX_TIME, "%Y-%m-%dT%H:%M:%S"))
    px = curl_json(f"https://coins.llama.fi/prices/historical/{ts}/ethereum:{X}?searchWidth=6h")["coins"]["ethereum:" + X]
    pe = curl_json(f"https://coins.llama.fi/prices/historical/{ts}/coingecko:ethereum?searchWidth=6h")["coins"]["coingecko:ethereum"]
    vx, ve = amount / 1e9 * px["price"], eth_wei / 1e18 * pe["price"]
    gross = 242605
    print(f"  X price {px['price']:.10f} (confidence {px['confidence']:.2f}): {x9(amount)} X = ${vx:,.0f}")
    print(f"  ETH price {pe['price']:.4f} (confidence {pe['confidence']:.2f}): {eth_wei/1e18:.5f} ETH = ${ve:,.0f}")
    print(f"  Ethereum leg: gross (balance drop, 16/10 reconstruction) ${gross:,.0f}; X returned ${round(vx):,.0f} -> ${gross - round(vx):,.0f}; ETH returned ${round(ve):,.0f} -> ${gross - round(vx) - round(ve):,.0f} net of both returns")

if __name__ == "__main__":
    main()
