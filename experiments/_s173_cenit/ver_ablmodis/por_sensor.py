# -*- coding: utf-8 -*-
"""Verificador S173: Spearman razon contra cenit DENTRO de cada plataforma (Terra n 10, Aqua n 17) para K (pc), NAT, G5, FA,
RN; y nulo por barajado del cenit dentro de la plataforma (200, semilla 173). Pregunta: la caida con el cenit podria ser
'Aqua contra Terra' (hora de la noche) si el tramo oblicuo fuera casi todo Aqua. Denominador: 27 pasadas."""
import io, json, sys
import numpy as np
from scipy.stats import spearmanr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
P = json.load(open("D:/vrp-trabajo/temporales/s173_aud/ablacion_modis_run/s173-cenit-modis/s173_cenit_modis.json", encoding="utf-8"))["pasadas"]
z = np.array([e["z_record"] for e in P]); m = np.array([e["vrp_mirova_mw"] for e in P]); s = np.array([e["sensor"] for e in P])
def r(b):
    if b == "K": return np.array([float(e["K"]["pc_vrp_mw"] or 0) for e in P]) / m
    if b == "V": return np.array([float(e["V"]["pc_vrp_mw"] or 0) for e in P]) / m
    return np.array([float(e["brazos"][b]["vrp_mw"] or 0) for e in P]) / m
rng = np.random.default_rng(173)
def nulo_estrat(rr):
    perm = []
    for _ in range(200):
        zz = z.copy()
        for plat in ("MODIS_TERRA", "MODIS_AQUA"):
            k = s == plat; zz[k] = rng.permutation(z[k])
        perm.append(spearmanr(rr, zz).correlation)
    return np.percentile(perm, 2.5), np.percentile(perm, 97.5)
for b in ("K", "V", "NAT", "G5", "FA", "RN", "NAT_AREA"):
    rr = r(b); out = f"{b:9s}"
    for plat in ("MODIS_TERRA", "MODIS_AQUA"):
        k = s == plat
        out += f" | {plat[6:]} n {k.sum()} rho {spearmanr(rr[k], z[k]).correlation:+.3f} med<30 {np.median(rr[k & (z<30)]):.3f} (n {(k&(z<30)).sum()}) med>=30 {np.median(rr[k & (z>=30)]):.3f} (n {(k&(z>=30)).sum()})"
    lo, hi = nulo_estrat(rr)
    out += f" | rho total {spearmanr(rr, z).correlation:+.3f} nulo95 barajado dentro de plataforma [{lo:+.2f},{hi:+.2f}]"
    print(out)
