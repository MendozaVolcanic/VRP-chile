# -*- coding: utf-8 -*-
"""Verificador S173 (ver_ablmodis): segunda lectura.
(1) K y V con la magnitud que PUBLICA el tablero (primary_cluster.vrp_mw; para la via es la misma que vrp_mw):
    medias y medianas por tramo, Spearman, ceros. Compara con la de vrp_mw (suma de escena) de releer.py.
(2) Brazo propio NAT_G5 contra NAT (de recalcular_npz.json): si difieren, NAT y G5 comparten causa.
(3) Desplazamiento MxD03 contra 5 km en el crater, por tramo de cenit, y su Spearman con el cenit;
    G5 pc_dist_km contra V0 pc_dist_km (la caja sensible de 5 x 5 celdas del crater: +-2 km).
(4) Los ceros: en que tramo caen, con que MIROVA, y que pasa con cada brazo en esas pasadas.
(5) FA: la caida en publicacion (FA publica 0 en 6) contra la caida en magnitud (FA/V por tramo, sin ceros).
(6) Jackknife de la DIFERENCIA de medianas por tramo (sacando una pasada) para K, FA, NAT, G5.
Denominador: 27 pasadas, 2026-09-29 a 2026-11-02.
"""
import io
import json
import sys

import numpy as np
from scipy.stats import spearmanr

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
J = "D:/vrp-trabajo/temporales/s173_aud/ablacion_modis_run/s173-cenit-modis/s173_cenit_modis.json"
P = json.load(open(J, encoding="utf-8"))["pasadas"]
RC = {f["dt"]: f for f in json.load(open("C:/Users/nmend/vrp-wt/s173_cenit/ver_ablmodis/recalcular_npz.json", encoding="utf-8"))}
z = np.array([e["z_record"] for e in P]); m = np.array([e["vrp_mirova_mw"] for e in P]); dts = [e["dt"] for e in P]
lo, hi = z < 30, z >= 30


def pc(e, b):
    v = e[b].get("pc_vrp_mw") if b in ("K", "V") else e["brazos"][b].get("pc_vrp_mw")
    return float(v or 0.0)


def resumen(nombre, r):
    out = f"{nombre:10s}"
    for sel in (lo, hi):
        rr = r[sel]; nz = rr[rr > 0]
        out += f" | mediana {np.median(rr):.3f} media {rr.mean():.3f} media_s0 {nz.mean() if len(nz) else float('nan'):.3f} n0 {int((rr == 0).sum())}"
    rho = spearmanr(r, z).correlation
    rng = np.random.default_rng(173)
    perm = np.array([spearmanr(r, rng.permutation(z)).correlation for _ in range(200)])
    out += f" | rho {rho:+.3f} nulo95 [{np.percentile(perm, 2.5):+.2f},{np.percentile(perm, 97.5):+.2f}]"
    return out


print("== (1) magnitud publicada (pc.vrp_mw) / MIROVA")
rK = np.array([pc(e, "K") / e["vrp_mirova_mw"] for e in P])
rKsum = np.array([float(e["K"]["vrp_mw"] or 0) / e["vrp_mirova_mw"] for e in P])
rV = np.array([pc(e, "V") / e["vrp_mirova_mw"] for e in P])
print(resumen("K pc", rK)); print(resumen("K suma", rKsum)); print(resumen("V pc", rV))
print("  K: pc != suma de escena en", int((rK != rKsum).sum()), "pasadas; V: pc != vrp_mw en", sum(pc(e, "V") != float(e["V"]["vrp_mw"] or 0) for e in P))
print("  K pc por pasada:", [(dts[i], round(z[i], 1), round(rK[i], 3)) for i in range(27)])
print("  K pc >=30 sin las 2 del 2026-11-02 (produccion ya era V): mediana", round(float(np.median(rK[hi & ~np.array([d.startswith('2026-11-02') for d in dts])])), 3), "n", int((hi & ~np.array([d.startswith('2026-11-02') for d in dts])).sum()))
# razon con lo que publico produccion (disp_mw de la lista) : del JSON del arnes no esta; se reconstruye del record guardado
rG = np.array([float((e["guardado"] or {}).get("pc_vrp_mw") or 0) / e["vrp_mirova_mw"] for e in P])
print(resumen("guardado pc", rG))

print("\n== (2) NAT_G5 contra NAT (recalculo propio desde los npz)")
dif = [(d, f["NAT_vrp"], f["NAT_G5_vrp"]) for d, f in RC.items() if f["NAT_vrp"] != f["NAT_G5_vrp"] or f["NAT_npix"] != f["NAT_G5_npix"]]
print("  pasadas con NAT_G5 != NAT (vrp o npix):", len(dif), dif)
print("  NAT_G5 dcum vs NAT dcum (km):", [(d[:16], round(f["NAT_dcum"] or -1, 2), round(f["NAT_G5_dcum"] or -1, 2)) for d, f in RC.items() if f["NAT_dcum"] is not None])

print("\n== (3) desplazamiento MxD03 vs 5 km en el crater (km) por tramo; G5 pc_dist vs V0 pc_dist")
dd = np.array([RC[d]["despl_km_mxd03_vs_5km"] for d in dts])
print(f"  <30: mediana {np.median(dd[lo]):.2f} min {dd[lo].min():.2f} max {dd[lo].max():.2f} | >=30: mediana {np.median(dd[hi]):.2f} min {dd[hi].min():.2f} max {dd[hi].max():.2f} | rho(despl, cenit) {spearmanr(dd, z).correlation:+.3f}")
print("  por pasada (dt, z, despl km, G5 pc_dist, V0 pc_dist, G5 npix, V0 npix):",
      [(dts[i][:16], z[i], dd[i], RC[dts[i]]["G5_pc_dist_km"], P[i]["brazos"]["V0"]["pc_dist_km"], RC[dts[i]]["G5_npix"], RC[dts[i]]["V0_npix"]) for i in range(27)])
