# -*- coding: utf-8 -*-
"""S194: un mapa por volcán con las áreas del laboratorio y los alertados nocturnos de la vía desde 2025-02-15,
coloreados por el área que les tocó. Tres paneles: MODIS, VIIRS 375 y VIIRS 750.

Coordenadas en km desde el cráter (x este, y norte; proyección local equirectangular). Los círculos se dibujan desde
vent_lat/vent_lon de volcanoes.yaml; la asignación al cráter y al flanco usa dist_km de la vía, medida en la grilla
desde la posición del cráter, así que un punto pegado al círculo puede verse del otro lado por menos de media celda.

Uso: python experiments/_s194_areas/mapas.py [--salida DIR]   (lee pixeles.csv.gz de particion.py; escribe mapas/)
"""
import argparse
import collections
import csv
import gzip
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import Circle, Polygon as MplPolygon  # noqa: E402

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
import particion as P  # noqa: E402

COLORES = {"crater": "#d62728", "agua": "#1f77b4", "flanco": "#ff7f0e", "resto": "#7f3fbf"}
NOMBRES = {"crater": "cráter", "agua": "agua", "flanco": "flanco", "resto": "resto"}
FAMS = [("MODIS", "MODIS (1 km)"), ("VIIRS375", "VIIRS 375 m"), ("VIIRS750", "VIIRS 750 m")]


def _dibujar_lagos(ax, areas):
    for g in areas.lagos:
        ax.add_patch(MplPolygon(g.anillos[0], closed=True, facecolor="#cfe8fb", edgecolor="#5aa0d8", lw=0.4, zorder=1))
        for h in g.anillos[1:]:   # islas
            ax.add_patch(MplPolygon(h, closed=True, facecolor="white", edgecolor="#5aa0d8", lw=0.3, zorder=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default="D:/vrp-trabajo/temporales/s194_areas")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    conf = yaml.safe_load((RAIZ / "config" / "areas_laboratorio.yaml").read_text(encoding="utf-8"))
    vy = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    pix = collections.defaultdict(list)
    with gzip.open(Path(args.salida) / "pixeles.csv.gz", "rt", encoding="utf-8") as f:
        for q in csv.DictReader(f):
            pix[(q["volcan"], q["familia"])].append(q)
    dst = AQUI / "mapas"
    dst.mkdir(exist_ok=True)
    for volcan in conf["volcanes"]:
        areas = P.Areas(volcan, RAIZ, conf, vy[volcan])
        fig, axs = plt.subplots(1, 3, figsize=(16.5, 6.2), constrained_layout=True)
        for ax, (fam, titulo) in zip(axs, FAMS):
            _dibujar_lagos(ax, areas)
            ax.add_patch(Circle((0, 0), areas.flanco_km, fill=False, ls="--", lw=1.0, ec="#ff7f0e", zorder=2))
            ax.add_patch(Circle((0, 0), areas.inner_km, fill=False, lw=1.2, ec="#d62728", zorder=2))
            qs = pix.get((volcan, fam), [])
            cuenta = collections.Counter(q["area"] for q in qs)
            for a in ("resto", "flanco", "agua", "crater"):
                sel = [q for q in qs if q["area"] == a]
                if not sel:
                    continue
                xy = [areas.a_km(float(q["lat"]), float(q["lon"])) for q in sel]
                ax.scatter([p[0] for p in xy], [p[1] for p in xy], s=7, c=COLORES[a], alpha=0.35, lw=0, zorder=3,
                           label=f"{NOMBRES[a]} ({cuenta[a]})")
            ax.plot(0, 0, marker="^", color="k", ms=6, zorder=4)
            ax.set_xlim(-30, 30)
            ax.set_ylim(-30, 30)
            ax.set_aspect("equal")
            ax.grid(alpha=0.25)
            ax.set_xlabel("km al este del cráter")
            ax.set_title(f"{titulo}: {len(qs)} alertados")
            if qs:
                ax.legend(loc="lower left", fontsize=8, framealpha=0.85, title="área (píxeles)", title_fontsize=8)
        axs[0].set_ylabel("km al norte del cráter")
        fig.suptitle(f"{vy[volcan].get('display_name', volcan)}: alertados nocturnos de la vía desde 2025-02-15 por área "
                     f"(cráter {areas.inner_km:g} km, flanco hasta {areas.flanco_km:g} km, agua JRC ≥ 50 %)",
                     fontsize=11)
        out = dst / f"{volcan}.png"
        fig.savefig(out, dpi=110)
        plt.close(fig)
        print(out)


if __name__ == "__main__":
    main()
