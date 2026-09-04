# -*- coding: utf-8 -*-
"""
S133 - Prueba diferencial del cableado del area contra origin/main.

FICHA SDA - script de verificacion read-only. No modifica datos ni pipeline.

POR QUE. La suite verde prueba que lo que TIENE test sigue andando; no prueba que el
camino operacional devuelva lo mismo que antes. Varias veces en este proyecto un arreglo
rompio otra cosa (A49: una insercion se comio el return de la funcion anterior y la suite
no lo vio; A50: se etiquetaron fallos como "pre-existentes" sin comparar contra main).
Asi que aca no se razona: se trae el codigo de origin/main, se corre al lado del actual
sobre las MISMAS entradas y se comparan los numeros.

Que se compara:
  1. `viirs_pixel_areas` vieja contra nueva - no la toque, debe dar identico bit a bit.
  2. `resolve_viirs_pixel_areas(geolocated=False)` contra la `viirs_pixel_areas` VIEJA -
     este es el invariante que importa: con el flag apagado el procesador tiene que
     calcular exactamente el area que calculaba antes del commit.
  3. Que el flag este efectivamente apagado en el perfil operacional.
  4. Que todos los modulos que importan lo que toque sigan importando.

Se barren tanto grillas al azar como los casos de borde (nadir puro, borde de swath,
angulos negativos, el tope de MAX_SENSOR_ZENITH_DEG) y las dos bandas.
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

NADIR = {"I-band(375m)": 375.0 ** 2, "M-band(750m)": 750.0 ** 2}


def _modulo_de_main():
    """Carga pipeline/scan_geometry.py tal como esta en origin/main, sin tocar el repo."""
    src = subprocess.run(
        ["git", "show", "origin/main:pipeline/scan_geometry.py"],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    tmp = os.path.join(tempfile.mkdtemp(), "scan_geometry_main.py")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(src)
    spec = importlib.util.spec_from_file_location("scan_geometry_main", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _casos_de_zenital():
    """Casos de borde primero, azar despues. Los bordes son donde rompen los cambios."""
    rng = np.random.default_rng(20260904)
    casos = {
        "nadir_puro": np.zeros((8, 10)),
        "borde_de_swath": np.full((8, 10), 70.0),
        "gradiente_completo": np.linspace(0, 70, 80).reshape(8, 10),
        "negativos": -np.linspace(0, 70, 80).reshape(8, 10),
        "sobre_el_tope": np.full((8, 10), 89.0),
        "mezcla_con_ceros": np.where(rng.random((8, 10)) < 0.3, 0.0,
                                     rng.uniform(0, 70, (8, 10))),
    }
    for i in range(6):
        casos["azar_%d" % i] = rng.uniform(0.0, 70.0, (12, 16))
    return casos


def main():
    viejo = _modulo_de_main()
    from pipeline import scan_geometry as nuevo

    filas = []
    todo_ok = True

    for banda, nadir_area in NADIR.items():
        for nombre, zen in _casos_de_zenital().items():
            # lat/lon coherentes con la forma, solo para alimentar la firma nueva
            f = np.arange(zen.shape[0])[:, None] * 0.0034
            c = np.arange(zen.shape[1])[None, :] * 0.0034
            lat = -39.42 + f + 0.0 * c
            lon = -71.93 + c + 0.0 * f

            for nadir_fixed in (True, False):
                a_viejo = viejo.viirs_pixel_areas(zen, nadir_area,
                                                  nadir_fixed=nadir_fixed)
                a_nuevo = nuevo.viirs_pixel_areas(zen, nadir_area,
                                                  nadir_fixed=nadir_fixed)
                a_resuelto = nuevo.resolve_viirs_pixel_areas(
                    zen, nadir_area, lat, lon,
                    geolocated=False, nadir_fixed=nadir_fixed)

                id_funcion = bool(np.array_equal(a_viejo, a_nuevo))
                id_camino = bool(np.array_equal(a_viejo, a_resuelto))
                todo_ok = todo_ok and id_funcion and id_camino
                filas.append({
                    "banda": banda, "caso": nombre, "nadir_fixed": nadir_fixed,
                    "viirs_pixel_areas_identica_a_main": id_funcion,
                    "camino_OFF_identico_a_main": id_camino,
                    "max_abs_dif": float(np.nanmax(np.abs(a_viejo - a_resuelto))),
                })

    # El flag operacional tiene que estar apagado.
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    from pipeline import profile as perfil
    flag_off = (perfil.ENABLE_GEOLOCATED_PIXEL_AREA is False)

    # Todo modulo que importe lo que toque tiene que seguir importando.
    modulos = ["pipeline.scan_geometry", "pipeline.process_viirs",
               "pipeline.process_viirs_mod", "pipeline.process_modis",
               "pipeline.store", "pipeline.f5_core"]
    importan = {}
    for m in modulos:
        try:
            __import__(m)
            importan[m] = True
        except Exception as exc:                       # noqa: BLE001
            importan[m] = "ERROR: %s" % exc
            todo_ok = False

    res = {
        "sesion": "S133",
        "proposito": "prueba diferencial del cableado del area contra origin/main",
        "comparaciones": filas,
        "n_comparaciones": len(filas),
        "todas_identicas": all(f["viirs_pixel_areas_identica_a_main"]
                               and f["camino_OFF_identico_a_main"] for f in filas),
        "flag_operacional_apagado": flag_off,
        "modulos_importan": importan,
        "veredicto": "SIN REGRESION" if (todo_ok and flag_off) else "REVISAR",
    }
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "regresion_diferencial_area.json")
    with open(destino, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, ensure_ascii=False)

    print("comparaciones:", res["n_comparaciones"],
          "| todas identicas a origin/main:", res["todas_identicas"])
    print("flag operacional apagado:", flag_off)
    print("modulos que importan bien:",
          sum(1 for v in importan.values() if v is True), "/", len(modulos))
    malos = [f for f in filas if not (f["viirs_pixel_areas_identica_a_main"]
                                      and f["camino_OFF_identico_a_main"])]
    if malos:
        print("DIFERENCIAS:")
        for f in malos[:10]:
            print("  ", f)
    print("VEREDICTO:", res["veredicto"])
    print("JSON:", destino)
    return 0 if res["veredicto"] == "SIN REGRESION" else 1


if __name__ == "__main__":
    sys.exit(main())
