# Tarea 1.23: reparto de la MISMA muestra de la 1.17 en 24 medios jobs.
#
# POR QUE. Con 22 brazos (C, M y 20 nulos) el job mas cargado de la 1.17 (Lascar, 48 granulos) se predice
# en 43 a 54 min (presupuesto_tiempo_salida.txt), demasiado cerca de un presupuesto de 70 min para el
# margen de A15. Partido en dos (granulos pares e impares del job original, en el orden de poblacion.json),
# el peor caso baja a 27 min. La muestra no cambia: la union de las dos mitades es el job original, sin
# repetidos (un test lo comprueba). El nombre de cada mitad es el del job de la 1.17 mas "a" o "b".
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
POBLACION = AQUI.parent / "_s151_mxd03_etiquetas" / "poblacion.json"


def partir(pob):
    """{nombre: {"volcan", "granulos", "origen"}} con cada job de la 1.17 en dos mitades."""
    out = {}
    for j, x in pob["jobs"].items():
        for sufijo, sel in (("a", x["granulos"][0::2]), ("b", x["granulos"][1::2])):
            if sel:
                out[j + sufijo] = {"volcan": x["volcan"], "granulos": list(sel), "origen": j}
    return out


def cargar(path=POBLACION):
    return json.loads(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    print(json.dumps(list(partir(cargar()))))
