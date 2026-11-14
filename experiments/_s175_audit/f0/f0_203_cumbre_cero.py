"""F0 S175, hallazgo 203 de S160 (y C-08): cúmulos de cumbre de VIIRS 750 con 0,0 MW, que el tablero no publica.

Fenómeno: cuando el píxel del cráter está a la temperatura del anillo regional o más frío, el exceso de radiancia
sale negativo y el código lo recorta a cero (D25); un cúmulo con 0 MW no se publica.

Vara: banco_paridad de la base 752d348bc (predicado del tablero con node, etiquetar con la referencia del snapshot
del repo, SNAP_CONS y SNAP_OCR), árbol extraído con git archive en C:\\Users\\nmend\\vrp-temporales\\s175_audit\\f0\\arbol.

Línea base roja propia: la ventana K de S160 (2026-09-18 a 2026-10-21) tiene que volver a dar del orden de 30 de 97
(S160 V2; el corpus cambió desde entonces por reprocesos, A90, así que se informa el número de hoy, no se exige igual).
P1: si el recorte no existiera, la cuenta de pc_vrp == 0 sería 0; la vería. P2: control de identidad del predicado
y total de cúmulos de cumbre > 0; con el instrumento muerto ambos fallan.
"""
import io
import os
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ARBOL = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\f0\arbol")
sys.path.insert(0, str(ARBOL / "scripts"))
sys.path.insert(0, str(ARBOL))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

print("banco_paridad leído de:", bp.__file__)
print("referencia:", bp.SNAP_CONS, bp.SNAP_OCR)
print("CONTROL identidad del predicado:", bp.control_identidad_predicado())
coords = bp._coords_por_volcan()
inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
print("última fecha de la referencia:", max(str(f.get("dt") or f.get("fecha") or "") for f in filas)[:19])

for ventana in [("2026-09-18", "2026-10-21"), ("2026-10-22", "2026-11-02"), ("2026-11-03", "2026-11-07")]:
    recs = bp.cargar_nuestros(coords, inner, ventana)
    por_vb, ns, nv, n = bp.indexar_referencia(filas, coords, ventana)
    bp.etiquetar(recs, por_vb, ns, nv)
    print(f"\n=== ventana {ventana}: pasadas nocturnas {len(recs)}, publicadas {sum(r['pub'] for r in recs)}")
    for b in ("VIIRS750", "VIIRS375", "MODIS"):
        cum = [r for r in recs if r["b"] == b and r["pc_vrp"] is not None and r["dc"] == "summit"]
        cero = [r for r in cum if (r["pc_vrp"] or 0) == 0]
        lab = Counter(r["lab"] for r in cero)
        pub0 = sum(r["pub"] for r in cero)
        print(f"{b}: cúmulos de cumbre {len(cum)}, con 0,0 MW {len(cero)} "
              f"({round(100*len(cero)/len(cum),1) if cum else 'SIN DATO'} %), publicados entre los 0 MW {pub0}, "
              f"etiquetas {dict(lab)}")
        if b == "VIIRS750":
            for r in sorted(cero, key=lambda x: x["dt"]):
                if r["lab"] in ("pos", "minima"):
                    al = [f for f in bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"]) if bp.es_alerta(f["tipo"])]
                    print(f"   con alerta MIROVA: {r['vol']} {r['sensor']} {r['dt']:%Y-%m-%d %H:%M} "
                          f"MIROVA {[ (f['tipo'], f['vrp_mw']) for f in al]}")
