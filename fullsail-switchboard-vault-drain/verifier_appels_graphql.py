#!/usr/bin/env python3
"""Full Sail (Sui, 2026-08-29): what the attacker's 63 deposits and 63 withdrawals are, counted from the attacker's own transactions.

Standard library only. It pages every transaction SENT by the attacker address through Sui's public GraphQL endpoint (the JSON-RPC of the public fullnodes is
deprecated), reads each one's status, timestamp and Move calls, and counts the calls to port::deposit and port::withdraw_v2 in successful transactions and in
failed ones. The events used by reconstruct_exploit.py exist only for successful calls; a failed transaction is reverted whole and emits none.
Every claim is a CHECK line: PASS or FAIL; exit code 1 if one fails.   python3 verifier_appels_graphql.py
"""
import json, sys, time, urllib.request
from collections import Counter
URL = "https://graphql.mainnet.sui.io/graphql"
A = "0x9104d073e1fdfd76a6b756f61c5684e4affa0b3d124d383afc64aabbd87934cc"
results = []


def gq(q):
    last = None
    for attempt in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(URL, json.dumps({"query": q}).encode(), {"Content-Type": "application/json", "User-Agent": "curl/8"}), timeout=90))
        except Exception as exc:
            last = exc
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"GraphQL failed: {last}")


def check(name, cond, detail=""):
    results.append(bool(cond))
    print(f"CHECK {'PASS' if cond else 'FAIL'} {name} {detail}".rstrip())


nodes, cur = [], None
while True:
    after = f',after:"{cur}"' if cur else ""
    r = gq('{ transactions(first: 25, filter:{sentAddress:"%s"}%s) { pageInfo{hasNextPage endCursor} nodes { digest kind { ... on ProgrammableTransaction { commands(first: 50) { pageInfo{hasNextPage} nodes { __typename ... on MoveCallCommand { function { name module { name } } } } } } } effects { status timestamp executionError { message } } } } }' % (A, after))
    if r.get("errors") or "data" not in r:
        raise RuntimeError(r.get("errors"))
    t = r["data"]["transactions"]
    nodes += t["nodes"]
    if not t["pageInfo"]["hasNextPage"]:
        break
    cur = t["pageInfo"]["endCursor"]
print(f"{len(nodes)} transactions sent by {A}")
rows = []
for n in nodes:
    cmds = (n.get("kind") or {}).get("commands") or {}
    calls = [c["function"]["module"]["name"] + "::" + c["function"]["name"] for c in cmds.get("nodes", []) if c.get("function")]
    allc = [(c["function"]["module"]["name"] + "::" + c["function"]["name"]) if c.get("function") else c["__typename"] for c in cmds.get("nodes", [])]
    rows.append((n["digest"], n["effects"]["status"], n["effects"]["timestamp"], calls, bool(cmds.get("pageInfo", {}).get("hasNextPage")), (n["effects"].get("executionError") or {}).get("message", ""), allc))
trunc = [r for r in rows if r[4]]
print(f"transactions whose command list needed a second page: {len(trunc)}")
ok = [r for r in rows if r[1] == "SUCCESS"]
ko = [r for r in rows if r[1] != "SUCCESS"]
dep_ok = [r for r in ok if "port::deposit" in r[3]]
wd_ok = [r for r in ok if "port::withdraw_v2" in r[3]]
dep_ko = [r for r in ko if "port::deposit" in r[3]]
wd_ko = [r for r in ko if "port::withdraw_v2" in r[3]]
other_ko = [r for r in ko if r not in dep_ko and r not in wd_ko]
days = Counter(r[2][:10] for r in rows)
check("H12a the attacker address sent 165 transactions in all, 162 on 2026-08-29 and 3 on 2026-09-04; 10 of the 162 failed", len(rows) == 165 and days == {"2026-08-29": 162, "2026-09-04": 3} and len([r for r in ko]) == 10 and all(r[2].startswith("2026-08-29") for r in ko), f"({len(rows)} transactions, by day {dict(days)}, {len(ko)} failed)")
check("H12b 63 successful transactions each call port::deposit once and 63 successful transactions each call port::withdraw_v2 once, 63 and 63 calls in all, between 02:33:24 and 05:28:07 UTC on 2026-08-29", len(dep_ok) == 63 and len(wd_ok) == 63 and sum(r[3].count("port::deposit") for r in dep_ok) == 63 and sum(r[3].count("port::withdraw_v2") for r in wd_ok) == 63 and min(r[2] for r in dep_ok).startswith("2026-08-29T02:33:2") and max(r[2] for r in wd_ok).startswith("2026-08-29T05:28:07"), f"(first deposit {min(r[2] for r in dep_ok)}, last withdraw {max(r[2] for r in wd_ok)})")
import re


