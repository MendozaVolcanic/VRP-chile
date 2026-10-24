# -*- coding: utf-8 -*-
"""S162, evaluador del A/B de MxD03 sobre K (tarea 1.30, D-19). Implementa las reglas del §6 y los controles del §8 del
pre-registro sellado (experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md, sello D-48). Escrito y probado ANTES de
correr el A/B (probar_evaluar_mxd03.py: 12 pruebas que fallan contra evaluar_vacio.py y pasan aqui, mas 5 mutaciones).

POR QUE CADA REGLA ES ASI (resumen; el detalle esta en el pre-registro):
- P1 veto: una protegida (alerta de MIROVA de 1 MW o mas, lectura A) que K publica y X no basta para NO CUMPLE. Es la
  regla 1 de MISSION y ningun ruido la absuelve: la fragilidad (en cuantas R tambien se pierde) se informa, no decide.
- P2 suma bajo 1 MW: S = alertas bajo 1 MW sin publicar + publicaciones en negativos limpios. Decide solo con cenit <=
  35 grados, donde el nulo R (el mismo corrimiento en km sin informacion de direccion) es comparable; ruido = el segundo
  mayor |S(Rk) - S(K)| de 20 (percentil 95 de 20 semillas, elegido). Sobre 35 grados y sin Cordon Caulle se informa.
  Las mitades de pasada partida cuya hermana es sin_info no entran (un cambio ahi es invisible para MIROVA): van a P6.
- Si R no movio ningun cumulo publicado mas de 0,5 km, el nulo no puede ver un borde: P2 INDECIDIBLE (control 2).
- M (magnitud) SOLO INFORMA (§6, H2): d = |log10(X/MIROVA)| - |log10(K/MIROVA)| con el intervalo de regla_m de
  evaluar_d25.py por bloques noche-volcan, y g = mediana de X/K. El comparador d' de D-28 (comparar_con_ganancia) no
  esta en main: d' se da como estimacion puntual sin intervalo (lo preve el §8).
- La vara VIIRS (P3) solo DETIENE (INTERP MAS CERCA con el mismo signo en Terra y Aqua); se calcula aparte
  (vara_mxd03.py) y entra aqui como su estado. Sin vara el veredicto no puede ser CUMPLE SIN DAÑO.

Las dos preguntas del instrumento:
1. Si X no cambiara nada, ¿se veria? Si: P1 y P2 darian 0 y el control 8 (hash de grilla) acusaria la grilla igual.
2. Si el arnes estuviera roto, ¿se veria distinto de «sin dano»? Si: K2 != K, K del arnes != data/ sin reproducir en su
   codigo_sha, R que no mueve nada, un granulo faltante o el control de geometria fuera de 2,581 +- 0,05 km dan
   INDECIDIBLE o INCOMPLETO, nunca CUMPLE.

Uso: python evaluar_mxd03.py --art DIR_ARTEFACTOS [--vara vara_resultado.json] [--ref DIR_REF]
"""
import argparse
import collections
import glob
import hashlib
import importlib.util
import io
import json
import math
import statistics
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))

TOL_S = 120                     # §5, pareo fijo (el del verificador del pareo)
CENIT_P2 = 35.0                 # §3 y §6: corte propio (tarea 1.23)
N_NULOS = 20
NULOS = tuple("R%02d" % k for k in range(N_NULOS))
MUEVE_R_KM = 0.5                # §8 control 2
MOV_KM = 0.01                   # P4
TOL_MODULO_KM = 0.010           # §8 control 2: modulo aplicado igual al pedido a 10 m
UMBRAL_RESTO = 0.98             # §8 control 4, en el resto (heredado de F/K, elegido)
MIN_SHA_ESTRATO = 50            # lectura propia del «estratificado por codigo_sha»: los sha con 50 records o mas
CONTROL_S151_KM = (2.581, 0.05)
CC = "PuyehueCordonCaulle"


