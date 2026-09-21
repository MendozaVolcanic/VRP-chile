# -*- coding: utf-8 -*-
"""S149 FRENTE C. De las pasadas con alerta MODIS / VIIRS750 que produccion no publica: en cuantas
la MISMA noche y volcan se publico algo con cualquier sensor (unidad del operador, A94). n en cada linea."""
import io, sys, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev
bp = ev.bp
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = ev.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
for b, v in (("MODIS", ("2026-03-01", "2026-09-21")), ("VIIRS750", ("2026-06-13", "2026-09-21"))):
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, v)
    recs = ev.cargar_brazo(bp.DATA, coords, inner, v); bp.etiquetar(recs, por_vb, ns, nv)
    pubn = collections.defaultdict(set)
    for r in recs:
        if r["pub"]: pubn[(r["vol"], r["noche"])].add(r["b"])
    perd = [r for r in recs if r["b"] == b and r["lab"] == "pos" and not r["pub"]]
    noches = {(r["vol"], r["noche"]) for r in perd}
    cub = sum(1 for n in noches if pubn.get(n))
    print(b, v, "| pasadas con alerta no publicadas:", len(perd), "| noches de volcan:", len(noches), "| de esas, noches con alguna publicacion nuestra (cualquier sensor):", cub,
          "| por sensor que cubre:", dict(collections.Counter(s for n in noches for s in pubn.get(n, []))))
