# -*- coding: utf-8 -*-
"""Paso 5: mismo objeto o el otro. Para cada movida, desde los records crudos de las uniones:
n_pixels del cumulo de cada brazo, modo de un solo pixel, pixel mas caliente (anomaly_pixels, top-100 de la escena,
mas los descartados por la cerca de store), y si el centroide de K cae sobre un pixel que C0 tambien marco (y al
reves). Si el centroide de K cae a menos de media celda de un pixel anomalo de C0, el objeto es el mismo y lo que
cambio es la agregacion del cumulo; si no, K publica en un lugar donde C0 no vio nada."""
import json, math, sys, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
B = Path(r"C:\Users\nmend\AppData\Local\Temp\claude")
RAICES = {"V1": [B / "v1_38639658446/union_2766"], "V2": [B / "v2a_38648773684/union_2766", B / "v2b_39033530622/union"]}
ARM = {"C0": "_s146_ab_control", "K": "_s149_ab_sin_test1_b22_max"}
CELDA = {"VIIRS375": 0.375, "VIIRS750": 0.75, "MODIS": 1.0}
T = json.load(open('s1_tabla.json', encoding='utf-8'))


def hav(a, b, c, d):
    R = 6371.0088
    p1, p2 = math.radians(a), math.radians(c)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def bucket(s):
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")


_c = {}
def recs(w, arm, vol):
    key = (w, arm, vol)
    if key not in _c:
        out = []
        for r in RAICES[w]:
            p = r / ARM[arm] / (vol + ".json")
            if p.exists(): out += json.load(open(p, encoding="utf-8"))["records"]
        _c[key] = out
    return _c[key]


res = []
for m in T:
    vol, s, t = m["vol"], m["s"], m["t"]
    row = {"k": m["k"], "w": m["w"], "prot_A": m["prot_A"]}
    got = {}
    for arm in ("C0", "K"):
        cand = [r for r in recs(m["w"], arm, vol) if r["datetime_utc"][:16] == t and bucket(r["sensor"]) == s
                and r["sensor"] == m["plataforma"]]
        # puede haber duplicados por la union de intentos: se toma el que tenga el centroide publicado
        tgt = m[arm]
        best = None
        for r in cand:
            pc = r.get("primary_cluster") or {}
            if pc.get("centroid_lat") is not None and abs(pc["centroid_lat"] - tgt["lat"]) < 1e-4 and abs(pc["centroid_lon"] - tgt["lon"]) < 1e-4:
                best = r; break
        if best is None and cand: best = cand[0]
        got[arm] = best
        if best is None: row[arm] = None; continue
        pc = best["primary_cluster"] or {}
        px = (best.get("anomaly_pixels") or []) + (best.get("discarded_anomaly_pixels") or [])
        hot = max(px, key=lambda p: p["vrp_mw"]) if px else None
        row[arm] = {"n_pc": pc.get("n_pixels"), "single": pc.get("single_pixel_mode"), "n_anom": best.get("n_anomalous_pixels"),
                    "n_px_guardados": len(px), "hot": (hot["lat"], hot["lon"], hot["vrp_mw"]) if hot else None,
                    "fh_source": best.get("final_hotspot_source"), "n_cand": len(cand)}
        row[arm + "_px"] = [(p["lat"], p["lon"]) for p in px]
    if got.get("C0") and got.get("K"):
        c = CELDA[s]
        def cerca(lat, lon, pxs):
            return min((hav(lat, lon, a, b) for a, b in pxs), default=None)
        row["K_centro_a_px_C0"] = cerca(m["K"]["lat"], m["K"]["lon"], row["C0_px"])
        row["C0_centro_a_px_K"] = cerca(m["C0"]["lat"], m["C0"]["lon"], row["K_px"])
        row["hot_C0_K_km"] = hav(*row["C0"]["hot"][:2], *row["K"]["hot"][:2]) if row["C0"]["hot"] and row["K"]["hot"] else None
        kc = row["K_centro_a_px_C0"]
        row["clase"] = ("mismo campo (K sobre pixel de C0)" if kc is not None and kc <= 0.75 * c else
                        ("K en lugar sin pixel de C0" if kc is not None else "sin pixeles"))
    del row["C0_px"]; del row["K_px"]
    res.append(row)
json.dump(res, open('s5_pixeles.json', 'w', encoding='utf-8'), indent=1)
for r in res:
    f = lambda x: ("%.2f" % x) if isinstance(x, float) else str(x)
    print("%-44s A=%d C0[n=%s 1px=%s src=%s nguard=%s] K[n=%s 1px=%s src=%s nguard=%s] Kcentro->pxC0 %s C0centro->pxK %s hotC0-hotK %s | %s" % (
        r["k"], r["prot_A"], r["C0"]["n_pc"], r["C0"]["single"], r["C0"]["fh_source"], r["C0"]["n_px_guardados"],
        r["K"]["n_pc"], r["K"]["single"], r["K"]["fh_source"], r["K"]["n_px_guardados"],
        f(r.get("K_centro_a_px_C0")), f(r.get("C0_centro_a_px_K")), f(r.get("hot_C0_K_km")), r.get("clase")))
print(collections.Counter(r.get("clase") for r in res))
print("protegidas:", collections.Counter(r.get("clase") for r in res if r["prot_A"]))
