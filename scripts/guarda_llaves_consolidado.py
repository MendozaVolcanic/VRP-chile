# -*- coding: utf-8 -*-
"""Guarda S160: el CSV consolidado de MIROVA no puede traer llaves repetidas.

POR QUÉ. Cada fila de la tabla de MIROVA es una pasada de un sensor sobre un volcán: la llave
(Volcan, Sensor, Fecha_Satelite_UTC) es única en el scraper. Una llave repetida no es dato, es
daño de la cadena de copias: el bucle de push con `git pull --rebase -X theirs` mezclaba como
texto tres permutaciones del archivo y dejaba filas dos veces o ninguna (commit 81dd25ce3,
822 llaves repetidas y 163 perdidas, reproducido byte a byte en la auditoría de Mirova-v1,
hallazgo H-V1). La pérdida de filas no se ve desde un solo archivo, pero los duplicados sí, y
salen juntos del mismo mecanismo: son el síntoma que se puede vigilar antes de empujar.

Instrumento ciego = rojo: archivo vacío, sin filas o sin las columnas de la llave dan exit 1,
porque una guarda que no puede mirar no puede dar verde (A116).

Uso: python scripts/guarda_llaves_consolidado.py latest_consolidado.csv
Salida: exit 0 si todas las llaves son únicas; exit 1 en cualquier otro caso.
"""
import csv
import io
import sys
from collections import Counter

LLAVE = ("Volcan", "Sensor", "Fecha_Satelite_UTC")


def revisar(ruta):
    with open(ruta, "rb") as fh:
        texto = fh.read().decode("utf-8", "replace")
    lector = csv.DictReader(io.StringIO(texto))
    faltan = [c for c in LLAVE if c not in (lector.fieldnames or [])]
    if faltan:
        print(f"ROJO: {ruta} sin las columnas de la llave {faltan} (cabecera: {lector.fieldnames})")
        return 1
    cuenta = Counter(tuple(f[c] for c in LLAVE) for f in lector)
    filas = sum(cuenta.values())
    if filas == 0:
        print(f"ROJO: {ruta} no tiene filas")
        return 1
    repetidas = {k: n for k, n in cuenta.items() if n > 1}
    sobrantes = sum(n - 1 for n in repetidas.values())
    if sobrantes:
        print(f"ROJO: {ruta} filas={filas} llaves={len(cuenta)} filas_sobrantes={sobrantes} "
              f"llaves_repetidas={len(repetidas)}")
        for k, n in list(repetidas.items())[:5]:
            print(f"  {n}x {k}")
        return 1
    print(f"VERDE: {ruta} filas={filas} llaves unicas={len(cuenta)}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(revisar(sys.argv[1]))
