# -*- coding: utf-8 -*-
"""S163, pendiente 1 del instrumento: placebos de D-44 y de ganancia sobre producción (K), sin ningún brazo real.

POR QUÉ. Cada paquete del programa por sensor se va a juzgar con `scripts/evaluador_comun.py`. Antes de leer el primer
A/B hay que saber cuánto «decide» el instrumento cuando no hay ningún cambio de detector: con qué frecuencia P2 da
GANA o PIERDE por azar (placebo c, simétrico por bloque noche-volcán), si puede detectar un efecto real cuando lo hay
(placebos a y b), y si M aprueba una ganancia pareja (placebo K×1,2 y K×0,8, con y sin el comparador d′). D-44
(Nicolás, 2026-10-22) pidió correrlos sobre producción antes del tag de D25; S160 los corrió con el evaluador sellado
de D25 y P2 de D-34; aquí van con el evaluador común y P2 de D-45 (prueba de signos por bloque), que es lo que usarán
los A/B nuevos.

Lee, no escribe `data/`. Producción: `data/mirova_equivalent/` del commit de este árbol; referencia: los CSV de
`data/mirova_reference/` del mismo commit (sus sha256 quedan en la salida). Las semillas y el número de repeticiones
están fijados aquí ANTES de correr (V42-22: nada de agregar semillas después de mirar).

Uso: python -I experiments/_s163_instrumento_pendientes/placebos_produccion.py <salida.json> <resumen.md>
"""
import collections
import hashlib
import json
import math
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import banco_paridad as bp  # noqa: E402
import calidad_referencia_mirova as crm  # noqa: E402
import evaluador_comun as ec  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

PROD = RAIZ / "data" / "mirova_equivalent"
REF = {"cons": RAIZ / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv",
       "ocr": RAIZ / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv",
       "respaldo": RAIZ / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv",
       "historico": RAIZ / "data/mirova_reference/union_historica/consolidado_filas_perdidas.csv"}

# --- Pre-registro de la corrida (fijado antes de correr) ------------------------------------------------------------
# Ventanas del programa por sensor §2: T (tabla sola) y O (tabla más OCR, con la tabla sola al lado). O termina en el
# último día de la referencia congelada. Días fuera de O: 13 y 17 a 20 de octubre (D-29) y el 12 (los brazos lo pierden
# por el reproceso de NASA; producción lo tiene, pero un A/B lo va a excluir, así que la línea base también).
VENTANAS = [
    ("T", "2026-04-01", "2026-06-12", ("VIIRS375", "VIIRS750"), ("tabla",)),
    ("T", "2026-03-01", "2026-06-12", ("MODIS",), ("tabla",)),
    ("O", "2026-06-13", None, ("VIIRS375", "VIIRS750", "MODIS"), ("union", "tabla")),
]
EXCLUIR_O = ("2026-10-12", "2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")
N_C, FRACCIONES_C = 400, (0.5, 1.0)          # placebo simétrico: tasa de falsos de P2
N_AB, FRACCIONES_AB = 40, (0.1, 0.25, 0.5)   # placebos a y b: poder
N_C_ESTRATO = 200                            # placebo simétrico por estrato (fracción 1,0)
SEMILLA_BASE = {"c": 20261026, "a": 30261026, "b": 40261026, "c_estrato": 50261026}
REGLA_MINIMAS = "SN"                         # D-9


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(max(0.0, c - m), 4), round(min(1.0, c + m), 4))


def tasa(resultados, que):
    k, n = sum(r == que for r in resultados), len(resultados)
    return {"k": k, "n": n, "tasa": round(k / n, 4) if n else None, "ic95": wilson(k, n)}


