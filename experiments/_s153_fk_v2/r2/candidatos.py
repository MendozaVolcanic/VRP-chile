"""R2 F/K: arma candidatos por categoria, con record de C0 y K y TIF de MIROVA emparejado por hora de adquisicion."""
import json, csv, math, sys, io, collections
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
T = "C:/Users/nmend/AppData/Local/Temp/claude/"
UNI = {"V1": [T + "v1_38639658446/union_2766/"],
       "V2": [T + "v2a_38648773684/union_2766/", T + "v2b_39033530622/union/"]}
C0, K = "_s146_ab_control", "_s149_ab_sin_test1_b22_max"
NOMBRE_TIF = {"NevadosDeChillan": "ChillanNevadosde"}

def bucket(s):
    if s.startswith("MODIS"): return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    if s.startswith("VIIRS"): return "VIIRS375"

def hav(a, b, c, d):
    R = 6371.0; p1, p2 = math.radians(a), math.radians(c)
    dp, dl = p2 - p1, math.radians(d - b)
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

recs = {}
for V, dirs in UNI.items():
    for d in dirs:
        for br in (C0, K):
            import glob, os
            for f in glob.glob(d + br + "/*.json"):
                vol = os.path.basename(f)[:-5]
                for r in json.load(open(f, encoding="utf-8"))["records"]:
                    b = bucket(r.get("sensor", ""))
                    if b: recs[(V, br, vol, r["sensor"], r["datetime_utc"])] = r

idx = collections.defaultdict(list)
for r in csv.DictReader(open(T + "r2_fk/index.csv")):
    if r["acquisition_utc"] and int(r["size_bytes"] or 0) > 0:
        idx[(r["volcano"], r["sensor"])].append(r)
md5n = collections.Counter(r["md5"] for v in idx.values() for r in v)

def tif(vol, b, dt):
    t = datetime.strptime(dt, "%Y-%m-%d %H:%M")
    best = None
    for r in idx.get((NOMBRE_TIF.get(vol, vol), b), []):
        a = datetime.fromisoformat(r["acquisition_utc"]).replace(tzinfo=None)
        dd = abs((a - t).total_seconds())
        if dd <= 15*60 and (best is None or dd < best[0]): best = (dd, r)
    return best

out = []
for V in ("V1", "V2"):
    for l in open(T + f"r3_fk/pasadas_{V}.jsonl"):
        p = json.loads(l); vol, sen, dt = p["k"]
        if not ("2026-05-01" <= dt < "2026-09-23"): continue
        rc = recs.get((V, C0, vol, sen, dt)); rk = recs.get((V, K, vol, sen, dt))
        pcC = (rc or {}).get("primary_cluster") or {}; pcK = (rk or {}).get("primary_cluster") or {}
        mov = None
        if pcC.get("centroid_lat") is not None and pcK.get("centroid_lat") is not None:
            mov = hav(pcC["centroid_lat"], pcC["centroid_lon"], pcK["centroid_lat"], pcK["centroid_lon"])
        tt = tif(vol, p["b"], dt)
        x = rc or rk or {}
        out.append(dict(V=V, vol=vol, sen=sen, dt=dt, b=p["b"], neg=p["neg"], alerta=p["alerta"], protA=p["protA"],
                        vrpA=p["vrpA"], snpp_ocr=p["snpp_ocr"], C0=p["pub_C0"], K=p["pub_K"],
                        zen=x.get("sensor_zenith_deg"), tbg=x.get("t_bg_k"), mov=mov,
                        pcC=(pcC.get("centroid_lat"), pcC.get("centroid_lon"), pcC.get("n_pixels"), pcC.get("vrp_mw"), pcC.get("geo_class")),
                        pcK=(pcK.get("centroid_lat"), pcK.get("centroid_lon"), pcK.get("n_pixels"), pcK.get("vrp_mw"), pcK.get("geo_class")),
                        tif=(tt[1]["tif_path"], tt[0], tt[1]["md5"], md5n[tt[1]["md5"]], tt[1]["acquisition_utc"]) if tt else None))
json.dump(out, open(T + "r2_fk/candidatos.json", "w"), indent=0)

def show(nombre, L):
    print(f"\n== {nombre}: {len(L)} (con TIF {sum(1 for c in L if c['tif'])}, TIF md5 unico {sum(1 for c in L if c['tif'] and c['tif'][3]==1)})")
    for c in L[:25]:
        print(c["V"], c["vol"], c["sen"], c["dt"], "zen", c["zen"], "tbg", c["tbg"], "vrpA", c["vrpA"], "mov", None if c["mov"] is None else round(c["mov"], 2), "tif", c["tif"] and (c["tif"][0].split('/')[-1], c["tif"][1], c["tif"][3]))

v375 = [c for c in out if c["b"] == "VIIRS375"]
show("1 neg limpio V375 borde>52 fondo<260, C0 pub K calla", [c for c in v375 if c["neg"] and c["C0"] and not c["K"] and c["zen"] and c["zen"] > 52 and c["tbg"] and c["tbg"] < 260 and c["tif"]])
show("2 neg limpio V375 nadir<36, C0 pub K calla", [c for c in v375 if c["neg"] and c["C0"] and not c["K"] and c["zen"] is not None and c["zen"] < 36 and c["tif"]])
show("3 protA V375 Lascar", [c for c in v375 if c["protA"] and c["vol"] == "Lascar"])
show("4 MODIS alerta K recupera (C0 0 K 1)", [c for c in out if c["b"] == "MODIS" and c["alerta"] and not c["C0"] and c["K"]])
show("5 alerta con mov>0.5", [c for c in out if c["alerta"] and c["mov"] and c["mov"] > 0.5])
