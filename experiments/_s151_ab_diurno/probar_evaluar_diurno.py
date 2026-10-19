# -*- coding: utf-8 -*-
"""Autoprueba de evaluar_diurno.py: salidas fabricadas con respuesta CONOCIDA, que tienen que dar lo esperado y
algunas de las cuales TIENEN que fallar (A110, A116: un control se valida midiendo su nulo, y un evaluador que
nunca dice que no, no mide). Salida: probar_salida.txt.

Cómo se fabrica. Se toma el universo REAL del pre-registro (sustrato.universo sobre la referencia del repo) y, para
cada pasada diurna de la tabla y cada positivo de las seis ventanas, se escribe un record del brazo diurno a esa
hora, con una plantilla que el predicado del tablero (node, A97) publica o con una que no publica. Cada volcán
lleva además una pasada nocturna por día, idéntica en los dos brazos. Los logs traen la línea FLAGS_BRAZO como la
escribe el workflow. Así la prueba pasa por el mismo camino que una corrida real: referencia, índice, node,
emparejamiento a 120 s, nulo barajado y binomial.

Casos (respuesta esperada entre paréntesis):
  1  solo_protegidas    publica sólo en los positivos                          (ADOPTAR)
  2  todo_publica       publica en todas las pasadas diurnas                   (G2 FALLA en los dos sensores; NO ADOPTAR)
  3  azar               publica al azar en 30 % de las pasadas diurnas         (G1 FALLA; NO ADOPTAR)
  4  una_no_procesada   el 1 sin el record de un positivo de W2                (sale del denominador; sigue ADOPTAR)
  5  w3_sin_procesar    el 1 sin el único positivo de W3                       (PENDIENTE DE REPETICION; con --repetidas W3, W3 sale y ADOPTAR)
  6  solo_w2            publica sólo en los positivos de W2                    (DEPENDE DEL OCR, DECIDE NICOLAS)
  7  control_vs_si      el control contra sí mismo                             (INDECIDIBLE por nulo 1; noches iguales; 0 publicaciones diurnas)
  8  noche_distinta     el 1 con un record nocturno cambiado en el brazo diurno (G3 FALLA; INDECIDIBLE)
  9  cableado_roto      el 1 con un log diurno que leyó el flag apagado        (INDECIDIBLE por cableado)
  10 skip_daytime       el 1 con un gránulo VIIRS saltado por diurno en el log  (INDECIDIBLE por cableado)
  10b filtro_de_fetch   el 1 con el filtro nocturno de fetch aplicado a VIIRS  (INDECIDIBLE por cableado)
  11 g2_borde           umbral binomial a cobertura completa                   (20 en VIIRS 375 y 6 en VIIRS 750, §6)
  12 trampa_a118        indexar_referencia con el flag apagado                  (no ve ninguna pasada diurna del universo)
  13 regla_minimas      sin la regla en el árbol: PENDIENTE; con una regla neutra inyectada: SN y SE iguales a original
  14 cobertura          contar_pasadas_noche.py (paso recolectar del workflow) sobre los casos 1, 7, 19 y 8, y sin
                        las noches de un volcán en el brazo diurno            (0, 1, 1, 0 y 1)
  Agregados tras el verificador del PR #822 (cada uno atrapa una mutación de mutar_evaluador.py):
  15 lascar_todo        publica todo Láscar de día y nada más                  (G1 FALLA; atrapa estrato_unico)
  16 g2_un_sensor       G2 cumple en 375 y falla en 750                         (DECIDE NICOLAS CON M4, no ADOPTAR; atrapa g2_any)
  17 volatiles          noches con processed_utc y first_processed_utc distintos (G3 CUMPLE; atrapa volatiles)
  18 granulo_distinto   una noche con otro nombre de gránulo                    (G3 cobertura, no cableado)
  19 v750_cerrado       el brazo diurno sin ninguna pasada diurna de 750        (INDECIDIBLE por nulo 1 de VIIRS750)
  20 tabla_sin_procesar 15 % de la tabla VIIRS 375 de W5 sin procesar           (PENDIENTE DE REPETICION antes de G2)
  21 control_nulo       el control del nulo con el nulo ×0,3 y corrido −0,5     (FALLA; sin romper, OK; atrapa nulo_angosto)
  Agregados en la vuelta 70 del loop (W1 real dio G3 FALLA por ruido de punto flotante entre runners):
  22 ruido_flotante     noches con floats que difieren en 2e-16 relativo         (G3 CUMPLE)
  22b diferencia_real   noches con floats que difieren en 1e-6 relativo          (G3 FALLA)
  22c pixel_distinto    1e-6 sólo dentro de anomaly_pixels                       (G3 FALLA; atrapa listas o dicts siempre iguales)
  22d pixel_extra       el brazo diurno con un píxel más                         (G3 FALLA; atrapa el largo de la lista)
  22e none_vs_cero      None en el control, 0.0 en el diurno                     (G3 FALLA; atrapa None igual a todo)
  22f relativo_1e8      floats que difieren en 1e-8 relativo                     (G3 FALLA; atrapa rel_tol=5e-7)
  22g absoluto_5e13     diag_mu_deti 2e-8 con 5e-13 absoluto de diferencia       (G3 FALLA; atrapa abs_tol=1e-12)
  Agregados con la desviación D2 (2026-10-17: el G3 clasifica cada par con unir_intentos.comparar más el predicado
  del tablero). Cada uno atrapa una mutación g3_* de mutar_evaluador.py:
  23  orden_pixeles     los mismos dos píxeles en otro orden                     (G3 CUMPLE, pares «orden»; atrapa g3_orden_falla)
  23b borde_v375_f5     otro píxel en la lista (llena: 100 con los descartados) y otro hotspot, VIIRS 375 con
                        f5_core_vrp_mw (el tablero no lee los píxeles)          (G3 CUMPLE, pares «borde»; atrapa g3_borde_falla)
  23c borde_v375_sin_f5 lo mismo sin f5_core_vrp_mw (el tablero SÍ los lee)      (G3 FALLA)
  23d borde_lista_corta lo de 23b con la lista de 2 píxeles: el recorte top-100 no
                        cortó nada, otro píxel es otra detección (PR #847)      (G3 FALLA; atrapa u_sin_recorte_lleno)
  23e borde_fuera_del_corte lo de 23b, pero cambia el píxel más caliente y no el del
                        puesto 100: un desempate no puede hacerlo (verificador V2) (G3 FALLA; atrapa u_fuera_del_corte)
  24  hotspot_escena    MODIS: un brazo con el rescate por cúmulo y el otro no   (G3 CUMPLE, pares «hotspot_escena»; atrapa g3_escena_falla)
  24b escena_predicado  lo mismo con el cúmulo en 0 MW: comparar lo admite y el
                        predicado del tablero da distinto (isSummitDetection)   (G3 FALLA; atrapa g3_sin_predicado)
  25  clase_una_noche   una sola noche con distance_class distinta              (G3 FALLA; atrapa g3_distinto_admitido)
"""
from __future__ import annotations

import contextlib
import io
import json
import math
import os
import random
import shutil
import sys
import tempfile
import types
from datetime import datetime, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import evaluar_diurno as ED  # noqa: E402  (deja sys.stdout en utf-8)
import sustrato as S  # noqa: E402

bp, cm = ED.bp, ED.cm
PUB = {"vrp_mw": 0.4, "distance_class": "summit", "t_max_k": 290, "f5_core_vrp_mw": 0.4, "triggered_test1": False,
       "primary_cluster": {"vrp_mw": 0.4, "centroid_dist_km": 1.0, "n_pixels": 2}}
NO = {"vrp_mw": 0.0, "distance_class": "summit", "t_max_k": 270, "triggered_test1": False, "primary_cluster": None}
SENSOR = {"VIIRS375": "VIIRS_NOAA20", "VIIRS750": "VIIRS_NOAA20_750"}
FLAGS_BASE = {"ENABLE_DAYTIME_MODIS": False, "ENABLE_TEST1_PATH": True, "ENABLE_TESTS_23_PROSE_BRANCH": False,
              "ENABLE_MODIS_B22_PRIMARY": False, "ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER": False, "PATH_D_ONLY_CAP_MW": 5.0,
              "ENABLE_TESTS_23_NO_BT_GATE_VIIRS375": False, "ENABLE_VENT_ANCHORED_CLUSTERING": True, "ENABLE_ROI1_BOX_PAPER": False}


