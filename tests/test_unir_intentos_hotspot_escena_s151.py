# -*- coding: utf-8 -*-
"""Guard de la categoria `hotspot_escena` de experiments/_s151_ab_diurno/unir_intentos.py (decision D-16 a de
Nicolas, 2026-10-17).

Por que: dos corridas del MISMO commit dejan en MODIS el «pixel mas caliente» de la primera pasada
(`hotspot_*`, pipeline/process_modis.py:1097, el primero de `np.argsort(-per_pixel_vrp_mw)` en la l. 1085) en
lugares distintos, con la misma BT maxima, el mismo cumulo y los mismos pixeles guardados. Cuando ese pixel cae
mas alla de `max_hotspot_dist_km`, el rescate por cumulo (A46, pipeline/store.py:390-422) reescribe
`final_hotspot_*`, `final_hotspot_source`, `discarded_reason` y el `vrp_mw` del record. Casos reales: F/K V1
(run 38639658446) Llaima control, y diurno W2a (run 38853230521) Copahue `_s151_ab_diurno_on`. Nicolas decidio
admitirlo acotado e informado (D-16 a); el arreglo del desempate en produccion es otra tarea (D-16 b).

Cada condicion tiene un caso que bloquea si sólo ella falla (A116), y cada una tiene una mutacion del codigo que
este archivo atrapa: si se quita la condicion, el caso que deberia bloquear une.
"""
import copy
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
RUTA = RAIZ / "experiments" / "_s151_ab_diurno" / "unir_intentos.py"
HAY_NODE = shutil.which("node") is not None
RESCATE = "single_pixel_far_overridden_by_cluster"


def cargar(mutacion=None):
    """El modulo, o una copia con UNA mutacion textual (viejo, nuevo) que tiene que aparecer exactamente una vez."""
    src = RUTA.read_text(encoding="utf-8")
    if mutacion:
        viejo, nuevo = mutacion
        assert src.count(viejo) == 1, "la mutacion no encuentra su texto exactamente una vez: %r" % viejo
        src = src.replace(viejo, nuevo)
    nombre = "unir_intentos_mut" if mutacion else "unir_intentos_he"
    spec = importlib.util.spec_from_loader(nombre, loader=None, origin=str(RUTA))
    m = importlib.util.module_from_spec(spec)
    m.__file__ = str(RUTA)
    exec(compile(src, str(RUTA), "exec"), m.__dict__)
    return m


ui = cargar()

PC = {"n_pixels": 11, "vrp_mw": 1.834, "centroid_lat": -37.85699, "centroid_lon": -71.19365,
      "centroid_dist_km": 0.941, "focal_magnitude": True, "focal_degraded": False, "single_pixel_mode": False,
      "geo_class": "summit"}


def rec_test1(**cambios):
    """Record MODIS con la forma del de Copahue W2a, intento 1: Test 1, pixel mas caliente a 20 km sin rescate.
    Como en el dato real, `discarded_reason` no esta (la clave falta, no vale None)."""
    r = {
        "sensor": "MODIS_AQUA", "datetime_utc": "2026-06-18 07:30", "granule": "MYD021KM.A2026169.0730.061.x.hdf",
        "product_version": "standard", "processed_utc": "I1", "first_processed_utc": "x",
        "distance_class": "summit", "vrp_mw": 4.782, "vrp_mir_mw": 4.782, "vrp_vent_mw": 0.0, "t_max_k": 274.29,
        "diag_t_max_dist_km": 20.31, "triggered_test1": True, "n_anomalous_pixels": 11, "n_test1_pixels": 11,
        "f5_core_vrp_mw": None, "final_hotspot_source": "test1", "sensor_zenith_deg": 40.1,
        "hotspot_lat": -37.79802, "hotspot_lon": -71.40227, "hotspot_dist_km": 20.31,
        "final_hotspot_lat": -37.856813643710396, "final_hotspot_lon": -71.20037054948875,
        "final_hotspot_dist_km": 1.528, "primary_cluster": dict(PC),
        "anomaly_pixels": [{"lat": -37.86 - 0.001 * i, "lon": -71.21, "dist_km": 2.0, "bt_k": 255.0 - i,
                            "vrp_mw": 0.98 - 0.05 * i} for i in range(11)],
    }
    r.update(cambios)
    return r