g5v = np.array([RC[d]["G5_vrp"] for d in dts]) / np.array([RC[d]["V0_vrp"] for d in dts])
print("  G5/V0 por tramo: <30 mediana", round(float(np.median(g5v[lo])), 3), ">=30 mediana", round(float(np.median(g5v[hi])), 3), "| rho(G5/V0, despl)", round(spearmanr(g5v, dd).correlation, 3), "| rho(G5/V0, cenit)", round(spearmanr(g5v, z).correlation, 3))
g5d = np.array([RC[d]["G5_pc_dist_km"] or 0 for d in dts])
print("  G5 con pc_dist > 2 km (fuera de la caja sensible de 5x5):", int((g5d > 2).sum()), "de 27; sus z:", sorted(z[g5d > 2].tolist()))

print("\n== (4) los ceros")
for b in ("K", "V"):
    print(f"  {b} pc=0:", [(dts[i], z[i], m[i], P[i][b]['npix']) for i in range(27) if pc(P[i], b) == 0])
for b in ("FA", "G5", "NAT", "NAT_AREA"):
    print(f"  {b} vrp=0:", [(dts[i], z[i], m[i], P[i]['brazos'][b]['npix']) for i in range(27) if float(P[i]['brazos'][b]['vrp_mw'] or 0) == 0])
print("  pasadas con MIROVA < 4 MW y z > 57:", [(dts[i], z[i], m[i]) for i in range(27) if m[i] < 4 and z[i] > 57])

print("\n== (5) FA: publicacion contra magnitud")
rFA = np.array([float(P[i]["brazos"]["FA"]["vrp_mw"] or 0) / m[i] for i in range(27)])
fav = np.array([float(P[i]["brazos"]["FA"]["vrp_mw"] or 0) / float(P[i]["brazos"]["V0"]["vrp_mw"]) for i in range(27)])
print("  FA publica por tramo: <30", sum(P[i]["brazos"]["FA"]["publica"] for i in range(27) if lo[i]), "de", int(lo.sum()), "| >=30", sum(P[i]["brazos"]["FA"]["publica"] for i in range(27) if hi[i]), "de", int(hi.sum()))
nz = fav > 0
print(f"  FA/V0 sin ceros: <30 mediana {np.median(fav[lo & nz]):.3f} (n {int((lo & nz).sum())}) | >=30 mediana {np.median(fav[hi & nz]):.3f} (n {int((hi & nz).sum())}) | rho(FA/V0, z) sin ceros {spearmanr(fav[nz], z[nz]).correlation:+.3f} | con ceros {spearmanr(fav, z).correlation:+.3f}")
print(f"  FA/MIROVA sin ceros: <30 mediana {np.median(rFA[lo & nz]):.3f} | >=30 mediana {np.median(rFA[hi & nz]):.3f} | rho sin ceros {spearmanr(rFA[nz], z[nz]).correlation:+.3f}")
# FA en los 6 ceros: npix > 0?
print("  FA ceros con npix:", [(dts[i], P[i]["brazos"]["FA"]["npix"], P[i]["brazos"]["V0"]["vrp_mw"]) for i in range(27) if rFA[i] == 0])

print("\n== (6) jackknife de la diferencia de medianas (<30 menos >=30), min..max al sacar una pasada")
for b, r in (("K pc", rK), ("FA", rFA), ("NAT", np.array([float(P[i]["brazos"]["NAT"]["vrp_mw"] or 0) / m[i] for i in range(27)])),
             ("G5", np.array([float(P[i]["brazos"]["G5"]["vrp_mw"] or 0) / m[i] for i in range(27)])), ("V pc", rV),
             ("RN", np.array([float(P[i]["brazos"]["RN"]["vrp_mw"] or 0) / m[i] for i in range(27)]))):
    difs = []
    for k in range(27):
        keep = np.ones(27, bool); keep[k] = False
        difs.append(np.median(r[lo & keep]) - np.median(r[hi & keep]))
    print(f"  {b:6s} dif completa {np.median(r[lo]) - np.median(r[hi]):+.3f} | jackknife {min(difs):+.3f}..{max(difs):+.3f}")

print("\n== (7) RN: cuanto mueve respecto a V0, por tramo")
rn = np.array([float(P[i]["brazos"]["RN"]["vrp_mw"] or 0) / float(P[i]["brazos"]["V0"]["vrp_mw"]) for i in range(27)])
print(f"  RN/V0 mediana <30 {np.median(rn[lo]):.3f} >=30 {np.median(rn[hi]):.3f} | min {rn.min():.3f} max {rn.max():.3f} | rho(RN/V0, z) {spearmanr(rn, z).correlation:+.3f}")
fsh = np.array([float(P[i]["brazos"]["FSH"]["vrp_mw"] or 0) / float(P[i]["brazos"]["V0"]["vrp_mw"]) for i in range(27)])
print(f"  FSH/V0 mediana <30 {np.median(fsh[lo]):.3f} >=30 {np.median(fsh[hi]):.3f} | min {fsh.min():.3f} max {fsh.max():.3f}")
print("\n== (8) t_max_k de V0 bajo 273,15 K (regla de cirrus del tablero) por pasada:", [(d, f["V0_t_max_k"], f["V0_vrp"]) for d, f in RC.items() if f["V0_t_max_k"] is not None and f["V0_t_max_k"] < 273.15])
