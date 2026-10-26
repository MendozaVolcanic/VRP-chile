# -*- coding: utf-8 -*-
"""F1 (S158): umbral de detección de un foco débil, MIROVA contra nuestra cadena K, sobre el fondo real de Etna.

El exceso de la anomalía de Etna (M13 y M15 sobre el fondo interpolado de MIROVA, dentro de su dilatación de 5) se
escala por f y se coloca (a) donde está, a ~1,8 km del centro, dentro de la caja 7x7 de MIROVA, y (b) corrido 5 celdas
(3,75 km) al este y al norte, FUERA de la caja de MIROVA pero DENTRO de un círculo de 5 km como el nuestro.
Para cada f: píxeles alertados y VRP de MIROVA; píxeles, VRP de record y publicado de nuestra cadena (inner 5 km).

Instrumento 1: si las dos cadenas tuvieran el mismo umbral, la f mínima detectada sería la misma; se imprime.
Instrumento 2: f = 1 en (a) debe dar los 5 píxeles de MIROVA en las dos (control positivo, igual que
etna_k_contra_mirova.py); f = 0 debe dar 0 en las dos (control negativo: el fondo solo no dispara).
Uso: python -B experiments/_s158_audit/f1/etna_barrido_fino.py
"""
import os, sys, io
os.environ["VRP_PROFILE"] = "mirova_equivalent"
sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.join(os.getcwd(), "experiments", "_s158_oraculo_mirova"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np, scipy.io as sio
from scipy.ndimage import binary_dilation
import mirova_v750 as M
from nuestro_k_en_grilla import nuestro_k, planck_inv

S = sio.loadmat("experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat")
m13, m15, box = S["ZI_M13"].astype(float), S["ZI_M15"].astype(float), S["BOX"]
sg = M.sunglint_angle(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())
al = M.hotspot_detection(m13, m15, box, 0, sg)
mk = np.zeros(m13.size, bool); mk[al] = True; mk = mk.reshape(m13.shape, order="F")
dil = binary_dilation(mk, structure=np.ones((5, 5), bool))
bk13 = M._fillmissing2_linear(np.where(dil, np.nan, m13))
bk15 = M._fillmissing2_linear(np.where(dil, np.nan, m15))
ex13 = np.where(dil, m13 - bk13, 0.0)
ex15 = np.where(dil, m15 - bk15, 0.0)
bt_bk = planck_inv(bk13[mk], 4.05)
print("BT de M13 del fondo interpolado de MIROVA bajo los 5 alertados:", np.round(bt_bk, 2), "K")
for nombre, desp in (("(a) en su lugar, dentro de la caja 7x7", (0, 0)), ("(b) corrido 5 celdas NE, fuera de la caja", (-5, 5))):
    e13 = np.roll(ex13, desp, axis=(0, 1)); e15 = np.roll(ex15, desp, axis=(0, 1))
    b13 = np.roll(np.where(dil, bk13, m13), (0, 0), axis=(0, 1))
    base13 = np.where(dil, bk13, m13); base15 = np.where(dil, bk15, m15)
    print("\n" + nombre)
    print(" f      | MIROVA npix VRP_MW | NUESTRO npix fp/sp  VRP_rec  publicado  t_bg")
    for f in [0, 1, 0.3, 0.2, 0.15, 0.12, 0.1, 0.08, 0.07, 0.06, 0.05, 0.045, 0.04, 0.035, 0.03]:
        a13 = base13 + f * e13
        a15 = base15 + f * e15
        al2 = M.hotspot_detection(a13, a15, box, 0, sg)
        v2 = M.vrp(a13, al2)
        o = nuestro_k(a13, a15, inner_km=5.0)
        print(f" {f:<6} | {v2[1]:>3} {np.nan_to_num(v2[0]):8.3f}  | {int(o['hot'].sum()):>3}  {o['n_fp']}/{o['n_sp_new']}"
              f"  {o['vrp_record']:8.3f}  {o['publicado']:8.3f}  {o['t_bg']:.2f}")
