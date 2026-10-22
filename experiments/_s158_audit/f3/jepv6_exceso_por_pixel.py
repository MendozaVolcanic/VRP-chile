# -*- coding: utf-8 -*-
"""F3: en los datos de MIROVA de Vulcano (OSF jepv6, VIIRS 375, 2021-2023; sin licencia: se lee, no se copia), ¿el
exceso POR PÍXEL baja cuando Npix sube (un foco repartido en más celdas) o se mantiene (más superficie caliente)?
Complementa reparto_foco.py con datos de MIROVA sola, sin pareo con nosotros. L_hot por píxel incluye el fondo (~0,2),
que tapa la diferencia; por eso se mira el EXCESO por píxel. Control: VRP / ΣΔL = 2.531.250 en todas (k*A fijo).
Instrumento: si Npix no variara, no habría estratos (se imprime el conteo por Npix). Cenit <= 30 para no mezclar la huella.
Uso: python -B jepv6_exceso_por_pixel.py <S1_MIROVA_Vulcano.csv>
"""
import sys
import pandas as pd
d = pd.read_csv(sys.argv[1])
d.columns = ["date", "zen", "azi", "npix", "lhot", "lbk", "vrp"]
print("k*A min/max:", (d.vrp / (d.lhot - d.lbk)).min().round(0), (d.vrp / (d.lhot - d.lbk)).max().round(0), " n total", len(d))
g = d[d.zen <= 30].copy()
g["exc_px"] = (g.lhot - g.lbk) / g.npix
g["lhot_px"] = g.lhot / g.npix
print(g.groupby(g.npix.clip(upper=4)).agg(n=("vrp", "size"), exc_px_med=("exc_px", "median"), exc_tot_med=("vrp", lambda x: (x / 2531250).median()),
                                           lhot_px_med=("lhot_px", "median"), lbk_px_med=("lbk", lambda x: (x / g.loc[x.index, "npix"]).median())).round(4).to_string())
