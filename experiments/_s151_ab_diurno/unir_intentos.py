# -*- coding: utf-8 -*-
"""Une los records de dos o más intentos del MISMO brazo y el mismo código (vuelta 68 del loop, 2026-10-16;
tolerancia numérica y píxel de borde en la vuelta siguiente, rama loop/unir-intentos-tolerancia).

Por qué se une: en W1 cada intento del brazo diurno perdió pasadas nocturnas distintas por caídas sueltas de
descarga, y repetir otra vez puede perder otra (decisión D-13 de Nicolás: los A/B largos se repiten y se unen
los intentos). Antes de unir hay que comprobar que en los gránulos comunes los dos intentos dicen LO MISMO: si
lo dicen, la unión es una corrida completa con el mismo código. Si no, no se une y se informa. En W1: 325
comunes, 0 distintos; la unión cubre las 183 noches del control.

Una sola regla en los dos modos (verificador del PR #841, vueltas 1 y 2): los comunes se clasifican SIEMPRE
con `comparar`, el predicado del tablero se corre sobre los de borde, y cualquier `distinto` que quede BLOQUEA.
Una diferencia de decisión entre dos corridas del mismo commit dice que los intentos no son del mismo código o
que el pipeline no es determinista en ese campo; en los dos casos el A/B pierde sentido, y `evaluar_fk.py` no
lee `_union_intentos`, así que informarla no basta. Sólo cuando no hay distintos cambia qué se entrega: si un
intento SOLO cubre todas las pasadas de la unión, ese intento ENTERO (el primero en el orden de la línea de
comandos, y sin pasadas repetidas), sin mezclar records de dos corridas en un archivo; si ninguno las cubre, la
mezcla record a record. Sobre V2a, 21 de 22 archivos tienen un intento completo.

Por qué no basta `!=` (medido en el A/B F/K V2a, run 38648773684, intento 1 y re-run sobre el MISMO commit):
en 8 de 22 archivos difieren TODOS los records comunes, y no por el código.
  1. Ruido de máquina. `diag_mu_deti` difiere hasta 5,1e-10 relativo (1,3e-15 absoluto) y `diag_sd_deti`
     hasta 4,0e-12 relativo: es la regresión del ETI (`np.polyfit`), que pasa por LAPACK de OpenBLAS y cambia
     los últimos bits según la CPU del runner. Mismo mecanismo que el G3 del evaluador diurno (#833), y la
     tolerancia es la suya: `REL_TOL, ABS_TOL = 1e-9, 1e-14`, comparada con math.isclose. El piso absoluto
     cubre los valores casi cero (mu del dETI) y está 11 órdenes bajo el umbral físico más fino del dETI
     (C1 = 3e-3); una diferencia de 1e-3 relativo sobre un valor de orden 1e-2 no pasa. Los enteros, bools,
     None y strings se comparan exactos. El test fija los dos lados (5e-10 une, 1e-3 no).
  2. Empates en el recorte de la lista de píxeles (lo que el código llama «borde»). En 11.642 records comunes,
     24 traen `anomaly_pixels` distinto: 9 sólo en el orden y 15 con otro conjunto, más 1 con sólo
     `discarded_anomaly_pixels` distinto. Ningún píxel cruza un umbral: la máscara de detección es la misma
     en los dos intentos (`n_anomalous_pixels`, de 273 a 789, y `primary_cluster` idénticos). Lo que cambia
     es cuáles entran a la lista guardada, que se recorta a los 100 de mayor VRP con
     `np.argsort(-per_pixel_vrp_mw)[:100]` (`pipeline/process_modis.py:1085`), un orden NO estable: en los 16
     casos la lista mide exactamente 100 y cada píxel que entra o sale tiene el mismo `vrp_mw` que el mínimo
     de la lista, valor que comparten de 1 a 45 píxeles (se intercambian hasta 8 por lado). Después
     `pipeline/store.py:285-301` reparte esa lista por distancia y recalcula `vrp_mir_mw` y `hotspot_*`, y de
     ahí salen los derivados distintos. Dos records (Isluga MODIS_TERRA 2026-03-28 01:15 y Chillán MODIS_AQUA
     2026-04-17 07:30) tienen además un empate en el MÁXIMO (dos píxeles de 3,3930 y de 2,6865 MW): el que el
     sort deja primero pasa a `final_hotspot`, y con él la geometría de visión evaluada ahí, incluido
     `sensor_zenith_deg`, que en MODIS es derivado (ver abajo). Todos son MODIS del control, `far`, topados en
     5,0 MW.
     SOSPECHA no verificada: que el orden de los empates cambie con la CPU por el despacho SIMD del sort de
     numpy, el mismo patrón que OpenBLAS en el ETI. (Medido por el verificador del PR #841, `a3_empates.py`.)

Regla de comparación de un record común (`comparar`):
  * igual / tolerancia / orden: idéntico, idéntico salvo floats dentro de la tolerancia, o idéntico salvo el
    orden de las listas de píxeles (se comparan como multiconjunto, con la misma tolerancia). Une.
  * borde: alguna lista de píxeles difiere como conjunto. Une SÓLO si (a) todo campo de CAMPOS_DECISION es
    igual dentro de la tolerancia; (b) todo otro campo distinto está en DERIVADOS_DEL_BORDE (lista cerrada);
    (c) el tablero no lee los píxeles para ese record (VIIRS 375 sin `f5_core_vrp_mw` sí los lee); y (d) el
    predicado del tablero ejecutado con node (A97, `scripts/banco_paridad.py::correr_node`, con el mismo
    record recortado que le pasan los evaluadores) da lo mismo con los dos records. Cada unión de este tipo
    se informa record por record, por stdout y en la clave `_union_intentos` del JSON de salida.
  * hotspot_escena (decisión D-16 a de Nicolás, 2026-10-17): sólo MODIS, misma BT máxima de escena (`t_max_k`
    presente en los dos e igual), mismo cúmulo (presente), misma clase y los mismos píxeles (como conjunto, o
    distintos sólo por la regla de borde), y los únicos campos distintos están en CAMPOS_HOTSPOT_ESCENA (lista
    cerrada). Si cambian `final_hotspot_source`, `discarded_reason` o `vrp_mw`, tiene que ser exactamente el
    rescate por cúmulo de `pipeline/store.py:390-422` (un solo lado `cluster_rescue`, con su etiqueta y con
    `vrp_mw` igual a `pc.vrp_mw`). Además (verificador del PR #843): (a) la geometría de visión, el ancla final
    y `hotspot_dist_km` sólo cambian si se movió `hotspot_lat/lon`; (b) el ancla final sólo cambia con el
    rescate, o con la misma fuente y final == hotspot en los dos lados (rama eruption); (c) en el lado rescatado
    `hotspot_*` es el centroide del cúmulo (`store.py:397-399`). Lo que estas reglas NO acotan, porque el record no
    guarda con qué compararlo: el `vrp_mw` del lado no rescatado (la suma de escena del Test 1) y la distancia del
    hotspot del lado no rescatado (el `max_hotspot_dist_km` del volcán no viaja en el record). Ninguno de los dos
    lo lee un evaluador de F/K; el predicado del tablero lee `vrp_mw` sólo cuando vale 0 (frontend/index.html:1596).
    El predicado del tablero con node tiene que dar lo mismo, como en el borde.
    Se une conservando el record que entrega la unión (`conservado`: el del primer intento en la mezcla, el del
    intento entero si lo hay) y cada caso se lista con los valores de los dos lados, por stdout y en
    `_union_intentos["hotspot_escena"]`.
  * distinto: cualquier otra diferencia. Bloquea la unión, como en la vuelta 68.

El fenómeno de hotspot_escena (medido en F/K V1, run 38639658446, Llaima control, y en diurno W2a, run
38853230521, Copahue `_s151_ab_diurno_on`): `hotspot_*` es el primer píxel de `np.argsort(-per_pixel_vrp_mw)` de
la PRIMERA pasada (`pipeline/process_modis.py:1085-1099`); en los records del Test 1 esa lista se reemplaza
después (l. 1399) y no queda guardada. Entre dos corridas del mismo commit ese primer píxel cambia con la misma
`t_max_k` y el mismo `diag_t_max_dist_km` (el `np.nanargmax` de la l. 1218 da lo mismo en los dos intentos, así que
no es él). Cuando el píxel elegido cae más allá de `max_hotspot_dist_km`, el rescate reescribe el ancla, la fuente,
la etiqueta y el `vrp_mw`. SOSPECHA no verificada: empate de VRP por píxel (con área nadir fija y fondo global, dos
píxeles con la misma BT dan el mismo VRP) que el sort SIMD de numpy ordena distinto según la CPU, como en el borde.

Qué magnitud y qué campos leen los evaluadores (condición 5 de D-16 a; leído en el código, no supuesto):
  * `evaluar_fk.py`: P3 (razón de magnitud, l. 379-389) usa `disp`, que sale de `armar_tabla.py:44` y viene de
    `_s146_ab_sin_test1/evaluar.py:105`, o sea la 4.ª salida del predicado del tablero (`mirovaEqVrpDisplay`,
    `scripts/banco_paridad.py:129`). En MODIS con cúmulo eso es `pc.vrp_mw` (frontend/index.html:1148, 1164 y
    1289): el `vrp_mw` del record NO entra. P1, P2 y el gemelo usan `pub` (la 5.ª salida); el movimiento usa
    `pc_lat`/`pc_lon` (evaluar_fk.py:403); `crudos` (l. 145) lee `product_version` y `triggered_test1`. Nada de
    eso cambia en hotspot_escena (cúmulo igual, y el predicado se comprueba con node).
  * `evaluar_diurno.py`: M1 a M4 usan `pub` (l. 269). Pero el G3 (`noches_identicas`, l. 404-420) compara el
    record crudo de control y diurno campo a campo, y SÍ lee `vrp_mw`, `hotspot_*`, `final_hotspot_*` y
    `discarded_reason`. No se bloquea por eso, se propaga: el G3 no lee `_union_intentos`, así que en una noche
    con hotspot_escena su veredicto depende de qué record conserva la unión. Medido en W2a Copahue 2026-06-18
    07:30 MODIS_AQUA: con el intento 1 primero, el record conservado coincide con el control y el G3 no ve nada;
    con el orden invertido, ve 9 campos distintos en esa noche y daría FALLA. El mismo empate entre los jobs de
    los dos brazos produce eso sin unión de por medio: es el mismo pendiente del G3 que la comparación posicional
    de píxeles (abajo), y se arregla en el evaluador, no aquí.
    RESUELTO por la desviación D2 del pre-registro (rama loop/diurno-g3-comparar, 2026-10-17): el G3 ya clasifica
    cada par nocturno con `comparar()` más `_predicado` (evaluar_diurno.py, `noches_identicas`); `distinto` hace
    FALLA y `orden`, `borde` y `hotspot_escena` se informan aparte. Sobre W2 unido en los dos órdenes da el mismo
    veredicto. El texto que sigue se conserva por historia.
    REGLA DE USO (verificador del PR #843): el G3 del diurno compara el record crudo, por posición en las listas,
    y no lee `_union_intentos`. Por eso el diurno NO se evalúa sobre una unión que tenga casos `hotspot_escena`,
    `borde` u `orden` hasta que el G3 clasifique cada par nocturno con `comparar()` más el predicado del tablero
    (`distinto` hace FALLA; los otros se cuentan aparte). Ese cambio del evaluador es desviación del pre-registro
    y va registrado en su propio PR. F/K sí puede usar estas uniones: sus métricas no leen esos campos.

CAMPOS_DECISION sale de leer los consumidores, no de adivinar (A89):
  * `scripts/banco_paridad.py:136` CAMPOS_JS, lo que se le pasa al predicado del tablero: primary_cluster
    (entero, incluye n_pixels del filtro de campo difuso y centroid_* del corte por inner), distance_class,
    vrp_mw, discarded_reason, triggered_test1, vrp_vent_mw, t_max_k, sensor, f5_core_vrp_mw. Dos van con
    condición, porque el predicado sólo los lee en un caso: anomaly_pixels cuando f5_core_vrp_mw es None
    (banco_paridad.py:284) y el sensor es VIIRS 375 (frontend/index.html:1238 y 1289); vrp_mir_mw cuando el
    record no tiene primary_cluster ni vrp_mw (`r.vrp_mw ?? r.vrp_mir_mw`, frontend/index.html:1148-1149).
    Fuera de esos casos son derivados del píxel de borde (vrp_mir_mw es la suma MIR de los píxeles).
  * sensor_zenith_deg decide SÓLO en VIIRS 375 y por eso va en DERIVADOS_DEL_BORDE con condición (grep de
    `"z"`, `zbin` y `sensor_zenith` en la cadena, vuelta 2 del verificador): `scripts/banco_paridad.py:282` y
    `_s146_ab_sin_test1/evaluar.py:91` lo copian como «z»; su único lector en banco_paridad es
    `cenital_neg_v375` (l. 464-469), que filtra `r["b"] == "VIIRS375"`; `armar_tabla.py:45` lo entrega y
    `evaluar_fk.py` no lo lee (0 usos). Fuera de la cadena F/K, `_s149_prereg_invierno/medir_predicciones.py:12
    y 31` arma la zona del barrido para el sensor que recibe por argumento (VIIRS375 por defecto): si alguien
    lo corre con MODIS sobre una unión con un record de borde, ese record trae el cenit del intento entregado.
  * `experiments/_s146_ab_sin_test1/evaluar.py:92-96` final_hotspot_source, n_anomalous_pixels (decide en las
    l. 372 y 378) y granule; ese cargador es el de `armar_tabla.py`, que es el de `evaluar_fk.py`.
  * `experiments/_s151_prereg_fk_11/evaluar_fk.py:145` product_version y triggered_test1.
  * `experiments/_s151_ab_diurno/evaluar_diurno.py:261` diag_umbrales_diurnos; l. 417 product_version y granule.
  * datetime_utc y sensor van además en la clave.
La clave es la PASADA, (sensor, datetime_utc al minuto), igual que agrupan los evaluadores
(`_s146_ab_sin_test1/evaluar.py:109-110`, `evaluar_diurno.py:253`), no el gránulo. Con el gránulo en la clave
(vuelta 68), la misma pasada con otro gránulo o versión (NRT contra estándar, o un reproceso de NASA entre
intentos) salía dos veces y `armar_tabla.py:43` se quedaba en silencio con la última. Ahora se comparan, y
`granule` y `product_version` distintos son una diferencia que bloquea la mezcla.
Nota de diseño: CAMPOS_DECISION y DERIVADOS_DEL_BORDE son disjuntos (se comprueba al importar), así que en un
record de borde quien bloquea es la lista cerrada de derivados: todo campo distinto que no esté en ella
bloquea. CAMPOS_DECISION documenta de dónde sale cada campo; agregarle uno no cambia la regla.
Estándar incoherente RESUELTO por la desviación D2 (ver arriba); texto original por historia: el G3 de `evaluar_diurno.py:386-401 y 420` compara las listas de
píxeles POSICIONALMENTE, así que marcaría como diferencia los 8 records de orden y los 14 de borde que esta
herramienta declara «mismo pipeline» (`verif_841/a4_g3.py`). No lo crea la unión: entre los dos brazos, que
son jobs distintos, el mismo empate del sort puede dar FALLA de G3. `evaluar_fk.py` no tiene G3 campo a campo.

Resultado sobre V2a: ver el informe del PR (se vuelve a correr en cada cambio, no se fija aquí).

En la mezcla, para los records comunes se conserva el del PRIMER intento en el orden de la línea de comandos
(determinista); los que sólo están en un intento posterior se agregan. Los metadatos del documento salen del
primer intento. Con un intento entero, todo (records y metadatos) sale de ese intento.

Uso: python unir_intentos.py --out <json> [--volcan V] <intento1.json> <intento2.json> [...]
Sale con 1 si no une; con 0 si une.
"""
import argparse
import json
import math
import sys
from pathlib import Path

