# -*- coding: utf-8 -*-
"""S166 MOD-D fase 4: evaluador del A/B de la vía «código MIROVA» de MODIS (flag encendido en memoria) contra K, con
los tres brazos de posición. Implementa TAL CUAL las reglas de PREREGISTRO_MODD_F4.md (§6 a §9). Si una regla cambia,
cambia aquí y en el pre-registro en el mismo commit, con adenda fechada.

POR QUÉ CADA PIEZA (resumen; el detalle está en el pre-registro):
- La vara es lo que publica MIROVA (lectura A, pareo ±120 s, etiquetas de la población). «Publica» y la magnitud
  mostrada salen del predicado de frontend/index.html ejecutado con node (banco_paridad.correr_node, A97) sobre el
  record que dejó store.append_record en el runner; el placebo es el record de K con toda magnitud por 1,2.
- P1, P1b, P2 y M son las reglas selladas de MOD-D (experiments/_s162_modis_paquete/PREREGISTRO.md §4, tag
  s162-modd-tag) con V en el lugar del PM. Las piezas estadísticas se importan sin copiar del blob sellado de
  evaluar_d25.py (1dbabf65, el mismo que usó MOD-D): prueba_signos_p2 y regla_signos_p2 (D-45), pesos_bloque, regla_m y
  comparar_con_ganancia (D-28).
- P2' suma a P2 las pasadas en que MIROVA ubicó el calor lejos del cráter (far_ref, fila FALSO_POSITIVO sin ALERTA):
  publicarlas como cumbre es publicar de más (decisión de Nicolás del 2026-10-27, programa §7).
- Los brazos de posición comparten detección y VRP con V; sólo cambia el punto desde donde se mide la distancia al
  cráter, y con ella summit/far (variante_posicion).

LAS DOS PREGUNTAS DEL INSTRUMENTO:
1. Si V no cambiara nada respecto de K, ¿se vería? Sí: P2 daría EMPATE con neto 0 o SIN SUSTRATO, M SIN PARES o NEUTRO
   y el veredicto no podría ser PROPONER; los escenarios de probar_evaluar_f4.py arman cada salida a propósito.
2. Si el arnés o el evaluador estuvieran rotos, ¿se vería distinto de PROPONER? Sí: una vía que no corrió (record sin
   la marca), una identidad rota contra la vía sobre las grillas del censo, un placebo con d′ distinto de 0, un
   contador que no ve 50 publicaciones inyectadas, una pasada faltante o repetida, una variante radiante que no
   reproduce al record, o un control externo ausente dan INDECIDIBLE.
Uso: python evaluar_f4.py --art DIR --poblacion poblacion_f4.json --identidad identidad.json
     --externos externos.json [--salida resultado.json]
"""
from __future__ import annotations

import argparse
import collections
import copy
import glob
import hashlib
import importlib.util
import json
import math
import os
import statistics
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
# F4_RAIZ sólo la usa mutar_evaluar_f4.py, que corre copias mutadas fuera del repositorio
RAIZ = Path(os.environ.get("F4_RAIZ") or AQUI.parents[1])
sys.path.insert(0, str(RAIZ / "scripts"))

D25_BLOB = "1dbabf657407b6db0f91d9e2fc98eb16a8051873"
D25_RUTA = RAIZ / "experiments/_s157_prereg_d25/evaluar_d25.py"


def blob(ruta):
    b = Path(ruta).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


D = _cargar("evaluar_d25_f4", D25_RUTA)

ETIQUETAS = ("protegida", "bajo1", "neg_limpio", "far_ref", "sin_info")
BRAZOS_V = ("V", "V-cercano", "V-pico")                      # §3: la misma detección, tres reglas de posición
REGLA_DE = {"V": "radiante", "V-cercano": "cercano", "V-pico": "pico"}
PLACEBO = 1.2
CORTE_MW = 1.0
MOTIVOS_SELLADOS = ("volcan_fuera_del_granulo", "escena_invalida")
TOL_VRP_IDENTIDAD = 1e-3            # §8.2: MW
TOL_DIST_POSICION = 6e-4            # §8.9: km (el record redondea a 0,001)
MAX_OTRO_GRANULO = 0.01             # §8.2: fracción de las pasadas con grilla del censo
N_GRILLAS_CENSO = 5321              # §8.2: grilla_NNNN.npz del censo MOD-D (S165 modis_salida.txt; 5.321 en disco)
INICIO_E = "2026-10-17"             # §4: primer día del tramo E (la cola posterior al censo)
N_INYECTAR, SEMILLA_INYECTAR = 50, 166
VRP_INYECTADO, DIST_INYECTADA = 0.3, 0.5
CORTE_CENIT_CHILLAN = 30.0          # §9, el corte sellado de MOD-D §5
CHILLAN = "NevadosDeChillan"
CAMPOS_MAG = ("vrp_mw", "vrp_mir_mw", "vrp_vent_mw", "f5_core_vrp_mw")
EXTERNOS_REQUERIDOS = ("referencia", "reetiquetado", "manifiesto", "procedencia", "predicado")


