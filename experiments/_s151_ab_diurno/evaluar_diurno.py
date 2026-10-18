# -*- coding: utf-8 -*-
"""Evaluador del A/B diurno de VIIRS (D-10, issue #813): implementa experiments/_s151_ab_diurno/PREREGISTRO.md
§4 a §6 TAL CUAL. Si una regla cambia, cambia acá y allá en el mismo commit.

EL FENÓMENO. De día el canal de infrarrojo medio suma a la emisión térmica la luz solar reflejada, y una nube o
un salar levantan píxeles sin nada caliente debajo. MIROVA mira de día con umbrales altos y casi no alerta (13 de
2.511 pasadas VIIRS 375 diurnas de su tabla). La pregunta del A/B: con la rama diurna encendida, ¿la réplica
recupera las alertas diurnas protegidas de MIROVA siendo de día tan callada como MIROVA?

QUÉ REUSA, SIN REIMPLEMENTAR.
  * Las poblaciones (positivos protegidos usables bajo A119, negativos diurnos limpios, pasadas diurnas de la
    tabla, parsimonia de MIROVA) salen de `sustrato.universo`, la MISMA función que contó el sustrato del
    pre-registro. El evaluador exige además que la referencia que lee reproduzca `sustrato.json` (control de
    referencia: si la base de MIROVA cambió desde el pre-registro, no se decide).
  * La referencia se indexa con `banco_paridad.indexar_referencia`, con la rama diurna ENCENDIDA en
    `pipeline.profile` mientras se indexa (si no, `es_pasada_diurna_descartada` tira justo las pasadas VIIRS
    diurnas que se quieren medir: PREREGISTRO §7.3, A118). El evaluador comprueba las dos caras: con el flag
    encendido el índice ve todas las pasadas del universo; con el flag apagado ve cero filas VIIRS diurnas.
  * «Publicamos» es el predicado del dashboard ejecutado con node (`banco_paridad.correr_node`, A97), nunca uno
    reconstruido a mano. Día y noche de cada record por elevación solar explícita (`pipeline.diurno.
    pasada_es_diurna`, la regla de store), nunca por una función que siga al flag.
  * La lectura de FLAGS_BRAZO es la de `experiments/_s151_prereg_fk_11/evaluar_fk.py::flags_leidos`.

QUÉ DECIDE (§6): G1 (discrimina: M1 − q_neg sobre el percentil 95 de un nulo barajado dentro de volcán ×
sensor, en W2 a W6 y en W3 a W6), G2 (binomial de una cola contra la parsimonia diurna de MIROVA, por sensor,
W2 a W6), G3 (noches idénticas, cada par clasificado con unir_intentos.comparar más el predicado del tablero:
desviación D2 del pre-registro). W1 se informa aparte (A119). La regla D-9 de alertas mínimas decide con «original»;
si `clase_mirova.aplicar_regla_minimas` existe (PR #820), SN y SE se INFORMAN en una sección aparte.

EL NULO BARAJADO, por qué es exacto con la hipergeométrica. Barajar las etiquetas positivo/negativo dentro de un
estrato con n pasadas, P positivas y K publicadas sólo cambia cuántas publicadas caen en positivas, X, y X sigue
una hipergeométrica (n, K, P). M1 y q_neg dependen de los X de cada estrato, así que muestrear X es el mismo
barajado que mover etiquetas, sin el costo de 10.000 permutaciones de miles de pasadas.

Uso:
  python evaluar_diurno.py --raiz <salidas/run_W1> --raiz <salidas/run_W2> ... --out resultado.json
  (cada raíz trae <brazo>/<volcan>.json y logs/<brazo>_<volcan>.log; --logs por defecto es <raiz>/logs)
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (str(RAIZ), str(RAIZ / "scripts"), str(AQUI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

import banco_paridad as bp  # noqa: E402
import clase_mirova as cm  # noqa: E402
import sustrato as S  # noqa: E402
import unir_intentos as U  # noqa: E402  (G3: comparar y el predicado del tablero, desviación D2)
from pipeline.diurno import pasada_es_diurna  # noqa: E402
from referencia_mirova_unificada import (HISTORICO_RECUPERADAS, RESPALDO_20260408,  # noqa: E402
                                         SNAP_CONS, SNAP_OCR, cargar_referencia_unificada)

# ---------------------------------------------------------------- lo que el pre-registro fija
BRAZOS = {"control": "_s151_ab_diurno_control", "diurno": "_s151_ab_diurno_on"}       # §2
DECLARADO = {"control": {"ENABLE_DAYTIME_VIIRS": False, "ENABLE_DAYTIME_MODIS": False},
             "diurno": {"ENABLE_DAYTIME_VIIRS": True, "ENABLE_DAYTIME_MODIS": False}}
# S154 (tarea 1.32): el A/B se repite sobre K. Con --base k el cableado exige además, en los dos brazos, los tres flags
# de K leídos desde el log (si un brazo corrió con el Test 1 encendido, el A/B no sería sobre K y no se decide).
FLAGS_BASE = {"c0": {}, "k": {"ENABLE_TEST1_PATH": False, "ENABLE_TESTS_23_PROSE_BRANCH": True,
                              "ENABLE_MODIS_B22_PRIMARY": True}}


# S154, adenda K sellada por Nicolás (experiments/_s151_ab_diurno/ADENDA_K.md): con --base k, G1 decide con la cola
# exacta del nulo (§3.1) y «cumple sin W2, falla con W2» pasa a DECIDE NICOLAS CON M4 (§3.2). Con c0 rige el
# pre-registro original tal cual, para que la corrida sobre C0 siga siendo reproducible.
REGLA = {"cola_exacta": False, "w2_decide_nicolas": False}


def configurar_brazos(control, diurno, base="c0"):
    """Nombres de los brazos y flags de base que el cableado exige (--brazos, --base). Por defecto, los de W2 a W6."""
    BRAZOS.update({"control": control, "diurno": diurno})
    for n, palanca in (("control", False), ("diurno", True)):
        DECLARADO[n] = {"ENABLE_DAYTIME_VIIRS": palanca, "ENABLE_DAYTIME_MODIS": False, **FLAGS_BASE[base]}
    REGLA.update(cola_exacta=(base == "k"), w2_decide_nicolas=(base == "k"))


def resolver_base(brazos, base):
    """H2b (adenda K §4): con brazos que no son los de W2 a W6 sobre C0, --base tiene que venir explícito; si no, el
    evaluador se niega (antes, olvidar --base k apagaba en silencio la exigencia de K)."""
    if base is not None:
        return base
    if brazos == "%s,%s" % ("_s151_ab_diurno_control", "_s151_ab_diurno_on"):
        return "c0"
    raise SystemExit("--brazos %s sin --base: decir explícitamente el detector de base (c0 o k), adenda K §4 H2b" % brazos)


def cableado_records(raices, sha):
    """H2a (adenda K §4): el cableado por log no ve un job repetido desde otra referencia (unir_ventana no copia logs).
    Con base K se exige sobre los RECORDS de los dos brazos: ninguno con el Test 1 (triggered_test1 o
    final_hotspot_source = test1_roi; en producción bajo K son 0 de 3.548) y todos con regimen.codigo_sha = el commit
    del tag de despacho."""
    prob = []
    for nombre in ("control", "diurno"):
        for raiz in raices:
            for p in sorted((Path(raiz) / BRAZOS[nombre]).glob("*.json")):
                recs = json.loads(p.read_text(encoding="utf-8")).get("records", [])
                t1 = sum(1 for r in recs if r.get("triggered_test1") is True or r.get("final_hotspot_source") == "test1_roi")
                otro = sum(1 for r in recs if ((r.get("regimen") or {}).get("codigo_sha")) != sha)
                if t1:
                    prob.append("%s/%s: %d records con el Test 1" % (BRAZOS[nombre], p.stem, t1))
                if otro:
                    prob.append("%s/%s: %d records con codigo_sha distinto del tag (o sin marca)" % (BRAZOS[nombre], p.stem, otro))
    return prob
VIIRS = ("VIIRS375", "VIIRS750")
VENTANAS = [w[0] for w in S.VENTANAS]                                                  # §3
VENTANA = {w[0]: {"desde": w[1], "hasta": w[2], "vols": w[3] or list(bp.VOLS)} for w in S.VENTANAS}
DECIDEN = ("W2", "W3", "W4", "W5", "W6")       # §6 G1 y G2: W1 se informa aparte (A119)
SIN_W2 = ("W3", "W4", "W5", "W6")              # §6 G1: el veredicto tiene que sostenerse sin W2 (sólo OCR)
P_MIROVA = {"VIIRS375": (13, 2511), "VIIRS750": (2, 2483)}   # §3 y §6 G2 (sustrato_salida.txt, W2 a W6)
POSITIVOS_PREREGISTRO = 37                     # §3
N_BARAJADOS = 10000                            # §5.5
PERCENTIL_NULO = 95                            # §5.5
ALFA_G2 = 0.05                                 # §6 G2
MAX_NO_PROCESADAS_POS = 0.10                   # §5.4: más de 10 % de positivos no procesados -> repetir
SEMILLA = 0
# Campos que cambian entre dos jobs sin que cambie la medición (§5.2). `first_processed_utc` NO está en la lista
# del pre-registro: es la hora en que store guardó el record por primera vez y difiere siempre entre dos jobs.
# Se excluye y se deja como PREGUNTA para el verificador (PREREGISTRO §9).
VOLATILES = ("updated", "processed_utc", "regimen", "first_processed_utc")
# Informativos, no deciden (anotados en el pre-registro):
BANDA_SATURACION = 0.80     # A114: con el Test 1 encendido la publicación en negativos limpios es 80 a 92 %
UMBRAL_AUDITORIA = 0.30     # regla de skills del proyecto: mejora de más de 30 % exige auditoría independiente
N_BRAZOS_AZAR = 1000        # control del nulo: brazos que publican al azar dentro de cada estrato
TIPO_MINIMA_SE = S.TIPO_MINIMA_SE


# ---------------------------------------------------------------- utilidades
def sha_lf(p):
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def a_dt(t):
    return datetime.strptime(t[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def ventana_de(clave_):
    vol, _, t = clave_
    for w in VENTANAS:
        c = VENTANA[w]
        if c["desde"] <= t[:10] <= c["hasta"] and vol in c["vols"]:
            return w
    return None


@contextlib.contextmanager
def flag_viirs(valor):
    """Fija la rama diurna en pipeline.profile mientras dura el bloque. `es_pasada_diurna_descartada` lee el flag
    VIVO (pipeline.diurno.flag_viirs_diurno), así que indexar_referencia ve o no ve las pasadas diurnas según
    este valor. Se restaura siempre."""
    import pipeline.profile as P
    viejo = P.ENABLE_DAYTIME_VIIRS
    P.ENABLE_DAYTIME_VIIRS = valor
    try:
        yield
    finally:
        P.ENABLE_DAYTIME_VIIRS = viejo


def tasa(a, n):
    return a / n if n else None


def pct(x):
    return "  -  " if x is None else "%5.1f %%" % (100 * x)


# ---------------------------------------------------------------- referencia
_CACHE_FILAS = {}


def cargar_filas(a):
    """Filas normalizadas de la referencia (en memoria por rutas: la autoprueba evalúa muchos casos)."""
    coords = bp._coords_por_volcan()
    clave_ = (a.cons, a.ocr, a.respaldo, a.historico)
    if clave_ not in _CACHE_FILAS:
        filas = cargar_referencia_unificada(Path(a.cons), Path(a.ocr),
                                            respaldo_path=Path(a.respaldo) if a.respaldo else None,
                                            historico_path=Path(a.historico) if a.historico else None)
        _CACHE_FILAS[clave_] = [f for f in filas if f["volcano"] in coords]
    return [dict(f) for f in _CACHE_FILAS[clave_]], coords


def regla_disponible():
    return hasattr(cm, "aplicar_regla_minimas")


def aplicar_regla(filas, modo):
    if modo == "original":
        return filas
    if not regla_disponible():
        raise RuntimeError("regla_minimas no existe en este árbol (PR #820 sin mergear)")
    return cm.aplicar_regla_minimas(filas, modo).filas


def universo_por_ventana(U):
    """Por ventana: claves de positivos, negativos diurnos limpios y pasadas diurnas de la tabla, y las de la tabla
    con alerta (tabla u OCR a 120 s, la vara de G2)."""
    out = {w: {"pos": set(), "neg": set(), "tabla": set(), "alerta": set()} for w in VENTANAS}
    for nombre, conj in (("pos", U["pos"]), ("neg", U["neg"]), ("tabla", U["tabla"]),
                         ("alerta", U["con_alerta_cualquiera"])):
        for k in conj:
            w = ventana_de(k)
            if w:
                out[w][nombre].add(k)
    return out


def control_referencia(UW, ruta_json):
    """La referencia que se lee tiene que ser la del pre-registro: mismos positivos, negativos, pasadas y alertas
    por ventana y sensor que sustrato.json, y los 37 positivos y la parsimonia de §3."""
    esperado = {w["nombre"]: w for w in json.loads(Path(ruta_json).read_text(encoding="utf-8"))["ventanas"]}
    dif = []
    for w in VENTANAS:
        e, u = esperado[w], UW[w]
        pos = sorted("|".join(k) for k in u["pos"])
        if pos != e["positivos"]:
            dif.append("%s positivos %d contra %d del pre-registro" % (w, len(pos), len(e["positivos"])))
        for s in VIIRS:
            for etq, mio, suyo in (("negativos", sum(1 for k in u["neg"] if k[1] == s), e["n_negativos_limpios"][s]),
                                   ("pasadas de tabla", sum(1 for k in u["tabla"] if k[1] == s), e["pasadas_tabla_por_sensor"][s]),
                                   ("con alerta", sum(1 for k in u["alerta"] if k[1] == s), e["con_alerta_tabla_u_ocr_por_sensor"][s])):
                if mio != suyo:
                    dif.append("%s %s %s: %d contra %d" % (w, s, etq, mio, suyo))
            # Identidad, no sólo tamaño (verificador del PR #822, hueco 4): mismo conteo con otras pasadas
            # también es otra referencia.
            hu = e.get("huellas", {}).get(s)
            if hu is None:
                dif.append("%s %s: sustrato.json sin huellas (anterior al PR #822), no se puede comparar identidad" % (w, s))
                continue
            for etq, conj in (("neg", u["neg"]), ("tabla", u["tabla"]), ("alerta", u["alerta"])):
                if S.huella(k for k in conj if k[1] == s) != hu[etq]:
                    dif.append("%s %s: las pasadas «%s» no son las del pre-registro (huella distinta)" % (w, s, etq))
    tot_pos = sum(len(UW[w]["pos"]) for w in VENTANAS)
    if tot_pos != POSITIVOS_PREREGISTRO:
        dif.append("positivos totales %d contra %d" % (tot_pos, POSITIVOS_PREREGISTRO))
    for s, (a_, n_) in P_MIROVA.items():
        mio = (sum(1 for w in DECIDEN for k in UW[w]["alerta"] if k[1] == s), sum(1 for w in DECIDEN for k in UW[w]["tabla"] if k[1] == s))
        if mio != (a_, n_):
            dif.append("p_MIROVA %s %d/%d contra %d/%d" % (s, mio[0], mio[1], a_, n_))
    return dif


def control_indexado(filas, coords, UW):
    """A118. Con el flag encendido, indexar_referencia tiene que ver cada pasada del universo; con el flag apagado,
    cero filas VIIRS diurnas. Devuelve (por_vb con el flag encendido por ventana, problemas, texto)."""
    por_vb_on, prob, txt = {}, [], []
    for w in VENTANAS:
        c = VENTANA[w]
        with flag_viirs(True):
            pv_on, _, _, _ = bp.indexar_referencia(filas, coords, (c["desde"], c["hasta"]))
        with flag_viirs(False):
            pv_off, _, _, _ = bp.indexar_referencia(filas, coords, (c["desde"], c["hasta"]))
        por_vb_on[w] = pv_on
        ciegas = [k for k in UW[w]["pos"] | UW[w]["tabla"] if not bp.parear(pv_on.get((k[0], k[1]), []), a_dt(k[2]))]
        dia_off = sum(1 for (vol, b), lista in pv_off.items() if b in VIIRS and vol in c["vols"]
                      for dt, f in lista if pasada_es_diurna(f["fecha_utc"][:16], *coords[vol]))
        n_univ = len(UW[w]["pos"] | UW[w]["tabla"])
        txt.append("   %s: flag encendido, el índice ve %d de %d pasadas del universo | flag apagado, filas VIIRS diurnas indexadas: %d"
                   % (w, n_univ - len(ciegas), n_univ, dia_off))
        if ciegas:
            prob.append("%s: indexar_referencia no ve %d pasadas del universo con el flag encendido (%s)" % (w, len(ciegas), sorted(ciegas)[:3]))
        if dia_off:
            prob.append("%s: con el flag apagado indexar_referencia deja %d filas VIIRS diurnas (la trampa A118 no es la que se cree)" % (w, dia_off))
    return por_vb_on, prob, txt


# ---------------------------------------------------------------- brazos
def cargar_brazo(raices, nombre, coords, inner):
    """Todos los records del brazo (día y noche), unidos sobre las raíces, con el predicado del tablero por node.
    Si una pasada aparece en dos raíces gana la ÚLTIMA: la raíz de una repetición por cobertura (§5.4) se pasa
    después de la original."""
    por_clave, dup = {}, 0
    for raiz in raices:
        for vol in bp.VOLS:
            p = Path(raiz) / BRAZOS[nombre] / (vol + ".json")
            if not p.exists():
                continue
            for r in json.loads(p.read_text(encoding="utf-8")).get("records", []):
                b = bp.bucket(r.get("sensor"))
                t = r.get("datetime_utc") or ""
                if b is None or len(t) < 16:
                    continue
                k = (vol, r.get("sensor"), t[:16])
                dup += k in por_clave
                por_clave[k] = (vol, b, t, r)
    recs, casos = [], []
    for vol, b, t, r in por_clave.values():
        dt = a_dt(t)
        recs.append({"vol": vol, "b": b, "dt": dt, "t": t[:16], "noche": dt.strftime("%Y-%m-%d"),
                     "dia": pasada_es_diurna(t[:16], *coords[vol]), "sensor": r.get("sensor"),
                     "diag_dia": bool(r.get("diag_umbrales_diurnos")), "raw": r})
        slim = {k_: r.get(k_) for k_ in bp.CAMPOS_JS if k_ != "anomaly_pixels"}
        if r.get("f5_core_vrp_mw") is None:
            slim["anomaly_pixels"] = [{k_: q.get(k_) for k_ in ("lat", "lon", "vrp_mw", "bt_k")}
                                      for q in (r.get("anomaly_pixels") or [])]
        casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos) if casos else []
    for rec, p in zip(recs, pred):
        rec["disp"], rec["pub"] = p[3], int(p[4])
    return recs, dup


def indice(recs):
    out = collections.defaultdict(list)
    for r in recs:
        out[(r["vol"], r["b"])].append((r["dt"], r))
    for v in out.values():
        v.sort(key=lambda x: x[0])
    return out


def emparejar(idx, k):
    """El record del brazo a 120 s o menos de la pasada de referencia (el más cercano), o None."""
    t = a_dt(k[2])
    cand = bp.parear(idx.get((k[0], k[1]), []), t)
    return min(cand, key=lambda r: abs((r["dt"] - t).total_seconds())) if cand else None


_RE_GRANULO = re.compile(r"A(\d{4})(\d{3})\.(\d{2})(\d{2})")


def motivos_log(logs, nombre, vols):
    """Por (vol, minuto): lo que el log dice de un gránulo que no llegó a record (SKIP daytime, ERROR processing,
    No geolocation match). Sólo diagnostica las no procesadas; la clase la decide la presencia del record."""
    out = {}
    for d in logs:
        for vol in vols:
            p = Path(d) / ("%s_%s.log" % (BRAZOS[nombre], vol))
            if not p.exists():
                continue
            for linea in p.read_text(encoding="utf-8", errors="replace").splitlines():
                for etq in ("SKIP daytime", "ERROR processing", "No geolocation match"):
                    if etq in linea:
                        m = _RE_GRANULO.search(linea)
                        if m:
                            y, j, hh, mm = (int(x) for x in m.groups())
                            dt = datetime(y, 1, 1, hh, mm, tzinfo=timezone.utc) + timedelta(days=j - 1)
                            out[(vol, dt.strftime("%Y-%m-%d %H:%M"))] = etq
    return out


def flags_leidos(logs, nombre, vol):
    out = []
    for d in logs:
        p = Path(d) / ("%s_%s.log" % (BRAZOS[nombre], vol))
        fl = None
        if p.exists():
            for linea in p.read_text(encoding="utf-8", errors="replace").splitlines():
                if linea.startswith("FLAGS_BRAZO "):
                    fl = json.loads(linea[len("FLAGS_BRAZO "):])
                    break
        out.append((Path(d).as_posix(), fl))
    return out


def cableado(raices, logs, nombre):
    """Cada job tiene que probar desde su log qué flags leyó (A89). Además, en el brazo diurno ningún gránulo VIIRS
    puede salir con «SKIP daytime»: sería una compuerta que el flag no abrió (A118, el caso S92)."""
    prob = []
    for raiz, d in zip(raices, logs):
        for vol in bp.VOLS:
            if not (Path(raiz) / BRAZOS[nombre] / (vol + ".json")).exists():
                continue
            (_, fl), = flags_leidos([d], nombre, vol)
            donde = "%s (%s)" % (vol, Path(d).as_posix())
            if fl is None:
                prob.append("%s: sin línea FLAGS_BRAZO" % donde)
                continue
            if fl.get("PROFILE_NAME") != BRAZOS[nombre] or fl.get("DATA_SUBDIR") != BRAZOS[nombre]:
                prob.append("%s: perfil o directorio %s/%s" % (donde, fl.get("PROFILE_NAME"), fl.get("DATA_SUBDIR")))
            for c, v in DECLARADO[nombre].items():
                if fl.get(c) is not v:
                    prob.append("%s: %s=%s, declarado %s" % (donde, c, fl.get(c), v))
            if nombre == "diurno":
                # Las dos huellas de una compuerta cerrada que el log deja: el salto del gránulo en
                # run_pipeline («SKIP daytime») y el filtro previo a la descarga de fetch («VIIRS_x: kept
                # N of M granules (night filter)»). Con el flag encendido ninguna puede salir para VIIRS.
                p = Path(d) / ("%s_%s.log" % (BRAZOS[nombre], vol))
                for linea in p.read_text(encoding="utf-8", errors="replace").splitlines():
                    if (("SKIP daytime" in linea and re.search(r"V(NP|J1|J2)0[23](IMG|MOD)", linea))
                            or re.search(r"VIIRS_\w+: kept \d+ of \d+ granules \(night filter\)", linea)):
                        prob.append("%s: compuerta diurna cerrada para VIIRS: %s" % (donde, linea.strip()[:90]))
                        break
    return prob


def flags_iguales(raices, logs):
    """Fuera de la palanca, los dos brazos tienen que haber leído lo mismo (producción)."""
    prob = []
    for raiz, d in zip(raices, logs):
        for vol in bp.VOLS:
            (_, fc), = flags_leidos([d], "control", vol)
            (_, fd), = flags_leidos([d], "diurno", vol)
            if fc is None or fd is None:
                continue
            dif = sorted(k for k in set(fc) | set(fd)
                         if k not in ("PROFILE_NAME", "DATA_SUBDIR", "ENABLE_DAYTIME_VIIRS") and fc.get(k) != fd.get(k))
            if dif:
                prob.append("%s: los brazos leyeron distinto %s" % (vol, dif))
    return prob


# ---------------------------------------------------------------- nulos
# Tolerancia de G3 (vuelta 70 del loop, 2026-10-16; desviación registrada en PREREGISTRO.md). W1 real (run
# 38723828037) dio FALLA con diag_mu_deti (179 noches) y diag_sd_deti (170) distintos, y nada más: ni hojas anidadas
# ni el dNTI del mismo pool. Mecanismo reproducido por el verificador limpio (verif_g3): np.polyfit pasa por LAPACK
# de OpenBLAS, que elige el kernel por CPU, y cambia el último bit de la regresión del ETI entre runners. MODIS
# también difiere y no lee el flag, así que el flag no es la causa. Comparar floats con != mide la máquina (S142).
# La diferencia relativa a mu llega a 1,4e-11 porque mu es casi cero (no "1e-16", cifra que estaba mal); contra la
# escala natural |dmu|/sigma <= 5,4e-14. Por eso la tolerancia lleva un piso ABSOLUTO de 1e-14 (el umbral físico
# más fino del dETI, C1, es 3e-3) además de la relativa de 1e-9. Los enteros se comparan exactos.
# La autoprueba fija los dos lados: casos 22 (CUMPLE) y 22b a 22g (FALLA), uno por cada mutación que sobrevivía.
G3_REL_TOL, G3_ABS_TOL = 1e-9, 1e-14
# Desde la desviación D2 (2026-10-17) la comparación la hace `unir_intentos.comparar`, que usa SU tolerancia y
# excluye SU lista de campos de proceso. Las dos tienen que ser las de este archivo: si alguien cambia una sola, el
# evaluador deja de decir lo que el pre-registro anota, y eso se ve al importar, no en un veredicto.
assert (G3_REL_TOL, G3_ABS_TOL) == (U.REL_TOL, U.ABS_TOL), "G3 y unir_intentos con tolerancias distintas"
assert set(VOLATILES) == U.PROCESO, "G3 y unir_intentos excluyen campos de proceso distintos"

# G3 por par nocturno control/diurno (desviación D2 del pre-registro, 2026-10-17; regla mínima del verificador del
# PR #843, VERIFICADOR_843.md §3). Antes: record crudo campo a campo con las listas de píxeles por POSICIÓN. Eso
# fallaba por dos causas que no son del experimento: (1) los brazos corren en runners distintos y el recorte top-100
# de `np.argsort(-per_pixel_vrp_mw)` de process_modis.py:1085-1099 desempata distinto (orden, conjunto de la lista y
# a veces el hotspot de escena, con el rescate por cúmulo de store.py:390-422 detrás); (2) con ventanas unidas, el
# veredicto dependía del orden de los intentos (W2a Copahue 2026-06-18 07:30: 9 campos con el orden (2,1), ninguno
# con (1,2)). Ahora cada par se clasifica con `unir_intentos.comparar` (la MISMA regla que decide si dos intentos
# del mismo código dicen lo mismo) y los de `borde` y `hotspot_escena` pasan además por el predicado del tablero con
# node (`unir_intentos._predicado`): si el tablero da distinto, el par es `distinto`. `igual` y `tolerancia` son lo
# que el G3 ya admitía; `orden`, `borde` y `hotspot_escena` se admiten y se INFORMAN aparte, par por par.
# Cualquier par fuera de G3_ADMITIDAS hace FALLA.
G3_ADMITIDAS = ("igual", "tolerancia", "orden", "borde", "hotspot_escena")
# Las categorías de unir_intentos.comparar, todas, aparte de cuáles se admiten (una mutación de G3_ADMITIDAS
# tiene que cambiar el veredicto, no romper el conteo).
G3_CATEGORIAS = ("igual", "tolerancia", "orden", "borde", "hotspot_escena", "distinto")


def noches_identicas(rc, rd, predicado=None):
    """Nulo 2 y 3: cada par nocturno (vol, sensor, minuto) de los dos brazos, clasificado con unir_intentos.comparar
    (sin VOLATILES) y, si es `borde` o `hotspot_escena`, con el predicado del tablero. Devuelve la cobertura
    (faltan/sobran, versión de producto o gránulo distintos, A108), el conteo por categoría, los pares admitidos
    de orden/borde/hotspot_escena (para informarlos) y los campos de los pares distintos.
    `predicado(pares, volcan)` devuelve los índices de los pares en que el tablero difiere (por defecto el de
    unir_intentos, con node); se puede inyectar para probar que el paso importa."""
    predicado = predicado or U._predicado
    nc = {(r["vol"], r["sensor"], r["t"]): r["raw"] for r in rc if not r["dia"]}
    nd = {(r["vol"], r["sensor"], r["t"]): r["raw"] for r in rd if not r["dia"]}
    faltan, sobran = sorted(set(nc) - set(nd)), sorted(set(nd) - set(nc))
    campos, version, ejemplos = collections.Counter(), [], []
    estados = {e: 0 for e in G3_CATEGORIAS}
    admitidos = {e: [] for e in ("orden", "borde", "hotspot_escena")}
    a_probar = collections.defaultdict(list)          # vol -> [(clave, control, diurno, estado, detalle)]
    sin_predicado = []                                 # pares que el predicado del tablero no pudo juzgar

    def anotar_distinto(k, det):
        estados["distinto"] += 1
        cs = det.get("campos") or sorted(det.get("pixeles") or []) or ["(sin campo: %s)" % det]
        campos.update(cs)
        if len(ejemplos) < 5:
            ejemplos.append("%s: %s" % ("|".join(k), sorted(cs)[:6]))

    for k in sorted(set(nc) & set(nd)):
        a_, b_ = nc[k], nd[k]
        # Otra versión de producto u otro gránulo (el nombre trae la hora de producción de NASA: un gránulo
        # reprocesado entre los dos jobs) es otra entrada, no otro cableado: cuenta como cobertura (A108,
        # verificador del PR #822, hueco 1), igual que en contar_pasadas_noche.py.
        if a_.get("product_version") != b_.get("product_version") or a_.get("granule") != b_.get("granule"):
            version.append("|".join(k))
            continue
        est, det = U.comparar({c: v for c, v in a_.items() if c not in VOLATILES},
                              {c: v for c, v in b_.items() if c not in VOLATILES})
        if est in ("borde", "hotspot_escena"):
            a_probar[k[0]].append((k, a_, b_, est, det))
        elif est == "distinto":
            anotar_distinto(k, det)
        else:
            estados[est] += 1
            if est == "orden":
                admitidos["orden"].append("%s: %s" % ("|".join(k), det.get("listas_reordenadas")))
    for vol, lista in sorted(a_probar.items()):
        try:
            malos = set(predicado([(x[1], x[2]) for x in lista], vol))
        except Exception as e:  # sin node o sin el volcán en el tablero: no se sabe, el G3 queda INDECIDIBLE
            sin_predicado.extend("%s: %s" % ("|".join(x[0]), e) for x in lista)
            continue
        for j, (k, _, _, est, det) in enumerate(lista):
            if j in malos:
                anotar_distinto(k, {"campos": ["predicado del tablero distinto"]})
            else:
                estados[est] += 1
                admitidos[est].append("%s: píxeles (control, diurno) %s, campos distintos %s"
                                      % ("|".join(k), det.get("pixeles") or "iguales como conjunto",
                                         det.get("campos") if est == "hotspot_escena" else det.get("campos_derivados")))
    return {"n_control": len(nc), "n_diurno": len(nd), "faltan": len(faltan), "sobran": len(sobran),
            "ej_cobertura": ["|".join(k) for k in (faltan + sobran)[:5]], "version_distinta": len(version),
            "estados": estados, "admitidos": admitidos, "campos_distintos": dict(campos), "ejemplos": ejemplos,
            "sin_predicado": len(sin_predicado), "ej_sin_predicado": sin_predicado[:3]}


def veredicto_g3(ni):
    """Cobertura primero (A108); después, FALLA si algún par quedó fuera de G3_ADMITIDAS; después, INDECIDIBLE si
    el predicado del tablero no pudo juzgar algún par de borde o hotspot_escena."""
    if ni["faltan"] or ni["sobran"] or ni["version_distinta"]:
        return "COBERTURA NOCTURNA DESPAREJA (repetir el job, A108)"
    if any(n for e, n in ni["estados"].items() if e not in G3_ADMITIDAS):
        return "FALLA (noches distintas: defecto del cableado)"
    if ni.get("sin_predicado"):
        # verificador del PR #847: sin node no se sabe si esos pares son distintos; no es un defecto del cableado
        return "INDECIDIBLE (el predicado del tablero no corrió en %d pares, p. ej. %s)" % (
            ni["sin_predicado"], ni["ej_sin_predicado"][:1])
    return "CUMPLE"


def nulo_barajado(estratos, rng, n=N_BARAJADOS):
    """Distribución de M1 − q_neg barajando positivo/negativo dentro de cada estrato (vol, sensor).
    `estratos`: lista de (n_s, P_s, K_s). Hipergeométrica exacta, ver el docstring del módulo."""
    P = sum(e[1] for e in estratos)
    N = sum(e[0] - e[1] for e in estratos)
    K = sum(e[2] for e in estratos)
    if not P or not N:
        return None
    X = np.zeros(n)
    for n_s, p_s, k_s in estratos:
        if p_s and k_s:
            X += rng.hypergeometric(k_s, n_s - k_s, p_s, size=n)
    return X / P - (K - X) / N


def distribucion_x_exacta(estratos):
    """Distribución exacta de X = publicadas que caen en positivos bajo el barajado dentro de cada estrato: suma de
    hipergeométricas independientes (población n_s, K_s publicadas, P_s positivos), por convolución. D = M1 − q_neg es
    creciente en X, así que P(nulo >= D) = P(X >= x_obs). Adenda K §3.1."""
    pmf = np.array([1.0])
    for n_s, p_s, k_s in estratos:
        pmf = np.convolve(pmf, stats.hypergeom(n_s, k_s, p_s).pmf(np.arange(p_s + 1)))
    return pmf


def cola_exacta(estratos, x):
    """P(X >= x), incluido el propio x (la regla de la adenda es «P(nulo >= D) < 0,05»)."""
    pmf = distribucion_x_exacta(estratos)
    return float(pmf[max(x, 0):].sum()) if x < len(pmf) else 0.0


def estratos_de(cls, ventanas, publicado=None):
    """(n_s, P_s, K_s) por (vol, sensor) sobre positivos y negativos PROCESADOS. `publicado` permite reemplazar la
    publicación real por la de un brazo sintético (controles del nulo)."""
    est = collections.defaultdict(lambda: [0, 0, 0])
    for k, c in cls.items():
        if c["ventana"] not in ventanas or c["estado"] == "no_procesada" or not ({"pos", "neg"} & c["pob"]):
            continue
        e = est[(k[0], k[1])]
        e[0] += 1
        e[1] += "pos" in c["pob"]
        e[2] += (publicado(k, c) if publicado else c["estado"] == "publicada")
    # S154 (H2): orden por clave. `cls` se arma iterando conjuntos de strings (orden según PYTHONHASHSEED), y el orden
    # de los estratos decide cómo reparte el generador sus números: sin ordenar, el p95 cambiaba de un proceso a otro
    # con la misma semilla (+0,2446 contra +0,2760 en W2 a W6).
    return [tuple(est[k]) for k in sorted(est)]


# Igualdad numérica, no umbral: cuando el nulo es degenerado (por ejemplo, un brazo que publica TODO un estrato y
# nada en los demás) cada muestra del nulo es exactamente el D observado, y dos cuentas de punto flotante del mismo
# número pueden diferir en el último bit. «Supera el p95» se lee como «lo supera por más que eso».
EPS_D = 1e-12


def d_de(cls, ventanas):
    """M1, q_neg y D = M1 − q_neg sobre positivos y negativos PROCESADOS. Es la única cuenta de D: la usan G1 y el
    control (a) del nulo, para que el control pase por el mismo código que decide."""
    pos = [k for k, c in cls.items() if c["ventana"] in ventanas and "pos" in c["pob"] and c["estado"] != "no_procesada"]
    neg = [k for k, c in cls.items() if c["ventana"] in ventanas and "neg" in c["pob"] and c["estado"] != "no_procesada"]
    if not pos or not neg:
        return None, None, None, len(pos), len(neg)
    m1 = sum(cls[k]["estado"] == "publicada" for k in pos) / len(pos)
    qn = sum(cls[k]["estado"] == "publicada" for k in neg) / len(neg)
    return m1, qn, m1 - qn, len(pos), len(neg)


def g1(cls, ventanas, rng, con_nulo=False):
    """M1 − q_neg contra el percentil 95 del nulo barajado. Devuelve dict con el veredicto."""
    m1, qn, d, npos, nneg = d_de(cls, ventanas)
    if d is None:
        return {"veredicto": "SIN SUSTRATO", "n_pos": npos, "n_neg": nneg}
    est = estratos_de(cls, ventanas)
    nulo = nulo_barajado(est, rng)
    p95 = float(np.percentile(nulo, PERCENTIL_NULO))
    # Cola exacta (adenda K §3.1): siempre se informa; decide sólo con --base k.
    x_obs = int(round(m1 * npos))
    pmf = distribucion_x_exacta(est)
    p_cola = float(pmf[x_obs:].sum())
    kk = sum(e[2] for e in est)
    x95 = int(np.searchsorted(np.cumsum(pmf), PERCENTIL_NULO / 100.0 - 1e-12))
    p95_exacto = x95 / npos - (kk - x95) / nneg
    cumple = (p_cola < ALFA_G2) if REGLA["cola_exacta"] else (d > p95 + EPS_D)
    out = {"veredicto": "CUMPLE" if cumple else "FALLA", "M1": m1, "q_neg": qn, "D": d, "p95": p95,
           "mediana_nulo": float(np.median(nulo)), "n_pos": npos, "n_neg": nneg,
           "x_obs": x_obs, "p_cola_exacta": p_cola, "p95_exacto": p95_exacto,
           "regla": "cola exacta" if REGLA["cola_exacta"] else "p95 muestreado"}
    if con_nulo:
        out["_nulo"] = nulo
    return out


def grupos_de(cls, ventanas):
    """Pasadas procesadas positivas o negativas, agrupadas por estrato (vol, sensor), con su etiqueta original."""
    grupos = collections.defaultdict(list)
    for k, c in cls.items():
        if c["ventana"] in ventanas and c["estado"] != "no_procesada" and ({"pos", "neg"} & c["pob"]):
            grupos[(k[0], k[1])].append(k)
    # S154 (H2): mismo motivo que en estratos_de; las pasadas también ordenadas, porque la permutación las recorre
    return [(sorted(grupos[g]), ["pos" in cls[k]["pob"] for k in sorted(grupos[g])]) for g in sorted(grupos)]


_POS, _NEG = frozenset({"pos"}), frozenset({"neg"})


def permutar_pob(cls, grupos, rng):
    """Una copia de `cls` con las etiquetas pos/neg PERMUTADAS dentro de cada estrato (vol, sensor), sobre las
    pasadas procesadas; la publicación de cada pasada queda donde estaba. Es un brazo que no discrimina por
    construcción, armado con los datos de este run. `grupos` sale de grupos_de (se arma una vez por control)."""
    out = {}
    for ks, etiquetas in grupos:
        perm = list(etiquetas)
        rng.shuffle(perm)
        for k, es_pos in zip(ks, perm):
            c = cls[k]
            out[k] = {"ventana": c["ventana"], "pob": _POS if es_pos else _NEG, "estado": c["estado"]}
    return out


def controles_del_nulo(cls, ventanas, rng):
    """§5.5, antes de usar el nulo, sobre la estructura de estratos de ESTE run. Los dos controles pasan por el
    código que decide (d_de y g1), no sólo por el que arma el nulo (verificador del PR #822: el control anterior
    comparaba muestras del nulo contra su propio p95 y seguía en «OK» con el nulo roto a propósito):
    (a) N_BRAZOS_AZAR permutaciones REALES de las etiquetas pos/neg dentro de cada estrato sobre `cls`; para cada
        una se calcula D con `d_de` y se cuenta cuántas superan el p95 que da `g1` sobre los datos reales. Esa
        fracción tiene que coincidir, dentro de 3 errores estándar, con la que el propio nulo pone sobre su p95:
        5 % cuando D es continuo, menos cuando D toma pocos valores y hay empates en el p95 (por eso la vara es la
        fracción del nulo y no un 5 % fijo; con un 5 % fijo un brazo con pocas publicaciones haría fallar el
        control sin que el nulo esté mal). Un nulo angosto o corrido hace subir la fracción de las permutaciones
        lejos de la del nulo, y el control falla.
    (b) un brazo sintético que publica exactamente en los positivos procesados tiene que pasar G1.
    PREGUNTA anotada (PREREGISTRO §9): el pre-registro pide que con etiquetas ya barajadas «el percentil 95 quede
    alrededor de cero»; con estratos de tasa distinta el centro del nulo NO es cero (es lo que el estrato corrige),
    así que se controla la tasa de falsos «discrimina», que es la propiedad que importa."""
    real = g1(cls, ventanas, rng, con_nulo=True)
    if "D" not in real:
        return {"ok": False, "texto": "sin sustrato para controlar el nulo"}
    if REGLA["cola_exacta"]:
        # Adenda K §3.1 (H4e del verificador): el control valida la regla que decide. (a) La fracción de
        # permutaciones reales que «cumplen» (cola exacta < 0,05) tiene que coincidir con la probabilidad exacta de
        # cumplir por azar, P(X >= x_crit), dentro de 3 errores estándar de las permutaciones. (b) Un brazo que
        # publica sólo en positivos tiene que cumplir.
        est = estratos_de(cls, ventanas)
        pmf = distribucion_x_exacta(est)
        colas = pmf[::-1].cumsum()[::-1]
        criticos = [x for x in range(len(pmf)) if colas[x] < ALFA_G2]
        x_crit = criticos[0] if criticos else len(pmf)
        esperada = float(colas[x_crit]) if criticos else 0.0
        grupos = grupos_de(cls, ventanas)
        sobre = 0
        for _ in range(N_BRAZOS_AZAR):
            m1p, _q, _d, npp, _n = d_de(permutar_pob(cls, grupos, rng), ventanas)
            sobre += m1p is not None and int(round(m1p * npp)) >= x_crit
        frac = sobre / N_BRAZOS_AZAR
        tol = 3 * math.sqrt(max(esperada * (1 - esperada), 1e-12) / N_BRAZOS_AZAR)
        est_b = estratos_de(cls, ventanas, publicado=lambda k, c: "pos" in c["pob"])
        pasa_b = cola_exacta(est_b, sum(e[1] for e in est_b)) < ALFA_G2
        ok = abs(frac - esperada) <= tol and pasa_b
        return {"ok": ok, "frac_permutaciones": frac, "frac_nulo": esperada, "tolerancia": tol, "perfecto_pasa": pasa_b,
                "texto": "cola exacta: permutaciones reales de pos/neg por estrato que cumplen: %.3f contra %.3f exacto (± %.3f) | brazo que publica sólo en positivos pasa G1: %s"
                         % (frac, esperada, tol, "sí" if pasa_b else "NO")}
    p95, nulo = real["p95"], real.pop("_nulo")
    esperada = float(np.mean(nulo > p95 + EPS_D))
    sobre = 0
    grupos = grupos_de(cls, ventanas)
    for _ in range(N_BRAZOS_AZAR):
        d = d_de(permutar_pob(cls, grupos, rng), ventanas)[2]
        sobre += d is not None and d > p95 + EPS_D
    frac = sobre / N_BRAZOS_AZAR
    tol = 3 * math.sqrt(esperada * (1 - esperada) / N_BRAZOS_AZAR) + 3 * math.sqrt(esperada * (1 - esperada) / len(nulo))
    ok_a = abs(frac - esperada) <= tol
    # (b) brazo perfecto.
    est_b = estratos_de(cls, ventanas, publicado=lambda k, c: "pos" in c["pob"])
    nulo_b = nulo_barajado(est_b, rng)
    d_b = 1.0 - 0.0
    pasa_b = d_b > float(np.percentile(nulo_b, PERCENTIL_NULO)) + EPS_D
    ok = ok_a and pasa_b
    return {"ok": ok, "frac_permutaciones": frac, "frac_nulo": esperada, "tolerancia": tol, "perfecto_pasa": pasa_b,
            "texto": "permutaciones reales de pos/neg por estrato sobre el p95: %.3f contra %.3f del nulo (± %.3f) | brazo que publica sólo en positivos pasa G1: %s"
                     % (frac, esperada, tol, "sí" if pasa_b else "NO")}


def binomial_g2(x, n, p):
    """P(X >= x | n, p), una cola."""
    return float(stats.binom.sf(x - 1, n, p)) if n else None


def umbral_g2(n, p):
    """La menor cuenta de publicaciones que hace fallar G2 con n pasadas procesadas."""
    x = 0
    while binomial_g2(x, n, p) >= ALFA_G2:
        x += 1
    return x


def clopper_pearson(a, n, conf=0.95):
    lo = stats.beta.ppf((1 - conf) / 2, a, n - a + 1) if a else 0.0
    hi = stats.beta.ppf(1 - (1 - conf) / 2, a + 1, n - a) if a < n else 1.0
    return float(lo), float(hi)


# ---------------------------------------------------------------- clasificación y métricas
def clasificar(UW, idx_d, ventanas_ok):
    """Cada pasada del universo (positivo o pasada diurna de la tabla) en una de tres clases (§5.4)."""
    cls = {}
    for w in ventanas_ok:
        for k in UW[w]["pos"] | UW[w]["tabla"]:
            r = emparejar(idx_d, k)
            pob = set()
            if k in UW[w]["pos"]:
                pob.add("pos")
            if k in UW[w]["neg"]:
                pob.add("neg")
            if k in UW[w]["tabla"]:
                pob.add("tabla")
            estado = "no_procesada" if r is None else ("publicada" if r["pub"] else "sin_publicar")
            cls[k] = {"ventana": w, "pob": pob, "estado": estado, "rec": r}
    return cls


def contar(cls, ventanas, pob, sensor=None, filtro_vol=None):
    xs = [c for k, c in cls.items() if c["ventana"] in ventanas and pob in c["pob"]
          and (sensor is None or k[1] == sensor) and (filtro_vol is None or filtro_vol(k[0]))]
    proc = [c for c in xs if c["estado"] != "no_procesada"]
    return sum(c["estado"] == "publicada" for c in proc), len(proc), len(xs) - len(proc)


def metricas(cls, ventanas, sensor=None, filtro_vol=None):
    out = {}
    for m, pob in (("M1", "pos"), ("M2", "neg"), ("M3", "tabla")):
        a_, n_, nop = contar(cls, ventanas, pob, sensor, filtro_vol)
        out[m] = {"publicadas": a_, "procesadas": n_, "no_procesadas": nop, "tasa": tasa(a_, n_)}
    return out


def m5(rc, filas, coords, ventanas):
    """M5 (informativa): publicación del CONTROL en negativos limpios NOCTURNOS, con el flag apagado (como lo
    etiquetaría la producción). Nunca bajo el perfil del brazo diurno (§4)."""
    out = collections.Counter()
    for w in ventanas:
        c = VENTANA[w]
        with flag_viirs(False):
            pv, ns, nv, _ = bp.indexar_referencia(filas, coords, (c["desde"], c["hasta"]))
        recs = [dict(r) for r in rc if not r["dia"] and r["vol"] in c["vols"] and c["desde"] <= r["t"][:10] <= c["hasta"]]
        bp.etiquetar(recs, pv, ns, nv)
        for r in recs:
            if r["lab"] == "neg_limpio":
                out[(r["b"], "n")] += 1
                out[(r["b"], "pub")] += r["pub"]
    return {s: (out[(s, "pub")], out[(s, "n")]) for s in bp.BUCKETS}


# ---------------------------------------------------------------- evaluación con una regla
def evaluar_regla(filas, coords, modo, rc, rd, a, rng, decide):
    """Todo lo que depende de la referencia: universo, cobertura diurna, métricas, G1 y G2."""
    filas_m = aplicar_regla(filas, modo)
    UW = universo_por_ventana(S.universo(filas_m, coords))
    res = {"modo": modo}
    if decide:
        dif = control_referencia(UW, a.sustrato)
        res["referencia_ok"] = not dif
        print("\n== 3. REFERENCIA: la base que se lee reproduce sustrato.json del pre-registro? %s"
              % ("SÍ" if not dif else "NO: " + "; ".join(dif[:6])))
        por_vb_on, prob_idx, txt = control_indexado(filas_m, coords, UW)
        print("\n== 4. ÍNDICE (banco_paridad.indexar_referencia con la rama diurna encendida mientras indexa; A118)")
        for t in txt:
            print(t)
        res["indice_ok"] = not prob_idx
        for p in prob_idx:
            print("   PROBLEMA: " + p)
        res["por_vb_on"] = por_vb_on
    idx_d = indice(rd)
    ventanas_con_datos = [w for w in VENTANAS if w in a.ventanas_presentes]
    cls = clasificar(UW, idx_d, ventanas_con_datos)
    res["cls"] = cls
    res["UW"] = UW
    # ---- cobertura diurna (§5.4)
    excluidas, repetir = [], []
    if decide:
        motivos = motivos_log(a.logs, "diurno", bp.VOLS)
        print("\n== 5. COBERTURA DIURNA (§5.4): positivos y pasadas diurnas de la tabla en el brazo diurno")
        print("   %-3s %-8s %-28s %-28s %s" % ("W", "sensor", "positivos: no proc/sin pub/pub", "tabla: no proc/sin pub/pub", "motivo en el log de las no procesadas"))
    motivo_cob = {}
    for w in ventanas_con_datos:
        npos = [c for k, c in cls.items() if c["ventana"] == w and "pos" in c["pob"]]
        nop = sum(c["estado"] == "no_procesada" for c in npos)
        corta = []
        if npos and nop > MAX_NO_PROCESADAS_POS * len(npos):
            corta.append("positivos %d de %d" % (nop, len(npos)))
        # El mismo 10 % sobre las pasadas de la TABLA, por ventana y sensor, antes de G2 (verificador del PR #822,
        # hueco 5): las no procesadas salen del n de G2, y un corte de NASA de un día entero no es al azar.
        for s in VIIRS:
            xs = [c for k, c in cls.items() if c["ventana"] == w and "tabla" in c["pob"] and k[1] == s]
            nt = sum(c["estado"] == "no_procesada" for c in xs)
            if xs and nt > MAX_NO_PROCESADAS_POS * len(xs):
                corta.append("tabla %s %d de %d" % (s, nt, len(xs)))
        if corta:
            motivo_cob[w] = corta
            (excluidas if w in a.repetidas else repetir).append(w)
        if decide:
            for s in VIIRS:
                cuenta = {}
                for pob in ("pos", "tabla"):
                    xs = [c for k, c in cls.items() if c["ventana"] == w and pob in c["pob"] and k[1] == s]
                    cuenta[pob] = "%d/%d/%d de %d" % tuple([sum(c["estado"] == e for c in xs) for e in ("no_procesada", "sin_publicar", "publicada")] + [len(xs)])
                mot = collections.Counter(motivos.get((k[0], k[2]), "sin rastro en el log") for k, c in cls.items()
                                          if c["ventana"] == w and k[1] == s and c["estado"] == "no_procesada")
                print("   %-3s %-8s %-28s %-28s %s" % (w, s, cuenta["pos"], cuenta["tabla"], dict(mot) or "-"))
    if decide:
        for w in repetir:
            print("   %s: más del 10 %% sin procesar (%s): REPETIR el job corto antes de evaluar (§5.4)" % (w, "; ".join(motivo_cob[w])))
        for w in excluidas:
            print("   %s: ya repetida y siguen faltando (%s): COBERTURA INSUFICIENTE, no entra al veredicto (§5.4)" % (w, "; ".join(motivo_cob[w])))
    res["repetir"], res["excluidas"] = repetir, excluidas
    dec = tuple(w for w in DECIDEN if w in ventanas_con_datos and w not in excluidas)
    sin2 = tuple(w for w in SIN_W2 if w in ventanas_con_datos and w not in excluidas)
    res["deciden"], res["sin_w2"] = dec, sin2
    # ---- métricas (§4)
    if decide:
        print("\n== 6. MÉTRICAS (§4; denominadores = pasadas PROCESADAS por el brazo diurno)")
        print("   %-24s %-9s %-24s %-24s %-24s" % ("ventanas", "sensor", "M1 recall diurno", "M2 q_neg", "M3 q_dia"))
        for etq, vs in (("W2 a W6", dec), ("W3 a W6 (sin W2)", sin2)) + tuple((w, (w,)) for w in ventanas_con_datos):
            for s in (None,) + VIIRS:
                for filtro, nom in ((None, ""),) + (((lambda v: v == "Lascar"), " Láscar"), ((lambda v: v != "Lascar"), " resto")):
                    m = metricas(cls, vs, s, filtro)
                    print("   %-24s %-9s %-24s %-24s %-24s" % (
                        etq + nom, s or "ambos",
                        *["%s (%d/%d)" % (pct(m[x]["tasa"]), m[x]["publicadas"], m[x]["procesadas"]) for x in ("M1", "M2", "M3")]))
        res["metricas"] = {etq: {s or "ambos": metricas(cls, vs, s) for s in (None,) + VIIRS}
                           for etq, vs in (("W2-W6", dec), ("W3-W6", sin2), ("W1", ("W1",) if "W1" in ventanas_con_datos else ()))}
    # ---- G1 (§6)
    r1 = g1(cls, dec, rng)
    r2 = g1(cls, sin2, rng)
    r0 = g1(cls, ("W1",), rng) if "W1" in ventanas_con_datos else {"veredicto": "SIN DATOS"}
    ctrl = controles_del_nulo(cls, dec, rng)
    res.update({"G1_W2W6": r1, "G1_W3W6": r2, "G1_W1": r0, "controles_nulo": ctrl})
    # ---- G2 (§6)
    g2 = {}
    for s in VIIRS:
        a_, n_ = P_MIROVA[s] if modo == "original" else (
            sum(1 for w in DECIDEN for k in UW[w]["alerta"] if k[1] == s), sum(1 for w in DECIDEN for k in UW[w]["tabla"] if k[1] == s))
        p = a_ / n_
        x, n, _ = contar(cls, dec, "tabla", s)
        pv = binomial_g2(x, n, p)
        g2[s] = {"publicadas": x, "procesadas": n, "p_MIROVA": p, "p_MIROVA_cuenta": [a_, n_], "p_valor": pv,
                 "umbral_con_n": umbral_g2(n, p) if n else None, "clopper_pearson": clopper_pearson(a_, n_),
                 "veredicto": "SIN SUSTRATO" if not n else ("FALLA" if pv < ALFA_G2 else "CUMPLE")}
    res["G2"] = g2
    return res


def imprimir_g1_g2(res, titulo):
    print("\n== %s" % titulo)
    for etq, r in (("W2 a W6 (decide)", res["G1_W2W6"]), ("W3 a W6 (sin W2, decide)", res["G1_W3W6"]), ("W1 (informa, A119)", res["G1_W1"])):
        if "D" in r:
            print("   G1 %-26s M1 %s - q_neg %s = %+.4f | p95 del nulo barajado %+.4f (mediana %+.4f) | %d positivos, %d negativos procesados -> %s"
                  % (etq, pct(r["M1"]), pct(r["q_neg"]), r["D"], r["p95"], r["mediana_nulo"], r["n_pos"], r["n_neg"], r["veredicto"]))
            print("      cola exacta (adenda K §3.1): P(nulo >= D) = %.4f | p95 exacto %+.4f | decide: %s"
                  % (r["p_cola_exacta"], r["p95_exacto"], r["regla"]))
        else:
            print("   G1 %-26s %s" % (etq, r["veredicto"]))
    print("   controles del nulo (§5.5): %s -> %s" % (res["controles_nulo"]["texto"], "OK" if res["controles_nulo"]["ok"] else "FALLA"))
    for s, g in res["G2"].items():
        print("   G2 %-8s publica en %d de %d pasadas diurnas de la tabla procesadas | p_MIROVA %d/%d = %.4f (Clopper-Pearson 95 %% [%.4f, %.4f]) | P(X >= %d) = %s | falla desde %s -> %s"
              % (s, g["publicadas"], g["procesadas"], g["p_MIROVA_cuenta"][0], g["p_MIROVA_cuenta"][1], g["p_MIROVA"],
                 g["clopper_pearson"][0], g["clopper_pearson"][1], g["publicadas"],
                 "%.4g" % g["p_valor"] if g["p_valor"] is not None else "-", g["umbral_con_n"], g["veredicto"]))


def veredicto(res, controles):
    """§6, en orden: controles; repetición; G3; G1 con y sin W2; G2."""
    if controles:
        return "INDECIDIBLE (" + "; ".join(controles[:4]) + ")"
    if res["repetir"]:
        return "PENDIENTE DE REPETICION (%s)" % ", ".join(res["repetir"])
    faltan = [w for w in DECIDEN if w not in res["ventanas_presentes"]]
    if faltan:
        return "INCOMPLETO (faltan las ventanas %s)" % ", ".join(faltan)
    if res["G3"] != "CUMPLE":
        return "INDECIDIBLE (G3: %s; se resuelve antes de mirar M1 a M4)" % res["G3"]
    g1a, g1b = res["G1_W2W6"]["veredicto"], res["G1_W3W6"]["veredicto"]
    g2 = [res["G2"][s]["veredicto"] for s in VIIRS]
    if g1a != "CUMPLE":
        if REGLA["w2_decide_nicolas"] and g1b == "CUMPLE":
            # Adenda K §3.2 (sellada): simétrica de «pasa sólo con W2»; las alertas de W2 son sólo del OCR.
            return ("DECIDE NICOLAS CON M4 (G1 cumple sin W2 y falla con W2: las alertas de W2 son sólo OCR, adenda K "
                    "§3.2; G2 %s)" % dict(zip(VIIRS, g2)))
        return "NO ADOPTAR (G1 falla en W2 a W6: %s)" % g1a
    if g1b != "CUMPLE":
        return "DEPENDE DEL OCR, DECIDE NICOLAS (G1 pasa sólo con W2; G2 %s; ver M4)" % dict(zip(VIIRS, g2))
    if all(g == "CUMPLE" for g in g2):
        return "ADOPTAR (G1, G2 y G3; antes del flip: R2 por píxel, verificador independiente y el frontend corregido, §6 y §8)"
    return "DECIDE NICOLAS CON M4 (G1 y G3 cumplen, G2 %s)" % dict(zip(VIIRS, g2))


def evaluar(a):
    if getattr(a, "brazos", None):
        control, diurno = [x.strip() for x in a.brazos.split(",")]
        a.base = resolver_base(a.brazos.replace(" ", ""), getattr(a, "base", None))
        if a.base == "k" and not getattr(a, "sha_codigo", None):
            raise SystemExit("--base k exige --sha-codigo (commit del tag de despacho), adenda K §4 H2a")
        configurar_brazos(control, diurno, a.base)
        print("[brazos] control %s, diurno %s, base %s | regla G1: %s | W2: %s" % (
            control, diurno, a.base, "cola exacta" if REGLA["cola_exacta"] else "p95 muestreado",
            "decide Nicolás si cumple sin W2" if REGLA["w2_decide_nicolas"] else "pre-registro original"))
    a.raiz = [str(Path(r)) for r in a.raiz]
    a.logs = a.logs or [str(Path(r) / "logs") for r in a.raiz]
    if len(a.logs) != len(a.raiz):
        raise SystemExit("--logs tiene que traer un directorio por cada --raiz")
    a.repetidas = set(a.repetidas.split(",")) if a.repetidas else set()
    rng = np.random.default_rng(SEMILLA)
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    print("== A/B DIURNO DE VIIRS (D-10) | raíces %s" % a.raiz)
    print("   predicado del tablero: frontend/index.html sha256 %s" % sha_lf(RAIZ / "frontend" / "index.html"))
    refs = [("consolidado", a.cons), ("ocr", a.ocr), ("respaldo", a.respaldo), ("historico", a.historico)]
    print("   referencia: " + " | ".join("%s %s sha256 %s" % (n, Path(p).name, sha_lf(p)[:16]) for n, p in refs if p))
    filas, coords = cargar_filas(a)
    rc, dup_c = cargar_brazo(a.raiz, "control", coords, inner)
    rd, dup_d = cargar_brazo(a.raiz, "diurno", coords, inner)
    # Ventanas presentes: las que traen JSON de los dos brazos para todos sus volcanes en alguna raíz.
    presentes = []
    for w in VENTANAS:
        c = VENTANA[w]
        ok = all(any((Path(r) / BRAZOS[n] / (v + ".json")).exists() for r in a.raiz) for n in BRAZOS for v in c["vols"])
        hay = any(c["desde"] <= x["t"][:10] <= c["hasta"] and x["vol"] in c["vols"] for x in rc)
        if ok and hay:
            presentes.append(w)
    a.ventanas_presentes = presentes
    print("   ventanas con los dos brazos: %s | records control %d, diurno %d (pasadas repetidas entre raíces, gana la última: %d/%d)"
          % (presentes, len(rc), len(rd), dup_c, dup_d))
    controles = []

    # ---------------- 1. cableado
    print("\n== 1. CABLEADO (línea FLAGS_BRAZO de cada job, A89; ningún VIIRS saltado por diurno en el brazo diurno, A118)")
    for n in BRAZOS:
        p = cableado(a.raiz, a.logs, n)
        print("   %-8s %s" % (n, "OK" if not p else "ROTO: " + "; ".join(p[:3]) + (" (y %d más)" % (len(p) - 3) if len(p) > 3 else "")))
        if p:
            controles.append("cableado del brazo %s" % n)
    p = flags_iguales(a.raiz, a.logs)
    print("   fuera de la palanca los dos brazos leyeron lo mismo: %s" % ("OK" if not p else "NO: " + "; ".join(p[:3])))
    if p:
        controles.append("los brazos leyeron flags distintos fuera de la palanca")
    if getattr(a, "base", "c0") == "k":
        p = cableado_records(a.raiz, a.sha_codigo)
        print("   records de los dos brazos sin Test 1 y con codigo_sha %s (adenda K §4 H2a): %s"
              % (a.sha_codigo[:12], "OK" if not p else "ROTO: " + "; ".join(p[:3]) + (" (y %d más)" % (len(p) - 3) if len(p) > 3 else "")))
        if p:
            controles.append("records de los brazos fuera de K o de otro commit (H2a)")

    # ---------------- 2. nulo 1: el instrumento puede dar distinto de cero
    # POR SENSOR (verificador del PR #822, hueco 6): VIIRS 375 y 750 son dos procesadores y dos compuertas; con
    # «375 o 750» una compuerta de 750 cerrada pasaba sin aviso. Se exige cada sensor que tiene pasadas diurnas
    # de la tabla en la ventana (sustrato.json; hoy, los dos en las seis).
    tabla_por_sensor = {w["nombre"]: w["pasadas_tabla_por_sensor"]
                        for w in json.loads(Path(a.sustrato).read_text(encoding="utf-8"))["ventanas"]}
    print("\n== 2. NULO 1 (§5.1, por sensor): records diurnos con umbrales diurnos en el brazo diurno, ninguno en el control")
    for w in presentes:
        c = VENTANA[w]
        dentro = lambda x: c["desde"] <= x["t"][:10] <= c["hasta"] and x["vol"] in c["vols"]  # noqa: E731
        nd = {s: sum(1 for x in rd if dentro(x) and x["dia"] and x["b"] == s and x["diag_dia"]) for s in VIIRS}
        nmod = sum(1 for x in rd if dentro(x) and x["dia"] and x["b"] == "MODIS")
        ncd = sum(1 for x in rc if dentro(x) and x["dia"])
        mudos = [s for s in VIIRS if tabla_por_sensor[w][s] > 0 and nd[s] == 0]
        ok = not mudos and ncd == 0 and nmod == 0
        print("   %s: brazo diurno records diurnos con diag_umbrales_diurnos %s, %d MODIS diurnos | control %d diurnos -> %s"
              % (w, nd, nmod, ncd, "OK" if ok else "FALLA" + (" (sin records diurnos en %s)" % mudos if mudos else "")))
        if not ok:
            controles.append("nulo 1 en %s" % w + (" (%s)" % ", ".join(mudos) if mudos else ""))

    # ---------------- 3, 4, 5, 6, G1 y G2 con la regla original (decide)
    res = evaluar_regla(filas, coords, "original", rc, rd, a, rng, decide=True)
    res["ventanas_presentes"] = presentes
    if not res["referencia_ok"]:
        controles.append("la referencia no es la del pre-registro (congelarla o recontar el sustrato)")
    if not res["indice_ok"]:
        controles.append("indexar_referencia no ve el universo diurno")
    if not res["controles_nulo"]["ok"]:
        controles.append("controles del nulo barajado")

    # ---------------- 7. G3 (nulos 2 y 3)
    ni = noches_identicas(rc, rd)
    res["G3"] = veredicto_g3(ni)
    print("\n== 7. G3, NOCHES INTACTAS (nulos 2 y 3; pares clasificados con unir_intentos.comparar más el predicado del tablero, desviación D2): records nocturnos control %d, diurno %d | faltan %d, sobran %d %s | versión de producto o gránulo distintos %d | pares por categoría %s | campos de los distintos %s %s -> %s"
          % (ni["n_control"], ni["n_diurno"], ni["faltan"], ni["sobran"], ni["ej_cobertura"], ni["version_distinta"],
             ni["estados"], ni["campos_distintos"] or "ninguno", ni["ejemplos"], res["G3"]))
    for est in ("orden", "borde", "hotspot_escena"):
        for x in ni["admitidos"][est]:
            print("   admitido (%s, informa): %s" % (est, x))
    print("   campos excluidos de la comparación: %s (first_processed_utc agregado, ver PREGUNTAS del pre-registro)" % (VOLATILES,))
    res["noches"] = ni

    imprimir_g1_g2(res, "8. G1 Y G2 (regla de alertas mínimas: original, la que decide)")

    # ---------------- 9. M4
    print("\n== 9. M4: alertas protegidas recuperadas contra publicaciones en negativos diurnos limpios (por sensor y ventana)")
    cls = res["cls"]
    m4 = {}
    for w in presentes:
        for s in VIIRS:
            rec = sorted("|".join(k) for k, c in cls.items() if c["ventana"] == w and k[1] == s and "pos" in c["pob"] and c["estado"] == "publicada")
            agr = sorted("|".join(k) for k, c in cls.items() if c["ventana"] == w and k[1] == s and "neg" in c["pob"] and c["estado"] == "publicada")
            m4["%s|%s" % (w, s)] = {"recuperadas": rec, "agregadas_en_negativos": agr}
            print("   %s %-8s recuperadas %3d | agregadas en negativos limpios %4d" % (w, s, len(rec), len(agr)))
            for k in rec:
                print("      recuperada: %s" % k)
            for k in agr[:15]:
                print("      agregada:   %s" % k)
            if len(agr) > 15:
                print("      (y %d agregadas más, en el JSON)" % (len(agr) - 15))
    res["M4"] = m4
    emparejados = {id(c["rec"]) for c in cls.values() if c["rec"] is not None}
    fuera = collections.Counter(r["b"] for r in rd if r["dia"] and r["pub"] and r["b"] in VIIRS
                                and ventana_de((r["vol"], r["b"], r["t"])) in presentes and id(r) not in emparejados)
    print("   (informa) publicaciones diurnas del brazo diurno dentro de las ventanas sin pasada de la tabla ni positivo a 120 s: %s"
          % (dict(fuera) or "ninguna"))
    res["publicaciones_fuera_de_tabla"] = dict(fuera)

    # ---------------- 10. M5
    print("\n== 10. M5 (informa, NO entra al criterio): publicación del CONTROL en negativos limpios nocturnos, etiquetados con la rama diurna apagada")
    for etq, vs in (("W1", tuple(w for w in ("W1",) if w in presentes)), ("W2 a W6", tuple(w for w in DECIDEN if w in presentes))):
        if vs:
            x = m5(rc, filas, coords, vs)
            print("   %-8s %s" % (etq, " | ".join("%s %s (%d/%d)" % (s, pct(tasa(*x[s])), x[s][0], x[s][1]) for s in bp.BUCKETS)))

    # ---------------- 11. avisos informativos
    print("\n== 11. AVISOS (informan, no cambian el veredicto)")
    r1 = res["G1_W2W6"]
    if "q_neg" in r1:
        sd = math.sqrt(max(r1["q_neg"] * (1 - r1["q_neg"]), 1e-12) / r1["n_pos"])
        print("   poder (§5.6): con %d positivos y q_neg %s la desviación de M1 bajo azar es ~%.3f" % (r1["n_pos"], pct(r1["q_neg"]), sd))
        if r1["q_neg"] >= BANDA_SATURACION:
            print("   SATURACIÓN (A114): q_neg %s en la banda del Test 1 encendido; el A/B no puede decidir nada sobre la Tabla 1 diurna" % pct(r1["q_neg"]))
        # S154 (verificador de W2 a W6, H1): también por sensor. Con un sensor saturado y el otro callado el q_neg
        # conjunto queda bajo la banda y el aviso de arriba no sale (W2 a W6 real: VIIRS 375 89,3 %, conjunto 60,0 %).
        res["saturacion"] = {}
        for s in VIIRS:
            m2 = (res.get("metricas", {}).get("W2-W6", {}).get(s) or {}).get("M2") or {}
            q = m2.get("tasa")
            res["saturacion"][s] = bool(q is not None and q >= BANDA_SATURACION)
            if res["saturacion"][s]:
                print("   SATURACIÓN (A114) %s: q_neg %s (%d/%d) en la banda del Test 1 encendido; en ese sensor el A/B no puede "
                      "decidir nada sobre la Tabla 1 diurna" % (s, pct(q), m2["publicadas"], m2["procesadas"]))
        if r1["M1"] >= UMBRAL_AUDITORIA:
            print("   M1 sube de 0 a %s: mejora de más de 30 %%, exige auditoría independiente antes de aceptarla" % pct(r1["M1"]))

    # ---------------- 12. regla D-9 (informa)
    print("\n== 12. REGLA DE ALERTAS MÍNIMAS D-9 (informa; decide «original»)")
    res["regla_minimas"] = {}
    if not regla_disponible():
        print("   PENDIENTE: clase_mirova.aplicar_regla_minimas no existe en este árbol (PR #820 sin mergear). Cuando se mergee, esta sección informa SN y SE sin tocar lo que decide.")
        res["regla_minimas"] = "PENDIENTE (PR #820)"
    else:
        for modo in ("SN", "SE"):
            r = evaluar_regla(filas, coords, modo, rc, rd, a, np.random.default_rng(SEMILLA), decide=False)
            r.update({"G3": res["G3"], "ventanas_presentes": presentes})
            imprimir_g1_g2(r, "12.%s regla %s (INFORMA)" % (modo, modo))
            v = veredicto(r, controles)
            print("   veredicto con %s: %s%s" % (modo, v, "" if v == veredicto(res, controles) else "  <- DISTINTO del que decide"))
            res["regla_minimas"][modo] = {"G1_W2W6": r["G1_W2W6"]["veredicto"], "G1_W3W6": r["G1_W3W6"]["veredicto"],
                                          "G2": {s: r["G2"][s]["veredicto"] for s in VIIRS}, "veredicto": v}

    res["controles"] = controles
    res["veredicto"] = veredicto(res, controles)
    print("\n== VEREDICTO (§6, regla original): %s" % res["veredicto"])
    if a.out:
        sal = {k: v for k, v in res.items() if k not in ("cls", "UW", "por_vb_on")}
        sal["clases"] = {"|".join(k): {"ventana": c["ventana"], "pob": sorted(c["pob"]), "estado": c["estado"]} for k, c in sorted(res["cls"].items())}
        Path(a.out).write_text(json.dumps(sal, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return res


def parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raiz", action="append", required=True, help="salidas de una corrida: <brazo>/<volcan>.json")
    ap.add_argument("--logs", action="append", default=[], help="logs de cada raíz (por defecto <raiz>/logs)")
    ap.add_argument("--brazos", default="%s,%s" % (BRAZOS["control"], BRAZOS["diurno"]),
                    help="control,diurno (S154: el A/B sobre K usa _s154_ab_diurno_k_control,_s154_ab_diurno_k_on)")
    ap.add_argument("--base", choices=sorted(FLAGS_BASE), default=None,
                    help="detector de base que el cableado exige en los logs (k: los tres flags de K). Obligatorio si "
                         "--brazos no es el de W2 a W6 sobre C0 (adenda K §4 H2b)")
    ap.add_argument("--sha-codigo", dest="sha_codigo", default=None,
                    help="commit del tag de despacho; con --base k cada record de los dos brazos tiene que traerlo (H2a)")
    ap.add_argument("--repetidas", default="", help="ventanas ya repetidas por cobertura (§5.4), separadas por coma")
    ap.add_argument("--out")
    ap.add_argument("--cons", default=str(SNAP_CONS))
    ap.add_argument("--ocr", default=str(SNAP_OCR))
    ap.add_argument("--respaldo", default=str(RESPALDO_20260408))
    ap.add_argument("--historico", default=str(HISTORICO_RECUPERADAS))
    ap.add_argument("--sustrato", default=str(AQUI / "sustrato.json"))
    return ap


def main(argv=None):
    evaluar(parser().parse_args(argv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
