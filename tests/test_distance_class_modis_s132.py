# -*- coding: utf-8 -*-
"""S132 — origen de `distance_class` en MODIS (decisión #4 de AUDIT_S131 §4).

EL FENÓMENO. `distance_class` decide si una detección se pinta como del cráter o como
lejana, y el dashboard la usa como compuerta: `mirovaEqVrp` devuelve 0 cuando la etiqueta
no es "summit". Hoy la etiqueta se deriva del `final_hotspot`, que en MODIS es el máximo
de radiancia MIR ABSOLUTA de la escena.

POR QUÉ ESO NO SIRVE A 1 KM. El campo crudo de MIR nocturno está dominado por el gradiente
de altitud, no por la actividad volcánica (A69): la cumbre nevada está fría y el valle de
baja altitud está tibio, así que el máximo absoluto se va al valle. A resolución de 1 km el
efecto es tan fuerte que el máximo cae a 21 km del cráter — y S131 midió que el máximo de
la propia escena de MIROVA cae a 20,8 km, con correlación 0,023 entre los dos. Es decir: a
1 km el MIR absoluto no ve el volcán tampoco para ellos. La etiqueta está anclada a un
punto que mide topografía.

LA CONSECUENCIA MEDIDA. En la banda de ≤ 2 km del cráter, 1.073 de 1.233 detecciones MODIS
(87 %) llevan `distance_class = far` y por lo tanto desaparecen del dashboard, aunque su
cúmulo esté sobre el edificio. No es un problema de detección: los cúmulos existen y la
detección viene de los paths contextuales de NTI/dNTI, no del MIR absoluto.

POR QUÉ VA TRAS FLAG Y NO SE PRENDE ACÁ. S113 cerró a propósito la cara far→summit del
bug A46 (guard unidireccional en `store.py`, ver A81): al medirla sobre VIIRS, el grueso
del flip era el artefacto topográfico de NdC, que no hay que destapar. La evidencia de
S131 es nueva y es específica de MODIS, así que el alcance correcto es MODIS y la decisión
del flip necesita el número de MODIS, no el de VIIRS. El flag existe para poder medirlo.
"""
import ast
import os

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_flag_arranca_apagado():
    from pipeline.profile import ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER
    assert ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER is False


def test_apagado_deriva_del_final_hotspot():
    from pipeline.process_modis import derivar_distance_class
    # hotspot lejano (máximo MIR en el valle), cúmulo sobre el cráter
    assert derivar_distance_class(final_dist_km=21.0, pc_dist_km=1.2, inner_km=5.0,
                                  desde_cluster=False) == "far"


def test_encendido_deriva_del_cumulo():
    from pipeline.process_modis import derivar_distance_class
    assert derivar_distance_class(final_dist_km=21.0, pc_dist_km=1.2, inner_km=5.0,
                                  desde_cluster=True) == "summit"


def test_encendido_no_inventa_summit_cuando_el_cumulo_tambien_esta_lejos():
    from pipeline.process_modis import derivar_distance_class
    assert derivar_distance_class(final_dist_km=21.0, pc_dist_km=18.0, inner_km=5.0,
                                  desde_cluster=True) == "far"


def test_encendido_sin_cumulo_cae_al_final_hotspot():
    """Sin centroide de cúmulo no hay de dónde derivar: se conserva el comportamiento viejo."""
    from pipeline.process_modis import derivar_distance_class
    assert derivar_distance_class(final_dist_km=1.0, pc_dist_km=None, inner_km=5.0,
                                  desde_cluster=True) == "summit"
    assert derivar_distance_class(final_dist_km=21.0, pc_dist_km=None, inner_km=5.0,
                                  desde_cluster=True) == "far"


def test_sin_inner_radius_no_hay_etiqueta():
    from pipeline.process_modis import derivar_distance_class
    assert derivar_distance_class(1.0, 1.0, None, True) is None
    assert derivar_distance_class(None, 1.0, 5.0, True) is None


def test_distance_class_no_se_lee_aguas_arriba_en_modis():
    """Prueba mecánica de que el cambio es SÓLO de etiqueta y no toca la selección de cúmulo.

    A18 exige reproc real cuando un parámetro puede mover `cluster_hotspots`. Acá no puede,
    y en vez de afirmarlo se verifica: en `process_modis.py` el nombre `distance_class`
    aparece únicamente como destino de asignación y como valor del dict de salida — nunca
    como lectura que alimente otra decisión. Si alguien agrega una lectura, este test cae y
    la conclusión "es sólo una etiqueta" deja de valer.

    Importa porque MODIS no corre en Windows (pyhdf) y el A/B tiene que poder hacerse sobre
    los records ya persistidos.
    """
    ruta = os.path.join(ROOT, "pipeline", "process_modis.py")
    with open(ruta, encoding="utf-8") as fp:
        arbol = ast.parse(fp.read())

    lecturas = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Name) and nodo.id == "distance_class" \
                and isinstance(nodo.ctx, ast.Load):
            lecturas.append(nodo.lineno)

    # La única lectura admisible es la que arma el dict de retorno.
    fuente = open(ruta, encoding="utf-8").read().splitlines()
    indebidas = [ln for ln in lecturas
                 if '"distance_class": distance_class' not in fuente[ln - 1]]
    assert not indebidas, (
        f"`distance_class` se lee aguas arriba en process_modis.py, líneas {indebidas}: "
        "el cambio ya no es sólo de etiqueta y el A/B necesita reproc real (A18)")
