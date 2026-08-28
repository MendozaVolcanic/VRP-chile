# -*- coding: utf-8 -*-
"""S124 — Mapa: DONDE estan los clusters que la replica llama "cumbre".

Responde la pregunta de Nicolas (2026-08-25): "como es posible que replica
MIROVA tenga mas datos que el experimental? o lo que muestra mirova replica
estan en sectores mas alejados?"

(Los numeros del docstring original quedaron obsoletos tras varios cambios de
radio y filtros; los vigentes son los que imprime la leyenda al generar. La
replica acepta como "cumbre" el inner de 5 km del KML MIROVA; el experimental
solo cuenta el crater. Este mapa lo muestra sobre la grilla real de MIROVA.)
"""
import json, io, math, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

sys.path.insert(0, str(Path(__file__).parent))
from basemap import satelital_km, ATRIBUCION

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
NIC = (-36.867210, -71.378241)
# Radio del foco: 500 m (pedido de Nicolás, S124). A 375 m de píxel VIIRS I,
# 500 m son ~1,3 píxeles: es el círculo más ajustado que el sensor soporta sin
# volverse un solo píxel. Medido antes de aplicarlo: bajar de 1 km a 500 m
# cuesta 1 noche de la réplica y 0 del experimental, y las 3 alertas de MIROVA
# que reproducimos sobreviven las 3 — las detecciones están en el cráter, no
# desparramadas.
FOCO_KM = 0.5

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
    if (pc.get("centroid_dist_km") or 0) > 5.0: continue   # el resto se cuenta en el panel B
    rep.append((pc["centroid_lat"], pc["centroid_lon"], v))

# AUDIT S125 — la leyenda comparaba 139 (radio 5 km) contra 29 (radio 500 m):
# radios distintos, numeros no comparables. El par comparable es DENTRO del foco.
rep_foco = [t for t in rep if hav(NIC[0], NIC[1], t[0], t[1]) <= FOCO_KM]

# experimental: clusters en el foco
foc = []
_foc_noches = set()   # AUDIT S125: n=29 son CLUSTERS; las noches son menos
dd = json.loads(FOCO_JSON.read_text(encoding="utf-8"))
for r in dd["records"]:
    # AUDIT S124 (subagente, hallazgo 2): el experimental arranca en mayo pero el
    # titulo dice "desde junio" — sin este filtro, 7 de 30 verdes eran de MAYO y
    # la densidad visual quedaba sesgada a favor del experimental.
    if (r.get("datetime_utc") or "")[:10] < "2026-06-01":
        continue
    pc = r.get("primary_cluster") or {}
    v = pc.get("vrp_mw") or 0
    if v > 0 and pc.get("centroid_lat") is not None and hav(NIC[0], NIC[1], pc["centroid_lat"], pc["centroid_lon"]) <= FOCO_KM:
        foc.append((pc["centroid_lat"], pc["centroid_lon"], v))
        _foc_noches.add((r.get("datetime_utc") or "")[:10])

fig, ax = plt.subplots(figsize=(9.5, 9.5))
ax.set_title("¿Dónde detecta cada uno? — clusters VIIRS 375 m desde junio\n"
             "(coordenadas en km respecto del cráter Nicanor)", fontsize=12, fontweight="bold")

# Fondo satelital: sin él no se puede juzgar si una anomalía cae sobre el
# cráter, sobre el glaciar o sobre el valle. zorder bajo = debajo de todo.
LIM = 0.8          # pedido de Nicolás: mostrar solo el entorno del cráter
_img, _ext = satelital_km(NIC[0], NIC[1], LIM, zoom=17)   # ventana de 800 m: máximo detalle
if _img is not None:
    ax.imshow(_img, extent=_ext, origin="upper", zorder=0, interpolation="bilinear")
    # velo tenue: la imagen es oscura y contrastada; sin esto los puntos y los
    # círculos se pierden encima del terreno.
    ax.add_patch(plt.Rectangle((-LIM * 2, -LIM * 2), LIM * 4, LIM * 4,
                               fc="white", alpha=0.22, zorder=1, ec="none"))

# circulos de referencia
for rkm, col, lab in ((FOCO_KM, "#1a7a33", f"radio experimental ({FOCO_KM*1000:.0f} m)"),):
    c = plt.Circle((0, 0), rkm, fill=False, color=col, lw=2.4,
                   ls="--", label=lab, zorder=2,
                   path_effects=[pe.withStroke(linewidth=4.2, foreground="white")])
    ax.add_patch(c)

xs, ys, vs = zip(*[(*km_xy(la, lo), v) for la, lo, v in rep])
ax.scatter(xs, ys, s=[22+180*v for v in vs], c="#88a8c8", alpha=0.9,
           edgecolors="#1f4e79", lw=0.8, zorder=5,
           label=f"réplica: cluster «summit» — {len(rep_foco)} dentro del foco de {FOCO_KM*1000:.0f} m "
                 f"(de {len(rep)} en un radio de 5 km)")
if foc:
    xs, ys, vs = zip(*[(*km_xy(la, lo), v) for la, lo, v in foc])
    ax.scatter(xs, ys, s=[60+320*v for v in vs], c="#2ca02c", marker="s", alpha=0.75,
               edgecolors="#14501f", lw=0.6, zorder=4,
               label=f"experimental: {len(foc)} clusters dentro del foco de {FOCO_KM*1000:.0f} m "
                 f"en {len(_foc_noches)} noches")
ax.plot(0, 0, "^", ms=16, c="#cc3311", mec="k", zorder=5, label="cráter Nicanor")