def rec_rescate(**cambios):
    """El mismo record con el pixel mas caliente en otro lugar: el rescate por cumulo (store.py:405-422)."""
    r = rec_test1(processed_utc="I2", final_hotspot_source="cluster_rescue", vrp_mw=1.834,
                  hotspot_lat=-37.85699, hotspot_lon=-71.19365, hotspot_dist_km=0.941,
                  final_hotspot_lat=-37.85699, final_hotspot_lon=-71.19365, final_hotspot_dist_km=0.941,
                  discarded_reason=RESCATE)
    r.update(cambios)
    return r


SOLO1 = rec_test1(datetime_utc="2026-06-01 07:30", granule="solo1.hdf")
SOLO2 = rec_test1(datetime_utc="2026-06-02 07:30", granule="solo2.hdf")
# el pixel mas caliente en otro lugar, sin rescate (la forma de Llaima control 2026-09-24 02:05)
MOVIDO = {"hotspot_lat": -38.0, "hotspot_lon": -71.5, "hotspot_dist_km": 7.1}


def doc(*recs):
    return {"volcano": "Copahue", "updated": "x", "records": [copy.deepcopy(r) for r in recs]}


def mezcla(a, b, mod=None):
    """Ninguno de los dos intentos cubre la union: la herramienta mezcla record a record."""
    salida, inf = (mod or ui).unir([doc(SOLO1, a), doc(b, SOLO2)], "Copahue")
    assert inf["modo"] == "mezcla"
    return salida, inf


def en_viirs(r):
    """El mismo record como VIIRS 375 con nucleo guardado (asi la regla de pixeles de VIIRS no interviene)."""
    return dict(r, sensor="VIIRS_SNPP", f5_core_vrp_mw=1.5)


# ---------------------------------------------------------------- une
@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_rescate_por_otro_hotspot_une_e_informa():
    salida, inf = mezcla(rec_test1(), rec_rescate())
    assert inf["ok"] and inf["estados"]["hotspot_escena"] == 1 and inf["estados"]["distinto"] == 0
    (h,) = inf["hotspot_escena"]
    assert h["clave"] == ["MODIS_AQUA", "2026-06-18 07:30"] and h["intentos"] == [1, 2]
    assert set(h["campos"]) == {"hotspot_lat", "hotspot_lon", "hotspot_dist_km", "final_hotspot_lat",
                                "final_hotspot_lon", "final_hotspot_dist_km", "final_hotspot_source",
                                "discarded_reason", "vrp_mw"}
    assert h["valores"]["vrp_mw"] == [4.782, 1.834]
    assert h["valores"]["final_hotspot_source"] == ["test1", "cluster_rescue"]
    assert h["valores"]["discarded_reason"] == ["<ausente>", RESCATE]
    assert h["conservado"] == 1
    # se conserva el record del primer intento, y la lista viaja en el JSON de salida
    comun = [r for r in salida["records"] if r["datetime_utc"] == "2026-06-18 07:30"]
    assert len(comun) == 1 and comun[0]["vrp_mw"] == 4.782 and comun[0]["processed_utc"] == "I1"
    assert salida["_union_intentos"]["hotspot_escena"] == inf["hotspot_escena"]


@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_solo_cambia_el_hotspot_une():
    """La forma de Llaima control 2026-09-24 02:05: el hotspot se mueve y nada mas (ningun rescate)."""
    b = rec_test1(**MOVIDO)
    salida, inf = mezcla(rec_test1(), b)
    assert inf["ok"] and inf["estados"]["hotspot_escena"] == 1
    assert sorted(inf["hotspot_escena"][0]["campos"]) == ["hotspot_dist_km", "hotspot_lat", "hotspot_lon"]


@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_con_pixel_de_borde_ademas_une_por_las_dos_reglas():
    """Si ademas los pixeles difieren como conjunto, la regla de borde de #841 sigue valiendo para ellos."""
    a = rec_test1()
    b = rec_rescate(anomaly_pixels=a["anomaly_pixels"][:-1], vrp_mir_mw=4.6)
    salida, inf = mezcla(a, b)
    assert inf["ok"] and inf["estados"]["hotspot_escena"] == 1 and inf["estados"]["borde"] == 0
    h = inf["hotspot_escena"][0]
    assert h["pixeles"]["anomaly_pixels"] == [11, 10] and "vrp_mir_mw" in h["campos"]


