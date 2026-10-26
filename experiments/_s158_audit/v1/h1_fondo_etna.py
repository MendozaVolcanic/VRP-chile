# -*- coding: utf-8 -*-
"""V1 (S158) verificacion de F1-H1: con los MISMOS pixeles alertados de Etna, cuanto cambia el VRP
solo por la regla del fondo (escalar mediana del anillo 5-25 km + recorte, contra interpolacion local de MIROVA).

No usa la reimplementacion de F1 (nuestro_k_en_grilla). Aisla la formula de magnitud.
Pregunta 1: si la regla del fondo fuera distinta, se veria? Si: se comparan sumas de L_bk sobre los mismos pixeles.
Pregunta 2: instrumento muerto? Control positivo: el oraculo debe dar 5 pixeles y ~9,88 MW; y nuestra formula con el
fondo de MIROVA en vez del escalar debe devolver el mismo 9,88 MW (si no, la formula/k difiere y no es el fondo).
Supuesto declarado: grilla 750 m centrada en (33,33), como F1; produccion corre en barrido nativo (D17).
"""
import os, sys, io
sys.path.insert(0, os.path.join(os.getcwd(), "experiments", "_s158_oraculo_mirova"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np, scipy.io as sio
import mirova_v750 as M

S = sio.loadmat("experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat")
m13, m15, box = S["ZI_M13"].astype(float), S["ZI_M15"].astype(float), S["BOX"]
sg = M.sunglint_angle(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())
al = M.hotspot_detection(m13, m15, box, int(S["dayflag"].item()), sg)
vrp_m, npix, dl, bk, lhot, lbk = M.vrp(m13, al)
print("dayflag", S["dayflag"].item(), "sunglint", round(sg, 2))
print("CONTROL oraculo: npix", npix, "unicos", len(set(al.tolist())), "VRP MW", round(vrp_m, 4), "Lhot", round(lhot, 6), "Lbk", round(lbk, 6))
K = 19.7 * 750.0**2 / 1e6   # WOOSTER_COEFF * area / 1e6, process_viirs_mod.py:66 y :1056
print("k nuestro (MW por unidad de L)", K, " k MIROVA", 1.97e7 * 0.5625 / 1e6)

n = m13.shape[0]; c = (n - 1) / 2
fi, co = np.indices(m13.shape)
dist = np.hypot(fi - c, co - c) * 0.75
ring = (dist >= 5) & (dist <= 25) & np.isfinite(m13)
rr, cc = np.unravel_index(np.unique(al), m13.shape, order="F")
Lh = m13[rr, cc]
print("pixeles (fila,col,dist km):", [(int(a), int(b), round(float(dist[a, b]), 2)) for a, b in zip(rr, cc)])
print("L_hot por pixel", np.round(Lh, 4))
print("L_bk MIROVA por pixel", np.round(bk[rr, cc], 4))
# nuestra regla: t_bg = mediana BT anillo; L_bg = Planck(t_bg). Mediana de BT == Planck^-1 de mediana de L
# (monotona) salvo cuenta par; se calcula por BT como el pipeline.
bt = M.radiance_to_temperature(m13, M.WAVELENGTH_M13)
t_bg = float(np.median(bt[ring]))
Lbg = float(M.temperature_to_radiance(np.float64(t_bg), M.WAVELENGTH_M13))
print("anillo n", int(ring.sum()), "t_bg mediana K", round(t_bg, 3), "L_bg escalar", round(Lbg, 5),
      " | L_bk MIROVA media en los 5", round(float(bk[rr, cc].mean()), 5))
dl_nuestro = Lh - Lbg
print("dL nuestro por pixel", np.round(dl_nuestro, 4), " recortados a 0:", int((dl_nuestro < 0).sum()))
v_clip = K * np.maximum(dl_nuestro, 0).sum()
v_noclip = K * dl_nuestro.sum()
v_mirbk = K * (Lh - bk[rr, cc]).sum()
print("VRP nuestro (escalar + recorte) MW", round(v_clip, 4))
print("VRP nuestro (escalar sin recorte) MW", round(v_noclip, 4))
print("CONTROL: nuestra k con fondo MIROVA MW", round(v_mirbk, 4), "(debe = oraculo)")
print("razon nuestro/MIROVA", round(v_clip / vrp_m, 4))
# variantes del fondo para ver si la palabra 'local' explica la brecha
for nm, msk in [("anillo 5-25 km media", ring)]:
    Lb = float(M.temperature_to_radiance(np.float64(np.mean(bt[msk])), M.WAVELENGTH_M13))
    print(nm, "VRP", round(K * np.maximum(Lh - Lb, 0).sum(), 4))
# radiance-space median for comparison
print("mediana en radiancia del anillo", round(float(np.median(m13[ring])), 5))
# perfil radial del fondo: mediana de L por corona
for a, b in [(1, 3), (3, 5), (5, 10), (10, 15), (15, 20), (20, 25)]:
    msk = (dist >= a) & (dist < b) & np.isfinite(m13)
    msk[rr, cc] = False
    print(f"corona {a}-{b} km n={int(msk.sum())} mediana L {float(np.median(m13[msk])):.5f}")

# Barrido de intensidad, SOLO magnitud: mismos pixeles alertados que MIROVA en cada f (oraculo), formula nuestra.
# Control: con f=1 debe repetir 2,748. Pregunta 2: si nuestra formula diera siempre lo mismo que MIROVA, la razon seria 1.
from scipy.ndimage import binary_dilation
mask_al = np.zeros(m13.size, bool); mask_al[al] = True
mask_al = mask_al.reshape(m13.shape, order="F")
dil = binary_dilation(mask_al, structure=np.ones((5, 5), bool))
bk13 = M._fillmissing2_linear(np.where(dil, np.nan, m13))
bk15 = M._fillmissing2_linear(np.where(dil, np.nan, m15))
print("\nBARRIDO f | MIROVA npix VRP | nuestro VRP (mismos pixeles, escalar+recorte) | pixeles con dL<=0")
for f in [1, 0.5, 0.3, 0.2, 0.15, 0.1, 0.05]:
    a13 = np.where(dil, bk13 + f * (m13 - bk13), m13)
    a15 = np.where(dil, bk15 + f * (m15 - bk15), m15)
    al2 = M.hotspot_detection(a13, a15, box, 0, sg)
    v2 = M.vrp(a13, al2)
    if v2[1] == 0:
        print(f, "MIROVA sin alerta"); continue
    r2, c2 = np.unravel_index(np.unique(al2), m13.shape, order="F")
    bt2 = M.radiance_to_temperature(a13, M.WAVELENGTH_M13)
    Lb2 = float(M.temperature_to_radiance(np.float64(np.median(bt2[ring])), M.WAVELENGTH_M13))
    d2 = a13[r2, c2] - Lb2
    print(f" {f:<5} | {v2[1]} {v2[0]:.3f} | {K*np.maximum(d2,0).sum():.3f} | {int((d2<=0).sum())} de {len(d2)}")