# ------------------------------------------------------------------ posición (§3 y §6 bis)
def distancias(celdas, rad, pos_crater, paso_km, cumulo):
    """celdas: [(fila, col)] alertadas por la vía; rad: su radiancia MIR (mismo orden); pos_crater: posición
    fraccionaria del cráter en la grilla (la de la vía); cumulo: la función que elige el cúmulo de la alertada más
    radiante (MV._cumulo_del_mas_radiante en el arnés, sin copiarla). Devuelve las distancias al cráter de las tres
    reglas, en km, sin redondear."""
    n = 1 + max(max(f for f, _ in celdas), max(c for _, c in celdas))
    mascara = np.zeros((n, n), bool)
    m = np.zeros((n, n), float)
    for (f, c), L in zip(celdas, rad):
        mascara[f, c] = True
        m[f, c] = L
    cu = cumulo(mascara, m)
    fr, fc = float(np.mean([a for a, _ in cu])), float(np.mean([b for _, b in cu]))
    pico = max(((f, c) for f, c in celdas), key=lambda p: m[p])

    def d(a, b):
        return float(np.hypot(a - pos_crater[0], b - pos_crater[1]) * paso_km)
    return {"radiante": d(fr, fc), "cercano": min(d(f, c) for f, c in celdas), "pico": d(*pico)}


def clase_dc(dist, inner):
    return "summit" if dist <= inner else "far"              # procesar_grilla: dcen <= inner_km


def variante_posicion(rec, regla, dists, inner):
    """El record de la vía con la distancia de otra regla. Sólo cambian distance_class, pc.centroid_dist_km y
    final_hotspot_dist_km (lo que leen el guard A46 de store y mirovaEqVrp del tablero); VRP y píxeles no cambian."""
    r = copy.deepcopy(rec)
    if regla == "radiante" or not (r or {}).get("primary_cluster"):
        return r
    dd = dists[regla]
    r["distance_class"] = clase_dc(dd, inner)
    r["primary_cluster"]["centroid_dist_km"] = round(dd, 3)
    r["final_hotspot_dist_km"] = round(dd, 3)
    return r


# ------------------------------------------------------------------ records y predicado
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


def predicado_node(casos):
    """[(slim, inner)] -> [(publica 0/1, magnitud mostrada)], con node sobre frontend/index.html."""
    import banco_paridad as bp
    vivos = [(i, c) for i, c in enumerate(casos) if c[0] is not None]
    out = [(0, 0.0)] * len(casos)
    if vivos:
        res = bp.correr_node([[{k: c[0].get(k) for k in bp.CAMPOS_JS} | {"anomaly_pixels": c[0].get("anomaly_pixels")
                                                                           or []}, c[1]] for _, c in vivos])
        for (i, _), p in zip(vivos, res):
            out[i] = (int(p[4]), float(p[3] or 0.0))
    return out


def evaluable(f):
    """§8.6: sólo «volcán fuera del gránulo» y «escena inválida» salen del denominador de TODOS los brazos. Una falla
    del arnés, o una vía que no corrió (record de V sin la marca via_codigo_mirova True: siguió K), es falla del
    instrumento: sale del cálculo con su motivo y deja la cobertura en rojo."""
    if f.get("estado") != "ok":
        return False, "falla_arnes_" + str(f.get("estado"))
    mot = f.get("motivo")
    if mot in MOTIVOS_SELLADOS:
        return False, mot
    if mot:
        return False, "falla_" + str(mot)
    if f.get("v_marca") is not True:
        return False, "falla_via_" + str(f.get("v_marca"))
    return True, None


def armar_tabla(filas, predicado=predicado_node):
    casos, idx = [], []
    for i, f in enumerate(filas):
        if not f["_evaluable"]:
            continue
        for b, rec in (("K", f.get("k_slim")), ("placebo", escalar(f.get("k_slim"), PLACEBO)),
                       ("V", f.get("v_slim")), ("V-cercano", f.get("vcerc_slim")), ("V-pico", f.get("vpico_slim"))):
            casos.append((rec, f["inner"]))
            idx.append((i, b))
    for (i, b), v in zip(idx, predicado(casos)):
        filas[i].setdefault("_t", {})[b] = {"pub": v[0], "mag": v[1]}
    return filas


def _pub(f, b):
    return f["_t"][b]["pub"]


def _mag(f, b):
    return f["_t"][b]["mag"]


def _bloque(f):
    return "%s|%s" % (f["vol"], f.get("noche") or f["dt"][:10])


def _ev(filas):
    return [f for f in filas if f["_evaluable"]]


# ------------------------------------------------------------------ pruebas (§6)
def _lab(f, union=False):
    """§5 (A119): `lab` es la etiqueta con la tabla sola, la que decide; `lab_union` la de tabla más OCR, que informa
    (sin `lab_union` la pasada no tiene fila sólo OCR y las dos coinciden)."""
    return f.get("lab_union", f["lab"]) if union else f["lab"]


def p1(filas, b, ref="K"):
    """Veto: protegidas que ref publica y b no. Una protegida de la tabla perdida veta; una que es protegida sólo en la
    unión con el OCR (solo_ocr) no veta: lleva a DECIDE NICOLÁS (§7, fila 5)."""
    perd = [{"vol": f["vol"], "dt": f["dt"], "z": f.get("z"), "vrp_ref": _mag(f, ref), "vrp_mirova": f.get("vrp_mirova"),
             "solo_ocr": f["lab"] != "protegida"}
            for f in _ev(filas) if _lab(f, True) == "protegida" and _pub(f, ref) == 1 and _pub(f, b) == 0]
    return {"estado": "VETADO" if any(not x["solo_ocr"] for x in perd) else (
        "SOLO OCR" if perd else "SIN PERDIDA"), "perdidas": perd,
        "mirova_sin_ninguno": [(f["vol"], f["dt"]) for f in _ev(filas)
                               if f["lab"] == "protegida" and _pub(f, b) == 0 and _pub(f, ref) == 0]}


