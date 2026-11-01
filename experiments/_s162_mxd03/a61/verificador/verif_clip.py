# -*- coding: utf-8 -*-
"""¿La diferencia de SUM(L) del grupo 2 la explica el recorte dL>=0 (process_modis.py:1118) de un pixel marginal,
y no un cambio de pixel? Bajo recorte: dSUM = k * (Lbg_X - Lbg_K) con k entero en [0, n]. Bajo cambio de pixel: k
no entero y sin relacion con el fondo. P1: el control positivo (npx distinto) da k lejos de entero. P2: grupo 1 da k~0.
Uso: python -I verif_clip.py"""
import csv, glob, io, json, math, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ART = Path(r"D:\vrp-trabajo\temporales\s162_mxd03\tandas"); EXP = Path(r"C:\vrp-trabajo\s162-a61\experiments\_s162_mxd03")
C1, C2, LAM = 1.191042e8, 1.4387752e4, 3.929
pl = lambda t: C1 / (LAM ** 5 * (math.exp(C2 / (LAM * t)) - 1))
sl = lambda b: b["pc_vrp"] / 18.9 + b["pc_n_pixels"] * pl(b["t_bg_k"])
tab = {(f["vol"], f["dt"]): f for f in csv.DictReader(open(EXP / "a61" / "a61_protegidas.csv", encoding="utf-8"))}
def grupo(f):
    if f["K_npx"] == "1" and f["X_npx"] == "1" and f["pico_es_pcK"] == "True" and f["pico_es_pcX"] == "True": return 1
    if f["K_npx"] == f["X_npx"] and float(f["residuo_km"]) < 0.3: return 2
    return 3
for p in sorted(glob.glob(str(ART / "**" / "ab_parte*.jsonl"), recursive=True)):
    for l in open(p, encoding="utf-8"):
        r = json.loads(l)
        if r.get("tipo") != "record" or r.get("lab") != "protegida" or r["pub"]["K"] != 1: continue
        K, X = r["brazos"]["K"], r["brazos"]["X"]
        g = grupo(tab[(r["vol"], r["dt"])])
        if g == 1: continue
        dS = sl(X) - sl(K); dB = pl(X["t_bg_k"]) - pl(K["t_bg_k"])
        print("g%d %s %s npx %s/%s t_bg %.2f/%.2f | dSUM %+.5f dLbg %+.5f k=dSUM/dLbg %+.2f | pc_vrp %.3f/%.3f" % (
            g, r["vol"][:7], r["dt"], K["pc_n_pixels"], X["pc_n_pixels"], K["t_bg_k"], X["t_bg_k"], dS, dB, dS / dB if dB else float("nan"), K["pc_vrp"], X["pc_vrp"]))
