# -*- coding: utf-8 -*-
"""Evaluador del A/B diurno sobre la vía «código MIROVA» (S190, issue #813). Implementa ADENDA_VIA.md §3 y §4.

EL FENÓMENO. De día el canal de 4 µm suma a la emisión térmica la luz del Sol reflejada. MIROVA mira de día con
umbrales más altos y descarta la escena con reflejo especular bajo 12°; desde S186 nuestro detector ES el `.m` de
MIROVA (la vía), con esa rama diurna adentro. Lo que la apaga son tres compuertas previas (descarga, salto del gránulo y
store). El brazo diurno las abre con `enable_daytime_viirs` y `enable_daytime_modis`; la pregunta es la de S163: ¿comete
menos errores que hoy según el criterio de victoria (docs/MISSION.md)?

POR QUÉ ESTE ARCHIVO Y NO OTRO EVALUADOR. La adenda V manda reusar el evaluador sellado de S163
(`experiments/_s163_diurno_k/evaluar_diurno_k.py`) importándolo, y cambiar sólo los puntos 1 a 8 de su §3 y la regla
de su §4. Se reusan tal cual: los casos a a e (`veredicto_sensor`, opción e-ii), la prueba D, las métricas por sensor
(`metricas_sensor`), las banderas por periodo, I5 y su huella, I6 y sus placebos, R1, la robustez del §6.4
(`veredicto_final`), la desproporción y el filtro informativo de 12°. Se reescriben, con la lista de sensores como
parámetro, sólo las piezas de S163 que tenían a VIIRS fijo adentro o que la adenda cambia:
  * sensores: MODIS, VIIRS 375 y VIIRS 750 (§3.1); la carga, las pasadas y el control sintético ya no saltan el día
    de MODIS;
  * I1 (§3.2): los flags de la vía y los dos del día en la línea FLAGS_BRAZO; por record, como en S163, el sha de 40
    caracteres y cero records con el Test 1;
  * I2 (§3.3 y §3.4): el marcador es `diag_codigo_mirova.dayflag`; un record diurno de la vía sin `solar_zenith_deg`
    hace fallar I2 (la vía lo habría tratado como noche en silencio); la tabla cruzada dayflag contra elevación se
    informa;
  * I4 (c) con la vara de los tres sensores (`sustrato_via.json`);
  * M5 a M8 y la regla del §4: R-CH, R-W7, veredicto por flag y sin la cláusula de VIIRS 750 de S163.
Día sigue siendo elevación solar mayor que 0 sobre el volcán (`pipeline.store._solar_elevation`), no el dayflag.

Pruebas: tests/test_evaluar_diurno_via_s190.py; mutaciones: mutaciones.json (corredor
experiments/_s162_instrumento/mutar.py) con su salida en mutaciones_salida.txt; brazos sintéticos sobre la referencia
congelada: brazos_sinteticos.py.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import json
import os
import re
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
S163 = ROOT / "experiments" / "_s163_diurno_k"
for _p in (str(ROOT), str(ROOT / "scripts"), str(S163), str(AQUI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import clase_mirova as cm  # noqa: E402
import evaluador_comun as ec  # noqa: E402
import evaluar_diurno_k as ek  # noqa: E402
import sustrato_via as sv  # noqa: E402

SENSORES = ("MODIS", "VIIRS375", "VIIRS750")          # adenda V §3.1
SENSORES_VIIRS = ("VIIRS375", "VIIRS750")
OPCION_E = "e-ii"                                     # adenda V §4: la opción sellada en S163
CHILLAN = "NevadosDeChillan"                          # R-CH
FLAGS_VIA = ("ENABLE_MODIS_CODIGO_MIROVA", "ENABLE_V375_CODIGO_MIROVA", "ENABLE_V750_CODIGO_MIROVA")
MARCAS_K = ("sin_grilla", "sin_mxd03", "geo_distinta")   # records que cayeron a K (M6)
M5_MIN_PARES = 5
M5_RANGO = (0.5, 2.0)
M8_MIN_1MW = 5
FLAG_MODIS, FLAG_VIIRS = "enable_daytime_modis", "enable_daytime_viirs"
INVALIDO, INDECIDIBLE = ek.INVALIDO, ek.INDECIDIBLE
ADOPTAR, NO_ADOPTAR, SIN_CAMBIO = ek.ADOPTAR, ek.NO_ADOPTAR, ek.SIN_CAMBIO
DECIDE, DECIDE_M4 = ek.DECIDE, ek.DECIDE_M4


# =========================================================================================== reglas puras (§4)
def aplicar_modificadores(base, sin_chillan, sin_w7, m5, m8_1mw):
    """Adenda V §4 sobre el veredicto base (casos a a e) de un sensor. Devuelve (veredicto, motivos).

    R-CH: base ADOPTAR y sin Chillán NO ADOPTAR -> DECIDE NICOLÁS CON M4 (beneficio de un solo volcán en erupción).
    R-W7: sin W7 sale NO ADOPTAR -> DECIDE NICOLÁS CON M4. Se aplica como está escrito: también cuando el base ya es
      NO ADOPTAR (ver el informe de S190: un brazo malo en todas las ventanas sale así DECIDE NICOLÁS CON M4).
    M5: con 5 pares o más, una mediana nuestro/MIROVA fuera de 0,5 a 2 impide ADOPTAR -> DECIDE NICOLÁS.
    M8: 5 o más publicaciones diurnas de 1 MW o más en pasadas sin fila de MIROVA impiden ADOPTAR -> DECIDE NICOLÁS
      CON M4.
    Si a la vez corresponde DECIDE NICOLÁS y DECIDE NICOLÁS CON M4, manda el segundo (pide más a la vista)."""
    motivos, m4, dec = [], False, False
    if base == ADOPTAR and sin_chillan == NO_ADOPTAR:
        motivos.append("R-CH: sin Chillán sale NO ADOPTAR")
        m4 = True
    if sin_w7 == NO_ADOPTAR:
        motivos.append("R-W7: sin W7 sale NO ADOPTAR")
        m4 = True
    pares, med = m5
    if base == ADOPTAR and pares >= M5_MIN_PARES and med is not None and not (M5_RANGO[0] <= med <= M5_RANGO[1]):
        motivos.append("M5: mediana nuestro/MIROVA %.3f en %d pares, fuera de 0,5 a 2" % (med, pares))
        dec = True
    if base == ADOPTAR and m8_1mw >= M8_MIN_1MW:
        motivos.append("M8: %d publicaciones diurnas de 1 MW o más sin fila de MIROVA" % m8_1mw)
        m4 = True
    if m4:
        return DECIDE_M4, motivos
    if dec:
        return DECIDE, motivos
    return base, motivos


def veredicto_viirs(v375, v750):
    """Adenda V §4: `enable_daytime_viirs` abre VIIRS 375 y 750 juntos."""
    vs = {v375, v750}
    if None in vs:
        return INVALIDO
    if DECIDE_M4 in vs:
        return DECIDE_M4
    if DECIDE in vs:
        return DECIDE
    if ADOPTAR in vs and NO_ADOPTAR in vs:
        return DECIDE                     # separar el flag por sensor es un parche en pipeline/ (A45)
    if ADOPTAR in vs:
        return ADOPTAR                    # los dos ADOPTAR, o uno ADOPTAR y el otro SIN CAMBIO
    return NO_ADOPTAR


def veredicto_flags(comp, r1, por_sensor):
    """Adenda V §4, veredicto global: I1 a I4 (o R1, S163 §6.1) INVÁLIDO; I5 o I6 INDECIDIBLE; por lo demás un veredicto
    por flag. Sin la cláusula de S163 «VIIRS 750 en ADOPTAR pasa a DECIDE NICOLÁS». Un sensor que no se evaluó deja su
    flag INVÁLIDO (es un defecto del instrumento, no un resultado)."""
    if comp["invalido"] or r1:
        return {FLAG_MODIS: INVALIDO, FLAG_VIIRS: INVALIDO}
    if comp["indecidible"]:
        return {FLAG_MODIS: INDECIDIBLE, FLAG_VIIRS: INDECIDIBLE}
    v = {s: (por_sensor.get(s) or {}).get("veredicto") for s in ("MODIS", "VIIRS375", "VIIRS750")}
    return {FLAG_MODIS: v["MODIS"] if v["MODIS"] is not None else INVALIDO,
            FLAG_VIIRS: veredicto_viirs(v["VIIRS375"], v["VIIRS750"])}


def veredicto_final_flags(principal, variantes):
    """S163 §6.4 por flag: si el principal es ADOPTAR o NO ADOPTAR y una variante da otro, DECIDE NICOLÁS."""
    out = {}
    for flag, v in principal.items():
        out[flag] = ek.veredicto_final(v, {k: var[flag] for k, var in variantes.items()})
    return out


# =========================================================================================== compuertas y métricas
def compuerta_i2(recs_c, recs_b, pasadas, ventanas, sensores=SENSORES):
    """Adenda V §3.3 y §3.4. El control trae cero records diurnos (por elevación) en los tres sensores; el brazo trae
    records diurnos con dayflag 1 en cada ventana y sensor con pasadas diurnas de MIROVA; ningún record diurno de la vía
    llega sin `solar_zenith_deg` (la vía lo habría tratado como noche, dayflag 0, sin avisar)."""
    prob = []
    dia_c = [r for r in recs_c if r["b"] in sensores and r["es_dia"]]
    if dia_c:
        prob.append("I2: el control trae %d records diurnos (tendría que traer cero)" % len(dia_c))
    sin_ang = [r for r in recs_b if r["es_dia"] and r.get("via") is True and r.get("soz") is None]
    if sin_ang:
        prob.append("I2: %d records diurnos de la vía sin solar_zenith_deg (la vía los trató como noche)" % len(sin_ang))
    for w, desde, hasta in ventanas:
        for s in sensores:
            hay_mirova = any(p.sensor_bucket == s and p._es_dia and desde <= p.instante.strftime("%Y-%m-%d") <= hasta
                             for p in pasadas)
            hay_b = any(r["b"] == s and r["es_dia"] and r.get("dayflag") == 1
                        and desde <= r["dt"].strftime("%Y-%m-%d") <= hasta for r in recs_b)
            if hay_mirova and not hay_b:
                prob.append("I2 %s %s: MIROVA tiene pasadas diurnas y el brazo ningún record con dayflag 1" % (w, s))
    return prob


def tabla_dayflag(recs_por_lado):
    """Adenda V §3.4, informativa: dayflag de la vía contra día por elevación, por lado y sensor."""
    c = collections.Counter()
    for lado, recs in recs_por_lado.items():
        for r in recs:
            c["%s|%s|%s|dayflag=%s" % (lado, r["b"], "dia" if r["es_dia"] else "noche", r.get("dayflag"))] += 1
    return dict(sorted(c.items()))


def compuerta_i4(T, recs_b, brazo, p_sup, sensores=SENSORES):
    """evaluar_diurno_k.compuerta_i4 con la lista de sensores como parámetro (en S163 recorría sólo VIIRS)."""
    prob, det = [], {}
    dia_b = collections.Counter((r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d")) for r in recs_b if r["es_dia"])
    for s in sensores:
        filas = [f for f in T if ek._sensor_dia(f, s)]
        sin = [f for f in filas if f["rec"][brazo] is None]
        for f in sin:
            if f["pasada"].estado == "alerta":
                prob.append("I4a %s: alerta diurna sin record del brazo (MIROVA %s MW)" % (f["clave"], f["pasada"].vrp_mw))
        vacios = sorted({(f["pasada"].volcano, s, f["dia"]) for f in filas
                         if dia_b[(f["pasada"].volcano, s, f["dia"])] == 0})
        for v in vacios:
            prob.append("I4b %s|%s|%s: pasadas diurnas de MIROVA y ningún record diurno del brazo" % v)
        if ek.cobertura_diurna_excede(len(sin), len(filas), p_sup[s]):
            prob.append("I4c %s: %d de %d pasadas diurnas de MIROVA sin record del brazo (p_sup %.4f)"
                        % (s, len(sin), len(filas), p_sup[s]))
        det[s] = {"pasadas_diurnas": len(filas), "sin_record": len(sin), "p_sup": p_sup[s]}
    return prob, det


def completar_control_diurno(T, control, brazo, sensores=SENSORES):
    """evaluar_diurno_k.completar_control_diurno con los tres sensores: el control no mira el día; en cada pasada diurna
    que el brazo observó, «observado, no publica»."""
    for f in T:
        if f["es_dia"] and f["pasada"].sensor_bucket in sensores and f["rec"][brazo] is not None \
                and f["rec"][control] is None:
            f["rec"][control] = {"pub": False, "disp": 0.0, "sintetico": True}
            f["cob"][control] = ec.OBSERVADO


def separar_k_diurnos(recs_b):
    """M6 (adenda V §1): los records diurnos del brazo que cayeron a K no son lo que se adopta. Devuelve (los demás,
    los diurnos de K)."""
    k = [r for r in recs_b if r["es_dia"] and r.get("via") is not True]
    return [r for r in recs_b if not (r["es_dia"] and r.get("via") is not True)], k


def claves_con_record(pasadas, recs):
    """Claves de las pasadas que tienen alguno de `recs` a ±120 s (para sacar de la regla las que vio K, M6)."""
    if not recs:
        return set()
    idx = ec.indexar_records(recs)
    return {ec.clave(p) for p in pasadas if ec.record_de(idx, p) is not None}


def contar_reflejo(recs_por_lado, sensores=SENSORES):
    """M7 (adenda V §3.5): escenas que el .m descartó por reflejo especular (`diag_codigo_mirova.motivo_vacio`), por lado,
    sensor y periodo; y si en VIIRS de día el brazo no descartó ninguna (sospecha de cableado)."""
    c = {lado: {s: {"dia": 0, "noche": 0} for s in sensores} for lado in recs_por_lado}
    for lado, recs in recs_por_lado.items():
        for r in recs:
            if r["b"] in sensores and r.get("motivo") == "sunglint":
                c[lado][r["b"]]["dia" if r["es_dia"] else "noche"] += 1
    return c


def publicaciones_sin_fila(pasadas, recs_b, sensores=SENSORES):
    """M8 (adenda V §3.6): publicaciones diurnas del brazo en pasadas que MIROVA no lista (ninguna pasada de MIROVA a
    ±120 s del mismo volcán y sensor), con su magnitud. Devuelve {sensor: {"lista": [...], "n_1mw": n}}."""
    idx = collections.defaultdict(list)
    for p in pasadas:
        idx[(p.volcano, p.sensor_bucket)].append(p.instante.replace(tzinfo=None))
    for v in idx.values():
        v.sort()
    out = {s: {"lista": [], "n_1mw": 0} for s in sensores}
    for r in recs_b:
        if r["b"] not in sensores or not r["es_dia"] or not r["pub"]:
            continue
        ts = idx.get((r["vol"], r["b"]), [])
        t = r["dt"].replace(tzinfo=None)
        i = bisect.bisect_left(ts, t - timedelta(seconds=cm.VENTANA_S))
        if i < len(ts) and ts[i] <= t + timedelta(seconds=cm.VENTANA_S):
            continue
        d = float(r["disp"] or 0.0)
        out[r["b"]]["lista"].append("%s|%s|%s|%.3f MW" % (r["vol"], r["b"], t.strftime("%Y-%m-%d %H:%M"), d))
        out[r["b"]]["n_1mw"] += d >= cm.UMBRAL_PROTEGIDA_MW
    return out


def magnitud_diurna(T, brazo, s):
    """M5 (adenda V §3.7): (pares, mediana nuestro/MIROVA) en las alertas diurnas de MIROVA (protegidas y bajo 1 MW)
    que el brazo observó y publicó."""
    razones = [ec._disp(f["rec"][brazo]) / f["pasada"].vrp_mw for f in T
               if ek._sensor_dia(f, s) and f["cob"][brazo] == ec.OBSERVADO and f["pasada"].estado == "alerta"
               and f["pasada"].vrp_mw and ec._pub(f["rec"][brazo])]
    return len(razones), (statistics.median(razones) if razones else None)


# =========================================================================================== evaluación
def _dias_de(ventanas, nombre):
    return {d.strftime("%Y-%m-%d") for w, d0, d1 in ventanas if w == nombre for d in ek._dias(d0, d1)}


def evaluar(pasadas, recs_por_lado, control, brazo, p_sup, sha, ventanas, excluir_claves=(), excluir_dias=(),
            problemas_log=(), otra_como_negativo=False, sin_volcanes=(), con_i6=True, con_robustez=True):
    """Una evaluación completa (adenda V §3 y §4) sobre pasadas de MIROVA y records ya cargados (con `pub`, `disp`,
    `es_dia`, `t1`, `fuente_hotspot`, `sha`, `via`, `dayflag`, `motivo`, `soz`). Con `con_robustez`, cada sensor se
    vuelve a evaluar sin Chillán (R-CH) y sin W7 (R-W7) para aplicar el §4."""
    if not re.fullmatch(r"[0-9a-f]{40}", str(sha)):
        raise ValueError("sha del tag: hacen falta los 40 caracteres de git rev-parse <tag>^{commit}")
    excl_d, sin_v = set(excluir_dias), set(sin_volcanes)
    pas = [p for p in pasadas if p.instante.strftime("%Y-%m-%d") not in excl_d and p.volcano not in sin_v]
    if otra_como_negativo:
        # S163 §6.4 (d), ahora en los tres sensores: los FALSO_POSITIVO diurnos de la tabla cuentan como RUTINA.
        pas = [p._replace(estado="rutina") if (p.estado == "fp" and p.fuente == "CONS" and p.sensor_bucket in SENSORES
                                               and ek.es_dia_vol(p.volcano, p.instante)) else p for p in pas]
    recs = {lado: [r for r in rs if r["dt"].strftime("%Y-%m-%d") not in excl_d and r["vol"] not in sin_v]
            for lado, rs in recs_por_lado.items()}
    rc = recs[control]
    rb, k_dia = separar_k_diurnos(recs[brazo])
    claves_k = claves_con_record([p for p in pas if ek.es_dia_vol(p.volcano, p.instante)], k_dia)
    excl_k = set(excluir_claves) | claves_k
    recs_regla = {control: rc, brazo: rb}
    marcadas = [ek._Marcada(p, ek.es_dia_vol(p.volcano, p.instante)) for p in pas]
    marcadas_eval = [m for m in marcadas if ec.clave(m._p) not in excl_k]
    comp = {"invalido": list(problemas_log), "indecidible": []}
    comp["invalido"] += ek.compuerta_i1(recs, sha)
    comp["invalido"] += compuerta_i2(rc, rb, marcadas_eval, ventanas)
    T = ec.tabla_por_pasada(pas, recs_regla, control)
    for f, m in zip(T, marcadas):
        f["es_dia"] = m._es_dia
    ek.banderas_por_periodo(T, otra_como_negativo)
    T = [f for f in T if f["clave"] not in excl_k]
    Tn = [f for f in T if not f["es_dia"]]
    cob_n = ec.cobertura(Tn, {lado: [r for r in rs if not r["es_dia"]] for lado, rs in recs_regla.items()}, control)
    if cob_n["veredicto"] != ec.COBERTURA_OK:
        comp["invalido"].append("I3: cobertura nocturna %s (protegidas %d, días vacíos %d, control sin protegida %d)" % (
            cob_n["veredicto"], len(cob_n["protegidas_sin_record_en_brazos"]),
            len(cob_n["dias_con_pasadas_de_mirova_y_sin_records"]), len(cob_n["control_sin_protegida_que_un_brazo_tiene"])))
    p4, det4 = compuerta_i4(T, rb, brazo, p_sup)
    comp["invalido"] += p4
    i5, solo = ek.compuerta_i5(rc, rb)
    comp["indecidible"] += i5
    huellas = ek.huellas_nocturnas_distintas(rc, rb)
    if not any("I2: el control" in x for x in comp["invalido"]):
        completar_control_diurno(T, control, brazo)
    m8 = publicaciones_sin_fila(pas, rb)
    sub_ch = sub_w7 = None
    if con_robustez:
        kw = dict(p_sup=p_sup, sha=sha, ventanas=ventanas, excluir_claves=excluir_claves, problemas_log=problemas_log,
                  otra_como_negativo=otra_como_negativo, con_i6=False, con_robustez=False)
        sub_ch = evaluar(pasadas, recs_por_lado, control, brazo, excluir_dias=excl_d, sin_volcanes=sin_v | {CHILLAN},
                         **kw)
        sub_w7 = evaluar(pasadas, recs_por_lado, control, brazo, excluir_dias=excl_d | _dias_de(ventanas, "W7"),
                         sin_volcanes=sin_v, **kw)
    por_sensor, i6 = {}, {}
    for s in SENSORES:
        m = ek.metricas_sensor(T, rb, control, brazo, s, ventanas)
        m["base"], m["caso"] = ek.veredicto_sensor(m, OPCION_E)
        m["M5"] = magnitud_diurna(T, brazo, s)
        m["M8"] = m8[s]
        m["sin_chillan"] = sub_ch["por_sensor"][s]["base"] if sub_ch else None
        m["sin_W7"] = sub_w7["por_sensor"][s]["base"] if sub_w7 else None
        m["veredicto"], m["motivos"] = aplicar_modificadores(m["base"], m["sin_chillan"], m["sin_W7"], m["M5"],
                                                             m8[s]["n_1mw"])
        por_sensor[s] = m
        if con_i6:
            i6[s] = ek.compuerta_i6(T, brazo, s)
            comp["indecidible"] += ["I6 %s: %s" % (s, x) for x in i6[s]["problemas"]]
    r1 = ek.r1_perdidas(T, control, brazo)
    flags = veredicto_flags(comp, r1, por_sensor)
    m7 = contar_reflejo(recs)
    return {"flags": flags, "compuertas": comp, "por_sensor": por_sensor, "i6": i6, "r1": r1, "T": T,
            "cobertura_nocturna": cob_n, "cobertura_diurna": det4, "noche_solo_un_lado": solo,
            "noche_records_distintos_en_otros_campos": huellas,
            "M6_diurnos_de_K": ["%s|%s|%s|%s" % (r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M"), r.get("via"))
                                for r in k_dia],
            "M6_pasadas_fuera_de_la_regla": sorted(claves_k),
            "M7_reflejo": m7,
            # §3.5: sin ningún descarte VIIRS diurno en el brazo se informa sospecha de cableado antes del veredicto.
            "M7_sospecha": sum(m7[brazo][s]["dia"] for s in SENSORES_VIIRS) == 0,
            "dayflag_contra_elevacion": tabla_dayflag(recs),
            "pasadas": len(T), "pasadas_diurnas": sum(1 for f in T if f["es_dia"])}


def pasadas_de(filas, canal, ventanas, vols=None, regla=ek.REGLA_MINIMAS, umbral=cm.UMBRAL_MINIMA_MW):
    """evaluar_diurno_k.pasadas_de sin saltar el día de MODIS: pasadas de MIROVA de las ventanas, los tres sensores, de
    día y de noche."""
    out = []
    for p in cm.resumir_pasadas(filas, canal=canal, regla_minimas=regla, umbral_minima_mw=umbral):
        d = p.instante.strftime("%Y-%m-%d")
        if p.volcano not in ek.coords() or p.sensor_bucket not in SENSORES:
            continue
        if vols and p.volcano not in vols:
            continue
        if not any(w[1] <= d <= w[2] for w in ventanas):
            continue
        out.append(p)
    return out


def evaluar_completo(filas, recs, control, brazo, p_sup, sha, ventanas, problemas_log=(), filas_1_13=()):
    """El veredicto por flag con la robustez de S163 §6.4 (tabla sola, sin W2, sin reflejo probable, «otra» como
    negativo) y lo informativo (mínimas, filtro de 12° que la vía ya aplica, desproporción). Separado de main() para
    que la batería lo pruebe."""
    kw = dict(p_sup=p_sup, sha=sha, ventanas=ventanas, problemas_log=problemas_log)
    pas_u = pasadas_de(filas, "union", ventanas)
    principal = evaluar(pas_u, recs, control, brazo, **kw)
    reflejo, sin_pareo = ek.claves_reflejo(pas_u, filas_1_13)
    sin_pareo = [x for x in sin_pareo if any(w[1] <= x.split("|")[2][:10] <= w[2] for w in ventanas)]
    variantes = {"tabla": evaluar(pasadas_de(filas, "tabla", ventanas), recs, control, brazo, **kw)["flags"],
                 "sin_W2": evaluar(pas_u, recs, control, brazo, excluir_dias=_dias_de(ventanas, "W2"), **kw)["flags"],
                 "sin_reflejo": evaluar(pas_u, recs, control, brazo, excluir_claves=reflejo, **kw)["flags"],
                 "otra_como_negativo": evaluar(pas_u, recs, control, brazo, otra_como_negativo=True, **kw)["flags"]}
    final = veredicto_final_flags(principal["flags"], variantes)
    info = {"minimas_SE": evaluar(pasadas_de(filas, "union", ventanas, regla="SE"), recs, control, brazo,
                                  **kw)["flags"],
            "minimas_original": evaluar(pasadas_de(filas, "union", ventanas, regla="original"), recs, control, brazo,
                                        **kw)["flags"],
            "minimas_SN_0,04": evaluar(pasadas_de(filas, "union", ventanas, umbral=cm.UMBRAL_MINIMA_VARIANTE_MW), recs,
                                       control, brazo, **kw)["flags"]}
    rb12 = ek.aplicar_filtro_reflejo(recs[brazo])
    info["con_filtro_reflejo_12"] = evaluar(pas_u, {control: recs[control], brazo: rb12}, control, brazo, **kw)["flags"]
    reflejo12 = {"apagadas": sum(1 for r0, r1 in zip(recs[brazo], rb12) if r0["pub"] and not r1["pub"]),
                 "sin_angulos": sum(1 for r in recs[brazo] if r["es_dia"] and r["pub"] and ek.angulo_reflejo(r) is None)}
    return {"principal": principal, "variantes": variantes, "final": final, "info": info, "reflejo": reflejo,
            "reflejo_sin_pareo": sin_pareo, "reflejo12": reflejo12}


# =========================================================================================== carga real
def record_ligero(r, vol, b, dt, es_dia):
    """Los campos del record que lee el evaluador (sin la publicación, que la da el predicado del tablero)."""
    dg = r.get("diag_codigo_mirova") or {}
    return {"vol": vol, "b": b, "dt": dt, "es_dia": es_dia, "t1": r.get("triggered_test1"),
            "huella": ek.huella_record(r), "fuente_hotspot": r.get("final_hotspot_source"),
            "sha": (r.get("regimen") or {}).get("codigo_sha"), "via": r.get("via_codigo_mirova"),
            "dayflag": dg.get("dayflag"), "motivo": dg.get("motivo_vacio"),
            "sz": r.get("sensor_zenith_deg"), "sa": r.get("sensor_azimuth_deg"),
            "soz": r.get("solar_zenith_deg"), "soa": r.get("solar_azimuth_deg")}


def cargar_brazo(raices, brazo, ventanas, inner):
    """Records de los tres sensores, de día y de noche, con el predicado del tablero (node, A97)."""
    import banco_paridad as bp
    recs, casos = [], []
    vistos = set()
    for raiz in raices:
        for vol in bp.VOLS:
            ruta = Path(raiz) / brazo / ("%s.json" % vol)
            if not ruta.exists():
                continue
            for r in json.loads(ruta.read_text(encoding="utf-8"))["records"]:
                b = bp.bucket(r.get("sensor"))
                tt = r.get("datetime_utc", "")
                if b not in SENSORES or not any(w[1] <= tt[:10] <= w[2] for w in ventanas):
                    continue
                try:
                    dt = datetime.strptime(tt, "%Y-%m-%d %H:%M")
                except ValueError:
                    continue
                k = (vol, r.get("sensor"), tt)
                if k in vistos:
                    continue
                vistos.add(k)
                recs.append(record_ligero(r, vol, b, dt, ek.es_dia_vol(vol, dt)))
                slim = {kk: r.get(kk) for kk in bp.CAMPOS_JS if kk != "anomaly_pixels"}
                if r.get("f5_core_vrp_mw") is None:
                    slim["anomaly_pixels"] = [{kk: px.get(kk) for kk in ("lat", "lon", "vrp_mw", "bt_k")}
                                              for px in (r.get("anomaly_pixels") or [])]
                casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos) if casos else []
    for rr, p in zip(recs, pred):
        rr["disp"], rr["pub"] = p[3], bool(p[4])
    return recs


def problemas_flags(fl, brazo, control, donde):
    """I1 (a) de la adenda V §3.2 sobre una línea FLAGS_BRAZO ya leída: la vía en los tres sensores en los dos brazos y
    los dos flags del día apagados en el control y encendidos en el diurno; más lo que S163 ya pedía (K sin Test 1,
    rama de prosa, banda 22) y el perfil y el directorio del brazo."""
    if fl is None:
        return ["I1a %s: sin línea FLAGS_BRAZO" % donde]
    diurno = brazo != control
    esperado = {"ENABLE_TEST1_PATH": False, "ENABLE_TESTS_23_PROSE_BRANCH": True, "ENABLE_MODIS_B22_PRIMARY": True,
                "ENABLE_DAYTIME_VIIRS": diurno, "ENABLE_DAYTIME_MODIS": diurno, "PROFILE_NAME": brazo,
                "DATA_SUBDIR": brazo}
    esperado.update({k: True for k in FLAGS_VIA})
    return ["I1a %s: %s=%s, declarado %s" % (donde, k, fl.get(k), v) for k, v in esperado.items() if fl.get(k) != v]


def problemas_de_logs(raices, brazos, control):
    """I1 (a): la línea FLAGS_BRAZO de cada job, cuando la raíz trae logs/."""
    import banco_paridad as bp
    prob = []
    for raiz in raices:
        logs = Path(raiz) / "logs"
        if not logs.is_dir():
            continue
        for brazo in brazos:
            for vol in bp.VOLS:
                if not (Path(raiz) / brazo / ("%s.json" % vol)).exists():
                    continue
                p = logs / ("%s_%s.log" % (brazo, vol))
                fl = None
                if p.exists():
                    for linea in p.read_text(encoding="utf-8", errors="replace").splitlines():
                        if linea.startswith("FLAGS_BRAZO "):
                            fl = json.loads(linea[len("FLAGS_BRAZO "):])
                            break
                prob += problemas_flags(fl, brazo, control, "%s %s (%s)" % (brazo, vol, Path(raiz).name))
    return prob


def p_sup_de_vara(vara):
    """I4 (c): cota de Clopper-Pearson al 95 % de la tasa nocturna de producción sin record, los tres sensores."""
    return {s: sv.p_sup(vara[s]["sin_record_produccion"], vara[s]["pasadas_nocturnas"]) for s in SENSORES}


def imprimir(r):
    p = r["principal"]
    if p["M7_sospecha"]:
        print("SOSPECHA DE CABLEADO (M7): el brazo diurno no descartó por reflejo ninguna escena VIIRS diurna en W2 a W7")
    print("M7 escenas descartadas por reflejo (sunglint) por lado y sensor: %s" % p["M7_reflejo"])
    print("COMPUERTAS: inválido %d, indecidible %d" % (len(p["compuertas"]["invalido"]), len(p["compuertas"]["indecidible"])))
    for x in p["compuertas"]["invalido"][:30] + p["compuertas"]["indecidible"][:30]:
        print("  ", x)
    print("cobertura diurna:", p["cobertura_diurna"])
    print("noche, records en un solo brazo:", p["noche_solo_un_lado"])
    print("dayflag contra elevación (informativo, §3.4):", p["dayflag_contra_elevacion"])
    print("M6 records diurnos del brazo que cayeron a K: %d %s; pasadas fuera de la regla: %d"
          % (len(p["M6_diurnos_de_K"]), p["M6_diurnos_de_K"][:10], len(p["M6_pasadas_fuera_de_la_regla"])))
    print("R1:", len(p["r1"]))
    for s, m in p["por_sensor"].items():
        print("%s: P2 %s (neto %+d, B %d) | protegidas %d de %d | alertas<1MW %d de %d | negativos %d de %d (Q_d %.4f) | "
              "Q_n %.4f (%d) | D %s | neg>=1MW %d | pub en «otra» %d"
              % (s, m["p2"], m["neto"], m["p2_det"]["B"], m["P"], m["P_obs"], m["amb_recuperadas"], m["amb_obs"],
                 m["neg_pub"], m["neg_obs"], m["Qd"], m["Qn"], m["Qn_den"], m["D"], m["neg_1mw"], m["pub_otra"]))
        print("   base %s (caso %s) | sin Chillán %s | sin W7 %s | M5 %s | M8 %d de 1 MW o más %s"
              % (m["base"], m["caso"], m["sin_chillan"], m["sin_W7"], m["M5"], m["M8"]["n_1mw"], m["M8"]["lista"][:5]))
        print("   -> %s %s" % (m["veredicto"], m["motivos"]))
        print("   M4 por ventana:", m["por_ventana"])
    print("FLAGS (principal):", p["flags"])
    print("VARIANTES (§6.4 de S163):", r["variantes"])
    print("VEREDICTO FINAL POR FLAG:", r["final"])


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Evaluador del A/B diurno sobre la vía (ADENDA_VIA.md)")
    ap.add_argument("--raiz", action="append", required=True, help="raíz de una corrida (W2 a W7), repetible")
    ap.add_argument("--brazos", default="_s190_ab_diurno_via_control,_s190_ab_diurno_via_on")
    ap.add_argument("--ref", required=True, help="carpeta con los 4 CSV congelados (congelar_referencia.py)")
    ap.add_argument("--sustrato", default=str(AQUI / "sustrato_via.json"))
    ap.add_argument("--sha-codigo", required=True)
    ap.add_argument("--excluidos", default=None, help="json con excluir_dias (adenda 1 de S163, regla a y b')")
    ap.add_argument("--salida", default=None)
    ap.add_argument("--recorte", default=None, help="DESDE,HASTA: SÓLO para la prueba de humo")
    a = ap.parse_args(argv)
    import banco_paridad as bp
    import sustrato_k as sk
    import evaluar_con_exclusion as ece
    control, brazo = a.brazos.split(",")
    sus = json.loads(Path(a.sustrato).read_text(encoding="utf-8"))
    ref = Path(a.ref)
    distintos = [n for n in sk.ARCHIVOS_REF if ek.sha256(ref / n) != sus["sha256"][n]]
    if distintos:
        print("REFERENCIA DISTINTA DE LA DEL SUSTRATO (sha256): %s. No se decide." % distintos)
        return 3
    ventanas = [(w[0], w[1], w[2]) for w in sv.VENTANAS]
    dias = []
    if a.excluidos:
        dias = list(json.loads(Path(a.excluidos).read_text(encoding="utf-8"))["excluir_dias"])
        malos = ece.validar_dias(dias, ventanas)
        if malos:
            print("DÍAS EXCLUIDOS QUE NO SON FECHAS DE W2 A W7: %s. No se decide." % malos)
            return 4
    if a.recorte:
        d0, d1 = a.recorte.split(",")
        ventanas = [(w, max(x, d0), min(y, d1)) for w, x, y in ventanas if max(x, d0) <= min(y, d1)]
        print("RECORTE DE PRUEBA %s a %s: esto NO es la evaluación que decide" % (d0, d1))
    filas = sk.cargar_ref(ref)
    p_sup = p_sup_de_vara(sus["vara_cobertura_nocturna_produccion"])
    inner = bp.inner_desde_html()
    recs = {control: cargar_brazo(a.raiz, control, ventanas, inner), brazo: cargar_brazo(a.raiz, brazo, ventanas, inner)}
    logs = problemas_de_logs(a.raiz, (control, brazo), control)
    if dias:
        print("DÍAS EXCLUIDOS POR HUECO DE NASA: %s" % dias)
        filas, recs = ece.quitar_dias(filas, recs, dias)
    r = evaluar_completo(filas, recs, control, brazo, p_sup, a.sha_codigo, ventanas, logs, ek._filas_1_13())
    imprimir(r)
    print("INFORMATIVO (no decide): %s" % r["info"])
    print("filtro de reflejo de 12° sobre lo publicado (la vía ya lo aplica): apaga %d; %d diurnas sin ángulos"
          % (r["reflejo12"]["apagadas"], r["reflejo12"]["sin_angulos"]))
    for s in SENSORES:
        print("  %s desproporción (1.13 a) sobre lo nuestro): %s" % (s, ek.desproporcion(recs[brazo], s)))
    print("noche, records en los dos brazos con otros campos distintos (informativo): %d %s"
          % (len(r["principal"]["noche_records_distintos_en_otros_campos"]),
             r["principal"]["noche_records_distintos_en_otros_campos"][:10]))
    r["principal"].pop("T", None)
    if a.salida:
        Path(a.salida).write_text(json.dumps({"excluir_dias": dias, "principal": r["principal"],
                                              "variantes": r["variantes"], "final": r["final"], "info": r["info"]},
                                             ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