PROCESO = {"processed_utc", "first_processed_utc", "regimen", "updated"}
REL_TOL, ABS_TOL = 1e-9, 1e-14          # = G3_REL_TOL, G3_ABS_TOL de evaluar_diurno.py (el test lo vigila)
LISTAS_PIXELES = ("anomaly_pixels", "discarded_anomaly_pixels")
CAMPOS_DECISION = {
    "primary_cluster": "banco_paridad.py:136 (predicado)", "distance_class": "banco_paridad.py:136",
    "vrp_mw": "banco_paridad.py:136",
    "discarded_reason": "banco_paridad.py:136", "triggered_test1": "banco_paridad.py:136, evaluar_fk.py:145",
    "vrp_vent_mw": "banco_paridad.py:136", "t_max_k": "banco_paridad.py:136", "sensor": "banco_paridad.py:136",
    "f5_core_vrp_mw": "banco_paridad.py:136",
    "final_hotspot_source": "_s146_ab_sin_test1/evaluar.py:92", "n_anomalous_pixels": "evaluar.py:95",
    "granule": "evaluar.py:96, evaluar_diurno.py:417", "product_version": "evaluar_fk.py:145",
    "diag_umbrales_diurnos": "evaluar_diurno.py:261", "datetime_utc": "clave",
}
# Lo que se calcula desde el conjunto de píxeles y ningún consumidor lee (grep de los cinco consumidores de
# arriba: 0 usos). Lista CERRADA: un campo nuevo que difiera en un record de borde bloquea hasta que se agregue
# aquí con su razón.
DERIVADOS_DEL_BORDE = {
    "anomaly_pixels": "la lista misma", "discarded_anomaly_pixels": "la lista de descartados",
    "discarded_n_pixels": "conteo de descartados",
    "hotspot_lat": "píxel más caliente", "hotspot_lon": "píxel más caliente", "hotspot_dist_km": "píxel más caliente",
    "final_hotspot_lat": "píxel más caliente", "final_hotspot_lon": "píxel más caliente",
    "final_hotspot_dist_km": "píxel más caliente",
    "sensor_azimuth_deg": "geometría en el hotspot", "solar_zenith_deg": "geometría en el hotspot",
    "solar_azimuth_deg": "geometría en el hotspot",
    # va en CAMPOS_JS, pero el predicado sólo lo lee como respaldo de `r.vrp_mw ?? r.vrp_mir_mw` cuando el
    # record NO tiene primary_cluster (frontend/index.html:1148-1149); en ese caso decide y bloquea (comparar)
    "vrp_mir_mw": "suma de VRP MIR de los píxeles",
    # geometría de visión en el píxel más caliente; decide sólo en VIIRS 375 (banco_paridad.py:464-469), ahí bloquea
    "sensor_zenith_deg": "geometría en el hotspot",
}
_VIIRS375 = ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21")
assert not set(CAMPOS_DECISION) & set(DERIVADOS_DEL_BORDE), "un campo no puede decidir y ser derivado a la vez"

