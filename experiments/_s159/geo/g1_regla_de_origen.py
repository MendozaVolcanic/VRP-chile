# -*- coding: utf-8 -*-
"""S159 frente GEO, parte G: la regla que fija el origen de la grilla UTM de MIROVA.

HIPOTESIS H-A (formulada en esta sesion, antes de mirar el resultado por volcan): MIROVA arma los centros de celda
como en MATLAB `x = X0-25000 : paso : X0+25000` (e igual en y, de sur a norte), con (X0, Y0) = UTM del punto de
referencia del volcan. Con paso 375 eso da 134 centros (0..133), con 750 da 67 y con 1000 da 51: los tres tamanos
de grilla conocidos (134 en los TIF, 67 en Campus 2022 y en el .m, 51 en Coppola 2023) salen de una sola regla.
Consecuencias comprobables en la grilla de 375 m:
  esquina UL (borde) = (X0 - 25187,5 ; Y0 + 25062,5), centro de la grilla = (X0 - 62,5 ; Y0 - 62,5).
Predicciones para las otras grillas (NO medibles con TIF de 375 m):
  750 m: 67 centros, centro de grilla = (X0 - 250 ; Y0 - 250), bordes en X0 - 25375 + 750 k;
  1000 m: 51 centros, centro de grilla = (X0 ; Y0), bordes en X0 - 25500 + 1000 k.
  O sea, con H-A la grilla de 750 NO es 2 x 2 de la de 375 (sus bordes caen a media celda de 375 de los bordes
  de 375), aunque sus centros pares coincidan con centros de 375 (X0 - 25000 + 750 k es centro de 375 con 2k).

Medicion: para cada TIF UTM del inventario (r1), deducir (X0, Y0) = (UL_x + 25187,5 ; UL_y - 25062,5), pasarlo a
lat/lon y compararlo con `lat`/`lon` del yaml (que en 8 de 11 es la coordenada GVP sin tocar, S158 3.1). Si la
regla es cierta, el residuo es del orden del redondeo de la coordenada (3 decimales = hasta 55 m en lat).

Las dos preguntas del instrumento:
1. Si la regla fuera otra (por ejemplo centro en X0 exacto, o esquina en X0 - 25125), el residuo saldria de 62,5
   o 125 m en alguna componente; el control negativo imprime el residuo bajo esas reglas alternativas.
2. Si la lectura del TIF estuviera muerta, no habria filas UTM (se imprime el conteo) y el script se detiene.
Uso: python -I g1_regla_de_origen.py <inventario r1 csv> <volcanoes.yaml>
"""
import io
import math
import sys

import pandas as pd
import yaml
from pyproj import Transformer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ALIAS = {"ChillanNevadosde": "NevadosDeChillan"}
REGLAS = {  # desfase (UL_x -> X0, UL_y -> Y0) en metros, para celda de 375 m
    "H-A  X0-25000:375:X0+25000 (sur a norte)": (25187.5, -25062.5),
    "alt1 grilla centrada en X0 (134 celdas)": (25125.0, -25125.0),
    "alt2 X0-25000:375 de norte a sur": (25187.5, -24937.5),
}


def main(inv_csv, yml):
    inv = pd.read_csv(inv_csv)
    u = inv[(inv.epsg.notna()) & (inv.epsg != 4326)].copy()
    print("TIF UTM en el inventario:", len(u), "| por sensor:", u.groupby("sensor").size().to_dict())
    if u.empty:
        sys.exit("sin TIF UTM: instrumento sin dato")
    vols = {v["name"]: v for v in yaml.safe_load(open(yml, encoding="utf-8"))["volcanoes"]}
    u["md5_ok"] = u.md5_archivo == u.md5_indice
    print("md5 del archivo bajado = md5 del indice:", int(u.md5_ok.sum()), "de", len(u))
    # grillas distintas por volcan y sensor
    g = u.groupby(["volcano", "sensor", "epsg", "a", "ancho", "alto", "c", "f"]).size().reset_index(name="n")
    print("\ngrillas UTM distintas (volcan, sensor, EPSG, celda, ancho x alto, UL):")
    print(g.to_string(index=False))
    print("\nresiduo de la regla contra lat/lon del yaml (metros este, norte; distancia):")
    for nom, (dx, dy) in REGLAS.items():
        print(" ", nom)
        for _, r in g[g.sensor == "VIIRS375"].drop_duplicates("volcano").iterrows():
            v = vols[ALIAS.get(r.volcano, r.volcano)]
            epsg = int(r.epsg)
            fwd = Transformer.from_crs(4326, epsg, always_xy=True)
            inv_t = Transformer.from_crs(epsg, 4326, always_xy=True)
            X0, Y0 = r.c + dx, r.f + dy
            xv, yv = fwd.transform(v["lon"], v["lat"])
            lon0, lat0 = inv_t.transform(X0, Y0)
            print(f"    {r.volcano:20s} X0-yaml ({X0 - xv:+7.1f}, {Y0 - yv:+7.1f}) {math.hypot(X0 - xv, Y0 - yv):6.1f} m"
                  f" | punto implicito ({lat0:.5f}, {lon0:.5f}) | yaml ({v['lat']}, {v['lon']})")


def comparar_grillas(inv_csv):
    """Relacion entre la grilla de 750 m (y de 1 km si la hay) y la de 375 m del mismo volcan.
    H-A predice UL_750 - UL_375 = (-187,5 ; -187,5) m; la hipotesis 2 x 2 (misma esquina, mismo centro) predice
    (0 ; 0). Para MODIS 51 x 51 con H-A: UL_1000 - UL_375 = (-312,5 ; -312,5)."""
    inv = pd.read_csv(inv_csv)
    u = inv[(inv.epsg.notna()) & (inv.epsg != 4326)]
    g = u.groupby(["volcano", "sensor"]).agg(epsg=("epsg", "first"), c=("c", "first"), f=("f", "first"),
                                             a=("a", "first"), w=("ancho", "first"), nc=("c", "nunique"),
                                             nf=("f", "nunique"), n=("c", "size")).reset_index()
    print("\ngrilla por volcan y sensor (nc, nf = origenes distintos entre archivos; n = archivos):")
    print(g.to_string(index=False))
    print("\nUL del sensor menos UL de VIIRS 375 del mismo volcan (H-A: 750 -> -187,5/-187,5; 1000 -> -312,5/-312,5;"
          " 2 x 2 -> 0/0):")
    for vol, gg in g.groupby("volcano"):
        b = gg[gg.sensor == "VIIRS375"]
        if b.empty:
            continue
        b = b.iloc[0]
        for _, r in gg[gg.sensor != "VIIRS375"].iterrows():
            if r.epsg != b.epsg:
                print(f"  {vol:20s} {r.sensor}: otra zona UTM ({int(r.epsg)} contra {int(b.epsg)})")
                continue
            print(f"  {vol:20s} {r.sensor} {int(r.w)}x{int(r.w)} celda {r.a:.1f}: dUL = ({r.c - b.c:+.2f}, {r.f - b.f:+.2f}) m;"
                  f" centro del sensor menos centro 375 = ({r.c + r.a * r.w / 2 - (b.c + b.a * b.w / 2):+.2f}, "
                  f"{r.f - r.a * r.w / 2 - (b.f - b.a * b.w / 2):+.2f}) m")


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[3] == "--grillas":
        comparar_grillas(sys.argv[1])
        sys.exit()
    main(sys.argv[1], sys.argv[2])
