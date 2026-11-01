"""O1/O2 (S159): lee resultado_o2.mat (salida de correr_o2.m en MATLAB Online) y lo compara con Octave y los ports.
Uso: python leer_o2.py [ruta a resultado_o2.mat]   (por defecto o2_paquete/resultado_o2.mat)
Pregunta 1: si los ports o Octave fallaran en la detección frente a MATLAB, se vería como lista distinta en alguna de
las 311 escenas. Pregunta 2: si el archivo viniera vacío o de otra corrida, Etna no daría 5 píxeles (se exige).
Para el VRP: informa cuál de los modelos de fillmissing2 coincide con MATLAB, y el Tot_Lmir_bk de Etna contra el OSF."""
import json, sys
from pathlib import Path
import numpy as np, scipy.io as sio
AQUI = Path(__file__).resolve().parent; EXP = AQUI.parents[1]
sys.path.insert(0, str(EXP / "_s158_audit_r2" / "oraculo")); import mirova_v750_r2 as R2
import importlib.util
spec = importlib.util.spec_from_file_location("o1p", EXP / "_s158_oraculo_mirova" / "mirova_v750.py")
O1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(O1)
ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "o2_paquete" / "resultado_o2.mat"
M = sio.loadmat(ruta)
print("archivo:", ruta, "| version:", M["version_matlab"])
etq = json.loads((AQUI / "o2_paquete" / "entradas_o2_etiquetas.json").read_text(encoding="utf-8"))
E = sio.loadmat(AQUI / "o2_paquete" / "entradas_o2.mat")
D = sio.loadmat(AQUI / "salida_original.mat"); V = sio.loadmat(AQUI / "salida_vrp_octave_shim.mat")
A = D["ALERTAS"].ravel().astype(int); off = D["OFFSET"].ravel().astype(int); n = D["NALERT"].ravel().astype(int)
al = [np.asarray(x).ravel().astype(int).tolist() for x in M["ALERTAS"].ravel()]
assert len(al[0]) == 5, al[0]
dif_det = []; filas = []
for j, e in enumerate(etq):
    k = e["idx_o1"]; oc = A[off[k]:off[k] + n[k]].tolist()
    if al[j] != oc: dif_det.append((e, al[j], oc))
    if al[j]:
        m13 = E["M13"][:, :, j]; mk = np.zeros(m13.shape, bool); mk[np.unravel_index(np.array(al[j]) - 1, m13.shape, order="F")] = True
        filas.append((e, len(al[j]), M["VRP"].ravel()[j], V["VRP"].ravel()[k], R2.vrp(m13, mk)["VRP_MW"], O1.vrp(m13, np.array(al[j]) - 1)[0]))
print(f"detección: escenas {len(etq)}, con alerta en MATLAB {sum(1 for x in al if x)}, listas distintas de Octave: {len(dif_det)}")
for d in dif_det[:10]: print("   DIF", d)
print(f"Etna Tot_Lmir_bk MATLAB {M['LBK'].ravel()[0]:.9f} (OSF 1.072886152) | VRP {M['VRP'].ravel()[0]*1e6:.1f} W (OSF 9889528.4)")
x = np.array([[f[2], f[3], f[4], f[5]] for f in filas])
for i, nom in ((1, "shim Octave"), (2, "segundo port"), (3, "primer port")):
    r = np.abs(x[:, i] / x[:, 0] - 1)
    print(f"VRP {nom} / MATLAB - 1: mediana {np.median(r):.2e}, max {r.max():.2e}, >1 %: {int((r>0.01).sum())} de {r.size}, igual a 1e-9: {int((r<1e-9).sum())}")
for f in filas:
    if f[0]["familia"] in ("etna", "chile_guardada"):
        e = f[0]; print(f"   {e['id']:38s} {e.get('metodo',''):7s} {e.get('caja',''):15s} np={f[1]} MATLAB {f[2]:.4f} shim {f[3]:.4f} R2 {f[4]:.4f} O1 {f[5]:.4f}")
