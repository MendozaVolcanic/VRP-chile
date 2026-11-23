# -*- coding: utf-8 -*-
"""S196: arma el visor de radios del edificio a partir de plantilla_visor.html, datos_visor.json y fondos.json.

POR QUÉ dos salidas: Nicolás abre los HTML desde su disco (visor_radios.html, documento completo, con las imágenes en
fondos/ al lado), y el mismo contenido se publica como Artifact, donde la plataforma pone el esqueleto del documento y
el visor guarda los radios en su base de datos. Los datos van incrustados (no se piden con fetch) porque un HTML
abierto desde el disco no puede leer archivos vecinos con fetch.

Uso: python experiments/_s196_visor_radios/construir_visor.py [--artifact RUTA]
Salidas: experiments/_s196_visor_radios/visor_radios.html y, con --artifact, el cuerpo para publicar.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def json_en_script(obj) -> str:
    # Dentro de <script> un «<» podría cerrar la etiqueta: se escribe < (JSON válido igual).
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", default="")
    args = ap.parse_args()
    cuerpo = (AQUI / "plantilla_visor.html").read_text(encoding="utf-8")
    css = (AQUI / "vendor" / "leaflet-1.9.4.css").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s*\n\s*", "\n", css).strip()
    datos = json.loads((AQUI / "datos_visor.json").read_text(encoding="utf-8"))
    fondos = json.loads((AQUI / "fondos.json").read_text(encoding="utf-8"))
    for marca, valor in (("/*__LEAFLET_CSS__*/", css), ("/*__DATOS__*/", json_en_script(datos)),
                         ("/*__FONDOS__*/", json_en_script(fondos))):
        assert cuerpo.count(marca) == 1, marca
        cuerpo = cuerpo.replace(marca, valor)
    local = ("<!doctype html>\n<html lang=\"es-CL\">\n<head>\n<meta charset=\"utf-8\">\n"
             "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
             "<style>body{margin:0}[hidden]{display:none!important}</style>\n</head>\n<body>\n"
             + cuerpo + "\n</body>\n</html>\n")
    (AQUI / "visor_radios.html").write_text(local, encoding="utf-8", newline="\n")
    print("visor_radios.html", len(local.encode("utf-8")), "bytes")
    if args.artifact:
        Path(args.artifact).write_text(cuerpo, encoding="utf-8", newline="\n")
        print(args.artifact, len(cuerpo.encode("utf-8")), "bytes")


if __name__ == "__main__":
    main()
