# -*- coding: utf-8 -*-
"""S133 - Recalibracion del criterio C2 del A/B de `distance_class` en MODIS. READ-ONLY.

QUE PROBLEMA RESUELVE (regla A91, error de S132). El C2 pre-registrado en S132 pedia
">= 80 % del flip con el cumulo a <= 2 km del crater". Pero el corte que decide la etiqueta
summit/far NO son 2 km: es el `inner_radius_km` de cada volcan, que en los 11 Tier A va de
3 km (Lastarria, Planchon-Peteroa) a 20 km (Puyehue-Cordon Caulle). Un umbral en kilometros
absolutos mide una cosa distinta en cada volcan, y en 9 de los 11 es MAS ESTRICTO que el
cambio que evalua. Aca se re-expresa la misma pregunta en unidades del propio corte:

    d_norm = dist_cluster_km / inner_radius_km

NO SE CAMBIA EL VEREDICTO DE S132. El A/B corrido queda como esta (NO ADOPTAR, C2 fallado
segun lo pre-registrado). Esto es insumo para formular el C2 de un futuro A/B, no una
re-corrida del anterior: mover el poste despues de ver el dato es justo lo que el
pre-registro impide (A66).

FUENTES. `experiments/_s132/ab_distance_class_modis_flip.csv` (un record por flip, columnas
volcano / datetime_utc / sensor / final_hotspot_dist_km / pc_dist / pc_vrp /
mirova_confirma; `pc_dist` es `primary_cluster.centroid_dist_km`) y `volcanoes.yaml`
(`inner_radius_km` oficial de los KML de MIROVA).

TAUTOLOGIA (se verifica, no se asume). El flip de S132 se define como
`pc_dist <= inner` cuando `pc_dist` no es nulo, con fallback a `final_hotspot_dist_km`
cuando lo es. Si NINGUN record del flip uso el fallback, entonces `d_norm <= 1` se cumple
por construccion y como criterio no informa nada. El script lo comprueba contando los
`pc_dist` nulos y midiendo la fraccion observada; ambos quedan en el JSON.

REFERENCIA CONTRA LA QUE SE LEE d_norm. Si los cumulos cayeran al azar y uniformemente
sobre el AREA del disco de radio inner, la fraccion con d_norm <= x seria x**2 (mediana
0,707; P(<=0,5) = 25 %). Esa es la hipotesis nula "el cumulo no sabe donde esta el crater".
Un C2 informativo es el que exige separarse de ella.

REGLA S91: ningun numero de esta medicion se transcribe a mano. La fuente de verdad es
`experiments/_s133/c2_normalizado_inner_radius.json`.
"""
import io
import json
import os
import sys

import pandas as pd
import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CSV = os.path.join(REPO, "experiments", "_s132", "ab_distance_class_modis_flip.csv")
YML = os.path.join(REPO, "volcanoes.yaml")
OUT = os.path.dirname(os.path.abspath(__file__))

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

QS = [0.05, 0.25, 0.50, 0.75, 0.95]


def _q(s, qs=QS):
    """Cuartiles (mas p5/p95) redondeados; None si la serie esta vacia."""
    if not len(s):
        return None
    return {f"p{int(q * 100)}": round(float(s.quantile(q)), 4) for q in qs}


