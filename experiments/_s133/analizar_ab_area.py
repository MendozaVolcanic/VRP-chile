# -*- coding: utf-8 -*-
"""S133 - Veredicto del A/B del AREA del pixel VIIRS (3 brazos).

FICHA SDA (Resolucion CPLT N.372)
================================
Rol            : evaluacion off-line de un A/B. NO participa de la deteccion NRT ni
                 escribe en `data/mirova_equivalent/`. Read-only sobre los tres
                 `data_subdir` aislados de los brazos.
Entradas       : data/_s133_area_control/<vol>.json  (area nadir fija, lo actual)
                 data/_s133_area_geoloc/<vol>.json   (+ area medida)
                 data/_s133_area_corona/<vol>.json   (+ fondo Eq.6 en VIIRS375)
                 ground truth MIROVA CONS union OCR (via experiments/_s126_lib).
Salida         : experiments/_s133/resultado_ab_area.json - TODOS los numeros que se
                 citen despues salen de ahi y no de esta consola (regla S91).
Criterios      : CONGELADOS antes de correr, en docs/s132/AB_AREA_GEOLOCALIZADA.md,
                 seccion "Lo que falta correr, y con que criterio". Este script no los
                 reinterpreta: los ejecuta.

EL FENOMENO, en una linea
=========================
El VRP es una radiancia -energia por unidad de area- MULTIPLICADA por el area del
pixel. Un pixel oblicuo del borde del swath cubre hasta 4,38 veces mas terreno que uno
del nadir; usar el area del nadir en esas pasadas sub-reporta la magnitud justo ahi.
S131 midio, por pasada, que la razon contra MIROVA cae de 0,77 en el nadir a 0,45 a
50 grados o mas, y que la ley de area del ATBD deja los cinco bins planos. Este script
comprueba si medir el area en la geolocalizacion del granule reproduce esa planitud
sobre datos REALES reprocesados, y si el fondo de la Eq.6 cierra el deficit uniforme
de ~0,82 que el area no explica.

LOS CUATRO CRITERIOS, tal como estan escritos
=============================================
  1. el bin de 50+ y el de nadir, AMBOS entre 0,9 y 1,1;
  2. >= 6 de 8 volcanes en banda en VIIRS375;
  3. 0 noches de MIROVA perdidas -mirando FN a nivel RECORD, no la mediana-;
  4. pares con razon > 2 en <= 10 %.

Una sola cosa el texto no la fija y hay que leerla: en el criterio 2 dice "en banda"
sin repetir cual. Se toma la MISMA banda 0,9-1,1 del criterio 1, aplicada a la mediana
por volcan de la razon por pasada. Queda dicho aca para que se vea que es una lectura y
no un numero inventado; si Nicolas la quiere distinta, se cambia UNA constante.

POR QUE POR PASADA Y NUNCA POR NOCHE
====================================
El maximo de la noche mezcla pasadas de angulos cenitales distintos: una pasada oblicua
debil termina comparada contra la mejor pasada de MIROVA de esa noche, que suele ser
otra y mas cerca del nadir. Eso inflo el gradiente que S130 heredo (0,74 -> 0,25 en vez
de 0,77 -> 0,45). La ground truth trae hora al segundo, asi que el pareo honesto contra
MIROVA es por pasada (<= 20 min), y el pareo entre brazos es por `granule`, que es el
identificador del objeto fisico.

LAS MINAS DE ESTE PROYECTO, esquivadas a proposito
==================================================
  · VIIRS375 = sensor VIIRS_* SIN sufijo; el sufijo _750 es M-band. El bucket lo
    resuelve `_s126_lib.bucket`, que ya conoce la convencion (A48: un regex inventado
    tipo "375 in s" clasifica mal nuestros I-band y da conclusiones falsas).
  · Para VIIRS375 la magnitud que ve el operador es `f5_core_vrp_mw` -el recorte del
    cumulo al entorno del pixel pico, el mismo recorte que hace MIROVA al informar el
    cumulo del crater- con fallback a `primary_cluster.vrp_mw` cuando falta (asimetria
    A46: sin cumulo validado o sin pixeles dentro del inner no se recomputa). Para
    VIIRS750 la magnitud es `primary_cluster.vrp_mw` (A10, matiz S132).
  · Nunca se compara con != sobre NaN: `NaN != NaN` da True y un campo ausente se
    contaria como diferencia. Primero se decide si el valor EXISTE (`_es_finito`), y
    recien despues se lo compara. Asi "fallo" C4 en S132.
  · Se estratifica por volcan y NO se publica una mediana agrupada como veredicto: los
    regimenes son opuestos (focal caliente contra nevado de senal debil) y agrupar
    invierte veredictos (S126).
  · Cada numero lleva su denominador y su ventana (A90).

USO
===
    python experiments/_s133/analizar_ab_area.py

Si los brazos todavia no corrieron, sale con codigo 2 y dice que falta. No es un error
del script: es que el experimento no se corrio.
"""
from __future__ import annotations

