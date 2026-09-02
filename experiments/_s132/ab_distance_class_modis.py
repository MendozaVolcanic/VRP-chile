# -*- coding: utf-8 -*-
"""S132 - A/B de `distance_class` en MODIS (decision #4 de AUDIT_S131 §4). READ-ONLY.

CRITERIO PRE-REGISTRADO, escrito antes de mirar ningun resultado (el A/B es una apuesta,
no una racionalizacion a posteriori):

  C1  Las pasadas TP de MODIS (nuestra deteccion summit coincide con una ALERTA de MIROVA
      esa noche) NO PUEDEN BAJAR. Es la condicion de no-regresion.
  C2  El flip tiene que ser mayoritariamente hacia el edificio: >= 80 % de los records que
      pasan de `far` a `summit` deben tener su cumulo a <= 2 km del crater.
  C3  Los records que el flip destapa y MIROVA NO confirma no pueden ser mayoritariamente
      del volcan que S113/A81 identifico como artefacto topografico (NdC): si NdC aporta
      mas del 50 % del flip, el hallazgo es el artefacto A69 y NO se adopta.
  C4  El flip no puede tocar VIIRS: es MODIS-only por construccion. Control.

POR QUE SE PUEDE MEDIR SIN REPROC. Lo que cambia es de que punto se deriva la etiqueta, y
`distance_class` en MODIS no se lee aguas arriba: no entra en deteccion, ni en seleccion de
cumulo, ni en magnitud. Eso NO se afirma, se verifica mecanicamente con AST en
tests/test_distance_class_modis_s132.py::test_distance_class_no_se_lee_aguas_arriba_en_modis.
Por eso A18 (el preview offline no predice la seleccion de cumulo) no aplica aca, y ademas
MODIS no corre en Windows (pyhdf), asi que la alternativa seria un reproc en GH Actions que
no aportaria informacion distinta.

LIMITE HONESTO. El guard S113 de `store.py` puede reetiquetar summit->far despues; y la
Regla D del vent puede forzar summit. Esta medicion usa el `distance_class` FINAL
persistido, que ya incluye esos efectos, y simula el flip sobre el; es exactamente lo que
veria el dashboard.
"""
import io
import json
import os
import sys

import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "experiments", "_s131_audit", "ground_truth"))
sys.path.insert(0, REPO)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from _lib import TIER_A, load_mirova_rows, load_records, load_volcanoes  # noqa: E402

OUT = os.path.join(REPO, "experiments", "_s132")


