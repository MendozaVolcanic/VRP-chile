# -*- coding: utf-8 -*-
"""Pruebas del evaluador de MOD-D (evaluar_paquete.py) sobre pasadas sintéticas, con el predicado REAL del tablero
(node sobre frontend/index.html). Cada prueba arma a propósito una salida de las reglas selladas del pre-registro
(§4 a §8 y adenda 1) y comprueba que el evaluador la da.

Regla de la batería (S156): contra el evaluador vacío (evaluar_vacio.py, que devuelve siempre la estructura completa
con CANDIDATO y todo en orden) TODAS las pruebas tienen que fallar POR ASERCIÓN, no por excepción; contra el evaluador
de verdad, todas en verde. Una prueba que pasa contra el vacío no prueba nada.
Uso: python probar_evaluar_paquete.py [--modulo evaluar_vacio.py]   (sale 1 si alguna prueba no da lo esperado)
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
import tempfile
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
GRILLAS = json.load(open(AQUI / "grillas.json", encoding="utf-8"))
OK_EXT = {k: "OK" for k in ("blobs", "predicado", "procedencia", "referencia", "reetiquetado", "union")}


class Falla(AssertionError):
    pass


def exige(cond, msg):
    if not cond:
        raise Falla(msg)


def g(res, *ruta, defecto=None):
    x = res
    for k in ruta:
        if isinstance(x, dict) and k in x:
            x = x[k]
        else:
            return defecto
    return x


# ------------------------------------------------------------------ pasadas sintéticas
def port(v):
    if v is None:
        return {"npix": 0, "vrp_mw": None, "pixeles": [], "motivo_vacio": None}
    return {"npix": 1, "vrp_mw": v, "pixeles": [[25, 25, 2, 0.3, 0.1, 300.0]], "motivo_vacio": None}


def k_slim(v):
    if v is None:
        return None
    return {"sensor": "MODIS_AQUA", "vrp_mw": v, "f5_core_vrp_mw": v, "t_max_k": 300.0, "triggered_test1": False,
            "distance_class": "summit", "primary_cluster": {"vrp_mw": v, "n_pixels": 1, "centroid_dist_km": 0.3},
            "vrp_mir_mw": v, "discarded_reason": None, "vrp_vent_mw": None, "anomaly_pixels": []}


def fila(vol, dt, lab, k=None, pm=None, geo5="=pm", sens="=pm", mirova=None, z=20.0, **extra):
    geo5 = pm if geo5 == "=pm" else geo5
    sens = pm if sens == "=pm" else sens
    f = {"tipo": "record", "estado": "ok", "vol": vol, "dt": dt, "noche": dt[:10], "lab": lab, "z": z,
         "sensor": "MODIS_AQUA", "inner": 5.0, "vrp_mirova": mirova, "decide": False, "k_difiere_de_guardado": False,
         "codigo_sha": "abc", "k_slim": k_slim(k), "k33_slim": k_slim(k),
         "pub": {"K": int(bool(k)), "K33": int(bool(k))},
         "brazos": {"K": {"pc_vrp": k}, "K33": {"pc_vrp": k}}, "k33_igual_k": True, "port_estado": "ok",
         "port_grilla": None, "port": {"fisica": port(pm), "fisica_geo5km": port(geo5), "sensible": port(sens),
                                       "pixel": port(pm), "fisica_b21": port(pm)},
         "crater_mxd03": {"linea": 5, "frame": 600, "costura": False}, "saturados": {"b22_nan_con_b21": 0},
         "s1": {"estado": "ok", "identidad_ok": True, "u_nti2_g": 0.003, "u_eti2_g": 0.003, "n2_g": 0, "n2_roi1": 0}}
    f.update(extra)
    return f


def dia(n, h=1):
    return (datetime(2026, 4, 1, h, 5) + timedelta(days=n)).strftime("%Y-%m-%d %H:%M")


def base():
    """60 negativos limpios callados por todos (sustrato del contador), 6 noches donde sólo K publica en un negativo
    (P2 GANA), 2 alertas bajo 1 MW que los dos publican igual (pares de M y del placebo), y la pasada común con S159."""
    fs = [fila("Lascar", dia(i), "neg_limpio") for i in range(60)]
    fs += [fila("Llaima", dia(100 + i), "neg_limpio", k=0.2) for i in range(6)]
    fs += [fila("Lascar", dia(200 + i), "bajo1", k=0.5, pm=0.5, mirova=0.5) for i in range(2)]
    fs.append(fila("Lascar", "2026-03-27 07:10", "protegida", k=2.0, pm=2.0, mirova=2.0))
    return fs


def s159_dir(td, filas, cambiar=None, cambiar_npix=False):
    d = Path(td) / "s159"
    d.mkdir(exist_ok=True)
    f = next((x for x in filas if x["dt"] == "2026-03-27 07:10"), None)
    filas_s159 = []
    if f is not None:
        p = copy.deepcopy(f["port"]["fisica"])
        if cambiar:
            p["vrp_mw"] += cambiar
        if cambiar_npix:
            p["npix"] += 1
        filas_s159 = [{"volcan": f["vol"], "hora_utc": f["dt"], "estado": "ok", "port": {"fisica": p}}]
    (d / "resultados_MODIS_00.json").write_text(json.dumps(filas_s159), encoding="utf-8")
    return d


def correr(E, filas, recorridos=(), esperadas=None, nuestros=(), alertas=None, ext=None, cambiar_s159=None,
           crudas=None, cambiar_npix_s159=False):
    filas = copy.deepcopy(filas)
    with tempfile.TemporaryDirectory() as td:
        d = s159_dir(td, filas, cambiar_s159, cambiar_npix_s159)
        esp = [(f["vol"], f["dt"]) for f in filas] if esperadas is None else esperadas
        return E.evaluar(filas, GRILLAS, list(recorridos), dict(OK_EXT if ext is None else ext), esp,
                         filas if crudas is None else crudas, list(nuestros), alertas or {}, d)


# ------------------------------------------------------------------ pruebas
def t01_base_candidato(E):
    r = correr(E, base())
    exige(r["veredicto"] == "CANDIDATO", "base: veredicto %s, esperado CANDIDATO" % r["veredicto"])
    exige(g(r, "brazos", "PM", "p2", "estado") == "GANA" and g(r, "brazos", "PM", "p2", "neto") == -6
          and g(r, "brazos", "PM", "p2", "B") == 6, "base: P2 %s" % g(r, "brazos", "PM", "p2", "estado"))
    exige(all(g(r, "controles", k, "estado") == "OK" for k in ("k_produccion", "port_s159", "placebo", "contador",
                                                                 "cobertura")), "base: algun control no OK")


def t02_p1_veto(E):
    fs = base() + [fila("Lascar", dia(300), "protegida", k=3.0, pm=None, geo5=None, sens=3.0, mirova=3.0)]
    r = correr(E, fs)
    exige(r["veredicto"] == "NO CANDIDATO", "P1: veredicto %s" % r["veredicto"])
    per = g(r, "brazos", "PM", "p1", "perdidas", defecto=[])
    exige(len(per) == 1 and per[0].get("tambien_pierden") == ["PM-geo5"], "P1: atribucion %s" % per)


def t03_p2_pierde(E):
    fs = [x for x in base() if x["vol"] != "Llaima"]
    fs += [fila("Copahue", dia(150 + i), "neg_limpio", pm=0.2) for i in range(6)]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "p2", "estado") == "PIERDE", "P2 PIERDE: %s" % g(r, "brazos", "PM", "p2", "estado"))
    exige(r["veredicto"] == "NO CANDIDATO", "P2 PIERDE: veredicto %s" % r["veredicto"])


def t04_p2_sin_sustrato(E):
    fs = [x for x in base() if not (x["vol"] == "Llaima" and x["dt"] > dia(102))]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "p2", "estado") == "SIN SUSTRATO" and g(r, "brazos", "PM", "p2", "B") == 3,
          "SIN SUSTRATO: %s B %s" % (g(r, "brazos", "PM", "p2", "estado"), g(r, "brazos", "PM", "p2", "B")))
    exige(r["veredicto"] == "INDECIDIBLE", "SIN SUSTRATO: veredicto %s" % r["veredicto"])


def t05_p2_bloquea(E):
    fs = [x for x in base() if not (x["vol"] == "Llaima" and x["dt"] > dia(101))]
    fs += [fila("Copahue", dia(150 + i), "neg_limpio", pm=0.2) for i in range(4)]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "p2", "estado") == "BLOQUEA", "BLOQUEA: %s neto %s" % (
        g(r, "brazos", "PM", "p2", "estado"), g(r, "brazos", "PM", "p2", "neto")))
    exige(r["veredicto"] == "DECIDE NICOLÁS", "BLOQUEA: veredicto %s" % r["veredicto"])


def t06_p2_empate(E):
    fs = [x for x in base() if not (x["vol"] == "Llaima" and x["dt"] > dia(102))]
    fs += [fila("Copahue", dia(150 + i), "neg_limpio", pm=0.2) for i in range(3)]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "p2", "estado") == "EMPATE" and g(r, "brazos", "PM", "p2", "neto") == 0
          and g(r, "brazos", "PM", "p2", "B") == 6,
          "EMPATE: %s" % g(r, "brazos", "PM", "p2", "estado"))
    exige(r["veredicto"] == "CANDIDATO", "EMPATE: veredicto %s" % r["veredicto"])


def t07_p1b(E):
    fs = base() + [fila("Lascar", dia(310), "protegida", k=1.3, pm=0.7, mirova=1.5)]
    r = correr(E, fs)
    exige(len(g(r, "brazos", "PM", "p1b", "decide", defecto=[])) == 1, "P1b: no la lista")
    exige(r["veredicto"] == "DECIDE NICOLÁS", "P1b: veredicto %s" % r["veredicto"])
    fs2 = base() + [fila("Lascar", dia(311), "protegida", k=0.7, pm=1.3, mirova=1.5)]
    r2 = correr(E, fs2)
    exige(r2["veredicto"] == "CANDIDATO" and len(g(r2, "brazos", "PM", "p1b", "contraria_lista", defecto=[])) == 1,
          "P1b contraria: tiene que listarse y no decidir (%s)" % r2["veredicto"])


def t08_m_empeora(E):
    fs = base() + [fila("Isluga", dia(400 + i), "bajo1", k=0.5, pm=0.9, mirova=0.5) for i in range(20)]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "m", "regla") == "EMPEORA", "M: %s" % g(r, "brazos", "PM", "m", "regla"))
    exige(r["veredicto"] == "DECIDE NICOLÁS", "M EMPEORA: veredicto %s" % r["veredicto"])
    fs2 = base() + [fila("Isluga", dia(400 + i), "bajo1", k=0.25, pm=0.5, mirova=0.5) for i in range(20)]
    r2 = correr(E, fs2)
    exige(g(r2, "brazos", "PM", "m", "regla") == "MEJORA" and r2["veredicto"] == "CANDIDATO",
          "M MEJORA no decide: %s %s" % (g(r2, "brazos", "PM", "m", "regla"), r2["veredicto"]))


def t09_control_k(E):
    fs = base()
    fs[0] = dict(fs[0], decide=True, k_difiere_de_guardado=True)
    r = correr(E, fs)
    exige(g(r, "controles", "k_produccion", "estado") == "INDECIDIBLE" and r["veredicto"] == "INDECIDIBLE",
          "control 1: %s %s" % (g(r, "controles", "k_produccion", "estado"), r["veredicto"]))
    fs2 = base()
    fs2[0] = dict(fs2[0], pub={"K": 1, "K33": 0})
    r2 = correr(E, fs2)
    exige(g(r2, "controles", "k_produccion", "estado") == "INDECIDIBLE", "control 1: predicado del runner distinto")


def t10_control_s159(E):
    r = correr(E, base(), cambiar_s159=0.01)
    exige(g(r, "controles", "port_s159", "estado") == "INDECIDIBLE" and r["veredicto"] == "INDECIDIBLE",
          "control 2: %s" % g(r, "controles", "port_s159", "estado"))


def t11_cobertura(E):
    fs = base()
    r = correr(E, fs, esperadas=[(f["vol"], f["dt"]) for f in fs] + [("Lascar", "2026-09-01 01:05")])
    exige(g(r, "controles", "cobertura", "estado") == "INDECIDIBLE" and r["veredicto"] == "INDECIDIBLE",
          "control 5 (falta): %s" % g(r, "controles", "cobertura", "estado"))
    r2 = correr(E, fs, crudas=fs + [fs[0]])
    exige(g(r2, "controles", "cobertura", "estado") == "INDECIDIBLE", "control 5 (repetida) no marcado")


def t12_fuera_del_denominador(E):
    fs = base() + [fila("Lascar", dia(320), "protegida", k=3.0, pm=None, mirova=3.0,
                        port_estado="volcan_fuera_del_granulo", port=None)]
    r = correr(E, fs)
    # adenda 4 (VCM-01): una protegida que K publica fuera del denominador no puede pasar en silencio a CANDIDATO
    exige(r["veredicto"] == "DECIDE NICOLÁS", "fuera del denominador: veredicto %s" % r["veredicto"])
    pf = g(r, "controles", "cobertura", "protegidas_fuera_del_denominador", defecto=[])
    exige(len(pf) == 1 and pf[0].get("k_publica") == 1
          and g(r, "controles", "cobertura", "fuera_del_denominador", "volcan_fuera_del_granulo") == 1,
          "fuera del denominador: no la cuenta (%s)" % pf)
    fs2 = base() + [fila("Lascar", dia(321), "neg_limpio", k=0.4, pm=None,
                         port={"fisica": dict(port(None), motivo_vacio="escena_invalida")})]
    r2 = correr(E, fs2)
    exige(g(r2, "brazos", "PM", "p2", "neto") == -6, "escena invalida: entro a P2")


def t13_chillan(E):
    al = [fila("NevadosDeChillan", dia(500 + i), "protegida", k=0.6, pm=1.0, mirova=1.0, z=20.0) for i in range(7)]
    r = correr(E, base() + al)
    exige(g(r, "chillan", "estado") == "RESUELTO POR EL PAQUETE", "Chillan 7 de 7: %s" % g(r, "chillan", "estado"))
    r2 = correr(E, base() + al[:4])
    exige(g(r2, "chillan", "estado") == "SIN SUSTRATO", "Chillan 4 pares: %s" % g(r2, "chillan", "estado"))
    al3 = ([fila("NevadosDeChillan", dia(600 + i), "protegida", k=0.6, pm=1.0, mirova=1.0, z=20.0) for i in range(4)]
           + [fila("NevadosDeChillan", dia(610 + i), "protegida", k=0.5, pm=0.3, mirova=1.0, z=45.0) for i in range(3)])
    r3 = correr(E, base() + al3)
    exige(g(r3, "chillan", "estado") == "ES DEL SENSOR", "Chillan sensor: %s" % g(r3, "chillan", "estado"))
    al4 = al[:6] + [fila("NevadosDeChillan", dia(520), "protegida", k=None, pm=1.0, mirova=1.0)]
    r4 = correr(E, base() + al4)
    exige(len(g(r4, "chillan", "recuperadas", defecto=[])) == 1, "Chillan: recuperada no listada")


def t14_soporte_adenda1(E):
    fs = [x for x in base() if x["vol"] != "Llaima"]
    fs += [fila("Llaima", dia(100 + i), "neg_limpio", k=0.2) for i in range(5)]
    fs += [fila("Copahue", "2026-05-01 03:05", "neg_limpio", pm=0.2), fila("Copahue", "2026-05-03 03:05",
                                                                           "neg_limpio", pm=0.2)]
    t = datetime(2026, 5, 1, 5, 0, tzinfo=timezone.utc)
    nuestros = [{"vol": "Copahue", "b": "VIIRS375", "sensor": "VIIRS_NOAA20", "dt": t, "noche": "2026-05-01",
                 "dc": "summit", "pub": 1, "disp": 0.3}]
    alertas = {"Copahue": [(t, "VIIRS375")]}
    r = correr(E, fs, nuestros=nuestros, alertas=alertas)
    s = g(r, "brazos", "PM", "soporte_adenda1", defecto={})
    exige(s.get("n") == 2 and len(s.get("candidatas", [])) == 1 and s["candidatas"][0]["dt"] == "2026-05-01 03:05"
          and s["candidatas"][0]["mirova_alerto_6h"], "adenda 1: %s" % s)


def t15_sin_info_no_entra(E):
    fs = base() + [fila("Lascar", dia(330 + i), "sin_info", pm=0.3) for i in range(6)]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "p2", "neto") == -6 and r["veredicto"] == "CANDIDATO",
          "sin_info entro a P2 (neto %s)" % g(r, "brazos", "PM", "p2", "neto"))


def t16_contador_y_placebo(E):
    r = correr(E, base())
    c = g(r, "controles", "contador", defecto={})
    exige(c.get("estado") == "OK" and c.get("inyectados") == 50 and c.get("s_pm_con_inyeccion", 0) - c.get(
        "s_pm_antes", 0) == 50, "contador: %s" % c)
    p = g(r, "controles", "placebo", defecto={})
    exige(p.get("estado") == "OK" and p.get("dprima_max_abs") == 0 and p.get("n") == 3, "placebo: %s" % p)
    r2 = correr(E, [x for x in base() if x["lab"] not in ("bajo1", "protegida")])
    exige(g(r2, "controles", "placebo", "estado") == "INDECIDIBLE", "placebo sin pares tiene que ser INDECIDIBLE")


def t17_precedencia(E):
    fs = base() + [fila("Lascar", dia(340), "protegida", k=3.0, pm=None, mirova=3.0)]
    r = correr(E, fs, ext=dict(OK_EXT, referencia={"estado": "INDECIDIBLE"}))
    exige(r["veredicto"] == "INDECIDIBLE", "un control rojo manda sobre P1 (%s)" % r["veredicto"])
    fs2 = [x for x in base() if x["vol"] != "Llaima"]
    fs2 += [fila("Copahue", dia(150 + i), "neg_limpio", pm=0.2) for i in range(6)]
    fs2 += [fila("Lascar", dia(341), "protegida", k=3.0, pm=None, mirova=3.0)]
    r2 = correr(E, fs2)
    exige(r2["veredicto"] == "NO CANDIDATO" and g(r2, "brazos", "PM", "p1", "estado") == "VETADO",
          "P1 y P2 PIERDE: %s" % r2["veredicto"])


def t18_informativos_no_deciden(E):
    fs = base() + [fila("Lascar", dia(350), "protegida", k=3.0, pm=3.0, geo5=None, sens=None, mirova=3.0)]
    r = correr(E, fs)
    exige(r["veredicto"] == "CANDIDATO" and g(r, "brazos", "PM-geo5", "p1", "estado") == "VETADO",
          "PM-geo5 no decide pero tiene que informar su P1 (%s, %s)" % (r["veredicto"],
                                                                       g(r, "brazos", "PM-geo5", "p1", "estado")))


def t19_borde_granulo(E):
    fs = base() + [fila("Lascar", dia(360), "neg_limpio", pm=0.2,
                        crater_mxd03={"linea": 0, "frame": 600, "costura": True, "forma": [2030, 1354], "borde": True})]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "borde_granulo", defecto={}) == {"neg_limpio|K0|PM1": 1},
          "borde del granulo: %s" % g(r, "brazos", "PM", "borde_granulo"))


# ------------------------------------------------------------------ adenda 4 (verificador del candado, VCM-01 a VCM-06)
def t20_falla_del_port_es_roja(E):
    fs = base() + [fila("Lascar", dia(370), "neg_limpio", port_estado="error: ValueError: x", port=None)]
    r = correr(E, fs)
    exige(g(r, "controles", "cobertura", "estado") == "INDECIDIBLE"
          and g(r, "controles", "cobertura", "n_fallas_del_instrumento") == 1 and r["veredicto"] == "INDECIDIBLE",
          "falla del port: %s %s" % (g(r, "controles", "cobertura", "estado"), r["veredicto"]))


def t21_grilla_incompleta_cuenta(E):
    fs = base() + [fila("Lascar", dia(371), "protegida", k=3.0, pm=None, geo5=3.0, sens=3.0, mirova=3.0,
                        port_grilla="grilla_incompleta")]
    r = correr(E, fs)
    exige(r["veredicto"] == "NO CANDIDATO" and g(r, "brazos", "PM", "p1", "estado") == "VETADO",
          "grilla incompleta con detector corrido tiene que contar: %s" % r["veredicto"])


def t22_protegida_fuera_que_k_calla(E):
    fs = base() + [fila("Lascar", dia(372), "protegida", k=None, pm=None, mirova=3.0, port_estado="volcan_fuera_del_granulo",
                        port=None)]
    r = correr(E, fs)
    pf = g(r, "controles", "cobertura", "protegidas_fuera_del_denominador", defecto=[])
    exige(r["veredicto"] == "CANDIDATO" and len(pf) == 1 and pf[0].get("k_publica") == 0,
          "protegida fuera que K tampoco publica: %s %s" % (r["veredicto"], pf))


def t23_bloque_noche(E):          # verificador, x01 (§4 P2: dos pasadas de una noche-volcán son un bloque)
    fs = base() + [fila("Llaima", dia(100).replace("01:05", "03:05"), "neg_limpio", k=0.2)]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "p2", "B") == 6 and g(r, "brazos", "PM", "p2", "neto") == -7,
          "bloque: B %s neto %s (esperado 6 y -7)" % (g(r, "brazos", "PM", "p2", "B"), g(r, "brazos", "PM", "p2", "neto")))


def t24_chillan_6_de_7(E):        # verificador, x02 (§5.3: p = 8/128 no alcanza)
    al = [fila("NevadosDeChillan", dia(500 + i), "protegida", k=0.6, pm=1.0, mirova=1.0, z=20.0) for i in range(6)]
    al.append(fila("NevadosDeChillan", dia(506), "protegida", k=1.0, pm=0.6, mirova=1.0, z=20.0))
    c = g(correr(E, base() + al), "chillan", defecto={})
    exige(c.get("n_pares") == 7 and c.get("b_mas_cerca") == 6 and c.get("estado") == "SIN RESOLVER",
          "Chillan 6 de 7: %s" % {k: c.get(k) for k in ("n_pares", "b_mas_cerca", "estado")})


def t25_p1_k_calla(E):            # verificador, x03 (§4 P1: sólo protegidas que K publica)
    fs = base() + [fila("Lascar", dia(300), "protegida", k=None, pm=None, mirova=3.0)]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "p1", "estado") == "SIN PERDIDA" and r["veredicto"] == "CANDIDATO"
          and g(r, "brazos", "PM", "p1", "n_protegidas_k") == 1,
          "P1 con K callado: %s %s" % (g(r, "brazos", "PM", "p1", "estado"), r["veredicto"]))


def t26_bajo1_sin_publicar(E):    # verificador, x04 (§4 P2: no publicar una alerta bajo 1 MW es error)
    fs = base() + [fila("Lascar", dia(220 + i), "bajo1", k=0.5, pm=None, mirova=0.5) for i in range(2)]
    r = correr(E, fs)
    exige(g(r, "brazos", "PM", "p2", "neto") == -4 and g(r, "brazos", "PM", "p2", "s_b") == 2
          and g(r, "brazos", "PM", "p2", "B") == 8, "bajo1 sin publicar: %s" % {
              k: g(r, "brazos", "PM", "p2", k) for k in ("neto", "s_b", "B")})


def t27_chillan_regla4_bajo(E):   # verificador, x06 (§5.4 exige la banda bajo 30 grados)
    al = ([fila("NevadosDeChillan", dia(600 + i), "protegida", k=0.6, pm=1.6, mirova=1.0, z=20.0) for i in range(4)]
          + [fila("NevadosDeChillan", dia(610 + i), "protegida", k=0.5, pm=0.3, mirova=1.0, z=45.0) for i in range(3)])
    c = g(correr(E, base() + al), "chillan", defecto={})
    exige(c.get("estado") == "SIN RESOLVER" and c.get("n_pares") == 7, "regla 4 sin banda baja: %s" % c.get("estado"))


def t28_chillan_empate(E):        # verificador, x07 (§5.5: el empate exacto sale y se lista)
    al = [fila("NevadosDeChillan", dia(500 + i), "protegida", k=0.6, pm=1.0, mirova=1.0, z=20.0) for i in range(5)]
    al.append(fila("NevadosDeChillan", dia(506), "protegida", k=0.5, pm=0.5, mirova=1.0, z=20.0))
    c = g(correr(E, base() + al), "chillan", defecto={})
    exige(c.get("n_pares") == 5 and len(c.get("empates", [])) == 1 and c.get("estado") == "RESUELTO POR EL PAQUETE",
          "empate: %s" % {k: c.get(k) for k in ("n_pares", "estado")})


def t29_chillan_grupo_vacio(E):   # verificador, x08 (§5.5, VCD-16)
    al = ([fila("NevadosDeChillan", dia(600 + i), "protegida", k=0.6, pm=1.0, mirova=1.0, z=20.0) for i in range(3)]
          + [fila("NevadosDeChillan", dia(610 + i), "protegida", k=1.0, pm=0.6, mirova=1.0, z=20.0) for i in range(2)])
    c = g(correr(E, base() + al), "chillan", defecto={})
    exige(c.get("estado") == "SIN RESOLVER" and c.get("n_pares") == 5 and c.get("mediana_z_gt30") is None,
          "grupo > 30 vacio: %s" % c.get("estado"))


def t30_soporte_mismo_modis(E):   # verificador, x09 (adenda 1 y A109)
    fs = base() + [fila("Copahue", "2026-05-01 03:05", "neg_limpio", pm=0.2)]
    t = datetime(2026, 5, 1, 3, 5, tzinfo=timezone.utc)
    nuestros = [{"vol": "Copahue", "b": "MODIS", "sensor": "MODIS_AQUA", "dt": t, "noche": "2026-05-01",
                 "dc": "summit", "pub": 1, "disp": 0.3}]
    s = g(correr(E, fs, nuestros=nuestros), "brazos", "PM", "soporte_adenda1", defecto={})
    exige(s.get("n") == 1 and len(s.get("candidatas", [])) == 0, "el mismo MODIS conto como soporte: %s" % s)


def t31_control_s159_npix(E):     # VCM-04
    r = correr(E, base(), cambiar_npix_s159=True)
    exige(g(r, "controles", "port_s159", "estado") == "INDECIDIBLE", "control 2 no mira npix")


def t32_k33_por_predicado(E):     # VCM-06
    fs = base() + [fila("Lascar", dia(380), "protegida", k=3.0, pm=3.0, mirova=3.0, k33_slim=None)]
    r = correr(E, fs)
    exige(g(r, "brazos", "K33", "p1", "estado") == "VETADO" and r["veredicto"] == "CANDIDATO",
          "K33 por el predicado: %s" % g(r, "brazos", "K33", "p1", "estado"))


def t33_protegida_fuera_por_escena_invalida(E):   # adenda 4, punto 1 (b), condición 3 de la coordinadora S163
    fs = base() + [fila("Lascar", dia(390), "protegida", k=3.0, pm=None, mirova=3.0,
                        port={"fisica": dict(port(None), motivo_vacio="escena_invalida")})]
    r = correr(E, fs)
    pf = g(r, "controles", "cobertura", "protegidas_fuera_del_denominador", defecto=[])
    exige(r["veredicto"] == "DECIDE NICOLÁS" and len(pf) == 1 and pf[0].get("motivo") == "escena_invalida"
          and pf[0].get("k_publica") == 1 and g(r, "brazos", "PM", "p1", "estado") == "SIN PERDIDA",
          "protegida fuera por escena invalida: %s %s" % (r["veredicto"], pf))


PRUEBAS = [v for k, v in sorted(globals().items()) if k.startswith("t") and k[1:3].isdigit()]


def cargar(ruta):
    spec = importlib.util.spec_from_file_location("evaluador_bajo_prueba", ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--modulo", default=str(AQUI / "evaluar_paquete.py"))
    ap.add_argument("--json", default=None, help="escribe {prueba: pasa|falla|cae} aqui")
    a = ap.parse_args(argv)
    E = cargar(a.modulo)
    res = {}
    for t in PRUEBAS:
        try:
            t(E)
            res[t.__name__] = "pasa"
        except Falla as e:
            res[t.__name__] = "falla"
            print("  FALLA %s: %s" % (t.__name__, e))
        except Exception as e:  # noqa: BLE001
            res[t.__name__] = "cae"
            print("  CAE %s: %s: %s" % (t.__name__, type(e).__name__, str(e)[:200]))
            print("    " + traceback.format_exc().splitlines()[-3][:200])
    n = {s: sum(1 for v in res.values() if v == s) for s in ("pasa", "falla", "cae")}
    print("%s: pasan %d, fallan %d, caen %d (de %d)" % (Path(a.modulo).name, n["pasa"], n["falla"], n["cae"], len(res)))
    if a.json:
        Path(a.json).write_text(json.dumps(res), encoding="utf-8")
    return 0 if n["pasa"] == len(res) else 1


if __name__ == "__main__":
    sys.exit(main())