@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_intento_entero_informa_que_intento_se_entrega():
    """Con un intento que cubre todo se entrega ese intento entero (#841); el informe dice de cual sale el record."""
    salida, inf = ui.unir([doc(rec_test1()), doc(rec_rescate(), SOLO2)], "Copahue")
    assert inf["ok"] and inf["modo"] == "intento_entero" and inf["intento_entero"] == 2
    assert inf["hotspot_escena"][0]["conservado"] == 2
    assert [r["vrp_mw"] for r in salida["records"] if r["datetime_utc"] == "2026-06-18 07:30"] == [1.834]


# ---------------------------------------------------------------- bloquea (una condicion por caso)
def test_bloquea_si_cambia_distance_class():
    salida, inf = mezcla(rec_test1(), rec_rescate(distance_class="far"))
    assert not inf["ok"] and salida is None and "distance_class" in inf["distintos"][0]["campos"]


def test_bloquea_si_cambia_primary_cluster():
    salida, inf = mezcla(rec_test1(), rec_rescate(primary_cluster=dict(PC, n_pixels=12)))
    assert not inf["ok"] and "primary_cluster" in inf["distintos"][0]["campos"]


def test_bloquea_si_el_sensor_es_viirs():
    salida, inf = mezcla(en_viirs(rec_test1()), en_viirs(rec_rescate()))
    assert not inf["ok"]
    d = inf["distintos"][0]
    assert "vrp_mw" in d["campos"] and "MODIS" in d["no_es_hotspot_escena"]


def test_bloquea_si_difiere_la_bt_maxima():
    salida, inf = mezcla(rec_test1(), rec_rescate(t_max_k=274.31))
    assert not inf["ok"] and "t_max_k" in inf["distintos"][0]["campos"]


def test_bloquea_sin_bt_maxima():
    salida, inf = mezcla(rec_test1(t_max_k=None), rec_test1(t_max_k=None, **MOVIDO))
    assert not inf["ok"] and "BT" in inf["distintos"][0]["no_es_hotspot_escena"]


def test_bloquea_sin_cumulo():
    """Sin cumulo el tablero publica `vrp_mw` (frontend/index.html:1148-1149) y el rescate no existe."""
    salida, inf = mezcla(rec_test1(primary_cluster=None), rec_test1(primary_cluster=None, **MOVIDO))
    assert not inf["ok"] and "cumulo" in inf["distintos"][0]["no_es_hotspot_escena"]


def test_bloquea_si_vrp_mw_cambia_sin_rescate():
    salida, inf = mezcla(rec_test1(), rec_test1(vrp_mw=3.9))
    assert not inf["ok"] and "rescate" in inf["distintos"][0]["no_es_hotspot_escena"]


def test_bloquea_si_el_rescate_no_toma_la_magnitud_del_cumulo():
    salida, inf = mezcla(rec_test1(), rec_rescate(vrp_mw=2.0))
    assert not inf["ok"] and "rescate" in inf["distintos"][0]["no_es_hotspot_escena"]


def test_bloquea_si_los_dos_lados_son_rescate():
    """Dos rescates no tienen nada que pueda diferir: el hotspot de los dos es el centroide del cumulo."""
    salida, inf = mezcla(rec_rescate(), rec_rescate(vrp_mw=1.9))
    assert not inf["ok"]


# ---------------------------------------------------------------- verificador del PR #843
def test_bloquea_si_el_lado_no_rescatado_trae_etiqueta():
    """Mata m1 del verificador (quitar «el otro lado no trae etiqueta de descarte»)."""
    salida, inf = mezcla(rec_test1(discarded_reason="eruption_hotspot_too_far"), rec_rescate())
    assert not inf["ok"] and "rescate" in inf["distintos"][0]["no_es_hotspot_escena"]


@pytest.mark.parametrize("etiqueta", [None, "<sin clave>", "cluster_too_large_for_volcano"])
def test_bloquea_si_el_rescate_no_trae_su_etiqueta(etiqueta):
    """Mata m2 del verificador (quitar «el rescate trae su etiqueta», store.py:422)."""
    b = rec_rescate(discarded_reason=etiqueta)
    if etiqueta == "<sin clave>":
        del b["discarded_reason"]
    salida, inf = mezcla(rec_test1(), b)
    assert not inf["ok"] and "rescate" in inf["distintos"][0]["no_es_hotspot_escena"]


