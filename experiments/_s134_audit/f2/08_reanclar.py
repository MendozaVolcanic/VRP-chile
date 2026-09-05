# -*- coding: utf-8 -*-
"""F2/08 - RE-ANCLAR antes de concluir (reference_s115_pcc_anchor_parity, A13, D15).

EL RIESGO. MIROVA no mide su Distancia_km desde nuestro vent_lat/lon: la mide desde el
centro de SU grilla. Si ese centro esta a 7 km del crater -- y en PCC lo esta -- entonces
una Distancia_km de 8 km puede describir un punto que esta EN el crater. Comparar su numero
contra el nuestro sin re-anclar seria comparar dos reglas con cero distinto.

QUE HAGO: (1) mido el offset ancla-crater en los 11; (2) recomputo NUESTRA distancia desde
el ancla de MIROVA, que es la unica comparacion apples-to-apples; (3) recien ahi comparo.
Read-only."""
import json, os, statistics as st
import f2_lib as F
F.utf8()
_d = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(_d, "resultados.json"), encoding="utf-8"))["filas"]
cat = F.catalogo()

print("=== (1) OFFSET del ancla de MIROVA respecto del crater (vent_lat/lon) ===")
print("%-21s %-12s %-12s" % ("volcan", "mirova_center", "gvp"))
off = {}
for v in sorted(set(r["volcan"] for r in R)):
    c = cat[v]
    dmc = (F.haversine(c["vent_lat"], c["vent_lon"], c["mirova_center_lat"], c["mirova_center_lon"])
           if c.get("mirova_center_lat") is not None else None)
    dg = F.haversine(c["vent_lat"], c["vent_lon"], c["lat"], c["lon"])
    off[v] = (dmc, dg)
    print("%-21s %-12s %-12.2f" % (v, "%.2f" % dmc if dmc is not None else "s/d", dg))

print("\n=== (2) NUESTRO cumulo medido desde el ANCLA DE MIROVA, vs su Distancia_km ===")
print("Ahora las dos reglas tienen el mismo cero. Si MIROVA integrara el crater y nosotros")
print("el flanco, su numero seria el chico. Ventana: ALERTAS VIIRS375 desde 2026-06-01.\n")
print("%-21s %4s | %-13s %-13s | %-11s | %s" % (
    "volcan","n","nuestro@mc","MIROVA_decl","delta_med","MIROVA mas cerca"))
GA, GB = [], []
recs = {}
for v in sorted(set(r["volcan"] for r in R)):
    c = cat[v]
    if c.get("mirova_center_lat") is None: continue
    mla, mlo = c["mirova_center_lat"], c["mirova_center_lon"]
    p = []
    for x in [r for r in R if r["volcan"] == v and r.get("dist_km_mirova") is not None]:
        # recomputo la distancia de NUESTRO centroide desde el ancla de MIROVA
        key = (v, x["pasada_utc"])
        if v not in recs:
            import datetime as dt
            recs[v] = {r["_ts"].strftime("%Y-%m-%d %H:%M:%S"): r
                       for r in F.records(v, F.IBAND, dt.datetime(2026,6,1,tzinfo=dt.timezone.utc))}
        r0 = recs[v].get(x["pasada_utc"])
        if r0 is None:
            # el record puede diferir 1-2 s del sello de la alerta
            cand = [rr for kk, rr in recs[v].items() if kk[:16] == x["pasada_utc"][:16]]
            r0 = cand[0] if cand else None
        if r0 is None: continue
        pc = r0.get("primary_cluster") or {}
        if pc.get("centroid_lat") is None: continue
        p.append((F.haversine(mla, mlo, pc["centroid_lat"], pc["centroid_lon"]), x["dist_km_mirova"]))
    if not p: print("%-21s %4d | SIN DATO" % (v, 0)); continue
    a = [q[0] for q in p]; b = [q[1] for q in p]; d = [y-x for x, y in p]
    GA += a; GB += b
    print("%-21s %4d | %-13.2f %-13.2f | %+-11.2f | %.0f%%" % (
        v, len(p), st.median(a), st.median(b), st.median(d),
        100*sum(1 for x in d if x < 0)/len(d)))
print("%-21s %4d | %-13.2f %-13.2f | %+-11.2f | %.0f%%" % (
    "GLOBAL", len(GA), st.median(GA), st.median(GB),
    st.median([y-x for x, y in zip(GA, GB)]),
    100*sum(1 for x, y in zip(GA, GB) if y < x)/len(GA)))
print("\n  delta>0 = MIROVA declara su punto MAS LEJOS de su propio centro que el nuestro.")
print("  'MIROVA mas cerca' = %% de pasadas en que su cumulo esta mas pegado al centro que el nuestro.")
