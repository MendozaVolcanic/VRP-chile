# -*- coding: utf-8 -*-
"""Tarea 1.17 del loop: tests del probe que re-etiqueta detecciones MODIS con la geolocalizacion MxD03.

POR QUE. El probe de #828 midio en 7 granulos (casi solo Lascar) que `_interp_geo`
(`pipeline/process_modis.py:342`) deja el pixel corrido de 1 a 3 km respecto de MxD03. De esa
posicion cuelgan la etiqueta summit/far y la publicacion en el tablero. Estos tests fijan lo que el
probe tiene que cumplir antes de gastar una corrida en GitHub Actions:

  1. la poblacion (estratos A, B y control) sale de una regla escrita, no de mirar los datos;
  2. el muestreo es determinista y respeta los topes;
  3. el probe llama a `calculate_vrp` y a `store.append_record` con los MISMOS argumentos que
     `scripts/run_pipeline.py` (comparado por AST, no por subcadena: A92);
  4. el instrumento distingue un desplazamiento presente de uno ausente, de punta a punta, con el
     pipeline real y el predicado del tablero ejecutado con node (A97, A116);
  5. el veredicto sigue el criterio pre-registrado en el README.

Criterio y diseno: experiments/_s151_mxd03_etiquetas/README.md
"""
import ast
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

import seleccionar_mxd03 as S  # noqa: E402
import evaluar_mxd03 as E  # noqa: E402


def _rec(final=None, pc=None, dc="far", sensor="MODIS_AQUA", dt="2026-03-14 07:05",
         granule="MYD021KM.A2026073.0705.061.2026074000000.hdf"):
    r = {"final_hotspot_dist_km": final, "distance_class": dc, "sensor": sensor,
         "datetime_utc": dt, "granule": granule}
    r["primary_cluster"] = None if pc is None else {"centroid_dist_km": pc, "vrp_mw": 0.3}
    return r


# ------------------------------------------------------------------ 1. estratos
@pytest.mark.parametrize("final,pc,esperado", [
    (4.0, None, "A"),        # hotspot final a 1 km del limite de 5
    (7.9, 30.0, "A"),        # a 2,9 km por fuera: todavia A
    (21.0, 3.9, "B"),        # final lejos (el Salar), cumulo cerca del limite: B
    (21.0, 1.5, None),       # cumulo a 3,5 km del limite: banda intermedia
    (21.0, 12.0, "control"),  # todo a mas de 6 km del limite
    (9.5, None, None),       # a 4,5 km del limite: banda intermedia, fuera de la muestra
    (None, None, None),      # sin distancias
])
def test_estrato(final, pc, esperado):
    assert S.estrato(_rec(final, pc), inner=5.0) == esperado


def test_estrato_a_gana_sobre_b():
    """Si el hotspot final esta cerca del limite, el record es A aunque el cumulo tambien lo este."""
    assert S.estrato(_rec(5.5, 4.5), inner=5.0) == "A"


def test_control_exige_todas_las_distancias_lejos():
    assert S.estrato(_rec(21.0, 10.5), inner=5.0) is None   # cumulo a 5,5 km del limite
    assert S.estrato(_rec(21.0, 11.5), inner=5.0) == "control"


# ------------------------------------------------------------------ 2. clave y muestreo
def test_clave_granulo_desde_el_nombre():
    assert S.clave_granulo(_rec()) == "MYD021KM.A2026073.0705"
    r = _rec(sensor="MODIS_TERRA", granule="MOD021KM.A2026289.0145.061.2026289022621.NRT.hdf")
    assert S.clave_granulo(r) == "MOD021KM.A2026289.0145"


def test_clave_granulo_sin_nombre_sale_de_sensor_y_hora():
    r = _rec(sensor="MODIS_TERRA", dt="2026-03-16 01:15", granule=None)
    assert S.clave_granulo(r) == "MOD021KM.A2026075.0115"


def test_muestreo_determinista_y_con_tope():
    xs = ["g%03d" % i for i in range(50)]
    a = S.muestrear(xs, 10)
    assert len(a) == 10 and a == S.muestrear(list(reversed(xs)), 10)
    assert sorted(S.muestrear(xs, 100)) == sorted(xs)
    assert set(S.muestrear(xs, 10, sal="otra")) != set(a)


