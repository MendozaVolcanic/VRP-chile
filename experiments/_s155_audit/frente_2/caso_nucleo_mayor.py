"""Caso: Nevados de Chillan 2026-10-18 06:48 VIIRS_NOAA21 (K), nucleo 8,9 MW contra cumulo 4,1 MW. Que pixeles suma el nucleo.
Ademas: cuantos records K de VIIRS 375 cambian de nivel MIROVA (umbrales 1/10/100 MW) entre cumulo y nucleo."""
import json, os, io, sys, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
def hav(a,b,c,d):
    R=6371.0; p1,p2=math.radians(a),math.radians(c); dp=p2-p1; dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2; return 2*R*math.asin(math.sqrt(x))
recs = json.load(open(os.path.join(ROOT,"data","mirova_equivalent","NevadosDeChillan.json"),encoding="utf-8"))["records"]
for dt, sen in [("2026-10-18 06:48","VIIRS_NOAA21"),("2026-10-18 07:50",None)]:
    for r in recs:
        if r["datetime_utc"] != dt or (sen and r["sensor"] != sen): continue
        pc = r["primary_cluster"] or {}
        print(dt, r["sensor"], "pc.vrp", pc.get("vrp_mw"), "pc.n", pc.get("n_pixels"), "f5", r.get("f5_core_vrp_mw"), "rec.vrp", r.get("vrp_mw"), "src", r.get("final_hotspot_source"), "pc keys", sorted(pc.keys()))
        for p in r.get("anomaly_pixels") or []:
            print("   px", round(p["lat"],4), round(p["lon"],4), "vrp", p.get("vrp_mw"), "bt", p.get("bt_k"), "d_centroide_km", round(hav(p["lat"],p["lon"],pc["centroid_lat"],pc["centroid_lon"]),2), {k:p[k] for k in p if k not in ("lat","lon","vrp_mw","bt_k")})
TIER = ["Isluga","Lascar","Lastarria","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Copahue","Llaima","Villarrica","PuyehueCordonCaulle","Chaiten"]
def lvl(x): return 0 if x<=0 else (1 if x<1 else 2 if x<10 else 3 if x<100 else 4)
cambios = []; n = 0
for v in TIER:
    for r in json.load(open(os.path.join(ROOT,"data","mirova_equivalent",v+".json"),encoding="utf-8"))["records"]:
        if r["datetime_utc"][:10] < "2026-09-18": continue
        s = r["sensor"]
        if not s.startswith("VIIRS") or s.endswith("_750") or r.get("distance_class") != "summit": continue
        pc = r.get("primary_cluster") or {}; f = r.get("f5_core_vrp_mw")
        if not (pc.get("vrp_mw") or 0) > 0 or not isinstance(f,(int,float)) or f <= 0: continue
        n += 1
        if lvl(f) != lvl(pc["vrp_mw"]): cambios.append((v, r["datetime_utc"], s, round(pc["vrp_mw"],3), round(f,3)))
print("\nK VIIRS375 summit con pc>0 y f5>0:", n, " cambian de nivel:", len(cambios))
for c in cambios: print("  ", c)
