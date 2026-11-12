import sys, json
sys.path[:0] = [r"D:\vrp-trabajo\worktrees\s181-verif-994\scripts", r"D:\vrp-trabajo\worktrees\s181-verif-994"]
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada
ventana = ("2026-03-01", "2026-11-01")
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana, regla_minimas=bp.MODO_MINIMAS)
out = {}
for nombre, data in (("antes_K", r"D:\vrp-trabajo\temporales\s181_verif994\antes_data"),
                     ("despues_via", r"D:\vrp-trabajo\worktrees\s181-verif-994\data\mirova_equivalent")):
    recs = bp.cargar_nuestros(coords, inner, ventana, data=data)
    bp.etiquetar(recs, por_vb, ns, nv)
    sr = bp.alertas_sin_record(por_vb, recs)
    ps, pv = bp.resumen(recs, sr)
    out[nombre] = {"por_sensor": ps, "por_volcan": pv}
json.dump(out, open(r"D:\vrp-trabajo\temporales\s181_verif994\banco_ab.json", "w", encoding="utf-8"), indent=1)
for b in list(out["antes_K"]["por_sensor"]):
    for nombre in out:
        p = out[nombre]["por_sensor"][b]
        print(f"{b:10s} {nombre:11s} pasada: pos {p['pasada']['n_pos']:4d} recall {p['pasada']['recall_pos']}  neg {p['pasada']['n_neg_limpio']:5d} pub_neg {p['pasada']['tasa_pub_neg']}  | noche: pos {p['noche_volcan']['n_pos']} recall {p['noche_volcan']['recall_pos']} neg {p['noche_volcan']['n_neg']} pub_neg {p['noche_volcan']['tasa_pub_neg']}")
for nombre in out:
    p = out[nombre]["por_volcan"]["PuyehueCordonCaulle"]["MODIS"]
    print("PCC MODIS", nombre, p["noche_volcan"], "pasada pos", p["pasada"]["n_pos"], p["pasada"]["recall_pos"])

# S181: pasadas pos que K publica y la via no (y al reves), con el VRP maximo de MIROVA en la pasada.
recsK = bp.cargar_nuestros(coords, inner, ventana, data=r"D:\vrp-trabajo\temporales\s181_verif994\antes_data")
recsV = bp.cargar_nuestros(coords, inner, ventana, data=r"D:\vrp-trabajo\worktrees\s181-verif-994\data\mirova_equivalent")
for rs in (recsK, recsV): bp.etiquetar(rs, por_vb, ns, nv)
k = lambda r: (r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M"))
iK = {k(r): r for r in recsK if r["lab"] == "pos"}; iV = {k(r): r for r in recsV if r["lab"] == "pos"}
def mw(r):
    return max((f["vrp_mw"] or 0) for f in bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"]) if bp.es_alerta(f["tipo"]))
perdidas = sorted((mw(iK[c]), c) for c in iK if iK[c]["pub"] and c in iV and not iV[c]["pub"])
ganadas = sorted((mw(iV[c]), c) for c in iV if iV[c]["pub"] and c in iK and not iK[c]["pub"])
solo = [c for c in iK if c not in iV]
print("pos que K publica y la via no:", len(perdidas), " >=1 MW:", [(round(m,2), c) for m, c in perdidas if m >= 1])
print("pos que la via publica y K no:", len(ganadas), " >=1 MW:", sum(1 for m, c in ganadas if m >= 1))
print("pos de K sin pasada en la via:", len(solo), [(c, round(mw(iK[c]),2), iK[c]["pub"]) for c in solo][:8])
nochesV = {(r["vol"], r["b"], r["noche"]) for r in recsV if r["pub"]}
nochesVany = {(r["vol"], r["noche"]) for r in recsV if r["pub"]}
for m, c in perdidas:
    if m < 1: continue
    r = iK[c]
    print(c, round(m, 2), "noche V375 publicada por la via:", (r["vol"], r["b"], r["noche"]) in nochesV, "| cualquier sensor:", (r["vol"], r["noche"]) in nochesVany)
