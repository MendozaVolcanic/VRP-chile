"""Frente G: NULO del Test 1 integrado. Campo de BT = ruido gaussiano puro (sin cuerpo caliente) sobre una grilla regular.
Usa la funcion REAL pipeline.test1_integrated.compute_test1_mir con los parametros efectivos del perfil. Solo lectura."""
import os, sys, json, numpy as np
os.environ["VRP_PROFILE"] = "mirova_equivalent"
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")); sys.path.insert(0, root)
import pipeline.profile as p
from pipeline.test1_integrated import compute_test1_mir
rng = np.random.default_rng(146)
out = {}
for nombre, cell_km, lam in (("VIIRS375", 0.375, 3.74), ("VIIRS750", 0.75, 4.05), ("MODIS", 1.0, 3.959)):
    n = int(10 / cell_km); ax = (np.arange(n) - n / 2 + 0.5) * cell_km
    lat0 = -39.42; lat = lat0 + (ax[::-1][:, None] / 111.32) * np.ones((1, n)); lon = -71.94 + (ax[None, :] / (111.32 * np.cos(np.radians(lat0)))) * np.ones((n, 1))
    out[nombre] = {}
    for sd in (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
        trig = absc = relc = 0; nroi = None; N = 300
        for _ in range(N):
            bt = 265.0 + rng.normal(0, sd, size=(n, n))
            r = compute_test1_mir(bt=bt, lat=lat, lon=lon, vent_lat=lat0, vent_lon=-71.94, lambda_um=lam,
                                  roi_km=p.TEST1_ROI_KM, inner_ring_km=p.TEST1_INNER_RING_KM, k_sigma=p.TEST1_K_SIGMA,
                                  mir_relative=p.TEST1_MIR_RELATIVE, nti_hot_mask=None)
            trig += bool(r["triggered"]); absc += bool(r["abs_criterion"]); relc += bool(r["rel_criterion"]); nroi = r["n_roi"]
        out[nombre][str(sd)] = {"n_roi": nroi, "tasa_abs": absc / N, "tasa_rel": relc / N, "tasa_dispara": trig / N}
        print(nombre, "sd_BT=", sd, "K n_roi=", nroi, "abs=", absc / N, "rel=", relc / N, "DISPARA=", trig / N)
json.dump({"params": {"roi_km": p.TEST1_ROI_KM, "inner_ring_km": p.TEST1_INNER_RING_KM, "k_sigma": p.TEST1_K_SIGMA, "mir_relative": p.TEST1_MIR_RELATIVE},
           "t_fondo_K": 265.0, "resultado": out}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "nulo_test1_ruido_puro.json"), "w"), indent=1)
