"""S130 · La discrepancia de A81: S113 conto 2.527 far->summit y hoy se citan 9.181.

POR QUE: el bloque de arranque S130 marca esa diferencia como BLOQUEANTE — "resolver
eso ANTES de proponer nada ahi". Un numero que se triplica sin explicacion invalida
cualquier razonamiento apoyado en el.

Regla de la etapa: no heredar la cifra de un informe previo. Se mide hoy con la
definicion VERBATIM de docs/S113_A46_COHERENCE_GUARD.md:24 —

    far->summit = distance_class == "far"
                  AND primary_cluster.vrp_mw > 0
                  AND primary_cluster.centroid_dist_km <= inner_radius_km

o sea: el cluster ES crateriano, pero un pixel lejano (Salar, fuego, glaciar) le
robo el `final_hotspot` y la etiqueta quedo en "far".

Se estratifica por MES para separar las dos explicaciones posibles: corpus que
crecio (S113 fue en junio de 2026; hoy es agosto) contra un cambio real de
comportamiento del pipeline.
"""
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultado_far_summit.json")

# INNER de CLAUDE.md (Reglas geometricas S14), mismos valores que auto_audit_weekly
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
         "Copahue": 4, "PuyehueCordonCaulle": 20, "Isluga": 5,
         "NevadosDeChillan": 5, "Llaima": 5, "Villarrica": 5, "Chaiten": 5}

# S113 corrio el 2026-06-2X. Su corpus terminaba, como mucho, ahi.
CORTE_S113 = "2026-06-30"


def bucket(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    if sensor.endswith("_750"):
        return "VIIRS750"
    if sensor.startswith("VIIRS"):
        return "VIIRS375"
    return "otro"


def main():
    total_records = 0
    far_summit = 0
    hasta_corte = 0          # lo que S113 pudo haber contado
    despues_corte = 0        # corpus nuevo
    por_mes = defaultdict(int)
    por_vol = defaultdict(int)
    por_sensor = defaultdict(int)
    records_por_mes = defaultdict(int)

    for vol, inner in INNER.items():
        p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
        if not os.path.exists(p):
            print(f"[WARN] falta {vol}", file=sys.stderr)
            continue
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            total_records += 1
            dt = r.get("datetime_utc") or ""
            mes = dt[:7]
            records_por_mes[mes] += 1

            if r.get("distance_class") != "far":
                continue
            pc = r.get("primary_cluster") or {}
            v = pc.get("vrp_mw") or 0
            cd = pc.get("centroid_dist_km")
            if not (v > 0 and cd is not None and cd <= inner):
                continue

            far_summit += 1
            por_mes[mes] += 1
            por_vol[vol] += 1
            por_sensor[bucket(r.get("sensor", ""))] += 1
            if dt[:10] <= CORTE_S113:
                hasta_corte += 1
            else:
                despues_corte += 1

    res = {
        "definicion": (
            "far->summit = distance_class=='far' AND primary_cluster.vrp_mw>0 AND "
            "primary_cluster.centroid_dist_km <= inner_radius_km. Verbatim de "
            "docs/S113_A46_COHERENCE_GUARD.md:24. Sobre los 11 Tier A, toda la data."
        ),
        "total_records_tier_a": total_records,
        "far_summit_hoy": far_summit,
        "declarado_S113": 2527,
        "hasta_corte_S113_2026_06_30": hasta_corte,
        "despues_del_corte": despues_corte,
        "por_mes": dict(sorted(por_mes.items())),
        "records_totales_por_mes": dict(sorted(records_por_mes.items())),
        "por_volcan": dict(sorted(por_vol.items(), key=lambda kv: -kv[1])),
        "por_sensor": dict(sorted(por_sensor.items(), key=lambda kv: -kv[1])),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    print(f"total records Tier A ......... {total_records}")
    print(f"far->summit HOY .............. {far_summit}")
    print(f"declarado en S113 ............ 2527")
    print(f"  de los de hoy, hasta 06-30 . {hasta_corte}   <- lo comparable con S113")
    print(f"  posteriores al corte ....... {despues_corte}")
    print("\npor sensor:")
    for k, v in res["por_sensor"].items():
        print(f"  {k:10s} {v:6d}")
    print("\npor volcan:")
    for k, v in res["por_volcan"].items():
        print(f"  {k:24s} {v:6d}")
    print("\npor mes (far->summit / records del mes):")
    for m in sorted(set(por_mes) | set(records_por_mes)):
        if records_por_mes[m]:
            print(f"  {m}  {por_mes[m]:5d} / {records_por_mes[m]:5d}"
                  f"   {100*por_mes[m]/records_por_mes[m]:5.1f}%")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
