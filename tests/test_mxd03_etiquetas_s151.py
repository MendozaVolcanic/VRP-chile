# -*- coding: utf-8 -*-
"""Tarea 1.17 del loop: tests del probe que re-etiqueta detecciones MODIS con la geolocalizacion MxD03.

POR QUE. El probe de #828 midio en 7 granulos (casi solo Lascar) que `_interp_geo`
(`pipeline/process_modis.py:342`) deja el pixel corrido de 1 a 3 km respecto de MxD03. De esa
posicion cuelgan la etiqueta summit/far y la publicacion en el tablero. El verificador de #834 pidio
cinco arreglos (v2), y estos tests fijan cada uno antes de gastar una corrida:

  1. la banda de cada record es el corrimiento que predice el modelo de #828 para su cenit, acimut y
     satelite (no una banda fija de 3 km), y el control queda limpio a cenit alto;
  2. las pasadas con alerta de MIROVA (y todas las protegidas, lectura A) y los B summit van en censo;
  3. el veredicto principal es la compuerta de la regla 1 de docs/MISSION.md (ninguna protegida se
     pierde) y el balance de la regla 2, no umbrales elegidos (A115);
  4. un brazo C' (la lat/lon interpolada por el MISMO parche) tiene que dar identico al brazo C;
  5. el evaluador: INCOMPLETO si falta un job o una protegida, CAMBIA POCO prohibido con la banda
     corta, neto aparte del bruto;
  6. el JSON se escribe por granulo.

Criterio y diseno: experiments/_s151_mxd03_etiquetas/README.md
"""
import ast
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "_s151_mxd03_etiquetas"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(EXP))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, str(ROOT / "tests"))
from produccion_pre_k import produccion_pre_k  # noqa: E402


# S153: esta sonda MxD03 (tarea 1.17) se diseno y sello sobre la produccion de ANTES de K: sus escenas sinteticas
# ejercen la rama del Test 1, la conectiva `min` y la banda 21, y sus mutaciones estan calibradas contra eso.
# Desde la adopcion de K (#848) la produccion ya no tiene esa rama, asi que cada test del modulo corre con los
# procesadores en la deteccion del ancla congelada (tests/produccion_pre_k.py). Sin esto las pruebas sinteticas
# caen y, peor, las mutaciones quedan "atrapadas" por fallas que no son las suyas (A116).
@pytest.fixture(autouse=True)
def _produccion_pre_k():
    with produccion_pre_k():
        yield


import seleccionar_mxd03 as S  # noqa: E402
import evaluar_mxd03 as E  # noqa: E402


def _rec(final=None, pc=None, dc="far", sensor="MODIS_AQUA", z=10.0, az=-80.0, dt="2026-03-14 07:05",
         granule="MYD021KM.A2026073.0705.061.2026074000000.hdf"):
    r = {"final_hotspot_dist_km": final, "distance_class": dc, "sensor": sensor, "datetime_utc": dt,
         "granule": granule, "sensor_zenith_deg": z, "sensor_azimuth_deg": az}
    r["primary_cluster"] = None if pc is None else {"centroid_dist_km": pc, "vrp_mw": 0.3}
    return r


# ------------------------------------------------------------------ 1. modelo de corrimiento y bandas
@pytest.mark.parametrize("cenit,acimut,sensor,lo,hi", [
    (44.7, 101.07, "MODIS_AQUA", 2.6, 3.2),     # #828 A2026073.0705: midio 2,58, su modelo dio 2,82
    (40.0, 101.22, "MODIS_AQUA", 2.0, 2.6),     # #828 A2026086.0710: midio 2,21
    (31.3, -99.91, "MODIS_TERRA", 1.3, 1.9),    # #828 A2026078.0155: lado del frame 0 en Terra
    (30.5, -82.64, "MODIS_AQUA", 0.1, 0.5),     # otro lado: midio 0,25
    (65.0, 101.0, "MODIS_AQUA", 8.5, 10.5),     # el verificador: 9,6 km a 65 grados
    (54.0, 101.0, "MODIS_AQUA", 4.3, 5.3),      # 4,8 km a 54 grados
])
def test_corrimiento_predicho_reproduce_828_y_el_verificador(cenit, acimut, sensor, lo, hi):
    assert lo <= S.corrimiento_predicho(cenit, acimut, sensor) <= hi