def failing_call(r):
    """The call the abort happened in: the error text says 'Error in Nth command', read here as 1-based (the named aborts land on a deposit or a withdraw_v2 call, which is why)."""
    m = re.search(r"Error in (\d+)(?:st|nd|rd|th) command", r[5])
    return (r[6][int(m.group(1)) - 1], int(m.group(1))) if m and int(m.group(1)) <= len(r[6]) else (None, None)


t_first, t_last = min(r[2] for r in dep_ok), max(r[2] for r in wd_ok)
at_dep = [r for r in dep_ko if failing_call(r)[0] == "port::deposit"]
before_dep = [r for r in dep_ko if r not in at_dep]
at_wd = [r for r in wd_ko if failing_call(r)[0] == "port::withdraw_v2"]
inw = lambda r: t_first <= r[2] <= t_last
check("H12c the 10 failed transactions are: 7 that contain a port::deposit, 2 that contain a port::withdraw_v2 and 1 swap that ran out of gas; a failed transaction is reverted whole, so none of their calls emitted an event or moved funds", len(dep_ko) == 7 and len(wd_ko) == 2 and len(other_ko) == 1 and "port::deposit" not in other_ko[0][3], f"({len(dep_ko)} with a deposit, {len(wd_ko)} with a withdraw_v2, {len(other_ko)} other)")
check("H12e of the 7 failed transactions that contain a deposit, 3 aborted in the deposit call itself (one inside the attack window, 03:23:15 UTC, hard_cap_reached; two before it, not_updated_osail_growth_time and not_updated_reward_growth_time) and 4 aborted earlier, before reaching it (2 in calculate_aum before the window, 2 in update_pool_reward_v2 with port_is_pause after it)", len(at_dep) == 3 and sum(inw(r) for r in at_dep) == 1 and len(before_dep) == 4 and sorted(failing_call(r)[0] for r in before_dep) == ["port::calculate_aum"] * 2 + ["port::update_pool_reward_v2"] * 2 and sum(inw(r) for r in before_dep) == 0, f"({[(r[0][:8], r[2][11:19], failing_call(r)[0]) for r in dep_ko]})")
check("H12f both failed transactions that contain a withdraw_v2 aborted in that call and both are inside the window (02:33:38 high_price_difference and 02:55:40 not_updated_osail_growth_time); so inside the window (02:33:24 to 05:28:07 UTC) the failures at a deposit or withdraw call are 1 deposit and 2 withdrawals", len(at_wd) == 2 and all(inw(r) for r in at_wd) and sum(inw(r) for r in at_dep + at_wd) == 3 and sum(inw(r) for r in at_dep) == 1, f"({[(r[0][:8], r[2][11:19], r[5][-40:]) for r in at_wd]})")
check("H12d one successful transaction has more than 50 commands and only its first 50 were read; it was sent at 01:38:27 UTC, before the first successful deposit at 02:33:24, and the 63 and 63 above match the event counts of reconstruct_exploit.py, so it holds no deposit or withdrawal that those counts miss", len(trunc) == 1 and trunc[0][1] == "SUCCESS" and trunc[0][2] < min(r[2] for r in dep_ok), f"({[(r[0][:8], r[2]) for r in trunc]})")
print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
