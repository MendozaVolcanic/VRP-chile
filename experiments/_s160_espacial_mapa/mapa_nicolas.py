# -*- coding: utf-8 -*-
"""S160: mapa pedido por Nicolas. Dónde publicamos en noches limpias (negativos limpios) y dónde están las fuentes
persistentes, contra la caja y el anillo de MIROVA. Lee las tablas de la auditoría espacial (sin modificarlas).
Uso: python -I mapa_nicolas.py <carpeta_auditoria> <salida.png>"""
import csv, math, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

AUD, OUT = Path(sys.argv[1]), sys.argv[2]
V = {  # volcanoes.yaml (origin/main): vent, centro de la grilla de MIROVA, radio interno
    "PuyehueCordonCaulle": dict(vent=(-40.525499, -72.146137), ctr=(-40.5903, -72.1187), inner=20, nombre="Puyehue-Cordón Caulle"),
    "Tupungatito": dict(vent=(-33.389044, -69.826374), ctr=(-33.42694, -69.80039), inner=7, nombre="Tupungatito"),
    "Isluga": dict(vent=(-19.15, -68.83), ctr=(-19.15212, -68.83269), inner=5, nombre="Isluga"),
}
# Fuentes persistentes (celdas de 0,02 grados, ~2 km) que la auditoría señaló como no publicadas por ningún sistema
# (02d_fuentes_persistentes_salida.txt): conteo de TIF RUTINA (MIROVA miró y no alertó) con ese foco dominante.
FUENTES = {
    "PuyehueCordonCaulle": [((-40.52, -72.02), "10,7 km E del cráter\nfoco dominante en 15 de 161 TIF RUTINA")],
    "Tupungatito": [((-33.34, -69.84), "5,6 km N del cráter\n13 de 144 TIF RUTINA")],
    "Isluga": [((-19.10, -68.84), "5,7 km N del cráter\n7 de 95 TIF RUTINA (y 8 ALERTA)")],
}

def km(lat0, lon0, lat, lon):
    return ((lon - lon0) * 111.32 * math.cos(math.radians(lat0)), (lat - lat0) * 110.57)

filas = list(csv.DictReader(open(AUD / "03_pareo_geometria_pasadas.csv", encoding="utf-8")))
COL = {"VIIRS375": "#d62728", "VIIRS750": "#1f77b4", "MODIS": "#2ca02c"}
fig, axs = plt.subplots(1, 3, figsize=(19, 7))
for ax, (vol, g) in zip(axs, V.items()):
    c0 = g["ctr"]
    def xy(lat, lon): return km(c0[0], c0[1], lat, lon)
    ax.add_patch(Rectangle((-7.1, -7.9), 14.2, 15.8, fill=False, ls="--", lw=1.6, ec="orange",
                           label="anillo MIROVA 21 × 19 celdas (umbrales de escena)"))
    ax.add_patch(Rectangle((-2.6, -2.6), 5.2, 5.2, fill=False, lw=2, ec="gold", label="caja de cumbre MIROVA 7 × 7 (más sensible)"))
    vx, vy = xy(*g["vent"])
    ax.add_patch(Circle((vx, vy), g["inner"], fill=False, lw=1.5, ec="c", label="nuestro radio interno (%d km desde el cráter)" % g["inner"]))
    ax.add_patch(Circle((vx, vy), 2, fill=False, lw=1, ls=":", ec="gray", label="2 km del cráter"))
    n = {}
    for f in filas:
        if f["vol"] != vol or f["pub"] != "1" or not f["pc_lat"]:
            continue
        x, y = xy(float(f["pc_lat"]), float(f["pc_lon"]))
        if f["lab"] == "neg_limpio":
            n[f["b"]] = n.get(f["b"], 0) + 1
            ax.scatter(x, y, s=34, marker="^", color=COL.get(f["b"], "k"), edgecolor="k", lw=0.4, zorder=4)
        elif f["lab"] == "pos":
            ax.scatter(x, y, s=8, color="0.6", zorder=2)
    for s, cnum in COL.items():
        ax.scatter([], [], marker="^", color=cnum, edgecolor="k", label="publicamos, MIROVA no vio nada: %s (n = %d)" % (s, n.get(s, 0)))
    ax.scatter([], [], s=8, color="0.6", label="publicamos, con alerta de MIROVA")
    for (lat, lon), txt in FUENTES[vol]:
        x, y = xy(lat, lon)
        ax.add_patch(Rectangle((x - 1.1, y - 1.1), 2.2, 2.2, fill=True, alpha=0.25, fc="purple", ec="purple", zorder=1))
        ax.annotate("fuente persistente\n" + txt, (x, y), xytext=(x + 1.5, y + 2.5), fontsize=8, color="purple",
                    arrowprops=dict(arrowstyle="->", color="purple"))
    ax.scatter(vx, vy, marker="*", s=260, color="yellow", edgecolor="k", zorder=6, label="cráter (vent)")
    ax.scatter(0, 0, marker="D", s=70, color="orange", edgecolor="k", zorder=6, label="centro de la imagen de MIROVA")
    R = max(g["inner"] + 3, 12)
    ax.set_xlim(vx - R, vx + R); ax.set_ylim(vy - R, vy + R); ax.set_aspect("equal")
    ax.axhline(0, color="0.9", lw=0.5); ax.axvline(0, color="0.9", lw=0.5)
    ax.set_title(g["nombre"]); ax.set_xlabel("km al este del centro de MIROVA"); ax.set_ylabel("km al norte")
    ax.legend(loc="lower left", fontsize=6.5, framealpha=0.9)
fig.suptitle("S160, SIN VERIFICAR: dónde publicamos en noches en que MIROVA no vio nada, y focos recurrentes que nadie publica\n"
             "(nuestros cúmulos de producción, origin/main db0dfe847; tabla de MIROVA hasta 2026-10-14; fuentes de los TIF de MIROVA hasta 2026-09-21)", fontsize=10)
fig.tight_layout(); fig.savefig(OUT, dpi=130)
print("ok", OUT)
