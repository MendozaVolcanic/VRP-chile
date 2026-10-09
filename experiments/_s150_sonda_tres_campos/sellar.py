# -*- coding: utf-8 -*-
"""S150, sonda de los tres campos: sello del pre-registro.

POR QUE. El criterio de decision vive en DISENO.md y en evaluar.py, y la lista de pasadas en
pasadas.json y negativos_camino_d22.json. Si cualquiera de esos archivos cambia despues de ver datos, el
resultado deja de ser una prediccion. Este script escribe el sha256 de cada uno (con finales de linea LF,
para que Windows y Linux den lo mismo) en SELLO_PREREGISTRO.txt, y el workflow se niega a correr si el
sello no existe o no coincide.

  python sellar.py              escribe el sello (lo hace quien aprueba el pre-registro, DESPUES del verificador)
  python sellar.py --verificar  sale con 1 si falta el sello o algun archivo no coincide
"""
import argparse, hashlib, io, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
SELLO = AQUI / "SELLO_PREREGISTRO.txt"
ARCHIVOS = ["DISENO.md", "evaluar.py", "campos.py", "sonda.py", "seleccionar_pasadas.py",
            "pasadas.json", "negativos_camino_d22.json", "plantillas_tif.json"]


def h(nombre):
    return hashlib.sha256((AQUI / nombre).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--verificar", action="store_true"); a = ap.parse_args()
    if not a.verificar:
        SELLO.write_text("".join("%s  %s\n" % (h(n), n) for n in ARCHIVOS), encoding="utf-8")
        print(SELLO.read_text(encoding="utf-8"))
        return
    if not SELLO.exists():
        print("SIN SELLO: el pre-registro no esta aprobado; no se corre")
        sys.exit(1)
    esperado = dict(reversed(l.split()) for l in SELLO.read_text(encoding="utf-8").splitlines() if l.strip())
    mal = 0
    for n in ARCHIVOS:
        ok = esperado.get(n) == h(n)
        print(n, "COINCIDE" if ok else "NO COINCIDE")
        mal += not ok
    sys.exit(1 if mal else 0)


if __name__ == "__main__":
    main()
