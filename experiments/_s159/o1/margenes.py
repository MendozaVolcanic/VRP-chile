"""O1 (S159): ¿qué tan lejos de su umbral queda la decisión más ajustada de cada escena?

Por qué: Octave no es MATLAB. Que el .m corrido en Octave y los dos ports coincidan prueba que los ports traducen bien
el .m, pero un píxel que quede a 1e-15 de un umbral podría decidirse distinto en MATLAB (otro orden de suma en
mean/std, otro polyfit). Si el margen mínimo de las escenas con decisión es muchos órdenes mayor que el error de
redondeo de doble precisión (~1e-16 relativo), esa vía no puede cambiar ninguna máscara.
Pregunta 1: si hubiera un píxel en el filo, ¿se vería? Sí: se reporta el margen mínimo por escena y por familia.
Pregunta 2: instrumento muerto daría margen NaN o infinito en todas; se cuentan las escenas con margen finito.
Usa el segundo port instrumentado (copia en memoria con un registro, sin tocar el archivo).
"""
import json
import sys
import types
from collections import defaultdict
from pathlib import Path

import numpy as np
import scipy.io as sio

AQUI = Path(__file__).resolve().parent
EXP = AQUI.parents[1]
src = (EXP / "_s158_audit_r2" / "oraculo" / "mirova_v750_r2.py").read_text(encoding="utf-8")
A = "    return a0, a1, a2, diag"
B = "        absol = nti_roi > u_abs                                      # l. 206"
assert src.count(A) == 1 and src.count(B) == 1
src = src.replace(A, "    _LOG.append(('ctx', c_nti, c_eti, u_nti1, u_nti2, u_eti1, u_eti2, m0, m1, m2))\n" + A)
src = src.replace(B, B + "\n        _LOG.append(('abs', nti_roi, u_abs))")
R = types.ModuleType("r2i"); R.__dict__["_LOG"] = []
sys.path.insert(0, str(EXP / "_s158_audit_r2" / "oraculo"))
exec(compile(src, "r2i", "exec"), R.__dict__)

E = sio.loadmat(AQUI / "entradas.mat")
etq = json.loads((AQUI / "entradas_etiquetas.json").read_text(encoding="utf-8"))
K = E["M13"].shape[2]


def margen_escena(log):
    m = np.inf
    for ent in log:
        if ent[0] == "abs":
            v = np.abs(ent[1] - ent[2]); v = v[np.isfinite(v)]
            if v.size: m = min(m, v.min())
            continue
        _, cn, ce, un1, un2, ue1, ue2, m0, m1, m2 = ent
        for mk, un, ue in ((m0, un1, ue1), (m1, un1, ue1), (m2, un2, ue2)):
            sel = mk == 1
            a, b = cn[sel] - un, ce[sel] - ue
            ok = np.isfinite(a) & np.isfinite(b)
            a, b = a[ok], b[ok]
            pasa = (a > 0) & (b > 0)
            # pasa: basta que uno cruce; no pasa: tienen que cruzar los que fallan
            mm = np.where(pasa, np.minimum(a, b), np.maximum(np.where(a <= 0, -a, 0), np.where(b <= 0, -b, 0)))
            if mm.size: m = min(m, mm.min())
    return m


por_fam = defaultdict(list); peores = []
for k in range(K):
    R._LOG.clear()
    R.detectar(E["M13"][:, :, k], E["M15"][:, :, k], E["BOX"][:, :, k], E["DAY"].ravel()[k], E["SG"].ravel()[k])
    m = margen_escena(R._LOG) if R._LOG else np.nan
    por_fam[etq[k]["familia"]].append(m); peores.append((m, k))
for f, v in por_fam.items():
    v = np.array(v); fin = v[np.isfinite(v)]
    print(f"{f}: escenas {v.size}, con margen finito {fin.size}, margen mínimo {fin.min():.3e}, "
          f"percentil 1 {np.percentile(fin, 1):.3e}, mediana {np.median(fin):.3e}")
peores = sorted([p for p in peores if np.isfinite(p[0])])[:5]
for m, k in peores:
    print(f"  más ajustada: {m:.3e} {etq[k]}")