def test_sin_angulos_no_hay_prediccion_y_la_banda_es_la_maxima():
    assert S.corrimiento_predicho(None, 10.0, "MODIS_AQUA") is None
    r = _rec(4.0, None, z=None, az=None)
    assert S.banda(r) >= 9.5


def test_estrato_usa_la_banda_del_record():
    # a cenit bajo la banda es ~1 km: un hotspot a 2,5 km del limite no alcanza
    assert S.estrato(_rec(7.5, None, z=10.0, az=-80.0), inner=5.0) == "fuera"
    # a 60 grados del lado del frame 0 si alcanza
    assert S.estrato(_rec(7.5, None, z=60.0, az=100.0), inner=5.0) == "A"


def test_estrato_b_se_parte_en_summit_y_far():
    assert S.estrato(_rec(21.0, 5.3, dc="summit"), inner=5.0) == "B_summit"
    assert S.estrato(_rec(21.0, 5.3, dc="far"), inner=5.0) == "B_far"


def test_control_limpio_a_cenit_alto():
    """A 65 grados el corrimiento predicho pasa de 9 km: 8 km del limite NO es control."""
    r_bajo = _rec(21.0, 13.5, z=10.0, az=-80.0)
    r_alto = _rec(21.0, 13.5, z=65.0, az=100.0)
    assert S.estrato(r_bajo, inner=5.0) == "control"
    assert S.estrato(r_alto, inner=5.0) != "control"


def test_clave_granulo():
    assert S.clave_granulo(_rec()) == "MYD021KM.A2026073.0705"
    assert S.clave_granulo(_rec(sensor="MODIS_TERRA", dt="2026-03-16 01:15", granule=None)) == "MOD021KM.A2026075.0115"


def test_muestreo_determinista():
    xs = ["g%03d" % i for i in range(50)]
    assert S.muestrear(xs, 10) == S.muestrear(list(reversed(xs)), 10)
    assert sorted(S.muestrear(xs, 100)) == sorted(xs)


# ------------------------------------------------------------------ 2. censo y jobs
def _etiqueta_fija(tabla):
    def f(vol, r):
        return tabla.get(r["granule"], {"lab": "neg_limpio", "prot": False, "vrp_ref": None, "pub": 0})
    return f


def test_censo_de_alertas_protegidas_y_b_summit():
    recs = [_rec(21.0, 15.0, granule="MYD021KM.A2026%03d.0705.x.hdf" % d) for d in range(60, 100)]   # control
    recs += [_rec(5.5, 5.0, z=10.0, granule="MOD021KM.A2026%03d.0115.x.hdf" % d) for d in range(60, 100)]  # A
    recs += [_rec(21.0, 5.3, dc="summit", granule="MOD021KM.A2026%03d.0300.x.hdf" % d) for d in range(60, 63)]
    tabla = {"MYD021KM.A2026061.0705.x.hdf": {"lab": "pos", "prot": True, "vrp_ref": 3.0, "pub": 1},
             "MYD021KM.A2026062.0705.x.hdf": {"lab": "pos", "prot": False, "vrp_ref": 0.3, "pub": 0}}
    pob = S.construir_poblacion({"Lascar": recs}, {"Lascar": 5.0}, _etiqueta_fija(tabla),
                                ventana=("2026-03-01", "2026-10-12"), topes={"A": 30, "B_far": 6, "control": 4})
    m = pob["Lascar"]["muestra"]
    claves = {g["clave"] for g in m}
    assert "MYD021KM.A2026061.0705" in claves and "MYD021KM.A2026062.0705" in claves   # alertas en censo
    assert sum(g["estrato"] == "B_summit" for g in m) == 3                            # B summit entero
    assert sum(g["estrato"] == "A" for g in m) == 30
    assert sum(g["estrato"] == "control" and not g["censo"] for g in m) == 4
    assert pob["Lascar"]["n_protegidas"] == 1
    assert pob["Lascar"]["N"]["control"]["neg_limpio"] == 38