@pytest.mark.parametrize("campo, valor", [("solar_zenith_deg", 120.0), ("sensor_zenith_deg", 60.0),
                                          ("hotspot_dist_km", 7.1), ("final_hotspot_dist_km", 3.0)])
def test_a_geometria_y_ancla_final_solo_si_se_mueve_el_hotspot(campo, valor):
    """(a), LAX4 a LAX6: lo que se evalua en el hotspot no cambia si el hotspot no se movio."""
    salida, inf = mezcla(rec_test1(), rec_test1(**{campo: valor}))
    assert not inf["ok"] and "hotspot" in inf["distintos"][0]["no_es_hotspot_escena"]


def test_b_ancla_final_sin_rescate_con_fuente_test1_bloquea():
    """(b), LAX6 con el hotspot movido: con fuente test1 el ancla final es el centroide del Test 1
    (process_modis.py:1296-1298), que no depende del hotspot."""
    salida, inf = mezcla(rec_test1(), rec_test1(final_hotspot_lat=-37.65, **MOVIDO))
    assert not inf["ok"] and "ancla final" in inf["distintos"][0]["no_es_hotspot_escena"]


def rec_eruption(**cambios):
    """Fuente eruption: el ancla final ES el hotspot (process_modis.py:1307-1310)."""
    r = rec_test1(final_hotspot_source="eruption", final_hotspot_lat=-37.79802, final_hotspot_lon=-71.40227,
                  final_hotspot_dist_km=20.31)
    r.update(cambios)
    return r


ERUPTION_MOVIDO = {"hotspot_lat": -37.8, "hotspot_lon": -71.3, "hotspot_dist_km": 9.0,
                   "final_hotspot_lat": -37.8, "final_hotspot_lon": -71.3, "final_hotspot_dist_km": 9.0}


@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_b_ancla_final_con_fuente_eruption_y_final_igual_al_hotspot_une():
    """(b), rama permitida: misma fuente y final == hotspot en los dos lados."""
    salida, inf = mezcla(rec_eruption(), rec_eruption(**ERUPTION_MOVIDO))
    assert inf["ok"] and inf["estados"]["hotspot_escena"] == 1


def test_b_ancla_final_con_fuente_eruption_y_final_distinto_del_hotspot_bloquea():
    b = rec_eruption(**dict(ERUPTION_MOVIDO, final_hotspot_lat=-37.81))
    salida, inf = mezcla(rec_eruption(), b)
    assert not inf["ok"] and "ancla final" in inf["distintos"][0]["no_es_hotspot_escena"]


def test_c_el_lado_rescatado_tiene_el_hotspot_en_el_cumulo():
    """(c): el rescate escribe el centroide del cumulo en hotspot_* (store.py:397-399)."""
    salida, inf = mezcla(rec_test1(), rec_rescate(hotspot_lat=-37.9))
    assert not inf["ok"] and "centroide" in inf["distintos"][0]["no_es_hotspot_escena"]


@pytest.mark.parametrize("campo, valor", [("n_anomalous_pixels", 12), ("triggered_test1", False),
                                          ("product_version", "nrt"), ("diag_t_max_dist_km", 7.1),
                                          ("vrp_vent_mw", 0.5)])
def test_bloquea_si_cambia_otro_campo(campo, valor):
    salida, inf = mezcla(rec_test1(), rec_rescate(**{campo: valor}))
    assert not inf["ok"] and campo in inf["distintos"][0]["campos"]


def test_bloquea_si_el_predicado_da_distinto(monkeypatch):
    monkeypatch.setattr(ui, "_predicado", lambda pares, volcan: [0])
    salida, inf = mezcla(rec_test1(), rec_rescate())
    assert not inf["ok"] and inf["distintos"][0]["campos"] == ["predicado del tablero"]
    assert inf["estados"]["hotspot_escena"] == 0 and inf["estados"]["distinto"] == 1


def test_bloquea_si_el_predicado_no_corre(monkeypatch):
    def roto(pares, volcan):
        raise RuntimeError("sin node")
    monkeypatch.setattr(ui, "_predicado", roto)
    salida, inf = mezcla(rec_test1(), rec_rescate())
    assert not inf["ok"] and "sin node" in inf["distintos"][0]["predicado"]


