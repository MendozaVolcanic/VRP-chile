# -*- coding: utf-8 -*-
"""S159 frente GEO, parte S: el escalon del OSF v2.5 en VIIRS 750 sobre 50 grados de cenit, contra las zonas
de agregacion de la banda M del VIIRS.

HIPOTESIS A REFUTAR (sospecha del coordinador): las filas V750 que no cumplen VRP = dL x 1,97e7 x 0,5625 son las
de la zona de agregacion del borde (1:1), y la razon VRP_OSF / VRP_formula es constante en ellas.

Fuente de los limites (renderizado a imagen en esta sesion, atbd_geo_p49.png): VIIRS Geolocation ATBD 2014
(423-ATBD-002), pagina impresa 27 (pagina 49 del PDF), seccion 3.3.1.1: 3:1 a 2:1 en +/-31,589 grados de
angulo de barrido, 2:1 a 1:1 en +/-44,680 grados; barrido maximo 56,063. Altura nominal 828 +/- 12 km
(pagina impresa 9, pagina 31 del PDF, atbd_geo_p31.png).
Conversion cenit -> angulo de barrido (Tierra esferica): sin(theta) = R / (R + h) * sin(z), R = 6371 km.

Las dos preguntas del instrumento:
1. Si el escalon estuviera en el limite de zona, esta medicion lo veria: el control positivo inyecta un escalon
   sintetico en theta = 44,680 sobre filas que si cumplen y el localizador de cambio lo debe encontrar ahi.
2. Si el instrumento estuviera muerto (columnas mal leidas, k equivocado), MODIS y VIIRS 375 no darian 100 %
   de cumplimiento (control negativo) y la fraccion V750 bajo 50 grados no daria 0.
Denominador: filas del OSF v2.5 por sensor (2000-02 a 2025-12, global). Ventana: todo el archivo.

Uso: python -I s1_escalon_vs_zonas.py <csv OSF> <carpeta salida>
"""
import io
import os
import sys

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = 6371.0
LIM = (31.589, 44.680, 56.063)
K = {"MODIS_1000": 1.89e7, "VIIRS_375": 18.0 * 140625, "VIIRS_750": 1.97e7 * 0.5625}


def theta(z, h):
    return np.degrees(np.arcsin(np.clip(R / (R + h) * np.sin(np.radians(z)), -1, 1)))


def zen(th, h):
    return np.degrees(np.arcsin(np.clip((R + h) / R * np.sin(np.radians(th)), -1, 1)))


def cambio(x, y, lo, hi, paso=0.01):
    """Umbral c que mejor separa y (booleano) en x<c (todo y=0) contra x>=c: maximiza la diferencia de
    fraccion entre una ventana de 0,5 grados a cada lado."""
    best = (None, -1)
    for c in np.arange(lo, hi, paso):
        a = y[(x >= c - 0.5) & (x < c)]
        b = y[(x >= c) & (x < c + 0.5)]
        if len(a) < 20 or len(b) < 20:
            continue
        d = b.mean() - a.mean()
        if d > best[1]:
            best = (round(c, 3), d)
    return best


