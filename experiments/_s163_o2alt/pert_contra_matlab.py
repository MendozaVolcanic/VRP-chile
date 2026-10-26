"""S163 O2 alternativa, parte 2: ¿la regla de desempate que acertó a Etna (perturbación simbólica tipo CGAL, marco
x = fila, y = columna) reproduce el fillmissing2 de MATLAB en TODAS las escenas de O2, no sólo en Etna?

POR QUÉ. Etna es un solo número; acertarlo por suerte tiene probabilidad medida en etna_ancla.py. La prueba de verdad
es el resultado de MATLAB R2026b sobre las 311 escenas de O2 (166 con alerta, 64 de un píxel aprox.), que la
coordinadora corrió el 2026-10-25: archivo
C:\\vrp-trabajo\\s159-pruebas\\experiments\\_s159\\o1\\o2_paquete\\resultado_o2.mat (md5 1f7fdc4bed0f8cb6223204bbce42ba43).
No se copia: se lee por ruta y se comprueba el md5 antes de usarlo.

Pregunta 1 (¿mide lo que dice?): se usan las MISMAS alertas que devolvió MATLAB (no las de Octave) y se exige L_hot
idéntico al de MATLAB; así la única diferencia posible es el fondo. Pregunta 2 (¿puede dar distinto de cero?): el
candidato del marco cambiado (x = columna) se corre igual y debe diferir de MATLAB en las escenas de empate; si los
dos coincidieran con MATLAB en todas, la prueba no discriminaría nada.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import scipy.io as sio
from scipy.ndimage import binary_dilation

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import delaunay_perturbado as DP  # noqa: E402

O2 = Path(r"C:\vrp-trabajo\s159-pruebas\experiments\_s159\o1\o2_paquete")
MD5 = "1f7fdc4bed0f8cb6223204bbce42ba43"
md5 = hashlib.md5((O2 / "resultado_o2.mat").read_bytes()).hexdigest()
assert md5 == MD5, f"resultado_o2.mat cambió: {md5}"
R = sio.loadmat(O2 / "resultado_o2.mat")
E = sio.loadmat(O2 / "entradas_o2.mat")
etq = json.loads((O2 / "entradas_o2_etiquetas.json").read_text(encoding="utf-8"))
print(f"MATLAB {R['version_matlab'][0]} | md5 OK | escenas {len(etq)}")

TOLR = 1e-9
VARS = (("pert_fila_col", "xy_fila_col"), ("pert_col_fila", "xy_col_fila"))
filas = []
for k in range(len(etq)):
    a = np.asarray(R["ALERTAS"][k, 0]).ravel().astype(int)
    if a.size == 0:
        continue
    m13 = E["M13"][:, :, k].astype(float)
    mask = np.zeros(m13.shape, bool); mask[np.unravel_index(a - 1, m13.shape, order="F")] = True
    npix = a.size
    enm = m13.copy(); enm[mask] = np.nan
    kk = 3 if npix <= 4 else (5 if npix <= 30 else 7)
    enm[binary_dilation(np.isnan(enm), structure=np.ones((kk, kk), bool))] = np.nan
    lhot = float(np.nansum(m13.ravel(order="F")[a - 1]))
    fila = {"k": k, "familia": etq[k].get("familia"), "id": etq[k].get("id"), "metodo": etq[k].get("metodo", ""),
            "caja": etq[k].get("caja", ""), "dx": etq[k].get("dx", 0), "dy": etq[k].get("dy", 0), "npix": npix,
            "lhot_dif": abs(lhot - float(R["LHOT"][k, 0])), "vrp_matlab": float(R["VRP"][k, 0])}
    bkm = R["BK"][k, 0]
    for nom, ejes in VARS:
        B, info = DP.rellenar(enm, ejes)
        lbk = float(np.nansum(B.ravel(order="F")[a - 1]))
        vrp = (lhot - lbk) * 1.97e7 * 0.5625 / 1e6
        fila[f"vrp_{nom}"] = vrp
        fila[f"ileg_{nom}"] = info["ilegales"]
        fila[f"rel_{nom}"] = abs(vrp / fila["vrp_matlab"] - 1) if fila["vrp_matlab"] != 0 else abs(vrp)
        if bkm.size:  # matriz de fondo completa de MATLAB (Etna y las 190 chilenas)
            d = np.abs(B - bkm); falt = np.isnan(enm)
            fila[f"bkmax_falt_{nom}"] = float(np.nanmax(d[falt]))  # sólo celdas rellenadas
    filas.append(fila)

print(f"escenas con alerta en MATLAB: {len(filas)}; L_hot distinto de MATLAB (>1e-12): "
      f"{sum(f['lhot_dif'] > 1e-12 for f in filas)}; aristas ilegales: "
      f"{sum(f['ileg_pert_fila_col'] + f['ileg_pert_col_fila'] for f in filas)}")
for nom, _ in VARS:
    rel = np.array([f[f"rel_{nom}"] for f in filas])
    print(f"{nom}: VRP/MATLAB-1 mediana {np.median(rel):.2e} max {rel.max():.2e} | igual a 1e-9: "
          f"{int((rel < TOLR).sum())} de {rel.size} | >1 %: {int((rel > 0.01).sum())}")
    for clase, sel in (("1 px", lambda f: f["npix"] == 1), ("2-4 px", lambda f: 2 <= f["npix"] <= 4),
                       ("5+ px", lambda f: f["npix"] >= 5)):
        r = np.array([f[f"rel_{nom}"] for f in filas if sel(f)])
        if r.size:
            print(f"    {clase:6s}: n={r.size:3d} igual a 1e-9 {int((r < TOLR).sum()):3d} | max {r.max():.2e}")
    bk = [f[f"bkmax_falt_{nom}"] for f in filas if f"bkmax_falt_{nom}" in f]
    print(f"    matriz de fondo completa (celdas rellenadas), {len(bk)} escenas: max |dif| {max(bk):.2e}; "
          f"escenas con max<1e-9: {sum(b < 1e-9 for b in bk)}")
    malas = [f for f in filas if f[f"rel_{nom}"] >= TOLR]
    print(f"    escenas que NO calzan ({len(malas)}), por familia: {dict(Counter(f['familia'] for f in malas))}")
    for f in malas[:12]:
        print(f"      k={f['k']:3d} {f['id']} {f['metodo']} {f['caja']} np={f['npix']} MATLAB {f['vrp_matlab']:.6f} "
              f"{nom} {f[f'vrp_{nom}']:.6f}")
(AQUI / "pert_contra_matlab.json").write_text(json.dumps(filas, ensure_ascii=False, indent=0), encoding="utf-8")
print("escrito pert_contra_matlab.json")
