"""S172: qué otros volcanes de volcanoes.yaml caen dentro de la grilla de cada uno de los 34, y en qué parte de la caja.

POR QUÉ (VS34-01 del verificador): la vía suma en vrp_mw TODOS los píxeles alertados de la grilla (D32), también los
de fuera de la caja sensible (con el umbral estricto), y el cúmulo que da la posición es el del píxel más radiante.
Un vecino activo dentro de la grilla (Villarrica a 19,8 km de Quetrupillán) aparece entonces como calor del volcán
nuevo, con su magnitud y su posición, y sin etiqueta (los 34 no tienen inner_radius_km). No se cambia pipeline/
(congelado, A45): esta lista es el dato para separarlo después, al leer la sombra.

CÓMO SE MIDE (la misma geometría que la vía, no un cuadrado de ±25 km; VS34-07): para cada familia (VIIRS 750 de
67 x 67 celdas, VIIRS 375 de 134 x 134, MODIS de 51 x 51) la celda del vecino es floor((x - ul_x) / paso),
floor((ul_y - y) / paso) en la grilla del volcán, y su clase es la de la caja que usa la vía (caja_roi en VIIRS 750 y
MODIS, caja_v375 en VIIRS 375), con la primera y la última fila y columna en NaN como hace detectar_mirova:
  2 = caja sensible, 1 = anillo conservador, 0 = resto de la grilla (umbral estricto), "borde" = fila o columna de
  borde (no alerta, pero su calor puede llegar interpolado a la celda vecina), "fuera" = fuera de la grilla.
km = distancia del vecino al punto (X0, Y0) del volcán.

Uso: python experiments/_s172_sombra34/vecinos_en_la_grilla.py              # imprime la tabla
     python experiments/_s172_sombra34/vecinos_en_la_grilla.py --escribir   # además escribe vecinos.yaml al lado
tests/test_sombra_34_s172.py recalcula la tabla y exige que sea igual a vecinos.yaml.
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import numpy as np
import yaml
from pyproj import Transformer

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from pipeline import mirova_v750_codigo as MV  # noqa: E402

SALIDA = Path(__file__).resolve().parent / "vecinos.yaml"
FAMILIAS = ("VIIRS750", "VIIRS375", "MODIS")


def _caja(g, v, familia):
    cfg = MV.FAMILIAS[familia]
    if cfg.get("roi1_half_m") is not None:
        box = MV.caja_v375(g, v["lat"], v["lon"], lado_sensible=cfg["lado_sensible"], half_roi1_m=cfg["roi1_half_m"])
    else:
        box = MV.caja_roi(g["roi"], n=g["n"], celda_crater=MV.celda_de(g, v["lat"], v["lon"]),
                          lado_sensible=cfg["lado_sensible"], lado_anillo=cfg["lado_anillo"], paso_m=g["paso"])
    box = np.array(box, float)
    box[:, [0, -1]] = np.nan
    box[[0, -1], :] = np.nan
    return box


def clase_en_la_grilla(v, w, familia):
    """Clase del volcán w dentro de la grilla del volcán v para la familia: 0, 1, 2, 'borde' o 'fuera'."""
    cfg = MV.FAMILIAS[familia]
    g = MV.grilla_del_volcan(v["name"], paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
    x, y = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True).transform(w["lon"], w["lat"])
    col, fila = int((x - g["ul_x"]) // g["paso"]), int((g["ul_y"] - y) // g["paso"])
    if not (0 <= fila < g["n"] and 0 <= col < g["n"]):
        return "fuera"
    c = _caja(g, v, familia)[fila, col]
    return "borde" if np.isnan(c) else int(c)


def vecinos():
    """{volcán de los 34: [ {vecino, tier_a, km, caja: {familia: clase}} ]}, sólo los que tienen algún vecino dentro."""
    vols = yaml.safe_load((REPO / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]
    nrt = set(yaml.safe_load((REPO / ".github/workflows/nrt.yml").read_text(encoding="utf-8"))
              ["jobs"]["process"]["strategy"]["matrix"]["volcano"])
    out = {}
    for v in vols:
        if v["name"] in nrt:
            continue
        g = MV.grilla_del_volcan(v["name"])
        t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
        lista = []
        for w in vols:
            if w["name"] == v["name"]:
                continue
            caja = {f: clase_en_la_grilla(v, w, f) for f in FAMILIAS}
            if all(c == "fuera" for c in caja.values()):
                continue
            x, y = t.transform(w["lon"], w["lat"])
            lista.append({"vecino": w["name"], "tier_a": w["name"] in nrt,
                          "km": round(float(np.hypot(x - g["x0"], y - g["y0"])) / 1000.0, 1), "caja": caja})
        if lista:
            out[v["name"]] = sorted(lista, key=lambda e: e["km"])
    return out


CABECERA = """\
# S172 (VS34-01 y VS34-07): volcanes de la sombra de los 34 con otro volcán de volcanoes.yaml dentro de su grilla de
# MIROVA. Generado por experiments/_s172_sombra34/vecinos_en_la_grilla.py --escribir; no editar a mano
# (tests/test_sombra_34_s172.py lo recalcula). caja: clase de la celda del vecino en la caja de la vía, por familia:
# 2 sensible, 1 anillo, 0 resto de la grilla (umbral estricto), borde (no alerta; su calor puede llegar interpolado),
# fuera (fuera de la grilla). km: distancia del vecino al punto (X0, Y0) del volcán. tier_a: el vecino es uno de los 11.
# La vía suma todos los alertados de la grilla: el calor de un vecino activo entra en vrp_mw del volcán de la izquierda.
"""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--escribir", action="store_true")
    a = ap.parse_args(argv)
    d = vecinos()
    for nombre, lista in d.items():
        txt = "; ".join(f"{e['vecino']}{' (Tier A)' if e['tier_a'] else ''} a {e['km']} km "
                        f"[V750 {e['caja']['VIIRS750']}, V375 {e['caja']['VIIRS375']}, MODIS {e['caja']['MODIS']}]"
                        for e in lista)
        print(f"{nombre:22s} {txt}")
    print(f"\n{len(d)} de 34 tienen otro volcán de volcanoes.yaml dentro de su grilla (en alguna familia)")
    print(f"con un vecino de los 11: {sorted(n for n, l in d.items() if any(e['tier_a'] for e in l))}")
    if a.escribir:
        texto = CABECERA + yaml.safe_dump({"volcanes": d}, allow_unicode=True, sort_keys=False, width=120)
        with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print(f"escrito {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.exit(main())