def p1b(filas, b):
    baja, sube = [], []
    for f in _ev(filas):
        if f["lab"] != "protegida" or not (_pub(f, "K") == 1 and _pub(f, b) == 1):
            continue
        fila = {"vol": f["vol"], "dt": f["dt"], "mag_k": _mag(f, "K"), "mag_b": _mag(f, b),
                "vrp_mirova": f.get("vrp_mirova")}
        if _mag(f, "K") >= CORTE_MW > _mag(f, b):
            baja.append(fila)
        elif _mag(f, "K") < CORTE_MW <= _mag(f, b):
            sube.append(fila)
    return {"decide": baja, "contraria_lista": sube}


def _error(f, b, lejana, union=False):
    lab = _lab(f, union)
    if lab == "bajo1":
        return _pub(f, b) == 0
    if lab == "neg_limpio":
        return _pub(f, b) == 1
    if lejana and lab == "far_ref":
        return _pub(f, b) == 1
    return False


def contribuciones(filas, b, ref="K", lejana=False, union=False):
    """+1 si el error es sólo de b, -1 si es sólo de ref (signo de D-45: positivo es malo para b)."""
    labs = ("bajo1", "neg_limpio", "far_ref") if lejana else ("bajo1", "neg_limpio")
    out = []
    for f in _ev(filas):
        if _lab(f, union) not in labs:
            continue
        er, eb = _error(f, ref, lejana, union), _error(f, b, lejana, union)
        if er != eb:
            out.append({"vol": f["vol"], "dt": f["dt"], "lab": _lab(f, union), "c": 1 if eb else -1,
                        "bloque": _bloque(f), "z": f.get("z")})
    return out


def p2(filas, b, ref="K", lejana=False, union=False):
    """P2 (lejana=False, sellada en MOD-D) y P2' (lejana=True): prueba de signos por bloque noche-volcán, D-45.
    union=True la repite con las etiquetas de tabla más OCR (informa, A119)."""
    c = contribuciones(filas, b, ref, lejana, union)
    neto = sum(x["c"] for x in c)
    por_bloque = collections.Counter()
    for x in c:
        por_bloque[x["bloque"]] += x["c"]
    sumas = [por_bloque[k] for k in sorted(por_bloque)]
    B = len(sumas)
    pr = D.prueba_signos_p2(sumas, neto)
    estado = D.regla_signos_p2(neto, B, pr)
    labs = ("bajo1", "neg_limpio", "far_ref") if lejana else ("bajo1", "neg_limpio")
    s_ref = sum(1 for f in _ev(filas) if _lab(f, union) in labs and _error(f, ref, lejana, union))
    s_b = sum(1 for f in _ev(filas) if _lab(f, union) in labs and _error(f, b, lejana, union))
    return {"estado": estado, "neto": neto, "B": B, "s_ref": s_ref, "s_b": s_b, "p_gana": pr["gana"],
            "p_pierde": pr["pierde"], "metodo": pr["metodo"], "discordantes": c}


def pares_m(filas, b):
    out = []
    for f in _ev(filas):
        if f["lab"] not in ("protegida", "bajo1") or not (_pub(f, "K") == 1 and _pub(f, b) == 1):
            continue
        k, d, mm = _mag(f, "K"), _mag(f, b), f.get("vrp_mirova")
        if k > 0 and d > 0 and mm and mm > 0:
            out.append({"k": k, "d": d, "m": mm, "clave": "%s|MODIS|%s" % (f["vol"], f["dt"]), "bloque": _bloque(f),
                        "z": f.get("z"), "vol": f["vol"]})
    return out


def m(filas, b):
    P = pares_m(filas, b)
    if not P:
        return {"n": 0, "regla": "SIN PARES"}
    d = [abs(math.log10(p["d"] / p["m"])) - abs(math.log10(p["k"] / p["m"])) for p in P]
    bloques = [p["bloque"] for p in P]
    W = D.pesos_bloque(bloques)
    regla, lo, hi = D.regla_m(d, W)
    out = {"n": len(P), "regla": regla, "ic95_d": [lo, hi], "mediana_d": statistics.median(d)}
    try:
        out["dprima"] = D.comparar_con_ganancia(P, W, bloques)
    except Exception as e:  # noqa: BLE001  (informa: si no corre, se dice)
        out["dprima"] = {"error": f"{type(e).__name__}: {e}"[:200]}
    return out


def razon_protegidas(filas, b):
    """Informa (§6.5): mediana de b/MIROVA en TODAS las protegidas que b publica, publique K o no."""
    r = [_mag(f, b) / f["vrp_mirova"] for f in _ev(filas)
         if f["lab"] == "protegida" and _pub(f, b) == 1 and _mag(f, b) > 0 and (f.get("vrp_mirova") or 0) > 0]
    return {"n": len(r), "mediana": statistics.median(r) if r else None,
            "en_banda_0_9_1_1": (r and 0.9 <= statistics.median(r) <= 1.1) or False}


