# -*- coding: utf-8 -*-
"""S168 V375-E: batería del lector de la sombra (PREREGISTRO_E.md §11; arreglos de S169 en §11.11).

Escenas SINTÉTICAS (ningún dato de la ventana P), con el predicado del tablero ejecutado con node, banco_paridad real y
las dependencias del tag sellado (lector de la retrospectiva, evaluar.py, curva_cenit.py, evaluador_comun.py). Cubre cada
función del §11 en verde y en rojo: población y clases, los brazos (escena LEJANA: cercano publica y radiante calla), el
borde (vuelta conjunta y mixta), los controles S0 a S10, la marca de régimen S8, que con un control caído o antes de la
parada no salga nada de la población (VA168-01, VS168-01 y 02), el corte que decide en la noche de la parada, la regla de
criterios con valores fabricados y su cableado en leer_brazo (VS168-08), los controles de la curva del brazo y de K, las
mitades, la parada, y main() de punta a punta sobre carpetas y CSV sintéticos.

Las escenas tienen 2 a 25 noches: para que lleguen a la parada sin fabricar 30 noches, algunas pruebas bajan los umbrales
de la parada con `parada_de_prueba`; las pruebas de `noche_parada` usan los de verdad (30 y 40).
Uso: python -I probar_sombra.py [--dir <carpeta con leer_sombra_v375e.py a probar>]  (exit 0 si todo pasa)
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import importlib.util
import io
import json
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

RES = []
COMMIT = "c42ee0eb709a9df6c6d4bef92cc6b2f6e610775d"


def chk(nombre, cond, detalle=""):
    RES.append(bool(cond))
    print(f"{'PASA ' if cond else 'FALLA'}  {nombre} {'' if cond else detalle}", flush=True)


def cargar(d):
    spec = importlib.util.spec_from_file_location("leer_sombra_v375e", Path(d) / "leer_sombra_v375e.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@contextlib.contextmanager
def parada_de_prueba(LS, noches, alertas):
    viejo = (LS.PARADA_NOCHES, LS.PARADA_ALERTAS)
    LS.PARADA_NOCHES, LS.PARADA_ALERTAS = noches, alertas
    try:
        yield
    finally:
        LS.PARADA_NOCHES, LS.PARADA_ALERTAS = viejo


class Seguro(dict):
    """Un dict del lector en que una clave ausente da un Seguro vacío (falso), para que una mutación que quita una clave
    se vea como aserción fallida y no como caída de la batería."""
    def __missing__(self, k):
        return Seguro()


def seguro(o):
    """Seguro en todos los niveles de un resultado de analizar (los dicts anidados también)."""
    if isinstance(o, dict):
        return Seguro({k: seguro(v) for k, v in o.items()})
    if isinstance(o, list):
        return [seguro(v) for v in o]
    return o


@contextlib.contextmanager
def seccion(nombre):
    """Una excepción dentro de la sección se registra como FALLA con su nombre (no cae la batería entera). La carga del
    lector queda fuera de toda sección: una mutación que rompe la importación sigue siendo CAÍDA."""
    try:
        yield
    except Exception as e:      # noqa: BLE001
        chk(f"sección «{nombre}» sin excepción", False, repr(e)[:300])


class Proxy:
    """Un módulo con algunas funciones reemplazadas (para probar el cableado de leer_brazo, VS168-08)."""
    def __init__(self, base, **f):
        self._b, self._f = base, f

    def __getattr__(self, k):
        return self._f[k] if k in self._f else getattr(self._b, k)


def dia(n):
    return (date(2026, 11, 4) + timedelta(days=n)).isoformat()


REG_K = {"perfil": "mirova_equivalent", "codigo_sha": COMMIT, "origen": "actions"}
REG_VIA = {"perfil": "sombra_codigo_mirova", "codigo_sha": COMMIT, "origen": "actions"}


# ---------------------------------------------------------------- escenas
def rec_via(hora, px, cen, pico, vrp=1.5, inner=5.0, sensor="VIIRS_NOAA20", dc=None):
    pix = [{"lat": -23.37, "lon": -67.73, "dist_km": d, "bt_k": 300.0, "fila": 60 + i, "col": 60 + i}
           for i, d in enumerate(px)]
    r = {"sensor": sensor, "datetime_utc": hora, "via_codigo_mirova": True, "triggered_test1": False,
         "vrp_vent_mw": 0.0, "n_anomalous_pixels": len(pix), "anomaly_pixels": pix, "t_max_k": 300.0,
         "vrp_mw": vrp if pix else 0.0, "sensor_zenith_deg": 20.0, "regimen": dict(REG_VIA)}
    if pix:
        r.update({"distance_class": dc or ("summit" if cen <= inner else "far"), "hotspot_dist_km": pico,
                  "final_hotspot_dist_km": cen, "final_hotspot_source": "codigo_mirova",
                  "primary_cluster": {"vrp_mw": vrp, "n_pixels": len(pix), "centroid_dist_km": cen,
                                      "centroid_lat": -23.37, "centroid_lon": -67.73, "single_pixel_mode": False}})
    else:
        r.update({"distance_class": None, "primary_cluster": None, "hotspot_dist_km": None})
    return r


def rec_k(hora, pub, vrp=1.0, sensor="VIIRS_NOAA20", z=20.0):
    cen = 1.0 if pub else 15.0
    return {"sensor": sensor, "datetime_utc": hora, "triggered_test1": False, "vrp_vent_mw": 0.0, "t_max_k": 300.0,
            "vrp_mw": vrp, "f5_core_vrp_mw": vrp, "distance_class": "summit" if pub else "far",
            "sensor_zenith_deg": z, "n_anomalous_pixels": 2, "anomaly_pixels": [], "regimen": dict(REG_K),
            "primary_cluster": {"vrp_mw": vrp, "n_pixels": 2, "centroid_dist_km": cen, "centroid_lat": -23.37,
                                "centroid_lon": -67.73, "single_pixel_mode": False}}


def entrada(i, hora, clase, sensor="VIIRS_NOAA20", mir=0.0, z=20.0, pub=False, disp=None, vol="Lascar", tabla=True):
    return {"id": i, "volcan": vol, "hora_utc": hora, "noche": hora[:10], "sensor": sensor, "clase": clase,
            "protegida": clase == "pos_prot", "alerta_tabla": tabla, "mirova_vrp": mir, "z": z,
            "estrato": f"{vol}|{'z<=40' if z <= 40 else 'z>40'}", "pub_prod": pub, "disp_k": disp, "dist_ref": None,
            "lote": "P", "partida": False}


def escena(LS, publicar, inner, n_noches=12, lejana_prot=True, borde_km=None, neg_aparte=0, borde_far_km=None):
    """n noches en Láscar desde el 2026-11-04: protegida y alerta bajo 1 MW publicadas por todos, un negativo limpio
    callado, un negativo que K publica, una lejana de la tabla (cercano publica, radiante no) y, si se pide, una
    protegida LEJANA que K publica (radiante la calla: veta a radiante, no a cercano). `neg_aparte`: corre los negativos
    esa cantidad de noches (para main(), donde banco_paridad sólo llama limpio a un negativo de una noche sin alerta).
    `borde_km`: una alerta bajo 1 MW de borde; `borde_far_km`: una lejana de la tabla de borde."""
    pob, via, kfull = [], {}, {}
    inn = inner["Lascar"]
    i = 0
    for n in range(n_noches):
        for h, cl, mir, z, kpub, rv in (
                ("05:00", "pos_prot", 2.0, 10.0, True, rec_via(None, [0.8, 1.2], 1.0, 0.8, 2.0, inn)),
                ("05:30", "pos_bajo", 0.5, 12.0, True, rec_via(None, [0.5], 0.5, 0.5, 0.5, inn)),
                ("06:00", "neg_resto", 0.0, 30.0, False, rec_via(None, [], 0, 0, 0.0, inn)),
                ("06:30", "neg_pub", 0.0, 35.0, True, rec_via(None, [], 0, 0, 0.0, inn)),
                ("07:00", "far_tabla", 0.0, 40.0, True, rec_via(None, [0.4, 15.0, 15.2], 14.9, 15.0, 3.0, inn))):
            hora = f"{dia(n + (neg_aparte if cl.startswith('neg') else 0))} {h}"
            rv["datetime_utc"] = hora
            kr = rec_k(hora, kpub, 1.0, z=z)
            kfull[("Lascar", "VIIRS_NOAA20", hora)] = kr
            via[("Lascar", "VIIRS_NOAA20", hora)] = rv
            pob.append(entrada(i, hora, cl, mir=mir, z=z, pub=kpub))
            i += 1
    extra = []
    if lejana_prot:
        extra.append(("2026-11-05 08:00", "pos_prot", 1.6, rec_via(None, [0.6, 14.0, 14.1], 13.9, 14.0, 1.6, inn)))
    if borde_km is not None:
        extra.append(("2026-11-06 08:00", "pos_bajo", 0.3, rec_via(None, [inn + borde_km], inn + borde_km,
                                                                     inn + borde_km, 0.3, inn)))
    if borde_far_km is not None:
        extra.append(("2026-11-07 08:00", "far_tabla", 0.0, rec_via(None, [inn + borde_far_km, 15.0], 10.0, 15.0, 0.4,
                                                                      inn)))
    for hora, cl, mir, rv in extra:
        rv["datetime_utc"] = hora
        via[("Lascar", "VIIRS_NOAA20", hora)] = rv
        kfull[("Lascar", "VIIRS_NOAA20", hora)] = rec_k(hora, True, 1.0)
        pob.append(entrada(i, hora, cl, mir=mir, pub=True))
        i += 1
    keys = [(o["volcan"], o["sensor"], o["hora_utc"]) for o in pob]
    res = publicar([(kfull[k], inn) for k in keys])
    for o, (disp, pub) in zip(pob, res):
        o["disp_k"], o["pub_prod"] = disp, bool(pub)
    return pob, via, kfull


def sin_cambio(a, b):
    return []


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(AQUI))
    a = ap.parse_args(argv)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    LS = cargar(a.dir)
    import banco_paridad as B
    from clase_mirova import alerta_protegida

    # ---- S0 dependencias
    with seccion("S0 dependencias"):
        deps, malos = LS.cargar_deps()
        chk("S0: las dependencias son las del tag y del sello del lector", deps is not None and not malos, malos)
        clave0 = next(iter(LS.SHA_DEPS))
        viejo = LS.SHA_DEPS[clave0]
        LS.SHA_DEPS[clave0] = "0" * 64
        d2, m2 = LS.cargar_deps()
        LS.SHA_DEPS[clave0] = viejo
        chk("S0: con un sha distinto no carga ninguna", d2 is None and len(m2) == 1, m2)
        chk("S0 (VS168-04): el sello del lector fija banco_paridad, clase_mirova, la referencia, auto_audit_weekly, "
            "la calidad, el cargador del CSV, diurno y el index.html",
            {p.name for p in LS.SHA_SELLO_LECTOR} == {"banco_paridad.py", "clase_mirova.py",
                                                        "referencia_mirova_unificada.py", "auto_audit_weekly.py",
                                                        "calidad_referencia_mirova.py", "mirova_csv_loader.py",
                                                        "diurno.py", "index.html"}, sorted(p.name for p in LS.SHA_SELLO_LECTOR))
        for nom in ("banco_paridad.py", "index.html"):
            cl = next(p for p in LS.SHA_SELLO_LECTOR if p.name == nom)
            vs = LS.SHA_SELLO_LECTOR[cl]
            LS.SHA_SELLO_LECTOR[cl] = "0" * 64
            d3, m3 = LS.cargar_deps()
            LS.SHA_SELLO_LECTOR[cl] = vs
            chk(f"S0 (VS168-04): {nom} distinto del sello no carga nada", d3 is None and len(m3) == 1, m3)
        LP, E = deps["LP"], deps["E"]
        EC, CC = deps["EC"], deps["CC"]
        inner = B.inner_desde_html()

        def publicar(casos):
            return [(x[3], x[4]) for x in B.correr_node([[E.slim(r), inn] for r, inn in casos])]

    # ---- clases (§11.2)
    with seccion("clases (§11.2)"):
        fp_cons = [{"tipo": "FALSO_POSITIVO", "source": "CONS", "vrp_mw": 0.4}]
        fp_ocr = [{"tipo": "FALSO_POSITIVO_OCR", "source": "OCR", "vrp_mw": 0.4}]
        prot = [{"tipo": "ALERTA_TERMICA", "source": "CONS", "vrp_mw": 1.5}]
        bajo = [{"tipo": "ALERTA_TERMICA", "source": "CONS", "vrp_mw": 0.5}]
        cd = lambda lab, ref, pub=False: LS.clase_de({"lab": lab, "pub": pub}, ref, B, alerta_protegida)
        chk("clase: pos con 1,5 MW es pos_prot", cd("pos", prot) == "pos_prot")
        chk("clase: pos con 0,5 MW es pos_bajo", cd("pos", bajo) == "pos_bajo")
        chk("clase: neg_limpio que K publica es neg_pub", cd("neg_limpio", [], True) == "neg_pub")
        chk("clase: neg_limpio que K calla es neg_resto", cd("neg_limpio", [], False) == "neg_resto")
        chk("clase: FALSO_POSITIVO de la tabla es far_tabla", cd("far_ref", fp_cons) == "far_tabla")
        chk("clase: FALSO_POSITIVO sólo del OCR es far_ocr", cd("far_ref", fp_ocr) == "far_ocr")
        chk("clase: minima, sin_geometria y sin_info quedan fuera",
            all(cd(x, bajo) is None for x in ("minima", "sin_geometria", "sin_info")))

    # ---- población: Suomi NPP fuera, otros sensores fuera
    with seccion("población: Suomi NPP fuera, otros sensores fuera"):
        from datetime import datetime, timezone
        dt = datetime(2026, 11, 4, 5, 0, tzinfo=timezone.utc)
        recs = [{"vol": "Lascar", "b": "VIIRS375", "dt": dt, "noche": "2026-11-04", "lab": "pos", "pub": 1, "disp": 1.0,
                 "sensor": "VIIRS_NOAA20", "z": 50.0, "dist_ref": None},
                {"vol": "Lascar", "b": "VIIRS375", "dt": dt, "noche": "2026-11-04", "lab": "pos", "pub": 1, "disp": 1.0,
                 "sensor": "VIIRS_SNPP", "z": 10.0, "dist_ref": None},
                {"vol": "Lascar", "b": "MODIS", "dt": dt, "noche": "2026-11-04", "lab": "pos", "pub": 1, "disp": 1.0,
                 "sensor": "MODIS_AQUA", "z": 10.0, "dist_ref": None},
                {"vol": "Lascar", "b": "VIIRS375", "dt": dt, "noche": "2026-11-04", "lab": "sin_info", "pub": 0,
                 "disp": 0.0, "sensor": "VIIRS_NOAA21", "z": 10.0, "dist_ref": None}]
        por_vb = {("Lascar", "VIIRS375"): [(dt, {"tipo": "ALERTA_TERMICA", "source": "CONS", "vrp_mw": 1.5,
                                                 "fecha_utc": "2026-11-04 05:00:10"})]}
        pob0, fuera0, snpp0 = LS.poblacion(recs, por_vb, B, alerta_protegida)
        chk("población: una pasada, protegida, con su estrato de cenit, mirova_vrp y tabla",
            len(pob0) == 1 and pob0[0]["clase"] == "pos_prot" and pob0[0]["estrato"] == "Lascar|z>40"
            and pob0[0]["mirova_vrp"] == 1.5 and pob0[0]["alerta_tabla"] and pob0[0]["id"] == 0, pob0)
        chk("población: Suomi NPP fuera y contado; MODIS fuera; sin_info contado",
            snpp0 == 1 and fuera0 == {"sin_info": 1}, (snpp0, fuera0))

    # ---- escena principal
    with seccion("escena principal"):
        pob, via, kfull = escena(LS, publicar, inner)
        arms, info = LS.brazos(pob, via, inner, publicar, LP)
        lej = next(o for o in pob if o["hora_utc"] == "2026-11-05 08:00")
        far1 = next(o for o in pob if o["clase"] == "far_tabla")
        neg1 = next(o for o in pob if o["clase"] == "neg_resto")
        chk("brazos: protegida LEJANA, cercano publica y radiante calla",
            arms[lej["id"]][LS.DECIDE][0] and not arms[lej["id"]][("VIA", "radiante")][0], arms[lej["id"]])
        chk("brazos: lejana de la tabla, cercano publica y radiante calla",
            arms[far1["id"]][LS.DECIDE][0] and not arms[far1["id"]][("VIA", "radiante")][0])
        chk("brazos: sin alertados nadie publica y sinfiltro tampoco",
            not any(v[0] for v in arms[neg1["id"]].values()))
        chk("brazos: sinfiltro publica toda pasada con alertado, con su VRP",
            arms[far1["id"]][("VIA", "sinfiltro")] == (True, 3.0, 3))
        chk("brazos: magnitud mostrada del brazo es el VRP de la vía (suma de todos)",
            abs(arms[lej["id"]][LS.DECIDE][1] - 1.6) < 1e-9, arms[lej["id"]][LS.DECIDE])
        chk("brazos: distancias desde el record", info[lej["id"]]["dist"] == {"radiante": 13.9, "pico": 14.0,
                                                                              "cercano": 0.6})
        p_sin = dict(pob[0], id=999, hora_utc="2026-11-30 05:00")
        a2, i2 = LS.brazos(pob + [p_sin], via, inner, publicar, LP)
        chk("brazos: pasada sin record de la vía no entra", 999 not in a2 and 999 not in i2)

    # ---- controles
    with seccion("controles"):
        chk("S1: ventana desde 2026-11-03 OK", LS.control_s1("2026-11-03", "2026-11-20", pob)[0])
        chk("S1: desde antes del 2026-11-03 cae", not LS.control_s1("2026-11-02", "2026-11-20", pob)[0])
        chk("S1 (VS168-01): desde DESPUÉS del 2026-11-03 también cae",
            not LS.control_s1("2026-11-10", "2026-11-20", [o for o in pob if o["noche"] >= "2026-11-10"])[0])
        chk("S1: pasada fuera de la ventana cae", not LS.control_s1("2026-11-03", "2026-11-05", pob)[0])
        chk("S1: clave repetida cae", not LS.control_s1("2026-11-03", "2026-11-20", pob + [dict(pob[0], id=500)])[0])
        chk("S1: hasta antes de desde cae", not LS.control_s1("2026-11-03", "2026-11-02", [])[0])
        ok2, r2 = LS.control_s2(pob, via, inner, publicar, LP)
        chk("S2: summit, far, summit da [True, False, True]", ok2 and r2 == [True, False, True], r2)
        vacios = {k: rec_via(k[2], [], 0, 0, 0.0) for k in via}
        chk("S2: sin pasada de la vía con VRP cae", not LS.control_s2(pob, vacios, inner, publicar, LP)[0])
        llamadas = []

        def pub_tarde(casos):
            llamadas.append(1)
            return [(0.0, False)] * len(casos) if len(llamadas) == 1 else publicar(casos)
        chk("S2: si la primera pasada no publica en summit, prueba con las siguientes",
            LS.control_s2(pob, via, inner, pub_tarde, LP)[0] and len(llamadas) == 2, llamadas)
        chk("S2: un predicado que no responde a la clase cae",
            not LS.control_s2(pob, via, inner, lambda c: [(1.0, True)] * len(c), LP)[0])
        ok3, d3 = LS.control_s3(info)
        chk("S3: pasadas de un alertado, radiante y cercano a 0,0051 km o menos", ok3 and d3["n"] > 0, d3)
        info_m = {k: dict(v) for k, v in info.items()}
        k1 = next(k for k, v in info_m.items() if v["npix"] == 1)
        info_m[k1] = dict(info_m[k1], dist={"radiante": 0.52, "cercano": 0.5, "pico": 0.5})
        chk("S3: una diferencia de 0,02 km cae", not LS.control_s3(info_m)[0])
        info_t = {k: dict(v) for k, v in info.items()}
        info_t[k1] = dict(info_t[k1], dist={"radiante": 0.5062, "cercano": 0.5, "pico": 0.5})
        chk("S3: una diferencia de 0,0062 km cae (tolerancia 0,0051)", not LS.control_s3(info_t)[0])
        info_u = {k: dict(v) for k, v in info.items()}
        info_u[k1] = dict(info_u[k1], dist={"radiante": 0.5048, "cercano": 0.5, "pico": 0.5})
        chk("S3: una diferencia de 0,0048 km pasa", LS.control_s3(info_u)[0])
        chk("S3: sin pasadas de un alertado cae", not LS.control_s3({k: v for k, v in info.items() if v["npix"] != 1})[0])
        chk("S4: radiante tiene la clase del record", LS.control_s4(pob, info, inner, LP)[0])
        info_c = {k: dict(v) for k, v in info.items()}
        info_c[lej["id"]] = dict(info_c[lej["id"]], dc="summit")
        chk("S4: una clase distinta cae", not LS.control_s4(pob, info_c, inner, LP)[0])
        chk("S4: sin pasadas con alertados cae", not LS.control_s4(pob, {}, inner, LP)[0])
        inn_l = inner["Lascar"]
        info_r = {k: dict(v) for k, v in info.items()}
        info_r[lej["id"]] = dict(info_r[lej["id"]], dc="summit", dist=dict(info_r[lej["id"]]["dist"], radiante=inn_l + 0.0004))
        ok4r, d4r = LS.control_s4(pob, info_r, inner, LP)
        chk("S4 (VS168-10): radiante a 0,0004 km del radio con otra clase se excluye y no cae",
            ok4r and d4r["excluidas_por_redondeo"] == 1, d4r)
        info_r2 = {k: dict(v) for k, v in info.items()}
        info_r2[lej["id"]] = dict(info_r2[lej["id"]], dc="summit", dist=dict(info_r2[lej["id"]]["dist"], radiante=inn_l + 0.002))
        chk("S4 (VS168-10): a 0,002 km del radio con otra clase sí cae", not LS.control_s4(pob, info_r2, inner, LP)[0])
        ok5, d5 = LS.control_s5(pob, kfull, inner, publicar, LP)
        chk("S5: PLACEBO K x 1,2 publica igual que K", ok5 and d5["n"] == len(pob), d5)
        chk("S5: sin records de K cae (0 de 0 no prueba nada)", not LS.control_s5(pob, {}, inner, publicar, LP)[0])
        chk("S5: si K x 1,2 publica distinto cae",
            not LS.control_s5(pob, kfull, inner, lambda c: [(1.0, True)] * len(c), LP)[0])
        filas0 = LS.filas_de(pob, arms, E)
        marco0 = [x for x in filas0 if x["c"] not in LP.CLASES_FAR]
        ok6, d6 = LS.control_s6(marco0, LP, EC)
        chk("S6 (VS168-08): el placebo de M sin MEJORA y con sustrato pasa, e informa sus pares",
            ok6 and d6["pares"] >= 5 and d6["noches"] >= 3, d6)
        fake_ec = Proxy(EC, placebo_ganancia=lambda P, modo: {"1.2": {"sin_comparador": "MEJORA", "con_comparador": "MEJORA"},
                                                              "0.8": {"sin_comparador": "NEUTRO", "con_comparador": "NEUTRO"}})
        chk("S6 (VS168-08): un placebo que da MEJORA cae", not LS.control_s6(marco0, LP, fake_ec)[0])
        chk("S6 (VS168-08): sin sustrato (dos noches) cae aunque no dé MEJORA",
            not LS.control_s6([x for x in marco0 if x["noche"] <= "2026-11-05"], LP, EC)[0])
        ok7, d7 = LS.control_s7(pob, arms)
        chk("S7: cobertura completa OK", ok7 and all(v["sin_dato"] == 0 for v in d7.values()), d7)
        id_prot = next(o["id"] for o in pob if o["clase"] == "pos_prot")
        falta = {k: v for k, v in arms.items() if k != id_prot}
        chk("S7: una protegida sin dato en 13 (7,7 %) no cae", LS.control_s7(pob, falta)[0])
        sin2 = [o["id"] for o in pob if o["clase"] == "pos_prot"][:2]
        chk("S7: dos protegidas sin dato en 13 (más del 10 %) cae",
            not LS.control_s7(pob, {k: v for k, v in arms.items() if k not in sin2})[0])
        chk("S7: población vacía cae", not LS.control_s7([], {})[0])
        pob9 = [o for o in pob if o["noche"] <= "2026-11-11"]
        uno9 = next(o["id"] for o in pob9 if o["clase"] == "pos_prot")
        chk("S7: una protegida sin dato en 9 (11,1 %, sobre el umbral del 10 %) cae",
            sum(o["clase"] == "pos_prot" for o in pob9) == 9
            and not LS.control_s7(pob9, {k: v for k, v in arms.items() if k != uno9})[0])
        sin_o = [o["id"] for o in pob if o["clase"] == "far_tabla"][:2]
        chk("S7: far_tabla también decide la cobertura",
            not LS.control_s7(pob, {k: v for k, v in arms.items() if k not in sin_o})[0])
        chk("S7: la lista de SIN DATO va completa (sin truncar)",
            len(LS.control_s7(pob, {k: v for k, v in arms.items() if k not in
                                    {o["id"] for o in pob if o["clase"] == "pos_bajo"}})[1]["pos_bajo"]["lista"]) == 12)
        ok10, d10 = LS.control_s10(info)
        chk("S10 (VS168-11): sin alertados sin distancias pasa", ok10 and d10["n"] == 0, d10)
        info_10 = dict(info)
        info_10[far1["id"]] = dict(info[far1["id"]], dist=None)
        chk("S10 (VS168-11): una pasada con alertados y sin distancias cae", not LS.control_s10(info_10)[0])
        rv_sd = dict(via[(far1["volcan"], far1["sensor"], far1["hora_utc"])])
        rv_sd["anomaly_pixels"] = [dict(p, dist_km=None) for p in rv_sd["anomaly_pixels"]]
        _, info_sd = LS.brazos([far1], {(far1["volcan"], far1["sensor"], far1["hora_utc"]): rv_sd}, inner, publicar, LP)
        chk("S10 (VS168-11): brazos deja dist None si un alertado no trae dist_km, y S10 lo ve",
            info_sd[far1["id"]]["dist"] is None and not LS.control_s10(info_sd)[0], info_sd)
        chk("S9 (VS168-05): tabla hasta 2 días después del corte pasa",
            LS.control_s9("2026-12-05 03:00:00", "2026-12-03")[0])
        chk("S9 (VS168-05): tabla hasta 1 día después del corte cae",
            not LS.control_s9("2026-12-04 23:59:00", "2026-12-03")[0])
        chk("S9 (VS168-05): sin filas de la tabla cae", not LS.control_s9(None, "2026-12-03")[0])
        # S8 marca de régimen
        rk_ok = [dict(regimen=dict(REG_K))]
        rv_ok = [dict(regimen=dict(REG_VIA))]
        ok8, d8 = LS.control_s8(rk_ok, rv_ok, COMMIT, sin_cambio)
        chk("S8 (VS168-04): mismo régimen, sin cambio", ok8 and not d8["cambios"], d8)
        otro = "f" * 40
        ok8b, d8b = LS.control_s8(rk_ok + [dict(regimen=dict(REG_K, codigo_sha=otro))], rv_ok, COMMIT,
                                  lambda x, y: ["pipeline/process_viirs.py"] if y == otro else [])
        chk("S8 (VS168-04): un commit de los records que cambia pipeline/ marca", not ok8b and otro in d8b["cambios"], d8b)
        chk("S8 (VS168-04): compara contra c42ee0eb7 (un record de otro commit sin cambios contra la base no marca)",
            LS.control_s8(rk_ok + [dict(regimen=dict(REG_K, codigo_sha=otro))], rv_ok, COMMIT,
                          lambda x, y: [] if x == COMMIT else ["x"])[0])
        chk("S8 (VS168-04): el --commit también se compara",
            not LS.control_s8(rk_ok, rv_ok, otro, lambda x, y: ["pipeline/x.py"] if y == otro else [])[0])
        chk("S8 (VS168-04): un sha que git no resuelve marca", not LS.control_s8(rk_ok, rv_ok, COMMIT, lambda x, y: None)[0])
        chk("S8 (VS168-04): un record sin régimen marca", not LS.control_s8(rk_ok + [{}], rv_ok, COMMIT, sin_cambio)[0])
        chk("S8 (VS168-04): un perfil de la vía distinto marca",
            not LS.control_s8(rk_ok, [dict(regimen=dict(REG_VIA, perfil="mirova_equivalent"))], COMMIT, sin_cambio)[0])
        chk("S8 (VS168-04): un perfil de K distinto marca",
            not LS.control_s8([dict(regimen=dict(REG_K, perfil="experimental"))], rv_ok, COMMIT, sin_cambio)[0])
        chk("S8 (VS168-04): diff_git ve que c42ee0eb7 contra sí mismo no cambia pipeline/",
            LS.diff_git(COMMIT, COMMIT) == [], LS.diff_git(COMMIT, COMMIT))
        chk("S8 (VS168-04): diff_git devuelve None con un sha inexistente", LS.diff_git(COMMIT, "0" * 40) is None)

    # ---- analizar: VA168-01, con un control caído no sale nada de la población
    with seccion("analizar: VA168-01, con un control caído no sale nada de la población"):
        res_f, fal_f = LS.analizar(pob, via, kfull, inner, publicar, deps, "2026-11-02", "2026-11-20", commit=COMMIT,
                                   diff_fn=sin_cambio)
        res_f = seguro(res_f)
        chk("VA168-01: S1 caído, analizar devuelve sólo controles y el corte",
            fal_f == ["S1"] and set(res_f) == {"controles", "corte", "hasta_pedido", "parada_alcanzada"},
            (fal_f, list(res_f)))
        via10 = dict(via)
        k10 = (far1["volcan"], far1["sensor"], far1["hora_utc"])
        via10[k10] = dict(via[k10], anomaly_pixels=[dict(p, dist_km=None) for p in via[k10]["anomaly_pixels"]])
        res_10, fal_10 = LS.analizar(pob, via10, kfull, inner, publicar, deps, "2026-11-03", "2026-11-20", commit=COMMIT,
                                     diff_fn=sin_cambio)
        res_10 = seguro(res_10)
        chk("S10 (VS168-11): en analizar, una pasada con alertados sin distancias hace caer la lectura",
            fal_10 == ["S10"] and "parada" not in res_10, fal_10)
        res_i, fal_i = LS.analizar(pob, via, kfull, inner, publicar, deps, "2026-11-03", "2026-11-20", identidad_ok=False,
                                   commit=COMMIT, diff_fn=sin_cambio)
        res_i = seguro(res_i)
        chk("S2: la identidad del predicado caída hace caer S2", fal_i == ["S2"] and "brazos" not in res_i, fal_i)
        res_p, fal_p = LS.analizar(pob, via, kfull, inner, publicar, deps, "2026-11-03", "2026-11-20", commit=COMMIT,
                                   diff_fn=sin_cambio)
        res_p = seguro(res_p)
        chk("VS168-01: antes de la parada (30 y 40) analizar no lee: sólo controles y contadores",
            fal_p == [] and "brazos" not in res_p and "estado" not in res_p
            and res_p["parada"] == {"noches": 12, "alertas": 25, "alcanzada": False, "noche": None}, (fal_p, list(res_p)))
        chk("VS168-01: antes de la parada no corre S9", "S9" not in res_p["controles"], list(res_p["controles"]))
        p2n, v2n, k2n = escena(LS, publicar, inner, n_noches=2)
        with parada_de_prueba(LS, 2, 4):
            res_6, fal_6 = LS.analizar(p2n, v2n, k2n, inner, publicar, deps, "2026-11-03", "2026-11-20",
                                       ultima_tabla="2026-12-30 00:00:00", commit=COMMIT, diff_fn=sin_cambio)
            res_6 = seguro(res_6)
        chk("S6 (VS168-08): en analizar, S6 sin sustrato hace caer la lectura", fal_6 == ["S6"] and "brazos" not in res_6,
            fal_6)
        with parada_de_prueba(LS, 12, 20):
            res_9, fal_9 = LS.analizar(pob, via, kfull, inner, publicar, deps, "2026-11-03", "2026-11-20",
                                       ultima_tabla="2026-11-16 00:00:00", commit=COMMIT, diff_fn=sin_cambio)
            res_9 = seguro(res_9)
        chk("S9 (VS168-05): en analizar, con la parada alcanzada la referencia fresca hace caer la lectura",
            fal_9 == ["S9"] and "brazos" not in res_9 and res_9["parada_alcanzada"] and res_9["corte"] == "2026-11-15",
            (fal_9, res_9.get("corte")))

        with parada_de_prueba(LS, 12, 20):
            res, fal = LS.analizar(pob, via, kfull, inner, publicar, deps, "2026-11-03", "2026-11-20",
                                   ultima_tabla="2026-12-30 00:00:00", commit=COMMIT, diff_fn=sin_cambio)
            res = seguro(res)
        chk("analizar: escena principal con la parada alcanzada, sin controles caídos", fal == [], fal)
        br = res["brazos"]
        chk("VS168-01: el corte que decide es la noche de la parada (recortado desde el 2026-11-20)",
            res["corte"] == "2026-11-15" and res["hasta_pedido"] == "2026-11-20" and res["parada"]["noche"] == "2026-11-15",
            (res["corte"], res["parada"]))
        chk("S9 y S10 corren con la parada alcanzada", res["controles"]["S9"]["ok"] and res["controles"]["S10"]["ok"])
        chk("(a): radiante calla la protegida LEJANA que K publica y no cumple",
            br[("VIA", "radiante")]["P1_veta"] == [("Lascar", "2026-11-05 08:00")]
            and br[("VIA", "radiante")]["criterios"]["a"] == LS.NO_CUMPLE, br[("VIA", "radiante")]["P1_veta"])
        chk("(a): cercano no calla ninguna y cumple", br[LS.DECIDE]["P1_veta"] == []
            and br[LS.DECIDE]["criterios"]["a"] == LS.CUMPLE)
        chk("lejanas: cercano publica las 12 far_tabla, radiante 0, K 12",
            br[LS.DECIDE]["lejanas"]["publica"] == 12 and br[("VIA", "radiante")]["lejanas"]["publica"] == 0
            and res["lejanas_K"]["far_tabla"]["publica"] == 12,
            (br[LS.DECIDE]["lejanas"]["publica"], res["lejanas_K"]["far_tabla"]["publica"]))
        chk("lejanas (VS168-12): far_ocr se informa por brazo y para K",
            br[LS.DECIDE]["lejanas_ocr"]["n"] == 0 and res["lejanas_K"]["far_ocr"]["n"] == 0)
        chk("(b): P2-L de radiante contra K gana (calla donde K publica)",
            br[("VIA", "radiante")]["P2L_K"]["veredicto"] == "GANA", br[("VIA", "radiante")]["P2L_K"])
        chk("(b): P2-L de cercano contra K empata en bloques (publica igual que K)",
            br[LS.DECIDE]["P2L_K"]["B"] == 0, br[LS.DECIDE]["P2L_K"])
        chk("(b) por valor (VS168-08): cercano calla los neg_pub de K, P2 GANA, silencio acotado y (b) CUMPLE",
            br[LS.DECIDE]["P2_K"]["veredicto"] == "GANA" and br[LS.DECIDE]["silencio"] == "SILENCIO ACOTADO BAJO K"
            and br[LS.DECIDE]["criterios"]["b"] == LS.CUMPLE and not br[LS.DECIDE]["b_sin_evidencia"],
            (br[LS.DECIDE]["P2_K"]["veredicto"], br[LS.DECIDE]["silencio"], br[LS.DECIDE]["criterios"]))
        chk("(c) por valor (VS168-08): el estado de (c) sale del veredicto de M por la tabla de §11.6",
            br[LS.DECIDE]["criterios"]["c"] == {"MEJORA": LS.CUMPLE, "NEUTRO": LS.CUMPLE, "SIN SUSTRATO": LS.NICOLAS}.get(
                str(br[LS.DECIDE]["M"]["veredicto"]), LS.NO_CUMPLE), (br[LS.DECIDE]["M"]["veredicto"], br[LS.DECIDE]["criterios"]))
        chk("(d) por valor (VS168-08): curva sin sustrato da (d) DECIDE NICOLAS y el estado también",
            br[LS.DECIDE]["curva"]["condicionada"]["veredicto"] == "SIN SUSTRATO"
            and br[LS.DECIDE]["criterios"]["d"] == LS.NICOLAS and res["estado"] == LS.NICOLAS,
            (br[LS.DECIDE]["curva"]["condicionada"], br[LS.DECIDE]["criterios"]))
        chk("N-3: en la ventana P no toca ninguna fila", br[LS.DECIDE]["n3_filas"] == [])
        chk("parada: 12 noches y 25 alertas con la parada de prueba", res["parada"]["noches"] == 12
            and res["parada"]["alertas"] == 25 and res["parada"]["alcanzada"], res["parada"])
        chk("borde: sin pasadas de borde, estado sin motivo", res["borde"] == [] and res["motivo"] == "")
        chk("régimen (S8): sin cambio en la escena", res["regimen"]["sin_cambio"])
        chk("VS168-07: los controles de la curva de K se calculan", "d0" in res["controles_curva_K"])
        chk("mitades: corte en la noche de la mediana (6 de 12 en la primera)",
            br[LS.DECIDE]["mitades"]["corte_noche"] == "2026-11-09", br[LS.DECIDE]["mitades"]["corte_noche"])
        chk("mitades: la primera tiene las noches hasta el corte y la segunda las posteriores",
            br[LS.DECIDE]["mitades"]["primera"]["n"] == 25 and br[LS.DECIDE]["mitades"]["segunda"]["n"] == 24,
            br[LS.DECIDE]["mitades"])
        chk("(c): M lee los pares de cercano con el evaluador común", br[LS.DECIDE]["M"]["n"] > 0, br[LS.DECIDE]["M"]["n"])
        chk("informan: radiante y P-sinfiltro están en la lectura", set(br) == {LS.DECIDE, ("VIA", "radiante"),
                                                                               ("VIA", "sinfiltro")}, list(br))

    # ---- cableado de leer_brazo (VS168-08) y criterios nuevos (VS168-03, 06, 07)
    with seccion("cableado de leer_brazo (VS168-08) y criterios nuevos (VS168-03, 06, 07)"):
        filas_p = LS.filas_de(pob, arms, E)
        Nn = {"neg_pub": 12, "neg_resto": 12}
        cur = {"condicionada": {"veredicto": "REPRODUCE LA CURVA", "d": [1.0, [0.9, 1.1]]}}
        cur_k = {"condicionada": {"veredicto": "SIN SUSTRATO", "d": [None, [None, None]]}}
        p2 = lambda filas, a, ref: {"veredicto": "PIERDE", "neto": 9.0, "B": 9, "p": None}
        p2l = lambda filas, a, ref, E_, f: {"veredicto": "GANA", "neto": -9.0, "B": 9, "p": None}
        mag = lambda filas, a, EC_, v="EMPEORA": {"veredicto": v, "n": 9, "salen_publica_uno": 0, "detalle": {},
                                                  "informa": {}}
        curva = lambda filas, a, E_, CC_: cur if a != "K" else cur_k
        LPx = Proxy(LP, p2_con=p2l, magnitud=mag, curva=curva)
        Ex = Proxy(E, p2=p2)
        dx = dict(deps, LP=LPx, E=Ex)
        rx = LS.leer_brazo(filas_p, LS.DECIDE, dx, Nn, 0.5, [], False, True)
        chk("cableado (VS168-08): P2 PIERDE da (b) NO CUMPLE aunque P2-L GANE",
            rx["criterios"]["b"] == LS.NO_CUMPLE and rx["P2_K"]["veredicto"] == "PIERDE", rx["criterios"])
        chk("cableado (VS168-08): M EMPEORA da (c) NO CUMPLE", rx["criterios"]["c"] == LS.NO_CUMPLE, rx["criterios"])
        chk("cableado (VS168-08): la curva del brazo REPRODUCE y la de K sin sustrato dan (d) CUMPLE (orden de los "
            "argumentos de estado_d_sombra)", rx["criterios"]["d"] == LS.CUMPLE, rx["criterios"])
        chk("cableado: el estado con (b) y (c) en NO CUMPLE es NO CUMPLE", rx["criterios"]["estado"] == LS.NO_CUMPLE)
        rx2 = LS.leer_brazo(filas_p, LS.DECIDE, dict(dx, E=Proxy(E, p2=lambda f, a, r: {"veredicto": "GANA", "neto": -9.0,
                                                                                        "B": 9, "p": None}),
                                                     LP=Proxy(LP, p2_con=lambda f, a, r, E_, g: {"veredicto": "PIERDE",
                                                                                                 "neto": 9.0, "B": 9,
                                                                                                 "p": None},
                                                              magnitud=lambda f, a, EC_: mag(f, a, EC_, "SIN SUSTRATO"),
                                                              curva=curva)),
                            Nn, 0.5, [], False, True)
        chk("cableado (VS168-08): P2-L PIERDE da (b) NO CUMPLE aunque P2 GANE", rx2["criterios"]["b"] == LS.NO_CUMPLE,
            rx2["criterios"])
        chk("(c) (VS168-06): M SIN SUSTRATO en la sombra da (c) DECIDE NICOLAS, no NO CUMPLE",
            rx2["criterios"]["c"] == LS.NICOLAS, rx2["criterios"])
        rx3 = LS.leer_brazo(filas_p, LS.DECIDE, dict(dx, LP=Proxy(LP, magnitud=lambda f, a, EC_: mag(f, a, EC_, "MEJORA"),
                                                                  curva=curva)), Nn, 0.5, [], True, True)
        chk("(d) (VS168-07): un control de la curva de K caído lleva (d) a DECIDE NICOLAS",
            rx3["criterios"]["d"] == LS.NICOLAS and rx3["criterios"]["c"] == LS.CUMPLE, rx3["criterios"])
        rx4 = LS.leer_brazo(filas_p, LS.DECIDE, dict(deps, LP=Proxy(LP, magnitud=lambda f, a, EC_: mag(f, a, EC_, "MEJORA"),
                                                                  curva=curva)), Nn, 0.5, [], False, False)
        chk("S8 (VS168-04): con la marca de régimen los CUMPLE de (c) y (d) pasan a DECIDE NICOLAS",
            rx4["criterios"]["c"] == LS.NICOLAS and rx4["criterios"]["d"] == LS.NICOLAS
            and rx4["criterios"]["estado"] == LS.NICOLAS, rx4["criterios"])
        o_sd = next(o for o in pob if o["clase"] == "pos_prot")
        rx5 = LS.leer_brazo(filas_p, LS.DECIDE, deps, Nn, 0.5, [dict(o_sd, hora_utc="2026-11-29 05:00", pub_prod=True),
                                                             dict(o_sd, hora_utc="2026-11-29 06:00", pub_prod=False)],
                            False, True)
        chk("(a) (VS168-03): una protegida SIN DATO que K publica veta",
            ("Lascar", "2026-11-29 05:00") in rx5["P1_veta"] and rx5["criterios"]["a"] == LS.NO_CUMPLE, rx5["P1_veta"])
        chk("(a) (VS168-03): una SIN DATO que K calla no veta pero se lista con las otras",
            ("Lascar", "2026-11-29 06:00") not in rx5["P1_veta"]
            and rx5["P1_sin_dato"] == [("Lascar", "2026-11-29 05:00", "K publica"), ("Lascar", "2026-11-29 06:00", "K calla")],
            rx5["P1_sin_dato"])
        rx6 = LS.leer_brazo(filas_p, LS.DECIDE, dict(dx, E=Proxy(E, p2=lambda f, a, r: {"veredicto": "SIN SUSTRATO",
                                                                                        "neto": 0.0, "B": 0, "p": None}),
                                                     LP=Proxy(LP, p2_con=p2l, magnitud=mag, curva=curva)),
                            {"neg_pub": 0, "neg_resto": 12}, 0.0, [], False, True)
        chk("(b) sin neg_pub (VS168-08): el silencio queda SIN SUSTRATO, sin lecturas, y el CUMPLE se rotula por falta de "
            "evidencia", rx6["lecturas"] is None and rx6["silencio"].startswith("SIN SUSTRATO")
            and rx6["criterios"]["b"] == LS.CUMPLE and rx6["b_sin_evidencia"], (rx6["silencio"], rx6["criterios"]))

    # ---- régimen y protegida SIN DATO a nivel de analizar (con la parada de prueba)
    with seccion("régimen y protegida SIN DATO a nivel de analizar (con la parada de prueba)"):
        p6, v6, k6 = escena(LS, publicar, inner, n_noches=6)
        otro_sha = "e" * 40
        for k in list(k6)[:3]:
            k6[k] = dict(k6[k], regimen=dict(REG_K, codigo_sha=otro_sha))
        with parada_de_prueba(LS, 6, 10):
            r6, f6 = LS.analizar(p6, v6, k6, inner, publicar, deps, "2026-11-03", "2026-11-20",
                                 ultima_tabla="2026-12-30 00:00:00", commit=COMMIT,
                                 diff_fn=lambda x, y: ["pipeline/store.py"] if y == otro_sha else [])
            r6 = seguro(r6)
        chk("S8 en analizar (VS168-04): un record de otro régimen marca la lectura y sus CUMPLE de (b) pasan a DECIDE "
            "NICOLAS", f6 == [] and not r6["regimen"]["sin_cambio"] and otro_sha in r6["regimen"]["detalle"]["cambios"]
            and r6["brazos"][LS.DECIDE]["criterios"]["b"] == LS.NICOLAS and r6["estado"] != LS.CUMPLE,
            (f6, r6.get("regimen"), r6.get("brazos", {}).get(LS.DECIDE, {}).get("criterios")))
        chk("S8 en analizar: la marca se aplica a los brazos que informan también (no imprimen estado, pero el JSON lo "
            "omite)", "criterios" not in seguro(LS.para_json(r6, "decide"))["brazos"][("VIA", "radiante")]
            and "criterios" in seguro(LS.para_json(r6, "decide"))["brazos"][LS.DECIDE])

    # ---- borde (VA168-08 y VS168-09)
    with seccion("borde (VA168-08 y VS168-09)"):
        pb, vb, kb = escena(LS, publicar, inner, n_noches=6, borde_km=-0.003, borde_far_km=-0.002)
        ab, ib = LS.brazos(pb, vb, inner, publicar, LP)
        idb = next(o["id"] for o in pb if o["hora_utc"] == "2026-11-06 08:00")
        idf = next(o["id"] for o in pb if o["hora_utc"] == "2026-11-07 08:00")
        chk("borde: cercano a 0,003 km dentro del radio es de borde (y la lejana a 0,002 km también)",
            LS.borde(pb, ib, inner) == sorted([idb, idf]), LS.borde(pb, ib, inner))
        pc, vc, kc = escena(LS, publicar, inner, n_noches=2, borde_km=-0.02)
        _, ic = LS.brazos(pc, vc, inner, publicar, LP)
        chk("borde: a 0,02 km dentro no es de borde", LS.borde(pc, ic, inner) == [])
        pd_, vd, kd = escena(LS, publicar, inner, n_noches=2, borde_km=0.004)
        _, idd = LS.brazos(pd_, vd, inner, publicar, LP)
        chk("borde: a 0,004 km fuera también es de borde", len(LS.borde(pd_, idd, inner)) == 1)
        pe, ve, ke = escena(LS, publicar, inner, n_noches=2, borde_km=0.0045)
        _, ie = LS.brazos(pe, ve, inner, publicar, LP)
        chk("borde: a 0,0045 km fuera también es de borde (umbral 0,005)", len(LS.borde(pe, ie, inner)) == 1)
        chk("borde mixto (VS168-09): la alerta en summit entra, la lejana en summit no",
            LS.borde_mixto(pb, ib, inner, [idb, idf], LP) == frozenset([idb]))
        chk("borde mixto (VS168-09): una lejana de borde en far entra",
            LS.borde_mixto(pd_ + [], {**idd}, inner, LS.borde(pd_, idd, inner), LP) == frozenset()
            and LS.borde_mixto([dict(o, clase="far_tabla") for o in pd_], idd, inner, LS.borde(pd_, idd, inner), LP)
            == frozenset(LS.borde(pd_, idd, inner)))
        af, _ = LS.brazos(pb, vb, inner, publicar, LP, flip=frozenset([idb]))
        chk("borde: dar vuelta la clase cambia la publicación de cercano",
            ab[idb][LS.DECIDE][0] and not af[idb][LS.DECIDE][0], (ab[idb], af[idb]))
        with parada_de_prueba(LS, 6, 10):
            rb, fb = LS.analizar(pb, vb, kb, inner, publicar, deps, "2026-11-03", "2026-11-20",
                                 ultima_tabla="2026-12-30 00:00:00", commit=COMMIT, diff_fn=sin_cambio)
            rb = seguro(rb)
        chk("borde: analizar lista las dos pasadas y calcula la vuelta conjunta y la mixta",
            fb == [] and rb["borde"] == [("Lascar", "2026-11-06 08:00"), ("Lascar", "2026-11-07 08:00")]
            and set(rb["estado_vueltas"]) == {"conjunta", "mixta"}, (fb, rb.get("borde"), rb.get("estado_vueltas")))
        base = {LS.DECIDE: {"criterios": {"estado": LS.CUMPLE}}}
        otro_e = {LS.DECIDE: {"criterios": {"estado": LS.NO_CUMPLE}}}
        chk("estado_final: la vuelta conjunta que cambia el estado da DECIDE NICOLAS",
            LS.estado_final(base, [("conjunta", otro_e)])[0] == LS.NICOLAS)
        chk("estado_final (VS168-09): la vuelta mixta que cambia el estado da DECIDE NICOLAS aunque la conjunta no",
            LS.estado_final(base, [("conjunta", base), ("mixta", otro_e)]) ==
            (LS.NICOLAS, "la vuelta mixta del borde cambia el estado (§11.5)"))
        chk("estado_final: las vueltas que no lo cambian dejan el estado",
            LS.estado_final(base, [("conjunta", base), ("mixta", base)])[0] == LS.CUMPLE)
        chk("estado_final: sin borde, el estado base", LS.estado_final(otro_e, [])[0] == LS.NO_CUMPLE)

    # ---- criterios con valores fabricados (§11.7)
    with seccion("criterios con valores fabricados (§11.7)"):
        cs = LS.criterios_sombra
        ok = dict(veta=[], p2k="GANA", silencio="SILENCIO ACOTADO BAJO K", p2l="EMPATE", est_c=LS.CUMPLE, cae_curva=False,
                  est_d=LS.CUMPLE)
        chk("criterios: todo favorable cumple", cs(**ok)["estado"] == LS.CUMPLE)
        for k, v, esp in (("veta", [("x", "y")], LS.NO_CUMPLE), ("p2k", "PIERDE", LS.NO_CUMPLE),
                          ("p2k", "BLOQUEA", LS.NO_CUMPLE), ("p2k", "EMPATE", LS.CUMPLE),
                          ("p2k", "SIN SUSTRATO", LS.CUMPLE), ("silencio", "ENCIENDE DE MAS", LS.NO_CUMPLE),
                          ("silencio", "NO RESUELTO", LS.CUMPLE), ("p2l", "PIERDE", LS.NO_CUMPLE),
                          ("p2l", "BLOQUEA", LS.NO_CUMPLE), ("p2l", "GANA", LS.CUMPLE),
                          ("est_c", LS.NO_CUMPLE, LS.NO_CUMPLE), ("est_c", LS.NICOLAS, LS.NICOLAS),
                          ("est_d", LS.NICOLAS, LS.NICOLAS),
                          ("est_d", LS.NO_CUMPLE, LS.NO_CUMPLE), ("cae_curva", True, LS.NICOLAS)):
            chk(f"criterios: {k} = {v} da {esp}", cs(**dict(ok, **{k: v}))["estado"] == esp)
        chk("criterios: NO CUMPLE manda sobre DECIDE NICOLAS",
            cs(**dict(ok, veta=[1], est_d=LS.NICOLAS))["estado"] == LS.NO_CUMPLE)
        chk("criterios: la curva caída deja (d) en DECIDE NICOLAS aunque est_d cumpla",
            cs(**dict(ok, cae_curva=True))["d"] == LS.NICOLAS)
        cr = cs(**dict(ok, regimen_ok=False))
        chk("criterios (S8): con la marca de régimen (b), (c) y (d) CUMPLE pasan a DECIDE NICOLAS y (a) queda",
            cr == {"a": LS.CUMPLE, "b": LS.NICOLAS, "c": LS.NICOLAS, "d": LS.NICOLAS, "estado": LS.NICOLAS}, cr)
        cr2 = cs(**dict(ok, p2k="PIERDE", regimen_ok=False))
        chk("criterios (S8): con la marca de régimen un NO CUMPLE se queda NO CUMPLE",
            cr2["b"] == LS.NO_CUMPLE and cr2["estado"] == LS.NO_CUMPLE, cr2)
        chk("(c) (VS168-06): estado_c_sombra da DECIDE NICOLAS sólo con SIN SUSTRATO",
            [LS.estado_c_sombra(v, LP) for v in ("SIN SUSTRATO", "INDECIDIBLE", "EMPEORA", "MEJORA", "NEUTRO")]
            == [LS.NICOLAS, LS.NO_CUMPLE, LS.NO_CUMPLE, LS.CUMPLE, LS.CUMPLE])

    # ---- controles de la curva (VA168-02)
    with seccion("controles de la curva (VA168-02)"):
        def filas_curva(sesgo=1.0, n=10):
            fl = []
            for k in range(n):
                for h, z, mir, v, plat in (("05:00", 10.0, 2.0, 2.0, "VIIRS_NOAA20"),
                                          ("07:00", 50.0, 1.0, 0.9 * sesgo, "VIIRS_NOAA21")):
                    fl.append({"vol": "Lascar", "hora": f"{dia(k)} {h}", "z": z, "mir": mir, "c": "pos_prot",
                               "sensor": plat, "X": {LS.DECIDE: True}, "V": {LS.DECIDE: v}, "K": True, "VK": v})
            return fl
        cae, det = LS.controles_curva(filas_curva(), LS.DECIDE, E, CC)
        chk("curva: sin sesgo, la ganancia pareja no mueve D y la del cenit lo sube",
            not cae and det["ganancia_pareja"]["ok"] and det["ganancia_cenit"]["ok"] and det["n"] == 10, det)
        cae_s, det_s = LS.controles_curva(filas_curva(sesgo=0.3), LS.DECIDE, E, CC)
        chk("curva: un sesgo de plataforma x0,3 cae", cae_s and det_s["sesgo_plataforma"], det_s["sesgo_plataforma"])
        cc_roto = Proxy(CC, pares_por_noche=lambda pp, a_, b_, condicionar=True: [p for p in pp if p["pub"]],
                        resumen=lambda P, nulo=None: {"todas": {"d": [sum(p["vrp"] or 0 for p in P) / max(len(P), 1),
                                                                      [0, 0]], "n_noches": len(P)}},
                        sesgo_plataforma=lambda pp, a_, b_: {"sesgado": False, "por_plataforma": {}})
        cae_r, det_r = LS.controles_curva(filas_curva(), LS.DECIDE, E, cc_roto)
        chk("curva: un instrumento que no es invariante a la escala hace caer la ganancia pareja",
            cae_r and not det_r["ganancia_pareja"]["ok"] and det_r["ganancia_cenit"]["ok"], det_r)
        cae_ks, _ = LS.controles_curva(filas_curva(sesgo=0.3), "K", E, CC)
        chk("curva (VS168-07): los controles corren también para K y ven su sesgo", cae_ks)
        cae_v, det_v = LS.controles_curva([], LS.DECIDE, E, CC)
        chk("curva: sin pares los controles dan SIN SUSTRATO y no caen",
            not cae_v and det_v["ganancia_pareja"] == "SIN SUSTRATO", det_v)
        fl_mal = filas_curva()
        for x in fl_mal:
            x["z"] = 10.0
        cae_z, det_z = LS.controles_curva(fl_mal, LS.DECIDE, E, CC)
        chk("curva: sin diferencia de cenit no hay pares y no cae", not cae_z and det_z["n"] == 0, det_z)

    # ---- parada (§11.8) con los umbrales de verdad
    with seccion("parada (§11.8) con los umbrales de verdad"):
        def fp2(nn, na, dato=True):
            fl = [{"id": k, "noche": f"N{k:03d}", "clase": "neg_resto"} for k in range(nn)]
            fl += [{"id": 1000 + j, "noche": "N000", "clase": "pos_prot" if j % 2 else "pos_bajo"} for j in range(na)]
            return fl, ({o["id"] for o in fl} if dato else set())
        chk("parada: los umbrales son 30 noches y 40 alertas", (LS.PARADA_NOCHES, LS.PARADA_ALERTAS) == (30, 40))
        chk("parada: 30 noches y 40 alertas, alcanzada en la noche 30", LS.noche_parada(*fp2(30, 40))[0] == "N029")
        chk("parada: 29 noches no alcanza", LS.noche_parada(*fp2(29, 40))[0] is None)
        chk("parada: 39 alertas no alcanza", LS.noche_parada(*fp2(30, 39))[0] is None)
        chk("parada: far y negativos no cuentan como alertas",
            LS.noche_parada(*fp2(30, 0))[1]["alertas"] == 0)
        chk("parada: sin dato no cuenta", LS.noche_parada(*fp2(30, 40, dato=False))[1] == {
            "noches": 0, "alertas": 0, "alcanzada": False, "noche": None})
        fl_t, cd_t = fp2(35, 0)
        fl_t += [{"id": 2000 + j, "noche": f"N{20 + j // 2:03d}", "clase": "pos_bajo"} for j in range(30)]
        fl_t += [{"id": 3000 + j, "noche": "N033", "clase": "pos_prot"} for j in range(10)]
        cd_t |= {o["id"] for o in fl_t}
        chk("parada (VS168-01): la noche N es la PRIMERA con 30 noches y 40 alertas («lo que llegue último»)",
            LS.noche_parada(fl_t, cd_t) == ("N034", {"noches": 35, "alertas": 40, "alcanzada": True, "noche": "N034"}),
            LS.noche_parada(fl_t, cd_t))

    # ---- main() de punta a punta sobre carpetas y CSV sintéticos
    with seccion("main() de punta a punta sobre carpetas y CSV sintéticos"):
        pm, vm, km = escena(LS, publicar, inner, neg_aparte=12)
        id_sd = next(o for o in pm if o["clase"] == "pos_prot" and o["hora_utc"].startswith("2026-11-10"))
        with tempfile.TemporaryDirectory(dir=str(AQUI)) as t:
            t = Path(t)
            for sub in ("k", "s"):
                (t / sub).mkdir()
            for vol in B.VOLS:
                ks, ss = [], []
                if vol == "Lascar":
                    ks = [km[k] for k in sorted(km)]
                    ss = [vm[k] for k in sorted(vm) if k[2] != id_sd["hora_utc"]]   # una protegida SIN DATO (VS168-03)
                    ss.append(dict(rec_via("2026-11-04 05:00", [0.5], 0.5, 0.5, 0.5), sensor="VIIRS_NOAA20_750"))
                    # una alerta mínima (0,04 MW): con la regla D-9 en modo SN cuenta como «MIROVA no vio nada»
                    ks.append(rec_k("2026-11-29 05:00", False, 0.1))
                    ss.append(rec_via("2026-11-29 05:00", [], 0, 0, 0.0))
                (t / "k" / f"{vol}.json").write_text(json.dumps({"records": ks}), encoding="utf-8")
                (t / "s" / f"{vol}.json").write_text(json.dumps({"records": ss}), encoding="utf-8")
            cab = ["timestamp", "Fecha_Satelite_UTC", "Fecha_Captura_Chile", "Volcan", "Sensor", "VRP_MW", "Distancia_km",
                   "Tipo_Registro", "Clasificacion Mirova", "Ruta Foto", "Fecha_Proceso_GitHub", "Ultima_Actualizacion",
                   "Editado"]
            with open(t / "cons.csv", "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(cab)
                for o in pm:
                    tipo = {"pos_prot": "ALERTA_TERMICA", "pos_bajo": "ALERTA_TERMICA", "far_tabla": "FALSO_POSITIVO"}.get(
                        o["clase"], "RUTINA")
                    vrp = o["mirova_vrp"] if o["clase"].startswith("pos") else (0.4 if o["clase"] == "far_tabla" else 0.0)
                    dist = 1.0 if o["clase"].startswith("pos") else (15.0 if o["clase"] == "far_tabla" else 0.0)
                    w.writerow([0, o["hora_utc"] + ":10", "", "Lascar", "VIIRS375", vrp, dist, tipo, "Bajo", "", "", "", "NO"])
                w.writerow([0, "2026-11-29 05:00:10", "", "Lascar", "VIIRS375", 0.04, 1.0, "ALERTA_TERMICA", "Bajo", "", "",
                            "", "NO"])
                # una alerta de MIROVA sin record de K (VS168-12) y una fila RUTINA posterior para el rezago (S9)
                w.writerow([0, "2026-11-12 09:00:10", "", "Lascar", "VIIRS375", 0.7, 1.0, "ALERTA_TERMICA", "Bajo", "", "",
                            "", "NO"])
                w.writerow([0, "2026-12-08 05:00:10", "", "Lascar", "VIIRS375", 0.0, 0.0, "RUTINA", "Bajo", "", "", "", "NO"])
            with open(t / "ocr.csv", "w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerow(cab + ["Nota_Validacion"])

            def correr(dsal, *extra, hasta="2026-11-30"):
                args = ["--data-k", str(t / "k"), "--data-sombra", str(t / "s"), "--cons", str(t / "cons.csv"),
                        "--ocr", str(t / "ocr.csv"), "--hasta", hasta, "--commit", COMMIT, "--dir-salida", str(dsal)]
                cod = LS.main(args + list(extra))
                txts = sorted(Path(dsal).glob("*.txt")) if Path(dsal).exists() else []
                jss = sorted(Path(dsal).glob("*.json")) if Path(dsal).exists() else []
                return cod, txts, jss

            # provisional, con los umbrales de verdad (24 noches): sólo controles y contadores
            cod_p, tx_p, js_p = correr(t / "o_prov")
            txt_p = tx_p[0].read_text(encoding="utf-8") if tx_p else ""
            out_p = json.loads(js_p[0].read_text(encoding="utf-8"), object_hook=Seguro) if js_p else Seguro()
            chk("main (VS168-01): antes de la parada sale 5 y escribe controles_sombra_<hasta>_<hora>",
                cod_p == 5 and len(tx_p) == 1 and tx_p[0].name.startswith("controles_sombra_2026-11-30_"), (cod_p, tx_p))
            chk("main (VS168-01): antes de la parada no hay población, criterios, estado ni lecturas",
                "== población" not in txt_p and "== cercano" not in txt_p and "PAQUETE" not in txt_p
                and "criterios" not in txt_p and "NO ALCANZADA" in txt_p and set(out_p) == {"procedencia", "corte",
                                                                                             "controles", "parada"},
                (txt_p[-1200:], list(out_p)))
            chk("main (VS168-02): antes de la parada los controles salen sin detalle (ni conteos ni nombres)",
                "'n':" not in txt_p and "sin_dato" not in txt_p and "pos_prot" not in txt_p
                and "2026-11-" not in txt_p.split("== controles")[1]
                and out_p["controles"] and all(set(v) == {"ok", "motivo"} for v in out_p["controles"].values()), txt_p[-1500:])
            chk("main: los contadores de la parada sí salen", "noches 25 de 30" in txt_p and out_p["parada"]["noches"] == 25,
                (txt_p[-400:], out_p.get("parada")))

            # la lectura que decide, con la parada de prueba (25 noches y 20 alertas): N es la última noche
            with parada_de_prueba(LS, 25, 20):
                cod, tx, jsl = correr(t / "o_dec")
            txt = tx[0].read_text(encoding="utf-8") if tx else ""
            out = json.loads(jsl[0].read_text(encoding="utf-8"), object_hook=Seguro) if jsl else Seguro()
            chk("main: la lectura que decide sale 0 y se llama lectura_sombra_corte_<N>",
                cod == 0 and [x.name for x in tx] == ["lectura_sombra_corte_2026-11-29.txt"], (cod, tx, txt[-1500:]))
            chk("main: los controles S1 a S10 en verde", all(v["ok"] for v in out["controles"].values())
                and set(out["controles"]) == {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S9", "S10"}, out.get("controles"))
            chk("main: la población sale de banco_paridad con las clases de la escena",
                "'pos_prot': 13" in txt and "'far_tabla': 12" in txt and "'neg_pub': 12" in txt and "'pos_bajo': 12" in txt,
                txt[:3000])
            chk("main: radiante rotulado posterior a la lectura", "radiante (informa, posterior a la lectura)" in txt)
            chk("main: referencia y records con sha256 en la salida", "referencia congelada" in txt
                and out["procedencia"]["referencia"]["cons"] and out["procedencia"]["records_k"]["Lascar"])
            chk("main (VS168-04): el lector imprime su propio sha256 y el commit de los records",
                out["procedencia"]["lector"] == LS.sha256_lf(Path(a.dir) / "leer_sombra_v375e.py")
                and out["procedencia"]["commit"] == COMMIT and "lector sha256 LF" in txt)
            chk("main: el record de VIIRS 750 de la sombra no entra", "VIIRS_NOAA20_750" not in json.dumps(out))
            chk("main (VS168-03): la protegida SIN DATO que K publica veta a cercano y el paquete no cumple",
                out["estado"] == LS.NO_CUMPLE and ["Lascar", id_sd["hora_utc"]] in out["brazos"]["VIA|cercano"]["P1_veta"]
                and out["brazos"]["VIA|cercano"]["criterios"]["a"] == LS.NO_CUMPLE, out.get("brazos", {}).get("VIA|cercano",
                                                                                                             {}).get("P1_veta"))
            chk("main: con la regla SN la alerta de 0,04 MW cuenta como negativo limpio (13 neg_resto, no pos_bajo)",
                "'neg_resto': 13" in txt and "'pos_bajo': 12" in txt, txt[:2500])
            chk("main (VS168-12): las alertas de MIROVA sin record de K se informan", out["alertas_sin_record_K"] == {
                "Lascar": 1} and "sin record de K (informa): 1" in txt, out.get("alertas_sin_record_K"))
            chk("main (VS168-13): radiante y P-sinfiltro sin criterios ni estado, en pantalla y en el JSON",
                txt.count("criterios:") == 1 and "criterios" not in out["brazos"]["VIA|radiante"]
                and "criterios" not in out["brazos"]["VIA|sinfiltro"], txt.count("criterios:"))
            chk("main (VS168-02): en la lectura que decide los controles salen con detalle",
                "S7 OK: {" in txt and "detalle" in out["controles"]["S7"])
            chk("main: el estado del paquete está en la salida", "PAQUETE en la sombra" in txt and out.get("estado"))

            # la lectura que decide no se vuelve a escribir (VS168-01 y 05)
            with parada_de_prueba(LS, 25, 20):
                cod_r, tx_r, _ = correr(t / "o_dec")
            chk("main (VS168-01): leer otra vez el mismo corte sale 2 y no toca la lectura",
                cod_r == 2 and [x.name for x in tx_r] == ["lectura_sombra_corte_2026-11-29.txt"]
                and tx_r[0].read_text(encoding="utf-8") == txt, cod_r)

            # el recorte: con la parada de prueba en 12 noches, N = 2026-11-15 aunque --hasta sea el 30
            with parada_de_prueba(LS, 12, 20):
                cod_c, tx_c, js_c = correr(t / "o_rec")
            txt_c = tx_c[0].read_text(encoding="utf-8") if tx_c else ""
            out_c = json.loads(js_c[0].read_text(encoding="utf-8"), object_hook=Seguro) if js_c else Seguro()
            chk("main (VS168-01): con --hasta posterior lee sólo hasta la noche de la parada y lo dice",
                cod_c == 0 and [x.name for x in tx_c] == ["lectura_sombra_corte_2026-11-15.txt"]
                and out_c.get("corte") == "2026-11-15" and "recortado: --hasta 2026-11-30" in txt_c
                and "neg_resto" not in txt_c.split("por clase:")[1].split("\n")[0], (cod_c, tx_c, txt_c[:1500]))
            chk("main (VS168-01): después del corte nada entra (la protegida SIN DATO del 11-10 sí, la alerta del 11-29 no)",
                out_c["brazos"]["VIA|cercano"]["criterios"]["a"] == LS.NO_CUMPLE
                and "2026-11-29" not in json.dumps(out_c["brazos"]["VIA|cercano"]["P1_veta"]), out_c.get("corte"))

            # S9: la referencia fresca hace caer la lectura que decide
            with open(t / "cons.csv", encoding="utf-8") as fh:
                filas_cons = fh.read()
            (t / "cons_fresca.csv").write_text(filas_cons.replace("2026-12-08 05:00:10", "2026-11-28 05:00:10"),
                                               encoding="utf-8")
            args9 = ["--data-k", str(t / "k"), "--data-sombra", str(t / "s"), "--cons", str(t / "cons_fresca.csv"),
                     "--ocr", str(t / "ocr.csv"), "--hasta", "2026-11-30", "--commit", COMMIT, "--dir-salida",
                     str(t / "o_s9b")]
            with parada_de_prueba(LS, 25, 20):
                cod_9b = LS.main(args9)
            tx_9b = sorted((t / "o_s9b").glob("*.txt"))
            txt_9b = tx_9b[0].read_text(encoding="utf-8") if tx_9b else ""
            chk("main (VS168-05): con la tabla a 1 día del corte S9 cae, sale 3 y no escribe la lectura del corte",
                cod_9b == 3 and "S9 CAE" in txt_9b and tx_9b and tx_9b[0].name.startswith("controles_sombra_2026-11-29_")
                and "== población" not in txt_9b, (cod_9b, tx_9b, txt_9b[-800:]))
            chk("main (VS168-05): con la tabla a 9 días del corte la lectura sí se escribe", cod == 0, cod)

            # controles caídos: nada de la población, sólo nombre, CAE y motivo (VS168-02)
            ide = LS.IDENTIDAD_ESPERADA
            LS.IDENTIDAD_ESPERADA = ([1, 1, 1, 1, 1], [1, 1])
            cod4, tx4, _ = correr(t / "o_ide")
            LS.IDENTIDAD_ESPERADA = ide
            chk("main: la identidad del predicado distinta de la esperada hace caer S2 y sale 3",
                cod4 == 3 and "S2 CAE" in tx4[0].read_text(encoding="utf-8"))
            for desde in ("2026-11-02", "2026-11-10"):
                cod2, tx2, js2 = correr(t / f"o_d{desde}", "--desde", desde)
                txt2 = tx2[0].read_text(encoding="utf-8") if tx2 else ""
                out2 = json.loads(js2[0].read_text(encoding="utf-8"), object_hook=Seguro) if js2 else Seguro()
                chk(f"main VA168-01: desde {desde} sale 3 sin nada de la población",
                    cod2 == 3 and "== población" not in txt2 and "== cercano" not in txt2 and "PAQUETE" not in txt2
                    and set(out2) == {"procedencia", "corte", "controles"}, (cod2, txt2[-800:]))
                chk(f"main VS168-02: con S1 caído ({desde}) no salen conteos ni nombres de pasadas",
                    "S1 CAE: " + LS.MOTIVO["S1"] in txt2 and "'n':" not in txt2 and "sin_dato" not in txt2
                    and "pos_prot" not in txt2 and "noches" not in txt2 and "2026-11-" not in txt2.split("== controles")[1]
                    and out2["controles"] and all(set(v) == {"ok", "motivo"} for v in out2["controles"].values()), txt2[-1500:])
            # con S7 caído (más del 10 % de protegidas sin dato): no salen conteos (VS168-02)
            ss7 = [vm[k] for k in sorted(vm) if not (k[2].endswith("05:00") and k[2][:10] <= "2026-11-08")]
            (t / "s7").mkdir()
            for vol in B.VOLS:
                (t / "s7" / f"{vol}.json").write_text(json.dumps({"records": ss7 if vol == "Lascar" else []}),
                                                      encoding="utf-8")
            args7 = ["--data-k", str(t / "k"), "--data-sombra", str(t / "s7"), "--cons", str(t / "cons.csv"),
                     "--ocr", str(t / "ocr.csv"), "--hasta", "2026-11-30", "--commit", COMMIT, "--dir-salida",
                     str(t / "o_s7")]
            cod7 = LS.main(args7)
            tx7 = sorted((t / "o_s7").glob("*.txt"))
            txt7 = tx7[0].read_text(encoding="utf-8") if tx7 else ""
            chk("main VS168-02: con S7 caído sale 3, sólo el motivo, sin conteos por clase ni nombres de pasadas",
                cod7 == 3 and "S7 CAE: " + LS.MOTIVO["S7"] in txt7 and "pos_prot" not in txt7 and "'n':" not in txt7
                and "2026-11-0" not in txt7.split("== controles")[1], txt7[-1500:])
            viejo = LS.SHA_DEPS[clave0]
            LS.SHA_DEPS[clave0] = "0" * 64
            cod3, tx3, _ = correr(t / "o_s0")
            LS.SHA_DEPS[clave0] = viejo
            txt3 = tx3[0].read_text(encoding="utf-8") if tx3 else ""
            chk("main: S0 caído sale 3 sin leer nada", cod3 == 3 and "== población" not in txt3
                and "LECTURA NO LEGIBLE" in txt3 and "referencia congelada" not in txt3, txt3[-500:])
            try:
                LS.main(["--data-k", str(t / "k"), "--data-sombra", str(t / "s"), "--cons", str(t / "cons.csv"),
                         "--ocr", str(t / "ocr.csv"), "--hasta", "2026-11-30", "--dir-salida", str(t / "o_x")])
                sin_commit = False
            except SystemExit:
                sin_commit = True
            chk("main (VS168-14): sin --commit no corre", sin_commit)

            # cargar_records: sólo la vía, sólo VIIRS 375, sólo la ventana
            (t / "c").mkdir()
            rs = [rec_via("2026-11-04 05:00", [0.5], 0.5, 0.5, 0.5),
                  dict(rec_via("2026-11-04 06:00", [0.5], 0.5, 0.5, 0.5), via_codigo_mirova="sin_grilla"),
                  dict(rec_via("2026-11-04 07:00", [0.5], 0.5, 0.5, 0.5), sensor="VIIRS_NOAA21_750"),
                  rec_via("2026-11-01 05:00", [0.5], 0.5, 0.5, 0.5), rec_via("2026-12-01 05:00", [0.5], 0.5, 0.5, 0.5),
                  dict(rec_via("2026-11-04 08:00", [0.5], 0.5, 0.5, 0.5), sensor="MODIS_AQUA")]
            (t / "c" / "Lascar.json").write_text(json.dumps({"records": rs}), encoding="utf-8")
            cv, sh = LS.cargar_records(t / "c", ["Lascar", "Isluga"], "2026-11-03", "2026-11-30", solo_via=True)
            chk("cargar_records: sólo la vía VIIRS 375 dentro de la ventana",
                list(cv) == [("Lascar", "VIIRS_NOAA20", "2026-11-04 05:00")], list(cv))
            ck, _ = LS.cargar_records(t / "c", ["Lascar"], "2026-11-03", "2026-11-30")
            chk("cargar_records: sin solo_via entra también la sin_grilla", len(ck) == 2, list(ck))
            chk("cargar_records: sha256 del archivo y None si falta", sh["Lascar"] and sh["Isluga"] is None, sh)

    n = len(RES)
    print(f"\nRESULTADO: {sum(RES)} de {n}")
    return 0 if all(RES) else 1


if __name__ == "__main__":
    sys.exit(main())
