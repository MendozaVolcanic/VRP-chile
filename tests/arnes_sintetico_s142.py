# -*- coding: utf-8 -*-
"""Arnés sintético S142 (D22/D25): corre `calculate_vrp` de los tres procesadores sobre escenas
fabricadas, con los lectores de gránulo reemplazados, y vuelca el resultado a JSON canónico.

POR QUÉ EXISTE. Hasta S140 no había un test que procesara un gránulo de punta a punta
(tests/test_fondo_persistido_s140.py lo dice en su docstring), así que "apagado no cambia nada"
sólo se podía afirmar leyendo código. Este arnés congela la salida de hoy en
tests/golden_s142/apagado.json y la compara, como TEXTO, con la de después. Se compara texto y no
diccionarios porque NaN != NaN en Python (el mismo modo de falla que S132).

LA ESCENA PRINCIPAL. Un cono nevado de noche: cumbre a 255 K y valle más tibio (+1,2 K por km
hasta 12 km). En el cráter hay un foco sub-píxel (el MIR sube a 266 K y el TIR casi no) y a su
lado un vecino tibio (262 K). Los dos quedan bajo la compuerta t_bg + 3 K (t_bg ~269,4 K) y bajo
la mediana del anillo, que es exactamente lo que miden D22 y D25.

LA ESCENA DEL TEST 1 (`test1_difuso`, agregada en S142 por el verificador, hallazgo H1). El mismo
cono, pero con un halo térmico suave y ancho sobre el cráter en vez de un píxel puntual: sube el
MIR ~5 K sobre el propio entorno de la cumbre y casi nada el TIR. El halo es más tibio que el
anillo de 1 a 3 km (por eso el Test 1 integrado dispara) y más frío que la mediana del anillo
regional de 5 a 25 km (por eso la compuerta lo rechaza y el fondo de hoy lo recorta a cero). Sin
esta escena, el golden no cubre el camino `test1_roi`, que es por donde sale la mayoría de las
detecciones reales de VIIRS 375, y una mutación del fondo de esos bloques pasaría el control
(hallazgo H1 del verificador del plan).

LA ESCENA MODIS `nevado_vecino_tibio` (agregada en S142, hallazgo H6 del verificador) es la misma
construcción a 1 km: sin ella la escena MODIS no ejercita la compuerta y el test "MODIS no cambia"
pasaría por construcción, aunque MODIS perdiera la compuerta.

Uso:
    VRP_PROFILE=mirova_equivalent python tests/arnes_sintetico_s142.py --salida X.json \
        [--parche NOMBRE=valor ...] [--solo v375]
Los parches reemplazan constantes de módulo de pipeline.process_viirs. Un nombre que no existe
hace fallar la corrida (patch.object levanta AttributeError): un brazo que no lee su flag no
puede pasar por control (S133).
"""
import argparse
import ast
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import numpy as np  # noqa: E402

LAT0, LON0 = -39.42, -71.94
N_V375 = 161
CENTRO_V375 = N_V375 // 2
_ANGULOS = {"sensor_zenith_deg": None, "sensor_azimuth_deg": None,
            "solar_zenith_deg": None, "solar_azimuth_deg": None}
ESCENAS_V375 = ("nevado_vecino_tibio", "test1_difuso", "foco_3x3", "plana")
ESCENAS_V750 = ("nevado", "plana")
ESCENAS_MODIS = ("nevado", "nevado_vecino_tibio", "plana")

# Halo del cráter de la escena `test1_difuso`: amplitud (K) y radio (km). Calibrados con un barrido
# (S142) para que el Test 1 integrado dispare con margen (k_sigma observado 12,1 contra 3 exigido;
# criterio relativo 0,0273 contra 0,02) y, a la vez, NINGÚN camino per-píxel marque nada: el halo es
# tan suave que ningún píxel es anómalo contra sus 8 vecinos. Resultado medido: primer pase 0,
# recaptura 0, camino contextual 0, n_anomalous_pixels 0 y `final_hotspot_source = "test1_roi"`.
# Subir la amplitud a 8 K mete un píxel de recaptura y la fuente pasa a `ctx_cluster`: el margen de
# esta escena es deliberadamente estrecho por arriba, y por eso el test comprueba las cuatro
# propiedades antes de usarla (si la escena deja de ejercer el camino del Test 1, el test lo dice
# en vez de pasar por la razón equivocada).
T1_HALO_AMP_K = 6.0
T1_HALO_RADIO_KM = 2.0


