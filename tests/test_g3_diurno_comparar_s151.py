# -*- coding: utf-8 -*-
"""Guard del G3 («noches intactas») del evaluador del A/B diurno tras la desviación D2 del pre-registro
(experiments/_s151_ab_diurno/PREREGISTRO.md §11, 2026-10-17).

Por qué: los dos brazos corren en runners distintos y MODIS no es determinista bit a bit (el recorte top-100 de
`np.argsort(-per_pixel_vrp_mw)` en pipeline/process_modis.py:1085-1099 desempata distinto según la CPU), y las
ventanas se arman uniendo intentos. El G3 comparaba el record crudo con las listas por posición: fallaba por el
ruido de máquina y su veredicto dependía del orden de los intentos. Ahora cada par nocturno se clasifica con
`unir_intentos.comparar` más el predicado del tablero; `distinto` hace FALLA y `orden`, `borde` y
`hotspot_escena` se informan aparte.

Cada caso fija un lado (A116): el G3 PUEDE fallar (un campo de decisión distinto en una noche, el predicado del
tablero distinto), admite lo que el mismo código produce entre runners, cada categoría importa (si se saca de
G3_ADMITIDAS, su caso falla) y el veredicto no depende de qué intento conservó la unión. El predicado se inyecta
en la mayoría de los casos para no depender de node; un caso lo corre de verdad.
"""
import copy
import json
import shutil
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
AQUI = RAIZ / "experiments" / "_s151_ab_diurno"


def _importar_aislado():
    """evaluar_diurno mete su carpeta en sys.path e importa `sustrato` y `unir_intentos` por nombre corto; otros
    tests importan OTRO `sustrato` (tests/test_sustrato_s145.py). Se importa y se deja sys.path y sys.modules como
    estaban, salvo los módulos de fuera de esta carpeta, para no contaminar la colección del resto de la suite."""
    path0, mods0 = list(sys.path), set(sys.modules)
    sys.path.insert(0, str(AQUI))
    try:
        return pytest.importorskip("evaluar_diurno")
    finally:
        sys.path[:] = path0
        for nombre in set(sys.modules) - mods0:
            f = getattr(sys.modules[nombre], "__file__", None) or ""
            if Path(f).resolve().parent == AQUI.resolve():
                del sys.modules[nombre]


ED = _importar_aislado()
U = ED.U
HAY_NODE = shutil.which("node") is not None
RESCATE = "single_pixel_far_overridden_by_cluster"
P1 = {"lat": -37.85, "lon": -71.17, "vrp_mw": 0.05, "bt_k": 280.0}
P2 = {"lat": -37.86, "lon": -71.16, "vrp_mw": 0.04, "bt_k": 279.0}
P3 = {"lat": -37.84, "lon": -71.18, "vrp_mw": 0.04, "bt_k": 279.0}
LEJOS = {"lat": -38.3, "lon": -71.4, "vrp_mw": 0.04, "bt_k": 277.0}   # empata con P2 y P3: el mínimo de la lista
PC = {"vrp_mw": 0.4, "centroid_lat": -37.85, "centroid_lon": -71.17, "centroid_dist_km": 1.0, "n_pixels": 2}


def base(**kw):
    r = {"sensor": "MODIS_AQUA", "datetime_utc": "2026-06-18 07:30", "granule": "MYD021KM.A2026169.0730.061.x.hdf",
         "product_version": "standard", "t_max_k": 280.0, "distance_class": "summit", "triggered_test1": True,
         "primary_cluster": dict(PC), "vrp_mw": 3.0, "final_hotspot_source": "test1",
         "hotspot_lat": -38.1, "hotspot_lon": -71.4, "hotspot_dist_km": 30.0,
         "final_hotspot_lat": -37.86, "final_hotspot_lon": -71.17, "final_hotspot_dist_km": 1.2,
         # 2 guardados + 98 descartados = los 100 del recorte top-100, donde el desempate puede actuar (PR #847)
         "anomaly_pixels": [dict(P1), dict(P2)], "discarded_anomaly_pixels": [dict(LEJOS, lat=-38.3 - 0.001 * i)
                                                                         for i in range(98)],
         "diag_mu_deti": -9.871330774512634e-06, "n_anomalous_pixels": 140,   # >100: el recorte cortó (verificador V2)
         "processed_utc": "2026-10-15T00:00:00Z", "first_processed_utc": "2026-10-15T00:00:00Z"}
    r.update(kw)
    return r


