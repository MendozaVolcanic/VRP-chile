# -*- coding: utf-8 -*-
"""Extrae a CSV las pasadas VIIRS 750 de las tablas por pasada del A/B de meses (control B, brazo F).

POR QUE. El verificador de la tarea 1.10 encontro que esas tablas (salida de armar_tabla.py, abril a agosto)
vivian solo en un scratchpad de la sesion S150. Sin ellas la suma de errores no se puede recontar pasada por
pasada. Las tablas enteras pesan unos 9 MB y traen los tres sensores; aca se guarda solo lo que la 1.10 usa.

Uso: python extraer_tablas.py <carpeta con tabla_<mes>.json>
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

MESES = ["abril", "mayo", "junio", "julio", "agosto"]
SALIDA = Path(__file__).resolve().parent / "pasadas_viirs750_B_F.csv"
CAMPOS = ["mes", "clave", "lab", "alerta_solo_ocr", "vrp_ref", "pub_B", "pub_F"]


def main(origen):
    filas, labs = [], Counter()
    for mes in MESES:
        T = json.load(open(Path(origen) / f"tabla_{mes}.json", encoding="utf-8"))["pasadas"]
        for clave, v in sorted(T.items()):
            if "|VIIRS750|" not in clave:
                continue
            c, b = v.get("control"), v.get("brazo")
            if c is None or b is None or c["lab"] != b["lab"]:
                raise ValueError(f"{mes} {clave}: pasada en un solo brazo o con etiqueta distinta")
            labs[c["lab"]] += 1
            filas.append({"mes": mes, "clave": clave, "lab": c["lab"], "alerta_solo_ocr": int(bool(c.get("alerta_solo_ocr"))),
                          "vrp_ref": c.get("vrp_ref"), "pub_B": int(c["pub"]), "pub_F": int(b["pub"])})
    with open(SALIDA, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} pasadas VIIRS 750 -> {SALIDA.name}; etiquetas: {dict(labs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
