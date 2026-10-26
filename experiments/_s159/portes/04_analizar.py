# -*- coding: utf-8 -*-
"""S159 frente PORTES, lectura: controles primero (PREREGISTRO.md §4), después las lecturas R1 a R4 y el veredicto
MISSION del port contra K, por sensor y por estrato (§5).

«Publica» = el predicado del tablero (isSummitDetection && isValidDetection && !isThermalArtifact &&
mirovaEqVrpDisplay > 0) ejecutado con node desde frontend/index.html (banco_paridad.correr_node). Para K, sobre el
record publicado en data/ (pub_prod de la población) y, como control, sobre el record re-corrido en el runner. Para el
port, sobre un RECORD SINTÉTICO (§4 del pre-registro): vrp_mw = primary_cluster.vrp_mw = f5_core_vrp_mw = VRP del
código, distance_class = summit si el centroide de los alertados está a inner_radius_km o menos de (X0, Y0),
t_max_k = temperatura MIR del alertado más radiante.

Pregunta 1 del instrumento: si el port no publicara nunca, R2 daría 0 y el control positivo (§4.5) fallaría; si
publicara siempre, R3 daría 1. Pregunta 2: una pasada sin resultado es SIN DATO y no entra a ningún denominador; el
conteo de SIN DATO se imprime antes de cualquier número.
Uso: python -I 04_analizar.py --art <carpeta con resultados_*.json> --n-art <carpeta del lote de N>
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(AQUI))
import banco_paridad as B  # noqa: E402

VARIANTES = {"VIIRS375": ["fisica", "pixel", "sensible"],
             "MODIS": ["fisica", "pixel", "sensible", "fisica_b21", "fisica_geo5km"]}
K_POB_NEG = {"VIIRS375": (134, 3482), "MODIS": (39, 5132)}     # PREREGISTRO §5 R3 (población sin 17-20 oct)
VARA_R2 = {"todas": 145 / 181, "prot": 71 / 78}                # oráculo de N en VIIRS 750 (N-2)
FRONTERA_OCR = "2026-06-13"
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def record_port(p, inner, sensor):
    if not p or not p.get("npix") or p.get("vrp_mw") is None:
        return {"sensor": sensor, "vrp_mw": 0.0, "primary_cluster": None, "distance_class": None}
    px = p["pixeles"]
    # centroide en distancia: promedio de las posiciones relativas no está guardado; se usa la distancia media
    # ponderada igual (aproximación) y, para la clase, la del centroide en filas y columnas convertida con la celda
    fr, fc = np.mean([q[0] for q in px]), np.mean([q[1] for q in px])
    dcen = p.get("_dcen")
    tmax = max(q[5] for q in px)
    v = round(float(p["vrp_mw"]), 4)
    return {"sensor": sensor, "vrp_mw": v, "f5_core_vrp_mw": v, "t_max_k": tmax, "triggered_test1": False,
            "distance_class": "summit" if dcen <= inner else "far",
            "primary_cluster": {"vrp_mw": v, "n_pixels": p["npix"], "centroid_dist_km": round(dcen, 3)},
            "_fr": fr, "_fc": fc}


def dist_centroide(p, g):
    """Distancia del centroide (filas, columnas) de los alertados al punto de referencia (X0, Y0), en km."""
    px = p["pixeles"]
    fr, fc = np.mean([q[0] for q in px]), np.mean([q[1] for q in px])
    x = g["ul_x"] + g["celda"] * (fc + 0.5)
    y = g["ul_y"] - g["celda"] * (fr + 0.5)
    return float(np.hypot(x - g["X0"], y - g["Y0"]) / 1000.0)


def slim(rec):
    s = {k: rec.get(k) for k in B.CAMPOS_JS}
    s.setdefault("anomaly_pixels", [])
    if s["anomaly_pixels"] is None:
        s["anomaly_pixels"] = []
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True, nargs="+")
    ap.add_argument("--n-art", required=True)
    ap.add_argument("--salida", default=str(AQUI / "04_analizar_salida.txt"))
    a = ap.parse_args()
    obj = {o["id"]: o for o in json.loads((AQUI / "objetivos_portes.json").read_text(encoding="utf-8"))}
    res = {}
    for d in a.art:
        for f in sorted(Path(d).rglob("resultados_*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                if r.get("estado") == "ok" or r["id"] not in res:
                    res[r["id"]] = r
    inner = B.inner_desde_html()
    pr("== 1. cobertura (A108): objetivos", len(obj), "con resultado", len(res))
    cob = collections.Counter((o["b"], o["clase"], (res.get(i) or {}).get("estado", "sin_resultado"))
                              for i, o in obj.items())
    for k, v in sorted(cob.items()):
        pr("  ", k, v)
    ok = {i for i, r in res.items() if r.get("estado") == "ok" and r.get("port")}
    pr("   SIN DATO:", [(i, obj[i]["b"], obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["clase"],
                         (res.get(i) or {}).get("estado", "sin_resultado")) for i in sorted(obj) if i not in ok])

    # ---------------------------------------------------------- casos para node
    casos, idx = [], []
    for i in sorted(ok):
        o, r = obj[i], res[i]
        if o["b"] == "VIIRS750":
            continue
        v = o["volcan"]
        krec = (r.get("K") or {}).get("record")
        if krec is not None:
            casos.append([slim(krec), inner[v]])
            idx.append((i, "Krun"))
        for m in VARIANTES[o["b"]]:
            p = r["port"].get(m)
            if p and p.get("npix"):
                p["_dcen"] = dist_centroide(p, o["grilla"])
            rp = record_port(p, inner[v], o["sensor"])
            rp = {k: x for k, x in rp.items() if not k.startswith("_")}
            casos.append([slim(rp), inner[v]])
            idx.append((i, m))
    P = {k: (bool(p[4]), p[3]) for k, p in zip(idx, B.correr_node(casos))}
    pub = lambda i, m: P.get((i, m), (False, 0))[0]

    # ---------------------------------------------------------- 2. controles
    pr("\n== 2. controles (antes de leer)")
    # CTL750 contra N
    nres = {}
    for f in sorted(Path(a.n_art).rglob("resultados_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok":
                nres[r["id"]] = r
    ctl = [i for i in sorted(obj) if obj[i]["b"] == "VIIRS750"]
    iguales, filas = 0, []
    for i in ctl:
        if i not in ok:
            filas.append((i, "SIN DATO"))
            continue
        mine = res[i]["port"]["fisica"]
        ref = (nres.get(obj[i]["id_n"]) or {}).get("oraculo", {}).get("geo_linear")
        if ref is None:
            filas.append((i, "N sin oraculo"))
            continue
        same = mine["npix"] == ref["npix"] and (
            (mine["vrp_mw"] is None and ref["vrp_mw"] is None) or
            (mine["vrp_mw"] is not None and ref["vrp_mw"] is not None and abs(mine["vrp_mw"] - ref["vrp_mw"]) < 1e-6))
        iguales += same
        filas.append((i, obj[i]["volcan"], obj[i]["hora_utc"], mine["npix"], mine["vrp_mw"], ref["npix"], ref["vrp_mw"],
                      "IGUAL" if same else "DISTINTO"))
    pr(f"  CTL750 (cadena completa en el runner contra el oráculo de N): iguales {iguales} de {len(ctl)}")
    for x in filas:
        pr("    ", x)
    # K re-corrido contra lo publicado
    for b in ("VIIRS375", "MODIS"):
        ids = [i for i in sorted(ok) if obj[i]["b"] == b]
        dpub, dvrp, sin_k = [], [], []
        for i in ids:
            if (i, "Krun") not in P:
                sin_k.append(i)
                continue
            if bool(obj[i]["pub_prod"]) != pub(i, "Krun"):
                dpub.append((i, obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["clase"], obj[i]["pub_prod"],
                             pub(i, "Krun")))
            pk = ((res[i]["K"]["record"] or {}).get("primary_cluster") or {}).get("vrp_mw")
            po = obj[i]["pc_vrp"]
            if not ((pk is None and po is None) or (pk is not None and po is not None and abs(pk - po) <= 0.001)):
                dvrp.append((i, obj[i]["volcan"], obj[i]["hora_utc"], po, pk))
        pr(f"  K re-corrido = publicado, {b}: publica igual {len(ids) - len(sin_k) - len(dpub)} de {len(ids) - len(sin_k)}; "
           f"pc.vrp_mw a 0,001 MW {len(ids) - len(sin_k) - len(dvrp)} de {len(ids) - len(sin_k)}; sin record K: {len(sin_k)}")
        pr("    publica distinto:", dpub[:15])
        pr("    pc distinto:", dvrp[:15])
        # control positivo del port
        cp = [(i, obj[i]["volcan"], obj[i]["hora_utc"], res[i]["port"]["fisica"]["npix"], res[i]["port"]["fisica"]["vrp_mw"],
               obj[i]["mirova_vrp"]) for i in ids if obj[i]["clase"] == "pos_prot"
              and obj[i]["volcan"] in ("Lascar", "NevadosDeChillan")]
        n_cp = sum(1 for x in cp if x[3])
        pr(f"  control positivo del port {b}: protegidas de Láscar o Chillán con píxeles {n_cp} de {len(cp)}")
        motivos = collections.Counter(res[i]["port"]["fisica"]["motivo_vacio"] for i in ids)
        pr(f"  motivos de vacío del port {b} (caja física):", dict(motivos))

    # ---------------------------------------------------------- 3. lecturas por sensor
    rng = np.random.default_rng(159)
    resumen = {}
    for b in ("VIIRS375", "MODIS"):
        ids = [i for i in sorted(ok) if obj[i]["b"] == b]
        pr(f"\n================ {b} ({len(ids)} pasadas ok) ================")
        clases = ("pos_prot", "pos_bajo", "neg_pub", "neg_resto")
        for m in VARIANTES[b]:
            pr(f"\n--- variante {m} ---")
            filas = []
            for i in ids:
                o = obj[i]
                p = res[i]["port"].get(m) or {}
                ratio = None
                if pub(i, m) and o["mirova_vrp"]:
                    ratio = p["vrp_mw"] / o["mirova_vrp"]
                band = p.get("vrp_banda")
                amb = bool(p.get("npix") and band and (band[0] <= 0 < band[1] or band[0] < 0 <= band[1]))
                filas.append({"i": i, "c": o["clase"], "w": o["peso"], "K": bool(o["pub_prod"]), "X": pub(i, m),
                              "ratio": ratio, "amb": amb, "npix": p.get("npix"), "vrp": p.get("vrp_mw"),
                              "band": band, "mir": o["mirova_vrp"], "vol": o["volcan"], "z": o["estrato_z"],
                              "h": o["hora_utc"], "part": o.get("partida"),
                              "Kdisp": None})
            resumen[(b, m)] = lecturas(b, m, filas, rng, principal=(m == "fisica"))
            if m == "fisica":
                estratos(b, filas)
    # K magnitud (lo que muestra el tablero) para comparar con R4
    for b in ("VIIRS375", "MODIS"):
        ids = [i for i in sorted(ok) if obj[i]["b"] == b and obj[i]["lab"] == "pos" and (i, "Krun") in P]
        rk = [P[(i, "Krun")][1] / obj[i]["mirova_vrp"] for i in ids if P[(i, "Krun")][0] and obj[i]["mirova_vrp"]]
        if rk:
            q = np.percentile(rk, [25, 50, 75])
            pr(f"\nK (re-corrido, mirovaEqVrpDisplay) / MIROVA en {b}, alertas que K publica: mediana {q[1]:.3f} "
               f"[{q[0]:.3f}, {q[2]:.3f}] n {len(rk)}; en [0,8; 1,25]: {sum(0.8 <= x <= 1.25 for x in rk)}")
    Path(a.salida).write_text("\n".join(L) + "\n", encoding="utf-8")
    (AQUI / "resumen.json").write_text(json.dumps({f"{b}|{m}": v for (b, m), v in resumen.items()}, indent=1,
                                                  default=float), encoding="utf-8")


def ponderado(filas, f):
    w = sum(x["w"] for x in filas)
    return (sum(x["w"] for x in filas if f(x)) / w) if w else float("nan")


def boot(filas, est, rng, n=2000):
    por = collections.defaultdict(list)
    for x in filas:
        por[x["c"]].append(x)
    vals = []
    for _ in range(n):
        s = []
        for c, lst in por.items():
            s += [lst[k] for k in rng.integers(0, len(lst), len(lst))]
        vals.append(est(s))
    vals = [v for v in vals if not (isinstance(v, float) and math.isnan(v))]
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) if vals else (float("nan"),) * 2


def lecturas(b, m, filas, rng, principal):
    pos = [x for x in filas if x["c"] in ("pos_prot", "pos_bajo")]
    prot = [x for x in filas if x["c"] == "pos_prot"]
    bajo = [x for x in filas if x["c"] == "pos_bajo"]
    neg = [x for x in filas if x["c"] in ("neg_pub", "neg_resto")]
    out = {}
    # R1
    perd = [x for x in prot if x["K"] and not x["X"]]
    gan = [x for x in prot if not x["K"] and x["X"]]
    out["R1_perdidas"] = len(perd)
    pr(f"R1 protegidas que K publica y el port no: {len(perd)} de {sum(x['K'] for x in prot)} (muestra); "
       f"ganadas {len(gan)} de {sum(not x['K'] for x in prot)}")
    if perd and principal:
        pr("    perdidas:", [(x["vol"], x["h"], x["npix"], x["vrp"], x["mir"]) for x in perd])
    # R2
    for nombre, lst, vara in (("todas", pos, VARA_R2["todas"]), ("prot", prot, VARA_R2["prot"]), ("bajo", bajo, None)):
        k = sum(x["X"] for x in lst)
        kk = sum(x["K"] for x in lst)
        wl = wilson(k, len(lst))
        pw = ponderado(lst, lambda x: x["X"])
        bw = boot(lst, lambda s: ponderado(s, lambda x: x["X"]), rng, 1000)
        pk = ponderado(lst, lambda x: x["K"])
        if vara is None:
            ver = "(sin vara)"
        elif max(wl[1], bw[1]) < vara:
            ver = "NO REPRODUCE"
        else:
            ver = "REPRODUCE"
        out[f"R2_{nombre}"] = {"crudo": [k, len(lst)], "wilson": wl, "ponderado": pw, "ic_pond": bw, "K_pond": pk,
                               "K_crudo": kk, "veredicto": ver}
        pr(f"R2 recall {nombre}: port {k} de {len(lst)} (Wilson {wl[0]:.3f} a {wl[1]:.3f}); ponderado {pw:.3f} "
           f"[{bw[0]:.3f}, {bw[1]:.3f}]; K {kk} de {len(lst)} (pond {pk:.3f}); vara V750 "
           f"{'' if vara is None else round(vara, 3)} -> {ver}")
    # R3
    kp, kn = K_POB_NEG[b]
    tasa_k = kp / kn
    pw = ponderado(neg, lambda x: x["X"])
    bw = boot(neg, lambda s: ponderado(s, lambda x: x["X"]), rng)
    ver = "NO REPRODUCE" if bw[0] > tasa_k else "REPRODUCE"
    enc = [x for x in neg if x["X"] and not x["K"]]
    apa = [x for x in neg if x["K"] and not x["X"]]
    out["R3"] = {"ponderado": pw, "ic": bw, "K": tasa_k, "crudo": [sum(x["X"] for x in neg), len(neg)],
                 "encendidos_crudo": len(enc), "apagados_crudo": len(apa), "veredicto": ver}
    pr(f"R3 negativos limpios publicados: port {sum(x['X'] for x in neg)} de {len(neg)} crudo; ponderado {pw:.4f} "
       f"[{bw[0]:.4f}, {bw[1]:.4f}] contra K {tasa_k:.4f} ({kp} de {kn}) -> {ver}; encendidos {len(enc)}, apagados "
       f"{len(apa)} (crudo)")
    if principal and enc:
        pr("    encendidos:", [(x["vol"], x["h"], x["c"], x["npix"], round(x["vrp"], 3), x["band"]) for x in enc][:30])
    # R4
    rr = [x["ratio"] for x in pos if x["ratio"] is not None]
    if rr:
        q = np.percentile(rr, [25, 50, 75])
        dentro = sum(0.8 <= r <= 1.25 for r in rr)
        if 0.95 <= q[1] <= 1.05 and dentro >= 0.75 * len(rr):
            ver = "REPRODUCE"
        elif not (0.8 <= q[1] <= 1.25):
            ver = "NO REPRODUCE"
        else:
            ver = "PARCIAL"
        bm = boot([x for x in pos if x["ratio"] is not None], lambda s: float(np.median([x["ratio"] for x in s])), rng, 1000)
        out["R4"] = {"mediana": q[1], "q1": q[0], "q3": q[2], "n": len(rr), "dentro": dentro, "ic_mediana": bm,
                     "veredicto": ver}
        pr(f"R4 razón port/MIROVA: mediana {q[1]:.3f} [{q[0]:.3f}, {q[2]:.3f}] n {len(rr)} (IC de la mediana "
           f"{bm[0]:.3f} a {bm[1]:.3f}); en [0,8; 1,25] {dentro} de {len(rr)} -> {ver}")
        for npx, nom in ((1, "1 px"), (2, "2 a 4 px"), (5, "5+ px")):
            sub = [x for x in pos if x["ratio"] is not None and
                   ((npx == 1 and x["npix"] == 1) or (npx == 2 and 2 <= x["npix"] <= 4) or (npx == 5 and x["npix"] >= 5))]
            if sub:
                qq = np.percentile([x["ratio"] for x in sub], [25, 50, 75])
                pr(f"    {nom}: mediana {qq[1]:.3f} [{qq[0]:.3f}, {qq[2]:.3f}] n {len(sub)}; a menos de 5 %: "
                   f"{sum(abs(x['ratio'] - 1) < 0.05 for x in sub)}")
    else:
        out["R4"] = {"n": 0, "veredicto": "SIN DATO"}
        pr("R4: el port no publica ninguna alerta: SIN DATO")
    # ambiguas por triangulación
    am = [x for x in filas if x["amb"]]
    pr(f"pasadas ambiguas por la triangulación (la banda cruza 0): {len(am)}",
       [(x["vol"], x["h"], x["c"], x["band"]) for x in am][:10])
    # MISSION
    def dE(s):
        bp = sum(x["w"] for x in s if x["c"] == "pos_bajo" and x["K"] and not x["X"])
        bg = sum(x["w"] for x in s if x["c"] == "pos_bajo" and not x["K"] and x["X"])
        ne = sum(x["w"] for x in s if x["c"] in ("neg_pub", "neg_resto") and x["X"] and not x["K"])
        na = sum(x["w"] for x in s if x["c"] in ("neg_pub", "neg_resto") and x["K"] and not x["X"])
        return (bp - bg) + (ne - na)
    de = dE(filas)
    ic = boot(filas, dE, rng)
    if out["R1_perdidas"] > 0:
        ver = "PIERDE PROTEGIDA"
    elif de == 0:
        ver = "EMPATE"
    elif ic[1] < 0:
        ver = "GANA"
    elif ic[0] > 0:
        ver = "ENCIENDE DE MÁS"
    else:
        ver = "NO RESUELTO"
    out["MISSION"] = {"dE": de, "ic": ic, "veredicto": ver}
    pr(f"MISSION port contra K: ΔE {de:+.1f} [{ic[0]:+.1f}, {ic[1]:+.1f}] -> {ver}")
    return out


def estratos(b, filas):
    pr(f"\n  estratos {b}, caja física (crudo: port publica / n; K publica / n):")
    for clave, f in (("volcán", lambda x: x["vol"]), ("cenit", lambda x: x["z"]),
                     ("tramo A119", lambda x: "antes 06-13" if x["h"][:10] < FRONTERA_OCR else "desde 06-13")):
        if clave == "tramo A119" and b != "VIIRS375":
            continue
        g = collections.defaultdict(lambda: collections.Counter())
        for x in filas:
            k = (f(x), "pos" if x["c"].startswith("pos") else "neg")
            g[k]["n"] += 1
            g[k]["X"] += x["X"]
            g[k]["K"] += x["K"]
        pr(f"   por {clave}:", {f"{k[0]}|{k[1]}": f"{v['X']}/{v['K']}/{v['n']}" for k, v in sorted(g.items())})
    part = [x for x in filas if x["part"]]
    pr("   partidas (aparte):", [(x["vol"], x["h"], x["c"], "port" if x["X"] else "-", "K" if x["K"] else "-")
                                for x in part])


if __name__ == "__main__":
    main()