def rescatado(r):
    """El rescate por cúmulo de store.py:390-422 sobre el mismo record (lo que otro runner deja si su hotspot de
    escena cae lejos): hotspot y ancla final al centroide, fuente, etiqueta y vrp_mw del cúmulo."""
    pc = r["primary_cluster"]
    return dict(r, vrp_mw=pc["vrp_mw"], final_hotspot_source="cluster_rescue", discarded_reason=RESCATE,
                hotspot_lat=pc["centroid_lat"], hotspot_lon=pc["centroid_lon"], hotspot_dist_km=pc["centroid_dist_km"],
                final_hotspot_lat=pc["centroid_lat"], final_hotspot_lon=pc["centroid_lon"],
                final_hotspot_dist_km=pc["centroid_dist_km"])


def fila(raw, vol="Copahue"):
    return {"vol": vol, "sensor": raw["sensor"], "t": raw["datetime_utc"][:16], "dia": False, "raw": raw}


def g3(pares, predicado=lambda p, v: []):
    """pares: [(record control, record diurno)], cada uno en otra pasada. Devuelve (veredicto, noches)."""
    rc, rd = [], []
    for i, (a, b) in enumerate(pares):
        t = "2026-06-%02d 07:30" % (10 + i)
        rc.append(fila(dict(a, datetime_utc=t)))
        rd.append(fila(dict(b, datetime_utc=t)))
    ni = ED.noches_identicas(rc, rd, predicado=predicado)
    return ED.veredicto_g3(ni), ni


def test_tolerancia_y_volatiles_coherentes_con_unir_intentos():
    assert (ED.G3_REL_TOL, ED.G3_ABS_TOL) == (U.REL_TOL, U.ABS_TOL)
    assert set(ED.VOLATILES) == U.PROCESO
    assert set(ED.G3_CATEGORIAS) == {"igual", "tolerancia", "orden", "borde", "hotspot_escena", "distinto"}
    assert "distinto" not in ED.G3_ADMITIDAS


def test_igual_ruido_y_volatiles_cumplen():
    a = base()
    b = dict(a, diag_mu_deti=a["diag_mu_deti"] * (1 + 2e-16), processed_utc="2026-10-16T09:00:00Z",
             first_processed_utc="2026-10-16T09:00:30Z")
    v, ni = g3([(a, a), (a, b)])
    assert v == "CUMPLE" and ni["estados"]["igual"] == 1 and ni["estados"]["tolerancia"] == 1


@pytest.mark.parametrize("campo,valor", [("distance_class", "far"), ("t_max_k", 281.0), ("triggered_test1", False),
                                         ("diag_mu_deti", -9.9e-06), ("primary_cluster", dict(PC, vrp_mw=0.41))])
def test_un_campo_de_decision_distinto_en_una_noche_falla(campo, valor):
    a = base()
    v, ni = g3([(a, a), (a, a), (a, dict(a, **{campo: valor}))])
    assert v.startswith("FALLA") and ni["estados"]["distinto"] == 1
    assert ni["campos_distintos"] == {campo: 1}


def test_orden_se_admite_y_se_informa():
    a = base()
    v, ni = g3([(a, dict(a, anomaly_pixels=[dict(P2), dict(P1)]))])
    assert v == "CUMPLE" and ni["estados"]["orden"] == 1 and len(ni["admitidos"]["orden"]) == 1


