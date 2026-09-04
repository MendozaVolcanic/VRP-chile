# -*- coding: utf-8 -*-
"""S133 — Veredicto del A/B de B22 como banda MIR primaria en MODIS.

FICHA SDA (Resolucion CPLT N.372)
================================
Rol            : evaluacion off-line de un A/B. NO participa de la deteccion NRT
                 ni escribe en `data/mirova_equivalent/`. Read-only sobre los dos
                 `data_subdir` aislados de los brazos.
Entradas       : data/_s133_b22_control/<vol>.json  (B21 primaria, lo actual)
                 data/_s133_b22_enabled/<vol>.json  (B22 primaria, el paper)
                 ground truth MIROVA CONS union OCR (pipeline/mirova_csv_loader).
Salida         : experiments/_s133/resultado_ab_b22.json — TODOS los numeros que
                 se citen despues salen de ahi y no de esta consola (regla S91).
Criterios      : CONGELADOS antes de correr, en docs/s133/B22_EVIDENCIA.md,
                 seccion "Validacion propuesta". Este script no los reinterpreta:
                 los ejecuta.

EL FENOMENO, en una linea
=========================
B21 y B22 son el mismo trozo del espectro (3,9 um) visto por dos detectores de
distinta ganancia. B22 tiene una decima parte del ruido de B21 (NEdT 0,017 contra
0,183 K) y a cambio se satura pasando los ~331 K. Coppola 2016a manda B22 y deja
B21 solo para la saturacion; el repo hace hoy lo inverso. Como la banda primaria
fija el ruido del fondo, y el fondo fija donde caen los umbrales contextuales
N.sigma, el cambio puede mover DETECCION y no solo magnitud (A67) — aunque el
efecto medido sobre el fondo sea de 0,0036 K, indistinguible de cero.

POR QUE SE PAREA POR GRANULE Y NO POR FECHA
===========================================
Una noche puede tener dos pasadas MODIS (Terra y Aqua) sobre el mismo volcan. Son
dos objetos fisicos distintos, con distinto angulo cenital y distinto fondo.
Parear por fecha los mezcla y compara el Terra de un brazo contra el Aqua del
otro. El `granule` es el identificador del objeto; es el unico pareo honesto.

POR QUE NUNCA SE COMPARA CON != SOBRE NaN
=========================================
En S132 el criterio C4 "fallo" midiendo la semantica de pandas en vez del dato:
`NaN != NaN` da True, asi que un campo ausente se contaba como diferencia. Aca
toda comparacion pasa por `_es_finito()` y las mascaras son explicitas: primero
se decide si el valor EXISTE, y recien despues se lo compara.

USO
===
    python experiments/_s133/analizar_ab_b22.py

Si los brazos todavia no corrieron, sale con codigo 2 y dice que falta. No es un
error del script: es que el experimento no se corrio.
"""
from __future__ import annotations

import io
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# --- Parametros del pre-registro. Congelados; no se tocan al ver resultados. ---

BRAZO_OFF = "_s133_b22_control"   # B21 primaria (lo que corre hoy)
BRAZO_ON = "_s133_b22_enabled"    # B22 primaria (lo que dice el paper)

# Lascar es el mas caliente y el de sigma mas alto; Villarrica el nevado de senal
# debil, que es donde un sigma menor moveria un umbral si lo va a mover (A83).
# NUNCA leer la mediana agrupada de los dos: son regimenes opuestos.
VOLCANES = ["Lascar", "Villarrica"]

# C1 — el fondo, en kelvin. Prediccion -0,0036 K.
C1_TOLERANCIA_K = 0.05
# C3 — la magnitud, en razon. Un cambio de RUIDO no deberia mover la senal.
C3_BANDA = (0.95, 1.05)
# C3b — la paridad contra MIROVA no puede salirse de la banda de siempre.
C3_PARIDAD_MIROVA = (0.5, 2.0)
# C4 — techo de saturacion de B22. Es el unico caso donde repo y paper coinciden;
# si aparece un solo pixel encima, el A/B deja de aislar la diferencia entre bandas.
C4_TECHO_B22_K = 331.0

SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "resultado_ab_b22.json")

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
CONS = os.path.join(SNAP, "registro_vrp_consolidado.csv")
OCR = os.path.join(SNAP, "registro_vrp_ocr.csv")


