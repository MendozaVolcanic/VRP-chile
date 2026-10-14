# -*- coding: utf-8 -*-
"""Controles del evaluador ANTES del despacho (A110, A116): el instrumento tiene que poder dar cada veredicto.

Sobre los records de produccion en disco de la ventana del pre-registro, cinco brazos fabricados:
  1. nulo: el control contra una copia de si mismo. Debe dar K1 y K2 ok, K4 = 0 y "INDECIDIBLE: EL MECANISMO
     NO ACTUO" (nunca INERTE ni GANA: un brazo que no cambia nada no prueba nada).
  2. A1 simulado: las pasadas que el sustrato clasifica seguro o estimado (solo VIIRS 375, el unico sensor que
     pasa C1) se reemplazan por su cumulo lejano. Debe dar K4 > 0, P2 cumplida (no toca pasadas de Regla D) y
     tantas silenciadas como pasadas simuladas que el control publicaba.
  3. A2 sintetico: en las pasadas de Regla D que publican, un cumulo de un pixel en el pixel mas energetico
     de la escena, con el doble de energia que el del crater. Debe dar veto en la candidata de P5.
  4. K1: al brazo le falta una pasada. Debe dar INDECIDIBLE POR INSTRUMENTO.
  5. K2: el brazo cambia una pasada de un solo cumulo sin Test 1. Debe dar INDECIDIBLE POR INSTRUMENTO.
Si un caso no da lo esperado, el script termina con codigo 1. Salida: probar_evaluar_salida.txt.
"""
from __future__ import annotations

import copy
import io
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import comun as C  # noqa: E402
import evaluar as E  # noqa: E402
import sustrato as S  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402


def main():
    out = io.StringIO()
    fallas = []

    def P(*a):
        print(*a)
        print(*a, file=out)

    ventana = tuple(E.PAR["ventana"])
    coords = C._coords_por_volcan()
    ancla, inner, inner_html = C.anclas_y_inner()
    filas = cargar_referencia_unificada()
    base = C.cargar_records(C.ROOT / "data" / "mirova_equivalent", ventana, coords)
    for x, p in zip(base, C.predicado(base, inner_html)):
        x["pub"] = p

    def esperar(caso, cond, detalle):
        P(f"[{'OK' if cond else 'FALLA'}] {caso}: {detalle}")
        if not cond:
            fallas.append(caso)

    # 1. nulo
    res, _ = E.evaluar(copy.deepcopy(base), {"A1": copy.deepcopy(base)}, filas, ventana, logs=None)
    r = res["A1"]
    esperar("1 nulo", r["K1"]["ok"] and r["K2"]["ok"] and r["K4"]["cumulo_movido_lejos"] == 0
            and r["veredicto_A"] == "PRUEBA INDECIDIBLE: EL MECANISMO NO ACTUO",
            f"K4 {r['K4']['cumulo_movido_lejos']}, veredicto {r['veredicto_A']}")

    # 2. A1 simulado
    brazo = copy.deepcopy(base)
    n_sim = {b: 0 for b in C.BUCKETS}
    for x in brazo:
        if not x["pub"] or x["b"] != "VIIRS375":
            continue
        cl, mx = S.clasificar(x["rec"], ancla[x["vol"]], inner[x["vol"]], 2.2 * S.NOMINAL_KM["VIIRS375"])
        if cl in ("seguro", "estimado") and mx is not None and mx["centroid_dist_km"] > inner[x["vol"]]:
            x["rec"] = S.simular(x["rec"], mx)
            n_sim[x["b"]] += 1
    res, _ = E.evaluar(copy.deepcopy(base), {"A1": brazo}, filas, ventana, logs=None)
    r = res["A1"]
    esperar("2 A1 simulado", r["K4"]["ok"] and r["predicciones"]["P2"]
            and r["por_sensor"]["VIIRS375"]["silenciadas"] == n_sim["VIIRS375"]
            and r["veredicto_A"].startswith("PRUEBA GANA SOLO POR ACCIDENTE"),
            f"simuladas {n_sim['VIIRS375']}, silenciadas {r['por_sensor']['VIIRS375']['silenciadas']}, "
            f"K4 {r['K4']['cumulo_movido_lejos']}, P2 {r['predicciones']['P2']}, veredicto {r['veredicto_A']}")

    # 3. A2 sintetico
    brazo = copy.deepcopy(base)
    n3 = 0
    for x in brazo:
        rec = x["rec"]
        pc = rec.get("primary_cluster") or {}
        if (x["pub"] and rec.get("triggered_test1") and (rec.get("hotspot_dist_km") or 0) > inner[x["vol"]]
                and rec.get("hotspot_lat") is not None):
            d = C.haversine_km(rec["hotspot_lat"], rec["hotspot_lon"], *ancla[x["vol"]])
            if d <= inner[x["vol"]]:
                continue
            x["rec"] = S.simular(rec, {"n_pixels": 1, "vrp_mw": 2 * (pc.get("vrp_mw") or 0.01),
                                       "centroid_lat": rec["hotspot_lat"], "centroid_lon": rec["hotspot_lon"],
                                       "centroid_dist_km": d})
            n3 += 1
    res, _ = E.evaluar(copy.deepcopy(base), {"A2": brazo}, filas, ventana, logs=None)
    r = res["A2"]
    esperar("3 A2 sintetico", r["predicciones"]["P5_veto_en_candidata"] and r["veredicto_A"].startswith("PRUEBA NO ADOPTAR (veto"),
            f"pasadas modificadas {n3}, veredicto {r['veredicto_A']}, P5 {r['predicciones']['P5_veto_en_candidata']}")

    # 4. K1
    brazo = copy.deepcopy(base)[1:]
    res, _ = E.evaluar(copy.deepcopy(base), {"A1": brazo}, filas, ventana, logs=None)
    esperar("4 K1", res["A1"]["veredicto_A"] == "PRUEBA INDECIDIBLE POR INSTRUMENTO", res["A1"]["veredicto_A"])

    # 5. K2
    brazo = copy.deepcopy(base)
    for x in brazo:
        rec = x["rec"]
        if (rec.get("n_hotspots_clustered") or 0) == 1 and not rec.get("triggered_test1") and rec.get("primary_cluster"):
            rec["primary_cluster"]["vrp_mw"] = (rec["primary_cluster"].get("vrp_mw") or 0) + 1.0
            break
    res, _ = E.evaluar(copy.deepcopy(base), {"A1": brazo}, filas, ventana, logs=None)
    esperar("5 K2", res["A1"]["veredicto_A"] == "PRUEBA INDECIDIBLE POR INSTRUMENTO", res["A1"]["veredicto_A"])

    P("RESULTADO:", "los cinco controles dan lo esperado" if not fallas else f"FALLAN {fallas}")
    (HERE / "probar_evaluar_salida.txt").write_text(out.getvalue(), encoding="utf-8")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
