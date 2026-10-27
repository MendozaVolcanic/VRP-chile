# -*- coding: utf-8 -*-
"""VAD2-05 / T6: la vara 3 (distancia de cada brazo contra la Distancia_km de MIROVA, grupo 'alertas con distancia') toma
la primera fila ALERTA con distancia, venga de la tabla (CONS) o del OCR, y de cualquier fecha. A119: el OCR tenía la
geometría mal calibrada hasta 2026-06-11 y sin distancia medida hasta 2026-06-13.
Escena: 3 alertas con fila CONS (dist 0.8, píxel a 0.75 km del centro) y 2 alertas solo OCR antes del 2026-06-13 con una
distancia de 20 km (mal calibrada). Si el lector filtrara por fuente, n sería 3 y la mediana ~0.1; si no, n = 5.
Pregunta 1: si la vara 3 mezclara fuentes, esto lo ve (n y mediana). Pregunta 2: el control es la misma escena sin las dos
filas OCR (n = 3)."""
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ver_comun import Pob, TMP, lector  # noqa: E402

UNO = [(33, 34, 0.9)]


def correr(con_ocr):
    d = TMP / "t6" / ("con_ocr" if con_ocr else "sin_ocr")
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    p = Pob()
    for n in range(12):
        p.pasada(f"2026-04-{1 + n:02d} 05:00", "neg_limpio", [])
    for n in range(3):
        p.pasada(f"2026-06-{20 + n:02d} 05:00", "pos", UNO, 0.4, dist_mirova=0.8, pub_prod=True)
    if con_ocr:
        for n in range(2):
            h = f"2026-05-{1 + n:02d} 05:00"
            p.pasada(h, "pos", UNO, 0.4, dist_mirova=20.0, pub_prod=True, source="OCR",
                     filas=[{"fecha_utc": h + ":00", "tipo": "ALERTA_TERMICA_OCR", "vrp_mw": 0.4, "dist_km": 20.0,
                             "source": "OCR"}])
    p.pasada("2026-07-04 05:00", "far_ref", UNO, 3.0, dist_mirova=13.1)
    p.escribir(d)
    rc, out = lector(d)
    m = re.search(r"alertas con distancia B0: (.*)", out)
    print(("CON dos alertas solo-OCR de mayo: " if con_ocr else "SIN ellas:                        "),
          f"rc={rc} |", m.group(1) if m else "sin línea")


correr(False)
correr(True)