@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_el_predicado_ve_la_diferencia_de_clase():
    """El chequeo (4) no es decorativo con estos records: summit contra far da distinto en node."""
    assert ui._predicado([(rec_test1(), rec_rescate()), (rec_test1(), rec_rescate(distance_class="far"))],
                         "Copahue") == [1]


# ---------------------------------------------------------------- mutaciones: cada condicion importa
MUTACIONES = {
    # (texto viejo, texto nuevo, caso que tiene que dejar de bloquear[, "une": el caso une y la mutacion lo bloquea])
    "sin_modis": ('    if not str(a.get("sensor") or "").startswith("MODIS_"):',
                  '    if False:', "viirs"),
    "sin_bt_presente": ('    if a.get("t_max_k") is None or b.get("t_max_k") is None:', '    if False:', "sin_bt"),
    "bt_en_la_lista": ('CAMPOS_HOTSPOT_ESCENA = {', 'CAMPOS_HOTSPOT_ESCENA = {"t_max_k": "mutacion",', "bt"),
    "cumulo_en_la_lista": ('CAMPOS_HOTSPOT_ESCENA = {', 'CAMPOS_HOTSPOT_ESCENA = {"primary_cluster": "mutacion",',
                           "cumulo"),
    "clase_en_la_lista": ('CAMPOS_HOTSPOT_ESCENA = {', 'CAMPOS_HOTSPOT_ESCENA = {"distance_class": "mutacion",',
                          "clase"),
    "sin_cumulo_presente": ('    if not a.get("primary_cluster"):', '    if False:', "sin_cumulo"),
    "sin_coherencia_rescate": ('    if rescate and not _rescate_coherente(a, b):', '    if False:', "vrp_sin_rescate"),
    "sin_predicado": ('    a_probar, nb = borde + escena, len(borde)', '    a_probar, nb = borde, len(borde)', "predicado"),
    # m1 y m2 del verificador del PR #843
    "m1_otro_lado_sin_etiqueta": ('    if otro.get("discarded_reason") is not None:', '    if False:', "otro_con_etiqueta"),
    "m2_rescate_sin_su_etiqueta": ('    if r.get("discarded_reason") != _RESCATE:', '    if False:', "rescate_sin_etiqueta"),
    # (a), (b) y (c) del verificador del PR #843
    "a_sin_hotspot_movido": ('    if (d & _SIGUEN_AL_HOTSPOT) and not movio:', '    if False:', "geometria_quieta"),
    "b_sin_ancla_final": ('    if (d & _ANCLA_FINAL) and not (_rescate_coherente(a, b) or _final_es_hotspot(a, b)):',
                          '    if False:', "final_test1"),
    "b_rama_eruption_rota": ('    return all(a.get("final_hotspot_source") == b.get("final_hotspot_source") and',
                             '    return False and all(a.get("final_hotspot_source") == b.get("final_hotspot_source") and',
                             "final_eruption", "une"),
    "c_sin_hotspot_en_el_cumulo": ('        if r.get("final_hotspot_source") == "cluster_rescue" and not _hotspot_en_el_cumulo(r):',
                                   '        if False:', "rescate_fuera_del_cumulo"),
}


def _caso(nombre, mod, monkeypatch):
    """Corre el caso con el modulo `mod` y devuelve True si UNE."""
    if nombre == "predicado":
        monkeypatch.setattr(mod, "_predicado", lambda pares, volcan: list(range(len(pares))))
    else:
        monkeypatch.setattr(mod, "_predicado", lambda pares, volcan: [])
    a, b = {
        "viirs": (en_viirs(rec_test1()), en_viirs(rec_rescate())),
        "sin_bt": (rec_test1(t_max_k=None), rec_test1(t_max_k=None, **MOVIDO)),
        "bt": (rec_test1(), rec_rescate(t_max_k=274.31)),
        "cumulo": (rec_test1(), rec_rescate(primary_cluster=dict(PC, n_pixels=12))),
        "clase": (rec_test1(), rec_rescate(distance_class="far")),
        "sin_cumulo": (rec_test1(primary_cluster=None), rec_test1(primary_cluster=None, **MOVIDO)),
        "vrp_sin_rescate": (rec_test1(), rec_test1(vrp_mw=3.9)),
        "predicado": (rec_test1(), rec_rescate()),
        "otro_con_etiqueta": (rec_test1(discarded_reason="eruption_hotspot_too_far"), rec_rescate()),
        "rescate_sin_etiqueta": (rec_test1(), rec_rescate(discarded_reason=None)),
        "geometria_quieta": (rec_test1(), rec_test1(solar_zenith_deg=120.0)),
        "final_test1": (rec_test1(), rec_test1(final_hotspot_lat=-37.65, **MOVIDO)),
        "final_eruption": (rec_eruption(), rec_eruption(**ERUPTION_MOVIDO)),
        "rescate_fuera_del_cumulo": (rec_test1(), rec_rescate(hotspot_lat=-37.9)),
    }[nombre]
    salida, inf = mod.unir([doc(SOLO1, a), doc(b, SOLO2)], "Copahue")
    return inf["ok"]


