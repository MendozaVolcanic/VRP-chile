# -*- coding: utf-8 -*-
"""Evaluador común del instrumento (S162, fase 0 del programa por sensor): sirve a VIIRS 375, VIIRS 750 y MODIS.

POR QUÉ. En el A/B de D25 el 2026-10-12 a los tres brazos les faltaban 44 pasadas que producción sí tenía (una
protegida de Chillán de 8,44 MW), porque CMR no devolvió los gránulos reprocesados; el job dijo «Cobertura: completa»,
la cobertura comparó brazos entre sí y el evaluador sólo revisaba protegidas que ya tenían record en algún brazo
(`experiments/_s162_vuelta2/RECORD_FALTANTE_CHILLAN_12OCT.md`). Un hueco común a todos los brazos no se ve
comparando brazos entre sí; se ve partiendo de las pasadas de MIROVA. Eso hace este módulo:

- T1, cobertura contra la referencia: cada pasada de MIROVA (`clase_mirova.resumir_pasadas`, una por pasada a
  ±120 s) se busca en cada lado (brazos y control, que suele ser producción). Es INVÁLIDO POR INSTRUMENTO, antes de
  leer ningún veredicto: (a) una protegida (lectura A) sin record en algún brazo y que el control sí tiene (basta un
  brazo: uno con menos cobertura sesga igual que un hueco común, verificador de #904); (b) un volcán, sensor y día con
  pasadas de MIROVA y cero records en un brazo; (c) una protegida que algún brazo tiene y el control no (el control no
  sirve de vara de cobertura). Los días declarados como excluidos (D-29) no cuentan y se informan.
- T2, «no observado» como estado propio: si ningún lado (ni el control) tiene record de la pasada, no se sabe si el
  volcán cayó fuera del gránulo, si la escena fue inválida (el procesador devuelve None sin dejar record,
  `pipeline/process_viirs.py`, «if not np.any(roi_mask): return None») o si hubo un hueco común con el control. Esa
  pasada sale de todos los denominadores y se cuenta aparte. Si el control la tiene y el brazo no, es
  `falta_cobertura` (cuenta contra el instrumento, no contra el detector).
- T5, P1b en las dos direcciones (cruces de 1 MW del valor publicado entre control y brazo) y publicaciones sobre
  pasadas que la tabla de MIROVA lista como RUTINA (VE162-03), que P2 no cuenta cuando otra pasada de la noche alertó.

- T3, magnitud M con el comparador de ganancia d′ (D-28) y el placebo K×1,2 y K×0,8; P2 con la prueba de signos por
  bloque noche-volcán (D-45) y los tres placebos de D-44 (ver el bloque T3 más abajo).

- S163, tarea 1.35: las métricas también por tramo de 10° de cenit del sensor y por régimen (antes de #535, de #535 a
  K, desde K); informan, no deciden. Y la causa de cada pasada ausente (hueco de NASA, búsqueda vacía, sin incidencia,
  sin registro) con el JSON de cobertura del run (#909).

Las pruebas viven en `tests/test_evaluador_comun_s162.py`, `tests/test_evaluador_comun_t3_s162.py` y
`tests/test_evaluador_comun_s163.py`.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import glob
import json
import math
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import clase_mirova as cm  # noqa: E402

TOL_S = cm.VENTANA_S
UMBRAL_P1B_MW = cm.UMBRAL_PROTEGIDA_MW
OBSERVADO, FALTA, NO_OBSERVADO = "observado", "falta_cobertura", "no_observado"
INVALIDO = "INVALIDO POR INSTRUMENTO"
COBERTURA_OK = "COBERTURA OK"


# ------------------------------------------------------------------------------------------- pareo
def indexar_records(recs):
    """(volcán, sensor) -> lista ordenada de (instante, record). Los records traen `vol`, `b` y `dt` (naive UTC)."""
    idx = collections.defaultdict(list)
    for r in recs:
        idx[(r["vol"], r["b"])].append((r["dt"].replace(tzinfo=None), r))
    for v in idx.values():
        v.sort(key=lambda x: x[0])
    return idx


def record_de(idx, p, tol_s=TOL_S):
    """El record más cercano a la pasada dentro de ±tol_s, o None."""
    lista = idx.get((p.volcano, p.sensor_bucket), [])
    ts = [x[0] for x in lista]
    i = bisect.bisect_left(ts, p.instante - timedelta(seconds=tol_s))
    mejor = None
    while i < len(lista) and lista[i][0] <= p.instante + timedelta(seconds=tol_s):
        d = abs((lista[i][0] - p.instante).total_seconds())
        if mejor is None or d < mejor[0]:
            mejor = (d, lista[i][1])
        i += 1
    return None if mejor is None else mejor[1]


def clave(p):
    return "%s|%s|%s" % (p.volcano, p.sensor_bucket, p.instante.strftime("%Y-%m-%d %H:%M:%S"))


def tabla_por_pasada(pasadas, recs_por_lado, control, tol_s=TOL_S):
    """Una fila por pasada de MIROVA con el record de cada lado y su estado de cobertura.

    Estado del brazo: observado (tiene record), falta_cobertura (no lo tiene y el control sí), no_observado (nadie lo
    tiene). Estado del control: observado o no_observado.
    """
    if control not in recs_por_lado:
        raise ValueError("el control %r no está entre los lados %s" % (control, sorted(recs_por_lado)))
    idx = {lado: indexar_records(recs) for lado, recs in recs_por_lado.items()}
    alertas_noche = {(p.volcano, p.sensor_bucket, p.instante.strftime("%Y-%m-%d"))
                     for p in pasadas if p.estado == "alerta"}
    fp_noche = {(p.volcano, p.sensor_bucket, p.instante.strftime("%Y-%m-%d")) for p in pasadas if p.estado == "fp"}
    T = []
    for p in pasadas:
        rec = {lado: record_de(ix, p, tol_s) for lado, ix in idx.items()}
        hay_ctrl = rec[control] is not None
        cob = {}
        for lado, r in rec.items():
            if r is not None:
                cob[lado] = OBSERVADO
            elif lado != control and hay_ctrl:
                cob[lado] = FALTA
            else:
                cob[lado] = NO_OBSERVADO
        T.append({"pasada": p, "clave": clave(p), "dia": p.instante.strftime("%Y-%m-%d"), "rec": rec, "cob": cob,
                  "protegida": cm.es_protegida(p),
                  # S163 (1.35): el cenit es el del record del control (mismo gránulo que el brazo); sin record, None.
                  "z": (rec[control] or {}).get("z"), "regimen": regimen(p.instante),
                  "noche_con_alerta": (p.volcano, p.sensor_bucket, p.instante.strftime("%Y-%m-%d")) in alertas_noche,
                  "noche_con_fp": (p.volcano, p.sensor_bucket, p.instante.strftime("%Y-%m-%d")) in fp_noche})
    return T


# ------------------------------------------------------------------------------------------- T1 y T2
def cobertura(T, recs_por_lado, control, dias_excluidos=()):
    """Fallas de cobertura contra la referencia de MIROVA y resumen por lado. Ver el docstring del módulo."""
    brazos = sorted(l for l in recs_por_lado if l != control)
    excl = set(dias_excluidos)
    con_rec = collections.defaultdict(collections.Counter)    # lado -> (vol, b, día) -> n records
    for lado, recs in recs_por_lado.items():
        for r in recs:
            con_rec[lado][(r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d"))] += 1
    protegidas_sin_record, alertas_sin_record, excluidas = [], [], []
    control_sin_protegida, control_sin_record = [], 0
    dias_mirova = collections.Counter()
    no_obs_dia = collections.Counter()
    for f in T:
        p = f["pasada"]
        dias_mirova[(p.volcano, p.sensor_bucket, f["dia"])] += 1
        if f["cob"][control] == NO_OBSERVADO and f["dia"] not in excl:
            no_obs_dia[f["dia"]] += 1
        faltan = [b for b in brazos if f["rec"][b] is None]
        tienen = [b for b in brazos if f["rec"][b] is not None]
        if f["rec"][control] is None and tienen and f["dia"] not in excl:
            # Verificador de #904, hallazgo 2: el control no cubre lo que un brazo sí; no sirve de vara de cobertura.
            if f["protegida"]:
                control_sin_protegida.append("%s (MIROVA %s MW) la tiene %s" % (f["clave"], p.vrp_mw, ", ".join(tienen)))
            else:
                control_sin_record += 1
        # Verificador de #904, hallazgo 1: basta que falte en UN brazo (un brazo con menos cobertura sesga igual).
        if not (faltan and f["rec"][control] is not None and p.estado == "alerta"):
            continue
        destino = excluidas if f["dia"] in excl else (protegidas_sin_record if f["protegida"] else alertas_sin_record)
        destino.append("%s (MIROVA %s MW) falta en %s" % (f["clave"], p.vrp_mw, ", ".join(faltan)))
    dias_vacios = []
    for (vol, b, dia), n in sorted(dias_mirova.items()):
        for lado in brazos:
            if con_rec[lado][(vol, b, dia)] == 0:
                (excluidas if dia in excl else dias_vacios).append(
                    "%s|%s|%s sin records en %s (MIROVA %d pasadas, control %d records)"
                    % (vol, b, dia, lado, n, con_rec[control][(vol, b, dia)]))
    resumen = {}
    for lado in recs_por_lado:
        c = collections.Counter(f["cob"][lado] for f in T if f["dia"] not in excl)
        resumen[lado] = {"pasadas": sum(c.values()), OBSERVADO: c[OBSERVADO], FALTA: c[FALTA],
                         NO_OBSERVADO: c[NO_OBSERVADO]}
    veredicto = INVALIDO if (protegidas_sin_record or dias_vacios or control_sin_protegida) else COBERTURA_OK
    return {"veredicto": veredicto, "protegidas_sin_record_en_brazos": protegidas_sin_record,
            "dias_con_pasadas_de_mirova_y_sin_records": dias_vacios,
            "control_sin_protegida_que_un_brazo_tiene": control_sin_protegida,
            "aviso_control_sin_record_que_un_brazo_tiene": control_sin_record,
            "aviso_alertas_no_protegidas_sin_record_en_brazos": alertas_sin_record,
            # Verificador de #904, hallazgo 3: las no observadas por día dejan ver un hueco común con el control.
            "no_observado_por_dia": dict(sorted(no_obs_dia.items(), key=lambda x: (-x[1], x[0]))),
            "en_dias_excluidos": excluidas, "por_lado": resumen}


def observada_en(f, *lados):
    """La pasada entra a un denominador sólo si todos los lados la observaron (T2)."""
    return all(f["cob"][l] == OBSERVADO for l in lados)


# ------------------------------------------------------------------------------------------- T5
def _pub(r):
    return bool(r is not None and r.get("pub"))


def _disp(r):
    return float((r or {}).get("disp") or 0.0) if _pub(r) else 0.0


def p1b(T, control, brazo, umbral=UMBRAL_P1B_MW, dias_excluidos=()):
    """Cruces de `umbral` del valor publicado, en las dos direcciones, sobre pasadas observadas por los dos lados.

    abajo: protegida A que los dos publican, el control con `umbral` o más y el brazo debajo (el de D25).
    arriba: pasada donde el brazo publica `umbral` o más y el control publica menos o no publica; se informa por
    estado de MIROVA (una protegida que sube es acercarse a MIROVA; una RUTINA o un FALSO_POSITIVO que sube es una
    publicación de clase Bajo que MIROVA no hizo).
    """
    excl = set(dias_excluidos)
    abajo, arriba = [], collections.defaultdict(list)
    for f in T:
        if f["dia"] in excl or not observada_en(f, control, brazo):
            continue
        c, b, p = f["rec"][control], f["rec"][brazo], f["pasada"]
        if f["protegida"] and _pub(c) and _pub(b) and _disp(c) >= umbral > _disp(b):
            abajo.append("%s | %s %.3f -> %s %.3f | MIROVA %s" % (f["clave"], control, _disp(c), brazo, _disp(b),
                                                                  p.vrp_mw))
        if _pub(b) and _disp(b) >= umbral > _disp(c):
            estrato = "protegida" if f["protegida"] else p.estado
            arriba[estrato].append("%s | %s %.3f -> %s %.3f | MIROVA %s %s" % (
                f["clave"], control, _disp(c), brazo, _disp(b), p.estado, p.vrp_mw))
    return {"abajo": abajo, "arriba": dict(arriba)}


def publicaciones_sobre_rutina(T, lados, dias_excluidos=()):
    """Por lado: pasadas que la TABLA de MIROVA lista como RUTINA (fuente CONS) y el lado publica, separadas por si
    otra pasada del mismo volcán, sensor y día alertó (las que P2 no cuenta, VE162-03). Sólo pasadas observadas por
    todos los lados (T2)."""
    excl = set(dias_excluidos)
    out = {}
    base = [f for f in T if f["dia"] not in excl and f["pasada"].estado == "rutina" and f["pasada"].fuente == "CONS"
            and observada_en(f, *lados)]
    for lado in lados:
        con = [f["clave"] for f in base if _pub(f["rec"][lado]) and f["noche_con_alerta"]]
        sin = [f["clave"] for f in base if _pub(f["rec"][lado]) and not f["noche_con_alerta"]]
        out[lado] = {"rutinas_observadas": len(base), "publica_en_noche_con_alerta": con,
                     "publica_en_noche_sin_alerta": sin}
    return out


# ===========================================================================================================
# S163, tarea 1.35: estratos por cenit del sensor y por régimen. POR QUÉ: un píxel oblicuo es más grande y más
# deformado, y en Chillán la razón contra MIROVA cae con el cenit (experiments/_s154_chillan/razon_por_cenit.py,
# atribución SIN ATRIBUIR); un agregado promedia esa curva y una ventana con más pasadas de borde se lee como efecto del
# brazo (A90, A114). Y una ventana que cruza #535 (máscara de nube de 260 K, A104) o la adopción de K mezcla regímenes.
# El programa por sensor (§2) pide todo por tramos de 10° de cenit. Los estratos INFORMAN: no tocan cobertura(), p1b()
# ni ningún veredicto (tests/test_evaluador_comun_s163.py lo fija). Los tramos del auto-audit (banco_paridad.zbin, 4
# tramos anchos) son otra definición, más gruesa; aquí manda el programa.
# ===========================================================================================================
ANCHO_TRAMO_CENIT = 10
# Mismos cortes que el resto del proyecto (prueba de guarda): auto_audit_weekly.CORTE_535 y CAMBIO_DETECTOR_UTC del
# frontend, que lee vigilancia_sombra.leer_adopcion (K, #850). En producción los datos son todos de K tras el reproceso
# (#883): estos cortes no separan detectores ahí, separan temporada y canal de referencia; en un brazo sí pueden.
CORTE_535 = datetime(2026, 8, 28, 23, 0)
CORTE_K = datetime(2026, 10, 18, 9, 57, 30)
REGIMENES = ("antes_535", "535_a_K", "desde_K")


def tramo_cenit(z):
    """'z00-10', 'z10-20', ... según el cenit del sensor en grados; sin cenit, 'sin_cenit' (estrato aparte)."""
    if z is None:
        return "sin_cenit"
    lo = int(float(z) // ANCHO_TRAMO_CENIT) * ANCHO_TRAMO_CENIT
    return "z%02d-%02d" % (lo, lo + ANCHO_TRAMO_CENIT)


def regimen(instante):
    """Régimen por la hora UTC (naive) de la pasada de MIROVA."""
    if instante < CORTE_535:
        return "antes_535"
    return "535_a_K" if instante < CORTE_K else "desde_K"


def estrato_cenit(f):
    return tramo_cenit(f["z"])


def estrato_regimen(f):
    return f["regimen"]


def metricas_por_estrato(T, control, brazos, estrato_de, dias_excluidos=()):
    """Las métricas del evaluador recalculadas dentro de cada estrato (`estrato_de(f)` da su nombre).

    Por estrato: pasadas, estados de cobertura por lado, P1b (cuántos cruces abajo y arriba), publicaciones sobre RUTINA
    y P2 (neto, discordantes y bloques, sin regla: informa). Cada pasada cae en un solo estrato, así que las cuentas
    suman el agregado. La marca «noche con alerta» viene de la tabla entera: una RUTINA de 60° en una noche con alerta a
    20° sigue siendo de noche con alerta."""
    excl = set(dias_excluidos)
    grupos = collections.defaultdict(list)
    for f in T:
        if f["dia"] not in excl:
            grupos[estrato_de(f)].append(f)
    lados = [control] + list(brazos)
    out = {}
    for nom, Ts in sorted(grupos.items()):
        cob = {l: collections.Counter({OBSERVADO: 0, FALTA: 0, NO_OBSERVADO: 0}) for l in lados}
        for f in Ts:
            for l in lados:
                cob[l][f["cob"][l]] += 1
        rut = publicaciones_sobre_rutina(Ts, lados)
        e = {"pasadas": len(Ts), "cobertura": {l: dict(c) for l, c in cob.items()},
             "rutina": {l: {"rutinas_observadas": r["rutinas_observadas"],
                            "publica_en_noche_con_alerta": len(r["publica_en_noche_con_alerta"]),
                            "publica_en_noche_sin_alerta": len(r["publica_en_noche_sin_alerta"])}
                        for l, r in rut.items()},
             "p1b": {}, "p2": {}}
        for b in brazos:
            p = p1b(Ts, control, b)
            e["p1b"][b] = {"abajo": len(p["abajo"]), "arriba": sum(len(v) for v in p["arriba"].values())}
            contrib = contribuciones_p2(Ts, control, b)
            e["p2"][b] = {"neto": sum(x["c"] for x in contrib), "n_discordantes": len(contrib),
                          "B": len({x["bloque"] for x in contrib})}
        out[nom] = e
    return out


# ===========================================================================================================
# S163: causa de cada pasada ausente, con la cobertura que deja el run (#909). POR QUÉ: una pasada que MIROVA publicó
# y que un lado no tiene puede ser legítima (el gránulo llegó y no dejó record: volcán fuera de la escena, escena
# inválida) o un hueco de NASA. El 2026-10-12, en V1 de D25, CMR respondió vacío para NOAA-21 y Suomi NPP y el job dijo
# «Cobertura: completa» (experiments/_s162_vuelta2/RECORD_FALTANTE_CHILLAN_12OCT.md). Desde #909 el JSON de
# --cobertura-json trae las fallas (búsqueda o descarga) y las incidencias (sin_granulos, sin_geolocalizacion,
# dia_parcial) por volcán, día y plataforma. fetch registra sin_granulos «sin juicio» porque no sabe si debía haber
# pasada; aquí sí se sabe algo más: MIROVA tuvo una pasada de ese sensor ese día. Como su CSV no trae plataforma, una
# búsqueda vacía en UNA plataforma del sensor deja la ausencia como hueco PROBABLE, no seguro. Informa: no cambia
# cobertura() ni su veredicto (decidir si un hueco de NASA invalida es del pre-registro).
# ===========================================================================================================
CAUSA_HUECO = "hueco_nasa"                 # búsqueda o descarga fallida, L1B sin geolocalización o día parcial
CAUSA_VACIA = "busqueda_vacia"             # el catálogo respondió vacío en una plataforma del sensor: hueco probable
CAUSA_SIN_INCIDENCIA = "sin_incidencia"    # el run no registró nada: no observado legítimo (o pérdida del proceso)
CAUSA_SIN_REGISTRO = "sin_registro_de_cobertura"   # el lado no trae JSON de cobertura: causa desconocida
_TIPOS_HUECO = ("falla_busqueda", "falla_descarga", "sin_geolocalizacion", "dia_parcial")


def cargar_eventos_cobertura(rutas):
    """Fallas e incidencias de uno o más JSON de `run_pipeline.py --cobertura-json`, en una sola lista de eventos
    {tipo, volcan, fecha, plataforma}. Las fallas quedan como 'falla_<etapa>'."""
    out = []
    for ruta in rutas:
        d = json.loads(Path(ruta).read_text(encoding="utf-8"))
        for x in d.get("fallas") or []:
            out.append({"tipo": "falla_%s" % (x.get("etapa") or "busqueda"), "volcan": x.get("volcan"),
                        "fecha": x.get("fecha"), "plataforma": x.get("plataforma")})
        for x in d.get("incidencias") or []:
            out.append({"tipo": x.get("tipo"), "volcan": x.get("volcan"), "fecha": x.get("fecha"),
                        "plataforma": x.get("plataforma")})
    return out


def causa_ausencia(f, lado, eventos):
    """Causa de que `lado` no tenga record de la pasada `f`, o None si lo tiene. `eventos`: los del lado, o None si el
    lado no trajo cobertura. Un evento explica la ausencia si es del mismo volcán (o sin volcán) y día, y de una
    plataforma del mismo sensor (o sin plataforma: día parcial, falla general)."""
    import banco_paridad as bp
    if f["rec"][lado] is not None:
        return None
    if eventos is None:
        return CAUSA_SIN_REGISTRO
    p = f["pasada"]
    tipos = {e["tipo"] for e in eventos
             if e.get("fecha") == f["dia"] and e.get("volcan") in (None, p.volcano)
             and (e.get("plataforma") is None or bp.bucket(e["plataforma"]) == p.sensor_bucket)}
    if tipos & set(_TIPOS_HUECO):
        return CAUSA_HUECO
    if "sin_granulos" in tipos:
        return CAUSA_VACIA
    return CAUSA_SIN_INCIDENCIA


def huecos(T, eventos_por_lado, dias_excluidos=()):
    """Por lado: pasadas sin record contadas por causa y estado de cobertura, y la lista de protegidas sin record con su
    causa. `eventos_por_lado[lado]` es la lista de `cargar_eventos_cobertura` o None (sin cobertura)."""
    excl = set(dias_excluidos)
    out = {}
    for lado, eventos in eventos_por_lado.items():
        por = collections.defaultdict(collections.Counter)
        prot = []
        for f in T:
            if f["dia"] in excl:
                continue
            c = causa_ausencia(f, lado, eventos)
            if c is None:
                continue
            por[c][f["cob"][lado]] += 1
            if f["protegida"]:
                prot.append("%s (MIROVA %s MW) %s %s" % (f["clave"], f["pasada"].vrp_mw, f["cob"][lado], c))
        out[lado] = {"por_causa": {c: dict(n) for c, n in sorted(por.items())}, "protegidas": prot}
    return out


# ===========================================================================================================
# T3: magnitud M con el comparador de ganancia d′ (D-28) y su placebo; P2 con la prueba de signos (D-45) y los
# placebos de D-44. Portado de experiments/_s157_prereg_d25/evaluar_d25.py (tag s161-d25-lectura, 724e43452), que
# sólo sirve a VIIRS y al A/B de D25; acá queda para cualquier sensor y cualquier A/B nuevo. Las constantes y semillas
# son las selladas allí (D-27, D-28, D-30, D-32, D-45): un evaluador nuevo que quiera otras las declara en su
# pre-registro. La equivalencia con el original se prueba en experiments/_s162_instrumento/t3_equivalencia.py.
#
# POR QUÉ M necesita comparador: K queda bajo MIROVA (razón 0,5 a 0,65), así que cualquier brazo que sólo multiplique
# la magnitud de K por 1,2 «se acerca» a MIROVA en promedio y la regla simétrica le da MEJORA (R2-8 de AUDIT_S158_R2).
# d′ pregunta otra cosa: si el brazo queda más cerca de MIROVA que una ganancia UNIFORME del mismo tamaño (K×ĝ), o sea
# si sube los pares que debe subir. Para una ganancia pareja d′ es 0 y el MEJORA no cuenta.
# POR QUÉ P2 con signos por bloque: las pasadas de una noche comparten volcán y atmósfera; bajo el nulo el control y el
# brazo son intercambiables dentro de una noche, y cambiarlos invierte todos los aportes de esa noche a la vez.
# ===========================================================================================================
N_BOOT, SEMILLA = 10000, 157
N_MIN_PARES, N_MIN_NOCHES = 5, 3
N_CALIB, MAX_FALSOS_CALIB = 200, 0.05
MIN_VOLCANES_MEJORA, MIN_PARES_VOLCAN = 2, 3
MIN_PARES_PODER = 20
PLACEBO_GANANCIAS = (1.2, 0.8)
NOTA_COMPARADOR = "sube en promedio, no en los pares correctos (ADENDA_PLACEBO.md, D-28)"
NOTA_CALIB_DPRIMA = "la calibración de d′ falla: no se sabe si D sube los pares correctos (ADENDA_PLACEBO.md §5, D-30)"
SEMILLA_CALIB_DPRIMA = SEMILLA + 3       # 160, D-32
N_CALIB_DPRIMA = 1000                    # D-32
DEC_DPRIMA = 12
SEMILLA_P2_SIGNOS = SEMILLA + 5          # 162, D-45
N_SORTEOS_P2_SIGNOS = 10000
MAX_B_EXACTO_P2 = 20
MAX_B_SIN_SUSTRATO_P2 = 4
TOPE_P2_DEN = 20
UMBRAL_M_PROTEGIDA = cm.UMBRAL_PROTEGIDA_MW


def pesos_bloque(bloques, n_boot=N_BOOT, semilla=SEMILLA):
    """(n_boot x n_pares): cuántas veces entra cada par al remuestrear BLOQUES (noche-volcán) con reposición."""
    uniq = sorted(set(bloques))
    idx = np.array([uniq.index(b) for b in bloques])
    rng = np.random.default_rng(semilla)
    elegidos = rng.integers(0, len(uniq), size=(n_boot, len(uniq)))
    cuenta = np.zeros((n_boot, len(uniq)), dtype=np.int64)
    np.add.at(cuenta, (np.repeat(np.arange(n_boot), len(uniq)), elegidos.ravel()), 1)
    return cuenta[:, idx]


def medianas_ponderadas(d, W):
    o = np.argsort(d)
    ds, Ws = np.asarray(d, dtype=np.float64)[o], W[:, o]
    cs = np.cumsum(Ws, axis=1)
    tot = cs[:, -1]
    lo_r, hi_r = (tot - 1) // 2, tot // 2
    i_lo = (cs <= lo_r[:, None]).sum(axis=1)
    i_hi = (cs <= hi_r[:, None]).sum(axis=1)
    return (ds[i_lo] + ds[i_hi]) / 2.0


def medianas_ponderadas_filas(Dm, W):
    Dm = np.asarray(Dm, dtype=np.float64)
    o = np.argsort(Dm, axis=1, kind="stable")
    ds, Ws = np.take_along_axis(Dm, o, axis=1), np.take_along_axis(W, o, axis=1)
    cs = np.cumsum(Ws, axis=1)
    tot = cs[:, -1]
    lo_r, hi_r = (tot - 1) // 2, tot // 2
    i_lo = (cs <= lo_r[:, None]).sum(axis=1)
    i_hi = (cs <= hi_r[:, None]).sum(axis=1)
    filas = np.arange(Dm.shape[0])
    return (ds[filas, i_lo] + ds[filas, i_hi]) / 2.0


def regla_m(d, W):
    """MEJORA si el intervalo al 95 % de la mediana de d queda entero bajo 0; EMPEORA si entero sobre 0."""
    meds = medianas_ponderadas(d, W)
    lo, hi = np.percentile(meds, 2.5), np.percentile(meds, 97.5)
    return ("MEJORA" if hi < 0 else "EMPEORA" if lo > 0 else "NEUTRO"), float(lo), float(hi)


def d_par(k_mw, d_mw, m_mw):
    """Cuánto se acerca el brazo a MIROVA en ese par (negativo = más cerca), en unidades de log10."""
    return abs(math.log10(d_mw / m_mw)) - abs(math.log10(k_mw / m_mw))


def calibrar_simetrico(d, W, bloques, n_rep=N_CALIB, semilla=SEMILLA + 2):
    """D-27: el signo de d se sortea por bloque (nulo de mediana 0); devuelve (falsos MEJORA, falsos EMPEORA, poder)."""
    rng = np.random.default_rng(semilla)
    bl = list(bloques)
    uniq = sorted(set(bl)); idx = np.array([uniq.index(b) for b in bl])
    a = np.abs(np.asarray(d, dtype=np.float64))
    falsos = collections.Counter()
    for _ in range(n_rep):
        falsos[regla_m(rng.choice((-1.0, 1.0), size=len(uniq))[idx] * a, W)[0]] += 1
    poder = regla_m(-a, W)[0] == "MEJORA" if np.any(a > 0) else False
    return falsos["MEJORA"] / n_rep, falsos["EMPEORA"] / n_rep, bool(poder)


def comparar_con_ganancia(P, W, bloques):
    """D-28 §2 y §3 con D-30 (respuesta 2) y D-32: la regla simétrica sobre d′ = |log10(D/M)| − |log10(ĝ·K/M)|."""
    K = np.array([p["k"] for p in P], dtype=np.float64)
    Dv = np.array([p["d"] for p in P], dtype=np.float64)
    M = np.array([p["m"] for p in P], dtype=np.float64)
    lK, lD = np.log10(K / M), np.log10(Dv / M)
    g = lD - lK
    g_hat = float(np.median(g))
    dp = np.round(np.abs(lD) - np.abs(lK + g_hat), DEC_DPRIMA)
    g_b = medianas_ponderadas(g, W)
    Dp = np.round(np.abs(lD)[None, :] - np.abs(lK[None, :] + g_b[:, None]), DEC_DPRIMA)
    meds = medianas_ponderadas_filas(Dp, W)
    lo, hi = float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))
    r_p = "MEJORA" if hi < 0 else "EMPEORA" if lo > 0 else "NEUTRO"
    f_mej, f_emp, poder = calibrar_simetrico(dp, W, bloques, n_rep=N_CALIB_DPRIMA, semilla=SEMILLA_CALIB_DPRIMA)
    calibrada = f_mej <= MAX_FALSOS_CALIB
    vols_neg, vols_n, g_vol = 0, 0, {}
    for v_ in sorted({p["clave"].split("|")[0] for p in P}):
        sel = np.array([p["clave"].startswith(v_ + "|") for p in P])
        if sel.sum() >= MIN_PARES_VOLCAN:
            vols_n += 1; vols_neg += float(np.median(dp[sel])) < 0
        gv = float(np.median(g[sel]))
        g_vol[v_] = {"n": int(sel.sum()), "log": gv, "factor": float(10 ** gv)}
    return {"g_hat_log": g_hat, "g_hat_factor": float(10 ** g_hat),
            "g_hat_ic95": [float(np.percentile(g_b, 2.5)), float(np.percentile(g_b, 97.5))],
            "g_hat_por_volcan": g_vol, "regla_dprima": r_p, "dprima_mediana": float(np.median(dp)),
            "ic95_dprima": [lo, hi], "dprima_max_abs": float(np.max(np.abs(dp))),
            "falsos_mejora_dprima": f_mej, "falsos_empeora_dprima": f_emp, "calibrada_dprima": calibrada,
            "poder_dprima": poder if len(P) >= MIN_PARES_PODER else None,
            "volcanes_con_dprima_negativa": vols_neg, "volcanes_con_3_pares_dprima": vols_n,
            "dprima_da_mejora": bool(r_p == "MEJORA" and calibrada and vols_neg >= MIN_VOLCANES_MEJORA)}


def decidir_estrato(P, modo, comparador=True, ok_ctrl=True):
    """M de un estrato (pares k, d, m, clave, bloque) con la calibración simétrica (D-27) y el comparador (D-28).

    modo: "decide" (MEJORA y EMPEORA cuentan), "bloquea" (sólo EMPEORA cuenta) o "informa". Sin sustrato (menos de 5
    pares o de 3 noches): SIN SUSTRATO. comparador=False es sólo para informar el placebo «sin comparador»."""
    bl = [p["bloque"] for p in P]
    if len(P) < N_MIN_PARES or len(set(bl)) < N_MIN_NOCHES:
        return "SIN SUSTRATO", {"n": len(P), "noches": len(set(bl)), "modo": modo}
    d = np.array([d_par(p["k"], p["d"], p["m"]) for p in P])
    W = pesos_bloque(bl)
    r, lo, hi = regla_m(d, W)
    vols_neg, vols_n = 0, 0
    for v_ in sorted({p["clave"].split("|")[0] for p in P}):
        dv = [x for x, p in zip(d, P) if p["clave"].startswith(v_ + "|")]
        if len(dv) >= MIN_PARES_VOLCAN:
            vols_n += 1; vols_neg += float(np.median(dv)) < 0
    nota = ""
    f_mej, f_emp, poder = calibrar_simetrico(d, W, bl)
    calibrada = (f_emp <= MAX_FALSOS_CALIB) if modo == "bloquea" else (f_mej <= MAX_FALSOS_CALIB and f_emp <= MAX_FALSOS_CALIB)
    if modo == "informa":
        r_dec = r
    elif not ok_ctrl or not calibrada:
        r_dec = "INDECIDIBLE"
    elif modo == "bloquea" and r == "MEJORA":
        r_dec = "NEUTRO"
    elif r == "MEJORA" and vols_neg < MIN_VOLCANES_MEJORA:
        r_dec, nota = "NEUTRO", "MEJORA sostenida por menos de %d volcanes (adenda, H4)" % MIN_VOLCANES_MEJORA
    else:
        r_dec = r
    detalle = {"n": len(P), "noches": len(set(bl)), "modo": modo, "regla": r, "d_mediana": float(np.median(d)),
               "ic95": [lo, hi], "razon_K": float(np.median([p["k"] / p["m"] for p in P])),
               "razon_D": float(np.median([p["d"] / p["m"] for p in P])),
               "falsos_mejora": f_mej, "falsos_empeora": f_emp, "volcanes_con_d_negativa": vols_neg,
               "volcanes_con_3_pares": vols_n, "nota": nota, "calibrada": calibrada,
               "poder": poder if len(P) >= MIN_PARES_PODER else None}
    if comparador and modo != "informa":
        detalle.update(comparar_con_ganancia(P, W, bl))
        if r_dec == "MEJORA" and not detalle["calibrada_dprima"]:
            r_dec = "INDECIDIBLE"
            detalle["nota"] = "%s (falsos MEJORA de d′ %.3f, tope %.2f)" % (
                NOTA_CALIB_DPRIMA, detalle["falsos_mejora_dprima"], MAX_FALSOS_CALIB)
        elif r_dec == "MEJORA" and not detalle["dprima_da_mejora"]:
            r_dec = "NEUTRO"
            detalle["nota"] = NOTA_COMPARADOR
    return r_dec, detalle


def placebo_ganancia(P, modo, ganancias=PLACEBO_GANANCIAS):
    """El brazo placebo D = K×g. Sin comparador muestra cuánto aprobaría una ganancia cualquiera; con comparador tiene
    que quedar sin MEJORA (d′ es 0 idénticamente). Informa: no vuelve inválido nada (D-28 §2.5)."""
    out = {}
    for g in ganancias:
        Pg = [dict(p, d=p["k"] * g) for p in P]
        out[str(g)] = {"sin_comparador": decidir_estrato(Pg, modo, comparador=False)[0],
                       "con_comparador": decidir_estrato(Pg, modo, comparador=True)[0]}
    return out


def pares_m(T, control, brazo, estrato_de, excluir=lambda f: False, dias_excluidos=()):
    """Pares de M: alertas de MIROVA con VRP que los dos lados publican con magnitud mayor que 0, observadas por los
    dos (T2). `estrato_de(f)` da el nombre del estrato de la fila (por sensor, cenit, kernel...) o None."""
    excl = set(dias_excluidos)
    pares, salen = collections.defaultdict(list), collections.Counter()
    for f in T:
        p = f["pasada"]
        if f["dia"] in excl or p.estado != "alerta" or not p.vrp_mw or excluir(f) or not observada_en(f, control, brazo):
            continue
        c, b = f["rec"][control], f["rec"][brazo]
        if _pub(c) != _pub(b):
            salen["%s publica, %s no" % ((control, brazo) if _pub(c) else (brazo, control))] += 1
            continue
        if not (_pub(c) and _disp(c) > 0 and _disp(b) > 0):
            continue
        nom = estrato_de(f)
        if nom is None:
            continue
        pares[nom].append({"k": _disp(c), "d": _disp(b), "m": p.vrp_mw, "clave": f["clave"],
                           "bloque": "%s|%s" % (p.volcano, f["dia"])})
    return dict(pares), dict(salen)


# ----------------------------------------------------------------------------------------------- P2 (D-45)
def clase_p2(f, excluir=lambda f: False):
    """alerta_mb (alerta de MIROVA bajo 1 MW: error si no se publica), negativo (negativo limpio: RUTINA de la tabla en
    un volcán, sensor y día sin alerta ni FALSO_POSITIVO de MIROVA: error si se publica) u otra."""
    p = f["pasada"]
    if excluir(f):
        return "otra"
    if p.estado == "alerta" and not f["protegida"]:
        return "alerta_mb"
    if p.estado == "rutina" and p.fuente == "CONS" and not f["noche_con_alerta"] and not f["noche_con_fp"]:
        return "negativo"
    return "otra"


def es_error(f, lado, excluir=lambda f: False):
    c = clase_p2(f, excluir)
    pub = _pub(f["rec"][lado])
    return (c == "alerta_mb" and not pub) or (c == "negativo" and pub)


def contribuciones_p2(T, control, brazo, excluir=lambda f: False, dias_excluidos=()):
    """Pasadas discordantes (error en un lado y no en el otro), observadas por los dos: +1 si el error es sólo del
    brazo, -1 si es sólo del control. El bloque es volcán|día."""
    excl = set(dias_excluidos)
    out = []
    for f in sorted(T, key=lambda f: f["clave"]):
        if f["dia"] in excl or not observada_en(f, control, brazo):
            continue
        ec_, eb = es_error(f, control, excluir), es_error(f, brazo, excluir)
        if ec_ != eb:
            out.append({"clave": f["clave"], "c": 1 if eb else -1, "bloque": "%s|%s" % (f["pasada"].volcano, f["dia"])})
    return out


def prueba_signos_p2(sumas, neto, n_sorteos=N_SORTEOS_P2_SIGNOS, semilla=SEMILLA_P2_SIGNOS):
    """D-45 §2.3 a §2.5: exacta con 20 bloques o menos (enumeración por convolución), si no 10.000 sorteos."""
    B = len(sumas)
    if B <= MAX_B_EXACTO_P2:
        dist = {0: 1}
        for x in sumas:
            nueva = collections.Counter()
            for v, k in dist.items():
                nueva[v + x] += k
                nueva[v - x] += k
            dist = nueva
        den = 2 ** B
        return {"metodo": "exacto", "gana": [sum(k for v, k in dist.items() if v <= neto), den],
                "pierde": [sum(k for v, k in dist.items() if v >= neto), den],
                "dos_colas": [sum(k for v, k in dist.items() if abs(v) >= abs(neto)), den], "minimo": [1, den]}
    rng = np.random.default_rng(semilla)
    S = rng.choice((-1, 1), size=(n_sorteos, B))
    tot = S @ np.asarray(sumas, dtype=np.int64)
    den = int(n_sorteos) + 1
    return {"metodo": "sorteos", "gana": [1 + int((tot <= neto).sum()), den],
            "pierde": [1 + int((tot >= neto).sum()), den],
            "dos_colas": [1 + int((np.abs(tot) >= abs(neto)).sum()), den], "minimo": [1, den]}


def regla_signos_p2(neto, B, pr):
    """D-45 §2.6 y §2.7 (comparación con el 5 % en enteros)."""
    if B <= MAX_B_SIN_SUSTRATO_P2:
        return "SIN SUSTRATO"
    if neto < 0 and TOPE_P2_DEN * pr["gana"][0] <= pr["gana"][1]:
        return "GANA"
    if neto > 0 and TOPE_P2_DEN * pr["pierde"][0] <= pr["pierde"][1]:
        return "PIERDE"
    if neto > 0:
        return "BLOQUEA"
    return "EMPATE"


def decidir_p2(contrib, ok_ctrl=True):
    """P2 con la prueba de signos por bloque noche-volcán (D-45). Devuelve (resultado, detalle).

    Con los controles generales caídos (`ok_ctrl=False`, por ejemplo cobertura INVALIDO de T1) el resultado es
    INDECIDIBLE, como en el sellado (D-45 §2.8); los campos de la prueba se calculan igual. Diferencias declaradas con
    `evaluar_d25.decidir_p2_bloques` (verificador de #905): no informa D-34 ni D-42 (retiradas por D-45), y los
    filtros de sensor, volcán o Suomi NPP los pone quien llama (callback `excluir` de contribuciones_p2)."""
    neto = sum(x["c"] for x in contrib)
    por_bloque = collections.Counter()
    for x in contrib:
        por_bloque[x["bloque"]] += int(x["c"])
    sumas = [por_bloque[b] for b in sorted(por_bloque)]
    pr = prueba_signos_p2(sumas, neto)
    det = {"neto": neto, "n_discordantes": len(contrib), "B": len(sumas), "metodo": pr["metodo"],
           "p_gana": pr["gana"][0] / pr["gana"][1], "p_pierde": pr["pierde"][0] / pr["pierde"][1],
           "p_dos_colas": pr["dos_colas"][0] / pr["dos_colas"][1]}
    if not ok_ctrl:
        return "INDECIDIBLE", det
    return regla_signos_p2(neto, len(sumas), pr), det


# ----------------------------------------------------------------------------------------------- placebos de D-44
def placebo_p2(T, control, tipo, fraccion, semilla, excluir=lambda f: False, dias_excluidos=()):
    """Un brazo sintético a partir del control, a nivel de tabla (cambia `pub`, no los records), y su P2 contra el
    control. Los tres de D-44 (verificador de D-42, V42-10), que SÍ pueden fallar:
      a: apaga una fracción de las publicaciones del control en negativos limpios: tiene que dar GANA donde hay sustrato;
      b: apaga una fracción de sus publicaciones en alertas bajo 1 MW: tiene que dar PIERDE;
      c: simétrico por BLOQUE noche-volcán (corrige V42-21: el placebo de S160 sorteaba por pasada, y el nulo de P2 es
         por bloque). Lado +1: alertas bajo 1 MW publicadas (se apagan) y negativos limpios sin publicar (se
         encienden); lado -1: negativos publicados (se apagan) y alertas sin publicar (se encienden). Se toman sin
         reposición round(fracción·N) bloques al azar de los N que tienen pasadas de LOS DOS lados; en cada uno se tira
         una moneda justa y se voltean m = mín(n₊, n₋) pasadas del lado que salió. El aporte del bloque es ±m con
         probabilidad 1/2 exacta, así que el neto tiene distribución simétrica y la tasa de GANA y PIERDE es la de
         falsos de P2. (Primera versión: volteaba el bloque entero de un lado; como los bloques +1 traen más pasadas
         que los -1, el neto salía sesgado y dio 11 PIERDE de 40 en la prueba sintética.)
    Devuelve (resultado de P2, detalle con cuántas pasadas se tocaron y cuántos bloques eran elegibles)."""
    excl = set(dias_excluidos)
    rng = random.Random(semilla)
    elegibles = [f for f in T if f["dia"] not in excl and f["cob"][control] == OBSERVADO]
    voltear = set()
    faltaron = 0
    if tipo in ("a", "b"):
        buscada = "negativo" if tipo == "a" else "alerta_mb"
        pool = sorted(f["clave"] for f in elegibles if clase_p2(f, excluir) == buscada and _pub(f["rec"][control]))
        voltear = set(rng.sample(pool, int(round(fraccion * len(pool)))))
    elif tipo == "c":
        lados = {+1: collections.defaultdict(list), -1: collections.defaultdict(list)}
        for f in elegibles:
            c, pub = clase_p2(f, excluir), _pub(f["rec"][control])
            s = (+1 if pub else -1) if c == "alerta_mb" else (-1 if pub else +1) if c == "negativo" else 0
            if s:
                lados[s]["%s|%s" % (f["pasada"].volcano, f["dia"])].append(f["clave"])
        bloques = sorted(set(lados[+1]) & set(lados[-1]))
        faltaron = len(set(lados[+1]) ^ set(lados[-1]))      # bloques con un solo lado: no sirven al placebo
        for b in rng.sample(bloques, int(round(fraccion * len(bloques)))):
            s = rng.choice((+1, -1))
            m = min(len(lados[+1][b]), len(lados[-1][b]))
            voltear.update(rng.sample(sorted(lados[s][b]), m))
    else:
        raise ValueError("placebo %r: a, b o c" % tipo)
    nombre = "_placebo_%s" % tipo
    for f in T:
        r = f["rec"][control]
        if f["clave"] in voltear:
            f["rec"][nombre] = dict(r, pub=not _pub(r), disp=(0.0 if _pub(r) else 0.3))
        else:
            f["rec"][nombre] = r
        f["cob"][nombre] = f["cob"][control]
    try:
        res, det = decidir_p2(contribuciones_p2(T, control, nombre, excluir, dias_excluidos))
    finally:
        for f in T:
            f["rec"].pop(nombre, None)
            f["cob"].pop(nombre, None)
    det.update(tocadas=len(voltear), bloques_de_un_solo_lado=faltaron)
    return res, det


# ------------------------------------------------------------------------------------------- carga real
def cargar_lado(directorio, ventana, sensores, coords, inner):
    """Records nocturnos de un directorio de JSON por volcán, con el predicado del tablero (node) de banco_paridad.

    A diferencia de `banco_paridad.cargar_nuestros`, un volcán sin archivo no hace caer la carga: se informa (un
    brazo sin el JSON de un volcán es en sí una falla de cobertura, que verá `cobertura`)."""
    import banco_paridad as bp
    recs, casos, faltan = [], [], []
    for vol in bp.VOLS:
        ruta = Path(directorio) / ("%s.json" % vol)
        if not ruta.exists():
            faltan.append(vol)
            continue
        for r in json.loads(ruta.read_text(encoding="utf-8"))["records"]:
            b = bp.bucket(r.get("sensor"))
            t = r.get("datetime_utc", "")
            if b not in sensores or not (ventana[0] <= t[:10] <= ventana[1]):
                continue
            try:
                dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            lat, lon = coords[vol]
            if bp.es_pasada_diurna_descartada(b, lat, lon, dt.replace(tzinfo=__import__("datetime").timezone.utc)):
                continue
            recs.append({"vol": vol, "b": b, "dt": dt, "sensor": r.get("sensor"), "z": r.get("sensor_zenith_deg")})
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos) if casos else []
    for rec, p in zip(recs, pred):
        rec["disp"], rec["pub"] = p[3], p[4]
    return recs, faltan


def pasadas_nocturnas(ref, ventana, sensores, coords, canal, regla_minimas):
    import banco_paridad as bp
    from datetime import timezone
    out = []
    for p in cm.resumir_pasadas(ref, canal=canal, regla_minimas=regla_minimas):
        dia = p.instante.strftime("%Y-%m-%d")
        if p.sensor_bucket not in sensores or not (ventana[0] <= dia <= ventana[1]) or p.volcano not in coords:
            continue
        lat, lon = coords[p.volcano]
        if bp.es_pasada_diurna_descartada(p.sensor_bucket, lat, lon, p.instante.replace(tzinfo=timezone.utc)):
            continue
        out.append(p)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Evaluador común: cobertura contra MIROVA, no observado, P1b, RUTINA")
    ap.add_argument("--lado", action="append", required=True, help="NOMBRE=DIRECTORIO (repetible; brazos y control)")
    ap.add_argument("--control", required=True, help="nombre del lado control (p. ej. produccion)")
    ap.add_argument("--desde", required=True)
    ap.add_argument("--hasta", required=True)
    ap.add_argument("--sensores", default="VIIRS375,VIIRS750,MODIS")
    ap.add_argument("--ref", required=True, help="carpeta congelada con registro_vrp_consolidado.csv, registro_vrp_ocr.csv,"
                                                  " consolidado_filas_perdidas.csv y respaldo_20260408.csv")
    ap.add_argument("--canal", default="union", choices=cm.CANALES)
    ap.add_argument("--regla-minimas", default=cm.MODO_MINIMAS, choices=cm.MODOS_MINIMAS)
    ap.add_argument("--excluir-dias", default="", help="días UTC separados por coma (D-29)")
    ap.add_argument("--cobertura", action="append", default=[],
                    help="NOMBRE=RUTA (repetible): JSON de --cobertura-json del run de ese lado, o un patrón glob")
    ap.add_argument("--salida", help="JSON de salida")
    a = ap.parse_args(argv)
    import banco_paridad as bp
    from referencia_mirova_unificada import cargar_referencia_unificada
    ref_dir = Path(a.ref)
    opc = lambda n: (ref_dir / n) if (ref_dir / n).exists() else None  # noqa: E731
    ref = cargar_referencia_unificada(ref_dir / "registro_vrp_consolidado.csv", ref_dir / "registro_vrp_ocr.csv",
                                      respaldo_path=opc("respaldo_20260408.csv"),
                                      historico_path=opc("consolidado_filas_perdidas.csv"))
    sensores = tuple(s for s in a.sensores.split(",") if s)
    ventana = (a.desde, a.hasta)
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    lados = dict(x.split("=", 1) for x in a.lado)
    recs, faltan = {}, {}
    for nombre, d in lados.items():
        recs[nombre], faltan[nombre] = cargar_lado(d, ventana, sensores, coords, inner)
    pasadas = pasadas_nocturnas(ref, ventana, sensores, coords, a.canal, a.regla_minimas)
    excl = tuple(x for x in a.excluir_dias.split(",") if x)
    T = tabla_por_pasada(pasadas, recs, a.control)
    brazos = [l for l in lados if l != a.control]
    res = {"ventana": ventana, "sensores": sensores, "canal": a.canal, "regla_minimas": a.regla_minimas,
           "dias_excluidos": excl, "volcanes_sin_archivo": faltan, "pasadas_mirova": len(pasadas),
           # Verificador de #905: si la tabla y el OCR discrepan en una pasada, este evaluador sigue a la tabla y los
           # sellados unían las filas; se cuenta en cada corrida para que el día que aparezca no pase en silencio.
           "ocr_contradice_tabla": sum(p.ocr_contradice_tabla for p in pasadas),
           "ocr_cruza_1mw": sum(p.ocr_cruza_1mw for p in pasadas),
           "cobertura": cobertura(T, recs, a.control, excl),
           "p1b": {b: p1b(T, a.control, b, dias_excluidos=excl) for b in brazos},
           "rutina": publicaciones_sobre_rutina(T, list(lados), excl),
           # S163 (1.35): informan, no deciden.
           "estratos": {"cenit": metricas_por_estrato(T, a.control, brazos, estrato_cenit, excl),
                        "regimen": metricas_por_estrato(T, a.control, brazos, estrato_regimen, excl)}}
    # S163: causa de las ausencias con la cobertura del run (lado sin --cobertura: causa desconocida).
    rutas_cob = collections.defaultdict(list)
    for x in a.cobertura:
        nombre, patron = x.split("=", 1)
        rutas_cob[nombre] += sorted(glob.glob(patron)) or [patron]
    res["huecos"] = huecos(T, {l: (cargar_eventos_cobertura(rutas_cob[l]) if l in rutas_cob else None) for l in lados},
                           excl)
    if any(faltan.values()) and res["cobertura"]["veredicto"] == COBERTURA_OK:
        res["cobertura"]["veredicto"] = INVALIDO
    c = res["cobertura"]
    print("COBERTURA CONTRA MIROVA:", c["veredicto"])
    print("  pasadas donde el OCR contradice a la tabla (decide la tabla): %d; alerta a distinto lado de 1 MW: %d"
          % (res["ocr_contradice_tabla"], res["ocr_cruza_1mw"]))
    print("  protegidas sin record en algún brazo que el control tiene:", len(c["protegidas_sin_record_en_brazos"]))
    for x in c["protegidas_sin_record_en_brazos"][:20]:
        print("    ", x)
    print("  volcán-sensor-día con pasadas de MIROVA y sin records en un brazo:",
          len(c["dias_con_pasadas_de_mirova_y_sin_records"]))
    for x in c["dias_con_pasadas_de_mirova_y_sin_records"][:20]:
        print("    ", x)
    print("  protegidas que algún brazo tiene y el control no:", len(c["control_sin_protegida_que_un_brazo_tiene"]))
    for x in c["control_sin_protegida_que_un_brazo_tiene"][:20]:
        print("    ", x)
    print("  aviso: pasadas que algún brazo tiene y el control no:", c["aviso_control_sin_record_que_un_brazo_tiene"])
    print("  no observadas por día (las 5 más):", list(c["no_observado_por_dia"].items())[:5])
    print("  aviso: alertas no protegidas sin record en algún brazo que el control tiene:",
          len(c["aviso_alertas_no_protegidas_sin_record_en_brazos"]))
    print("  en días excluidos (no cuentan):", len(c["en_dias_excluidos"]))
    print("  volcanes sin archivo:", {k: v for k, v in faltan.items() if v})
    for lado, r in c["por_lado"].items():
        print("  %-12s %s" % (lado, r))
    for b, r in res["p1b"].items():
        print("P1b %s: abajo %d, arriba %s" % (b, len(r["abajo"]), {k: len(v) for k, v in r["arriba"].items()}))
    for lado, r in res["rutina"].items():
        print("RUTINA %s: de %d observadas, publica %d en noche con alerta y %d en noche sin alerta" % (
            lado, r["rutinas_observadas"], len(r["publica_en_noche_con_alerta"]), len(r["publica_en_noche_sin_alerta"])))
    for lado, h in res["huecos"].items():
        print("AUSENCIAS %s por causa: %s; protegidas sin record: %d" % (lado, h["por_causa"], len(h["protegidas"])))
        for x in h["protegidas"][:10]:
            print("    ", x)
    for eje, est in res["estratos"].items():
        print("ESTRATOS por %s (informan, no deciden):" % eje)
        for nom, e in est.items():
            print("  %-10s pasadas %5d | %s" % (nom, e["pasadas"], " | ".join(
                "%s: P1b %d/%d, P2 neto %+d en %d discordantes" % (b, e["p1b"][b]["abajo"], e["p1b"][b]["arriba"],
                                                                  e["p2"][b]["neto"], e["p2"][b]["n_discordantes"])
                for b in brazos)))
    if a.salida:
        Path(a.salida).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0 if c["veredicto"] == COBERTURA_OK else 2


if __name__ == "__main__":
    sys.exit(main())