def _tramo(z):
    return None if z is None else "%d-%d" % (int(z // 10) * 10, int(z // 10) * 10 + 10)


def curva_cenit(filas, b, vol=None):
    t = collections.defaultdict(list)
    for f in _ev(filas):
        if vol and f["vol"] != vol:
            continue
        if f["lab"] in ("protegida", "bajo1") and _pub(f, b) == 1 and f.get("vrp_mirova") and f.get("z") is not None:
            t[_tramo(f["z"])].append(_mag(f, b) / f["vrp_mirova"])
    return {k: {"n": len(v), "mediana": statistics.median(v)} for k, v in sorted(t.items())}


def _signos_una_cola(k, n):
    return sum(math.comb(n, i) for i in range(k, n + 1)), 2 ** n


def chillan(filas, b="V"):
    """§9.1: la prueba propia sellada de MOD-D §5, con V en el lugar del PM, sobre C ∪ E."""
    al = [f for f in _ev(filas) if f["vol"] == CHILLAN and f["lab"] in ("protegida", "bajo1")]
    recup = [{"dt": f["dt"], "z": f.get("z"), "razon": _mag(f, b) / f["vrp_mirova"] if f.get("vrp_mirova") else None}
             for f in al if _pub(f, "K") == 0 and _pub(f, b) == 1]
    pares, empates = [], []
    for f in al:
        if _pub(f, "K") == 1 and _pub(f, b) == 1 and f.get("vrp_mirova") and _mag(f, "K") > 0 and _mag(f, b) > 0:
            mm = f["vrp_mirova"]
            dk, db = abs(math.log10(_mag(f, "K") / mm)), abs(math.log10(_mag(f, b) / mm))
            par = {"dt": f["dt"], "z": f.get("z"), "razon_b": _mag(f, b) / mm, "razon_k": _mag(f, "K") / mm,
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
    return {"estado": estado, "brazo": b, "recuperadas": recup, "pares": pares, "empates": empates, "n_pares": n,
            "b_mas_cerca": k, "p_una_cola": [num, den], "mediana_razon": med, "mediana_z_le30": med_bajo,
            "mediana_z_gt30": med_sobre}


def chillan_por_tramo(filas, b="V"):
    """§9.2 (informa): por tramo de 10° de cenit, protegidas de Chillán, cuántas publica K y cuántas b, y las razones."""
    t = collections.defaultdict(lambda: {"protegidas": 0, "pub_K": 0, "pub_b": 0, "razon_K": [], "razon_b": []})
    for f in _ev(filas):
        if f["vol"] != CHILLAN or f["lab"] != "protegida":
            continue
        x = t[_tramo(f.get("z"))]
        x["protegidas"] += 1
        for br, kk in (("K", "K"), (b, "b")):
            if _pub(f, br):
                x["pub_" + kk] += 1
                if f.get("vrp_mirova"):
                    x["razon_" + kk].append(_mag(f, br) / f["vrp_mirova"])
    return {k: dict(v, razon_K=statistics.median(v["razon_K"]) if v["razon_K"] else None,
                    razon_b=statistics.median(v["razon_b"]) if v["razon_b"] else None) for k, v in sorted(t.items())}


def curva_misma_noche(filas, b):
    """§6.6 (informa): en cada noche-volcán con dos alertas que b y MIROVA publican, razón (más oblicua / menos
    oblicua) de b y de MIROVA. No se busca aplanar la curva con el cenit sino reproducir la de MIROVA."""
    g = collections.defaultdict(list)
    for f in _ev(filas):
        if f["lab"] in ("protegida", "bajo1") and _pub(f, b) == 1 and f.get("vrp_mirova") and f.get("z") is not None \
                and _mag(f, b) > 0:
            g[_bloque(f)].append(f)
    rb, rm = [], []
    for v in g.values():
        if len(v) < 2:
            continue
        v = sorted(v, key=lambda f: f["z"])
        lo, hi = v[0], v[-1]
        if hi["z"] - lo["z"] < 10:
            continue
        rb.append(_mag(hi, b) / _mag(lo, b))
        rm.append(hi["vrp_mirova"] / lo["vrp_mirova"])
    return {"n": len(rb), "mediana_b": statistics.median(rb) if rb else None,
            "mediana_mirova": statistics.median(rm) if rm else None}


# ------------------------------------------------------------------ regla de posición (§6 bis)
def descriptivas_posicion(filas):
    """§6 bis (descriptivas, no deciden): por brazo de posición, las pasadas cuya publicación cambia contra V, por
    nombre y etiqueta; y cuántas pasadas far_ref tienen algún alertado de la vía (un cero de E_lejana sin alertados no
    dice nada)."""
    out = {}
    for b in BRAZOS_V[1:]:
        out[b] = [{"vol": f["vol"], "dt": f["dt"], "lab": f["lab"], "V": _pub(f, "V"), b: _pub(f, b)}
                  for f in _ev(filas) if _pub(f, b) != _pub(f, "V")]
    lej = [f for f in _ev(filas) if f["lab"] == "far_ref"]
    out["far_ref"] = {"n": len(lej), "con_alertados": sum(1 for f in lej if (f.get("v_slim") or {}).get("primary_cluster"))}
    return out


def _no_peor(p):
    return p["estado"] in ("GANA", "EMPATE") or (p["estado"] == "SIN SUSTRATO" and p["neto"] <= 0)


def _e_total(x):
    return x["p2l_vs_K"]["s_b"]


def regla_posicion(res):
    """Elige el brazo de posición antes del veredicto. Elegible = P1 contra K no VETADO y, para V-cercano y V-pico,
    tampoco VETADO contra V (VF4-01: una posición no puede cambiar una protegida que V publica por publicaciones bajo
    1 MW; una pérdida sólo del OCR no quita la elegibilidad: la lleva el §7 a DECIDE NICOLÁS). Gana = elegible
    distinto de V cuyo P2' contra V da GANA. Si ganan dos, el de menor E + E_lejana; a igual valor, V-pico (preferencia
    a priori, VF4-12). Si ninguno gana, V si es elegible. Si V no es elegible, el elegible no peor que V en P2'; si son
    dos, el de menor E + E_lejana y a igual valor V-pico; si ninguno, NINGUNA."""
    br = res["brazos"]
    eleg = [b for b in BRAZOS_V if br[b]["p1"]["estado"] != "VETADO"
            and (b == "V" or br[b]["p1_vs_V"]["estado"] != "VETADO")]
    otros = [b for b in eleg if b != "V"]
    ganan = [b for b in otros if br[b]["p2l_vs_V"]["estado"] == "GANA"]

    def mejor(lista):
        return sorted(lista, key=lambda b: (_e_total(br[b]), 0 if b == "V-pico" else 1))[0]
    if ganan:
        return mejor(ganan), "gana en P2' contra V"
    if "V" in eleg:
        return "V", "ninguno gana contra V"
    nop = [b for b in otros if _no_peor(br[b]["p2l_vs_V"])]
    if nop:
        return mejor(nop), "V no es elegible; no peor que V"
    return None, "NINGUNA POSICIÓN ELEGIBLE"


# ------------------------------------------------------------------ controles (§8)
def control_identidad(ident, filas, n_grillas_censo=None):
    """§8.2: la vía del runner (del HDF) contra la vía corrida sobre la grilla que guardó el censo MOD-D, en cada pasada
    de C con grilla del censo. ident: {(vol, dt): {"mismo_granulo", "misma_mascara", "dvrp", "misma_clase"}}.
    VF4-02: el conjunto que se exige sale de la POBLACIÓN (campo grilla_censo), no del archivo de identidad, y la
    población tiene que traer exactamente las 5.321 grillas del censo; si no, la identidad no se midió entera."""
    n_grillas_censo = N_GRILLAS_CENSO if n_grillas_censo is None else n_grillas_censo
    n_pob = sum(1 for f in filas if f.get("grilla_censo"))
    con_grilla = [(f["vol"], f["dt"]) for f in _ev(filas) if f.get("grilla_censo")]
    faltan = sorted(k for k in con_grilla if k not in ident)
    otro = [k for k in con_grilla if k in ident and not ident[k]["mismo_granulo"]]
    malas = [{"clave": list(k), **ident[k]} for k in con_grilla
             if k in ident and ident[k]["mismo_granulo"] and not (
                 ident[k]["misma_mascara"] and abs(ident[k]["dvrp"]) <= TOL_VRP_IDENTIDAD and ident[k]["misma_clase"])]
    frac_otro = len(otro) / len(con_grilla) if con_grilla else 1.0
    ok = n_pob == n_grillas_censo and bool(con_grilla) and not faltan and not malas and frac_otro <= MAX_OTRO_GRANULO
    return {"estado": "OK" if ok else "INDECIDIBLE", "n_grillas_en_poblacion": n_pob,
            "n_grillas_esperadas": n_grillas_censo, "n_con_grilla": len(con_grilla), "n_faltan": len(faltan),
            "faltan": faltan[:20], "n_otro_granulo": len(otro), "otro_granulo": otro[:20], "n_distintas": len(malas),
            "distintas": malas[:20]}


def control_posicion(filas):
    """§8.9: (a) la distancia radiante que el arnés calculó reproduce el pc.centroid_dist_km y la clase del record de V
    en cada pasada con alertados; (b) las variantes cercano y pico conservan los píxeles de V y, cuando quedan en la
    misma clase que V, también su VRP (con otra clase, store puede tratarlas distinto: eso es parte de la regla)."""
    malas, n = [], 0
    for f in _ev(filas):
        v = f.get("v_slim") or {}
        if not v.get("primary_cluster"):
            continue
        n += 1
        d = (f.get("dist") or {}).get("radiante")
        pc = v["primary_cluster"]
        bien = d is not None and abs(d - pc["centroid_dist_km"]) <= TOL_DIST_POSICION and \
            clase_dc(d, f["inner"]) == v.get("distance_class")
        for b, c in (("V-cercano", "vcerc_slim"), ("V-pico", "vpico_slim")):
            if f.get(c) is None and (f.get("store_descarto") or {}).get(b):
                continue
            w = f.get(c) or {}
            bien = bien and len(w.get("anomaly_pixels") or []) == len(v.get("anomaly_pixels") or [])
            if w.get("distance_class") == v.get("distance_class"):
                bien = bien and w.get("vrp_mw") == v.get("vrp_mw") and \
                    (w.get("primary_cluster") or {}).get("vrp_mw") == pc.get("vrp_mw")
        if not bien:
            malas.append((f["vol"], f["dt"]))
    return {"estado": "OK" if n and not malas else "INDECIDIBLE", "n_con_alertados": n, "malas": malas[:20],
            "n_malas": len(malas)}


def control_predicado(predicado=predicado_node):
    """§8.9 (pregunta 2 del instrumento): el predicado cambia con distance_class; si no, un brazo de posición nunca
    podría cambiar una publicación."""
    base = {"vrp_mw": 0.4, "distance_class": "summit", "t_max_k": 290, "sensor": "MODIS_AQUA", "triggered_test1": False,
            "primary_cluster": {"vrp_mw": 0.4, "centroid_dist_km": 1.0, "n_pixels": 2}, "final_hotspot_dist_km": 1.0,
            "anomaly_pixels": []}
    lejos = variante_posicion(base | {"primary_cluster": dict(base["primary_cluster"])}, "cercano",
                              {"cercano": 9.0}, 5.0)
    r = [x[0] for x in predicado([(base, 5.0), (lejos, 5.0)])]
    return {"estado": "OK" if r == [1, 0] else "INDECIDIBLE", "publica": r}


def control_marca(filas):
    """§8.3: toda pasada evaluable (v_marca True: la vía corrió) trae los tres records de V. Una vía que no corrió ya
    sale de evaluable() como falla; aquí se atrapa la que corrió pero no dejó record (store lo descartó o el arnés no
    lo guardó), que de otro modo se leería como «V no publica»."""
    malas = [(f["vol"], f["dt"]) for f in _ev(filas)
             for b, c in (("V", "v_slim"), ("V-cercano", "vcerc_slim"), ("V-pico", "vpico_slim"))
             if f.get(c) is None and not (f.get("store_descarto") or {}).get(b)]
    return {"estado": "OK" if not malas else "INDECIDIBLE", "malas": malas[:20], "n_malas": len(malas)}


def control_placebo(filas):
    """§8.4: el placebo K x 1,2 da d′ = 0 en todo par (cableado de M)."""
    P = pares_m(filas, "placebo")
    if not P:
        return {"estado": "INDECIDIBLE", "motivo": "sin pares para el placebo"}
    bloques = [p["bloque"] for p in P]
    W = D.pesos_bloque(bloques)
    r = D.comparar_con_ganancia(P, W, bloques)
    gan = [p["d"] / p["k"] for p in P]
    ok = r["dprima_max_abs"] == 0 and all(abs(g - PLACEBO) < 1e-9 for g in gan)
    return {"estado": "OK" if ok else "INDECIDIBLE", "n": len(P), "dprima_max_abs": r["dprima_max_abs"]}


def control_contador(filas, predicado=predicado_node):
    """§8.5 (fuera de línea): (a) toda publicación de V con magnitud 0 deja de publicar; (b) 50 negativos que V no
    publica, con un cúmulo de cumbre de 0,3 MW a 0,5 km inyectado, pasan a publicar, y P2 de V cuenta 50 errores más."""
    ev = _ev(filas)
    pub_v = [f for f in ev if _pub(f, "V") == 1]
    casos = []
    for f in pub_v:
        r = copy.deepcopy(f["v_slim"])
        for k in CAMPOS_MAG:
            if k in r:
                r[k] = 0.0
        if r.get("primary_cluster"):
            r["primary_cluster"]["vrp_mw"] = 0.0
        casos.append((r, f["inner"]))
    siguen = [(f["vol"], f["dt"]) for f, x in zip(pub_v, predicado(casos)) if x[0] == 1]
    negs = sorted([f for f in ev if f["lab"] == "neg_limpio" and _pub(f, "V") == 0], key=lambda f: (f["vol"], f["dt"]))
    rng = np.random.default_rng(SEMILLA_INYECTAR)
    sel = [negs[i] for i in sorted(rng.choice(len(negs), size=min(N_INYECTAR, len(negs)), replace=False))] if negs else []
    casos = []
    for f in sel:
        r = {"vrp_mw": VRP_INYECTADO, "distance_class": "summit", "t_max_k": 300.0, "sensor": f.get("sensor"),
             "triggered_test1": False, "via_codigo_mirova": True, "final_hotspot_dist_km": DIST_INYECTADA,
             "primary_cluster": {"vrp_mw": VRP_INYECTADO, "centroid_dist_km": DIST_INYECTADA, "n_pixels": 1},
             "anomaly_pixels": [{"dist_km": DIST_INYECTADA, "bt_k": 300.0}]}
        casos.append((r, f["inner"]))
    no_pasan = [(f["vol"], f["dt"]) for f, x in zip(sel, predicado(casos)) if x[0] != 1]
    s_antes = p2(filas, "V")["s_b"]
    for f in sel:
        f["_t"]["V_guardado"] = dict(f["_t"]["V"])
        f["_t"]["V"] = {"pub": 1, "mag": VRP_INYECTADO}
    try:
        s_despues = p2(filas, "V")["s_b"]
    finally:
        for f in sel:
            f["_t"]["V"] = f["_t"].pop("V_guardado")
    ok = not siguen and len(sel) == N_INYECTAR and not no_pasan and s_despues - s_antes == len(sel)
    return {"estado": "OK" if ok else "INDECIDIBLE", "v_publica": len(pub_v), "siguen_con_cero": siguen[:20],
            "inyectados": len(sel), "no_pasan": no_pasan[:20], "s_v_antes": s_antes, "s_v_con_inyeccion": s_despues}


def _es_e(dt):
    return str(dt)[:10] >= INICIO_E


def control_cobertura(filas, esperadas, sin_pasada_nuestra=None, predicado=predicado_node):
    """§8.6 (A108): cada pasada de la población con una fila, sin repetidas ni sobrantes; sólo los dos motivos sellados
    salen del denominador; una falla del arnés o una vía que no corrió deja el control en rojo. sin_pasada_nuestra:
    pasadas MODIS de la referencia (protegida o bajo 1 MW) sin pasada de la población a ±120 s (programa §8.1), como
    tuplas (vol, dt, lab): en rojo. Si la lista no viene (None), el control queda en rojo: no se midió (VF4-03).
    Las listas van completas: el protocolo del tramo E (§7) las necesita enteras para decidir dónde está el rojo."""
    claves = [(f["vol"], f["dt"]) for f in filas]
    rep = sorted(k for k, n in collections.Counter(claves).items() if n > 1)
    faltan = sorted(set(esperadas) - set(claves))
    sobran = sorted(set(claves) - set(esperadas))
    fallas = [{"vol": f["vol"], "dt": f["dt"], "motivo": f["_motivo"]} for f in filas
              if not f["_evaluable"] and f["_motivo"] not in MOTIVOS_SELLADOS]
    # como en el sellado de MOD-D (VCR-06): «K publica» en estas pasadas sale del predicado del evaluador sobre el record
    # de K; si no coincide con lo que dijo el runner, es una falla del instrumento
    sel = [f for f in filas if not f["_evaluable"] and _lab(f, True) == "protegida" and f["_motivo"] in MOTIVOS_SELLADOS]
    prot_fuera = []
    for f, (pub, _m) in zip(sel, predicado([(f.get("k_slim"), f["inner"]) for f in sel])):
        if pub != int((f.get("pub_runner") or {}).get("K") or 0):
            fallas.append({"vol": f["vol"], "dt": f["dt"], "motivo": "predicado_de_K_distinto_del_runner"})
        if pub:
            prot_fuera.append({"vol": f["vol"], "dt": f["dt"], "motivo": f["_motivo"]})
    sin_medir = sin_pasada_nuestra is None
    sin = [tuple(x) for x in (sin_pasada_nuestra or ())]
    ok = not rep and not faltan and not sobran and not fallas and not sin and not sin_medir
    return {"estado": "OK" if ok else "INDECIDIBLE", "repetidas": rep, "faltan": faltan, "n_faltan": len(faltan),
            "sobran": sobran, "fallas": fallas, "n_fallas": len(fallas), "protegidas_k_fuera": prot_fuera,
            "sin_pasada_nuestra": sin, "sin_pasada_nuestra_no_medida": sin_medir,
            "fuera_del_denominador": dict(collections.Counter(f["_motivo"] for f in filas if not f["_evaluable"])),
            "n_evaluables": sum(1 for f in filas if f["_evaluable"])}


def rojo_solo_en_e(cob):
    """§7, protocolo del tramo E (VF4-06): True si la cobertura está en rojo y TODO lo que la pone en rojo es del tramo
    E (fecha desde INICIO_E). Entonces E se excluye entero en todos los brazos y se lee C solo, declarado."""
    if cob["estado"] == "OK" or cob["sin_pasada_nuestra_no_medida"]:
        return False
    dts = [k[1] for k in cob["repetidas"] + cob["faltan"] + cob["sobran"]] + [x["dt"] for x in cob["fallas"]] + \
        [x[1] for x in cob["sin_pasada_nuestra"]]
    return bool(dts) and all(_es_e(d) for d in dts)


def control_k_produccion(filas):
    """§8.1: K del arnés = data/ (el arnés marca k_difiere_de_guardado y la re-corrida en el codigo_sha del record
    guardado; una diferencia no reproducida en su sha es falla), y el predicado del evaluador da la misma publicación
    de K que el del runner. Una fila ok sin el campo k_difiere_de_guardado es falla: no se comparó (VF4-03)."""
    sin_campo = [(f["vol"], f["dt"]) for f in filas if f.get("estado") == "ok" and "k_difiere_de_guardado" not in f]
    sin_explicar = [(f["vol"], f["dt"]) for f in filas if f.get("estado") == "ok" and f.get("k_difiere_de_guardado")
                    and not f.get("k_reproducida_en_su_sha")]
    distinto = [(f["vol"], f["dt"]) for f in _ev(filas) if _pub(f, "K") != int((f.get("pub_runner") or {}).get("K") or 0)]
    return {"estado": "OK" if not sin_campo and not sin_explicar and not distinto else "INDECIDIBLE",
            "sin_campo": sin_campo[:20], "n_sin_campo": len(sin_campo), "sin_explicar": sin_explicar[:20],
            "predicado_distinto_del_runner": distinto[:20]}


# ------------------------------------------------------------------ veredicto (§7)
def _rojo(c):
    return (c if isinstance(c, str) else c.get("estado")) != "OK"


def veredicto(res):
    """§7, primera fila que se cumpla, sobre el brazo elegido por la regla de posición."""
    if any(_rojo(c) for c in res["controles"].values()):
        return "INDECIDIBLE"
    b = res.get("posicion_elegida")
    if b is None:
        return "NO ADOPTAR"
    x = res["brazos"][b]
    if x["p1"]["estado"] == "VETADO":
        return "NO ADOPTAR"
    est = {x["p2"]["estado"], x["p2l_vs_K"]["estado"]}
    if "PIERDE" in est:
        return "NO ADOPTAR"
    if "SIN SUSTRATO" in est:
        return "INDECIDIBLE"
    prot_k = res["controles"]["cobertura"].get("protegidas_k_fuera") or []
    if ("BLOQUEA" in est or x["p1"]["estado"] == "SOLO OCR" or x["p1b"]["decide"] or x["m"]["regla"] == "EMPEORA"
            or prot_k or res.get("protegidas_que_otra_posicion_publica")):
        return "DECIDE NICOLÁS"
    if est <= {"GANA", "EMPATE"}:
        return "PROPONER ADOPCIÓN"
    return "INDECIDIBLE"


def _evaluar(filas, esperadas, ident, externos, sin_pasada_nuestra, predicado, n_grillas_censo):
    for f in filas:
        f["_evaluable"], f["_motivo"] = evaluable(f)
    armar_tabla(filas, predicado)
    ctl = {"k_produccion": control_k_produccion(filas), "identidad": control_identidad(ident, filas, n_grillas_censo),
           "marca": control_marca(filas), "placebo": control_placebo(filas),
           "contador": control_contador(filas, predicado),
           "cobertura": control_cobertura(filas, esperadas, sin_pasada_nuestra, predicado),
           "posicion": control_posicion(filas), "predicado_distance_class": control_predicado(predicado),
           "evaluar_d25": {"estado": "OK" if blob(D25_RUTA) == D25_BLOB else "INDECIDIBLE", "blob": blob(D25_RUTA)}}
    for k in EXTERNOS_REQUERIDOS:
        ctl[k] = externos.get(k) or {"estado": "INDECIDIBLE", "motivo": "control externo ausente"}
    res = {"controles": ctl, "brazos": {}}
    for b in BRAZOS_V:
        res["brazos"][b] = {"p1": p1(filas, b), "p1b": p1b(filas, b), "p2": p2(filas, b),
                            "p2l_vs_K": p2(filas, b, "K", lejana=True), "m": m(filas, b),
                            "p2_union": {k: v for k, v in p2(filas, b, union=True).items() if k != "discordantes"},
                            "razon_protegidas": razon_protegidas(filas, b), "curva_cenit": curva_cenit(filas, b),
                            "curva_misma_noche": curva_misma_noche(filas, b)}
        if b != "V":
            res["brazos"][b]["p1_vs_V"] = p1(filas, b, "V")
            res["brazos"][b]["p2l_vs_V"] = p2(filas, b, "V", lejana=True)
    res["curva_cenit_K"] = curva_cenit(filas, "K")
    res["curva_misma_noche_K"] = curva_misma_noche(filas, "K")
    res["posicion_elegida"], res["posicion_motivo"] = regla_posicion(res)
    res["descriptivas_posicion"] = descriptivas_posicion(filas)
    bc = res["posicion_elegida"] or "V"
    # VF4-01: una protegida que otra regla de posición publica y la elegida no, no se cambia en silencio (§7, fila 5)
    res["protegidas_que_otra_posicion_publica"] = sorted({(x["vol"], x["dt"]) for o in BRAZOS_V if o != bc
                                                         for x in p1(filas, bc, o)["perdidas"]})
    res["chillan"] = chillan(filas, bc)
    res["chillan_por_tramo"] = chillan_por_tramo(filas, bc)
    res["por_tramo"] = {t: {"p2": p2([f for f in filas if f.get("tramo") == t], bc)["estado"]} for t in ("C", "E")
                        if any(f.get("tramo") == t for f in filas)}
    res["veredicto"] = veredicto(res)
    return res


def evaluar(filas, esperadas, ident, externos, sin_pasada_nuestra=None, predicado=predicado_node,
            n_grillas_censo=None):
    """El veredicto del §7, con el protocolo del tramo E: si la cobertura queda en rojo sólo por pasadas del tramo E,
    E se excluye entero en todos los brazos (filas, esperadas y pasadas de MIROVA sin pasada nuestra) y se evalúa C
    solo; el resultado lo declara en `e_excluido`. Un rojo que toca C deja todo INDECIDIBLE."""
    res = _evaluar(filas, esperadas, ident, externos, sin_pasada_nuestra, predicado, n_grillas_censo)
    if rojo_solo_en_e(res["controles"]["cobertura"]):
        motivo = {k: res["controles"]["cobertura"][k] for k in ("repetidas", "faltan", "sobran", "fallas",
                                                                "sin_pasada_nuestra")}
        res = _evaluar([f for f in filas if not _es_e(f["dt"])], [k for k in esperadas if not _es_e(k[1])], ident,
                       externos, [x for x in sin_pasada_nuestra if not _es_e(x[1])], predicado, n_grillas_censo)
        res["e_excluido"] = motivo
    else:
        res["e_excluido"] = None
    return res


# ------------------------------------------------------------------ E/S
def cargar(art):
    filas, cab = [], []
    for p in sorted(glob.glob(str(Path(art) / "**" / "f4_parte*.jsonl"), recursive=True)):
        for x in open(p, encoding="utf-8"):
            r = json.loads(x)
            (cab if r.get("tipo") == "cabecera" else filas if r.get("tipo") == "record" else []).append(r)
    return filas, cab


def main(argv=None, predicado=predicado_node):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True)
    ap.add_argument("--poblacion", required=True, help="poblacion_f4.json (C y E, etiquetas con la referencia congelada)")
    ap.add_argument("--identidad", required=True, help="identidad.json de identidad_f4.py")
    ap.add_argument("--externos", required=True, help="externos.json con los controles del candado")
    ap.add_argument("--salida", default=None)
    a = ap.parse_args(argv)
    pob = json.load(open(a.poblacion, encoding="utf-8"))
    filas, _cab = cargar(a.art)
    por = {(p["vol"], p["dt"]): p for p in pob["pasadas"]}
    for f in filas:
        f.update({k: v for k, v in por.get((f["vol"], f["dt"]), {}).items() if k not in f})
    idn = json.load(open(a.identidad, encoding="utf-8"))
    ident = {(x["vol"], x["dt"]): x for x in idn["pasadas"]}
    res = evaluar(filas, list(por), ident, json.load(open(a.externos, encoding="utf-8")),
                  pob.get("sin_pasada_nuestra"), predicado)
    print("VEREDICTO:", res["veredicto"], "| posición:", res["posicion_elegida"], "(%s)" % res["posicion_motivo"],
          "| tramo E excluido:", bool(res["e_excluido"]))
    for k, c in res["controles"].items():
        print("  control %-26s %s" % (k, c if isinstance(c, str) else c.get("estado")))
    for b, x in res["brazos"].items():
        print("  %-10s P1 %s | P1b %d | P2 %s neto %s B %s | P2' %s neto %s | M %s n %s | razón %s" % (
            b, x["p1"]["estado"], len(x["p1b"]["decide"]), x["p2"]["estado"], x["p2"]["neto"], x["p2"]["B"],
            x["p2l_vs_K"]["estado"], x["p2l_vs_K"]["neto"], x["m"]["regla"], x["m"]["n"],
            x["razon_protegidas"]["mediana"]))
    print("  Chillán:", {k: res["chillan"][k] for k in ("estado", "brazo", "n_pares", "b_mas_cerca", "mediana_razon")})
    out = Path(a.salida) if a.salida else Path(a.art) / "resultado_f4.json"
    for f in filas:
        f.pop("_t", None)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("escrito", out)
    return res


if __name__ == "__main__":
    main()
