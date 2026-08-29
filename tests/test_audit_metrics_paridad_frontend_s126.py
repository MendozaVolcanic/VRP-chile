# -*- coding: utf-8 -*-
"""S126 - `mirova_eq_vrp` (Python) contra `mirovaEqVrp` (las 3 copias del frontend).

CONTEXTO. S125 anoto como bug de infra que `audit_metrics.mirova_eq_vrp()` estaba
"muerta y ya divergida de las 3 copias del frontend — un audit que la use mide otra
cosa que el dashboard". Verificado en S126, la afirmacion esta exagerada en sus dos
mitades:

  · NO esta muerta: la importan experiments/_s90, _s91 y _s92.
  · NO mide otra cosa: sobre los 60.315 records operacionales hay **0 desacuerdos**
    entre la version Python y las tres del frontend, y las tres del frontend entre si.

Pero la divergencia LATENTE en el codigo si es real, y son tres puntos:

  1. **Cap de 50.000 MW.** Las 3 copias JS lo aplican en los dos caminos (fallback y
     cluster); el Python no lo tenia. Un fosil pre-S41 (caso real: PP 2026-03-18 con
     695.431 MW antes del fix) contaria en un audit y saldria 0 en el dashboard.
  2. **Orden de los chequeos sin `primary_cluster`.** `index.html` y `mosaico.html`
     devuelven el fallback ANTES de mirar `distance_class`; `diario.html` y el Python
     miran `distance_class` primero. Para un record sin `pc` y con `distance_class`
     'far' las dos ramas dan cosas distintas.
  3. **Fallback a `vrp_mir_mw`.** index/mosaico caen a `vrp_mir_mw` si falta `vrp_mw`;
     diario y Python no.

Ninguno se dispara con los datos de hoy porque `store.py` ya capea a 50.000 y todos
los records modernos traen `primary_cluster`. Son trampas para el dia que aparezca un
JSON viejo o un path nuevo — exactamente el tipo de cosa que en esta misma sesion
resulto estar viva sin que nadie mirara (la mascara de nube).

Este archivo fija los casos borde ANTES de tocar la funcion (regla del proyecto: tests
sinteticos antes de modificar `audit_metrics.py`).
"""
import pytest

from pipeline.audit_metrics import mirova_eq_vrp

CAP = 50000.0


def rec(**kw):
    base = {"datetime_utc": "2026-07-01 05:00", "sensor": "VIIRS_SNPP"}
    base.update(kw)
    return base


# --- lo que ya funcionaba y no se debe romper ---

def test_cluster_dentro_del_inner_devuelve_su_vrp():
    r = rec(distance_class="summit",
            primary_cluster={"vrp_mw": 1.5, "centroid_dist_km": 2.0})
    assert mirova_eq_vrp(r, inner_km=5) == 1.5


def test_cluster_fuera_del_inner_da_cero():
    r = rec(distance_class="summit",
            primary_cluster={"vrp_mw": 1.5, "centroid_dist_km": 7.0})
    assert mirova_eq_vrp(r, inner_km=5) == 0


def test_distance_class_far_da_cero():
    r = rec(distance_class="far",
            primary_cluster={"vrp_mw": 1.5, "centroid_dist_km": 2.0})
    assert mirova_eq_vrp(r, inner_km=5) == 0


def test_sin_primary_cluster_cae_al_vrp_global():
    r = rec(distance_class="summit", vrp_mw=0.7)
    assert mirova_eq_vrp(r, inner_km=5) == 0.7


def test_record_vacio_da_cero():
    assert mirova_eq_vrp(None) == 0
    assert mirova_eq_vrp({}) == 0


# --- el punto 1: el cap que el frontend tiene y el Python no tenia ---

def test_un_fosil_por_encima_del_cap_da_cero_igual_que_el_dashboard():
    """Caso real: Planchon-Peteroa 2026-03-18 con 695.431 MW antes del fix S41.

    Las 3 copias del frontend devuelven 0. Si el Python devolviera el valor, un audit
    contaria como deteccion algo que el operador ve en cero.
    """
    r = rec(distance_class="summit",
            primary_cluster={"vrp_mw": 695431.0, "centroid_dist_km": 1.0})
    assert mirova_eq_vrp(r, inner_km=5) == 0


def test_el_cap_tambien_aplica_al_camino_de_fallback():
    r = rec(distance_class="summit", vrp_mw=695431.0)
    assert mirova_eq_vrp(r, inner_km=5) == 0


@pytest.mark.parametrize("v", [CAP - 0.01, CAP])
def test_justo_en_el_cap_o_debajo_no_se_recorta(v):
    """El frontend usa `> 50000`, no `>=`: el borde exacto pasa."""
    r = rec(distance_class="summit",
            primary_cluster={"vrp_mw": v, "centroid_dist_km": 1.0})
    assert mirova_eq_vrp(r, inner_km=5) == v


# --- puntos 2 y 3: se DOCUMENTAN, no se cambian ---

def test_sin_pc_y_far_sigue_la_semantica_de_diario_no_la_de_index():
    """Divergencia conocida entre las propias copias del frontend.

    `diario.html` y el Python miran `distance_class` primero -> 0.
    `index.html` y `mosaico.html` devuelven el fallback antes de mirarlo -> 0.9.

    No se unifica acá: elegir cual gana es una decision de producto (que muestra el
    dashboard), no de refactor, y hoy no hay ni un record en esa situacion sobre los
    60.315 operacionales. El test deja la eleccion actual por escrito para que un
    cambio futuro sea deliberado.
    """
    r = rec(distance_class="far", vrp_mw=0.9)
    assert mirova_eq_vrp(r, inner_km=5) == 0


def test_no_cae_a_vrp_mir_mw_cuando_falta_vrp_mw():
    """index/mosaico caen a `vrp_mir_mw`; diario y Python no. Documentado, no unificado.

    `vrp_mir_mw` es PRE-filtro geofencing (bug S12: barras fantasma en el chart), asi
    que caer a el es discutible. Se deja como esta.
    """
    r = rec(distance_class="summit", vrp_mir_mw=2.0)
    assert mirova_eq_vrp(r, inner_km=5) == 0
