"""S147 - el estadistico del Test 1 integrado, medido contra su propio nulo.

EL FENOMENO, PRIMERO. El Test 1 integrado suma el exceso de radiancia MIR de todos los
pixeles de un disco de 3 km alrededor del crater y pregunta si esa suma es "mucha". Para
saber si es mucha necesita una vara: cuanto valdria esa suma si no hubiera nada caliente,
solo el ruido del sensor y del terreno. Ahi esta el defecto (AUDIT_S146 V-06, D30): la suma
RECORTA los excesos negativos a cero (un volcan solo agrega calor, no lo quita), pero se
compara contra la desviacion de la suma SIN recortar. Al recortar, el ruido puro deja de
promediar cero: cada pixel aporta en promedio sigma/raiz(2 pi), y la suma de N pixeles crece
con N mientras la vara crece solo con raiz(N). El cociente vale 0,399 por raiz(N) y sigma se
cancela: el criterio termina midiendo EL TAMANO DEL DISCO, no el calor. Se cumple solo con
N mayor que 56,6, y el disco tiene ~200 pixeles en VIIRS 375 m.

LAS DOS PREGUNTAS DEL INSTRUMENTO (obligatorias, guia maestra de auditorias):
1. Si lo que mide estuviera completamente roto, esta prueba fallaria? SI: si el estadistico
   corregido no centrara el nulo, `test_ruido_puro_no_dispara_*` falla, porque mide el
   disparo sobre escenas donde por construccion NO hay nada caliente.
2. Si el instrumento mismo estuviera muerto (un estadistico que nunca dispara), el resultado
   se veria distinto? SI: `test_control_positivo_*` inyecta una fuente real y exige que
   dispare igual. Un "corregido" que apaga todo falla ese control.

La semilla esta fijada y ademas se barren 40 escenas, para que el veredicto no dependa del
azar de una sola (regla del workspace: una prueba con azar cambia de veredicto sola).
"""
from __future__ import annotations
import math

import numpy as np

from pipeline.test1_integrated import compute_test1_mir


# El nulo del estadistico recortado, derivado (X ~ N(0, sigma)):
#   E[max(0, X)]   = sigma / raiz(2 pi)          = 0.398942 sigma
#   Var[max(0, X)] = sigma^2 (1/2 - 1/(2 pi))    = 0.340845 sigma^2
_MEDIA_NULA_POR_PIXEL = 1.0 / math.sqrt(2.0 * math.pi)


def _grilla(n=20, vent_lat=0.0, vent_lon=0.0, pixel_km=0.375):
    """Grilla sintetica tipo VIIRS banda I centrada en el crater."""
    deg_por_km_lat = 1 / 111.0
    deg_por_km_lon = 1 / (111.0 * math.cos(math.radians(vent_lat)))
    mitad = (n - 1) / 2.0
    di = np.arange(n) - mitad
    dj = np.arange(n) - mitad
    dlat = di[:, None] * pixel_km * deg_por_km_lat
    dlon = dj[None, :] * pixel_km * deg_por_km_lon
    return vent_lat + dlat * np.ones((n, n)), vent_lon + dlon * np.ones((n, n))


def _escena_de_ruido(semilla, n=20, bt_fondo=265.0, sigma_bt=1.5):
    """Escena SIN nada caliente: fondo uniforme mas ruido gaussiano en temperatura."""
    rng = np.random.default_rng(semilla)
    return np.full((n, n), bt_fondo) + rng.normal(0.0, sigma_bt, size=(n, n))


def _corrido(bt, **kw):
    lat, lon = _grilla(bt.shape[0])
    base = dict(vent_lat=0.0, vent_lon=0.0, lambda_um=3.74, roi_km=3.0,
                inner_ring_km=1.0, k_sigma=3.0, mir_relative=0.02)
    base.update(kw)
    return compute_test1_mir(bt, lat, lon, **base)


# === 1. El defecto existe: linea base ROJA del estadistico de hoy ===

def test_ruido_puro_dispara_el_criterio_absoluto_de_hoy():
    """LINEA BASE. Con ruido puro el criterio absoluto de hoy se cumple casi siempre.

    No es un test de lo deseable: documenta el defecto para que el arreglo tenga contra que
    medirse. Si algun dia este test falla, el estadistico cambio y hay que revisar D30.
    """
    disparos = 0
    for semilla in range(40):
        r = _corrido(_escena_de_ruido(semilla))
        assert r["n_roi"] > 56.6, "la derivacion solo predice disparo con N > 56,6"
        disparos += int(r["abs_criterion"])
    assert disparos >= 38, f"esperaba casi 40 disparos con ruido puro, hubo {disparos}"


def test_el_valor_de_reposo_sigue_la_curva_derivada():
    """El k_sigma observado con ruido puro vale ~0,399 por raiz(N), no ~0."""
    observados = [_corrido(_escena_de_ruido(s))["k_sigma_observed"] for s in range(40)]
    r0 = _corrido(_escena_de_ruido(0))
    predicho = _MEDIA_NULA_POR_PIXEL * math.sqrt(r0["n_roi"])
    medido = float(np.mean(observados))
    assert abs(medido - predicho) / predicho < 0.15, (
        f"medido {medido:.3f} contra predicho {predicho:.3f}"
    )