def correr_placebo(T, tipo, fraccion, n, semilla0, excluir=lambda f: False, excl=()):
    res, tocadas, B = [], [], []
    for i in range(n):
        r, det = ec.placebo_p2(T, "prod", tipo, fraccion, semilla0 + i, excluir, excl)
        res.append(r)
        tocadas.append(det["tocadas"])
        B.append(det["B"])
    c = collections.Counter(res)
    return {"fraccion": fraccion, "n": n, "resultados": dict(c), "GANA": tasa(res, "GANA"),
            "PIERDE": tasa(res, "PIERDE"), "SIN_SUSTRATO": tasa(res, "SIN SUSTRATO"),
            "tocadas_mediana": sorted(tocadas)[n // 2], "B_mediana": sorted(B)[n // 2]}


def placebos_m(T, estrato_de, excl):
    out = {}
    P_por, salen = ec.pares_m(T, "prod", "prod_id", estrato_de, dias_excluidos=excl)
    for nom, P in sorted(P_por.items()):
        ident, det_id = ec.decidir_estrato(P, "decide")
        e = {"n_pares": len(P), "noches": len({p["bloque"] for p in P}), "identidad": ident}
        if ident != "SIN SUSTRATO":
            # La identidad da d = 0 en todos los pares: su calibración es trivial. La que informa es la del placebo
            # (signos al azar por bloque sobre los |d| de K×g, D-27): cuántas veces la regla simétrica decidiría sola.
            e["razon_K_mediana"] = round(det_id["razon_K"], 4)
            for g in ec.PLACEBO_GANANCIAS:
                Pg = [dict(p, d=p["k"] * g) for p in P]
                sin = ec.decidir_estrato(Pg, "decide", comparador=False)
                con = ec.decidir_estrato(Pg, "decide", comparador=True)
                e["K_x_%s" % g] = {"sin_comparador": sin[0], "con_comparador": con[0],
                                   "falsos_mejora_calib": sin[1]["falsos_mejora"],
                                   "falsos_empeora_calib": sin[1]["falsos_empeora"],
                                   "dprima_mediana": con[1].get("dprima_mediana"),
                                   "falsos_mejora_dprima": con[1].get("falsos_mejora_dprima"),
                                   "nota": con[1].get("nota")}
        out[nom] = e
    return out, salen


def main(salida, resumen):
    t0 = time.time()
    commit = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    ref = cargar_referencia_unificada(REF["cons"], REF["ocr"], respaldo_path=REF["respaldo"],
                                      historico_path=REF["historico"])
    fin_ref = max(f["fecha_utc"] for f in ref)[:10]
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    out = {"commit": commit, "referencia_sha256": {k: sha(v) for k, v in REF.items()}, "fin_referencia": fin_ref,
           "regla_minimas": REGLA_MINIMAS, "preregistro": {
               "N_C": N_C, "FRACCIONES_C": FRACCIONES_C, "N_AB": N_AB, "FRACCIONES_AB": FRACCIONES_AB,
               "N_C_ESTRATO": N_C_ESTRATO, "SEMILLA_BASE": SEMILLA_BASE, "EXCLUIR_O": EXCLUIR_O},
           "celdas": []}
    for nom_v, desde, hasta, sensores, canales in VENTANAS:
        hasta = hasta or fin_ref
        crm.avisar(desde, hasta)
        excl = EXCLUIR_O if nom_v == "O" else ()
        recs, faltan = ec.cargar_lado(PROD, (desde, hasta), sensores, coords, inner)
        for canal in canales:
            pas = ec.pasadas_nocturnas(ref, (desde, hasta), sensores, coords, canal, REGLA_MINIMAS)
            for sensor in sensores:
                ps = [p for p in pas if p.sensor_bucket == sensor]
                rs = [r for r in recs if r["b"] == sensor]
                lados = {"prod": rs, "prod_id": [dict(r) for r in rs]}
                T = ec.tabla_por_pasada(ps, lados, "prod")
                celda = {"ventana": nom_v, "desde": desde, "hasta": hasta, "sensor": sensor, "canal": canal,
                         "dias_excluidos": excl, "volcanes_sin_archivo": faltan, "pasadas_mirova": len(ps),
                         "records_prod": len(rs)}
                cob = ec.cobertura(T, lados, "prod", excl)
                celda["cobertura"] = {"veredicto": cob["veredicto"], "por_lado": cob["por_lado"]["prod"],
                                      "no_observado_por_dia_top5": list(cob["no_observado_por_dia"].items())[:5]}
                # Identidad: producción contra su copia. Todo tiene que dar cero (control de que el armado no inventa).
                contrib_id = ec.contribuciones_p2(T, "prod", "prod_id", dias_excluidos=excl)
                p1b_id = ec.p1b(T, "prod", "prod_id", dias_excluidos=excl)
                celda["identidad"] = {"p2_discordantes": len(contrib_id), "p1b_abajo": len(p1b_id["abajo"]),
                                      "p1b_arriba": sum(len(v) for v in p1b_id["arriba"].values())}
                clases = collections.Counter(ec.clase_p2(f) for f in T if f["dia"] not in excl
                                             and f["cob"]["prod"] == ec.OBSERVADO)
                pub = collections.Counter(ec.clase_p2(f) for f in T if f["dia"] not in excl
                                          and f["cob"]["prod"] == ec.OBSERVADO and ec._pub(f["rec"]["prod"]))
                celda["sustrato_p2"] = {"alerta_mb": clases["alerta_mb"], "alerta_mb_publicadas": pub["alerta_mb"],
                                        "negativos": clases["negativo"], "negativos_publicados": pub["negativo"]}
                celda["placebo_c"] = [correr_placebo(T, "c", fr, N_C, SEMILLA_BASE["c"], excl=excl)
                                      for fr in FRACCIONES_C]
                celda["placebo_a"] = [correr_placebo(T, "a", fr, N_AB, SEMILLA_BASE["a"], excl=excl)
                                      for fr in FRACCIONES_AB]
                celda["placebo_b"] = [correr_placebo(T, "b", fr, N_AB, SEMILLA_BASE["b"], excl=excl)
                                      for fr in FRACCIONES_AB]
                # Por estrato (tarea 1.35): el simétrico con fracción 1,0 restringido a cada tramo de cenit y régimen.
                celda["placebo_c_por_estrato"] = {}
                for eje, fn in (("cenit", ec.estrato_cenit), ("regimen", ec.estrato_regimen)):
                    noms = sorted({fn(f) for f in T if f["dia"] not in excl})
                    celda["placebo_c_por_estrato"][eje] = {
                        n: correr_placebo(T, "c", 1.0, N_C_ESTRATO, SEMILLA_BASE["c_estrato"],
                                          excluir=(lambda f, n=n, fn=fn: fn(f) != n), excl=excl) for n in noms}
                celda["placebo_m"], celda["m_pares_que_salen"] = placebos_m(
                    T, lambda f: f["pasada"].sensor_bucket, excl)
                celda["placebo_m_por_cenit"], _ = placebos_m(T, ec.estrato_cenit, excl)
                out["celdas"].append(celda)
                print("%s %s %s %s: %d pasadas, c(1.0) GANA %s PIERDE %s | %.0f s" % (
                    nom_v, sensor, canal, desde, len(ps), celda["placebo_c"][1]["GANA"]["k"],
                    celda["placebo_c"][1]["PIERDE"]["k"], time.time() - t0), flush=True)
    out["segundos"] = round(time.time() - t0)
    Path(salida).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    Path(resumen).write_text(escribir_resumen(out), encoding="utf-8")


def _t(x):
    return "%d/%d (%.1f %%; IC95 %.1f a %.1f)" % (x["k"], x["n"], 100 * x["tasa"], 100 * x["ic95"][0],
                                                  100 * x["ic95"][1]) if x["n"] else "sin datos"


def escribir_resumen(out):
    L = ["# Placebos de D-44 y de ganancia sobre producción (generado por placebos_produccion.py)", "",
         "Commit `%s`; referencia hasta %s; regla de mínimas %s. Sha256 de la referencia en el JSON." % (
             out["commit"], out["fin_referencia"], out["regla_minimas"]), "",
         "## Sustrato e identidad", "",
         "| ventana | sensor | canal | pasadas MIROVA | prod observa / no observa | alertas <1 MW (pub.) |"
         " negativos (pub.) | identidad: P2 disc., P1b |", "|---|---|---|---|---|---|---|---|"]
    for c in out["celdas"]:
        s, o, i = c["sustrato_p2"], c["cobertura"]["por_lado"], c["identidad"]
        L.append("| %s %s..%s | %s | %s | %d | %d / %d | %d (%d) | %d (%d) | %d, %d/%d |" % (
            c["ventana"], c["desde"], c["hasta"], c["sensor"], c["canal"], c["pasadas_mirova"], o["observado"],
            o["no_observado"], s["alerta_mb"], s["alerta_mb_publicadas"], s["negativos"], s["negativos_publicados"],
            i["p2_discordantes"], i["p1b_abajo"], i["p1b_arriba"]))
    L += ["", "## P2: placebo simétrico (c), tasa de falsos (debe quedar bajo 5 % por cola)", "",
          "BLOQUEA (D-45: el neto va en contra del brazo sin llegar a significancia) no es un falso de la prueba: sin "
          "ningún efecto sale cerca de la mitad de las veces que el neto no es cero. Un BLOQUEA no es evidencia contra "
          "un brazo (verificador de S163).", "",
          "| ventana | sensor | canal | fracción | GANA | PIERDE | BLOQUEA | SIN SUSTRATO | B mediana |",
          "|---|---|---|---|---|---|---|---|---|"]
    for c in out["celdas"]:
        for x in c["placebo_c"]:
            bl = x["resultados"].get("BLOQUEA", 0)
            L.append("| %s | %s | %s | %.2f | %s | %s | %s | %s | %d |" % (
                c["ventana"], c["sensor"], c["canal"], x["fraccion"], _t(x["GANA"]), _t(x["PIERDE"]),
                _t({"k": bl, "n": x["n"], "tasa": bl / x["n"], "ic95": wilson(bl, x["n"])}),
                _t(x["SIN_SUSTRATO"]), x["B_mediana"]))
    L += ["", "## P2: poder (a debe dar GANA, b debe dar PIERDE)", "",
          "| ventana | sensor | canal | fracción | a: GANA | a: SIN SUSTRATO | b: PIERDE | b: SIN SUSTRATO |",
          "|---|---|---|---|---|---|---|---|"]
    for c in out["celdas"]:
        for xa, xb in zip(c["placebo_a"], c["placebo_b"]):
            L.append("| %s | %s | %s | %.2f | %s | %s | %s | %s |" % (
                c["ventana"], c["sensor"], c["canal"], xa["fraccion"], _t(xa["GANA"]), _t(xa["SIN_SUSTRATO"]),
                _t(xb["PIERDE"]), _t(xb["SIN_SUSTRATO"])))
    L += ["", "## P2: placebo simétrico por estrato (fracción 1,0)", "",
          "| ventana | sensor | canal | eje | estrato | GANA | PIERDE | SIN SUSTRATO |", "|---|---|---|---|---|---|---|---|"]
    for c in out["celdas"]:
        for eje, d in c["placebo_c_por_estrato"].items():
            for n, x in d.items():
                L.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
                    c["ventana"], c["sensor"], c["canal"], eje, n, _t(x["GANA"]), _t(x["PIERDE"]),
                    _t(x["SIN_SUSTRATO"])))
    L += ["", "## M: identidad y placebo de ganancia (con comparador no debe quedar MEJORA)", "",
          "| ventana | sensor | canal | estrato | pares | noches | identidad | K/MIROVA |"
          " falsos MEJORA/EMPEORA (calib. sobre K×1,2) | falsos MEJORA d′ | K×1,2 sin / con | K×0,8 sin / con |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in out["celdas"]:
        for nom, e in list(c["placebo_m"].items()) + list(c["placebo_m_por_cenit"].items()):
            if e["identidad"] == "SIN SUSTRATO":
                L.append("| %s | %s | %s | %s | %d | %d | SIN SUSTRATO | | | | | |" % (
                    c["ventana"], c["sensor"], c["canal"], nom, e["n_pares"], e["noches"]))
                continue
            g = e["K_x_1.2"]
            fd = g["falsos_mejora_dprima"]
            L.append("| %s | %s | %s | %s | %d | %d | %s | %.3f | %.3f / %.3f | %s | %s / %s | %s / %s |" % (
                c["ventana"], c["sensor"], c["canal"], nom, e["n_pares"], e["noches"], e["identidad"],
                e["razon_K_mediana"], g["falsos_mejora_calib"], g["falsos_empeora_calib"],
                "%.3f" % fd if fd is not None else "",
                e["K_x_1.2"]["sin_comparador"], e["K_x_1.2"]["con_comparador"],
                e["K_x_0.8"]["sin_comparador"], e["K_x_0.8"]["con_comparador"]))
    L.append("")
    L.append("Duración: %d s." % out["segundos"])
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    if sys.argv[1] == "--solo-resumen":
        # Regenera el resumen desde un JSON ya corrido (no repite los placebos).
        Path(sys.argv[3]).write_text(escribir_resumen(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))),
                                     encoding="utf-8")
    else:
        main(sys.argv[1], sys.argv[2])
