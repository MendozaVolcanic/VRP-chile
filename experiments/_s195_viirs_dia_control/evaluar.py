# -*- coding: utf-8 -*-
"""Evaluador pre-registrado del control diurno de VIIRS (S195). Criterio sellado en
`experiments/_s195_viirs_dia_control/PREREGISTRO.md`; la prueba `tests/test_viirs_dia_control_preregistro_s195.py`
compara el sha256 de este archivo (fin de línea LF) con el que declara el pre-registro.

EL FENÓMENO. De día la banda de 4 µm de VIIRS (I4 en 375 m, M13 en 750 m) suma a la emisión térmica la luz del Sol
reflejada y el calentamiento de superficies iluminadas: laderas de roca desnuda, bordes de nube, suelo de los cauces. El
detector de MIROVA (la vía) publica entonces manchas que no son calor volcánico. El calor volcánico de verdad (lago de
lava, cráter, fumarolas, una erupción) está también de noche, cuando no hay Sol; la mancha solar no.

LA REGLA CANDIDATA (R1, persistencia nocturna). Una publicación diurna se conserva sólo si alguna de sus celdas
alertadas (fila y columna de la grilla fija de MIROVA del sensor) tiene a una celda o menos de distancia una celda que
el detector alertó de noche en los 30 días anteriores, mismo volcán y misma grilla (375 o 750 m). Dos alternativas
declarada antes de medir: R2, la condición se exige a la celda radiante (la de mayor temperatura de brillo), que es la
que decide la posición publicada (regla «radiante»). La regla sólo decide si la pasada se publica: no cambia VRP ni
posición.

QUÉ HACE. Funciones puras, probadas con datos sintéticos de verdad conocida:
  * `indexar_noches`, `celdas_historia`, `conserva`: la regla sobre un record diurno;
  * `etiquetar`: cada publicación diurna en P (protegida de cumbre: la TABLA de MIROVA alertó la pasada con 1 MW o más a
    no más del radio interno), A (artefacto sin respaldo: MIROVA no alertó, 1 MW o más, sin respaldo independiente), R
    (real con respaldo: NHI alertó a ±3 días en una caja que contiene la posición publicada, o, si MIROVA no tiene la
    pasada, la tabla de MIROVA alertó 1 MW o más en la cumbre del mismo volcán a ±12 h), O (otra) o «menor» (bajo
    1 MW, MIROVA no alertó);
  * `evaluar_regla`, `p_hiper`, `veredicto`: el criterio de éxito del §5 del pre-registro;
  * `revisar_instrumento`: las compuertas del §6.
Y la carga de datos reales (`cargar_*`), que importa los módulos del repo sólo cuando se llama.

Uso:
  python experiments/_s195_viirs_dia_control/evaluar.py evaluar --fase desarrollo --raiz <W2> ... --ref <ref>
      --nhi-dir <dir> --produccion data/mirova_equivalent --out r.json
  python experiments/_s195_viirs_dia_control/evaluar.py evaluar --fase veredicto ...   (no antes de FECHA_MIN_VEREDICTO)
"""
from __future__ import annotations

import argparse
import bisect
import collections
import json
import math
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AQUI = Path(__file__).resolve().parent

