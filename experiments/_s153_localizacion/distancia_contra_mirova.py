import sys, statistics as st, collections
sys.path.insert(0, "scripts")
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada
V = ("2026-09-01", "2026-10-16")
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, V)
recs = bp.cargar_nuestros(coords, inner, V)
out = collections.defaultdict(list)
for r in recs:
    if not r.get("pub"): continue
    al = [f for f in bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"]) if bp.es_alerta(f["tipo"]) and f.get("dist_km") is not None]
    if not al or r["pc_dist"] is None: continue
    f = al[0]
    out[r["b"]].append((r["vol"], r["pc_dist"], f["dist_km"], f.get("source")))
for b, l in sorted(out.items()):
    d = [o - m for _, o, m, _ in l]; a = [abs(x) for x in d]
    print(f"{b:9s} n {len(l):4d} | dist nuestra mediana {st.median(o for _,o,_,_ in l):.2f} km, MIROVA {st.median(m for _,_,m,_ in l):.2f} km | "
          f"|dif| mediana {st.median(a):.2f} km, p90 {sorted(a)[int(.9*len(a))]:.2f} | dentro de 1 km {sum(x<=1 for x in a)/len(a):.0%}, de 2 km {sum(x<=2 for x in a)/len(a):.0%} | "
          f"dif con signo mediana {st.median(d):+.2f}")
    pv = collections.defaultdict(list)
    for v, o, m, _ in l: pv[v].append(abs(o - m))
    print("    por volcan |dif| mediana:", {v: (len(x), round(st.median(x), 2)) for v, x in sorted(pv.items())})
