# -*- coding: utf-8 -*-
"""MODIS bajo K (2026-09-18 a 2026-10-18): las pasadas con ALERTA de MIROVA y las negativas limpias con
cumulo con magnitud dentro del inner; cuantas oculta la etiqueta 'far' (cara far->summit de A81/D12).
P1: si la etiqueta no ocultara nada bajo K, la columna 'far con inner' sale 0. P2: el predicado es el
de node (banco_paridad, identidad verificada); la ventana C0 previa se lista con el mismo codigo como
contraste (debe mostrar far con inner en negativos, A82)."""
import sys, io, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402
coords = B._coords_por_volcan(); inner = B.inner_desde_html()
assert B.control_identidad_predicado() == ([0, 1, 1, 1, 0], [1, 0])
filas = B.cargar_referencia_unificada(B.SNAP_CONS, B.SNAP_OCR)
for nombre, ven in [("C0", ("2026-08-18", "2026-09-17")), ("K", ("2026-09-18", "2026-10-18"))]:
    por_vb, ns, nv, _ = B.indexar_referencia(filas, coords, ven)
    recs = [r for r in B.cargar_nuestros(coords, inner, ven) if r["b"] == "MODIS"]
    B.etiquetar(recs, por_vb, ns, nv)
    c = collections.Counter()
    for r in recs:
        mi = (r["pc_vrp"] or 0) > 0 and r["pc_dist"] is not None and r["pc_dist"] <= inner[r["vol"]]
        c[(r["lab"], "mag_inner" if mi else "sin", r["dc"], "pub" if r["pub"] else "nopub")] += 1
    print(f"\n== {nombre} {ven} MODIS nocturno, n={len(recs)}")
    for k in sorted(c, key=str):
        if k[0] in ("pos", "neg_limpio"):
            print("  ", k, c[k])
    if nombre == "K":
        for r in recs:
            if r["lab"] == "pos":
                print("    pos", r["vol"], r["dt"], "dc", r["dc"], "pc", r["pc_vrp"], r["pc_dist"], "pub", r["pub"])