# ------------------------------------------------------------------------------------------------ valores sellados
SENSORES_VIIRS = ("VIIRS375", "VIIRS750")
PASO_M = {"VIIRS375": 375, "VIIRS750": 750}       # grilla fija de MIROVA (pipeline/grillas_mirova.yaml)
DIAS_HISTORIA = 30          # ventana previa de noches
VECINDAD = 1                # celdas (distancia de Chebyshev) para «la misma celda» entre pasadas
UMBRAL_MW = 1.0             # protegida de MIROVA y artefacto que cuenta (clase_mirova.UMBRAL_PROTEGIDA_MW)
TOL_S = 120                 # pareo con MIROVA (clase_mirova.VENTANA_S)
DIAS_SWIR = 3               # escena NHI a ±3 días de la fecha UTC de la pasada
HORAS_MIROVA_VECINA = 12     # respaldo de una pasada que MIROVA no tiene: su cumbre alertada a ±12 h
N_MIN_A = 6                 # SIN PODER bajo esto
N_MIN_P = 5
QUITAR_A = (2, 3)           # quitar al menos 2/3 de los A: 3 q_A >= 2 n_A
MAX_P_PERDIDAS = 0
MAX_R_PERDIDAS = (1, 3)     # a lo más 1/3 de los R: 3 q_R <= n_R
ALFA_REGLA = {"R1": 0.04, "R2": 0.01}   # suma 0,05 (Bonferroni)
ORDEN_REGLAS = ("R1", "R2")
MIN_FRAC_DIAS_HISTORIA = 0.90
MAX_FRAC_SIN_CELDAS = 0.01
MAX_FRAC_MIROVA_SIN_RECORD = 0.05
MIN_ACUERDO_NOCHE = 0.95
BRAZO = "_s190_ab_diurno_via_on"
VENTANAS_DESARROLLO = (("W2", "2026-06-13", "2026-06-30"), ("W3", "2026-07-20", "2026-07-31"),
                       ("W4", "2026-08-13", "2026-08-31"), ("W5", "2026-09-01", "2026-09-20"),
                       ("W6", "2026-10-01", "2026-10-14"), ("W7", "2026-10-15", "2026-11-15"))
VENTANAS_VEREDICTO = (("V1", "2026-04-01", "2026-06-12"), ("V2", "2026-07-01", "2026-07-19"),
                      ("V3", "2026-08-01", "2026-08-12"), ("V4", "2026-09-21", "2026-09-30"),
                      ("V5", "2026-11-23", "2027-02-28"))
FECHA_MIN_VEREDICTO = "2027-03-07"   # fin de V5 más los ±3 días de NHI y la latencia de la referencia

INVALIDO, SIN_PODER, CUMPLE, NO_CUMPLE = "INVALIDO", "SIN PODER", "CUMPLE", "NO CUMPLE"
ETIQUETAS = ("P", "A", "R", "O", "menor")


def puede_medir_veredicto(hoy_iso):
    """El veredicto se mide una sola vez, desde FECHA_MIN_VEREDICTO (§3 del pre-registro)."""
    return hoy_iso >= FECHA_MIN_VEREDICTO


def n_grilla(b):
    return 50000 // PASO_M[b] + 1


def en_ventanas(d, ventanas):
    return any(w[1] <= d <= w[2] for w in ventanas)


# ------------------------------------------------------------------------------------------------ la regla
def indexar_noches(recs):
    """{(vol, b): (instantes ordenados, conjuntos de celdas)} con los records NOCTURNOS que alertaron alguna celda."""
    por = collections.defaultdict(list)
    for r in recs:
        if r["es_dia"] or r["b"] not in SENSORES_VIIRS:
            continue
        cs = frozenset((c[0], c[1]) for c in r.get("celdas") or ())
        if cs:
            por[(r["vol"], r["b"])].append((r["dt"], cs))
    out = {}
    for k, v in por.items():
        v.sort(key=lambda x: x[0])
        out[k] = ([x[0] for x in v], [x[1] for x in v])
    return out


def celdas_historia(idx, vol, b, dt, dias=DIAS_HISTORIA):
    """Celdas alertadas de noche en [dt - dias, dt), estrictamente antes de la pasada (se puede aplicar en NRT)."""
    ts, cs = idx.get((vol, b), ([], []))
    i0 = bisect.bisect_left(ts, dt - timedelta(days=dias))
    i1 = bisect.bisect_left(ts, dt)
    out = set()
    for c in cs[i0:i1]:
        out |= c
    return out


def con_historia(celda, hist, vecindad=VECINDAD):
    f, c = celda[0], celda[1]
    return any((f + df, c + dc) in hist for df in range(-vecindad, vecindad + 1) for dc in range(-vecindad, vecindad + 1))


def radiante(celdas):
    """La celda de mayor temperatura de brillo MIR; empate: la de menor (fila, col)."""
    return min(celdas, key=lambda c: (-c[2], c[0], c[1]))


