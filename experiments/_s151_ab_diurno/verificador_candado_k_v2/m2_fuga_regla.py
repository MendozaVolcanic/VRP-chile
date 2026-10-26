# -*- coding: utf-8 -*-
"""¿Las comprobaciones rápidas del arnés dejan ED.REGLA en la base k al salir? Si sí, la comprobación
«con base c0 se informa la cola exacta sin cambiar la regla» (chequear_cola_exacta, última) corre con la regla k."""
import contextlib, io, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AQUI))
import probar_evaluar_diurno as PE
ED = PE.ED
print("inicio:", ED.REGLA)
for f in ("chequear_orden_del_nulo", "chequear_base_k", "chequear_cola_exacta", "chequear_regla_w2", "chequear_h2a_h2b"):
    with contextlib.redirect_stdout(io.StringIO()):
        getattr(PE, f)()
    print("tras %-24s REGLA = %s" % (f, ED.REGLA))
# la comprobación de c0 al final de chequear_cola_exacta: ¿con qué regla decide g1 ahí?
est_e = [(4, 2, 2), (6, 1, 2)]
cls_e = PE._cls_desde_estratos(est_e, [2, 1])
r0 = ED.g1(cls_e, ("W3",), ED.np.random.default_rng(ED.SEMILLA))
print("g1 en el punto de la comprobación «base c0»: regla =", r0["regla"])
print("resultados:", sum(ok for _c, ok in PE.RESULTADOS), "de", len(PE.RESULTADOS))
