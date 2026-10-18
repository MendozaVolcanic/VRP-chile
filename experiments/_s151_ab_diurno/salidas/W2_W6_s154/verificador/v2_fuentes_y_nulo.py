# -*- coding: utf-8 -*-
"""Verificador con contexto limpio del A/B diurno (D-10). Sólo lee.

1. Re-arma la clasificación de pasadas con las funciones del evaluador (mismo universo, mismo predicado
   del tablero con node) y además con un pareo propio a 120 s escrito acá, para comparar.
2. Para cada publicación diurna del brazo diurno: de qué camino viene (final_hotspot_source del ancla
   honesta: ctx_cluster = cúmulo contextual de los Tests 2 y 3; test1_roi / test1_nti_peak = sólo el Test 1
   integrado dio posición), triggered_test1 y diagnósticos de los pasos contextuales.
3. Contrafactual «sin Test 1»: sólo cuentan como publicadas las que traen cúmulo contextual (ctx_cluster).
   Recalcula M1, q_neg, G2 con eso.
4. Nulo exacto de G1 (convolución de hipergeométricas por estrato, sin muestreo): P(nulo >= D observado).
5. Fuentes de las publicaciones NOCTURNAS del control en negativos limpios (M5), para ver qué satura.
Uso: python -I v2_fuentes_y_nulo.py <raiz1> ... <raizN> > salida
"""
import collections
import json
import sys
from pathlib import Path
from types import SimpleNamespace

REPO = Path(__file__).resolve().parents[5]
for p in (str(REPO), str(REPO / "scripts"), str(REPO / "experiments" / "_s151_ab_diurno")):
    sys.path.insert(0, p)
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

import evaluar_diurno as E  # noqa: E402
import banco_paridad as bp  # noqa: E402
import sustrato as S  # noqa: E402

raices = sys.argv[1:]
a = SimpleNamespace(cons=str(E.SNAP_CONS), ocr=str(E.SNAP_OCR), respaldo=str(E.RESPALDO_20260408),
                    historico=str(E.HISTORICO_RECUPERADAS))
filas, coords = E.cargar_filas(a)
inner = bp.inner_desde_html()
rc, _ = E.cargar_brazo(raices, "control", coords, inner)
rd, _ = E.cargar_brazo(raices, "diurno", coords, inner)
UW = E.universo_por_ventana(S.universo(filas, coords))
DEC = E.DECIDEN
cls = E.clasificar(UW, E.indice(rd), DEC)

# ---- pareo propio (no usa emparejar del evaluador)
por = collections.defaultdict(list)
for r in rd:
    por[(r["vol"], r["b"])].append(r)
discrep = 0
for k, c in cls.items():
    t = E.a_dt(k[2])
    cand = [r for r in por[(k[0], k[1])] if abs((r["dt"] - t).total_seconds()) <= 120]
    est = "no_procesada" if not cand else ("publicada" if min(cand, key=lambda r: abs((r["dt"] - t).total_seconds()))["pub"] else "sin_publicar")
    discrep += est != c["estado"]
print("== 1. pareo propio contra el del evaluador: %d pasadas, %d con estado distinto" % (len(cls), discrep))

for s in E.VIIRS:
    for pob in ("pos", "neg", "tabla"):
        xs = [c for k, c in cls.items() if k[1] == s and pob in c["pob"]]
        print("   %s %-5s total %d | procesadas %d | publicadas %d" % (s, pob, len(xs),
              sum(c["estado"] != "no_procesada" for c in xs), sum(c["estado"] == "publicada" for c in xs)))


def fuente(r):
    return r["raw"].get("final_hotspot_source")


# ---- 2. fuentes de las publicaciones diurnas
print("\n== 2. de qué camino vienen las publicaciones diurnas del brazo diurno (W2 a W6)")
for s in E.VIIRS:
    for pob in ("pos", "neg", "tabla"):
        pubs = [c["rec"] for k, c in cls.items() if k[1] == s and pob in c["pob"] and c["estado"] == "publicada"]
        f = collections.Counter(fuente(r) for r in pubs)
        t1 = sum(bool(r["raw"].get("triggered_test1")) for r in pubs)
        fp = sum((r["raw"].get("diag_n_first_pass_pixels") or 0) > 0 for r in pubs)
        print("   %s %-5s publicadas %4d | final_hotspot_source %s | triggered_test1 %d | con píxeles del primer pase %d"
              % (s, pob, len(pubs), dict(f), t1, fp))
# también: todos los records diurnos publicados del brazo (incluye los que no parean con la tabla)
for s in E.VIIRS:
    pubs = [r for r in rd if r["dia"] and r["b"] == s and r["pub"]
            and E.ventana_de((r["vol"], s, r["t"])) in DEC]
    print("   %s todos los records diurnos publicados: %d | fuentes %s" % (s, len(pubs), dict(collections.Counter(fuente(r) for r in pubs))))

# ---- 3. contrafactual sin Test 1
CTX = {"ctx_cluster"}


def pub_ctx(c):
    return c["estado"] == "publicada" and fuente(c["rec"]) in CTX