# ── MIROVA: lo que su Distancia_km REALMENTE dice ───────────────────────────
# AUDITORIA S124 (Nicolás preguntó "¿respecto a qué punto mide?" y la respuesta
# no era la que yo asumía). Su `Distancia_km` NO es una distancia continua a un
# punto: está CUANTIZADA a celdas de su grilla resampleada. Verificado sobre el
# consolidado completo — cada valor publicado es sqrt(i²+j²)·celda con i,j
# enteros: 10.085/10.085 registros MODIS con celda 1 km (los valores son
# 0, 1, √2, 2, √5, √10, √13, √41, √61, √65, √82, √90, √113…) y 11.810/11.810
# VIIRS375 con celda 0,375 km sobre 450 valores distintos.
#
# ── La grilla REAL de MIROVA (de sus propios GeoTIFF) ───────────────────────
# S124: los TIF del archivo (../mirova-tif-archive) estan georreferenciados.
# De 20260520_044801_VIIRS375.tif: grilla 134x134 (confirma F70.2b), celdas
# ~382x381 m, origen y extent FIJOS entre pasadas. Centro de la grilla:
# (-36.863270, -71.378535) = a 140 m del GVP y 439 m al NORTE del crater
# Nicanor. O sea: la grilla NO esta centrada en el crater activo — la sospecha
# de Nicolas ("¿justo la celda cae simetrica sobre el crater?") era correcta.
#
# CAVEAT honesto: el TIF esta en EPSG:4326 (reproyeccion de visualizacion de su
# grilla UTM), asi que estos bordes de celda aproximan los UTM reales a menos
# de media celda. Se probo inferir la celda de referencia del Distancia_km
# contra las 4 alertas al crater y NO cerro (0/4 con las dos candidatas): la
# cuantizacion vive en la grilla UTM, no en esta reproyeccion. Por eso se
# dibujan las lineas como "grilla publicada (reproyectada)" sin marcar celda
# de referencia.
LEFT, TOP, DXX, DYY = -71.665032, -36.633069, 0.004276, 0.003436
import numpy as _np
_kx = 111.32 * math.cos(math.radians(NIC[0]))
for k in range(134 + 1):
    x = (LEFT + k * DXX - NIC[1]) * _kx
    if -LIM <= x <= LIM:
        ax.axvline(x, color="#cc3311", lw=0.7, ls="-", alpha=0.45, zorder=2)
    y = (TOP - k * DYY - NIC[0]) * 111.32
    if -LIM <= y <= LIM:
        ax.axhline(y, color="#cc3311", lw=0.7, ls="-", alpha=0.45, zorder=2)
_cgx = (-71.378535 - NIC[1]) * _kx
_cgy = (-36.863270 - NIC[0]) * 111.32
ax.plot(_cgx, _cgy, "*", ms=15, c="#cc3311", mec="white", mew=0.9, zorder=6,
        label=("centro de la grilla de MIROVA: cae sobre la coordenada de\n"
               "catálogo del complejo (a 140 m), no sobre el cráter (a 439 m)"))
ax.plot([], [], color="#cc3311", lw=0.9, alpha=0.6,
        label="grilla MIROVA publicada (reproyectada; celdas ~375 m)")

ax.set_xlabel("km al Este del cráter")
ax.set_ylabel("km al Norte del cráter")
ax.set_xlim(-LIM, LIM); ax.set_ylim(-LIM, LIM)
ax.set_aspect("equal")
ax.grid(True, alpha=0.18, color="white", lw=0.6)

# Barra de escala (feedback Nicolas): el eje ya esta en km, pero una barra
# permite estimar distancias sin leer los ticks.
_sb = 0.25   # km
_x0, _y0 = LIM - _sb - 0.10, -LIM + 0.10
ax.plot([_x0, _x0 + _sb], [_y0, _y0], "-", color="white", lw=4.5, solid_capstyle="butt", zorder=9)
ax.plot([_x0, _x0 + _sb], [_y0, _y0], "-", color="black", lw=2.0, solid_capstyle="butt", zorder=10)
ax.text(_x0 + _sb / 2, _y0 + 0.035, f"{_sb*1000:.0f} m", ha="center", va="bottom",
        fontsize=8.5, color="black", zorder=10,
        bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none", alpha=0.8))
# FEEDBACK NICOLAS (S125): los iconos se superponian. Mas interlineado,
# handles mas separados y la leyenda ANCLADA DEBAJO del eje, no encima.
ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.085), fontsize=8.2,
          framealpha=0.95, labelspacing=0.85, handlelength=2.4,
          handletextpad=0.9, borderpad=0.7, ncol=1)
ax.text(0.98, 0.98,
        "MIROVA publicó además 3 alertas FUERA de esta ventana:\n"
        "15-jul 0.02 MW @ 2.86 km  ·  26-ago 0.02 MW @ 3.02 km\n"
        "12-jun 0.32 MW @ 4.14 km (18:18 UTC, DIURNA — artefacto solar A76)",
        transform=ax.transAxes, ha="right", va="top", fontsize=8, color="#8a1f0e",
        bbox=dict(boxstyle="round,pad=0.35", fc="#fff6f4", ec="#cc8877", alpha=0.95),
        zorder=8)
ax.text(0.02, 0.02, "El tamaño del punto crece con el VRP.",
        transform=ax.transAxes, va="bottom", fontsize=8.5, color="#444",
        bbox=dict(boxstyle="round,pad=0.35", fc="#f7f7f7", ec="#bbb"))
ax.text(0.995, 0.005, ATRIBUCION, transform=ax.transAxes, ha="right", va="bottom",
        fontsize=7.5, color="white", zorder=6,
        path_effects=[pe.withStroke(linewidth=2.2, foreground="#00000088")])
fig.tight_layout()
out = Path(__file__).parent / "ndc_mapa_s124.png"
fig.savefig(out, dpi=150)
print("figura:", out)
