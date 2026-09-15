# Descriptivo: clase global del contraste si se mide solo sobre los vecinos calientes PERDIDOS (no es el pre-registro)
import sys, io, statistics as st
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE))
from juntar import cargar
from analisis_v2 import fila_valida, _clase_estable, CONTRASTE_MIN_K, N_MIN_VOLCAN
filas = cargar(HERE / "artefactos"); val = [f for f in filas if fila_valida(f)[0]]
med = lambda xs: st.median(xs) if xs else None
pv = {}
for vol in sorted({f["volcan"] for f in val}):
    fs = [f for f in val if f["volcan"] == vol]
    lo = [med([v["exceso_local_k"] for v in f["resumen"]["vecinos"] if v["caliente"] and not v["incluido"] and v["exceso_local_k"] is not None]) for f in fs]
    lo = [x for x in lo if x is not None]
    ctl = med([f["resumen"]["control"]["exceso_mediano_calientes_k"] for f in fs if f["resumen"].get("control")])
    c = med(lo) - ctl
    pv[vol] = {"contraste": "VECINOS_TIBIOS" if c >= CONTRASTE_MIN_K else "SIN_CONTRASTE", "evaluable": len(fs) >= N_MIN_VOLCAN}
print(pv)
print("clase global solo perdidos:", _clase_estable(pv, "contraste", ("VECINOS_TIBIOS", "SIN_CONTRASTE")))
