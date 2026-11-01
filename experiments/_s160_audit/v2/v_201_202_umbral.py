#!/usr/bin/env python
"""Verificador V2 de 201 y 202, por otro camino que el auditor.

Pregunta 1 (si lo medido estuviera roto, lo veria?): parte A mide el factor de conversion
NUMERICAMENTE con la funcion real del pipeline (_nanmean_8neighbors_fast de la instantanea) contra un
port de colfilt 3x3 'omitnan' con central; si el factor no fuera 8/9 lo veria. Parte B estratifica
por dia/noche (solar_zenith_deg), por volcan y usa los C1/C2 leidos de pipeline.profile, no tecleados.
Pregunta 2 (instrumento muerto?): control negativo = poner los minimos de MIROVA como los nuestros
debe dar 0 %; control positivo = subir el minimo comparado a 1.0 debe dar 100 %.
Denominador: records con diag_mu/sd dnti/deti. Ventanas: corpus entero (todo es K desde 2025-02-15
segun frontend/cambio_detector.js) y 2026-09-18 en adelante (la del auditor).
"""
import json, os, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
SNAP = Path(r"D:\vrp-trabajo\temporales\s160_audit\main")
sys.path.insert(0, str(SNAP))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import pipeline.profile as P
from pipeline.detection_context import _nanmean_8neighbors_fast
OUT = Path(__file__).with_name("v_201_202_umbral_salida.txt")
L = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s); L.append(s)

# ---- A: factor numerico
rng = np.random.default_rng(20261022)
A = rng.normal(-0.93, 0.005, (67, 67))
A[30, 30] += 0.05  # un pixel caliente
def colfilt_nanmean_3x3(X):
    Y = np.full_like(X, np.nan); H, W = X.shape
    Xp = np.pad(X, 1, constant_values=0.0)  # colfilt rellena con 0 en bordes
    for i in range(H):
        for j in range(W):
            Y[i, j] = np.nanmean(Xp[i:i+3, j:j+3])
    return Y
cM = A - colfilt_nanmean_3x3(A)
cO = A - _nanmean_8neighbors_fast(A)
inner = (slice(1, -1), slice(1, -1))
ratio = cM[inner] / cO[inner]
p("A. factor contraste MIROVA / nuestro, interior sin NaN: min", round(float(np.nanmin(ratio)), 6),
  "max", round(float(np.nanmax(ratio)), 6), "(8/9 =", round(8/9, 6), ")")
# con un vecino NaN (pixel alertado removido en MIROVA): factor k/(k+1)
B = A.copy(); B[30, 31] = np.nan
cMb = B - colfilt_nanmean_3x3(B); cOb = B - _nanmean_8neighbors_fast(B)
p("A. con 1 vecino NaN, pixel [30,30]: factor", round(float(cMb[30, 30] / cOb[30, 30]), 6), "(7/8 =", round(7/8, 6), ")")
p("A. minimos MIROVA en nuestro espacio (x9/8): dNTI escena", 0.02*9/8, "dETI escena", 0.01*9/8,
  "cumbre", 0.003*9/8, "piso -0.1 ->", -0.1*9/8)

# ---- B: umbral efectivo por estrato
C1S, C1E = P.DNTI_CONTEXTUAL_C1_SUMMIT, P.DNTI_CONTEXTUAL_C1_SCENE
C1D = P.DNTI_CONTEXTUAL_C1_DAY
p("B. perfil efectivo: C1 cumbre", C1S, "escena", C1E, "dia", C1D, "C2 noche", P.C2_DNTI_SUMMIT_NIGHT,
  P.C2_DNTI_SCENE_NIGHT, "dia", P.C2_DNTI_DAY, "prose(max)", P.ENABLE_TESTS_23_PROSE_BRANCH)
F = 9/8
def mins(dia):
    if dia:
        return {"dnti_sce": 0.02*F, "deti_sce": 0.02*F, "dnti_sum": 0.02*F, "deti_sum": 0.02*F}
    return {"dnti_sce": 0.02*F, "deti_sce": 0.01*F, "dnti_sum": 0.003*F, "deti_sum": 0.003*F}
