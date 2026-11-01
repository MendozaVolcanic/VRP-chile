# -*- coding: utf-8 -*-
"""F1 (S158): la pasada de Etna de MIROVA (ejemplo OSF) por el código de MIROVA y por nuestra cadena K.

Pregunta del instrumento 1: si nuestra cadena difiriera de MIROVA en detección o magnitud, ¿se vería?
Sí: se comparan los índices de píxel alertados y el VRP, sobre la misma matriz. Control positivo: el oráculo
debe dar 5 píxeles y 9.880.936 W (README del oráculo); si no, el instrumento está roto y nada vale.
Pregunta 2: si el instrumento estuviera muerto (nuestra cadena no corriera) daría 'rechazo' o 0 píxeles,
distinto de un resultado con píxeles; se imprime explícito.

Barrido débil: la anomalía se escala con f (L' = L_bk + f (L - L_bk), fondo = interpolación de MIROVA con
la dilatación de 5) en M13 y M15, para ver dónde cada detector deja de ver el foco. Etna es fuerte (README);
el barrido es lo que da una pasada débil con la que comparar umbrales.

Uso: python -B experiments/_s158_audit/f1/etna_k_contra_mirova.py
"""
import os, sys
os.environ["VRP_PROFILE"] = "mirova_equivalent"
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), "experiments", "_s158_oraculo_mirova"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
import scipy.io as sio
from scipy.ndimage import binary_dilation
import mirova_v750 as M
from nuestro_k_en_grilla import nuestro_k

S = sio.loadmat("experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat")
m13, m15, box = S["ZI_M13"].astype(float), S["ZI_M15"].astype(float), S["BOX"]
sg = M.sunglint_angle(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())


def mirova(a13, a15):
    al, dg = M.hotspot_detection(a13, a15, box, 0, sg, devolver_diag=True)
    v = M.vrp(a13, al)
    return al, v, dg


def ij(lin, shape=(67, 67)):
    return sorted(zip(*np.unravel_index(np.asarray(lin, int), shape, order="F")))


al, v, dg = mirova(m13, m15)
print("CONTROL oráculo: npix", v[1], "VRP W", round(v[0] * 1e6, 1), "(esperado 5 y 9.880.936)")
print("  alertas MIROVA (fila, col):", ij(al), "absolutas:", dg["n_absolutas"], "pase1", dg["n_pase1"], "pase2", dg["n_pase2"])
print("  umbrales pase1:", {k: round(x, 5) for k, x in dg["pase1"].items() if k.startswith("thr") or k.startswith("mu") or k.startswith("sd")})
for inner, box_half in ((5.0, None), (2.625, None), (5.0, 2.625), (20.0, None)):
    o = nuestro_k(m13, m15, inner_km=inner, roi1_box_half_km=box_half)
    if "rechazo" in o:
        print("NUESTRO inner", inner, "RECHAZO", o["rechazo"]); continue
    nh = list(zip(*np.where(o["hot"])))
    print(f"NUESTRO K inner={inner} caja={box_half}: t_bg {o['t_bg']:.2f} K  fp {o['n_fp']} sp_nuevos {o['n_sp_new']} "
          f"| pixeles {len(nh)} {sorted(nh)[:12]} | VRP record {o['vrp_record']:.3f} MW sin recorte "
          f"{o.get('vrp_sin_recorte', 0):.3f} | pc {o['pc']} | publicado {o['publicado']} MW")
    print(f"   mu/sd dNTI {o['mu_dnti']:.2e}/{o['sd_dnti']:.2e}  mu/sd dETI {o['mu_deti']:.2e}/{o['sd_deti']:.2e}")

# Fondo de MIROVA para escalar la anomalía (dilatación 5 por npix=5, interpolación lineal)
mask_al = np.zeros(m13.size, bool); mask_al[al] = True
mask_al = mask_al.reshape(m13.shape, order="F")
dil = binary_dilation(mask_al, structure=np.ones((5, 5), bool))
bk13 = M._fillmissing2_linear(np.where(dil, np.nan, m13))
bk15 = M._fillmissing2_linear(np.where(dil, np.nan, m15))
print("\nBARRIDO DÉBIL f (anomalía escalada en M13 y M15 dentro de la dilatación)")
print(" f        | MIROVA npix  VRP MW  | NUESTRO pix(fp/sp)  VRP rec MW  pc.vrp  publicado (inner 5 km)")
for f in [1, 0.5, 0.2, 0.1, 0.05, 0.03, 0.02, 0.015, 0.01, 0.007, 0.005, 0.003, 0.002, 0.001]:
    a13 = np.where(dil, bk13 + f * (m13 - bk13), m13)
    a15 = np.where(dil, bk15 + f * (m15 - bk15), m15)
    al2, v2, dg2 = mirova(a13, a15)
    o = nuestro_k(a13, a15, inner_km=5.0)
    npx = int(o["hot"].sum()) if "hot" in o else -1
    pc = o.get("pc") or {}
    print(f" {f:<8} | {v2[1]:>3}  {np.nan_to_num(v2[0]):8.3f}  (abs {dg2['n_absolutas']}, p1 {sum(dg2['n_pase1'])}, p2 {sum(dg2['n_pase2'])}) "
          f"| {npx:>3} ({o.get('n_fp')}/{o.get('n_sp_new')})  {o.get('vrp_record', 0):8.3f}  {pc.get('vrp_mw', 0):8.3f}  {o.get('publicado', 0):8.3f}"
          f"  sp_mode={pc.get('single_pixel_mode')}")
