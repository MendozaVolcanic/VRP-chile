# -*- coding: utf-8 -*-
"""
S133 - El flag del area geolocalizada tiene que tener consumidor en produccion.

FICHA SDA - test de guardia sobre el cableado de un parametro que, encendido, cambia la
magnitud del VRP reportado. No participa el mismo de la deteccion.

POR QUE ESTE TEST EXISTE: S132 construyo `pixel_areas_from_geolocation` y la probo contra
el ATBD, y definio el flag `ENABLE_GEOLOCATED_PIXEL_AREA` en el perfil. Las dos cosas
quedaron verdes y sin embargo el A/B de 3 brazos que se planifico no podia medir nada,
porque NADIE llamaba a la funcion ni leia el flag: el brazo "area" habria sido identico al
control. Un test que solo prueba la funcion aislada no detecta eso (leccion S130: la
pregunta previa a "mejora algo?" es "llega a ejecutarse?").

El chequeo se hace por AST y no por grep de texto, porque el nombre en el punto de uso no
tiene por que coincidir con el de la definicion (A89), y porque un grep cuenta como uso los
comentarios y los docstrings que solo lo mencionan.
"""
import ast
import glob
import os

import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FLAG = "ENABLE_GEOLOCATED_PIXEL_AREA"
FUNC = "pixel_areas_from_geolocation"


def _modulos_de_pipeline():
    return sorted(glob.glob(os.path.join(RAIZ, "pipeline", "**", "*.py"),
                            recursive=True))


def _analizar():
    """Devuelve (lecturas_del_flag, llamadas_a_la_funcion) como 'archivo:linea'."""
    lecturas, llamadas = [], []
    for ruta in _modulos_de_pipeline():
        rel = os.path.relpath(ruta, RAIZ).replace("\\", "/")
        with open(ruta, encoding="utf-8") as fh:
            try:
                arbol = ast.parse(fh.read(), filename=rel)
            except SyntaxError:
                continue
        for nodo in ast.walk(arbol):
            # Lectura del flag. La asignacion en profile.py es la DEFINICION y no cuenta
            # como consumo: por eso se descartan los contextos Store.
            if isinstance(nodo, ast.Name) and nodo.id == FLAG:
                if not isinstance(getattr(nodo, "ctx", None), ast.Store):
                    lecturas.append("%s:%d" % (rel, nodo.lineno))
            elif isinstance(nodo, ast.Attribute) and nodo.attr == FLAG:
                lecturas.append("%s:%d" % (rel, nodo.lineno))
            elif isinstance(nodo, ast.Call):
                f = nodo.func
                nombre = (f.id if isinstance(f, ast.Name)
                          else f.attr if isinstance(f, ast.Attribute) else None)
                if nombre == FUNC:
                    llamadas.append("%s:%d" % (rel, nodo.lineno))
    return sorted(set(lecturas)), sorted(set(llamadas))


def test_el_flag_del_area_tiene_consumidor_en_produccion():
    """Alguien en pipeline/ debe LEER el flag, aparte de definirlo en profile.py."""
    lecturas, _ = _analizar()
    fuera_de_profile = [x for x in lecturas if not x.startswith("pipeline/profile.py")]
    assert fuera_de_profile, (
        "%s se define pero no lo lee ningun modulo de produccion: el brazo 'area' del "
        "A/B seria identico al control. Cablearlo en process_viirs.py y "
        "process_viirs_mod.py." % FLAG)


def test_la_funcion_del_area_geolocalizada_se_llama_en_produccion():
    """La funcion medida contra el ATBD tiene que estar enchufada al procesador."""
    _, llamadas = _analizar()
    assert llamadas, (
        "%s no tiene ninguna llamada en pipeline/: esta construida y probada, pero "
        "desconectada del procesador." % FUNC)


