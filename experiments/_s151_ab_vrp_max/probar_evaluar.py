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
  6. INERTE: el brazo mueve lejos el cumulo de una pasada que el control NO publica (K4 > 0) y nada mas: 0
     silenciadas, 0 nuevas, delta E 0.
  7. GANA EL CRITERIO: lo del 6, y ademas una positiva Muy Bajo que el control no publica y el brazo si.
  8. NO ADOPTAR por suma: lo del 6, y ademas el brazo calla una positiva Muy Bajo que el control publica.
  9. Corridas y K3 con logs (camino de linea de comandos, `evaluar.main`): dos corridas de media ventana en
     carpetas temporales con la forma de `salidas/<run_id>` (Lascar e Isluga). (a) logs correctos: K1 y K3 ok y
     veredicto sin el prefijo PRUEBA; (b) un log del brazo dice el flag equivocado: INDECIDIBLE POR
     INSTRUMENTO; (c) falta un log: idem; (d) la misma corrida pasada dos veces: K1 en rojo por repetidas.
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

    # ---------------------------------------------------------------- 6 a 8: veredictos por la suma
    C.etiquetar(base, filas, coords, ventana)

    def multi(x):
        return (x["rec"].get("n_hotspots_clustered") or 0) >= 2 or bool(x["rec"].get("triggered_test1"))

    def mover_lejos(x):
        pc = dict(x["rec"].get("primary_cluster") or {})
        pc.update({"vrp_mw": 0.5, "n_pixels": 1, "centroid_dist_km": inner[x["vol"]] + 10.0,
                   "centroid_lat": ancla[x["vol"]][0] + 0.15, "centroid_lon": ancla[x["vol"]][1]})
        x["rec"]["primary_cluster"] = pc
        x["rec"]["distance_class"] = "far"
        x["rec"]["f5_core_vrp_mw"] = None
    def ya_lejos(x):
        pc = x["rec"].get("primary_cluster") or {}
        return (pc.get("centroid_dist_km") or 0) > inner[x["vol"]] and (pc.get("vrp_mw") or 0) > 0
    # la version 1 tomo una pasada cuyo cumulo YA estaba lejos: K4 no la cuenta (no se movio) y el caso fallo
    i_mov = next(i for i, x in enumerate(base) if not x["pub"] and multi(x) and x["b"] == "VIIRS375" and not ya_lejos(x))
    i_mb = next(i for i, x in enumerate(base) if x["pub"] and multi(x) and x["b"] == "VIIRS375" and x["lab"] == "pos"
                and not x["prot_A"] and x["decide"] and i != i_mov)

    brazo = copy.deepcopy(base)
    mover_lejos(brazo[i_mov])
    res, _ = E.evaluar(copy.deepcopy(base), {"A1": brazo}, filas, ventana, logs=None)
    r = res["A1"]
    esperar("6 INERTE", r["veredicto_A"] == "PRUEBA INERTE", f"K4 {r['K4']['cumulo_movido_lejos']}, {r['veredicto_A']}")

    ctrl = copy.deepcopy(base)
    ctrl[i_mb]["rec"]["primary_cluster"]["vrp_mw"] = 0.0
    ctrl[i_mb]["rec"]["f5_core_vrp_mw"] = 0.0
    res, _ = E.evaluar(ctrl, {"A1": copy.deepcopy(brazo)}, filas, ventana, logs=None)
    r = res["A1"]
    esperar("7 GANA EL CRITERIO", r["veredicto_A"].startswith("PRUEBA GANA EL CRITERIO"),
            f"delta V375 {r['por_sensor']['VIIRS375']['R2_delta_E']}, {r['veredicto_A']}")

    brazo8 = copy.deepcopy(brazo)
    mover_lejos(brazo8[i_mb])
    res, _ = E.evaluar(copy.deepcopy(base), {"A1": brazo8}, filas, ventana, logs=None)
    r = res["A1"]
    esperar("8 NO ADOPTAR por suma", r["veredicto_A"] == "PRUEBA NO ADOPTAR (la suma de errores sube en VIIRS375)",
            f"delta V375 {r['por_sensor']['VIIRS375']['R2_delta_E']}, {r['veredicto_A']}")

    # ---------------------------------------------------------------- 9: corridas y K3 con logs
    import json
    import shutil
    import tempfile
    from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR
    tmp = Path(tempfile.mkdtemp(prefix="s151_k3_"))
    try:
        mitades = E.PAR["medias_ventanas_de_despacho"]
        perfiles = {"_s146_ab_control": True, "_s151_ab_vrp_max": False}
        corridas = []
        for k, (a, b) in enumerate(mitades):
            d = tmp / f"run{k}"
            (d / "logs").mkdir(parents=True)
            for perfil, flag in perfiles.items():
                (d / perfil).mkdir()
                for vol in ("Lascar", "Isluga"):
                    recs = [x["rec"] for x in base if x["vol"] == vol and a <= x["noche"] <= b]
                    (d / perfil / f"{vol}.json").write_text(json.dumps({"records": recs}), encoding="utf-8")
                    (d / "logs" / f"{perfil}_{vol}.log").write_text(
                        "FLAGS_BRAZO " + json.dumps({"PROFILE_NAME": perfil, "DATA_SUBDIR": perfil,
                                                     "ENABLE_VENT_ANCHORED_CLUSTERING": flag}) + "\nresto del log\n",
                        encoding="utf-8")
            corridas.append(d)
        arg = ["--cons", str(SNAP_CONS), "--ocr", str(SNAP_OCR), "--out", str(tmp / "e.json")]
        cmd = sum((["--corrida", str(d)] for d in corridas), []) + arg
        r = E.main(cmd)["A1"]
        esperar("9a corridas y logs correctos", r["K1"]["ok"] and r["K3"]["ok"] is True
                and r["veredicto_A"] == "INDECIDIBLE: EL MECANISMO NO ACTUO", f"K3 {r['K3']}, {r['veredicto_A']}")
        lg = corridas[1] / "logs" / "_s151_ab_vrp_max_Isluga.log"
        texto = lg.read_text(encoding="utf-8")
        lg.write_text(texto.replace('"ENABLE_VENT_ANCHORED_CLUSTERING": false', '"ENABLE_VENT_ANCHORED_CLUSTERING": true'),
                      encoding="utf-8")
        r = E.main(cmd)["A1"]
        esperar("9b flag equivocado en un log", r["K3"]["ok"] is False and r["veredicto_A"] == "INDECIDIBLE POR INSTRUMENTO",
                f"K3 {r['K3']['brazo']}")
        lg.unlink()
        r = E.main(cmd)["A1"]
        esperar("9c falta un log", r["K3"]["ok"] is False and r["veredicto_A"] == "INDECIDIBLE POR INSTRUMENTO",
                f"K3 {r['K3']['brazo']}")
        lg.write_text(texto, encoding="utf-8")
        r = E.main(["--corrida", str(corridas[0]), "--corrida", str(corridas[0])] + arg)["A1"]
        esperar("9d corrida repetida", not r["K1"]["ok"] and r["K1"]["repetidas_control"] > 0
                and r["veredicto_A"] == "INDECIDIBLE POR INSTRUMENTO", f"K1 {r['K1']}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    P("RESULTADO:", "los controles dan lo esperado" if not fallas else f"FALLAN {fallas}")
    (HERE / "probar_evaluar_salida.txt").write_text(out.getvalue(), encoding="utf-8")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
