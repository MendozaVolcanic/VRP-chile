# -*- coding: utf-8 -*-
"""S139 - ¿desde qué punto mide MIROVA sus distancias, y cuánto separan las dos definiciones?

EL PROBLEMA CON LA SONDA 01. El control positivo falló: en las filas con `Npix=1` (un solo
píxel alertado) `Max_Dist` y la distancia al píxel más caliente TIENEN que ser el mismo
número, y sólo coincidían en el 47 % de los casos. O el archivo es incoherente, o mi punto
de referencia no es el suyo: el CSV publica `Volc_LAT/LON` redondeado a 3 decimales (hasta
110 m de error) y nada garantiza que ése sea el origen real de la medición.

EL MÉTODO. Las filas `Npix=1` son una trilateración: para cada una conozco la posición del
único píxel alertado (`LAT/LON`) y su distancia exacta al origen (`Max_Dist`). Con muchas de
esas filas, el origen queda sobredeterminado y se despeja por mínimos cuadrados, por volcán.
Recién con ese origen se puede medir de verdad cuánto se separan las dos definiciones.

CONTROL POSITIVO: tras despejar el origen, el residuo de las filas `Npix=1` debe caer a
decenas de metros. Si no cae, el modelo "Max_Dist = distancia euclídea desde un punto fijo"
es falso y todo lo que sigue se cae.
CONTROL NEGATIVO: el mismo ajuste corrido sobre coordenadas BARAJADAS (el píxel de una fila
con la distancia de otra) debe dar un residuo grande. Si también ajusta bien, el método
ajusta ruido.

Read-only.
"""
import io
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
OSF = os.path.join(ROOT, "data", "mirova_reference", "VRP_GLOBAL_ARCHIVE_2025.csv")
CHILE = ["Láscar", "Chaitén", "Puyehue-Cordón Caulle", "Lastarria", "Villarrica",
         "Chillán, Nevados de", "Isluga", "Copahue", "Planchón-Peteroa", "Llaima"]


def xy_km(lat, lon, lat0, lon0):
    """Plano local en km. A esta escala (<50 km) el error del plano es despreciable."""
    return ((lon - lon0) * 111.320 * np.cos(np.radians(lat0)),
            (lat - lat0) * 110.574)


def ajustar(lat, lon, dist_km, lat0, lon0):
    x, y = xy_km(lat, lon, lat0, lon0)

    def res(p):
        return np.hypot(x - p[0], y - p[1]) - dist_km
    s = least_squares(res, [0.0, 0.0])
    r = res(s.x)
    return s.x, r