def _malla(n, px_km):
    d = (np.arange(n) - n // 2) * px_km
    y, x = np.meshgrid(d, d, indexing="ij")
    lat = (LAT0 + y / 111.0).astype(np.float32)
    lon = (LON0 + x / (111.0 * np.cos(np.radians(LAT0)))).astype(np.float32)
    return lat, lon, np.hypot(y, x)


def _geo(lat, lon):
    return {"lat": lat, "lon": lon, "sensor_zenith": np.zeros(lat.shape, np.float32),
            "angles": dict(_ANGULOS)}


def _cono(r, rng):
    return 255.0 + np.clip(r, 0, 12) * 1.2 + rng.normal(0, 0.15, r.shape)


def _halo_suave(r, amp_k, radio_km):
    """Campana coseno: vale amp_k en el centro y 0 en radio_km, con derivada nula en los dos
    extremos. La suavidad es deliberada: un escalón haría anómalo al píxel del borde contra sus 8
    vecinos y dispararía el camino contextual, que es justo el que esta escena NO quiere ejercitar.
    """
    x = np.clip(r / radio_km, 0.0, 1.0)
    return amp_k * 0.5 * (1.0 + np.cos(np.pi * x))


def escena_v375(tipo, semilla=0):
    lat, lon, r = _malla(N_V375, 0.375)
    rng = np.random.default_rng(semilla)
    bt4 = _cono(r, rng)
    bt5 = bt4 - 1.0 + rng.normal(0, 0.15, r.shape)
    c = CENTRO_V375
    if tipo == "nevado_vecino_tibio":
        bt4[c, c], bt5[c, c] = 266.0, 255.5
        bt4[c, c + 1], bt5[c, c + 1] = 262.0, 254.5
    elif tipo == "test1_difuso":
        halo = _halo_suave(r, T1_HALO_AMP_K, T1_HALO_RADIO_KM)
        bt4 = bt4 + halo
        bt5 = bt5 + 0.1 * halo   # el TIR casi no sube: firma sub-píxel
    elif tipo == "foco_3x3":
        bt4[c - 1:c + 2, c - 1:c + 2] = 300.0
        bt4[c, c] = 320.0
        bt5[c - 1:c + 2, c - 1:c + 2] += 3.0
    elif tipo != "plana":
        raise ValueError(tipo)
    return {"I04": bt4.astype(np.float32), "I05": bt5.astype(np.float32)}, _geo(lat, lon)


def escena_v750(tipo, semilla=1):
    n = 81
    lat, lon, r = _malla(n, 0.75)
    rng = np.random.default_rng(semilla)
    m13 = _cono(r, rng)
    m15 = m13 - 1.0 + rng.normal(0, 0.15, r.shape)
    c = n // 2
    if tipo == "nevado":
        m13[c, c], m15[c, c] = 275.0, 256.0
        m13[c, c + 1], m15[c, c + 1] = 263.0, 255.0
    elif tipo != "plana":
        raise ValueError(tipo)
    return {"M13": m13.astype(np.float32), "M15": m15.astype(np.float32)}, _geo(lat, lon)


def escena_modis(tipo, semilla=2):
    import pipeline.process_modis as pm
    n = 61
    lat, lon, r = _malla(n, 1.0)
    rng = np.random.default_rng(semilla)
    bt21 = _cono(r, rng)
    bt31 = bt21 - 1.0 + rng.normal(0, 0.15, r.shape)
    c = n // 2
    if tipo == "nevado":
        bt21[c, c], bt31[c, c] = 290.0, 258.0
    elif tipo == "nevado_vecino_tibio":
        # H6 del verificador: la escena `nevado` tiene el cráter a 290 K, muy por encima de
        # t_bg + 3 K, así que la compuerta no decide nada y el test "MODIS no cambia" pasaría
        # igual con la compuerta rota. Acá el cráter (266 K) y su vecino (262 K) quedan DEBAJO
        # de la compuerta y son anómalos contra sus 8 vecinos: es la escena donde la compuerta
        # sí manda, a 1 km de píxel.
        bt21[c, c], bt31[c, c] = 266.0, 255.5
        bt21[c, c + 1], bt31[c, c + 1] = 262.0, 254.5
    elif tipo != "plana":
        raise ValueError(tipo)

    def rad(bt, lam):
        return (pm.C1 / (lam ** 5 * (np.exp(pm.C2 / (lam * bt)) - 1))).astype(np.float32)

    lam21 = pm.BAND21_LAMBDA
    return {"band21": rad(bt21, lam21), "band22": rad(bt21, lam21),
            "band31": rad(bt31, 11.03), "lat": lat, "lon": lon}


def _con_parches(modulo, parches):
    ctx = [patch.object(modulo, k, v) for k, v in parches.items()]
    for p in ctx:
        p.start()
    return ctx


def correr_v375(tipo, local_kernel_bg_compatible, parches):
    import pipeline.process_viirs as pv
    bands, geo = escena_v375(tipo)
    ctx = _con_parches(pv, parches)
    try:
        with patch.object(pv, "read_viirs_l1b", return_value=bands), \
                patch.object(pv, "read_viirs_geo", return_value=geo):
            return pv.calculate_vrp(
                Path("VNP02IMG.A2026200.0600.002.nc"), Path("VNP03IMG.sintetico.nc"),
                volcano_lat=LAT0, volcano_lon=LON0, radius_km=25.0,
                vent_lat=LAT0, vent_lon=LON0, inner_radius_km=5.0,
                local_kernel_bg_compatible=local_kernel_bg_compatible)
    finally:
        for p in ctx:
            p.stop()


def correr_v750(tipo):
    import pipeline.process_viirs_mod as pvm
    bands, geo = escena_v750(tipo)
    with patch.object(pvm, "read_viirs_mod_l1b", return_value=bands), \
            patch.object(pvm, "read_viirs_mod_geo", return_value=geo):
        return pvm.calculate_vrp(
            Path("VNP02MOD.A2026200.0600.002.nc"), Path("VNP03MOD.sintetico.nc"),
            volcano_lat=LAT0, volcano_lon=LON0, radius_km=25.0,
            vent_lat=LAT0, vent_lon=LON0, inner_radius_km=5.0)


def correr_modis(tipo):
    import pipeline.process_modis as pm
    data = escena_modis(tipo)
    with patch.object(pm, "read_modis_l1b", return_value=data):
        return pm.calculate_vrp(
            hdf_path=Path("MOD021KM.A2026200.0300.061.hdf"), geo_path=Path("MOD03.sintetico.hdf"),
            volcano_lat=LAT0, volcano_lon=LON0, radius_km=25.0,
            vent_lat=LAT0, vent_lon=LON0, inner_radius_km=5.0)


def entradas_helpers():
    """Entradas de los helpers de detection_context sacadas de la escena principal."""
    import pipeline.process_viirs as pv
    from pipeline.detection_context import compute_nti_and_nti_app
    bands, geo = escena_v375("nevado_vecino_tibio")
    bt4 = bands["I04"].astype(np.float64)
    bt5 = bands["I05"].astype(np.float64)
    l_mir = pv.bt_to_spectral_radiance(bt4, pv.I04_LAMBDA)
    nti, nti_app = compute_nti_and_nti_app(rad_mir=l_mir, bt_tir=bt5,
                                           lambda_mir_um=pv.I04_LAMBDA, lambda_tir_um=11.450)
    dist = pv.haversine_km(LAT0, LON0, geo["lat"], geo["lon"])
    roi = pv.roi_mask_bbox(geo["lat"], geo["lon"], LAT0, LON0, 25.0)
    t_bg = float(np.median(bt4[(dist >= 5.0) & (dist <= 25.0)]))
    return {"bt": bt4, "nti": nti, "nti_app": nti_app, "dist": dist, "roi": roi, "t_bg": t_bg}


def salidas_helpers(**extra):
    """Las tres funciones con la compuerta, llamadas como las llama producción.
    `extra` se reenvía a las tres (lo usa el test de D22 con apply_bt_gate=False)."""
    from pipeline.detection_context import (contextual_dnti_hot_mask,
                                            dual_roi_contextual_dnti_hot_mask,
                                            first_pass_tests_2_and_3)
    e = entradas_helpers()
    ctx = contextual_dnti_hot_mask(nti=e["nti"], bt=e["bt"], roi_mask=e["roi"], t_bg=e["t_bg"],
                                   c1=0.003, bt_sanity_k=3.0, apply_unsuitable_filters=True, **extra)
    dual = dual_roi_contextual_dnti_hot_mask(nti=e["nti"], bt=e["bt"], roi_mask=e["roi"],
                                             dist_km=e["dist"], t_bg=e["t_bg"], c1_summit=0.003,
                                             c1_scene=0.010, inner_km=5.0, bt_sanity_k=3.0,
                                             apply_unsuitable_filters=True, **extra)
    fp, diag = first_pass_tests_2_and_3(nti=e["nti"], nti_app=e["nti_app"], bt=e["bt"],
                                        roi_mask=e["roi"], dist_km=e["dist"], t_bg=e["t_bg"],
                                        bt_sanity_k=3.0, inner_km=5.0, c1_dnti_scene=0.010,
                                        c1_deti_scene=0.010, c2_dnti_scene=10, c2_deti_scene=10,
                                        **extra)
    return {
        "contextual": np.flatnonzero(ctx).tolist(),
        "dual": np.flatnonzero(dual).tolist(),
        "first_pass": np.flatnonzero(fp).tolist(),
        "first_pass_diag": {k: diag[k] for k in ("n_first_pass_pixels", "mu_dnti", "sd_dnti",
                                                  "mu_deti", "sd_deti", "n_bg_used")},
    }


def generar(parches, solo=None):
    import pipeline.profile as prof
    out = {"perfil": prof.PROFILE_NAME}
    if solo in (None, "helpers"):
        out["helpers"] = salidas_helpers()
    if solo in (None, "v375"):
        out["v375"] = {f"{t}|kernel={k}": correr_v375(t, k, parches)
                       for t in ESCENAS_V375 for k in (False, True)}
    if solo in (None, "v750"):
        out["v750"] = {t: correr_v750(t) for t in ESCENAS_V750}
    if solo in (None, "modis"):
        out["modis"] = {t: correr_modis(t) for t in ESCENAS_MODIS}
    return out


def _a_json(o):
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    return repr(o)


# S142: cifras significativas con que se escribe cada float del golden.
# POR QUÉ. El mismo cálculo da el último dígito distinto en Windows y en Linux (orden de las
# operaciones de la BLAS y del compilador): `sd_dnti` 0,00025641447808233127 contra
# 0,0002564144780823313, o sea 1e-16 relativo. Comparando el JSON como texto crudo, el golden
# mide en qué máquina corrió y no si el pipeline cambió: así se cayó el CI del PR #681. Con 12
# cifras el ruido desaparece y cualquier cambio con sentido físico sigue viéndose (un VRP que
# pasa de 0,0 a 0,097 MW, o el 1e-6 relativo del control en
# tests/test_apagado_no_cambia_nada_s142.py). No es tolerancia numérica del pipeline: es cómo se
# escribe el archivo de comparación.
SIGNIFICATIVAS = 12


def _redondear(o):
    """Redondea a SIGNIFICATIVAS cada float del árbol, respetando NaN, inf y enteros."""
    if isinstance(o, bool) or isinstance(o, int):
        return o
    if isinstance(o, float):
        if o != o or o in (float("inf"), float("-inf")) or o == 0.0:
            return o
        return float(f"{o:.{SIGNIFICATIVAS}g}")
    if isinstance(o, np.ndarray):
        return [_redondear(v) for v in o.tolist()]
    if isinstance(o, np.generic):
        return _redondear(o.item())
    if isinstance(o, dict):
        return {k: _redondear(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_redondear(v) for v in o]
    return o


def canonico(obj):
    return json.dumps(_redondear(obj), sort_keys=True, indent=1, default=_a_json,
                      ensure_ascii=False)


def correr_en_subproceso(tmp_dir, perfil="mirova_equivalent", parches=(), solo=None):
    """Corre el arnés en un proceso limpio (pipeline.profile se lee al importar) y devuelve el
    TEXTO del JSON. Cada perfil o parche necesita su propio proceso."""
    import subprocess
    salida = Path(tmp_dir) / f"arnes_{perfil}_{len(parches)}_{solo}.json"
    cmd = [sys.executable, str(ROOT / "tests" / "arnes_sintetico_s142.py"), "--salida", str(salida)]
    for p in parches:
        cmd += ["--parche", p]
    if solo:
        cmd += ["--solo", solo]
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=1800,
                       env={**os.environ, "VRP_PROFILE": perfil, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-4000:]
    return salida.read_text(encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--parche", action="append", default=[])
    ap.add_argument("--solo", choices=("helpers", "v375", "v750", "modis"), default=None)
    a = ap.parse_args(argv)
    parches = {}
    for s in a.parche:
        k, v = s.split("=", 1)
        parches[k] = ast.literal_eval(v)
    texto = canonico(generar(parches, a.solo))
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(a.salida).write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    main()