def test_borde_se_admite_si_el_tablero_da_lo_mismo_y_falla_si_no():
    a = base()
    b = dict(a, anomaly_pixels=[dict(P1), dict(P3)], final_hotspot_lat=-37.84)
    v, ni = g3([(a, b)])
    assert v == "CUMPLE" and ni["estados"]["borde"] == 1 and len(ni["admitidos"]["borde"]) == 1
    v, ni = g3([(a, b)], predicado=lambda p, vol: [0])
    assert v.startswith("FALLA") and ni["campos_distintos"] == {"predicado del tablero distinto": 1}


@pytest.mark.parametrize("sensor", ["MODIS_AQUA", "VIIRS_NOAA20", "VIIRS_NOAA21_750"])
def test_borde_con_lista_corta_falla(sensor):
    """Verificador del PR #847: con menos de 100 píxeles el recorte top-100 no corta nada, así que otro conjunto
    de píxeles es otra detección, no un empate. Es la población de la rama diurna (VIIRS)."""
    a = base(sensor=sensor, f5_core_vrp_mw=0.3, discarded_anomaly_pixels=[])
    for b in (dict(a, anomaly_pixels=[dict(P1), dict(P3)]),                       # un píxel desplazado
              dict(a, anomaly_pixels=[dict(P1), dict(P3)], vrp_mir_mw=1.3),       # y vrp_mir_mw distinto
              dict(a, anomaly_pixels=[dict(P1), dict(P2), dict(P3)])):            # un píxel de más
        v, ni = g3([(a, b)])
        assert v.startswith("FALLA") and ni["estados"]["distinto"] == 1, (sensor, b["anomaly_pixels"])


def test_borde_en_viirs_con_lista_llena_se_admite():
    """El empate del recorte también existe en VIIRS (W2a, Tupungatito VIIRS_NOAA21_750 2026-06-17 17:30, lista
    llena): no se restringe a MODIS."""
    a = base(sensor="VIIRS_NOAA21_750")
    v, ni = g3([(a, dict(a, anomaly_pixels=[dict(P1), dict(P3)]))])
    assert v == "CUMPLE" and ni["estados"]["borde"] == 1


def test_hotspot_escena_se_admite_si_el_tablero_da_lo_mismo_y_falla_si_no():
    a = base()
    assert U.comparar(a, rescatado(a))[0] == "hotspot_escena"
    v, ni = g3([(a, rescatado(a))])
    assert v == "CUMPLE" and ni["estados"]["hotspot_escena"] == 1
    v, ni = g3([(a, rescatado(a))], predicado=lambda p, vol: [0])
    assert v.startswith("FALLA") and ni["estados"]["hotspot_escena"] == 0


def test_predicado_que_no_corre_es_indecidible_no_falla():
    """Verificador del PR #847: si node no corre, no se sabe si el par es distinto. Es INDECIDIBLE, no un defecto
    del cableado; y un distinto real en otra noche sigue dando FALLA."""
    def roto(p, vol):
        raise RuntimeError("sin node")
    a = base()
    v, ni = g3([(a, rescatado(a))], predicado=roto)
    assert v.startswith("INDECIDIBLE") and "sin node" in v
    assert ni["sin_predicado"] == 1 and ni["estados"]["distinto"] == 0 and ni["estados"]["hotspot_escena"] == 0
    v, ni = g3([(a, rescatado(a)), (a, dict(a, distance_class="far"))], predicado=roto)
    assert v.startswith("FALLA")


def test_el_predicado_recibe_cada_volcan_con_sus_pares():
    vistos = []

    def espia(p, vol):
        vistos.append((vol, len(p)))
        return []
    a = base()
    rc = [fila(dict(a, datetime_utc="2026-06-1%d 07:30" % i), vol) for i, vol in enumerate(["Copahue", "Llaima", "Llaima"])]
    rd = [fila(dict(rescatado(a), datetime_utc=x["t"]), x["vol"]) for x in rc]
    ED.noches_identicas(rc, rd, predicado=espia)
    assert sorted(vistos) == [("Copahue", 1), ("Llaima", 2)]


def test_rescate_incoherente_no_es_escena_y_falla():
    a = base()
    b = dict(rescatado(a), vrp_mw=3.0)        # rescate con vrp_mw distinto del cúmulo: no es store.py:396
    v, ni = g3([(a, b)])
    assert v.startswith("FALLA")


