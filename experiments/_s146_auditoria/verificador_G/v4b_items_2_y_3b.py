# -*- coding: utf-8 -*-
"""V4b - correccion de un error MIO en v4: use la cadena "test1" donde el codigo escribe
"test1_roi" (pipeline/anchor.py:89). Un filtro con el nombre equivocado no da error: da cero,
y el cero se lee como "no pasa" (A89). Aca se rehacen los items 2 y 3b con los valores reales
que `final_hotspot_source` toma en los records.

(1) Si lo que mide estuviera roto, ¿fallaria?
    El script imprime PRIMERO el censo completo de valores de `final_hotspot_source` y de
    `primary_cluster.geo_class`, asi que un filtro que no matchea nada se ve al lado del
    universo que deberia matchear, en vez de salir como un cero silencioso.
(2) Si el instrumento estuviera muerto, ¿se veria distinto?
    Si: los subconjuntos son anidados y se imprimen con su complemento; la cadena
    n_sensor >= source_test1_roi >= dist_0 >= summit >= cumulo_lejos tiene que ser monotona.
    Si se rompiera la monotonia, el cargador estaria mal.

Ventana 2026-09-01 en adelante. Solo lectura.
"""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "mirova_equivalent"
OUT = Path(__file__).with_suffix(".json")
INICIO = "2026-09-01"
TIER_A = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
          "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
LEGACY = ("diag_n_bt_path", "diag_n_nti_path", "diag_n_dnti_ctx_path", "diag_n_eti_path")


def bucket(s):
    s = s or ""
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")


def med(xs):
    s = sorted(x for x in xs if x is not None)
    return s[len(s) // 2] if s else None


recs = []
for vol in TIER_A:
    for r in json.load(open(DATA / f"{vol}.json", encoding="utf-8"))["records"]:
        if r.get("datetime_utc", "") >= INICIO and r.get("sensor"):
            r["_vol"] = vol
            r["_b"] = bucket(r["sensor"])
            recs.append(r)

out = {"ventana_desde": INICIO, "n": len(recs), "censo_source": {}, "censo_geoclass": {},
       "item2_G19": {}, "item3b_ancla": {}}
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    sub = [r for r in recs if r["_b"] == b]
    out["censo_source"][b] = dict(Counter(str(r.get("final_hotspot_source")) for r in sub))
    out["censo_geoclass"][b] = dict(Counter(
        str((r.get("primary_cluster") or {}).get("geo_class")) for r in sub))

# ---- ITEM 2 (G-19): only_test1_source verdadero con mascara contextual viva
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    sub = [r for r in recs if r["_b"] == b]
    only = [r for r in sub if r.get("triggered_test1")
            and all((r.get(k) or 0) == 0 for k in LEGACY)]
    ctx_viva = [r for r in only if (r.get("diag_n_first_pass_pixels") or 0) > 0
                or (r.get("diag_n_second_pass_recapture") or 0) > 0]
    # el cumulo contextual existe y ADEMAS el ancla honesta lo descarto (source test1_roi)
    descartado = [r for r in ctx_viva if r.get("final_hotspot_source") == "test1_roi"]
    con_cumulo = [r for r in descartado if r.get("primary_cluster")]
    out["item2_G19"][b] = {
        "n_sensor": len(sub),
        "only_test1_source_verdadero": len(only),
        "de_esos_con_pixeles_contextuales_en_la_mascara": len(ctx_viva),
        "complemento_sin_contextuales": len(only) - len(ctx_viva),
        "y_ancla_termina_en_test1_roi": len(descartado),
        "y_ademas_hay_primary_cluster": len(con_cumulo),
        "mediana_first_pass": med([r.get("diag_n_first_pass_pixels") for r in ctx_viva]),
        "mediana_second_pass": med([r.get("diag_n_second_pass_recapture") for r in ctx_viva]),
        "mediana_n_anomalous": med([r.get("n_anomalous_pixels") for r in ctx_viva]),
    }

# ---- ITEM 3b: ancla test1_roi a 0,0 km + summit con el cumulo de la magnitud lejos
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    sub = [r for r in recs if r["_b"] == b]
    src = [r for r in sub if r.get("final_hotspot_source") == "test1_roi"]
    cero = [r for r in src if r.get("final_hotspot_dist_km") == 0.0]
    summit = [r for r in cero if r.get("distance_class") == "summit"]
    lejos = [r for r in summit
             if ((r.get("primary_cluster") or {}).get("centroid_dist_km") or 0) > 1.0]
    out["item3b_ancla"][b] = {
        "n_sensor": len(sub), "source_test1_roi": len(src), "dist_exactamente_0km": len(cero),
        "y_summit": len(summit), "y_cumulo_a_mas_de_1km": len(lejos),
        "complemento_cumulo_dentro_de_1km_o_sin_cumulo": len(summit) - len(lejos),
        "sin_primary_cluster_entre_los_summit": sum(1 for r in summit if not r.get("primary_cluster")),
        "mediana_dist_cumulo_en_lejos": med(
            [(r.get("primary_cluster") or {}).get("centroid_dist_km") for r in lejos]),
        "max_dist_cumulo_en_lejos": max(
            [(r.get("primary_cluster") or {}).get("centroid_dist_km") for r in lejos], default=None),
        "de_los_lejos_inner_radius_superado": None,
    }

OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps(out, indent=1, ensure_ascii=False))
print("\nJSON:", OUT)