def main(osf_csv, out):
    o = pd.read_csv(osf_csv)
    o["sensor"] = o.Satellite.map({1: "MODIS", 2: "MODIS", 3: "VIIRS", 4: "VIIRS"}) + "_" + o.Resolution.astype(str)
    o["dL"] = o.Tot_Lmir_hot - o.Tot_Lmir_bk
    o["ratio"] = o.VRP / (o.dL * o.sensor.map(K))
    o["nocumple"] = (o.ratio - 1).abs() > 1e-2
    o["th828"] = theta(o.SatZen, 828.0)
    print("conversion: limites de zona en cenit (h = 816 / 828 / 840 km):")
    for t in LIM:
        print(f"  theta {t:.3f} -> z {zen(t, 816):.2f} / {zen(t, 828):.2f} / {zen(t, 840):.2f}")
    print("  chequeo contra el ATBD p. impresa 27 ('55 grados de barrido ~ 65 de cenit'):", round(zen(55, 828), 2))
    print("  cenit 50,000 -> theta", round(float(theta(50.0, 828)), 3), "(h 816:", round(float(theta(50.0, 816)), 3),
          ", h 840:", round(float(theta(50.0, 840)), 3), ")")

    print("\nfraccion que NO cumple al 1 %, por sensor y tramo de ANGULO DE BARRIDO (h = 828 km):")
    bins = [0, 20, 31.589, 36, 40, 42, 42.5, 42.69, 43, 43.5, 44, 44.68, 46, 48, 50, 52, 54, 56.5]
    o["tb"] = pd.cut(o.th828, bins, right=False)
    t = o.groupby(["tb", "sensor"], observed=True).nocumple.agg(["mean", "size"]).unstack("sensor")
    print(t.round(4).to_string())

    v = o[o.sensor == "VIIRS_750"]
    print("\nlocalizador de cambio, V750, en cenit:", cambio(v.SatZen.values, v.nocumple.values, 40, 60))
    print("localizador de cambio, V750, en theta:", cambio(v.th828.values, v.nocumple.values, 35, 50))
    print("filas V750 en theta [44,0, 44,68) / [44,68, 45,4): no cumplen",
          round(v[(v.th828 >= 44.0) & (v.th828 < 44.68)].nocumple.mean(), 4),
          "/", round(v[(v.th828 >= 44.68) & (v.th828 < 45.4)].nocumple.mean(), 4))
    print("filas V750 con theta en zona 2:1 (31,589 a 44,680) y cenit > 50: n",
          int(((v.th828 < 44.68) & (v.SatZen > 50)).sum()), "no cumplen",
          int(((v.th828 < 44.68) & (v.SatZen > 50) & v.nocumple).sum()))

    # Control positivo: escalon sintetico en theta = 44,680 sobre filas que cumplen
    s = v[~v.nocumple].copy()
    rng = np.random.default_rng(159)
    s["sint"] = (s.th828 >= 44.68) & (rng.random(len(s)) < 0.25)
    print("control positivo (escalon sintetico en theta 44,680, 25 %): cambio en theta =",
          cambio(s.th828.values, s.sint.values, 35, 50), "; en cenit =", cambio(s.SatZen.values, s.sint.values, 40, 60))
    # Control negativo: MODIS y VIIRS 375
    for sen in ("MODIS_1000", "VIIRS_375"):
        w = o[o.sensor == sen]
        print(f"control negativo {sen}: no cumplen {int(w.nocumple.sum())} de {len(w)}; sobre 50 grados de cenit: "
              f"{int(w[w.SatZen > 50].nocumple.sum())} de {int((w.SatZen > 50).sum())}")

    # Razon en las que no cumplen: constante?
    m = v[v.nocumple]
    print("\nrazon VRP_OSF / VRP_formula en las que NO cumplen (n =", len(m), "):")
    print(m.ratio.describe(percentiles=[.05, .25, .5, .75, .95]).round(4).to_string())
    for c, nom in ((0.5, "1/2"), (2 / 3, "2/3"), (1 / 3, "1/3")):
        print(f"  fraccion a menos de 1 % de {nom}: {((m.ratio / c - 1).abs() < 0.01).mean():.4f}")
    print("  mediana de la razon por tramo de theta:")
    print(m.groupby(pd.cut(m.th828, [42, 43, 44, 44.68, 46, 48, 50, 52, 54, 56.5]), observed=True).ratio
          .agg(["median", "size"]).round(4).to_string())
    print("  por Dayflag:", m.groupby("Dayflag").ratio.median().round(4).to_dict(),
          "| fraccion no cumple sobre 50 por Dayflag:",
          v[v.SatZen > 50].groupby("Dayflag").nocumple.mean().round(4).to_dict())
    # lado del barrido (SatAzi): azimut relativo cambia de signo a cada lado del nadir
    print("  fraccion no cumple sobre 50 grados por signo de SatAzi:",
          v[v.SatZen > 50].groupby(np.sign(v.SatAzi)).nocumple.mean().round(4).to_dict())

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
        for sen, col in (("VIIRS_750", "C3"), ("VIIRS_375", "C0"), ("MODIS_1000", "C2")):
            w = o[o.sensor == sen]
            bb = np.arange(0, 70.5, 0.5)
            g = w.groupby(pd.cut(w.SatZen, bb), observed=True).nocumple.mean()
            ax[0].plot([b.left + 0.25 for b in g.index], g.values, color=col, label=sen)
            if sen != "MODIS_1000":
                bt = np.arange(0, 56.5, 0.25)
                g2 = w.groupby(pd.cut(w.th828, bt), observed=True).nocumple.mean()
                ax[1].plot([b.left + 0.125 for b in g2.index], g2.values, color=col, label=sen)
        ax[0].axvline(50, ls=":", color="k", label="cenit 50")
        for tl in LIM[:2]:
            ax[0].axvline(zen(tl, 828), ls="--", color="gray")
            ax[1].axvline(tl, ls="--", color="gray")
        ax[1].axvline(float(theta(50, 828)), ls=":", color="k", label="theta de cenit 50")
        ax[0].set_xlabel("cenit del sensor (grados)")
        ax[1].set_xlabel("angulo de barrido (grados, h = 828 km)")
        for a in ax:
            a.set_ylabel("fraccion que no cumple VRP = dL k")
            a.legend(fontsize=8)
        ax[0].set_title("OSF v2.5, limites de zona en gris (cenit equivalente)")
        ax[1].set_title("mismo dato contra el angulo de barrido")
        fig.tight_layout()
        fig.savefig(os.path.join(out, "s1_escalon_vs_zonas.png"), dpi=110)
        print("\nfigura:", os.path.join(out, "s1_escalon_vs_zonas.png"))
    except ImportError:
        print("sin matplotlib, sin figura")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
