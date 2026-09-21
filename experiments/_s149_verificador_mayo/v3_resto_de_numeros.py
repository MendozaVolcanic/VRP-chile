# -*- coding: utf-8 -*-
"""Verificador S149 (mayo). P2, P5, supervivencias, composicion de los negativos y estadisticas de la
tabla por volcan, recalculadas sobre v1 (mismas funciones). Tambien P1 por volcan y por plataforma."""
import io, sys, collections, statistics
sys.argv = [sys.argv[0], sys.argv[1]]
_real = sys.stdout
_mudo = io.TextIOWrapper(io.BytesIO()); sys.stdout = _mudo   # silencia la salida de v1 al importarlo (la referencia evita que se cierre)
import v1_reimplementacion as v
sys.stdout = io.TextIOWrapper(_real.buffer, encoding="utf-8")
B, F, claves = v.B, v.F, v.claves
L = v.etiquetar(claves, v.cons + v.ocr, True)
neg = [k for k in claves if L[k]["lab"] == "neg_limpio"]; pos = [k for k in claves if L[k]["lab"] == "pos"]
def zona(z): return "nadir" if z < 36 else ("medio" if z < 52 else "borde")
print("P2 por zona (angulo del control):")
t = {}
for zn in ("nadir", "medio", "borde"):
    s = [k for k in neg if zona(B[k]["z"]) == zn]; t[zn] = (sum(B[k]["pub"] for k in s), sum(F[k]["pub"] for k in s), len(s)); print("   ", zn, t[zn])
print("   razon B %.2f | F %.2f" % ((t["borde"][0] / t["borde"][2]) / (t["nadir"][0] / t["nadir"][2]), (t["borde"][1] / t["borde"][2]) / max(t["nadir"][1] / t["nadir"][2], 1 / t["nadir"][2])))
print("P1 por volcan (n, B, F):")
for vol in sorted({k[0] for k in neg}):
    s = [k for k in neg if k[0] == vol]; print("    %-20s %3d %3d %3d" % (vol, len(s), sum(B[k]["pub"] for k in s), sum(F[k]["pub"] for k in s)))
print("P1 por plataforma:", {p: (sum(1 for k in neg if B[k]["plat"] == p), sum(B[k]["pub"] for k in neg if B[k]["plat"] == p), sum(F[k]["pub"] for k in neg if B[k]["plat"] == p)) for p in sorted({B[k]["plat"] for k in neg})})
noche_al = {(f["vol"], f["dt"].strftime("%Y-%m-%d")) for f in v.cons + v.ocr if f["tipo"].startswith("ALERTA")}
e = [k for k in claves if L[k]["lab"] == "sin_info" and any(f["tipo"] == "RUTINA" and f["fuente"] == "CONS" and f["vrp"] == 0 for f in L[k]["ff"]) and (k[0], k[1].strftime("%Y-%m-%d")) in noche_al]
a, b = sum(B[k]["pub"] for k in e), sum(F[k]["pub"] for k in e); pubs = [k for k in claves if B[k]["pub"]]
print("P5: n %d | B %d | F %d | razon %.2f | parejo %.2f (F conserva %d de %d publicadas por B)" % (len(e), a, b, b / a, sum(F[k]["pub"] for k in pubs) / len(pubs), sum(F[k]["pub"] for k in pubs), len(pubs)))
print("F publica y B no, en todo V375:", sum(1 for k in claves if F[k]["pub"] and not B[k]["pub"]))
print("Alertas V375 de la TABLA en mayo por volcan (n, mediana, max):")
por = collections.defaultdict(list)
for f in v.cons:
    if f["tipo"].startswith("ALERTA"): por[f["vol"]].append(f["vrp"])
for vol, x in sorted(por.items()): print("    %-20s %3d %.2f %.2f" % (vol, len(x), statistics.median(x), max(x)))
print("Noches (volcan, noche) con alerta de la tabla V375 donde B publica alguna pasada positiva y F ninguna:")
nB = collections.defaultdict(int); nF = collections.defaultdict(int)
for k in pos:
    if any(f["fuente"] == "CONS" for f in L[k]["al"]):
        n = (k[0], k[1].strftime("%Y-%m-%d")); nB[n] += B[k]["pub"]; nF[n] += F[k]["pub"]
print("    noches con B>0: %d | de esas con F=0: %s" % (sum(1 for n in nB if nB[n]), [n for n in nB if nB[n] and not nF[n]]))
