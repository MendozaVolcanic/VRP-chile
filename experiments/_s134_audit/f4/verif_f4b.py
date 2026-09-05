# -*- coding: utf-8 -*-
"""VERIFICADOR F4, parte B: sensibilidades. READ-ONLY."""
from __future__ import annotations
import io, json, math, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile"
sys.path.insert(0, os.path.join(REPO, "experiments"))

import f4_solape_ley_intermedia as M
from _s126_lib import SENSOR_MAP, bucket

out = {}

# --- A. sensor bucket: que sensores entran como v375 ---
d0 = json.load(io.open(os.path.expanduser(
    "~/ab_area/s133area-_s133_area_geoloc-Lascar/Lascar.json"), encoding="utf-8"))
recs = d0["records"] if isinstance(d0, dict) else d0
out["A_sensores_en_el_json"] = Counter(r.get("sensor") for r in recs).most_common()
out["A_bucket_de_cada_sensor"] = {s: bucket(s) for s in
                                  sorted(set(str(r.get("sensor")) for r in recs))}
out["A_SENSOR_MAP_gt"] = {k: v for k, v in SENSOR_MAP.items()}

# --- B. ground truth: snapshot congelado en vez del CSV vivo ---
gt_live, n_live = M.cargar_gt()
pares_live, _ = M.pares_de("_s133_area_geoloc", gt_live)


def resumen(ps, campo="razon_x_f"):
    r = {b: {"n": sum(1 for p in ps if p["bin"] == b),
             "med": M._mediana([p[campo] for p in ps if p["bin"] == b])}
         for b in M.BINS}
    xs = [p[campo] for p in ps]
    r["n_total"] = len(xs)
    r["cola_frac"] = sum(1 for x in xs if x > 2) / float(len(xs)) if xs else None
    return r


SNAP = os.path.join(REPO, "data", "mirova_reference", "mirova_v1_snapshot",
                    "registro_vrp_consolidado.csv")
M.FUENTES_GT = (SNAP, M.FUENTES_GT[1])
gt_snap, n_snap = M.cargar_gt()
pares_snap, _ = M.pares_de("_s133_area_geoloc", gt_snap)
out["B_gt_vivo_vs_snapshot"] = {
    "filas_alerta_nocturnas_vivo": n_live, "filas_alerta_nocturnas_snapshot": n_snap,
    "resumen_vivo": resumen(pares_live), "resumen_snapshot": resumen(pares_snap),
}

# --- C. sensibilidad a la tension S4 (el solape empieza a ~19 grados) ---
RE = 6371.0


def slant(th, H):
    t = math.radians(th); rh = RE + H
    return rh * math.cos(t) - math.sqrt(RE ** 2 - (rh * math.sin(t)) ** 2)


H = M.H_EFECTIVA_KM
# filas de solape que el modelo predice en theta=19 y que el ATBD dice que NO existen
OFFSET = 32 * (slant(19.0, H) / H) - 32


def f_S4(zen):
    th = M.theta_de_zenital(zen, H)
    r = slant(th, H) / H
    k = M.filas_entregadas(th)
    return min(1.0, (32.0 + OFFSET) / (k * r))


for p in pares_live:
    p["razon_x_f_S4"] = p["vrp_ours_mw"] * f_S4(p["zenital_deg"]) / p["vrp_mirova_mw"]
out["C_sensibilidad_S4"] = {
    "offset_filas": OFFSET,
    "f_S4_en_zenital_70": f_S4(70.0), "f_original_en_70": M.f_solape(70.0)[0],
    "resumen": resumen(pares_live, "razon_x_f_S4"),
}

# --- D. la cola: cruce bin cenital x tramo de MIROVA ---
cross = defaultdict(lambda: [0, 0])
for p in pares_live:
    t = "<0.5" if p["vrp_mirova_mw"] < 0.5 else (">=0.5")
    cross[(p["bin"], t)][0] += 1
    if p["razon_x_f"] > 2:
        cross[(p["bin"], t)][1] += 1
out["D_cola_bin_x_tramo"] = {"%s|%s" % k: {"n": v[0], "cola": v[1],
                                           "frac": v[1] / float(v[0]) if v[0] else None}
                             for k, v in sorted(cross.items())}
# dispersion por bin (la mediana en banda puede esconder una cola ancha)
for b in M.BINS:
    xs = sorted(p["razon_x_f"] for p in pares_live if p["bin"] == b)
    if len(xs) >= 15:
        q1 = xs[len(xs) // 4]; q3 = xs[3 * len(xs) // 4]
        out.setdefault("D_dispersion_por_bin", {})[b] = {
            "n": len(xs), "p25": q1, "med": M._mediana(xs), "p75": q3,
            "iqr_relativo": (q3 - q1) / M._mediana(xs)}
# lo mismo en el control, para saber si la cola del borde es NUEVA
for b in M.BINS:
    xs = sorted(p["razon"] for p in M.pares_de("_s133_area_control", gt_live)[0]
                if p["bin"] == b)
    if len(xs) >= 15:
        q1 = xs[len(xs) // 4]; q3 = xs[3 * len(xs) // 4]
        out.setdefault("D_dispersion_por_bin_control", {})[b] = {
            "n": len(xs), "p25": q1, "med": M._mediana(xs), "p75": q3,
            "iqr_relativo": (q3 - q1) / M._mediana(xs)}

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
with io.open(os.path.join(HERE, "verif_resultados_b.json"), "w", encoding="utf-8") as fh:
    fh.write(json.dumps(out, indent=1, ensure_ascii=False, default=str))
print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
