# -*- coding: utf-8 -*-
"""Comprobaciones cortas: H2 cenit > 65,6 por granulo; H6 modulos de R > 20 km; H3 halo de zoom con bloque -999;
H4 distribucion X/K de pc_vrp; E3 K->VIIRS; M9 el record bajo1 en el borde. Uso: python -I verif_extra.py"""
import glob, io, json, math, statistics, sys, collections
from pathlib import Path
import numpy as np
from scipy.ndimage import zoom
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ART = Path(r"D:\vrp-trabajo\temporales\s162_mxd03\tandas"); EXP = Path(r"C:\vrp-trabajo\s162-a61\experiments\_s162_mxd03")
ok = []
for p in sorted(glob.glob(str(ART / "**" / "ab_parte*.jsonl"), recursive=True)):
    for l in open(p, encoding="utf-8"):
        r = json.loads(l)
        if r.get("tipo") == "record" and r.get("estado") == "ok": ok.append(r)
hz = [(r["vol"], r["dt"], r["z"], r["clave"], r.get("n_fill_mxd03", 0), r["desplazamiento"]["km"]) for r in ok if r["z"] is not None and r["z"] > 65.6]
print("H2 z>65,6: %d | granulos %s | n_fill>0 en %d" % (len(hz), sorted({x[3] for x in hz}), sum(1 for x in hz if x[4] > 0)))
print("   max z sin relleno: %.2f | max desp sin relleno: %.2f km" % (max(r["z"] for r in ok if not r.get("n_fill_mxd03")), max(r["desplazamiento"]["km"] for r in ok if not r.get("n_fill_mxd03"))))
print("   desp > 11,45 km: %s" % sorted((round(r["desplazamiento"]["km"], 1), r["clave"], r.get("n_fill_mxd03", 0)) for r in ok if r["desplazamiento"]["km"] > 11.45))
big = [(r["vol"], r["dt"], n["km_pedido"]) for r in ok if r.get("r_nulos") for n in (r.get("nulos") or [])[:1] if n["km_pedido"] > 20]
print("H6 records con R y modulo pedido > 20 km: %s | records con R: %d" % (big, sum(1 for r in ok if r.get("r_nulos"))))
c = np.zeros((406, 271), np.float32) + np.linspace(-30, -20, 406)[:, None]
c[100:130, :] = -999.0
f = zoom(c, (2030 / 406, 1354 / 271), order=1)
col = f[:, 600]
exact = np.where(col == -999.0)[0]; cont = np.where((col < -40) & (col != -999.0))[0]
print("H3 sintetico: lineas -999 exacto %d..%d (%d) | contaminadas %s | lineas reales del bloque 5*100+2=%d a 5*129+2=%d" % (exact.min(), exact.max(), len(exact), cont.tolist(), 502, 647))
P = [r for r in ok if r["lab"] == "protegida" and r["pub"]["K"] == 1 and r["brazos"]["X"] and r["brazos"]["X"].get("pc_vrp")]
q = sorted((r["brazos"]["X"]["pc_vrp"] / r["brazos"]["K"]["pc_vrp"], r["vol"], r["dt"]) for r in P)
print("H4 X/K pc_vrp (n %d): min %.3f %s | max %.3f %s | |X/K-1|>0,10: %d | >0,20: %d" % (len(q), q[0][0], q[0][1:], q[-1][0], q[-1][1:], sum(1 for x in q if abs(x[0]-1) > .1), sum(1 for x in q if abs(x[0]-1) > .2)))
vara = json.load(open(EXP / "vara_viirs_mxd03.json", encoding="utf-8"))
def hav(a, b, c_, d):
    p1, p2 = math.radians(a), math.radians(c_)
    x = math.sin(math.radians(c_ - a) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))
kv, xv = [], []
for r in P:
    vv = vara["granulos"].get("%s|%s" % (r["vol"], r["clave"]))
    if not vv: continue
    ps = vv["estricta"]["pasadas"] or vv["amplia"]["pasadas"]
    if not ps: continue
    la, lo = statistics.median(p["lat"] for p in ps), statistics.median(p["lon"] for p in ps)
    kv.append(hav(r["brazos"]["K"]["pc_lat"], r["brazos"]["K"]["pc_lon"], la, lo)); xv.append(hav(r["brazos"]["X"]["pc_lat"], r["brazos"]["X"]["pc_lon"], la, lo))
print("E3 n %d | K->VIIRS mediana %.2f | X->VIIRS mediana %.2f max %.3f | X<K en %d" % (len(kv), statistics.median(kv), statistics.median(xv), max(xv), sum(1 for a, b in zip(kv, xv) if b < a)))
sinv = [ (r["vol"], r["dt"]) for r in P if not (vara["granulos"].get("%s|%s" % (r["vol"], r["clave"])) or {}).get("estricta", {}).get("pasadas") and not (vara["granulos"].get("%s|%s" % (r["vol"], r["clave"])) or {}).get("amplia", {}).get("pasadas")]
print("   sin vara: %s" % sinv)
b = [r for r in ok if r["lab"] == "bajo1" and (r["desplazamiento"]["linea"] in (0, 1, 2028, 2029) or r["desplazamiento"]["frame"] in (0, 1353))]
for r in b:
    print("M9 bajo1 en borde: %s %s %s linea %d frame %d z %.1f | K n_anom %s anillo %s pub %s | X n_anom %s pub %s" % (r["vol"], r["dt"], r["clave"], r["desplazamiento"]["linea"], r["desplazamiento"]["frame"], r["z"], r["brazos"]["K"]["n_anom"], r["brazos"]["K"]["diag_n_bg_anillo"], r["pub"]["K"], r["brazos"]["X"]["n_anom"], r["pub"]["X"]))
lab = collections.Counter(r["lab"] for r in ok if (r["desplazamiento"]["linea"] in (0, 2029) or r["desplazamiento"]["frame"] in (0, 1353)))
print("M9 solo linea 0/2029 o frame 0/1353: %s" % dict(lab))