# === 2. El arreglo: el estadistico corregido centra el nulo ===

def test_ruido_puro_no_dispara_con_el_estadistico_corregido():
    """Con `null_corrected=True`, una escena sin nada caliente no debe disparar."""
    disparos = 0
    for semilla in range(40):
        r = _corrido(_escena_de_ruido(semilla), null_corrected=True)
        disparos += int(r["abs_criterion"])
    assert disparos <= 2, f"esperaba a lo sumo 2 disparos de 40, hubo {disparos}"


def test_el_nulo_corregido_tiene_media_cero_y_desviacion_uno():
    """El control que valida al propio instrumento: sobre ruido puro, z ~ N(0,1)."""
    zs = [_corrido(_escena_de_ruido(s), null_corrected=True)["k_sigma_observed"]
          for s in range(40)]
    media = float(np.mean(zs))
    desv = float(np.std(zs, ddof=1))
    assert abs(media) < 1.0, f"media del nulo corregido {media:.3f}, deberia rondar 0"
    assert 0.3 < desv < 2.5, f"desviacion del nulo corregido {desv:.3f}, deberia rondar 1"


def test_el_umbral_corregido_no_depende_del_tamano_del_disco():
    """La firma del defecto era que el valor de reposo crecia con raiz(N). Ya no."""
    chico = [_corrido(_escena_de_ruido(s), null_corrected=True, roi_km=1.6)["k_sigma_observed"]
             for s in range(40)]
    grande = [_corrido(_escena_de_ruido(s), null_corrected=True, roi_km=3.0)["k_sigma_observed"]
              for s in range(40)]
    assert _corrido(_escena_de_ruido(0), roi_km=3.0)["n_roi"] > \
        3 * _corrido(_escena_de_ruido(0), roi_km=1.6)["n_roi"], "los discos deben diferir"
    assert abs(float(np.mean(grande)) - float(np.mean(chico))) < 1.0


# === 3. Control positivo: el corregido sigue viendo calor real ===

def test_control_positivo_una_fuente_sub_pixel_sigue_disparando():
    """Un foco real en el crater dispara igual con el estadistico corregido.

    Sin este control, un "arreglo" que simplemente nunca dispara pasaria los tests de arriba.
    """
    bt = _escena_de_ruido(7)
    centro = bt.shape[0] // 2
    bt[centro, centro] = 320.0          # foco sub-pixel tipo lago de lava
    bt[centro, centro + 1] = 300.0      # su vecino tibio
    r = _corrido(bt, null_corrected=True)
    assert r["abs_criterion"], "el estadistico corregido debe ver un foco real"
    assert r["k_sigma_observed"] > 3.0


def test_control_positivo_el_foco_sobresale_del_ruido():
    """El foco real queda MUY por encima del nulo; el ruido puro, no. Los dos, medidos."""
    bt = _escena_de_ruido(7)
    centro = bt.shape[0] // 2
    bt[centro, centro] = 320.0
    con_foco = _corrido(bt, null_corrected=True)["k_sigma_observed"]
    sin_foco = _corrido(_escena_de_ruido(7), null_corrected=True)["k_sigma_observed"]
    assert con_foco > sin_foco + 5.0, f"foco {con_foco:.2f} contra ruido {sin_foco:.2f}"


# === 4. El apagado es un no-op de verdad (regla S126: un no-op necesita su test) ===

def test_flag_apagado_es_identico_al_comportamiento_de_hoy():
    """Con el flag apagado, cada campo numerico sale identico a no pasar el argumento."""
    for semilla in (0, 1, 2):
        bt = _escena_de_ruido(semilla)
        antes = _corrido(bt)
        despues = _corrido(bt, null_corrected=False)
        for clave in ("delta_L_integrated", "sigma_delta_L_integrated", "k_sigma_observed",
                      "rel_observed", "L_bg", "sigma_bg", "n_roi", "n_bg", "n_contributing"):
            assert antes[clave] == despues[clave], f"difiere {clave} en la semilla {semilla}"
        assert antes["triggered"] == despues["triggered"]
        assert antes["abs_criterion"] == despues["abs_criterion"]
        assert np.array_equal(antes["mask_contributing"], despues["mask_contributing"])


def test_el_flag_no_toca_la_posicion_ni_los_pixeles_que_contribuyen():
    """El arreglo es de la VARA, no de que pixeles se suman: el centroide no se mueve."""
    bt = _escena_de_ruido(7)
    centro = bt.shape[0] // 2
    bt[centro, centro] = 320.0
    a = _corrido(bt)
    b = _corrido(bt, null_corrected=True)
    assert a["delta_L_integrated"] == b["delta_L_integrated"]
    assert a["n_contributing"] == b["n_contributing"]
    assert a["centroid_lat"] == b["centroid_lat"]
    assert a["centroid_lon"] == b["centroid_lon"]
