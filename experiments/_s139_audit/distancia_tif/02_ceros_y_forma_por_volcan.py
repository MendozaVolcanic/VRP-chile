# -*- coding: utf-8 -*-
"""S139 - el discriminante de los CEROS: ¿la web publica el más caliente o el más lejano?

EL FENÓMENO. Una pasada con anomalía tiene un cúmulo de píxeles alertados. El píxel más
caliente casi siempre cae sobre el cráter, es decir sobre el nodo central de la grilla:
su distancia a la cumbre es CERO. El píxel más LEJANO del mismo cúmulo sólo puede estar
a cero si el cúmulo es de un único píxel y además ese píxel es el central. O sea: las dos
definiciones se separan de manera brutal justo en el valor 0, y el valor 0 se puede contar
sin ningún supuesto.

EL INSTRUMENTO. Se compara la fracción de ceros en tres series de la MISMA familia de
volcanes y sensores:
  (a) `Max_Dist` del archivo OSF v2.5 (definición "píxel más lejano", dada por el esquema),
  (b) haversine(cumbre, LAT/LON) del mismo archivo ("píxel más caliente", dada por el esquema),
  (c) `Distancia_km` del CSV que el scraper lee de la web (la incógnita).
Si (c) se parece a (b) y no a (a), la web publica el más caliente, y al revés.

CONTROL POSITIVO: las filas con Npix=1, donde las dos definiciones DEBEN coincidir; si
ahí (a) y (b) no coinciden, el instrumento está roto y nada de esto vale.
CONTROL NEGATIVO: las filas con Npix>=11, donde las dos DEBEN separarse; si ahí tampoco
se separan, la comparación no tiene poder resolutivo.

Limitación declarada: (a) y (b) son 2018-2025 y (c) es 2026, así que no son las mismas
pasadas. Lo que se compara es la FORMA de la distribución por volcán y sensor, no filas
pareadas. Read-only.
"""
import io
import json
import os
import sys

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
OSF = os.path.join(ROOT, "data", "mirova_reference", "VRP_GLOBAL_ARCHIVE_2025.csv")
WEB = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot",
                   "registro_vrp_consolidado.csv")

# OSF -> nombre del scraper (A14: las variantes de nombre son un vector de error).
OSF2WEB = {"Láscar": "Lascar", "Chaitén": "Chaiten",
           "Puyehue-Cordón Caulle": "Puyehue-Cordon Caulle", "Lastarria": "Lastarria",
           "Villarrica": "Villarrica", "Chillán, Nevados de": "Nevados de Chillan",
           "Isluga": "Isluga", "Copahue": "Copahue",
           "Planchón-Peteroa": "PlanchonPeteroa", "Llaima": "Llaima"}
RES2WEB = {375: "VIIRS375", 750: "VIIRS", 1000: "MODIS"}