def main():
    d = pd.read_csv(OSF)
    d = d[d.Volc_Name.isin(CHILE)].copy()
    d["res"] = d.Resolution.round().astype(int)
    d["max_dist_km"] = d.Max_Dist / 1000.0
    d = d.dropna(subset=["LAT", "LON", "max_dist_km"])

    R = {"_meta": {
        "fuente": os.path.relpath(OSF, ROOT),
        "modelo": "Max_Dist = distancia euclídea desde un origen fijo por volcán al píxel "
                  "alertado más lejano; con Npix=1 ese píxel es LAT/LON",
        "unidades": "km salvo donde diga m"}}

    origenes, tabla = {}, []
    for v in CHILE:
        sub = d[(d.Volc_Name == v) & (d.Npix == 1)]
        if len(sub) < 50:
            tabla.append({"volcan": v, "n_npix1": int(len(sub)), "nota": "muestra insuficiente"})
            continue
        lat0, lon0 = float(sub.Volc_LAT.iloc[0]), float(sub.Volc_LON.iloc[0])
        p, r = ajustar(sub.LAT.values, sub.LON.values, sub.max_dist_km.values, lat0, lon0)
        # Residuo ANTES de mover el origen (usando Volc_LAT/LON tal cual).
        x, y = xy_km(sub.LAT.values, sub.LON.values, lat0, lon0)
        r0 = np.hypot(x, y) - sub.max_dist_km.values
        # Control negativo: mismas distancias, coordenadas barajadas.
        rng = np.random.default_rng(139)
        idx = rng.permutation(len(sub))
        _, rperm = ajustar(sub.LAT.values, sub.LON.values,
                           sub.max_dist_km.values[idx], lat0, lon0)
        lat_fit = lat0 + p[1] / 110.574
        lon_fit = lon0 + p[0] / (111.320 * np.cos(np.radians(lat0)))
        origenes[v] = (lat_fit, lon_fit)
        tabla.append({
            "volcan": v, "n_npix1": int(len(sub)),
            "volc_latlon_csv": [lat0, lon0],
            "origen_ajustado": [round(lat_fit, 5), round(lon_fit, 5)],
            "corrimiento_m": round(float(np.hypot(*p)) * 1000, 1),
            "residuo_mediano_m_con_volc_latlon": round(float(np.median(np.abs(r0))) * 1000, 1),
            "residuo_mediano_m_con_origen_ajustado": round(float(np.median(np.abs(r))) * 1000, 1),
            "residuo_p90_m_ajustado": round(float(np.percentile(np.abs(r), 90)) * 1000, 1),
            "control_negativo_residuo_mediano_m": round(float(np.median(np.abs(rperm))) * 1000, 1)})
    R["origen_por_volcan"] = tabla

    # ── Con el origen despejado: ¿cuánto separan las dos definiciones? ──────
    def hav_local(lat, lon, lat0, lon0):
        x, y = xy_km(lat, lon, lat0, lon0)
        return np.hypot(x, y)

    filas = []
    for v, (la0, lo0) in origenes.items():
        sub = d[d.Volc_Name == v].copy()
        sub["d_hot_km"] = hav_local(sub.LAT.values, sub.LON.values, la0, lo0)
        sub["delta"] = sub.max_dist_km - sub.d_hot_km
        filas.append(sub)
    dd = pd.concat(filas)

    def resumen(sel, etiqueta):
        if len(sel) == 0:
            return {"etiqueta": etiqueta, "n": 0}
        de = sel.delta.values
        return {"etiqueta": etiqueta, "n": int(len(sel)),
                "npix_mediana": float(np.median(sel.Npix)),
                "d_hot_mediana_km": round(float(np.median(sel.d_hot_km)), 3),
                "max_dist_mediana_km": round(float(np.median(sel.max_dist_km)), 3),
                "delta_mediana_km": round(float(np.median(de)), 3),
                "delta_p90_km": round(float(np.percentile(de, 90)), 3),
                "iguales_<=0.19km_pct": round(100.0 * float((np.abs(de) <= 0.19).mean()), 1),
                "iguales_<=0.5km_pct": round(100.0 * float((np.abs(de) <= 0.5).mean()), 1),
                "delta_negativo_<-0.19km_pct": round(100.0 * float((de < -0.19).mean()), 2)}

    R["separacion_con_origen_ajustado"] = {
        "global": resumen(dd, "Chile, todas"),
        "npix_1_CONTROL_POSITIVO": resumen(dd[dd.Npix == 1], "Npix=1: deben coincidir"),
        "npix_2_3": resumen(dd[(dd.Npix >= 2) & (dd.Npix <= 3)], "Npix 2-3"),
        "npix_4_10": resumen(dd[(dd.Npix >= 4) & (dd.Npix <= 10)], "Npix 4-10"),
        "npix_>=11_CONTROL_NEGATIVO": resumen(dd[dd.Npix >= 11], "Npix>=11: deben separarse"),
        "por_resolucion": {str(r): resumen(dd[dd.res == r], f"{r} m")
                           for r in sorted(dd.res.unique())},
        "por_volcan": {v: resumen(dd[dd.Volc_Name == v], v) for v in origenes}}

    # ¿Cuántas filas serían mal etiquetadas si la web publicara Max_Dist?
    et = {}
    for radio in (3, 4, 5, 7, 20):
        sel = dd[(dd.max_dist_km > radio) & (dd.d_hot_km <= radio)]
        sup = int((dd.max_dist_km > radio).sum())
        et[f"radio_{radio}km"] = {
            "filas_que_superarian_el_radio_por_max_dist": sup,
            "de_esas_con_el_pixel_mas_caliente_adentro": int(len(sel)),
            "pct": round(100.0 * len(sel) / max(1, sup), 2)}
    R["mal_etiquetadas_si_publicara_max_dist"] = et

    out = os.path.join(AQUI, "03_desde_donde_mide_mirova.json")
    json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("escrito:", out)
    print()
    for t in tabla:
        if "origen_ajustado" not in t:
            print(f"{t['volcan']:24s} {t.get('nota')}")
            continue
        print(f"{t['volcan']:24s} n={t['n_npix1']:5d}  corrimiento {t['corrimiento_m']:7.1f} m  "
              f"residuo: {t['residuo_mediano_m_con_volc_latlon']:7.1f} m -> "
              f"{t['residuo_mediano_m_con_origen_ajustado']:6.1f} m   "
              f"(barajado: {t['control_negativo_residuo_mediano_m']:7.1f} m)")
    print()
    for k, v in R["separacion_con_origen_ajustado"].items():
        if k == "por_resolucion" or k == "por_volcan":
            continue
        print(f"{k:32s} n={v['n']:6d}  delta mediana {v.get('delta_mediana_km')} km  "
              f"iguales<=0.19km {v.get('iguales_<=0.19km_pct')}%")
    print()
    print(json.dumps(et, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