print("\n== 3. contrafactual «sin Test 1»: publicada sólo si el cúmulo publicado es contextual (ctx_cluster)")
for etq, ws in (("W2 a W6", DEC), ("W3 a W6", E.SIN_W2)):
    pos = [c for k, c in cls.items() if c["ventana"] in ws and "pos" in c["pob"] and c["estado"] != "no_procesada"]
    neg = [c for k, c in cls.items() if c["ventana"] in ws and "neg" in c["pob"] and c["estado"] != "no_procesada"]
    m1 = sum(pub_ctx(c) for c in pos) / len(pos)
    qn = sum(pub_ctx(c) for c in neg) / len(neg)
    print("   %s ambos sensores: M1 %d/%d = %.3f | q_neg %d/%d = %.3f" % (etq, sum(pub_ctx(c) for c in pos), len(pos), m1,
          sum(pub_ctx(c) for c in neg), len(neg), qn))
    for s in E.VIIRS:
        ps = [c for k, c in cls.items() if c["ventana"] in ws and "pos" in c["pob"] and c["estado"] != "no_procesada" and k[1] == s]
        ns = [c for k, c in cls.items() if c["ventana"] in ws and "neg" in c["pob"] and c["estado"] != "no_procesada" and k[1] == s]
        ts = [c for k, c in cls.items() if c["ventana"] in ws and "tabla" in c["pob"] and c["estado"] != "no_procesada" and k[1] == s]
        x = sum(pub_ctx(c) for c in ts)
        p = E.P_MIROVA[s][0] / E.P_MIROVA[s][1]
        print("      %s: M1 %d/%d | q_neg %d/%d | G2 tabla %d de %d (umbral de falla con ese n: %s; P(X>=x) = %.3g)"
              % (s, sum(pub_ctx(c) for c in ps), len(ps), sum(pub_ctx(c) for c in ns), len(ns), x, len(ts),
                 E.umbral_g2(len(ts), p), stats.binom.sf(x - 1, len(ts), p)))
# positivos publicados: lista con fuente
print("   positivos publicados (W2 a W6) y su fuente:")
for k, c in sorted(cls.items()):
    if "pos" in c["pob"] and c["estado"] == "publicada":
        r = c["rec"]["raw"]
        print("      %s | %s | pc %.3f MW a %s km | t1 %s | primer pase %s" % ("|".join(k), fuente(c["rec"]),
              (r.get("primary_cluster") or {}).get("vrp_mw") or 0, (r.get("primary_cluster") or {}).get("centroid_dist_km"),
              r.get("triggered_test1"), r.get("diag_n_first_pass_pixels")))


# ---- 4. nulo exacto de G1
def nulo_exacto(ws, publicado=lambda c: c["estado"] == "publicada"):
    est = collections.defaultdict(lambda: [0, 0, 0])
    xobs = 0
    for k, c in cls.items():
        if c["ventana"] not in ws or c["estado"] == "no_procesada" or not ({"pos", "neg"} & c["pob"]):
            continue
        e = est[(k[0], k[1])]
        e[0] += 1
        e[1] += "pos" in c["pob"]
        e[2] += bool(publicado(c))
        xobs += ("pos" in c["pob"]) and bool(publicado(c))
    P = sum(e[1] for e in est.values())
    N = sum(e[0] - e[1] for e in est.values())
    K = sum(e[2] for e in est.values())
    pmf = np.array([1.0])
    for n_s, p_s, k_s in est.values():
        lo, hi = max(0, p_s - (n_s - k_s)), min(p_s, k_s)
        xs = np.arange(0, hi + 1)
        f = np.zeros(hi + 1)
        f[lo:] = stats.hypergeom.pmf(xs[lo:], n_s, k_s, p_s)
        pmf = np.convolve(pmf, f)
    xs = np.arange(len(pmf))
    D = xs / P - (K - xs) / N
    dobs = xobs / P - (K - xobs) / N
    cdf = np.cumsum(pmf)
    p95_x = int(np.searchsorted(cdf, 0.95))
    return {"D_obs": dobs, "X_obs": xobs, "P": P, "N": N, "K": K, "media_D": float((pmf * D).sum()),
            "P(nulo>=D)": float(pmf[xobs:].sum()), "P(nulo>D)": float(pmf[xobs + 1:].sum()),
            "cuantil95_D": float(D[p95_x])}


print("\n== 4. nulo EXACTO de G1 (convolución de hipergeométricas por volcán x sensor)")
for etq, ws in (("W2 a W6", DEC), ("W3 a W6", E.SIN_W2)):
    print("   %s: %s" % (etq, nulo_exacto(ws)))
    print("   %s contrafactual sin Test 1: %s" % (etq, nulo_exacto(ws, pub_ctx)))

# ---- 5. fuentes de la publicación nocturna del control en negativos limpios (M5)
print("\n== 5. control, noches, negativos limpios (M5): fuentes de lo publicado")
cnt = collections.Counter()
for w in DEC:
    c = E.VENTANA[w]
    with E.flag_viirs(False):
        pv, ns, nv, _ = bp.indexar_referencia(filas, coords, (c["desde"], c["hasta"]))
    recs = [dict(r) for r in rc if not r["dia"] and r["vol"] in c["vols"] and c["desde"] <= r["t"][:10] <= c["hasta"]]
    bp.etiquetar(recs, pv, ns, nv)
    for r in recs:
        if r["lab"] == "neg_limpio":
            cnt[(r["b"], "n")] += 1
            if r["pub"]:
                cnt[(r["b"], "pub")] += 1
                cnt[(r["b"], fuente(r))] += 1
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    print("   %s: publica %d de %d | fuentes %s" % (b, cnt[(b, "pub")], cnt[(b, "n")],
          {k[1]: v for k, v in cnt.items() if k[0] == b and k[1] not in ("n", "pub")}))

# ---- 6. Láscar: el estrato con más positivos
print("\n== 6. W2 (sólo OCR) contra el resto, contrafactual: positivos publicados por ctx_cluster")
for w in DEC:
    ps = [c for k, c in cls.items() if c["ventana"] == w and "pos" in c["pob"] and c["estado"] != "no_procesada"]
    print("   %s: %d positivos, publicados %d, por ctx_cluster %d" % (w, len(ps), sum(c["estado"] == "publicada" for c in ps), sum(pub_ctx(c) for c in ps)))
