# -*- coding: utf-8 -*-
"""S164 MOD-D fase 3: la vía «código MIROVA» para MODIS (pipeline/mirova_v750_codigo.py parametrizado por sensor),
apagada por flag (`enable_modis_codigo_mirova`).

POR QUÉ. El censo MOD-D (5.465 de 5.465 pasadas nocturnas, verificador limpio) midió que el código de VIIRS 750 de MIROVA
portado a MODIS, con el relleno del fondo según la regla de `fillmissing2` de MATLAB, se equivoca menos que K contra
MIROVA (P2: 8 errores contra 49) y acerca la magnitud (M MEJORA). Nicolás lo aprobó como CANDIDATO el 2026-10-26 y
confirmó en el chat de esta sesión que la vía entra a pipeline/ APAGADA (A45); encenderla es otra decisión suya. Antes
de que nadie la encienda, cada una de estas cosas tiene su prueba aquí:
  1. el flag existe, se lee de `pipeline.profile` bajo `thresholds:` (S124, A89) y está APAGADO en producción y en el
     laboratorio;
  2. con el flag apagado el procesador MODIS da bit a bit lo que daba K antes de este cambio (golden congelado con el
     árbol de pipeline/ sin tocar, `tests/datos_s164_modis/modis_k_antes.json`), y con el flag encendido el record SÍ
     cambia (control: si el flag no actuara, el "bit a bit" pasaría por construcción, A116);
  3. sobre cinco grillas del censo la vía da los mismos píxeles alertados que el port del censo y el VRP del port con
     la regla de MATLAB, calculado por código independiente (`delaunay_perturbado.py`, blob f273a47a del tag
     s162-modd-tag; ver `tests/datos_s164_modis/armar_fixtures.py`);
  4. el caso que decidió el CANDIDATO: Láscar 2026-04-25 07:35 da 1,1124 MW (el port con su propio desempate daba
     0,9731, bajo el corte de 1 MW de una alerta protegida);
  5. un volcán sin grilla de MIROVA sigue K y el record lo dice (A118);
  6. el almacén no aplica a un record MODIS de la vía las compuertas de la era K que el código de MIROVA no tiene.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))

from pipeline import mirova_v750_codigo as MV  # noqa: E402

DATOS = REPO / "tests" / "datos_s164_modis"
ESPERADO = json.loads((DATOS / "esperado.json").read_text(encoding="utf-8"))
PASADAS = {p["id"]: p for p in ESPERADO["pasadas"]}
MODIS = MV.FAMILIAS["MODIS"]


def _flag(perfil):
    """Lee el flag como lo lee el código: importando pipeline.profile con el perfil elegido (A89)."""
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "-c", "import pipeline.profile as p; print(p.ENABLE_MODIS_CODIGO_MIROVA)"],
                       cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout.strip().splitlines()[-1]


def _yaml_volcan(nombre):
    import yaml
    v = {x["name"]: x for x in yaml.safe_load((REPO / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    return v[nombre]


def _grilla(pid):
    z = np.load(DATOS / f"grilla_{pid}.npz")
    return z["mir"].astype(float), z["tir"].astype(float)


# ------------------------------------------------------------------------------------------------ 1. el flag
@pytest.mark.parametrize("perfil", ["mirova_equivalent", "experimental"])
def test_flag_apagado_en_produccion_y_laboratorio(perfil):
    assert _flag(perfil) == "False"


def test_flag_se_lee_de_thresholds_y_llega_al_procesador():
    src = (REPO / "pipeline/profile.py").read_text(encoding="utf-8")
    assert 'ENABLE_MODIS_CODIGO_MIROVA: bool = bool(_t.get("enable_modis_codigo_mirova", False))' in src
    from pipeline import process_modis as PM
    assert PM.ENABLE_MODIS_CODIGO_MIROVA is False


# ------------------------------------------------------------------------------------------------ constantes
def test_constantes_de_modis_son_las_del_paper_y_de_produccion():
    """Coppola 2016a (sp426_5.txt l. 174-180 y 374): banda 22 a 3,959 um, banda 31 a 11,03 um, RP = 18,9 A_pix dL con
    A_pix = 1 km² (CLAUDE.md, «Reglas científicas», validado S14). Son las mismas de process_modis y del port del
    censo; si alguien cambia una, la vía deja de ser la que se midió."""
    from pipeline import process_modis as PM
    sys.path.insert(0, str(REPO / "experiments/_s159/portes"))
    import mirova_port as MP
    assert MODIS["lam_mir"] == PM.BAND22_LAMBDA == MP.SENSORES["MODIS"]["lam_mir"] == 3.959
    assert MODIS["lam_tir"] == PM.BAND31_LAMBDA == MP.SENSORES["MODIS"]["lam_tir"] == 11.03
    assert MODIS["coef"] == pytest.approx(PM.WOOSTER_COEFF * PM.NADIR_PIXEL_AREA_M2 / 1e6, rel=1e-15)
    assert MODIS["coef"] == pytest.approx(MP.SENSORES["MODIS"]["coef"] * MP.SENSORES["MODIS"]["area"] / 1e6, rel=1e-15)
    assert MODIS["paso_m"] == 1000.0
    # VIIRS 750 sigue con las del .m
    v = MV.FAMILIAS["VIIRS750"]
    assert (v["lam_mir"], v["lam_tir"], v["coef"], v["paso_m"]) == (MV.LAMBDA_M13, MV.LAMBDA_M15, MV.COEF_VRP_V750,
                                                                     MV.PASO_V750_M)


# ------------------------------------------------------------------------------------------------ grilla y caja
@pytest.mark.parametrize("nombre", sorted(MV._referencias()))
def test_grilla_y_caja_de_modis_son_las_del_censo(nombre):
    """La grilla de 1 km sale de la misma regla GEO que la de 750 m y reproduce la del censo (grillas.json del tag
    s162-modd-tag, copiada en esperado.json para los volcanes de las fixtures) y la caja «fisica» del port (±2.625 m
    sensible y ±7.875 m conservadora alrededor de X0, Y0: 5 x 5 y 15 x 15 celdas)."""
    sys.path.insert(0, str(REPO / "experiments/_s159/portes"))
    import mirova_port as MP
    g = MV.grilla_del_volcan(nombre, paso_m=MODIS["paso_m"], clave_roi=MODIS["clave_roi"])
    assert g["n"] == 51 and g["paso"] == 1000.0 and g["roi"] == "def"
    r = MV._referencias()[nombre]
    gc = {"ul_x": g["ul_x"], "ul_y": g["ul_y"], "n": 51, "celda": 1000.0}
    box_port = MP.caja(gc, float(r["x0"]), float(r["y0"]), "fisica")
    box = MV.caja_roi("def", n=g["n"], lado_sensible=MODIS["lado_sensible"], lado_anillo=MODIS["lado_anillo"],
                      paso_m=g["paso"])
    assert np.array_equal(box, box_port)
    assert int((box == 2).sum()) == 25 and int((box >= 1).sum()) == 225
    for p in PASADAS.values():
        if p["vol"] == nombre:
            gcen = p["grilla_censo"]
            assert abs(g["ul_x"] - gcen["ul_x"]) < 0.01 and abs(g["ul_y"] - gcen["ul_y"]) < 0.01
            assert g["n"] == gcen["n"] and g["epsg"] == gcen["epsg"]


# ------------------------------------------------------------------------------------------------ 3. identidad
def _via_sobre_grilla(pid):
    p = PASADAS[pid]
    mir, tir = _grilla(pid)
    g = MV.grilla_del_volcan(p["vol"], paso_m=MODIS["paso_m"], clave_roi=MODIS["clave_roi"])
    box = MV.caja_roi("def", n=g["n"], lado_sensible=MODIS["lado_sensible"], lado_anillo=MODIS["lado_anillo"],
                      paso_m=g["paso"])
    mask, d = MV.detectar_mirova(mir, tir, box, p["dayflag"], p["sunglint"], devolver_diag=True,
                                 lam_mir=MODIS["lam_mir"], lam_tir=MODIS["lam_tir"])
    return p, mir, tir, g, box, mask, d


@pytest.mark.parametrize("pid", sorted(PASADAS))
def test_identidad_con_el_port_del_censo(pid):
    p, mir, _tir, _g, _box, mask, d = _via_sobre_grilla(pid)
    assert "pasada1" in d and "pasada2" in d
    pix = sorted([int(f), int(k)] for f, k in zip(*np.nonzero(mask)))
    assert pix == sorted([q[0], q[1]] for q in p["censo_pixeles"])
    assert int(mask.sum()) == p["censo_npix"]
    assert (d.get("n_abs") or 0, d.get("n_p1") or 0, d.get("n_p2") or 0) == (p["censo_n_abs"], p["censo_n_p1"],
                                                                               p["censo_n_p2"])
    # los números internos de cada pase (media, desvío y umbrales del contraste, regresión del ETI) son los del port
    # del censo con las λ de MODIS: es lo que fija las λ del detector, que en estas cinco grillas no mueven la máscara
    sys.path.insert(0, str(REPO / "experiments/_s159/portes"))
    import mirova_port as MP
    r = MV._referencias()[p["vol"]]
    gc = {"ul_x": _g["ul_x"], "ul_y": _g["ul_y"], "n": _g["n"], "celda": _g["paso"]}
    _m, _l, dp = MP.detectar(mir, _tir, MP.caja(gc, float(r["x0"]), float(r["y0"]), "fisica"), p["dayflag"],
                             p["sunglint"], MP.SENSORES["MODIS"])
    for pase in ("pasada1", "pasada2"):
        for k in ("mu_nti", "sd_nti", "u_nti1", "u_nti2", "mu_eti", "sd_eti", "u_eti1", "u_eti2"):
            assert d[pase][k] == pytest.approx(dp[pase][k], rel=1e-12, abs=1e-15), (pase, k)
        assert np.allclose(d[pase]["coef"], dp[pase]["coef"], rtol=1e-12, atol=0)
    v = MV.vrp_mirova(mir, mask, coef=MODIS["coef"])
    if p["vrp_regla_matlab"] is None:
        assert v["npix"] == 0
    else:
        assert v["VRP_MW"] == pytest.approx(p["vrp_regla_matlab"], rel=1e-9)


def test_las_fixtures_ejercen_lo_que_dicen():
    """Control del instrumento: entre las cinco hay una sin alertas, una de un píxel (halo 3), una de 5 a 30 (halo 5),
    y al menos una donde la regla de MATLAB y el desempate del port dan VRP distinto. Sin esa última, la identidad
    pasaría igual con el relleno equivocado."""
    npix = [p["censo_npix"] for p in PASADAS.values()]
    assert 0 in npix and 1 in npix and any(5 <= n <= 30 for n in npix)
    distintas = [p for p in PASADAS.values() if p["vrp_regla_matlab"] is not None
                 and abs(p["vrp_regla_matlab"] / p["censo_vrp_port"] - 1) > 0.05]
    assert len(distintas) >= 1


# ------------------------------------------------------------------------------------------------ 4. Láscar P1b
def test_lascar_2026_04_25_0735_da_1_1124_mw():
    p, mir, tir, g, box, mask, _d = _via_sobre_grilla(1611)
    assert (p["vol"], p["dt"], p["lab"]) == ("Lascar", "2026-04-25 07:35", "protegida")
    v = MV.vrp_mirova(mir, mask, coef=MODIS["coef"])
    assert v["npix"] == 1
    assert v["VRP_MW"] == pytest.approx(1.1124, abs=5e-5)
    assert v["VRP_MW"] >= 1.0
    # el port del censo, con su desempate, la dejaba bajo el corte: la regla de MATLAB es la que decide
    assert p["censo_vrp_port"] == pytest.approx(0.9731, abs=5e-5)
    vl = _yaml_volcan("Lascar")
    rec = MV.procesar_grilla(mir, tir, g, box, p["dayflag"], p["sunglint"], MV.posicion_de(g, vl["lat"], vl["lon"]),
                             p["inner"], "MODIS_AQUA", familia="MODIS")
    assert rec["vrp_mw"] == 1.112 and rec["primary_cluster"]["vrp_mw"] == 1.112
    assert rec["via_codigo_mirova"] is True and rec["sensor"] == "MODIS_AQUA"
    assert rec["distance_class"] == "summit"


def test_procesar_grilla_usa_la_longitud_de_onda_del_sensor():
    """t_max_k sale de la radiancia MIR con la λ de MODIS (3,959 um), no con la de M13 (4,05 um)."""
    p, mir, tir, g, box, mask, _d = _via_sobre_grilla(3392)
    vl = _yaml_volcan(p["vol"])
    rec = MV.procesar_grilla(mir, tir, g, box, p["dayflag"], p["sunglint"], MV.posicion_de(g, vl["lat"], vl["lon"]),
                             p["inner"], "MODIS_TERRA", familia="MODIS")
    pico = max(zip(*np.nonzero(mask)), key=lambda q: mir[q])
    t_modis = float(MV.radiancia_a_temperatura(np.array([mir[pico]]), 3.959)[0])
    t_m13 = float(MV.radiancia_a_temperatura(np.array([mir[pico]]), MV.LAMBDA_M13)[0])
    assert rec["t_max_k"] == round(t_modis, 2) and abs(t_modis - t_m13) > 1.0
    assert rec["vrp_mw"] == round(PASADAS[3392]["vrp_regla_matlab"], 3)


# ------------------------------------------------------------------------------------------------ lectura MODIS
class _SDS:
    def __init__(self, a, sf=1.0):
        self._a, self._sf = a, sf

    def get(self):
        return self._a

    def attributes(self):
        return {"scale_factor": self._sf}


def test_leer_geo_mxd03_como_el_probe_del_censo(monkeypatch):
    """lat y lon del MxD03 en float64, fuera de rango a NaN, y los ángulos con su factor de escala (como
    experiments/_s159/portes/probe_portes.py::leer_modis). pyhdf no está en Windows: se simula el lector."""
    lat = np.array([[-23.0, -91.0], [-23.1, -23.2]], np.float32)
    lon = np.array([[-67.7, -67.8], [-181.0, -67.9]], np.float32)
    ang = np.array([[100, 200], [300, 400]], np.int16)
    tablas = {"Latitude": _SDS(lat), "Longitude": _SDS(lon), "SensorZenith": _SDS(ang, 0.01),
              "SensorAzimuth": _SDS(ang, 0.01), "SolarZenith": _SDS(ang, 0.01), "SolarAzimuth": _SDS(ang, 0.01)}

    class _SD:
        def __init__(self, *_a):
            pass

        def select(self, nombre):
            return tablas[nombre]

        def end(self):
            pass

    mod = types.ModuleType("pyhdf.SD")
    mod.SD, mod.SDC = _SD, types.SimpleNamespace(READ=1)
    monkeypatch.setitem(sys.modules, "pyhdf", types.ModuleType("pyhdf"))
    monkeypatch.setitem(sys.modules, "pyhdf.SD", mod)
    la, lo, an = MV.leer_geo_mxd03("MYD03.A2026115.0735.061.hdf")
    assert la.dtype == np.float64 and np.isnan(la[0, 1]) and np.isnan(lo[1, 0]) and la[1, 1] == np.float64(lat[1, 1])
    assert set(an) == {"sensor_zenith", "sensor_azimuth", "solar_zenith", "solar_azimuth"}
    assert an["solar_zenith"][1, 1] == pytest.approx(4.0)


def test_leer_radiancia_modis_fusiona_con_la_banda_22_primaria(monkeypatch):
    """MIR = banda 22, y la 21 sólo donde la 22 saturó (NaN); TIR = banda 31; en float64 (como el probe)."""
    from pipeline import process_modis as PM
    b21 = np.array([[0.30, 0.40]], np.float32)
    b22 = np.array([[0.10, np.nan]], np.float32)
    b31 = np.array([[8.0, 9.0]], np.float32)
    monkeypatch.setattr(PM, "read_modis_l1b", lambda _p: {"band21": b21, "band22": b22, "band31": b31,
                                                         "lat": None, "lon": None, "angles": {}})
    rad = MV.leer_radiancia_modis("MYD021KM.A2026115.0735.061.hdf")
    assert set(rad) == {"MIR", "TIR"} and rad["MIR"].dtype == np.float64
    assert tuple(sorted(rad)) == tuple(sorted(MODIS["bandas"])) and MODIS["bandas"][0] == "MIR"
    assert rad["MIR"][0, 0] == np.float64(b22[0, 0]) and rad["MIR"][0, 1] == np.float64(b21[0, 1])
    assert np.array_equal(rad["TIR"], b31.astype(np.float64))


# ------------------------------------------------------------------------------------------------ 2 y 5. cableado
def _canon(obj):
    import arnes_sintetico_s142 as arnes
    return json.dumps(arnes._redondear(obj), sort_keys=True, default=arnes._a_json, ensure_ascii=False)


def test_flag_apagado_bit_a_bit_con_k_de_antes(tmp_path):
    """Con el flag apagado, las tres escenas MODIS del arnés S142 dan el texto que daba el código de main antes de
    este cambio (congelado en modis_k_antes.json con pipeline/ sin tocar, mismo redondeo que el golden de S142)."""
    from arnes_sintetico_s142 import correr_en_subproceso
    hoy = correr_en_subproceso(tmp_path, solo="modis")
    antes = json.loads((DATOS / "modis_k_antes.json").read_text(encoding="utf-8"))
    assert _canon(json.loads(hoy)["modis"]) == _canon(antes["modis"])
    assert antes["modis"]["nevado"]["vrp_mw"] > 0      # el golden no es trivial: una escena publica


class _K(Exception):
    pass


class _ViaTocada(Exception):
    pass


def _lascar_args():
    v = _yaml_volcan("Lascar")
    return v["lat"], v["lon"]


def test_flag_apagado_no_toca_la_via(monkeypatch):
    from pipeline import process_modis as PM
    monkeypatch.setattr(PM, "ENABLE_MODIS_CODIGO_MIROVA", False)
    monkeypatch.setattr(PM, "read_modis_l1b", lambda *_a, **_k: (_ for _ in ()).throw(_K()))
    for nombre in ("grilla_del_volcan", "leer_radiancia_modis", "leer_geo_mxd03", "calcular_vrp_granulo",
                   "volcan_por_coordenadas"):
        monkeypatch.setattr(MV, nombre, lambda *_a, **_k: (_ for _ in ()).throw(_ViaTocada()))
    with pytest.raises(_K):
        PM.calculate_vrp(Path("MYD021KM.A2026115.0735.061.hdf"), Path("MYD03.A2026115.0735.061.hdf"),
                         *_lascar_args())


def test_flag_encendido_devuelve_el_record_de_la_via(monkeypatch):
    from pipeline import process_modis as PM
    monkeypatch.setattr(PM, "ENABLE_MODIS_CODIGO_MIROVA", True)
    monkeypatch.setattr(PM, "read_modis_l1b", lambda *_a, **_k: (_ for _ in ()).throw(_K()))
    llamado = {}
    monkeypatch.setattr(MV, "leer_radiancia_modis", lambda p: {"MIR": 1, "TIR": 2})
    monkeypatch.setattr(MV, "leer_geo_mxd03", lambda p: ("lat", "lon", {}))

    def falso(rad, lat, lon, ang, nombre, vlat, vlon, inner, sensor, familia="VIIRS750"):
        llamado.update(nombre=nombre, vlat=vlat, inner=inner, sensor=sensor, familia=familia, geo=lat)
        return {"vrp_mw": 1.5, "via_codigo_mirova": True}
    monkeypatch.setattr(MV, "calcular_vrp_granulo", falso)
    r = PM.calculate_vrp(Path("MYD021KM.A2026115.0735.061.hdf"), Path("MYD03.A2026115.0735.061.hdf"),
                         *_lascar_args(), vent_lat=-23.37, vent_lon=-67.73, inner_radius_km=5.0)
    assert r.get("via_codigo_mirova") is True and r.get("granule") == "MYD021KM.A2026115.0735.061.hdf"
    assert r.get("datetime_utc") == "2026-04-25 07:35" and r.get("product_version") == "standard"
    assert llamado == {"nombre": "Lascar", "vlat": -23.37, "inner": 5.0, "sensor": "MODIS_AQUA",
                       "familia": "MODIS", "geo": "lat"}


def _marca_de_k(monkeypatch, geo_path, rad=None, geo=None):
    """Corre calculate_vrp con el flag encendido y K sobre la escena `nevado` del arnés S142 (lector de K
    reemplazado), y devuelve la marca del record. La vía no puede llegar a calcular."""
    import arnes_sintetico_s142 as arnes
    from pipeline import process_modis as PM
    monkeypatch.setattr(PM, "ENABLE_MODIS_CODIGO_MIROVA", True)
    monkeypatch.setattr(PM, "read_modis_l1b", lambda *_a, **_k: arnes.escena_modis("nevado"))
    # si un control se saltara, la vía «correría» y devolvería un record con la marca True: se ve por aserción
    monkeypatch.setattr(MV, "calcular_vrp_granulo", lambda *_a, **_k: {"via_codigo_mirova": True})
    # la escena del arnés está en (LAT0, LON0); se hace pasar por Láscar, que tiene grilla
    monkeypatch.setattr(MV, "volcan_por_coordenadas", lambda la, lo: "Lascar")
    if rad is None:
        rad = {"MIR": np.zeros((4, 4)), "TIR": np.zeros((4, 4))}
        geo = (np.zeros((4, 4)), np.zeros((4, 4)), {})
    monkeypatch.setattr(MV, "leer_radiancia_modis", lambda p: rad)
    monkeypatch.setattr(MV, "leer_geo_mxd03", lambda p: geo)
    r = PM.calculate_vrp(Path("MYD021KM.A2026115.0735.061.hdf"), geo_path, arnes.LAT0, arnes.LON0, radius_km=25.0,
                         vent_lat=arnes.LAT0, vent_lon=arnes.LON0, inner_radius_km=5.0)
    return r.get("via_codigo_mirova"), r


def test_flag_encendido_sin_mxd03_sigue_k_y_lo_dice(monkeypatch):
    """La vía es la del censo con la geolocalización del MxD03 de 1 km; sin ese archivo no cae a la de 5 km
    interpolada (otra vía, la que el censo midió aparte como fisica_geo5km): corre K y el record lo dice."""
    marca, r = _marca_de_k(monkeypatch, None)
    assert marca == "sin_mxd03" and r.get("final_hotspot_source") != "codigo_mirova"


def test_flag_encendido_con_geo_de_otra_forma_sigue_k_y_lo_dice(monkeypatch):
    marca, _r = _marca_de_k(monkeypatch, Path("MYD03.hdf"),
                            rad={"MIR": np.zeros((4, 4)), "TIR": np.zeros((4, 4))},
                            geo=(np.zeros((3, 4)), np.zeros((3, 4)), {}))
    assert marca == "geo_distinta"


def test_flag_encendido_cambia_el_record_y_sin_grilla_sigue_k_y_lo_dice(monkeypatch):
    """Control del bit a bit (A116) y prueba 5: el arnés corre en coordenadas que no son de ningún volcán con grilla
    (-39,42; -71,94, a 860 m de Villarrica del yaml), así que con el flag encendido corre K y el record lleva la marca
    "sin_grilla"; con el flag apagado la marca no existe. La vía no se toca."""
    import arnes_sintetico_s142 as arnes
    from pipeline import process_modis as PM
    assert MV.volcan_por_coordenadas(arnes.LAT0, arnes.LON0) is None
    monkeypatch.setattr(MV, "leer_radiancia_modis", lambda *_a, **_k: (_ for _ in ()).throw(_ViaTocada()))
    apagado = arnes.correr_modis("nevado")
    monkeypatch.setattr(PM, "ENABLE_MODIS_CODIGO_MIROVA", True)
    encendido = arnes.correr_modis("nevado")
    assert "via_codigo_mirova" not in apagado
    assert encendido.get("via_codigo_mirova") == "sin_grilla"
    encendido.pop("via_codigo_mirova", None)
    assert _canon(encendido) == _canon(apagado)


def test_extremo_a_extremo_con_granulo_sintetico_en_lascar(monkeypatch):
    """Gránulo sintético de 1 km sobre Láscar (lat/lon como un MxD03, ángulos de noche) con un píxel caliente en el
    cráter: con el flag encendido sale el record de la vía, distinto del de K y con la alerta en la cumbre."""
    from pipeline import process_modis as PM
    vl = _yaml_volcan("Lascar")
    n = 121
    d = (np.arange(n) - n // 2) * 1.0
    y, x = np.meshgrid(d, d, indexing="ij")
    lat = vl["lat"] - y / 111.0
    lon = vl["lon"] + x / (111.0 * np.cos(np.radians(vl["lat"])))
    T_mir = 265.0 + 0.0 * x
    T_tir = 265.0 + 0.0 * x
    rng = np.random.default_rng(164)
    T_mir = T_mir + rng.normal(0, 0.3, T_mir.shape)
    T_tir = T_tir + rng.normal(0, 0.3, T_tir.shape)
    T_mir[n // 2, n // 2] = 300.0
    mir = MV.temperatura_a_radiancia(T_mir, 3.959)
    tir = MV.temperatura_a_radiancia(T_tir, 11.03)
    ang = {"sensor_zenith": np.full(lat.shape, 10.0), "sensor_azimuth": np.full(lat.shape, 0.0),
           "solar_zenith": np.full(lat.shape, 130.0), "solar_azimuth": np.full(lat.shape, 90.0)}
    monkeypatch.setattr(PM, "ENABLE_MODIS_CODIGO_MIROVA", True)
    monkeypatch.setattr(MV, "leer_radiancia_modis", lambda p: {"MIR": mir, "TIR": tir})
    monkeypatch.setattr(MV, "leer_geo_mxd03", lambda p: (lat, lon, ang))
    visto = {}
    original = MV.procesar_grilla

    def espia(m13g, m15g, grilla, box, *a, **k):
        visto.update(n=grilla["n"], sens=int((box == 2).sum()), roi=int((box >= 1).sum()), familia=k.get("familia"))
        return original(m13g, m15g, grilla, box, *a, **k)
    monkeypatch.setattr(MV, "procesar_grilla", espia)
    r = PM.calculate_vrp(Path("MYD021KM.A2026115.0735.061.hdf"), Path("MYD03.A2026115.0735.061.hdf"),
                         vl["lat"], vl["lon"], vent_lat=vl["lat"], vent_lon=vl["lon"], inner_radius_km=5.0)
    assert r["via_codigo_mirova"] is True and r["final_hotspot_source"] == "codigo_mirova"
    assert r["n_anomalous_pixels"] >= 1 and r["vrp_mw"] > 0 and r["distance_class"] == "summit"
    assert r["diag_codigo_mirova"]["dayflag"] == 0 and r["diag_codigo_mirova"]["roi"] == "def"
    assert r["sensor"] == "MODIS_AQUA" and r["sensor_zenith_deg"] == 10.0
    assert visto == {"n": 51, "sens": 25, "roi": 225, "familia": "MODIS"}


def test_volcan_lejos_del_granulo_no_da_record():
    """Como el probe del censo: si el píxel más cercano al centro de la grilla está a más de 5 km, el volcán está
    fuera del gránulo y no hay record (en VIIRS 750 ese corte no existe: dist_max_centro_km es None)."""
    vl = _yaml_volcan("Lascar")
    n = 121
    d = (np.arange(n) - n // 2) * 1.0
    y, x = np.meshgrid(d, d, indexing="ij")
    lat = vl["lat"] - y / 111.0
    lon = vl["lon"] + (x + 70.0) / (111.0 * np.cos(np.radians(vl["lat"])))   # gránulo corrido 10 a 130 km al este
    lon[:, : n // 2 - 54] = np.nan
    rad = {"MIR": np.ones(lat.shape), "TIR": np.ones(lat.shape)}
    g = MV.grilla_del_volcan("Lascar", paso_m=1000.0, clave_roi="roi_modis")
    dmin = np.nanmin(MV._haversine(lat, lon, g["centro_lat"], g["centro_lon"]))
    assert 5.0 < dmin < MV.RADIO_RECORTE_KM
    assert MV.calcular_vrp_granulo(rad, lat, lon, {}, "Lascar", vl["lat"], vl["lon"], 5.0, "MODIS_AQUA",
                                   familia="MODIS") is None
    assert MV.FAMILIAS["VIIRS750"]["dist_max_centro_km"] is None


# ------------------------------------------------------------------------------------------------ 6. almacén
@pytest.mark.parametrize("marca,vrp_esperado", [(True, 4.0), (False, 0.0), ("sin_grilla", 0.0)])
def test_almacen_no_aplica_las_compuertas_de_k_al_record_modis_de_la_via(tmp_path, monkeypatch, marca, vrp_esperado):
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    r = {"datetime_utc": "2026-04-25 07:35", "sensor": "MODIS_AQUA", "vrp_mw": 4.0, "vrp_vent_mw": 0.0,
         "hotspot_lat": -23.1, "hotspot_lon": -67.7, "hotspot_dist_km": 30.0,
         "primary_cluster": {"vrp_mw": 4.0, "n_pixels": 20, "centroid_lat": -23.1, "centroid_lon": -67.7,
                             "centroid_dist_km": 30.0, "single_pixel_mode": False},
         "anomaly_pixels": [{"lat": -23.1, "lon": -67.7, "dist_km": 30.0, "bt_k": 300.0}],
         "distance_class": "far", "product_version": "standard", "via_codigo_mirova": marca}
    store.append_record("TestVolcano", r, max_hotspot_dist_km=25.0, max_cluster_pixels=12,
                        enable_pixel_level_distance_filter=True, inner_radius_km=5.0)
    assert r["vrp_mw"] == vrp_esperado