# ===================== utilidades numericas defensivas =====================

def _es_finito(x):
    """True solo si x es un numero real utilizable.

    POR QUE existe: `None`, `"NaN"` y `float('nan')` son tres formas de "no hay
    dato" que el JSON mezcla. Decidir la EXISTENCIA antes de comparar es lo que
    evita el bug de S132 (comparar con != sobre NaN mide pandas, no el dato).
    """
    if x is None or isinstance(x, bool):
        return False
    try:
        v = float(x)
    except (TypeError, ValueError):
        return False
    return math.isfinite(v)


def _f(x, defecto=None):
    return float(x) if _es_finito(x) else defecto


def _mediana(xs):
    ys = sorted(x for x in xs if _es_finito(x))
    n = len(ys)
    if n == 0:
        return None
    m = n // 2
    return float(ys[m]) if n % 2 else (float(ys[m - 1]) + float(ys[m])) / 2.0


def _percentil(xs, q):
    ys = sorted(x for x in xs if _es_finito(x))
    if not ys:
        return None
    k = (len(ys) - 1) * (q / 100.0)
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    if lo == hi:
        return float(ys[lo])
    return float(ys[lo]) * (hi - k) + float(ys[hi]) * (k - lo)


def _resumen(xs):
    ys = [float(x) for x in xs if _es_finito(x)]
    if not ys:
        return {"n": 0}
    return {"n": len(ys), "mediana": _mediana(ys), "p10": _percentil(ys, 10),
            "p90": _percentil(ys, 90), "min": min(ys), "max": max(ys)}


# ============================== carga de datos ==============================

def _ruta_brazo(brazo, vol):
    return os.path.join(ROOT, "data", brazo, vol + ".json")


def _faltantes():
    out = []
    for brazo in (BRAZO_OFF, BRAZO_ON):
        for vol in VOLCANES:
            p = _ruta_brazo(brazo, vol)
            if not os.path.exists(p):
                out.append(p)
    return out


def _cargar_modis(brazo, vol):
    """Devuelve {granule: record} con SOLO los MODIS del brazo.

    El pareo se indexa por `granule` (ver cabecera). Si un brazo trajera dos
    records para el mismo granule seria un sintoma de reproceso sucio, no un
    empate a resolver: se reporta en `avisos` en vez de elegir uno en silencio.
    """
    with io.open(_ruta_brazo(brazo, vol), encoding="utf-8") as f:
        doc = json.load(f)
    recs = doc.get("records", doc) if isinstance(doc, dict) else doc
    por_granule, duplicados = {}, []
    for r in recs:
        if "MODIS" not in str(r.get("sensor", "")).upper():
            continue
        g = r.get("granule")
        if not g:
            continue
        if g in por_granule:
            duplicados.append(g)
            continue
        por_granule[g] = r
    return por_granule, duplicados


def _pc_vrp(rec):
    pc = rec.get("primary_cluster") or {}
    return _f(pc.get("vrp_mw"))


def _detectado(rec):
    """Detectado = el cumulo primario publica magnitud > 0.

    POR QUE `primary_cluster.vrp_mw` y no `record.vrp_mw`: el segundo es la suma
    de TODA la escena; el primero es el cumulo anclado al crater, que es lo que
    MIROVA informa y lo que el dashboard usa (A10).
    """
    v = _pc_vrp(rec)
    return v is not None and v > 0.0


# ======================= ground truth MIROVA (A11: CONS union OCR) ==========

def _noches_mirova_modis(vol):
    """Fechas UTC (YYYY-MM-DD) en que MIROVA publico una ALERTA MODIS del volcan.

    Se usa a nivel de NOCHE y no de granule porque el CSV de MIROVA no informa el
    granule: es lo mas fino que el ground truth permite sin inventar un pareo.
    """
    try:
        from pipeline.mirova_csv_loader import load_mirova_alertas
    except ImportError as e:      # el loader vive en el repo; si falta, decirlo
        return None, "no se pudo importar pipeline.mirova_csv_loader: %s" % e
    if not (os.path.exists(CONS) or os.path.exists(OCR)):
        return None, "no hay CSV de ground truth en %s" % SNAP
    fechas = {}
    for a in load_mirova_alertas(cons_path=CONS, ocr_path=OCR, volcano=vol):
        if a.get("sensor_bucket") != "MODIS":
            continue
        f = (a.get("fecha_utc") or "")[:10]
        if not f:
            continue
        v = _f(a.get("vrp_mw"), 0.0)
        fechas[f] = max(fechas.get(f, 0.0), v)
    return fechas, None


