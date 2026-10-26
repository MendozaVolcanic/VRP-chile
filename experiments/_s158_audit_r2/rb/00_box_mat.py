"""Lee la matriz de ejemplo del OSF y describe BOX: qué clase está en el centro
y cuántos píxeles tiene cada clase. Pregunta 1 del instrumento: si BOX estuviera
al revés (1 afuera, 2 adentro) la geometría de las clases lo mostraría. Pregunta 2:
si el .mat no cargara, scipy lanza excepción (no un cero)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np
from scipy.io import loadmat
p = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2\experiments\_s158_d17_diseno\osf_codigo_mirova\Example\VIIRS750_example.mat"
S = loadmat(p)
for k, v in S.items():
    if k.startswith("__"): continue
    a = np.asarray(v)
    print(k, a.shape, a.dtype, (a.ravel()[:3] if a.size <= 3 or a.dtype.kind in "SUO" else ""))
BOX = np.asarray(S["BOX"], dtype=float)
print("shape BOX", BOX.shape)
vals, cnt = np.unique(BOX[~np.isnan(BOX)], return_counts=True)
print("clases:", dict(zip(vals.tolist(), cnt.tolist())), "NaN:", int(np.isnan(BOX).sum()))
r0, c0 = BOX.shape[0]//2, BOX.shape[1]//2
print("centro (r,c)=", (r0, c0), "BOX centro =", BOX[r0, c0])
for cl in vals:
    rr, cc = np.where(BOX == cl)
    print(f"clase {cl}: filas {rr.min()}..{rr.max()} cols {cc.min()}..{cc.max()} n={len(rr)} centroide=({rr.mean():.1f},{cc.mean():.1f})")
# radio aproximado de cada clase desde el centro
for cl in vals:
    rr, cc = np.where(BOX == cl)
    d = np.hypot(rr - r0, cc - c0)
    print(f"clase {cl}: dist al centro min {d.min():.1f} max {d.max():.1f} (pix de 750 m -> km min {d.min()*0.75:.1f} max {d.max()*0.75:.1f})")
print("dayflag", S["dayflag"], "sat_zen", S["sat_zen"], "sun_zen", S["sun_zen"], "acq", S.get("acquisition_id"))
# fila/col del centro: imprimir una cruz
print("fila central BOX:", "".join("x" if np.isnan(v) else str(int(v)) for v in BOX[r0, :]))
print("col  central BOX:", "".join("x" if np.isnan(v) else str(int(v)) for v in BOX[:, c0]))
