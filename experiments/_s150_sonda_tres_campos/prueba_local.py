# -*- coding: utf-8 -*-
"""S150, sonda de los tres campos: prueba local SIN NASA (y sin credenciales).

Lo que se puede probar sin bajar granulos, y por que importa cada cosa:
  P1. La interpolacion swath -> grilla de MIROVA reproduce un campo analitico suave (si no, el campo (c)
      seria un artefacto del interpolador y no la grilla de MIROVA).
  P2. Recortar el granulo al ROI con margen no cambia mu, sigma ni la mascara del primer pase: se
      comprueba contra la funcion REAL sobre el granulo entero (el control de identidad que la sonda
      repite en cada pasada real).
  P3. De punta a punta con un granulo SINTETICO (lectores reemplazados por arrays): los cinco campos
      corren el calculate_vrp REAL, el record pasa por el store.append_record real a un temporal, la
      replica del segundo pase coincide con la funcion real, y la validacion contra un "TIF" conocido
      elige el interpolador correcto (control positivo de la validacion) y distingue a los otros.
  P4. La validacion contra un GeoTIFF REAL de MIROVA en disco (sin bajar nada): contra si mismo da 1,
      contra una version suavizada baja la razon de desviaciones, contra una corrida una celda baja la
      correlacion de la textura. O sea, la metrica esta viva en las dos direcciones.
  P0. Las guardas de entorno detienen la sonda sin token, con usuario y clave, o con otro perfil.
  P5. evaluar.py corre sobre las salidas de P3 (con grupos ficticios) sin romperse.
  P6. evaluar.py con clones que publican en TODO sobre la meta real (365 pasadas): el nativo no reproduce
      el A/B y el veredicto TIENE que ser INDETERMINADO POR INSTRUMENTO (antes daba CONFIRMA con salvedad).
  P7. Poblaciones sinteticas con la meta real: CONFIRMA, REFUTA (por falsos y por recall), zona gris,
      cobertura insuficiente (el piloto, y el borde de 2 y 3 perdidas faltantes), reproduccion en su borde,
      brecha minima, sigma contra el A/B, control positivo de D22, identidad de escena y modo piloto. Un
      veredicto solo se cree si se le ve salir cuando corresponde y no salir cuando no (A110 d).
  P7b. Un caso por hallazgo del segundo verificador (V2-1 a V2-7 y V2-10); cada uno falla con el evaluador
      de 5eda5b942 y pasa con el nuevo.
  P7c. Un caso por hallazgo del tercer verificador (N1, N2, N3, N5); cada uno falla con aae4a4ed0.
  P8. El sello cubre la sonda, pipeline/, el predicado, el arnes, el catalogo y el yml, y se rompe.

  VRP_PROFILE=_s147_ab_sin_test1_max python prueba_local.py
"""
import io
import json
import os
import sys
import tempfile
import zlib
from pathlib import Path

os.environ["VRP_PROFILE"] = "_s147_ab_sin_test1_max"
for k in ("EARTHDATA_USERNAME", "EARTHDATA_PASSWORD"):
    os.environ.pop(k, None)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
import numpy as np  # noqa: E402

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for p in (RAIZ, RAIZ / "scripts", AQUI):
    sys.path.insert(0, str(p))
import campos as cp  # noqa: E402
import sonda  # noqa: E402

FALLAS = []
N_CHEQUEOS = [0]
SALTADAS = [0]     # comprobaciones que no corrieron (P4 sin el TIF en disco, P8 sin bash): se dicen al final


def chequear(cond, msg):
    N_CHEQUEOS[0] += 1
    print(("  OK   " if cond else "  FALLA ") + msg, flush=True)
    if not cond:
        FALLAS.append(msg)


def swath_sintetico(clat, clon, n=720, paso=0.375, rot_deg=12.0, semilla=7, foco=True, ruido=0.35):
    """Swath con rotacion y estiramiento a lo largo del barrido (pixel 1,0 a 1,5 veces), como VIIRS."""
    rng = np.random.default_rng(semilla)
    i, j = np.meshgrid(np.arange(n) - n / 2, np.arange(n) - n / 2, indexing="ij")
    estira = 1.0 + 0.5 * ((j + n / 2) / n)               # el pixel crece hacia un borde
    u = np.cumsum(np.ones(n) * paso * estira[0, :]) - (paso * estira[0, :]).sum() / 2
    x0 = np.broadcast_to(u, (n, n)); y0 = -i * paso
    a = np.radians(rot_deg)
    x = x0 * np.cos(a) - y0 * np.sin(a); y = x0 * np.sin(a) + y0 * np.cos(a)
    kx = 111.320 * np.cos(np.radians(clat))
    lat = clat + y / 111.320; lon = clon + x / kx
    base = 268.0 + 4.0 * np.sin(x / 7.0) * np.cos(y / 9.0)
    bt5 = base + rng.normal(0, ruido, (n, n))
    bt4 = base - 1.0 + rng.normal(0, ruido, (n, n))
    if foco:
        d = np.hypot(x, y)
        k = np.unravel_index(np.argmin(d), d.shape)
        bt4[k] += 9.0
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di or dj:
                    bt4[k[0] + di, k[1] + dj] += 2.0
    sz = np.full((n, n), 40.0, dtype=np.float32)
    ang = {"sensor_zenith_deg": sz.copy(), "sensor_azimuth_deg": np.full((n, n), 90.0, np.float32),
           "solar_zenith_deg": np.full((n, n), 120.0, np.float32), "solar_azimuth_deg": np.full((n, n), 0.0, np.float32)}
    geo = {"lat": lat.astype(np.float32), "lon": lon.astype(np.float32), "sensor_zenith": sz, "angles": ang}
    bands = {"I04": bt4.astype(np.float32), "I05": bt5.astype(np.float32)}
    return bands, geo, (x, y)


def p0_guardas():
    print("P0. guardas de entorno: sin token o con usuario y clave la sonda no arranca (A71)", flush=True)
    viejo = dict(os.environ)
    try:
        os.environ.pop("EARTHDATA_TOKEN", None)
        try:
            sonda.guardas_de_entorno(); chequear(False, "sin token deberia detenerse")
        except SystemExit as e:
            chequear("EARTHDATA_TOKEN" in str(e), "sin token se detiene: %s" % e)
        os.environ["EARTHDATA_TOKEN"] = "x"; os.environ["EARTHDATA_USERNAME"] = "alguien"
        try:
            sonda.guardas_de_entorno(); chequear(False, "con usuario deberia detenerse")
        except SystemExit as e:
            chequear("USERNAME" in str(e), "con usuario y clave en el entorno se detiene")
        os.environ.pop("EARTHDATA_USERNAME"); os.environ["VRP_PROFILE"] = "mirova_equivalent"
        try:
            sonda.guardas_de_entorno(); chequear(False, "con otro perfil deberia detenerse")
        except SystemExit as e:
            chequear("VRP_PROFILE" in str(e), "con un perfil distinto del F se detiene")
    finally:
        os.environ.clear(); os.environ.update(viejo)


