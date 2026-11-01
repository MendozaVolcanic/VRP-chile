# -*- coding: utf-8 -*-
"""Verificador S164, A2: la parametrizacion por sensor (FAMILIAS) no cambia la via de VIIRS 750.

Carga DOS copias del modulo pipeline/mirova_v750_codigo.py: la del tag base (extraida con git archive al scratchpad) y
la de HEAD, y corre con los argumentos por defecto (los que usa process_viirs_mod.py) sobre:
  (a) la pasada de ejemplo del OSF (Etna, VIIRS750_example.mat);
  (b) las 8 escenas del oro de MATLAB (tests/data/fillmissing2_matlab_o2.npz): fondo y VRP;
  (c) 30 grillas sinteticas 67 x 67 con focos al azar y bordes NaN: detectar_mirova + diag, vrp_mirova, procesar_grilla;
  (d) grilla_del_volcan y caja_roi para los 11 volcanes y los 5 tipos de ROI;
  (e) calcular_vrp_granulo sobre un granulo sintetico de 750 m en Lascar (remuestreo incluido).
Compara con repr exacto de cada float (sin tolerancia).
Uso: python a2_v750_base_vs_head.py <ruta_base_tag>
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
BASE = Path(sys.argv[1])


def cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def crudo(o):
    if isinstance(o, dict):
        return {str(k): crudo(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [crudo(v) for v in o]
    if isinstance(o, np.ndarray):
        return crudo(o.tolist())
    if isinstance(o, np.generic):
        return crudo(o.item())
    if isinstance(o, float):
        return repr(o)
    return o


def igual(a, b):
    return json.dumps(crudo(a), sort_keys=True) == json.dumps(crudo(b), sort_keys=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    # el modulo lee grillas_mirova.yaml y volcanoes.yaml relativo a su archivo / a la raiz: se parchea igual en los dos
    B = cargar("mv_base", BASE / "pipeline/mirova_v750_codigo.py")
    H = cargar("mv_head", RAIZ / "pipeline/mirova_v750_codigo.py")
    print("constantes V750:", {k: (getattr(B, k), getattr(H, k)) for k in
                               ("LAMBDA_M13", "LAMBDA_M15", "COEF_VRP_V750", "PASO_V750_M", "MEDIA_GRILLA_M",
                                "RADIO_RECORTE_KM", "FLAG_MIN_DN")})
    res = {}

    # (a) Etna
    import scipy.io as sio
    S = sio.loadmat(RAIZ / "experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat")
    args = (S["ZI_M13"], S["ZI_M15"], S["BOX"], int(S["dayflag"].item()))
    sgB = B.sunglint_deg(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())
    sgH = H.sunglint_deg(S["sat_zen"].item(), S["sun_zen"].item(), S["sat_azi"].item(), S["sun_azi"].item())
    mB, dB = B.detectar_mirova(*args, sgB, devolver_diag=True)
    mH, dH = H.detectar_mirova(*args, sgH, devolver_diag=True)
    quitar = lambda d: {k: v for k, v in d.items() if k not in ("contrastes", "box", "nti")}  # noqa: E731
    res["a_etna_mascara"] = np.array_equal(mB, mH)
    res["a_etna_diag"] = igual(quitar(dB), quitar(dH)) and all(
        np.array_equal(np.asarray(dB["contrastes"][p][i]), np.asarray(dH["contrastes"][p][i]), equal_nan=True)
        for p in (1, 2) for i in (0, 1))
    res["a_etna_vrp"] = igual(B.vrp_mirova(S["ZI_M13"], mB), H.vrp_mirova(S["ZI_M13"], mH))

    # (b) oro MATLAB
    z = np.load(RAIZ / "tests/data/fillmissing2_matlab_o2.npz")
    from scipy.ndimage import binary_dilation
    ok_b = True
    for n in range(len(z["k_o2"])):
        m13, mask = z[f"m13_{n}"], z[f"mask_{n}"]
        enm = m13.copy()
        enm[mask] = np.nan
        k = 3 if mask.sum() <= 4 else (5 if mask.sum() <= 30 else 7)
        enm[binary_dilation(np.isnan(enm), structure=np.ones((k, k), bool))] = np.nan
        ok_b &= np.array_equal(B._fillmissing2_lineal(enm), H._fillmissing2_lineal(enm), equal_nan=True)
        ok_b &= igual(B.vrp_mirova(m13, mask), H.vrp_mirova(m13, mask))
    res["b_oro_matlab_8_escenas"] = bool(ok_b)

    # (c) sinteticas
    g = H.grilla_del_volcan("Lascar")
    gB = B.grilla_del_volcan("Lascar")
    res["d_grilla_lascar"] = igual(g, gB)
    ok_c, n_alert = True, 0
    for s in range(30):
        r = np.random.default_rng(s)
        n = 67
        m13 = H.temperatura_a_radiancia(270 + r.normal(0, 0.5, (n, n)), 4.05)
        m15 = H.temperatura_a_radiancia(268 + r.normal(0, 0.5, (n, n)), 10.763)
        for _ in range(r.integers(0, 4)):
            i, j = r.integers(28, 39, 2)
            m13[i, j] *= r.uniform(1.5, 6.0)
        if s % 3 == 1:
            m13[: r.integers(2, 12), :] = np.nan
            m15[: 3, :] = np.nan
        box = H.caja_roi("def")
        for M in (B, H):
            assert np.array_equal(M.caja_roi("def"), box)
        mB, dB = B.detectar_mirova(m13, m15, box, 0, 40.0, devolver_diag=True)
        mH, dH = H.detectar_mirova(m13, m15, box, 0, 40.0, devolver_diag=True)
        ok_c &= np.array_equal(mB, mH) and igual(quitar(dB), quitar(dH))
        ok_c &= igual(B.vrp_mirova(m13, mB), H.vrp_mirova(m13, mH))
        rB = B.procesar_grilla(m13, m15, gB, box, 0, 40.0, (33.0, 33.0), 5.0, "VIIRS_NOAA20_750")
        rH = H.procesar_grilla(m13, m15, g, box, 0, 40.0, (33.0, 33.0), 5.0, "VIIRS_NOAA20_750")
        ok_c &= igual(rB, rH)
        n_alert += int(mH.sum() > 0)
    res["c_sinteticas_30_detectar_vrp_record"] = bool(ok_c)
    res["c_sinteticas_con_alerta"] = n_alert

    # (d) grillas y cajas
    ok_d = True
    for nombre in sorted(H._referencias()):
        ok_d &= igual(B.grilla_del_volcan(nombre), H.grilla_del_volcan(nombre))
        for tipo in ("def", "sens", "corona"):
            ok_d &= np.array_equal(B.caja_roi(tipo), H.caja_roi(tipo))
        ok_d &= np.array_equal(B.caja_roi("crater", celda_crater=(33, 35)), H.caja_roi("crater", celda_crater=(33, 35)))
        ok_d &= np.array_equal(B.caja_roi("inner", inner_km=5.0), H.caja_roi("inner", inner_km=5.0))
    res["d_grillas_y_cajas_11_volcanes"] = bool(ok_d)

    # (e) granulo sintetico 750 m en Lascar
    import yaml
    vl = {x["name"]: x for x in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}["Lascar"]
    n = 161
    d = (np.arange(n) - n // 2) * 0.75
    y, x = np.meshgrid(d, d, indexing="ij")
    lat = vl["lat"] - y / 111.0
    lon = vl["lon"] + x / (111.0 * np.cos(np.radians(vl["lat"])))
    r = np.random.default_rng(750)
    T13 = 265.0 + r.normal(0, 0.3, lat.shape)
    T15 = 265.0 + r.normal(0, 0.3, lat.shape)
    T13[n // 2, n // 2] = 310.0
    rad = {"M13": H.temperatura_a_radiancia(T13, 4.05), "M15": H.temperatura_a_radiancia(T15, 10.763)}
    ang = {"sensor_zenith": np.full(lat.shape, 20.0), "sensor_azimuth": np.full(lat.shape, 0.0),
           "solar_zenith": np.full(lat.shape, 140.0), "solar_azimuth": np.full(lat.shape, 90.0)}
    rB = B.calcular_vrp_granulo(rad, lat, lon, ang, "Lascar", vl["lat"], vl["lon"], 5.0, "VIIRS_NOAA20_750")
    rH = H.calcular_vrp_granulo(rad, lat, lon, ang, "Lascar", vl["lat"], vl["lon"], 5.0, "VIIRS_NOAA20_750")
    res["e_granulo_sintetico_750m"] = igual(rB, rH)
    res["e_granulo_npix_vrp"] = (rH["n_anomalous_pixels"], rH["vrp_mw"])

    for k, v in res.items():
        print(f"  {k}: {v}")
    print("A2 V750 base == head en todo:", all(v is True for k, v in res.items()
                                                 if k not in ("c_sinteticas_con_alerta", "e_granulo_npix_vrp")))


if __name__ == "__main__":
    main()