def _d25():
    spec = importlib.util.spec_from_file_location("evaluar_d25", RAIZ / "experiments/_s157_prereg_d25/evaluar_d25.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ pareo
def pareadas(lista, t):
    """Filas de referencia a +-TOL_S de t (banco_paridad.parear, importado; TOL_S se lee al llamar)."""
    import banco_paridad as bp
    return bp.parear(lista, t, TOL_S)


# ------------------------------------------------------------------ P1
def _ok(f):
    return f.get("estado") == "ok"


def p1(filas):
    perdidas = []
    for f in filas:
        if _ok(f) and f["lab"] == "protegida" and f["pub"]["K"] == 1 and f["pub"]["X"] == 0:
            frag = sum(1 for b in NULOS if f["pub"].get(b) == 0) if f.get("r_nulos") else None
            perdidas.append({"vol": f["vol"], "dt": f["dt"], "z": f["z"], "fragilidad": frag,
                             "vrp_k": (f["brazos"]["K"] or {}).get("pc_vrp"), "vrp_mirova": f.get("vrp_mirova")})
    return {"estado": "VETADO" if perdidas else "SIN PERDIDA", "perdidas": perdidas,
            "n_protegidas_k": sum(1 for f in filas if _ok(f) and f["lab"] == "protegida" and f["pub"]["K"] == 1)}


def p1b(filas):
    out = []
    for f in filas:
        if not (_ok(f) and f["lab"] == "protegida" and f["pub"]["K"] == 1 and f["pub"]["X"] == 1):
            continue
        vk, vx = (f["brazos"]["K"] or {}).get("pc_vrp"), (f["brazos"]["X"] or {}).get("pc_vrp")
        if vk is not None and vk >= 1.0 and (vx is None or vx < 1.0):
            out.append({"vol": f["vol"], "dt": f["dt"], "vrp_k": vk, "vrp_x": vx, "vrp_mirova": f.get("vrp_mirova")})
    return out


# ------------------------------------------------------------------ P2
def _invisible(f):
    return bool(f.get("partida")) and "sin_info" in (f.get("hermanos_lab") or [])


def _base_p2(filas):
    return [f for f in filas if _ok(f) and f["lab"] in ("bajo1", "neg_limpio") and not _invisible(f)]


def filas_p2(filas):
    """Las que deciden P2: cenit <= 35 grados."""
    return [f for f in _base_p2(filas) if f["z"] is not None and f["z"] <= CENIT_P2]


def saldo(fs, b):
    return (sum(1 for f in fs if f["lab"] == "bajo1" and f["pub"].get(b, f["pub"]["K"]) == 0)
            + sum(1 for f in fs if f["lab"] == "neg_limpio" and f["pub"].get(b, f["pub"]["K"]) == 1))


def ruido_p2(dr):
    a = sorted((abs(x) for x in dr), reverse=True)
    return a[1] if len(a) > 1 else (a[0] if a else 0)


def regla_p2(dx, dr, r_vivo):
    if not r_vivo:
        return "INDECIDIBLE"
    ruido = ruido_p2(dr)
    return "GANA" if dx < -ruido else ("PIERDE" if dx > ruido else "EMPATE")


def _dist_km(a, b):
    if not a or not b or a.get("pc_lat") is None or b.get("pc_lat") is None:
        return None
    dn = (a["pc_lat"] - b["pc_lat"]) * 111.32
    de = (a["pc_lon"] - b["pc_lon"]) * 111.32 * math.cos(math.radians(a["pc_lat"]))
    return math.hypot(dn, de)


def r_vivo(filas):
    """§8 control 2: en el censo <= 35, al menos un cumulo publicado de alguna Rk se mueve mas de 0,5 km respecto de K."""
    for f in filas:
        if not (_ok(f) and f.get("r_nulos")):
            continue
        for b in NULOS:
            if f["pub"].get(b) == 1:
                d = _dist_km(f["brazos"].get(b), f["brazos"].get("K"))
                if d is not None and d > MUEVE_R_KM:
                    return True
    return False


def _p2_sobre(fs, filas_vivo):
    sk = saldo(fs, "K")
    dx = saldo(fs, "X") - sk
    dr = [saldo(fs, b) - sk for b in NULOS]
    vivo = r_vivo(filas_vivo)
    return {"estado": regla_p2(dx, dr, vivo), "delta_x": dx, "delta_r": dr, "ruido": ruido_p2(dr), "r_vivo": vivo,
            "s_k": sk, "n": len(fs), "rango_x": sum(1 for x in dr if x < dx)}


def p2(filas):
    return _p2_sobre(filas_p2(filas), filas)


def _cambios(fs):
    return [{"vol": f["vol"], "dt": f["dt"], "lab": f["lab"], "z": f["z"], "pub_k": f["pub"]["K"],
             "pub_x": f["pub"]["X"]} for f in fs if f["pub"]["K"] != f["pub"]["X"]]


def p2_informe(filas):
    sobre = [f for f in _base_p2(filas) if f["z"] is None or f["z"] > CENIT_P2]
    sk = saldo(sobre, "K")
    sin_cc = [f for f in filas if f["vol"] != CC]
    sin_cc_sobre = [f for f in sobre if f["vol"] != CC]
    return {"sobre35": {"delta_x": saldo(sobre, "X") - sk, "s_k": sk, "n": len(sobre), "cambios": _cambios(sobre)},
            "sin_cc_le35": _p2_sobre(filas_p2(sin_cc), sin_cc),
            "sin_cc_sobre35": {"delta_x": saldo(sin_cc_sobre, "X") - saldo(sin_cc_sobre, "K"), "n": len(sin_cc_sobre)}}


# ------------------------------------------------------------------ P4, P5, P6
def p4(filas):
    mov, dc = [], []
    for f in filas:
        if not _ok(f):
            continue
        k, x = f["brazos"].get("K"), f["brazos"].get("X")
        d = _dist_km(k, x)
        if d is not None and d > MOV_KM:
            mov.append({"vol": f["vol"], "dt": f["dt"], "lab": f["lab"], "km": round(d, 3)})
        if (k or {}).get("dc") != (x or {}).get("dc"):
            dc.append({"vol": f["vol"], "dt": f["dt"], "lab": f["lab"], "dc_k": (k or {}).get("dc"),
                       "dc_x": (x or {}).get("dc")})
    prot = sorted({(m["vol"], m["dt"]) for m in mov + dc if m["lab"] == "protegida"})
    return {"n_movidos": len(mov), "cambios_dc": dc, "auditoria_a61_requerida": bool(prot), "protegidas": prot}


def p5(filas):
    out = []
    for f in filas:
        a = f.get("atribucion")
        if _ok(f) and a:
            out.append({"vol": f["vol"], "dt": f["dt"], "lab": f["lab"], "pub_k": f["pub"]["K"], "pub_x": f["pub"]["X"],
                        "pub_x_fondo": a["X_fondo"]["pub"], "pub_x_det": a["X_det"]["pub"],
                        "identidades": [a.get("XF_id_igual_K"), a.get("XD_id_igual_X")]})
    return out


def p6(filas):
    return [{"vol": f["vol"], "dt": f["dt"], "lab": f["lab"], "partida": bool(f.get("partida")),
             "pub_k": f["pub"]["K"], "pub_x": f["pub"]["X"]}
            for f in filas if _ok(f) and f["pub"]["K"] != f["pub"]["X"]
            and (f["lab"] in ("sin_info", "far_ref") or _invisible(f))]


# ------------------------------------------------------------------ M (solo informa)
def m_informa(filas):
    pares = []
    for f in filas:
        if not (_ok(f) and f["lab"] in ("protegida", "bajo1") and f["pub"]["K"] == 1 and f["pub"]["X"] == 1):
            continue
        vk, vx, vm = (f["brazos"]["K"] or {}).get("pc_vrp"), (f["brazos"]["X"] or {}).get("pc_vrp"), f.get("vrp_mirova")
        if vk and vx and vm and vk > 0 and vx > 0 and vm > 0:
            pares.append((f, vk, vx, vm))
    if not pares:
        return {"n": 0, "regla_d": "SIN PARES", "g": None}
    D = _d25()
    d = [abs(math.log10(vx / vm)) - abs(math.log10(vk / vm)) for _, vk, vx, vm in pares]
    g = statistics.median(vx / vk for _, vk, vx, _ in pares)
    dp = [abs(math.log10(vx / vm)) - abs(math.log10(g * vk / vm)) for _, vk, vx, vm in pares]
    bloques = ["%s|%s" % (f["vol"], f["dt"][:10]) for f, *_ in pares]
    W = D.pesos_bloque(bloques)
    regla, lo, hi = D.regla_m(d, W)
    por_vol = collections.defaultdict(list)
    for (f, vk, vx, vm), x in zip(pares, d):
        por_vol[f["vol"]].append(x)
    return {"n": len(pares), "regla_d": regla, "ic_d": [lo, hi], "mediana_d": statistics.median(d), "g": g,
            "mediana_d_prima": statistics.median(dp), "d_prima_sin_intervalo": True,
            "por_volcan": {v: {"n": len(x), "mediana_d": statistics.median(x)} for v, x in por_vol.items() if len(x) >= 3}}


# ------------------------------------------------------------------ vara (solo detiene)
def regla_vara(terra, aqua):
    """Estado de la lectura 3 de la vara VIIRS por satelite (MXD03 MAS CERCA / INTERP MAS CERCA / otro)."""
    if terra == aqua == "INTERP MAS CERCA":
        return "DETIENE"
    if {terra, aqua} == {"INTERP MAS CERCA", "MXD03 MAS CERCA"}:
        return "SESGO POR SATELITE"
    return "NO DETIENE"


def vara_desde_estado(estado):
    """El estado de evaluar_sola.vara (lectura 3, 1.23) ya exige el mismo signo en los dos satelites para decir
    INTERP MAS CERCA; con signos opuestos da SESGO POR SATELITE. SIN VARA, INDECIDIBLE y MXD03 MAS CERCA no detienen."""
    if estado == "INTERP MAS CERCA":
        return "DETIENE"
    return "SESGO POR SATELITE" if estado == "SESGO POR SATELITE" else "NO DETIENE"


# ------------------------------------------------------------------ controles
def control_k2(filas):
    return "OK" if all(f.get("k2_igual") for f in filas if _ok(f)) else "INDECIDIBLE"


def control_arnes(filas, recorridos):
    """§8 control 4: sin tolerancia donde decide (re-corrida en su codigo_sha); 98 % en el resto, por codigo_sha."""
    rc = {(r["vol"], r["dt"]): r for r in recorridos}
    deriva, no_rep = [], []
    for f in filas:
        if _ok(f) and f.get("decide") and f.get("k_difiere_de_guardado"):
            r = rc.get((f["vol"], f["dt"]))
            (deriva if r and r.get("estado") == "deriva_de_version" else no_rep).append(
                {"vol": f["vol"], "dt": f["dt"], "lab": f["lab"], "codigo_sha": f.get("codigo_sha"),
                 "recorrida": None if r is None else r.get("estado")})
    resto = [f for f in filas if _ok(f) and not f.get("decide")]
    por_sha = collections.defaultdict(lambda: [0, 0])
    for f in resto:
        por_sha[(f.get("codigo_sha") or "?")[:9]][0] += 1
        por_sha[(f.get("codigo_sha") or "?")[:9]][1] += int(not f.get("k_difiere_de_guardado"))
    frac_total = (sum(v[1] for v in por_sha.values()) / max(1, sum(v[0] for v in por_sha.values())))
    malos = {s: v for s, v in por_sha.items() if v[0] >= MIN_SHA_ESTRATO and v[1] / v[0] < UMBRAL_RESTO}
    estado = "INDECIDIBLE" if (no_rep or frac_total < UMBRAL_RESTO or malos) else "OK"
    return {"estado": estado, "deriva": deriva, "no_reproduce": no_rep, "resto_frac": frac_total,
            "por_sha": {s: {"n": v[0], "iguales": v[1]} for s, v in por_sha.items()}, "sha_bajo_umbral": malos}


def control_cobertura(filas, esperadas):
    vistos = {(f["vol"], f["dt"]) for f in filas if _ok(f)}
    faltan = [e for e in esperadas if tuple(e) not in vistos]
    nones = collections.Counter()
    for f in filas:
        if _ok(f):
            for b, r in f["brazos"].items():
                nones[b] += int(r is None)
    return {"estado": "OK" if not faltan else "INCOMPLETO", "faltan": faltan,
            "none_por_brazo": {b: n for b, n in nones.items() if n}}


def control_r_modulo(filas):
    malos = []
    for f in filas:
        if _ok(f) and f.get("r_nulos"):
            ns = f.get("nulos") or []
            ang = sorted(n["angulo_grados"] for n in ns)
            sep = [(b - a) % 360 for a, b in zip(ang, ang[1:] + ang[:1])] if ang else []
            if (len(ns) != N_NULOS or any(abs(n["km_aplicado"] - n["km_pedido"]) > TOL_MODULO_KM for n in ns)
                    or any(abs(s - 360.0 / N_NULOS) > 1e-3 for s in sep)):
                malos.append((f["vol"], f["dt"]))
    return {"estado": "OK" if not malos else "INDECIDIBLE", "malos": malos[:20], "n_malos": len(malos)}


def control_geometria(filas):
    """§8 control 1: S151 en su granulo (hacia el sensor 2,581 +- 0,05 km) y el nulo _interp_geo contra si misma = 0."""
    ctl = [f["control_s151"] for f in filas if _ok(f) and f.get("control_s151")]
    nulo_max = max((f.get("nulo_geo_crater_km") or 0.0 for f in filas if _ok(f)), default=None)
    pos_ok = bool(ctl) and abs(ctl[0]["obs_hacia_sensor_km"] - CONTROL_S151_KM[0]) <= CONTROL_S151_KM[1]
    nulo_ok = nulo_max is not None and nulo_max <= 1e-6
    return {"estado": "OK" if pos_ok and nulo_ok else "INDECIDIBLE", "control_s151": ctl[:1], "nulo_max_km": nulo_max}


def control_cableado(filas):
    """§8 control 8: X con grilla distinta de K donde hay corrimiento; cada nulo con grilla propia."""
    malos = []
    for f in filas:
        if not _ok(f):
            continue
        h = f.get("hash_grilla") or {}
        if (f.get("desplazamiento") or {}).get("km", 0) > 0.01 and h.get("X") == h.get("K"):
            malos.append((f["vol"], f["dt"], "X=K"))
        if f.get("r_nulos") and len({h.get(b) for b in NULOS} | {h.get("K")}) != N_NULOS + 1:
            malos.append((f["vol"], f["dt"], "nulos repetidos"))
    return {"estado": "OK" if not malos else "INDECIDIBLE", "malos": malos[:20], "n_malos": len(malos)}


# ------------------------------------------------------------------ evaluacion y veredicto
def evaluar_filas(filas, recorridos, vara=None, externos=None, esperadas=None):
    esperadas = [(f["vol"], f["dt"]) for f in filas] if esperadas is None else esperadas
    ctl = {"cobertura": control_cobertura(filas, esperadas), "k2": control_k2(filas),
           "arnes": control_arnes(filas, recorridos), "r_modulo": control_r_modulo(filas)}
    ctl.update(externos or {})
    return {"controles": ctl, "p1": p1(filas), "p1b": p1b(filas), "p2": p2(filas), "p2_informe": p2_informe(filas),
            "p4": p4(filas), "p5": p5(filas), "p6": p6(filas), "m": m_informa(filas), "vara": vara}


def _estado_ctl(c):
    return c if isinstance(c, str) else c.get("estado")


def veredicto(res):
    """Tabla del §10. M no entra (solo informa)."""
    ctl = res["controles"]
    if any(_estado_ctl(c) == "INDECIDIBLE" for c in ctl.values()):
        return "INDECIDIBLE"
    if _estado_ctl(ctl["cobertura"]) == "INCOMPLETO":
        return "INCOMPLETO"
    if res["p1"]["estado"] == "VETADO" or res["p2"]["estado"] == "PIERDE":
        return "NO CUMPLE"
    if res["p2"]["estado"] == "INDECIDIBLE":
        return "INDECIDIBLE"
    if res["vara"] == "DETIENE":
        return "DETENIDO POR LA VARA"
    if res["vara"] is None:
        return "PENDIENTE DE LA VARA"
    if res["p1b"] or res["p2_informe"]["sobre35"]["delta_x"] > 0:
        return "DECIDE NICOLÁS"
    return "CUMPLE SIN DAÑO"


# ------------------------------------------------------------------ E/S
def _sha256_lf(p):
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def cargar(art):
    filas, recorridos, cabeceras = [], [], []
    for p in sorted(glob.glob(str(Path(art) / "**" / "ab_parte*.jsonl"), recursive=True)):
        for x in open(p, encoding="utf-8"):
            r = json.loads(x)
            (cabeceras if r.get("tipo") == "cabecera" else filas if r.get("tipo") == "record" else []).append(r)
    for p in sorted(glob.glob(str(Path(art) / "**" / "recorridos_parte*.jsonl"), recursive=True)):
        recorridos += [json.loads(x) for x in open(p, encoding="utf-8")]
    return filas, recorridos, cabeceras


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True)
    ap.add_argument("--poblacion", default=str(AQUI / "poblacion.json"))
    ap.add_argument("--vara", default=None, help="vara_resultado.json de vara_mxd03.py --evaluar")
    ap.add_argument("--ref", default=None, help="carpeta con los CSV congelados: verifica su sha256 contra MANIFIESTO")
    a = ap.parse_args()
    pob = json.load(open(a.poblacion, encoding="utf-8"))
    externos = {}
    if pob.get("tol_s") != TOL_S:
        externos["pareo"] = {"estado": "INDECIDIBLE", "tol_poblacion": pob.get("tol_s")}
    if a.ref:
        mal = {n: _sha256_lf(Path(a.ref) / n) for n, v in pob["referencia"].items()
               if _sha256_lf(Path(a.ref) / n) != v["sha256_lf"]}
        externos["referencia"] = {"estado": "INDECIDIBLE" if mal else "OK", "distintos": mal}
    crudas, recorridos, cab = cargar(a.art)
    commits = sorted({c.get("commit") for c in cab})
    externos["procedencia"] = {"estado": "OK" if len(commits) == 1 else "INDECIDIBLE", "commits": commits,
                               "partes": sorted(c.get("parte") for c in cab)}
    pobf = {(f["vol"], f["dt"]): f for g in pob["granulos"] for f in g["records"]}
    filas, distintas = [], []
    for r in crudas:
        # la etiqueta, el cenit y las marcas de la poblacion congelada mandan sobre lo que repite el arnes
        pf = pobf.get((r.get("vol"), r.get("dt")), {})
        if pf and r.get("estado") == "ok" and any(r.get(k) != pf.get(k) for k in ("lab", "z", "r_nulos")):
            distintas.append((r.get("vol"), r.get("dt")))
        base = dict(r)
        base.update(pf)
        filas.append(base)
    externos["union"] = {"estado": "INDECIDIBLE" if distintas else "OK", "distintas": distintas[:20],
                         "sin_poblacion": sum(1 for r in crudas if (r.get("vol"), r.get("dt")) not in pobf)}
    if externos["union"]["sin_poblacion"]:
        externos["union"]["estado"] = "INDECIDIBLE"
    externos["geometria"] = control_geometria(filas)
    externos["cableado"] = control_cableado(filas)
    vara = None
    if a.vara:
        v = json.load(open(a.vara, encoding="utf-8"))
        vara = vara_desde_estado(v["estado"])
        externos["vara_cruda"] = {"estado": "OK", "estado_evaluar_sola": v["estado"]}
    res = evaluar_filas(filas, recorridos, vara=vara, externos=externos, esperadas=list(pobf))
    res["veredicto"] = veredicto(res)
    print("VEREDICTO:", res["veredicto"])
    for k, c in res["controles"].items():
        print("  control %-12s %s" % (k, _estado_ctl(c)))
    print("  P1:", res["p1"]["estado"], res["p1"]["perdidas"])
    print("  P1b:", res["p1b"])
    print("  P2 (<= 35):", {k: res["p2"][k] for k in ("estado", "delta_x", "ruido", "rango_x", "n", "s_k")})
    print("  P2 sobre 35 (informa):", {k: v for k, v in res["p2_informe"]["sobre35"].items() if k != "cambios"})
    print("  P2 sin Cordon Caulle <= 35 (informa):",
          {k: res["p2_informe"]["sin_cc_le35"][k] for k in ("estado", "delta_x", "ruido")})
    print("  P4:", {k: v for k, v in res["p4"].items() if k != "cambios_dc"}, "cambios de clase:", len(res["p4"]["cambios_dc"]))
    print("  P5 (atribucion):", len(res["p5"]), "pasadas | P6 (fuera del censo decisor):", len(res["p6"]))
    print("  M (informa):", {k: v for k, v in res["m"].items() if k != "por_volcan"})
    print("  vara:", res["vara"])
    out = Path(a.art) / "resultado_mxd03.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("escrito", out)


if __name__ == "__main__":
    main()
