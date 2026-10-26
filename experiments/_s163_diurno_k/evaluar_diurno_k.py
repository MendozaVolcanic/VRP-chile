# -*- coding: utf-8 -*-
"""Evaluador del A/B diurno de VIIRS sobre K (tarea 1.32, D-10, issue #813). Implementa PREREGISTRO.md §4 a §6.

EL FENÓMENO. De día el infrarrojo medio suma luz solar reflejada y MIROVA, con umbrales altos, casi no alerta. La
réplica no mira el día. El brazo diurno enciende la rama diurna sobre K; la pregunta es si comete menos errores que
hoy según el criterio de victoria (docs/MISSION.md): ninguna protegida perdida y, bajo 1 MW, una alerta perdida y una
publicación de más en un negativo limpio pesan igual.

POR QUÉ ESTE EVALUADOR Y NO EL COMÚN SOLO. `scripts/evaluador_comun.py` descarta las pasadas diurnas al cargar (es
para A/B nocturnos) y su cobertura usa el control como vara, que de día no tiene records. Aquí se reusan sus piezas
(tabla por pasada, cobertura nocturna, clases de P2, prueba de signos D-45, placebos D-44) y se agrega lo diurno:
- el control se toma como «observado, no publica» en las pasadas diurnas que el brazo observó, sólo después de
  comprobar que no trae ningún record VIIRS diurno (I2);
- la cobertura diurna tiene vara externa: la tasa nocturna de producción sin record (I4, `sustrato_k.json`);
- la noche tiene que quedar idéntica record a record (I5).

Pruebas: test_evaluar_diurno_k.py (batería; salida roja en probar_salida_roja.txt) y mutaciones.json.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import statistics
import sys
from datetime import datetime
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
for _p in (str(ROOT), str(ROOT / "scripts"), str(AQUI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import clase_mirova as cm  # noqa: E402
import evaluador_comun as ec  # noqa: E402

REGLA_MINIMAS = "SN"                     # D-9: decide la regla SN
SENSORES_DIA = ("VIIRS375", "VIIRS750")  # la rama diurna es sólo VIIRS (#821)
SENSORES_NOCHE = ("VIIRS375", "VIIRS750", "MODIS")
ALFA = 0.05
MIN_BLOQUES_PLACEBO = 5                  # D-45: con 4 bloques o menos P2 da SIN SUSTRATO
SEMILLAS_C = tuple(range(161, 201))      # 40 semillas del placebo simétrico
# Verificador v2, V-N3: cada sorteo del placebo c es falso si da GANA o PIERDE, dos pruebas de una cola al 5 %, así que
# la tasa nominal por sorteo es de hasta 10 % (medida: 7,2 a 8,3 %). P(Bin(40; 0,10) >= 8) = 0,042: con 8 o más falla.
MAX_FALSOS_C = 7
# Verificador v3, V3-4: lo que lleva a adoptar es el lado GANA, y la suma deja pasar 7 GANA y 0 PIERDE. Tope propio
# para GANA: P(Bin(40; 0,05) >= 5) = 0,048, con 5 o más falla.
MAX_GANA_C = 4
FRACCION_A = 0.5
INVALIDO, INDECIDIBLE = "INVÁLIDO POR INSTRUMENTO", "INDECIDIBLE"
ADOPTAR, NO_ADOPTAR, SIN_CAMBIO = "ADOPTAR", "NO ADOPTAR", "SIN CAMBIO"
DECIDE, DECIDE_M4 = "DECIDE NICOLÁS", "DECIDE NICOLÁS CON M4"
OPCIONES_E = ("e-i", "e-ii")
FUENTES_TEST1 = ("test1", "test1_roi")

_COORDS = None


def coords():
    global _COORDS
    if _COORDS is None:
        import banco_paridad as bp
        _COORDS = bp._coords_por_volcan()
    return _COORDS


def es_dia_vol(vol, instante):
    """La regla del pipeline: elevación solar > 0 sobre el volcán a la hora (UTC) de la pasada."""
    from pipeline.store import _solar_elevation
    lat, lon = coords()[vol]
    return _solar_elevation(lat, lon, instante.replace(tzinfo=None)) > 0


# =========================================================================================== reglas puras (§6)
def veredicto_sensor(m, opcion):
    """§6.2. m: p2 (resultado de P2 diurno), neto, P (protegidas diurnas recuperadas), D (el brazo discrimina, §6.2),
    publica (el brazo publica alguna pasada diurna del sensor), Qd, Qn. Devuelve (veredicto, caso)."""
    if opcion not in OPCIONES_E:
        raise ValueError("opción del caso e %r: %s" % (opcion, OPCIONES_E))
    if m["p2"] == "GANA":
        return ADOPTAR, "a"
    con_beneficio = m["P"] >= 1 and m["D"]
    if m["neto"] <= 0:
        if con_beneficio:
            return ADOPTAR, "b"
        return (SIN_CAMBIO if not m["publica"] else NO_ADOPTAR), "c"
    if not con_beneficio:
        return NO_ADOPTAR, "d"
    if opcion == "e-i" and m["Qd"] <= m["Qn"]:
        return ADOPTAR, "e-i"
    return DECIDE_M4, opcion


def discrimina(recuperadas, alertas_obs, qd):
    """§6.2, prueba D: ¿recupera más alertas diurnas de MIROVA que las que daría publicar al azar con la misma
    probabilidad con que publica en negativos diurnos limpios? Binomial exacta de una cola, P(X >= recuperadas) < 0,05.
    Es la pregunta de G1 de la adenda (si el brazo separa alertas de negativos) sin barajado."""
    if recuperadas <= 0 or alertas_obs <= 0:
        return False
    if qd <= 0:
        return True
    from scipy.stats import binom
    return bool(binom.sf(recuperadas - 1, alertas_obs, qd) < ALFA)


def veredicto_global(comp, r1, por_sensor):
    """§6.3. comp: {"invalido": [...], "indecidible": [...]}; r1: protegidas que el control publica y el brazo no;
    por_sensor: {sensor: veredicto}."""
    if comp["invalido"]:
        return INVALIDO
    if comp["indecidible"]:
        return INDECIDIBLE
    if r1:
        # Con I5 en verde la noche es idéntica y de día el control no publica: una pérdida aquí es un defecto del
        # evaluador, no del brazo (PREREGISTRO §6.1).
        return INVALIDO
    vs = set(por_sensor.values())
    if DECIDE_M4 in vs:
        return DECIDE_M4
    if ADOPTAR in vs and NO_ADOPTAR in vs:
        return DECIDE
    if por_sensor.get("VIIRS750") == ADOPTAR:
        # Verificador v2, V-N7: para VIIRS 750 manda el código de MIROVA (docs/MISSION.md, decisión del 2026-10-21), y
        # de día su código usa K1 -0,5 y descarta la escena con reflejo bajo 12°; la rama diurna usa la Tabla 1 (-0,6) y
        # no filtra. Un ADOPTAR de VIIRS 750 medido con otra configuración no se adopta solo.
        return DECIDE
    if ADOPTAR in vs:
        return ADOPTAR
    return NO_ADOPTAR


def veredicto_final(principal, variantes):
    """§6.4. Si el principal es ADOPTAR o NO ADOPTAR y una variante da otro veredicto global, decide Nicolás."""
    if principal in (ADOPTAR, NO_ADOPTAR):
        distintas = {k: v for k, v in variantes.items() if v != principal}
        if distintas:
            return DECIDE, "el veredicto cambia en: " + ", ".join("%s (%s)" % (k, v) for k, v in sorted(distintas.items()))
    return principal, ""


def juzgar_i6(res_a, bloques_a, falsos_c, gana_c=0):
    """§5 I6: placebo a tiene que dar GANA con 5 bloques o más; el simétrico no puede dar 8 falsos (GANA o PIERDE) o
    más de 40, ni 5 GANA o más."""
    prob = []
    if bloques_a >= MIN_BLOQUES_PLACEBO and res_a != "GANA":
        prob.append("placebo a: %s con %d bloques (tenía que dar GANA)" % (res_a, bloques_a))
    if falsos_c > MAX_FALSOS_C:
        prob.append("placebo c: %d de %d con GANA o PIERDE (máximo %d)" % (falsos_c, len(SEMILLAS_C), MAX_FALSOS_C))
    if gana_c > MAX_GANA_C:
        prob.append("placebo c: %d de %d con GANA (máximo %d)" % (gana_c, len(SEMILLAS_C), MAX_GANA_C))
    return prob


def cobertura_diurna_excede(x, n, p_sup):
    """§5 I4c: P(Bin(n, p_sup) >= x) < 0,05."""
    if x <= 0 or n <= 0:
        return False
    from scipy.stats import binom
    return bool(binom.sf(x - 1, n, p_sup) < ALFA)


# =========================================================================================== evaluación de una tabla
def _sensor_dia(f, s):
    return f["es_dia"] and f["pasada"].sensor_bucket == s


def compuerta_i1(recs_por_lado, sha):
    prob = []
    for lado, recs in recs_por_lado.items():
        t1 = [r for r in recs if r.get("t1") is True or r.get("fuente_hotspot") in FUENTES_TEST1]
        otro = [r for r in recs if r.get("sha") != sha]
        if t1:
            prob.append("I1 %s: %d records con el Test 1 (K no lo tiene)" % (lado, len(t1)))
        if otro:
            prob.append("I1 %s: %d records con codigo_sha distinto del tag %s" % (lado, len(otro), sha[:12]))
    return prob


def compuerta_i2(recs_c, recs_b, pasadas, ventanas):
    prob = []
    dia_c = [r for r in recs_c if r["b"] in SENSORES_DIA and r["es_dia"]]
    if dia_c:
        prob.append("I2: el control trae %d records VIIRS diurnos (tendría que traer cero)" % len(dia_c))
    noche_diag = [r for r in recs_b if not r["es_dia"] and r.get("diag_dia")]
    if noche_diag:
        prob.append("I2: %d records nocturnos del brazo con umbrales diurnos" % len(noche_diag))
    for w, desde, hasta in ventanas:
        for s in SENSORES_DIA:
            hay_mirova = any(p.sensor_bucket == s and p._es_dia and desde <= p.instante.strftime("%Y-%m-%d") <= hasta
                             for p in pasadas)
            hay_b = any(r["b"] == s and r["es_dia"] and r.get("diag_dia")
                        and desde <= r["dt"].strftime("%Y-%m-%d") <= hasta for r in recs_b)
            if hay_mirova and not hay_b:
                prob.append("I2 %s %s: MIROVA tiene pasadas diurnas y el brazo ningún record con umbrales diurnos"
                            % (w, s))
    return prob


def compuerta_i4(T, recs_b, brazo, p_sup):
    """Cobertura diurna contra la referencia. Devuelve (problemas, detalle por sensor)."""
    prob, det = [], {}
    dia_b = collections.Counter((r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d")) for r in recs_b if r["es_dia"])
    for s in SENSORES_DIA:
        filas = [f for f in T if _sensor_dia(f, s)]
        sin = [f for f in filas if f["rec"][brazo] is None]
        for f in sin:
            # verificador V10: toda alerta diurna (protegida o bajo 1 MW) se vigila una por una; con 10 alertas bajo
            # 1 MW en VIIRS 375, perder unas pocas achicaría D y el neto en silencio.
            if f["pasada"].estado == "alerta":
                prob.append("I4a %s: alerta diurna sin record del brazo (MIROVA %s MW)" % (f["clave"],
                                                                                      f["pasada"].vrp_mw))
        vacios = sorted({(f["pasada"].volcano, s, f["dia"]) for f in filas
                         if dia_b[(f["pasada"].volcano, s, f["dia"])] == 0})
        for v in vacios:
            prob.append("I4b %s|%s|%s: pasadas diurnas de MIROVA y ningún record diurno del brazo" % v)
        excede = cobertura_diurna_excede(len(sin), len(filas), p_sup[s])
        if excede:
            prob.append("I4c %s: %d de %d pasadas diurnas de MIROVA sin record del brazo (p_sup %.4f)"
                        % (s, len(sin), len(filas), p_sup[s]))
        det[s] = {"pasadas_diurnas": len(filas), "sin_record": len(sin), "p_sup": p_sup[s]}
    return prob, det


def compuerta_i5(recs_c, recs_b):
    """Noche idéntica record a record: misma publicación y misma magnitud publicada."""
    def idx(recs):
        return {(r["vol"], r["b"], r["dt"]): r for r in recs if not r["es_dia"]}
    ic, ib = idx(recs_c), idx(recs_b)
    distintos = []
    for k in sorted(set(ic) & set(ib)):
        rc, rb = ic[k], ib[k]
        if bool(rc["pub"]) != bool(rb["pub"]) or (rc["pub"] and round(float(rc["disp"] or 0), 6)
                                                   != round(float(rb["disp"] or 0), 6)):
            distintos.append("I5 %s|%s|%s: control %s %.4f, brazo %s %.4f" % (
                k[0], k[1], k[2].strftime("%Y-%m-%d %H:%M"), rc["pub"], rc["disp"] or 0, rb["pub"], rb["disp"] or 0))
    solo = {"solo_control": len(set(ic) - set(ib)), "solo_brazo": len(set(ib) - set(ic))}
    # verificador V6: «noches intactas» exige también los mismos records nocturnos en los dos brazos.
    for lado, n in solo.items():
        if n:
            distintos.append("I5 %d records nocturnos sólo en el %s" % (n, lado.split("_")[1]))
    return distintos, solo


def banderas_por_periodo(T, otra_como_negativo=False):
    """«Día con alerta» y «día con FALSO_POSITIVO» por periodo (verificador V2 y V7): una pasada diurna mira sólo las
    pasadas DIURNAS de su volcán, sensor y día UTC, y una nocturna sólo las nocturnas. De día MIROVA usa otros umbrales
    y su pasada es una mirada aparte: una alerta de la madrugada no hace que su RUTINA del mediodía deje de ser un
    silencio de MIROVA, y un día al que a la tabla le falta la noche no cambia la clase de sus pasadas diurnas. De noche
    es la misma definición del evaluador común, que sólo ve pasadas nocturnas."""
    def k(f):
        return (f["pasada"].volcano, f["pasada"].sensor_bucket, f["dia"], f["es_dia"])
    alerta = {k(f) for f in T if f["pasada"].estado == "alerta"}
    fp = {k(f) for f in T if f["pasada"].estado == "fp"}
    for f in T:
        f["noche_con_alerta"], f["noche_con_fp"] = k(f) in alerta, k(f) in fp
        if otra_como_negativo and f["es_dia"]:
            # Verificador v2, V-N4 (variante d del §6.4): toda RUTINA diurna de la tabla cuenta como negativo, aunque su
            # periodo tenga una alerta o un FALSO_POSITIVO de MIROVA. Así lo que el brazo publique en «otra» pesa.
            f["noche_con_alerta"] = f["noche_con_fp"] = False


def huellas_nocturnas_distintas(recs_c, recs_b):
    """Verificador v2, V-N5, INFORMATIVO: records nocturnos presentes en los dos brazos cuyo contenido difiere en algún
    campo fuera de los volátiles y de los `diag_*` (ver huella_record), aunque publiquen igual. La G3 de la adenda
    pedía el record entero; aquí decide la publicación y la magnitud (I5) porque es lo único que lee el criterio, y un
    desempate que depende de la CPU (S152, D-16, D-22) cambia campos que no deciden. Se listan para que se vean."""
    def idx(recs):
        return {(r["vol"], r["b"], r["dt"]): r.get("huella") for r in recs if not r["es_dia"]}
    ic, ib = idx(recs_c), idx(recs_b)
    return ["%s|%s|%s" % (k[0], k[1], k[2].strftime("%Y-%m-%d %H:%M")) for k in sorted(set(ic) & set(ib))
            if ic[k] is not None and ib[k] is not None and ic[k] != ib[k]]


def completar_control_diurno(T, control, brazo):
    """El control no mira el día: en cada pasada diurna VIIRS que el brazo observó, «observado, no publica»."""
    for f in T:
        if f["es_dia"] and f["pasada"].sensor_bucket in SENSORES_DIA and f["rec"][brazo] is not None \
                and f["rec"][control] is None:
            f["rec"][control] = {"pub": False, "disp": 0.0, "sintetico": True}
            f["cob"][control] = ec.OBSERVADO


def elevacion(vol, instante):
    from pipeline.store import _solar_elevation
    lat, lon = coords()[vol]
    return _solar_elevation(lat, lon, instante.replace(tzinfo=None))


def angulo_reflejo(r):
    """Ángulo de reflejo especular, fórmula del README del código de MIROVA (OSF zm62w, l. 32 a 36), con los ángulos
    que el record guarda en el punto reportado (process_viirs.py, observation_geometry). None si falta alguno."""
    import math
    v = [r.get(k) for k in ("sz", "sa", "soz", "soa")]
    if any(x is None for x in v):
        return None
    sz, sa, soz, soa = (math.radians(float(x)) for x in v)
    c = math.cos(sz) * math.cos(soz) - math.sin(sz) * math.sin(soz) * math.cos(soa - sa)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


UMBRAL_REFLEJO_GRADOS = 12.0       # código de MIROVA de VIIRS 750, l. 87 (informativo aquí, §7)


def aplicar_filtro_reflejo(recs_b):
    """Variante INFORMATIVA (§7): copia de los records del brazo en que las publicaciones diurnas con ángulo de
    reflejo menor que 12° quedan sin publicar, como hace MIROVA con la escena entera. No cambia la entrada."""
    out = []
    for r in recs_b:
        g = angulo_reflejo(r) if r.get("es_dia") else None
        out.append(dict(r, pub=False, disp=0.0) if (r.get("pub") and g is not None and g < UMBRAL_REFLEJO_GRADOS)
                   else r)
    return out


def metricas_sensor(T, recs_b, control, brazo, s, ventanas=()):
    excl = lambda f, s=s: not _sensor_dia(f, s)  # noqa: E731
    contrib = ec.contribuciones_p2(T, control, brazo, excluir=excl)
    p2, det = ec.decidir_p2(contrib)
    obs_d = [f for f in T if _sensor_dia(f, s) and f["cob"][brazo] == ec.OBSERVADO]
    prot = [f for f in obs_d if f["protegida"]]
    neg_d = [f for f in obs_d if ec.clase_p2(f) == "negativo"]
    otra = [f for f in obs_d if ec.clase_p2(f) == "otra" and not f["protegida"]]
    amb = [f for f in obs_d if ec.clase_p2(f) == "alerta_mb"]
    neg_n = [f for f in T if not f["es_dia"] and f["pasada"].sensor_bucket == s
             and f["cob"][control] == ec.OBSERVADO and ec.clase_p2(f) == "negativo"]
    pub = lambda f, lado: ec._pub(f["rec"][lado])  # noqa: E731
    P = sum(pub(f, brazo) for f in prot)
    recuperadas = [f for f in prot + amb if pub(f, brazo) and f["pasada"].vrp_mw]
    razones = [ec._disp(f["rec"][brazo]) / f["pasada"].vrp_mw for f in recuperadas]
    neg_pub = [f for f in neg_d if pub(f, brazo)]
    qd = len(neg_pub) / len(neg_d) if neg_d else 0.0
    rec_alertas = sum(pub(f, brazo) for f in prot + amb)
    return {
        "D": discrimina(rec_alertas, len(prot) + len(amb), qd), "alertas_recuperadas": rec_alertas,
        "alertas_obs": len(prot) + len(amb),
        "p2": p2, "neto": det["neto"], "p2_det": det,
        "P": P, "P_obs": len(prot),
        "amb_recuperadas": sum(pub(f, brazo) for f in amb), "amb_obs": len(amb),
        "neg_pub": len(neg_pub), "neg_obs": len(neg_d),
        "Qd": qd,
        "Qn": sum(pub(f, control) for f in neg_n) / len(neg_n) if neg_n else 0.0,
        "Qn_den": len(neg_n),
        "neg_1mw": sum(1 for f in neg_pub if ec._disp(f["rec"][brazo]) >= cm.UMBRAL_PROTEGIDA_MW),
        "pub_otra": sum(pub(f, brazo) for f in otra),
        "publica": any(r["pub"] for r in recs_b if r["es_dia"] and r["b"] == s),
        "razon_mag_mediana": statistics.median(razones) if razones else None,
        "protegidas_recuperadas": [f["clave"] for f in prot if pub(f, brazo)],
        "protegidas_no_publicadas": [f["clave"] for f in prot if not pub(f, brazo)],
        "negativos_publicados": [f["clave"] for f in neg_pub],
        # informativo (verificador V3 y V8)
        "P_1mw": sum(1 for f in prot if pub(f, brazo) and ec._disp(f["rec"][brazo]) >= cm.UMBRAL_PROTEGIDA_MW),
        "neg_pub_por_elevacion": dict(collections.Counter(
            ("0-30" if e <= 30 else "30-60" if e <= 60 else ">60")
            for e in (elevacion(f["pasada"].volcano, f["pasada"].instante) for f in neg_pub))),
        "por_ventana": {w: {"P": sum(pub(f, brazo) for f in prot if d0 <= f["dia"] <= d1),
                            "P_obs": sum(1 for f in prot if d0 <= f["dia"] <= d1),
                            "amb": sum(pub(f, brazo) for f in amb if d0 <= f["dia"] <= d1),
                            "amb_obs": sum(1 for f in amb if d0 <= f["dia"] <= d1),
                            "neg_pub": sum(1 for f in neg_pub if d0 <= f["dia"] <= d1),
                            "neg_obs": sum(1 for f in neg_d if d0 <= f["dia"] <= d1)}
                        for w, d0, d1 in ventanas},
    }


def compuerta_i6(T, brazo, s):
    excl = lambda f, s=s: not _sensor_dia(f, s)  # noqa: E731
    res_a, det_a = ec.placebo_p2(T, brazo, "a", FRACCION_A, 161, excluir=excl)
    res_b, det_b = ec.placebo_p2(T, brazo, "b", FRACCION_A, 161, excluir=excl)
    falsos = gana = 0
    for sem in SEMILLAS_C:
        res_c, _ = ec.placebo_p2(T, brazo, "c", 1.0, sem, excluir=excl)
        falsos += res_c in ("GANA", "PIERDE")
        gana += res_c == "GANA"
    return {"a": {"resultado": res_a, "bloques": det_a["B"], "tocadas": det_a["tocadas"]},
            "b": {"resultado": res_b, "bloques": det_b["B"], "tocadas": det_b["tocadas"]},
            "c_falsos": falsos, "c_gana": gana, "problemas": juzgar_i6(res_a, det_a["B"], falsos, gana)}


def r1_perdidas(T, control, brazo):
    return [f["clave"] for f in T if f["protegida"] and ec.observada_en(f, control, brazo)
            and ec._pub(f["rec"][control]) and not ec._pub(f["rec"][brazo])]


def evaluar(pasadas, recs_por_lado, control, brazo, opcion, p_sup, sha, ventanas, excluir_claves=(),
            excluir_dias=(), p_sup_override=None, problemas_log=(), otra_como_negativo=False):
    """Una evaluación completa (§5 y §6) sobre pasadas de MIROVA y records ya cargados (con `pub`, `disp`, `es_dia`,
    `t1`, `fuente_hotspot`, `sha`, `diag_dia`). `excluir_claves` y `excluir_dias` arman las variantes del §6.4."""
    if not re.fullmatch(r"[0-9a-f]{40}", str(sha)):
        raise ValueError("sha del tag: hacen falta los 40 caracteres de git rev-parse <tag>^{commit}")
    if opcion not in OPCIONES_E:
        raise ValueError("opción del caso e %r: %s" % (opcion, OPCIONES_E))
    p_sup = dict(p_sup_override or p_sup)
    excl_d, excl_k = set(excluir_dias), set(excluir_claves)
    pas = [p for p in pasadas if p.instante.strftime("%Y-%m-%d") not in excl_d]
    if otra_como_negativo:
        # Verificador v3, V3-1: en la variante (d) también las pasadas FALSO_POSITIVO diurnas de la tabla cuentan como
        # RUTINA (MIROVA no alertó en el radio), así que lo que el brazo publique ahí pesa como publicación de más.
        pas = [p._replace(estado="rutina") if (p.estado == "fp" and p.fuente == "CONS" and p.sensor_bucket in SENSORES_DIA
                                               and es_dia_vol(p.volcano, p.instante)) else p for p in pas]
    recs = {lado: [r for r in rs if r["dt"].strftime("%Y-%m-%d") not in excl_d] for lado, rs in recs_por_lado.items()}
    rc, rb = recs[control], recs[brazo]
    marcadas = [_Marcada(p, es_dia_vol(p.volcano, p.instante)) for p in pas]
    marcadas_eval = [m for m in marcadas if ec.clave(m._p) not in excl_k]
    comp = {"invalido": list(problemas_log), "indecidible": []}
    comp["invalido"] += compuerta_i1(recs, sha)
    comp["invalido"] += compuerta_i2(rc, rb, marcadas_eval, ventanas)
    T = ec.tabla_por_pasada(pas, recs, control)
    for f, m in zip(T, marcadas):
        f["es_dia"] = m._es_dia
    banderas_por_periodo(T, otra_como_negativo)
    # verificador V5: las pasadas excluidas salen DESPUÉS de marcar los días con alerta, así no vuelven negativos a
    # sus vecinas.
    T = [f for f in T if f["clave"] not in excl_k]
    Tn = [f for f in T if not f["es_dia"] or f["pasada"].sensor_bucket not in SENSORES_DIA]
    # Verificador v2, V-N6: la cobertura nocturna cuenta sólo records nocturnos; con los de día, un record diurno del
    # brazo tapaba un día sin ningún record nocturno.
    cob_n = ec.cobertura(Tn, {lado: [r for r in rs if not r["es_dia"]] for lado, rs in recs.items()}, control)
    if cob_n["veredicto"] != ec.COBERTURA_OK:
        comp["invalido"].append("I3: cobertura nocturna %s (protegidas %d, días vacíos %d, control sin protegida %d)" % (
            cob_n["veredicto"], len(cob_n["protegidas_sin_record_en_brazos"]),
            len(cob_n["dias_con_pasadas_de_mirova_y_sin_records"]), len(cob_n["control_sin_protegida_que_un_brazo_tiene"])))
    p4, det4 = compuerta_i4(T, rb, brazo, p_sup)
    comp["invalido"] += p4
    i5, solo = compuerta_i5(rc, rb)
    comp["indecidible"] += i5
    huellas = huellas_nocturnas_distintas(rc, rb)
    if not any("I2: el control" in x for x in comp["invalido"]):
        completar_control_diurno(T, control, brazo)
    por_sensor, i6 = {}, {}
    for s in SENSORES_DIA:
        m = metricas_sensor(T, rb, control, brazo, s, ventanas)
        m["veredicto"], m["caso"] = veredicto_sensor(m, opcion)
        por_sensor[s] = m
        i6[s] = compuerta_i6(T, brazo, s)
        comp["indecidible"] += ["I6 %s: %s" % (s, x) for x in i6[s]["problemas"]]
    r1 = r1_perdidas(T, control, brazo)
    glob = veredicto_global(comp, r1, {s: m["veredicto"] for s, m in por_sensor.items()})
    return {"global": glob, "compuertas": comp, "por_sensor": por_sensor, "i6": i6, "r1": r1, "T": T,
            "cobertura_nocturna": cob_n, "cobertura_diurna": det4, "noche_solo_un_lado": solo,
            "noche_records_distintos_en_otros_campos": huellas,
            "pasadas": len(T), "pasadas_diurnas_viirs": sum(1 for f in T if f["es_dia"]
                                                              and f["pasada"].sensor_bucket in SENSORES_DIA)}


class _Marcada:
    """Una pasada con su marca de día, para las compuertas que trabajan antes de la tabla."""
    __slots__ = ("_p", "_es_dia")

    def __init__(self, p, es_dia):
        self._p, self._es_dia = p, es_dia

    def __getattr__(self, k):
        return getattr(self._p, k)


# =========================================================================================== carga real
def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


CAMPOS_VOLATILES = ("updated", "processed_utc", "first_processed_utc", "regimen")


def huella_record(r):
    """sha1 del record sin los campos volátiles ni los diagnósticos `diag_*` (para la comparación informativa de la
    noche, V-N5). Los `diag_*` quedan fuera porque no deciden nada y algunos (diag_mu_deti, diag_sd_deti) difieren entre
    dos corridas del mismo código por punto flotante: en la prueba de humo sobre C0 lo hacían en 64 a 67 de 71 records
    nocturnos de Chaitén y tapaban cualquier diferencia de posición o de cúmulo."""
    return hashlib.sha1(json.dumps({k: v for k, v in r.items() if k not in CAMPOS_VOLATILES
                                    and not k.startswith("diag_")}, sort_keys=True,
                                   default=str).encode("utf-8")).hexdigest()


def cargar_brazo(raices, brazo, ventanas, inner):
    """Records de los dos sensores VIIRS y de MODIS, de día y de noche, con el predicado del tablero (node)."""
    import banco_paridad as bp
    recs, casos = [], []
    desde, hasta = min(w[1] for w in ventanas), max(w[2] for w in ventanas)
    vistos = set()
    for raiz in raices:
        for vol in bp.VOLS:
            ruta = Path(raiz) / brazo / ("%s.json" % vol)
            if not ruta.exists():
                continue
            for r in json.loads(ruta.read_text(encoding="utf-8"))["records"]:
                b = bp.bucket(r.get("sensor"))
                tt = r.get("datetime_utc", "")
                if b not in SENSORES_NOCHE or not (desde <= tt[:10] <= hasta):
                    continue
                if not any(w[1] <= tt[:10] <= w[2] for w in ventanas):
                    continue
                try:
                    dt = datetime.strptime(tt, "%Y-%m-%d %H:%M")
                except ValueError:
                    continue
                k = (vol, r.get("sensor"), tt)
                if k in vistos:
                    continue
                vistos.add(k)
                dia = es_dia_vol(vol, dt)
                if b == "MODIS" and dia:
                    continue          # MODIS diurno sigue apagado en los dos brazos (no entra a nada)
                recs.append({"vol": vol, "b": b, "dt": dt, "es_dia": dia, "t1": r.get("triggered_test1"),
                             "huella": huella_record(r),
                             "fuente_hotspot": r.get("final_hotspot_source"),
                             "sha": (r.get("regimen") or {}).get("codigo_sha"),
                             "diag_dia": r.get("diag_umbrales_diurnos"),
                             "sz": r.get("sensor_zenith_deg"), "sa": r.get("sensor_azimuth_deg"),
                             "soz": r.get("solar_zenith_deg"), "soa": r.get("solar_azimuth_deg")})
                slim = {kk: r.get(kk) for kk in bp.CAMPOS_JS if kk != "anomaly_pixels"}
                if r.get("f5_core_vrp_mw") is None:
                    slim["anomaly_pixels"] = [{kk: px.get(kk) for kk in ("lat", "lon", "vrp_mw", "bt_k")}
                                              for px in (r.get("anomaly_pixels") or [])]
                casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos) if casos else []
    for rr, p in zip(recs, pred):
        rr["disp"], rr["pub"] = p[3], bool(p[4])
    return recs


def problemas_de_logs(raices, brazos, control):
    """I1a: la línea FLAGS_BRAZO de cada job, cuando la raíz trae logs/."""
    import banco_paridad as bp
    prob = []
    declarado = {"ENABLE_TEST1_PATH": False, "ENABLE_TESTS_23_PROSE_BRANCH": True, "ENABLE_MODIS_B22_PRIMARY": True,
                 "ENABLE_DAYTIME_MODIS": False}
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
                donde = "%s %s (%s)" % (brazo, vol, Path(raiz).name)
                if fl is None:
                    prob.append("I1a %s: sin línea FLAGS_BRAZO" % donde)
                    continue
                esperado = dict(declarado, ENABLE_DAYTIME_VIIRS=(brazo != control), PROFILE_NAME=brazo,
                                DATA_SUBDIR=brazo)
                for k, v in esperado.items():
                    if fl.get(k) != v:
                        prob.append("I1a %s: %s=%s, declarado %s" % (donde, k, fl.get(k), v))
    return prob


def p_sup_de_vara(vara):
    """§5 I4c: cota superior de Clopper-Pearson al 95 % (una cola) de la tasa nocturna de producción sin record."""
    from scipy.stats import beta
    return {s: float(beta.ppf(1 - ALFA, vara[s]["sin_record_produccion"] + 1,
                              vara[s]["pasadas_nocturnas"] - vara[s]["sin_record_produccion"]))
            for s in SENSORES_DIA}


def pasadas_de(filas, canal, ventanas, vols=None, regla=REGLA_MINIMAS, umbral=cm.UMBRAL_MINIMA_MW):
    """Pasadas de MIROVA de las ventanas, VIIRS de día y de noche y MODIS sólo de noche."""
    out = []
    for p in cm.resumir_pasadas(filas, canal=canal, regla_minimas=regla, umbral_minima_mw=umbral):
        d = p.instante.strftime("%Y-%m-%d")
        if p.volcano not in coords() or p.sensor_bucket not in SENSORES_NOCHE:
            continue
        if vols and p.volcano not in vols:
            continue
        if not any(w[1] <= d <= w[2] for w in ventanas):
            continue
        if p.sensor_bucket == "MODIS" and es_dia_vol(p.volcano, p.instante):
            continue
        out.append(p)
    return out


def evaluar_completo(filas, recs, control, brazo, opcion, p_sup, sha, ventanas, problemas_log=(), filas_1_13=()):
    """El veredicto del §6 con su robustez (§6.4) y lo informativo (§6.4 y §7), a partir de las filas de la referencia
    y los records ya cargados. Separado de main() para que la batería lo pruebe (verificador v2, V-N2)."""
    kw = dict(opcion=opcion, p_sup=p_sup, sha=sha, ventanas=ventanas, problemas_log=problemas_log)
    pas_u = pasadas_de(filas, "union", ventanas)
    principal = evaluar(pas_u, recs, control, brazo, **kw)
    dias_w2 = {d.strftime("%Y-%m-%d") for w, d0, d1 in ventanas if w == "W2" for d in _dias(d0, d1)}
    reflejo, sin_pareo = claves_reflejo(pas_u, filas_1_13)
    sin_pareo = [x for x in sin_pareo if any(w[1] <= x.split("|")[2][:10] <= w[2] for w in ventanas)]
    variantes = {"tabla": evaluar(pasadas_de(filas, "tabla", ventanas), recs, control, brazo, **kw)["global"],
                 "sin_W2": evaluar(pas_u, recs, control, brazo, excluir_dias=dias_w2, **kw)["global"],
                 "sin_reflejo": evaluar(pas_u, recs, control, brazo, excluir_claves=reflejo, **kw)["global"],
                 "otra_como_negativo": evaluar(pas_u, recs, control, brazo, otra_como_negativo=True, **kw)["global"]}
    final, motivo = veredicto_final(principal["global"], variantes)
    info = {"minimas_SE": evaluar(pasadas_de(filas, "union", ventanas, regla="SE"), recs, control, brazo,
                                  **kw)["global"],
            "minimas_original": evaluar(pasadas_de(filas, "union", ventanas, regla="original"), recs, control, brazo,
                                        **kw)["global"],
            "minimas_SN_0,04": evaluar(pasadas_de(filas, "union", ventanas, umbral=cm.UMBRAL_MINIMA_VARIANTE_MW), recs,
                                       control, brazo, **kw)["global"]}
    rb12 = aplicar_filtro_reflejo(recs[brazo])
    con12 = evaluar(pas_u, {control: recs[control], brazo: rb12}, control, brazo, **kw)
    info["con_filtro_reflejo_12"] = con12["global"]
    reflejo12 = {"apagadas": sum(1 for r0, r1 in zip(recs[brazo], rb12) if r0["pub"] and not r1["pub"]),
                 "sin_angulos": sum(1 for r in recs[brazo] if r["es_dia"] and r["pub"] and angulo_reflejo(r) is None),
                 "por_sensor": con12["por_sensor"]}
    return {"principal": principal, "variantes": variantes, "final": final, "motivo": motivo, "info": info,
            "reflejo": reflejo, "reflejo_sin_pareo": sin_pareo, "reflejo12": reflejo12}


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Evaluador del A/B diurno sobre K (PREREGISTRO.md)")
    ap.add_argument("--raiz", action="append", required=True, help="raíz de una corrida (W2 a W6), repetible")
    ap.add_argument("--w1", action="append", default=[], help="raíz de W1 (se informa aparte)")
    ap.add_argument("--brazos", default="_s154_ab_diurno_k_control,_s154_ab_diurno_k_on")
    ap.add_argument("--ref", required=True, help="carpeta con los 4 CSV congelados (congelar_referencia.py)")
    ap.add_argument("--sustrato", default=str(AQUI / "sustrato_k.json"))
    ap.add_argument("--sha-codigo", required=True)
    ap.add_argument("--opcion-e", required=True, choices=OPCIONES_E)
    ap.add_argument("--salida", default=None)
    ap.add_argument("--recorte", default=None, help="DESDE,HASTA: SÓLO para la prueba de humo; la evaluación que decide "
                                                     "usa W2 a W6 enteras (PREREGISTRO §8)")
    a = ap.parse_args(argv)
    import banco_paridad as bp
    import sustrato_k as sk
    control, brazo = a.brazos.split(",")
    sus = json.loads(Path(a.sustrato).read_text(encoding="utf-8"))
    ref = Path(a.ref)
    distintos = [n for n in sk.ARCHIVOS_REF if sha256(ref / n) != sus["sha256"][n]]
    if distintos:
        print("REFERENCIA DISTINTA DE LA DEL PRE-REGISTRO (sha256): %s. No se decide." % distintos)
        return 3
    filas = sk.cargar_ref(ref)
    p_sup = p_sup_de_vara(sus["vara_cobertura_nocturna_produccion"])
    inner = bp.inner_desde_html()
    ventanas = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
    if a.recorte:
        d0, d1 = a.recorte.split(",")
        ventanas = [(w, max(x, d0), min(y, d1)) for w, x, y in ventanas if max(x, d0) <= min(y, d1)]
        print("RECORTE DE PRUEBA %s a %s: esto NO es la evaluación que decide" % (d0, d1))
    recs = {control: cargar_brazo(a.raiz, control, ventanas, inner),
            brazo: cargar_brazo(a.raiz, brazo, ventanas, inner)}
    logs = problemas_de_logs(a.raiz, (control, brazo), control)
    r = evaluar_completo(filas, recs, control, brazo, a.opcion_e, p_sup, a.sha_codigo, ventanas, logs, _filas_1_13())
    principal, variantes, final, motivo = r["principal"], r["variantes"], r["final"], r["motivo"]
    print("reflejo probable (1.13): %d pasadas; filas del estudio dentro de las ventanas sin pasada: %d %s"
          % (len(r["reflejo"]), len(r["reflejo_sin_pareo"]), r["reflejo_sin_pareo"][:5]))
    imprimir(principal, variantes, final, motivo, a.opcion_e)
    print()
    print("INFORMATIVO (no decide): %s" % r["info"])
    print("  ¿alguna variante de mínimas cambia el veredicto principal (%s)? %s"
          % (principal["global"], {k: v != principal["global"] for k, v in r["info"].items()}))
    print("filtro de reflejo de 12°: apaga %d publicaciones diurnas del brazo; %d publicaciones diurnas sin ángulos"
          % (r["reflejo12"]["apagadas"], r["reflejo12"]["sin_angulos"]))
    for s in SENSORES_DIA:
        m12 = r["reflejo12"]["por_sensor"][s]
        print("  con filtro %s: %s (caso %s), negativos %d de %d, protegidas %d de %d" % (
            s, m12["veredicto"], m12["caso"], m12["neg_pub"], m12["neg_obs"], m12["P"], m12["P_obs"]))
        print("  %s desproporción (1.13 a) sobre lo nuestro): %s" % (s, desproporcion(recs[brazo], s)))
    print("noche, records en los dos brazos con otros campos distintos (informativo, V-N5): %d %s"
          % (len(principal["noche_records_distintos_en_otros_campos"]),
             principal["noche_records_distintos_en_otros_campos"][:10]))

    def pasadas(canal, vent, vols=None):
        return pasadas_de(filas, canal, vent, vols)
    if a.w1:
        w1 = next(w for w in sk.VENTANAS if w[0] == "W1")
        v1 = [(w1[0], w1[1], w1[2])]
        r1w = {control: cargar_brazo(a.w1, control, v1, inner), brazo: cargar_brazo(a.w1, brazo, v1, inner)}
        rw = evaluar(pasadas("tabla", v1, w1[3]), r1w, control, brazo, opcion=a.opcion_e, p_sup=p_sup,
                     sha=a.sha_codigo, ventanas=v1, problemas_log=problemas_de_logs(a.w1, (control, brazo), control))
        print()
        print("--- W1 (Láscar, sólo la tabla, A119): INFORMATIVA, no entra al veredicto ---")
        imprimir(rw, {}, rw["global"], "", a.opcion_e)
    principal.pop("T", None)
    if a.salida:
        Path(a.salida).write_text(json.dumps({"principal": principal, "variantes": variantes, "final": final,
                                              "motivo": motivo}, ensure_ascii=False, indent=1, default=str),
                                  encoding="utf-8")
    return 0


def desproporcion(recs_b, s, ventana_h=72, umbral=3.16):
    """Instrumento a) del estudio 1.13 sobre las publicaciones diurnas del brazo: magnitud diurna contra la mayor
    publicación nocturna del brazo, mismo volcán y sensor, a ±72 h; desproporcionada sobre T = 3,16, aislada si no
    hay ninguna nocturna. Informativo (§7)."""
    from datetime import timedelta
    noc = collections.defaultdict(list)
    for r in recs_b:
        if r["b"] == s and not r["es_dia"] and r["pub"] and (r["disp"] or 0) > 0:
            noc[r["vol"]].append((r["dt"], r["disp"]))
    c = collections.Counter()
    for r in recs_b:
        if r["b"] != s or not r["es_dia"] or not r["pub"]:
            continue
        vec = [d for t, d in noc[r["vol"]] if abs(t - r["dt"]) <= timedelta(hours=ventana_h)]
        if not vec:
            c["aislada"] += 1
        elif (r["disp"] or 0) / max(vec) > umbral:
            c["desproporcionada"] += 1
        else:
            c["consistente"] += 1
    return dict(c)


def _dias(desde, hasta):
    from datetime import timedelta
    d0, d1 = datetime.strptime(desde, "%Y-%m-%d"), datetime.strptime(hasta, "%Y-%m-%d")
    while d0 <= d1:
        yield d0
        d0 += timedelta(days=1)


def claves_reflejo(pasadas, filas_1_13):
    """Pasadas de MIROVA que son protegidas diurnas de reflejo probable según el estudio 1.13 (clase desproporcionada
    o aislada), pareadas por volcán, sensor y ±120 s (la fila del estudio puede no ser la primera de su pasada).
    Devuelve (claves, filas del estudio que no encontraron pasada)."""
    from datetime import timedelta
    por_vs = collections.defaultdict(list)
    for p in pasadas:
        por_vs[(p.volcano, p.sensor_bucket)].append(p)
    out, sin = set(), []
    for f in filas_1_13:
        if f.get("clase") not in ("desproporcionada", "aislada"):
            continue
        t0 = datetime.strptime(f["fecha_utc"], "%Y-%m-%d %H:%M:%S")
        cand = [p for p in por_vs.get((f["volcano"], f["sensor_bucket"]), [])
                if abs((p.instante.replace(tzinfo=None) - t0).total_seconds()) <= cm.VENTANA_S]
        if cand:
            out.add(ec.clave(min(cand, key=lambda p: abs((p.instante.replace(tzinfo=None) - t0).total_seconds()))))
        else:
            sin.append("%s|%s|%s" % (f["volcano"], f["sensor_bucket"], f["fecha_utc"]))
    return out, sin


def _filas_1_13():
    p = ROOT / "experiments" / "_s151_alertas_diurnas" / "real_o_reflejo_filas.json"
    return json.loads(p.read_text(encoding="utf-8"))


def imprimir(r, variantes, final, motivo, opcion):
    print("COMPUERTAS: inválido %d, indecidible %d" % (len(r["compuertas"]["invalido"]), len(r["compuertas"]["indecidible"])))
    for x in r["compuertas"]["invalido"][:30] + r["compuertas"]["indecidible"][:30]:
        print("  ", x)
    print("cobertura diurna:", r["cobertura_diurna"])
    print("noche, records en un solo brazo:", r["noche_solo_un_lado"])
    print("R1 (protegidas que el control publica y el brazo no):", len(r["r1"]))
    for s, m in r["por_sensor"].items():
        print("%s: P2 %s (neto %+d, B %d, p_gana %.4f, p_pierde %.4f) | protegidas %d de %d | alertas<1MW %d de %d | "
              "negativos %d de %d (Q_d %.4f) | Q_n %.4f (%d) | D %s (%d de %d alertas) | neg>=1MW %d | pub en «otra» %d | razón mag %s"
              % (s, m["p2"], m["neto"], m["p2_det"]["B"], m["p2_det"]["p_gana"], m["p2_det"]["p_pierde"], m["P"],
                 m["P_obs"], m["amb_recuperadas"], m["amb_obs"], m["neg_pub"], m["neg_obs"], m["Qd"], m["Qn"],
                 m["Qn_den"], m["D"], m["alertas_recuperadas"], m["alertas_obs"], m["neg_1mw"], m["pub_otra"], m["razon_mag_mediana"]))
        print("   -> %s (caso %s, opción %s)" % (m["veredicto"], m["caso"], opcion))
        print("   I6:", {k: v for k, v in r["i6"][s].items() if k != "problemas"})
        print("   M4 por ventana:", m["por_ventana"])
        print("   protegidas recuperadas publicadas con 1 MW o más: %d; negativos publicados por elevación solar: %s"
              % (m["P_1mw"], m["neg_pub_por_elevacion"]))
    print("GLOBAL (principal):", r["global"])
    print("VARIANTES:", variantes)
    print("VEREDICTO FINAL (§6.4):", final, ("| " + motivo) if motivo else "")


if __name__ == "__main__":
    sys.exit(main())
