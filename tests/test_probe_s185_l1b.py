"""Pruebas del instrumento del probe S185 (experiments/_s185_l1b/ y .github/workflows/probe-s185-l1b.yml).

POR QUÉ: el análisis decide qué hacer con dos sospechas sobre la vía «código MIROVA», y un instrumento que nunca falló no
prueba nada (A110, A116). Estas pruebas corren con datos SINTÉTICOS y sin red: miden que el análisis hace lo que dice (las
variantes cambian lo que dicen que cambian, la variante de producción es la de producción, el driver borra los L1B y sale 2 si
falta una pasada) y que el workflow cumple las reglas duras (solo workflow_dispatch, solo EARTHDATA_TOKEN, sin push, sin data/).
"""
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
AQUI = ROOT / "experiments" / "_s185_l1b"
for p in (ROOT, AQUI):
    sys.path.insert(0, str(p))

from pipeline import mirova_v750_codigo as MV  # noqa: E402
import analisis as AN  # noqa: E402
import interpoladores as IP  # noqa: E402
import bajar_y_medir as BM  # noqa: E402

MANIFIESTO = json.load(open(AQUI / "manifiesto_s185.json", encoding="utf-8"))
WORKFLOW = ROOT / ".github" / "workflows" / "probe-s185-l1b.yml"
GEO_DE = {"VJ102MOD": "VJ103MOD", "VJ202MOD": "VJ203MOD", "VNP02MOD": "VNP03MOD",
          "VJ102IMG": "VJ103IMG", "VJ202IMG": "VJ203IMG", "VNP02IMG": "VNP03IMG"}