def test_repartir_en_jobs_parte_al_volcan_grande():
    pob = {"Lascar": {"muestra": [{"clave": "g%02d" % i} for i in range(55)]},
           "Isluga": {"muestra": [{"clave": "h%02d" % i} for i in range(20)]}}
    jobs = S.repartir_en_jobs(pob, max_por_job=40)
    assert set(jobs) == {"Lascar-1", "Lascar-2", "Isluga"}
    assert all(len(j["granulos"]) <= 40 for j in jobs.values())
    assert sorted(jobs["Lascar-1"]["granulos"] + jobs["Lascar-2"]["granulos"]) == ["g%02d" % i for i in range(55)]


# ------------------------------------------------------------------ 3. mismos argumentos que produccion
def _llamadas_en_run_pipeline(nombre):
    arbol = ast.parse((ROOT / "scripts" / "run_pipeline.py").read_text(encoding="utf-8"))
    pd_ = next(n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name == "process_date")
    return [n for n in ast.walk(pd_) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == nombre and isinstance(n.func.value, ast.Name)]


def test_calculate_vrp_con_los_mismos_argumentos_que_run_pipeline():
    import probe_etiquetas as P
    c = [x for x in _llamadas_en_run_pipeline("calculate_vrp") if x.func.value.id == "process_modis"]
    assert len(c) == 1 and len(c[0].args) == 5
    v = {"name": "X", "lat": -23.0, "lon": -67.0, "radius_km": 25, "vent_lat": -23.0, "vent_lon": -67.0}
    assert set(P.argumentos_calculate_vrp(v)) == {k.arg for k in c[0].keywords}


def test_append_record_con_los_mismos_argumentos_que_run_pipeline():
    import probe_etiquetas as P
    ll = [x for x in _llamadas_en_run_pipeline("append_record") if x.func.value.id == "store"]
    claves = {frozenset(k.arg for k in x.keywords) for x in ll}
    assert len(claves) == 1
    v = {"name": "X", "lat": -23.0, "lon": -67.0, "radius_km": 25}
    assert set(P.argumentos_append_record(v, overwrite=True)) == set(next(iter(claves)))


# ------------------------------------------------------------------ 4. comparacion, C' y escritura incremental
def test_comparar_clasifica_los_cambios():
    import probe_etiquetas as P
    c = {"dc": "summit", "n_anom": 2, "pc_vrp": 0.4}
    assert P.comparar(c, dict(c, dc="far"), 1, 0) == {"etiqueta": "summit->far", "pub": "1->0",
                                                      "deteccion_cambia": False}
    assert P.comparar(c, dict(c), 1, 1) == {"etiqueta": "igual", "pub": "igual", "deteccion_cambia": False}
    assert P.comparar(c, dict(c, n_anom=3), 1, 1)["deteccion_cambia"]
    assert P.comparar(None, dict(c, dc="far"), 0, 0)["etiqueta"] == "None->far"


def test_registros_iguales_ignora_solo_las_marcas_de_hora():
    import probe_etiquetas as P
    a = {"vrp_mw": 1.0, "distance_class": "summit", "processed_utc": "x", "first_processed_utc": "x"}
    assert P.registros_iguales(a, dict(a, processed_utc="y", first_processed_utc="y"))
    assert not P.registros_iguales(a, dict(a, distance_class="far"))
    assert not P.registros_iguales(a, None) and P.registros_iguales(None, None)


def test_desplazamiento_en_el_crater_mide_el_corrimiento_impuesto():
    import probe_etiquetas as P
    k = 40
    lats = -23.36 + (k - np.arange(81)) / 111.32
    lons = -67.73 + (np.arange(81) - k) / (111.32 * np.cos(np.radians(-23.36)))
    lat, lon = np.meshgrid(lats, lons, indexing="ij")
    d = P.desplazamiento_crater(lat + 1.5 / 111.32, lon, lat, lon, (-23.36, -67.73))
    assert abs(d["dn_km"] - 1.5) < 0.01 and abs(d["km"] - 1.5) < 0.01
    assert P.desplazamiento_crater(lat, lon, lat, lon, (-23.36, -67.73))["km"] < 1e-6


def test_mxd03_con_relleno_no_entra_como_posicion():
    import probe_etiquetas as P
    lat = np.full((3, 3), -23.0, dtype=np.float32)
    lat[0, 0] = -999.0
    out = P.limpiar_relleno(lat)
    assert np.isnan(out[0, 0]) and out[1, 1] == np.float32(-23.0)


