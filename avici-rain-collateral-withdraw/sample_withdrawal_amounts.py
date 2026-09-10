"""
Supplementary to reconstruct_exploit.py: why this project does NOT claim an
independently re-summed dollar total for this incident, only a sourced one.

The attacker's own USDC loot account had 5,392 transactions touch it (see
reconstruct_exploit.py Step 2). Fully re-summing all 5,392 individual
token-balance deltas is possible but was not exhaustively done here: this
script instead draws a fixed random sample (seed=42, so it is exactly
reproducible) of 35 of those 5,392 transactions, computes each one's real
token-balance delta on that account, and reports the sample's own
statistics. The result: about 71% of sampled transactions moved 0 USDC (a
victim account the attacker had already drained, or one with nothing to
take), and the 29% that did move funds range from single-digit dollars to
several thousand, a distribution too skewed for a 35-transaction sample to
extrapolate a reliable total from (naive extrapolation over-estimates by
roughly 75% against the $500,859.22 figure Avici and DefiLlama both
report). That is reported here as the reason, not glossed over: this
project's own attempt at independent recomputation was inconclusive, so
the $500,859.22 figure in the README is sourced (Avici's own X statement,
matching DefiLlama's independently tracked figure for this incident) and
labeled as such, not claimed as independently re-derived.

RPC endpoint: https://api.mainnet-beta.solana.com (public, no key).
"""
import json
import time
import random
import urllib.request

RPC = "https://api.mainnet-beta.solana.com"
ATTACKER = "FVNFzqAny8spWdPmYw6RQ9TkYa29ueFFiqCFD1gQnCEj"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def rpc(method, params, retries=4):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(RPC, data=body, headers={"Content-Type": "application/json"})
    last_err = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read())
                if "result" in d:
                    return d["result"]
                last_err = d.get("error")
        except Exception as e:
            last_err = e
        time.sleep(1)
    raise RuntimeError(f"RPC {method} failed after {retries} attempts: {last_err}")


if __name__ == "__main__":
    doc = rpc("getTokenAccountsByOwner", [ATTACKER, {"mint": USDC_MINT}, {"encoding": "jsonParsed"}])
    ata = doc["value"][0]["pubkey"]
    print(f"attacker USDC loot account: {ata}")

    print("collecting the full signature list touching that account (paginated)...")
    before = None
    sigs = []
    while True:
        params = [ata, {"limit": 1000}]
        if before:
            params[1]["before"] = before
        page = rpc("getSignaturesForAddress", params)
        if not page:
            break
        sigs.extend(s["signature"] for s in page)
        before = page[-1]["signature"]
        if len(page) < 1000:
            break
    print(f"total: {len(sigs)}")

    random.seed(42)
    sample = random.sample(sigs, 35)
    print(f"\ndrawing a fixed, reproducible random sample of {len(sample)} (seed=42)")

    deltas = []
    for i, sig in enumerate(sample):
        tx = rpc("getTransaction", [sig, {"maxSupportedTransactionVersion": 0, "encoding": "jsonParsed"}])
        msg = tx["transaction"]["message"]
        keys = [k["pubkey"] if isinstance(k, dict) else k for k in msg["accountKeys"]]
        idx = keys.index(ata)
        meta = tx["meta"]
        pre = next((b["uiTokenAmount"]["uiAmount"] or 0 for b in meta["preTokenBalances"] if b["accountIndex"] == idx), 0)
        post = next((b["uiTokenAmount"]["uiAmount"] or 0 for b in meta["postTokenBalances"] if b["accountIndex"] == idx), 0)
        delta = post - pre
        deltas.append(delta)
        print(f"  {i:2d}  {sig}  delta={delta:+.6f} USDC")
        time.sleep(0.15)

    nonzero = [d for d in deltas if d > 0]
    print(f"\n{len(nonzero)} of {len(deltas)} sampled transactions moved USDC into the loot account "
          f"({len(nonzero)/len(deltas):.0%})")
    avg_all = sum(deltas) / len(deltas)
    naive_total = avg_all * len(sigs)
    print(f"mean delta across all {len(deltas)} sampled (incl. zero): {avg_all:.6f} USDC")
    print(f"naive extrapolation over all {len(sigs)} transactions: ${naive_total:,.2f}")
    reported = 500859.22
    print(f"Avici/DefiLlama's own reported figure: ${reported:,.2f}")
    print(f"naive extrapolation is {(naive_total / reported - 1):+.0%} off the reported figure")
    print("-> the sample's variance is too high (a handful of large withdrawals dominate a mostly-zero")
    print("   distribution) for 35 transactions to extrapolate a reliable independent total; see README.md")