# ================================ criterios ================================

def _c1_fondo(pares):
    """C1 — el fondo, en kelvin. Mediana pareada de sigma_ON - sigma_OFF.

    Prediccion -0,0036 K: restando en cuadratura el ruido instrumental, el sigma
    del anillo pasa de 4,586 a 4,582 K. Falla si |mediana| > 0,05 K, porque eso ya
    no seria ruido sino desacuerdo de CALIBRACION entre las dos bandas, y hay que
    entenderlo antes de adoptar.
    """
    deltas, sin_dato = [], 0
    for _g, off, on in pares:
        a = _f(off.get("diag_sigma_bg_k"))
        b = _f(on.get("diag_sigma_bg_k"))
        if a is None or b is None:      # mascara explicita, nunca != sobre NaN
            sin_dato += 1
            continue
        deltas.append(b - a)
    med = _mediana(deltas)
    ok = med is not None and abs(med) <= C1_TOLERANCIA_K
    return {
        "criterio": "C1 — el fondo, en kelvin",
        "unidad": "K", "prediccion": -0.0036, "tolerancia_abs": C1_TOLERANCIA_K,
        "n_pares_con_dato": len(deltas), "n_pares_sin_dato": sin_dato,
        "mediana_delta_k": med, "distribucion_delta_k": _resumen(deltas),
        "sigma_off": _resumen([_f(o.get("diag_sigma_bg_k")) for _g, o, _n in pares]),
        "sigma_on": _resumen([_f(n.get("diag_sigma_bg_k")) for _g, _o, n in pares]),
        "pasa": bool(ok),
    }


def _c2_deteccion(pares, noches_mirova):
    """C2 — la deteccion, en pasadas. Pares que cambian `triggered_test1`.

    Prediccion 0. GANAR detecciones no es falla: se reporta. FALLA solo si se
    PIERDE una pasada que MIROVA publico — A79, verificar el evento concreto y no
    la metrica agregada. Por eso cada perdida se cruza contra el ground truth y se
    lista una por una con su granule.
    """
    gana, pierde = [], []
    for g, off, on in pares:
        a, b = bool(off.get("triggered_test1")), bool(on.get("triggered_test1"))
        if a == b:
            continue
        fecha = (on.get("datetime_utc") or off.get("datetime_utc") or "")[:10]
        item = {"granule": g, "fecha_utc": fecha,
                "mirova_publico_esa_noche": (
                    None if noches_mirova is None else fecha in noches_mirova),
                "vrp_mirova_mw": (
                    None if noches_mirova is None else noches_mirova.get(fecha)),
                "pc_vrp_off": _pc_vrp(off), "pc_vrp_on": _pc_vrp(on)}
        (gana if b else pierde).append(item)
    perdidas_confirmadas = [p for p in pierde if p["mirova_publico_esa_noche"]]
    # Sin ground truth no se puede afirmar que no se perdio nada: no pasa por defecto.
    ok = noches_mirova is not None and not perdidas_confirmadas
    return {
        "criterio": "C2 — la deteccion, en pasadas",
        "unidad": "pasadas", "prediccion": 0,
        "n_pares": len(pares),
        "n_cambian_triggered_test1": len(gana) + len(pierde),
        "n_gana_deteccion": len(gana), "n_pierde_deteccion": len(pierde),
        "n_pierde_pasada_que_MIROVA_publico": len(perdidas_confirmadas),
        "perdidas_confirmadas": perdidas_confirmadas,
        "perdidas_sin_respaldo_mirova": [p for p in pierde
                                         if not p["mirova_publico_esa_noche"]],
        "ganadas": gana,
        "ground_truth_disponible": noches_mirova is not None,
        "pasa": bool(ok),
    }