def p1_interpolacion():
    print("P1. interpolacion a la grilla de MIROVA contra un campo analitico suave", flush=True)
    pl = json.loads((AQUI / "plantillas_tif.json").read_text(encoding="utf-8"))["Chaiten"]
    lat_g, lon_g = cp.grilla_plantilla(pl)
    clat, clon = float(lat_g.mean()), float(lon_g.mean())
    _, geo, _ = swath_sintetico(clat, clon, foco=False)
    from pipeline.regrid import _utm_like_xy
    def campo(la, lo):
        x, y = _utm_like_xy(la, lo, clat, clon)
        return 0.05 + 0.01 * np.sin(x / 7.0) * np.cos(y / 9.0)
    v_sw = campo(geo["lat"].astype(np.float64), geo["lon"].astype(np.float64))
    verdad = campo(lat_g, lon_g)
    validas = np.ones(v_sw.shape, dtype=bool)
    for metodo, tope in (("linear", 2e-4), ("cubic", 2e-4), ("nearest", 1e-3)):
        f, info = cp.interpolador_a_grilla(geo["lat"], geo["lon"], lat_g, lon_g, metodo, validas)
        g = f(v_sw)
        m = np.isfinite(g)
        err = float(np.nanmax(np.abs(g[m] - verdad[m])))
        chequear(m.mean() > 0.99 and err < tope, "%s: %.1f %% de celdas con dato, error maximo %.2e (tope %.0e)" % (
            metodo, 100 * m.mean(), err, tope))
    # ida y vuelta de Planck exacta
    bt = np.array([230.0, 260.0, 300.0, 350.0])
    for lam in (cp.LAMBDA_I04, cp.LAMBDA_I05):
        chequear(np.allclose(cp.rad_a_bt(cp.bt_a_rad(bt, lam), lam), bt, atol=1e-9), "Planck ida y vuelta a %.2f um" % lam)


def p2_recorte():
    print("P2. el recorte al ROI no cambia mu, sigma ni la mascara (contra la funcion REAL sobre el granulo entero)", flush=True)
    from pipeline import detection_context as dc
    from pipeline.scan_geometry import haversine_km, roi_mask_bbox
    from pipeline.process_viirs import bt_to_spectral_radiance
    clat, clon = -42.835, -72.650
    bands, geo, _ = swath_sintetico(clat, clon)
    lat, lon = geo["lat"], geo["lon"]
    roi = roi_mask_bbox(lat, lon, clat, clon, 25.0)
    L4 = bt_to_spectral_radiance(bands["I04"], 3.74); L5 = bt_to_spectral_radiance(bands["I05"], 11.45)
    nti = (L4 - L5) / (L4 + L5)
    _, nti_app = dc.compute_nti_and_nti_app(L4, bands["I05"], 3.74, 11.45)
    dist = haversine_km(clat, clon, lat, lon)
    kw = dict(nti=nti, nti_app=nti_app, bt=bands["I04"], roi_mask=roi, dist_km=dist, roi1_mask=None,
              t_bg=267.0, bt_sanity_k=3.0, c1_dnti_summit=0.003, c1_deti_summit=0.003, c2_dnti_summit=5.0,
              c2_deti_summit=5.0, inner_km=5.0, c1_dnti_scene=0.01, c1_deti_scene=0.01, c2_dnti_scene=10.0,
              c2_deti_scene=10.0, test1_mask=None, unsuitable_dnti_floor=-0.1, unsuitable_deti_floor=-0.1,
              use_prose_branch=True, apply_bt_gate=True)
    hot, diag = dc.first_pass_tests_2_and_3(**kw)
    sp_kw = {"c1_dnti": 0.003, "c1_deti": 0.003, "c2_dnti": 5.0, "c2_deti": 5.0, "is_summit": "ARRAY",
             "c1_dnti_scene": 0.01, "c1_deti_scene": 0.01, "c2_dnti_scene": 10.0, "c2_deti_scene": 10.0,
             "conditioned": False, "use_prose_branch": True}
    # la corrida REAL del segundo pase sobre el granulo ENTERO (lo que la sonda captura como sp_out_n)
    sp_real = dc.second_pass_adjacent(nti=nti, eti=diag["eti"], active_mask=hot,
                                      **{**sp_kw, "is_summit": dc.roi1_summit_mask(dist, 5.0, None)})
    cap = {"fp_kw": kw, "fp_diag": {k: v for k, v in diag.items() if not isinstance(v, np.ndarray)},
           "sp_kw": sp_kw, "fp_hot": hot, "sp_out_n": int(np.sum(sp_real))}
    ev = cp.evaluar_campo(cap, lat, lon, [(clat, clon)], np.random.default_rng(1))
    caja = cp.caja_recorte(roi)
    chequear(caja[0].stop - caja[0].start < roi.shape[0] or caja[1].stop - caja[1].start < roi.shape[1],
             "el recorte es mas chico que el granulo (%s de %s)" % ((caja[0].stop - caja[0].start, caja[1].stop - caja[1].start), roi.shape))
    rel = ev["identidad_primer_pase"]
    chequear(all(v is not None and v < 1e-9 for v in rel.values()), "mu y sigma recortados = los del granulo entero: %s" % rel)
    chequear(ev["identidad_n_pool"], "mismo tamano del pozo de fondo (%d)" % ev["primer_pase"]["n_pool"])
    d = ev["decision"]["max|con_compuerta"]
    chequear(d["n_hot_1_escena"] == int((hot & roi).sum()), "misma cantidad de pixeles del primer pase (%d)" % d["n_hot_1_escena"])
    chequear(all(v["identidad_hot_1"] for v in ev["decision"].values()), "mascara del primer pase = funcion real en las 4 combinaciones")
    chequear(all(v["identidad_final"] for k, v in ev["decision"].items() if not k.endswith("d26")),
             "replica del segundo pase = funcion real en las 4 combinaciones")
    chequear(sum(1 for k in ev["decision"] if k.endswith("d26")) == 4, "variante D26 (pozo del 2o pase con filtros) calculada en las 4")
    chequear(d["objetivo_final"] and ev["decision"]["min|con_compuerta"]["objetivo_final"],
             "el foco sintetico (9 K en I04) pasa con max y con min en el nativo (control positivo de la decision)")
    # control negativo de la decision: zonas nulas casi nunca pasan con max
    chequear(d["nulo_final"] is not None and d["nulo_final"] <= 3,
             "zonas nulas que pasan con max: %s de %d" % (d["nulo_final"], ev["n_zonas_nulas"]))
    # hallazgo 6: la replica sobre el recorte cuenta lo mismo que la corrida real sobre el granulo ENTERO
    ie = ev["identidad_escena"]
    chequear(ie["ok"] is True, "identidad con la corrida entera: primer pase %s = %s, finales %s = %s" % (
        ie["n_hot_1_replica"], ie["n_hot_1_real"], ie["n_final_replica"], ie["n_final_real"]))
    # y puede fallar: con un conteo real distinto, la identidad de escena da False
    ev_mal = cp.evaluar_campo({**cap, "sp_out_n": cap["sp_out_n"] + 1}, lat, lon, [(clat, clon)], np.random.default_rng(1))
    chequear(ev_mal["identidad_escena"]["ok"] is False, "con un conteo real de finales distinto la identidad de escena falla")
    # hallazgo 5: L_i05 en la tabla y el peso de I04 en la varianza de dNTI del pozo
    pp = ev["primer_pase"]
    chequear("L_i05" in ev["pixeles"] and all(v is None or v > 0 for v in ev["pixeles"]["L_i05"]),
             "la tabla por pixel guarda L_i05 (%d pixeles)" % len(ev["pixeles"]["L_i05"]))
    print("        varianza de dNTI del pozo: termino I04 %.3f | termino I05 %.3f | linealizada %.3f" % (
        pp["frac_var_dnti_termino_i04"], pp["frac_var_dnti_termino_i05"], pp["frac_var_dnti_linealizada"]), flush=True)
    chequear(abs(pp["frac_var_dnti_linealizada"] - 1) < 0.05,
             "la linealizacion de dNTI en I04 e I05 explica su varianza (%.3f, a 5 %% de 1)" % pp["frac_var_dnti_linealizada"])


