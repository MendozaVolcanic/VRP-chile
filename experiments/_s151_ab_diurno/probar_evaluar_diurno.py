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
"""
from __future__ import annotations

import contextlib
import io
import json
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


def escribir(dirc, UW, publica, sacar=(), diurno_igual_control=False, flags_diurno=None, cambiar_noche=False,
             linea_extra="", volatiles_distintos=False, granulo_distinto=False, ruido_relativo=None,
             modificar_noche=None):
    """Escribe <dirc>/<brazo>/<vol>.json y <dirc>/logs/<brazo>_<vol>.log."""
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
    (dirc / "logs").mkdir(parents=True, exist_ok=True)
    for n in ED.BRAZOS:
        (dirc / ED.BRAZOS[n]).mkdir(parents=True, exist_ok=True)
        for vol, recs in por[n].items():
            if not recs:
                continue
            (dirc / ED.BRAZOS[n] / (vol + ".json")).write_text(json.dumps({"volcano": vol, "records": recs}), encoding="utf-8")
            fl = dict(FLAGS_BASE, PROFILE_NAME=ED.BRAZOS[n], DATA_SUBDIR=ED.BRAZOS[n],
                      ENABLE_DAYTIME_VIIRS=(n == "diurno"))
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


def main():
    tmp = Path(tempfile.mkdtemp(prefix="probar_diurno_"))
    try:
        filas, coords = ED.cargar_filas(ED.parser().parse_args(["--raiz", "x"]))
        UW = ED.universo_por_ventana(S.universo(filas, coords))
        print("Universo real del pre-registro: %s" % {w: (len(UW[w]["pos"]), len(UW[w]["neg"]), len(UW[w]["tabla"])) for w in ED.VENTANAS})
        pos_w2 = sorted(UW["W2"]["pos"])
        pos_w3 = sorted(UW["W3"]["pos"])
        rnd = random.Random(7)
        azar = {k for w in ED.VENTANAS for k in UW[w]["pos"] | UW[w]["tabla"] if rnd.random() < 0.30}
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
            ("19 v750_cerrado", dict(publica=lambda w, k, U: k in U[w]["pos"], sacar=todo_v750), []),
            ("20 tabla_sin_procesar", dict(publica=lambda w, k, U: k in U[w]["pos"], sacar=quince_w5), []),
        ]
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
