#!/usr/bin/env python
"""V2: etiquetas de las pasadas V375 por dia, 2026-10-30 a 2026-11-07, en el arbol 752d348bc (F2-207). P1: el control es que
antes del corte (10-30..11-01) existan neg_limpio y pos; P2: la tabla acaba el 11-02, asi que desde el 03 todo debe ser sin_info."""
import collections, os, sys
from pathlib import Path
ARBOL = Path(sys.argv[1]); sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL)); os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
recs = bp.cargar_nuestros(coords, inner, ("2026-10-30", "2026-11-07"))
por_vb, ns, nv, n = bp.indexar_referencia(filas, coords, ("2026-10-30", "2026-11-07"), regla_minimas="SN")
bp.etiquetar(recs, por_vb, ns, nv)
t = collections.defaultdict(collections.Counter)
for r in recs:
    if r["b"] == "VIIRS375": t[r["noche"]][r["lab"]] += 1; t[r["noche"]]["pub"] += r["pub"]
out = [f"{d} {dict(t[d])}" for d in sorted(t)]
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(out) + "\n"); print("\n".join(out))