def record(vol, sensor_b, t, plantilla, dia, n):
    r = dict(plantilla)
    r.update({"datetime_utc": t, "sensor": SENSOR[sensor_b], "product_version": "standard",
              "granule": "VJ102%s.A%s.002.sintetico.nc" % ("IMG" if sensor_b == "VIIRS375" else "MOD",
                                                          datetime.strptime(t, "%Y-%m-%d %H:%M").strftime("%Y%j.%H%M")),
              "processed_utc": "2026-10-15T00:%02d:00Z" % (n % 60), "first_processed_utc": "2026-10-15T00:%02d:00Z" % (n % 60)})
    if dia:
        r["diag_umbrales_diurnos"] = True
    return r


def noches(UW):
    """Una pasada nocturna (06:00 UTC, 02:00 hora local) por volcán y por día de cada ventana, sin publicar."""
    out = []
    for w in ED.VENTANAS:
        c = ED.VENTANA[w]
        d = datetime.strptime(c["desde"], "%Y-%m-%d")
        while d.strftime("%Y-%m-%d") <= c["hasta"]:
            for vol in c["vols"]:
                out.append((vol, "VIIRS375", d.strftime("%Y-%m-%d") + " 06:00"))
            d += timedelta(days=1)
    return out


# Casos 23 a 25 (desviación D2). Píxeles y pares de records con la forma de los del pipeline.
P1 = {"lat": -23.37, "lon": -67.73, "vrp_mw": 0.05, "bt_k": 280.0}
P2 = {"lat": -23.36, "lon": -67.72, "vrp_mw": 0.04, "bt_k": 279.0}
P3 = {"lat": -23.38, "lon": -67.74, "vrp_mw": 0.04, "bt_k": 279.0}


def noche_orden(n, r):
    r["anomaly_pixels"] = [dict(P1), dict(P2)] if n == "control" else [dict(P2), dict(P1)]


# vrp 0,04, igual a P2 y P3: el mínimo de la lista llena, el único que un desempate en el corte puede cambiar
LEJOS_98 = [{"lat": -23.6 - 0.001 * i, "lon": -67.9, "vrp_mw": 0.04, "bt_k": 277.0} for i in range(98)]


def noche_borde(con_f5, llena=True, caliente=False):
    """El empate del recorte top-100: entra otro píxel del mismo VRP y con él cambia el hotspot de escena. Con
    `llena` la lista guardada mide los 100 del recorte (2 guardados + 98 descartados), donde el empate puede
    actuar; sin `llena` mide 2 y el recorte no cortó nada, así que otro píxel es otra detección (PR #847)."""
    def f(n, r):
        if caliente:   # cambia el píxel más caliente, no el del corte: un desempate en el puesto 100 no puede hacerlo
            otro = dict(P1, lat=P1["lat"] - 0.02)
            r.update(anomaly_pixels=[dict(P1 if n == "control" else otro), dict(P2)],
                     hotspot_lat=-23.36 if n == "control" else -23.38, hotspot_lon=-67.73)
        else:
            r.update(anomaly_pixels=[dict(P1), dict(P2 if n == "control" else P3)],
                     hotspot_lat=-23.36 if n == "control" else -23.38, hotspot_lon=-67.73)
        if llena:
            r["discarded_anomaly_pixels"] = [dict(q) for q in LEJOS_98]
            r["n_anomalous_pixels"] = 140     # >100: el recorte cortó (verificador V2 del PR #847)
        if con_f5:
            r["f5_core_vrp_mw"] = 0.0
    return f


def noche_escena(pc_vrp):
    """Rescate por cúmulo (store.py:390-422) en el brazo diurno y no en el control, con todo lo demás igual: el par
    que unir_intentos.comparar llama `hotspot_escena`. Con pc_vrp = 0 el lado rescatado queda con vrp_mw 0 y
    etiqueta de descarte, y isSummitDetection (frontend/index.html:1596) lo baja de summit: sólo el predicado lo ve."""
    pc = {"vrp_mw": pc_vrp, "centroid_lat": -38.0, "centroid_lon": -71.0, "centroid_dist_km": 1.0, "n_pixels": 2}

    def f(n, r):
        r.update(sensor="MODIS_AQUA", t_max_k=280.0, triggered_test1=pc_vrp > 0, primary_cluster=dict(pc))
        if n == "control":
            r.update(vrp_mw=3.0, final_hotspot_source="test1", hotspot_lat=-38.3, hotspot_lon=-71.3,
                     hotspot_dist_km=30.0, final_hotspot_lat=-38.01, final_hotspot_lon=-71.01, final_hotspot_dist_km=1.2)
        else:
            r.update(vrp_mw=pc_vrp, final_hotspot_source="cluster_rescue",
                     discarded_reason="single_pixel_far_overridden_by_cluster", hotspot_lat=-38.0, hotspot_lon=-71.0,
                     hotspot_dist_km=1.0, final_hotspot_lat=-38.0, final_hotspot_lon=-71.0, final_hotspot_dist_km=1.0)
    return f


def noche_clase_una():
    """distance_class distinta en UNA noche del brazo diurno (la primera que escribe)."""
    hecho = []

    def f(n, r):
        if n == "diurno" and not hecho:
            r["distance_class"] = "far"
            hecho.append(1)
    return f


def escribir(dirc, UW, publica, sacar=(), diurno_igual_control=False, flags_diurno=None, cambiar_noche=False,
             linea_extra="", volatiles_distintos=False, granulo_distinto=False, ruido_relativo=None,
             modificar_noche=None, flags_ambos=None, regimen_sha=None, tocar_records=None):
    """Escribe <dirc>/<brazo>/<vol>.json y <dirc>/logs/<brazo>_<vol>.log.
    S154 (casos de punta a punta con --base k): `flags_ambos` se aplica al FLAGS_BRAZO de los dos brazos, `regimen_sha`
    pone la marca regimen en cada record y `tocar_records(por)` permite romper records a propósito (H2a)."""
    por = {n: {v: [] for v in bp.VOLS} for n in ED.BRAZOS}
    i = 0
    for vol, b, t in noches(UW):
        i += 1
        for n in ED.BRAZOS:
            r = record(vol, b, t, NO, False, i)
            if ruido_relativo is not None:
                # Valor real de W1 (Láscar MODIS Terra 2026-03-01 01:40, diag_mu_deti), también dentro de una lista
                # de píxeles: el brazo diurno lo trae multiplicado por (1 + ruido_relativo).
                f = (1 + ruido_relativo) if n == "diurno" else 1.0
                r["diag_mu_deti"] = -9.871330774512634e-06 * f
                r["anomaly_pixels"] = [{"lat": -23.37, "lon": -67.73, "eti": 4.920530419179312e-07 * f}]
            if modificar_noche is not None:
                # (brazo, record) -> None: cambia el record nocturno en el lugar (casos 22c a 22g).
                modificar_noche(n, r)
            if n == "diurno" and volatiles_distintos:
                # Dos jobs guardan el mismo record a horas distintas: no es una diferencia de medición.
                r.update({"processed_utc": "2026-10-16T09:%02d:00Z" % (i % 60),
                          "first_processed_utc": "2026-10-16T09:%02d:30Z" % (i % 60)})
            por[n][vol].append(r)
    if cambiar_noche:
        por["diurno"]["Lascar"][0] = dict(por["diurno"]["Lascar"][0], t_max_k=999.0)
    if granulo_distinto:
        # La misma pasada con otro nombre de gránulo (NASA la reprodujo entre los dos jobs): cobertura, no cableado.
        r = por["diurno"]["Lascar"][0]
        por["diurno"]["Lascar"][0] = dict(r, granule=r["granule"].replace("sintetico", "reproducido"))
    if not diurno_igual_control:
        for w in ED.VENTANAS:
            for k in sorted(UW[w]["pos"] | UW[w]["tabla"]):
                if k in sacar:
                    continue
                i += 1
                por["diurno"][k[0]].append(record(k[0], k[1], k[2], PUB if publica(w, k, UW) else NO, True, i))
    if regimen_sha is not None:
        for n in ED.BRAZOS:
            for recs in por[n].values():
                for r in recs:
                    r["regimen"] = {"perfil": ED.BRAZOS[n], "codigo_sha": regimen_sha, "origen": "actions"}
    if tocar_records is not None:
        tocar_records(por)
    (dirc / "logs").mkdir(parents=True, exist_ok=True)
    for n in ED.BRAZOS:
        (dirc / ED.BRAZOS[n]).mkdir(parents=True, exist_ok=True)
        for vol, recs in por[n].items():
            if not recs:
                continue
            (dirc / ED.BRAZOS[n] / (vol + ".json")).write_text(json.dumps({"volcano": vol, "records": recs}), encoding="utf-8")
            fl = dict(FLAGS_BASE, PROFILE_NAME=ED.BRAZOS[n], DATA_SUBDIR=ED.BRAZOS[n],
                      ENABLE_DAYTIME_VIIRS=(n == "diurno"))
            if flags_ambos:
                fl.update(flags_ambos)
            if n == "diurno" and flags_diurno:
                fl.update(flags_diurno)
            txt = "FLAGS_BRAZO " + json.dumps(fl) + "\n"
            if n == "diurno" and linea_extra and vol == "Lascar":
                txt += linea_extra + "\n"
            (dirc / "logs" / ("%s_%s.log" % (ED.BRAZOS[n], vol))).write_text(txt, encoding="utf-8")


