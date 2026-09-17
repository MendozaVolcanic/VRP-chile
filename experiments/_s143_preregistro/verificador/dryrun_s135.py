import sys, io, json, collections, math, random
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT/"scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import banco_paridad as bp
V = ("2026-06-01","2026-08-31")
D = ROOT/"experiments/_s143_preregistro/_dl_referencia"
filas = bp.cargar_referencia_unificada(D/"registro_vrp_consolidado.csv", D/"registro_vrp_ocr.csv")
coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, V)
A = ROOT/"experiments/_artefactos_ab"
VOLS = ["Isluga","Lascar","Lastarria","PuyehueCordonCaulle","PlanchonPeteroa","Tupungatito"]
ARMS = {"A":"_s135_ab_a_control","B":"_s135_ab_b_nokeeppeak","D":"_s135_ab_d_ambos"}
def load(arm, vol):
    u = {}
    for run in ("34173711390","34208191011"):
        p = A/f"s135ab-{arm}-{vol}__run{run}"/f"{vol}.json"
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            u[(r["datetime_utc"], r["sensor"])] = r
    return list(u.values())
def publica_en_crater(r, inn):
    pc = r.get("primary_cluster") or {}
    vrp = pc.get("vrp_mw") or 0.0; cd = pc.get("centroid_dist_km"); dc = r.get("distance_class")
    return (0 < vrp <= 50000 and cd is not None and cd <= inn and (not dc or dc == "summit"))
res = {}
lost12 = {("Isluga","2026-07-01"),("Isluga","2026-07-16"),("Isluga","2026-08-19"),("Lastarria","2026-07-02"),("Lastarria","2026-08-28"),("PlanchonPeteroa","2026-06-22"),("PlanchonPeteroa","2026-06-26"),("PlanchonPeteroa","2026-07-24"),("PlanchonPeteroa","2026-08-09"),("PlanchonPeteroa","2026-08-24"),("Tupungatito","2026-07-07"),("Tupungatito","2026-08-01")}
allrecs = {}
for L, arm in ARMS.items():
    recs, casos = [], []
    for vol in VOLS:
        for r in load(arm, vol):
            b = bp.bucket(r.get("sensor"))
            if b != "VIIRS375" or not (V[0] <= r["datetime_utc"][:10] <= V[1]): continue
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            lat, lon = coords[vol]
            if bp.es_pasada_diurna_descartada(b, lat, lon, dt): continue
            recs.append({"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"), "key": r["datetime_utc"], "ev": publica_en_crater(r, inner[vol]), "f5": r.get("f5_core_vrp_mw")})
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat","lon","vrp_mw","bt_k")} for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos)
    for rec, p in zip(recs, pred):
        rec["pub"] = p[4]
    bp.etiquetar(recs, por_vb, ns, nv)
    allrecs[L] = {(r["vol"], r["key"]): r for r in recs}
    c = collections.Counter()
    for r in recs:
        if r["lab"] == "neg_limpio":
            c["neg"] += 1; c["neg_pub"] += r["pub"]; c["neg_ev"] += r["ev"]
        if r["lab"] == "pos":
            c["pos"] += 1; c["pos_pub"] += r["pub"]
        if r["pub"] != int(r["ev"]): c["pred_disagree"] += 1
    c["n"] = len(recs); c["f5_present_pub"] = sum(1 for r in recs if r["pub"] and r["f5"] is not None); c["pub"] = sum(r["pub"] for r in recs)
    print(L, dict(c))
    for (vol, n) in sorted(lost12):
        rr = [r for r in recs if r["vol"]==vol and r["noche"]==n]
        print("   ", vol, n, "dash_pub", max([r["pub"] for r in rr] or [0]), "ev_pub", max([int(r["ev"]) for r in rr] or [0]))
# paired neg by stratum A vs D, B
FOC = {"Lascar","Lastarria","Isluga","PlanchonPeteroa","PuyehueCordonCaulle"}
for L in ("B","D"):
    for est in ("focal","nevado"):
        keys = [k for k,r in allrecs["A"].items() if r["lab"]=="neg_limpio" and ((k[0] in FOC) == (est=="focal")) and k in allrecs[L]]
        a = sum(allrecs["A"][k]["pub"] for k in keys); d = sum(allrecs[L][k]["pub"] for k in keys)
        print(L, est, "n", len(keys), "ctrl", a, "arm", d)
