# Verificador S157: ¿cambia el pixel de mayor VRP (hotspot_*, final_hotspot) al encender el flag?
import json, math, sys, os
sys.path.insert(0, r"D:/vrp-trabajo/s157-lambda-b22"); sys.path.insert(0, r"D:/vrp-trabajo/s157-lambda-b22/scripts")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline.constants import C1, C2
import banco_paridad as bp
from auto_audit_weekly import detector_de_record, leer_frontera_k
L21, L22, K, A = 3.929, 3.959, 18.9, 1e6
P = lambda t, l: C1 / (l**5 * (math.exp(C2 / (l * t)) - 1))
inv = lambda L, l: C2 / (l * math.log(C1 / (L * l**5) + 1))
fr = leer_frontera_k(); n = nmulti = nswap = 0; casos = []
for vol in bp.VOLS:
    for r in json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))["records"]:
        if "MODIS" not in (r.get("sensor") or "") or detector_de_record(r, fr) != "K": continue
        ap = [p for p in (r.get("anomaly_pixels") or []) if p["vrp_mw"] > 0]
        n += 1
        if len(ap) < 2: continue
        nmulti += 1
        nuevos = []
        for p in ap:
            Lbg = P(p["bt_k"], L21) - p["vrp_mw"] * 1e6 / (K * A)
            if Lbg <= 0: nuevos.append(p["vrp_mw"]); continue
            tbk = inv(Lbg, L21)
            nuevos.append(K * A * (P(p["bt_k"], L22) - P(tbk, L22)) / 1e6)
        i_old = max(range(len(ap)), key=lambda i: ap[i]["vrp_mw"]); i_new = max(range(len(ap)), key=lambda i: nuevos[i])
        if i_old != i_new:
            nswap += 1; casos.append((vol, r["datetime_utc"], ap[i_old]["vrp_mw"], ap[i_new]["vrp_mw"], r.get("diag_L_bg_local_w_m2_sr_um") is not None))
print("records MODIS K", n, "con >=2 pixeles VRP>0", nmulti, "top cambia", nswap)
for c in casos: print(c)
