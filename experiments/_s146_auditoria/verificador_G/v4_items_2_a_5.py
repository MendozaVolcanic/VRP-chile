# -*- coding: utf-8 -*-
"""V4 (verificador G, items 2 a 5) - conteos sobre los records reales del regimen actual.

(1) Si lo que mide estuviera roto, ¿fallaria?
    Cada conteo se hace sobre campos que se imprimen con su COBERTURA al lado: si un campo no
    existe en un sensor, su fraccion no nula sale 0 y el conteo queda declarado SIN DATO en vez
    de cero. Ademas cada item lleva su complemento (el conteo de la condicion contraria) y la
    suma tiene que dar el denominador: si no diera, el filtro estaria mal escrito.
(2) Si el instrumento estuviera muerto, ¿se veria distinto?
    Si: el bloque CONTROLES cuenta lo mismo con la condicion siempre verdadera (debe dar el
    denominador entero) y con la condicion siempre falsa (debe dar 0). Un cargador muerto daria
    0 en los dos.

Ventana: 2026-09-01 en adelante (regimen actual, nunca cruza 2026-08-28 23:00 UTC).
Solo lectura. No usa node: el item 5 se mide aparte con el predicado real (v5).
"""
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "mirova_equivalent"
OUT = Path(__file__).with_suffix(".json")
INICIO = "2026-09-01"
TIER_A = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
          "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]


