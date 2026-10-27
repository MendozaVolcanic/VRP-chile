# -*- coding: utf-8 -*-
"""Verificador S165 (regla de posición), 3: ¿puede el instrumento dar distinto de cero en la dirección «calla»? (A116)
Sólo lectura; el almacén temporal se escribe en D:\\vrp-trabajo\\temporales\\s165_regla_posicion_verif.

POR QUÉ. El informe dice «ninguna en la dirección calla» en los tres sensores. Ese cero vale si la cadena
comun.variante -> store.append_record -> predicado con node PUEDE producir una pasada que la vía publica y «cercano»
calla. Se arman tres máscaras sintéticas sobre la grilla real de Láscar (750 m) y se pasan por la misma cadena:
  S1  anillo alrededor del cráter (centroide en el cráter, ningún píxel a menos de 2 celdas): la vía da summit y
      cerc_cr da far si el radio del anillo supera el inner. Con inner 5 km y celdas de 0,75 km hace falta un
      anillo de radio 8 celdas, 8-conexo: calla con cerc_cr.
  S2  un píxel en el cráter de Tupungatito (donde el cráter está lejos de X0, Y0): la vía (desde el cráter) da
      summit, cerc_ref (desde la referencia) da far: calla con cerc_ref, por el punto de medida.
  S3  el caso de Láscar del informe (píxel débil a 1 celda del cráter, fuente radiante a 20 celdas): publica de más.
Uso: python 03_nulo_instrumento.py  (escribe 03_nulo_instrumento_salida.txt)
"""
import io
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import comun as C  # noqa: E402
import banco_paridad as B  # noqa: E402

C.TEMP = Path(r"D:\vrp-trabajo\temporales\s165_regla_posicion_verif")
C.TEMP.mkdir(parents=True, exist_ok=True)
MV = C.MV
L = []


def pr(*x):
    s = " ".join(str(v) for v in x)
    L.append(s)
    print(s, flush=True)


def caso(nombre, volcan, celdas, rad, hora, V, inner_html):
    v = V[volcan]
    g = MV.grilla_del_volcan(volcan)
    la, lo = C.get_detection_anchor(v)
    pos = MV.posicion_de(g, la, lo)
    ref = ((g["ul_y"] - g["y0"]) / g["paso"] - 0.5, (g["x0"] - g["ul_x"]) / g["paso"] - 0.5)
    d = C.reglas(celdas, rad, g["n"], pos, ref, 0.75)
    rec = C.record_desde_pixeles(celdas, rad, g, pos, v["inner_radius_km"], "VIIRS_NOAA20_750", 2.0,
                                 MV.FAMILIAS["VIIRS750"]["lam_mir"])
    variantes = {"via": rec, "cerc_cr": C.variante(rec, d["cerc_cr"], v["inner_radius_km"]),
                 "cerc_ref": C.variante(rec, d["cerc_ref"], v["inner_radius_km"])}
    st = {k: C.por_el_almacen(r, volcan, v, hora) for k, r in variantes.items()}
    pub = dict(zip(st, C.publicar([(s, inner_html[volcan]) for s in st.values()])))
    pr(f"   {nombre} ({volcan}, inner {v['inner_radius_km']}): distancias", {k: round(d[k], 3) for k in ("via", "cerc_cr", "cerc_ref")},
       "| distance_class tras el almacén", {k: (s or {}).get("distance_class") for k, s in st.items()},
       "| publica", pub)
    return pub


def main():
    V = C.volcanes()
    inner_html = B.inner_desde_html()
    pr("== control del predicado:", C.control_predicado())
    out = {}
    # S1: anillo de radio 8 celdas alrededor de la celda del cráter de Láscar (inner 5 km = 6,67 celdas)
    g = MV.grilla_del_volcan("Lascar")
    la, lo = C.get_detection_anchor(V["Lascar"])
    f0, c0 = MV.celda_de(g, la, lo)
    celdas = []
    for a in range(-8, 9):
        for b in range(-8, 9):
            if 7.5 <= np.hypot(a, b) <= 8.5:
                celdas.append((f0 + a, c0 + b))
    rad = [1.0 + 0.001 * k for k in range(len(celdas))]       # una de ellas es la más radiante
    out["S1_anillo_cerc_cr"] = caso("S1 anillo r=8 celdas", "Lascar", celdas, rad, "2026-06-01 05:00", V, inner_html)
    # S2: un píxel en Planchón-Peteroa (cráter a 2,07 km de X0, Y0; inner 3) a menos de 3 km del cráter y a más de
    # 3 km de la referencia: se busca la celda, si existe, barriendo el entorno del cráter
    g = MV.grilla_del_volcan("PlanchonPeteroa")
    la, lo = C.get_detection_anchor(V["PlanchonPeteroa"])
    pos = MV.posicion_de(g, la, lo)
    ref = ((g["ul_y"] - g["y0"]) / g["paso"] - 0.5, (g["x0"] - g["ul_x"]) / g["paso"] - 0.5)
    inner = V["PlanchonPeteroa"]["inner_radius_km"]
    cand = []
    for a in range(-8, 9):
        for b in range(-8, 9):
            f, c = int(round(pos[0])) + a, int(round(pos[1])) + b
            dcr = np.hypot(f - pos[0], c - pos[1]) * 0.75
            dre = np.hypot(f - ref[0], c - ref[1]) * 0.75
            if dcr <= inner < dre:
                cand.append((dre - dcr, (f, c)))
    pr("   S2: celdas de PP a menos del inner del cráter y a más del inner de X0, Y0:", len(cand))
    celda = max(cand)[1]
    out["S2_crater_tupun"] = caso("S2 un píxel cerca del cráter de PP, lejos de X0, Y0", "PlanchonPeteroa", [celda],
                                  [2.0], "2026-06-01 05:00", V, inner_html)
    # S3: el caso del informe, en Láscar: píxel débil a 1 celda y fuente radiante a 20 celdas
    g = MV.grilla_del_volcan("Lascar")
    la, lo = C.get_detection_anchor(V["Lascar"])
    f0, c0 = MV.celda_de(g, la, lo)
    out["S3_lejana_radiante"] = caso("S3 débil cerca + radiante lejos", "Lascar", [(f0 + 1, c0), (f0 + 20, c0 + 5)],
                                     [0.8, 5.0], "2026-06-01 05:00", V, inner_html)
    calla_cr = out["S1_anillo_cerc_cr"]["via"] and not out["S1_anillo_cerc_cr"]["cerc_cr"]
    calla_ref = out["S2_crater_tupun"]["via"] and not out["S2_crater_tupun"]["cerc_ref"]
    demas = not out["S3_lejana_radiante"]["via"] and out["S3_lejana_radiante"]["cerc_cr"]
    pr("\n== veredicto del nulo: el instrumento produce «calla» con cerc_cr:", calla_cr,
       "| «calla» con cerc_ref:", calla_ref, "| «publica de más»:", demas)
    (AQUI / "03_nulo_instrumento_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
