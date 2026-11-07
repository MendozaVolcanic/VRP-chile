#!/usr/bin/env python
"""F2 S175, linea base roja (2): la estratificacion por cenit tiene que ver la caida de magnitud de Nevados de Chillan.

Memoria S154 (experiments/_s154_chillan/razon_por_cenit_salida_20261018.txt en 752d348bc): en VIIRS 375 el 2026-10-18
la razon nuestro/MIROVA fue 0,64 y 0,72 a 20-22 grados, 0,46 a 49 y 0,35 a 68. Si mi estratificacion (campo
record.sensor_zenith_deg, bins de f2_banco_v375.zb) no separa esas magnitudes, esta ciega.

Diferencias con S154, declaradas: la magnitud nuestra es el display del predicado del tablero ejecutado con node (no
f5_core leido a mano); la de MIROVA es la mayor fila de alerta pareada a +-TOL_S tras la regla SN (S154 tomaba el
consolidado remoto sobre el OCR remoto, por minuto). Referencia: snapshot del arbol.
P1: si el cenit no ordenara nada, las medianas por bin serian iguales. P2: n por bin impreso; bin vacio = SIN DATO.
Control positivo: el mismo calculo sobre el dia exacto de S154 tiene que dar sus cuatro razones VIIRS 375.
Uso: python lb2_chillan_cenit.py <arbol> <salida.txt>
"""
import collections, json, os, statistics, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve(); OUT = Path(sys.argv[2])
sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp, clase_mirova as cm  # noqa: E401,E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada  # noqa: E402
assert Path(bp.__file__).resolve().is_relative_to(ARBOL)
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
L = []
for nombre, ini, fin in (("dia_S154", "2026-10-18", "2026-10-18"), ("erupcion_1018_1107", "2026-10-18", "2026-11-07"),
                         ("toda_0301_1107", "2026-03-01", "2026-11-07")):
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, (ini, fin), regla_minimas="SN")
    recs = [r for r in bp.cargar_nuestros(coords, inner, (ini, fin)) if r["vol"] == "NevadosDeChillan" and r["b"] == "VIIRS375"]
    bp.etiquetar(recs, por_vb, ns, nv)
    porbin = collections.defaultdict(list)
    L.append(f"== {nombre} {ini}..{fin} records V375 Chillan {len(recs)}")
    for r in sorted(recs, key=lambda r: r["dt"]):
        if r["lab"] != "pos":
            continue
        al = [f for f in bp.parear(por_vb[(r["vol"], r["b"])], r["dt"]) if f["tipo"] in cm.TIPOS_ALERTA and f["vrp_mw"]]
        if not al:
            continue
        m = max(f["vrp_mw"] for f in al)
        razon = (r["disp"] or 0) / m
        z = r["z"]
        b = "z<30" if z < 30 else ("z30-50" if z < 50 else ("z50-60" if z < 60 else "z>=60"))
        porbin[b].append(razon)
        if nombre == "dia_S154":
            L.append(f"  {r['dt']:%Y-%m-%d %H:%M} {r['sensor']:13s} cenit {z:5.1f} nuestro {r['disp']:.2f} MIROVA {m:.2f} razon {razon:.2f} pub {r['pub']}")
    for b in ("z<30", "z30-50", "z50-60", "z>=60"):
        x = porbin.get(b, [])
        L.append(f"  {b:7s} n {len(x):3d} mediana {statistics.median(x):.3f}" if x else f"  {b:7s} n   0 SIN DATO")
OUT.write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))