# D-16 a (Nicolas, 2026-10-17): lo que cambia cuando el pixel mas caliente de la primera pasada MODIS cae en otro
# lugar entre dos corridas del mismo commit. Lista CERRADA, igual que DERIVADOS_DEL_BORDE: cualquier otro campo
# distinto bloquea, y eso es lo que exige que la BT maxima, la clase, el cumulo, los pixeles (como conjunto o por
# la regla de borde), el Test 1, la version y el granulo sean iguales. Cuatro campos de aca deciden en otra parte
# (CAMPOS_DECISION) y por eso entran con condiciones (`motivo_no_escena`) y con el predicado del tablero.
CAMPOS_HOTSPOT_ESCENA = {
    "hotspot_lat": "primer pixel de argsort(-vrp) de la primera pasada (process_modis.py:1085-1099)",
    "hotspot_lon": "idem", "hotspot_dist_km": "idem",
    "final_hotspot_lat": "con el rescate, el centroide del cumulo (store.py:407-409)",
    "final_hotspot_lon": "idem", "final_hotspot_dist_km": "idem",
    "final_hotspot_source": "test1 contra cluster_rescue (store.py:410); evaluar.py:92 lo copia como `fuente` y "
                            "sólo lo imprime posicion_cumulo (evaluar.py:317), que evaluar_fk.py no llama",
    "discarded_reason": "la etiqueta del rescate (store.py:422); el predicado la lee sólo con vrp_mw 0 "
                        "(frontend/index.html:1596)",
    "vrp_mw": "con el rescate pasa a ser pc.vrp_mw (store.py:396 y 456); el tablero publica pc.vrp_mw cuando hay "
              "cumulo (frontend/index.html:1148 y 1164)",
    "sensor_zenith_deg": "geometria en el hotspot; en MODIS ningun evaluador la lee (banco_paridad.py:464-469)",
    "sensor_azimuth_deg": "idem", "solar_zenith_deg": "idem", "solar_azimuth_deg": "idem",
}
_RESCATE = "single_pixel_far_overridden_by_cluster"
_CAMPOS_DEL_RESCATE = {"final_hotspot_source", "discarded_reason", "vrp_mw"}
_AUSENTE = "<ausente>"
_HOTSPOT = ("hotspot_lat", "hotspot_lon", "hotspot_dist_km")
_ANCLA_FINAL = {"final_hotspot_lat", "final_hotspot_lon", "final_hotspot_dist_km"}
# lo que se evalua en el hotspot o lo sigue: no puede cambiar si el hotspot no se movio (verificador del PR #843, a)
_SIGUEN_AL_HOTSPOT = _ANCLA_FINAL | {"hotspot_dist_km", "sensor_zenith_deg", "sensor_azimuth_deg",
                                     "solar_zenith_deg", "solar_azimuth_deg"}


