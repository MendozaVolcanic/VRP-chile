# -*- coding: utf-8 -*-
"""S139 - ¿cuánto se separan `Max_Dist` y la distancia al píxel más caliente?

POR QUÉ. El esquema OSF v2.5 define dos cosas distintas para la misma fila-pasada:
`LAT/LON` es el píxel alertado MÁS CALIENTE y `Max_Dist` es la distancia de la cumbre
al píxel alertado MÁS LEJANO. La web publica UN solo número de distancia por pasada y
no dice cuál de los dos es. Antes de averiguar cuál, conviene saber cuánto importa:
si en los volcanes chilenos las dos cantidades casi siempre coinciden (porque el cúmulo
es de uno o dos píxeles), la pregunta es académica; si se separan decenas de kilómetros,
decide si una fila FALSO_POSITIVO puede tener el cráter adentro.

Esta sonda es EXÓGENA: usa el archivo del propio MIROVA (OSF v2.5), donde los dos
campos conviven en la misma fila, así que la comparación no depende de ningún supuesto
nuestro. Read-only.
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


def hav_km(la1, lo1, la2, lo2):
    R = 6371.0088
    p1, p2 = np.radians(la1), np.radians(la2)
    dp = p2 - p1
    dl = np.radians(lo2 - lo1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def main():
    d = pd.read_csv(OSF)
    n_total = len(d)
    d = d[d.Volc_Name.isin(CHILE)].copy()
    d["t"] = pd.to_datetime(d.timeUTC, format="%d/%m/%Y %H:%M", errors="coerce")
    d["d_hot_km"] = hav_km(d.Volc_LAT.values, d.Volc_LON.values,
                           d.LAT.values, d.LON.values)
    d["max_dist_km"] = d.Max_Dist / 1000.0
    d["delta_km"] = d.max_dist_km - d.d_hot_km
    d = d.dropna(subset=["d_hot_km", "max_dist_km"])

    # Resolución nominal del sensor: la fila la trae en metros.
    d["res"] = d.Resolution.round().astype(int)
    R = {"_meta": {
        "fuente": os.path.relpath(OSF, ROOT),
        "filas_totales_archivo": int(n_total),
        "volcanes": CHILE,
        "ventana": [str(d.t.min()), str(d.t.max())],
        "definiciones": {
            "d_hot_km": "haversine(Volc_LAT/LON, LAT/LON) = cumbre -> píxel alertado MÁS CALIENTE",
            "max_dist_km": "Max_Dist/1000 = cumbre -> píxel alertado MÁS LEJANO (campo del esquema)",
            "delta_km": "max_dist_km - d_hot_km; por definición >= 0 salvo redondeo"},
        "n_filas_chile": int(len(d))}}

    def resumen(sel, etiqueta):
        if len(sel) == 0:
            return {"n": 0}
        delta = sel.delta_km.values
        return {
            "etiqueta": etiqueta,
            "n": int(len(sel)),
            "npix_mediana": float(np.median(sel.Npix)),
            "npix_p90": float(np.percentile(sel.Npix, 90)),
            "npix_igual_1_pct": round(100.0 * float((sel.Npix == 1).mean()), 1),
            "d_hot_mediana_km": round(float(np.median(sel.d_hot_km)), 3),
            "max_dist_mediana_km": round(float(np.median(sel.max_dist_km)), 3),
            "delta_mediana_km": round(float(np.median(delta)), 3),
            "delta_p90_km": round(float(np.percentile(delta, 90)), 3),
            "delta_max_km": round(float(np.max(delta)), 3),
            "coinciden_<=0.5km_pct": round(100.0 * float((np.abs(delta) <= 0.5).mean()), 1),
            "coinciden_<=1km_pct": round(100.0 * float((np.abs(delta) <= 1.0).mean()), 1),
            "delta_negativo_pct": round(100.0 * float((delta < -0.05).mean()), 2),
        }

    R["global_chile"] = resumen(d, "todas las filas Chile")
    R["por_resolucion"] = {str(r): resumen(d[d.res == r], f"Resolution={r} m")
                           for r in sorted(d.res.unique())}
    R["por_volcan"] = {v: resumen(d[d.Volc_Name == v], v) for v in CHILE}
    R["por_clase"] = {str(c): resumen(d[d["class"] == c], f"class={c}")
                      for c in sorted(d["class"].dropna().unique())}
    # Estratificado por tamaño del cúmulo: es el mecanismo que separa las dos cifras.
    for lo, hi, nom in [(1, 1, "npix=1"), (2, 3, "npix 2-3"), (4, 10, "npix 4-10"),
                        (11, 10 ** 9, "npix>=11")]:
        R.setdefault("por_npix", {})[nom] = resumen(
            d[(d.Npix >= lo) & (d.Npix <= hi)], nom)

    # ¿Qué fracción de filas tendría el cráter "adentro" si se publicara Max_Dist?
    # Proxy: filas donde max_dist > 5 km pero el píxel más caliente está a < 5 km.
    for radio in (3, 5, 10):
        sel = d[(d.max_dist_km > radio) & (d.d_hot_km <= radio)]
        R.setdefault("crater_adentro_pero_maxdist_lejos", {})[f"radio_{radio}km"] = {
            "n": int(len(sel)),
            "pct_de_chile": round(100.0 * len(sel) / len(d), 2),
            "de_las_que_superan_el_radio_por_maxdist_pct": round(
                100.0 * len(sel) / max(1, int((d.max_dist_km > radio).sum())), 2)}

    # Cuantización de Max_Dist (¿pasos de celda?) sobre VIIRS 375 m y MODIS 1 km.
    for r in sorted(d.res.unique()):
        v = np.sort(np.unique(np.round(d[d.res == r].max_dist_km.values, 3)))
        v = v[v > 0]
        R.setdefault("cuantizacion_max_dist", {})[str(r)] = {
            "n_valores_unicos": int(len(v)),
            "primeros_20_km": [round(float(x), 3) for x in v[:20]],
            "paso_minimo_km": round(float(np.min(np.diff(v))), 4) if len(v) > 1 else None}

    out = os.path.join(AQUI, "01_osf_maxdist_vs_hotpixel.json")
    json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("escrito:", out)
    print()
    print("GLOBAL CHILE:", json.dumps(R["global_chile"], ensure_ascii=False, indent=1))
    print()
    for k, v in R["por_npix"].items():
        print(f"  {k:10s} n={v['n']:6d}  delta mediana {v.get('delta_mediana_km')} km  "
              f"coinciden<=0.5km {v.get('coinciden_<=0.5km_pct')}%")
    print()
    print("crater adentro / maxdist lejos:",
          json.dumps(R["crater_adentro_pero_maxdist_lejos"], ensure_ascii=False))


if __name__ == "__main__":
    main()