def correr(dirc, extra=()):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = ED.evaluar(ED.parser().parse_args(["--raiz", str(dirc)] + list(extra)))
    return res, buf.getvalue()


RESULTADOS = []


def chequear(caso, cond, detalle):
    RESULTADOS.append((caso, bool(cond)))
    print("   [%s] %s" % ("OK" if cond else "FALLA", detalle))


def chequear_orden_del_nulo():
    """S154 (verificador de W2 a W6, H2): el nulo barajado no puede depender del orden en que se recorre `cls`.
    `cls` se arma iterando conjuntos de strings, cuyo orden cambia con PYTHONHASHSEED en cada proceso; si los estratos
    salen en ese orden, el generador reparte sus números distinto y el p95 cambia con la misma semilla (+0,2446 contra
    +0,2760 en dos corridas de W2 a W6). Mismos datos en dos órdenes: estratos, grupos y p95 idénticos."""
    np = ED.np
    base = []
    for i, (vol, s) in enumerate([("Lascar", "VIIRS375"), ("Llaima", "VIIRS375"), ("Chaiten", "VIIRS750"),
                                  ("Villarrica", "VIIRS375"), ("Copahue", "VIIRS750")]):
        for j in range(40):
            k = (vol, s, "2026-07-%02d %02d:00" % (1 + j % 28, j % 24))
            base.append((k, {"ventana": "W3", "pob": {"pos"} if j % (5 + i) == 0 else {"neg"},
                             "estado": "publicada" if (j * (i + 3)) % 7 < 3 else "sin_publicar"}))
    a, b = dict(base), dict(reversed(base))
    ea, eb = ED.estratos_de(a, ("W3",)), ED.estratos_de(b, ("W3",))
    chequear("orden_del_nulo", ea == eb, "estratos en el mismo orden con cls recorrido al derecho y al revés")
    ga, gb = ED.grupos_de(a, ("W3",)), ED.grupos_de(b, ("W3",))
    chequear("orden_del_nulo", ga == gb, "grupos del control del nulo en el mismo orden")
    # el nulo entero, no sólo el p95: con un nulo discreto el p95 puede coincidir de casualidad aunque las muestras
    # salgan en otro reparto (pasó con estos datos antes del arreglo)
    na = ED.g1(a, ("W3",), np.random.default_rng(ED.SEMILLA), con_nulo=True)["_nulo"]
    nb = ED.g1(b, ("W3",), np.random.default_rng(ED.SEMILLA), con_nulo=True)["_nulo"]
    chequear("orden_del_nulo", np.array_equal(na, nb),
             "las %d muestras del nulo idénticas con la misma semilla (difieren %d)" % (len(na), int(np.sum(na != nb))))


def chequear_base_k():
    """S154 (tarea 1.32): con `--brazos` y `--base k` el evaluador lee los brazos del A/B sobre K y su cableado exige
    los tres flags de K en los logs; un brazo que corrió con el Test 1 encendido tiene que salir como cableado roto."""
    flags_k = {"ENABLE_TEST1_PATH": False, "ENABLE_TESTS_23_PROSE_BRANCH": True, "ENABLE_MODIS_B22_PRIMARY": True}
    brazos0, decl0 = dict(ED.BRAZOS), {k: dict(v) for k, v in ED.DECLARADO.items()}
    tmp = Path(tempfile.mkdtemp(prefix="probar_base_k_"))
    try:
        ED.configurar_brazos("_s154_ab_diurno_k_control", "_s154_ab_diurno_k_on", "k")
        chequear("base_k", ED.BRAZOS == {"control": "_s154_ab_diurno_k_control", "diurno": "_s154_ab_diurno_k_on"},
                 "--brazos cambia los nombres que lee el evaluador")
        chequear("base_k", all(ED.DECLARADO[n][c] is v for n in ("control", "diurno") for c, v in flags_k.items()),
                 "--base k exige los tres flags de K en los dos brazos")

        def escribir_log(test1):
            for n, diurno in (("control", False), ("diurno", True)):
                b = ED.BRAZOS[n]
                (tmp / b).mkdir(parents=True, exist_ok=True)
                (tmp / b / "Lascar.json").write_text('{"volcano": "Lascar", "records": []}', encoding="utf-8")
                fl = dict(flags_k, PROFILE_NAME=b, DATA_SUBDIR=b, ENABLE_DAYTIME_VIIRS=diurno, ENABLE_DAYTIME_MODIS=False,
                          ENABLE_TEST1_PATH=test1)
                (tmp / "logs").mkdir(exist_ok=True)
                (tmp / "logs" / ("%s_Lascar.log" % b)).write_text("FLAGS_BRAZO " + json.dumps(fl) + "\n", encoding="utf-8")

        escribir_log(test1=False)
        ok = ED.cableado([str(tmp)], [str(tmp / "logs")], "control") + ED.cableado([str(tmp)], [str(tmp / "logs")], "diurno")
        chequear("base_k", ok == [], "brazos que leyeron K: cableado limpio (%s)" % ok)
        escribir_log(test1=True)
        mal = ED.cableado([str(tmp)], [str(tmp / "logs")], "control")
        chequear("base_k", any("ENABLE_TEST1_PATH" in x for x in mal), "un brazo con el Test 1 encendido sale como cableado roto (%s)" % mal)
    finally:
        ED.BRAZOS.clear(); ED.BRAZOS.update(brazos0)
        ED.DECLARADO.clear(); ED.DECLARADO.update(decl0)
        shutil.rmtree(tmp, ignore_errors=True)


