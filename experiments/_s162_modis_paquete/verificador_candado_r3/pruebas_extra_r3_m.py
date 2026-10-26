# Verificador r3: la identidad de m_con_regla_matlab con el port en las ramas k=5 y k=7 y con mascaras de borde
import sys, numpy as np
from pathlib import Path
AQUI = Path(r"C:/vrp-trabajo/s162-modd/experiments/_s162_modis_paquete")
sys.path.insert(0, str(AQUI))
import m_con_regla_matlab as M
import evaluar_paquete as EP
sys.path.insert(0, str(EP.RAIZ / "experiments/_s159/portes"))
import mirova_port as MP
print("MP.SENSORES MODIS:", {k: v for k, v in MP.SENSORES["MODIS"].items() if k in ("coef", "area")}, "COEF_MODIS", M.COEF_MODIS)
res = {}
for n in (1, 2, 4, 5, 12, 30, 31, 45):
    mal, tot, difiere_regla = 0, 0, 0
    for s in range(12):
        r = np.random.default_rng(1000 + s)
        x = 0.1 + r.normal(0, 0.002, (51, 51))
        if s % 3 == 0: x[:r.integers(2, 12), :] = np.nan
        # mascara contigua en blob alrededor de (25,25) o (3,3) en el borde
        c = (25, 25) if s % 2 == 0 else (2, 3)
        mk = np.zeros(x.shape, bool)
        cand = sorted(((i, j) for i in range(51) for j in range(51)), key=lambda p: (p[0]-c[0])**2 + (p[1]-c[1])**2 + r.random()*0.1)[:n]
        for i, j in cand: mk[i, j] = True; x[i, j] = 0.3 + 0.01 * r.random()
        try:
            ref = MP.vrp(x, mk, MP.SENSORES["MODIS"])
            refv = ref["VRP_MW"]; npx = ref["npix"]
        except Exception as e:
            refv, npx = ("EXC " + type(e).__name__), None
        try:
            v = M.vrp_con(x, mk, MP.ORA._fillmissing2_lineal)
        except Exception as e:
            v = "EXC " + type(e).__name__
        tot += 1
        if isinstance(refv, float) and isinstance(v, float):
            if not (np.isnan(refv) and np.isnan(v)) and abs(v - refv) > 1e-9 * max(1, abs(refv)): mal += 1
        elif refv != v: mal += 1
        try:
            vr = M.vrp_con(x, mk, M.regla)
            if isinstance(v, float) and abs(vr - v) > 1e-6: difiere_regla += 1
        except Exception as e:
            pass
    res[n] = (mal, tot, difiere_regla)
    print("n=%d: identidad con el port falla en %d de %d; regla distinta del port en %d" % (n, mal, tot, difiere_regla))