def test_construir_poblacion_respeta_topes_y_cuenta_la_poblacion():
    recs = ([_rec(4.5, 4.0, granule="MYD021KM.A2026%03d.0705.x.hdf" % d) for d in range(60, 100)]
            + [_rec(21.0, 4.0, granule="MOD021KM.A2026%03d.0115.x.hdf" % d) for d in range(60, 80)]
            + [_rec(21.0, 15.0, granule="MOD021KM.A2026%03d.0300.x.hdf" % d) for d in range(60, 70)]
            + [_rec(9.5, None, granule="MOD021KM.A2026%03d.0400.x.hdf" % d) for d in range(60, 65)]
            + [_rec(4.5, 4.0, dt="2026-02-01 07:05", granule="MYD021KM.A2026032.0705.x.hdf")])  # fuera de ventana
    p = S.construir_poblacion({"Lascar": recs}, {"Lascar": 5.0}, ventana=("2026-03-01", "2026-10-12"),
                              topes={"A": 30, "B": 8, "control": 6})
    v = p["Lascar"]
    assert v["N"] == {"A": 40, "B": 20, "control": 10, "medio": 5, "sin_distancia": 0, "total": 75}
    cuenta = {e: sum(1 for g in v["muestra"] if g["estrato"] == e) for e in ("A", "B", "control")}
    assert cuenta == {"A": 30, "B": 8, "control": 6}
    assert len({g["clave"] for g in v["muestra"]}) == 44


# ------------------------------------------------------------------ 3. mismos argumentos que produccion
def _llamada_en_run_pipeline(nombre_funcion):
    arbol = ast.parse((ROOT / "scripts" / "run_pipeline.py").read_text(encoding="utf-8"))
    pd_ = next(n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name == "process_date")
    llamadas = []
    for n in ast.walk(pd_):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == nombre_funcion and isinstance(n.func.value, ast.Name)):
            llamadas.append(n)
    return llamadas


def test_calculate_vrp_con_los_mismos_argumentos_que_run_pipeline():
    import probe_etiquetas as P
    modis = [c for c in _llamada_en_run_pipeline("calculate_vrp") if c.func.value.id == "process_modis"]
    assert len(modis) == 1
    c = modis[0]
    assert len(c.args) == 5
    v = {"name": "X", "lat": -23.0, "lon": -67.0, "radius_km": 25, "vent_lat": -23.0, "vent_lon": -67.0}
    assert set(P.argumentos_calculate_vrp(v)) == {k.arg for k in c.keywords}


def test_append_record_con_los_mismos_argumentos_que_run_pipeline():
    import probe_etiquetas as P
    llamadas = [c for c in _llamada_en_run_pipeline("append_record") if c.func.value.id == "store"]
    assert llamadas, "run_pipeline ya no llama store.append_record"
    claves = {frozenset(k.arg for k in c.keywords) for c in llamadas}
    assert len(claves) == 1, "las ramas de run_pipeline llaman append_record con argumentos distintos"
    v = {"name": "X", "lat": -23.0, "lon": -67.0, "radius_km": 25}
    assert set(P.argumentos_append_record(v, overwrite=True)) == set(next(iter(claves)))


# ------------------------------------------------------------------ 4. comparacion y desplazamiento
def test_comparar_clasifica_los_cambios():
    import probe_etiquetas as P
    c = {"dc": "summit", "n_anom": 2, "pc_vrp": 0.4}
    m = {"dc": "far", "n_anom": 2, "pc_vrp": 0.4}
    out = P.comparar(c, m, 1, 0)
    assert out == {"etiqueta": "summit->far", "pub": "1->0", "deteccion_cambia": False}
    out = P.comparar(c, dict(c), 1, 1)
    assert out == {"etiqueta": "igual", "pub": "igual", "deteccion_cambia": False}
    assert P.comparar(c, {"dc": "summit", "n_anom": 3, "pc_vrp": 0.4}, 1, 1)["deteccion_cambia"]
    assert P.comparar(None, m, 0, 0)["etiqueta"] == "None->far"


def test_desplazamiento_en_el_crater_mide_el_corrimiento_impuesto():
    import probe_etiquetas as P
    k = 40
    lats = -23.36 + (k - np.arange(81)) / 111.32
    lons = -67.73 + (np.arange(81) - k) / (111.32 * np.cos(np.radians(-23.36)))
    lat, lon = np.meshgrid(lats, lons, indexing="ij")
    d = P.desplazamiento_crater(lat + 1.5 / 111.32, lon, lat, lon, (-23.36, -67.73))
    assert abs(d["dn_km"] - 1.5) < 0.01 and abs(d["de_km"]) < 0.01 and abs(d["km"] - 1.5) < 0.01
    cero = P.desplazamiento_crater(lat, lon, lat, lon, (-23.36, -67.73))
    assert cero["km"] < 1e-6


def test_mxd03_con_relleno_no_entra_como_posicion():
    import probe_etiquetas as P
    lat = np.full((3, 3), -23.0, dtype=np.float32)
    lat[0, 0] = -999.0
    out = P.limpiar_relleno(lat)
    assert np.isnan(out[0, 0]) and out[1, 1] == np.float32(-23.0)


# ------------------------------------------------------------------ 5. de punta a punta (sintetico)
@pytest.mark.skipif(shutil.which("node") is None, reason="el predicado del tablero corre con node")
def test_el_instrumento_distingue_desplazamiento_presente_de_ausente(tmp_path):
    import probar_probe_mxd03 as T
    presente, ausente = T.correr()
    assert presente["comparacion"]["etiqueta"] == "summit->far"
    assert presente["comparacion"]["pub"] == "1->0"
    assert abs(presente["desplazamiento"]["km"] - T.CORRIMIENTO_KM) < 0.05
    assert ausente["comparacion"] == {"etiqueta": "igual", "pub": "igual", "deteccion_cambia": False}
    assert ausente["desplazamiento"]["km"] < 1e-6


