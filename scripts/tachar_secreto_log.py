"""S169 ronda 2 (VV169-07): tacha el EARTHDATA_TOKEN en archivos que se suben como artefacto de un repo público.

POR QUÉ. El workflow de la sombra sube `pipeline.log` y `cobertura.json` como artefacto, y el repo es público. GitHub
enmascara los secretos en el VISOR de logs, no en un archivo escrito con `tee`. No se vio que el pipeline imprima el
token (grep de token, Bearer y Authorization en pipeline/fetch.py y en earthaccess 0.17.0, sólo loguea la fecha de
vencimiento a nivel info), pero el runner instala earthaccess sin versión fija y un mensaje de excepción podría
cambiar. Esto es la defensa barata: si el token aparece, se reemplaza por *** y se avisa, sin imprimirlo.

S169 ronda 3 (VR2-03): falla CERRADO. Si un archivo que existe no se puede leer o escribir, sigue con los demás y
sale con 1; el workflow sólo sube el artefacto si este paso salió bien (`steps.tachar.outcome == 'success'`). Tacha
también las variantes en que el token puede aparecer escrito: codificado como URL (quote y quote_plus) y escapado en
JSON (`\\/`). Con un JWT de Earthdata (base64url y puntos) esas variantes casi siempre son el mismo texto; se tachan
igual porque cuestan nada.

QUÉ HACE. Para cada archivo pasado que exista, reemplaza cada variante del valor de EARTHDATA_TOKEN (sin espacios ni
salto de línea al borde; si queda vacío no toca nada) por ***. Un archivo que no existe se salta. Nunca imprime el
valor. Salida 0 si todo lo que existía quedó revisado; 1 si algo no se pudo revisar.

Uso: python scripts/tachar_secreto_log.py pipeline.log cobertura.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import quote, quote_plus


def variantes(token):
    """El token y las formas en que puede aparecer escrito, de la más larga a la más corta."""
    vs = {token, quote(token, safe=""), quote_plus(token), json.dumps(token)[1:-1], token.replace("/", "\\/"),
          json.dumps(token)[1:-1].replace("/", "\\/")}
    return sorted(vs, key=len, reverse=True)


def main(argv=None):
    rutas = sys.argv[1:] if argv is None else argv
    token = (os.environ.get("EARTHDATA_TOKEN") or "").strip()
    if not token:
        print("sin EARTHDATA_TOKEN en el entorno: nada que tachar")
        return 0
    vs = variantes(token)
    fallo = False
    for r in rutas:
        p = Path(r)
        if not p.exists():
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
            n = 0
            for v in vs:
                n += txt.count(v)
                txt = txt.replace(v, "***")
            if n:
                p.write_text(txt, encoding="utf-8")
                print(f"::warning title=Token en {p.name}::{n} apariciones del token tachadas antes de subir el artefacto")
            else:
                print(f"{p.name}: sin el token")
        except Exception as e:  # noqa: BLE001  falla cerrado: cualquier cosa que impida revisar el archivo
            fallo = True
            print(f"::error title=No se pudo tachar {p.name}::{type(e).__name__}; el artefacto no se sube")
    return 1 if fallo else 0


if __name__ == "__main__":
    sys.exit(main())