def hav_km(la1, lo1, la2, lo2):
    R = 6371.0088
    p1, p2 = np.radians(la1), np.radians(la2)
    a = (np.sin((p2 - p1) / 2) ** 2
         + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lo2 - lo1) / 2) ** 2)
    return 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def frac_cero(v, umbral):
    v = np.asarray(v, dtype=float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return None
    return round(100.0 * float((v <= umbral).mean()), 1)


def main():
    o = pd.read_csv(OSF)
    o = o[o.Volc_Name.isin(OSF2WEB)].copy()
    o["res"] = o.Resolution.round().astype(int)
    o["d_hot_km"] = hav_km(o.Volc_LAT.values, o.Volc_LON.values, o.LAT.values, o.LON.values)
    o["max_dist_km"] = o.Max_Dist / 1000.0
    o["web_name"] = o.Volc_Name.map(OSF2WEB)
    o["web_sensor"] = o.res.map(RES2WEB)

    w = pd.read_csv(WEB)
    w["f"] = pd.to_datetime(w.Fecha_Satelite_UTC, errors="coerce")
    w = w[w.Tipo_Registro.isin(["ALERTA_TERMICA", "FALSO_POSITIVO"])]
    w = w[pd.to_numeric(w.VRP_MW, errors="coerce") > 0]
    w["Distancia_km"] = pd.to_numeric(w.Distancia_km, errors="coerce")
    w = w.dropna(subset=["Distancia_km"])

    R = {"_meta": {
        "osf": {"archivo": os.path.relpath(OSF, ROOT), "n_filas_chile": int(len(o)),
                "ventana": ["2018-2025 (ver sonda 01)"]},
        "web": {"archivo": os.path.relpath(WEB, ROOT), "n_filas_usadas": int(len(w)),
                "filtro": "Tipo_Registro in (ALERTA_TERMICA, FALSO_POSITIVO) y VRP_MW>0",
                "ventana": [str(w.f.min()), str(w.f.max())]},
        "umbral_cero": "<= 0.05 km (la web redondea a 2 decimales; medio píxel de 375 m son 0.19 km)",
        "limite": "OSF y web NO son las mismas pasadas (2018-2025 vs 2026): se comparan "
                  "FORMAS de distribución por volcán y sensor, no filas pareadas."}}

    # ── CONTROLES DEL INSTRUMENTO ────────────────────────────────────────────
    c1 = o[o.Npix == 1]
    c2 = o[o.Npix >= 11]
    R["controles"] = {
        "positivo_npix_1": {
            "que_deberia_pasar": "Max_Dist y d_hot coinciden (un solo píxel alertado)",
            "n": int(len(c1)),
            "coinciden_<=0.19km_pct": round(100.0 * float(
                (np.abs(c1.max_dist_km - c1.d_hot_km) <= 0.19).mean()), 1),
            "ceros_max_dist_pct": frac_cero(c1.max_dist_km, 0.05),
            "ceros_d_hot_pct": frac_cero(c1.d_hot_km, 0.05)},
        "negativo_npix_>=11": {
            "que_deberia_pasar": "se separan (cúmulo grande)",
            "n": int(len(c2)),
            "coinciden_<=0.19km_pct": round(100.0 * float(
                (np.abs(c2.max_dist_km - c2.d_hot_km) <= 0.19).mean()), 1),
            "ceros_max_dist_pct": frac_cero(c2.max_dist_km, 0.05),
            "ceros_d_hot_pct": frac_cero(c2.d_hot_km, 0.05)}}

    # ── LA COMPARACIÓN, por volcán × sensor ─────────────────────────────────
    filas = []
    for vosf, vweb in OSF2WEB.items():
        for res, sweb in RES2WEB.items():
            oo = o[(o.Volc_Name == vosf) & (o.res == res)]
            ww = w[(w.Volcan == vweb) & (w.Sensor == sweb)]
            if len(oo) < 30 or len(ww) < 10:
                continue
            filas.append({
                "volcan": vweb, "sensor": sweb,
                "n_osf": int(len(oo)), "n_web": int(len(ww)),
                "osf_ceros_max_dist_pct": frac_cero(oo.max_dist_km, 0.05),
                "osf_ceros_d_hot_pct": frac_cero(oo.d_hot_km, 0.05),
                "web_ceros_distancia_pct": frac_cero(ww.Distancia_km, 0.05),
                "osf_max_dist_mediana": round(float(np.median(oo.max_dist_km)), 3),
                "osf_d_hot_mediana": round(float(np.median(oo.d_hot_km)), 3),
                "web_distancia_mediana": round(float(np.median(ww.Distancia_km)), 3),
                "osf_npix_mediana": float(np.median(oo.Npix))})
    R["por_volcan_sensor"] = filas

    # Agregado sobre los pares comparables (mismo universo en las tres series).
    def agg(campo):
        vals = [f[campo] for f in filas if f[campo] is not None]
        return round(float(np.mean(vals)), 1) if vals else None
    R["agregado"] = {
        "pares_comparados": len(filas),
        "media_pct_ceros_osf_max_dist": agg("osf_ceros_max_dist_pct"),
        "media_pct_ceros_osf_d_hot": agg("osf_ceros_d_hot_pct"),
        "media_pct_ceros_web_distancia": agg("web_ceros_distancia_pct")}

    out = os.path.join(AQUI, "02_ceros_y_forma_por_volcan.json")
    json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("escrito:", out)
    print()
    print("CONTROLES:", json.dumps(R["controles"], ensure_ascii=False, indent=1))
    print()
    print(f"{'volcan':22s} {'sensor':9s} {'nOSF':>6s} {'nWEB':>5s} "
          f"{'%0 maxdist':>10s} {'%0 dhot':>8s} {'%0 WEB':>7s} "
          f"{'med maxd':>8s} {'med dhot':>8s} {'med WEB':>8s}")
    for f in filas:
        print(f"{f['volcan']:22s} {f['sensor']:9s} {f['n_osf']:6d} {f['n_web']:5d} "
              f"{str(f['osf_ceros_max_dist_pct']):>10s} {str(f['osf_ceros_d_hot_pct']):>8s} "
              f"{str(f['web_ceros_distancia_pct']):>7s} "
              f"{f['osf_max_dist_mediana']:8.2f} {f['osf_d_hot_mediana']:8.2f} "
              f"{f['web_distancia_mediana']:8.2f}")
    print()
    print("AGREGADO:", json.dumps(R["agregado"], ensure_ascii=False))


if __name__ == "__main__":
    main()
