# -*- coding: utf-8 -*-
"""S165 V375-E (PD3): la vía «código MIROVA» para VIIRS 375 (pipeline/mirova_v750_codigo.py con FAMILIAS["VIIRS375"]),
apagada por flag (`enable_v375_codigo_mirova`).

POR QUÉ. V375-C midió que el código de VIIRS 750 de MIROVA, llevado a 375 cambiando sólo lo que el código hace depender
del sensor y con la caja C13 en el cráter (PD1), da la magnitud de MIROVA al milésimo (C13: 0,999) donde K la da a dos
tercios. Antes de medir el paquete contra K (PREREGISTRO_E.md) la vía tiene que vivir en pipeline/, apagada. Nicolás
autorizó cablearla APAGADA en el chat de esta sesión (A45, 2026-10-27, tag pre-s165-via-375); encenderla es otra decisión
suya. Pre-registro de implementación: experiments/_s165_v375_via/PREREGISTRO_IMPL_V375E.md. Cada cosa con su prueba:
  1. el flag existe, se lee de `pipeline.profile` bajo `thresholds:` (S124, A89) y está apagado en los tres perfiles;
  2. los números de 375 son los del port (`mirova_port.SENSORES["VIIRS375"]`) y la grilla es la que guardó el lote;
  3. la caja es, celda por celda, la del brazo C13 de `brazos.py` (ROI1 física de S159 y 13 x 13 en el cráter);
  4. sobre siete grillas del lote la vía da la máscara del port índice por índice, los mismos conteos de cada pase y el
     VRP de MATLAB en las escenas de 1 a 4 píxeles (sobre 4, el del port a 1e-3 MW); código independiente, armado por
     `tests/datos_s165_v375/armar_fixtures.py`;
  5. con el flag apagado el procesador de 375 no toca la vía y da bit a bit lo que daba el código del tag
     (`tests/datos_s165_v375/v375_k_antes.json`); con el flag encendido el record SÍ cambia (A116);
  6. el almacén no calcula el núcleo F5 para un record de la vía (la suma de MIROVA no se recorta) y sí para uno de K.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))
sys.path.insert(0, str(REPO / "experiments" / "_s162_v375"))

from pipeline import mirova_v750_codigo as MV  # noqa: E402

DATOS = REPO / "tests" / "datos_s165_v375"
ESPERADO = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))
PASADAS = {p["id"]: p for p in ESPERADO["pasadas"]}
OBJETIVOS = json.loads((REPO / "experiments/_s162_v375/objetivos_v375_bc.json").read_text(encoding="utf-8"))["pasadas"]


def _fam():
    return MV.FAMILIAS["VIIRS375"]


def _flag(perfil):
    """Lee el flag como lo lee el código: importando pipeline.profile con el perfil elegido (A89)."""
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", "import pipeline.profile as p; print(p.ENABLE_V375_CODIGO_MIROVA)"],
                       cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout.strip().splitlines()[-1]


def _volcanes():
    import yaml
    return {x["name"]: x for x in yaml.safe_load((REPO / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}


def _grilla(pid):
    z = np.load(DATOS / f"grilla_{pid}.npz")
    return z["mir"].astype(float), z["tir"].astype(float)


def _a_brazos(g):
    """La grilla de la vía en el formato de brazos.py / mirova_port (celda, X0, Y0)."""
    return {"epsg": g["epsg"], "ul_x": g["ul_x"], "ul_y": g["ul_y"], "n": g["n"], "celda": g["paso"],
            "X0": g["x0"], "Y0": g["y0"], "centro_lat": g["centro_lat"], "centro_lon": g["centro_lon"]}


# ------------------------------------------------------------------------------------------------ 1. el flag
@pytest.mark.parametrize("perfil", ["mirova_equivalent", "experimental", "experimental_ndc_focus"])
def test_flag_apagado_en_produccion_y_laboratorio(perfil):
    assert _flag(perfil) == "False"


def test_flag_se_lee_de_thresholds_y_llega_al_procesador():
    src = (REPO / "pipeline" / "profile.py").read_text(encoding="utf-8")
    assert 'ENABLE_V375_CODIGO_MIROVA: bool = bool(_t.get("enable_v375_codigo_mirova", False))' in src
    from pipeline import process_viirs as PV
    assert PV.ENABLE_V375_CODIGO_MIROVA is False


# ------------------------------------------------------------------------------------------------ 2. números y grilla
def test_constantes_de_375_son_las_del_port():
    import brazos as BR          # pone experiments/_s159/portes en el path e importa mirova_port
    MP = BR.MP
    s, f = MP.SENSORES["VIIRS375"], _fam()
    assert f["lam_mir"] == s["lam_mir"] == 3.74 and f["lam_tir"] == s["lam_tir"] == 11.45
    assert f["coef"] == pytest.approx(s["coef"] * s["area"] / 1e6, rel=1e-15)
    assert f["coef"] == pytest.approx(1.80e7 * 0.140625 / 1e6, rel=1e-15)
    assert f["paso_m"] == 375.0 and MV.n_celdas(f["paso_m"]) == 134
    assert f["bandas"] == ("I04", "I05") and f["lado_sensible"] == 13
    assert f["roi1_half_m"] == MP.HALF_ROI1_M == 7875.0 and f["dist_max_centro_km"] == 5.0
    # 750 y MODIS no cambian
    assert MV.FAMILIAS["VIIRS750"]["coef"] == pytest.approx(1.97e7 * 0.5625 / 1e6)
    assert MV.FAMILIAS["MODIS"]["paso_m"] == 1000.0


def test_grilla_de_375_es_la_que_guardo_el_lote():
    vistos = {}
    for o in OBJETIVOS:
        vistos.setdefault(o["volcan"], o["grilla"])
    assert len(vistos) >= 9
    for nombre, go in vistos.items():
        g = MV.grilla_del_volcan(nombre, paso_m=_fam()["paso_m"], clave_roi=_fam()["clave_roi"])
        assert g["epsg"] == go["epsg"] and g["n"] == go["n"] == 134 and g["paso"] == go["celda"] == 375.0, nombre
        for a, b in (("ul_x", "ul_x"), ("ul_y", "ul_y"), ("x0", "X0"), ("y0", "Y0"), ("centro_lat", "centro_lat"),
                     ("centro_lon", "centro_lon")):
            assert g[a] == pytest.approx(go[b], abs=0.06), (nombre, a)   # el lote guarda al décimo de metro


# ------------------------------------------------------------------------------------------------ 3. la caja C13
def test_caja_de_375_es_la_del_brazo_c13_en_los_volcanes_con_grilla():
    import brazos as BR
    V = _volcanes()
    con_grilla = [n for n in V if MV.grilla_del_volcan(n, paso_m=375.0) is not None]
    assert len(con_grilla) == 11
    for nombre in con_grilla:
        v = V[nombre]
        g = MV.grilla_del_volcan(nombre, paso_m=375.0, clave_roi=_fam()["clave_roi"])
        vlat, vlon = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
        gb = _a_brazos(g)
        xc, yc = BR.crater_xy(gb, vlat, vlon)
        esperada = BR.caja(gb, "C13", gb["X0"], gb["Y0"], xc, yc, v["inner_radius_km"], nombre)
        box = MV.caja_v375(g, vlat, vlon)
        assert np.array_equal(box, esperada), nombre
        X, Y = BR.MP.centros(gb)
        roi1 = (np.abs(X - gb["X0"]) <= 7875.0) & (np.abs(Y - gb["Y0"]) <= 7875.0)
        assert (box == 2).sum() == 169 and roi1.sum() == 42 * 42 and ((box == 1) == (roi1 & (box != 2))).all(), nombre


# ------------------------------------------------------------------------------------------------ 4. identidad
def _via_sobre_grilla(pid):
    p = PASADAS[pid]
    v = _volcanes()[p["volcan"]]
    g = MV.grilla_del_volcan(p["volcan"], paso_m=375.0, clave_roi=_fam()["clave_roi"])
    vlat, vlon = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
    mir, tir = _grilla(pid)
    box = MV.caja_v375(g, vlat, vlon)
    rec = MV.procesar_grilla(mir, tir, g, box, p["dayflag"], p["sunglint"], MV.posicion_de(g, vlat, vlon),
                             v["inner_radius_km"], p["sensor"], familia="VIIRS375")
    mascara, d = MV.detectar_mirova(mir, tir, box, p["dayflag"], p["sunglint"], devolver_diag=True,
                                    lam_mir=_fam()["lam_mir"], lam_tir=_fam()["lam_tir"])
    return rec, mascara, d, mir


@pytest.mark.parametrize("pid", sorted(PASADAS))
def test_identidad_con_el_port_c13(pid):
    p = PASADAS[pid]
    rec, mascara, d, mir = _via_sobre_grilla(pid)
    esperada = sorted(tuple(x) for x in p["mascara"])
    assert sorted(zip(*map(lambda a: a.tolist(), np.nonzero(mascara)))) == esperada
    assert sorted((q["fila"], q["col"]) for q in rec["anomaly_pixels"]) == esperada
    assert (d.get("n_abs"), d.get("n_p1"), d.get("n_p2")) == (p["n_abs"], p["n_p1"], p["n_p2"])
    assert rec["n_anomalous_pixels"] == p["npix"] and rec["via_codigo_mirova"] is True
    if p["npix"] == 0:
        assert rec["vrp_mw"] == 0.0 and rec["primary_cluster"] is None
        return
    v = MV.vrp_mirova(mir, mascara, coef=_fam()["coef"])
    if p["fuente_vara"] == "matlab":
        assert v["VRP_MW"] == pytest.approx(p["vrp_vara_mw"], rel=1e-9)
    else:
        assert abs(v["VRP_MW"] - p["vrp_vara_mw"]) <= 1e-3
    assert rec["vrp_mw"] == round(v["VRP_MW"], 3) == rec["primary_cluster"]["vrp_mw"]


def test_las_fixtures_ejercen_lo_que_dicen():
    """Control: si una fixture no tuviera el fondo de MATLAB distinto del port, la prueba de 1 a 4 píxeles no vería un
    relleno equivocado; si ninguna fuera protegida grande, no vería la suma de muchos alertados."""
    m = [p for p in ESPERADO["pasadas"] if p["fuente_vara"] == "matlab"]
    assert sum(abs(p["vrp_vara_mw"] - p["vrp_port_mw"]) > 1e-3 for p in m) >= 2
    assert any(p["protegida"] and p["npix"] > 10 for p in ESPERADO["pasadas"])
    assert any(p["npix"] == 0 for p in ESPERADO["pasadas"])


def test_calcular_vrp_granulo_de_375_usa_la_caja_c13_y_las_bandas_i():
    """De punta a punta: un «gránulo» cuyos píxeles son los centros de la grilla (el remuestreo lineal los devuelve
    tal cual) da la misma máscara que la fixture. Si calcular_vrp_granulo armara la caja de 750 o leyera M13, no."""
    pid = 1305
    p = PASADAS[pid]
    v = _volcanes()[p["volcan"]]
    g = MV.grilla_del_volcan(p["volcan"], paso_m=375.0, clave_roi=_fam()["clave_roi"])
    mir, tir = _grilla(pid)
    fil, col = np.indices(mir.shape)
    lat = np.empty(mir.shape)
    lon = np.empty(mir.shape)
    for f, k in zip(fil.ravel(), col.ravel()):
        lat[f, k], lon[f, k] = MV.latlon_de(g, f, k)
    ang = {"sensor_zenith": np.zeros(mir.shape), "solar_zenith": np.full(mir.shape, 120.0),
           "sensor_azimuth": np.zeros(mir.shape), "solar_azimuth": np.zeros(mir.shape)}
    rec = MV.calcular_vrp_granulo({"I04": mir, "I05": tir}, lat, lon, ang, p["volcan"],
                                  v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]), v["inner_radius_km"],
                                  "VIIRS_NOAA20", familia="VIIRS375")
    assert sorted((q["fila"], q["col"]) for q in rec["anomaly_pixels"]) == sorted(tuple(x) for x in p["mascara"])
    assert rec["diag_codigo_mirova"]["dayflag"] == 0


def test_leer_radiancia_l1b_lee_las_bandas_i(tmp_path):
    import h5py
    ruta = tmp_path / "VJ102IMG.A2026283.0654.021.nc"
    dn = np.array([[100, 65528], [200, 300]], np.uint16)
    with h5py.File(ruta, "w") as f:
        obs = f.create_group("observation_data")
        for b, sf in (("I04", 0.5), ("I05", 0.25)):
            ds = obs.create_dataset(b, data=dn)
            ds.attrs["scale_factor"] = np.float32(sf)
            ds.attrs["add_offset"] = np.float32(1.0)
    rad = MV.leer_radiancia_l1b(ruta, bandas=_fam()["bandas"])
    assert sorted(rad) == ["I04", "I05"]
    assert rad["I04"][0, 0] == 51.0 and rad["I05"][1, 1] == 76.0 and np.isnan(rad["I04"][0, 1])
    assert MV.leer_radiancia_l1b(ruta) is None          # el default sigue siendo M13/M15 (VIIRS 750)


# ------------------------------------------------------------------------------------------------ 5. cableado
def _canon(obj):
    import arnes_sintetico_s142 as arnes
    return json.dumps(arnes._redondear(obj), sort_keys=True, default=arnes._a_json, ensure_ascii=False)


def test_flag_apagado_bit_a_bit_con_k_de_antes(tmp_path):
    """Con el flag apagado, las escenas de 375 del arnés S142 dan el texto que daba el código del tag pre-s165-via-375
    (congelado en v375_k_antes.json desde un árbol extraído del tag, mismo redondeo que el golden de S142)."""
    from arnes_sintetico_s142 import correr_en_subproceso
    hoy = correr_en_subproceso(tmp_path, solo="v375")
    antes = json.loads((DATOS / "v375_k_antes.json").read_text(encoding="utf-8"))
    assert _canon(json.loads(hoy)["v375"]) == _canon(antes["v375"])
    assert antes["v375"]["foco_3x3|kernel=False"]["vrp_mir_mw"] > 0      # el golden no es trivial


class _K(Exception):
    pass


class _ViaTocada(Exception):
    pass


def _args(nombre="NevadosDeChillan"):
    v = _volcanes()[nombre]
    return v["lat"], v["lon"]


def test_flag_apagado_no_toca_la_via(monkeypatch):
    from pipeline import process_viirs as PV
    monkeypatch.setattr(PV, "ENABLE_V375_CODIGO_MIROVA", False)
    monkeypatch.setattr(PV, "read_viirs_l1b", lambda *_a, **_k: (_ for _ in ()).throw(_K()))
    for nombre in ("grilla_del_volcan", "leer_radiancia_l1b", "leer_geo_l1b", "calcular_vrp_granulo",
                   "volcan_por_coordenadas"):
        monkeypatch.setattr(MV, nombre, lambda *_a, **_k: (_ for _ in ()).throw(_ViaTocada()))
    with pytest.raises(_K):
        PV.calculate_vrp(Path("VJ102IMG.A2026283.0654.021.nc"), Path("VJ103IMG.A2026283.0654.021.nc"), *_args())


def test_flag_encendido_devuelve_el_record_de_la_via(monkeypatch):
    from pipeline import process_viirs as PV
    monkeypatch.setattr(PV, "ENABLE_V375_CODIGO_MIROVA", True)
    monkeypatch.setattr(PV, "read_viirs_l1b", lambda *_a, **_k: (_ for _ in ()).throw(_K()))
    llamado = {}

    def leer(ruta, bandas=("M13", "M15")):
        llamado["bandas"] = bandas
        return {"I04": 1, "I05": 2}
    monkeypatch.setattr(MV, "leer_radiancia_l1b", leer)
    monkeypatch.setattr(MV, "leer_geo_l1b", lambda p: ("lat", "lon", {}))

    def falso(rad, lat, lon, ang, nombre, vlat, vlon, inner, sensor, familia="VIIRS750"):
        llamado.update(nombre=nombre, vlat=vlat, inner=inner, sensor=sensor, familia=familia, rad=rad, geo=lat)
        return {"vrp_mw": 1.5, "via_codigo_mirova": True}
    monkeypatch.setattr(MV, "calcular_vrp_granulo", falso)
    r = PV.calculate_vrp(Path("VJ102IMG.A2026283.0654.021.nc"), Path("VJ103IMG.A2026283.0654.021.nc"), *_args(),
                         vent_lat=-36.87, vent_lon=-71.38, inner_radius_km=5.0)
    assert r.get("via_codigo_mirova") is True and r.get("granule") == "VJ102IMG.A2026283.0654.021.nc"
    assert r.get("datetime_utc") == "2026-10-10 06:54" and r.get("product_version") == "standard"
    assert llamado == {"bandas": ("I04", "I05"), "nombre": "NevadosDeChillan", "vlat": -36.87, "inner": 5.0,
                       "sensor": "VIIRS_NOAA20", "familia": "VIIRS375", "rad": {"I04": 1, "I05": 2}, "geo": "lat"}


def test_flag_encendido_cambia_el_record_y_sin_grilla_sigue_k_y_lo_dice(monkeypatch):
    """Control del bit a bit (A116) y A118: el arnés corre en coordenadas que no son de ningún volcán con grilla, así
    que con el flag encendido corre K y el record lleva la marca "sin_grilla"; con el flag apagado la marca no existe.
    El resto del record es el de K."""
    import arnes_sintetico_s142 as arnes
    from pipeline import process_viirs as PV
    assert MV.volcan_por_coordenadas(arnes.LAT0, arnes.LON0) is None
    monkeypatch.setattr(MV, "leer_radiancia_l1b", lambda *_a, **_k: (_ for _ in ()).throw(_ViaTocada()))
    apagado = arnes.correr_v375("foco_3x3", False, {})
    monkeypatch.setattr(PV, "ENABLE_V375_CODIGO_MIROVA", True)
    encendido = arnes.correr_v375("foco_3x3", False, {})
    assert "via_codigo_mirova" not in apagado
    assert encendido.get("via_codigo_mirova") == "sin_grilla"
    encendido.pop("via_codigo_mirova", None)
    assert _canon(encendido) == _canon(apagado)


def test_flag_encendido_con_granulo_fuera_del_volcan_devuelve_none(monkeypatch):
    from pipeline import process_viirs as PV
    monkeypatch.setattr(PV, "ENABLE_V375_CODIGO_MIROVA", True)
    monkeypatch.setattr(PV, "read_viirs_l1b", lambda *_a, **_k: (_ for _ in ()).throw(_K()))
    monkeypatch.setattr(MV, "leer_radiancia_l1b", lambda *_a, **_k: {"I04": 1, "I05": 2})
    monkeypatch.setattr(MV, "leer_geo_l1b", lambda p: ("lat", "lon", {}))
    monkeypatch.setattr(MV, "calcular_vrp_granulo", lambda *_a, **_k: None)
    assert PV.calculate_vrp(Path("VJ102IMG.A2026283.0654.021.nc"), Path("VJ103IMG.nc"), *_args()) is None


def test_run_pipeline_no_indexa_campos_de_k_en_el_log_de_375():
    """Un record de la vía no trae vrp_mir_mw, vrp_tir_mw, t_max_i04_k ni n_vent_pixels; el log de 375 los leía con
    corchetes DESPUÉS de guardar el record, y el KeyError salía como «ERROR processing» de un record guardado."""
    src = (REPO / "scripts" / "run_pipeline.py").read_text(encoding="utf-8")
    for campo in ("vrp_mir_mw", "vrp_tir_mw", "t_max_i04_k", "n_vent_pixels"):
        assert not re.search(r"result\[\s*['\"]" + campo + r"['\"]\s*\]", src), campo


# ------------------------------------------------------------------------------------------------ 6. el almacén
def _record_via_iband(marca):
    r = {"datetime_utc": "2026-10-10 06:54", "sensor": "VIIRS_NOAA20", "vrp_mw": 14.073, "vrp_vent_mw": 0.0,
         "hotspot_lat": -36.86, "hotspot_lon": -71.37, "hotspot_dist_km": 0.4,
         "primary_cluster": {"vrp_mw": 14.073, "n_pixels": 3, "centroid_lat": -36.86, "centroid_lon": -71.37,
                             "centroid_dist_km": 0.4, "single_pixel_mode": False},
         "anomaly_pixels": [{"lat": -36.86, "lon": -71.37, "dist_km": 0.4, "bt_k": 330.0},
                            {"lat": -36.863, "lon": -71.37, "dist_km": 0.6, "bt_k": 320.0}],
         "distance_class": "summit", "product_version": "standard"}
    if marca is not None:
        r["via_codigo_mirova"] = marca
    return r


def test_almacen_no_recorta_con_el_nucleo_f5_la_suma_de_la_via(tmp_path, monkeypatch):
    """Los píxeles de la vía no traen vrp_mw por píxel: el núcleo F5 los sumaría como 0 y el tablero, que prefiere
    f5_core_vrp_mw, publicaría 0 MW donde la vía midió la suma de MIROVA."""
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    r = _record_via_iband(True)
    store.append_record("TestVolcano", r, inner_radius_km=5.0)
    assert "f5_core_vrp_mw" not in r and r["vrp_mw"] == 14.073


@pytest.mark.parametrize("marca", [None, "sin_grilla"])
def test_almacen_si_calcula_el_nucleo_f5_para_k(tmp_path, monkeypatch, marca):
    """Control: un record de K (sin marca, o con la marca de K "sin_grilla") sí pasa por el núcleo F5."""
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    r = _record_via_iband(marca)
    for q, w in zip(r["anomaly_pixels"], (10.0, 4.0)):
        q["vrp_mw"] = w
    store.append_record("TestVolcano", r, inner_radius_km=5.0)
    assert r["f5_core_vrp_mw"] == pytest.approx(14.0)
