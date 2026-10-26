# -*- coding: utf-8 -*-
"""S162 MOD-D, evaluador del censo del paquete MODIS (PM) contra K. Implementa TAL CUAL las reglas selladas del
pre-registro experiments/_s162_modis_paquete/PREREGISTRO.md (v2, sello D-48): pruebas del §4, Chillán del §5, veredicto
del §6, controles del §8, y los estratos informativos de las adendas 1 y 3. Si una regla cambia, cambia aquí y en el
pre-registro en el mismo commit, con adenda fechada.

POR QUÉ CADA PIEZA (resumen; el detalle está en el pre-registro):
- «Publica» y «magnitud mostrada» salen del predicado de frontend/index.html EJECUTADO CON NODE (banco_paridad.
  correr_node, A97), sobre el record de K que guardó el arnés y sobre el record sintético del port (`record_port` de
  04_analizar.py de S159, sin cambios). El placebo es el record de K con toda magnitud por 1,2, también por node.
- P1 veto, P1b, P2 por la prueba de signos por bloque noche-volcán (D-45: `prueba_signos_p2` y `regla_signos_p2`) y M
  con `regla_m` (sólo EMPEORA decide) y d′ de D-28 (`comparar_con_ganancia`, informa): todo importado del blob sellado
  de evaluar_d25.py (commit ded217af4, blob 1dbabf65, copiado sin cambios como evaluar_d25_ded217af4.py y comprobado
  por su hash).
- Sólo «volcán fuera del gránulo» y «escena inválida» sacan una pasada del denominador de TODOS los brazos (§8 control
  5); una falla del arnés o del port deja el control 5 en rojo; una protegida que K publica y sale por uno de esos dos
  motivos lleva el veredicto a DECIDE NICOLÁS (adenda 4, regla aprobada por la coordinadora S163).
- PM-geo5 y PM-sens reciben el mismo cálculo como información (§6). K33, `pixel` y `fisica_b21` se informan.

Las dos preguntas del instrumento:
1. Si el PM no cambiara nada respecto de K, ¿se vería? Sí: P2 daría EMPATE con B = 0 o SIN SUSTRATO, y M SIN PARES o
   NEUTRO; las pruebas del archivo probar_evaluar_paquete.py arman cada salida a propósito.
2. Si el arnés o el evaluador estuvieran rotos, ¿se vería distinto de CANDIDATO? Sí: K distinto de data/ sin
   reproducir en su codigo_sha, el PM distinto del de S159, un placebo con d′ distinto de 0, un contador que no ve 50
   publicaciones inyectadas, una pasada faltante o repetida, o una referencia con otro sha256 dan INDECIDIBLE.
Uso: python evaluar_paquete.py --art DIR [--ref DIR_CSV] [--modb DIR_ARTEFACTOS_MODB] [--salida resultado.json]
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import importlib.util
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
# MODD_RAIZ sólo la usa mutar_evaluar_paquete.py, que corre copias mutadas fuera del repositorio
RAIZ = Path(os.environ.get("MODD_RAIZ") or AQUI.parents[1])
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "experiments/_s159/portes"))
sys.path.insert(1, str(RAIZ / "experiments/_s162_modis_paquete"))      # manifiesto_candado (copias mutadas fuera)


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


D25_BLOB = "1dbabf657407b6db0f91d9e2fc98eb16a8051873"
D25_RUTA = RAIZ / "experiments/_s162_modis_paquete/evaluar_d25_ded217af4.py"
D = _cargar("evaluar_d25_ded217af4", D25_RUTA)
AN = _cargar("analizar_s159", RAIZ / "experiments/_s159/portes/04_analizar.py")
EM = _cargar("evaluar_mxd03_modd", RAIZ / "experiments/_s162_mxd03/evaluar_mxd03.py")
import banco_paridad as bp  # noqa: E402

POBLACION = RAIZ / "experiments/_s162_mxd03/poblacion.json"
GRILLAS = AQUI / "grillas.json"
S159 = AQUI / "referencia_s159"
BRAZOS_PORT = {"PM": "fisica", "PM-geo5": "fisica_geo5km", "PM-sens": "sensible", "PM-pixel": "pixel",
               "PM-b21": "fisica_b21"}
DECIDE = "PM"
INFORMA = ("PM-geo5", "PM-sens")
PLACEBO = 1.2
TOL_PORT_S159 = 1e-6
N_INYECTAR = 50
SEMILLA_INYECTAR = 162
VRP_INYECTADO, DIST_INYECTADA = 0.3, 0.5
VENTANA_SOPORTE_H = 6.0
CORTE_CENIT_SOPORTE = 40.0
CORTE_CENIT_CHILLAN = 30.0
CHILLAN = "NevadosDeChillan"
BLOBS_SELLADOS = {"experiments/_s159/portes/probe_portes.py": "8ec50e7bbb76c16e765a92e2773270c26c6ed9ac",
                  "experiments/_s159/portes/mirova_port.py": "96769a89e6ee2233d86d973917c696cdb2405f29",
                  "experiments/_s158_audit_r2/oraculo/mirova_v750_r2.py": "07da701094f5aca7f14d7d9de39741589721c478"}
CAMPOS_MAG = ("vrp_mw", "vrp_mir_mw", "vrp_vent_mw", "f5_core_vrp_mw")


def blob(ruta):
    b = Path(ruta).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


# ------------------------------------------------------------------ records sintéticos y predicado
def record_port(p, inner, sensor, grilla):
    """El record sintético del port de S159 (04_analizar.record_port y dist_centroide, sin cambios)."""
    if p and p.get("npix"):
        p = dict(p)
        p["_dcen"] = AN.dist_centroide(p, grilla)
    r = AN.record_port(p, inner, sensor)
    return {k: x for k, x in r.items() if not k.startswith("_")}


def escalar(slim, f):
    """El placebo: toda magnitud del record por f (también la del cúmulo y la de cada píxel)."""
    if slim is None:
        return None
    s = json.loads(json.dumps(slim))
    for k in CAMPOS_MAG:
        if isinstance(s.get(k), (int, float)):
            s[k] = s[k] * f
    if isinstance(s.get("primary_cluster"), dict) and isinstance(s["primary_cluster"].get("vrp_mw"), (int, float)):
        s["primary_cluster"]["vrp_mw"] *= f
    for p in s.get("anomaly_pixels") or []:
        if isinstance(p.get("vrp_mw"), (int, float)):
            p["vrp_mw"] *= f
    return s


def predicado(casos):
    """[(slim, inner)] -> [(publica 0/1, magnitud mostrada)], con node sobre frontend/index.html."""
    vivos = [(i, c) for i, c in enumerate(casos) if c[0] is not None]
    out = [(0, 0.0)] * len(casos)
    if vivos:
        res = bp.correr_node([[AN.slim(c[0]), c[1]] for _, c in vivos])
        for (i, _), p in zip(vivos, res):
            out[i] = (int(p[4]), float(p[3] or 0.0))
    return out


MOTIVOS_SELLADOS = ("volcan_fuera_del_granulo", "escena_invalida")   # §8 control 5, los dos únicos que salen


def evaluable(f):
    """§8 control 5 (adenda 4, VCM-01): sólo «volcán fuera del gránulo» y «escena inválida» salen del denominador de
    todos los brazos. Una falla del arnés o del port (error, gránulo no encontrado, descarga vacía) NO es una propiedad
    de la escena: sale del cálculo con su motivo y deja el control de cobertura en rojo. «grilla_incompleta» del probe
    sola no saca la pasada: si el detector corrió, su resultado cuenta (el .m declara la escena inválida por su cuenta)."""
    if f.get("estado") != "ok":
        return False, "falla_arnes_" + str(f.get("estado"))
    if f.get("port_estado") == "volcan_fuera_del_granulo":
        return False, "volcan_fuera_del_granulo"
    if f.get("port_estado") != "ok" or not f.get("port"):
        return False, "falla_port_" + str(f.get("port_estado"))
    pf = f["port"].get("fisica") or {}
    if pf.get("motivo_vacio") == "escena_invalida":
        return False, "escena_invalida"
    return True, None


def armar_tabla(filas, grillas):
    """Por pasada evaluable: (pub, magnitud) de K, placebo y de cada brazo del port, y K33 del runner."""
    casos, idx = [], []
    for i, f in enumerate(filas):
        if not f["_evaluable"]:
            continue
        k = f.get("k_slim")
        casos.append((k, f["inner"]))
        idx.append((i, "K"))
        casos.append((escalar(k, PLACEBO), f["inner"]))
        idx.append((i, "placebo"))
        if "k33_slim" in f:      # adenda 4 (VCM-06): K33 por el mismo predicado y la misma magnitud mostrada
            casos.append((f["k33_slim"], f["inner"]))
            idx.append((i, "K33"))
        for b, m in BRAZOS_PORT.items():
            casos.append((record_port(f["port"].get(m), f["inner"], f["sensor"], grillas[f["vol"]]), f["inner"]))
            idx.append((i, b))
    for (i, b), v in zip(idx, predicado(casos)):
        filas[i].setdefault("_t", {})[b] = {"pub": v[0], "mag": v[1]}
    for f in filas:
        if f["_evaluable"] and "K33" not in f["_t"]:
            k33 = (f.get("brazos") or {}).get("K33") or {}
            f["_t"]["K33"] = {"pub": int((f.get("pub") or {}).get("K33") or 0), "mag": float(k33.get("pc_vrp") or 0.0)}
    return filas


def _pub(f, b):
    return f["_t"][b]["pub"]


def _mag(f, b):
    return f["_t"][b]["mag"]


def _bloque(f):
    return "%s|%s" % (f["vol"], f.get("noche") or f["dt"][:10])


def _ev(filas):
    return [f for f in filas if f["_evaluable"]]


# ------------------------------------------------------------------ pruebas del §4
def p1(filas, b):
    perd = [{"vol": f["vol"], "dt": f["dt"], "z": f["z"], "vrp_k": _mag(f, "K"), "vrp_mirova": f.get("vrp_mirova"),
             "tambien_pierden": [x for x in ("PM-geo5", "PM-sens") if x != b and _pub(f, x) == 0]}
            for f in _ev(filas) if f["lab"] == "protegida" and _pub(f, "K") == 1 and _pub(f, b) == 0]
    return {"estado": "VETADO" if perd else "SIN PERDIDA", "perdidas": perd,
            "n_protegidas_k": sum(1 for f in _ev(filas) if f["lab"] == "protegida" and _pub(f, "K") == 1)}


def p1b(filas, b):
    baja, sube = [], []
    for f in _ev(filas):
        if f["lab"] != "protegida" or not (_pub(f, "K") == 1 and _pub(f, b) == 1):
            continue
        fila = {"vol": f["vol"], "dt": f["dt"], "mag_k": _mag(f, "K"), "mag_b": _mag(f, b),
                "vrp_mirova": f.get("vrp_mirova")}
        if _mag(f, "K") >= 1.0 > _mag(f, b):
            baja.append(fila)
        elif _mag(f, "K") < 1.0 <= _mag(f, b):
            sube.append(fila)
    return {"decide": baja, "contraria_lista": sube}


def _error(f, b):
    if f["lab"] == "bajo1":
        return _pub(f, b) == 0
    if f["lab"] == "neg_limpio":
        return _pub(f, b) == 1
    return False


def contribuciones_p2(filas, b):
    """+1 si el error es sólo del brazo, -1 si es sólo de K (signo de D-45: positivo es malo para el brazo)."""
    out = []
    for f in _ev(filas):
        if f["lab"] not in ("bajo1", "neg_limpio"):
            continue
        ek, eb = _error(f, "K"), _error(f, b)
        if ek != eb:
            out.append({"vol": f["vol"], "dt": f["dt"], "lab": f["lab"], "c": 1 if eb else -1, "bloque": _bloque(f),
                        "invisible": EM._invisible(f), "z": f["z"]})
    return out


def p2(filas, b):
    c = contribuciones_p2(filas, b)
    neto = sum(x["c"] for x in c)
    por_bloque = collections.Counter()
    for x in c:
        por_bloque[x["bloque"]] += x["c"]
    sumas = [por_bloque[k] for k in sorted(por_bloque)]
    B = len(sumas)
    pr = D.prueba_signos_p2(sumas, neto)
    estado = D.regla_signos_p2(neto, B, pr)
    s_k = sum(1 for f in _ev(filas) if f["lab"] in ("bajo1", "neg_limpio") and _error(f, "K"))
    s_b = sum(1 for f in _ev(filas) if f["lab"] in ("bajo1", "neg_limpio") and _error(f, b))
    return {"estado": estado, "neto": neto, "B": B, "s_k": s_k, "s_b": s_b, "sumas_bloque": sorted(sumas),
            "p_gana": pr["gana"], "p_pierde": pr["pierde"], "metodo": pr["metodo"],
            "n_invisibles_discordantes": sum(1 for x in c if x["invisible"]), "discordantes": c}


def pares_m(filas, b):
    out = []
    for f in _ev(filas):
        if f["lab"] not in ("protegida", "bajo1") or not (_pub(f, "K") == 1 and _pub(f, b) == 1):
            continue
        k, d, m = _mag(f, "K"), _mag(f, b), f.get("vrp_mirova")
        if k > 0 and d > 0 and m and m > 0:
            out.append({"k": k, "d": d, "m": m, "clave": "%s|MODIS|%s" % (f["vol"], f["dt"]), "bloque": _bloque(f),
                        "z": f["z"], "vol": f["vol"]})
    return out


def m(filas, b):
    P = pares_m(filas, b)
    if not P:
        return {"n": 0, "regla": "SIN PARES"}
    d = [abs(math.log10(p["d"] / p["m"])) - abs(math.log10(p["k"] / p["m"])) for p in P]
    bloques = [p["bloque"] for p in P]
    W = D.pesos_bloque(bloques)
    regla, lo, hi = D.regla_m(d, W)
    out = {"n": len(P), "regla": regla, "ic95_d": [lo, hi], "mediana_d": statistics.median(d),
           "g_mediana": statistics.median(p["d"] / p["k"] for p in P)}
    try:
        out["dprima"] = D.comparar_con_ganancia(P, W, bloques)
    except Exception as e:  # noqa: BLE001  (informa: si no corre, se dice)
        out["dprima"] = {"error": f"{type(e).__name__}: {e}"[:200]}
    pv = collections.defaultdict(list)
    for p, x in zip(P, d):
        pv[p["vol"]].append(x)
    out["por_volcan"] = {v: {"n": len(x), "mediana_d": statistics.median(x)} for v, x in sorted(pv.items())}
    return out


def curva_cenit(filas, b):
    t = collections.defaultdict(list)
    for f in _ev(filas):
        if f["lab"] in ("protegida", "bajo1") and _pub(f, b) == 1 and f.get("vrp_mirova") and f["z"] is not None:
            t[int(f["z"] // 10) * 10].append(_mag(f, b) / f["vrp_mirova"])
    return {"%d-%d" % (k, k + 10): {"n": len(v), "mediana": statistics.median(v)} for k, v in sorted(t.items())}


def _signos_una_cola(k, n):
    return sum(math.comb(n, i) for i in range(k, n + 1)), 2 ** n


def chillan(filas, b="PM"):
    al = [f for f in _ev(filas) if f["vol"] == CHILLAN and f["lab"] in ("protegida", "bajo1")]
    recup = [{"dt": f["dt"], "z": f["z"], "razon": _mag(f, b) / f["vrp_mirova"] if f.get("vrp_mirova") else None}
             for f in al if _pub(f, "K") == 0 and _pub(f, b) == 1]
    pares, empates = [], []
    for f in al:
        if _pub(f, "K") == 1 and _pub(f, b) == 1 and f.get("vrp_mirova"):
            mm = f["vrp_mirova"]
            dk, db = abs(math.log10(_mag(f, "K") / mm)), abs(math.log10(_mag(f, b) / mm))
            par = {"dt": f["dt"], "z": f["z"], "razon_b": _mag(f, b) / mm, "razon_k": _mag(f, "K") / mm,
                   "b_mas_cerca": db < dk}
            (empates if db == dk else pares).append(par)
    n = len(pares)
    k = sum(1 for p in pares if p["b_mas_cerca"])
    num, den = _signos_una_cola(k, n) if n else (1, 1)
    med = statistics.median(p["razon_b"] for p in pares) if pares else None
    bajo = [p["razon_b"] for p in pares if p["z"] is not None and p["z"] <= CORTE_CENIT_CHILLAN]
    sobre = [p["razon_b"] for p in pares if p["z"] is not None and p["z"] > CORTE_CENIT_CHILLAN]
    med_bajo = statistics.median(bajo) if bajo else None
    med_sobre = statistics.median(sobre) if sobre else None
    if n < 5:
        estado = "SIN SUSTRATO"
    elif med is not None and 0.8 <= med <= 1.25 and 20 * num <= den:
        estado = "RESUELTO POR EL PAQUETE"
    elif med_bajo is not None and med_sobre is not None and med_sobre < 0.8 and 0.8 <= med_bajo <= 1.25:
        estado = "ES DEL SENSOR"
    else:
        estado = "SIN RESOLVER"
    return {"estado": estado, "recuperadas": recup, "pares": pares, "empates": empates, "n_pares": n,
            "b_mas_cerca": k, "p_una_cola": [num, den], "mediana_razon": med, "mediana_z_le30": med_bajo,
            "mediana_z_gt30": med_sobre}


def noches_a94(filas, b, nuestros):
    """Noches con protegida MODIS que K publica y el brazo no, y que ningún record VIIRS publicado cubre esa noche."""
    viirs = {(r["vol"], r["noche"]) for r in nuestros if r["b"] != "MODIS" and r.get("pub")}
    out = []
    for f in _ev(filas):
        if f["lab"] == "protegida" and _pub(f, "K") == 1 and _pub(f, b) == 0:
            out.append({"vol": f["vol"], "noche": f.get("noche"), "dt": f["dt"],
                        "cubierta_por_viirs": (f["vol"], f.get("noche")) in viirs})
    return {"n_noches_perdidas": len({(x["vol"], x["noche"]) for x in out if not x["cubierta_por_viirs"]}),
            "lista": out}


def _dt(s):
    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def soporte_independiente(filas, b, nuestros, alertas_mirova):
    """Adenda 1 (informa): cada publicación del brazo en un negativo limpio, con o sin soporte de otro sensor a 6 h o
    menos (VIIRS de cualquier satélite o el otro MODIS, cúmulo summit publicado por el tablero) y, aparte, si MIROVA
    alertó en cualquier canal en esa ventana."""
    w = timedelta(hours=VENTANA_SOPORTE_H)
    lista = []
    for f in _ev(filas):
        if f["lab"] != "neg_limpio" or _pub(f, b) != 1:
            continue
        t = _dt(f["dt"])
        sop = [{"sensor": r["sensor"], "dt": r["dt"].strftime("%Y-%m-%d %H:%M"), "disp": r.get("disp")}
               for r in nuestros if r["vol"] == f["vol"] and r.get("pub") and r.get("dc") == "summit"
               and abs(r["dt"] - t) <= w and (r["b"] != "MODIS" or r.get("sensor") != f["sensor"])]
        mir = [x for x in alertas_mirova.get(f["vol"], []) if abs(x[0] - t) <= w]
        lista.append({"vol": f["vol"], "dt": f["dt"], "z": f["z"], "mag": _mag(f, b), "soporte": sop,
                      "mirova_alerto_6h": [(x[0].strftime("%Y-%m-%d %H:%M"), x[1]) for x in mir],
                      "candidata_experimental": bool(sop)})
    tab = collections.Counter(("con" if x["soporte"] else "sin",
                               "z<=40" if (x["z"] is not None and x["z"] <= CORTE_CENIT_SOPORTE) else "z>40")
                              for x in lista)
    return {"n": len(lista), "por_soporte_y_cenit": {"%s|%s" % k: v for k, v in sorted(tab.items())},
            "candidatas": [x for x in lista if x["candidata_experimental"]], "lista": lista}


def costura(filas, b):
    t = collections.Counter()
    for f in _ev(filas):
        if f["lab"] in ("protegida", "bajo1"):
            c = bool((f.get("crater_mxd03") or {}).get("costura"))
            t[("costura" if c else "interior", "K%d" % _pub(f, "K"), "%s%d" % (b, _pub(f, b)))] += 1
    return {"|".join(k): v for k, v in sorted(t.items())}


def borde_granulo(filas, b):
    """Informa (VA61-01 del verificador de la A61): pasadas cuyo píxel MxD03 más cercano al cráter está en la primera o
    la última línea o frame del gránulo, donde el cráter probablemente quedó fuera de la imagen y el record se guarda
    igual como «observado». Cuántas son por clase y qué publica cada brazo ahí."""
    t = collections.Counter()
    for f in _ev(filas):
        if (f.get("crater_mxd03") or {}).get("borde"):
            t[(f["lab"], "K%d" % _pub(f, "K"), "%s%d" % (b, _pub(f, b)))] += 1
    return {"|".join(k): v for k, v in sorted(t.items())}


def s1_informe(filas):
    """Diagnóstico S-1 (informa): cuántas veces el umbral de cumbre lo fija la sigma de toda la grilla y no el piso, y
    en cuántas pasadas la cumbre de la primera pasada cambiaría con la sigma de la ROI1."""
    ok = [f for f in _ev(filas) if (f.get("s1") or {}).get("estado") == "ok"]
    ident_mal = [(f["vol"], f["dt"]) for f in ok if not f["s1"].get("identidad_ok")]
    usa = [f for f in ok if f["s1"].get("identidad_ok")]
    tab = collections.Counter()
    for f in usa:
        s = f["s1"]
        por_sigma = s["u_nti2_g"] > 0.003 or s["u_eti2_g"] > 0.003
        cambia = (s["n2_g"] > 0) != (s["n2_roi1"] > 0)
        clase = f["lab"] if f["lab"] in ("protegida", "bajo1", "neg_limpio") else "otra"
        tab[(clase, "PM%d" % _pub(f, "PM"), "sigma" if por_sigma else "piso", "cambia" if cambia else "igual")] += 1
    return {"n_ok": len(ok), "identidad_falla": ident_mal[:20], "n_identidad_falla": len(ident_mal),
            "otros_estados": dict(collections.Counter((f.get("s1") or {}).get("estado") for f in _ev(filas)
                                                      if (f.get("s1") or {}).get("estado") != "ok")),
            "tabla": {"|".join(k): v for k, v in sorted(tab.items())}}


# ------------------------------------------------------------------ controles del §8
def control_k_produccion(filas, recorridos):
    """§8 control 1: K del arnés = data/ (control_arnes de MOD-B, re-corrida en su codigo_sha), y el predicado del
    evaluador da la misma publicación de K que el del runner."""
    c = EM.control_arnes([f for f in filas if f.get("estado") == "ok"], recorridos)
    distinto = [(f["vol"], f["dt"]) for f in _ev(filas) if _pub(f, "K") != int((f.get("pub") or {}).get("K") or 0)]
    if distinto:
        c = dict(c, estado="INDECIDIBLE")
    c["predicado_distinto_del_runner"] = distinto[:20]
    return c


def control_port_s159(filas, dir_s159=S159):
    """§8 control 2: el PM de este censo es el del lote de S159 en las pasadas comunes (npix y VRP a 1e-6 MW)."""
    ref = {}
    for p in sorted(Path(dir_s159).glob("resultados_MODIS_*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")):
            if r.get("estado") == "ok":
                ref[(r["volcan"], r["hora_utc"])] = r["port"]["fisica"]
    comunes, malos = 0, []
    con_pix = 0
    for f in _ev(filas):
        r = ref.get((f["vol"], f["dt"]))
        if r is None:
            continue
        comunes += 1
        a = f["port"]["fisica"]
        con_pix += int(bool(r.get("npix")))
        igual = a.get("npix") == r.get("npix") and (
            (a.get("vrp_mw") is None and r.get("vrp_mw") is None)
            or (a.get("vrp_mw") is not None and r.get("vrp_mw") is not None
                and abs(a["vrp_mw"] - r["vrp_mw"]) <= TOL_PORT_S159))
        if not igual:
            malos.append({"vol": f["vol"], "dt": f["dt"], "npix": [a.get("npix"), r.get("npix")],
                          "vrp": [a.get("vrp_mw"), r.get("vrp_mw")]})
    estado = "OK" if comunes and con_pix and not malos else "INDECIDIBLE"
    return {"estado": estado, "comunes": comunes, "comunes_con_pixeles": con_pix, "distintos": malos[:20],
            "n_distintos": len(malos), "en_s159": len(ref)}


def control_placebo(filas):
    """§8 control 3: el placebo K x 1,2 da d′ = 0 en todo par (cableado de M)."""
    P = pares_m(filas, "placebo")
    if not P:
        return {"estado": "INDECIDIBLE", "motivo": "sin pares para el placebo"}
    bloques = [p["bloque"] for p in P]
    W = D.pesos_bloque(bloques)
    r = D.comparar_con_ganancia(P, W, bloques)
    gan = [p["d"] / p["k"] for p in P]
    ok = r["dprima_max_abs"] == 0 and all(abs(g - PLACEBO) < 1e-9 for g in gan)
    return {"estado": "OK" if ok else "INDECIDIBLE", "n": len(P), "dprima_max_abs": r["dprima_max_abs"],
            "ganancia_min_max": [min(gan), max(gan)]}


def control_contador(filas, grillas):
    """§8 control 4 (fuera de línea): (a) toda publicación del PM con vrp_mw = 0 deja de publicar; (b) 50 negativos
    que el PM no publica (semilla 162), con un cúmulo de cumbre de 0,3 MW a 0,5 km inyectado, pasan a publicar, y P2
    del PM cuenta exactamente 50 errores más."""
    ev = _ev(filas)
    pub_pm = [f for f in ev if _pub(f, "PM") == 1]
    casos = []
    for f in pub_pm:
        p = dict(f["port"]["fisica"])
        r = record_port(p, f["inner"], f["sensor"], grillas[f["vol"]])
        for k in CAMPOS_MAG:
            if k in r:
                r[k] = 0.0
        if r.get("primary_cluster"):
            r["primary_cluster"]["vrp_mw"] = 0.0
        casos.append((r, f["inner"]))
    a = predicado(casos)
    siguen = [(f["vol"], f["dt"]) for f, x in zip(pub_pm, a) if x[0] == 1]
    negs = sorted([f for f in ev if f["lab"] == "neg_limpio" and _pub(f, "PM") == 0], key=lambda f: (f["vol"], f["dt"]))
    rng = np.random.default_rng(SEMILLA_INYECTAR)
    sel = [negs[i] for i in sorted(rng.choice(len(negs), size=min(N_INYECTAR, len(negs)), replace=False))] if negs else []
    casos = []
    for f in sel:
        g = grillas[f["vol"]]
        p = {"npix": 1, "vrp_mw": VRP_INYECTADO, "pixeles": [[25, 25, 2, DIST_INYECTADA, 0.1, 350.0]]}
        p["_dcen"] = DIST_INYECTADA
        r = {k: x for k, x in AN.record_port(p, f["inner"], f["sensor"]).items() if not k.startswith("_")}
        casos.append((r, f["inner"]))
    b = predicado(casos)
    no_pasan = [(f["vol"], f["dt"]) for f, x in zip(sel, b) if x[0] != 1]
    s_antes = p2(filas, "PM")["s_b"]
    marca = {(f["vol"], f["dt"]) for f in sel}
    for f in sel:
        f["_t"]["PM_guardado"] = dict(f["_t"]["PM"])
        f["_t"]["PM"] = {"pub": 1, "mag": VRP_INYECTADO}
    try:
        s_despues = p2(filas, "PM")["s_b"]
    finally:
        for f in sel:
            f["_t"]["PM"] = f["_t"].pop("PM_guardado")
    ok = (not siguen and len(sel) == N_INYECTAR and not no_pasan and s_despues - s_antes == len(marca))
    return {"estado": "OK" if ok else "INDECIDIBLE", "pm_publica": len(pub_pm), "siguen_publicando_con_cero": siguen[:20],
            "inyectados": len(sel), "no_pasan_a_publicar": no_pasan[:20], "s_pm_antes": s_antes,
            "s_pm_con_inyeccion": s_despues}


def control_cobertura(filas, esperadas, crudas):
    """§8 control 5: cada pasada de la población con fila del arnés, sin repetidas; las que salen por uno de los dos
    motivos sellados se cuentan aparte por motivo; una falla del arnés o del port (adenda 4) deja el control en rojo."""
    c = EM.control_cobertura([f for f in filas if f.get("estado") == "ok"], esperadas)
    dup = EM.control_duplicados(crudas)
    fuera = collections.Counter(f["_motivo"] for f in filas if not f["_evaluable"])
    fallas = [{"vol": f["vol"], "dt": f["dt"], "motivo": f["_motivo"]} for f in filas
              if not f["_evaluable"] and f["_motivo"] not in MOTIVOS_SELLADOS]
    sel = [f for f in filas
           if not f["_evaluable"] and f.get("lab") == "protegida" and f["_motivo"] in MOTIVOS_SELLADOS]
    # VCR-06 (ronda 2): «K publica» de estas pasadas sale del predicado del evaluador sobre el record de K, como en las
    # evaluables; si no coincide con lo que dijo el runner, es una falla del instrumento (control en rojo)
    pk = predicado([(f.get("k_slim"), f["inner"]) for f in sel])
    prot_fuera = []
    for f, (pub, _mag) in zip(sel, pk):
        runner = int((f.get("pub") or {}).get("K") or 0)
        prot_fuera.append({"vol": f["vol"], "dt": f["dt"], "motivo": f["_motivo"], "k_publica": pub,
                           "k_publica_runner": runner})
        if pub != runner:
            fallas.append({"vol": f["vol"], "dt": f["dt"], "motivo": "predicado_de_K_distinto_del_runner"})
    estado = "OK" if c["estado"] == "OK" and dup["estado"] == "OK" and not fallas else "INDECIDIBLE"
    return {"estado": estado, "faltan": c["faltan"][:20], "n_faltan": len(c["faltan"]), "duplicadas": dup,
            "fallas_del_instrumento": fallas[:20], "n_fallas_del_instrumento": len(fallas),
            "fuera_del_denominador": dict(fuera), "protegidas_fuera_del_denominador": prot_fuera,
            "n_evaluables": sum(1 for f in filas if f["_evaluable"])}


# ------------------------------------------------------------------ veredicto
def _rojo(c):
    return (c if isinstance(c, str) else c.get("estado")) not in ("OK",)


def veredicto(res):
    """§6, primera fila que se cumpla."""
    if any(_rojo(c) for c in res["controles"].values()):
        return "INDECIDIBLE"
    b = res["brazos"][DECIDE]
    if b["p1"]["estado"] == "VETADO":
        return "NO CANDIDATO"
    if b["p2"]["estado"] == "PIERDE":
        return "NO CANDIDATO"
    if b["p2"]["estado"] == "SIN SUSTRATO":
        return "INDECIDIBLE"
    # adenda 4 (VCM-01): una protegida que K publica y que salió del denominador por un motivo sellado no puede pasar
    # en silencio a CANDIDATO (el port no la habría publicado); va a la fila 5 con su lista
    prot_k = [p for p in res["controles"]["cobertura"].get("protegidas_fuera_del_denominador", []) if p.get("k_publica")]
    if b["p2"]["estado"] == "BLOQUEA" or b["p1b"]["decide"] or b["m"]["regla"] == "EMPEORA" or prot_k:
        return "DECIDE NICOLÁS"
    if b["p2"]["estado"] in ("GANA", "EMPATE"):
        return "CANDIDATO"
    return "INDECIDIBLE"


def evaluar(filas, grillas, recorridos, externos, esperadas, crudas, nuestros=(), alertas_mirova=None,
            dir_s159=S159):
    alertas_mirova = alertas_mirova or {}
    for f in filas:
        f["_evaluable"], f["_motivo"] = evaluable(f)
    armar_tabla(filas, grillas)
    ctl = {"k_produccion": control_k_produccion(filas, recorridos), "port_s159": control_port_s159(filas, dir_s159),
           "placebo": control_placebo(filas), "contador": control_contador(filas, grillas),
           "cobertura": control_cobertura(filas, esperadas, crudas)}
    ctl.update(externos)
    res = {"controles": ctl, "brazos": {}}
    for b in (DECIDE,) + INFORMA + ("K33", "PM-pixel", "PM-b21"):
        res["brazos"][b] = {"p1": p1(filas, b), "p1b": p1b(filas, b), "p2": p2(filas, b), "m": m(filas, b),
                            "curva_cenit": curva_cenit(filas, b), "costura": costura(filas, b),
                            "borde_granulo": borde_granulo(filas, b),
                            "noches_a94": noches_a94(filas, b, nuestros),
                            "soporte_adenda1": soporte_independiente(filas, b, nuestros, alertas_mirova)}
    res["curva_cenit_K"] = curva_cenit(filas, "K")
    res["chillan"] = chillan(filas, DECIDE)
    res["s1"] = s1_informe(filas)
    res["k33_igual_k"] = dict(collections.Counter(bool(f.get("k33_igual_k")) for f in _ev(filas)))
    res["d33_dentro_del_pm"] = sum(1 for f in _ev(filas) if ((f.get("saturados") or {}).get("b22_nan_con_b21") or 0) > 0)
    res["veredicto"] = veredicto(res)
    return res


# ------------------------------------------------------------------ E/S
def cargar(art):
    filas, recorridos, cabeceras = [], [], []
    for p in sorted(glob.glob(str(Path(art) / "**" / "ab_parte*.jsonl"), recursive=True)):
        for x in open(p, encoding="utf-8"):
            r = json.loads(x)
            (cabeceras if r.get("tipo") == "cabecera" else filas if r.get("tipo") == "record" else []).append(r)
    for p in sorted(glob.glob(str(Path(art) / "**" / "recorridos_parte*.jsonl"), recursive=True)):
        recorridos += [json.loads(x) for x in open(p, encoding="utf-8")]
    return filas, recorridos, cabeceras


def externos_de_entrada(pob, cab, crudas, ref, commit_esperado=None):
    ext = {}
    import manifiesto_candado as MC       # adenda 4 (VCM-02): hash de cada archivo del candado
    ext["manifiesto"] = MC.comprobar()
    # VCR-03 (ronda 2): el hash del manifiesto que se usó, para cotejarlo con `git ls-tree <tag>` (el chequeo de arriba
    # compara el árbol de quien lee con SU manifiesto; leer desde el checkout del tag es lo que lo ata al candado)
    ext["manifiesto"]["blob_manifiesto"] = blob(MC.MANIFIESTO) if Path(MC.MANIFIESTO).exists() else None
    malos = {r: blob(RAIZ / r) for r, h in BLOBS_SELLADOS.items() if blob(RAIZ / r) != h}
    d25 = blob(D25_RUTA)
    cab_blobs = sorted({json.dumps(c.get("blobs"), sort_keys=True) for c in cab})
    ext["blobs"] = {"estado": "OK" if not malos and d25 == D25_BLOB and cab_blobs == [json.dumps(BLOBS_SELLADOS,
                    sort_keys=True)] else "INDECIDIBLE", "distintos_aqui": malos, "evaluar_d25": d25,
                    "blobs_jobs": cab_blobs}
    sha_html = hashlib.sha256((RAIZ / "frontend/index.html").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    shas = sorted({c.get("sha256_frontend_index") for c in cab})
    ext["predicado"] = {"estado": "OK" if shas == [sha_html] else "INDECIDIBLE", "local": sha_html, "jobs": shas}
    commits = sorted({c.get("commit") for c in cab})
    # adenda 4 (VCM-02): todos los jobs en UN commit, y ese commit es el del tag del candado (--commit)
    # VCR-04 (ronda 2): el sha completo, igual, no un prefijo
    ok_commit = bool(commit_esperado) and len(str(commit_esperado)) == 40 and commits == [commit_esperado]
    ext["procedencia"] = {"estado": "OK" if ok_commit else "INDECIDIBLE", "commits": commits,
                          "commit_esperado": commit_esperado, "partes": sorted(c.get("parte") for c in cab)}
    if ref is None:
        ext["referencia"] = {"estado": "INDECIDIBLE", "motivo": "falta --ref: sin referencia congelada no hay veredicto"}
        return ext
    mal = {n: EM._sha256_lf(Path(ref) / n) for n, v in pob["referencia"].items()
           if EM._sha256_lf(Path(ref) / n) != v["sha256_lf"]}
    ext["referencia"] = {"estado": "INDECIDIBLE" if mal else "OK", "distintos": mal}
    with tempfile.TemporaryDirectory() as td:
        dst = Path(td) / "poblacion_reetiquetada.json"
        pr = subprocess.run([sys.executable, "-I", str(RAIZ / "experiments/_s162_mxd03/poblacion_mxd03.py"), "--ref",
                             str(ref), "--sin-bajar", "--salida", str(dst)], capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
        if pr.returncode != 0 or not dst.exists():
            ext["reetiquetado"] = {"estado": "INDECIDIBLE", "error": (pr.stdout + pr.stderr)[-1500:]}
        else:
            ext["reetiquetado"] = EM.control_reetiquetado(
                {(f["vol"], f["dt"]): f for g in pob["granulos"] for f in g["records"]},
                json.loads(dst.read_text(encoding="utf-8")))
    return ext


def contexto(ref):
    """Nuestros records (todos los sensores, predicado del tablero) y alertas de MIROVA por volcán, de la ventana."""
    PM_ = _cargar("poblacion_mxd03_modd", RAIZ / "experiments/_s162_mxd03/poblacion_mxd03.py")
    coords = PM_._coords_por_volcan()
    inner = bp.inner_desde_html()
    nuestros = bp.cargar_nuestros(coords, inner, PM_.VENTANA)
    alertas = collections.defaultdict(list)
    if ref is not None:
        filas = PM_.cargar_referencia_unificada(Path(ref) / PM_.NOMBRES[0], Path(ref) / PM_.NOMBRES[1])
        por_vb, _ns, _nv, _n = bp.indexar_referencia(filas, coords, PM_.VENTANA, regla_minimas="SN")
        for (vol, buck), lista in por_vb.items():
            for dt, f in lista:
                if bp.es_alerta(f["tipo"]):
                    alertas[vol].append((dt, buck))
    return nuestros, dict(alertas)


def unir(crudas, pob):
    pobf = {(f["vol"], f["dt"]): f for g in pob["granulos"] for f in g["records"]}
    filas, distintas = [], []
    for r in crudas:
        pf = pobf.get((r.get("vol"), r.get("dt")), {})
        if pf and r.get("estado") == "ok" and any(r.get(k) != pf.get(k) for k in ("lab", "z")):
            distintas.append((r.get("vol"), r.get("dt")))
        base = dict(r)
        base.update(pf)
        base["inner"] = r.get("inner", pf.get("inner"))
        filas.append(base)
    sin_pob = sum(1 for r in crudas if (r.get("vol"), r.get("dt")) not in pobf)
    return filas, {"estado": "INDECIDIBLE" if distintas or sin_pob else "OK", "distintas": distintas[:20],
                   "sin_poblacion": sin_pob}, list(pobf)


def cruce_modb(filas, dir_modb):
    """Informa: el K de este censo contra el K del A/B de MxD03 (mismo main, misma población): tienen que coincidir."""
    if not dir_modb:
        return None
    mb, _r, _c = EM.cargar(dir_modb)
    k = {(f["vol"], f["dt"]): f for f in mb if f.get("estado") == "ok"}
    dist, n = [], 0
    for f in filas:
        o = k.get((f["vol"], f["dt"]))
        if f.get("estado") != "ok" or o is None:
            continue
        n += 1
        a, b = (f.get("brazos") or {}).get("K"), (o.get("brazos") or {}).get("K")
        if (f.get("pub") or {}).get("K") != (o.get("pub") or {}).get("K") or (a or {}).get("pc_vrp") != (b or {}).get("pc_vrp"):
            dist.append((f["vol"], f["dt"]))
    return {"comparadas": n, "distintas": len(dist), "ejemplos": dist[:10]}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True)
    ap.add_argument("--poblacion", default=str(POBLACION))
    ap.add_argument("--ref", default=None)
    ap.add_argument("--modb", default=None)
    ap.add_argument("--s159", default=str(S159))
    ap.add_argument("--salida", default=None)
    ap.add_argument("--commit", default=None, help="sha del tag del candado: sin el, procedencia INDECIDIBLE")
    a = ap.parse_args()
    pob = json.load(open(a.poblacion, encoding="utf-8"))
    grillas = json.load(open(GRILLAS, encoding="utf-8"))
    crudas, recorridos, cab = cargar(a.art)
    filas, union, esperadas = unir(crudas, pob)
    ext = externos_de_entrada(pob, cab, crudas, a.ref, a.commit)
    ext["union"] = union
    nuestros, alertas = contexto(a.ref)
    res = evaluar(filas, grillas, recorridos, ext, esperadas, crudas, nuestros, alertas, a.s159)
    res["cruce_k_modb"] = cruce_modb(filas, a.modb)
    print("VEREDICTO:", res["veredicto"])
    for k, c in res["controles"].items():
        print("  control %-14s %s" % (k, c if isinstance(c, str) else c.get("estado")))
    for b, x in res["brazos"].items():
        print("  %-8s P1 %s (%d) | P1b %d | P2 %s neto %s B %s (S_K %s, S_b %s) | M %s n %s" % (
            b, x["p1"]["estado"], len(x["p1"]["perdidas"]), len(x["p1b"]["decide"]), x["p2"]["estado"],
            x["p2"]["neto"], x["p2"]["B"], x["p2"]["s_k"], x["p2"]["s_b"], x["m"]["regla"], x["m"]["n"]))
    print("  Chillan:", {k: res["chillan"][k] for k in ("estado", "n_pares", "b_mas_cerca", "mediana_razon",
                                                       "mediana_z_le30", "mediana_z_gt30")})
    print("  S-1:", {k: res["s1"][k] for k in ("n_ok", "n_identidad_falla")}, res["s1"]["tabla"])
    print("  protegidas fuera del denominador:", res["controles"]["cobertura"]["protegidas_fuera_del_denominador"])
    print("  cruce con el K de MOD-B:", res["cruce_k_modb"])
    print("  manifiesto usado (blob, cotejar con git ls-tree del tag):", res["controles"]["manifiesto"].get("blob_manifiesto"))
    out = Path(a.salida) if a.salida else Path(a.art) / "resultado_paquete.json"
    for f in filas:
        f.pop("_t", None)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("escrito", out)


if __name__ == "__main__":
    main()
