# Adversarial pass: independent code, different providers where possible, raw JSON-RPC only.
import json, urllib.request, time, re
UA={"content-type":"application/json","user-agent":"Mozilla/5.0"}
def rpc(url,m,p):
    r=json.load(urllib.request.urlopen(urllib.request.Request(url,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers=UA),timeout=90))
    if "error" in r: raise Exception(r["error"])
    return r["result"]
DS="https://bsc-dataseed.binance.org"; DS2="https://bsc-dataseed1.defibit.io"; DRPC="https://bsc.drpc.org"; BLAST="https://bsc-mainnet.public.blastapi.io"
TX="0xcc71a3bb131c73462b0f25533070113a63c85e942a22e18bc945eec184eb5799"
BTX="0xaa242a47f4cc074e59cbc7d65309b1f21202aaa3"; USDT="0x55d398326f99059ff775485246999027b3197955"
V1="0x1e647faadb05f2124bfccfc003edc06d1a90bf5d"; V2="0x9a7a92240fbac4030b65a6e61239928d6bcc716f"
EX="0x371700b96b484b501812e92cab5a388d105a922d"; EOA="0x67b2f08683a735cfe6f6e57fa86909b62218c2a1"
print("A. receipt re-fetched from", DS2)
rc=rpc(DS2,"eth_getTransactionReceipt",[TX])
print("  status",rc["status"],"block",int(rc["blockNumber"],16),"logs",len(rc["logs"]))
T="0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
bal={}
for l in rc["logs"]:
    if l["topics"][0]!=T or len(l["topics"])!=3: continue
    tok=l["address"]; f="0x"+l["topics"][1][26:]; t="0x"+l["topics"][2][26:]; v=int(l["data"],16)
    bal[(tok,f)]=bal.get((tok,f),0)-v; bal[(tok,t)]=bal.get((tok,t),0)+v
for who,name in ((V1,"V1"),(V2,"V2"),(EX,"executor"),(EOA,"EOA"),("0xaa2ea785744b123b1e8a1679c8e7ab9b255aad94","treasury"),("0xa5db84d7bccb799fb31bd3c417d04d5bc29da96d","target pool"),("0x238a358808379702088667322f80ac48bad5e6c4","0x238a...e6c4"),("0x8f73b65b4caaf64fba2af91cc5d4a2a1318e5d8c","0x8f73...5d8c")):
    print(f"  net in tx {name:14s} BTX {bal.get((BTX,who),0)/1e18:+,.6f}  USDT {bal.get((USDT,who),0)/1e18:+,.6f}")
print("  EOA net USDT exact wei:",bal.get((USDT,EOA),0))
# largest contributor to the attacker's USDT: log with max USDT to executor from non-flash source
big=max((l for l in rc["logs"] if l["topics"][0]==T and l["address"]==USDT and "0x"+l["topics"][2][26:]==EX and "0x8f73" not in l["topics"][1]), key=lambda l:int(l["data"],16))
print("  largest USDT inflow to executor: log",int(big["logIndex"],16),"from 0x"+big["topics"][1][26:],int(big["data"],16)/1e18,"txHash matches exploit:",big["transactionHash"]==TX)
# what did the executor send to that same address in the same tx
paired=[(int(l["logIndex"],16),l["address"],int(l["data"],16)/1e18) for l in rc["logs"] if l["topics"][0]==T and "0x"+l["topics"][2][26:]=="0x"+big["topics"][1][26:] and "0x"+l["topics"][1][26:]==EX]
print("  executor -> same counterparty in tx:",paired)

print("\nB. historical balances via drpc (different archive provider) and via log arithmetic")
def bal_of(url,tok,who,block):
    return int(rpc(url,"eth_call",[{"to":tok,"data":"0x70a08231"+"0"*24+who[2:]},block]),16)
N=int(rc["blockNumber"],16)
for who,name in ((V1,"V1"),(V2,"V2")):
    now=bal_of(DS,BTX,who,"latest")
    try:
        pre=bal_of(DRPC,BTX,who,hex(N-1)); src="drpc"
    except Exception as e:
        time.sleep(3)
        try: pre=bal_of(DRPC,BTX,who,hex(N-1)); src="drpc(retry)"
        except Exception as e2: pre=None; src="drpc failed: "+str(e2)[:60]
    print(f"  {name}: latest (dataseed) {now/1e18:,.6f}; pre-block ({src}) {pre/1e18 if pre else None}; pre implied by latest - tx net = {(now-bal.get((BTX,who),0))/1e18:,.6f} (valid only if no later BTX transfers)")
    time.sleep(2)

