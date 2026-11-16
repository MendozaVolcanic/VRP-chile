#!/usr/bin/env python
"""V2: F2-201, las 5 noches con una protegida no publicada: que otras pasadas de esa noche (volcan, V375) hay, cuales publican y con
que etiqueta de MIROVA. P1: el control es que la protegida perdida aparezca en la lista con pub 0; P2: n de pasadas de cada noche impreso."""
import os, sys
from pathlib import Path
ARBOL = Path(sys.argv[1]); sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL)); os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp, clase_mirova as cm
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
recs = bp.cargar_nuestros(coords, inner, ("2026-03-01", "2026-11-07"))
por_vb, ns, nv, n = bp.indexar_referencia(filas, coords, ("2026-03-01", "2026-11-07"), regla_minimas="SN"); bp.etiquetar(recs, por_vb, ns, nv)
out = []
for vol, noche in (("Lascar", "2026-08-22"), ("Lastarria", "2026-04-18"), ("Lastarria", "2026-05-02"), ("Tupungatito", "2026-09-28"), ("Tupungatito", "2026-09-29")):
    out.append(f"== {vol} {noche}")
    for r in sorted((r for r in recs if r["vol"] == vol and r["noche"] == noche and r["b"] == "VIIRS375"), key=lambda r: r["dt"]):
        par = bp.parear(por_vb.get((vol, "VIIRS375"), []), r["dt"])
        out.append(f"   {r['dt']:%H:%M} {r['sensor']:13s} z {r['z']:5.1f} lab {r['lab']:11s} pub {r['pub']} disp {r['disp']} dc {r['dc']} mirova {[(f['tipo'], f['source'], f['vrp_mw']) for f in par]}")
Path(sys.argv[2]).write_text("\n".join(out) + "\n", encoding="utf-8"); print("\n".join(out))
