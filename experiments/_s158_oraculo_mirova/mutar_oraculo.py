# -*- coding: utf-8 -*-
"""Control de mutaciones del oráculo sobre la pasada de Etna (S158).

POR QUÉ: un port que reproduce un caso puede hacerlo por suerte si sus pasos no deciden nada en ese caso. Cada
mutación cambia un paso del código de MIROVA por la versión nuestra (o lo apaga) y mira si el resultado de Etna
cambia. Las que no cambian quedan DECLARADAS: el control de Etna no las cubre.
Instrumento: cada mutación corre en un intérprete nuevo, sin bytecode (-B), sobre una copia del módulo en una carpeta
temporal. La primera versión mutaba el archivo e importlib.reload reusó el .pyc viejo: siete «igual», uno falso.
Uso: python -I -B mutar_oraculo.py <raiz del repo> <carpeta temporal>
"""
import json, os, shutil, subprocess, sys

RAIZ, TMP = sys.argv[1], sys.argv[2]
SRC = os.path.join(RAIZ, "experiments", "_s158_oraculo_mirova", "mirova_v750.py")
EJ = os.path.join(RAIZ, "experiments", "_s158_d17_diseno", "osf_codigo_mirova", "Example", "VIIRS750_example.mat")
CORRER = r'''
import sys, json, numpy as np, scipy.io as sio
sys.path.insert(0, sys.argv[1]); import mirova_v750 as m
S = sio.loadmat(sys.argv[2])
sg = m.sunglint_angle(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())
a = m.hotspot_detection(S["ZI_M13"], S["ZI_M15"], S["BOX"], 0, sg)
v, n, dl, bk, lh, lb = m.vrp(S["ZI_M13"], a)
print(json.dumps({"alertas": sorted(int(x) for x in a), "npix": int(n), "vrp_w": float(v * 1e6)}))
'''
MUT = {
    "control (sin mutación)": None,
    "8 vecinos sin el central": ("for i in range(3) for j in range(3)], axis=0)", "for i in range(3) for j in range(3) if (i, j) != (1, 1)], axis=0)"),
    "min en vez de max (NTI cumbre y fuera)": ("    thr_n1 = max(mu_n + s1 * sd_n, n1)\n    thr_n2 = max(mu_n + s2 * sd_n, n2)", "    thr_n1 = min(mu_n + s1 * sd_n, n1)\n    thr_n2 = min(mu_n + s2 * sd_n, n2)"),
    "mínimo de dNTI fuera 0,010": ("-0.7, 10, 5, 0.02, 0.003, 0.01, 0.003", "-0.7, 10, 5, 0.010, 0.003, 0.01, 0.003"),
    "K1 -0,8": ("k1, s1, s2, n1, n2, e1, e2 = -0.7,", "k1, s1, s2, n1, n2, e1, e2 = -0.8,"),
    "sin segundo pase": ("    r2 = _contextual_pass(*args, absolute, pass1,", "    r2 = ((np.array([], dtype=int),) * 3) if True else _contextual_pass(*args, absolute, pass1,"),
    "sin dilatación del fondo": ("k = 3 if npix <= 4 else (5 if npix <= 30 else 7)", "k = 1"),
    "recorte a cero por píxel": ("    delta = l_hot - l_bk", "    delta = np.nansum(np.maximum(flat_m13[alert] - flat_bk[alert], 0))"),
    "fondo = media de los 8 vecinos no alertados": ("    bk = _fillmissing2_linear(masked)", "    bk = _media_vecinos(m13, alert)"),
}
EXTRA = '''
def _media_vecinos(m13, alert):
    """Brazo D25 (media de los vecinos no alertados de la 3x3) para comparar."""
    A = m13.copy(); flat = A.ravel(order="F"); es = np.zeros(flat.size, bool); es[alert] = True
    es = es.reshape(A.shape, order="F"); out = np.full(A.shape, np.nan)
    for (f, c) in zip(*np.nonzero(es)):
        v = [A[i, j] for i in range(f - 1, f + 2) for j in range(c - 1, c + 2)
             if 0 <= i < A.shape[0] and 0 <= j < A.shape[1] and not es[i, j] and np.isfinite(A[i, j])]
        out[f, c] = np.mean(v) if v else np.nan
    return out
'''
src = open(SRC, encoding="utf-8").read()
res = {}
for nombre, mut in MUT.items():
    d = os.path.join(TMP, "mut_" + str(len(res))); os.makedirs(d, exist_ok=True)
    s = src if mut is None else src.replace(mut[0], mut[1])
    if mut is not None:
        assert src.count(mut[0]) == 1, nombre
    if "media de los 8 vecinos" in nombre:
        s += EXTRA
    open(os.path.join(d, "mirova_v750.py"), "w", encoding="utf-8").write(s)
    out = subprocess.run([sys.executable, "-I", "-B", "-c", CORRER, d, EJ], capture_output=True, text=True)
    res[nombre] = json.loads(out.stdout) if out.returncode == 0 else {"error": out.stderr[-300:]}
base = res["control (sin mutación)"]
print(f"control: npix {base['npix']}, VRP {base['vrp_w']:,.1f} W (MIROVA OSF v2.5: 5 píxeles, 9.889.528,4 W)")
for k, r in res.items():
    if k.startswith("control"):
        continue
    if "error" in r:
        print(f"{k:45s} ERROR {r['error']}"); continue
    cambia = r["alertas"] != base["alertas"] or abs(r["vrp_w"] - base["vrp_w"]) > 1e-6
    print(f"{k:45s} {'CAMBIA' if cambia else 'igual (no cubierto por Etna)'}  npix {r['npix']}  VRP {r['vrp_w']:,.1f} W ({100 * (r['vrp_w'] / 9889528.362 - 1):+.2f} % contra MIROVA)")
shutil.rmtree(TMP, ignore_errors=True)