@pytest.mark.parametrize("cat,par", [
    ("orden", lambda a: (a, dict(a, anomaly_pixels=[dict(P2), dict(P1)]))),
    ("borde", lambda a: (a, dict(a, anomaly_pixels=[dict(P1), dict(P3)], final_hotspot_lat=-37.84))),
    ("hotspot_escena", lambda a: (a, rescatado(a))),
    ("tolerancia", lambda a: (a, dict(a, diag_mu_deti=a["diag_mu_deti"] * (1 + 2e-16)))),
])
def test_cada_categoria_importa(cat, par, monkeypatch):
    """Si la categoría sale de G3_ADMITIDAS, su caso tiene que fallar: veredicto_g3 la lee de ahí."""
    a = base()
    assert g3([par(a)])[0] == "CUMPLE"
    monkeypatch.setattr(ED, "G3_ADMITIDAS", tuple(c for c in ED.G3_ADMITIDAS if c != cat))
    v, ni = g3([par(a)])
    assert ni["estados"][cat] == 1 and v.startswith("FALLA")


def test_el_veredicto_no_depende_de_que_intento_conservo_la_union():
    """Dos intentos del brazo diurno: uno igual al control y otro con el rescate (el caso de W2a Copahue
    2026-06-18 07:30). La unión conserva uno u otro según el orden; el G3 tiene que decir lo mismo."""
    a = base()
    i1, i2 = copy.deepcopy(a), rescatado(a)
    u12 = U.unir([{"records": [i1]}, {"records": [i2]}], "Copahue") if HAY_NODE else None
    for diurno in (i1, i2):
        assert g3([(a, diurno)])[0] == "CUMPLE"
    if u12 is not None:
        u21 = U.unir([{"records": [i2]}, {"records": [i1]}], "Copahue")
        assert u12[1]["ok"] and u21[1]["ok"]
        r12, r21 = u12[0]["records"][0], u21[0]["records"][0]
        assert r12 != r21                                   # la unión sí depende del orden
        assert g3([(a, r12)], predicado=U._predicado)[0] == g3([(a, r21)], predicado=U._predicado)[0] == "CUMPLE"


@pytest.mark.skipif(not HAY_NODE, reason="sin node no corre el predicado del tablero")
def test_predicado_real_atrapa_lo_que_comparar_admite():
    """Cúmulo en 0 MW: el lado rescatado queda con vrp_mw 0 y etiqueta de descarte, e isSummitDetection
    (frontend/index.html:1596) lo baja de summit. comparar lo admite como hotspot_escena; el tablero no."""
    a = base(primary_cluster=dict(PC, vrp_mw=0.0), triggered_test1=False)
    b = rescatado(a)
    assert U.comparar(a, b)[0] == "hotspot_escena"
    v, ni = g3([(a, b)], predicado=U._predicado)
    assert v.startswith("FALLA") and ni["campos_distintos"] == {"predicado del tablero distinto": 1}
    v, _ = g3([(base(), rescatado(base()))], predicado=U._predicado)
    assert v == "CUMPLE"


W2 = Path(r"C:\Users\nmend\AppData\Local\Temp\claude\g3_s151")


@pytest.mark.skipif(not (W2 / "g3_w2_12.json").exists() or not (W2 / "g3_w2_21.json").exists(),
                    reason="salidas de g3_solo.py sobre W2 sólo en la máquina de Nicolás")
def test_w2_unido_en_los_dos_ordenes_da_el_mismo_g3():
    a = json.loads((W2 / "g3_w2_12.json").read_text(encoding="utf-8"))
    b = json.loads((W2 / "g3_w2_21.json").read_text(encoding="utf-8"))
    assert a["G3"] == b["G3"] == "CUMPLE"
    assert a["estados"]["distinto"] == b["estados"]["distinto"] == 0
    assert sum(a["estados"].values()) == sum(b["estados"].values())