def main():
    with open(YML, encoding="utf-8") as f:
        vols = yaml.safe_load(f)["volcanoes"]
    inner = {v["name"]: float(v["inner_radius_km"]) for v in vols
             if v.get("inner_radius_km") is not None}

    df = pd.read_csv(CSV)
    df["dt"] = pd.to_datetime(df["datetime_utc"], utc=True, errors="coerce")
    df["inner"] = df["volcano"].map(inner)

    # --- integridad del insumo antes de calcular nada -------------------------------
    integridad = {
        "filas_csv": int(len(df)),
        "volcanes": int(df["volcano"].nunique()),
        "sin_inner_radius_en_yaml": sorted(
            df.loc[df["inner"].isna(), "volcano"].unique().tolist()),
        "pc_dist_nulos": int(df["pc_dist"].isna().sum()),
        "final_hotspot_dist_nulos": int(df["final_hotspot_dist_km"].isna().sum()),
        "inner_radius_por_volcan": {k: inner[k] for k in sorted(df["volcano"].unique())
                                    if k in inner},
    }

    d = df.dropna(subset=["pc_dist", "inner"]).copy()
    d["d_norm"] = d["pc_dist"] / d["inner"]

    # --- ventana temporal y denominadores (A90) --------------------------------------
    denominadores = {
        "que_cuenta_cada_numero": (
            "un record MODIS del flip far->summit del A/B de S132; NO son noches ni "
            "pasadas ni detecciones de todo el corpus"),
        "n_flip_total": int(len(df)),
        "n_flip_con_d_norm_calculable": int(len(d)),
        "ventana_utc": [str(d["dt"].min()), str(d["dt"].max())],
        "corpus_del_que_sale_el_flip": {
            "records_modis": 11749,
            "fuente": "experiments/_s132/ab_distance_class_modis.json:records_modis",
            "nota": "denominador del A/B de S132, no recomputado aca",
        },
        "n_flip_confirmado_por_mirova": int(d["mirova_confirma"].sum()),
        "n_flip_no_confirmado_por_mirova": int((~d["mirova_confirma"]).sum()),
    }

    # --- tautologia de d_norm <= 1 -----------------------------------------------------
    frac_le_1 = float((d["d_norm"] <= 1.0).mean())
    tautologia = {
        "definicion_del_flip_en_s132": (
            "far -> summit si (pc_dist if pc_dist is not None else "
            "final_hotspot_dist_km) <= inner_radius_km"),
        "frac_d_norm_le_1_observada": round(frac_le_1, 6),
        "records_que_usaron_el_fallback_final_hotspot": integridad["pc_dist_nulos"],
        "es_tautologico": bool(integridad["pc_dist_nulos"] == 0 and frac_le_1 == 1.0),
        "por_que": (
            "ningun record del flip uso el fallback, asi que el mismo `pc_dist` que define "
            "el flip es el numerador de d_norm: d_norm <= 1 se cumple por construccion y "
            "un C2 escrito asi no puede fallar nunca"
        ) if integridad["pc_dist_nulos"] == 0 and frac_le_1 == 1.0 else (
            "hay records del flip que entraron por el fallback a final_hotspot_dist_km, "
            "asi que d_norm <= 1 NO se cumple por construccion para todos"),
    }

    # --- agregado --------------------------------------------------------------------
    cortes = [0.25, 0.33, 0.50, 0.75, 1.0]
    agregado = {
        "n": int(len(d)),
        "d_norm_cuantiles": _q(d["d_norm"]),
        "d_norm_media": round(float(d["d_norm"].mean()), 4),
        "frac_d_norm_le": {str(c): round(float((d["d_norm"] <= c).mean()), 4)
                           for c in cortes},
        "nulo_area_uniforme_frac_esperada": {str(c): round(c ** 2, 4) for c in cortes},
        "dist_km_cuantiles": _q(d["pc_dist"]),
        "frac_dist_km_le_2_criterio_s132": round(float((d["pc_dist"] <= 2.0).mean()), 4),
    }

    # --- estratificado por volcan (leccion S126) --------------------------------------
    por_volcan = {}
    for v, g in d.groupby("volcano"):
        por_volcan[v] = {
            "n": int(len(g)),
            "inner_radius_km": float(g["inner"].iloc[0]),
            "d_norm_cuantiles": _q(g["d_norm"]),
            "frac_d_norm_le": {str(c): round(float((g["d_norm"] <= c).mean()), 4)
                               for c in cortes},
            "dist_km_p50": round(float(g["pc_dist"].median()), 4),
            "frac_dist_km_le_2_criterio_s132": round(float((g["pc_dist"] <= 2.0).mean()), 4),
            "n_confirmado_por_mirova": int(g["mirova_confirma"].sum()),
            "ventana_utc": [str(g["dt"].min()), str(g["dt"].max())],
        }
    por_volcan = dict(sorted(por_volcan.items(), key=lambda kv: -kv[1]["n"]))

    # Cuanto se mueve el veredicto agregado si se pesa cada volcan igual (S126: una
    # mediana agrupada puede invertir un veredicto porque los n son desparejos).
    macro = {
        "d_norm_p50_macro_promedio_de_medianas_por_volcan": round(
            float(pd.Series([g["d_norm_cuantiles"]["p50"]
                             for g in por_volcan.values()]).mean()), 4),
        "d_norm_p50_micro_mediana_agrupada": agregado["d_norm_cuantiles"]["p50"],
        "frac_le_0.5_macro": round(float(pd.Series(
            [g["frac_d_norm_le"]["0.5"] for g in por_volcan.values()]).mean()), 4),
        "frac_le_0.5_micro": agregado["frac_d_norm_le"]["0.5"],
        "peor_volcan_por_frac_le_0.5": min(
            por_volcan.items(), key=lambda kv: kv[1]["frac_d_norm_le"]["0.5"])[0],
        "mejor_volcan_por_frac_le_0.5": max(
            por_volcan.items(), key=lambda kv: kv[1]["frac_d_norm_le"]["0.5"])[0],
    }

    # --- corte estratificado por confirmacion de MIROVA -------------------------------
    por_mirova = {}
    for k, g in [("confirmado", d[d["mirova_confirma"]]),
                 ("no_confirmado", d[~d["mirova_confirma"]])]:
        por_mirova[k] = {"n": int(len(g)), "d_norm_cuantiles": _q(g["d_norm"]),
                         "frac_d_norm_le_0.5": round(float((g["d_norm"] <= 0.5).mean()), 4)}

    res = {
        "que_es_esto": ("recalibracion del criterio C2 del A/B de distance_class MODIS de "
                        "S132 en unidades de inner_radius_km; NO cambia el veredicto de S132"),
        "integridad_del_insumo": integridad,
        "denominadores_A90": denominadores,
        "tautologia_d_norm_le_1": tautologia,
        "agregado": agregado,
        "micro_vs_macro_S126": macro,
        "por_volcan": por_volcan,
        "por_confirmacion_mirova": por_mirova,
        "propuesta_C2_no_adoptada": {
            "estado": "PROPUESTA - no adoptada, no pre-registrada, no aplicada a S132",
            "formulacion": ("C2' — en cada uno de los 11 Tier A por separado, la mediana de "
                            "d_norm del flip debe ser <= 0.5, y en el agregado >= 60 % del "
                            "flip debe tener d_norm <= 0.5"),
            "por_que_no_es_tautologica": ("0.5 del inner es estrictamente interior al corte "
                                          "que define el flip, asi que puede fallar"),
            "referencia_nula": ("bajo cumulos uniformes en area dentro del inner la fraccion "
                                "esperada con d_norm <= 0.5 es 25 %; el criterio exige "
                                "separarse de esa nula"),
            "por_que_por_volcan": ("S126: la mediana agrupada puede invertir el veredicto "
                                   "porque los inner van de 3 a 20 km y los n son desparejos"),
        },
    }

    # Como le iria al flip de S132 bajo la propuesta. NO es el veredicto de S132 (que queda
    # como esta) ni una adopcion: es la prueba de que el criterio PUEDE fallar, o sea que no
    # es tautologico. Se calcula aca y no se transcribe a mano (S91). El umbral NO se ajusta
    # para que pase: eso seria repetir el error A91/A66 con otro disfraz.
    fallan = [v for v, g in por_volcan.items() if g["d_norm_cuantiles"]["p50"] > 0.5]
    res["propuesta_C2_no_adoptada"]["evaluacion_retrospectiva_sobre_el_flip_de_s132"] = {
        "advertencia": "diagnostico, NO veredicto; el veredicto de S132 no se toca",
        "volcanes_que_fallarian_la_mediana_0.5": fallan,
        "volcanes_que_pasarian": [v for v in por_volcan if v not in fallan],
        "agregado_frac_le_0.5": agregado["frac_d_norm_le"]["0.5"],
        "agregado_pasaria_el_60_pct": bool(agregado["frac_d_norm_le"]["0.5"] >= 0.60),
        "lectura": ("el criterio discrimina: no lo pasan todos, luego no es tautologico"),
        "limite_del_normalizado": (
            "normalizar por inner NO arregla Puyehue-Cordon Caulle: con inner = 20 km "
            "cualquier cumulo sobre el edificio da d_norm chico y el criterio se vuelve "
            "vacio ahi. El inner grande de PCC es una decision de MIROVA sobre un lacolito "
            "difuso de ~707 km2, no una medida de cercania al crater"),
    }

    with open(os.path.join(OUT, "c2_normalizado_inner_radius.json"), "w",
              encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