import csv
import io
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import ALIAS, FUENTES_GT, SENSOR_MAP, bucket  # noqa: E402

# ===================== parametros del pre-registro (congelados) =====================

BRAZOS = ["_s133_area_control", "_s133_area_geoloc", "_s133_area_corona"]
BRAZO_CONTROL = "_s133_area_control"

# Los ocho salen del dato, no del gusto: son los unicos con pares VIIRS375 contra MIROVA
# y poblacion en los dos bins extremos. Medido en experiments/_s133/sustrato_ab_area.py.
VOLCANES = [
    "Lascar", "Isluga", "Lastarria", "PuyehueCordonCaulle",
    "PlanchonPeteroa", "Tupungatito", "Chaiten", "Villarrica",
]

# Criterio 1 y 2 — la banda de paridad contra MIROVA.
BANDA = (0.9, 1.1)
# Criterio 2 — cuantos volcanes tienen que caer en banda.
MIN_VOLCANES_EN_BANDA = 6
# Criterio 4 — cola de sobre-estimacion tolerada.
RAZON_COLA = 2.0
FRACCION_COLA_MAX = 0.10
# Piso de n para que la mediana de un bin o de un volcan signifique algo. Es el MIN_N
# de S131 (`_s131_audit/magnitud/03_pares_por_pasada.py`); se hereda para no mover la
# vara a mitad de camino. Un bin por debajo NO se juzga: se reporta como no evaluable.
MIN_N = 15

BINS = ("0-15", "15-25", "25-35", "35-50", "50+")
BINS_JUZGADOS = ("0-15", "50+")     # el nadir y el borde del swath
TOL = timedelta(minutes=20)
HORAS_NOCHE = (3, 9)                # el MIR solo se usa de noche

SALIDA = os.path.join(HERE, "resultado_ab_area.json")


# ===================== utilidades numericas defensivas =====================