def conserva(regla, rec, hist):
    """True si la regla deja publicar el record diurno. Sin celdas no se puede juzgar: se conserva (y cuenta en I1)."""
    cs = rec.get("celdas") or ()
    if not cs:
        return True
    if regla == "R1":
        return any(con_historia(c, hist) for c in cs)
    if regla == "R2":
        return con_historia(radiante(cs), hist)
    if regla == "R0":                     # referencia sin voto: el volcán alertó algo de noche en su grilla
        return bool(hist)
    if regla == "ninguna":
        return True
    raise ValueError(regla)


# ------------------------------------------------------------------------------------------------ etiquetas
def indexar_pasadas(pasadas):
    idx = collections.defaultdict(list)
    for p in pasadas:
        idx[(p["vol"], p["b"])].append(p)
    for v in idx.values():
        v.sort(key=lambda p: p["dt"])
    return idx


def pasada_de(idx, rec, tol_s=TOL_S):
    """La pasada de MIROVA más cercana a ±tol_s, mismo volcán y sensor; None si no hay."""
    lista = idx.get((rec["vol"], rec["b"]), [])
    mejor, dmin = None, None
    for p in lista:
        d = abs((p["dt"] - rec["dt"]).total_seconds())
        if d <= tol_s and (dmin is None or d < dmin):
            mejor, dmin = p, d
    return mejor


def en_caja(lat, lon, caja):
    if lat is None or lon is None:
        return False
    dlat = caja["buffer_km"] / 111.0
    dlon = caja["buffer_km"] / (111.0 * abs(math.cos(math.radians(caja["lat"]))))
    return abs(lat - caja["lat"]) <= dlat and abs(lon - caja["lon"]) <= dlon


def respaldo_swir(rec, caja, escenas, dias=DIAS_SWIR):
    """NHI respalda si su caja es usable (contiene el punto del volcán), contiene la posición publicada y alguna escena
    a ±dias de la fecha UTC de la pasada tiene alerta."""
    if not caja or not caja.get("usable") or not en_caja(rec.get("lat"), rec.get("lon"), caja):
        return False
    d0 = rec["dt"].date()
    for e in escenas or ():
        if e.get("alerta") is True and abs((date.fromisoformat(e["fecha"][:10]) - d0).days) <= dias:
            return True
    return False


def a_desmentible(rec, caja, escenas, dias=DIAS_SWIR):
    """Una A que SWIR podría haber desmentido: caja usable que contiene la posición publicada y alguna escena NHI con
    alerta no nula a ±dias. Sólo se informa (crítica 3)."""
    if not caja or not caja.get("usable") or not en_caja(rec.get("lat"), rec.get("lon"), caja):
        return False
    d0 = rec["dt"].date()
    return any(e.get("alerta") is not None and abs((date.fromisoformat(e["fecha"][:10]) - d0).days) <= dias
               for e in escenas or ())


def cumbre_alertada_cerca(pasadas_vol, dt, inner_km, horas=HORAS_MIROVA_VECINA):
    """La tabla de MIROVA alertó 1 MW o más a no más del radio interno, cualquier sensor del volcán, a ±horas."""
    return any(p["fuente"] == "CONS" and p["estado"] == "alerta" and (p["vrp_mw"] or 0.0) >= UMBRAL_MW
               and p["dist_km"] is not None and p["dist_km"] <= inner_km
               and abs((p["dt"] - dt).total_seconds()) <= horas * 3600 for p in pasadas_vol)


def etiquetar(rec, pasada, inner_km, caja, escenas, cumbre_cerca=False):
    """P, A, R, O o menor (§4 del pre-registro). `rec` es una publicación diurna; `cumbre_cerca` es
    `cumbre_alertada_cerca` para su volcán e instante."""
    if (pasada and pasada["estado"] == "alerta" and pasada["fuente"] == "CONS" and pasada["vrp_mw"] is not None
            and pasada["vrp_mw"] >= UMBRAL_MW and pasada["dist_km"] is not None and pasada["dist_km"] <= inner_km):
        return "P"
    if pasada is not None and pasada["estado"] not in ("rutina", "fp"):
        return "O"
    if float(rec.get("disp") or 0.0) < UMBRAL_MW:
        return "menor"
    if respaldo_swir(rec, caja, escenas) or (pasada is None and cumbre_cerca):
        return "R"
    return "A"


