"""Clasifica cada par de records MODIS que difiere entre dos intentos del mismo commit.

Pregunta: la diferencia se explica entera por empates EXACTOS (a la precision guardada)
en el VRP por pixel, en el borde del top-100 o en el primer puesto?
"""
import json, glob
from collections import Counter
BASE = "C:/Users/nmend/AppData/Local/Temp/claude"
pares = [("v1_38639658446", "i1", "i3"), ("v2a_38648773684", "i1", "i2"), ("w2a_38853230521", "i1", "i2")]
ESCALARES_PIPE = ["n_anomalous_pixels", "t_bg_k", "t_max_k", "diag_sigma_bg_k", "diag_nti_max", "diag_mu_dnti",
                  "diag_sd_dnti", "diag_n_first_pass_pixels", "diag_n_second_pass_recapture", "test1_k_observed",
                  "n_test1_pixels", "diag_L_bg_w_m2_sr_um", "diag_L_bg_local_w_m2_sr_um", "n_hotspots_clustered"]


def idx(root):
    out = {}
    for p in glob.glob(root + "/**/*.json", recursive=True):
        parts = p.replace("\\", "/").split("/")
        if parts[-2].startswith("_s1"):
            out[parts[-2] + "/" + parts[-1]] = p
    return out


clases = Counter()
tot = 0
escalar_dif = Counter()
detalles = []
for run, a, b in pares:
    A, B = idx(f"{BASE}/{run}/{a}"), idx(f"{BASE}/{run}/{b}")
    for k in sorted(set(A) & set(B)):
        ra = {(r["sensor"], r["datetime_utc"]): r for r in json.load(open(A[k]))["records"] if "MODIS" in r["sensor"]}
        rb = {(r["sensor"], r["datetime_utc"]): r for r in json.load(open(B[k]))["records"] if "MODIS" in r["sensor"]}
        for kk in sorted(set(ra) & set(rb)):
            x, y = ra[kk], rb[kk]
            tot += 1
            for f in ESCALARES_PIPE:
                if x.get(f) != y.get(f):
                    escalar_dif[f] += 1
            px, py = x.get("anomaly_pixels") or [], y.get("anomaly_pixels") or []
            sx = [(p["lat"], p["lon"]) for p in px]
            sy = [(p["lat"], p["lon"]) for p in py]
            if sx == sy and x.get("vrp_mw") == y.get("vrp_mw"):
                continue
            setx, sety = set(sx), set(sy)
            onlyx = [p for p in px if (p["lat"], p["lon"]) not in sety]
            onlyy = [p for p in py if (p["lat"], p["lon"]) not in setx]
            borde = {px[-1]["vrp_mw"], py[-1]["vrp_mw"]} if px and py else set()
            # valor (vrp, bt) de los pixeles que entran o salen
            vals = {(p["vrp_mw"], p["bt_k"]) for p in onlyx + onlyy}
            borde_ok = all(p["vrp_mw"] in borde for p in onlyx + onlyy) and len({v for v, _ in vals}) <= 1
            top_cambia = bool(px and py and sx[0] != sy[0])
            top_empata = top_cambia and px[0]["vrp_mw"] == py[0]["vrp_mw"] and px[0]["bt_k"] == py[0]["bt_k"]
            if top_cambia and not top_empata:
                c = "top_cambia_SIN_empate"
            elif top_cambia:
                c = "top_empate" + ("+borde_empate" if (onlyx or onlyy) and borde_ok else ("+borde_NO" if onlyx or onlyy else ""))
            elif onlyx or onlyy:
                c = "borde_empate" if borde_ok else "borde_NO_explicado"
            elif setx == sety:
                # mismo conjunto, mismo top: orden interno o solo vrp_mw
                c = "solo_orden_interno" if sx != sy else "solo_vrp_mw"
            clases[c] += 1
            if not c.startswith("borde_empate") and c != "solo_orden_interno":
                detalles.append((run, k, kk, c, x.get("vrp_mw"), y.get("vrp_mw"), x.get("final_hotspot_source"), y.get("final_hotspot_source"),
                                 px[0] if px else None, py[0] if py else None))
print("pares MODIS comparados", tot)
print("clases de diferencia", dict(clases))
print("escalares del pipeline que difieren (sobre todos los pares)", dict(escalar_dif))
for d in detalles:
    print(d)
