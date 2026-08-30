# -*- coding: utf-8 -*-
"""S126 — D13: clasificar los records que la cerca del frontend apaga.

D13 quedo ABIERTA (documental) en S124 con una consigna explicita, que es lo que este
script cumple:

    "Anti-A8: no reabrir como 'hay que levantar la cerca' sin antes clasificar por
     categoria A54 los records que se destaparian. Y ojo con A72: si lo que se destapa
     es artefacto, la raiz es no generarlo en la deteccion, no la cerca."

Las 3 vistas del frontend ponen la magnitud en cero cuando `distance_class != "summit"`.
S124 midio el ALCANCE (31 % de los records, 17.678 MW) pero no el CONTENIDO.

Lo que hace posible clasificarlo ahora es el hallazgo de S126: existe una firma espacial
del artefacto topografico — el cluster cae en el anillo [1,5-3] km, que es donde el fondo
autorreferente lo fabrica. Con eso se puede separar lo que la cerca apaga en:

  · cluster EN EL ANILLO      -> mismo artefacto que ya documentamos;
  · cluster A MENOS DE 1 km   -> candidato a senal real (cat-b de A54);
  · corroborado por MIROVA    -> senal, sin ambiguedad.

DATO QUE REENCUADRA TODO (S126): el artefacto TAMBIEN pasa la cerca cuando queda
etiquetado `summit`. Villarrica publica 380 detecciones con el 92 % del cluster a mas de
1,5 km, todas en rojo, porque 2,8 km < inner_radius 5. O sea que la cerca **no** protege
del artefacto: es ortogonal al problema.

Persiste en 01_que_apaga_la_cerca.json.
"""
import io
import json
import os
import statistics as st
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _s126_lib import ROOT, VENTS, bucket, cargar_mirova, haversine, resumen   # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

VENTANA = ("2026-05-01", "2026-08-28")
ANILLO = (1.5, 3.0)
CERCA_KM = 1.0

mir, _ = cargar_mirova(VENTANA)
res = {"ventana": list(VENTANA), "anillo_km": list(ANILLO), "por_volcan": {},
       "total": {}}
tot = defaultdict(int)

print("D13 — QUE APAGA LA CERCA `distance_class != summit`")
print("ventana %s a %s, los 3 sensores\n" % VENTANA)
print("%-20s %7s %7s %8s %13s %14s %11s %11s %10s" %
      ("volcan", "total", "far", "% far", "cluster d_med", "final_hs d_med",
       "% anillo", "% <1km", "en MIROVA"))

for vol, vent in VENTS.items():
    p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    if not os.path.exists(p):
        continue
    n = 0
    d_cl, d_hs, vrps = [], [], []
    en_anillo = cerca = en_mir = 0
    noches_mir = set(mir.get(vol) or {})
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        b = bucket(r.get("sensor"))
        f = r["datetime_utc"][:10]
        if b is None or not (VENTANA[0] <= f <= VENTANA[1]):
            continue
        pc = r.get("primary_cluster") or {}
        if not pc.get("vrp_mw"):
            continue
        n += 1
        if r.get("distance_class") == "summit":
            continue                       # la cerca NO lo apaga
        if pc.get("centroid_lat") is None:
            continue
        d = haversine((pc["centroid_lat"], pc["centroid_lon"]), vent)
        d_cl.append(d)
        vrps.append(pc["vrp_mw"])
        if ANILLO[0] <= d <= ANILLO[1]:
            en_anillo += 1
        if d < CERCA_KM:
            cerca += 1
        if r.get("final_hotspot_dist_km") is not None:
            d_hs.append(r["final_hotspot_dist_km"])
        if (f, b) in noches_mir:
            en_mir += 1

    if len(d_cl) < 20:
        continue
    d = {"records_con_vrp": n, "apagados": len(d_cl),
         "pct_apagados": round(100 * len(d_cl) / n, 1),
         "cluster_dist_km": resumen(d_cl),
         "final_hotspot_dist_km": resumen(d_hs) if d_hs else None,
         "pct_cluster_en_anillo": round(100 * en_anillo / len(d_cl), 1),
         "pct_cluster_bajo_1km": round(100 * cerca / len(d_cl), 1),
         "corroborados_por_mirova": en_mir,
         "vrp_mediana": resumen(vrps)["mediana"]}
    res["por_volcan"][vol] = d
    for k, v in (("n", n), ("apag", len(d_cl)), ("anillo", en_anillo),
                 ("cerca", cerca), ("mir", en_mir)):
        tot[k] += v
    print("%-20s %7d %7d %7.0f%% %13.2f %14.2f %10.0f%% %10.0f%% %10d"
          % (vol, n, len(d_cl), d["pct_apagados"], d["cluster_dist_km"]["mediana"],
             d["final_hotspot_dist_km"]["mediana"] if d_hs else -1,
             d["pct_cluster_en_anillo"], d["pct_cluster_bajo_1km"], en_mir))

res["total"] = {
    "records_con_vrp": tot["n"], "apagados": tot["apag"],
    "pct_apagados": round(100 * tot["apag"] / tot["n"], 1),
    "pct_en_anillo": round(100 * tot["anillo"] / tot["apag"], 1),
    "pct_bajo_1km": round(100 * tot["cerca"] / tot["apag"], 1),
    "corroborados_por_mirova": tot["mir"],
    "pct_corroborados": round(100 * tot["mir"] / tot["apag"], 1)}

t = res["total"]
print("\n" + "=" * 100)
print("CLASIFICACION DE LOS %d RECORDS APAGADOS (%.0f %% de los %d con VRP)"
      % (t["apagados"], t["pct_apagados"], t["records_con_vrp"]))
print("  cluster en el anillo 1,5-3 km  : %5.1f %%   <- misma firma que el artefacto documentado"
      % t["pct_en_anillo"])
print("  cluster a menos de 1 km        : %5.1f %%   <- candidato a senal real (cat-b, A54)"
      % t["pct_bajo_1km"])
print("  corroborados por MIROVA        : %5d      (%.1f %%)"
      % (t["corroborados_por_mirova"], t["pct_corroborados"]))
print("\n  El `final_hotspot` de estos records esta a ~19-24 km: un salar, un lago o un")
print("  incendio le roba el maximo de escena y arrastra la etiqueta, mientras el cluster")
print("  sigue crateriano. Es la asimetria A46/A81, no una deteccion lejana de verdad.")

dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), "01_que_apaga_la_cerca.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
