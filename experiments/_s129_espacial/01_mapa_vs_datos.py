# -*- coding: utf-8 -*-
"""S129 — auditoría ESPACIAL de los 11 mapas del dashboard operativo.

Nicolás miró los mapas y marcó tres cosas. La regla A62 dice que la insistencia del
experto de dominio es señal, no ruido, así que esto las mide en vez de opinar:

  1. «En Planchón-Peteroa veo pocos puntos, como si todos estuvieran agrupados en el
     mismo lugar.»
  2. «En Cordón Caulle nuestra manera de ver MODIS dispara detecciones en el lacolito
     y MIROVA no lo reporta.»
  3. «En ese mismo volcán hay una cantidad de puntos fuera del volcán, en zonas de
     bosque.»

QUÉ COORDENADA MIRA. El mapa dibuja `final_hotspot_lat/lon` con fallback a
`hotspot_lat` y `vent_hotspot_lat` (`frontend/index.html:2220-2221`). Ese es el punto
que Nicolás ve, así que es el que hay que auditar — NO el `primary_cluster.centroid`,
que es de donde sale la magnitud. La regla A46 del proyecto avisa justamente que esas
dos representaciones pueden discrepar.

MÉTRICAS, por volcán y por sensor:
  · dispersión real de los puntos dibujados (cuántas posiciones DISTINTAS hay);
  · distancia al cráter: mediana y percentiles, más el rumbo (A70: la mediana del
    offset direccional, no la media de la distancia, que los outliers deforman);
  · cuántos caen fuera del `inner_radius_km` del volcán;
  · para MODIS: cuántos tienen contraparte en el ground truth de MIROVA.

Read-only.
"""
import collections
import io
import json
import math
import os
import statistics as st
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import VENTS, bucket, cargar_mirova              # noqa: E402

import yaml                                                     # noqa: E402

VENTANA = ("2026-01-01", "2026-12-31")
cfg = {v["name"]: v for v in yaml.safe_load(
    open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
mir, _ = cargar_mirova(VENTANA)


def dkm(la, lo, vla, vlo):
    return 111.32 * math.hypot(la - vla, (lo - vlo) * math.cos(math.radians(vla)))


def rumbo(la, lo, vla, vlo):
    """Rumbo cardinal desde el cráter hacia el punto."""
    dy = la - vla
    dx = (lo - vlo) * math.cos(math.radians(vla))
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return "="
    a = (math.degrees(math.atan2(dx, dy)) + 360) % 360
    return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int((a + 22.5) % 360 // 45)]


R = {}
for vol in sorted(VENTS):
    p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    if not os.path.exists(p):
        continue
    vla, vlo = VENTS[vol]
    c = cfg.get(vol, {})
    inner = c.get("inner_radius_km")
    por_sensor = collections.defaultdict(list)
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        d = r.get("datetime_utc", "")[:10]
        if not (VENTANA[0] <= d <= VENTANA[1]):
            continue
        b = bucket(r.get("sensor"))
        if b is None:
            continue
        # Exactamente lo que dibuja el mapa (index.html:2220-2221).
        la = r.get("final_hotspot_lat") or r.get("hotspot_lat") or r.get("vent_hotspot_lat")
        lo = r.get("final_hotspot_lon") or r.get("hotspot_lon") or r.get("vent_hotspot_lon")
        v = (r.get("primary_cluster") or {}).get("vrp_mw") or 0.0
        if la is None or lo is None or v <= 0:
            continue
        por_sensor[b].append({"fecha": d, "lat": la, "lon": lo, "vrp": v,
                              "dist": dkm(la, lo, vla, vlo),
                              "rumbo": rumbo(la, lo, vla, vlo)})

    fila = {"inner_radius_km": inner, "por_sensor": {}}
    for b, pts in sorted(por_sensor.items()):
        ds = sorted(p_["dist"] for p_ in pts)
        # ¿Cuántas posiciones DISTINTAS dibuja el mapa? Redondeo a ~11 m.
        distintas = len({(round(p_["lat"], 4), round(p_["lon"], 4)) for p_ in pts})
        rum = collections.Counter(p_["rumbo"] for p_ in pts)
        fuera = sum(1 for x in ds if inner and x > inner)
        # Contraparte de MIROVA para ese sensor.
        noches = {p_["fecha"] for p_ in pts}
        con_gt = sum(1 for f in noches if (mir.get(vol) or {}).get((f, b)))
        fila["por_sensor"][b] = {
            "n_puntos": len(pts), "posiciones_distintas": distintas,
            "pct_posiciones_distintas": round(100.0 * distintas / len(pts), 1),
            "dist_km": {"p10": round(ds[len(ds) // 10], 2),
                        "mediana": round(st.median(ds), 2),
                        "p90": round(ds[9 * len(ds) // 10], 2),
                        "max": round(ds[-1], 2)},
            "rumbo_dominante": rum.most_common(2),
            "fuera_del_inner": fuera,
            "pct_fuera_del_inner": round(100.0 * fuera / len(pts), 1),
            "noches": len(noches), "noches_con_gt_mirova": con_gt,
            "pct_noches_confirmadas": round(100.0 * con_gt / len(noches), 1) if noches else 0,
        }
    R[vol] = fila

out = os.path.join(AQUI, "01_mapa_vs_datos.json")
os.makedirs(AQUI, exist_ok=True)
json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

print("AUDITORÍA ESPACIAL — lo que el mapa dibuja (final_hotspot), por volcán y sensor\n")
print("%-20s %-7s %6s %7s %8s %8s %8s %8s %7s %7s"
      % ("volcán", "sensor", "pts", "posic.", "%dist", "med_km", "p90_km",
         "%fuera", "rumbo", "%conf"))
for vol, f in R.items():
    for b, s in f["por_sensor"].items():
        print("%-20s %-7s %6d %7d %7.1f%% %8.2f %8.2f %7.1f%% %7s %6.1f%%"
              % (vol, b, s["n_puntos"], s["posiciones_distintas"],
                 s["pct_posiciones_distintas"], s["dist_km"]["mediana"],
                 s["dist_km"]["p90"], s["pct_fuera_del_inner"],
                 s["rumbo_dominante"][0][0] if s["rumbo_dominante"] else "-",
                 s["pct_noches_confirmadas"]))
    print("%-20s inner_radius_km = %s" % ("", f["inner_radius_km"]))
print("\nescrito:", out)