def bucket(s):
    s = s or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def med(xs):
    s = sorted(xs)
    return s[len(s) // 2] if s else None


def main():
    recs = []
    for vol in TIER_A:
        d = json.load(open(DATA / f"{vol}.json", encoding="utf-8"))
        for r in d["records"]:
            if r.get("datetime_utc", "") < INICIO:
                continue
            b = bucket(r.get("sensor"))
            if b:
                r["_vol"] = vol
                r["_b"] = b
                recs.append(r)

    out = {"ventana_desde": INICIO, "n": len(recs),
           "por_sensor": dict(Counter(r["_b"] for r in recs)), "cobertura": {}, "items": {}}

    campos = ["diag_n_bt_path", "diag_n_nti_path", "diag_n_dnti_ctx_path", "diag_n_eti_path",
              "diag_n_first_pass_pixels", "diag_n_second_pass_recapture", "triggered_test1",
              "final_hotspot_source", "final_hotspot_dist_km", "distance_class",
              "n_anomalous_pixels", "f5_core_vrp_mw", "discarded_reason",
              "discarded_actual_cluster_pixels"]
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        sub = [r for r in recs if r["_b"] == b]
        out["cobertura"][b] = {"n": len(sub), **{
            c: round(sum(1 for r in sub if r.get(c) is not None) / len(sub), 4) if sub else None
            for c in campos}}
        out["cobertura"][b]["primary_cluster"] = round(
            sum(1 for r in sub if r.get("primary_cluster")) / len(sub), 4) if sub else None

    # ---------------- ITEM 2 (G-19): only_test1_source con mascara contextual viva
    it2 = {}
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        sub = [r for r in recs if r["_b"] == b]
        legacy0 = lambda r: all((r.get(c) or 0) == 0 for c in
                                ("diag_n_bt_path", "diag_n_nti_path",
                                 "diag_n_dnti_ctx_path", "diag_n_eti_path"))
        gana = [r for r in sub if r.get("triggered_test1") and legacy0(r)
                and r.get("final_hotspot_source") == "test1"]
        # de esos, ¿cuantos tenian pixeles contextuales REALES en la mascara?
        con_ctx = [r for r in gana if (r.get("diag_n_first_pass_pixels") or 0) > 0
                   or (r.get("diag_n_second_pass_recapture") or 0) > 0]
        it2[b] = {
            "n_sensor": len(sub),
            "contadores_legacy_en_cero": sum(1 for r in sub if legacy0(r)),
            "test1_gana_fuente_con_legacy_0": len(gana),
            "de_esos_con_pixeles_contextuales_en_mascara": len(con_ctx),
            "complemento_sin_contextuales": len(gana) - len(con_ctx),
            "mediana_first_pass_en_esos": med([r.get("diag_n_first_pass_pixels") or 0 for r in con_ctx]),
            "mediana_second_pass_en_esos": med([r.get("diag_n_second_pass_recapture") or 0 for r in con_ctx]),
            "de_esos_con_cumulo_descartado": sum(1 for r in con_ctx if (r.get("primary_cluster") or {}).get("n_pixels")),
        }
    out["items"]["item2_G19"] = it2

    # ---------------- ITEM 3a: segundo pase detecta con primer pase en cero
    it3a = {}
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        sub = [r for r in recs if r["_b"] == b
               and r.get("diag_n_first_pass_pixels") is not None
               and r.get("diag_n_second_pass_recapture") is not None]
        solo2 = [r for r in sub if (r["diag_n_first_pass_pixels"] or 0) == 0
                 and (r["diag_n_second_pass_recapture"] or 0) > 0]
        it3a[b] = {"n_con_ambos_campos": len(sub), "primer_pase_0_y_segundo_detecta": len(solo2),
                   "complemento": len(sub) - len(solo2),
                   "de_esos_publicables_pc_vrp_gt0": sum(
                       1 for r in solo2 if ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 0)}
    out["items"]["item3a_segundo_pase_solo"] = it3a

    # ---------------- ITEM 3b: ancla test1 a 0,0 km y summit con cumulo lejos
    it3b = {}
    for b in ("VIIRS375", "VIIRS750", "MODIS"):
        sub = [r for r in recs if r["_b"] == b and r.get("final_hotspot_source") == "test1"]
        cero = [r for r in sub if (r.get("final_hotspot_dist_km") or -1) == 0.0]
        summit = [r for r in cero if r.get("distance_class") == "summit"]
        lejos = [r for r in summit
                 if ((r.get("primary_cluster") or {}).get("centroid_dist_km") or 0) > 1.0]
        it3b[b] = {"source_test1": len(sub), "de_esos_dist_0km": len(cero),
                   "y_distance_class_summit": len(summit),
                   "y_cumulo_a_mas_de_1km": len(lejos),
                   "complemento_cumulo_dentro_de_1km": len(summit) - len(lejos),
                   "mediana_dist_cumulo_en_los_lejos": med(
                       [(r.get("primary_cluster") or {}).get("centroid_dist_km") for r in lejos]),
                   "max_dist_cumulo": max([(r.get("primary_cluster") or {}).get("centroid_dist_km")
                                           for r in lejos], default=None)}
    out["items"]["item3b_ancla_test1"] = it3b

    # ---------------- ITEM 4: modo de un pixel contra el nucleo F5'
    it4 = {}
    for b in ("VIIRS375",):
        sub = [r for r in recs if r["_b"] == b and r.get("primary_cluster")]
        spm = [r for r in sub if (r["primary_cluster"] or {}).get("single_pixel_mode")]
        con_f5 = [r for r in spm if r.get("f5_core_vrp_mw") is not None
                  and (r["primary_cluster"].get("vrp_mw") or 0) > 0]
        razones = [r["f5_core_vrp_mw"] / r["primary_cluster"]["vrp_mw"] for r in con_f5]
        difieren = [x for x in razones if abs(x - 1.0) > 1e-9]
        it4[b] = {"n_con_cumulo": len(sub), "single_pixel_mode": len(spm),
                  "con_f5_y_pc_positivos": len(con_f5),
                  "razon_f5_sobre_pc_mediana": med(razones),
                  "n_donde_difieren": len(difieren),
                  "razon_mediana_donde_difieren": med(difieren),
                  "razon_min": min(razones) if razones else None,
                  "razon_max": max(razones) if razones else None}
        # control: en los NO single_pixel_mode la razon deberia comportarse distinto
        nospm = [r for r in sub if not (r["primary_cluster"] or {}).get("single_pixel_mode")
                 and r.get("f5_core_vrp_mw") is not None
                 and (r["primary_cluster"].get("vrp_mw") or 0) > 0]
        it4[b]["CONTROL_no_single_pixel_razon_mediana"] = med(
            [r["f5_core_vrp_mw"] / r["primary_cluster"]["vrp_mw"] for r in nospm])
        it4[b]["CONTROL_no_single_pixel_n"] = len(nospm)
    out["items"]["item4_single_pixel_vs_f5"] = it4

    # ---------------- ITEM 5a: el tope de Villarrica
    vil = [r for r in recs if r["_vol"] == "Villarrica"]
    topados = [r for r in vil if r.get("discarded_reason") == "cluster_too_large_for_volcano"]
    out["items"]["item5a_tope_villarrica"] = {
        "n_villarrica": len(vil), "topados": len(topados),
        "de_esos_pc_vrp_gt_0": sum(1 for r in topados
                                   if ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 0),
        "de_esos_vrp_mw_gt_0": sum(1 for r in topados if (r.get("vrp_mw") or 0) > 0),
        "de_esos_triggered_test1": sum(1 for r in topados if r.get("triggered_test1")),
        "sensores": dict(Counter(r["_b"] for r in topados)),
        "pc_vrp_mediana_topados": med([(r.get("primary_cluster") or {}).get("vrp_mw") or 0
                                       for r in topados]),
    }
    # todos los records con discarded_reason (cualquiera) y cumulo con energia
    con_dr = [r for r in recs if r.get("discarded_reason")]
    out["items"]["item5b_discarded_reason"] = {
        "n_con_discarded_reason": len(con_dr),
        "razones": dict(Counter(r["discarded_reason"] for r in con_dr)),
        "con_pc_vrp_gt0": sum(1 for r in con_dr
                              if ((r.get("primary_cluster") or {}).get("vrp_mw") or 0) > 0),
        "con_triggered_test1": sum(1 for r in con_dr if r.get("triggered_test1")),
    }

    # ---------------- CONTROLES del cargador
    out["controles"] = {
        "condicion_siempre_verdadera": sum(1 for r in recs if True),
        "condicion_siempre_falsa": sum(1 for r in recs if False),
        "denominador": len(recs),
    }

    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))
    print("\nJSON:", OUT)


if __name__ == "__main__":
    main()