def test_los_dos_procesadores_viirs_consumen_el_flag():
    """I-band y M-band calculan area por separado; cablear uno solo deja el otro mudo."""
    lecturas, _ = _analizar()
    archivos = {x.split(":")[0] for x in lecturas}
    faltan = {"pipeline/process_viirs.py", "pipeline/process_viirs_mod.py"} - archivos
    assert not faltan, (
        "estos procesadores VIIRS no leen %s: %s. Cada uno tiene su propia llamada a "
        "viirs_pixel_areas (process_viirs.py:710, process_viirs_mod.py:453)."
        % (FLAG, sorted(faltan)))


def test_el_modo_geolocalizado_no_pasa_por_el_tope_de_2x():
    """
    El tope de 2,0x de la rama lineal de viirs_pixel_areas viene de leer como factor de
    AREA el "approximately 2" que el ATBD da POR EJE (S131 §5). El area real crece 4,38x
    del nadir al borde, asi que ese tope estrangularia justo lo que se quiere medir. El
    modo geolocalizado tiene que ser una tercera opcion explicita, no un parametro que
    caiga dentro del modelo lineal.
    """
    from pipeline import scan_geometry

    fuente = open(scan_geometry.__file__, encoding="utf-8").read()
    arbol = ast.parse(fuente)
    fn = next((n for n in ast.walk(arbol)
               if isinstance(n, ast.FunctionDef) and n.name == "viirs_pixel_areas"), None)
    assert fn is not None, "no existe viirs_pixel_areas en scan_geometry"
    params = [a.arg for a in fn.args.args] + [a.arg for a in fn.args.kwonlyargs]
    assert "nadir_fixed" in params, "cambio la firma de viirs_pixel_areas"
    # El modo nuevo no puede colarse como un booleano mas dentro de la rama lineal:
    # si aparece un parametro de geolocalizacion aca, tiene que venir con su propia
    # rama de retorno y no multiplicando el factor topado.
    if any("geoloc" in p or "lat" in p for p in params):
        cuerpo = ast.get_source_segment(fuente, fn) or ""
        assert "np.minimum(factor, 2.0)" not in cuerpo.split("return")[-1], (
            "el modo geolocalizado esta cayendo dentro de la rama con tope 2,0x")


# ────────────────────────────────────────────────────────────────────
# El cableado tiene que ser un NO-OP con el flag apagado, y eso hay que probarlo.
# POR QUE: S126 dejo la leccion de que un no-op necesita un test — el PR #535 apago la
# mascara de nube en produccion creyendo que no cambiaba nada. Aca el flag arranca OFF y
# el NRT corre 12 veces al dia sobre 11 volcanes: si la rama OFF no fuera identica, el
# error se replicaria a cientos de records antes de que nadie lo note (A45).
# ────────────────────────────────────────────────────────────────────

def _grilla_sintetica(filas=12, cols=16, lat0=-39.42, lon0=-71.93, paso=0.0034):
    """Grilla regular chica; el paso ~0,0034 grados es del orden de 375 m."""
    import numpy as np
    f = np.arange(filas)[:, None] * paso
    c = np.arange(cols)[None, :] * paso
    lat = lat0 + f + 0.0 * c
    lon = lon0 + c + 0.0 * f
    zen = np.linspace(0.0, 60.0, cols)[None, :].repeat(filas, axis=0)
    return lat, lon, zen


@pytest.mark.parametrize("nadir_fixed", [True, False])
def test_con_el_flag_apagado_devuelve_exactamente_lo_de_antes(nadir_fixed):
    """La rama OFF tiene que ser identica bit a bit a llamar viirs_pixel_areas directo."""
    import numpy as np
    from pipeline.scan_geometry import viirs_pixel_areas, resolve_viirs_pixel_areas

    lat, lon, zen = _grilla_sintetica()
    nadir = 375.0 ** 2
    antes = viirs_pixel_areas(zen, nadir, nadir_fixed=nadir_fixed)
    ahora = resolve_viirs_pixel_areas(zen, nadir, lat, lon,
                                      geolocated=False, nadir_fixed=nadir_fixed)
    assert np.array_equal(antes, ahora), "la rama OFF dejo de ser un no-op"