print("\nC. paused() and treasury at latest via blastapi (the script used dataseed for this)")
for who,name in ((V1,"V1"),(V2,"V2")):
    print(" ",name,"paused",int(rpc(BLAST,"eth_call",[{"to":who,"data":"0x5c975abb"},"latest"]),16),"owner 0x"+rpc(BLAST,"eth_call",[{"to":who,"data":"0x8da5cb5b"},"latest"])[26:])

print("\nD. skeptic check on the 23 'legitimate depositors'")
recs=json.load(open("records_pre_exploit.json"))
owner="0x62382d13b909b611c17b54eb19f8e5bc3d9c1e24"; treas="0xaa2ea785744b123b1e8a1679c8e7ab9b255aad94"
openusers=[]
for name in ("V1","V2"):
    for r in recs[name]:
        if not r[8]: openusers.append((name,r[0],r[1].lower(),r[4]-r[7],time.strftime('%Y-%m-%d',time.gmtime(r[5]))))
addrs={u for _,_,u,_,_ in openusers}
print("  open records",len(openusers),"distinct addresses",len(addrs),"any = owner/treasury/attacker/executor:",bool(addrs & {owner,treas,EOA,EX}))
print("  addresses in both contracts:",len({u for n,_,u,_,_ in openusers if n=="V1"} & {u for n,_,u,_,_ in openusers if n=="V2"}))
big=max(openusers,key=lambda x:x[3]); print("  largest open record:",big)
code=rpc(DS,"eth_getCode",[big[2],"latest"]); print("  largest open depositor code size:",(len(code)-2)//2, "(0 = EOA)")
nonce=int(rpc(DS,"eth_getTransactionCount",[big[2],"latest"]),16); print("  its nonce:",nonce)
# re-simulate its claim via blastapi and dataseed
sel="0x62abebce"+"0"*62+"20"+"0"*63+"1"+hex(big[1])[2:].rjust(64,"0") if big[0]=="V1" else "0x4e71d92d"
tgt=V1 if big[0]=="V1" else V2
for url in (DS,BLAST):
    try: rpc(url,"eth_call",[{"from":big[2],"to":tgt,"data":sel},"latest"]); print("  claim sim",url,"SUCCEEDS")
    except Exception as e: print("  claim sim",url,"reverts",str(e)[:120])

print("\nE. price move from the swap log itself vs slot0 before (drpc)")
for l in rc["logs"]:
    if l["address"]=="0xa5db84d7bccb799fb31bd3c417d04d5bc29da96d" and l["topics"][0].startswith("0x19b47279"):
        w=[l["data"][2+64*k:2+64*(k+1)] for k in range(7)]
        sp=int(w[2],16); print("  swap log",int(l["logIndex"],16),"USDT/BTX after",(2**96/sp)**2)
try:
    s0=rpc(DRPC,"eth_call",[{"to":"0xa5db84d7bccb799fb31bd3c417d04d5bc29da96d","data":"0x3850c7bd"},hex(N-1)])
    sp=int(s0[2:66],16); print("  slot0 at N-1 via drpc: USDT/BTX",(2**96/sp)**2)
except Exception as e: print("  drpc slot0 failed",str(e)[:80])

print("\nF. executor bytecode from dataseed, raw PUSH32 selector scan")
code=rpc(DS,"eth_getCode",[EX,"latest"])[2:]
for sel,sig in (("4e71d92d","claim()"),("3ccfd60b","withdraw()"),("62abebce","claimBatch(uint256[])"),("2e1a7d4d","withdraw(uint256)")):
    print(" ",sig,("7f"+sel+"0"*56) in code)

print("\nG. Ethereum DAI via a third endpoint (cloudflare / llamarpc)")
for url in ("https://cloudflare-eth.com","https://eth.llamarpc.com","https://ethereum-rpc.publicnode.com"):
    try:
        d=int(rpc(url,"eth_call",[{"to":"0x6b175474e89094c44da98b954eedeac495271d0f","data":"0x70a08231"+"0"*24+EOA[2:]},"latest"]),16)
        n=int(rpc(url,"eth_getTransactionCount",[EOA,"latest"]),16); b=int(rpc(url,"eth_blockNumber",[]),16)
        print(" ",url,"block",b,"DAI",d/1e18,"nonce",n); break
    except Exception as e: print(" ",url,"failed",str(e)[:60])