def _rescate_coherente(a, b):
    """True si la diferencia de fuente, etiqueta y magnitud es exactamente el rescate por cumulo de store.py:390-422:
    un solo lado es `cluster_rescue`, con la etiqueta del rescate y vrp_mw igual al del cumulo; el otro no trae
    etiqueta de descarte."""
    lados = [r for r in (a, b) if r.get("final_hotspot_source") == "cluster_rescue"]
    if len(lados) != 1:
        return False
    r = lados[0]
    otro = b if r is a else a
    if r.get("discarded_reason") != _RESCATE:
        return False
    if otro.get("discarded_reason") is not None:
        return False
    return iguales(r.get("vrp_mw"), (r.get("primary_cluster") or {}).get("vrp_mw"))


def _final_es_hotspot(a, b):
    """Misma fuente en los dos lados y ancla final == hotspot en cada uno: la rama `eruption` de
    process_modis.py:1307-1310, donde el ancla final sigue al hotspot."""
    return all(a.get("final_hotspot_source") == b.get("final_hotspot_source") and
               all(iguales(r.get("final_" + c), r.get(c)) for c in _HOTSPOT) for r in (a, b))


def _hotspot_en_el_cumulo(r):
    """El rescate escribe el centroide del cumulo en hotspot_* (store.py:397-399)."""
    pc = r.get("primary_cluster") or {}
    return all(iguales(r.get(c), pc.get(c.replace("hotspot", "centroid"))) for c in _HOTSPOT)


