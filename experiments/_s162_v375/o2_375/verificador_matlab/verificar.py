# -*- coding: utf-8 -*-
"""Verificador independiente: la vara (vara_preliminar_375.json) contra MATLAB (resultado_v375.mat).
No reutiliza comparar_matlab_375.py. Uso: python -I verificar.py [ruta a delaunay_perturbado.py de cd812c746]"""
import hashlib
import importlib.util
import io
import json
import sys
from pathlib import Path

import numpy as np
import scipy.io as sio
from scipy.ndimage import binary_dilation
from scipy.spatial import Delaunay

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
D = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864\experiments\_s162_v375\o2_375")
N = 134
C375 = 1.80e7 * 0.140625 / 1e6
C750 = 1.97e7 * 0.5625 / 1e6

# 6. md5
md5 = hashlib.md5((D / "resultado_v375.mat").read_bytes()).hexdigest()
print("6. md5 resultado_v375.mat:", md5, "OK" if md5 == "71d0f8218a445c337560efd73d904374" else "DISTINTO")

S = sio.loadmat(D / "entradas_v375.mat")
R = sio.loadmat(D / "resultado_v375.mat", squeeze_me=True, struct_as_record=False)
E = json.loads((D / "entradas_v375_etiquetas.json").read_text(encoding="utf-8"))["escenas"]
V = json.loads((D / "vara_preliminar_375.json").read_text(encoding="utf-8"))["escenas"]
RAD, ALE, NAL = S["RAD"], S["ALE"].astype(int), np.ravel(S["NAL"]).astype(int)
K = RAD.shape[2]
DL, LHOT, LBK, NPIX, VRP = (np.ravel(R[k]).astype(float) for k in ("DL", "LHOT", "LBK", "NPIX", "VRP"))
BK = R["BK"]
print("K", K, "len E", len(E), "len V", len(V), "BK dtype", BK.dtype, BK.shape)

# orden
pos_E = [e["posicion"] for e in E]
pos_V = [v["posicion"] for v in V]
print("orden: posicion en etiquetas == 1..K:", pos_E == list(range(1, K + 1)), "| en vara == 1..K:", pos_V == list(range(1, K + 1)),
      "| ids iguales:", [e["id"] for e in E] == [v["id"] for v in V])
print("orden: vara['posicion'] == etiquetas['posicion'] por indice:", pos_E == pos_V)