# ------------------------------------------------------------------------------------------------ datos sintéticos
def barrido(lat0, lon0, paso_m, n, bandas, calientes, cenit=40.0, azimut=105.0):
    """Barrido sintético regular (fila 0 al norte) con ruido fijo y píxeles calientes: {(di, dj): factor} sobre la 1ª banda."""
    ii, jj = np.meshgrid(np.arange(n) - n // 2, np.arange(n) - n // 2, indexing="ij")
    lat = lat0 - ii * paso_m / 111000.0
    lon = lon0 + jj * paso_m / (111000.0 * np.cos(np.radians(lat0)))
    rng = np.random.default_rng(1)
    rad = {b: base * (1 + 0.01 * rng.standard_normal((n, n))) for b, base in bandas.items()}
    primera = list(bandas)[0]
    for (di, dj), f in calientes.items():
        rad[primera][n // 2 + di, n // 2 + dj] *= f
    ang = {"sensor_zenith": np.full((n, n), cenit), "sensor_azimuth": np.full((n, n), azimut),
           "solar_zenith": np.full((n, n), 120.0), "solar_azimuth": np.full((n, n), 20.0)}
    return rad, lat, lon, ang


@pytest.fixture(scope="module")
def tup_sintetico():
    return barrido(-33.4256, -69.7977, 750.0, 90, {"M13": 0.6, "M15": 7.0}, {(0, 0): 6.0, (0, 1): 3.0})


@pytest.fixture(scope="module")
def chi_sintetico():
    return barrido(-36.8636, -71.3777, 375.0, 150, {"I04": 0.5, "I05": 6.0}, {(0, 0): 8.0, (0, 1): 4.0, (1, 0): 3.0})


# ------------------------------------------------------------------------------------------------ manifiesto
def test_manifiesto_pasadas_y_roles():
    tup = [m for m in MANIFIESTO if m["proyecto"] == "tup"]
    chi = [m for m in MANIFIESTO if m["proyecto"] == "chi"]
    assert (len(tup), len(chi)) == (10, 8)
    assert sum(m["rol"] == "calla" for m in tup) == 6 and sum(m["rol"] == "control_detecta" for m in tup) == 4
    assert sum(m["rol"] == "baja_este" for m in chi) == 3
    assert sum(m["rol"].startswith("control_este") for m in chi) == 3 and sum(m["rol"].startswith("control_oeste") for m in chi) == 2


def test_manifiesto_geo_corresponde_al_l1b_y_cabe_en_el_tope():
    for m in MANIFIESTO:
        l1b, geo = m["l1b"].split("."), m["geo"].split(".")
        assert GEO_DE[l1b[0]] == geo[0], m
        assert l1b[1:3] == geo[1:3], m            # misma pasada (día juliano y hora)
        assert m["l1b"].endswith(".nc") and m["geo"].endswith(".nc")
    assert sum(m["mb"] for m in MANIFIESTO) < 6000   # tope del encargo: 6 GB en total


def test_manifiesto_tup_las_6_calladas_estan_bajo_su_umbral():
    for m in (x for x in MANIFIESTO if x["rol"] == "calla"):
        assert m["ref"]["publicado_n_pix"] == 0 and m["ref"]["publicado_celda_decisiva"]["margen"] < 1.0, m["rotulo"]
    for m in (x for x in MANIFIESTO if x["rol"] == "control_detecta"):
        assert m["ref"]["publicado_n_pix"] > 0 and m["ref"]["publicado_celda_decisiva"]["margen"] >= 1.0, m["rotulo"]


def test_manifiesto_chillan_las_bajas_son_del_este_y_bajo_0_7():
    for m in MANIFIESTO:
        if m["proyecto"] != "chi":
            continue
        r = m["ref"]
        if m["rol"] == "baja_este":
            assert r["azimut"] > 0 and r["razon_publicada"] < 0.7
        if m["rol"].startswith("control_oeste"):
            assert r["azimut"] < 0 and r["razon_publicada"] > 0.9
        if m["rol"].startswith("control_este"):
            assert r["azimut"] > 0 and r["razon_publicada"] > 0.9


# ------------------------------------------------------------------------------------------------ interpoladores
def test_celdas_de_vectorizada_igual_a_celda_de():
    g = MV.grilla_del_volcan("NevadosDeChillan", paso_m=375.0, clave_roi="roi_v375")
    lat = np.array([-36.863, -36.85, -36.9, -36.87])
    lon = np.array([-71.377, -71.4, -71.35, -71.33])
    f, c = IP.celdas_de(g, lat, lon)
    for k in range(len(lat)):
        assert (int(f[k]), int(c[k])) == MV.celda_de(g, lat[k], lon[k])


def test_interpoladores_conservan_un_campo_constante(tup_sintetico):
    _, lat, lon, _ = tup_sintetico
    g = MV.grilla_del_volcan("Tupungatito")
    m = np.full(lat.shape, 5.0)
    for f in (IP.vecino, IP.promedio, MV.remuestrear_grilla):
        a, b = f(lat, lon, m, m * 2, g)
        assert np.nanmax(np.abs(a - 5.0)) < 1e-9 and np.nanmax(np.abs(b - 10.0)) < 1e-9, f.__name__


def test_promedio_es_el_promedio_de_los_nativos_de_la_celda():
    g = MV.grilla_del_volcan("Tupungatito")
    from pyproj import Transformer
    lon0, lat0 = Transformer.from_crs(f"EPSG:{g['epsg']}", "EPSG:4326", always_xy=True).transform(
        g["ul_x"] + 33.5 * g["paso"], g["ul_y"] - 33.5 * g["paso"])
    # cuatro píxeles nativos dentro de la celda (33, 33), más un anillo de relleno alrededor para que la escena sea válida
    d = 150.0 / 111000.0
    lat = np.array([lat0 + d, lat0 - d, lat0 + d, lat0 - d] + [lat0 + 0.05 * k for k in range(1, 200)])
    lon = np.array([lon0 + d, lon0 - d, lon0 - d, lon0 + d] + [lon0] * 199)
    v = np.array([1.0, 2.0, 3.0, 6.0] + [0.0] * 199)
    m13, _ = IP.promedio(lat, lon, v, v, g)
    assert abs(m13[33, 33] - 3.0) < 1e-9


def test_grilla_desplazada_mueve_la_esquina_y_la_celda_del_crater():
    g = MV.grilla_del_volcan("Tupungatito")
    g2 = IP.grilla_desplazada(g, 375.0, 0.0)
    assert g2["ul_x"] == g["ul_x"] + 375.0 and g2["ul_y"] == g["ul_y"] and g["ul_x"] != g2["ul_x"]   # la original no se toca
    f0, c0 = MV.celda_de(g, *AN.VENT_TUP)
    f1, c1 = MV.celda_de(g2, *AN.VENT_TUP)
    assert f0 == f1 and abs(c1 - c0) <= 1


# ------------------------------------------------------------------------------------------------ analisis V750
REF_TUP = {"mirova_dist_km": 4.37, "mirova_vrp_mw": 0.17, "publicado_n_pix": 0, "publicado_celda_decisiva": None}


def test_correr_via_lineal_es_la_via_de_produccion_y_restaura_el_original(tup_sintetico):
    rad, lat, lon, ang = tup_sintetico
    g0 = MV.grilla_del_volcan("Tupungatito")
    original = MV.remuestrear_grilla
    directo = MV.calcular_vrp_granulo(rad, lat, lon, ang, "Tupungatito", *AN.VENT_TUP[:2], AN.INNER_TUP, "VIIRS_NOAA20_750", grilla=g0)
    via = AN.correr_via("VIIRS750", "Tupungatito", AN.VENT_TUP, AN.INNER_TUP, "VIIRS_NOAA20_750", rad, lat, lon, ang, g0, None)
    assert directo["n_anomalous_pixels"] == via["n_anomalous_pixels"] > 0 and directo["vrp_mw"] == via["vrp_mw"]
    AN.correr_via("VIIRS750", "Tupungatito", AN.VENT_TUP, AN.INNER_TUP, "VIIRS_NOAA20_750", rad, lat, lon, ang, g0, IP.vecino)
    assert MV.remuestrear_grilla is original          # una variante no deja el interpolador cambiado


def test_correr_via_con_otro_interpolador_cambia_el_resultado(tup_sintetico):
    """Control del instrumento: si la variante no hiciera nada, el A/B mediría el ruido."""
    rad, lat, lon, ang = tup_sintetico
    g0 = MV.grilla_del_volcan("Tupungatito")
    base = AN.correr_via("VIIRS750", "Tupungatito", AN.VENT_TUP, AN.INNER_TUP, "VIIRS_NOAA20_750", rad, lat, lon, ang, g0, None)
    vec = AN.correr_via("VIIRS750", "Tupungatito", AN.VENT_TUP, AN.INNER_TUP, "VIIRS_NOAA20_750", rad, lat, lon, ang, g0, IP.vecino)
    assert abs(base["vrp_mw"] - vec["vrp_mw"]) > 1e-6 or base["n_anomalous_pixels"] != vec["n_anomalous_pixels"]


def test_analizar_tup_estructura_y_reproduccion(tup_sintetico):
    rad, lat, lon, ang = tup_sintetico
    it = AN.analizar_tup("VJ102MOD.A2026063.0530.021.2026063113315.nc", rad, lat, lon, ang, REF_TUP)
    assert set(it["variantes"]) == {"lineal", "vecino", "promedio", "desp_E", "desp_O", "desp_N", "desp_S"}
    assert it["variantes"]["lineal"]["celda_decisiva"] is not None
    assert it["reproduce_publicado"] is False                       # sin referencia publicada no puede decir que reproduce
    assert it["mirova"]["dist_km"] == 4.37 and it["mirova"]["celdas_candidatas"]
    assert all(len(c) == 2 for c in it["mirova"]["celdas_candidatas"])
    assert it["nativos_cerca_del_crater"] and it["nativos_cerca_del_crater"][0]["celda"][0] >= 0
    # con la referencia publicada = la propia variante lineal, la reproducción da True (y con un margen alterado, False)
    cd = it["variantes"]["lineal"]["celda_decisiva"]
    ref_ok = dict(REF_TUP, publicado_celda_decisiva=cd, publicado_n_pix=it["variantes"]["lineal"]["n_pix"])
    ref_mal = dict(REF_TUP, publicado_celda_decisiva=dict(cd, margen=cd["margen"] + 0.01))
    assert AN.analizar_tup("VJ102MOD.A2026063.0530.021.2026063113315.nc", rad, lat, lon, ang, ref_ok)["reproduce_publicado"] is True
    assert AN.analizar_tup("VJ102MOD.A2026063.0530.021.2026063113315.nc", rad, lat, lon, ang, ref_mal)["reproduce_publicado"] is False


def test_recorte_tup_solo_trae_la_ventana_del_crater(tup_sintetico):
    rad, lat, lon, ang = tup_sintetico
    r = AN.recorte_tup(rad, lat, lon, ang)
    assert 0 < r["M13"].size < rad["M13"].size and r["M13"].shape == r["lat"].shape
    assert r["lat"].min() > AN.VENT_TUP[0] - 0.2 and r["lat"].max() < AN.VENT_TUP[0] + 0.2


# ------------------------------------------------------------------------------------------------ analisis V375
def test_area_nativa_de_una_grilla_regular_es_el_paso_al_cuadrado(chi_sintetico):
    _, lat, lon, _ = chi_sintetico
    a = AN.area_nativa_m2(lat, lon, 75, 75)
    assert abs(a - 375.0 ** 2) / 375.0 ** 2 < 0.02
    assert math.isnan(AN.area_nativa_m2(np.array([[0.0]]), np.array([[0.0]]), 0, 0))


def test_leer_banderas_decodifica_con_los_atributos_del_archivo(tmp_path):
    import h5py
    ruta = tmp_path / "x.nc"
    with h5py.File(ruta, "w") as f:
        o = f.create_group("observation_data")
        d = o.create_dataset("I04_quality_flags", data=np.array([[0, 1], [4, 5]], dtype=np.uint8))
        d.attrs["flag_masks"] = np.array([1, 2, 4], dtype=np.uint8)
        d.attrs["flag_meanings"] = np.bytes_("uno dos cuatro")
    fl = AN.leer_banderas(str(ruta))
    arr, nombres = fl["I04"]
    assert fl["I05"] is None and nombres == [(1, "uno"), (2, "dos"), (4, "cuatro")]
    assert [nm for mk, nm in nombres if int(arr[1, 1]) & mk] == ["uno", "cuatro"]


def test_terreno_es_descriptivo_dh_por_tangente_del_cenit_en_los_dos_sentidos(chi_sintetico):
    rad, lat, lon, ang = chi_sintetico
    g0 = MV.grilla_del_volcan("NevadosDeChillan", paso_m=375.0, clave_roi="roi_v375")
    top = [{"i": 75, "j": 75, "celda": list(MV.celda_de(g0, float(lat[75, 75]), float(lon[75, 75])))}]
    altura = np.full(lat.shape, 3000.0)
    t = AN.terreno(top, lat, lon, ang, altura, g0, dh_m=1500.0)
    esperado = 1500.0 * math.tan(math.radians(40.0))        # el desplazamiento es de dh, NO de la altura completa
    assert t["altura_dem_m"] == 3000.0 and abs(t["desplazamiento_por_dh_m"] - round(esperado)) <= 1
    for k in ("alejado_del_sensor_menos", "hacia_el_sensor_mas"):
        f, c = t[k]["celda"]
        d_cel = math.hypot(f - top[0]["celda"][0], c - top[0]["celda"][1]) * 375.0
        assert abs(d_cel - esperado) < 2 * 375.0     # dentro de una celda de la distancia de paralaje
    # azimut 105° (sensor al este-sureste): «menos» (alejado del sensor) cae al oeste y «mas» al este
    assert t["alejado_del_sensor_menos"]["celda"][1] < top[0]["celda"][1] < t["hacia_el_sensor_mas"]["celda"][1]
    assert AN.terreno(top, lat, lon, ang, None, g0) == "sin height en el GEO" and AN.terreno([], lat, lon, ang, altura, g0) == "sin pixeles"


def test_leer_altura_respeta_el_fillvalue_del_archivo(tmp_path):
    import h5py
    ruta = tmp_path / "g.nc"
    with h5py.File(ruta, "w") as f:
        g = f.create_group("geolocation_data")
        d = g.create_dataset("height", data=np.array([[3000, -9999, 2500]], dtype=np.int16))
        d.attrs["_FillValue"] = np.int16(-9999)
    h = AN.leer_altura(str(ruta))
    assert h[0, 0] == 3000 and np.isnan(h[0, 1]) and h[0, 2] == 2500


def test_area_nativa_toma_el_menor_espaciado_y_no_el_salto_entre_barridos():
    ii, jj = np.meshgrid(np.arange(5), np.arange(5), indexing="ij")
    lat = -36.0 - ii * 375.0 / 111000.0
    lon = -71.0 + jj * 375.0 / (111000.0 * np.cos(np.radians(36.0)))
    lat2 = lat.copy()
    lat2[3:, :] -= 3000.0 / 111000.0                          # un salto de 3 km entre la fila 2 y la 3 (borde de barrido)
    assert abs(AN.area_nativa_m2(lat2, lon, 2, 2) - 375.0 ** 2) / 375.0 ** 2 < 0.02


# ------------------------------------------------------------------------------------------------ variantes y energía
def test_variantes_desp_cambian_la_grilla_y_el_resultado(tup_sintetico):
    rad, lat, lon, ang = tup_sintetico
    g0 = MV.grilla_del_volcan("Tupungatito")
    v = AN.variantes(g0)
    for k in ("desp_E", "desp_O", "desp_N", "desp_S"):
        assert (v[k][0]["ul_x"], v[k][0]["ul_y"]) != (g0["ul_x"], g0["ul_y"]), k
    r0 = AN.correr_via("VIIRS750", "Tupungatito", AN.VENT_TUP, AN.INNER_TUP, "VIIRS_NOAA20_750", rad, lat, lon, ang, g0, None)
    r1 = AN.correr_via("VIIRS750", "Tupungatito", AN.VENT_TUP, AN.INNER_TUP, "VIIRS_NOAA20_750", rad, lat, lon, ang, v["desp_E"][0], None)
    assert r0["vrp_mw"] != r1["vrp_mw"]                       # media celda de corrimiento cambia lo que ve el detector


def test_grilla_corrida_una_celda_entera_corre_las_alertadas_un_indice(tup_sintetico):
    rad, lat, lon, ang = tup_sintetico
    g0 = MV.grilla_del_volcan("Tupungatito")
    g1 = IP.grilla_desplazada(g0, g0["paso"], 0.0)              # una celda entera hacia el este: el mismo punto del suelo pasa de la columna c a c-1
    r0 = AN.correr_via("VIIRS750", "Tupungatito", AN.VENT_TUP, AN.INNER_TUP, "VIIRS_NOAA20_750", rad, lat, lon, ang, g0, None)
    r1 = AN.correr_via("VIIRS750", "Tupungatito", AN.VENT_TUP, AN.INNER_TUP, "VIIRS_NOAA20_750", rad, lat, lon, ang, g1, None)
    a0 = {(p["fila"], p["col"]) for p in r0["anomaly_pixels"]}
    a1 = {(p["fila"], p["col"]) for p in r1["anomaly_pixels"]}
    assert a0 and {(f, c - 1) for f, c in a0} <= a1


def test_energia_ventana_da_1_en_una_escena_regular_suave():
    """Control del instrumento: sin estiramiento del barrido ni píxel aislado, nativo y grilla ven la misma energía. Una constante
    de área equivocada (p. ej. 750^2 en vez de 375^2) lo rompe por un factor 4."""
    rad, lat, lon, ang = barrido(-36.8636, -71.3777, 375.0, 150, {"I04": 0.5, "I05": 6.0}, {})
    n = 150
    ii, jj = np.meshgrid(np.arange(n) - n // 2, np.arange(n) - n // 2, indexing="ij")
    rad["I04"] = rad["I04"] + 4.0 * np.exp(-(ii ** 2 + jj ** 2) / (2 * 3.0 ** 2))        # blob gaussiano de 3 píxeles de sigma
    g0 = MV.grilla_del_volcan("NevadosDeChillan", paso_m=375.0, clave_roi="roi_v375")
    e = AN.energia_ventana(rad, lat, lon, g0)
    assert 0.95 < e["razon_E_ventana_nativa_sobre_grilla"] < 1.05, e
    assert e["n_nativos"] > 100 and e["n_celdas"] > 100


def test_energia_nativa_vs_grilla_cuenta_las_celdas_sin_nativo_y_separa_dL():
    rad, lat, lon, ang = barrido(-36.8636, -71.3777, 375.0, 150, {"I04": 0.5, "I05": 6.0}, {(0, 0): 8.0, (0, 1): 4.0, (1, 0): 3.0})
    g0 = MV.grilla_del_volcan("NevadosDeChillan", paso_m=375.0, clave_roi="roi_v375")
    rec = AN.correr_via("VIIRS375", "NevadosDeChillan", AN.VENT_CHI, AN.INNER_CHI, "VIIRS_NOAA20", rad, lat, lon, ang, g0, None)
    alert = {(p["fila"], p["col"]) for p in rec["anomaly_pixels"]}
    b = AN.energia_nativa_vs_grilla(rad, lat, lon, g0, alert, L_bk=rec["diag_codigo_mirova"]["L_bk"])
    assert b["n_celdas_con_nativo"] + b["n_celdas_sin_nativo"] == b["n_celdas_alertadas"] == len(alert)
    assert b["dL_nativo"] is not None and b["razon_dL_nativo_sobre_grilla"] is not None
    assert abs(b["area_nativa_mediana_m2"] - 375.0 ** 2) / 375.0 ** 2 < 0.02


def test_analizar_chi_estructura(chi_sintetico):
    rad, lat, lon, ang = chi_sintetico
    ref = {"mirova_vrp_mw": 10.0, "publicado_vrp_mw": None, "razon_publicada": None, "cenit": 40.0, "azimut": 105.0}
    it = AN.analizar_chi("VJ102IMG.A2026283.0512.021.2026283103733.nc", rad, lat, lon, ang, {"I04": None, "I05": None},
                         np.full(lat.shape, 3000.0), ref)
    assert set(it["variantes"]) == {"lineal", "vecino", "promedio", "desp_E", "desp_O", "desp_N", "desp_S"}
    b = it["B_energia"]
    assert b["n_celdas_alertadas"] > 0 and b["n_nativos_en_ellas"] > 0 and b["E_grilla"] > 0 and b["razon_E_nativa_sobre_grilla"] > 0
    assert it["B2_energia_ventana"]["razon_E_ventana_nativa_sobre_grilla"] is not None
    assert it["C_top25_nativos"] and it["C_top25_nativos"][0]["I04"] >= it["C_top25_nativos"][-1]["I04"]
    assert isinstance(it["D_terreno"], dict) and it["reproduce_publicado"] is False
    r = AN.recorte_chi(rad, lat, lon, ang, {"I04": None}, np.full(lat.shape, 3000.0))
    assert r["I04"].shape == r["lat"].shape == r["altura"].shape and "banderas_I04" not in r


# ------------------------------------------------------------------------------------------------ driver
def test_sello_del_nombre():
    assert BM.sello("VJ102MOD.A2026063.0530.021.2026063113315.nc") == "A2026063.0530"


def test_driver_sin_token_no_corre(monkeypatch):
    monkeypatch.delenv("EARTHDATA_TOKEN", raising=False)
    monkeypatch.setattr(sys, "argv", ["bajar_y_medir.py", "--caso", "tup"])
    assert BM.main() == 2


def test_driver_borra_el_temporal_y_sale_2_si_falta_una_pasada(monkeypatch, tmp_path):
    import pipeline.fetch as F
    monkeypatch.setenv("EARTHDATA_TOKEN", "token-de-prueba")
    monkeypatch.setattr(F, "auth", lambda: None)

    def bajar_falso(caso, clave, nombre, destino):
        Path(destino).mkdir(parents=True, exist_ok=True)
        (Path(destino) / "basura.nc").write_bytes(b"x" * 1000)    # un L1B a medio bajar
        return None, "sin gránulo de prueba"
    monkeypatch.setattr(BM, "bajar_uno", bajar_falso)
    tmp = tmp_path / "tmp"
    monkeypatch.setattr(sys, "argv", ["bajar_y_medir.py", "--caso", "chi", "--out", str(tmp_path / "out"), "--tmp", str(tmp), "--solo", "2"])
    assert BM.main() == 2
    assert not (tmp / "chi").exists()                              # el temporal se borra aunque falle
    res = json.load(open(tmp_path / "out" / "chi_resultados.json", encoding="utf-8"))
    assert len(res) == 2 and all(not r["ok"] and "sin gránulo" in r["error"] for r in res)


def test_driver_los_productos_existen_en_fetch():
    from pipeline.fetch import PRODUCTS
    for caso, d in BM.PRODUCTOS.items():
        for prefijo, claves in d.items():
            for k in claves:
                assert k in PRODUCTS, (caso, prefijo, k)


# ------------------------------------------------------------------------------------------------ workflow
def _wf():
    return yaml.safe_load(open(WORKFLOW, encoding="utf-8")), open(WORKFLOW, encoding="utf-8").read()


def test_workflow_solo_se_despacha_a_mano_y_es_de_solo_lectura():
    d, txt = _wf()
    assert list(d["on"].keys() if isinstance(d.get("on"), dict) else d.get(True, {}).keys()) == ["workflow_dispatch"]
    assert '"on":' in txt                                                    # A43
    assert d["jobs"]["probe"]["permissions"] == {"contents": "read"}
    # se revisan los comandos y la concurrencia reales, no los comentarios (que sí nombran push-main para decir que no se usa)
    cmds = "\n".join(p.get("run", "") for p in d["jobs"]["probe"]["steps"])
    assert "git push" not in cmds and "git commit" not in cmds and "git " not in cmds
    assert d["concurrency"]["group"] != "push-main"
    assert "data/" not in cmds and "mirova_equivalent" not in cmds             # no lee ni escribe data/


def test_workflow_solo_autentica_por_token_y_lo_exige_antes_de_todo():
    d, txt = _wf()
    assert "EARTHDATA_USERNAME" not in txt and "EARTHDATA_PASSWORD" not in txt
    pasos = d["jobs"]["probe"]["steps"]
    assert pasos[0]["name"] == "Token presente" and '[ -z "$EARTHDATA_TOKEN" ]' in pasos[0]["run"] and "exit 1" in pasos[0]["run"]
    assert all(p.get("env", {}).get("EARTHDATA_TOKEN") == "${{ secrets.EARTHDATA_TOKEN }}" for p in pasos if "EARTHDATA_TOKEN" in p.get("env", {}))


def test_workflow_runner_timeout_y_artefacto():
    d, txt = _wf()
    j = d["jobs"]["probe"]
    assert j["runs-on"] == "ubuntu-24.04" and j["strategy"]["matrix"]["caso"] == ["tup", "chi"]
    esperado_min = 30                                    # estimado del encabezado para el job más largo (chi)
    assert j["timeout-minutes"] >= 1.3 * esperado_min
    sube = [p for p in j["steps"] if p.get("uses", "").startswith("actions/upload-artifact")][0]
    assert sube["if"] == "always()" and ".nc" not in sube["with"]["path"] and "granulos" not in sube["with"]["path"]
    assert d["concurrency"]["group"] == "probe-s185-l1b"