# ------------------------------------------------------------------ 6. evaluador y veredicto
def test_wilson_bordes():
    lo, hi = E.wilson(0, 10)
    assert lo == 0.0 and 0.25 < hi < 0.35
    lo, hi = E.wilson(10, 10)
    assert 0.65 < lo < 0.75 and hi == pytest.approx(1.0)
    assert E.wilson(0, 0) == (0.0, 1.0)


def _vol(N_A, n_A, k_lab_A, k_pub_A, N_B=100, n_B=8, k_pub_B=0, n_ctrl=6, k_lab_ctrl=0,
         n_pub=100, faltan=0, desp=1.0):
    gr = []
    for i in range(n_A):
        gr.append({"estrato": "A", "estado": "ok", "desplazamiento": {"km": desp},
                   "comparacion": {"etiqueta": "summit->far" if i < k_lab_A else "igual",
                                   "pub": "1->0" if i < k_pub_A else "igual", "deteccion_cambia": False}})
    for i in range(n_B):
        gr.append({"estrato": "B", "estado": "ok", "desplazamiento": {"km": desp},
                   "comparacion": {"etiqueta": "igual", "pub": "1->0" if i < k_pub_B else "igual",
                                   "deteccion_cambia": False}})
    for i in range(n_ctrl):
        gr.append({"estrato": "control", "estado": "ok", "desplazamiento": {"km": desp},
                   "comparacion": {"etiqueta": "far->summit" if i < k_lab_ctrl else "igual",
                                   "pub": "igual", "deteccion_cambia": False}})
    for _ in range(faltan):
        gr.append({"estrato": "A", "estado": "error"})
    return {"N": {"A": N_A, "B": N_B, "control": 50, "medio": 0, "sin_distancia": 0,
                  "total": N_A + N_B + 50}, "n_pub_tramo": n_pub, "granulos": gr}


def test_veredicto_poco():
    vols = {v: _vol(20, 20, 0, 0) for v in ("a", "b", "c")}
    assert E.evaluar(vols)["veredicto"] == "CAMBIA POCO"


def test_veredicto_mucho_por_publicaciones():
    vols = {v: _vol(20, 20, 2, 2) for v in ("a", "b", "c")}      # 2 de 20 de A: 10 % de 20 -> 2 por volcan
    vols["d"] = _vol(100, 20, 4, 4, n_pub=10)                      # 20 % de 100 = 20 publicaciones movidas
    assert E.evaluar(vols)["veredicto"] == "CAMBIA MUCHO"


def test_un_solo_cambio_en_un_estrato_pesado_no_decide_mucho():
    """Un granulo B de Lastarria pesa 365/8 = 46 records: un cambio aislado da 7 % de 622 pero no basta."""
    vols = {v: _vol(20, 20, 0, 0, n_pub=60) for v in ("a", "b")}
    vols["c"] = _vol(20, 20, 0, 0, N_B=365, n_B=8, k_pub_B=1, n_pub=60)
    r = E.evaluar(vols)
    assert r["fraccion_publicaciones_movidas"] >= E.MUCHO_PUB
    assert r["veredicto"] != "CAMBIA MUCHO"


def test_veredicto_mucho_por_etiquetas_en_un_volcan():
    vols = {v: _vol(20, 20, 0, 0, n_pub=1000) for v in ("a", "b")}
    vols["c"] = _vol(30, 30, 15, 0, n_pub=1000)                    # 50 % de A cambia de etiqueta
    assert E.evaluar(vols)["veredicto"] == "CAMBIA MUCHO"


def test_veredicto_intermedio():
    vols = {v: _vol(20, 20, 0, 0, n_pub=100) for v in ("a", "b")}
    vols["c"] = _vol(20, 20, 5, 5, n_pub=100)   # publicaciones 5 de 300 (1,7 %); etiqueta: Wilson inferior 0,11
    assert E.evaluar(vols)["veredicto"] == "INTERMEDIO"


def test_veredicto_incompleto_si_un_volcan_pierde_mas_del_20_por_ciento():
    vols = {v: _vol(20, 20, 0, 0) for v in ("a", "b")}
    vols["c"] = _vol(20, 20, 0, 0, faltan=10)
    assert E.evaluar(vols)["veredicto"] == "INCOMPLETO"


def test_la_banda_corta_marca_cota_inferior():
    vols = {v: _vol(20, 20, 0, 0, desp=3.5) for v in ("a", "b")}
    r = E.evaluar(vols)
    assert r["cota_inferior"] is True


def test_el_control_que_cambia_queda_anotado():
    vols = {v: _vol(20, 20, 0, 0, n_ctrl=6, k_lab_ctrl=2) for v in ("a", "b")}
    assert E.evaluar(vols)["control_cambia"] is True
