# -*- coding: utf-8 -*-
"""S139 - separar el exceso REAL del error de origen: la prueba con más filo.

EL PROBLEMA A RESOLVER. La sonda 06 encontró que la distancia publicada queda, en las
pasadas con foco cerca del cráter, unos 260 m POR ENCIMA de la distancia al foco, y eso
es justo lo que predice la hipótesis "píxel más lejano" (en el archivo OSF, para VIIRS de
375 m, el píxel más lejano del cúmulo está a 213 m más que el más caliente, en mediana).
Pero 260 m es también el tamaño del corrimiento de origen que la sonda 03 despejó, así que
las dos explicaciones se confunden y el número solo no decide nada.

CÓMO SE SEPARAN. Mover el origen una distancia δ cambia la distancia a un punto en
−δ·û, donde û es la dirección del punto visto desde el origen: el efecto depende del RUMBO
del foco y de nada más. En cambio el exceso del cúmulo (el píxel más lejano contra el más
caliente) no mira el rumbo: es positivo siempre. Entonces se regresa el residuo contra el
rumbo del foco y se mira la CONSTANTE:

    residuo = a + b·cos(rumbo) + c·sen(rumbo)

  · La parte (b, c) es todo lo que un origen mal puesto puede explicar.
  · La constante `a` es lo que queda: 0 si la web publica el píxel más caliente, y del
    orden de +0,2 km (VIIRS 375 m) si publica el más lejano.

CONTROL POSITIVO: el mismo ajuste sobre el archivo OSF, poniendo como "publicada" la
distancia al píxel más caliente (constante esperada 0) y después `Max_Dist` (constante
esperada +0,2 km). Si el instrumento no distingue esos dos casos conocidos, no distingue nada.
CONTROL NEGATIVO: residuos barajados entre pasadas; la constante debe irse a la nada y el
ajuste perder todo poder.

Read-only.
"""
import io
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
OSF = os.path.join(ROOT, "data", "mirova_reference", "VRP_GLOBAL_ARCHIVE_2025.csv")
CORTE_KM = 1.0     # sólo pasadas donde el foco del TIF ES la anomalía publicada
CHILE = ["Láscar", "Chaitén", "Puyehue-Cordón Caulle", "Lastarria", "Villarrica",
         "Chillán, Nevados de", "Isluga", "Copahue", "Planchón-Peteroa", "Llaima"]


def regresion(resid, brg_deg, n_boot=2000, semilla=139):
    """Constante del ajuste residuo ~ a + b·cos(rumbo) + c·sen(rumbo), con IC bootstrap."""
    b = np.radians(brg_deg)
    X = np.column_stack([np.ones_like(b), np.cos(b), np.sin(b)])
    coef, *_ = np.linalg.lstsq(X, resid, rcond=None)
    rng = np.random.default_rng(semilla)
    boot = []
    for _ in range(n_boot):
        i = rng.integers(0, len(resid), len(resid))
        c, *_ = np.linalg.lstsq(X[i], resid[i], rcond=None)
        boot.append(c[0])
    boot = np.array(boot)
    return {"n": int(len(resid)),
            "constante_km": round(float(coef[0]), 3),
            "IC95_km": [round(float(np.percentile(boot, 2.5)), 3),
                        round(float(np.percentile(boot, 97.5)), 3)],
            "amplitud_direccional_km": round(float(np.hypot(coef[1], coef[2])), 3),
            "residuo_mediano_bruto_km": round(float(np.median(resid)), 3)}


def rumbo(dlat_km, dlon_km):
    return (np.degrees(np.arctan2(dlon_km, dlat_km)) + 360.0) % 360.0


