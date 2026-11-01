# -*- coding: utf-8 -*-
"""F1 (S158): en el barrido de Etna (a), ¿el primer pase vacío de nuestra cadena es la compuerta bt > t_bg + 3 K (D22)?
Se repite f = 1, 0,3, 0,1 con apply_bt_gate True (producción) y False. Instrumento: si la compuerta no fuera la causa,
fp no cambiaría al apagarla. Uso: python -B experiments/_s158_audit/f1/etna_compuerta.py"""
import os, sys, io
os.environ["VRP_PROFILE"] = "mirova_equivalent"
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), "experiments", "_s158_oraculo_mirova"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np, scipy.io as sio
from scipy.ndimage import binary_dilation
import mirova_v750 as M
from nuestro_k_en_grilla import nuestro_k
S = sio.loadmat("experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat")
m13, m15, box = S["ZI_M13"].astype(float), S["ZI_M15"].astype(float), S["BOX"]
sg = M.sunglint_angle(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())
al = M.hotspot_detection(m13, m15, box, 0, sg)
mk = np.zeros(m13.size, bool); mk[al] = True; mk = mk.reshape(m13.shape, order="F")
dil = binary_dilation(mk, structure=np.ones((5, 5), bool))
bk13 = M._fillmissing2_linear(np.where(dil, np.nan, m13)); bk15 = M._fillmissing2_linear(np.where(dil, np.nan, m15))
for f in (1, 0.3, 0.1):
    a13 = np.where(dil, bk13 + f * (m13 - bk13), m13); a15 = np.where(dil, bk15 + f * (m15 - bk15), m15)
    for g in (True, False):
        o = nuestro_k(a13, a15, inner_km=5.0, apply_bt_gate=g)
        print(f"f={f} compuerta={g}: fp {o['n_fp']} sp_nuevos {o['n_sp_new']} total {int(o['hot'].sum())} VRP_rec {o['vrp_record']:.3f}")
