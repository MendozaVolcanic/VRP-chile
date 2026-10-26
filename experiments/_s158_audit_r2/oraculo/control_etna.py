"""Control del segundo oráculo: la pasada de Etna de la matriz de ejemplo contra el OSF v2.5.

Pregunta 1 del instrumento: si el port estuviera roto (umbral, máscara, fondo), ¿se vería? Sí: se compara con
cuatro números independientes de producción de MIROVA (Npix, Tot_Lmir_hot, Tot_Lmir_bk, VRP) que el port no lee.
Pregunta 2: si el instrumento estuviera muerto (por ejemplo, detectar devuelve vacío), VRP sería NaN y Npix 0,
distinto del OSF. Control positivo de sensibilidad: mutaciones del port (abajo) deben cambiar el resultado.
Ventana: una sola pasada, 2023-05-19 00:54 UTC (VJ1 = NOAA-20).

Uso: python -I control_etna.py <ruta al CSV del OSF v2.5>
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import mirova_v750_r2 as M  # noqa: E402

MAT = AQUI.parents[1] / "_s158_d17_diseno" / "osf_codigo_mirova" / "Example" / "VIIRS750_example.mat"
osf = sys.argv[1]

S = sio.loadmat(MAT)
sg = M.sunglint_deg(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())
mask, lista, d = M.detectar(S["ZI_M13"], S["ZI_M15"], S["BOX"], int(S["dayflag"].item()), sg, devolver_diag=True)
r = M.vrp(S["ZI_M13"], mask)
print("adquisicion", S["acquisition_id"][0], "sunglint", round(sg, 2))
print("n_abs", d["n_abs"], "n_pasada1", d["n_p1"], "n_pasada2", d["n_p2"], "lista_len", len(lista),
      "duplicados", len(lista) - len(set(lista)))
rows, cols = np.nonzero(mask)
print("pixeles (fila,col base 0):", list(zip(rows.tolist(), cols.tolist())))
print("BOX en los pixeles:", S["BOX"][mask].tolist())
print("umbrales pasada1:", {k: d["pasada1"][k] for k in ("u_nti1", "u_nti2", "u_eti1", "u_eti2")})
print("umbrales pasada2:", {k: d["pasada2"][k] for k in ("u_nti1", "u_nti2", "u_eti1", "u_eti2")})
print(f"oraculo R2: npix={r['npix']} L_hot={r['L_hot']:.9f} L_bk={r['L_bk']:.9f} VRP_W={r['VRP_MW']*1e6:.1f}")

df = pd.read_csv(osf, usecols=["timeUTC", "Volc_Name", "Resolution", "Satellite", "Dayflag", "SatZen",
                               "Npix", "Tot_Lmir_hot", "Tot_Lmir_bk", "VRP"])
e = df[(df.Volc_Name.str.contains("Etna")) & (df.timeUTC.str.startswith("19/05/2023 00:5"))]
print("OSF filas Etna 19/05/2023 00:5x:")
print(e.to_string(index=False))
e750 = e[e.Resolution == 750]
if len(e750) == 1:
    f = e750.iloc[0]
    print(f"OSF: npix={f.Npix} L_hot={f.Tot_Lmir_hot:.9f} L_bk={f.Tot_Lmir_bk:.9f} VRP_W={f.VRP:.1f}")
    print(f"razones R2/OSF: L_hot {r['L_hot']/f.Tot_Lmir_hot:.6f}  L_bk {r['L_bk']/f.Tot_Lmir_bk:.6f}  "
          f"VRP {r['VRP_MW']*1e6/f.VRP:.6f}")

# Sensibilidad a la triangulación de fillmissing2 (no documentada): 50 perturbaciones de coordenadas de 1e-6 celdas.
v = [M.vrp(S["ZI_M13"], mask, jitter=1e-6, semilla=s)["VRP_MW"] * 1e6 for s in range(50)]
print(f"sensibilidad triangulacion (50 semillas, jitter 1e-6): min {min(v):.1f} max {max(v):.1f} "
      f"rango relativo {(max(v)-min(v))/np.median(v):.2e}")

# Controles positivos: mutaciones que deben mover el resultado.
def mutado(**kw):
    m13, m15, box = S["ZI_M13"].copy(), S["ZI_M15"].copy(), S["BOX"].copy()
    if kw.get("box_invertido"):
        box = np.where(box == 1, 2, np.where(box == 2, 1, box))
    mk, _ = M.detectar(m13, m15, box, kw.get("dayflag", 0), kw.get("sg", sg))
    return int(mk.sum()), M.vrp(m13, mk)["VRP_MW"] * 1e6

print("mutacion ROI invertido (BOX 1<->2):", mutado(box_invertido=True))
print("mutacion dayflag=1:", mutado(dayflag=1))
print("mutacion sunglint=5 (debe dar 0 pixeles):", mutado(sg=5.0))
