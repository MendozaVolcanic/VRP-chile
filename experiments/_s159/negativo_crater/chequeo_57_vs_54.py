# -*- coding: utf-8 -*-
"""Por que salen 57 negativos MODIS y no 54 (verificador del pareo): etiqueta del companero de los que salen.
P1: si la diferencia fuera de datos y no de definicion, los 57 tendrian todos companero sin_info. Uso: python -I este.py <espejo>"""
import collections, os, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = Path(sys.argv[1])
for p in (AQUI, RAIZ, RAIZ / "scripts"): sys.path.insert(0, str(p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp, auto_audit_weekly as aw, nlc
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
NBG, COMP, _ = nlc.indice_anillo(bp.DATA, bp.VOLS)
co = aw._coords_por_volcan(); w = ("2026-01-10", "2026-10-21")
pv, ns, nv, _ = bp.indexar_referencia(cargar_referencia_unificada(SNAP_CONS, SNAP_OCR), co, w)
recs = bp.cargar_nuestros(co, bp.inner_desde_html(), w); bp.etiquetar(recs, pv, ns, nv)
k = lambda r: (r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"))
idx = {k(r): r for r in recs}
for b in bp.BUCKETS:
    c = collections.Counter()
    for r in recs:
        if r["b"] != b or r["lab"] != "neg_limpio": continue
        f = nlc.fraccion(k(r), NBG, COMP)
        if f in (None, "indet") or f >= 0.5: continue
        q = COMP[k(r)]
        c[idx[q]["lab"] if q in idx else "companero fuera de la ventana o diurno"] += 1
    print(b, "salen por companero:", dict(c))
