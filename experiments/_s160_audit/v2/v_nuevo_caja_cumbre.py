"""Hallazgo propio: los C1/C2 de cumbre (0,003 y 5 sigma) rigen en nuestro circulo inner_radius_km (3 a 20 km),
y en el codigo de MIROVA sólo en la caja BOX==2 de 7x7 pixeles (ejemplo OSF: filas y columnas 30-36 de 67,
media anchura 2,625 km a 750 m). Fuera de la caja MIROVA usa 10 sigma y 0,02/0,01 (0,0225/0,01125 en 8 vecinos).
Mido cuantos records PUBLICADOS (predicado del tablero con node) tienen el centroide del cumulo a mas de
2,625 km del crater (fuera de la caja aunque sea una caja y no un circulo: en las diagonales la caja llega a
3,7 km, asi que 2,625 es cota inferior de la distancia a la que se sale; lo cuento tambien con 3,712).
Pregunta 1: si todo lo publicado cayera dentro de la caja, daria 0; control positivo: umbral 0 km debe dar 100 %.
Ventanas: 2026-03-01..2026-10-21 y 2026-09-18..2026-10-21, nocturnos."""
import os, sys
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
SNAP = Path(r"D:\vrp-trabajo\temporales\s160_audit\main")
sys.path.insert(0, str(SNAP / "scripts")); sys.path.insert(0, str(SNAP))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html(); out = []
for w in [("2026-03-01", "2026-10-21"), ("2026-09-18", "2026-10-21")]:
    recs = [r for r in bp.cargar_nuestros(coords, inner, w) if r["pub"]]
    c = Counter()
    for r in recs:
        b = r["b"]; d = r["pc_dist"]
        c[(b, "pub")] += 1
        if d is None: c[(b, "sin_dist")] += 1; continue
        if d > 0: c[(b, "CTRL>0")] += 1
        if d > 2.625: c[(b, ">2.625")] += 1
        if d > 3.712: c[(b, ">3.712")] += 1
        if d > 2.625: c[(b, r["vol"])] += 1
    for b in ["MODIS", "VIIRS375", "VIIRS750"]:
        n = c[(b, "pub")]
        out.append(f"{w} {b} publicados={n} >2,625km={c[(b,'>2.625')]} ({100*c[(b,'>2.625')]/n:.1f}%) >3,712km={c[(b,'>3.712')]} ({100*c[(b,'>3.712')]/n:.1f}%) CTRL>0={c[(b,'CTRL>0')]} sin_dist={c[(b,'sin_dist')]} | por volcan >2,625: " +
                   ", ".join(f"{v}={c[(b,v)]}" for v in bp.VOLS if c[(b, v)]))
print("\n".join(out))
Path(__file__).with_name("v_nuevo_caja_cumbre_salida.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
