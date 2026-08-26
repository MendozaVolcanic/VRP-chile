# -*- coding: utf-8 -*-
"""S124 - Existen huecos de la serie explicados por CEGUERA y no por calma?

POR QUE: una banda de observabilidad solo vale si hay casos donde el lector
sacaria la conclusion equivocada sin ella. Busco ventanas de >=5 dias SIN
deteccion summit y pregunto si en esa ventana el cielo estaba tapado.
Si casi ningun hueco es ciego, la banda es adorno y no se implementa.
"""
import json, sys, io, collections, pathlib, datetime as dt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PIX = (50/0.375)**2
VOLS = ["NevadosDeChillan","Villarrica","Lascar","Isluga","Llaima","Copahue",
        "Tupungatito","Lastarria","PuyehueCordonCaulle","PlanchonPeteroa","Chaiten"]

def dia(s): return s[:10]

total_huecos = total_ciegos = 0
detalle = []
for v in VOLS:
    p = pathlib.Path(f"data/mirova_equivalent/{v}.json")
    if not p.exists(): continue
    d = json.loads(p.read_text(encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) else d

    det = set()            # dias con deteccion summit
    ceg = collections.defaultdict(list)   # dia -> fracciones de ceguera VIIRS375
    dias = set()
    for r in recs:
        dd = dia(r["datetime_utc"]); dias.add(dd)
        pc = r.get("primary_cluster") or {}
        if r.get("distance_class") == "summit" and pc.get("vrp_mw"): det.add(dd)
        if r.get("n_cloud_masked") is not None:
            ceg[dd].append(100.0*r["n_cloud_masked"]/PIX)
    if not dias: continue

    d0, d1 = min(dias), max(dias)
    cur = dt.date.fromisoformat(d0); fin = dt.date.fromisoformat(d1)
    racha = []
    while cur <= fin:
        s = cur.isoformat()
        if s not in det: racha.append(s)
        else:
            if len(racha) >= 5:
                fr = [f for dd in racha for f in ceg.get(dd, [])]
                fr.sort()
                med = fr[len(fr)//2] if fr else None
                total_huecos += 1
                # "ciego" = la MEDIANA de la ventana tapa mas de la mitad del ROI
                if med is not None and med > 50:
                    total_ciegos += 1
                    detalle.append((v, racha[0], racha[-1], len(racha), med))
            racha = []
        cur += dt.timedelta(days=1)

print(f"Huecos de >=5 dias sin deteccion summit: {total_huecos}")
print(f"  de esos, CIEGOS (mediana de nube >50% del ROI): {total_ciegos}"
      f"  ({100*total_ciegos/total_huecos if total_huecos else 0:.0f}%)\n")
if detalle:
    print(f"{'volcan':22s} {'desde':11s} {'hasta':11s} {'dias':>5s} {'nube':>6s}")
    for v,a,b,n,m in sorted(detalle, key=lambda x:-x[3])[:15]:
        print(f"{v:22s} {a:11s} {b:11s} {n:5d} {m:5.0f}%")
else:
    print("  -> NINGUNO. La banda no tiene caso que justificarla.")
