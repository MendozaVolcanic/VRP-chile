# -*- coding: utf-8 -*-
"""S190, paso A del plan F1M-108, F1M-101, F1M-V201, F1V-104 y F1V-101: la vía «código MIROVA» marca cuándo le faltó
dato sobre el cráter, sin cambiar nada de lo que publica.

POR QUÉ (el fenómeno primero). Un píxel del cráter se puede perder ANTES de interpolar a la grilla de MIROVA: el
escaneo no trae posición (relleno del MxD03 o del GEO), la MIR de MODIS satura en las dos bandas (22 y 21), o el L1B de
VIIRS trae una bandera (Missing_EV, Cal_Fail) en ese píxel. La interpolación lineal rellena el hueco con los vecinos,
más fríos, y el detector ve una noche tranquila: 0 MW, o una fracción de la potencia, sin marca. `celdas_sin_dato` no
lo ve porque se cuenta DESPUÉS de interpolar (sólo cuenta celdas fuera de la envolvente del gránulo). En VIIRS además un
I04 o M13 saturado entra al techo como radiancia finita y la VRP sale baja sin aviso (F1V-101).

Qué se exige (plan `D:\\codex-vrp\\_salida\\ronda2\\PLAN_F1M_G3_PARA_NICOLAS.md`, aprobado por Nicolás el 2026-11-19):
(a) un hueco de posición sobre el cráter queda marcado (`crater_sin_posicion`);
(b) y (c) un píxel nativo perdido en el cráter (MIR o TIR no finita) queda contado (`px_mir_invalido_crater`), en
    MODIS, VIIRS 750 y VIIRS 375;
(d) control: el gránulo sano da las marcas en cero y el record, sin las claves nuevas, es el de antes del cambio
    (`datos_s190_dato_crater/sano_antes.json`, generado con el código sin tocar; ver `__main__` al final);
(e) control de que el instrumento distingue: lo mismo lejos del cráter no marca;
(f) VIIRS: el bit de saturación de `quality_flags` en el cráter queda contado (`px_saturados_crater`), sin cambiar la
    radiancia ni la VRP.
Las aserciones leen las claves con `.get` para que una marca ausente falle por aserción y no por excepción (una
mutación que cae no es una mutación atrapada, S152).

El gránulo es sintético: malla regular con un leve desorden de posición (para que la triangulación no tenga empates,
S152), fondo de 268 K y un foco en el píxel del cráter. Las temperaturas del foco y el ancho del hueco son
ilustrativos, elegidos para que el control detecte; no son valores instrumentales.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from pipeline import mirova_v750_codigo as MV

VOLC = "Villarrica"
V_LAT, V_LON = -39.42, -71.93          # volcanoes.yaml, Villarrica (volcan_por_coordenadas exige igualdad)
INNER_KM = 5.0                         # volcanoes.yaml, inner_radius_km de Villarrica
FAMILIAS = ("MODIS", "VIIRS750", "VIIRS375")
SENSOR = {"MODIS": "MODIS_AQUA", "VIIRS750": "VIIRS_NOAA20_750", "VIIRS375": "VIIRS_NOAA20"}
PASO_NATIVO_KM = {"MODIS": 1.0, "VIIRS750": 0.75, "VIIRS375": 0.375}   # el de la grilla de cada familia
T_FOCO_K = {"MODIS": 420.0, "VIIRS750": 340.0, "VIIRS375": 340.0}       # ilustrativas
GOLDEN = Path(__file__).resolve().parent / "datos_s190_dato_crater" / "sano_antes.json"
# S192: alertados_sin_fondo es la marca del fondo nulo (F4-101); el resto del record sano sigue idéntico al dorado
# (lo vigila tests/test_via_fondo_nulo_s192.py).
CLAVES_NUEVAS = ("crater_sin_posicion", "px_mir_invalido_crater", "px_saturados_crater", "alertados_sin_fondo")


def _granulo(familia, semilla=190):
    """Gránulo sintético de ±41 km alrededor del cráter (cubre el recorte de 45 km de la grilla de 50 × 50 km)."""
    paso = PASO_NATIVO_KM[familia]
    n = 2 * int(round(41.0 / paso)) + 1
    c = n // 2
    rng = np.random.default_rng(semilla)
    fil, col = np.indices((n, n))
    yn = (c - fil) * paso + rng.normal(0, 0.05 * paso, (n, n))
    xe = (col - c) * paso + rng.normal(0, 0.05 * paso, (n, n))
    lat = V_LAT + yn / 111.32
    lon = V_LON + xe / (111.32 * math.cos(math.radians(V_LAT)))
    lat[c, c], lon[c, c] = V_LAT, V_LON
    cfg = MV.FAMILIAS[familia]
    t = 268.0 + rng.normal(0, 0.4, (n, n))
    mir = MV.temperatura_a_radiancia(t, cfg["lam_mir"])
    tir = MV.temperatura_a_radiancia(t - 3.0, cfg["lam_tir"])
    mir[c, c] = MV.temperatura_a_radiancia(T_FOCO_K[familia], cfg["lam_mir"])
    tir[c, c] = MV.temperatura_a_radiancia(300.0, cfg["lam_tir"])
    ang = {"sensor_zenith": np.full((n, n), 20.0), "solar_zenith": np.full((n, n), 120.0),
           "sensor_azimuth": np.full((n, n), -100.0), "solar_azimuth": np.full((n, n), 50.0)}
    b_mir, b_tir = cfg["bandas"]
    return {"rad": {b_mir: mir, b_tir: tir}, "lat": lat, "lon": lon, "ang": ang, "c": c, "paso": paso,
            "b_mir": b_mir, "b_tir": b_tir}


def _correr(gr, familia):
    return MV.calcular_vrp_granulo(gr["rad"], gr["lat"], gr["lon"], gr["ang"], VOLC, V_LAT, V_LON, INNER_KM,
                                   SENSOR[familia], familia=familia)


def _diag(rec):
    assert rec is not None, "el gránulo sintético no dio record (error de armado, no del marcador)"
    return rec["diag_codigo_mirova"]


def _sin_claves_nuevas(rec):
    r = json.loads(json.dumps(rec, default=float))
    for k in CLAVES_NUEVAS:
        r["diag_codigo_mirova"].pop(k, None)
    return r


def _igual(a, b, ruta="rec"):
    """Igualdad de estructura exacta y de números a 1e-9 relativo (la triangulación puede variar en el último bit
    entre CPU, S152)."""
    if isinstance(a, dict):
        assert isinstance(b, dict) and sorted(a) == sorted(b), f"{ruta}: claves {sorted(a)} contra {sorted(b)}"
        for k in a:
            _igual(a[k], b[k], f"{ruta}.{k}")
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b), f"{ruta}: largo distinto"
        for i, (x, y) in enumerate(zip(a, b)):
            _igual(x, y, f"{ruta}[{i}]")
    elif isinstance(a, float) and not isinstance(b, bool):
        assert isinstance(b, (int, float)) and b == pytest.approx(a, rel=1e-9, abs=1e-9), f"{ruta}: {a} contra {b}"
    else:
        assert a == b, f"{ruta}: {a!r} contra {b!r}"


# ------------------------------------------------------------------------------------------ armado (control)
@pytest.mark.parametrize("familia", FAMILIAS)
def test_el_control_detecta_el_foco(familia):
    """Sin esto, un 0 MW en los casos con hueco no diría nada: el foco del gránulo sano tiene que alertar."""
    rec = _correr(_granulo(familia), familia)
    assert rec is not None and rec["vrp_mw"] > 0 and rec["n_anomalous_pixels"] >= 1


# ------------------------------------------------------------------------------------------ (a) hueco de posición
@pytest.mark.parametrize("familia", FAMILIAS)
def test_hueco_de_escaneo_sobre_el_crater_queda_marcado(familia):
    """Una franja de líneas sin lat ni lon que cruza el cráter (relleno del MxD03 o del GEO). Media franja de 3 km,
    para que el píxel con posición más cercano al centro quede dentro de los 5 km de MODIS y VIIRS 375 y haya record."""
    gr = _granulo(familia)
    c, paso = gr["c"], gr["paso"]
    filas = slice(c - int(3.0 / paso), c + int(3.0 / paso) + 1)
    gr["lat"][filas] = np.nan
    gr["lon"][filas] = np.nan
    d = _diag(_correr(gr, familia))
    assert d.get("crater_sin_posicion") is True
    assert d.get("celdas_sin_dato") == 0          # el campo de siempre no lo ve: por eso hace falta la marca


# ------------------------------------------------------------------------------------------ (b) y (c) píxel perdido
@pytest.mark.parametrize("banda", ("mir", "tir"))
@pytest.mark.parametrize("familia", FAMILIAS)
def test_pixel_nativo_perdido_en_el_crater_queda_marcado(familia, banda):
    """(b) MODIS: doble saturación de la MIR (B22 y B21) o relleno; (c) VIIRS 375 y 750: DN de bandera (Missing_EV,
    Cal_Fail) que el lector deja en NaN. La TIR perdida cuenta igual: sin ella el píxel no tiene NTI."""
    gr = _granulo(familia)
    c = gr["c"]
    control = _correr(_granulo(familia), familia)
    gr["rad"][gr["b_mir" if banda == "mir" else "b_tir"]][c, c] = np.nan
    rec = _correr(gr, familia)
    d = _diag(rec)
    assert d.get("px_mir_invalido_crater") == 1
    assert d.get("crater_sin_posicion") is False  # la posición está: lo que falta es la radiancia
    if banda == "mir":
        assert rec["vrp_mw"] < control["vrp_mw"]  # el caso es el peligroso: la potencia cae sin otra marca


@pytest.mark.parametrize("familia", FAMILIAS)
def test_doble_saturacion_en_el_crater_queda_marcada(familia):
    """El nombre del plan para (b): la MIR NaN en el píxel del cráter y en sus vecinos inmediatos (un núcleo 3 × 3)."""
    gr = _granulo(familia)
    c = gr["c"]
    gr["rad"][gr["b_mir"]][c - 1:c + 2, c - 1:c + 2] = np.nan
    d = _diag(_correr(gr, familia))
    assert d.get("px_mir_invalido_crater") == 9   # a 0 y a 1 o 1,41 celdas: los nueve dentro de las dos celdas


# ------------------------------------------------------------------------------------------ (d) control sano
@pytest.mark.parametrize("familia", FAMILIAS)
def test_granulo_sano_da_marcas_en_cero(familia):
    d = _diag(_correr(_granulo(familia), familia))
    assert d.get("crater_sin_posicion") is False
    assert d.get("px_mir_invalido_crater") == 0


@pytest.mark.parametrize("familia", FAMILIAS)
def test_granulo_sano_record_identico_al_de_antes(familia):
    """Regla dura del paso A: ninguna detección, potencia, posición ni campo existente cambia; sólo se agregan claves."""
    esperado = json.loads(GOLDEN.read_text(encoding="utf-8"))[familia]
    _igual(esperado, _sin_claves_nuevas(_correr(_granulo(familia), familia)))


# ------------------------------------------------------------------------------------------ (e) lejos no marca
@pytest.mark.parametrize("familia", FAMILIAS)
def test_lo_mismo_lejos_del_crater_no_marca(familia):
    """Franja sin posición a 14 km o más del cráter y MIR NaN a 3 y 4 celdas: nada de eso es el cráter. Con el píxel
    a 1 celda sí cuenta (el instrumento distingue la distancia, no sólo la presencia)."""
    gr = _granulo(familia)
    c, paso = gr["c"], gr["paso"]
    lejos = slice(c - int(20.0 / paso), c - int(14.0 / paso))
    gr["lat"][lejos] = np.nan
    gr["lon"][lejos] = np.nan
    gr["rad"][gr["b_mir"]][c, c + 3] = np.nan
    gr["rad"][gr["b_tir"]][c + 4, c] = np.nan
    d = _diag(_correr(gr, familia))
    assert d.get("crater_sin_posicion") is False
    assert d.get("px_mir_invalido_crater") == 0
    gr["rad"][gr["b_mir"]][c - 1, c] = np.nan
    assert _diag(_correr(gr, familia)).get("px_mir_invalido_crater") == 1


# ------------------------------------------------------------------------------------------ equivalencia con K
def _casos_equivalencia(familia):
    """Gránulo sano, hueco sobre el cráter, cráter en la última línea del gránulo, cráter en la primera columna, y
    hueco que termina justo al lado del píxel del cráter."""
    sano = _granulo(familia)
    c, paso = sano["c"], sano["paso"]
    hueco = _granulo(familia)
    hueco["lat"][c - 2:c + 3] = np.nan
    hueco["lon"][c - 2:c + 3] = np.nan
    yield "sano", sano
    yield "hueco", hueco
    for nombre, corte in (("ultima_linea", (slice(0, c + 1), slice(None))),
                          ("primera_columna", (slice(None), slice(c, None)))):
        g = _granulo(familia)
        g = {**g, "lat": g["lat"][corte], "lon": g["lon"][corte],
             "ang": {k: v[corte] for k, v in g["ang"].items()}, "rad": {k: v[corte] for k, v in g["rad"].items()}}
        yield nombre, g
        # el mismo borde con el píxel del cráter perdido: una ventana que recortara el borde del gránulo no lo contaría
        g2 = {**g, "rad": {k: v.copy() for k, v in g["rad"].items()}}
        g2["rad"][g["b_mir"]][(c, c) if nombre == "ultima_linea" else (c, 0)] = np.nan    # el píxel del cráter
        yield nombre + "_pixel_perdido", g2
    junto = _granulo(familia)
    junto["lat"][c + 1:c + 1 + int(3.0 / paso)] = np.nan
    junto["lon"][c + 1:c + 1 + int(3.0 / paso)] = np.nan
    yield "hueco_junto", junto


@pytest.mark.parametrize("familia", FAMILIAS)
def test_ventana_y_regla_de_k_son_equivalentes(familia):
    """calcular_vrp_granulo mide sólo en la caja del recorte de 45 km (por costo); tiene que dar lo mismo que medir en el
    gránulo entero, y crater_sin_posicion tiene que ser exactamente la negación de process_modis.crater_cubierto (la
    regla de K, importada y no copiada). Los casos de borde son los que podrían separar ventana y gránulo."""
    from pipeline.process_modis import crater_cubierto
    vistos = set()
    for nombre, gr in _casos_equivalencia(familia):
        rec = _correr(gr, familia)
        assert rec is not None, f"{nombre}: sin record (error de armado)"
        entero = MV.dato_faltante_crater(gr["rad"], gr["lat"], gr["lon"], gr["b_mir"], gr["b_tir"], V_LAT, V_LON,
                                         PASO_NATIVO_KM[familia] * 1000.0)
        d = rec["diag_codigo_mirova"]
        assert {k: d.get(k) for k in entero} == entero, nombre
        assert entero["crater_sin_posicion"] is (not crater_cubierto(gr["lat"], gr["lon"], V_LAT, V_LON)), nombre
        vistos.add(entero["crater_sin_posicion"])
        if nombre.endswith("_pixel_perdido"):
            assert entero["px_mir_invalido_crater"] == 1, nombre   # control: el caso de borde cuenta algo
    assert vistos == {True, False}      # control: los casos ejercen las dos respuestas de la regla


# ------------------------------------------------------------------------------------------ (f) saturación VIIRS
SF, AO = 0.0002, 0.0      # escala ilustrativa del doble del L1B: el lector la toma del atributo
BIT_SATURACION = 4        # Tabla C.1 del UserGuide VIIRS L1B (docs/F28_SATURATION_INVESTIGATION.md): bit value 4
BIT_TEMP_NO_NOMINAL = 8   # otro bit de la misma tabla, que no es saturación


def _l1b(tmp_path, gr, qf_mir=None, nombre="l1b.nc"):
    import h5py
    ruta = tmp_path / nombre
    with h5py.File(ruta, "w") as f:
        obs = f.create_group("observation_data")
        for b in (gr["b_mir"], gr["b_tir"]):
            dn = np.clip(np.round((gr["rad"][b] - AO) / SF), 0, 65527).astype(np.uint16)
            ds = obs.create_dataset(b, data=dn)
            ds.attrs["scale_factor"] = np.array([SF], np.float32)
            ds.attrs["add_offset"] = np.array([AO], np.float32)
        if qf_mir is not None:
            obs.create_dataset(f"{gr['b_mir']}_quality_flags", data=qf_mir.astype(np.uint16))
    return ruta


def _correr_l1b(ruta, gr, familia):
    rad = MV.leer_radiancia_l1b(ruta, bandas=(gr["b_mir"], gr["b_tir"]))
    return MV.calcular_vrp_granulo(rad, gr["lat"], gr["lon"], gr["ang"], VOLC, V_LAT, V_LON, INNER_KM,
                                   SENSOR[familia], familia=familia), rad


@pytest.mark.parametrize("familia", ("VIIRS750", "VIIRS375"))
def test_saturacion_viirs_en_el_crater_queda_marcada_sin_cambiar_la_vrp(tmp_path, familia):
    gr = _granulo(familia)
    c = gr["c"]
    qf0 = np.zeros(gr["lat"].shape, np.uint16)
    qf1 = qf0.copy()
    qf1[c, c] = BIT_SATURACION | 1      # con otro bit encendido a la vez (Substitute_Cal): se mira sólo el de saturación
    rec0, rad0 = _correr_l1b(_l1b(tmp_path, gr, qf0, "sano.nc"), gr, familia)
    rec1, rad1 = _correr_l1b(_l1b(tmp_path, gr, qf1, "sat.nc"), gr, familia)
    assert _diag(rec1).get("px_saturados_crater") == 1
    assert _diag(rec0).get("px_saturados_crater") == 0
    assert np.array_equal(rad0[gr["b_mir"]], rad1[gr["b_mir"]], equal_nan=True)   # la radiancia no se toca
    _igual(_sin_claves_nuevas(rec0), _sin_claves_nuevas(rec1))                   # ni nada de lo publicado


@pytest.mark.parametrize("familia", ("VIIRS750", "VIIRS375"))
def test_saturacion_lejos_u_otro_bit_no_marca(tmp_path, familia):
    gr = _granulo(familia)
    c = gr["c"]
    qf = np.zeros(gr["lat"].shape, np.uint16)
    qf[c, c] = BIT_TEMP_NO_NOMINAL
    qf[c, c + 4] = BIT_SATURACION
    rec, _ = _correr_l1b(_l1b(tmp_path, gr, qf), gr, familia)
    assert _diag(rec).get("px_saturados_crater") == 0


def test_sin_quality_flags_la_saturacion_queda_sin_dato(tmp_path):
    """Sin `quality_flags` en el L1B (y siempre en MODIS, donde la saturación es un DN que el lector ya deja en NaN y
    cuenta en px_mir_invalido_crater) la marca es None: no medido, que no es lo mismo que cero."""
    gr = _granulo("VIIRS750")
    rec, rad = _correr_l1b(_l1b(tmp_path, gr, None), gr, "VIIRS750")
    assert sorted(rad) == ["M13", "M15"]
    d = _diag(rec)
    assert "px_saturados_crater" in d and d["px_saturados_crater"] is None
    dm = _diag(_correr(_granulo("MODIS"), "MODIS"))
    assert "px_saturados_crater" in dm and dm["px_saturados_crater"] is None


def test_quality_flags_no_enteros_no_tumban_la_pasada(tmp_path):
    """Un `quality_flags` que no es entero (el L1B de NASA siempre lo trae entero; hallazgo del verificador S191) deja
    la marca sin dato y la pasada se procesa igual que sin el dataset: el diagnóstico nunca puede tumbar una pasada."""
    import h5py
    gr = _granulo("VIIRS750")
    sano = _l1b(tmp_path, gr, None, "sin_qf.nc")
    raro = _l1b(tmp_path, gr, None, "qf_float.nc")
    with h5py.File(raro, "a") as f:
        f["observation_data"].create_dataset(f"{gr['b_mir']}_quality_flags",
                                             data=np.full(gr["lat"].shape, 4.0, np.float32))
    rec0, _ = _correr_l1b(sano, gr, "VIIRS750")
    rec1, rad1 = _correr_l1b(raro, gr, "VIIRS750")
    assert sorted(rad1) == ["M13", "M15"]
    assert _diag(rec1)["px_saturados_crater"] is None
    _igual(rec0, rec1)


if __name__ == "__main__":
    # Genera la referencia de (d) con el código que esté en pipeline/ al correrlo. Se corrió UNA vez con el código sin
    # el marcador (rama s190-marcador-crater en 618d0c93e); volver a correrlo después del cambio la vaciaría de sentido.
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    GOLDEN.parent.mkdir(exist_ok=True)
    salida = {f: _sin_claves_nuevas(_correr(_granulo(f), f)) for f in FAMILIAS}
    GOLDEN.write_text(json.dumps(salida, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for f, r in salida.items():
        print(f, r["vrp_mw"], r["n_anomalous_pixels"], r["diag_codigo_mirova"])
