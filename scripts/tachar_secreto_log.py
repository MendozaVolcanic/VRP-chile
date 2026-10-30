"""S169 ronda 2 (VV169-07): tacha el EARTHDATA_TOKEN en archivos que se suben como artefacto de un repo público.

POR QUÉ. El workflow de la sombra sube `pipeline.log` y `cobertura.json` como artefacto, y el repo es público. GitHub
enmascara los secretos en el VISOR de logs, no en un archivo escrito con `tee`. No se vio que el pipeline imprima el
token (grep de token, Bearer y Authorization en pipeline/fetch.py y en earthaccess 0.17.0, sólo loguea la fecha de
vencimiento a nivel info), pero el runner instala earthaccess sin versión fija y un mensaje de excepción podría
cambiar. Esto es la defensa barata: si el token aparece, se reemplaza por *** y se avisa, sin imprimirlo.

QUÉ HACE. Para cada archivo pasado que exista, reemplaza el valor literal de EARTHDATA_TOKEN (si viene no vacío) por
***. Un archivo que no existe se salta. Sale 0 siempre: el aviso va como ::warning:: y nunca repite el valor.

Uso: python scripts/tachar_secreto_log.py pipeline.log cobertura.json
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main(argv=None):
    rutas = sys.argv[1:] if argv is None else argv
    token = (os.environ.get("EARTHDATA_TOKEN") or "").strip()
    if not token:
        print("sin EARTHDATA_TOKEN en el entorno: nada que tachar")
        return 0
    for r in rutas:
        p = Path(r)
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        n = txt.count(token)
        if n:
            p.write_text(txt.replace(token, "***"), encoding="utf-8")
            print(f"::warning title=Token en {p.name}::{n} apariciones del token tachadas antes de subir el artefacto")
        else:
            print(f"{p.name}: sin el token")
    return 0


if __name__ == "__main__":
    sys.exit(main())