def test_con_el_flag_encendido_usa_el_area_medida():
    """Encendido tiene que devolver la geolocalizacion, no el modelo."""
    import numpy as np
    from pipeline.scan_geometry import (pixel_areas_from_geolocation,
                                        resolve_viirs_pixel_areas)

    lat, lon, zen = _grilla_sintetica()
    medida = pixel_areas_from_geolocation(lat, lon)
    ahora = resolve_viirs_pixel_areas(zen, 375.0 ** 2, lat, lon,
                                      geolocated=True, nadir_fixed=True)
    finitos = np.isfinite(medida)
    assert finitos.any(), "la grilla sintetica no produjo areas validas"
    assert np.allclose(ahora[finitos], medida[finitos])


def test_la_geolocalizacion_invalida_cae_al_area_modelada_y_no_a_NaN():
    """
    Un NaN es lo correcto para analisis pero veneno en produccion: se propagaria a la
    magnitud y dejaria el record sin VRP. Los pixeles invalidos caen al area modelada,
    que es el mismo valor que tendrian con el flag apagado.
    """
    import numpy as np
    from pipeline.scan_geometry import viirs_pixel_areas, resolve_viirs_pixel_areas

    lat, lon, zen = _grilla_sintetica()
    lat = lat.copy(); lon = lon.copy()
    lat[5, 7] = np.nan
    lon[5, 7] = np.nan
    nadir = 375.0 ** 2
    modelada = viirs_pixel_areas(zen, nadir, nadir_fixed=True)
    ahora = resolve_viirs_pixel_areas(zen, nadir, lat, lon,
                                      geolocated=True, nadir_fixed=True)
    assert np.isfinite(ahora).all(), "quedaron NaN que llegarian a la magnitud"
    assert ahora[5, 7] == pytest.approx(modelada[5, 7])


def test_una_geolocalizacion_que_no_calza_es_error_y_no_un_reencuadre_inventado():
    import numpy as np
    from pipeline.scan_geometry import resolve_viirs_pixel_areas

    lat, lon, zen = _grilla_sintetica()
    with pytest.raises(ValueError, match="no calza"):
        resolve_viirs_pixel_areas(zen[:, :8], 375.0 ** 2, lat, lon,
                                  geolocated=True, nadir_fixed=True)


@pytest.mark.parametrize("modulo", ["pipeline.process_viirs",
                                   "pipeline.process_viirs_mod"],
                         ids=["iband", "mband"])
def test_el_flag_llega_hasta_calculate_vrp_y_no_solo_al_modulo(modulo):
    """
    Tripwire al estilo del de S103: no basta con importar el flag arriba del archivo, tiene
    que llegar a la funcion que calcula el VRP. Importarlo y no usarlo dejaria el flag
    muerto igual que si no existiera, y el A/B volveria a medir dos veces el control.

    La comprobacion exige frontera de palabra a proposito: `viirs_pixel_areas` es subcadena
    de `resolve_viirs_pixel_areas`, y una coincidencia de texto haria pasar el guard sin que
    el cableado exista. Ese falso verde ya ocurrio una vez, en el guard de S103, y por eso
    este test lo pide asi.
    """
    import importlib
    import inspect
    import re

    mod = importlib.import_module(modulo)
    src = inspect.getsource(mod.calculate_vrp)
    sin_espacios = re.sub(r"\s", "", src)

    assert re.search(r"(?<![A-Za-z0-9_])resolve_viirs_pixel_areas\s*\(", src), (
        "%s.calculate_vrp no llama resolve_viirs_pixel_areas()" % modulo)
    assert "geolocated=" + FLAG in sin_espacios, (
        "%s.calculate_vrp no pasa geolocated=%s: el flag quedaria muerto y el brazo "
        "'area' del A/B volveria a ser el control" % (modulo, FLAG))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
