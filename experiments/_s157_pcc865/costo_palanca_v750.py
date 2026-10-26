# -*- coding: utf-8 -*-
"""S157 issue #865: cuánto costaría volver VIIRS 750 a la conectiva `min` (la palanca que separa a K de C0 en esa
pasada), medido con la tabla por pasada del A/B de meses de S151 (experiments/_s151_max_v750/pasadas_viirs750_B_F.csv).

POR QUÉ ESTA TABLA. Sus dos brazos tienen el Test 1 APAGADO y difieren SÓLO en la conectiva de los Tests 2 y 3:
B = `min` (fórmula), F = `max` (prosa, la de K). En VIIRS 750 F es K (la banda 22 es sólo MODIS). O sea que B es
exactamente «K con `min` en VIIRS 750», la palanca que este issue pregunta. Ventana abril a agosto de 2026, referencia
congelada por mes (ver el docstring de experiments/_s151_max_v750/suma_de_errores.py, que nombra sus límites:
no tiene la razón de magnitud y las pasadas sin etiqueta no entran).
"""
import csv
import io
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
CSV = Path(__file__).resolve().parents[1] / "_s151_max_v750" / "pasadas_viirs750_B_F.csv"


def main():
    filas = list(csv.DictReader(open(CSV, encoding="utf-8")))
    por = defaultdict(Counter)
    for f in filas:
        vol = f["clave"].split("|")[0]
        for g in (vol, "TOTAL"):
            c = por[g]
            c[f["lab"]] += 1
            c[f["lab"] + "_B"] += int(f["pub_B"])
            c[f["lab"] + "_F"] += int(f["pub_F"])
            if f["lab"] == "pos" and f["vrp_ref"] and float(f["vrp_ref"]) >= 1.0:
                c["prot"] += 1
                c["prot_B"] += int(f["pub_B"])
                c["prot_F"] += int(f["pub_F"])
    print(f"{len(filas)} pasadas VIIRS 750, abril a agosto de 2026 (B = min sin Test 1, F = max sin Test 1 = K)")
    print(f"{'volcan':20s} | alertas pub B / F de n | protegidas>=1MW pub B / F de n | negativos limpios pub B / F de n")
    for g in sorted(por, key=lambda x: (x == "TOTAL", x)):
        c = por[g]
        print(f"{g:20s} | {c['pos_B']:4d} / {c['pos_F']:4d} de {c['pos']:4d} | {c['prot_B']:3d} / {c['prot_F']:3d} de "
              f"{c['prot']:3d} | {c['neg_limpio_B']:4d} / {c['neg_limpio_F']:4d} de {c['neg_limpio']:5d} "
              f"({100 * c['neg_limpio_B'] / max(c['neg_limpio'], 1):.1f} % / {100 * c['neg_limpio_F'] / max(c['neg_limpio'], 1):.1f} %)")


if __name__ == "__main__":
    main()