def test_guardar_escribe_json_valido_en_cada_llamada(tmp_path):
    import probe_etiquetas as P
    p = tmp_path / "Lascar-1.json"
    P.guardar(p, {"job": "Lascar-1", "completo": False, "granulos": [{"clave": "a"}]})
    assert json.loads(p.read_text(encoding="utf-8"))["granulos"] == [{"clave": "a"}]
    P.guardar(p, {"job": "Lascar-1", "completo": True, "granulos": [{"clave": "a"}, {"clave": "b"}]})
    assert json.loads(p.read_text(encoding="utf-8"))["completo"] is True
    assert not list(tmp_path.glob("*.tmp"))


# ------------------------------------------------------------------ 5. de punta a punta (sintetico)
@pytest.mark.skipif(shutil.which("node") is None, reason="el predicado del tablero corre con node")
def test_el_instrumento_distingue_presente_ausente_y_su_control_negativo():
    import probar_probe_mxd03 as T
    r = T.correr()
    assert r["presente"]["comparacion"] == {"etiqueta": "summit->far", "pub": "1->0", "deteccion_cambia": False}
    assert abs(r["presente"]["desplazamiento"]["km"] - T.CORRIMIENTO_KM) < 0.05
    assert r["ausente"]["comparacion"] == {"etiqueta": "igual", "pub": "igual", "deteccion_cambia": False}
    assert r["presente"]["cprima_igual"] is True          # C' por el parche == C
    assert r["relleno"]["comparacion"]["etiqueta"] == "igual"   # MxD03 con relleno lejos no rompe nada


# ------------------------------------------------------------------ 6. evaluador
def _fila(clave, estrato="A", lab="neg_limpio", prot=False, censo=False, pred=1.0):
    return {"clave": clave, "estrato": estrato, "lab": lab, "prot": prot, "censo": censo,
            "corrimiento_predicho_km": pred, "datetime_utc": "2026-03-14 07:05", "sensor": "MODIS_AQUA"}


def _medida(clave, pub=("igual", 0, 0), etiqueta="igual", det=False, desp=0.5, cprima=None):
    p, pc, pm = pub
    return {"clave": clave, "estado": "ok", "pub_c": pc, "pub_m": pm, "cprima_igual": cprima,
            "desplazamiento": {"km": desp},
            "comparacion": {"etiqueta": etiqueta, "pub": p, "deteccion_cambia": det}}


def _caso(filas_por_vol, medidas_por_vol, N=None, jobs=None):
    pob = {"volcanes": {}, "jobs": {}}
    sal = {}
    for vol, filas in filas_por_vol.items():
        n = N[vol] if N else {}
        if not n:
            for f in filas:
                n.setdefault(f["estrato"], {}).setdefault(f["lab"], 0)
                n[f["estrato"]][f["lab"]] += 1
        pob["volcanes"][vol] = {"N": n, "n_pub_tramo": 100, "muestra": filas}
        pob["jobs"][vol] = {"volcan": vol, "granulos": [f["clave"] for f in filas]}
        if vol in medidas_por_vol:
            sal[vol] = {"job": vol, "volcan": vol, "completo": True, "granulos": medidas_por_vol[vol]}
    return pob, sal


def _limpio(vol, n=10):
    filas = [_fila("%s%d" % (vol, i)) for i in range(n)]
    meds = [_medida(f["clave"], cprima=(True if i == 0 else None)) for i, f in enumerate(filas)]
    return filas, meds


def test_sin_cambios_da_sin_cambio_observado():
    f, m = _limpio("a")
    pob, sal = _caso({"a": f}, {"a": m})
    assert E.evaluar(pob, sal)["veredicto"] == "SIN CAMBIO OBSERVADO"


def test_c_prima_distinto_invalida_el_instrumento():
    f, m = _limpio("a")
    m[0]["cprima_igual"] = False
    pob, sal = _caso({"a": f}, {"a": m})
    assert E.evaluar(pob, sal)["veredicto"] == "INVALIDO"


def test_sin_ningun_c_prima_el_instrumento_no_esta_controlado():
    f, m = _limpio("a")
    m[0]["cprima_igual"] = None
    pob, sal = _caso({"a": f}, {"a": m})
    assert E.evaluar(pob, sal)["veredicto"] == "INCOMPLETO"


