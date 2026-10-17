import sys, collections, statistics as st, json
sys.path.insert(0, "scripts")
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada
V = ("2026-09-01", "2026-10-16")
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, V)
recs = bp.cargar_nuestros(coords, inner, V)
bp.etiquetar(recs, por_vb, ns, nv)
# 1) VRP minimo con que MIROVA publica alertas, y cuantas filas RUTINA/CONS traen VRP > 0
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    al = sorted(f["vrp_mw"] for f in filas if f["sensor_bucket"] == b and bp.es_alerta(f["tipo"]) and f["vrp_mw"] is not None and V[0] <= f["fecha_utc"][:10] <= V[1])
    rut = [f["vrp_mw"] for f in filas if f["sensor_bucket"] == b and f["tipo"] == "RUTINA" and V[0] <= f["fecha_utc"][:10] <= V[1]]
    print(f"{b}: alertas MIROVA n {len(al)}, VRP min {al[0] if al else None}, p10 {al[len(al)//10] if al else None} | RUTINA n {len(rut)}, con VRP>0 {sum(1 for x in rut if x)}, valores distintos de VRP en RUTINA {sorted(set(rut))[:6]}")
# 2) lo que publicamos en negativos limpios: magnitud que muestra el tablero (disp)
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    neg = [r for r in recs if r["b"] == b and r["lab"] == "neg_limpio" and r.get("pub")]
    disp = sorted(float(r["disp"]) for r in neg if r.get("disp") is not None)
    if not disp: print(b, "sin publicaciones en negativos"); continue
    q = lambda p: disp[min(len(disp) - 1, int(p * len(disp)))]
    cuenta = lambda t: sum(1 for x in disp if x < t)
    print(f"{b}: publicamos en {len(neg)} negativos | VRP mostrado mediana {st.median(disp):.3f}, p10 {q(.1):.3f}, p90 {q(.9):.3f}, max {disp[-1]:.2f} | "
          f"<0,005 {cuenta(0.005)}, <0,05 {cuenta(0.05)}, <0,1 {cuenta(0.1)}, <0,5 {cuenta(0.5)}, >=1 {sum(1 for x in disp if x >= 1)}")
