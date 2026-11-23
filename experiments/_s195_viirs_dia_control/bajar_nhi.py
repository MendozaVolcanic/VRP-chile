# -*- coding: utf-8 -*-
"""Baja las series NHI de los volcanes de `nhi_cajas.json` a una carpeta, a un commit fijo de NHI-v1 (S195).

POR QUÉ un commit fijo: NHI-v1 agrega escenas y puede recalcular las viejas; el veredicto tiene que poder repetirse con
las mismas escenas. El commit usado se escribe en <dest>/COMMIT.txt.

Uso: python experiments/_s195_viirs_dia_control/bajar_nhi.py --commit <sha de NHI-v1> --dest <carpeta>
"""
import argparse
import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", required=True)
    ap.add_argument("--dest", required=True)
    a = ap.parse_args()
    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    cajas = json.loads((AQUI / "nhi_cajas.json").read_text(encoding="utf-8"))["volcanes"]
    for vol, c in cajas.items():
        if not c.get("en_nhi"):
            continue
        ruta = "docs/nhi_data/%s/nhi_timeseries.json" % c["nombre_nhi"]
        o = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                            "repos/MendozaVolcanic/NHI-v1/contents/%s?ref=%s" % (urllib.parse.quote(ruta), a.commit)],
                           capture_output=True, check=False)
        if o.returncode != 0:
            print("%-20s sin serie (%s)" % (vol, o.stderr.decode("utf-8", "replace").strip()[:80]))
            continue
        serie = json.loads(o.stdout.decode("utf-8"))
        (dest / c["nombre_nhi"]).mkdir(exist_ok=True)
        (dest / c["nombre_nhi"] / "nhi_timeseries.json").write_bytes(o.stdout)
        print("%-20s %d escenas" % (vol, len(serie)))
    (dest / "COMMIT.txt").write_text(a.commit + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
