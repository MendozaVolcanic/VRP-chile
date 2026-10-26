# -*- coding: utf-8 -*-
"""F3: cuánto de la energía alertada DENTRO del inner_radius queda fuera del número publicado, por sensor.
MIROVA (código V750, H:241-248 y V:83-85) suma TODOS los alertados de su ventana; nosotros publicamos un cúmulo
(V750, MODIS) o el núcleo F5' (V375). Ventana 2026-03-01 a 2026-10-20, noche, records summit con cúmulo dentro del inner
y n_anomalous_pixels <= 100 (todos listados). Medida: publicado / Σ VRP de alertados a <= inner_radius_km del centro.
Instrumento: si el publicado fuera siempre la suma de los de dentro, la razón sería 1 en todas (control: se imprime la
fracción de pasadas con razón 1 exacta); si no hubiera píxeles dentro (dist_km ausente), la pasada sale (SIN DATO).
Uso: python -B cumulo_vs_inner.py <raiz>
"""
import json, os, sys
import numpy as np, pandas as pd, yaml
ROOT = sys.argv[1]
inner = {v["name"]: v.get("inner_radius_km", 10) for v in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
V = ["Villarrica", "Lascar", "Tupungatito", "PuyehueCordonCaulle", "Llaima", "Copahue", "NevadosDeChillan", "PlanchonPeteroa", "Isluga", "Lastarria", "Chaiten"]
def bucket(x):
    x = str(x or "").upper()
    return ("V750" if "750" in x else "V375") if "VIIRS" in x else "MODIS"
rows = []
for v in V:
    for r in json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", f"{v}.json"), encoding="utf-8"))["records"]:
        t = str(r["datetime_utc"])
        if t < "2026-03-01" or not (3 <= int(t[11:13]) <= 9):
            continue
        pc = r.get("primary_cluster") or {}
        px = r.get("anomaly_pixels") or []
        if r.get("distance_class") != "summit" or not pc or (pc.get("centroid_dist_km") or 0) > inner[v] or not px or len(px) != (r.get("n_anomalous_pixels") or 0):
            continue
        b = bucket(r.get("sensor"))
        e_in = sum(p["vrp_mw"] for p in px if p.get("dist_km") is not None and p["dist_km"] <= inner[v])
        n_in = sum(1 for p in px if p.get("dist_km") is not None and p["dist_km"] <= inner[v])
        f5 = r.get("f5_core_vrp_mw")
        pub = (f5 if (b == "V375" and isinstance(f5, (int, float)) and f5 > 0) else pc.get("vrp_mw") or 0)
        if e_in <= 0:
            continue
        rows.append({"vol": v, "b": b, "r": pub / e_in, "n_in": n_in, "pc_n": pc.get("n_pixels"), "spm": bool(pc.get("single_pixel_mode")), "e_in": e_in, "pub": pub})
D = pd.DataFrame(rows)
pd.set_option("display.width", 220)
T = D.groupby(["b", "vol"]).agg(n=("r", "size"), r_med=("r", "median"), r_sum=("pub", "sum"), e_sum=("e_in", "sum"), uno=("r", lambda x: float((np.isclose(x, 1, atol=1e-3)).mean())),
                                n_in_med=("n_in", "median"), pc_n_med=("pc_n", "median"), spm=("spm", "mean"))
T["r_sumas"] = T.r_sum / T.e_sum
print(T.drop(columns=["r_sum", "e_sum"]).round(3).to_string())
print(D.groupby("b").apply(lambda g: pd.Series({"n": len(g), "r_sumas": g.pub.sum() / g.e_in.sum(), "r_med": g.r.median()})).round(3).to_string())
