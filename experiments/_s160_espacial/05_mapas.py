# -*- coding: utf-8 -*-
"""Mapas PNG por volcan: un TIF de MIROVA (VIIRS 375, EPSG:4326) de fondo, los focos calientes de MIROVA (maximo del
residuo del TIF en pasadas con ALERTA, 02b), los pixeles que marca el codigo de MIROVA en VIIRS 750 (O-sens del censo
S159, 02a), el centro del TIF, el crater (vent), nuestra coordenada lat/lon de volcanoes.yaml, nuestro radio interno,
la caja de cumbre (7 x 7 de 750 m) y el anillo (21 x 19) de MIROVA centrados en el centro del TIF, y los centroides de
nuestros cumulos en las mismas pasadas (03). Solo lectura; escribe mapa_<Volcan>.png en esta carpeta.
Fondo: el TIF de la pasada con ALERTA de mayor prominencia en 02b (se imprime cual).
"""
from __future__ import annotations

import csv
import glob
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import rasterio  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402
from scipy.ndimage import median_filter  # noqa: E402

import comun as C  # noqa: E402

PAT = ["../mirova-tif-archive/data/tif/{v}/*VIIRS375*.tif", "experiments/_s147_tif/tif/{v}/*.tif",
       "experiments/_s144_conteo_tif/_dl_tif/*/data/tif/{v}/*.tif",
       "experiments/_s139_audit/distancia_tif/_dl_/data/tif/{v}/*VIIRS375*.tif", "experiments/_s142_ndc/_dl_tif/{v}/*.tif"]


def km_a_grados(lat0, dn_km, de_km):
    return dn_km / 111.195, de_km / (111.195 * math.cos(math.radians(lat0)))


