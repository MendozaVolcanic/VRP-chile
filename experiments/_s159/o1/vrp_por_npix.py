"""O1 (S159): dispersión del VRP entre tres modelos de fillmissing2 (shim de Octave, segundo port, primer port) según
el número de píxeles alertados. Mismas máscaras (las del .m en Octave), mismo L_hot; sólo cambia la triangulación del
fondo. Pregunta 2: si los tres modelos fueran el mismo, la razón max/min sería 1 en todas; se informa la mediana."""
import importlib.util, json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np, scipy.io as sio
AQUI = Path(__file__).resolve().parent; EXP = AQUI.parents[1]
sys.path.insert(0, str(EXP / "_s158_audit_r2" / "oraculo")); import mirova_v750_r2 as R2
spec = importlib.util.spec_from_file_location("o1p", EXP / "_s158_oraculo_mirova" / "mirova_v750.py")
O1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(O1)
E = sio.loadmat(AQUI / "entradas.mat"); V = sio.loadmat(AQUI / "salida_vrp_octave_shim.mat")
D = sio.loadmat(AQUI / "salida_original.mat"); etq = json.loads((AQUI / "entradas_etiquetas.json").read_text(encoding="utf-8"))
A = D["ALERTAS"].ravel().astype(int); off = D["OFFSET"].ravel().astype(int); n = D["NALERT"].ravel().astype(int)
g = defaultdict(list); neg = 0
for k in range(len(etq)):
    if n[k] == 0: continue
    a = A[off[k]:off[k] + n[k]]; m13 = E["M13"][:, :, k]
    mk = np.zeros(m13.shape, bool); mk[np.unravel_index(a - 1, m13.shape, order="F")] = True
    v = np.array([V["VRP"].ravel()[k], R2.vrp(m13, mk)["VRP_MW"], O1.vrp(m13, a - 1)[0]])
    if (v <= 0).any(): neg += 1; continue
    clase = "1" if n[k] == 1 else ("2-4" if n[k] <= 4 else ("5-30" if n[k] <= 30 else ">30"))
    g[clase].append(v.max() / v.min())
print(f"escenas con alerta y VRP>0 en los tres: {sum(len(x) for x in g.values())}; con algún VRP<=0: {neg}")
for c in ("1", "2-4", "5-30", ">30"):
    if c in g:
        x = np.array(g[c]); print(f"  npix {c:4s}: n={x.size:3d} max/min mediana {np.median(x):.4f} p90 {np.percentile(x,90):.4f} max {x.max():.4f} | >1,05: {int((x>1.05).sum())} | >1,25: {int((x>1.25).sum())}")