def _c3_magnitud(pares, noches_mirova):
    """C3 — la magnitud, en MW y en razon.

    Mediana de la razon ON/OFF de `pc.vrp_mw` sobre los pares DETECTADOS EN AMBOS
    brazos, banda 0,95-1,05: esto es un cambio de ruido, no de senal, asi que la
    magnitud no deberia moverse. Es el unico criterio con un efecto de verdad
    incierto — las dos bandas tienen calibraciones independientes y un sesgo
    relativo pequeno si se traslada al VRP. Por eso este A/B vale la pena aunque
    C1 sea un tramite.

    C3b: la paridad contra MIROVA de cada brazo debe seguir dentro de 0,5-2,0.
    """
    razones, mw_off, mw_on = [], [], []
    for _g, off, on in pares:
        if not (_detectado(off) and _detectado(on)):
            continue
        a, b = _pc_vrp(off), _pc_vrp(on)
        if a is None or b is None or a <= 0:   # mascara explicita
            continue
        razones.append(b / a)
        mw_off.append(a)
        mw_on.append(b)
    med = _mediana(razones)
    ok = med is not None and C3_BANDA[0] <= med <= C3_BANDA[1]

    paridad = {}
    if noches_mirova is not None:
        for etiqueta, idx in (("off", 1), ("on", 2)):
            rs = []
            for par in pares:
                rec = par[idx]
                fecha = (rec.get("datetime_utc") or "")[:10]
                m = noches_mirova.get(fecha)
                v = _pc_vrp(rec)
                if m is None or not _es_finito(m) or m <= 0 or v is None or v <= 0:
                    continue
                rs.append(v / m)
            paridad[etiqueta] = {"n": len(rs), "mediana_ratio_ours_mirova": _mediana(rs)}
        for etiqueta in ("off", "on"):
            r = paridad[etiqueta]["mediana_ratio_ours_mirova"]
            paridad[etiqueta]["dentro_de_banda"] = (
                r is not None and C3_PARIDAD_MIROVA[0] <= r <= C3_PARIDAD_MIROVA[1])
        if not paridad["on"]["dentro_de_banda"]:
            ok = False

    return {
        "criterio": "C3 — la magnitud, en MW y en razon",
        "unidad": "razon ON/OFF de primary_cluster.vrp_mw",
        "banda": list(C3_BANDA), "n_pares_detectados_en_ambos": len(razones),
        "mediana_razon_on_sobre_off": med,
        "distribucion_razon": _resumen(razones),
        "vrp_off_mw": _resumen(mw_off), "vrp_on_mw": _resumen(mw_on),
        "C3b_paridad_vs_mirova": paridad or None,
        "C3b_banda": list(C3_PARIDAD_MIROVA),
        "pasa": bool(ok),
    }


def _c4_control_saturacion(pares):
    """C4 — el control. Pixeles con B22 saturada en la muestra.

    Esperado 0 en Lascar, cuyo t_max historico es 294,75 K sobre 930 records. Si da
    0, el A/B aisla EXACTAMENTE la diferencia entre bandas, porque el unico caso en
    que repo y paper coinciden (B22 saturada -> los dos usan B21) no ocurre.

    La comparacion es con mascara explicita: un pixel sin `bt_k` se cuenta en
    `n_px_sin_bt`, no se lo compara. Asi fallo C4 en S132.
    """
    n_px = n_sin_bt = n_sat = 0
    records_con_sat, t_max_vistos = [], []
    for g, off, on in pares:
        for rec in (off, on):
            for px in (rec.get("anomaly_pixels") or []):
                n_px += 1
                bt = px.get("bt_k")
                if not _es_finito(bt):
                    n_sin_bt += 1
                    continue
                if float(bt) > C4_TECHO_B22_K:
                    n_sat += 1
                    if g not in records_con_sat:
                        records_con_sat.append(g)
            t_max_vistos.append(_f(rec.get("t_max_k")))
    return {
        "criterio": "C4 — el control (saturacion de B22)",
        "unidad": "pixeles", "techo_b22_k": C4_TECHO_B22_K, "esperado": 0,
        "n_px_anomalia_evaluados": n_px, "n_px_sin_bt_k": n_sin_bt,
        "n_px_sobre_techo": n_sat, "granules_con_px_saturado": records_con_sat,
        "t_max_k_en_la_muestra": _resumen(t_max_vistos),
        "pasa": bool(n_sat == 0),
    }