def main():
    vols = load_volcanoes()
    inner = {n: float(v.get("inner_radius_km") or 10.0) for n, v in vols.items()
             if n in TIER_A}

    df = load_records(volcanoes=TIER_A)   # ya trae dt y family
    df = df[df["dt"].notna()].copy()

    t0, t1 = df["dt"].min(), df["dt"].max()
    mir = load_mirova_rows(t0, t1)
    # Noches en que MIROVA publico algo para ese volcan (universo CONS u OCR, A11).
    noches_mir = set(zip(mir["volcano"], mir["dt"].dt.date))

    df["fam"] = df["family"]
    df["inner"] = df["volcano"].map(inner)
    df["pc_dist"] = df["primary_cluster"].map(
        lambda pc: (pc or {}).get("centroid_dist_km"))
    df["pc_vrp"] = df["primary_cluster"].map(lambda pc: (pc or {}).get("vrp_mw") or 0.0)
    df["fecha"] = df["dt"].dt.date
    df["mirova_confirma"] = [ (v, f) in noches_mir for v, f in zip(df["volcano"], df["fecha"]) ]

    # Etiqueta simulada con el flag encendido: relabel, nunca creacion (misma regla que
    # `derivar_distance_class`: se exige que ya hubiera etiqueta).
    def nueva(r):
        if r["distance_class"] is None or pd.isna(r["inner"]):
            return r["distance_class"]
        if r["fam"] != "MODIS":
            return r["distance_class"]          # C4: MODIS-only
        d = r["pc_dist"] if r["pc_dist"] is not None else r["final_hotspot_dist_km"]
        if d is None:
            return r["distance_class"]
        return "summit" if d <= r["inner"] else "far"

    df["dc_nueva"] = df.apply(nueva, axis=1)

    modis = df[df["fam"] == "MODIS"]
    flip = modis[(modis["distance_class"] == "far") & (modis["dc_nueva"] == "summit")]
    contraflip = modis[(modis["distance_class"] == "summit") & (modis["dc_nueva"] == "far")]

    # ---- C1: TP de MODIS antes y despues -------------------------------------------
    def tp(col):
        vis = modis[(modis[col] == "summit") & (modis["pc_vrp"] > 0)
                    & (modis["pc_dist"].notna()) & (modis["pc_dist"] <= modis["inner"])]
        return len(set(zip(vis["volcano"], vis["fecha"]))
                   & {(v, f) for (v, f) in noches_mir})

    tp_antes, tp_despues = tp("distance_class"), tp("dc_nueva")

    # ---- C2 / C3 ---------------------------------------------------------------------
    cerca = flip[flip["pc_dist"] <= 2.0]
    frac_cerca = len(cerca) / len(flip) if len(flip) else float("nan")
    sin_mirova = flip[~flip["mirova_confirma"]]
    por_vol_sin = sin_mirova["volcano"].value_counts().to_dict()
    frac_ndc = (por_vol_sin.get("NevadosDeChillan", 0) / len(sin_mirova)) if len(sin_mirova) else 0.0

    # ---- C4 --------------------------------------------------------------------------
    # OJO (bug de instrumento detectado y corregido en esta sesion): comparar dos columnas
    # con `!=` cuenta como "distintos" los pares NaN/NaN, porque NaN != NaN es True. Habia
    # 18.468 records no-MODIS sin `distance_class`, y el control fallaba midiendo la
    # semantica de pandas en vez del flip. Se comparan como texto con relleno explicito.
    _nm = df[df["fam"] != "MODIS"]
    no_modis_tocados = int((_nm["distance_class"].fillna("__nulo__").astype(str)
                            != _nm["dc_nueva"].fillna("__nulo__").astype(str)).sum())

    res = {
        "ventana": [str(t0), str(t1)],
        "records_modis": int(len(modis)),
        "flip_far_a_summit": int(len(flip)),
        "flip_summit_a_far": int(len(contraflip)),
        "C1_tp_modis_antes": tp_antes,
        "C1_tp_modis_despues": tp_despues,
        "C1_ok": bool(tp_despues >= tp_antes),
        "C2_frac_flip_cumulo_bajo_2km": round(float(frac_cerca), 4),
        "C2_ok": bool(frac_cerca >= 0.80),
        "C3_flip_sin_mirova": int(len(sin_mirova)),
        "C3_frac_ndc_del_flip_sin_mirova": round(float(frac_ndc), 4),
        "C3_ok": bool(frac_ndc <= 0.50),
        "C3_por_volcan": por_vol_sin,
        "C4_records_no_modis_tocados": no_modis_tocados,
        "C4_ok": bool(no_modis_tocados == 0),
        "flip_mediana_pc_dist_km": round(float(flip["pc_dist"].median()), 3) if len(flip) else None,
        "flip_mediana_final_dist_km": round(float(flip["final_hotspot_dist_km"].median()), 3) if len(flip) else None,
        "flip_mediana_pc_vrp_mw": round(float(flip["pc_vrp"].median()), 4) if len(flip) else None,
        "flip_confirmados_por_mirova": int(flip["mirova_confirma"].sum()),
        "flip_por_volcan": flip["volcano"].value_counts().to_dict(),
        # Diagnostico, NO criterio: el umbral fijo de 2 km de C2 es mas estricto que la
        # propia etiqueta, cuyo corte es el inner_radius de cada volcan (3 a 20 km).
        "diag_flip_dentro_del_inner": int((flip["pc_dist"] <= flip["inner"]).sum()),
        "diag_flip_entre_2km_y_inner": int(((flip["pc_dist"] > 2.0)
                                            & (flip["pc_dist"] <= flip["inner"])).sum()),
        "diag_flip_p25_p50_p75_pc_dist": [round(float(q), 3) for q in
                                          flip["pc_dist"].quantile([.25, .5, .75])] if len(flip) else None,
        "diag_pc_dist_bajo_2km_por_volcan": flip[flip["pc_dist"] <= 2.0]["volcano"].value_counts().to_dict(),
        "diag_denominadores_A90": {
            "records_modis_totales": int(len(modis)),
            "modis_con_etiqueta": int(modis["distance_class"].notna().sum()),
            "modis_con_cumulo_bajo_2km": int((modis["pc_dist"] <= 2.0).sum()),
            "modis_far_con_cumulo_bajo_2km": int(((modis["distance_class"] == "far")
                                                  & (modis["pc_dist"] <= 2.0)).sum()),
        },
    }
    res["VEREDICTO"] = "ADOPTAR" if all(res[k] for k in ("C1_ok", "C2_ok", "C3_ok", "C4_ok")) \
        else "NO ADOPTAR"

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "ab_distance_class_modis.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    flip[["volcano", "datetime_utc", "sensor", "final_hotspot_dist_km", "pc_dist",
          "pc_vrp", "mirova_confirma"]].to_csv(
        os.path.join(OUT, "ab_distance_class_modis_flip.csv"), index=False)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
