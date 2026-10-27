# -*- coding: utf-8 -*-
"""T7: escena que la batería del autor no tiene y que separa 'pico' de 'el más lejano' y de 'radiante'.
Un cúmulo de 9 píxeles (fila 33, columnas 36 a 44), el más radiante en el extremo cercano (col 36). Láscar, inner 5 km
(6,67 celdas), cráter y centro en (33, 33).
  radiante: centroide en col 40 = 5,25 km  -> far  -> calla
  cercano : col 36 = 2,25 km                -> summit -> publica
  pico    : col 36 (el de mayor M13)        -> summit -> publica
La copia mutada M11 (pico = el más lejano) daría pico far -> calla; la batería del autor no la distingue.
Pregunta 1: si pico estuviera roto, esta escena lo ve. Pregunta 2: control = los tres brazos sobre la escena BORDE del
autor (pico en el extremo lejano) tienen que dar pico far."""
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ver_comun import Pob, TMP, lector  # noqa: E402

CERCA = [(33, c, 5.0 if c == 36 else 0.9) for c in range(36, 45)]
LEJOS = [(33, c, 5.0 if c == 44 else 0.9) for c in range(36, 45)]


def correr(nombre, pix):
    d = TMP / "t7" / nombre
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    p = Pob()
    for n in range(12):
        p.pasada(f"2026-04-{1 + n:02d} 05:00", "neg_limpio", [])
    for n in range(3):
        p.pasada(f"2026-05-{1 + n:02d} 05:00", "pos", [(33, 34, 0.9)], 0.4, dist_mirova=0.8, pub_prod=True)
    p.pasada("2026-07-01 05:00", "pos", pix, 2.0, dist_mirova=2.0, pub_prod=False)   # protegida con la escena
    p.escribir(d)
    rc, out = lector(d, ["--salida", d / "lector2.txt"][:0])
    ms = {}
    for b in ("radiante", "cercano", "pico"):
        m = re.search(rf"^   B0 {b}\s+prot\s+(\d+) P1\s+(\d+)", out, re.M)
        ms[b] = None if m is None else int(m.group(2))
    print(f"{nombre}: rc={rc} | P1 de la protegida por brazo (1 = la pierde = calla): {ms}")
    return ms


a = correr("pico_cercano_radiante_lejos", CERCA)
b = correr("pico_en_el_extremo_lejano", LEJOS)
ok = a == {"radiante": 1, "cercano": 0, "pico": 0} and b["pico"] == 1 and b["cercano"] == 0
print("ESPERADO (cercano y pico publican en la escena CERCA; en LEJOS el pico es lejano):", "COINCIDE" if ok else "NO COINCIDE")