def _cls_desde_estratos(estratos, x_por_estrato):
    """cls sintético: por estrato (n, P, K) y cuántas publicadas caen en positivos (x_s)."""
    cls = {}
    for i, ((n, p, k), xs) in enumerate(zip(estratos, x_por_estrato)):
        for j in range(n):
            es_pos = j < p
            pub = (j < xs) if es_pos else (p <= j < p + (k - xs))
            cls[("V%d" % i, "VIIRS375", "2026-07-01 %02d:%02d" % (j // 60, j % 60))] = {
                "ventana": "W3", "pob": {"pos"} if es_pos else {"neg"}, "estado": "publicada" if pub else "sin_publicar"}
    return cls


def _pmf_fuerza_bruta(estratos):
    """Distribución de X (publicadas entre positivos) enumerando todas las elecciones de positivos por estrato."""
    from itertools import combinations
    dist = {0: 1.0}
    for n, p, k in estratos:
        cuenta = {}
        combos = list(combinations(range(n), p))
        for c in combos:
            x = sum(1 for i in c if i < k)          # las k primeras son las publicadas
            cuenta[x] = cuenta.get(x, 0) + 1
        nueva = {}
        for a_, pa in dist.items():
            for b_, cb in cuenta.items():
                nueva[a_ + b_] = nueva.get(a_ + b_, 0.0) + pa * cb / len(combos)
        dist = nueva
    return dist


def chequear_cola_exacta():
    """S154, adenda K §3.1 (sellada): G1 decide con P(nulo >= D) exacta. Pruebas pedidas por el verificador de la
    adenda (H4): contra fuerza bruta, el caso de empate, la mutación de «>=» por «>», y los controles del nulo con la
    regla exacta. La regla sólo decide con --base k; con c0 se informa (la corrida sobre C0 queda reproducible)."""
    np = ED.np
    rnd = random.Random(11)
    malos = 0
    for _ in range(60):
        est = []
        for _s in range(rnd.randint(1, 3)):
            n = rnd.randint(2, 9)
            est.append((n, rnd.randint(1, n - 1), rnd.randint(0, n)))
        bruta = _pmf_fuerza_bruta(est)
        exacta = ED.distribucion_x_exacta(est)
        malos += any(abs(exacta[x] - bruta.get(x, 0.0)) > 1e-12 for x in range(len(exacta))) or abs(sum(exacta) - 1) > 1e-12
    chequear("cola_exacta", malos == 0, "distribución exacta de X igual a la fuerza bruta en 60 casos chicos (malos %d)" % malos)
    est = [(9, 3, 4), (8, 2, 3), (7, 3, 2)]
    pmf = ED.distribucion_x_exacta(est)
    chequear("cola_exacta", all(abs(ED.cola_exacta(est, x) - float(sum(pmf[x:]))) < 1e-15 for x in range(len(pmf))),
             "cola_exacta(x) = suma de la distribución desde x (incluye el propio x)")
    # empate: un x con P(X >= x) >= 0,05 y P(X > x) < 0,05; la regla con «>=» FALLA y la mutada con «>» cumpliría
    est_e, x_e = None, None
    for n1 in range(4, 12):
        e = [(n1, 2, 2), (6, 1, 2)]
        pm = ED.distribucion_x_exacta(e)
        for x in range(len(pm)):
            if float(sum(pm[x:])) >= 0.05 > float(sum(pm[x + 1:])):
                est_e, x_e = e, x
                break
        if est_e:
            break
    chequear("cola_exacta", est_e is not None, "existe el caso de empate que distingue «>=» de «>» (%s, x=%s)" % (est_e, x_e))
    xs = [min(x_e, est_e[0][1]), x_e - min(x_e, est_e[0][1])]
    cls_e = _cls_desde_estratos(est_e, xs)
    brazos0, decl0, regla0 = dict(ED.BRAZOS), {k: dict(v) for k, v in ED.DECLARADO.items()}, dict(ED.REGLA)
    try:
        ED.configurar_brazos("_s154_ab_diurno_k_control", "_s154_ab_diurno_k_on", "k")
        r = ED.g1(cls_e, ("W3",), np.random.default_rng(ED.SEMILLA))
        chequear("cola_exacta", r["veredicto"] == "FALLA" and r["p_cola_exacta"] >= 0.05,
                 "en el empate la regla exacta FALLA (P(X>=x) = %.4f); con «>» cumpliría (%.4f)" % (
                     r["p_cola_exacta"], ED.cola_exacta(est_e, x_e + 1)))
        # verificador del candado, H-3: además fija x_obs y el valor exacto de la cola, para atrapar también los
        # errores conservadores (pmf[x_obs - 1:], x_obs - 1) que el veredicto solo no ve
        chequear("cola_exacta", r["x_obs"] == x_e and abs(r["p_cola_exacta"] - ED.cola_exacta(est_e, x_e)) < 1e-15,
                 "x_obs = %s (esperado %s) y la cola es exactamente P(X >= x_obs)" % (r["x_obs"], x_e))
        # control del nulo con la regla exacta, sobre un brazo que no discrimina y uno perfecto
        rnd2 = random.Random(3)
        est_c = [(60, 8, 30), (50, 6, 20), (40, 5, 25)]
        cls_c = _cls_desde_estratos(est_c, [rnd2.randint(0, min(p, k)) for n, p, k in est_c])
        c = ED.controles_del_nulo(cls_c, ("W3",), np.random.default_rng(ED.SEMILLA))
        chequear("cola_exacta", c["ok"] and "cola exacta" in c["texto"], "controles del nulo con la regla exacta: " + c["texto"])
        # verificador del candado, H-2 (e): el control tiene que FALLAR con un nulo roto (distribución corrida en +1)
        orig = ED.distribucion_x_exacta
        try:
            ED.distribucion_x_exacta = lambda e: np.concatenate([[0.0], orig(e)])
            c_roto = ED.controles_del_nulo(cls_c, ("W3",), np.random.default_rng(ED.SEMILLA))
        finally:
            ED.distribucion_x_exacta = orig
        chequear("cola_exacta", not c_roto["ok"], "con el nulo exacto corrido en +1 el control FALLA: " + c_roto["texto"])
        # H-2 (d): colas del muestreo contra colas exactas, en todos los x (no cuantiles: el p95 muestreado salta)
        n_m = 200000
        mues = ED.nulo_barajado(est_c, np.random.default_rng(ED.SEMILLA), n=n_m)
        pp, nn, kk = sum(e[1] for e in est_c), sum(e[0] - e[1] for e in est_c), sum(e[2] for e in est_c)
        peor = 0.0
        for x in range(pp + 1):
            ex = ED.cola_exacta(est_c, x)
            mc = float(np.mean(mues >= x / pp - (kk - x) / nn - 1e-12))
            peor = max(peor, abs(mc - ex) / (4 * math.sqrt(max(ex * (1 - ex), 1e-12) / n_m) + 1e-9))
        chequear("cola_exacta", peor <= 1.0, "colas del muestreo (%d) dentro de 4 errores estándar de las exactas en todos los x (peor %.2f)" % (n_m, peor))
    finally:
        ED.BRAZOS.clear(); ED.BRAZOS.update(brazos0)
        ED.DECLARADO.clear(); ED.DECLARADO.update(decl0)
        ED.REGLA.clear(); ED.REGLA.update(regla0)
    # con c0 la decisión sigue siendo la del p95 muestreado, y la cola exacta se informa igual
    r0 = ED.g1(cls_e, ("W3",), np.random.default_rng(ED.SEMILLA))
    chequear("cola_exacta", "p_cola_exacta" in r0 and "p95" in r0, "con base c0 se informa la cola exacta sin cambiar la regla")


def chequear_regla_w2():
    """S154, adenda K §3.2 (sellada): con base K, si G1 cumple sin W2 y falla con W2, decide Nicolás con M4."""
    res = {"repetir": [], "ventanas_presentes": list(ED.DECIDEN), "G3": "CUMPLE",
           "G1_W2W6": {"veredicto": "FALLA"}, "G1_W3W6": {"veredicto": "CUMPLE"},
           "G2": {s: {"veredicto": "FALLA"} for s in ED.VIIRS}}
    # Verificador del candado, H-1: la regla se arma con configurar_brazos (como en evaluar), no tocando REGLA a mano;
    # así una base k que no encienda la regla W2 cae. Y el caso «falla también sin W2» tiene que seguir en NO ADOPTAR.
    brazos0, decl0, regla0 = dict(ED.BRAZOS), {k: dict(v) for k, v in ED.DECLARADO.items()}, dict(ED.REGLA)
    ambos_fallan = dict(res, G1_W3W6={"veredicto": "FALLA"})
    try:
        ED.configurar_brazos("_s151_ab_diurno_control", "_s151_ab_diurno_on", "c0")
        v0 = ED.veredicto(res, [])
        ED.configurar_brazos("_s154_ab_diurno_k_control", "_s154_ab_diurno_k_on", "k")
        vk = ED.veredicto(res, [])
        vk_ambos = ED.veredicto(ambos_fallan, [])
    finally:
        ED.BRAZOS.clear(); ED.BRAZOS.update(brazos0)
        ED.DECLARADO.clear(); ED.DECLARADO.update(decl0)
        ED.REGLA.clear(); ED.REGLA.update(regla0)
    chequear("regla_w2", v0.startswith("NO ADOPTAR"), "base c0: falla con W2 -> NO ADOPTAR (%s)" % v0[:40])
    chequear("regla_w2", vk.startswith("DECIDE NICOLAS CON M4") and "W2" in vk, "base k: cumple sin W2 y falla con W2 -> DECIDE NICOLAS CON M4 (%s)" % vk[:70])
    chequear("regla_w2", vk_ambos.startswith("NO ADOPTAR"), "base k: falla con y sin W2 -> NO ADOPTAR (%s)" % vk_ambos[:40])


def chequear_h2a_h2b():
    """S154, adenda K §4 (sellada). H2a: con base K se revisan los records de los dos brazos (0 con Test 1 y el
    codigo_sha del tag). H2b: con brazos que no son los de W2 a W6 sobre C0, --base tiene que ser explícito."""
    tmp = Path(tempfile.mkdtemp(prefix="probar_h2a_"))
    brazos0 = dict(ED.BRAZOS)
    try:
        ED.BRAZOS.update({"control": "_s154_ab_diurno_k_control", "diurno": "_s154_ab_diurno_k_on"})

        def escribir_recs(**cambio):
            for b in ED.BRAZOS.values():
                (tmp / b).mkdir(parents=True, exist_ok=True)
                r = {"datetime_utc": "2026-07-01 05:00", "sensor": "VIIRS_SNPP", "triggered_test1": False,
                     "final_hotspot_source": "ctx_cluster", "regimen": {"perfil": b, "codigo_sha": "a" * 40}}
                r.update(cambio)
                (tmp / b / "Lascar.json").write_text(json.dumps({"volcano": "Lascar", "records": [r]}), encoding="utf-8")

        escribir_recs()
        chequear("h2a", ED.cableado_records([str(tmp)], "a" * 40) == [], "records de K con el sha del tag: limpio")
        chequear("h2a", len(ED.cableado_records([str(tmp)], None)) > 0, "sin sha: sale como problema, no se cae")
        for nom, cambio in (("triggered_test1", {"triggered_test1": True}),
                            ("test1_roi", {"final_hotspot_source": "test1_roi"}),
                            ("sha", {"regimen": {"perfil": "x", "codigo_sha": "b" * 40}}),
                            ("sin regimen", {"regimen": None})):
            escribir_recs(**cambio)
            p = ED.cableado_records([str(tmp)], "a" * 40)
            chequear("h2a", len(p) > 0, "%s: sale como roto (%s)" % (nom, p[:1]))
    finally:
        ED.BRAZOS.clear(); ED.BRAZOS.update(brazos0)
        shutil.rmtree(tmp, ignore_errors=True)
    por_defecto = "%s,%s" % (brazos0["control"], brazos0["diurno"])
    chequear("h2b", ED.resolver_base(por_defecto, None) == "c0", "brazos de W2 a W6 sobre C0 sin --base: c0")
    chequear("h2b", ED.resolver_base("_s154_ab_diurno_k_control,_s154_ab_diurno_k_on", "k") == "k", "--base k explícito: k")
    try:
        ED.resolver_base("_s154_ab_diurno_k_control,_s154_ab_diurno_k_on", None)
        rehusa = False
    except SystemExit:
        rehusa = True
    chequear("h2b", rehusa, "brazos K sin --base: el evaluador se niega")


def chequear_punta_a_punta_k(UW, tmp):
    """Verificador del candado, H-1: evaluar() de punta a punta con --brazos K, --base k y --sha-codigo, sobre el
    universo real del pre-registro. Antes, cuatro mutaciones de la ruta K pasaban con el arnés en verde."""
    k_brazos = ("_s154_ab_diurno_k_control", "_s154_ab_diurno_k_on")
    fk = {"ENABLE_TEST1_PATH": False, "ENABLE_TESTS_23_PROSE_BRANCH": True, "ENABLE_MODIS_B22_PRIMARY": True}
    sha = "c" * 40
    extra = ["--brazos", ",".join(k_brazos), "--base", "k", "--sha-codigo", sha]
    defecto = ("_s151_ab_diurno_control", "_s151_ab_diurno_on")

    def caso(nombre, publica, extra_=extra, **kw):
        d = tmp / nombre
        ED.configurar_brazos(*k_brazos, "k")
        try:
            escribir(d, UW, publica, flags_ambos=fk, regimen_sha=kw.pop("regimen_sha", sha), **kw)
            return correr(d, extra_)
        finally:
            ED.configurar_brazos(*defecto, "c0")

    res, txt = caso("k1", lambda w, k, U: k in U[w]["pos"])
    print("\n== caso k1 (punta a punta, base k, sólo protegidas) -> %s" % res["veredicto"])
    chequear("punta_a_punta_k", res["veredicto"].startswith("ADOPTAR") and res["G1_W2W6"]["regla"] == "cola exacta",
             "decide con la cola exacta y da ADOPTAR (P = %.2g)" % res["G1_W2W6"]["p_cola_exacta"])
    chequear("punta_a_punta_k", "codigo_sha cccccccccccc (adenda K §4 H2a): OK" in txt, "H2a corre y da OK sobre records limpios")

    # El caso «cumple sin W2, falla con W2» no se puede armar con datos sintéticos sobre el universo real (los 12
    # positivos de W2 no alcanzan a hundir G1 publicando negativos de W2: P 8,6e-08). La regla de la §3.2 se prueba en
    # chequear_regla_w2 con la configuración real de la base k.
    res, _ = caso("k2", lambda w, k, U: k in U[w]["neg"])
    chequear("punta_a_punta_k", res["veredicto"].startswith("NO ADOPTAR") and res["G1_W2W6"]["p_cola_exacta"] > 0.05,
             "base k, brazo que publica sólo en negativos: G1 falla con la cola exacta y da NO ADOPTAR (%s)" % res["veredicto"][:40])

    def con_test1(por):
        por["diurno"]["Lascar"][0]["triggered_test1"] = True
    res, _ = caso("k3", lambda w, k, U: k in U[w]["pos"], tocar_records=con_test1)
    chequear("punta_a_punta_k", res["veredicto"].startswith("INDECIDIBLE") and "H2a" in res["veredicto"],
             "un record con el Test 1 en el brazo diurno: INDECIDIBLE por H2a (%s)" % res["veredicto"][:70])
    res, _ = caso("k4", lambda w, k, U: k in U[w]["pos"], regimen_sha="d" * 40)
    chequear("punta_a_punta_k", res["veredicto"].startswith("INDECIDIBLE") and "H2a" in res["veredicto"],
             "records de otro commit: INDECIDIBLE por H2a")
    for nom, ex in (("sin --sha-codigo", ["--brazos", ",".join(k_brazos), "--base", "k"]),
                    ("brazos K con --base c0", ["--brazos", ",".join(k_brazos), "--base", "c0"])):
        try:
            caso("k5", lambda w, k, U: k in U[w]["pos"], extra_=ex)
            rehusa = False
        except SystemExit:
            rehusa = True
        chequear("punta_a_punta_k", rehusa, "%s: el evaluador se niega" % nom)


def main():
    chequear_orden_del_nulo()
    chequear_base_k()
    chequear_cola_exacta()
    chequear_regla_w2()
    chequear_h2a_h2b()
    tmp = Path(tempfile.mkdtemp(prefix="probar_diurno_"))
    try:
        filas, coords = ED.cargar_filas(ED.parser().parse_args(["--raiz", "x"]))
        UW = ED.universo_por_ventana(S.universo(filas, coords))
        print("Universo real del pre-registro: %s" % {w: (len(UW[w]["pos"]), len(UW[w]["neg"]), len(UW[w]["tabla"])) for w in ED.VENTANAS})
        if not os.environ.get("PROBAR_SOLO") or "k" in os.environ.get("PROBAR_SOLO", "").split(","):
            chequear_punta_a_punta_k(UW, tmp)
        pos_w2 = sorted(UW["W2"]["pos"])
        pos_w3 = sorted(UW["W3"]["pos"])
        rnd = random.Random(7)
        # sorted: iterar el conjunto sin ordenar sigue el hash de los strings, que cambia con PYTHONHASHSEED en cada
        # proceso; el sorteo «al azar» salía distinto por proceso (D de -0,094 a +0,030 con PYTHONHASHSEED 0 a 5) y
        # a veces G1 pasaba, como debe pasar un sorteo de cada veinte contra un p95 (D +0,154 contra p95 +0,123 en
        # la corrida de mutaciones del PR #847). Con el orden fijo, D -0,001 contra p95 +0,125 con cualquier semilla.
        azar = {k for w in ED.VENTANAS for k in sorted(UW[w]["pos"] | UW[w]["tabla"]) if rnd.random() < 0.30}
        # Seis negativos de VIIRS 750 en W4: con las 2 protegidas de tabla de 750 suman 8 publicaciones y G2 falla
        # en 750 (desde 6, caso 11); en 375 sigue en 6 de 2.511, lejos de 20.
        seis_v750 = set(sorted(k for k in UW["W4"]["neg"] if k[1] == "VIIRS750")[:6])
        todo_v750 = {k for w in ED.VENTANAS for k in UW[w]["pos"] | UW[w]["tabla"] if k[1] == "VIIRS750"}
        t5 = sorted(k for k in UW["W5"]["tabla"] - UW["W5"]["pos"] if k[1] == "VIIRS375")
        quince_w5 = set(t5[: int(0.15 * len(t5)) + 1])
        casos = [
            ("1 solo_protegidas", dict(publica=lambda w, k, U: k in U[w]["pos"]), []),
            ("2 todo_publica", dict(publica=lambda w, k, U: True), []),
            ("3 azar", dict(publica=lambda w, k, U: k in azar), []),
            ("4 una_no_procesada", dict(publica=lambda w, k, U: k in U[w]["pos"], sacar={pos_w2[0]}), []),
            ("5 w3_sin_procesar", dict(publica=lambda w, k, U: k in U[w]["pos"], sacar=set(pos_w3)), []),
            ("5b w3_sin_procesar repetida", dict(publica=lambda w, k, U: k in U[w]["pos"], sacar=set(pos_w3)), ["--repetidas", "W3"]),
            ("6 solo_w2", dict(publica=lambda w, k, U: w == "W2" and k in U[w]["pos"]), []),
            ("7 control_vs_si", dict(publica=lambda w, k, U: False, diurno_igual_control=True,
                                     flags_diurno={"ENABLE_DAYTIME_VIIRS": False}), []),
            ("8 noche_distinta", dict(publica=lambda w, k, U: k in U[w]["pos"], cambiar_noche=True), []),
            ("9 cableado_roto", dict(publica=lambda w, k, U: k in U[w]["pos"], flags_diurno={"ENABLE_DAYTIME_VIIRS": False}), []),
            ("10 skip_daytime", dict(publica=lambda w, k, U: k in U[w]["pos"],
                                     linea_extra="  SKIP daytime: VJ102IMG.A2026166.1724.021.2026166190000.nc (solar elev=40.1°)"), []),
            ("10b filtro_de_fetch", dict(publica=lambda w, k, U: k in U[w]["pos"],
                                         linea_extra="  VIIRS_NOAA20: kept 3 of 6 granules (night filter)"), []),
            ("15 lascar_todo", dict(publica=lambda w, k, U: k[0] == "Lascar"), []),
            ("16 g2_un_sensor", dict(publica=lambda w, k, U: k in U[w]["pos"] or k in seis_v750), []),
            ("26 satura_v375", dict(publica=lambda w, k, U: k in U[w]["pos"] or (k[1] == "VIIRS375" and k in U[w]["neg"])), []),
            ("17 volatiles", dict(publica=lambda w, k, U: k in U[w]["pos"], volatiles_distintos=True), []),
            ("18 granulo_distinto", dict(publica=lambda w, k, U: k in U[w]["pos"], granulo_distinto=True), []),
            ("22 ruido_flotante", dict(publica=lambda w, k, U: k in U[w]["pos"], ruido_relativo=2e-16), []),
            ("22b diferencia_real", dict(publica=lambda w, k, U: k in U[w]["pos"], ruido_relativo=1e-6), []),
            # 22c a 22g, del verificador limpio de la vuelta 70: cada uno atrapa una mutación de iguales() que
            # 22b no atrapaba, porque 22b mete el ruido también en el primer nivel.
            ("22c pixel_distinto", dict(publica=lambda w, k, U: k in U[w]["pos"], modificar_noche=lambda n, r: r.update(
                anomaly_pixels=[{"lat": -23.37, "lon": -67.73, "eti": 4.920530419179312e-07 * (1 + (1e-6 if n == "diurno" else 0))}])), []),
            ("22d pixel_extra", dict(publica=lambda w, k, U: k in U[w]["pos"], modificar_noche=lambda n, r: r.update(
                anomaly_pixels=[{"lat": -23.37, "lon": -67.73, "eti": 4.9e-07}] * (2 if n == "diurno" else 1))), []),
            ("22e none_vs_cero", dict(publica=lambda w, k, U: k in U[w]["pos"], modificar_noche=lambda n, r: r.update(
                diag_sd_deti=0.0 if n == "diurno" else None)), []),
            ("22f relativo_1e8", dict(publica=lambda w, k, U: k in U[w]["pos"], ruido_relativo=1e-8), []),
            ("22g absoluto_5e13", dict(publica=lambda w, k, U: k in U[w]["pos"], modificar_noche=lambda n, r: r.update(
                diag_mu_deti=2e-8 + (5e-13 if n == "diurno" else 0.0))), []),
            ("23 orden_pixeles", dict(publica=lambda w, k, U: k in U[w]["pos"], modificar_noche=noche_orden), []),
            ("23b borde_v375_f5", dict(publica=lambda w, k, U: k in U[w]["pos"], modificar_noche=noche_borde(True)), []),
            ("23c borde_v375_sin_f5", dict(publica=lambda w, k, U: k in U[w]["pos"], modificar_noche=noche_borde(False)), []),
            ("23d borde_lista_corta", dict(publica=lambda w, k, U: k in U[w]["pos"], modificar_noche=noche_borde(True, llena=False)), []),
            ("23e borde_fuera_del_corte", dict(publica=lambda w, k, U: k in U[w]["pos"], modificar_noche=noche_borde(True, caliente=True)), []),
            ("24 hotspot_escena", dict(publica=lambda w, k, U: k in U[w]["pos"], modificar_noche=noche_escena(0.4)), []),
            ("24b escena_predicado", dict(publica=lambda w, k, U: k in U[w]["pos"], modificar_noche=noche_escena(0.0)), []),
            ("25 clase_una_noche", dict(publica=lambda w, k, U: k in U[w]["pos"], modificar_noche=noche_clase_una()), []),
            ("19 v750_cerrado", dict(publica=lambda w, k, U: k in U[w]["pos"], sacar=todo_v750), []),
            ("20 tabla_sin_procesar", dict(publica=lambda w, k, U: k in U[w]["pos"], sacar=quince_w5), []),
        ]
        # PROBAR_SOLO=26,1 corre sólo esos casos (por número): sirve para ver el rojo y el verde de un caso nuevo sin
        # esperar la batería entera. La corrida que vale antes de un PR es la completa, sin la variable.
        solo = {x.strip() for x in os.environ.get("PROBAR_SOLO", "").split(",") if x.strip()}
        if solo:
            casos = [c for c in casos if c[0].split()[0] in solo]
            print("PROBAR_SOLO: sólo %s (NO es la batería completa)" % [c[0] for c in casos])
        salidas = {}
        for nombre, kw, extra in casos:
            d = tmp / nombre.split()[0]
            if not d.exists():
                escribir(d, UW, **kw)
            res, txt = correr(d, extra)
            salidas[nombre] = (res, txt)
            print("\n== caso %s -> %s" % (nombre, res["veredicto"]))
            g = res["G2"]
            n = nombre.split()[1]
            if n == "solo_protegidas":
                chequear(n, res["veredicto"].startswith("ADOPTAR"), "veredicto ADOPTAR")
                chequear(n, res["G1_W2W6"]["veredicto"] == "CUMPLE" and res["G1_W3W6"]["veredicto"] == "CUMPLE", "G1 cumple con y sin W2 (D %.3f, p95 %.3f)" % (res["G1_W2W6"]["D"], res["G1_W2W6"]["p95"]))
                chequear(n, all(g[s]["veredicto"] == "CUMPLE" for s in ED.VIIRS), "G2 cumple en los dos sensores (%s)" % {s: (g[s]["publicadas"], g[s]["procesadas"]) for s in ED.VIIRS})
                chequear(n, res["controles_nulo"]["ok"], "controles del nulo: " + res["controles_nulo"]["texto"])
                chequear(n, res["G3"] == "CUMPLE" and res["referencia_ok"] and res["indice_ok"], "G3, referencia e índice OK")
                chequear(n, res["metricas"]["W2-W6"]["ambos"]["M1"]["tasa"] == 1.0 and res["metricas"]["W2-W6"]["ambos"]["M2"]["publicadas"] == 0, "M1 = 1 y M2 = 0")
            elif n == "todo_publica":
                chequear(n, g["VIIRS375"]["veredicto"] == "FALLA" and g["VIIRS750"]["veredicto"] == "FALLA", "G2 FALLA en los dos sensores (p %.2g y %.2g)" % (g["VIIRS375"]["p_valor"], g["VIIRS750"]["p_valor"]))
                chequear(n, res["veredicto"].startswith("NO ADOPTAR"), "veredicto NO ADOPTAR")
                chequear(n, res["metricas"]["W2-W6"]["ambos"]["M2"]["tasa"] == 1.0, "M2 = 1")
            elif n == "azar":
                chequear(n, res["G1_W2W6"]["veredicto"] == "FALLA", "G1 FALLA (D %+.3f, p95 %+.3f)" % (res["G1_W2W6"]["D"], res["G1_W2W6"]["p95"]))
                chequear(n, res["veredicto"].startswith("NO ADOPTAR"), "veredicto NO ADOPTAR")
            elif n == "una_no_procesada":
                k = pos_w2[0]
                m = res["metricas"]["W2-W6"]["ambos"]["M1"]
                chequear(n, res["cls"][k]["estado"] == "no_procesada", "el positivo sin record queda «no procesada» (%s)" % "|".join(k))
                chequear(n, m["procesadas"] == 31 and m["no_procesadas"] == 1 and m["tasa"] == 1.0, "M1 sobre 31 procesados, 1 aparte, M1 = 1 (%s)" % m)
                chequear(n, res["veredicto"].startswith("ADOPTAR"), "1 de 12 en W2 (8 %) no obliga a repetir: veredicto ADOPTAR")
            elif nombre.startswith("5 "):
                chequear(n, res["veredicto"].startswith("PENDIENTE DE REPETICION") and "W3" in res["veredicto"], "W3 con su único positivo sin procesar: PENDIENTE DE REPETICION")
            elif nombre.startswith("5b"):
                chequear(n, "W3" in res["excluidas"] and "W3" not in res["deciden"], "con --repetidas W3, W3 sale del veredicto (cobertura insuficiente)")
                chequear(n, res["veredicto"].startswith("ADOPTAR"), "y el resto decide: ADOPTAR")
            elif n == "solo_w2":
                chequear(n, res["G1_W2W6"]["veredicto"] == "CUMPLE" and res["G1_W3W6"]["veredicto"] == "FALLA", "G1 pasa con W2 y falla sin W2")
                chequear(n, res["veredicto"].startswith("DEPENDE DEL OCR, DECIDE NICOLAS"), "veredicto DEPENDE DEL OCR, DECIDE NICOLAS")
            elif n == "control_vs_si":
                m = res["metricas"]["W2-W6"]["ambos"]
                chequear(n, res["veredicto"].startswith("INDECIDIBLE") and "nulo 1" in res["veredicto"], "INDECIDIBLE por el nulo 1 (el instrumento no puede dar distinto de cero)")
                chequear(n, res["G3"] == "CUMPLE", "noches idénticas (G3)")
                chequear(n, m["M2"]["publicadas"] == 0 and m["M3"]["publicadas"] == 0 and m["M3"]["procesadas"] == 0, "cero publicaciones diurnas (M2 y M3 sin pasadas procesadas: %s)" % {x: m[x] for x in ("M2", "M3")})
            elif n == "noche_distinta":
                chequear(n, res["G3"].startswith("FALLA") and res["veredicto"].startswith("INDECIDIBLE"), "G3 FALLA (%s) e INDECIDIBLE" % res["noches"]["campos_distintos"])
            elif n == "ruido_flotante":
                # W1 real (run 38723828037): diag_mu_deti y diag_sd_deti difieren en ~1e-16 relativo entre runners
                # (la regresión del ETI suma en otro orden); vrp_mw y los píxeles son idénticos. No es cableado.
                chequear(n, res["G3"] == "CUMPLE" and res["veredicto"].startswith("ADOPTAR"),
                         "ruido de punto flotante de 2e-16 no es defecto de cableado (G3 %s)" % res["G3"])
            elif n in ("diferencia_real", "pixel_distinto", "pixel_extra", "none_vs_cero", "relativo_1e8", "absoluto_5e13"):
                chequear(n, res["G3"].startswith("FALLA"),
                         "diferencia real en las noches: G3 FALLA (G3 %s, %s)" % (res["G3"][:20], res["noches"]["campos_distintos"]))
            elif n in ("orden_pixeles", "borde_v375_f5", "hotspot_escena"):
                # Lo que un mismo pipeline produce entre dos runners (desviación D2): se admite y se informa aparte.
                cat = {"orden_pixeles": "orden", "borde_v375_f5": "borde", "hotspot_escena": "hotspot_escena"}[n]
                e = res["noches"]["estados"]
                chequear(n, res["G3"] == "CUMPLE" and e[cat] == res["noches"]["n_control"] > 0 and e["distinto"] == 0,
                         "pares «%s» admitidos e informados: G3 %s, %s" % (cat, res["G3"], e))
                chequear(n, len(res["noches"]["admitidos"][cat]) == e[cat] and "admitido (%s, informa)" % cat in txt,
                         "cada par «%s» queda listado en la salida (%d)" % (cat, len(res["noches"]["admitidos"][cat])))
            elif n in ("borde_v375_sin_f5", "borde_lista_corta", "borde_fuera_del_corte", "escena_predicado", "clase_una_noche"):
                e = res["noches"]["estados"]
                esperado = {"borde_v375_sin_f5": res["noches"]["n_control"], "borde_lista_corta": res["noches"]["n_control"],
                            "borde_fuera_del_corte": res["noches"]["n_control"],
                            "escena_predicado": res["noches"]["n_control"], "clase_una_noche": 1}[n]
                chequear(n, res["G3"].startswith("FALLA") and e["distinto"] == esperado and res["veredicto"].startswith("INDECIDIBLE"),
                         "G3 FALLA con %d pares distintos (esperados %d; %s)" % (e["distinto"], esperado, res["noches"]["campos_distintos"]))
                if n == "escena_predicado":
                    chequear(n, set(res["noches"]["campos_distintos"]) == {"predicado del tablero distinto"},
                             "lo atrapa el predicado del tablero, no comparar (%s)" % res["noches"]["campos_distintos"])
            elif n == "cableado_roto":
                chequear(n, res["veredicto"].startswith("INDECIDIBLE") and "cableado del brazo diurno" in res["veredicto"], "INDECIDIBLE por cableado")
            elif n == "skip_daytime":
                chequear(n, res["veredicto"].startswith("INDECIDIBLE") and "cableado del brazo diurno" in res["veredicto"], "INDECIDIBLE: el log muestra un VIIRS saltado por diurno")
            elif n == "filtro_de_fetch":
                chequear(n, res["veredicto"].startswith("INDECIDIBLE") and "cableado del brazo diurno" in res["veredicto"], "INDECIDIBLE: el log muestra el filtro nocturno de fetch aplicado a VIIRS")
            elif n == "lascar_todo":
                # Publica todo Láscar de día y nada más: dentro del volcán no discrimina. Con el nulo estratificado D
                # queda en el p95 (FALLA); con un nulo sin estratos pasaría (mutación estrato_unico).
                r1 = res["G1_W2W6"]
                chequear(n, r1["veredicto"] == "FALLA", "G1 FALLA (D %+.4f, p95 %+.4f)" % (r1["D"], r1["p95"]))
                chequear(n, res["veredicto"].startswith("NO ADOPTAR"), "veredicto NO ADOPTAR")
            elif n == "satura_v375":
                # S154 (verificador de W2 a W6, H1): con VIIRS 375 saturado y VIIRS 750 callado, el q_neg conjunto queda
                # bajo la banda y el aviso conjunto no salía; en W2 a W6 real 375 estaba en 89,3 % y el conjunto en 60,0 %.
                q = {s: res["metricas"]["W2-W6"][s]["M2"]["tasa"] for s in ED.VIIRS}
                sat = res.get("saturacion", {})
                chequear(n, res["metricas"]["W2-W6"]["ambos"]["M2"]["tasa"] < ED.BANDA_SATURACION <= q["VIIRS375"],
                         "el caso es el de H1: conjunto bajo la banda, 375 sobre ella (%s)" % q)
                chequear(n, sat.get("VIIRS375") is True and sat.get("VIIRS750") is False,
                         "aviso de saturación por sensor: 375 sí, 750 no (%s)" % sat)
                chequear(n, "SATURACIÓN (A114) VIIRS375" in txt, "la línea del aviso nombra el sensor")
            elif n == "g2_un_sensor":
                chequear(n, g["VIIRS375"]["veredicto"] == "CUMPLE" and g["VIIRS750"]["veredicto"] == "FALLA",
                         "G2 cumple en 375 y falla en 750 (%s)" % {s: (g[s]["publicadas"], g[s]["procesadas"]) for s in ED.VIIRS})
                chequear(n, not res["veredicto"].startswith("ADOPTAR") and res["veredicto"].startswith("DECIDE NICOLAS CON M4"),
                         "con G2 en un solo sensor no da ADOPTAR: DECIDE NICOLAS CON M4")
            elif n == "volatiles":
                chequear(n, res["G3"] == "CUMPLE" and res["veredicto"].startswith("ADOPTAR"),
                         "processed_utc y first_processed_utc distintos entre brazos no son defecto de cableado (G3 %s)" % res["G3"])
            elif n == "granulo_distinto":
                chequear(n, res["G3"].startswith("COBERTURA") and res["veredicto"].startswith("INDECIDIBLE"),
                         "otro gránulo en la misma pasada cuenta como cobertura, no como cableado (G3 %s)" % res["G3"][:40])
            elif n == "v750_cerrado":
                chequear(n, res["veredicto"].startswith("INDECIDIBLE") and "VIIRS750" in res["veredicto"],
                         "compuerta de VIIRS 750 cerrada: el nulo 1 por sensor la atrapa (%s)" % res["veredicto"][:90])
            elif n == "tabla_sin_procesar":
                chequear(n, res["veredicto"].startswith("PENDIENTE DE REPETICION") and "W5" in res["veredicto"],
                         "%d pasadas de tabla VIIRS 375 de W5 sin procesar (más del 10 %%): PENDIENTE DE REPETICION antes de G2" % len(quince_w5))

        print("\n== caso 11 g2_borde")
        u375 = ED.umbral_g2(2511, 13 / 2511)
        u750 = ED.umbral_g2(2483, 2 / 2483)
        chequear("g2_borde", (u375, u750) == (20, 6), "a cobertura completa G2 falla desde %d (VIIRS 375) y %d (VIIRS 750); el pre-registro dice 20 y 6" % (u375, u750))
        chequear("g2_borde", ED.binomial_g2(19, 2511, 13 / 2511) >= 0.05 > ED.binomial_g2(20, 2511, 13 / 2511), "19 pasa y 20 falla en VIIRS 375")

        print("\n== caso 12 trampa_a118")
        c = ED.VENTANA["W2"]
        with ED.flag_viirs(False):
            pv, _, _, _ = bp.indexar_referencia(filas, coords, (c["desde"], c["hasta"]))
        univ = UW["W2"]["pos"] | UW["W2"]["tabla"]
        ciegas = [k for k in univ if not bp.parear(pv.get((k[0], k[1]), []), ED.a_dt(k[2]))]
        chequear("trampa_a118", len(ciegas) == len(univ), "con el flag apagado indexar_referencia no ve %d de %d pasadas diurnas de W2" % (len(ciegas), len(univ)))
        txt1 = salidas["1 solo_protegidas"][1]
        chequear("trampa_a118", "flag apagado, filas VIIRS diurnas indexadas: 0" in txt1, "el evaluador lo informa en cada ventana")

        print("\n== caso 13 regla_minimas")
        if not ED.regla_disponible():
            chequear("regla_minimas", salidas["1 solo_protegidas"][0]["regla_minimas"] == "PENDIENTE (PR #820)", "sin la regla en el árbol, la sección queda PENDIENTE")
            cm.aplicar_regla_minimas = lambda filas_, modo: types.SimpleNamespace(filas=list(filas_), minimas=set())
            try:
                res, _ = correr(tmp / "1")
                rm = res["regla_minimas"]
                chequear("regla_minimas", rm["SN"]["veredicto"] == res["veredicto"] == rm["SE"]["veredicto"], "con una regla neutra inyectada, SN y SE informan el mismo veredicto que original (%s)" % rm["SN"]["veredicto"][:20])
            finally:
                del cm.aplicar_regla_minimas
        else:
            res = salidas["1 solo_protegidas"][0]
            chequear("regla_minimas", set(res["regla_minimas"]) == {"SN", "SE"}, "la regla existe: SN y SE informados")

        print("\n== caso 21 control del nulo: tiene que FALLAR con el nulo roto a propósito (verificador del PR #822)")
        cls1 = salidas["1 solo_protegidas"][0]["cls"]
        orig = ED.nulo_barajado
        try:
            for etq, roto in (("sin romper", None),
                              ("nulo x0,3", lambda est, rng, n=ED.N_BARAJADOS: None if orig(est, rng, n) is None else 0.3 * orig(est, rng, n)),
                              ("nulo corrido -0,5", lambda est, rng, n=ED.N_BARAJADOS: None if orig(est, rng, n) is None else orig(est, rng, n) - 0.5)):
                if roto:
                    ED.nulo_barajado = roto
                for caso_cls, nom in ((cls1, "caso 1"), (salidas["3 azar"][0]["cls"], "caso 3")):
                    r = ED.controles_del_nulo(caso_cls, ED.DECIDEN, ED.np.random.default_rng(0))
                    chequear("control_nulo", r["ok"] is (roto is None), "%s, %s: %s -> %s" % (etq, nom, r["texto"], "OK" if r["ok"] else "FALLA"))
        finally:
            ED.nulo_barajado = orig

        print("\n== caso 14 cobertura del workflow (contar_pasadas_noche.py, el paso «recolectar»)")
        import contar_pasadas_noche as CP
        for caso, esperado, txt in (("1", 0, "caso 1: noches parejas, día como se espera -> 0"),
                                    ("7", 1, "caso 7: el brazo diurno sin ninguna pasada VIIRS diurna -> 1 (caso S92)"),
                                    ("19", 1, "caso 19: el brazo diurno sin pasadas diurnas de VIIRS 750 -> 1 (por sensor)"),
                                    ("8", 0, "caso 8: el conteo mira pasadas, no campos; el cambio de campo lo atrapa G3 -> 0")):
            d = tmp / caso
            with contextlib.redirect_stdout(io.StringIO()):
                rc = CP.main(["--control", str(d / ED.BRAZOS["control"]), "--brazo", str(d / ED.BRAZOS["diurno"]),
                              "--inicio", "2026-03-01", "--fin", "2026-10-14"])
            chequear("cobertura_workflow", rc == esperado, "%s (devolvió %d)" % (txt, rc))
        d = tmp / "1"
        js = d / ED.BRAZOS["diurno"] / "Villarrica.json"
        datos = json.loads(js.read_text(encoding="utf-8"))
        datos["records"] = [r for r in datos["records"] if not r["datetime_utc"].endswith(" 06:00")][:]
        js.write_text(json.dumps(datos), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = CP.main(["--control", str(d / ED.BRAZOS["control"]), "--brazo", str(d / ED.BRAZOS["diurno"]),
                          "--inicio", "2026-03-01", "--fin", "2026-10-14"])
        chequear("cobertura_workflow", rc == 1, "al brazo diurno le faltan las noches de Villarrica -> 1 (devolvió %d)" % rc)

        malos = [c for c, ok in RESULTADOS if not ok]
        print("\nAUTOPRUEBA: %d de %d comprobaciones OK%s" % (len(RESULTADOS) - len(malos), len(RESULTADOS),
                                                            "" if not malos else " | FALLAN: %s" % sorted(set(malos))))
        print("\n" + "=" * 100 + "\nSalida completa del evaluador en el caso 1 (solo_protegidas), como ejemplo:\n" + "=" * 100)
        print(salidas["1 solo_protegidas"][1])
        return 1 if malos else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
