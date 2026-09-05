# -*- coding: utf-8 -*-
"""F2/07 - (a) comparacion pareada contra la distancia que MIROVA declara, y
(b) CONTROL NEGATIVO del TIF: el maximo dentro del inner distingue ALERTA de RUTINA?

(b) POR QUE. Si dentro de 5 km el crater fuera SIEMPRE la roca mas tibia -- por seco, por
albedo, por lo que sea -- entonces "el maximo del TIF cae en el crater" no dice nada sobre
donde puso MIROVA su cumulo: diria solo que el crater es el punto mas caliente del edificio,
con o sin anomalia. La unica forma de saberlo es medir lo mismo en pasadas donde MIROVA
declara RUTINA (sin alerta termica). Si da igual, el instrumento no separa clases y su
"acierto" del control es vacuo.
Read-only."""
import datetime as dt, json, os, statistics as st, importlib.util
import numpy as np
import f2_lib as F
F.utf8()
_d = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(_d, "resultados.json"), encoding="utf-8"))["filas"]

print("=== (a) PAREADO: nuestro cumulo vs la Distancia_km que MIROVA DECLARA, misma pasada ===")
print("Es la via exogena que no depende del TIF: es el auto-reporte de MIROVA.")
print("%-21s %4s | %-11s %-13s | %-11s | %s" % (
    "volcan","n","nuestro_med","MIROVA_decl","delta_med","nuestro mas cerca"))
G = []
for v in sorted(set(r["volcan"] for r in R)):
    p = [r for r in R if r["volcan"] == v
         and r.get("d_crater_nuestro_km") is not None and r.get("dist_km_mirova") is not None]
    if not p: continue
    n = [r["d_crater_nuestro_km"] for r in p]; m = [r["dist_km_mirova"] for r in p]
    d = [b-a for a, b in zip(n, m)]
    G += d
    print("%-21s %4d | %-11.2f %-13.2f | %+-11.2f | %.0f%%" % (
        v, len(p), st.median(n), st.median(m), st.median(d),
        100*sum(1 for x in d if x > 0)/len(d)))
print("%-21s %4d | %-11s %-13s | %+-11.2f | %.0f%%" % (
    "GLOBAL", len(G), "", "", st.median(G), 100*sum(1 for x in G if x > 0)/len(G)))
print("  delta>0 = MIROVA declara su punto MAS LEJOS del crater que nuestro cumulo")

print("\n=== (b) CONTROL NEGATIVO del TIF: ALERTA vs RUTINA (Lascar y PlanchonPeteroa) ===")
_s = importlib.util.spec_from_file_location("emp", os.path.join(_d, "02_emparejar.py"))
emp = importlib.util.module_from_spec(_s); _s.loader.exec_module(emp)
cat = F.catalogo()
D0 = dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc)

def dmax(tifpath, vla, vlo, inner):
    a, lat, lon, _ = F.leer_tif(tifpath)
    dg = F.grilla_dist_km(lat, lon, vla, vlo)
    f = np.where((dg <= inner) & np.isfinite(a), a, -np.inf)
    if not np.isfinite(f).any(): return None
    i, j = np.unravel_index(int(np.argmax(f)), f.shape)
    return F.haversine(vla, vlo, float(lat[i, j]), float(lon[i, j]))

for VOL in ("Lascar", "PlanchonPeteroa"):
    c = cat[VOL]; vla, vlo = c["vent_lat"], c["vent_lon"]; inner = float(c["inner_radius_km"])
    con = set(r["pasada_utc"] for r in R if r["volcan"] == VOL)
    ix = [x for x in F.indice() if x["vol"] == VOL and x["sensor"] == "VIIRS375" and x["ts"] >= D0]
    # RUTINA = pasada con TIF pero SIN alerta MIROVA emparejada a <=120 s
    ts_al = [a["_ts"] for a in F.alertas(VOL) if a["sensor_bucket"] == "VIIRS375" and a["_ts"] >= D0]
    rut = [x for x in ix
           if not any(abs((x["ts"]-t).total_seconds()) <= 120 for t in ts_al)]
    rut = sorted(rut, key=lambda x: x["ts"], reverse=True)[:25]
    ds = []
    for x in rut:
        try:
            d = dmax(x["tif_path"], vla, vlo, inner)
            if d is not None: ds.append(d)
        except Exception:
            pass
    al = [r["d_max_tif_km"] for r in R if r["volcan"] == VOL and r.get("d_max_tif_km") is not None]
    print("\n  %s (inner=%.0f km)" % (VOL, inner))
    print("    ALERTA : n=%3d  d_max_TIF mediana=%.2f km  <1km=%.0f%%" % (
        len(al), st.median(al), 100*sum(1 for x in al if x < 1)/len(al)))
    if ds:
        print("    RUTINA : n=%3d  d_max_TIF mediana=%.2f km  <1km=%.0f%%" % (
            len(ds), st.median(ds), 100*sum(1 for x in ds if x < 1)/len(ds)))
        print("    -> el TIF %s separa ALERTA de RUTINA" %
              ("SI" if abs(st.median(ds)-st.median(al)) > 0.5 else "NO"))
    else:
        print("    RUTINA : SIN DATO (no hay pasadas con TIF sin alerta en la ventana)")
