"""Verificador S153: fraccion de publicaciones VIIRS 375 (V1, noche, node) que el operador ve a mas de 2 km del crater,
segun cada posicion que el tablero usa: marcador primario del mapa de detalle, mapa general / tabla (final_hotspot),
y el centroide del cumulo (pc, el campo de la afirmacion). Uso: ... <carpeta_union> <brazo>"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verif_posicion as vp  # noqa: E402
U, arm = sys.argv[1], sys.argv[2]
V = ("2026-08-29", "2026-10-08")
print(f"brazo {arm}: {'volcan':20s} n  | >2km pc | >2km marcador detalle | >2km general/tabla (final_hotspot)")
T = collections.Counter()
for v in vp.VOLS:
    m = [vp.medir(r, v) for r in vp.cargar(os.path.join(U, arm, v + ".json"), v, *V) if r["_pub"]]
    if not m: print(f"   {v:20s} 0"); continue
    a = sum(x["pc"] is not None and x["pc"] > 2 for x in m); b = sum(x["det"] is not None and x["det"] > 2 for x in m); c = sum(x["fin"] is not None and x["fin"] > 2 for x in m)
    T["n"] += len(m); T["pc"] += a; T["det"] += b; T["fin"] += c
    print(f"   {v:20s} {len(m):3d} | {a/len(m):4.0%} | {b/len(m):4.0%} | {c/len(m):4.0%}")
print("   TOTAL", dict(T))