def main():
    focos = [r for r in csv.DictReader(open(C.AQUI / "02b_tif_v375_focos.csv", encoding="utf-8"))]
    ora = [r for r in csv.DictReader(open(C.AQUI / "02a_oraculo_v750_pixeles.csv", encoding="utf-8"))]
    pas = [r for r in csv.DictReader(open(C.AQUI / "03_pareo_geometria_pasadas.csv", encoding="utf-8"))]
    for v in C.VOLS:
        g = C.GEO[v]
        tc, vent = g["tif_centro"], g["vent"]
        fv = [r for r in focos if r["vol"] == v]
        al = [r for r in fv if r["mir_tipo"].startswith("ALERTA")]
        fondo = max(al, key=lambda r: float(r["res_sigma"])) if al else None
        path = None
        if fondo:
            for pt in PAT:
                for f in glob.glob(str(C.ROOT / pt.format(v=v))):
                    if os.path.basename(f).replace("_lm", "") == fondo["base"]:
                        path = f
                        break
                if path:
                    break
        fig, axes = plt.subplots(1, 2, figsize=(17, 8.2))
        for ax, zoom in zip(axes, (False, True)):
            if path:
                with rasterio.open(path) as ds:
                    A = ds.read(1).astype(float)
                    b = ds.bounds
                A[A <= 0] = np.nan
                fill = np.where(np.isnan(A), np.nanmedian(A), A)
                res = fill - median_filter(fill, size=9, mode="nearest")
                campo = res if zoom else A
                vmin, vmax = np.nanpercentile(campo, [2, 99.5])
                ax.imshow(campo, extent=(b.left, b.right, b.bottom, b.top), cmap="inferno", vmin=vmin, vmax=vmax, origin="upper", alpha=0.85)
            # geometria de MIROVA alrededor del centro del TIF
            dlat, dlon = km_a_grados(tc[0], C.CAJA_KM, C.CAJA_KM)
            ax.add_patch(Rectangle((tc[1] - dlon, tc[0] - dlat), 2 * dlon, 2 * dlat, fill=False, ec="yellow", lw=1.8, label="caja de cumbre MIROVA 7x7 (±2,6 km)"))
            dlat, dlon = km_a_grados(tc[0], C.ANILLO_KM, 9.5 * 0.75)
            ax.add_patch(Rectangle((tc[1] - dlon, tc[0] - dlat), 2 * dlon, 2 * dlat, fill=False, ec="orange", lw=1.8, ls="--", label="anillo MIROVA 21x19 (±7,9 / ±7,1 km)"))
            # nuestro radio interno alrededor del vent (circulo en grados, aproximado con elipse de ejes iguales en km)
            dlat, dlon = km_a_grados(vent[0], g["inner_km"], g["inner_km"])
            th = np.linspace(0, 2 * np.pi, 200)
            ax.plot(vent[1] + dlon * np.cos(th), vent[0] + dlat * np.sin(th), color="cyan", lw=1.8, label=f"nuestro inner_radius {g['inner_km']:g} km (desde el vent)")
            # focos de MIROVA (TIF) en ALERTA
            fuertes = [r for r in al if float(r["res_sigma"]) >= 5]
            debiles = [r for r in al if float(r["res_sigma"]) < 5]
            if fuertes:
                ax.scatter([float(r["lon"]) for r in fuertes], [float(r["lat"]) for r in fuertes], s=28, c="red", marker="o", ec="white", lw=0.4, label=f"foco TIF V375 en ALERTA, >=5 sigma (n={len(fuertes)})", zorder=5)
            if debiles:
                ax.scatter([float(r["lon"]) for r in debiles], [float(r["lat"]) for r in debiles], s=16, c="lightgray", marker="o", ec="k", lw=0.3, label=f"foco TIF V375 en ALERTA, <5 sigma (n={len(debiles)})", zorder=4)
            # pixeles del codigo de MIROVA V750 (O-sens)
            op = [r for r in ora if r["volcan"] == v and r["lab"] == "pos"]
            on = [r for r in ora if r["volcan"] == v and r["lab"] == "neg_limpio"]
            if op:
                ax.scatter([float(r["lon"]) for r in op], [float(r["lat"]) for r in op], s=60, c="none", marker="s", ec="red", lw=1.2, label=f"pixel codigo MIROVA V750, pasada con alerta (n={len(op)})", zorder=6)
            if on:
                ax.scatter([float(r["lon"]) for r in on], [float(r["lat"]) for r in on], s=60, c="none", marker="s", ec="magenta", lw=1.2, label=f"pixel codigo MIROVA V750, negativo limpio (n={len(on)})", zorder=6)
            # nuestros cumulos
            pv = [r for r in pas if r["vol"] == v and r["pc_lat"]]
            pub_pos = [r for r in pv if r["lab"] == "pos" and r["pub"] == "1"]
            np_pos = [r for r in pv if r["lab"] == "pos" and r["pub"] == "0"]
            pub_neg = [r for r in pv if r["lab"] == "neg_limpio" and r["pub"] == "1"]
            ax.scatter([float(r["pc_lon"]) for r in pub_pos], [float(r["pc_lat"]) for r in pub_pos], s=10, c="deepskyblue", marker="o", alpha=0.7, label=f"nuestro cumulo, alerta MIROVA y publicado (n={len(pub_pos)})", zorder=7)
            ax.scatter([float(r["pc_lon"]) for r in np_pos], [float(r["pc_lat"]) for r in np_pos], s=30, c="white", marker="x", lw=1.0, label=f"nuestro cumulo, alerta MIROVA, NO publicado (n={len(np_pos)})", zorder=8)
            ax.scatter([float(r["pc_lon"]) for r in pub_neg], [float(r["pc_lat"]) for r in pub_neg], s=30, c="lime", marker="^", ec="k", lw=0.3, label=f"nuestro cumulo publicado en negativo limpio (n={len(pub_neg)})", zorder=8)
            # puntos de referencia
            ax.plot(tc[1], tc[0], "+", c="white", ms=16, mew=2.5, label="centro del TIF de MIROVA", zorder=9)
            ax.plot(vent[1], vent[0], "*", c="gold", ms=16, mec="k", label="crater (vent_lat/lon)", zorder=9)
            ax.plot(g["lon"], g["lat"], "^", c="white", ms=10, mec="k", label="lat/lon de volcanoes.yaml", zorder=9)
            ax.plot(g["mirova_center"][1], g["mirova_center"][0], "D", c="orange", ms=7, mec="k", label="mirova_center_lat/lon (yaml)", zorder=9)
            if zoom:
                dlat, dlon = km_a_grados(tc[0], 13, 13)
                ax.set_xlim(tc[1] - dlon, tc[1] + dlon)
                ax.set_ylim(tc[0] - dlat, tc[0] + dlat)
                ax.set_title(f"{v}: residuo del TIF (mediana movil 9 px) y geometrias, ±13 km", fontsize=10)
            else:
                ax.set_title(f"{v}: TIF VIIRS 375 {fondo['base'] if fondo else 'SIN TIF'} (BT MIR, K); escena completa", fontsize=10)
            ax.set_aspect(1 / math.cos(math.radians(tc[0])))
            ax.set_xlabel("lon")
            ax.set_ylabel("lat")
        axes[1].legend(loc="upper center", bbox_to_anchor=(-0.1, -0.08), fontsize=7, ncol=3, frameon=True)
        fig.suptitle(f"S160 auditoria espacial: {v}. Fondo {fondo['base'] if fondo else 'sin TIF'} (ALERTA MIROVA {fondo['mir_vrp'] if fondo else ''} MW @ {fondo['mir_dist'] if fondo else ''} km, prominencia {float(fondo['res_sigma']):.1f} sigma)" if fondo else v, fontsize=10)
        out = C.AQUI / f"mapa_{v}.png"
        fig.savefig(out, dpi=130, bbox_inches="tight")
        plt.close(fig)
        print("escrito", out, "fondo:", path)


if __name__ == "__main__":
    main()
