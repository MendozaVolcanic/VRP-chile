"""Baja los CSV vigentes de MendozaVolcanic/Mirova-v1 (rama main) a una carpeta.

Uso: python 00_descargar_remoto.py DESTINO
Deja tambien remoto_meta.txt con el sha y la fecha del ultimo commit del remoto,
para que cada numero del informe lleve su ventana (regla A90).
"""
import json
import os
import subprocess
import sys
import urllib.request

from comun import ARCHIVOS, POR_VOLCAN

BASE = "https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/"


def main():
    dest = sys.argv[1]
    os.makedirs(dest, exist_ok=True)
    for f in ARCHIVOS + POR_VOLCAN + ["anotaciones.csv", "estado_sistema.json", "bitacora_robot.txt"]:
        urllib.request.urlretrieve(BASE + f, os.path.join(dest, f))
        print("ok", f, os.path.getsize(os.path.join(dest, f)))
    meta = subprocess.run(
        ["gh", "api", "repos/MendozaVolcanic/Mirova-v1/commits?per_page=1",
         "--jq", ".[0] | [.sha, .commit.committer.date] | @tsv"],
        capture_output=True, text=True).stdout.strip()
    with open(os.path.join(dest, "remoto_meta.txt"), "w", encoding="utf-8") as fh:
        fh.write(meta + "\n")
    print("remoto:", meta)


if __name__ == "__main__":
    main()