def _es_finito(x):
    """True solo si x es un numero real utilizable.

    POR QUE existe: `None`, `"NaN"` y `float('nan')` son tres formas de "no hay dato"
    que el JSON mezcla. Decidir la EXISTENCIA antes de comparar es lo que evita medir
    la semantica de NaN en vez del dato.
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
    ys = sorted(float(x) for x in xs if _es_finito(x))
    n = len(ys)
    if n == 0:
        return None
    m = n // 2
    return ys[m] if n % 2 else (ys[m - 1] + ys[m]) / 2.0


def _percentil(xs, q):
    ys = sorted(float(x) for x in xs if _es_finito(x))
    if not ys:
        return None
    k = (len(ys) - 1) * (q / 100.0)
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    if lo == hi:
        return ys[lo]
    return ys[lo] * (hi - k) + ys[hi] * (k - lo)


def _resumen(xs):
    ys = [float(x) for x in xs if _es_finito(x)]
    if not ys:
        return {"n": 0}
    return {"n": len(ys), "mediana": _mediana(ys), "p10": _percentil(ys, 10),
            "p90": _percentil(ys, 90), "min": min(ys), "max": max(ys)}


def _en_banda(x):
    return x is not None and BANDA[0] <= x <= BANDA[1]


def _parse_dt(s):
    """El pipeline persiste `datetime_utc` con y sin segundos. Las dos formas valen."""
    s = (s or "").replace("T", " ").strip()[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def _bin_de(zen):
    z = abs(float(zen))
    if z < 15:
        return "0-15"
    if z < 25:
        return "15-25"
    if z < 35:
        return "25-35"
    if z < 50:
        return "35-50"
    return "50+"


# ============================== magnitud publicada ==============================

def magnitud_publicada(rec):
    """La magnitud que el OPERADOR ve para este record, y de donde sale.

    VIIRS375 -> `f5_core_vrp_mw` (el nucleo: el recorte del cumulo al entorno del pixel
    pico, que es el mismo recorte que hace MIROVA al informar el cumulo del crater),
    con fallback a `primary_cluster.vrp_mw` cuando el campo no esta -asimetria A46: sin
    cumulo validado o sin pixeles dentro del inner el pipeline no lo recomputa-.
    VIIRS750 y MODIS -> `primary_cluster.vrp_mw` (A10).

    NUNCA `record.vrp_mw`: ese es la suma de TODA la escena, no el cumulo del crater.
    """
    bk = bucket(rec.get("sensor"))
    pc = rec.get("primary_cluster") or {}
    v_pc = _f(pc.get("vrp_mw"))
    if bk != "v375":
        return v_pc, "primary_cluster.vrp_mw"
    v_f5 = _f(rec.get("f5_core_vrp_mw"))
    if v_f5 is not None:
        return v_f5, "f5_core_vrp_mw"
    return v_pc, "primary_cluster.vrp_mw (fallback A46)"


# ================================ carga de datos ================================

def _ruta(brazo, vol):
    return os.path.join(ROOT, "data", brazo, vol + ".json")


def _faltantes():
    return [_ruta(b, v) for b in BRAZOS for v in VOLCANES
            if not os.path.exists(_ruta(b, v))]


def cargar_brazo(brazo, vol, sensor="v375"):
    """{granule: record} con SOLO los records del bucket pedido.

    El pareo entre brazos se indexa por `granule`: es el identificador del objeto
    fisico. Un granule duplicado dentro de un brazo seria sintoma de reproceso sucio,
    no un empate a resolver: se reporta en vez de elegir uno en silencio.
    """
    with io.open(_ruta(brazo, vol), encoding="utf-8") as fh:
        doc = json.load(fh)
    recs = doc["records"] if isinstance(doc, dict) else doc
    por_granule, duplicados = {}, []
    for r in recs:
        if bucket(r.get("sensor")) != sensor:
            continue
        g = r.get("granule")
        if not g:
            continue
        if g in por_granule:
            duplicados.append(g)
            continue
        por_granule[g] = r
    return por_granule, duplicados


def cargar_gt():
    """{(vol, bucket): [(datetime, vrp_mw)]} de ALERTAS nocturnas de MIROVA.

    CONS union OCR (A11: el OCR no es validacion, es COMPLEMENTO — MIROVA publica en
    latest.php y deja el resto solo en las imagenes por volcan).
    """
    out = defaultdict(list)
    vistos = 0
    for fname in FUENTES_GT:
        path = os.path.join(ROOT, fname)
        if not os.path.exists(path):
            continue
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            for r in csv.DictReader(fh):
                nom = (r.get("Volcan") or "").strip()
                vol = next((v for v, al in ALIAS.items() if nom in al), None)
                if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                    continue
                bk = SENSOR_MAP.get((r.get("Sensor") or "").strip().upper())
                f = r.get("Fecha_Satelite_UTC") or ""
                if not bk:
                    continue
                try:
                    vrp = float(r.get("VRP_MW") or 0)
                    d = datetime.strptime(f[:19], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
                if vrp <= 0 or not (HORAS_NOCHE[0] <= d.hour <= HORAS_NOCHE[1]):
                    continue
                out[(vol, bk)].append((d, vrp))
                vistos += 1
    return out, vistos


def _mirova_de_la_pasada(gt, vol, bk, dt_rec):
    """La fila ALERTA de MIROVA mas cercana en tiempo dentro de +-20 min, o None."""
    if dt_rec is None:
        return None
    cand = [(abs(d - dt_rec), d, v) for d, v in gt.get((vol, bk), ()) if abs(d - dt_rec) <= TOL]
    if not cand:
        return None
    cand.sort(key=lambda t: t[0])
    return {"dt_mirova_utc": cand[0][1].strftime("%Y-%m-%d %H:%M:%S"),
            "vrp_mirova_mw": cand[0][2],
            "delta_min": round(cand[0][0].total_seconds() / 60.0, 2)}


# ================================== los pares ==================================

def pares_de(brazo, vol, gt, sensor="v375"):
    """Lista de pares POR PASADA de un brazo contra MIROVA.

    Par = record nuestro con magnitud publicada > 0 y `sensor_zenith_deg` persistido,
    emparejado con la ALERTA de MIROVA mas cercana a <= 20 min.
    """
    recs, duplicados = cargar_brazo(brazo, vol, sensor)
    pares, sin_zenith, sin_gt, sin_magnitud = [], 0, 0, 0
    for g, r in recs.items():
        mw, fuente = magnitud_publicada(r)
        if mw is None or mw <= 0:
            sin_magnitud += 1
            continue
        zen = r.get("sensor_zenith_deg")
        if not _es_finito(zen):
            sin_zenith += 1
            continue
        d = _parse_dt(r.get("datetime_utc"))
        m = _mirova_de_la_pasada(gt, vol, sensor, d)
        if m is None:
            sin_gt += 1
            continue
        pares.append({
            "granule": g,
            "datetime_utc": r.get("datetime_utc"),
            "sensor_zenith_deg": float(zen),
            "bin": _bin_de(zen),
            "vrp_ours_mw": mw,
            "fuente_magnitud": fuente,
            "vrp_mirova_mw": m["vrp_mirova_mw"],
            "razon_ours_sobre_mirova": mw / m["vrp_mirova_mw"],
        })
    return pares, {"n_records_del_bucket": len(recs),
                   "n_sin_magnitud_publicada": sin_magnitud,
                   "n_sin_sensor_zenith_deg": sin_zenith,
                   "n_sin_alerta_mirova_a_20min": sin_gt,
                   "granules_duplicados": duplicados}


# ================================== criterios ==================================

def crit_1_bins(pares):
    """Criterio 1 - el bin de 50+ y el del nadir, AMBOS entre 0,9 y 1,1.

    POR QUE estos dos bins y no la mediana global: el fenomeno es un GRADIENTE con el
    angulo. Una mediana global puede estar en banda con el nadir alto y el borde bajo,
    que es exactamente la enfermedad que el area viene a curar. Los dos extremos son la
    prueba; los tres del medio se reportan para ver la forma.
    """
    por_bin = {}
    for b in BINS:
        rs = [p["razon_ours_sobre_mirova"] for p in pares if p["bin"] == b]
        med = _mediana(rs)
        por_bin[b] = {
            "n_pares": len(rs), "mediana_razon": med,
            "distribucion": _resumen(rs),
            "evaluable": len(rs) >= MIN_N,
            "en_banda": bool(_en_banda(med)) if len(rs) >= MIN_N else None,
        }
    evaluables = all(por_bin[b]["evaluable"] for b in BINS_JUZGADOS)
    pasa = evaluables and all(por_bin[b]["en_banda"] for b in BINS_JUZGADOS)
    return {
        "criterio": "1 - el bin de 50+ y el de nadir, ambos en banda",
        "banda": list(BANDA), "min_n_por_bin": MIN_N,
        "bins_juzgados": list(BINS_JUZGADOS),
        "por_bin": por_bin,
        "los_dos_bins_evaluables": bool(evaluables),
        "pasa": bool(pasa),
    }


def crit_2_volcanes(por_volcan):
    """Criterio 2 - >= 6 de 8 volcanes en banda en VIIRS375.

    Se cuenta por VOLCAN, no sobre el pozo comun: los regimenes son opuestos (Lascar
    focal y caliente contra Villarrica nevado y debil) y una mediana agrupada invierte
    veredictos (S126). "En banda" se lee con la MISMA banda del criterio 1 (ver la
    cabecera: es la unica lectura que el texto pre-registrado deja abierta).
    """
    detalle, en_banda, no_evaluables = {}, 0, []
    for vol, d in por_volcan.items():
        rs = [p["razon_ours_sobre_mirova"] for p in d["pares"]]
        med = _mediana(rs)
        evaluable = len(rs) >= MIN_N
        ok = bool(_en_banda(med)) if evaluable else None
        if ok:
            en_banda += 1
        if not evaluable:
            no_evaluables.append(vol)
        detalle[vol] = {"n_pares": len(rs), "mediana_razon": med,
                        "evaluable": evaluable, "en_banda": ok,
                        "distribucion": _resumen(rs)}
    return {
        "criterio": "2 - >= 6 de 8 volcanes en banda",
        "banda": list(BANDA), "min_n_por_volcan": MIN_N,
        "n_volcanes_evaluados": len(por_volcan),
        "n_en_banda": en_banda, "minimo_exigido": MIN_VOLCANES_EN_BANDA,
        "volcanes_no_evaluables_por_n": no_evaluables,
        "por_volcan": detalle,
        "pasa": bool(en_banda >= MIN_VOLCANES_EN_BANDA),
    }


def crit_3_fn(por_volcan_brazo, por_volcan_control, gt):
    """Criterio 3 - 0 noches de MIROVA perdidas, mirando FN a NIVEL RECORD.

    El area es un multiplicador; A67 enseno que un cambio de area puede APAGAR
    detecciones y no solo mover magnitudes. La auditoria de S131 anoto ademas que el
    Test 1 de hoy integra `suma max(0, L - L_bg)` SIN area, asi que la prediccion es 0
    por construccion. El criterio se conserva igual -medir FN a nivel record es barato
    y protege contra cualquier gate en MW que quede aguas abajo-, y si diera distinto
    de 0 lo primero que hay que revisar es POR DONDE entro el area a la deteccion, no
    la magnitud.

    Perdida = granule donde el CONTROL publica magnitud > 0 y el brazo no, y donde
    MIROVA publico una ALERTA en esa misma pasada.
    """
    perdidas, ganadas, sin_gt = [], [], 0
    for vol in por_volcan_brazo:
        ctrl = por_volcan_control[vol]["recs"]
        brazo = por_volcan_brazo[vol]["recs"]
        for g in set(ctrl) & set(brazo):
            a, _fa = magnitud_publicada(ctrl[g])
            b, _fb = magnitud_publicada(brazo[g])
            det_a = a is not None and a > 0
            det_b = b is not None and b > 0
            if det_a == det_b:
                continue
            r = brazo[g]
            m = _mirova_de_la_pasada(gt, vol, "v375", _parse_dt(r.get("datetime_utc")))
            item = {"volcano": vol, "granule": g,
                    "datetime_utc": r.get("datetime_utc"),
                    "mirova_publico_esa_pasada": m is not None,
                    "vrp_mirova_mw": None if m is None else m["vrp_mirova_mw"],
                    "vrp_control_mw": a, "vrp_brazo_mw": b,
                    "triggered_test1_control": bool(ctrl[g].get("triggered_test1")),
                    "triggered_test1_brazo": bool(r.get("triggered_test1"))}
            if m is None:
                sin_gt += 1
            (ganadas if det_b else perdidas).append(item)
    confirmadas = [p for p in perdidas if p["mirova_publico_esa_pasada"]]
    return {
        "criterio": "3 - 0 noches de MIROVA perdidas (FN a nivel record)",
        "definicion_perdida": ("granule donde el control publica magnitud > 0, el brazo "
                               "no, y MIROVA publico ALERTA en esa misma pasada"),
        "prediccion": 0,
        "n_pierde_deteccion": len(perdidas),
        "n_pierde_pasada_que_MIROVA_publico": len(confirmadas),
        "n_gana_deteccion": len(ganadas),
        "n_cambios_sin_respaldo_mirova": sin_gt,
        "perdidas_confirmadas": confirmadas,
        "perdidas_sin_respaldo_mirova": [p for p in perdidas
                                         if not p["mirova_publico_esa_pasada"]],
        "ganadas": ganadas,
        "pasa": bool(not confirmadas),
    }


def crit_4_cola(pares):
    """Criterio 4 - pares con razon > 2 en <= 10 %.

    Una mediana en banda puede convivir con una cola de sobre-estimaciones gruesas: el
    criterio 1 mira el centro, este mira la cola. Se cuenta sobre TODOS los pares del
    brazo, con el denominador dicho (A90).
    """
    rs = [p["razon_ours_sobre_mirova"] for p in pares]
    n = len(rs)
    cola = [r for r in rs if r > RAZON_COLA]
    frac = (len(cola) / float(n)) if n else None
    return {
        "criterio": "4 - pares con razon > 2 en <= 10 %",
        "umbral_razon": RAZON_COLA, "fraccion_maxima": FRACCION_COLA_MAX,
        "n_pares": n, "n_sobre_umbral": len(cola),
        "fraccion_sobre_umbral": frac,
        "distribucion_razon": _resumen(rs),
        "pasa": bool(frac is not None and frac <= FRACCION_COLA_MAX),
    }


# ================================== veredicto ==================================

def evaluar_brazo(brazo, gt, control_recs=None):
    por_volcan, todos = {}, []
    for vol in VOLCANES:
        pares, diag = pares_de(brazo, vol, gt)
        recs, _dup = cargar_brazo(brazo, vol)
        por_volcan[vol] = {"pares": pares, "diagnostico": diag, "recs": recs}
        todos.extend(pares)

    res = {
        "brazo": brazo,
        "n_pares_totales": len(todos),
        "ventana_utc": {
            "desde": min([p["datetime_utc"] for p in todos] or [None]),
            "hasta": max([p["datetime_utc"] for p in todos] or [None]),
        },
        "fuentes_de_magnitud": _conteo([p["fuente_magnitud"] for p in todos]),
        "diagnostico_por_volcan": {v: por_volcan[v]["diagnostico"] for v in por_volcan},
        "C1_bins": crit_1_bins(todos),
        "C2_volcanes": crit_2_volcanes(por_volcan),
        "C4_cola": crit_4_cola(todos),
    }
    if control_recs is not None:
        res["C3_fn"] = crit_3_fn(por_volcan, control_recs, gt)
    else:
        res["C3_fn"] = {"criterio": "3 - 0 noches de MIROVA perdidas (FN a nivel record)",
                        "nota": "el control es su propia referencia; no aplica",
                        "pasa": True}
    res["pasa_los_cuatro"] = all(res[c]["pasa"] for c in
                                 ("C1_bins", "C2_volcanes", "C3_fn", "C4_cola"))
    # `recs` es pesado (los records enteros): se devuelve aparte y NO va al JSON.
    return res, por_volcan


def _conteo(xs):
    out = defaultdict(int)
    for x in xs:
        out[x] += 1
    return dict(out)


def main():
    faltan = _faltantes()
    if faltan:
        # Falla limpia: el experimento no corrio todavia. No es un error del script.
        print("Faltan los JSON de los brazos. Correr primero el workflow")
        print("  .github/workflows/reproc-s133-area-ab.yml")
        print("y bajar los artefactos con `gh run download <run_id> --dir data/`.")
        print("No estan (%d de %d):" % (len(faltan), len(BRAZOS) * len(VOLCANES)))
        for p in faltan:
            print("  -", p)
        return 2

    gt, n_filas_gt = cargar_gt()
    control_res, control_pv = evaluar_brazo(BRAZO_CONTROL, gt)

    out = {
        "_que_es": ("Veredicto S133 del A/B del area del pixel VIIRS. Criterios "
                    "congelados en docs/s132/AB_AREA_GEOLOCALIZADA.md; este script no "
                    "los reinterpreta."),
        "_brazos": BRAZOS,
        "_volcanes": VOLCANES,
        "_sensor": "VIIRS375 (VIIRS_* sin sufijo; el sufijo _750 es M-band, A48)",
        "_pareo": ("contra MIROVA por PASADA (<=20 min, ALERTA nocturna 03-09 UTC, "
                   "CONS union OCR); entre brazos por `granule`"),
        "_magnitud": ("VIIRS375: f5_core_vrp_mw con fallback a primary_cluster.vrp_mw "
                      "(A46); nunca record.vrp_mw"),
        "_lectura_declarada": ("el criterio 2 dice 'en banda' sin repetir cual: se toma "
                               "la misma banda %s del criterio 1" % (list(BANDA),)),
        "_parametros": {"banda": list(BANDA), "min_volcanes_en_banda": MIN_VOLCANES_EN_BANDA,
                        "razon_cola": RAZON_COLA, "fraccion_cola_max": FRACCION_COLA_MAX,
                        "min_n": MIN_N, "tolerancia_pareo_min": 20},
        "_ground_truth": {"n_filas_alerta_nocturnas": n_filas_gt,
                          "fuentes": list(FUENTES_GT)},
        "por_brazo": {},
    }

    for brazo in BRAZOS:
        if brazo == BRAZO_CONTROL:
            out["por_brazo"][brazo] = control_res
            continue
        res, _pv = evaluar_brazo(brazo, gt, control_recs=control_pv)
        out["por_brazo"][brazo] = res

    out["veredicto"] = {
        b: {"C1": out["por_brazo"][b]["C1_bins"]["pasa"],
            "C2": out["por_brazo"][b]["C2_volcanes"]["pasa"],
            "C3": out["por_brazo"][b]["C3_fn"]["pasa"],
            "C4": out["por_brazo"][b]["C4_cola"]["pasa"],
            "los_cuatro": out["por_brazo"][b]["pasa_los_cuatro"]}
        for b in BRAZOS
    }
    # NO se elige "ganador" automaticamente: el flip es decision de Nicolas (A45). El
    # script dice cuales brazos pasan los cuatro criterios, y nada mas.
    out["brazos_que_pasan_los_cuatro"] = [
        b for b in BRAZOS if b != BRAZO_CONTROL and out["por_brazo"][b]["pasa_los_cuatro"]]

    with io.open(SALIDA, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, indent=1, ensure_ascii=False, sort_keys=False))

    print("Escrito:", SALIDA)
    for b in BRAZOS:
        v = out["veredicto"][b]
        print("  %-22s n_pares=%5d  C1=%s C2=%s C3=%s C4=%s"
              % (b, out["por_brazo"][b]["n_pares_totales"],
                 v["C1"], v["C2"], v["C3"], v["C4"]))
    print("Los numeros se citan del JSON, no de esta consola (S91).")
    print("El flip es decision de Nicolas (A45): esto no adopta nada.")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main())
