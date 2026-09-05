# -*- coding: utf-8 -*-
"""F2/06 - CONTROL DEL CONDICIONAMIENTO. Por que mi d_crater no es el de S133?

EL FENOMENO. S133 midio el anillo sobre TODOS los records que publicamos (magnitud>0,
clase summit). Yo mido sobre el subconjunto en que MIROVA ADEMAS declaro ALERTA. No son
la misma poblacion: las pasadas con ALERTA son aquellas donde habia senal suficiente para
que DOS sistemas independientes la vieran. Si el anillo de 2,3-2,8 km viviera en las
pasadas que MIROVA no confirma, las dos medianas tienen que separarse. Este es el control
del denominador (A90): el mismo campo, dos poblaciones, un numero distinto.

LAS DOS PREGUNTAS:
1. Si NO hubiera efecto de condicionamiento, esto lo veria? SI: las dos medianas darian
   iguales dentro del ruido. El control positivo es Lascar, donde S133 midio 0,22 km sobre
   TODO y yo mido 0,16 sobre el subconjunto: ahi las dos poblaciones casi coinciden, o sea
   la medicion NO fabrica separacion donde no la hay.
2. Si mi replica de S133 estuviera muerta (filtro mal escrito, 0 records), se veria
   distinto? SI: reporto n de cada poblacion y comparo mi replica de la columna S133 contra
   la tabla publicada en docs/s133/ANILLO_TIER_A.md.
Read-only."""
import datetime as dt, json, os, statistics as st
import f2_lib as F
F.utf8()
_d = os.path.dirname(os.path.abspath(__file__))
D0 = dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc)
R = json.load(open(os.path.join(_d, "resultados.json"), encoding="utf-8"))["filas"]

# Tabla publicada por S133 (docs/s133/ANILLO_TIER_A.md), columna VIIRS 375 m
S133 = {"Lascar":(0.22,208),"Isluga":(0.96,313),"PuyehueCordonCaulle":(1.08,313),
        "Tupungatito":(2.27,223),"Lastarria":(2.28,144),"PlanchonPeteroa":(2.45,251),
        "Chaiten":(2.49,323),"NevadosDeChillan":(2.61,189),"Villarrica":(2.79,289),
        "Copahue":(2.80,305),"Llaima":(2.84,277)}

cat = F.catalogo()
print("REPLICA de S133 (todos los records publicados) vs SUBCONJUNTO con ALERTA MIROVA")
print("Ventana comun: desde 2026-06-01. Criterio S133: magnitud>0 y distance_class=summit.\n")
print("%-21s | %-22s | %-20s | %s" % ("volcan","S133 publicado (n)","mi replica (n)","con ALERTA MIROVA (n)"))
print("-"*92)
out = {}
for v in sorted(S133):
    c = cat[v]; vla, vlo = c["vent_lat"], c["vent_lon"]
    ds = []
    for r in F.records(v, F.IBAND, D0):
        p = r.get("primary_cluster") or {}
        if r.get("distance_class") != "summit": continue
        m = r.get("f5_core_vrp_mw"); m = p.get("vrp_mw") if m is None else m
        if not m or m <= 0: continue
        if p.get("centroid_lat") is None: continue
        ds.append(F.haversine(vla, vlo, p["centroid_lat"], p["centroid_lon"]))
    sub = [x["d_crater_nuestro_km"] for x in R
           if x["volcan"] == v and x.get("d_crater_nuestro_km") is not None]
    a, b = S133[v]
    print("%-21s | %5.2f km (n=%-4d)      | %5s km (n=%-4d)  | %5s km (n=%d)" % (
        v, a, b,
        "%.2f" % st.median(ds) if ds else "s/d", len(ds),
        "%.2f" % st.median(sub) if sub else "s/d", len(sub)))
    out[v] = dict(s133_publicado_km=a, s133_n=b,
                  replica_km=round(st.median(ds), 2) if ds else None, replica_n=len(ds),
                  con_alerta_km=round(st.median(sub), 2) if sub else None, con_alerta_n=len(sub))

todos = [x for v in out.values() if v["replica_km"] is not None for x in [v]]
print("\nCONTROL de la replica: mi mediana vs la de S133, por volcan")
e = [abs(v["replica_km"]-v["s133_publicado_km"]) for v in out.values() if v["replica_km"] is not None]
print("  error mediano de la replica contra la tabla publicada: %.2f km (n=%d volcanes)" % (st.median(e), len(e)))
print("  -> si fuera grande, mi replica no reproduce a S133 y la comparacion no valdria")

print("\nDESPLAZAMIENTO por condicionar en ALERTA MIROVA (replica -> con alerta):")
dd = [(v, o["replica_km"], o["con_alerta_km"], o["con_alerta_km"]-o["replica_km"])
      for v, o in out.items() if o["replica_km"] is not None and o["con_alerta_km"] is not None]
for v, a, b, d in sorted(dd, key=lambda x: x[3]):
    print("  %-21s %5.2f -> %5.2f  (%+.2f km)" % (v, a, b, d))
print("  mediana del desplazamiento: %+.2f km (n=%d volcanes)" % (st.median([x[3] for x in dd]), len(dd)))
json.dump(out, open(os.path.join(_d, "control_condicionamiento.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