# decodificacion de ALE
def mascara(n, orden):
    idx = ALE[n, :NAL[n]] - 1
    m = np.zeros((N, N), bool)
    if orden == "col":
        m[idx % N, idx // N] = True      # columna mayor base 1
    else:
        m[idx // N, idx % N] = True      # fila mayor
    return m

def rad_n(n):
    return RAD[:, :, n].astype(np.float64)

# 3. LHOT
lh_col = np.array([np.sum(rad_n(n)[mascara(n, "col")]) for n in range(K)])
lh_fil = np.array([np.nansum(rad_n(n)[mascara(n, "fil")]) for n in range(K)])
rel_col = np.abs(lh_col - LHOT) / np.maximum(np.abs(LHOT), 1e-300)
rel_fil = np.abs(lh_fil - LHOT) / np.maximum(np.abs(LHOT), 1e-300)
lv = np.array([v["l_hot"] for v in V])
print(f"3. LHOT vs RAD[ALE col-mayor]: max rel {rel_col.max():.2e}, escenas > 1e-12: {(rel_col > 1e-12).sum()}")
print(f"   LHOT vs RAD[ALE fila-mayor] (debe fallar): escenas > 1e-12: {(rel_fil > 1e-12).sum()} de {K}, max rel {rel_fil.max():.3f}")
print(f"   LHOT vs l_hot de la vara: max rel {(np.abs(LHOT - lv) / np.abs(LHOT)).max():.2e}")
print(f"   l_hot_port etiquetas vs LHOT: max rel {(np.abs(np.array([e['l_hot_port'] for e in E]) - LHOT) / np.abs(LHOT)).max():.2e}")
print("   NPIX == NAL:", bool((NPIX == NAL).all()), "| NPIX == etiquetas npix:", bool((NPIX == np.array([e['npix'] for e in E])).all()),
      "| distribucion NAL", np.bincount(NAL))
# alertas_matlab de etiquetas == ALE?
print("   alertas_matlab (etiquetas) == ALE:", all(sorted(E[n]["alertas_matlab"]) == sorted(ALE[n, :NAL[n]].tolist()) for n in range(K)))
# alertas duplicadas / fuera de rango
print("   ALE dentro de 1..N*N y sin duplicados:", all(((ALE[n, :NAL[n]] >= 1) & (ALE[n, :NAL[n]] <= N * N)).all() and len(set(ALE[n, :NAL[n]])) == NAL[n] for n in range(K)),
      "| ALE relleno tras NAL:", set(np.unique(ALE[NAL[0]:, :][ALE[NAL[0]:, :] == 0]).tolist()) if False else "n/a")

# 1. DL vs vara
dl_v = np.array([v["dl"] for v in V])
rel1 = np.abs(DL - dl_v) / np.maximum(np.abs(DL), 1e-300)
print(f"1. DL MATLAB vs vara: max rel {rel1.max():.2e}, escenas > 1e-9: {(rel1 > 1e-9).sum()}, mediana {np.median(rel1):.2e}")
print(f"   min |DL| {np.abs(DL).min():.3e}, DL negativos: {(DL < 0).sum()}, DL==0: {(DL == 0).sum()}")
# tambien en absoluto
print(f"   max abs dif DL {np.abs(DL - dl_v).max():.2e}")
# DL recomputado desde LHOT-LBK
print(f"   DL == LHOT-LBK: max abs {np.abs(DL - (LHOT - LBK)).max():.2e}")
# vrp_vara_mw coherente
vv = np.array([v["vrp_vara_mw"] for v in V])
print(f"   vrp_vara_mw == dl*C375: max rel {(np.abs(vv - dl_v * C375) / np.abs(vv)).max():.2e}; VRP .m == DL*C750: max rel {(np.abs(VRP - DL * C750) / np.abs(VRP)).max():.2e}")

# 4. control: MATLAB vs port
vp = np.array([e["vrp_port_mw"] for e in E])
dl_p = vp / C375
rel4 = np.abs(DL - dl_p) / np.maximum(np.abs(DL), 1e-300)
print(f"4. MATLAB vs port: escenas > 1e-9: {(rel4 > 1e-9).sum()}, max rel {rel4.max():.3f}; > 1e-6: {(rel4 > 1e-6).sum()}")
vara_vs_port = np.abs(vv - vp) / np.maximum(np.abs(vp), 1e-12)
print(f"   vara vs port (>1e-6): {(vara_vs_port > 1e-6).sum()}; coincide el conjunto de escenas que difieren (MATLAB!=port vs vara!=port):",
      bool(((rel4 > 1e-6) == (vara_vs_port > 1e-6)).all()))
print(f"   en las que no difieren del port, DL MATLAB vs port max rel: {rel4[rel4 <= 1e-6].max():.2e}")
# max con otro denominador (el del port), por si el denominador escondiera algo
rel4b = np.abs(DL - dl_p) / np.maximum(np.abs(dl_p), 1e-300)
print(f"   (denominador port) max rel {rel4b.max():.3f}")

# 5. LBK = suma de BK en alertas
lb_s = np.array([np.sum(BK[:, :, n].astype(np.float64)[mascara(n, "col")]) for n in range(K)])
lb_s_cast = np.array([np.sum(BK[:, :, n][mascara(n, "col")].astype(np.float64)) for n in range(K)])
r5 = np.abs(lb_s - LBK) / np.abs(LBK)
print(f"5. LBK vs sum(BK single en alertas): max rel {r5.max():.2e}, escenas > 1e-6: {(r5 > 1e-6).sum()}, > 1e-9: {(r5 > 1e-9).sum()}")
print(f"   LBK vs l_bk de la vara: max rel {(np.abs(LBK - np.array([v['l_bk'] for v in V])) / np.abs(LBK)).max():.2e}")

# 2. Etna
et = R["ETNA"]
print(f"2. Etna: NPIX {int(et.NPIX)}, LHOT {et.LHOT:.9f}, LBK {et.LBK:.9f}, VRP {et.VRP * 1e6:.1f} W, DL {et.DL:.9f}; alertas {np.ravel(et.alertas)}")
print("   LBK Etna - 1.072886152 =", et.LBK - 1.072886152, "| VRP W - 9889528.4 =", et.VRP * 1e6 - 9889528.4)
print("   salida_matlab_v375.txt:", (D / "salida_matlab_v375.txt").read_text(encoding="utf-8").replace("\n", " | ")[:400])

# ---- caminos de falla ----
print("\n== ligadura resultado <-> entradas: BK fuera del hueco dilatado debe ser single(RAD) exacto ==")
malos = 0
dentro_hueco_finito = True
dentro_dif = []
for n in range(K):
    m = mascara(n, "col")
    k = 3 if NAL[n] <= 4 else (5 if NAL[n] <= 30 else 7)
    excl = binary_dilation(m | np.isnan(RAD[:, :, n]), structure=np.ones((k, k), bool))
    # MATLAB: imdilate(isnan(masked)) incluye los NaN previos de RAD; strel square sin borde = padding falso
    fuera = ~excl
    if not np.array_equal(BK[:, :, n][fuera], RAD[:, :, n][fuera]):
        malos += 1
    dentro_hueco_finito &= bool(np.isfinite(BK[:, :, n]).all())
    dentro_dif.append(float(np.nanmax(np.abs(BK[:, :, n][excl].astype(float) - RAD[:, :, n][excl].astype(float)))) if np.isfinite(RAD[:, :, n][excl]).any() else 1.0)
print("escenas donde BK(fuera del hueco) != RAD:", malos, "de", K, "| BK todo finito:", dentro_hueco_finito,
      "| hueco: cambia respecto de RAD en todas:", all(d > 0 for d in dentro_dif))

# RAD no tiene NaN en las entradas?
print("RAD con NaN (celdas):", int(np.isnan(RAD).sum()), "| escenas con algun NaN:", int(np.isnan(RAD).any(axis=(0,1)).sum()), "| NaN en BK:", int(np.isnan(BK).sum()), "| escenas con alertas en el borde (fila o col 0/133):",
      sum(1 for n in range(K) if (lambda m: m[[0, N - 1], :].any() or m[:, [0, N - 1]].any())(mascara(n, "col"))))
print("escenas con hueco dilatado tocando el borde:", sum(1 for n in range(K) if (lambda e: e[[0, N - 1], :].any() or e[:, [0, N - 1]].any())(
    binary_dilation(mascara(n, "col"), structure=np.ones((3 if NAL[n] <= 4 else 5, 3 if NAL[n] <= 4 else 5), bool)))))

# Etiquetas: la radiancia de RAD corresponde a la escena etiquetada? (hash)
try:
    h = [hashlib.sha256(np.ascontiguousarray(RAD[:, :, n]).tobytes()).hexdigest() == E[n]["grilla_sha256"] for n in range(K)]
    print("grilla_sha256 == sha256(RAD[:,:,n] bytes single C-order):", sum(h), "de", K)
    h2 = [hashlib.sha256(np.asfortranarray(RAD[:, :, n]).tobytes()).hexdigest() == E[n]["grilla_sha256"] for n in range(K)]
    print("   (orden Fortran):", sum(h2))
    h3 = [hashlib.sha256(RAD[:, :, n].astype(np.float64).tobytes()).hexdigest() == E[n]["grilla_sha256"] for n in range(K)]
    print("   (float64 C-order):", sum(h3))
except Exception as ex:
    print("hash fallo", ex)

# (sensibilidad con scipy y regla del modulo: ver sens_scipy.py, modulo_vs_bk.py y nanpat.py)