@pytest.mark.parametrize("mut", sorted(MUTACIONES))
def test_cada_condicion_importa(mut, monkeypatch):
    viejo, nuevo, caso, *une = MUTACIONES[mut]
    une = bool(une)
    assert _caso(caso, ui, monkeypatch) == une, "sin mutacion el caso %s tiene que %s" % (caso, "unir" if une else "bloquear")
    assert _caso(caso, cargar((viejo, nuevo)), monkeypatch) != une, "la mutacion %s sobrevive" % mut


# ---------------------------------------------------------------- datos reales
T = Path(r"C:/Users/nmend/AppData/Local/Temp/claude")
LLAIMA = (T / "v1_38639658446/i1/experiments/_s146_ab_sin_test1/salidas/38639658446/_s146_ab_control/Llaima.json",
          T / "v1_38639658446/i3/_s146_ab_control/Llaima.json")
COPAHUE = (T / "w2a_38853230521/i1/experiments/_s151_ab_diurno/salidas/38853230521/_s151_ab_diurno_on/Copahue.json",
           T / "w2a_38853230521/i2/_s151_ab_diurno_on/Copahue.json")


def _reales(rutas):
    if not all(p.exists() for p in rutas):
        pytest.skip("salidas del A/B no estan en disco")
    return [json.loads(p.read_text(encoding="utf-8")) for p in rutas]


@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
@pytest.mark.parametrize("rutas, vol, n", [(LLAIMA, "Llaima", 2), (COPAHUE, "Copahue", 1)])
def test_real_une_con_hotspot_escena(rutas, vol, n):
    salida, inf = ui.unir(_reales(rutas), vol)
    assert inf["ok"] and inf["estados"]["distinto"] == 0
    assert inf["estados"]["hotspot_escena"] == n == len(salida["_union_intentos"]["hotspot_escena"])


@pytest.mark.skipif(not HAY_NODE, reason="el predicado del tablero corre con node")
def test_real_copahue_conserva_el_record_del_primer_intento():
    docs = _reales(COPAHUE)
    salida, inf = ui.unir(docs, "Copahue")
    (h,) = inf["hotspot_escena"]
    assert h["clave"] == ["MODIS_AQUA", "2026-06-18 07:30"]
    assert h["valores"]["vrp_mw"] == [4.782, 1.834] and h["conservado"] == 1
    r = [x for x in salida["records"] if x["sensor"] == "MODIS_AQUA" and x["datetime_utc"].startswith("2026-06-18 07:30")]
    assert len(r) == 1 and r[0]["vrp_mw"] == 4.782 and r[0]["final_hotspot_source"] == "test1"


@pytest.mark.parametrize("campo", ["distance_class", "primary_cluster", "t_max_k"])
def test_real_llaima_con_una_condicion_rota_no_une(campo):
    docs = _reales(LLAIMA)
    for r in docs[1]["records"]:
        if r["sensor"] == "MODIS_TERRA" and r["datetime_utc"].startswith("2026-10-06 01:45"):
            r[campo] = {"distance_class": "far", "t_max_k": r["t_max_k"] + 0.5,
                        "primary_cluster": dict(r["primary_cluster"], n_pixels=99)}[campo]
    salida, inf = ui.unir(docs, "Llaima")
    assert not inf["ok"] and salida is None
    assert any(campo in d["campos"] for d in inf["distintos"])
