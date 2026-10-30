# -*- coding: utf-8 -*-
"""S168 V375-E: batería del lector de la sombra (PREREGISTRO_E.md §11).

Escenas SINTÉTICAS (ningún dato de la ventana P), con el predicado del tablero ejecutado con node, banco_paridad real y
las dependencias del tag sellado (lector de la retrospectiva, evaluar.py, curva_cenit.py, evaluador_comun.py). Cubre cada
función del §11 en verde y en rojo: población y clases, los brazos (escena LEJANA: cercano publica y radiante calla), el
borde (VA168-08), los controles S0 a S7, que con un control caído no salga nada de la población (VA168-01), la regla de
criterios con valores fabricados, los controles de la curva (VA168-02), las mitades, la parada, y main() de punta a punta
sobre carpetas y CSV sintéticos.
Uso: python -I probar_sombra.py [--dir <carpeta con leer_sombra_v375e.py a probar>]  (exit 0 si todo pasa)
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

RES = []


def chk(nombre, cond, detalle=""):
    RES.append(bool(cond))
    print(f"{'PASA ' if cond else 'FALLA'}  {nombre} {'' if cond else detalle}", flush=True)


def cargar(d):
    spec = importlib.util.spec_from_file_location("leer_sombra_v375e", Path(d) / "leer_sombra_v375e.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- escenas
def rec_via(hora, px, cen, pico, vrp=1.5, inner=5.0, sensor="VIIRS_NOAA20", dc=None):
    pix = [{"lat": -23.37, "lon": -67.73, "dist_km": d, "bt_k": 300.0, "fila": 60 + i, "col": 60 + i}
           for i, d in enumerate(px)]
    r = {"sensor": sensor, "datetime_utc": hora, "via_codigo_mirova": True, "triggered_test1": False,
         "vrp_vent_mw": 0.0, "n_anomalous_pixels": len(pix), "anomaly_pixels": pix, "t_max_k": 300.0,
         "vrp_mw": vrp if pix else 0.0, "sensor_zenith_deg": 20.0}
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
            "sensor_zenith_deg": z, "n_anomalous_pixels": 2, "anomaly_pixels": [],
            "primary_cluster": {"vrp_mw": vrp, "n_pixels": 2, "centroid_dist_km": cen, "centroid_lat": -23.37,
                                "centroid_lon": -67.73, "single_pixel_mode": False}}


def entrada(i, hora, clase, sensor="VIIRS_NOAA20", mir=0.0, z=20.0, pub=False, disp=None, vol="Lascar", tabla=True):
    return {"id": i, "volcan": vol, "hora_utc": hora, "noche": hora[:10], "sensor": sensor, "clase": clase,
            "protegida": clase == "pos_prot", "alerta_tabla": tabla, "mirova_vrp": mir, "z": z,
            "estrato": f"{vol}|{'z<=40' if z <= 40 else 'z>40'}", "pub_prod": pub, "disp_k": disp, "dist_ref": None,
            "lote": "P", "partida": False}


def escena(LS, publicar, inner, n_noches=12, lejana_prot=True, borde_km=None, neg_aparte=0):
    """12 noches en Láscar: protegida y alerta bajo 1 MW publicadas por todos, un negativo limpio callado, un negativo
    que K publica, una lejana de la tabla (cercano publica, radiante no) y, si se pide, una protegida LEJANA que K
    publica (radiante la calla: veta a radiante, no a cercano). `neg_aparte`: corre los negativos esa cantidad de
    noches (para main(), donde banco_paridad sólo llama limpio a un negativo de una noche sin alerta)."""
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
            dia = f"2026-11-{4 + n + (neg_aparte if cl.startswith('neg') else 0):02d}"
            hora = f"{dia} {h}"
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
    for hora, cl, mir, rv in extra:
        rv["datetime_utc"] = hora
        via[("Lascar", "VIIRS_NOAA20", hora)] = rv
        kfull[("Lascar", "VIIRS_NOAA20", hora)] = rec_k(hora, True, 1.0)
        pob.append(entrada(i, hora, cl, mir=mir, pub=True))
        i += 1
    # disp de K: lo que muestra el tablero
    keys = [(o["volcan"], o["sensor"], o["hora_utc"]) for o in pob]
    res = publicar([(kfull[k], inn) for k in keys])
    for o, (disp, pub) in zip(pob, res):
        o["disp_k"], o["pub_prod"] = disp, bool(pub)
    return pob, via, kfull


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(AQUI))
    a = ap.parse_args(argv)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    LS = cargar(a.dir)
    import banco_paridad as B
    from clase_mirova import alerta_protegida

    # ---- S0 dependencias
    deps, malos = LS.cargar_deps()
    chk("S0: las cuatro dependencias son las del tag", deps is not None and not malos, malos)
    clave0 = next(iter(LS.SHA_DEPS))
    viejo = LS.SHA_DEPS[clave0]
    LS.SHA_DEPS[clave0] = "0" * 64
    d2, m2 = LS.cargar_deps()
    LS.SHA_DEPS[clave0] = viejo
    chk("S0: con un sha distinto no carga ninguna", d2 is None and len(m2) == 1, m2)
    LP, E = deps["LP"], deps["E"]
    inner = B.inner_desde_html()

    def publicar(casos):
        return [(x[3], x[4]) for x in B.correr_node([[E.slim(r), inn] for r, inn in casos])]

    # ---- clases (§11.2)
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
    chk("S1: ventana desde 2026-11-03 OK", LS.control_s1("2026-11-03", "2026-11-20", pob)[0])
    chk("S1: desde antes del 2026-11-03 cae", not LS.control_s1("2026-11-02", "2026-11-20", pob)[0])
    chk("S1: pasada fuera de la ventana cae", not LS.control_s1("2026-11-05", "2026-11-20", pob)[0])
    chk("S1: clave repetida cae", not LS.control_s1("2026-11-03", "2026-11-20", pob + [dict(pob[0], id=500)])[0])
    chk("S1: hasta antes de desde cae", not LS.control_s1("2026-11-03", "2026-11-02", [])[0])
    ok2, r2 = LS.control_s2(pob, via, inner, publicar, LP)
    chk("S2: summit, far, summit da [True, False, True]", ok2 and r2 == [True, False, True], r2)
    vacios = {k: rec_via(k[2], [], 0, 0, 0.0) for k in via}
    chk("S2: sin pasada de la vía con VRP cae", not LS.control_s2(pob, vacios, inner, publicar, LP)[0])
    chk("S2: un predicado que no responde a la clase cae",
        not LS.control_s2(pob, via, inner, lambda c: [(1.0, True)] * len(c), LP)[0])
    ok3, d3 = LS.control_s3(info)
    chk("S3: pasadas de un alertado, radiante y cercano a 0,0051 km o menos", ok3 and d3["n"] > 0, d3)
    info_m = {k: dict(v) for k, v in info.items()}
    k1 = next(k for k, v in info_m.items() if v["npix"] == 1)
    info_m[k1] = dict(info_m[k1], dist={"radiante": 0.52, "cercano": 0.5, "pico": 0.5})
    chk("S3: una diferencia de 0,02 km cae", not LS.control_s3(info_m)[0])
    chk("S3: sin pasadas de un alertado cae", not LS.control_s3({k: v for k, v in info.items() if v["npix"] != 1})[0])
    chk("S4: radiante tiene la clase del record", LS.control_s4(pob, info, inner, LP)[0])
    info_c = {k: dict(v) for k, v in info.items()}
    info_c[lej["id"]] = dict(info_c[lej["id"]], dc="summit")
    chk("S4: una clase distinta cae", not LS.control_s4(pob, info_c, inner, LP)[0])
    chk("S4: sin pasadas con alertados cae", not LS.control_s4(pob, {}, inner, LP)[0])
    ok5, d5 = LS.control_s5(pob, kfull, inner, publicar, LP)
    chk("S5: PLACEBO K x 1,2 publica igual que K", ok5 and d5["n"] == len(pob), d5)
    chk("S5: sin records de K cae (0 de 0 no prueba nada)", not LS.control_s5(pob, {}, inner, publicar, LP)[0])
    chk("S5: si K x 1,2 publica distinto cae",
        not LS.control_s5(pob, kfull, inner, lambda c: [(1.0, True)] * len(c), LP)[0])
    ok7, d7 = LS.control_s7(pob, arms)
    chk("S7: cobertura completa OK", ok7 and all(v["sin_dato"] == 0 for v in d7.values()), d7)
    falta = {k: v for k, v in arms.items() if k != next(o["id"] for o in pob if o["clase"] == "pos_prot")}
    chk("S7: una protegida sin dato en 13 (7,7 %) no cae", LS.control_s7(pob, falta)[0])
    sin2 = [o["id"] for o in pob if o["clase"] == "pos_prot"][:2]
    chk("S7: dos protegidas sin dato en 13 (más del 10 %) cae",
        not LS.control_s7(pob, {k: v for k, v in arms.items() if k not in sin2})[0])
    chk("S7: población vacía cae", not LS.control_s7([], {})[0])
    sin_o = [o["id"] for o in pob if o["clase"] == "far_tabla"][:2]
    chk("S7: far_tabla también decide la cobertura",
        not LS.control_s7(pob, {k: v for k, v in arms.items() if k not in sin_o})[0])

    # ---- analizar: VA168-01, con un control caído no sale nada de la población
    res_f, fal_f = LS.analizar(pob, via, kfull, inner, publicar, deps, "2026-11-02", "2026-11-20")
    chk("VA168-01: S1 caído, analizar devuelve sólo controles",
        fal_f == ["S1"] and set(res_f) == {"controles"}, (fal_f, list(res_f)))
    res_i, fal_i = LS.analizar(pob, via, kfull, inner, publicar, deps, "2026-11-03", "2026-11-20", identidad_ok=False)
    chk("S2: la identidad del predicado caída hace caer S2", fal_i == ["S2"] and set(res_i) == {"controles"}, fal_i)

    res, fal = LS.analizar(pob, via, kfull, inner, publicar, deps, "2026-11-03", "2026-11-20")
    chk("analizar: escena principal sin controles caídos", fal == [], fal)
    br = res["brazos"]
    chk("(a): radiante calla la protegida LEJANA que K publica y no cumple",
        br[("VIA", "radiante")]["P1_veta"] == [("Lascar", "2026-11-05 08:00")]
        and br[("VIA", "radiante")]["criterios"]["a"] == LS.NO_CUMPLE, br[("VIA", "radiante")]["P1_veta"])
    chk("(a): cercano no calla ninguna y cumple", br[LS.DECIDE]["P1_veta"] == []
        and br[LS.DECIDE]["criterios"]["a"] == LS.CUMPLE)
    chk("lejanas: cercano publica las 12 far_tabla, radiante 0, K 12",
        br[LS.DECIDE]["lejanas"]["publica"] == 12 and br[("VIA", "radiante")]["lejanas"]["publica"] == 0
        and res["lejanas_K"]["publica"] == 12, (br[LS.DECIDE]["lejanas"]["publica"], res["lejanas_K"]["publica"]))
    chk("(b): P2-L de radiante contra K gana (calla donde K publica)",
        br[("VIA", "radiante")]["P2L_K"]["veredicto"] == "GANA", br[("VIA", "radiante")]["P2L_K"])
    chk("(b): P2-L de cercano contra K empata en bloques (publica igual que K)",
        br[LS.DECIDE]["P2L_K"]["B"] == 0, br[LS.DECIDE]["P2L_K"])
    chk("N-3: en la ventana P no toca ninguna fila", br[LS.DECIDE]["n3_filas"] == [])
    chk("parada: 12 noches y 25 alertas, no alcanzada",
        res["parada"] == {"noches": 12, "alertas": 25, "alcanzada": False}, res["parada"])
    chk("borde: sin pasadas de borde, estado sin motivo", res["borde"] == [] and res["motivo"] == "")
    chk("estado del paquete es el de cercano", res["estado"] == br[LS.DECIDE]["criterios"]["estado"])
    chk("mitades: corte en la noche de la mediana (6 de 12 en la primera)",
        br[LS.DECIDE]["mitades"]["corte_noche"] == "2026-11-09", br[LS.DECIDE]["mitades"]["corte_noche"])
    chk("(c): M lee los pares de cercano con el evaluador común", br[LS.DECIDE]["M"]["n"] > 0, br[LS.DECIDE]["M"]["n"])
    chk("(d): la curva de K y la de cercano se calculan", "condicionada" in br[LS.DECIDE]["curva"]
        and "condicionada" in br[LS.DECIDE]["curva_K"])

    # ---- borde (VA168-08)
    pb, vb, kb = escena(LS, publicar, inner, borde_km=-0.003)
    ab, ib = LS.brazos(pb, vb, inner, publicar, LP)
    idb = next(o["id"] for o in pb if o["hora_utc"] == "2026-11-06 08:00")
    chk("borde: cercano a 0,003 km dentro del radio es de borde", LS.borde(pb, ib, inner) == [idb])
    pc, vc, kc = escena(LS, publicar, inner, borde_km=-0.02)
    _, ic = LS.brazos(pc, vc, inner, publicar, LP)
    chk("borde: a 0,02 km dentro no es de borde", LS.borde(pc, ic, inner) == [])
    pd_, vd, kd = escena(LS, publicar, inner, borde_km=0.004)
    _, idd = LS.brazos(pd_, vd, inner, publicar, LP)
    chk("borde: a 0,004 km fuera también es de borde", len(LS.borde(pd_, idd, inner)) == 1)
    af, _ = LS.brazos(pb, vb, inner, publicar, LP, flip=frozenset([idb]))
    chk("borde: dar vuelta la clase cambia la publicación de cercano",
        ab[idb][LS.DECIDE][0] and not af[idb][LS.DECIDE][0], (ab[idb], af[idb]))
    rb, fb = LS.analizar(pb, vb, kb, inner, publicar, deps, "2026-11-03", "2026-11-20")
    chk("borde: analizar lista la pasada y calcula el estado dado vuelta",
        rb["borde"] == [("Lascar", "2026-11-06 08:00")] and rb["estado_borde_dado_vuelta"] is not None, rb.get("borde"))
    base = {LS.DECIDE: {"criterios": {"estado": LS.CUMPLE}}}
    otro = {LS.DECIDE: {"criterios": {"estado": LS.NO_CUMPLE}}}
    chk("estado_final: el borde que cambia el estado da DECIDE NICOLAS",
        LS.estado_final(base, otro, [1])[0] == LS.NICOLAS)
    chk("estado_final: el borde que no lo cambia deja el estado", LS.estado_final(base, base, [1])[0] == LS.CUMPLE)
    chk("estado_final: sin borde, el estado base", LS.estado_final(otro, None, [])[0] == LS.NO_CUMPLE)

    # ---- criterios con valores fabricados (§11.7)
    cs = LS.criterios_sombra
    ok = dict(veta=[], p2k="GANA", silencio="SILENCIO ACOTADO BAJO K", p2l="EMPATE", est_c=LS.CUMPLE, cae_curva=False,
              est_d=LS.CUMPLE)
    chk("criterios: todo favorable cumple", cs(**ok)["estado"] == LS.CUMPLE)
    for k, v, esp in (("veta", [("x", "y")], LS.NO_CUMPLE), ("p2k", "PIERDE", LS.NO_CUMPLE),
                      ("p2k", "BLOQUEA", LS.NO_CUMPLE), ("p2k", "EMPATE", LS.CUMPLE),
                      ("p2k", "SIN SUSTRATO", LS.CUMPLE), ("silencio", "ENCIENDE DE MAS", LS.NO_CUMPLE),
                      ("silencio", "NO RESUELTO", LS.CUMPLE), ("p2l", "PIERDE", LS.NO_CUMPLE),
                      ("p2l", "BLOQUEA", LS.NO_CUMPLE), ("p2l", "GANA", LS.CUMPLE),
                      ("est_c", LS.NO_CUMPLE, LS.NO_CUMPLE), ("est_d", LS.NICOLAS, LS.NICOLAS),
                      ("est_d", LS.NO_CUMPLE, LS.NO_CUMPLE), ("cae_curva", True, LS.NICOLAS)):
        chk(f"criterios: {k} = {v} da {esp}", cs(**dict(ok, **{k: v}))["estado"] == esp)
    chk("criterios: NO CUMPLE manda sobre DECIDE NICOLAS",
        cs(**dict(ok, veta=[1], est_d=LS.NICOLAS))["estado"] == LS.NO_CUMPLE)
    chk("criterios: la curva caída deja (d) en DECIDE NICOLAS aunque est_d cumpla",
        cs(**dict(ok, cae_curva=True))["d"] == LS.NICOLAS)

    # ---- controles de la curva (VA168-02)
    import curva_cenit as CC

    def filas_curva(sesgo=1.0, n=10):
        fl = []
        for k in range(n):
            for h, z, mir, v, plat in (("05:00", 10.0, 2.0, 2.0, "VIIRS_NOAA20"),
                                      ("07:00", 50.0, 1.0, 0.9 * sesgo, "VIIRS_NOAA21")):
                fl.append({"vol": "Lascar", "hora": f"2026-11-{4 + k:02d} {h}", "z": z, "mir": mir, "c": "pos_prot",
                           "sensor": plat, "X": {LS.DECIDE: True}, "V": {LS.DECIDE: v}, "K": True, "VK": v})
        return fl
    cae, det = LS.controles_curva(filas_curva(), LS.DECIDE, E, CC)
    chk("curva: sin sesgo, la ganancia pareja no mueve D y la del cenit lo sube",
        not cae and det["ganancia_pareja"]["ok"] and det["ganancia_cenit"]["ok"] and det["n"] == 10, det)
    cae_s, det_s = LS.controles_curva(filas_curva(sesgo=0.3), LS.DECIDE, E, CC)
    chk("curva: un sesgo de plataforma x0,3 cae", cae_s and det_s["sesgo_plataforma"], det_s["sesgo_plataforma"])
    cae_v, det_v = LS.controles_curva([], LS.DECIDE, E, CC)
    chk("curva: sin pares los controles dan SIN SUSTRATO y no caen",
        not cae_v and det_v["ganancia_pareja"] == "SIN SUSTRATO", det_v)
    fl_mal = filas_curva()
    for x in fl_mal:
        x["z"] = 10.0 if x["hora"].endswith("05:00") else 10.0
    cae_z, det_z = LS.controles_curva(fl_mal, LS.DECIDE, E, CC)
    chk("curva: sin diferencia de cenit no hay pares y no cae", not cae_z and det_z["n"] == 0, det_z)

    # ---- parada (§11.8)
    def fp(nn, na):
        fl = [{"noche": f"2026-11-{k % 28 + 1:02d}" if nn > 28 else f"2026-11-{k + 1:02d}", "c": "neg_resto"}
              for k in range(nn)]
        fl += [{"noche": "2026-11-01", "c": "pos_bajo"} for _ in range(na)]
        return fl
    def fp2(nn, na):
        fl = [{"noche": f"N{k:03d}", "c": "neg_resto"} for k in range(nn)]
        fl += [{"noche": "N000", "c": "pos_prot" if j % 2 else "pos_bajo"} for j in range(na)]
        return fl
    chk("parada: 30 noches y 40 alertas, alcanzada", LS.parada(fp2(30, 40))["alcanzada"])
    chk("parada: 29 noches no alcanza", not LS.parada(fp2(29, 40))["alcanzada"])
    chk("parada: 39 alertas no alcanza", not LS.parada(fp2(30, 39))["alcanzada"])
    chk("parada: far y negativos no cuentan como alertas",
        LS.parada(fp2(30, 0) + [{"noche": "N001", "c": "far_tabla"}])["alertas"] == 0)

    # ---- main() de punta a punta sobre carpetas y CSV sintéticos
    pm, vm, km = escena(LS, publicar, inner, neg_aparte=12)
    with tempfile.TemporaryDirectory(dir=str(AQUI)) as t:
        t = Path(t)
        for sub in ("k", "s"):
            (t / sub).mkdir()
        for vol in B.VOLS:
            ks, ss = [], []
            if vol == "Lascar":
                ks = [km[k] for k in sorted(km)]
                ss = [vm[k] for k in sorted(vm)]
                ss.append(dict(rec_via("2026-11-04 05:00", [0.5], 0.5, 0.5, 0.5), sensor="VIIRS_NOAA20_750"))
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
        with open(t / "ocr.csv", "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow(cab + ["Nota_Validacion"])
        sal, js = t / "salida.txt", t / "salida.json"
        args = ["--data-k", str(t / "k"), "--data-sombra", str(t / "s"), "--cons", str(t / "cons.csv"),
                "--ocr", str(t / "ocr.csv"), "--hasta", "2026-11-30", "--salida", str(sal), "--json", str(js)]
        cod = LS.main(args)
        txt = sal.read_text(encoding="utf-8")
        chk("main: de punta a punta sale 0", cod == 0, txt[-1500:])
        out = json.loads(js.read_text(encoding="utf-8"))
        chk("main: los controles S1 a S7 en verde", all(v["ok"] for v in out["controles"].values()), out["controles"])
        chk("main: la población sale de banco_paridad con las clases de la escena",
            "'pos_prot': 13" in txt and "'far_tabla': 12" in txt and "'neg_pub': 12" in txt and "'neg_resto': 12" in txt, txt[:3000])
        chk("main: rotulado PROVISIONAL antes de la parada", "PROVISIONAL" in txt)
        chk("main: radiante rotulado posterior a la lectura", "radiante (informa, posterior a la lectura)" in txt)
        chk("main: referencia y records con sha256 en la salida", "referencia congelada" in txt
            and out["procedencia"]["referencia"]["cons"] and out["procedencia"]["records_k"]["Lascar"])
        chk("main: el record de VIIRS 750 de la sombra no entra", "VIIRS_NOAA20_750" not in json.dumps(out))
        chk("main: el estado del paquete está en la salida", "PAQUETE en la sombra" in txt and out.get("estado"))
        cod2 = LS.main(args[:-6] + ["--desde", "2026-11-02", "--hasta", "2026-11-30", "--salida", str(sal),
                                    "--json", str(js)])
        txt2 = sal.read_text(encoding="utf-8")
        out2 = json.loads(js.read_text(encoding="utf-8"))
        chk("main VA168-01: desde antes del 2026-11-03 sale 3 sin nada de la población",
            cod2 == 3 and "== población" not in txt2 and "== cercano" not in txt2 and "PAQUETE" not in txt2 and set(out2) == {"procedencia", "controles"},
            (cod2, txt2[-800:]))
        chk("main VA168-01: el aviso de no legible nombra el control", "LECTURA NO LEGIBLE" in txt2 and "S1" in txt2)
        viejo = LS.SHA_DEPS[clave0]
        LS.SHA_DEPS[clave0] = "0" * 64
        cod3 = LS.main(args)
        LS.SHA_DEPS[clave0] = viejo
        txt3 = sal.read_text(encoding="utf-8")
        chk("main: S0 caído sale 3 sin leer nada", cod3 == 3 and "== población" not in txt3
            and "LECTURA NO LEGIBLE" in txt3 and "referencia congelada" not in txt3, txt3[-500:])

    n = len(RES)
    print(f"\nRESULTADO: {sum(RES)} de {n}")
    return 0 if all(RES) else 1


if __name__ == "__main__":
    sys.exit(main())