def motivo_no_escena(a, b, dif):
    """None si el par puede ser `hotspot_escena`; si no, la razon. `dif` son los campos distintos (sin las listas de
    pixeles). La igualdad de BT maxima, clase y cumulo la impone la lista cerrada: aca va lo que la lista no ve."""
    if not str(a.get("sensor") or "").startswith("MODIS_"):
        return "sensor no MODIS: el fenomeno medido es del MODIS (D-16)"
    if a.get("t_max_k") is None or b.get("t_max_k") is None:
        return "sin BT maxima de escena"
    if not a.get("primary_cluster"):
        return "sin cumulo: el tablero publicaria vrp_mw (frontend/index.html:1148-1149)"
    rescate = _CAMPOS_DEL_RESCATE & set(dif)
    if rescate and not _rescate_coherente(a, b):
        return "%s distintos sin el rescate por cumulo de store.py:390-422" % sorted(rescate)
    # verificador del PR #843: (a) la geometria y el ancla final siguen al hotspot; (b) el ancla final sólo
    # cambia con el rescate, o en la rama eruption (misma fuente, final == hotspot); (c) el lado rescatado tiene
    # el hotspot en el centroide del cumulo
    d = set(dif)
    movio = bool({"hotspot_lat", "hotspot_lon"} & d)
    if (d & _SIGUEN_AL_HOTSPOT) and not movio:
        return "%s distintos sin que se mueva el hotspot" % sorted(d & _SIGUEN_AL_HOTSPOT)
    if (d & _ANCLA_FINAL) and not (_rescate_coherente(a, b) or _final_es_hotspot(a, b)):
        return "ancla final distinta sin rescate ni fuente eruption con final == hotspot"
    for r in (a, b):
        if r.get("final_hotspot_source") == "cluster_rescue" and not _hotspot_en_el_cumulo(r):
            return "rescate con el hotspot fuera del centroide del cumulo (store.py:397-399)"
    return None


