"""S147 - baja SOLO los TIF de VIIRS 375 de una ventana desde mirova-tif-archive, por la API.

POR QUE NO UN PULL. El repo `MendozaVolcanic/mirova-tif-archive` pesa 17 GB en el remoto y un
`git pull` ya lleno el disco una vez (regla del proyecto: no hacer pull de repos de datos
gigantes). Pero cada TIF pesa 20 a 40 KB: los 1.058 de la ventana 2026-09-01 a 2026-09-20 son 99 MB.
Se baja primero `index.csv` (5 MB), se filtra, y se traen solo esos archivos verificando su md5.

Los TIF NO se commitean (estan en el .gitignore de esta carpeta): se regeneran con este script.

Uso: python experiments/_s147_tif/bajar_tif.py [--desde 2026-09-01] [--hasta 2026-09-21]
"""
from __future__ import annotations
import argparse
import hashlib
import os
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
BASE = "https://raw.githubusercontent.com/MendozaVolcanic/mirova-tif-archive/main/"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2026-09-01")
    ap.add_argument("--hasta", default="2026-09-21")
    ap.add_argument("--sensor", default="VIIRS375")
    a = ap.parse_args()
    idx = AQUI / "index_remoto.csv"
    urllib.request.urlretrieve(BASE + "index.csv", idx)
    ix = pd.read_csv(idx)
    ix["lm"] = pd.to_datetime(ix.last_modified_utc, errors="coerce", utc=True)
    s = ix[(ix.lm >= a.desde) & (ix.lm < a.hasta) & (ix.sensor == a.sensor)]
    print(f"{len(s)} TIF de {a.sensor} entre {a.desde} y {a.hasta}, {s.size_bytes.sum() / 1e6:.1f} MB")

    def baja(row):
        out = AQUI / "tif" / row.tif_path.replace("data/tif/", "")
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists() and out.stat().st_size == row.size_bytes:
            return "ya estaba"
        try:
            urllib.request.urlretrieve(BASE + row.tif_path, out)
            return "ok" if hashlib.md5(out.read_bytes()).hexdigest() == row.md5 else "md5 distinto"
        except Exception as e:  # noqa: BLE001
            return "error: " + type(e).__name__

    with ThreadPoolExecutor(8) as ex:
        print(Counter(ex.map(baja, list(s.itertuples()))))


if __name__ == "__main__":
    main()
