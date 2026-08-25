# -*- coding: utf-8 -*-
"""S124 — Mapa: DONDE estan los clusters que la replica llama "cumbre".

Responde la pregunta de Nicolas (2026-08-25): "como es posible que replica
MIROVA tenga mas datos que el experimental? o lo que muestra mirova replica
estan en sectores mas alejados?"

Respuesta medida: de las 47 noches "summit" de la replica (VIIRS375, desde
junio), solo 20 tienen su cluster mas cercano a <=1 km del crater Nicanor;
la mediana esta a 1.80 km y 22 noches caen a 2-5 km. La replica acepta como
"cumbre" todo lo que caiga dentro del inner de 5 km (KML MIROVA); el
experimental solo cuenta el crater. Este mapa lo muestra.
"""
import json, io, math, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
NIC = (-36.867210, -71.378241)
FOCO_JSON = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/experimental_ndc_focus/NevadosDeChillan.json"

def hav(la1, lo1, la2, lo2):
    p = math.pi / 180
    a = (math.sin((la2-la1)*p/2)**2 + math.cos(la1*p)*math.cos(la2*p)*math.sin((lo2-lo1)*p/2)**2)
    return 2*6371.0*math.asin(math.sqrt(a))

def km_xy(lat, lon):
    """coordenadas locales en km respecto del crater Nicanor (E+, N+)."""
    return ((lon-NIC[1])*111.32*math.cos(math.radians(NIC[0])), (lat-NIC[0])*111.32)

# replica: clusters summit VIIRS375 desde junio
rep = []
d = json.loads((ROOT/"data/mirova_equivalent/NevadosDeChillan.json").read_text(encoding="utf-8"))
for r in d["records"]:
    f = (r.get("datetime_utc") or "")[:10]
    s = r.get("sensor") or ""
    if f < "2026-06-01" or "VIIRS" not in s or "750" in s: continue
    pc = r.get("primary_cluster") or {}
    v = pc.get("vrp_mw") or 0
    if v <= 0 or r.get("distance_class") != "summit" or pc.get("centroid_lat") is None: continue
    if (pc.get("centroid_dist_km") or 0) > 5.0: continue
    rep.append((pc["centroid_lat"], pc["centroid_lon"], v))

# experimental: clusters en el foco
foc = []
dd = json.loads(FOCO_JSON.read_text(encoding="utf-8"))
for r in dd["records"]:
    pc = r.get("primary_cluster") or {}
    v = pc.get("vrp_mw") or 0
    if v > 0 and pc.get("centroid_lat") is not None and hav(NIC[0], NIC[1], pc["centroid_lat"], pc["centroid_lon"]) <= 1.0:
        foc.append((pc["centroid_lat"], pc["centroid_lon"], v))

fig, ax = plt.subplots(figsize=(9.5, 9.5))
ax.set_title("¿Dónde detecta cada uno? — clusters VIIRS 375 m desde junio\n"
             "(coordenadas en km respecto del cráter Nicanor)", fontsize=12, fontweight="bold")

# circulos de referencia
for rkm, col, lab in ((1.0, "#1a7a33", "radio experimental (1 km)"),
                      (5.0, "#4477aa", 'radio "cumbre" de la réplica (5 km, KML MIROVA)')):
    c = plt.Circle((0, 0), rkm, fill=False, color=col, lw=1.6,
                   ls="-" if rkm == 1 else "--", label=lab)
    ax.add_patch(c)

xs, ys, vs = zip(*[(*km_xy(la, lo), v) for la, lo, v in rep])
ax.scatter(xs, ys, s=[28+260*v for v in vs], c="#88a8c8", alpha=0.7,
           edgecolors="#4477aa", lw=0.5, zorder=3,
           label=f"réplica: cluster «summit» de cada pasada (n={len(rep)})")
if foc:
    xs, ys, vs = zip(*[(*km_xy(la, lo), v) for la, lo, v in foc])
    ax.scatter(xs, ys, s=[28+260*v for v in vs], c="#2ca02c", marker="s", alpha=0.85,
               edgecolors="#14501f", lw=0.6, zorder=4,
               label=f"experimental: foco al cráter (n={len(foc)})")
ax.plot(0, 0, "^", ms=16, c="#cc3311", mec="k", zorder=5, label="cráter Nicanor (coordenada de Nicolás)")

ax.set_xlabel("km al Este del cráter")
ax.set_ylabel("km al Norte del cráter")
ax.set_xlim(-5.6, 5.6); ax.set_ylim(-5.6, 5.6)
ax.set_aspect("equal")
ax.grid(True, alpha=0.25)
ax.legend(loc="lower left", fontsize=8.5, framealpha=0.95)
ax.text(0.02, 0.98, "El tamaño del punto crece con el VRP.\n"
        "Todo lo que cae dentro del círculo azul\nla réplica lo etiqueta «cumbre».",
        transform=ax.transAxes, va="top", fontsize=8.5, color="#444",
        bbox=dict(boxstyle="round,pad=0.35", fc="#f7f7f7", ec="#bbb"))
fig.tight_layout()
out = Path(__file__).parent / "ndc_mapa_s124.png"
fig.savefig(out, dpi=150)
print("figura:", out)
