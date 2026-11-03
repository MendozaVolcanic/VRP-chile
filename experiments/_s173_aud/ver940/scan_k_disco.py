import json, subprocess, collections, sys
vols = ["Lascar","PuyehueCordonCaulle","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","Chaiten","Villarrica","NevadosDeChillan","Llaima","Copahue"]
tramos = {"F26":("2026-02-01","2026-03-31"),"DM":("2026-10-01","2026-10-16"),"R25":("2025-02-15","2025-12-31")}
def b(s):
    s=s or ""
    return "MODIS" if s.startswith("MODIS") else ("V750" if s.endswith("_750") else "V375") if s.startswith("VIIRS") else None
tot=collections.Counter(); proc=collections.Counter(); keys=collections.Counter(); dup=collections.Counter(); volkey=0
for v in vols:
    raw = subprocess.run(["git","show",f"origin/main:data/mirova_equivalent/{v}.json"],capture_output=True).stdout
    d=json.loads(raw)
    if d.get("volcano")==v: volkey+=1
    seen=set()
    for r in d.get("records",[]):
        dt=(r.get("datetime_utc") or "")[:10]
        for t,(a,z) in tramos.items():
            if a<=dt<=z:
                k=(t,b(r.get("sensor")),str(r.get("via_codigo_mirova")))
                tot[k]+=1
                proc[(t,b(r.get("sensor")),(r.get("processed_utc") or "")[:10])]+=1
                kk=(r.get("sensor"),r.get("datetime_utc"))
                if kk in seen: dup[(v,t)]+=1
                seen.add(kk)
print("volcano key present in", volkey, "of", len(vols))
print("--- (tramo, sensor, via_codigo_mirova): n")
for k in sorted(tot): print(k, tot[k])
print("--- processed_utc por tramo/sensor (top 6 por grupo)")
g=collections.defaultdict(list)
for (t,s,p),n in proc.items(): g[(t,s)].append((n,p))
for k in sorted(g): print(k, sorted(g[k],reverse=True)[:6])
print("--- duplicados (vol,tramo):", dict(dup))