def controles_osf():
    """El mismo instrumento sobre datos donde la respuesta se conoce."""
    d = pd.read_csv(OSF)
    d = d[d.Volc_Name.isin(CHILE)].copy()
    d["res"] = d.Resolution.round()
    d = d[d.res == 375].dropna(subset=["LAT", "LON", "Max_Dist"])
    out = {}
    for nombre, col in (("CONTROL_pos_publicada=mas_caliente", "d_hot"),
                        ("CONTROL_neg_publicada=Max_Dist", "max_dist")):
        filas = []
        for v, g in d.groupby("Volc_Name"):
            la0, lo0 = float(g.Volc_LAT.iloc[0]), float(g.Volc_LON.iloc[0])
            dy = (g.LAT.values - la0) * 110.574
            dx = (g.LON.values - lo0) * 111.320 * math.cos(math.radians(la0))
            dhot = np.hypot(dx, dy)
            pub = dhot if col == "d_hot" else g.Max_Dist.values / 1000.0
            # Se usa el MISMO origen equivocado a propósito (Volc_LAT/LON sin corregir),
            # que es la situación real de la sonda 06.
            resid = pub - dhot
            ok = np.abs(resid) <= CORTE_KM
            filas.append(pd.DataFrame({"resid": resid[ok],
                                       "brg": rumbo(dy[ok], dx[ok])}))
        f = pd.concat(filas)
        out[nombre] = regresion(f.resid.values, f.brg.values)
    # Y el caso realista: origen mal puesto Y publicada = Max_Dist.
    filas = []
    for v, g in d.groupby("Volc_Name"):
        la0, lo0 = float(g.Volc_LAT.iloc[0]), float(g.Volc_LON.iloc[0])
        dy = (g.LAT.values - la0) * 110.574
        dx = (g.LON.values - lo0) * 111.320 * math.cos(math.radians(la0))
        dhot_malo = np.hypot(dx, dy)          # medida desde el origen equivocado
        resid = g.Max_Dist.values / 1000.0 - dhot_malo
        ok = np.abs(resid) <= CORTE_KM
        filas.append(pd.DataFrame({"resid": resid[ok], "brg": rumbo(dy[ok], dx[ok])}))
    f = pd.concat(filas)
    out["CONTROL_neg_con_origen_corrido_250m"] = regresion(f.resid.values, f.brg.values)
    return out


def main():
    det = json.load(open(os.path.join(AQUI, "06_hipotesis_caliente_vs_lejano.json"),
                         encoding="utf-8"))["detalle"]
    d = pd.DataFrame(det)
    for c in ("dist_pub_km", "d_foco_km", "resid_km", "lat", "lon",
              "centro_lat", "centro_lon", "px_km", "vrp_mw", "prominencia_sigma"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["resid_km"])
    d["dy"] = (d.lat - d.centro_lat) * 110.574
    d["dx"] = (d.lon - d.centro_lon) * 111.320 * np.cos(np.radians(d.centro_lat))
    d["brg"] = rumbo(d.dy.values, d.dx.values)

    R = {"_meta": {
        "entrada": "06_hipotesis_caliente_vs_lejano.json (detalle)",
        "corte_km": CORTE_KM,
        "criterio_de_inclusion": "|distancia publicada - distancia al foco| <= 1 km, "
                                 "para quedarse con las pasadas donde el foco del TIF ES "
                                 "la anomalía que la web reportó",
        "modelo": "residuo = a + b·cos(rumbo) + c·sen(rumbo); `a` es el exceso que ningún "
                  "corrimiento de origen puede explicar",
        "esperado_si_mas_caliente_km": 0.0,
        "esperado_si_mas_lejano_km": "+0,21 (VIIRS375, mediana OSF de Max_Dist - d_hot)"}}

    R["controles_sobre_el_archivo_OSF"] = controles_osf()

    sel = d[np.abs(d.resid_km) <= CORTE_KM]
    R["n_disponibles"] = int(len(d))
    R["n_incluidos"] = int(len(sel))
    R["global"] = regresion(sel.resid_km.values, sel.brg.values)
    R["por_sensor"] = {s: regresion(g.resid_km.values, g.brg.values)
                       for s, g in sel.groupby("sensor") if len(g) >= 25}
    R["por_tipo"] = {t: regresion(g.resid_km.values, g.brg.values)
                     for t, g in sel.groupby("tipo") if len(g) >= 25}
    R["foco_cerca_<=5km"] = regresion(*(lambda g: (g.resid_km.values, g.brg.values))(
        sel[sel.d_foco_km <= 5])) if (sel.d_foco_km <= 5).sum() >= 25 else None
    R["foco_lejos_>10km"] = regresion(*(lambda g: (g.resid_km.values, g.brg.values))(
        sel[sel.d_foco_km > 10])) if (sel.d_foco_km > 10).sum() >= 25 else None
    R["por_volcan"] = {v: regresion(g.resid_km.values, g.brg.values)
                       for v, g in sel.groupby("volcan") if len(g) >= 25}

    rng = np.random.default_rng(139)
    R["control_negativo_residuos_barajados"] = regresion(
        rng.permutation(sel.resid_km.values), sel.brg.values)

    out = os.path.join(AQUI, "07_exceso_no_explicable_por_el_origen.json")
    json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    print("escrito:", out)
    print(json.dumps(R, ensure_ascii=False, indent=1, default=str)[:4000])


if __name__ == "__main__":
    main()
