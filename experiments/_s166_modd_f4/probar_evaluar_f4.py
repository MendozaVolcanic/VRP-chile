# -*- coding: utf-8 -*-
"""Batería de escenarios de evaluar_f4.py (S166 MOD-D fase 4). Cada escenario arma un mundo sintético, cambia UNA cosa
y asevera la salida que fija el pre-registro (PREREGISTRO_MODD_F4.md). Todas las comprobaciones son aserciones con
lectura tolerante (g() devuelve None si falta la clave), para que contra un evaluador vacío fallen POR ASERCIÓN y no
por excepción (lección S152/S156: sólo cuenta lo atrapado por aserción).

El predicado del tablero se reemplaza por uno sintético (publica si el record es summit con VRP > 0; magnitud = VRP del
cúmulo) salvo en N01 y N02, que corren node sobre frontend/index.html.

Uso: python probar_evaluar_f4.py [--modulo RUTA_DEL_EVALUADOR] [--solo E1,E2]
Salida: una línea por escenario (OK / FALLA ASERCION / CAE) y el resumen; código 0 si todo pasa, 1 si alguna falla
por aserción, 2 si sólo hay caídas, 3 si el módulo no carga.
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
    # solo_ocr: la alerta existe sólo en el OCR; con la tabla sola la pasada es un negativo limpio (RUTINA) (§5, A119)
    labs = {"lab": "neg_limpio", "lab_union": lab} if solo_ocr else {"lab": lab}
    return {"id": _ID[0], "vol": vol, "dt": dt, "noche": dt[:10], "sensor": "MODIS_AQUA", "z": z, **labs,
            "vrp_mirova": mir, "tramo": tramo, "grilla_censo": tramo == "C", "k_difiere_de_guardado": False,
            "estado": "ok", "motivo": None, "inner": INNER, "v_marca": True, "k_slim": krec, "v_slim": vrec,
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


def ident_ok(filas):
    return {(f["vol"], f["dt"]): {"mismo_granulo": True, "misma_mascara": True, "dvrp": 0.0, "misma_clase": True}
            for f in filas if f.get("grilla_censo")}


def correr(filas, ident=None, externos=None, sin=(), pred=pred_sintetico, esperadas=None, n_grillas=None):
    claves = [(f["vol"], f["dt"]) for f in filas]
    n = sum(1 for f in filas if f.get("grilla_censo")) if n_grillas is None else n_grillas
    return EV.evaluar(filas, esperadas if esperadas is not None else claves,
                      ident_ok(filas) if ident is None else ident, EXT_OK if externos is None else externos, sin,
                      predicado=pred, n_grillas_censo=n)


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
    idn = ident_ok(f)
    cg = list(idn)
    idn[cg[3]]["misma_mascara"] = False
    r = correr(f, ident=idn)
    chk(g(r, "controles", "identidad", "estado") == "INDECIDIBLE", "identidad máscara")
    chk(g(r, "controles", "identidad", "n_distintas") == 1, "identidad: una distinta")
    chk(g(r, "veredicto") == "INDECIDIBLE", "identidad: %s" % g(r, "veredicto"))
    f = mundo()
    idn = ident_ok(f)
    idn[list(idn)[5]]["misma_clase"] = False
    r = correr(f, ident=idn)
    chk(g(r, "controles", "identidad", "estado") == "INDECIDIBLE", "identidad con otra distance_class")


def E11_identidad_faltan():
    """VF4-02: el archivo de identidad que trae 1 de 70 pasadas no puede dar OK: lo que se exige sale de la población."""
    f = mundo()
    idn = ident_ok(f)
    del idn[list(idn)[0]]
    r = correr(f, ident=idn)
    chk(g(r, "controles", "identidad", "n_faltan") == 1, "identidad faltan")
    chk(g(r, "veredicto") == "INDECIDIBLE", "faltan: %s" % g(r, "veredicto"))
    f = mundo()
    idn = ident_ok(f)
    uno = {k: idn[k] for k in list(idn)[:1]}
    r = correr(f, ident=uno)
    chk(g(r, "controles", "identidad", "n_faltan") == 69, "identidad con 1 de 70: %s" % g(r, "controles", "identidad",
                                                                                          "n_faltan"))
    chk(g(r, "controles", "identidad", "estado") == "INDECIDIBLE", "identidad con 1 de 70 no es OK")


def E12_identidad_borde_vrp():
    for dv, esp in ((0.0009, "OK"), (0.0011, "INDECIDIBLE"), (-0.0011, "INDECIDIBLE")):
        f = mundo()
        idn = ident_ok(f)
        idn[list(idn)[0]]["dvrp"] = dv
        r = correr(f, ident=idn)
        chk(g(r, "controles", "identidad", "estado") == esp, "identidad dvrp %s: %s" % (dv, g(r, "controles",
                                                                                            "identidad")))


def E13_identidad_otro_granulo():
    f = mundo()                                               # 70 pasadas: 1 % es 0,7, así que una ya cierra
    idn = ident_ok(f)
    k0 = list(idn)[0]
    idn[k0]["mismo_granulo"] = False
    idn[k0]["misma_mascara"] = False                          # con otro gránulo la máscara no se exige
    r = correr(f, ident=idn)
    chk(g(r, "controles", "identidad", "n_otro_granulo") == 1, "otro gránulo contado")
    chk(g(r, "controles", "identidad", "n_distintas") == 0, "otro gránulo no se exige igual")
    chk(g(r, "controles", "identidad", "estado") == "INDECIDIBLE", "1 de 70 supera el 1 %")
    big = mundo() + [F(VOLS[i % 5], dia(i) + " 07:00", "neg_limpio") for i in range(40)]
    idn = ident_ok(big)                                       # 110 pasadas: 1 de 110 queda bajo el 1 %
    idn[list(idn)[0]]["mismo_granulo"] = False
    r = correr(big, ident=idn)
    chk(g(r, "controles", "identidad", "estado") == "OK", "1 de 110 queda bajo el 1 %")


def E41_identidad_grillas_declaradas():
    """VF4-02: la población tiene que traer exactamente las grillas del censo; con una de menos, la identidad no se
    midió entera aunque cada pasada presente esté bien."""
    f = mundo()
    n = sum(1 for x in f if x["grilla_censo"])
    r = correr(f, n_grillas=n + 1)
    chk(g(r, "controles", "identidad", "estado") == "INDECIDIBLE", "población con una grilla de menos")
    chk(g(EV.control_identidad(ident_ok(f), [dict(x, _evaluable=True) for x in f]), "estado") == "INDECIDIBLE",
        "sin n_grillas la identidad exige las 5.321 del censo")


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
    # en el tramo C: rojo y todo INDECIDIBLE
    r = correr(mundo(), sin=[("Lascar", "2026-05-20 03:00", "protegida")])
    chk(g(r, "controles", "cobertura", "estado") == "INDECIDIBLE", "pasada de MIROVA sin pasada nuestra")
    chk(g(r, "veredicto") == "INDECIDIBLE", "en C no hay protocolo: %s" % g(r, "veredicto"))
    # en el tramo E: el protocolo de §7 saca E entero y lo declara
    r = correr(mundo(), sin=[("Lascar", "2026-10-20 03:00", "protegida")])
    chk(g(r, "e_excluido") is not None, "en E: E excluido")


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


def E35_tramos_y_union_informan():
    """Decide la tabla sola (A119); la unión con el OCR informa. Un negativo de la tabla que K publica y V no es -1 en
    P2; si el OCR lo tiene como alerta bajo 1 MW, en la unión es +1 (V la calla). La tabla da -6 y la unión -4."""
    f = mundo()
    for x in f[-3:]:
        x["tramo"] = "E"
    f[-1]["lab_union"] = "bajo1"
    r = correr(f)
    chk(sorted(g(r, "por_tramo") or {}) == ["C", "E"], "por tramo C y E")
    chk(g(r, "brazos", "V", "p2", "neto") == -6, "decide la tabla sola: %s" % g(r, "brazos", "V", "p2", "neto"))
    chk(g(r, "brazos", "V", "p2_union", "neto") == -4, "la unión informa: %s" % g(r, "brazos", "V", "p2_union"))
    chk(g(r, "veredicto") == "PROPONER ADOPCIÓN", "la unión no decide: %s" % g(r, "veredicto"))


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


def E39_posicion_no_cambia_protegida_de_V():
    """VF4-01 (S1 del verificador): V-pico gana seis alertas bajo 1 MW pero pierde una protegida de Chillán que V
    publica. No es elegible: sigue V."""
    f = mundo() + [F(VOLS[i % 5], dia(100 + i) + " 03:00", "bajo1", k=0.3, v=0.3, mir=0.3,
                     vd={"radiante": 8.0, "cercano": 8.0, "pico": 1.0}) for i in range(6)]
    f += [F("NevadosDeChillan", dia(120) + " 07:20", "protegida", v=1.5, mir=1.6, z=58.0,
            vd={"radiante": 1.0, "cercano": 1.0, "pico": 8.0})]
    r = correr(f)
    chk(g(r, "brazos", "V-pico", "p1_vs_V", "estado") == "VETADO", "pico pierde la protegida de V")
    chk(g(r, "posicion_elegida") == "V", "pico no es elegible (%s)" % g(r, "posicion_elegida"))


def E40_otra_posicion_recupera_protegida():
    """VF4-01 (S2 del verificador): una protegida que V deja lejos y V-cercano publica no se pierde en silencio."""
    f = mundo() + [F("Lascar", dia(90) + " 03:00", "protegida", v=1.5, mir=1.6,
                     vd={"radiante": 8.0, "cercano": 1.0, "pico": 8.0})]
    r = correr(f)
    chk(g(r, "posicion_elegida") == "V", "sigue V (%s)" % g(r, "posicion_elegida"))
    chk(g(r, "protegidas_que_otra_posicion_publica") == [("Lascar", dia(90) + " 03:00")],
        "listada: %s" % g(r, "protegidas_que_otra_posicion_publica"))
    chk(g(r, "veredicto") == "DECIDE NICOLÁS", "recupera: %s" % g(r, "veredicto"))


def E42_listas_y_campos_ausentes():
    """VF4-03: sin la lista de pasadas de MIROVA sin pasada nuestra, o sin k_difiere_de_guardado, no hay OK."""
    r = correr(mundo(), sin=None)
    chk(g(r, "controles", "cobertura", "estado") == "INDECIDIBLE", "lista ausente")
    chk(g(r, "controles", "cobertura", "sin_pasada_nuestra_no_medida") is True, "lista ausente declarada")
    f = mundo()
    del f[0]["k_difiere_de_guardado"]
    r = correr(f)
    chk(g(r, "controles", "k_produccion", "estado") == "INDECIDIBLE", "campo ausente")
    chk(g(r, "controles", "k_produccion", "n_sin_campo") == 1, "campo ausente contado")


def E43_fallas_del_arnes():
    """§8.6: un estado del arnés distinto de ok, un motivo que no es de los sellados y una pasada sobrante dejan la
    cobertura en rojo (VF4-04, A06, A07, A17)."""
    f = mundo()
    f[0]["estado"] = "error_descarga"
    r = correr(f)
    chk(g(r, "controles", "cobertura", "n_fallas") == 1 and g(r, "veredicto") == "INDECIDIBLE", "estado del arnés")
    f = mundo()
    f[0]["motivo"] = "gránulo_corrupto"
    r = correr(f)
    chk(g(r, "controles", "cobertura", "n_fallas") == 1 and g(r, "veredicto") == "INDECIDIBLE", "motivo desconocido")
    f = mundo()
    r = correr(f, esperadas=[(x["vol"], x["dt"]) for x in f[1:]])
    chk(len(g(r, "controles", "cobertura", "sobran") or []) == 1 and g(r, "veredicto") == "INDECIDIBLE", "sobrante")


def E44_contador_cincuenta():
    r = correr(mundo())
    chk(g(r, "controles", "contador", "inyectados") == 50, "50 inyectados: %s" % g(r, "controles", "contador"))
    chk(g(r, "controles", "contador", "s_v_con_inyeccion") - g(r, "controles", "contador", "s_v_antes") == 50,
        "50 errores más")


def E45_p1b_k_exacto_1():
    f = mundo() + [F("Lascar", dia(90) + " 03:00", "protegida", k=1.0, v=0.9, mir=1.1)]
    r = correr(f)
    chk(len(g(r, "brazos", "V", "p1b", "decide") or []) == 1, "K = 1,0 MW exacto cuenta como sobre el corte")


def E46_chillan_bordes():
    def ch(vs, ks, z=15.0):
        f = mundo() + [F("NevadosDeChillan", dia(120 + i) + " 07:20", "protegida", k=k, v=v, mir=1.0, z=z)
                       for i, (v, k) in enumerate(zip(vs, ks))]
        return g(correr(f), "chillan")
    c = ch([0.8] * 5, [0.5] * 5)
    chk(g(c, "estado") == "RESUELTO POR EL PAQUETE", "0,8 está dentro de la banda: %s" % g(c, "estado"))
    c = ch([0.79] * 5, [0.5] * 5)
    chk(g(c, "estado") == "SIN RESOLVER", "0,79 queda fuera: %s" % g(c, "estado"))
    c = ch([1.3] * 5, [0.5] * 5)
    chk(g(c, "estado") == "SIN RESOLVER", "1,3 queda fuera: %s" % g(c, "estado"))
    c = ch([1.0] * 6 + [0.5], [0.5] * 6 + [0.9])
    chk(g(c, "p_una_cola") == [8, 128] and g(c, "estado") == "SIN RESOLVER", "6 de 7: p = 8/128 no alcanza: %s" % c)


def E47_no_peor_exige_neto_a_favor():
    """§6 bis: V no es elegible; V-cercano sí, pero publica de más una lejana (P2' contra V: +1, SIN SUSTRATO con neto
    en contra): no es «no peor» y no queda ninguna posición."""
    f = mundo() + [F("Lascar", dia(90) + " 03:00", "protegida", k=1.5, v=1.5, mir=1.6,
                     vd={"radiante": 8.0, "cercano": 1.0, "pico": 8.0})]
    f += [F("Lascar", dia(91) + " 03:00", "far_ref", v=4.0, vd={"radiante": 20.0, "cercano": 1.0, "pico": 20.0})]
    r = correr(f)
    chk(g(r, "brazos", "V-cercano", "p2l_vs_V", "estado") == "SIN SUSTRATO", "un bloque")
    chk(g(r, "posicion_elegida") is None and g(r, "veredicto") == "NO ADOPTAR", "ninguna: %s" % g(r, "veredicto"))


def E48_chillan_con_el_brazo_elegido():
    f = mundo() + [F("NevadosDeChillan", dia(120) + " 07:20", "protegida", k=1.0, v=1.5, mir=1.6, z=58.0,
                     vd={"radiante": 8.0, "cercano": 1.0, "pico": 8.0})]    # K distinto de V: con el mismo VRP es empate
    r = correr(f)
    chk(g(r, "posicion_elegida") == "V-cercano", "cercano elegido (%s)" % g(r, "posicion_elegida"))
    chk(g(r, "chillan", "brazo") == "V-cercano" and g(r, "chillan", "n_pares") == 1,
        "Chillán con el brazo elegido: %s" % g(r, "chillan"))


def E49_control_posicion_clase_y_vrp():
    f = mundo()
    for x in f:
        if x["lab"] == "protegida":
            x["v_slim"]["distance_class"] = "far"             # la distancia dice cumbre y el record dice lejos
            break
    chk(g(correr(f), "controles", "posicion", "estado") == "INDECIDIBLE", "clase que no calza con la distancia")
    f = mundo()
    for x in f:
        if x["lab"] == "protegida":
            x["vcerc_slim"]["vrp_mw"] = 9.9                   # misma clase que V y otro VRP
            break
    chk(g(correr(f), "controles", "posicion", "estado") == "INDECIDIBLE", "variante de la misma clase con otro VRP")


def E50_protocolo_tramo_e():
    """§7 (VF4-06): un rojo de cobertura sólo en el tramo E saca E entero y se lee C; un rojo que toca C deja todo
    INDECIDIBLE."""
    cola = [F(VOLS[i % 5], "2026-10-%02d 03:00" % (18 + i), "neg_limpio", tramo="E") for i in range(3)]
    f = mundo() + copy.deepcopy(cola)
    f[-1]["estado"] = "error_descarga"
    r = correr(f, sin=[("Lascar", "2026-10-25 07:20", "protegida")])
    chk(g(r, "e_excluido") is not None, "E excluido")
    chk(g(r, "controles", "cobertura", "estado") == "OK" and g(r, "veredicto") == "PROPONER ADOPCIÓN",
        "C se lee solo: %s" % g(r, "veredicto"))
    f = mundo() + copy.deepcopy(cola)
    f[-1]["estado"] = "error_descarga"
    f[0]["estado"] = "error_descarga"
    r = correr(f)
    chk(g(r, "e_excluido") is None and g(r, "veredicto") == "INDECIDIBLE", "rojo en C: %s" % g(r, "veredicto"))


def E51_main_de_punta_a_punta():
    """VF4-09: la lectura de archivos (cargar, fusión con la población, identidad, externos) da lo mismo que llamar al
    evaluador en memoria; y una población sin la lista sin_pasada_nuestra deja la cobertura en rojo."""
    import json
    import tempfile
    f = mundo()
    directo = correr(copy.deepcopy(f))
    pob_campos = ("lab", "lab_union", "vrp_mirova", "tramo", "grilla_censo")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "art").mkdir()
        with open(td / "art" / "f4_parte0.jsonl", "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"tipo": "cabecera"}) + "\n")
            for x in f:
                fh.write(json.dumps(dict({k: v for k, v in x.items() if k not in pob_campos}, tipo="record")) + "\n")
        pas = [{k: x[k] for k in ("vol", "dt") + pob_campos if k in x} for x in f]
        n = sum(1 for x in f if x["grilla_censo"])
        for nombre, pob in (("con", {"pasadas": pas, "sin_pasada_nuestra": []}), ("sin", {"pasadas": pas})):
            (td / ("pob_%s.json" % nombre)).write_text(json.dumps(pob), encoding="utf-8")
        (td / "ident.json").write_text(json.dumps({"pasadas": [dict(v, vol=k[0], dt=k[1])
                                                               for k, v in ident_ok(f).items()]}), encoding="utf-8")
        (td / "ext.json").write_text(json.dumps(EXT_OK), encoding="utf-8")
        base = ["--art", str(td / "art"), "--identidad", str(td / "ident.json"), "--externos", str(td / "ext.json")]
        # main no acepta otro total de grillas que el del censo (5.321): la prueba ajusta la constante del módulo, que es
        # lo único que puede cambiarlo, y la restituye al salir
        viejo, EV.N_GRILLAS_CENSO = EV.N_GRILLAS_CENSO, n
        try:
            r = EV.main(base + ["--poblacion", str(td / "pob_con.json"), "--salida", str(td / "r.json")],
                        predicado=pred_sintetico)
            r2 = EV.main(base + ["--poblacion", str(td / "pob_sin.json"), "--salida", str(td / "r2.json")],
                         predicado=pred_sintetico)
        finally:
            EV.N_GRILLAS_CENSO = viejo
        chk(g(r, "veredicto") == g(directo, "veredicto") == "PROPONER ADOPCIÓN", "main: %s" % g(r, "veredicto"))
        chk(g(r, "brazos", "V", "p2", "neto") == g(directo, "brazos", "V", "p2", "neto"), "main: mismo P2")
        chk((td / "r.json").exists(), "main escribe el resultado")
        chk(g(r2, "controles", "cobertura", "estado") == "INDECIDIBLE", "población sin la lista: rojo")


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
    try:
        EV = cargar(a.modulo)
    except Exception as x:  # noqa: BLE001  (VF4-08: una copia que no carga no es atrapada)
        print("NO CARGA        ", type(x).__name__, str(x)[:200])
        sys.exit(3)
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