# ------------------------------------------------------------------------------------------------ criterio
def p_hiper(n_total, n_exitos, k, a):
    """P(X >= a), X hipergeométrica: k sacados al azar de n_total con n_exitos. El nulo es una regla que suprime al azar
    el mismo número de publicaciones del universo P, A, R y O."""
    if k <= 0 or a <= 0:
        return 1.0
    den = math.comb(n_total, k)
    return sum(math.comb(n_exitos, x) * math.comb(n_total - n_exitos, k - x)
               for x in range(a, min(k, n_exitos) + 1)) / den


UNIVERSO = ("P", "A", "R", "O")


def p_estratificado(etiquetas, conservas, estratos):
    """Informativo (crítica 2): el mismo nulo, con la supresión al azar dentro de cada estrato (volcán y grilla), el
    mismo número que la regla en cada uno. P(suma de X_s >= q_A), por convolución exacta de hipergeométricas."""
    por = collections.defaultdict(lambda: [0, 0, 0, 0])          # N, A, k, q_A
    for e, c, s in zip(etiquetas, conservas, estratos):
        if e in UNIVERSO:
            x = por[s]
            x[0] += 1
            x[1] += e == "A"
            x[2] += not c
            x[3] += e == "A" and not c
    dist = {0: 1.0}
    for n_s, a_s, k_s, _ in por.values():
        f = {x: math.comb(a_s, x) * math.comb(n_s - a_s, k_s - x) / math.comb(n_s, k_s)
             for x in range(max(0, k_s - (n_s - a_s)), min(k_s, a_s) + 1)}
        nueva = collections.defaultdict(float)
        for s0, p0 in dist.items():
            for x, px in f.items():
                nueva[s0 + x] += p0 * px
        dist = nueva
    q_a = sum(x[3] for x in por.values())
    return sum(p for s, p in dist.items() if s >= q_a) if q_a > 0 else 1.0


def evaluar_regla(etiquetas, conservas, alfa, estratos=None, desmentibles=None):
    """`etiquetas` y `conservas` alineadas (una por publicación diurna de la fase). Devuelve conteos, p y estado.
    `estratos` y `desmentibles` (alineados) sólo agregan lo informativo de la crítica (2 y 3)."""
    n = collections.Counter(etiquetas)
    q = collections.Counter(e for e, c in zip(etiquetas, conservas) if not c)
    universo = sum(n[x] for x in UNIVERSO)
    k = sum(q[x] for x in UNIVERSO)
    p = p_hiper(universo, n["A"], k, q["A"])
    motivos = []
    if QUITAR_A[1] * q["A"] < QUITAR_A[0] * n["A"]:
        motivos.append("quita %d de %d artefactos (hace falta 2/3)" % (q["A"], n["A"]))
    if q["P"] > MAX_P_PERDIDAS:
        motivos.append("pierde %d protegidas de cumbre" % q["P"])
    if MAX_R_PERDIDAS[1] * q["R"] > MAX_R_PERDIDAS[0] * n["R"]:
        motivos.append("pierde %d de %d con respaldo SWIR (máximo 1/3)" % (q["R"], n["R"]))
    if not p < alfa:
        motivos.append("no supera al azar con la misma supresión: p = %.4g, alfa %.3g" % (p, alfa))
    info = {}
    if estratos is not None:
        info["p_estratificado_volcan_grilla"] = p_estratificado(etiquetas, conservas, estratos)
    if desmentibles is not None:
        for nombre, val in (("A_desmentibles", True), ("A_no_desmentibles", False)):
            sel = [c for e, c, d in zip(etiquetas, conservas, desmentibles) if e == "A" and bool(d) == val]
            info[nombre] = {"n": len(sel), "quitadas": sum(1 for c in sel if not c)}
    return {"n": dict(n), "quitadas": dict(q), "universo": universo, "k": k, "p": p, "alfa": alfa,
            "estado": CUMPLE if not motivos else NO_CUMPLE, "motivos": motivos, "informativo": info}


