# -*- coding: utf-8 -*-
"""S139 - prueba ortogonal: ¿el exceso crece con la magnitud de la anomalía?

LA IDEA, EN TÉRMINOS FÍSICOS. Cuanto más potente es la anomalía, más píxeles del sensor
supera el umbral y más grande es el cúmulo alertado. El píxel más CALIENTE sigue estando
sobre el foco pase lo que pase; el píxel más LEJANO se aleja a medida que el cúmulo crece.
O sea: si la web publica el más lejano, la distancia publicada tiene que despegarse de la
posición del foco cuando sube el VRP, y si publica el más caliente, no.

Esta prueba no depende del punto de origen (el VRP no tiene nada que ver con el rumbo), así
que es independiente de la sonda 07, donde el corrimiento de origen era el confusor.

La PENDIENTE esperada bajo la hipótesis "más lejano" no se inventa: se mide en el archivo
OSF del propio MIROVA, donde `Max_Dist` y el píxel más caliente conviven en la misma fila.
Bajo la hipótesis "más caliente" la pendiente es exactamente 0.

Read-only.
"""
import io
import json
import math
import os
import sys

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
OSF = os.path.join(ROOT, "data", "mirova_reference", "VRP_GLOBAL_ARCHIVE_2025.csv")
CHILE = ["Láscar", "Chaitén", "Puyehue-Cordón Caulle", "Lastarria", "Villarrica",
         "Chillán, Nevados de", "Isluga", "Copahue", "Planchón-Peteroa", "Llaima"]
CORTE_KM = 1.0


def pendiente(y, x, n_boot=2000, semilla=139):
    """y ~ a + m·log10(x); devuelve m y su IC bootstrap."""
    lx = np.log10(np.clip(x, 1e-3, None))
    X = np.column_stack([np.ones_like(lx), lx])
    c, *_ = np.linalg.lstsq(X, y, rcond=None)
    rng = np.random.default_rng(semilla)
    b = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        cc, *_ = np.linalg.lstsq(X[i], y[i], rcond=None)
        b.append(cc[1])
    b = np.array(b)
    return {"n": int(len(y)), "pendiente_km_por_decada": round(float(c[1]), 3),
            "IC95": [round(float(np.percentile(b, 2.5)), 3),
                     round(float(np.percentile(b, 97.5)), 3)],
            "constante_km": round(float(c[0]), 3)}


def por_bins(y, x, bordes):
    out = []
    for lo, hi in zip(bordes[:-1], bordes[1:]):
        m = (x >= lo) & (x < hi)
        if m.sum() < 8:
            continue
        out.append({"vrp_mw": f"[{lo},{hi})", "n": int(m.sum()),
                    "exceso_mediano_km": round(float(np.median(y[m])), 3)})
    return out


def main():
    BINS = [0.0, 0.3, 1.0, 3.0, 10.0, 1e9]
    R = {"_meta": {
        "modelo": "exceso ~ a + m·log10(VRP_MW)",
        "esperado_si_mas_caliente": "pendiente 0",
        "esperado_si_mas_lejano": "pendiente > 0, calibrada abajo sobre el archivo OSF",
        "corte_km": CORTE_KM}}

    # ── Calibración en el archivo del propio MIROVA ──────────────────────────
    d = pd.read_csv(OSF)
    d = d[d.Volc_Name.isin(CHILE)].copy()
    d["res"] = d.Resolution.round()
    d = d[d.res == 375].dropna(subset=["LAT", "LON", "Max_Dist", "VRP"])
    la0, lo0 = d.Volc_LAT.values, d.Volc_LON.values
    dy = (d.LAT.values - la0) * 110.574
    dx = (d.LON.values - lo0) * 111.320 * np.cos(np.radians(la0))
    dhot = np.hypot(dx, dy)
    exceso = d.Max_Dist.values / 1000.0 - dhot
    vrp_mw = d.VRP.values / 1e6
    ok = (np.abs(exceso) <= CORTE_KM) & (vrp_mw > 0)
    R["calibracion_OSF_VIIRS375"] = {
        "si_publicara_max_dist": pendiente(exceso[ok], vrp_mw[ok]),
        "si_publicara_mas_caliente": {"pendiente_km_por_decada": 0.0,
                                      "nota": "exacto por construcción"},
        "por_bins": por_bins(exceso[ok], vrp_mw[ok], BINS),
        "npix_mediana_por_bin": [
            {"vrp_mw": f"[{lo},{hi})",
             "npix_mediana": float(np.median(d.Npix.values[ok][
                 (vrp_mw[ok] >= lo) & (vrp_mw[ok] < hi)]))}
            for lo, hi in zip(BINS[:-1], BINS[1:])
            if ((vrp_mw[ok] >= lo) & (vrp_mw[ok] < hi)).sum() >= 8]}

    # ── La medición sobre la web ────────────────────────────────────────────
    det = json.load(open(os.path.join(AQUI, "06_hipotesis_caliente_vs_lejano.json"),
                         encoding="utf-8"))["detalle"]
    w = pd.DataFrame(det)
    for c in ("resid_km", "vrp_mw", "d_foco_km"):
        w[c] = pd.to_numeric(w[c], errors="coerce")
    w = w.dropna(subset=["resid_km", "vrp_mw"])
    w = w[(np.abs(w.resid_km) <= CORTE_KM) & (w.vrp_mw > 0)]
    R["web"] = {
        "global": pendiente(w.resid_km.values, w.vrp_mw.values),
        "por_bins": por_bins(w.resid_km.values, w.vrp_mw.values, BINS),
        "solo_VIIRS375": pendiente(*(lambda g: (g.resid_km.values, g.vrp_mw.values))(
            w[w.sensor == "VIIRS375"])) if (w.sensor == "VIIRS375").sum() >= 25 else None,
        "foco_cerca_<=5km": pendiente(*(lambda g: (g.resid_km.values, g.vrp_mw.values))(
            w[w.d_foco_km <= 5])) if (w.d_foco_km <= 5).sum() >= 25 else None}

    out = os.path.join(AQUI, "08_exceso_crece_con_la_magnitud.json")
    json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    print("escrito:", out)
    print(json.dumps(R, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
