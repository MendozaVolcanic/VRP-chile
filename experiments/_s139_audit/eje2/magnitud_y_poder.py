# -*- coding: utf-8 -*-
"""S139 eje 2: (1) magnitud publicada en noches positivas vs negativas por sensor y volcan, para
saber si las publicaciones en negativos son senal debil o fuerte (no se propone umbral);
(2) intervalos de Wilson del recall y de la tasa en negativos (poder del banco);
(3) diferencia minima detectable aproximada entre dos corridas pareadas.
P1: si la magnitud no importara, las medianas pos y neg serian iguales; se imprimen ambas.
P2: celdas con n=0 se marcan SIN DATO. Config: cons_ocr|pipeline|rutina_estricta, ventana ref.
"""
import collections, importlib.util, math, statistics
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("banco", HERE / "banco_noches.py")
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
coords = B._coords_por_volcan(); inner = B.inner_desde_html()
filas = B.cargar_referencia(coords); recs = B.cargar_nuestros(coords, inner)
VENT = (min(f["dt"] for f in filas).strftime("%Y-%m-%d"), max(f["dt"] for f in filas).strftime("%Y-%m-%d"))
ref, nos = B.armar(filas, recs, "cons_ocr", "pipeline", None)
_, fa = B.evaluar(ref, nos, "rutina_estricta", "pub", True, VENT)


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(p, 3), round(c - h, 3), round(c + h, 3)


print("(1) mediana de la magnitud publicada (disp, max por noche) en noches donde el dashboard publica")
for b in B.BUCKETS:
    for v in B.VOLS + ["TODOS"]:
        p = [x[3]["disp"] for x in fa if x[1] == b and (v == "TODOS" or x[0] == v) and x[2] == "pos" and x[3].get("disp", 0) > 0]
        n = [x[3]["disp"] for x in fa if x[1] == b and (v == "TODOS" or x[0] == v) and x[2] == "neg" and x[3].get("disp", 0) > 0]
        if len(p) + len(n) < 10:
            continue
        mp = round(statistics.median(p), 3) if p else "SIN DATO"
        mn = round(statistics.median(n), 3) if n else "SIN DATO"
        frac_debil = round(sum(1 for x in n if x < 0.1) / len(n), 2) if n else None
        print(f"  {b:9s} {v:20s} pos n={len(p):4d} med {mp}  | neg n={len(n):4d} med {mn}  frac neg<0,1MW {frac_debil}")

print("\n(2) Wilson 95 % por sensor (todos los volcanes) y CUALQUIERA")
t, _ = B.evaluar(ref, nos, "rutina_estricta", "pub", True, VENT)
g = B.agregar(t, "b")
for b, c in g.items():
    print(f"  {b:10s} recall {c['pos_det']}/{c['pos']} {wilson(c['pos_det'], c['pos'])}  tasa neg {c['neg_det']}/{c['neg']} {wilson(c['neg_det'], c['neg'])}")

print("\n(3) diferencia minima detectable (80 % poder, alfa 0,05, proporcion base p, n noches) = aprox 2,8*sqrt(2p(1-p)/n) [cota no pareada, conservadora]")
for b, c in g.items():
    for lab in ("pos", "neg"):
        n = c[lab]; k = c[lab + "_det"]
        if n:
            p = k / n
            mdd = 2.8 * math.sqrt(max(p * (1 - p), 1 / n) * 2 / n)
            print(f"  {b:10s} {lab}: n={n} p={p:.3f} MDD~{mdd:.3f} (= {mdd*n:.1f} noches)")