def veredicto(etiquetas, conservas_por_regla, problemas_instrumento=(), estratos=None, desmentibles=None):
    """§5 y §7 del pre-registro: INVALIDO, SIN PODER, CUMPLE con R1, CUMPLE con una alternativa, o NO CUMPLE. Con
    INVALIDO no se calcula ni se devuelve ninguna métrica (crítica 5: arreglar el instrumento sin ver el resultado).
    Las reglas de `conservas_por_regla` que no están en ORDEN_REGLAS (R0) se informan sin voto."""
    if problemas_instrumento:
        return {"problemas_instrumento": list(problemas_instrumento), "veredicto": INVALIDO, "regla": None}
    n = collections.Counter(etiquetas)
    por_regla = {r: evaluar_regla(etiquetas, conservas_por_regla[r], ALFA_REGLA[r], estratos, desmentibles)
                 for r in ORDEN_REGLAS}
    sin_voto = {r: evaluar_regla(etiquetas, c, ALFA_REGLA["R1"], estratos, desmentibles)
                for r, c in conservas_por_regla.items() if r not in ORDEN_REGLAS}
    base = {"n": dict(n), "por_regla": por_regla, "sin_voto": sin_voto, "problemas_instrumento": []}
    if n["A"] < N_MIN_A or n["P"] < N_MIN_P:
        return dict(base, veredicto=SIN_PODER, regla=None)
    if por_regla["R1"]["estado"] == CUMPLE:
        return dict(base, veredicto=CUMPLE, regla="R1")
    ok = [r for r in ORDEN_REGLAS[1:] if por_regla[r]["estado"] == CUMPLE]
    if not ok:
        return dict(base, veredicto=NO_CUMPLE, regla=None)
    elegida = min(ok, key=lambda r: (-por_regla[r]["quitadas"].get("A", 0), por_regla[r]["quitadas"].get("R", 0),
                                     ORDEN_REGLAS.index(r)))
    return dict(base, veredicto=CUMPLE, regla=elegida)