def clave(r):
    """La pasada, como la agrupan los evaluadores: (sensor, minuto). Sin el gránulo (verificador del PR #841)."""
    return (r.get("sensor"), (r.get("datetime_utc") or "")[:16])


def iguales(a, b):
    """Igualdad con tolerancia: floats con math.isclose(REL_TOL, ABS_TOL), resto exacto; recursiva en listas y
    dicts (posicional en listas; las listas de píxeles se comparan aparte como multiconjunto)."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, int) and isinstance(b, int):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
            return True
        return math.isclose(a, b, rel_tol=REL_TOL, abs_tol=ABS_TOL)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(iguales(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(iguales(x, y) for x, y in zip(a, b))
    return a == b


def mismo_multiconjunto(a, b):
    """True si las dos listas tienen los mismos elementos (dentro de la tolerancia) en cualquier orden."""
    a, b = list(a or []), list(b or [])
    if len(a) != len(b):
        return False
    libres = list(range(len(b)))
    for x in a:
        for j, i in enumerate(libres):
            if iguales(x, b[i]):
                del libres[j]
                break
        else:
            return False
    return True


def comparar(a, b):
    """Estado de un record común: ('igual'|'tolerancia'|'orden'|'borde'|'distinto', detalle)."""
    x = {c: v for c, v in a.items() if c not in PROCESO}
    y = {c: v for c, v in b.items() if c not in PROCESO}
    if x == y:
        return "igual", {}
    campos = sorted(set(x) | set(y))
    # un campo presente en un intento y ausente en el otro es diferencia, aunque valga None o []
    no_tol = [c for c in campos if (c in x) != (c in y) or
              (c not in LISTAS_PIXELES and not iguales(x.get(c), y.get(c)))]
    orden = [c for c in LISTAS_PIXELES if c in x and c in y and not iguales(x[c], y[c])]
    conjunto = [c for c in orden if not mismo_multiconjunto(x.get(c), y.get(c))]
    if not no_tol and not conjunto:
        return ("orden" if orden else "tolerancia"), {"listas_reordenadas": orden}
    motivo = motivo_no_escena(a, b, no_tol)

    def por_borde(c):
        return bool(conjunto) and c in DERIVADOS_DEL_BORDE and c not in CAMPOS_DECISION

    def por_escena(c):
        return motivo is None and c in CAMPOS_HOTSPOT_ESCENA
    if not conjunto and not any(por_escena(c) for c in no_tol):
        det = {"campos": no_tol}
        if any(c in CAMPOS_HOTSPOT_ESCENA for c in no_tol) and motivo:
            det["no_es_hotspot_escena"] = motivo
        return "distinto", det
    # borde: decide la lista de decisión, la lista cerrada de derivados y si el tablero lee los píxeles;
    # hotspot_escena (D-16 a): la otra lista cerrada, sólo si motivo_no_escena no puso reparos
    bloquean = [c for c in no_tol if not (por_borde(c) or por_escena(c))]
    if a.get("sensor") in _VIIRS375 and a.get("f5_core_vrp_mw") is None and "anomaly_pixels" in conjunto:
        bloquean.append("anomaly_pixels")
    if "vrp_mir_mw" in no_tol and not (a.get("primary_cluster") and a.get("vrp_mw") is not None):
        bloquean.append("vrp_mir_mw")
    if "sensor_zenith_deg" in no_tol and a.get("sensor") in _VIIRS375:
        bloquean.append("sensor_zenith_deg")
    det = {"pixeles": {c: [len(x.get(c) or []), len(y.get(c) or [])] for c in conjunto},
           "campos_derivados": [c for c in no_tol if c not in bloquean]}
    if bloquean:
        det["campos"] = sorted(set(bloquean))
        if any(c in CAMPOS_HOTSPOT_ESCENA for c in bloquean) and motivo:
            det["no_es_hotspot_escena"] = motivo
        return "distinto", det
    escena = [c for c in no_tol if por_escena(c) and not por_borde(c)]
    if escena or not conjunto:
        det["campos"] = sorted(no_tol)
        det["valores"] = {c: [x.get(c, _AUSENTE), y.get(c, _AUSENTE)] for c in sorted(no_tol)}
        return "hotspot_escena", det
    return "borde", det


def _predicado(pares, volcan):
    """Predicado del tablero (frontend/index.html con node) sobre (record1, record2), con el mismo recorte que
    le hacen los evaluadores (banco_paridad.py:283-286). Devuelve la lista de índices donde difiere."""
    raiz = Path(__file__).resolve().parents[2]
    for p in (str(raiz), str(raiz / "scripts")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import banco_paridad as bp
    inner = bp.inner_desde_html()[volcan]

    def slim(r):
        s = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
        if r.get("f5_core_vrp_mw") is None:
            s["anomaly_pixels"] = [{k: q.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                   for q in (r.get("anomaly_pixels") or [])]
        return s
    casos = [[slim(r), inner] for par in pares for r in par]
    out = bp.correr_node(casos)
    return [i for i in range(len(pares)) if out[2 * i] != out[2 * i + 1]]


def unir(docs, volcan):
    """(salida o None, informe). Clasifica los comunes, corre el predicado sobre los de borde y bloquea ante
    cualquier distinto, en los dos modos. Sin distintos entrega el intento que cubre todas las pasadas, entero,
    o si no hay ninguno, la mezcla conservando el record del primer intento."""
    union, origen = {}, {}
    estados = {e: 0 for e in ("igual", "tolerancia", "orden", "borde", "hotspot_escena", "distinto")}
    distintos, borde, escena, nuevos = [], [], [], []
    for i, d in enumerate(docs):
        n = 0
        for r in d["records"]:
            k = clave(r)
            if k not in union:
                union[k], origen[k] = r, i
                n += 1
                continue
            est, det = comparar(union[k], r)
            estados[est] += 1
            if est == "distinto":
                distintos.append(dict(det, clave=list(k), intentos=[origen[k] + 1, i + 1]))
            elif est == "borde":
                borde.append(dict(det, clave=list(k), intentos=[origen[k] + 1, i + 1],
                                  distance_class=union[k].get("distance_class"), vrp_mw=union[k].get("vrp_mw"),
                                  _par=(union[k], r)))
            elif est == "hotspot_escena":
                escena.append(dict(det, clave=list(k), intentos=[origen[k] + 1, i + 1],
                                   distance_class=union[k].get("distance_class"), _par=(union[k], r)))
        nuevos.append(n)
    # el predicado del tablero corre sobre los de borde y los de hotspot_escena (condicion 4 de D-16 a)
    a_probar, nb = borde + escena, len(borde)
    if a_probar and not distintos:
        try:
            malos = _predicado([b["_par"] for b in a_probar], volcan)
        except Exception as e:  # sin node o sin el volcán en el tablero: no se puede probar, no se une
            malos = list(range(len(a_probar)))
            for b in a_probar:
                b["predicado"] = "no se pudo correr: %s" % e
        for j in malos:
            b = a_probar[j]
            b.setdefault("predicado", "el tablero da distinto con los dos records")
            b["campos"] = ["predicado del tablero"]
            distintos.append(b)
            estados["borde" if j < nb else "hotspot_escena"] -= 1
            estados["distinto"] += 1
        borde = [b for j, b in enumerate(borde) if j not in malos]
        escena = [b for j, b in enumerate(escena) if nb + j not in malos]
    for b in borde + escena + distintos:
        b.pop("_par", None)
    entero = None
    for i, d in enumerate(docs):
        ks = [clave(r) for r in d["records"]]
        if len(set(ks)) == len(ks) and set(ks) == set(union):
            entero = i
            break
    # de qué intento sale el record que queda en la salida: el entero, o en la mezcla el primero que lo trae
    for h in escena:
        h["conservado"] = entero + 1 if entero is not None else h["intentos"][0]
    inf = {"ok": not distintos, "modo": "mezcla" if entero is None else "intento_entero",
           "intento_entero": None if entero is None else entero + 1, "volcan": volcan,
           "por_intento": [len(d["records"]) for d in docs], "nuevos_por_intento": nuevos,
           "comunes": sum(estados.values()), "estados": estados, "borde": borde, "hotspot_escena": escena,
           "distintos": distintos, "union": len(union)}
    if distintos:
        return None, inf
    if entero is not None:
        salida = dict(docs[entero])
        regla = "un intento cubre todas las pasadas: se usa entero, sin mezclar"
    else:
        salida = {c: v for c, v in docs[0].items() if c != "records"}
        salida["records"] = sorted(union.values(), key=lambda r: (r["datetime_utc"], r["sensor"]))
        regla = "mezcla: en los comunes se conserva el record del primer intento"
    salida["_union_intentos"] = {"regla": regla, "intento_entero": inf["intento_entero"],
                                 "tolerancia": [REL_TOL, ABS_TOL], "por_intento": inf["por_intento"],
                                 "estados": estados, "borde": borde, "hotspot_escena": escena}
    return salida, inf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--volcan", help="nombre del volcán para el inner del tablero (por defecto, el del JSON)")
    ap.add_argument("intentos", nargs="+")
    a = ap.parse_args()
    docs = [json.load(open(p, encoding="utf-8")) for p in a.intentos]
    volcan = a.volcan or docs[0].get("volcano") or Path(a.intentos[0]).stem
    salida, inf = unir(docs, volcan)
    for h in inf["hotspot_escena"]:
        print("  hotspot_escena admitido %s intentos %s (queda el record del intento %d), %s: %s"
              % ("|".join(map(str, h["clave"])), h["intentos"], h["conservado"], h["distance_class"],
                 json.dumps(h["valores"], ensure_ascii=False)))
    if inf["ok"] and inf["modo"] == "intento_entero":
        for b in inf["borde"]:
            print("  borde admitido %s intentos %s: pixeles %s, %s %s MW, derivados distintos %s"
                  % ("|".join(map(str, b["clave"])), b["intentos"], b["pixeles"], b["distance_class"],
                     b["vrp_mw"], b["campos_derivados"]))
        json.dump(salida, open(a.out, "w", encoding="utf-8"))
        print("%s: intentos %s -> usa ENTERO el intento %d (%d records, cubre las %d pasadas); comunes %d %s"
              % (volcan, inf["por_intento"], inf["intento_entero"], len(salida["records"]), inf["union"],
                 inf["comunes"], inf["estados"]))
        return
    for b in inf["borde"]:
        print("  borde admitido %s intentos %s: pixeles %s, %s %s MW, derivados distintos %s"
              % ("|".join(map(str, b["clave"])), b["intentos"], b["pixeles"], b["distance_class"], b["vrp_mw"],
                 b["campos_derivados"]))
    if not inf["ok"]:
        print("NO SE UNE %s: %d gránulos comunes distintos, p. ej. %s"
              % (volcan, len(inf["distintos"]), json.dumps(inf["distintos"][:3], ensure_ascii=False)))
        sys.exit(1)
    json.dump(salida, open(a.out, "w", encoding="utf-8"))
    print("%s: intentos %s -> unión %d records; comunes %d %s; %d por píxel de borde"
          % (volcan, inf["por_intento"], inf["union"], inf["comunes"], inf["estados"], len(inf["borde"])))


if __name__ == "__main__":
    main()