def nuestros(dia):
    if dia:
        return dict(c1s=C1D, c1e=C1D, c2s=P.C2_DNTI_DAY, c2e=P.C2_DNTI_DAY)
    return dict(c1s=C1S, c1e=C1E, c2s=P.C2_DNTI_SUMMIT_NIGHT, c2e=P.C2_DNTI_SCENE_NIGHT)
def bucket(s):
    s = s or ""
    return "MODIS" if s.startswith("MODIS") else "V750" if s.endswith("_750") else "V375" if s.startswith("VIIRS") else "?"
c = Counter(); cv = defaultdict(Counter); ctrl = Counter()
for fp in sorted((SNAP / "data" / "mirova_equivalent").glob("*.json")):
    d = json.load(open(fp, encoding="utf-8")); recs = d["records"] if isinstance(d, dict) else d
    for r in recs:
        mu, sd, mue, sde = (r.get(k) for k in ("diag_mu_dnti", "diag_sd_dnti", "diag_mu_deti", "diag_sd_deti"))
        if None in (mu, sd, mue, sde):
            c[("sin_diag", bucket(r.get("sensor")))] += 1; continue
        sz = r.get("solar_zenith_deg")
        dia = sz is not None and sz < 90  # convencion VRP: noche si cenit solar >= 90
        o = nuestros(dia); m = mins(dia)
        thr = {"dnti_sce": max(o["c1e"], mu + o["c2e"]*sd), "deti_sce": max(o["c1e"], mue + o["c2e"]*sde),
               "dnti_sum": max(o["c1s"], mu + o["c2s"]*sd), "deti_sum": max(o["c1s"], mue + o["c2s"]*sde)}
        dt = r.get("datetime_utc") or ""
        b = bucket(r.get("sensor")); dn = "dia" if dia else "noche"
        for w in ["todo"] + (["desde0918"] if dt >= "2026-09-18" else []):
            k = (w, b, dn); c[(k, "n")] += 1
            for nm, t in thr.items():
                if t < m[nm] - 1e-12: c[(k, nm)] += 1
            # ambos tests de escena laxos a la vez (lo que importa para un pixel de escena)
            if thr["dnti_sce"] < m["dnti_sce"] - 1e-12 and thr["deti_sce"] < m["deti_sce"] - 1e-12:
                c[(k, "AMBOS_sce")] += 1
            if w == "todo" and not dia:
                cv[fp.stem][(b, "n")] += 1
                if thr["dnti_sce"] < m["dnti_sce"]: cv[fp.stem][(b, "dnti_sce")] += 1
            # controles
            ctrl[(w, "n")] += 1
            thr_ctl = max(m["dnti_sce"], mu + o["c2e"]*sd)
            if thr_ctl < m["dnti_sce"] - 1e-12: ctrl[(w, "neg")] += 1
            if thr["dnti_sce"] < 1.0: ctrl[(w, "pos")] += 1
p("B. sin diag:", {k: v for k, v in c.items() if k[0] == "sin_diag"})
for k in sorted({k for (k, x) in c if x == "n" and k != "sin_diag"}):
    n = c[(k, "n")]
    p(f"B. {k} n={n} | " + " ".join(f"{nm}={100*c[(k,nm)]/n:.1f}%" for nm in
      ["dnti_sce", "deti_sce", "AMBOS_sce", "dnti_sum", "deti_sum"]))
for w in ["todo", "desde0918"]:
    n = ctrl[(w, "n")]
    p(f"CONTROL {w}: negativo (minimos MIROVA como nuestros) {ctrl[(w,'neg')]}/{n}; positivo (vara 1.0) {ctrl[(w,'pos')]}/{n}")
p("C. por volcan, noche, todo, dnti_sce laxo %:")
for v in sorted(cv):
    p("  ", v, " ".join(f"{b}={100*cv[v][(b,'dnti_sce')]/cv[v][(b,'n')]:.0f}%(n={cv[v][(b,'n')]})"
                       for b in ["MODIS", "V375", "V750"] if cv[v][(b, "n")]))
OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
