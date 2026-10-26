"""Magnitud mostrada con K contra C0: nucleo F5' (f5_core_vrp_mw) vs cumulo (pc.vrp_mw) en VIIRS 375, y topes D9.
Pregunta 1: si el nucleo persistido no correspondiera al cumulo publicado con K, la razon f5/pc saldria fuera de (0, 1]
  o el campo faltaria; se cuentan ambas cosas por era.
Pregunta 2: si f5_core_vrp_mw no existiera en ningun record, n_con_f5 seria 0 (distinto de 'razon normal').
Control positivo: en C0 hay records con f5 < pc (el nucleo recorta el halo): si la medicion da 0 alli, esta muerta.
Denominador: records de los 11 Tier A con distance_class summit y pc.vrp_mw > 0; eras por fecha de observacion
C0 = 2026-07-20..2026-09-17, K = 2026-09-18..2026-10-19."""
import json, os, io, sys, statistics as st
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TIER = ["Isluga","Lascar","Lastarria","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Copahue","Llaima","Villarrica","PuyehueCordonCaulle","Chaiten"]
def era(d): return "K" if d >= "2026-09-18" else ("C0" if d >= "2026-07-20" else None)
def bucket(s): return "MODIS" if s.startswith("MODIS") else ("V750" if s.endswith("_750") else "V375")
acc = {}
for v in TIER:
    for r in json.load(open(os.path.join(ROOT,"data","mirova_equivalent",v+".json"),encoding="utf-8"))["records"]:
        e = era(r["datetime_utc"][:10]); pc = r.get("primary_cluster") or {}
        if not e or not pc or not (pc.get("vrp_mw") or 0) > 0: continue
        b = bucket(r["sensor"]); a = acc.setdefault((b,e), {"n":0,"f5":0,"ratios":[],"gt1":0,"cap5":0,"d9":0,"summit":0,"rec_gt_pc":0})
        a["n"] += 1
        if r.get("distance_class") == "summit": a["summit"] += 1
        if abs(pc["vrp_mw"] - 5.0) < 1e-9: a["cap5"] += 1
        if pc.get("d9_capped"): a["d9"] += 1
        if (r.get("vrp_mw") or 0) > pc["vrp_mw"] + 1e-9: a["rec_gt_pc"] += 1
        f = r.get("f5_core_vrp_mw")
        if isinstance(f,(int,float)) and r.get("distance_class") == "summit":
            a["f5"] += 1; q = f/pc["vrp_mw"]; a["ratios"].append(q)
            if q > 1 + 1e-9: a["gt1"] += 1
for (b,e),a in sorted(acc.items()):
    rs = a["ratios"]
    print(f"{b:5s} {e:3s} n_pc>0={a['n']:5d} summit={a['summit']:5d} con_f5(summit)={a['f5']:5d} f5/pc mediana={st.median(rs) if rs else float('nan'):.3f} f5<pc={sum(1 for q in rs if q<1-1e-9):4d} f5>pc={a['gt1']:3d} | pc==5.0: {a['cap5']} d9_capped: {a['d9']} | vrp_mw(record)>pc: {a['rec_gt_pc']}")

# Segunda parte: cuanto mas grande que el cumulo sale el nucleo cuando lo es (cuantiles de f5/pc > 1), por era y volcan.
import collections
print("\nf5/pc cuando > 1.001 (VIIRS 375 summit): cuantiles 50/90/max y casos > 1.5")
por = collections.defaultdict(list); ej = []
for v in TIER:
    for r in json.load(open(os.path.join(ROOT,"data","mirova_equivalent",v+".json"),encoding="utf-8"))["records"]:
        e = era(r["datetime_utc"][:10]); pc = r.get("primary_cluster") or {}
        if not e or bucket(r["sensor"]) != "V375" or r.get("distance_class") != "summit" or not (pc.get("vrp_mw") or 0) > 0: continue
        f = r.get("f5_core_vrp_mw")
        if not isinstance(f,(int,float)): continue
        q = f/pc["vrp_mw"]
        if q > 1.001: por[e].append(q); por[(e,v)].append(q)
        if q > 1.5 and e == "K": ej.append((v, r["datetime_utc"], r["sensor"], round(pc["vrp_mw"],3), round(f,3), round(q,2), pc.get("n_pixels"), len(r.get("anomaly_pixels") or [])))
for e in ("C0","K"):
    s = sorted(por[e])
    if s: print(e, "n", len(s), "p50", round(s[len(s)//2],3), "p90", round(s[int(.9*(len(s)-1))],3), "max", round(s[-1],2), ">1.5:", sum(1 for q in s if q>1.5))
for x in sorted(ej, key=lambda t:-t[5])[:15]: print("  K", x)