def test_falta_un_job_pedido_da_incompleto():
    fa, ma = _limpio("a")
    fb, _ = _limpio("b")
    pob, sal = _caso({"a": fa, "b": fb}, {"a": ma})
    assert E.evaluar(pob, sal)["veredicto"] == "INCOMPLETO"


def test_falta_una_protegida_da_incompleto():
    f, m = _limpio("a")
    f.append(_fila("prot1", estrato="control", lab="pos", prot=True, censo=True))
    pob, sal = _caso({"a": f}, {"a": m})          # la protegida no se midio (10 de 11, bajo el 20 %)
    assert E.evaluar(pob, sal)["veredicto"] == "INCOMPLETO"


def test_perder_una_protegida_es_la_compuerta():
    f, m = _limpio("a")
    f.append(_fila("prot1", estrato="control", lab="pos", prot=True, censo=True))
    m.append(_medida("prot1", pub=("1->0", 1, 0)))
    pob, sal = _caso({"a": f}, {"a": m})
    r = E.evaluar(pob, sal)
    assert r["veredicto"] == "PIERDE PROTEGIDA" and r["regla1"]["perdidas"] == 1


def test_balance_mejora_cuando_se_apagan_publicaciones_de_mas():
    filas = [_fila("n%d" % i) for i in range(30)]
    meds = [_medida(f["clave"], pub=("1->0", 1, 0) if i < 20 else ("igual", 1, 1), cprima=(True if i == 0 else None))
            for i, f in enumerate(filas)]
    pob, sal = _caso({"a": filas}, {"a": meds})
    r = E.evaluar(pob, sal)
    assert r["regla2"]["delta_errores"] < 0 and r["veredicto"] == "MEJORA"


def test_balance_empeora_cuando_se_pierden_alertas_bajo_1_mw():
    f, m = _limpio("a", n=5)
    for i in range(8):
        f.append(_fila("al%d" % i, estrato="A", lab="pos", censo=True))
        m.append(_medida("al%d" % i, pub=("1->0", 1, 0)))
    pob, sal = _caso({"a": f}, {"a": m})
    r = E.evaluar(pob, sal)
    assert r["regla2"]["alertas_perdidas"] == 8 and r["veredicto"] == "EMPEORA"


def test_banda_corta_bloquea_el_balance_y_prohibe_cambia_poco():
    f, m = _limpio("a")
    for x in m:
        x["desplazamiento"]["km"] = 5.0           # predicho 1 km + 1 de margen: el modelo se quedo corto
    pob, sal = _caso({"a": f}, {"a": m})
    r = E.evaluar(pob, sal)
    assert r["banda_corta"] is True
    assert r["veredicto"] == "BANDA CORTA"
    assert r["magnitud"]["nivel"] != "CAMBIA POCO"


def test_neto_aparte_del_bruto_y_tipo_de_cambio():
    filas = [_fila("n%d" % i) for i in range(10)]
    meds = [_medida(f["clave"], cprima=(True if i == 0 else None)) for i, f in enumerate(filas)]
    meds[1] = _medida("n1", pub=("1->0", 1, 0), etiqueta="summit->far")
    meds[2] = _medida("n2", pub=("0->1", 0, 1), etiqueta="far->summit", det=True)
    meds[3] = _medida("n3", pub=("1->0", 1, 0), etiqueta="summit->far")
    pob, sal = _caso({"a": filas}, {"a": meds})
    mg = E.evaluar(pob, sal)["magnitud"]
    assert mg["bruto"] == {"1->0": 2, "0->1": 1} and mg["neto_observado"] == -1
    assert mg["por_tipo"] == {"misma_deteccion_otra_etiqueta": 2, "otra_deteccion": 1}


def test_el_control_que_cambia_queda_anotado():
    f, m = _limpio("a")
    for i in range(4):
        f.append(_fila("c%d" % i, estrato="control"))
        m.append(_medida("c%d" % i, etiqueta="far->summit" if i < 2 else "igual", det=True))
    pob, sal = _caso({"a": f}, {"a": m})
    assert E.evaluar(pob, sal)["control_cambia"] is True


def test_wilson_bordes():
    assert E.wilson(0, 0) == (0.0, 1.0)
    lo, hi = E.wilson(0, 10)
    assert lo == 0.0 and 0.25 < hi < 0.35


