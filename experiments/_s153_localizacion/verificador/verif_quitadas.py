"""Verificador S153: de lo que C0 publica en VIIRS 375 (V1, noche, predicado node), que quita K y donde estaba.

Uso: python -I experiments/_s153_localizacion/verificador/verif_quitadas.py <carpeta_union>
Para cada volcan: publicaciones de C0 que K conserva contra las que K quita; distancia del centroide del
cumulo (pc) y del marcador primario del mapa de detalle; fuente del ancla; etiqueta del evaluador
(banco_paridad.etiquetar: pos / neg_limpio / far_ref / sin_info).
"""
import sys, os, collections, statistics as st
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verif_posicion as vp  # noqa: E402
bp = vp.bp
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

U = sys.argv[1]
V = ("2026-08-29", "2026-10-08")
filas = cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
por_vb, ns, nv, _ = bp.indexar_referencia(filas, vp.COORDS, V)
tot = collections.Counter()
print(f"{'volcan':20s} {'K conserva: pc / mapa':38s} {'K quita: pc / mapa':38s} etiquetas quitadas | etiquetas conservadas | fuente quitadas")
for v in vp.VOLS:
    c0 = {r["datetime_utc"] + r["sensor"]: r for r in vp.cargar(os.path.join(U, "_s146_ab_control", v + ".json"), v, *V) if r["_pub"]}
    k = {r["datetime_utc"] + r["sensor"]: r for r in vp.cargar(os.path.join(U, "_s149_ab_sin_test1_b22_max", v + ".json"), v, *V) if r["_pub"]}
    grupos = {"cons": [], "quita": []}
    for kk, r in c0.items():
        m = vp.medir(r, v)
        dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        m.update(vol=v, b="VIIRS375", dt=dt, noche=dt.strftime("%Y-%m-%d"))
        grupos["cons" if kk in k else "quita"].append(m)
    for g in grupos.values():
        bp.etiquetar(g, por_vb, ns, nv)
    lab = {g: collections.Counter(x["lab"] for x in l) for g, l in grupos.items()}
    for g, c in lab.items():
        for kk2, n in c.items():
            tot[(g, kk2)] += n
    srcq = collections.Counter(x["src"] for x in grupos["quita"])
    f2 = lambda l: f"{vp.fmt([x['pc'] for x in l])} / {st.median([x['det'] for x in l]) if l else float('nan'):.2f}"
    print(f"{v:20s} {f2(grupos['cons']):38s} {f2(grupos['quita']):38s} {dict(lab['quita'])} | {dict(lab['cons'])} | {dict(srcq)}")
print("TOTAL etiquetas:", dict(tot))