# ------------------------------------------------------------------------------------------------ instrumento
def _dias(d0, d1):
    a, b = date.fromisoformat(d0), date.fromisoformat(d1)
    return [(a + timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]


def revisar_instrumento(pubs_dia, noches_hist, pasadas_dia_tabla, recs_dia, ventanas, acuerdo_noche, vols):
    """Compuertas del §6. `pubs_dia`: publicaciones diurnas de la fase; `noches_hist`: records nocturnos de la
    historia; `pasadas_dia_tabla`: pasadas diurnas VIIRS de la tabla de MIROVA en la fase; `recs_dia`: todos los records
    diurnos del brazo en la fase; `acuerdo_noche`: (iguales, comparables) entre noches del brazo y de producción."""
    prob = []
    sin = sum(1 for r in pubs_dia if not r.get("celdas"))
    if pubs_dia and sin > MAX_FRAC_SIN_CELDAS * len(pubs_dia):
        prob.append("I1: %d de %d publicaciones diurnas sin celdas" % (sin, len(pubs_dia)))
    dias_con = collections.defaultdict(set)
    for r in noches_hist:
        dias_con[(r["vol"], r["b"])].add(r["dt"].date().isoformat())
    for vol in vols:
        for b in SENSORES_VIIRS:
            for w in ventanas:
                inicio = (date.fromisoformat(w[1]) - timedelta(days=DIAS_HISTORIA)).isoformat()
                ds = _dias(inicio, w[2])
                tiene = sum(1 for d in ds if d in dias_con[(vol, b)])
                if tiene < MIN_FRAC_DIAS_HISTORIA * len(ds):
                    prob.append("I2: %s %s %s: historia nocturna en %d de %d días" % (vol, b, w[0], tiene, len(ds)))
    idx = collections.defaultdict(list)
    for r in recs_dia:
        idx[(r["vol"], r["b"])].append(r["dt"])
    faltan = sum(1 for p in pasadas_dia_tabla
                 if not any(abs((t - p["dt"]).total_seconds()) <= TOL_S for t in idx[(p["vol"], p["b"])]))
    if pasadas_dia_tabla and faltan > MAX_FRAC_MIROVA_SIN_RECORD * len(pasadas_dia_tabla):
        prob.append("I3: %d de %d pasadas diurnas de la tabla de MIROVA sin record del brazo" % (
            faltan, len(pasadas_dia_tabla)))
    iguales, comparables = acuerdo_noche
    if comparables and iguales < MIN_ACUERDO_NOCHE * comparables:
        prob.append("I4: noches del brazo y de producción con las mismas celdas en %d de %d" % (iguales, comparables))
    return prob


def acuerdo_noches(noches_brazo, noches_prod):
    """(iguales, comparables): records nocturnos del brazo con par en producción (mismo volcán, sensor e instante a
    ±TOL_S) y el mismo conjunto de celdas alertadas."""
    idx = collections.defaultdict(list)
    for r in noches_prod:
        idx[(r["vol"], r["sensor"])].append(r)
    iguales = comparables = 0
    for r in noches_brazo:
        par = [q for q in idx[(r["vol"], r["sensor"])] if abs((q["dt"] - r["dt"]).total_seconds()) <= TOL_S]
        if not par:
            continue
        comparables += 1
        a = {(c[0], c[1]) for c in r.get("celdas") or ()}
        b = {(c[0], c[1]) for c in par[0].get("celdas") or ()}
        iguales += a == b
    return iguales, comparables


def evaluar_fase(recs_brazo, noches_prod, pasadas, cajas, nhi, inner, ventanas, vols):
    """Arma etiquetas y supresiones por regla sobre las publicaciones diurnas de las ventanas, con la historia nocturna
    de producción. Devuelve (veredicto, detalle por publicación)."""
    hist_recs = [r for r in noches_prod if not r["es_dia"] and r["b"] in SENSORES_VIIRS]
    hidx = indexar_noches(hist_recs)
    pidx = indexar_pasadas(pasadas)
    pvol = collections.defaultdict(list)
    for p in pasadas:
        pvol[p["vol"]].append(p)
    dia = [r for r in recs_brazo if r["es_dia"] and r["b"] in SENSORES_VIIRS and r["vol"] in vols
           and en_ventanas(r["dt"].date().isoformat(), ventanas)]
    pubs = [r for r in dia if r["pub"]]
    etiquetas, conservas, detalle, estratos, desm = [], {r: [] for r in ORDEN_REGLAS + ("R0",)}, [], [], []
    for r in pubs:
        e = etiquetar(r, pasada_de(pidx, r), inner[r["vol"]], cajas.get(r["vol"]), nhi.get(r["vol"]),
                      cumbre_alertada_cerca(pvol[r["vol"]], r["dt"], inner[r["vol"]]))
        h = celdas_historia(hidx, r["vol"], r["b"], r["dt"])
        etiquetas.append(e)
        estratos.append((r["vol"], r["b"]))
        desm.append(e == "A" and a_desmentible(r, cajas.get(r["vol"]), nhi.get(r["vol"])))
        fila = {"vol": r["vol"], "b": r["b"], "dt": r["dt"].strftime("%Y-%m-%d %H:%M"), "disp": r.get("disp"),
                "etiqueta": e, "n_celdas": len(r.get("celdas") or ()), "desmentible": desm[-1]}
        for regla in ORDEN_REGLAS + ("R0",):
            c = conserva(regla, r, h)
            conservas[regla].append(c)
            fila[regla] = c
        detalle.append(fila)
    pas_tabla = [p for p in pasadas if p["fuente"] == "CONS" and p["es_dia"] and p["b"] in SENSORES_VIIRS
                 and p["vol"] in vols and en_ventanas(p["dt"].date().isoformat(), ventanas)]
    noches_brazo = [r for r in recs_brazo if not r["es_dia"] and r["b"] in SENSORES_VIIRS and r["vol"] in vols
                    and en_ventanas(r["dt"].date().isoformat(), ventanas)]
    prob = revisar_instrumento(pubs, hist_recs, pas_tabla, dia, ventanas, acuerdo_noches(noches_brazo, hist_recs), vols)
    return veredicto(etiquetas, conservas, prob, estratos, desm), detalle


# ------------------------------------------------------------------------------------------------ carga real
def _imports():
    for p in (str(ROOT), str(ROOT / "scripts"), str(ROOT / "experiments" / "_s163_diurno_k")):
        if p not in sys.path:
            sys.path.insert(0, p)
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    import banco_paridad as bp
    import evaluar_diurno_k as ek
    return bp, ek


def cargar_records(archivos, desde, hasta, con_predicado):
    """Records VIIRS de los JSON dados, con celdas, posición publicada y, si `con_predicado`, el predicado del tablero
    ejecutado con node (A97)."""
    bp, ek = _imports()
    inner = bp.inner_desde_html()
    recs, casos, vistos = [], [], set()
    for ruta in archivos:
        vol = Path(ruta).stem
        if vol not in inner:
            continue
        for r in json.loads(Path(ruta).read_text(encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor"))
            tt = r.get("datetime_utc", "")
            if b not in SENSORES_VIIRS or not (desde <= tt[:10] <= hasta):
                continue
            try:
                dt = datetime.strptime(tt, "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            k = (vol, r.get("sensor"), tt)
            if k in vistos:
                continue
            vistos.add(k)
            reg = r.get("regimen") or {}
            recs.append({"vol": vol, "b": b, "sensor": r.get("sensor"), "dt": dt, "es_dia": ek.es_dia_vol(vol, dt),
                         "celdas": [(px["fila"], px["col"], px.get("bt_k") or 0.0) for px in (r.get("anomaly_pixels") or [])
                                    if px.get("fila") is not None and px.get("col") is not None],
                         "lat": r.get("final_hotspot_lat"), "lon": r.get("final_hotspot_lon"),
                         "perfil": reg.get("perfil"), "sha": reg.get("codigo_sha"), "pub": False, "disp": 0.0})
            if con_predicado:
                slim = {kk: r.get(kk) for kk in bp.CAMPOS_JS if kk != "anomaly_pixels"}
                if r.get("f5_core_vrp_mw") is None:
                    slim["anomaly_pixels"] = [{kk: px.get(kk) for kk in ("lat", "lon", "vrp_mw", "bt_k")}
                                              for px in (r.get("anomaly_pixels") or [])]
                casos.append([slim, inner[vol]])
    if con_predicado and casos:
        for rr, p in zip(recs, bp.correr_node(casos)):
            rr["disp"], rr["pub"] = p[3], bool(p[4])
    return recs, inner


def cargar_pasadas(ref_dir):
    """Pasadas de MIROVA de los tres sensores (canal unión, clase_mirova.resumir_pasadas) desde una carpeta con los 4
    CSV. MODIS sólo sirve para `cumbre_alertada_cerca`: el pareo de una publicación es con su mismo sensor."""
    bp, ek = _imports()
    import clase_mirova as cm
    import sustrato_k as sk
    out = []
    for p in cm.resumir_pasadas(sk.cargar_ref(ref_dir), canal="union"):
        if p.sensor_bucket not in SENSORES_VIIRS + ("MODIS",) or p.volcano not in bp.VOLS:
            continue
        dt = p.instante.replace(tzinfo=None)
        out.append({"vol": p.volcano, "b": p.sensor_bucket, "dt": dt, "estado": p.estado, "vrp_mw": p.vrp_mw,
                    "dist_km": p.dist_km, "fuente": p.fuente, "es_dia": ek.es_dia_vol(p.volcano, dt)})
    return out


def cargar_cajas():
    """nhi_cajas.json (extraer_nhi_cajas.py) con `usable`: el punto de volcanoes.yaml cae dentro de la caja de NHI."""
    import yaml
    d = json.loads((AQUI / "nhi_cajas.json").read_text(encoding="utf-8"))
    vy = {v["name"]: v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    out = {}
    for vol, c in d["volcanes"].items():
        if c.get("en_nhi"):
            out[vol] = dict(c, usable=en_caja(vy[vol]["lat"], vy[vol]["lon"], c))
    return out


def cargar_nhi(nhi_dir, cajas):
    out = {}
    for vol, c in cajas.items():
        ruta = Path(nhi_dir) / c["nombre_nhi"] / "nhi_timeseries.json"
        if ruta.exists():
            out[vol] = [e for e in json.loads(ruta.read_text(encoding="utf-8")) if e.get("fecha")]
    return out


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Evaluador del control diurno de VIIRS (PREREGISTRO.md)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("evaluar")
    e.add_argument("--fase", choices=("desarrollo", "veredicto"), required=True)
    e.add_argument("--raiz", action="append", required=True, help="carpeta con <brazo>/<Volcan>.json, repetible")
    e.add_argument("--ref", required=True, help="carpeta con los 4 CSV de MIROVA (sustrato_k.ARCHIVOS_REF)")
    e.add_argument("--nhi-dir", required=True, help="carpeta con <Carpeta NHI>/nhi_timeseries.json")
    e.add_argument("--produccion", default=str(ROOT / "data" / "mirova_equivalent"))
    e.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.fase == "veredicto" and not puede_medir_veredicto(date.today().isoformat()):
        print("El veredicto se mide una sola vez, no antes de %s (PREREGISTRO §3)." % FECHA_MIN_VEREDICTO)
        return 2
    ventanas = VENTANAS_DESARROLLO if a.fase == "desarrollo" else VENTANAS_VEREDICTO
    desde = (date.fromisoformat(ventanas[0][1]) - timedelta(days=DIAS_HISTORIA)).isoformat()
    hasta = ventanas[-1][2]
    archivos = [p for raiz in a.raiz for p in sorted((Path(raiz) / BRAZO).glob("*.json"))]
    recs, inner = cargar_records(archivos, desde, hasta, con_predicado=True)
    prod, _ = cargar_records(sorted(Path(a.produccion).glob("*.json")), desde, hasta, con_predicado=False)
    vols = sorted({r["vol"] for r in recs})
    problemas_brazo = sorted({"%s|%s" % (r["perfil"], r["sha"]) for r in recs})
    cajas = cargar_cajas()
    v, detalle = evaluar_fase(recs, prod, cargar_pasadas(a.ref), cajas, cargar_nhi(a.nhi_dir, cajas), inner,
                              ventanas, vols)
    if len(problemas_brazo) != 1 or not problemas_brazo[0].startswith(BRAZO + "|"):
        v = {"problemas_instrumento": v["problemas_instrumento"] + [
            "I5: perfil y sha del brazo no son uno solo: %s" % problemas_brazo], "veredicto": INVALIDO, "regla": None}
    commit_nhi = Path(a.nhi_dir) / "COMMIT.txt"
    v.update({"fase": a.fase, "ventanas": ventanas, "volcanes": vols, "perfil_sha": problemas_brazo,
              "cajas_nhi_usables": sorted(k for k, c in cajas.items() if c["usable"]),
              "commit_nhi": commit_nhi.read_text(encoding="utf-8").strip() if commit_nhi.exists() else None,
              "produccion": a.produccion})
    if v["veredicto"] == INVALIDO:
        print("VEREDICTO: INVALIDO %s (sin métricas: PREREGISTRO §6)" % v["problemas_instrumento"])
        Path(a.out).write_text(json.dumps({"veredicto": v}, ensure_ascii=False, indent=1, default=str),
                               encoding="utf-8")
        return 0
    print("FASE %s%s" % (a.fase.upper(), " (NO DECIDE)" if a.fase == "desarrollo" else ""))
    print("días de la fase: %d (%s)" % (sum(len(_dias(w[1], w[2])) for w in ventanas), ", ".join(
        "%s %s a %s" % w for w in ventanas)))
    print("etiquetas: %s" % v["n"])
    for regla, x in list(v["por_regla"].items()) + [(r + " (sin voto)", x) for r, x in v["sin_voto"].items()]:
        print("  %s: quitadas %s, p = %.4g (alfa %.3g), %s %s" % (regla, x["quitadas"], x["p"], x["alfa"],
                                                                     x["estado"], x["motivos"]))
        print("      informativo: %s" % x["informativo"])
    for w in ventanas:
        sel = [d for d in detalle if w[1] <= d["dt"][:10] <= w[2]]
        print("  %s (informativo): %s; R1 quita %s" % (w[0], dict(collections.Counter(d["etiqueta"] for d in sel)),
                                                       dict(collections.Counter(d["etiqueta"] for d in sel
                                                                                if not d["R1"]))))
    print("instrumento: sin problemas")
    print("VEREDICTO: %s %s" % (v["veredicto"], v["regla"] or ""))
    Path(a.out).write_text(json.dumps({"veredicto": v, "detalle": detalle}, ensure_ascii=False, indent=1, default=str),
                           encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