# ================================= veredicto ================================

def analizar_volcan(vol):
    off, dup_off = _cargar_modis(BRAZO_OFF, vol)
    on, dup_on = _cargar_modis(BRAZO_ON, vol)
    comunes = sorted(set(off) & set(on))
    pares = [(g, off[g], on[g]) for g in comunes]

    noches, aviso_gt = _noches_mirova_modis(vol)

    res = {
        "volcano": vol,
        "pareo": {
            "por": "granule",
            "n_modis_off": len(off), "n_modis_on": len(on),
            "n_pares": len(pares),
            "solo_en_off": sorted(set(off) - set(on)),
            "solo_en_on": sorted(set(on) - set(off)),
            "granules_duplicados_off": dup_off,
            "granules_duplicados_on": dup_on,
        },
        "ventana_utc": {
            "desde": min([(r.get("datetime_utc") or "") for _g, r, _n in pares] or [None]),
            "hasta": max([(r.get("datetime_utc") or "") for _g, r, _n in pares] or [None]),
        },
        "ground_truth": {
            "n_noches_mirova_modis": None if noches is None else len(noches),
            "aviso": aviso_gt,
        },
        "C1": _c1_fondo(pares),
        "C2": _c2_deteccion(pares, noches),
        "C3": _c3_magnitud(pares, noches),
        "C4": _c4_control_saturacion(pares),
    }
    res["pasa_los_cuatro"] = all(res[c]["pasa"] for c in ("C1", "C2", "C3", "C4"))
    return res


def main():
    faltan = _faltantes()
    if faltan:
        # Falla limpia: el experimento no corrio todavia. No es un error del script.
        print("Faltan los JSON de los brazos. Correr primero el workflow")
        print("  .github/workflows/reproc-s133-b22-ab.yml")
        print("y bajar los artefactos con `gh run download <run_id> --dir data/`.")
        print("No estan:")
        for p in faltan:
            print("  -", p)
        return 2

    out = {
        "_que_es": ("Veredicto S133 del A/B de ENABLE_MODIS_B22_PRIMARY. "
                    "Criterios congelados en docs/s133/B22_EVIDENCIA.md."),
        "_brazos": {"off_control_b21": BRAZO_OFF, "on_b22_primaria": BRAZO_ON},
        "_pareo": "por granule (no por fecha: Terra y Aqua son dos objetos)",
        "_parametros": {
            "C1_tolerancia_k": C1_TOLERANCIA_K, "C3_banda": list(C3_BANDA),
            "C3b_paridad_mirova": list(C3_PARIDAD_MIROVA),
            "C4_techo_b22_k": C4_TECHO_B22_K,
        },
        "por_volcan": {},
    }
    for vol in VOLCANES:
        out["por_volcan"][vol] = analizar_volcan(vol)

    # NO se agrega una mediana de los dos volcanes: Lascar (focal caliente) y
    # Villarrica (nevado de senal debil) son regimenes opuestos y promediarlos
    # invierte veredictos (A83, y la leccion de S126 sobre estratificar).
    out["veredicto"] = {
        vol: {
            "C1": out["por_volcan"][vol]["C1"]["pasa"],
            "C2": out["por_volcan"][vol]["C2"]["pasa"],
            "C3": out["por_volcan"][vol]["C3"]["pasa"],
            "C4": out["por_volcan"][vol]["C4"]["pasa"],
            "los_cuatro": out["por_volcan"][vol]["pasa_los_cuatro"],
        } for vol in VOLCANES
    }
    out["adoptar"] = all(out["por_volcan"][v]["pasa_los_cuatro"] for v in VOLCANES)

    with io.open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=False))

    print("Escrito:", SALIDA)
    for vol in VOLCANES:
        v = out["veredicto"][vol]
        print("  %-12s n_pares=%d  C1=%s C2=%s C3=%s C4=%s" % (
            vol, out["por_volcan"][vol]["pareo"]["n_pares"],
            v["C1"], v["C2"], v["C3"], v["C4"]))
    print("Los numeros se citan del JSON, no de esta consola (S91).")
    return 0 if out["adoptar"] else 1


if __name__ == "__main__":
    sys.exit(main())