def p2b_tope():
    print("P2b. el tope de la tabla por pixel nunca corta un pixel activo o final de cumbre (hallazgo 7)", flush=True)
    from pipeline import detection_context as dc
    from pipeline.scan_geometry import haversine_km, roi_mask_bbox
    from pipeline.process_viirs import bt_to_spectral_radiance
    # campo ruidoso (1,5 K) y cumbre de 20 km (como Puyehue Cordon Caulle): muchos pixeles de interes, y
    # una parte activos con `min` o sin compuerta pero de dNTI bajo
    clat, clon = -40.59, -72.12
    bands, geo, _ = swath_sintetico(clat, clon, ruido=1.5, semilla=11)
    lat, lon = geo["lat"], geo["lon"]
    roi = roi_mask_bbox(lat, lon, clat, clon, 25.0)
    L4 = bt_to_spectral_radiance(bands["I04"], 3.74); L5 = bt_to_spectral_radiance(bands["I05"], 11.45)
    nti = (L4 - L5) / (L4 + L5)
    _, nti_app = dc.compute_nti_and_nti_app(L4, bands["I05"], 3.74, 11.45)
    dist = haversine_km(clat, clon, lat, lon)
    kw = dict(nti=nti, nti_app=nti_app, bt=bands["I04"], roi_mask=roi, dist_km=dist, roi1_mask=None,
              t_bg=267.0, bt_sanity_k=3.0, c1_dnti_summit=0.003, c1_deti_summit=0.003, c2_dnti_summit=5.0,
              c2_deti_summit=5.0, inner_km=20.0, c1_dnti_scene=0.01, c1_deti_scene=0.01, c2_dnti_scene=10.0,
              c2_deti_scene=10.0, test1_mask=None, unsuitable_dnti_floor=-0.1, unsuitable_deti_floor=-0.1,
              use_prose_branch=True, apply_bt_gate=True)
    hot, diag = dc.first_pass_tests_2_and_3(**kw)
    sp_kw = {"c1_dnti": 0.003, "c1_deti": 0.003, "c2_dnti": 5.0, "c2_deti": 5.0, "is_summit": "ARRAY",
             "c1_dnti_scene": 0.01, "c1_deti_scene": 0.01, "c2_dnti_scene": 10.0, "c2_deti_scene": 10.0,
             "conditioned": False, "use_prose_branch": True}
    cap = {"fp_kw": kw, "fp_diag": {k: v for k, v in diag.items() if not isinstance(v, np.ndarray)}, "sp_kw": sp_kw}

    def activos(ev):
        px = ev["pixeles"]
        return {(px["fila"][i], px["col"][i]) for i in range(len(px["fila"]))
                if px["cumbre"][i] and any(px[k][i] for k in px if k.startswith(("final_", "activo1_")))}
    ev_full = cp.evaluar_campo(cap, lat, lon, [(clat, clon)], np.random.default_rng(1))
    n_act = len(activos(ev_full)); n_int = ev_full["tabla_pixeles"]["n_interes"]
    tope = max(1, n_act // 2)
    # lo que habria guardado la regla VIEJA (los `tope` de mayor dNTI mas el objetivo): cuantos activos pierde
    px = ev_full["pixeles"]
    orden = sorted(range(len(px["fila"])), key=lambda i: -(px["dnti"][i] if px["dnti"][i] is not None else -9))
    viejo = {(px["fila"][i], px["col"][i]) for i in orden[:tope]} | {
        (px["fila"][i], px["col"][i]) for i in range(len(px["fila"])) if px["objetivo"][i]}
    perdia = len(activos(ev_full) - viejo)
    tope_viejo = cp.TOPE_PIXELES
    try:
        cp.TOPE_PIXELES = tope
        ev_t = cp.evaluar_campo(cap, lat, lon, [(clat, clon)], np.random.default_rng(1))
    finally:
        cp.TOPE_PIXELES = tope_viejo
    tp = ev_t["tabla_pixeles"]
    print("        %d pixeles de interes, %d activos o finales de cumbre; tope %d: la regla vieja perdia %d activos" % (
        n_int, n_act, tope, perdia), flush=True)
    chequear(n_int > n_act and perdia > 0, "el caso discrimina: hay pixeles de interes no activos y la regla vieja cortaba activos")
    chequear(activos(ev_t) == activos(ev_full) and tp["siempre_completo"],
             "con el tope %d la tabla conserva los %d activos o finales (guarda %d de %d)" % (
                 tope, n_act, tp["n_guardados"], tp["n_interes"]))
    chequear(tp["n_guardados"] < tp["n_interes"], "y el tope sigue cortando lo que no es activo ni final")


def p3_punta_a_punta(dir_out):
    print("P3. de punta a punta con granulo sintetico: calculate_vrp REAL en los cinco campos", flush=True)
    import pipeline.process_viirs as pv
    sonda.guardas_de_entorno(exigir_token=False)
    ctx = sonda.Contexto()
    vol = ctx.vols["Chaiten"]
    from pipeline.geo_utils import get_grid_center, get_detection_anchor
    clat, clon = vol["lat"], vol["lon"]
    vlat, vlon = get_detection_anchor(vol)
    bands, geo, _ = swath_sintetico(clat, clon)
    # el foco va en el crater (ancla), no en el centro del catalogo
    from pipeline.scan_geometry import haversine_km
    d = haversine_km(vlat, vlon, geo["lat"], geo["lon"])
    k = np.unravel_index(np.argmin(d), d.shape)
    bands["I04"][k] += 9.0
    ctx.cap.real["read_viirs_l1b"] = lambda p: {b: v.copy() for b, v in bands.items()}
    ctx.cap.real["read_viirs_geo"] = lambda p: geo
    l1b = Path("VJ102IMG.A2026139.0506.021.2026139000000.nc"); g = Path("VJ103IMG.A2026139.0506.021.2026139000000.nc")
    pasada = {"clave": "Chaiten|VIIRS375|2026-05-19 05:06", "vol": "Chaiten", "grupo": "perdida", "lote": 0,
              "granule": l1b.name, "B": {"pc_lat": float(geo["lat"][k]), "pc_lon": float(geo["lon"][k]), "anomaly_pixels": []}}
    # "TIF" conocido: el campo interpolado lineal, sin pasar por la sonda (para validar la validacion)
    pl = ctx.plantillas["Chaiten"]
    dep = {}
    cp.hacer_regrid_tif(pl, "linear", dep)(bands, geo)
    tif = dep["L_I04"].copy()
    fila = sonda.procesar_pasada(ctx, pasada, l1b, g, tif)
    ctx.cap.desinstalar()
    chequear(fila["ok"], "las 15 corridas terminaron sin error: %s" % fila["errores"][:3])
    chequear(sorted(fila["campos"]) == sorted(sonda.CORRIDAS), "los cinco campos evaluados: %s" % sorted(fila["campos"]))
    for campo, ev in fila["campos"].items():
        idp = ev.get("identidad_primer_pase") or {}
        ok_id = all(v is not None and v < 1e-9 for v in idp.values())
        ok_dec = all(v["identidad_hot_1"] and v["identidad_final"] is not False for v in ev["decision"].values())
        chequear(ok_id and ok_dec and ev["identidad_n_pool"], "%-7s identidad con la funcion real (mu/sigma, mascara 1er pase, 2o pase)" % campo)
        chequear(ev.get("sp_out_n_real") is not None, "%-7s se capturo la llamada real al segundo pase" % campo)
        ie = ev.get("identidad_escena") or {}
        chequear(ie.get("ok") is True and ev.get("sp_in_n_real") == ie.get("n_hot_1_real"),
                 "%-7s identidad con la corrida real sobre el granulo entero (1er pase %s, finales %s, entrada al 2o pase %s)" % (
                     campo, ie.get("n_hot_1_real"), ie.get("n_final_real"), ev.get("sp_in_n_real")))
        dm = ev["decision"]["max|con_compuerta"]
        print("        %-7s forma %s | n_roi %d | sd_dNTI %.5f sd_dETI %.5f | z_obj %.1f | max obj %s | min obj %s | nulo max %s/%d" % (
            campo, ev["forma"], ev["n_roi"], ev["primer_pase"]["sd_dnti"], ev["primer_pase"]["sd_deti"],
            dm["z_obj_max"] or float("nan"), dm["objetivo_final"], ev["decision"]["min|con_compuerta"]["objetivo_final"],
            dm["nulo_final"], ev["n_zonas_nulas"]), flush=True)
    chequear(fila["campos"]["tif_lin"]["forma"] == [134, 134] and fila["campos"]["utm_nn"]["forma"] == [134, 134],
             "las grillas miden 134 x 134 (la de MIROVA y la UTM existente)")
    for k_c, c in fila["corridas"].items():
        chequear(c.get("record") is not None, "%-24s record persistido por store.append_record real" % k_c)
    v = fila["validacion_tif"]
    print("        validacion:", {k: {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in x.items()
                                      if kk in ("r_L", "r_dL", "s_ratio")} for k, x in v.items()}, flush=True)
    chequear(abs(v["tif_lin"]["r_dL"] - 1) < 1e-9 and abs(v["tif_lin"]["s_ratio"] - 1) < 1e-9,
             "contra un TIF hecho con interpolacion lineal, tif_lin da r_dL = 1 y razon de sigma = 1")
    chequear(v["tif_nn"]["r_dL"] < 0.99, "y tif_nn se distingue (r_dL %.3f < 0,99)" % v["tif_nn"]["r_dL"])
    # el nativo y el lineal miden sigmas distintas: el instrumento puede dar distinto entre campos
    s_nat = fila["campos"]["nativo"]["primer_pase"]["sd_dnti"]; s_lin = fila["campos"]["tif_lin"]["primer_pase"]["sd_dnti"]
    print("        sigma dNTI lineal / nativo = %.3f" % (s_lin / s_nat), flush=True)
    chequear(s_lin != s_nat, "la sigma cambia entre el nativo y la grilla interpolada (el instrumento no es constante)")
    nombre = dir_out / "Chaiten_sintetico.json"
    nombre.write_text(json.dumps(cp.a_json(fila), ensure_ascii=False), encoding="utf-8")
    return nombre


def p4_tif_real():
    print("P4. validacion contra un GeoTIFF REAL de MIROVA ya en disco (no se baja nada)", flush=True)
    import rasterio
    base = RAIZ / "experiments" / "_s144_conteo_tif" / "_dl_tif" / "da4fe36e8920"
    pasadas = json.loads((AQUI / "pasadas.json").read_text(encoding="utf-8"))["pasadas"]
    ruta = None
    for p in pasadas:
        if p["grupo"] == "perdida" and p.get("tif") and p["tif"]["usable"] and (base / p["tif"]["tif_path"]).exists():
            ruta = base / p["tif"]["tif_path"]; clave = p["clave"]
            break
    if ruta is None:
        print("  (sin TIF de perdida en disco; se omiten las 5 comprobaciones de P4)")
        SALTADAS[0] += 5
        return
    with rasterio.open(ruta) as ds:
        t = ds.read(1).astype(np.float64)
        print("  %s -> %s | %s %s" % (clave, ruta.name, ds.crs, ds.shape), flush=True)
    # el lector de la sonda: misma grilla que la plantilla, y con una plantilla corrida la rechaza
    class _C:
        plantillas = json.loads((AQUI / "plantillas_tif.json").read_text(encoding="utf-8"))
    pas = next(p for p in pasadas if p["clave"] == clave)
    t2, meta = sonda.leer_tif(_C, pas, base)
    chequear(t2 is not None and meta["misma_grilla_que_plantilla"], "sonda.leer_tif lee el TIF y su grilla coincide con la plantilla")
    _C.plantillas = json.loads(json.dumps(_C.plantillas)); _C.plantillas[pas["vol"]]["transform"][2] += 0.01
    t3, meta3 = sonda.leer_tif(_C, pas, base)
    chequear(t3 is None and not meta3["misma_grilla_que_plantilla"], "con la plantilla corrida 0,01 grados el TIF no se usa para validar")
    from scipy.ndimage import uniform_filter
    v_id = cp.validar_contra_tif(t, t)
    v_sm = cp.validar_contra_tif(uniform_filter(np.nan_to_num(t, nan=np.nanmean(t)), 3), t)
    v_sh = cp.validar_contra_tif(np.roll(t, 1, axis=1), t)
    chequear(abs(v_id["r_dL"] - 1) < 1e-12 and abs(v_id["s_ratio"] - 1) < 1e-12, "contra si mismo: r_dL = 1, razon de sigma = 1")
    chequear(v_sm["s_ratio"] < 0.8, "suavizado 3x3: la razon de sigma baja a %.2f" % v_sm["s_ratio"])
    chequear(v_sh["r_dL"] < 0.8 and v_sh["r_L"] > 0.9, "corrido una celda: r_L sigue alto (%.3f) pero r_dL cae (%.3f)" % (v_sh["r_L"], v_sh["r_dL"]))


def p5_evaluador(salida):
    print("P5. evaluar.py corre sobre la salida sintetica", flush=True)
    import evaluar
    meta = {"Chaiten|VIIRS375|2026-05-19 05:06": {"grupo": "perdida", "grupos": ["perdida"], "etiqueta_confiable": True,
                                                  "camino_b": "d22", "B": {"diag_n_first_pass_pixels": 0}}}
    res = evaluar.evaluar([salida], pasadas_meta=meta,
                          totales={"residual_apagado": 766, "residual_sobrevive": 63, "negativo_b_no_publica": 1495},
                          predicado_node=True, negativos_d22={"camino_d22": []})
    chequear(isinstance(res, dict) and "veredictos" in res, "el evaluador devuelve veredictos: %s" % res.get("veredictos"))
    chequear(res["instrumento"]["identidad"]["fallan"] == 0, "identidad: 0 pares pasada-campo fallan")
    fila = json.loads(Path(salida).read_text(encoding="utf-8"))
    pub = evaluar.predicado([fila])
    print("        predicado del tablero (node) por corrida, la perdida sintetica:",
          {k[1]: v for k, v in sorted(pub.items())}, flush=True)
    chequear(len(pub) == 15 and all(v == 1 for v in pub.values()), "el predicado corrio sobre las 15 corridas y las 15 publican")
    chequear(isinstance(res["h3"], str), "con un gate caido no se escribe la tabla H3 (V2-3)")
    print("        validacion:", {k: (v["r_dL_mediana"], v["valido"]) for k, v in res["instrumento"]["validacion_tif"].items()},
          "| campo MIROVA elegido:", res["instrumento"]["campo_mirova"], flush=True)
    chequear(res["instrumento"]["campo_mirova"] == "tif_lin", "con un TIF lineal conocido, el evaluador elige tif_lin")
    # sin la sigma del A/B en la meta, el gate de sigma no puede pasar: el veredicto no sale
    chequear(res["veredictos"]["H1_sigma_del_campo"].startswith("INDETERMINADO POR INSTRUMENTO")
             and "sigma dNTI" in res["veredictos"]["H1_sigma_del_campo"],
             "sin la sigma del record del A/B para comparar, H1 es INDETERMINADO POR INSTRUMENTO")


# ---------------------------------------------------------------- poblaciones sinteticas para el evaluador
# El evaluador solo se puede creer si se le ve dar CADA veredicto cuando corresponde y NINGUNO cuando no
# (A110 d: un control que pasa en verde sobre un instrumento roto es un control roto; verificador S150,
# hallazgo 1). Las poblaciones usan la META REAL de pasadas.json (365 pasadas, los mismos grupos, etiquetas,
# caminos, lotes y TIF que el despacho) y como salida por pasada un clon de la salida sintetica de P3, cuyos
# 15 records PUBLICAN todos con el predicado REAL del tablero (node, comprobado en P5). "No publica" se
# arma quitando el record de esa corrida (el evaluador cuenta un record ausente sin error como no publica).
# Asi el predicado, la cobertura, los gates y las reglas corren de verdad; lo unico que se inventa es que
# corrida publica en que pasada.
CORRIDAS_15 = ["%s|%s" % (c, k) for c in ("nativo", "utm_nn", "tif_nn", "tif_lin", "tif_cub")
               for k in ("max", "min", "max_sin_compuerta")]
TOTALES = {"residual_apagado": 766, "residual_sobrevive": 63, "negativo_b_no_publica": 1495}


def poblacion(base, diseno, claves=None, sd_ab=None, cambiar_meta=None):
    """Clones de `base` para las pasadas de la meta real. diseno(meta, i, corrida) -> 0/1, con i el indice de
    la pasada dentro de su grupo primario. Devuelve (filas, meta, negativos_d22)."""
    import evaluar
    sel = json.loads((AQUI / "pasadas.json").read_text(encoding="utf-8"))
    negd22 = json.loads((AQUI / "negativos_camino_d22.json").read_text(encoding="utf-8"))
    sd = sd_ab if sd_ab is not None else base["campos"]["nativo"]["primer_pase"]["sd_dnti"]
    meta, filas, cont = {}, [], {}
    for p in sel["pasadas"]:
        m = json.loads(json.dumps(p))
        m["F"] = dict(m.get("F") or {}); m["F"]["diag_sd_dnti"] = sd    # la sigma del "A/B" = la del clon
        if cambiar_meta:
            cambiar_meta(m)
        meta[m["clave"]] = m
        # indice dentro del grupo primario; las perdidas confiables llevan su propio contador para que la
        # fraccion de R_L que pide el diseno sea la que se mide sobre ellas
        kg = (m["grupo"], bool(m.get("etiqueta_confiable")))
        i = cont.get(kg, 0); cont[kg] = i + 1
        if claves is not None and m["clave"] not in claves:
            continue
        corr = {}
        for c in CORRIDAS_15:
            rec = base["corridas"][c]["record"] if diseno(m, i, c) else None
            corr[c] = {"record": rec, "record_crudo_none": rec is None, "persistido_none": rec is None}
        tif_ok = bool((m.get("tif") or {}).get("usable"))
        filas.append({**base, "clave": m["clave"], "grupo": m["grupo"], "lote": m["lote"], "corridas": corr,
                      "validacion_tif": base["validacion_tif"] if tif_ok else {}, "segundos": 100.0, "rss_max_mb": 900.0})
    assert evaluar.F_PUBLICA.keys() >= {m["grupo"] for m in meta.values()}
    return filas, meta, negd22


def _ab(m, cn):
    """Lo que publico el A/B en el grupo de la pasada: F con `max`, B con `min`."""
    import evaluar
    return (evaluar.F_PUBLICA if cn == "max" else evaluar.B_PUBLICA)[m["grupo"]]


def diseno_confirma(m, i, corrida, r_l=0.75, frac_residual=0.10):
    """El nativo reproduce el A/B; el campo M (tif_lin, el que valida el TIF lineal de P3) con `max` publica una
    fraccion r_l de las perdidas, todas las conservadas y frac_residual del residual apagado. En el nativo, sin la
    compuerta se recuperan las perdidas del camino D22 y se reabre el 10 % de la muestra de negativos D22."""
    campo, cn = corrida.split("|")
    g = m["grupo"]
    if campo == "tif_lin" and cn == "max":
        if g == "perdida":
            return int((i % 10) < round(10 * r_l))
        if g == "residual_apagado":
            return int((i % 10) < round(10 * frac_residual))
        return _ab(m, "max")
    if cn == "max_sin_compuerta":
        if g == "perdida":
            return int(m.get("camino_b") == "d22")
        if g == "muestra_negativos_d22":
            return int(i % 10 == 0)
        return _ab(m, "max")
    return _ab(m, cn)


def _corre(filas, meta, negd22, piloto=False):
    import evaluar
    return evaluar.evaluar(filas, meta, TOTALES, predicado_node=not piloto, negativos_d22=negd22, piloto=piloto)


def p6_evaluador_grupos(salida, d):
    print("P6. clones que publican en TODO (la meta real, 365 pasadas): el nativo no reproduce el A/B", flush=True)
    base = json.loads(Path(salida).read_text(encoding="utf-8"))
    filas, meta, negd22 = poblacion(base, lambda m, i, c: 1)
    res = _corre(filas, meta, negd22)
    v = res["veredictos"]["H1_sigma_del_campo"]
    print("        H1:", v[:200], flush=True)
    print("        reproduccion por grupo:", {k: (x["n"], x["fallas"], x.get("maximo")) for k, x in res["instrumento"]["reproduccion_por_grupo"].items()},
          "| acuerdo agregado (informativo):", {k: round(x["acuerdo"], 3) for k, x in res["instrumento"]["acuerdo_agregado_ab_informativo"].items()}, flush=True)
    chequear(not res["instrumento"]["cobertura_fallas"], "cobertura completa (365 de 365): la falla tiene que venir del instrumento")
    chequear(v.startswith("INDETERMINADO POR INSTRUMENTO") and "reproduccion" in v and "CONFIRMA" not in v,
             "H1 da INDETERMINADO POR INSTRUMENTO por reproduccion (antes daba CONFIRMA con salvedad)")
    chequear("numeros" not in res["h1"] and isinstance(res["h3"], str) and not isinstance(res["h1"].get("mecanismo"), dict),
             "y no escribe numeros de H1, ni tabla H3, ni mecanismo")
    chequear(all(x.startswith("INDETERMINADO POR") and "reproduccion" in x for x in res["veredictos"]["D22_D26_nativo"].values()),
             "D22 y D26 en el nativo tambien quedan INDETERMINADO (por reproduccion; y por cobertura, sin perdidas D22 reproducidas)")
    chequear(res["d22_d26"]["muestra_en_lista_congelada"] is True, "la muestra D22 se comprueba contra la lista congelada")


def p7_veredictos_sinteticos(salida):
    print("P7. poblaciones sinteticas: cada veredicto sale cuando corresponde y solo entonces", flush=True)
    base = json.loads(Path(salida).read_text(encoding="utf-8"))

    def h1(res):
        return res["veredictos"]["H1_sigma_del_campo"]

    # CONFIRMA: el nativo reproduce, M recupera 3 de cada 4 perdidas y reabre 1 de cada 10 residuales
    filas, meta, negd22 = poblacion(base, diseno_confirma)
    res = _corre(filas, meta, negd22)
    n = res["h1"].get("numeros", {})
    print("        CONFIRMA esperado:", h1(res), flush=True)
    print("          D22 nativo:", res["veredictos"]["D22_D26_nativo"].get("D22_predicado"), flush=True)
    chequear(h1(res).startswith("CONFIRMA") and n.get("n_perdidas_reproducidas") == 32,
             "M recupera y no reabre: CONFIRMA, con R_L sobre las 32 perdidas reproducidas")
    chequear(res["veredictos"]["D22_D26_nativo"]["D22_predicado"].startswith("SELECTIVO"),
             "D22 sin compuerta recupera las 14 y reabre 1 de cada 10 negativos del camino: SELECTIVO")

    # REFUTA por falsos: M recupera igual pero reabre 7 de cada 10 residuales (como bajar C2)
    filas, meta, negd22 = poblacion(base, lambda m, i, c: diseno_confirma(m, i, c, frac_residual=0.70))
    res = _corre(filas, meta, negd22)
    print("        REFUTA esperado (falsos):", h1(res), flush=True)
    chequear(h1(res).startswith("REFUTA"), "M recupera pero devuelve mas de la mitad de los falsos que `max` apago: REFUTA")

    # REFUTA por recall: M casi no recupera
    filas, meta, negd22 = poblacion(base, lambda m, i, c: diseno_confirma(m, i, c, r_l=0.10, frac_residual=0.0))
    res = _corre(filas, meta, negd22)
    print("        REFUTA esperado (recall):", h1(res), flush=True)
    chequear(h1(res).startswith("REFUTA"), "M recupera 1 de cada 10 perdidas: REFUTA")

    # INDETERMINADO en la zona gris: recupera 0,40 sin reabrir
    filas, meta, negd22 = poblacion(base, lambda m, i, c: diseno_confirma(m, i, c, r_l=0.40, frac_residual=0.0))
    res = _corre(filas, meta, negd22)
    rl = res["h1"].get("numeros", {}).get("recall_perdidas_reproducidas")
    print("        INDETERMINADO esperado (zona gris):", h1(res), flush=True)
    chequear(rl is not None and 0.25 <= rl < 0.50 and h1(res).startswith("INDETERMINADO (R_L"),
             "R_L entre 0,25 y 0,50 (%s): INDETERMINADO, sin veredicto" % (None if rl is None else round(rl, 3)))

    # cobertura: el piloto (solo el lote 1) con el diseno que CONFIRMA, y el borde de 2 y 3 perdidas faltantes
    lote1 = {k for k, m in meta.items() if m["lote"] == 1}
    filas, meta, negd22 = poblacion(base, diseno_confirma, claves=lote1)
    res = _corre(filas, meta, negd22)
    print("        COBERTURA esperado (solo el lote 1, %d pasadas):" % len(filas), h1(res)[:160], flush=True)
    chequear(h1(res).startswith("INDETERMINADO POR COBERTURA"),
             "con solo el lote del piloto el evaluador no imprime CONFIRMA: INDETERMINADO POR COBERTURA")
    chequear(all(x.startswith("INDETERMINADO POR COBERTURA") for x in res["veredictos"]["D22_D26_nativo"].values()),
             "y D22 tampoco tiene veredicto")
    pc = sorted(k for k, m in meta.items() if m["grupo"] == "perdida" and m.get("etiqueta_confiable"))
    for faltan, espera in ((2, "CONFIRMA"), (3, "INDETERMINADO POR COBERTURA")):
        filas, meta, negd22 = poblacion(base, diseno_confirma, claves=set(meta) - set(pc[:faltan]))
        res = _corre(filas, meta, negd22)
        chequear(h1(res).startswith(espera), "faltan %d de 32 perdidas confiables (maximo 2): %s" % (faltan, h1(res)[:60]))

    # gate de reproduccion por grupo, en su borde: 2 perdidas que el nativo|max publica pasan, 3 no
    for n_mal, espera in ((2, "CONFIRMA"), (3, "INDETERMINADO POR INSTRUMENTO")):
        malas = set(pc[:n_mal])
        filas, meta, negd22 = poblacion(base, lambda m, i, c, malas=malas: 1 if (m["clave"] in malas and c == "nativo|max")
                                        else diseno_confirma(m, i, c))
        res = _corre(filas, meta, negd22)
        chequear(h1(res).startswith(espera), "%d perdidas que el nativo|max publica (maximo 2): %s" % (n_mal, h1(res)[:60]))

    # guarda de brecha: si el nativo|min no publica el residual, `max` no compro nada que medir. Desde que la
    # reproduccion por grupo cubre los negativos (V2-2), ese caso lo frena ANTES la reproduccion: con ese gate en
    # pie la brecha no puede bajar de ~0,27 (DISENO §5 bis), y la guarda queda como segundo candado.
    filas, meta, negd22 = poblacion(base, lambda m, i, c: 0 if (c == "nativo|min" and m["grupo"] in
                                                             ("residual_apagado", "muestra_negativos_d22"))
                                    else diseno_confirma(m, i, c))
    res = _corre(filas, meta, negd22)
    print("        BRECHA esperado:", h1(res)[:160], flush=True)
    chequear(h1(res).startswith("INDETERMINADO POR INSTRUMENTO") and "residual_apagado" in h1(res),
             "nativo|min sin publicar el residual (brecha 0): INDETERMINADO POR INSTRUMENTO, lo frena la reproduccion por grupo")

    # gate de sigma contra el A/B: 10 % de las pasadas con otra sigma (otro granulo u otro calculo)
    def otra_sigma(m):
        if zlib.crc32(m["clave"].encode("utf-8")) % 10 == 0:     # determinista (hash() cambia entre procesos)
            m["F"]["diag_sd_dnti"] = m["F"]["diag_sd_dnti"] * 1.01
    filas, meta, negd22 = poblacion(base, diseno_confirma, cambiar_meta=otra_sigma)
    n_otra = sum(1 for m in meta.values() if m["F"]["diag_sd_dnti"] != base["campos"]["nativo"]["primer_pase"]["sd_dnti"])
    res = _corre(filas, meta, negd22)
    print("        SIGMA esperado (%d pasadas con otra sigma):" % n_otra, h1(res)[:160], flush=True)
    chequear(n_otra > 0.05 * len(meta) and h1(res).startswith("INDETERMINADO POR INSTRUMENTO") and "sigma dNTI" in h1(res),
             "sigma del nativo distinta del A/B en mas del 5 %% (%d de %d): INDETERMINADO POR INSTRUMENTO" % (n_otra, len(meta)))

    # control positivo de D22 que FRENA: nativo|min no publica 1 perdida D22 (el gate general tolera 2)
    d22 = sorted(k for k in pc if meta[k].get("camino_b") == "d22")[:1]
    filas, meta, negd22 = poblacion(base, lambda m, i, c: 0 if (m["clave"] in d22 and c == "nativo|min")
                                    else diseno_confirma(m, i, c))
    res = _corre(filas, meta, negd22)
    vd = res["veredictos"]["D22_D26_nativo"]["D22_predicado"]
    print("        CONTROL POSITIVO D22 esperado:", vd[:160], "| H1:", h1(res)[:40], flush=True)
    chequear(vd.startswith("INDETERMINADO POR INSTRUMENTO") and "control positivo" in vd and h1(res).startswith("CONFIRMA"),
             "nativo|min no publica 1 de las 14: D22 queda INDETERMINADO POR INSTRUMENTO (H1 sigue, tolera 2)")

    # identidad: si la replica no reproduce la corrida real sobre el granulo entero, nada se lee
    malo = json.loads(json.dumps({k: base[k] for k in ("campos",)}))
    for ev in malo["campos"].values():
        ev["identidad_escena"]["ok"] = False
    filas, meta, negd22 = poblacion({**base, **malo}, diseno_confirma)
    res = _corre(filas, meta, negd22)
    chequear("identidad" in h1(res) and h1(res).startswith("INDETERMINADO POR"),
             "con la identidad de escena rota: INDETERMINADO (%s)" % h1(res)[:70])

    # piloto: sin predicado, sin veredictos de deteccion; solo cobertura, operativo y validacion
    filas, meta, negd22 = poblacion(base, diseno_confirma, claves=lote1)
    res = _corre(filas, meta, negd22, piloto=True)
    chequear(list(res["veredictos"]) == ["PILOTO"] and isinstance(res["h1"], str) and "tabla" not in res["h3"]
             and "operativo" in res["instrumento"] and "validacion_tif" in res["instrumento"],
             "el modo piloto no calcula H1, D22 ni la tabla: solo cobertura, tiempo, memoria y validacion")
    print("        piloto:", json.dumps({"cobertura": res["instrumento"]["cobertura_lotes_presentes"]["por_grupo"].get("perdida"),
                                         "operativo": res["instrumento"]["operativo"],
                                         "campo_mirova": res["instrumento"]["validacion_tif"]["campo_mirova"]}, ensure_ascii=False), flush=True)


def p7b_segundo_verificador(salida):
    """Un caso por hallazgo del segundo verificador (docs/audit_s150/VERIFICADOR2_SONDA_TRES_CAMPOS.md). Cada
    caso falla con el evaluador de 5eda5b942 y pasa con el nuevo; una excepcion cuenta como FALLA (el codigo
    viejo no tiene algunas claves), asi que el caso no puede pasar por no haber corrido."""
    print("P7b. los caminos que encontro el segundo verificador (V2-1 a V2-10)", flush=True)
    import evaluar
    base = json.loads(Path(salida).read_text(encoding="utf-8"))
    dc_ = diseno_confirma

    def h1(res):
        return res["veredictos"]["H1_sigma_del_campo"]

    def caso(msg, fn):
        try:
            cond, detalle = fn()
        except Exception as e:  # el evaluador viejo no tiene algunas claves: eso tambien es FALLA
            cond, detalle = False, "excepcion %s: %s" % (type(e).__name__, e)
        chequear(cond, "%s [%s]" % (msg, str(detalle)[:110]))

    def v21():
        r = _corre(*poblacion(base, lambda m, i, c: 0 if c.startswith("tif_") else dc_(m, i, c)))
        return h1(r).startswith("INDETERMINADO POR INSTRUMENTO") and "M no publica" in h1(r), h1(r)
    caso("V2-1: un M que no publica nada (ni las conservadas) da INDETERMINADO POR INSTRUMENTO, no REFUTA", v21)

    def v22b():
        def f(m, i, c):
            if c == "nativo|min" and m["grupo"] == "negativo_b_no_publica":
                return 1
            return dc_(m, i, c, frac_residual=0.40)
        r = _corre(*poblacion(base, f))
        return h1(r).startswith("INDETERMINADO POR INSTRUMENTO") and "negativo_b_no_publica" in h1(r), h1(r)
    caso("V2-2: nativo|min publica los negativos que B no publico: no sale CONFIRMA", v22b)

    def v22c():
        def f(m, i, c):
            if c == "nativo|max" and m["grupo"] == "residual_apagado":
                return int(i % 10 < 3)
            return dc_(m, i, c, frac_residual=0.40)
        r = _corre(*poblacion(base, f))
        return h1(r).startswith("INDETERMINADO POR INSTRUMENTO") and "residual_apagado" in h1(r), h1(r)
    caso("V2-2: nativo|max publica el 30 % del residual apagado (F: 0 %): no sale CONFIRMA", v22c)

    def v22ab():
        r = _corre(*poblacion(base, dc_))
        g = r["h1"]["gates_h1"]
        return abs(g["brecha_ab"] - 766 / 2324) < 1e-12 and abs(r["h1"]["numeros"]["brecha_menos_brecha_ab"]) < 1e-9, \
            "brecha %.3f, A/B %.3f" % (g["brecha"], g["brecha_ab"])
    caso("V2-2: la brecha de la corrida se informa contra la del A/B (766 / 2.324 = 0,330)", v22ab)

    lote1 = {p["clave"] for p in json.loads((AQUI / "pasadas.json").read_text(encoding="utf-8"))["pasadas"] if p["lote"] == 1}

    def v23a():
        r = _corre(*poblacion(base, dc_, claves=lote1))
        sin = isinstance(r["h3"], str) and not isinstance(r["h1"].get("mecanismo"), dict) and "numeros" not in r["h1"] \
            and not isinstance(r["d22_d26"].get("nativo"), dict) and not isinstance(r["instrumento"].get("nulo"), dict)
        return sin, h1(r)
    caso("V2-3: lote 1 sin --piloto: ni tabla H3, ni mecanismo, ni tasas de D22, ni nulo", v23a)

    def v23b():
        r = _corre(*poblacion(base, lambda m, i, c: 1))
        return isinstance(r["h3"], str) and not isinstance(r["h1"].get("mecanismo"), dict), h1(r)
    caso("V2-3: clones que publican en todo (gate de reproduccion caido): ni tabla H3 ni mecanismo", v23b)

    def v23yml():
        import shutil
        import subprocess
        import yaml
        bash = shutil.which("bash")
        if not bash:
            SALTADAS[0] += 1
            return True, "sin bash: saltada"
        wf = yaml.safe_load((RAIZ / ".github" / "workflows" / "probe-s150-tres-campos.yml").read_text(encoding="utf-8"))
        paso = next(s for s in wf["jobs"]["preparar"]["steps"] if s.get("name") == "Candado del pre-registro")
        res = {}
        for piloto, lotes in (("no", "1"), ("no", ""), ("si", ""), ("si", "1")):
            env = dict(os.environ, APROBADO="si", PILOTO=piloto, LOTES=lotes)
            res[(piloto, lotes)] = subprocess.run([bash, "-c", paso["run"]], env=env, capture_output=True).returncode
        esperado = {("no", "1"): 1, ("no", ""): 0, ("si", ""): 1, ("si", "1"): 0}
        return res == esperado, {"%s/%s" % k: v for k, v in res.items()}
    caso("V2-3: el candado del yml rechaza lotes parciales fuera del piloto (y un piloto sin lotes)", v23yml)

    def v24():
        filas, meta, negd22 = poblacion(base, dc_, claves=lote1)
        r = _corre(filas, meta, negd22, piloto=True)
        ins = r["instrumento"]
        bien = "sd_dnti_nativo_vs_record_ab" in ins and "mismo_granulo_que_ab" in ins and ins.get("sd_dnti_falla") is None

        def otra(m):
            m["F"]["diag_sd_dnti"] *= 1.01
        filas, meta, negd22 = poblacion(base, dc_, claves=lote1, cambiar_meta=otra)
        r2 = _corre(filas, meta, negd22, piloto=True)
        return bien and bool(r2["instrumento"].get("sd_dnti_falla")) and list(r2["veredictos"]) == ["PILOTO"], \
            r2["instrumento"].get("sd_dnti_falla")
    caso("V2-4: el piloto informa la sigma contra el A/B y el mismo granulo, y avisa si no coinciden", v24)

    def v25():
        filas, meta, negd22 = poblacion(base, lambda m, i, c: dc_(m, i, c, r_l=0.40, frac_residual=0.0))
        rep = [f for f in filas if meta[f["clave"]]["grupo"] == "perdida" and meta[f["clave"]].get("etiqueta_confiable")
               and f["corridas"]["tif_lin|max"]["record"] is not None]
        r = evaluar.evaluar(filas + rep + rep, meta, TOTALES, predicado_node=True, negativos_d22=negd22)
        return h1(r).startswith("INDETERMINADO POR INSTRUMENTO") and "duplicadas" in h1(r), h1(r)
    caso("V2-5: pasadas duplicadas no fabrican CONFIRMA: INDETERMINADO POR INSTRUMENTO", v25)

    def v26():
        _, meta0, _ = poblacion(base, dc_, claves=set())
        pc = sorted(k for k, m in meta0.items() if m["grupo"] == "perdida" and m.get("etiqueta_confiable"))
        d22 = sorted(k for k in pc if meta0[k].get("camino_b") == "d22")
        malas = set(d22[:2])
        filas, meta, negd22 = poblacion(base, lambda m, i, c: 1 if (m["clave"] in malas and c == "nativo|max") else dc_(m, i, c),
                                        claves=set(meta0) - {d22[2]})
        r = evaluar.evaluar(filas, meta, TOTALES, predicado_node=True, negativos_d22=negd22)
        v = r["veredictos"]["D22_D26_nativo"]["D22_predicado"]
        return v.startswith("INDETERMINADO POR COBERTURA") and "reproducidas" in v, v
    caso("V2-6: D22 con 11 perdidas reproducidas (promete 13 de 14): INDETERMINADO POR COBERTURA", v26)

    def v27():
        import re
        src = (AQUI / "sonda.py").read_text(encoding="utf-8")
        prints = []   # cada llamada a print completa, contando parentesis (anidados a cualquier profundidad)
        for mt in re.finditer(r"\bprint\(", src):
            prof, j = 0, mt.end() - 1
            while j < len(src):
                prof += {"(": 1, ")": -1}.get(src[j], 0)
                if prof == 0:
                    break
                j += 1
            prints.append(src[mt.start():j + 1])
        malos = [p for p in prints if re.search(r"objetivo_final|obj_final|distance_class", p)]
        return bool(prints) and not malos, "%d prints, %d con datos de deteccion" % (len(prints), len(malos))
    caso("V2-7: el log de la sonda no imprime ningun dato de deteccion", v27)

    def v210():
        def nan(m):
            m["F"]["diag_sd_dnti"] = float("nan")
        r = _corre(*poblacion(base, dc_, cambiar_meta=nan))
        return h1(r).startswith("INDETERMINADO POR INSTRUMENTO") and "sigma dNTI" in h1(r), h1(r)
    caso("V2-10: una sigma del A/B en NaN cuenta como distinta, no como identica", v210)


def p7c_tercer_verificador(salida):
    """Un caso por hallazgo del tercer verificador (docs/audit_s150/VERIFICADOR3_SONDA_TRES_CAMPOS.md): N1, N2,
    N3 y N5. Cada uno falla con el codigo de aae4a4ed0 y pasa con el nuevo; una excepcion cuenta como FALLA."""
    print("P7c. los caminos que encontro el tercer verificador (N1, N2, N3, N5)", flush=True)
    base = json.loads(Path(salida).read_text(encoding="utf-8"))
    dc_ = diseno_confirma

    def h1(res):
        return res["veredictos"]["H1_sigma_del_campo"]

    def caso(msg, fn):
        try:
            cond, detalle = fn()
        except Exception as e:
            cond, detalle = False, "excepcion %s: %s" % (type(e).__name__, e)
        chequear(cond, "%s [%s]" % (msg, str(detalle)[:110]))

    _, meta0, _ = poblacion(base, dc_, claves=set())
    pc = sorted(k for k, m in meta0.items() if m["grupo"] == "perdida" and m.get("etiqueta_confiable"))
    d22 = sorted(k for k in pc if meta0[k].get("camino_b") == "d22")

    def n2():
        # nativo con desvios DENTRO del 5 % (2 de 42 y 4 de 84), todos inflando FP(nativo, max); M reabre el 30 %
        def f(m, i, c):
            g = m["grupo"]
            if c == "nativo|max" and ((g == "negativo_b_no_publica" and i < 2) or (g == "residual_apagado" and i >= 80)):
                return 1
            return dc_(m, i, c, frac_residual=0.30)
        r0 = _corre(*poblacion(base, lambda m, i, c: dc_(m, i, c, frac_residual=0.30)))
        r1 = _corre(*poblacion(base, f))
        return (h1(r0).startswith("INDETERMINADO (R_L") and h1(r1).startswith("INDETERMINADO (R_L")), \
            "sano: %s | con desvios: %s" % (h1(r0)[:40], h1(r1)[:60])
    caso("N2: desvios tolerados por el 5 % no convierten un INDETERMINADO en CONFIRMA (contraste pareado)", n2)

    def n3():
        r = _corre(*poblacion(base, lambda m, i, c: 0 if c.startswith("tif_") else dc_(m, i, c)))
        vm = r["veredictos"].get("D22_D26_tif_lin") or {}
        return bool(vm) and all(v.startswith("INDETERMINADO POR INSTRUMENTO") and "M no publica" in v for v in vm.values()), \
            list(vm.values())[:1]
    caso("N3: D22 leida en un M muerto no da NO RECUPERA: INDETERMINADO POR INSTRUMENTO", n3)

    def n1():
        r = _corre(*poblacion(base, lambda m, i, c: 0 if (m["clave"] in d22[:1] and c == "nativo|min") else dc_(m, i, c)))
        t = r["h3"]["tabla"] if isinstance(r["h3"], dict) else None
        return (h1(r).startswith("CONFIRMA") and t is not None and "nativo|max" in t
                and not any(k.endswith("|max_sin_compuerta") for k in t)), \
            "H1 %s | filas sin compuerta: %s" % (h1(r)[:20], [k for k in (t or {}) if k.endswith("max_sin_compuerta")])
    caso("N1: con D22 frenada y H1 en pie, la tabla H3 no muestra las filas sin compuerta", n1)

    def n5():
        import shutil
        import subprocess
        import yaml
        bash = shutil.which("bash")
        if not bash:
            SALTADAS[0] += 1
            return True, "sin bash: saltada"
        wf = yaml.safe_load((RAIZ / ".github" / "workflows" / "probe-s150-tres-campos.yml").read_text(encoding="utf-8"))
        paso = next(s for s in wf["jobs"]["preparar"]["steps"] if s.get("id") == "plan")
        res = {}
        with tempfile.TemporaryDirectory() as td:
            for piloto, lotes in (("si", " "), ("si", ","), ("si", "1,2"), ("si", "1"), ("no", "")):
                env = dict(os.environ, PILOTO=piloto, LOTES=lotes, GITHUB_OUTPUT=str(Path(td) / "out.txt"))
                res[(piloto, lotes)] = int(subprocess.run([bash, "-c", paso["run"]], env=env, cwd=str(RAIZ),
                                                          capture_output=True).returncode != 0)
        esperado = {("si", " "): 1, ("si", ","): 1, ("si", "1,2"): 1, ("si", "1"): 0, ("no", ""): 0}
        return res == esperado, {"%s/%r" % k: v for k, v in res.items()}
    caso("N5: el plan de lotes rechaza un piloto sin un lote valido (' ', ',', '1,2') y acepta '1'", n5)


def p8_sello():
    print("P8. el sello cubre la sonda, pipeline/, el predicado, el arnes, el catalogo y el yml, y puede fallar", flush=True)
    import sellar
    txt = sellar.texto_sello("prueba local", "docs/audit_s150/VERIFICADOR_SONDA_TRES_CAMPOS.md", "0" * 40)
    nombres = [l.split(None, 1)[1] for l in txt.splitlines() if l and not l.startswith("#")]
    for p in ("raiz:pipeline/process_viirs.py", "raiz:pipeline/detection_context.py", "raiz:frontend/index.html",
              "raiz:scripts/banco_paridad.py", "raiz:scripts/run_pipeline.py", "raiz:volcanoes.yaml",
              "raiz:.github/workflows/probe-s150-tres-campos.yml", "evaluar.py", "DISENO.md", "sellar.py"):
        chequear(p in nombres, "el sello incluye %s" % p)
    chequear(sum(n.startswith("raiz:pipeline/profiles/") for n in nombres) > 0,
             "y los perfiles (%d archivos de pipeline/ en total)" % sum(n.startswith("raiz:pipeline/") for n in nombres))
    chequear(sellar.diferencias(txt) == [], "un sello recien hecho coincide con el arbol")
    lineas = txt.splitlines()
    i = next(k for k, l in enumerate(lineas) if l.endswith("raiz:pipeline/process_viirs.py"))
    alterado = list(lineas); alterado[i] = "0" * 64 + "  raiz:pipeline/process_viirs.py"
    chequear(any("process_viirs.py: NO COINCIDE" in x for x in sellar.diferencias("\n".join(alterado))),
             "un cambio en pipeline/process_viirs.py rompe el sello")
    sin = [l for l in lineas if not l.endswith("raiz:frontend/index.html")]
    chequear(any("index.html: NUEVO" in x for x in sellar.diferencias("\n".join(sin))),
             "un archivo que no estaba en el sello lo rompe")
    sin_cab = [l for l in lineas if not l.startswith("# aprobo")]
    chequear(any("aprobo" in x for x in sellar.diferencias("\n".join(sin_cab))), "un sello sin quien aprobo no vale")
    # V2-8: un re-sello que cambia una cota queda a la vista
    chequear(sellar.comparar_sellos(txt, "\n".join(alterado)) == ["raiz:pipeline/process_viirs.py"]
             and sellar.comparar_sellos(txt, txt) == [],
             "comparar_sellos nombra lo que cambio entre dos sellos (V2-8) y nada si son iguales")


def main():
    with tempfile.TemporaryDirectory() as d:
        p0_guardas()
        p1_interpolacion()
        p2_recorte()
        p2b_tope()
        salida = p3_punta_a_punta(Path(d))
        p4_tif_real()
        p5_evaluador(salida)
        p6_evaluador_grupos(salida, d)
        p7_veredictos_sinteticos(salida)
        p7b_segundo_verificador(salida)
        p7c_tercer_verificador(salida)
        p8_sello()
    print("\nRESULTADO: %d comprobaciones, %d saltadas, %s" % (
        N_CHEQUEOS[0], SALTADAS[0], "TODO OK" if not FALLAS else "%d FALLAS: %s" % (len(FALLAS), FALLAS)), flush=True)
    sys.exit(1 if FALLAS else 0)


if __name__ == "__main__":
    main()
