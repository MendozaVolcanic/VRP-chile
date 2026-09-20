# -*- coding: utf-8 -*-
"""I-02. El pareo temporal: distribucion real de la diferencia de hora y quien queda sin pareja.

P1: si la tolerancia uniera pasadas distintas, se veria como una segunda moda (p. ej. ~50 o ~100 min,
    la separacion entre plataformas VIIRS) o como pasadas con 2+ filas de referencia en la ventana.
P2: control muerto: desplazo NUESTRAS horas +37 min; el pareo a 2 min debe caer a casi 0.
"""
import sys, io, json, collections, bisect
from pathlib import Path
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
A = Path(__file__).parent
recs = json.load(open(A / "_cache_recs.json", encoding="utf-8"))
ref = [f for f in json.load(open(A / "_cache_ref.json", encoding="utf-8")) if not f["diurna"]]
for r in recs: r["t"] = datetime.fromisoformat(r["dt"]).replace(tzinfo=None)
for f in ref: f["t"] = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S")
C = collections.Counter
idx_ref = collections.defaultdict(list); idx_rec = collections.defaultdict(list)
for f in ref: idx_ref[(f["volcano"], f["sensor_bucket"])].append(f)
for r in recs: idx_rec[(r["vol"], r["b"])].append(r)
for v in idx_ref.values(): v.sort(key=lambda x: x["t"])
for v in idx_rec.values(): v.sort(key=lambda x: x["t"])

def cercano(lista, t):
    ts = [x["t"] for x in lista]
    i = bisect.bisect_left(ts, t); best = None
    for j in (i - 1, i):
        if 0 <= j < len(lista):
            d = (lista[j]["t"] - t).total_seconds()
            if best is None or abs(d) < abs(best[0]): best = (d, lista[j])
    return best

def binm(d):
    a = abs(d) / 60
    for lim, n in ((0.5, "0"), (1.5, "1"), (2.01, "2"), (5, "2-5"), (10, "5-10"), (30, "10-30"), (75, "30-75"), (130, "75-130")):
        if a <= lim: return n
    return ">130"
ORD = ["0", "1", "2", "2-5", "5-10", "10-30", "30-75", "75-130", ">130", "sin ref"]

print("== A. Nuestra pasada -> fila de referencia mas cercana (mismo volcan y sensor generico), |dt| en min")
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    h = C(); sg = C()
    for r in recs:
        if r["b"] != b: continue
        c = cercano(idx_ref.get((r["vol"], b), []), r["t"])
        if c is None: h["sin ref"] += 1; continue
        h[binm(c[0])] += 1
        if abs(c[0]) <= 600: sg[int(round(c[0] / 60))] += 1
    print(f" {b:9s} n={sum(h.values())}", {k: h[k] for k in ORD if h[k]})
    print(f"           signo (ref - nuestro), min, dentro de +-10: ", dict(sorted(sg.items())))
print("\n== A2. Igual, por plataforma nuestra")
for s in sorted({r["sensor"] for r in recs}):
    h = C()
    for r in recs:
        if r["sensor"] != s: continue
        c = cercano(idx_ref.get((r["vol"], r["b"]), []), r["t"])
        h["sin ref" if c is None else binm(c[0])] += 1
    print(f" {s:18s} n={sum(h.values())}", {k: h[k] for k in ORD if h[k]})

print("\n== B. Fila de referencia nocturna -> pasada nuestra mas cercana")
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    for grupo, test in (("ALERTA", lambda t: t.startswith("ALERTA")), ("FP", lambda t: t.startswith("FALSO")), ("RUTINA", lambda t: t == "RUTINA")):
        h = C()
        for f in ref:
            if f["sensor_bucket"] != b or not test(f["tipo"]): continue
            c = cercano(idx_rec.get((f["volcano"], b), []), f["t"])
            h["sin ref" if c is None else binm(c[0])] += 1
        if h: print(f" {b:9s} {grupo:7s} n={sum(h.values())}", {k: h[k] for k in ORD if h[k]})
print("\n== B2. RUTINA nocturna sin pasada nuestra a 2 min, por volcan y sensor (sin / total)")
t = collections.defaultdict(lambda: [0, 0])
for f in ref:
    if f["tipo"] != "RUTINA": continue
    c = cercano(idx_rec.get((f["volcano"], f["sensor_bucket"]), []), f["t"])
    t[(f["sensor_bucket"], f["volcano"])][1] += 1
    if c is None or abs(c[0]) > 120: t[(f["sensor_bucket"], f["volcano"])][0] += 1
for k in sorted(t): print("  ", k, t[k])
print("\n== A3. Pasadas nuestras sin fila de referencia a 2 min, por volcan y sensor (sin / total / de esas publican)")
t = collections.defaultdict(lambda: [0, 0, 0])
for r in recs:
    c = cercano(idx_ref.get((r["vol"], r["b"]), []), r["t"])
    t[(r["b"], r["vol"])][1] += 1
    if c is None or abs(c[0]) > 120:
        t[(r["b"], r["vol"])][0] += 1; t[(r["b"], r["vol"])][2] += r["pub"]
for k in sorted(t): print("  ", k, t[k])
tot = collections.defaultdict(lambda: [0, 0, 0])
for (b, v), x in t.items():
    for i in range(3): tot[b][i] += x[i]
print("  TOTAL", dict(tot))

print("\n== C. Multiplicidad: filas de referencia dentro de la ventana de cada pasada nuestra, segun tolerancia")
for tol in (60, 120, 300, 600):
    m = C()
    for r in recs:
        l = idx_ref.get((r["vol"], r["b"]), [])
        n = sum(1 for f in l if abs((f["t"] - r["t"]).total_seconds()) <= tol)
        claves = {(f["fecha_utc"][:16]) for f in l if abs((f["t"] - r["t"]).total_seconds()) <= tol}
        m[len(claves)] += 1
    print(f" tol {tol:4d}s: minutos distintos de referencia por pasada ->", dict(sorted(m.items())))
print("\n== C2. Y al reves: pasadas nuestras por fila de referencia (2+ = dos granulos nuestros comparten una fila)")
for tol in (60, 120, 300, 600):
    m = C()
    for f in ref:
        if f["source"] != "CONS": continue
        l = idx_rec.get((f["volcano"], f["sensor_bucket"]), [])
        m[sum(1 for r in l if abs((r["t"] - f["t"]).total_seconds()) <= tol)] += 1
    print(f" tol {tol:4d}s:", dict(sorted(m.items())))

print("\n== D. Control de instrumento muerto: nuestras horas +37 min, pareo a 120 s")
n = 0
for r in recs:
    c = cercano(idx_ref.get((r["vol"], r["b"]), []), r["t"] + timedelta(minutes=37))
    if c and abs(c[0]) <= 120: n += 1
print(f" pareadas con desplazamiento: {n} de {len(recs)}")
print("\n== E. Separacion minima entre dos pasadas NUESTRAS consecutivas del mismo volcan y sensor generico (min)")
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    h = C()
    for (v, bb), l in idx_rec.items():
        if bb != b: continue
        for x, y in zip(l, l[1:]):
            d = (y["t"] - x["t"]).total_seconds() / 60
            h["<=2" if d <= 2 else "2-5" if d <= 5 else "5-10" if d <= 10 else "10-40" if d <= 40 else "40-60" if d <= 60 else ">60"] += 1
    print(" ", b, dict(h))
