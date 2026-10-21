"""O1 (S159): VRP del .m original con shim de fillmissing2 (Octave) contra los dos ports, en Etna y las 40 chilenas
guardadas. NO es una reproducción del interpolador de MATLAB: los tres usan una triangulación de Delaunay distinta o
igual por azar. Lo que sí prueba: L_hot (suma de radiancia de los píxeles alertados, que no depende del fondo) y que
el VRP caiga dentro de unos pocos por ciento. Pregunta 2: si el .m de VRP no corriera, VRP saldría NaN en todas."""
import importlib.util, json, sys
from pathlib import Path
import numpy as np, scipy.io as sio
AQUI = Path(__file__).resolve().parent; EXP = AQUI.parents[1]
sys.path.insert(0, str(EXP / "_s158_audit_r2" / "oraculo")); import mirova_v750_r2 as R2
spec = importlib.util.spec_from_file_location("o1p", EXP / "_s158_oraculo_mirova" / "mirova_v750.py")
O1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(O1)
E = sio.loadmat(AQUI / "entradas.mat"); V = sio.loadmat(AQUI / "salida_vrp_octave_shim.mat")
D = sio.loadmat(AQUI / "salida_original.mat"); etq = json.loads((AQUI / "entradas_etiquetas.json").read_text(encoding="utf-8"))
A = D["ALERTAS"].ravel().astype(int); off = D["OFFSET"].ravel().astype(int); n = D["NALERT"].ravel().astype(int)
print(f"{'escena':60s} np  L_hot_oct    VRP_oct   VRP_R2   VRP_O1  oct/R2  oct/O1")
rel_r2, rel_o1, lhot_dif = [], [], 0
from collections import defaultdict
fam = defaultdict(list)
for k in range(len(etq)):
    if n[k] == 0: continue
    a = A[off[k]:off[k] + n[k]]; m13 = E["M13"][:, :, k]
    mk = np.zeros(m13.shape, bool); mk[np.unravel_index(a - 1, m13.shape, order="F")] = True
    r2 = R2.vrp(m13, mk); o1 = O1.vrp(m13, a - 1)  # primer port en base 0 (medido en comparar_octave_ports)
    vo = V["VRP"].ravel()[k]; lo = V["LHOT"].ravel()[k]
    if abs(lo - r2["L_hot"]) > 1e-12: lhot_dif += 1
    rel_r2.append(vo / r2["VRP_MW"] - 1); rel_o1.append(vo / o1[0] - 1); fam[etq[k]["familia"]].append((rel_r2[-1], rel_o1[-1]))
    if etq[k]["familia"] not in ("etna", "chile_guardada"): continue
    e = etq[k]; nom = e["id"] + " " + e.get("metodo", "") + " " + e.get("caja", "")
    print(f"{nom:60s} {n[k]:2d} {lo:10.6f} {vo:9.4f} {r2['VRP_MW']:8.4f} {o1[0]:8.4f} {vo/r2['VRP_MW']:7.4f} {vo/o1[0]:7.4f}")
r = np.abs(np.array(rel_r2)); q = np.abs(np.array(rel_o1))
print(f"escenas con alerta {r.size}; L_hot distinto {lhot_dif}; |oct/R2-1| max {r.max():.3e}, >1%: {int((r>0.01).sum())}; "
      f"|oct/O1-1| max {q.max():.3e}, >1%: {int((q>0.01).sum())}")
for f, v in fam.items():
    v = np.abs(np.array(v)); print(f"  {f}: n={len(v)} |oct/R2-1| mediana {np.median(v[:,0]):.2e} max {v[:,0].max():.2e} >1% {int((v[:,0]>0.01).sum())} | |oct/O1-1| mediana {np.median(v[:,1]):.2e} max {v[:,1].max():.2e} >1% {int((v[:,1]>0.01).sum())}")
