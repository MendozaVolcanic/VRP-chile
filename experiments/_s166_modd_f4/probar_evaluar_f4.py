# -*- coding: utf-8 -*-
"""Batería de escenarios de evaluar_f4.py (S166 MOD-D fase 4). Cada escenario arma un mundo sintético, cambia UNA cosa
y asevera la salida que fija el pre-registro (PREREGISTRO_MODD_F4.md). Todas las comprobaciones son aserciones con
lectura tolerante (g() devuelve None si falta la clave), para que contra un evaluador vacío fallen POR ASERCIÓN y no
por excepción (lección S152/S156: sólo cuenta lo atrapado por aserción).

El predicado del tablero se reemplaza por uno sintético (publica si el record es summit con VRP > 0; magnitud = VRP del
cúmulo) salvo en N01 y N02, que corren node sobre frontend/index.html.

Uso: python probar_evaluar_f4.py [--modulo RUTA_DEL_EVALUADOR] [--solo E1,E2]
Salida: una línea por escenario (OK / FALLA ASERCION / CAE) y el resumen; código 0 si todo pasa, 1 si alguna falla
por aserción, 2 si sólo hay caídas.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import sys
import traceback
from pathlib import Path

AQUI = Path(__file__).resolve().parent
EV = None


def cargar(ruta):
    spec = importlib.util.spec_from_file_location("evaluar_f4_bajo_prueba", ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["evaluar_f4_bajo_prueba"] = mod
    spec.loader.exec_module(mod)
    return mod


def g(x, *ruta):
    for k in ruta:
        try:
            x = x[k]
        except (KeyError, IndexError, TypeError):
            return None
    return x


def chk(cond, msg):
    if not cond:
        raise AssertionError(msg)


# ------------------------------------------------------------------ mundo sintético
INNER = 5.0
R0 = {"vrp_mw": 0.0, "primary_cluster": None, "distance_class": None, "t_max_k": None, "sensor": "MODIS_AQUA",
      "triggered_test1": False, "anomaly_pixels": [], "final_hotspot_dist_km": None}


def R(vrp, dist=1.0, inner=INNER, n=2):
    if vrp is None:
        return copy.deepcopy(R0)
    return {"vrp_mw": vrp, "distance_class": "summit" if dist <= inner else "far", "t_max_k": 300.0,
            "sensor": "MODIS_AQUA", "triggered_test1": False, "final_hotspot_dist_km": round(dist, 3),
            "primary_cluster": {"vrp_mw": vrp, "centroid_dist_km": round(dist, 3), "n_pixels": n},
            "anomaly_pixels": [{"dist_km": round(dist, 2), "bt_k": 300.0} for _ in range(n)]}


_ID = [0]


def F(vol, dt, lab, k=None, v=None, kd=1.0, vd=None, z=20.0, mir=None, tramo="C", solo_ocr=False):
    _ID[0] += 1
    vd = vd or {"radiante": 1.0, "cercano": 1.0, "pico": 1.0}
    vrec = R(v, vd["radiante"])
    krec = R(k, kd)
    return {"id": _ID[0], "vol": vol, "dt": dt, "noche": dt[:10], "sensor": "MODIS_AQUA", "z": z, "lab": lab,
            "vrp_mirova": mir, "tramo": tramo, "solo_ocr": solo_ocr, "estado": "ok", "motivo": None, "inner": INNER,
            "v_marca": True, "k_slim": krec, "v_slim": vrec,
            "vcerc_slim": EV.variante_posicion(vrec, "cercano", vd, INNER) if v is not None else copy.deepcopy(vrec),
            "vpico_slim": EV.variante_posicion(vrec, "pico", vd, INNER) if v is not None else copy.deepcopy(vrec),
            "dist": vd if v is not None else None,
            "pub_runner": {"K": int(k is not None and k > 0 and kd <= INNER)}}


VOLS = ("Lascar", "Villarrica", "Llaima", "Copahue", "Isluga")


def dia(i):
    m, d = divmod(i, 28)
    return "2026-%02d-%02d" % (3 + m, 1 + d)


def mundo():
    """60 negativos sin nada, 2 protegidas y 2 bajo 1 MW que publican los dos, y 6 negativos que K publica y V no
    (en 6 noches-volcán distintas): P2 de V contra K da GANA (neto -6, B 6, p = 1/64)."""
    filas = []
    for i in range(60):
        filas.append(F(VOLS[i % 5], dia(i) + " 03:00", "neg_limpio"))
    filas.append(F("Lascar", dia(70) + " 03:00", "protegida", k=2.0, v=2.2, mir=2.1))
    filas.append(F("Lascar", dia(71) + " 03:00", "protegida", k=1.8, v=2.0, mir=2.0))
    filas.append(F("Lascar", dia(72) + " 03:00", "bajo1", k=0.3, v=0.4, mir=0.4))
    filas.append(F("Lascar", dia(73) + " 03:00", "bajo1", k=0.3, v=0.35, mir=0.4))
    for i in range(6):
        filas.append(F(VOLS[i % 5], dia(80 + i) + " 05:00", "neg_limpio", k=0.2))
    return filas


def pred_sintetico(casos):
    out = []
    for r, _inner in casos:
        pc = (r or {}).get("primary_cluster") or {}
        pub = int(r is not None and r.get("distance_class") == "summit" and (pc.get("vrp_mw") or 0) > 0
                  and (r.get("vrp_mw") or 0) > 0)
        out.append((pub, float(pc.get("vrp_mw") or 0.0) if pub else 0.0))
    return out


def pred_sin_magnitud(casos):
    """Predicado roto: no mira la magnitud (el contador tiene que verlo)."""
    return [(int(r is not None and r.get("distance_class") == "summit"), 1.0) for r, _ in casos]


def pred_sin_clase(casos):
    """Predicado roto: no mira distance_class (el control del predicado tiene que verlo)."""
    return [(int(r is not None and (r.get("vrp_mw") or 0) > 0), float(r.get("vrp_mw") or 0) if r else 0.0)
            for r, _ in casos]


EXT_OK = {k: {"estado": "OK"} for k in ("referencia", "reetiquetado", "manifiesto", "procedencia", "predicado")}


def correr(filas, ident=None, con_grilla=None, externos=None, sin=(), pred=pred_sintetico, esperadas=None):
    claves = [(f["vol"], f["dt"]) for f in filas]
    cg = [(f["vol"], f["dt"]) for f in filas if f.get("tramo") == "C" and f.get("estado") == "ok"
          and not f.get("motivo") and f.get("v_marca") is True] if con_grilla is None else con_grilla
    idn = {k: {"mismo_granulo": True, "misma_mascara": True, "dvrp": 0.0, "misma_clase": True} for k in cg} \
        if ident is None else ident
    return EV.evaluar(filas, esperadas if esperadas is not None else claves, idn, cg,
                      EXT_OK if externos is None else externos, sin, predicado=pred)


# ------------------------------------------------------------------ escenarios
def E01_base_propone():
    r = correr(mundo())
    chk(g(r, "veredicto") == "PROPONER ADOPCIÓN", "base: %s" % g(r, "veredicto"))
    chk(g(r, "posicion_elegida") == "V", "base: posición %s" % g(r, "posicion_elegida"))
    chk(g(r, "brazos", "V", "p2", "estado") == "GANA", "base: P2 %s" % g(r, "brazos", "V", "p2", "estado"))
    chk(g(r, "brazos", "V", "p2", "neto") == -6 and g(r, "brazos", "V", "p2", "B") == 6, "base: neto/B")
    for c in ("k_produccion", "identidad", "marca", "placebo", "contador", "cobertura", "posicion",
              "predicado_distance_class", "evaluar_d25"):
        chk(g(r, "controles", c, "estado") == "OK", "base: control %s %s" % (c, g(r, "controles", c)))


def E02_sin_cambio_indecidible():
    f = [x for x in mundo() if not (x["lab"] == "neg_limpio" and g(x, "k_slim", "vrp_mw"))]
    r = correr(f)
    chk(g(r, "brazos", "V", "p2", "estado") == "SIN SUSTRATO", "sin cambio: P2 %s" % g(r, "brazos", "V", "p2", "estado"))
    chk(g(r, "veredicto") == "INDECIDIBLE", "sin cambio: %s" % g(r, "veredicto"))


def E03_p1_veto():
    f = mundo() + [F("Lascar", dia(90) + " 03:00", "protegida", k=1.5, v=None, mir=1.6)]
    r = correr(f)
    chk(g(r, "brazos", "V", "p1", "estado") == "VETADO", "veto: %s" % g(r, "brazos", "V", "p1", "estado"))
    chk(g(r, "posicion_elegida") is None, "veto: ningún brazo elegible")
    chk(g(r, "veredicto") == "NO ADOPTAR", "veto: %s" % g(r, "veredicto"))


def E04_p1_solo_ocr_decide_nicolas():
    f = mundo() + [F("Lascar", dia(90) + " 03:00", "protegida", k=1.5, v=None, mir=1.6, solo_ocr=True)]
    r = correr(f)
    chk(g(r, "brazos", "V", "p1", "estado") == "SOLO OCR", "solo OCR: %s" % g(r, "brazos", "V", "p1", "estado"))
    chk(g(r, "posicion_elegida") == "V", "solo OCR: V sigue elegible")
    chk(g(r, "veredicto") == "DECIDE NICOLÁS", "solo OCR: %s" % g(r, "veredicto"))


def E05_p2_pierde():
    f = [x for x in mundo() if not (x["lab"] == "neg_limpio" and g(x, "k_slim", "vrp_mw"))]
    f += [F(VOLS[i % 5], dia(80 + i) + " 05:00", "neg_limpio", v=0.2) for i in range(6)]
    r = correr(f)
    chk(g(r, "brazos", "V", "p2", "estado") == "PIERDE", "pierde: %s" % g(r, "brazos", "V", "p2", "estado"))
    chk(g(r, "veredicto") == "NO ADOPTAR", "pierde: %s" % g(r, "veredicto"))


def E06_p2_bloquea():
    f = [x for x in mundo() if not (x["lab"] == "neg_limpio" and g(x, "k_slim", "vrp_mw"))]
    f += [F(VOLS[i % 5], dia(80 + i) + " 05:00", "neg_limpio", v=0.2) for i in range(3)]
    f += [F(VOLS[i % 5], dia(90 + i) + " 05:00", "neg_limpio", k=0.2) for i in range(2)]
    r = correr(f)
    chk(g(r, "brazos", "V", "p2", "estado") == "BLOQUEA", "bloquea: %s" % g(r, "brazos", "V", "p2", "estado"))
    chk(g(r, "veredicto") == "DECIDE NICOLÁS", "bloquea: %s" % g(r, "veredicto"))


def E07_p1b_decide():
    f = mundo() + [F("Lascar", dia(90) + " 03:00", "protegida", k=1.2, v=0.9, mir=1.1)]
    r = correr(f)
    chk(len(g(r, "brazos", "V", "p1b", "decide") or []) == 1, "p1b: %s" % g(r, "brazos", "V", "p1b"))
    chk(g(r, "veredicto") == "DECIDE NICOLÁS", "p1b: %s" % g(r, "veredicto"))


def E08_p1b_contraria_no_decide():
    f = mundo() + [F("Lascar", dia(90) + " 03:00", "protegida", k=0.9, v=1.2, mir=1.1)]
    r = correr(f)
    chk(len(g(r, "brazos", "V", "p1b", "contraria_lista") or []) == 1, "p1b contraria listada")
    chk(not g(r, "brazos", "V", "p1b", "decide"), "p1b contraria no decide")
    chk(g(r, "veredicto") == "PROPONER ADOPCIÓN", "p1b contraria: %s" % g(r, "veredicto"))


def E09_m_empeora():
    f = mundo() + [F(VOLS[i % 5], dia(100 + i) + " 03:00", "bajo1", k=0.3, v=0.9, mir=0.3) for i in range(12)]
    r = correr(f)
    chk(g(r, "brazos", "V", "m", "regla") == "EMPEORA", "m: %s" % g(r, "brazos", "V", "m", "regla"))
    chk(g(r, "veredicto") == "DECIDE NICOLÁS", "m: %s" % g(r, "veredicto"))


def E10_identidad_mascara():
    f = mundo()
    cg = [(x["vol"], x["dt"]) for x in f]
    idn = {k: {"mismo_granulo": True, "misma_mascara": True, "dvrp": 0.0, "misma_clase": True} for k in cg}
    idn[cg[3]]["misma_mascara"] = False
    r = correr(f, ident=idn, con_grilla=cg)
    chk(g(r, "controles", "identidad", "estado") == "INDECIDIBLE", "identidad máscara")
    chk(g(r, "controles", "identidad", "n_distintas") == 1, "identidad: una distinta")
    chk(g(r, "veredicto") == "INDECIDIBLE", "identidad: %s" % g(r, "veredicto"))
    idn = {k: {"mismo_granulo": True, "misma_mascara": True, "dvrp": 0.0, "misma_clase": True} for k in cg}
    idn[cg[5]]["misma_clase"] = False
    r = correr(copy.deepcopy(mundo()), ident=idn, con_grilla=cg)
    chk(g(r, "controles", "identidad", "estado") == "INDECIDIBLE", "identidad con otra distance_class")


def E11_identidad_faltan():
    f = mundo()
    cg = [(x["vol"], x["dt"]) for x in f]
    idn = {k: {"mismo_granulo": True, "misma_mascara": True, "dvrp": 0.0, "misma_clase": True} for k in cg[1:]}
    r = correr(f, ident=idn, con_grilla=cg)
    chk(g(r, "controles", "identidad", "n_faltan") == 1, "identidad faltan")
    chk(g(r, "veredicto") == "INDECIDIBLE", "faltan: %s" % g(r, "veredicto"))


def E12_identidad_borde_vrp():
    f = mundo()
    cg = [(x["vol"], x["dt"]) for x in f]
    for dv, esp in ((0.0009, "OK"), (0.0011, "INDECIDIBLE"), (-0.0011, "INDECIDIBLE")):
        idn = {k: {"mismo_granulo": True, "misma_mascara": True, "dvrp": 0.0, "misma_clase": True} for k in cg}
        idn[cg[0]]["dvrp"] = dv
        r = correr(copy.deepcopy(f), ident=idn, con_grilla=cg)
        chk(g(r, "controles", "identidad", "estado") == esp, "identidad dvrp %s: %s" % (dv, g(r, "controles",
                                                                                            "identidad")))


def E13_identidad_otro_granulo():
    f = mundo()
    cg = [(x["vol"], x["dt"]) for x in f]                     # 70 pasadas: 1 % es 0,7, así que una ya cierra
    idn = {k: {"mismo_granulo": True, "misma_mascara": True, "dvrp": 0.0, "misma_clase": True} for k in cg}
    idn[cg[0]]["mismo_granulo"] = False
    idn[cg[0]]["misma_mascara"] = False                       # con otro gránulo la máscara no se exige
    r = correr(f, ident=idn, con_grilla=cg)
    chk(g(r, "controles", "identidad", "n_otro_granulo") == 1, "otro gránulo contado")
    chk(g(r, "controles", "identidad", "n_distintas") == 0, "otro gránulo no se exige igual")
    chk(g(r, "controles", "identidad", "estado") == "INDECIDIBLE", "1 de 70 supera el 1 %")
    big = f + [F(VOLS[i % 5], dia(i) + " 07:00", "neg_limpio") for i in range(40)]
    cg = [(x["vol"], x["dt"]) for x in big]                   # 110 pasadas: 1 de 110 queda bajo el 1 %
    idn = {k: {"mismo_granulo": True, "misma_mascara": True, "dvrp": 0.0, "misma_clase": True} for k in cg}
    idn[cg[0]]["mismo_granulo"] = False
    r = correr(big, ident=idn, con_grilla=cg)
    chk(g(r, "controles", "identidad", "estado") == "OK", "1 de 110 queda bajo el 1 %")


def E14_via_no_corrio():
    f = mundo()
    f[0]["v_marca"] = "sin_mxd03"
    r = correr(f)
    chk(g(r, "controles", "cobertura", "estado") == "INDECIDIBLE", "vía sin marca: cobertura")
    chk(g(r, "veredicto") == "INDECIDIBLE", "vía sin marca: %s" % g(r, "veredicto"))


def E15_motivo_sellado():
    f = mundo()
    f[0]["motivo"] = "volcan_fuera_del_granulo"
    r = correr(f)
    chk(g(r, "controles", "cobertura", "estado") == "OK", "motivo sellado no es falla")
    chk(g(r, "controles", "cobertura", "n_evaluables") == len(f) - 1, "motivo sellado sale del denominador")
    chk(g(r, "veredicto") == "PROPONER ADOPCIÓN", "motivo sellado: %s" % g(r, "veredicto"))
    f = mundo() + [F("Lascar", dia(90) + " 03:00", "protegida", k=1.5, v=1.5, mir=1.6)]
    f[-1]["motivo"] = "escena_invalida"
    r = correr(f)
    chk(len(g(r, "controles", "cobertura", "protegidas_k_fuera") or []) == 1, "protegida de K fuera listada")
    chk(g(r, "veredicto") == "DECIDE NICOLÁS", "protegida de K fuera: %s" % g(r, "veredicto"))
    f = mundo() + [F("Lascar", dia(90) + " 03:00", "protegida", k=1.5, v=1.5, mir=1.6)]
    f[-1]["motivo"] = "escena_invalida"
    f[-1]["pub_runner"] = {"K": 0}                            # el runner dijo otra cosa que el predicado del evaluador
    r = correr(f)
    chk(g(r, "controles", "cobertura", "estado") == "INDECIDIBLE", "predicado de K distinto del runner en una excluida")
    f = mundo() + [F("Lascar", dia(90) + " 03:00", "protegida", k=1.5, v=1.5, mir=1.6, kd=9.0)]
    f[-1]["motivo"] = "escena_invalida"                       # K la ve lejos: no publica, así que no se lista
    r = correr(f)
    chk(g(r, "controles", "cobertura", "protegidas_k_fuera") == [], "excluida que K no publica no se lista")


def E16_repetida_y_faltante():
    f = mundo()
    r = correr(f + [copy.deepcopy(f[0])])
    chk(g(r, "controles", "cobertura", "estado") == "INDECIDIBLE" and g(r, "controles", "cobertura", "repetidas"),
        "repetida")
    f = mundo()
    esperadas = [(x["vol"], x["dt"]) for x in f] + [("Lascar", "2026-09-30 03:00")]
    r = correr(f, esperadas=esperadas)
    chk(g(r, "controles", "cobertura", "n_faltan") == 1, "faltante")
    chk(g(r, "veredicto") == "INDECIDIBLE", "faltante: %s" % g(r, "veredicto"))


def E17_placebo_roto():
    f = mundo()
    for x in f:
        x["_evaluable"], x["_motivo"] = EV.evaluable(x)
    EV.armar_tabla(f, pred_sintetico)
    chk(g(EV.control_placebo(f), "estado") == "OK", "placebo sano")
    for x in f:
        if g(x, "_t", "placebo", "pub"):
            x["_t"]["placebo"]["mag"] *= 1.1
            break
    chk(g(EV.control_placebo(f), "estado") == "INDECIDIBLE", "placebo con una ganancia distinta de 1,2")


def E18_contador_ciego():
    r = correr(mundo(), pred=pred_sin_magnitud)
    chk(g(r, "controles", "contador", "estado") == "INDECIDIBLE", "contador con predicado sin magnitud")
    chk(g(r, "veredicto") == "INDECIDIBLE", "contador: %s" % g(r, "veredicto"))


def E19_predicado_sin_clase():
    r = correr(mundo(), pred=pred_sin_clase)
    chk(g(r, "controles", "predicado_distance_class", "estado") == "INDECIDIBLE", "predicado sin clase")
    chk(g(r, "veredicto") == "INDECIDIBLE", "predicado sin clase: %s" % g(r, "veredicto"))


def E20_far_ref_un_caso_no_gana():
    f = mundo() + [F("Lascar", dia(95) + " 03:00", "far_ref", v=11.7,
                     vd={"radiante": 26.2, "cercano": 0.26, "pico": 26.2})]
    r = correr(f)
    chk(g(r, "brazos", "V-cercano", "p2l_vs_V", "neto") == 1, "far_ref: cercano publica de más (+1)")
    chk(g(r, "brazos", "V-cercano", "p2l_vs_V", "estado") == "SIN SUSTRATO", "far_ref: un bloque")
    chk(g(r, "brazos", "V", "p2", "neto") == -6, "far_ref no entra a P2 sellada")
    chk(g(r, "posicion_elegida") == "V", "far_ref: sigue V (%s)" % g(r, "posicion_elegida"))
    d = g(r, "descriptivas_posicion") or {}
    chk([(x.get("vol"), x.get("lab")) for x in d.get("V-cercano") or []] == [("Lascar", "far_ref")],
        "descriptivas: la pasada lejana que cambia con cercano %s" % d.get("V-cercano"))
    chk(d.get("V-pico") == [] and g(d, "far_ref", "n") == 1 and g(d, "far_ref", "con_alertados") == 1,
        "descriptivas: pico no cambia; una lejana con alertados %s" % d)


def E21_cercano_gana():
    f = mundo() + [F(VOLS[i % 5], dia(100 + i) + " 03:00", "bajo1", k=0.3, v=0.3, mir=0.3,
                     vd={"radiante": 8.0, "cercano": 1.0, "pico": 8.0}) for i in range(6)]
    r = correr(f)
    chk(g(r, "brazos", "V-cercano", "p2l_vs_V", "estado") == "GANA", "cercano gana: %s" % g(
        r, "brazos", "V-cercano", "p2l_vs_V", "estado"))
    chk(g(r, "posicion_elegida") == "V-cercano", "cercano elegido: %s" % g(r, "posicion_elegida"))
    chk(g(r, "veredicto") == "PROPONER ADOPCIÓN", "cercano: veredicto sobre el elegido %s" % g(r, "veredicto"))


def E22_empate_de_dos_gana_pico():
    f = mundo() + [F(VOLS[i % 5], dia(100 + i) + " 03:00", "bajo1", k=0.3, v=0.3, mir=0.3,
                     vd={"radiante": 8.0, "cercano": 1.0, "pico": 1.0}) for i in range(6)]
    r = correr(f)
    chk(g(r, "posicion_elegida") == "V-pico", "empate: pico (%s)" % g(r, "posicion_elegida"))


def E23_menor_error_gana_entre_dos():
    f = mundo() + [F(VOLS[i % 5], dia(100 + i) + " 03:00", "bajo1", k=0.3, v=0.3, mir=0.3,
                     vd={"radiante": 8.0, "cercano": 1.0, "pico": 1.0}) for i in range(6)]
    f += [F("Lascar", dia(110) + " 03:00", "far_ref", v=5.0, vd={"radiante": 20.0, "cercano": 20.0, "pico": 2.0})]
    r = correr(f)
    chk(g(r, "posicion_elegida") == "V-cercano", "dos ganan, cercano con menos errores (%s)" % g(r, "posicion_elegida"))


def E24_v_no_elegible_cercano_si():
    f = mundo() + [F("Lascar", dia(90) + " 03:00", "protegida", k=1.5, v=1.5, mir=1.6,
                     vd={"radiante": 8.0, "cercano": 1.0, "pico": 8.0})]
    r = correr(f)
    chk(g(r, "brazos", "V", "p1", "estado") == "VETADO", "V vetado")
    chk(g(r, "posicion_elegida") == "V-cercano", "V no elegible: cercano (%s)" % g(r, "posicion_elegida"))
    chk(g(r, "veredicto") == "PROPONER ADOPCIÓN", "veredicto sobre cercano: %s" % g(r, "veredicto"))


def E25_ninguna_posicion():
    f = mundo() + [F("Lascar", dia(90) + " 03:00", "protegida", k=1.5, v=1.5, mir=1.6,
                     vd={"radiante": 8.0, "cercano": 7.0, "pico": 8.0})]
    r = correr(f)
    chk(g(r, "posicion_elegida") is None and g(r, "posicion_motivo") == "NINGUNA POSICIÓN ELEGIBLE", "ninguna")
    chk(g(r, "veredicto") == "NO ADOPTAR", "ninguna: %s" % g(r, "veredicto"))


def E26_p2_lejana_pierde():
    f = mundo() + [F(VOLS[i % 5], dia(100 + i) + " 03:00", "far_ref", v=3.0) for i in range(20)]
    r = correr(f)
    chk(g(r, "brazos", "V", "p2", "estado") == "GANA", "P2 sellada sigue GANA")
    chk(g(r, "brazos", "V", "p2l_vs_K", "estado") == "PIERDE", "P2' PIERDE: %s" % g(r, "brazos", "V", "p2l_vs_K"))
    chk(g(r, "veredicto") == "NO ADOPTAR", "P2' pierde: %s" % g(r, "veredicto"))


def E27_chillan_resuelto():
    f = mundo() + [F("NevadosDeChillan", dia(120 + i) + " 07:20", "protegida", k=0.5, v=1.0, mir=1.0, z=10 + 10 * i)
                   for i in range(5)]
    r = correr(f)
    chk(g(r, "chillan", "estado") == "RESUELTO POR EL PAQUETE", "chillán resuelto: %s" % g(r, "chillan"))
    chk(g(r, "chillan", "p_una_cola") == [1, 32], "chillán p")
    t = g(r, "chillan_por_tramo") or {}
    chk(sorted(t) == ["10-20", "20-30", "30-40", "40-50", "50-60"], "chillán por tramo: %s" % sorted(t))
    chk(g(t, "50-60", "razon_b") == 1.0 and g(t, "50-60", "razon_K") == 0.5, "chillán tramo razones")


def E28_chillan_sensor_y_sin_sustrato():
    f = mundo() + [F("NevadosDeChillan", dia(120 + i) + " 07:20", "protegida", k=0.5, v=1.0, mir=1.0, z=15)
                   for i in range(3)]
    f += [F("NevadosDeChillan", dia(130 + i) + " 07:20", "protegida", k=0.6, v=0.5, mir=1.0, z=50) for i in range(3)]
    r = correr(f)
    chk(g(r, "chillan", "estado") == "ES DEL SENSOR", "chillán sensor: %s" % g(r, "chillan"))
    f = mundo() + [F("NevadosDeChillan", dia(120 + i) + " 07:20", "protegida", k=0.5, v=1.0, mir=1.0) for i in range(4)]
    r = correr(f)
    chk(g(r, "chillan", "estado") == "SIN SUSTRATO", "chillán 4 pares: %s" % g(r, "chillan", "estado"))


def E29_k_produccion():
    f = mundo()
    f[0]["k_difiere_de_guardado"] = True
    r = correr(f)
    chk(g(r, "controles", "k_produccion", "estado") == "INDECIDIBLE", "K distinto sin reproducir")
    f = mundo()
    f[0]["k_difiere_de_guardado"] = True
    f[0]["k_reproducida_en_su_sha"] = True
    r = correr(f)
    chk(g(r, "controles", "k_produccion", "estado") == "OK", "K distinto reproducido en su sha")
    f = mundo()
    f[-1]["pub_runner"] = {"K": 0}
    r = correr(f)
    chk(g(r, "controles", "k_produccion", "estado") == "INDECIDIBLE", "predicado del runner distinto")


def E30_sin_pasada_nuestra():
    r = correr(mundo(), sin=[("Lascar", "2026-10-20 03:00", "protegida")])
    chk(g(r, "controles", "cobertura", "estado") == "INDECIDIBLE", "pasada de MIROVA sin pasada nuestra")


def E31_store_descarto():
    f = mundo()
    f[0]["v_slim"] = None
    r = correr(f)
    chk(g(r, "controles", "marca", "estado") == "INDECIDIBLE", "record de V ausente sin explicación")
    f = mundo()
    f[0]["v_slim"] = None
    f[0]["store_descarto"] = {"V": True}
    r = correr(f)
    chk(g(r, "controles", "marca", "estado") == "OK", "record de V descartado por store")


def E32_control_posicion():
    f = mundo()
    for x in f:
        if x["lab"] == "protegida":
            x["dist"] = {"radiante": 1.5, "cercano": 1.0, "pico": 1.0}
            break
    r = correr(f)
    chk(g(r, "controles", "posicion", "estado") == "INDECIDIBLE", "distancia radiante que no reproduce al record")
    f = mundo()
    for x in f:
        if x["lab"] == "protegida":
            x["vcerc_slim"]["anomaly_pixels"] = []
            break
    r = correr(f)
    chk(g(r, "controles", "posicion", "estado") == "INDECIDIBLE", "variante con otros píxeles")


def E33_externo_ausente():
    ext = dict(EXT_OK)
    ext.pop("referencia")
    r = correr(mundo(), externos=ext)
    chk(g(r, "controles", "referencia", "estado") == "INDECIDIBLE", "externo ausente")
    chk(g(r, "veredicto") == "INDECIDIBLE", "externo ausente: %s" % g(r, "veredicto"))
    ext = dict(EXT_OK, procedencia={"estado": "INDECIDIBLE"})
    chk(g(correr(mundo(), externos=ext), "veredicto") == "INDECIDIBLE", "externo en rojo")


def E34_empate_propone():
    f = [x for x in mundo() if not (x["lab"] == "neg_limpio" and g(x, "k_slim", "vrp_mw"))]
    f += [F(VOLS[i % 5], dia(80 + i) + " 05:00", "neg_limpio", k=0.2) for i in range(3)]
    f += [F(VOLS[i % 5], dia(90 + i) + " 05:00", "neg_limpio", v=0.2) for i in range(3)]
    r = correr(f)
    chk(g(r, "brazos", "V", "p2", "estado") == "EMPATE", "empate: %s" % g(r, "brazos", "V", "p2", "estado"))
    chk(g(r, "veredicto") == "PROPONER ADOPCIÓN", "empate: %s" % g(r, "veredicto"))


def E35_tramos_y_solo_ocr_informan():
    f = mundo()
    for x in f[-3:]:
        x["tramo"] = "E"
    f[-1]["solo_ocr"] = True
    r = correr(f)
    chk(sorted(g(r, "por_tramo") or {}) == ["C", "E"], "por tramo C y E")
    chk(g(r, "brazos", "V", "p2", "neto_sin_solo_ocr") == -5, "neto sin las solo OCR")


def E36_distancias_reglas():
    sys.path.insert(0, str(EV.RAIZ))
    from pipeline import mirova_v750_codigo as MV
    d = EV.distancias([(10, 10), (10, 11), (30, 30)], [5.0, 6.0, 9.0], (10.0, 10.0), 1.0, MV._cumulo_del_mas_radiante)
    chk(d and abs(d["radiante"] - 800 ** 0.5) < 1e-9 and d["cercano"] == 0.0 and abs(d["pico"] - 800 ** 0.5) < 1e-9,
        "distancias 1: %s" % d)
    d = EV.distancias([(10, 10), (10, 11), (30, 30)], [5.0, 9.0, 1.0], (10.0, 10.0), 1.0, MV._cumulo_del_mas_radiante)
    chk(d and abs(d["radiante"] - 0.5) < 1e-9 and d["cercano"] == 0.0 and abs(d["pico"] - 1.0) < 1e-9,
        "distancias 2: %s" % d)
    v = R(2.0, 8.0)
    w = EV.variante_posicion(v, "cercano", {"radiante": 8.0, "cercano": 0.4, "pico": 8.0}, INNER)
    chk(g(w, "distance_class") == "summit" and g(w, "primary_cluster", "centroid_dist_km") == 0.4
        and g(w, "final_hotspot_dist_km") == 0.4 and g(w, "vrp_mw") == 2.0 and g(v, "distance_class") == "far",
        "variante cercano")
    w = EV.variante_posicion(v, "pico", {"radiante": 8.0, "cercano": 0.4, "pico": 5.0}, INNER)
    chk(g(w, "distance_class") == "summit", "frontera inclusiva: 5,0 km con inner 5 es summit")


def E37_bloque_es_la_noche():
    """Cinco errores de K que V corrige, dos de ellos en la misma noche-volcán: son 4 bloques, no 5 (SIN SUSTRATO).
    Si el bloque fuera la pasada, saldría GANA con p = 1/32."""
    f = [x for x in mundo() if not (x["lab"] == "neg_limpio" and g(x, "k_slim", "vrp_mw"))]
    f += [F(VOLS[i % 5], dia(80 + i) + " 05:00", "neg_limpio", k=0.2) for i in range(3)]
    f += [F("Lascar", dia(90) + " 02:00", "neg_limpio", k=0.2), F("Lascar", dia(90) + " 06:00", "neg_limpio", k=0.2)]
    r = correr(f)
    chk(g(r, "brazos", "V", "p2", "B") == 4, "bloques: %s" % g(r, "brazos", "V", "p2", "B"))
    chk(g(r, "veredicto") == "INDECIDIBLE", "bloque noche: %s" % g(r, "veredicto"))


def E38_empate_de_posicion_no_gana():
    """V-cercano gana 3 alertas bajo 1 MW y publica de más 3 pasadas lejanas: P2' contra V da EMPATE (neto 0, B 6).
    Un empate no cambia la regla de posición: sigue V."""
    f = mundo() + [F(VOLS[i % 5], dia(100 + i) + " 03:00", "bajo1", k=0.3, v=0.3, mir=0.3,
                     vd={"radiante": 8.0, "cercano": 1.0, "pico": 8.0}) for i in range(3)]
    f += [F(VOLS[i % 5], dia(110 + i) + " 03:00", "far_ref", v=4.0, vd={"radiante": 20.0, "cercano": 1.0, "pico": 20.0})
          for i in range(3)]
    r = correr(f)
    chk(g(r, "brazos", "V-cercano", "p2l_vs_V", "estado") == "EMPATE", "empate de posición: %s" % g(
        r, "brazos", "V-cercano", "p2l_vs_V", "estado"))
    chk(g(r, "posicion_elegida") == "V", "empate de posición: sigue V (%s)" % g(r, "posicion_elegida"))


def N01_node_predicado_y_posicion():
    r = EV.control_predicado(EV.predicado_node)
    chk(g(r, "estado") == "OK" and g(r, "publica") == [1, 0], "node: control del predicado %s" % r)
    v = R(0.8, 8.0)
    w = EV.variante_posicion(v, "cercano", {"radiante": 8.0, "cercano": 0.4, "pico": 8.0}, INNER)
    out = EV.predicado_node([(v, INNER), (w, INNER)])
    chk([x[0] for x in out] == [0, 1] and abs(out[1][1] - 0.8) < 1e-9, "node: la variante cercana publica %s" % out)


def N02_node_contador():
    f = mundo()
    for x in f:
        x["_evaluable"], x["_motivo"] = EV.evaluable(x)
    EV.armar_tabla(f, EV.predicado_node)
    chk(g(EV.control_contador(f, EV.predicado_node), "estado") == "OK", "node: contador sobre el tablero real")


ESCENARIOS = [v for k, v in sorted(globals().items()) if k[:1] in "EN" and k[1:3].isdigit() and callable(v)]


def main():
    global EV
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--modulo", default=str(AQUI / "evaluar_f4.py"))
    ap.add_argument("--solo", default=None)
    a = ap.parse_args()
    EV = cargar(a.modulo)
    sel = [e for e in ESCENARIOS if not a.solo or e.__name__.split("_")[0] in a.solo.split(",")]
    ok = asercion = cae = 0
    for e in sel:
        _ID[0] = 0
        try:
            e()
            ok += 1
            print("OK              ", e.__name__, flush=True)
        except AssertionError as x:
            asercion += 1
            print("FALLA ASERCION  ", e.__name__, "|", str(x)[:160], flush=True)
        except Exception as x:  # noqa: BLE001
            cae += 1
            print("CAE             ", e.__name__, "|", type(x).__name__, str(x)[:160], flush=True)
            if "--traza" in sys.argv:
                traceback.print_exc()
    print("RESUMEN: %d escenarios, %d OK, %d fallan por aserción, %d caen" % (len(sel), ok, asercion, cae))
    sys.exit(0 if ok == len(sel) else 1 if asercion else 2)


if __name__ == "__main__":
    main()
