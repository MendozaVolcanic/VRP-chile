#!/usr/bin/env python
"""F2 S175: el estrato «sin_geometria» de VIIRS 375 (filas ALERTA_SIN_GEOMETRIA_OCR: MIROVA vio calor en ESA pasada, con
su VRP, pero la imagen de distancia era de otra). No es protegida bajo la lectura A (clase_mirova, decision conservadora
del 2026-10-15). ¿Cuantas son de 1 MW o mas y las publicamos? P1: si el estrato estuviera vacio se dice SIN DATO. P2: n.
Uso: python sin_geometria.py <arbol> <inicio> <fin> <salida.txt>
"""
import json, os, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve(); INI, FIN, OUT = sys.argv[2], sys.argv[3], Path(sys.argv[4])
sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL)); os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada  # noqa: E402
coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, (INI, FIN), regla_minimas="SN")
recs = [r for r in bp.cargar_nuestros(coords, inner, (INI, FIN)) if r["b"] == "VIIRS375"]
bp.etiquetar(recs, por_vb, ns, nv)
sg = [r for r in recs if r["lab"] == "sin_geometria"]
L = [f"arbol {ARBOL.name} ventana {INI}..{FIN} V375 sin_geometria n {len(sg)} publicadas {sum(r['pub'] for r in sg)}"]
for r in sg:
    v = max([f["vrp_mw"] or 0 for f in bp.parear(por_vb[(r["vol"], r["b"])], r["dt"]) if bp.es_sin_geometria(f["tipo"])], default=0)
    if v >= 1:
        L.append(f"  >=1 MW: {r['vol']} {r['dt']:%Y-%m-%d %H:%M} {r['sensor']} cenit {r['z']} MIROVA {v} MW | pub {r['pub']} disp {r['disp']} dc {r['dc']}")
OUT.write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))
