# -*- coding: utf-8 -*-
"""S162 V375-B y V375-C, evaluador: controles primero (PREREGISTRO_B.md §4 y PREREGISTRO_C.md §4), después las
lecturas. Sólo lectura.

QUÉ MIDE. Para cada pasada VIIRS 375 de la unión de los lotes S159 (experiments/_s159/portes/, grillas guardadas) y
S162 (objetivos_v375_bc.json), y para cada brazo de ROI de brazos.py: si el código de MIROVA, portado a 375, PUBLICARÍA
en nuestro tablero, con qué magnitud, y cómo se compara con lo que MIROVA publicó (la vara, A115) y con producción (K).

«Publica» = el predicado del tablero ejecutado con node desde frontend/index.html (banco_paridad.correr_node) sobre un
record sintético del brazo: vrp_mw = primary_cluster.vrp_mw = f5_core_vrp_mw = VRP del código (la suma de todos los
alertados de la ventana, como el .m), t_max_k = temperatura MIR del alertado más radiante, y distance_class «summit» si
la distancia de la regla está a inner_radius_km o menos del punto de referencia de MIROVA (X0, Y0). Dos reglas de
distancia: «cercano» (DECIDE: el alertado más cercano; MIROVA informa el píxel cercano aunque haya uno lejano más
brillante, verificador de S159 V-2) y «centroide» (la de S159, informa; con ella 3 de las 6 «perdidas» de S159 eran
artefacto del centroide, V-2 y V-5).

Las dos preguntas del instrumento. (1) Si el port no publicara nunca, el brazo de control NUNCA lo mostraría: recall 0
y todas las protegidas perdidas; si los brazos fueran todos el mismo, el nulo M14 contra M14 y el de PLACEBO lo
mostrarían con 0 discordantes. Los controles se leen antes que cualquier lectura y, si uno falla, el veredicto es
INVALIDO POR INSTRUMENTO. (2) Una pasada sin resultado es SIN DATO: no entra a ningún denominador y su estrato se
re-pondera; el conteo se imprime antes de cualquier número.
Uso: python -I evaluar.py --art162 <carpeta del run> --art159 D:\\vrp-trabajo\\temporales\\s159_portes\\run_39712862945
     [--cache cache_brazos.json] [--cobertura <archivo del instrumento>] [--protegida-crater <archivo de V375-A>]
     [--salida evaluar_salida.txt] [--json evaluar.json]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import math
import sys
from pathlib import Path

import numpy as np

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(AQUI))
import banco_paridad as B  # noqa: E402
import brazos as BR  # noqa: E402

EXCLUIDOS = ("2026-10-12", "2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20")
CONTROLES = ("NUNCA", "PLACEBO")           # brazos virtuales del evaluador (§4 de los dos pre-registros)
FACTOR_PLACEBO = 1.2                       # programa §2: «placebo K x 1,2 obligatorio», aquí sobre M14
REGLAS = ("cercano", "centroide")
# PREREGISTRO_C.md §5.1: a igual ΔE contra K, gana la caja de cumbre más chica (la más conservadora con los negativos)
ORDEN_DESEMPATE = ("PIX7", "M13", "C13", "M14", "C14", "M21", "C21", "SENS_PT", "CIRC", "SENS")
REGLA_DECIDE = "cercano"
CLASES_NEG = ("neg_pub", "neg_resto")
SEMILLA = 162
N_BOOT = 2000
MAX_B_EXACTO = 20                          # D-45 §2.5
MAX_B_SIN_SUSTRATO = 4                     # D-45 §2.7
N_SORTEOS = 10000                          # D-45 §2.5
TOL = 1e-9
BANDA_M = (0.8, 1.25)
TOL_RECALCULO_MW = 1e-6
UMBRAL_K_RECORRIDO = 0.95                  # pre-registro de S159 §4.4, misma regla
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


# ---------------------------------------------------------------- estadística
def wilson(k, n, z=1.96):
    if n <= 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(max(p * (1 - p) / n + z * z / (4 * n * n), 0.0)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def kish(w):
    w = np.asarray(w, float)
    return float(w.sum() ** 2 / (w ** 2).sum()) if len(w) and (w ** 2).sum() > 0 else 0.0


def tasa_ponderada(filas, f, z=1.96):
    """(tasa ponderada, IC de Wilson sobre el n efectivo de Kish). Con pesos parejos es la Wilson cruda. `z` sólo cambia
    en la lectura estricta de V375-B2, que se informa y no decide."""
    w = np.array([x["w"] for x in filas], float)
    if not len(w):
        return float("nan"), (float("nan"), float("nan")), 0.0
    k = np.array([bool(f(x)) for x in filas], float)
    p = float((w * k).sum() / w.sum())
    ne = kish(w)
    return p, wilson(p * ne, ne, z), ne


def prueba_signos(sumas, neto, n_sorteos=N_SORTEOS, semilla=SEMILLA):
    """D-45 §2.3 a §2.5 (experiments/_s157_prereg_d25/evaluar_d25.py::prueba_signos_p2 en el tag s161-d25-lectura),
    llevada a sumas de bloque REALES: aquí cada pasada lleva el peso de su estrato (la muestra es estratificada), así que
    la suma de un bloque noche-volcán no es entera. El nulo es el mismo: cada bloque entero cambia de signo con
    probabilidad 1/2. Exacto con B de 20 o menos (los 2^B repartos, por convolución sobre un arreglo); con más, 10.000
    sorteos con la semilla 162 y valor-p (1 + m) / (1 + 10.000). Las comparaciones de suma usan una tolerancia de 1e-9
    (la suma de reales no es exacta). Con sumas enteras da lo mismo que la función sellada (probar_evaluar.py)."""
    s = np.asarray(sumas, float)
    Bn = len(s)
    if Bn <= MAX_B_EXACTO:
        tot = np.zeros(1)
        for x in s:
            tot = np.concatenate([tot + x, tot - x])
        den = 2 ** Bn
        return {"metodo": "exacto", "gana": [int((tot <= neto + TOL).sum()), den],
                "pierde": [int((tot >= neto - TOL).sum()), den],
                "dos_colas": [int((np.abs(tot) >= abs(neto) - TOL).sum()), den]}
    rng = np.random.default_rng(semilla)
    S = rng.choice((-1.0, 1.0), size=(n_sorteos, Bn))
    tot = S @ s
    den = n_sorteos + 1
    return {"metodo": "sorteos", "gana": [1 + int((tot <= neto + TOL).sum()), den],
            "pierde": [1 + int((tot >= neto - TOL).sum()), den],
            "dos_colas": [1 + int((np.abs(tot) >= abs(neto) - TOL).sum()), den]}


def regla_signos(neto, Bn, p):
    """D-45 §2.6 y §2.7 (regla_signos_p2 del tag s161-d25-lectura): SIN SUSTRATO con 4 bloques o menos; GANA si el neto
    es negativo y su valor-p es 5 % o menos; PIERDE si es positivo y su valor-p es 5 % o menos; BLOQUEA si es positivo
    sin llegar; EMPATE si es 0 o negativo sin llegar. El neto cuenta ERRORES del brazo menos los de la referencia."""
    if Bn <= MAX_B_SIN_SUSTRATO:
        return "SIN SUSTRATO"
    if neto < -TOL and 20 * p["gana"][0] <= p["gana"][1]:
        return "GANA"
    if neto > TOL and 20 * p["pierde"][0] <= p["pierde"][1]:
        return "PIERDE"
    if neto > TOL:
        return "BLOQUEA"
    return "EMPATE"


def boot_estrat(filas, est, rng, n=N_BOOT):
    """Bootstrap estratificado por clase y estrato volcán x cenit (el diseño de la muestra)."""
    por = collections.defaultdict(list)
    for x in filas:
        por[(x["c"], x["h"])].append(x)
    vals = []
    for _ in range(n):
        s = []
        for lst in por.values():
            s += [lst[k] for k in rng.integers(0, len(lst), len(lst))]
        v = est(s)
        if not (isinstance(v, float) and math.isnan(v)):
            vals.append(v)
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) if vals else (float("nan"),) * 2


# ---------------------------------------------------------------- record sintético
def dist_regla(p, g, regla):
    px = p["pixeles"]
    if regla == "cercano":
        return float(min(q[3] for q in px))
    fr, fc = np.mean([q[0] for q in px]), np.mean([q[1] for q in px])
    x = g["ul_x"] + g["celda"] * (fc + 0.5)
    y = g["ul_y"] - g["celda"] * (fr + 0.5)
    return float(np.hypot(x - g["X0"], y - g["Y0"]) / 1000.0)


def record_sintetico(p, g, inner, sensor, regla, factor=1.0):
    if not p or not p.get("npix") or p.get("vrp_mw") is None:
        return {"sensor": sensor, "vrp_mw": 0.0, "primary_cluster": None, "distance_class": None,
                "anomaly_pixels": []}
    d = dist_regla(p, g, regla)
    v = round(float(p["vrp_mw"]) * factor, 4)
    return {"sensor": sensor, "vrp_mw": v, "f5_core_vrp_mw": v, "t_max_k": max(q[5] for q in p["pixeles"]),
            "triggered_test1": False, "distance_class": "summit" if d <= inner else "far",
            "primary_cluster": {"vrp_mw": v, "n_pixels": p["npix"], "centroid_dist_km": round(d, 3)},
            "anomaly_pixels": []}


def slim(rec):
    s = {k: rec.get(k) for k in B.CAMPOS_JS}
    if s.get("anomaly_pixels") is None:
        s["anomaly_pixels"] = []
    return s


# ---------------------------------------------------------------- carga
def volcanes():
    import yaml
    d = yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))
    lst = d["volcanoes"] if isinstance(d, dict) else d
    return {v["name"]: v for v in lst}


def tramo(h):
    d = h[:10]
    return "T" if d < "2026-06-13" else ("O1" if d < "2026-08-29" else "O2")


def leer_resultados(art, patron="resultados_VIIRS375_*.json"):
    res = {}
    if art is None:
        return res
    for f in sorted(Path(art).rglob(patron)):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok" or r["id"] not in res:
                res[r["id"]] = r
    return res


def grilla_npz(art, i):
    z = list(Path(art).rglob(f"grilla_{i:03d}.npz")) + list(Path(art).rglob(f"grilla_{i:04d}.npz"))
    z = sorted(set(z))
    if len(z) != 1:
        return None
    q = np.load(z[0])
    return q["mir"].astype(np.float64), q["tir"].astype(np.float64), hashlib.sha256(z[0].read_bytes()).hexdigest()


def recalcular(o, r, art, V, cache, brazos=BR.BRAZOS):
    """Los brazos recalculados sin red sobre la grilla guardada (con caché por sha256 de la grilla)."""
    g = grilla_npz(art, o["id"])
    if g is None:
        return None
    mir, tir, sha = g
    clave = f"{o['id']}|{sha}"
    if clave in cache and all(b in cache[clave] for b in brazos):
        return cache[clave]
    v = V[o["volcan"]]
    xc, yc = BR.crater_xy(o["grilla"], v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))
    out = BR.correr_brazos(mir, tir, o["grilla"], o["grilla"]["X0"], o["grilla"]["Y0"], xc, yc, v["inner_radius_km"],
                           o["volcan"], r["dayflag"], r["sunglint"], semillas=0, brazos=brazos)
    cache[clave] = out
    return out


def mismo(a, c):
    return a["npix"] == c["npix"] and ((a["vrp_mw"] is None and c["vrp_mw"] is None) or (
        a["vrp_mw"] is not None and c["vrp_mw"] is not None and abs(a["vrp_mw"] - c["vrp_mw"]) < TOL_RECALCULO_MW))


# ---------------------------------------------------------------- filas
def armar(obj, res, arms_por_id, inner, pub_k_rerun, vk_rerun, k_usa_recorrido, pesos):
    """Una fila por pasada ok con: clase, peso, estrato, publica y magnitud por (brazo, regla), y K."""
    filas = []
    for i, o in obj.items():
        if i not in arms_por_id or o["lote"] == "CTL":   # el control de vida no entra a ningún denominador
            continue
        r = res[i]
        z = (r.get("geometria_centro") or {}).get("sensor_zenith", o.get("z"))
        f = {"i": i, "lote": o["lote"], "c": o["clase"], "h": o["estrato"], "w": pesos[(o["clase"], o["estrato"])],
             "vol": o["volcan"], "hora": o["hora_utc"], "tramo": tramo(o["hora_utc"]), "z": z,
             "bloque": f"{o['volcan']}|{o['hora_utc'][:10]}", "prot": bool(o["protegida"]),
             "mir": float(o["mirova_vrp"] or 0.0), "tabla": bool(o.get("alerta_tabla")),
             "part": bool(o.get("partida")), "K": bool(pub_k_rerun[i]) if k_usa_recorrido else bool(o["pub_prod"]),
             "VK": vk_rerun.get(i), "X": {}, "V": {}, "npix": {}}
        for (b, regla), (pub, vdisp, npix) in arms_por_id[i].items():
            f["X"][(b, regla)] = pub
            f["V"][(b, regla)] = vdisp
            f["npix"][(b, regla)] = npix
        filas.append(f)
    return filas


def err(x, clave):
    """Error de la suma bajo 1 MW (MISSION, criterio de victoria punto 4): alerta bajo 1 MW sin publicar, o
    publicación en un negativo limpio. Las protegidas no entran aquí (las veta P1)."""
    pub = x["K"] if clave == "K" else x["X"][clave]
    return (x["c"] == "pos_bajo" and not pub) or (x["c"] in CLASES_NEG and pub)


def p2(filas, a, ref):
    """P2 por la prueba de signos por bloque noche-volcán (D-45) del brazo a contra la referencia ref."""
    blo = collections.defaultdict(float)
    for x in filas:
        ea, er = err(x, a), err(x, ref)
        if ea != er:
            blo[x["bloque"]] += x["w"] * (1 if ea else -1)
    sumas = [blo[k] for k in sorted(blo)]
    neto = float(sum(sumas))
    p = prueba_signos(sumas, neto)
    return {"neto": neto, "B": len(sumas), "p": p, "veredicto": regla_signos(neto, len(sumas), p)}


def delta_e(filas, a, ref):
    return sum(x["w"] * (int(err(x, a)) - int(err(x, ref))) for x in filas)


def publica(x, clave):
    return x["K"] if clave == "K" else x["X"][clave]


def lecturas(filas, a, rng, N_neg, tasa_k_neg):
    """Todas las lecturas de un brazo a = (brazo, regla)."""
    out = {}
    prot = [x for x in filas if x["c"] == "pos_prot"]
    bajo = [x for x in filas if x["c"] == "pos_bajo"]
    neg = [x for x in filas if x["c"] in CLASES_NEG]
    resto = [x for x in filas if x["c"] == "neg_resto"]
    npub = [x for x in filas if x["c"] == "neg_pub"]
    # P1: protegidas sin publicar
    perd = [x for x in prot if not x["X"][a]]
    out["P1"] = {"perdidas": len(perd), "de": len(prot),
                 "perdidas_que_K_publica": sum(1 for x in perd if x["K"]),
                 "perdidas_tabla": sum(1 for x in perd if x["tabla"]),
                 "ganadas_a_K": sum(1 for x in prot if x["X"][a] and not x["K"]),
                 "lista": [(x["vol"], x["hora"], "tabla" if x["tabla"] else "ocr", "K" if x["K"] else "-",
                            round(x["mir"], 3)) for x in perd]}
    # P1b: cruces de 1 MW en las dos direcciones (programa §2)
    baja = [x for x in prot if x["X"][a] and x["V"][a] < 1.0]
    sube = [x for x in filas if x["X"][a] and x["V"][a] >= 1.0 and not x["prot"]]
    out["P1b"] = {"baja": len(baja), "sube_crudo": len(sube), "sube_pond": sum(x["w"] for x in sube),
                  "sube_en_negativos": sum(1 for x in sube if x["c"] in CLASES_NEG),
                  "lista_baja": [(x["vol"], x["hora"], round(x["V"][a], 3), round(x["mir"], 3)) for x in baja][:20],
                  "lista_sube": [(x["vol"], x["hora"], x["c"], round(x["V"][a], 3), round(x["mir"], 3))
                                 for x in sube][:20]}
    # recall
    for nom, lst in (("prot", prot), ("bajo", bajo)):
        k = sum(1 for x in lst if x["X"][a])
        p, ic, ne = tasa_ponderada(lst, lambda x: x["X"][a])
        pk, _, _ = tasa_ponderada(lst, lambda x: x["K"])
        out[f"recall_{nom}"] = {"crudo": [k, len(lst)], "pond": p, "ic_kish": ic, "n_eff": ne, "K_pond": pk}
    # silencio en negativos limpios (B)
    pr_, icr, ner = tasa_ponderada(resto, lambda x: x["X"][a])
    pp_, icp, nep = tasa_ponderada(npub, lambda x: x["X"][a])
    if npub and abs(sum(x["w"] for x in npub) - len(npub)) < 1e-9:
        icp = (pp_, pp_)       # neg_pub es censo (peso 1 en todas): la tasa es exacta, sin error de muestreo
    Np, Nr = N_neg["neg_pub"], N_neg["neg_resto"]
    tot = Np + Nr
    pn = (Np * pp_ + Nr * pr_) / tot
    pn_hi = (Np * icp[1] + Nr * icr[1]) / tot
    pn_lo = (Np * icp[0] + Nr * icr[0]) / tot
    if pn_hi < tasa_k_neg:
        ver = "SILENCIO ACOTADO BAJO K"
    elif pn_lo > tasa_k_neg:
        ver = "ENCIENDE DE MAS"
    else:
        ver = "NO RESUELTO"
    out["silencio"] = {"neg_resto": {"crudo": [sum(1 for x in resto if x["X"][a]), len(resto)], "pond": pr_,
                                     "ic_kish": icr, "n_eff": ner},
                       "neg_pub": {"crudo": [sum(1 for x in npub if x["X"][a]), len(npub)], "pond": pp_, "ic": icp},
                       "negativos": {"pond": pn, "ic_conservador": [pn_lo, pn_hi], "K": tasa_k_neg},
                       "veredicto": ver}
    # MISSION contra K, con la cota honesta del estrato de cero eventos (verificador de S159 V-1)
    de = delta_e(filas, a, "K")
    ic = boot_estrat(filas, lambda s: delta_e(s, a, "K"), rng)
    p_enc, ic_enc, _ = tasa_ponderada(resto, lambda x: x["X"][a] and not x["K"])
    honesto_hi = max(ic[1], de + Nr * (ic_enc[1] - p_enc))
    if out["P1"]["perdidas_que_K_publica"] > 0:
        vm = "PIERDE PROTEGIDA"
    elif abs(de) < TOL and honesto_hi < TOL:
        vm = "EMPATE"
    elif honesto_hi < 0:
        vm = "GANA"
    elif ic[0] > 0:
        vm = "ENCIENDE DE MAS"
    else:
        vm = "NO RESUELTO"
    out["MISSION_K"] = {"dE": de, "ic_boot": ic, "cota_honesta_sup": honesto_hi, "veredicto": vm}
    # magnitud
    rr = [(x["V"][a] / x["mir"], x) for x in filas if x["c"].startswith("pos") and x["X"][a] and x["mir"] > 0]
    if rr:
        q = np.percentile([r for r, _ in rr], [25, 50, 75])
        out["M"] = {"n": len(rr), "mediana": float(q[1]), "q1": float(q[0]), "q3": float(q[2]),
                    "en_banda": sum(BANDA_M[0] <= r <= BANDA_M[1] for r, _ in rr)}
        por_z = collections.defaultdict(list)
        for r, x in rr:
            if x["z"] is not None:
                por_z[int(x["z"] // 10) * 10].append(r)
        out["M"]["por_cenit"] = {f"{k}-{k + 10}": [round(float(np.median(v)), 3), len(v)]
                                 for k, v in sorted(por_z.items())}
    else:
        out["M"] = {"n": 0}
    return out


def estratos(filas, a, clave_fn):
    g = collections.defaultdict(collections.Counter)
    for x in filas:
        k = (clave_fn(x), "pos" if x["c"].startswith("pos") else "neg")
        g[k]["n"] += 1
        g[k]["X"] += publica(x, a)
        g[k]["K"] += x["K"]
    return {f"{k[0]}|{k[1]}": f"{v['X']}/{v['K']}/{v['n']}" for k, v in sorted(g.items())}


def elegir_por_volcan(filas, candidatos, rng):
    """A115: el brazo por volcán se ELIGE en la ventana T (2026-04-01 a 06-12, decide la tabla sola) y se VALIDA en O.
    Elección: entre los brazos sin protegida perdida en T, el de menor suma ponderada de errores bajo 1 MW en T; a igual
    suma (a 1e-6), M14 si está entre los empatados y si no la caja más chica (ORDEN_DESEMPATE, la misma regla que el
    brazo global; corrección del verificador, verificador/INFORME.md). Un volcán sin pasadas en T queda en M14."""
    T = [x for x in filas if x["tramo"] == "T"]
    elec = {}
    for vol in sorted({x["vol"] for x in filas}):
        tv = [x for x in T if x["vol"] == vol]
        cand = []
        for a in candidatos:
            if any(x["c"] == "pos_prot" and not x["X"][a] for x in tv):
                continue
            e = sum(x["w"] for x in tv if err(x, a))
            orden = ORDEN_DESEMPATE.index(a[0]) if a[0] in ORDEN_DESEMPATE else len(ORDEN_DESEMPATE)
            cand.append((round(e, 6), 0 if a[0] == BR.REFERENCIA else 1, orden, a))
        elec[vol] = min(cand)[3] if (tv and cand) else (BR.REFERENCIA, REGLA_DECIDE)
    return elec


def compuesto(filas, elec):
    """Un volcán sin elección (no tiene pasadas en el subconjunto que eligió, por ejemplo el lote S162 frente a las
    protegidas de la unión que cuenta el veto) queda en M14, igual que un volcán sin pasadas en T. Lo destapó el humo
    del run 40115765406 (KeyError con Villarrica)."""
    for x in filas:
        a = elec.get(x["vol"], (BR.REFERENCIA, REGLA_DECIDE))
        x["X"][("POR_VOLCAN", REGLA_DECIDE)] = x["X"][a]
        x["V"][("POR_VOLCAN", REGLA_DECIDE)] = x["V"][a]


def k_marco():
    """Recall de K (lo publicado) en TODO el marco: la población congelada de S159 trae pub_prod de cada pasada, así
    que el recall de K no se estima, se cuenta (corrección del verificador: el disparador (b) comparaba contra la
    estimación de K en la muestra)."""
    pob = json.loads((RAIZ / "experiments/_s159/portes/poblacion_completa.json").read_text(encoding="utf-8"))["pasadas"]
    m = [o for o in pob if o["b"] == "VIIRS375" and o["decide"] and o["lab"] == "pos" and
         o["hora_utc"][:10] not in EXCLUIDOS]
    pr_ = [o for o in m if o["protegida"]]
    ba = [o for o in m if not o["protegida"]]
    return {"recall_prot": sum(bool(o["pub_prod"]) for o in pr_) / len(pr_), "n_prot": len(pr_),
            "recall_bajo": sum(bool(o["pub_prod"]) for o in ba) / len(ba), "n_bajo": len(ba)}


def repesar(filas, meta):
    """Copias de las filas con el peso recalculado dentro del subconjunto (N_h / n_ok_h del subconjunto). Un estrato
    sin ninguna pasada en el subconjunto queda sin representar; decidir() informa qué fracción de N cubre."""
    n = collections.Counter((x["c"], x["h"]) for x in filas)
    out = []
    for x in filas:
        y = dict(x)
        y["X"], y["V"] = dict(x["X"]), dict(x["V"])
        y["w"] = meta[x["c"]][x["h"]]["N"] / n[(x["c"], x["h"])]
        out.append(y)
    return out


def decidir(filas, N_neg, tasa_k_neg, rng, candidatos, ref, lk, etiqueta, veto=None):
    """PREREGISTRO_B.md §5 y PREREGISTRO_C.md §5.1 a §5.3 sobre un conjunto de filas (la unión o un lote).
    `veto`: las filas sobre las que se cuentan las protegidas perdidas (por defecto las mismas). Las protegidas son
    CENSO: el veto no se estima, se cuenta, y se cuenta siempre sobre la unión, también cuando decide el lote S162 (si
    no, 39 de las 80 protegidas, las de S159, quedarían fuera del veto; verificador/INFORME.md). `lk`: el recall de K
    en el MARCO entero (censo, exacto), no en la muestra."""
    veto = filas if veto is None else veto
    pr(f"\n  -- decisión sobre: {etiqueta} ({len(filas)} pasadas; veto de protegidas sobre {len(veto)}) --")
    cub = {c: sum(x["w"] for x in filas if x["c"] == c) for c in ("pos_prot", "pos_bajo", "neg_pub", "neg_resto")}
    pr("  N representado por clase:", {c: round(v, 1) for c, v in cub.items()})
    lb = lecturas(filas, ref, rng, N_neg, tasa_k_neg)
    out = {"B": lb["silencio"]["veredicto"], "B_detalle": lb["silencio"], "MISSION_M14_K": lb["MISSION_K"]}
    # V375-B2 §5.2: lectura estricta (informa, no decide): el mismo B con z = 2,241 (1,25 % por cola), la corrección de
    # Bonferroni por mirar dos veces la misma pregunta (S162 y S162 + B2)
    rs = [x for x in filas if x["c"] == "neg_resto"]
    ps = [x for x in filas if x["c"] == "neg_pub"]
    pr_s, ic_rs, _ = tasa_ponderada(rs, lambda x: x["X"][ref], z=2.241)
    pp_s, ic_ps, _ = tasa_ponderada(ps, lambda x: x["X"][ref], z=2.241)
    if ps and abs(sum(x["w"] for x in ps) - len(ps)) < 1e-9:
        ic_ps = (pp_s, pp_s)
    hi_s = (N_neg["neg_pub"] * ic_ps[1] + N_neg["neg_resto"] * ic_rs[1]) / (N_neg["neg_pub"] + N_neg["neg_resto"])
    out["B_estricto"] = {"cota_sup": hi_s, "veredicto": "SILENCIO ACOTADO BAJO K" if hi_s < tasa_k_neg else "NO RESUELTO"}
    pr(f"  B estricto (z 2,241, informa): cota {out['B_estricto']['cota_sup']:.4f} -> {out['B_estricto']['veredicto']}")
    pr(f"  B: neg_resto {lb['silencio']['neg_resto']['crudo']}, IC {lb['silencio']['neg_resto']['ic_kish']}; "
       f"negativos {lb['silencio']['negativos']['pond']:.4f} {lb['silencio']['negativos']['ic_conservador']} contra K "
       f"{tasa_k_neg:.4f} -> {out['B']}; MISSION M14 contra K {lb['MISSION_K']['veredicto']}")
    # §5.1: veto RELATIVO a M14 (la ROI no puede perder ninguna protegida que la referencia publica) y GANA en P2
    gan = []
    for a in candidatos:
        if a == ref:
            continue
        nuevas = sum(1 for x in veto if x["c"] == "pos_prot" and x["X"][ref] and not x["X"][a])
        v = p2(filas, a, ref)
        pr(f"  {a[0]:8s} protegidas que M14 publica y el brazo no: {nuevas}; P2 contra M14 {v['veredicto']} "
           f"(neto {v['neto']:+.1f}, B {v['B']})")
        if nuevas == 0 and v["veredicto"] == "GANA":
            gan.append((round(delta_e(filas, a, "K"), 6), ORDEN_DESEMPATE.index(a[0]), a[0]))
    out["candidatos"] = sorted(x[2] for x in gan)
    out["global"] = min(gan)[2] if gan else BR.REFERENCIA
    pr("  brazo global:", out["global"], "| candidatos:", out["candidatos"])
    # §5.2: por volcán, elegido en T y validado en O
    elec = elegir_por_volcan(filas, candidatos, rng)
    compuesto(filas, elec)
    if veto is not filas:
        compuesto(veto, elec)
    O = [x for x in filas if x["tramo"] != "T"]
    pv = ("POR_VOLCAN", REGLA_DECIDE)
    nuevas_o = sum(1 for x in veto if x["tramo"] != "T" and x["c"] == "pos_prot" and x["X"][ref] and not x["X"][pv])
    p2o = p2(O, pv, ref)
    p2ok = p2(O, pv, "K")
    out["eleccion"] = {v: b for v, (b, _) in elec.items()}
    # corrección del verificador: validar exige GANA, igual que el brazo global (EMPATE o SIN SUSTRATO no validan)
    if nuevas_o:
        estado = "NO VALIDA EN O (pierde protegidas que M14 publica)"
    elif p2o["veredicto"] == "GANA":
        estado = "VALIDA EN O"
    elif p2o["veredicto"] == "SIN SUSTRATO":
        estado = "SIN SUSTRATO EN O"
    else:
        estado = "NO VALIDA EN O"
    out["valida_en_O"] = estado
    pr("  por volcán, elegido en T:", {v: b for v, b in out["eleccion"].items() if b != BR.REFERENCIA},
       "(los demás M14)")
    pr(f"  validación en O: protegidas que M14 publica y el compuesto no {nuevas_o}; P2 contra M14 "
       f"{p2o['veredicto']} (neto {p2o['neto']:+.1f}, B {p2o['B']}); P2 contra K {p2ok['veredicto']} -> {estado}")
    # §5.3: disparador de V375-D. La pérdida contra K se mide con la TABLA sola (el canal más creíble; las protegidas
    # sólo OCR se informan y esperan la etiqueta de cráter de V375-A). El recall de K es el del marco (censo).
    ag = (out["global"], REGLA_DECIDE)
    lg = lecturas(filas, ag, rng, N_neg, tasa_k_neg)
    perd_tabla_k = sum(1 for x in veto if x["c"] == "pos_prot" and x["tabla"] and x["K"] and not x["X"][ag])
    perd_k = sum(1 for x in veto if x["c"] == "pos_prot" and x["K"] and not x["X"][ag])
    mot = []
    if out["B"] == "ENCIENDE DE MAS":
        mot.append("B: el port enciende de más en negativos")
    if lg["recall_bajo"]["ic_kish"][1] < lk["recall_bajo"]:
        mot.append(f"C: con el brazo global el IC del recall bajo 1 MW ({lg['recall_bajo']['ic_kish'][1]:.3f} arriba) "
                   f"queda entero bajo el de K en el marco ({lk['recall_bajo']:.3f})")
    if perd_tabla_k > 0:
        mot.append(f"C: el brazo global pierde {perd_tabla_k} protegidas de la tabla que K publica")
    out["V375_D"] = mot
    out["V375_D_necesario"] = bool(mot)
    out["perdidas_ocr_que_K_publica"] = perd_k - perd_tabla_k
    pr("  V375-D:", "NECESARIO: " + "; ".join(mot) if mot else "NO NECESARIO por B ni por C",
       f"| protegidas sólo OCR que K publica y el brazo global no: {out['perdidas_ocr_que_K_publica']} "
       "(esperan V375-A)")
    return out


# ---------------------------------------------------------------- principal
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--art162", default=None)
    ap.add_argument("--art159", default=r"D:\vrp-trabajo\temporales\s159_portes\run_39712862945")
    ap.add_argument("--objetivos", default=str(AQUI / "objetivos_v375_bc.json"))
    ap.add_argument("--cache", default=str(AQUI / "cache_brazos.json"))
    ap.add_argument("--cobertura", default=None, help="salida del instrumento (fase 0): pasadas de MIROVA sin record")
    ap.add_argument("--protegida-crater", default=None, help="V375-A: lista de protegidas de cráter (se informa)")
    ap.add_argument("--sin-s159", action="store_true", help="sólo para pruebas: no suma el lote de S159")
    # V375-B2 (b2/PREREGISTRO_B2.md): una segunda muestra de neg_resto (lote S162b) con sus artefactos, y qué lotes
    # forman el conjunto que decide. Por defecto, lo de V375-B y V375-C: sólo S162.
    ap.add_argument("--objetivos-extra", nargs="*", default=[], help="más archivos de objetivos (p. ej. el de B2)")
    ap.add_argument("--art-extra", nargs="*", default=[], help="carpetas de artefactos de los lotes extra")
    ap.add_argument("--deciden", nargs="+", default=["S162"], help="lotes del conjunto que decide")
    ap.add_argument("--neg-pub-de", default=None, help="lote del que sale neg_pub en el conjunto que decide (B2: S162)")
    ap.add_argument("--salida", default=str(AQUI / "evaluar_salida.txt"))
    ap.add_argument("--json", default=str(AQUI / "evaluar.json"))
    a = ap.parse_args(argv)
    L.clear()
    V = volcanes()
    inner = B.inner_desde_html()
    o162 = json.loads(Path(a.objetivos).read_text(encoding="utf-8"))
    meta = o162["meta"]["estratos"]
    obj = {o["id"]: dict(o) for o in o162["pasadas"]}
    for f in a.objetivos_extra:
        for o in json.loads(Path(f).read_text(encoding="utf-8"))["pasadas"]:
            assert o["id"] not in obj, ("id repetido entre objetivos", o["id"])
            obj[o["id"]] = dict(o)
    if not a.sin_s159:
        for o in json.loads((RAIZ / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8")):
            if o["b"] == "VIIRS375" and o["hora_utc"][:10] not in EXCLUIDOS:
                obj[o["id"]] = {**o, "lote": "S159", "estrato": f"{o['volcan']}|{o['estrato_z']}"}
    res = {}
    res.update({i: r for i, r in leer_resultados(a.art159).items() if i in obj and obj[i]["lote"] == "S159"})
    res.update({i: r for i, r in leer_resultados(a.art162).items() if i in obj and obj[i]["lote"] == "S162"})
    art_de = {}
    for d in a.art_extra:
        for i, r in leer_resultados(d).items():
            if i in obj and obj[i]["lote"] not in ("S159", "S162"):
                res[i] = r
                art_de[i] = d
    cache = json.loads(Path(a.cache).read_text(encoding="utf-8")) if Path(a.cache).exists() else {}
    ok = {i for i, r in res.items() if r.get("estado") == "ok" and r.get("port") is not None}
    veredicto_instr = []

    # ------------------------------------------------------------ 1. cobertura
    pr("== 1. cobertura (A108): objetivos", len(obj), "con estado ok", len(ok))
    cob = collections.Counter((o["lote"], o["clase"], (res.get(i) or {}).get("estado", "sin_resultado"))
                              for i, o in obj.items())
    for k, v in sorted(cob.items()):
        pr("  ", k, v)
    sin = [(i, obj[i]["lote"], obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["clase"],
            (res.get(i) or {}).get("estado", "sin_resultado")) for i in sorted(obj) if i not in ok]
    pr("   SIN DATO:", len(sin), sin[:40])
    for c in ("pos_prot", "pos_bajo", "neg_pub", "neg_resto"):
        n_c = sum(1 for o in obj.values() if o["clase"] == c)
        n_s = sum(1 for x in sin if x[4] == c)
        if n_c and n_s / n_c > 0.10:
            pr(f"   AVISO: {c} tiene {n_s} de {n_c} SIN DATO (más del 10 %): la lectura de esa clase se informa pero "
               "no decide (§4.1)")
            veredicto_instr.append(f"cobertura_{c}")
    # V375-B2 (verificador del borrador, F4): el mismo umbral, también por lote, para que un lote que decide no
    # esconda su hueco detrás de los otros
    for lote in sorted({o["lote"] for o in obj.values()}):
        for c in ("pos_prot", "pos_bajo", "neg_pub", "neg_resto"):
            n_c = sum(1 for o in obj.values() if o["clase"] == c and o["lote"] == lote)
            n_s = sum(1 for x in sin if x[4] == c and x[1] == lote)
            if n_c and n_s / n_c > 0.10:
                pr(f"   AVISO: lote {lote}, {c}: {n_s} de {n_c} SIN DATO (más del 10 %)")
                veredicto_instr.append(f"cobertura_{lote}_{c}")
    if a.cobertura:
        # salida de cobertura_marco.py (evaluador común del instrumento sobre el MARCO, con producción como único lado)
        cobm = json.loads(Path(a.cobertura).read_text(encoding="utf-8"))
        for canal in ("union", "tabla"):
            c = cobm[canal]
            sin_rec = [x for x in c["no_observadas"]]
            pr(f"   cobertura del marco contra MIROVA, canal {canal} (evaluador común {cobm['commit_evaluador_comun'][:9]}):"
               f" alertas {c['alertas']}, sin record de producción {len(sin_rec)} (protegidas "
               f"{sum(1 for x in sin_rec if x['protegida'])}) -> {c['veredicto_evaluador_comun']}")
            if sin_rec or c["veredicto_evaluador_comun"] != "COBERTURA OK":
                veredicto_instr.append(f"cobertura_marco_{canal}")
    else:
        pr("   cobertura contra la referencia de MIROVA (alertas sin record nuestro, 14 en el marco): PENDIENTE de la "
           "sesión del instrumento (fase 0). Sin ella el veredicto no se declara final (§4.1).")
        veredicto_instr.append("cobertura_referencia_pendiente")

    # ------------------------------------------------------------ 2. brazos por pasada y control de recálculo
    pr("\n== 2. controles (antes de leer)")
    arms = {}
    n_cmp = n_ig = 0
    dif = []
    for i in sorted(ok):
        o, r = obj[i], res[i]
        art = a.art159 if o["lote"] == "S159" else (a.art162 if o["lote"] == "S162" else art_de[i])
        rec = recalcular(o, r, art, V, cache)
        if rec is None:
            pr("   sin grilla:", i)
            continue
        if o["lote"] == "S159":
            for b, m in BR.EQUIV_S159.items():
                n_cmp += 1
                if mismo(rec[b], r["port"][m]):
                    n_ig += 1
                else:
                    dif.append((i, b))
            arms[i] = rec
        else:
            for b in BR.BRAZOS:
                n_cmp += 1
                if mismo(rec[b], r["port"][b]):
                    n_ig += 1
                else:
                    dif.append((i, b))
            arms[i] = r["port"]
    Path(a.cache).write_text(json.dumps(cache), encoding="utf-8")
    pr(f"  2.1 recálculo sin red = runner: {n_ig} de {n_cmp} (pasada x brazo; S159: M14, PIX7, SENS; S162: los 10)")
    if dif:
        pr("      distintos:", dif[:20])
        veredicto_instr.append("recalculo")

    # node: K re-corrido y cada brazo con cada regla
    casos, idx = [], []
    for i in sorted(arms):
        o, r = obj[i], res[i]
        krec = (r.get("K") or {}).get("record")
        if krec is not None:
            casos.append([slim(krec), inner[o["volcan"]]])
            idx.append((i, "Krun", ""))
        for b in BR.BRAZOS:
            for regla in REGLAS:
                casos.append([slim(record_sintetico(arms[i][b], o["grilla"], inner[o["volcan"]], o["sensor"], regla)),
                              inner[o["volcan"]]])
                idx.append((i, b, regla))
        casos.append([slim(record_sintetico(arms[i]["M14"], o["grilla"], inner[o["volcan"]], o["sensor"], REGLA_DECIDE,
                                            FACTOR_PLACEBO)), inner[o["volcan"]]])
        idx.append((i, "PLACEBO", REGLA_DECIDE))
    P = {k: (bool(p[4]), float(p[3] or 0.0)) for k, p in zip(idx, B.correr_node(casos))} if casos else {}
    arms_por_id = {}
    for i in arms:
        d = {}
        for b in BR.BRAZOS:
            for regla in REGLAS:
                pub, vd = P[(i, b, regla)]
                d[(b, regla)] = (pub, vd, arms[i][b]["npix"])
        pub, vd = P[(i, "PLACEBO", REGLA_DECIDE)]
        d[("PLACEBO", REGLA_DECIDE)] = (pub, vd, arms[i]["M14"]["npix"])
        d[("NUNCA", REGLA_DECIDE)] = (False, 0.0, 0)
        arms_por_id[i] = d

    # 2.2 K re-corrido = publicado
    pub_k = {i: P[(i, "Krun", "")][0] for i in arms if (i, "Krun", "") in P}
    vk = {i: P[(i, "Krun", "")][1] for i in arms if (i, "Krun", "") in P}
    con_k = [i for i in arms if i in pub_k]
    igual_k = sum(1 for i in con_k if pub_k[i] == bool(obj[i]["pub_prod"]))
    frac = igual_k / len(con_k) if con_k else 0.0
    k_usa_recorrido = frac < UMBRAL_K_RECORRIDO
    pr(f"  2.2 K re-corrido publica igual que el record publicado: {igual_k} de {len(con_k)} ({frac:.3f}); sin K "
       f"re-corrido {len(arms) - len(con_k)}; la lectura de K usa {'lo RE-CORRIDO' if k_usa_recorrido else 'lo publicado'}")
    pr("      distintos:", [(i, obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["clase"], obj[i]["pub_prod"], pub_k[i])
                            for i in con_k if pub_k[i] != bool(obj[i]["pub_prod"])][:15])
    if k_usa_recorrido:
        for i in arms:
            pub_k.setdefault(i, bool(obj[i]["pub_prod"]))

    # pesos de la unión (SIN DATO fuera: el estrato se re-pondera entre sus pasadas ok)
    n_ok = collections.Counter((obj[i]["clase"], obj[i]["estrato"]) for i in arms_por_id)
    pesos = {}
    for c, est in meta.items():
        for h, v in est.items():
            if n_ok.get((c, h)):
                pesos[(c, h)] = v["N"] / n_ok[(c, h)]
    sin_peso = [(c, h) for c, est in meta.items() for h in est if est[h]["N"] and not n_ok.get((c, h))]
    pr("  pesos: estratos sin ninguna pasada ok (su N queda sin representar):", sin_peso)
    N_neg = {c: sum(v["N"] for v in meta[c].values()) for c in CLASES_NEG}
    tasa_k_neg = N_neg["neg_pub"] / (N_neg["neg_pub"] + N_neg["neg_resto"])
    filas = armar(obj, res, arms_por_id, inner, pub_k, vk, k_usa_recorrido, pesos)

    # 2.2b control de vida del lote nuevo (V375-B2, b2/PREREGISTRO_B2.md §4; verificador v2, hallazgo 3): las pasadas
    # del lote CTL son re-mediciones de pasadas de S162 en el MISMO run del lote que decide; M14 tiene que dar los mismos
    # npix y VRP que en S162 (mismo gránulo, mismo código). Un port muerto o una dependencia rota no pasa esto.
    ctl = [i for i, o in obj.items() if o["lote"] == "CTL"]
    if ctl:
        ok_ctl = [i for i in ctl if i in arms]
        dif = [(i, obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["ref_M14"], (arms[i]["M14"]["npix"], arms[i]["M14"]["vrp_mw"]))
               for i in ok_ctl if not (arms[i]["M14"]["npix"] == obj[i]["ref_M14"][0] and (
                   (arms[i]["M14"]["vrp_mw"] is None and obj[i]["ref_M14"][1] is None) or (
                       arms[i]["M14"]["vrp_mw"] is not None and obj[i]["ref_M14"][1] is not None
                       and abs(arms[i]["M14"]["vrp_mw"] - obj[i]["ref_M14"][1]) < TOL_RECALCULO_MW)))]
        vivos = sum(1 for i in ok_ctl if arms[i]["M14"]["npix"])
        pr(f"  2.2b control de vida del lote nuevo: {len(ok_ctl)} de {len(ctl)} re-medidas ok; iguales a S162 "
           f"{len(ok_ctl) - len(dif)}; con píxeles {vivos}")
        if dif:
            pr("      distintas:", dif[:10])
        if len(ok_ctl) < 0.9 * len(ctl) or dif or not vivos:
            veredicto_instr.append("control_vida")

    # 2.3 control positivo
    cp = [x for x in filas if x["c"] == "pos_prot" and x["vol"] in ("Lascar", "NevadosDeChillan")]
    n_cp = sum(1 for x in cp if x["npix"][(BR.REFERENCIA, REGLA_DECIDE)])
    pr(f"  2.3 control positivo: protegidas de Láscar o Chillán con píxeles en M14: {n_cp} de {len(cp)}")
    if not n_cp:
        veredicto_instr.append("control_positivo")
    rng = np.random.default_rng(SEMILLA)
    ref = (BR.REFERENCIA, REGLA_DECIDE)
    # 2.4 nulo: M14 contra sí mismo
    nulo = p2(filas, ref, ref)
    pr(f"  2.4 nulo M14 contra M14: discordantes en {nulo['B']} bloques, neto {nulo['neto']:+.3f} -> {nulo['veredicto']}")
    if nulo["B"] != 0:
        veredicto_instr.append("nulo")
    # 2.5 NUNCA
    nun = ("NUNCA", REGLA_DECIDE)
    ln = lecturas(filas, nun, rng, N_neg, tasa_k_neg)
    p2n = p2(filas, nun, ref)
    pr(f"  2.5 NUNCA: recall protegidas {ln['recall_prot']['crudo']}, bajo {ln['recall_bajo']['crudo']}; protegidas "
       f"perdidas que K publica {ln['P1']['perdidas_que_K_publica']}; P2 contra M14 {p2n['veredicto']} "
       f"(neto {p2n['neto']:+.1f}, B {p2n['B']}); MISSION contra K {ln['MISSION_K']['veredicto']}")
    if ln["recall_prot"]["crudo"][0] != 0 or (p2n["B"] > MAX_B_SIN_SUSTRATO and p2n["veredicto"] != "PIERDE"):
        veredicto_instr.append("control_nunca")
    # 2.6 PLACEBO
    plc = ("PLACEBO", REGLA_DECIDE)
    p2p = p2(filas, plc, ref)
    lp = lecturas(filas, plc, rng, N_neg, tasa_k_neg)
    l14 = lecturas(filas, ref, rng, N_neg, tasa_k_neg)
    igual_det = all(x["X"][plc] == x["X"][ref] for x in filas)
    razon_plc = (lp["M"].get("mediana", float("nan")) / l14["M"]["mediana"]) if l14["M"].get("n") else float("nan")
    pr(f"  2.6 PLACEBO (M14 x {FACTOR_PLACEBO}): misma publicación {igual_det}; P2 contra M14 {p2p['veredicto']} (B "
       f"{p2p['B']}); mediana de M placebo / M14 = {razon_plc:.3f}; cruces de 1 MW: baja {lp['P1b']['baja']} contra "
       f"{l14['P1b']['baja']}, sube {lp['P1b']['sube_crudo']} contra {l14['P1b']['sube_crudo']}")
    if not igual_det or p2p["B"] != 0 or (l14["M"].get("n") and abs(razon_plc - FACTOR_PLACEBO) > 0.02):
        veredicto_instr.append("placebo")
    pr("  ESTADO DEL INSTRUMENTO:", "OK" if not [v for v in veredicto_instr if not v.startswith("cobertura")] else
       "INVALIDO POR INSTRUMENTO " + str(veredicto_instr), "| avisos de cobertura:",
       [v for v in veredicto_instr if v.startswith("cobertura")])
    invalido = bool([v for v in veredicto_instr if not v.startswith("cobertura")])

    # ------------------------------------------------------------ 3. lecturas
    resumen = {"instrumento": veredicto_instr, "invalido": invalido, "brazos": {}}
    candidatos = [(b, REGLA_DECIDE) for b in BR.BRAZOS]
    for regla in REGLAS:
        for b in BR.BRAZOS:
            a_ = (b, regla)
            lx = lecturas(filas, a_, rng, N_neg, tasa_k_neg)
            lx["P2_vs_M14"] = p2(filas, a_, ref) if regla == REGLA_DECIDE else None
            lx["P2_vs_K"] = p2(filas, a_, "K") if regla == REGLA_DECIDE else None
            resumen["brazos"][f"{b}|{regla}"] = lx
    lk = {"recall_prot": tasa_ponderada([x for x in filas if x["c"] == "pos_prot"], lambda x: x["K"])[0],
          "recall_bajo": tasa_ponderada([x for x in filas if x["c"] == "pos_bajo"], lambda x: x["K"])[0]}
    resumen["K"] = lk

    pr("\n== 3. V375-B: silencio del port (M14) en los negativos limpios, sobre TODAS las pasadas (informa; el veredicto "
       "de B es la línea «VEREDICTO B» de 4b)")
    sB = resumen["brazos"][f"M14|{REGLA_DECIDE}"]
    s = sB["silencio"]
    pr(f"  neg_resto: publica {s['neg_resto']['crudo'][0]} de {s['neg_resto']['crudo'][1]}; ponderado "
       f"{s['neg_resto']['pond']:.4f}, IC (Wilson sobre n efectivo {s['neg_resto']['n_eff']:.0f}) "
       f"[{s['neg_resto']['ic_kish'][0]:.4f}; {s['neg_resto']['ic_kish'][1]:.4f}]")
    pr(f"  neg_pub (censo): publica {s['neg_pub']['crudo'][0]} de {s['neg_pub']['crudo'][1]}")
    pr(f"  todos los negativos limpios: {s['negativos']['pond']:.4f} [{s['negativos']['ic_conservador'][0]:.4f}; "
       f"{s['negativos']['ic_conservador'][1]:.4f}] contra K {tasa_k_neg:.4f} -> {s['veredicto']}")
    m = sB["MISSION_K"]
    pr(f"  MISSION del port (M14) contra K: ΔE {m['dE']:+.1f}, IC bootstrap [{m['ic_boot'][0]:+.1f}; "
       f"{m['ic_boot'][1]:+.1f}], cota honesta superior {m['cota_honesta_sup']:+.1f} -> {m['veredicto']}")
    for regla in REGLAS:
        s2 = resumen["brazos"][f"M14|{regla}"]["silencio"]
        pr(f"  regla {regla}: neg_resto {s2['neg_resto']['crudo']}, negativos {s2['negativos']['pond']:.4f} -> "
           f"{s2['veredicto']}")
    pr("  por tramo (M14, publica port / K / n):", estratos(filas, ref, lambda x: x["tramo"]))

    pr("\n== 4. V375-C: brazos de ROI (regla «cercano» decide; «centroide» informa)")
    pr("  K: recall ponderado protegidas", round(lk["recall_prot"], 3), "bajo 1 MW", round(lk["recall_bajo"], 3))
    for b in BR.BRAZOS:
        lx = resumen["brazos"][f"{b}|{REGLA_DECIDE}"]
        pr(f"  {b:8s} P1 perdidas {lx['P1']['perdidas']} de {lx['P1']['de']} (K publica {lx['P1']['perdidas_que_K_publica']}, "
           f"tabla {lx['P1']['perdidas_tabla']}); recall bajo {lx['recall_bajo']['pond']:.3f} "
           f"[{lx['recall_bajo']['ic_kish'][0]:.3f}; {lx['recall_bajo']['ic_kish'][1]:.3f}]; negativos "
           f"{lx['silencio']['negativos']['pond']:.4f}; P1b baja {lx['P1b']['baja']} sube {lx['P1b']['sube_crudo']}; "
           f"P2 vs M14 {lx['P2_vs_M14']['veredicto']} (neto {lx['P2_vs_M14']['neto']:+.1f}, B {lx['P2_vs_M14']['B']}); "
           f"P2 vs K {lx['P2_vs_K']['veredicto']}; MISSION K {lx['MISSION_K']['veredicto']}; M "
           f"{lx['M'].get('mediana', float('nan')):.3f} n {lx['M']['n']}")
    for b in BR.BRAZOS:
        lc = resumen["brazos"][f"{b}|centroide"]
        pr(f"  {b:8s} (centroide) P1 perdidas {lc['P1']['perdidas']}, recall bajo {lc['recall_bajo']['pond']:.3f}, "
           f"negativos {lc['silencio']['negativos']['pond']:.4f}")
    # PREREGISTRO_C.md §5.1 a §5.3 y §5.5: decide el lote S162 (no visto antes del sello); la unión confirma
    lkm = k_marco()
    pr(f"  K en el marco entero (censo de la población de S159, sin los días excluidos): recall protegidas "
       f"{lkm['recall_prot']:.3f} ({lkm['n_prot']}), bajo 1 MW {lkm['recall_bajo']:.3f} ({lkm['n_bajo']})")
    resumen["K_marco"] = lkm
    dec_u = decidir(filas, N_neg, tasa_k_neg, rng, candidatos, ref, lkm, "unión S159 + S162 (confirma)")
    # V375-B2 §5.1: con --neg-pub-de, la clase neg_pub del conjunto que decide se toma de ese lote (en el marco no queda
    # ninguna neg_pub sin medir; las 113 de S162 entran como muestra, no como censo)
    def en_decide(x):
        if a.neg_pub_de and x["c"] == "neg_pub":
            return x["lote"] == a.neg_pub_de
        return x["lote"] in a.deciden
    vacios = [l for l in a.deciden if not any(x["lote"] == l for x in filas)]
    if vacios:
        # verificador del borrador de B2, F5: un lote que decide sin ninguna pasada ok no puede decidir en silencio
        pr("  INVALIDO POR INSTRUMENTO: lotes que deciden sin ninguna pasada ok:", vacios)
        veredicto_instr.append("lote_que_decide_vacio")
        invalido = True
        resumen["invalido"] = True
    f162 = repesar([x for x in filas if en_decide(x)], meta)
    dec_n = (decidir(f162, N_neg, tasa_k_neg, rng, candidatos, ref, lkm,
                     f"lotes {'+'.join(a.deciden)} (DECIDE)", veto=filas)
             if f162 else None)
    resumen["decision_union"], resumen["decision_s162"] = dec_u, dec_n
    pr("\n== 4b. acuerdo entre el lote nuevo (decide) y la unión (confirma), PREREGISTRO_C.md §5.5")
    if dec_n is None:
        pr("  SIN DATO: no hay pasadas del lote S162 (humo sobre S159 solo)")
        resumen["acuerdo"] = None
    else:
        acuerdo = {k: dec_n[k] == dec_u[k] for k in ("B", "global", "valida_en_O", "V375_D_necesario")}
        etq = "+".join(a.deciden) + (f" (neg_pub de {a.neg_pub_de})" if a.neg_pub_de else "")
        for k, v in acuerdo.items():
            pr(f"  {k}: {etq} {dec_n[k]} | unión {dec_u[k]} -> "
               f"{'DE ACUERDO' if v else 'DEPENDE DEL LOTE VISTO: NO RESUELTO'}")
        resumen["acuerdo"] = acuerdo
        # La línea que es el veredicto de B (verificador v2 de B2, hallazgo 5). Si un lote que decide pasa el umbral de
        # cobertura (10 % SIN DATO en su clase), B no decide (PREREGISTRO_B.md §4.1; B2 §4).
        hueco = [v for v in veredicto_instr if any(v.startswith(f"cobertura_{l}_") for l in a.deciden)]
        if invalido:
            vb = "INVALIDO POR INSTRUMENTO"
        elif hueco:
            vb = f"NO DECIDE (cobertura del lote que decide: {hueco})"
        else:
            vb = dec_n["B"] if acuerdo["B"] else "NO RESUELTO (depende del lote visto)"
        pr(f"  VEREDICTO B ({etq} decide, unión confirma): {vb}")
        resumen["veredicto_B"] = vb
    global_ = (dec_n or dec_u)["global"]
    pr("\n== 5. estratos del brazo global y de M14 (publica / K / n)")
    for nom, fn in (("volcán", lambda x: x["vol"]), ("tramo", lambda x: x["tramo"]),
                    ("cenit 10°", lambda x: None if x["z"] is None else int(x["z"] // 10) * 10),
                    ("canal", lambda x: "tabla" if x["tabla"] else ("ocr" if x["c"].startswith("pos") else "neg")),
                    ("lote", lambda x: x["lote"])):
        pr(f"  {nom} M14:", estratos(filas, ref, fn))
        if global_ != BR.REFERENCIA:
            pr(f"  {nom} {global_}:", estratos(filas, (global_, REGLA_DECIDE), fn))
    pr("  partidas (aparte):", [(x["vol"], x["hora"], x["c"], publica(x, ref), x["K"]) for x in filas if x["part"]])
    if a.protegida_crater:
        pr("  protegida de cráter (V375-A):", Path(a.protegida_crater).read_text(encoding="utf-8")[:2000])
    else:
        pr("  protegida de cráter (V375-A): PENDIENTE de la sesión del instrumento; se informará al lado de la lectura A")
    if invalido:
        pr("\nVEREDICTO: INVALIDO POR INSTRUMENTO", veredicto_instr)
    elif any(v == "cobertura_referencia_pendiente" or v.startswith("cobertura_marco") for v in veredicto_instr):
        pr("\nVEREDICTO: PROVISIONAL, falta la cobertura contra la referencia de MIROVA (instrumento, fase 0); "
           "avisos:", veredicto_instr)
    else:
        pr("\nVEREDICTO: los de §3 y §4b; avisos de cobertura:", veredicto_instr)
    Path(a.salida).write_text("\n".join(L) + "\n", encoding="utf-8")
    Path(a.json).write_text(json.dumps(resumen, default=str, indent=1), encoding="utf-8")
    return resumen


if __name__ == "__main__":
    main()