# ------------------------------------------------------------------ 7. tercera vuelta: el intervalo de Delta
# El verificador de #835 simulo el nulo (todo medido, nada cambia) con la poblacion real y obtuvo
# Delta en [-2.265, +2.265]: con un solo 0->1 salia INDETERMINADO y MEJORA/EMPEORA eran inalcanzables.
# El 97 % del ancho venia de B far, fuera y control, que el modelo declara inmoviles y que se muestrean
# con 3 a 6 granulos por volcan. Desde v3 Delta se decide con A expandido (Wilson por volcan) mas los
# censos en conteo exacto; los estratos inmoviles son la prueba del modelo.
ANCHO_MAX_NULO = 90.0    # ancho total (hi - lo) de Delta bajo el nulo con poblacion.json; medido en v3: 88,0


def _nulo_real():
    pob = json.loads((EXP / "poblacion.json").read_text(encoding="utf-8"))
    sal = {}
    for j, x in pob["jobs"].items():
        sal[j] = {"job": j, "volcan": x["volcan"], "completo": True, "granulos": [
            _medida(c, cprima=(True if i == 0 else None)) for i, c in enumerate(x["granulos"])]}
    return pob, sal


def test_nulo_con_la_poblacion_real_tiene_ancho_acotado():
    pob, sal = _nulo_real()
    r = E.evaluar(pob, sal)
    lo, hi = r["regla2"]["delta_intervalo"]
    assert r["veredicto"] == "SIN CAMBIO OBSERVADO"
    assert hi - lo <= ANCHO_MAX_NULO, "el intervalo de Delta bajo el nulo volvio a inflarse: %s" % [lo, hi]
    assert hi - lo > 0, "A se muestrea: bajo el nulo su Wilson no puede dar ancho cero"


def test_un_cambio_en_a_no_vuelve_inalcanzable_el_veredicto():
    """Con la poblacion real, apagar 30 publicaciones de mas en A tiene que poder dar MEJORA."""
    pob, sal = _nulo_real()
    mover = {(v, g["clave"]) for v, d in pob["volcanes"].items() for g in d["muestra"]
             if g["estrato"] == "A" and g["lab"] == "neg_limpio" and not g["censo"]}
    for s in sal.values():
        for g in s["granulos"]:
            if (s["volcan"], g["clave"]) in mover:
                g.update(pub_c=1, pub_m=0, comparacion={"etiqueta": "summit->far", "pub": "1->0",
                                                        "deteccion_cambia": False})
    assert E.evaluar(pob, sal)["veredicto"] == "MEJORA"


def test_censo_entero_no_lleva_wilson():
    filas = [_fila("bs%d" % i, estrato="B_summit", censo=True) for i in range(7)]
    meds = [_medida(f["clave"], cprima=(True if i == 0 else None)) for i, f in enumerate(filas)]
    pob, sal = _caso({"a": filas}, {"a": meds})
    assert E.evaluar(pob, sal)["regla2"]["delta_intervalo"] == [0.0, 0.0]


@pytest.mark.parametrize("estrato", ["B_far", "fuera", "control"])
def test_cambio_en_estrato_inmovil_es_prueba_del_modelo(estrato):
    f, m = _limpio("a")
    f.append(_fila("x1", estrato=estrato))
    m.append(_medida("x1", etiqueta="far->summit"))
    pob, sal = _caso({"a": f}, {"a": m})
    r = E.evaluar(pob, sal)
    assert r["veredicto"] == "INDETERMINADO"
    assert any("el modelo de corrimiento no explica esto" in x for x in r["motivos_indeterminado"])
    assert r["modelo_falla"]["n"] == 1


def test_un_estrato_inmovil_sin_cambios_no_entra_al_intervalo():
    f, m = _limpio("a", n=4)
    for i in range(3):
        f.append(_fila("bf%d" % i, estrato="B_far"))
        m.append(_medida("bf%d" % i))
    pob, sal = _caso({"a": f}, {"a": m}, N={"a": {"A": {"neg_limpio": 4}, "B_far": {"neg_limpio": 2000}}})
    lo, hi = E.evaluar(pob, sal)["regla2"]["delta_intervalo"]
    assert hi - lo < 4.0     # solo A (4 records, 4 medidos: exacto); los 2.000 de B far no suman ancho
