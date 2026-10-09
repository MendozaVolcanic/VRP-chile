# -*- coding: utf-8 -*-
"""S150, sonda de los tres campos: funciones puras (sin red, sin NASA). Las usa sonda.py y las prueba
prueba_local.py.

EL FENOMENO. El Test 2 pregunta si el NTI de un pixel sobresale de la media de sus 8 vecinos (dNTI), y
la lectura `max` exige ademas que ese exceso supere mu + 5 sigma, donde sigma es la variabilidad del
dNTI en toda la escena. Esa sigma depende del SUSTRATO sobre el que se mide: en el granulo nativo cada
pixel es una medicion independiente del sensor (con su ruido, su borde de barrido estirado y su bow tie);
en una grilla remuestreada e interpolada, cada celda es un promedio ponderado de varias mediciones
vecinas, y el ruido de pixel a pixel se suaviza. Si MIROVA calcula sigma sobre su grilla interpolada
(Campus et al. 2024, Bull. Volcanol. 86:25, p. 3: "after an initial resampling of the original granule
in a regular 50x50 km UTM grid"), su sigma puede ser menor que la nuestra y su umbral mu + 5 sigma mas
bajo. Pero el suavizado tambien baja el pico del foco. La sonda mide cual de los dos efectos gana.

QUE HAY ACA.
  - grilla_plantilla: centros de celda de la grilla de MIROVA (plantillas_tif.json).
  - interpolador_a_grilla: lleva el swath a esa grilla (vecino, lineal o cubico) en RADIANCIA, que es lo
    que publica el GeoTIFF de MIROVA (valores ~0,05 W m-2 sr-1 um-1, I04).
  - hacer_regrid_tif: reemplazo de `process_viirs._regrid_viirs_granule` con la misma firma y el mismo
    esquema de salida, para que calculate_vrp corra sin cambios sobre la grilla de MIROVA.
  - evaluar_campo: con las entradas reales que el pipeline le paso a `first_pass_tests_2_and_3`
    (capturadas por monkeypatch, A75), recalcula con las MISMAS funciones del pipeline dNTI, dETI, mu,
    sigma, mu2, sigma2 y la decision de los Tests 2 y 3 con `min` y con `max`, con y sin la compuerta de
    3 K (D22), y lo compara con lo que el pipeline calculo (control de identidad).
  - validar_contra_tif: cuanto se parece la radiancia I04 del campo a la del GeoTIFF de MIROVA.

Nada de esto modifica pipeline/: importa sus funciones y las llama.
"""
import math

import numpy as np

from pipeline import detection_context as dc
from pipeline.regrid import _utm_like_xy
from pipeline.scan_geometry import haversine_km

LAMBDA_I04 = 3.740    # pipeline/process_viirs.py:80 (I04_LAMBDA)
LAMBDA_I05 = 11.450   # pipeline/process_viirs.py:860
R_OBJ_KM = 0.75       # radio de la zona objetivo alrededor de lo que B publico (pre-registrado)
R_OBJ_SENS_KM = (0.5, 1.0)   # sensibilidad informada, no decide
N_NULO = 50           # zonas nulas por pasada y campo
SEP_NULO_KM = 3.0     # una zona nula queda a mas de esto de cualquier punto objetivo
MARGEN_CROP = 3       # pixeles de margen fuera del ROI al recortar el granulo nativo


# ---------------------------------------------------------------- radiancia <-> temperatura de brillo
def bt_a_rad(bt, lam):
    """Planck, mismas constantes que process_viirs.bt_to_spectral_radiance."""
    from pipeline.constants import C1, C2
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        return C1 / (lam ** 5 * (np.exp(C2 / (lam * np.asarray(bt, dtype=np.float64))) - 1))


def rad_a_bt(L, lam):
    """Inversa exacta de bt_a_rad (mismas constantes que process_viirs._radiance_to_bt_viirs)."""
    from pipeline.constants import C1, C2
    L = np.asarray(L, dtype=np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        bt = C2 / (lam * np.log(C1 / (L * lam ** 5) + 1))
    bt[~(L > 0)] = np.nan
    return bt


# ---------------------------------------------------------------- grilla de MIROVA
def grilla_plantilla(pl):
    """Centros de celda (lat, lon) de la grilla EPSG:4326 de un volcan (plantillas_tif.json)."""
    if pl["crs"] != "EPSG:4326":
        raise ValueError("plantilla no geografica: %s" % pl["crs"])
    a, b, c, d, e, f = pl["transform"]
    if b != 0 or d != 0:
        raise ValueError("transform con rotacion")
    alto, ancho = pl["alto"], pl["ancho"]
    jj = np.arange(ancho) + 0.5
    ii = np.arange(alto) + 0.5
    lon = c + a * jj
    lat = f + e * ii
    return lat[:, None] * np.ones((1, ancho)), np.ones((alto, 1)) * lon[None, :]


def interpolador_a_grilla(lat_sw, lon_sw, lat_g, lon_g, metodo, validas, max_dist_nn_km=1.5):
    """Prepara la interpolacion del swath a la grilla. Devuelve una funcion f(valores_swath) -> grilla.

    Trabaja en coordenadas locales en km (misma aproximacion que pipeline/regrid.py) centradas en la
    grilla. Recorta el swath a la caja de la grilla mas 3 km para que la triangulacion sea chica.
    `validas`: bool del swath, muestras que pueden representar a su celda (las mismas para todas las
    bandas, como hace regrid_to_utm con `required`).
    metodo: "nearest" (con distancia maxima: fuera de eso NaN), "linear" (Delaunay, NaN fuera de la
    envolvente) o "cubic" (Clough-Tocher, idem).
    """
    from scipy.interpolate import CloughTocher2DInterpolator, LinearNDInterpolator
    from scipy.spatial import Delaunay, cKDTree
    clat = float(np.nanmean(lat_g)); clon = float(np.nanmean(lon_g))
    xg, yg = _utm_like_xy(lat_g, lon_g, clat, clon)
    xs, ys = _utm_like_xy(lat_sw, lon_sw, clat, clon)
    margen = 3.0
    caja = ((xs >= np.nanmin(xg) - margen) & (xs <= np.nanmax(xg) + margen)
            & (ys >= np.nanmin(yg) - margen) & (ys <= np.nanmax(yg) + margen))
    sel = np.flatnonzero((caja & validas & np.isfinite(xs) & np.isfinite(ys)).ravel())
    pts = np.column_stack([xs.ravel()[sel], ys.ravel()[sel]])
    q = np.column_stack([xg.ravel(), yg.ravel()])
    forma = lat_g.shape
    info = {"n_muestras": int(sel.size), "metodo": metodo}
    if sel.size < 10:
        def f(_v):
            return np.full(forma, np.nan)
        return f, info
    if metodo == "nearest":
        arbol = cKDTree(pts)
        dist, idx = arbol.query(q)
        lejos = dist > max_dist_nn_km

        def f(v):
            out = np.asarray(v, dtype=np.float64).ravel()[sel][idx]
            out = out.copy(); out[lejos] = np.nan
            return out.reshape(forma)
        info["frac_celdas_sin_muestra"] = float(np.mean(lejos))
        return f, info
    tri = Delaunay(pts)

    def f(v):
        vals = np.asarray(v, dtype=np.float64).ravel()[sel]
        if metodo == "linear":
            it = LinearNDInterpolator(tri, vals)
        elif metodo == "cubic":
            it = CloughTocher2DInterpolator(tri, vals)
        else:
            raise ValueError(metodo)
        return it(q).reshape(forma)
    return f, info


def hacer_regrid_tif(plantilla, metodo, deposito):
    """Reemplazo de process_viirs._regrid_viirs_granule(bands, geo, center_lat, center_lon).

    Misma firma y mismo esquema de salida que la funcion real (process_viirs.py:489-545): bandas en
    temperatura de brillo (I04, I05) y geo con lat, lon (centros de celda), sensor_zenith y angles.
    Interpola RADIANCIA (lo que publica el GeoTIFF) y vuelve a temperatura de brillo con la inversa
    exacta de Planck, porque calculate_vrp espera temperatura de brillo y la vuelve a pasar a radiancia
    con las mismas constantes (ida y vuelta sin perdida). El centro que recibe se ignora: la grilla es
    la de MIROVA. `deposito` (dict) recibe la radiancia I04 interpolada para validar contra el TIF.
    """
    lat_g, lon_g = grilla_plantilla(plantilla)

    def regrid(bands, geo, center_lat=None, center_lon=None, **_kw):
        bt4, bt5 = bands["I04"], bands["I05"]
        validas = np.isfinite(bt4) & np.isfinite(bt5)
        f, info = interpolador_a_grilla(geo["lat"], geo["lon"], lat_g, lon_g, metodo, validas)
        L4 = f(bt_a_rad(bt4, LAMBDA_I04))
        L5 = f(bt_a_rad(bt5, LAMBDA_I05))
        out_b = {"I04": rad_a_bt(L4, LAMBDA_I04).astype(np.float32),
                 "I05": rad_a_bt(L5, LAMBDA_I05).astype(np.float32)}
        for k in bands:
            if k not in out_b:
                out_b[k] = f(bands[k]).astype(np.float32)
        # angulos: solo diagnosticos (con area nadir fija no entran a la magnitud); vecino es suficiente.
        fz, _ = interpolador_a_grilla(geo["lat"], geo["lon"], lat_g, lon_g, "nearest", validas)
        sz = fz(geo["sensor_zenith"])
        angles = {k: (fz(v) if v is not None else None) for k, v in (geo.get("angles") or {}).items()}
        deposito.update({"L_I04": L4, "L_I05": L5, "lat": lat_g, "lon": lon_g, "info": info,
                         "frac_celdas_con_dato": float(np.mean(np.isfinite(L4) & np.isfinite(L5)))})
        return out_b, {"lat": lat_g, "lon": lon_g, "sensor_zenith": sz, "angles": angles}
    return regrid


# ---------------------------------------------------------------- recorte del granulo nativo
def caja_recorte(roi_mask, margen=MARGEN_CROP):
    """Filas/columnas del ROI mas un margen. Recortar con margen >= 2 deja intactos dNTI, dETI y el pozo
    de fondo dentro del ROI (el kernel mira 1 pixel afuera; el pozo y la regresion del ETI solo usan el
    ROI; el borde del recorte queda fuera del ROI). Se comprueba en cada pasada contra el diag real."""
    filas = np.flatnonzero(roi_mask.any(axis=1)); cols = np.flatnonzero(roi_mask.any(axis=0))
    if filas.size == 0:
        return None
    r0 = max(0, filas[0] - margen); r1 = min(roi_mask.shape[0], filas[-1] + margen + 1)
    c0 = max(0, cols[0] - margen); c1 = min(roi_mask.shape[1], cols[-1] + margen + 1)
    return slice(r0, r1), slice(c0, c1)


def _rec(x, caja):
    if x is None or caja is None or np.ndim(x) != 2:
        return x
    return x[caja]


# ---------------------------------------------------------------- evaluacion de los Tests 2 y 3
def _stats(dnti, deti, pool):
    if int(pool.sum()) == 0:
        return None
    return {"mu_dnti": float(np.mean(dnti[pool])), "sd_dnti": float(np.std(dnti[pool])),
            "mu_deti": float(np.mean(deti[pool])), "sd_deti": float(np.std(deti[pool])),
            "n_pool": int(pool.sum())}


def _umbrales(st, kw, combinar):
    """Umbrales de cumbre y escena con la conectiva dada (detection_context.py:529-535)."""
    c1s_n = kw.get("c1_dnti_summit", 0.003); c1s_e = kw.get("c1_deti_summit", 0.003)
    c2s_n = kw.get("c2_dnti_summit", 5); c2s_e = kw.get("c2_deti_summit", 5)
    c1e_n = kw.get("c1_dnti_scene"); c1e_e = kw.get("c1_deti_scene")
    c2e_n = kw.get("c2_dnti_scene"); c2e_e = kw.get("c2_deti_scene")
    u = {"sum_dnti": combinar(c1s_n, st["mu_dnti"] + c2s_n * st["sd_dnti"]),
         "sum_deti": combinar(c1s_e, st["mu_deti"] + c2s_e * st["sd_deti"])}
    if c1e_n is not None:
        u["sce_dnti"] = combinar(c1e_n, st["mu_dnti"] + c2e_n * st["sd_dnti"])
        u["sce_deti"] = combinar(c1e_e, st["mu_deti"] + c2e_e * st["sd_deti"])
    else:
        u["sce_dnti"], u["sce_deti"] = u["sum_dnti"], u["sum_deti"]
    return u


def _segundo_pase_replica(nti, eti, activo, is_summit, kw_sp, combinar, pozo_d26=None):
    """Replica de second_pass_adjacent (detection_context.py:903-967) que ademas devuelve mu2, sigma2,
    dNTI2 y dETI2. Con pozo_d26=None se compara pixel a pixel con la salida de la funcion real (control
    de identidad).

    pozo_d26 = {"roi", "test1", "dnti_floor", "deti_floor"}: variante que NO existe en el pipeline y que
    solo se calcula aca, offline. Arma el pozo de mu2 y sigma2 con los mismos filtros de no aptos del
    primer pase (borde, dNTI o dETI bajo -0,1; Coppola 2016a, detection_context.py:492-499), que el
    segundo pase real no aplica (detection_context.py:922-929, D26). Separa D22 de D26 sin tocar codigo
    (verificador D22, H1 d)."""
    nti_m = np.where(activo, np.nan, nti); eti_m = np.where(activo, np.nan, eti)
    dnti2 = nti - dc._nanmean_8neighbors_fast(nti_m)
    deti2 = eti - dc._nanmean_8neighbors_fast(eti_m)
    pool2 = (~activo) & np.isfinite(dnti2) & np.isfinite(deti2)
    if pozo_d26 is not None:
        pool2 = pool2 & dc.build_unsuitable_mask(pozo_d26["roi"], dnti2, deti2, test1_mask=pozo_d26["test1"],
                                                 dnti_floor=pozo_d26["dnti_floor"], deti_floor=pozo_d26["deti_floor"])
    if int(pool2.sum()) < kw_sp.get("min_bg_pixels", 10):
        return activo.copy(), dnti2, deti2, None, None
    if kw_sp.get("conditioned") and not bool(activo.any()):
        return activo.copy(), dnti2, deti2, None, None
    st2 = _stats(dnti2, deti2, pool2)
    c1n, c1e_ = kw_sp["c1_dnti"], kw_sp["c1_deti"]; c2n, c2e_ = kw_sp["c2_dnti"], kw_sp["c2_deti"]
    dual = (kw_sp.get("is_summit") is not None and kw_sp.get("c1_dnti_scene") is not None)
    u2 = {"sum_dnti": combinar(c1n, st2["mu_dnti"] + c2n * st2["sd_dnti"]),
          "sum_deti": combinar(c1e_, st2["mu_deti"] + c2e_ * st2["sd_deti"])}
    if dual:
        u2["sce_dnti"] = combinar(kw_sp["c1_dnti_scene"], st2["mu_dnti"] + kw_sp["c2_dnti_scene"] * st2["sd_dnti"])
        u2["sce_deti"] = combinar(kw_sp["c1_deti_scene"], st2["mu_deti"] + kw_sp["c2_deti_scene"] * st2["sd_deti"])
        p2 = np.where(is_summit, dnti2 > u2["sum_dnti"], dnti2 > u2["sce_dnti"])
        p3 = np.where(is_summit, deti2 > u2["sum_deti"], deti2 > u2["sce_deti"])
    else:
        u2["sce_dnti"], u2["sce_deti"] = u2["sum_dnti"], u2["sum_deti"]
        p2 = dnti2 > u2["sum_dnti"]; p3 = deti2 > u2["sum_deti"]
    nuevo = p2 & p3 & np.isfinite(dnti2) & np.isfinite(deti2)
    if kw_sp.get("conditioned"):
        nuevo = nuevo & dc._vecindad_8(activo)
    st2.update({"umbrales": u2})
    return activo | nuevo, dnti2, deti2, st2, u2


def zona(lat, lon, puntos, r_km):
    """bool: celdas a <= r_km de alguno de los puntos (lat, lon)."""
    m = np.zeros(lat.shape, dtype=bool)
    for (pla, plo) in puntos:
        m |= haversine_km(pla, plo, lat, lon) <= r_km
    return m


def zonas_nulas(lat, lon, roi, puntos, rng, n=N_NULO, r_km=R_OBJ_KM, sep_km=SEP_NULO_KM):
    """Centros sorteados dentro del ROI a mas de sep_km de los puntos objetivo (semilla fija)."""
    lejos = roi.copy()
    for (pla, plo) in puntos:
        lejos &= haversine_km(pla, plo, lat, lon) > sep_km
    idx = np.flatnonzero(lejos.ravel())
    if idx.size == 0:
        return []
    elegidos = rng.choice(idx, size=min(n, idx.size), replace=False)
    return [(float(lat.ravel()[i]), float(lon.ravel()[i])) for i in elegidos]


def evaluar_campo(cap, lat, lon, puntos_obj, rng, guardar_pixeles=True):
    """Recalcula los Tests 2 y 3 sobre las entradas reales capturadas en una corrida de calculate_vrp.

    cap: {"fp_kw": kwargs con que el pipeline llamo a first_pass_tests_2_and_3 (arrays incluidos),
          "fp_diag": diag escalar que devolvio, "sp_kw": kwargs de la llamada real a second_pass_adjacent
          (sin arrays), "fp_hot": la mascara real del primer pase, "sp_out": la mascara real final}.
    lat, lon: geolocalizacion de esa misma corrida (swath nativo o grilla).
    puntos_obj: [(lat, lon)] de lo que B publico (zona objetivo).

    Devuelve un dict serializable con: control de identidad, mu y sigma de los dos pases para las dos
    conectivas, decision en la zona objetivo y en las zonas nulas para (min|max) x (con|sin compuerta),
    margen z del pixel mas favorable de la zona objetivo, y la tabla de pixeles de interes.
    """
    fp_api = dc.first_pass_tests_2_and_3          # siempre la funcion REAL (no el envoltorio)
    sp_api = dc.second_pass_adjacent
    kw = dict(cap["fp_kw"])
    caja = caja_recorte(kw["roi_mask"])
    if caja is None:
        return {"ok": False, "error": "roi vacio"}
    A = {k: _rec(v, caja) for k, v in kw.items()}
    la, lo = _rec(lat, caja), _rec(lon, caja)
    nti, nti_app, bt, roi = A["nti"], A["nti_app"], A["bt"], A["roi_mask"]
    t_bg, bt_k = A["t_bg"], A["bt_sanity_k"]
    test1 = A.get("test1_mask")
    is_summit = dc.roi1_summit_mask(A["dist_km"], A["inner_km"], A.get("roi1_mask"))

    # --- primer pase, mismas funciones que first_pass_tests_2_and_3 ---
    mval = roi & np.isfinite(nti) & np.isfinite(nti_app)
    eti = dc.compute_eti_scene_quadratic(nti, nti_app, mval)
    dnti = nti - dc._nanmean_8neighbors_fast(nti)
    deti = eti - dc._nanmean_8neighbors_fast(eti)
    pool = dc.build_unsuitable_mask(roi, dnti, deti, test1_mask=test1,
                                    dnti_floor=A.get("unsuitable_dnti_floor", dc.UNSUITABLE_DNTI_FLOOR_DEFAULT),
                                    deti_floor=A.get("unsuitable_deti_floor", dc.UNSUITABLE_DETI_FLOOR_DEFAULT))
    st = _stats(dnti, deti, pool)
    res = {"ok": True, "forma": list(nti.shape), "n_roi": int(roi.sum()), "t_bg": float(t_bg),
           "n_summit_roi": int((roi & is_summit).sum())}
    if st is None:
        return {**res, "ok": False, "error": "pozo de fondo vacio"}
    res["primer_pase"] = st
    d = cap.get("fp_diag") or {}
    res["identidad_primer_pase"] = {
        k: (None if d.get(k) is None else float(abs(st[k] - d[k]) / max(abs(d[k]), 1e-12)))
        for k in ("mu_dnti", "sd_dnti", "mu_deti", "sd_deti")}
    res["identidad_n_pool"] = (int(d.get("n_bg_used", -1)) == st["n_pool"])

    obj = zona(la, lo, puntos_obj, R_OBJ_KM) & roi
    objs = {r: zona(la, lo, puntos_obj, r) & roi for r in R_OBJ_SENS_KM}
    nulos = [zona(la, lo, [p], R_OBJ_KM) & roi for p in zonas_nulas(la, lo, roi, puntos_obj, rng)]
    res["n_celdas_objetivo"] = int(obj.sum())
    res["n_zonas_nulas"] = len(nulos)
    gate_bt = bt > t_bg + bt_k
    finite = np.isfinite(dnti) & np.isfinite(deti)

    decis = {}
    arrays = {}
    interes = (obj | (roi & is_summit & finite & ((dnti > 0.003) | (deti > 0.003))))
    sp_kw = dict(cap.get("sp_kw") or {})
    pozo_d26 = {"roi": roi, "test1": test1,
                "dnti_floor": A.get("unsuitable_dnti_floor", dc.UNSUITABLE_DNTI_FLOOR_DEFAULT),
                "deti_floor": A.get("unsuitable_deti_floor", dc.UNSUITABLE_DETI_FLOOR_DEFAULT)}
    zN = (dnti - st["mu_dnti"]) / st["sd_dnti"]; zE = (deti - st["mu_deti"]) / st["sd_deti"]
    zmin = np.where(obj & finite, np.minimum(zN, zE), -np.inf)
    for nombre_c, combinar in (("min", min), ("max", max)):
        u = _umbrales(st, A, combinar)
        p2 = np.where(is_summit, dnti > u["sum_dnti"], dnti > u["sce_dnti"])
        p3 = np.where(is_summit, deti > u["sum_deti"], deti > u["sce_deti"])
        # umbral de cumbre aplicado a TODA la escena: solo para las zonas nulas (tasa base de un
        # parche cualquiera de la escena si estuviera en la cumbre).
        p23_sum = (dnti > u["sum_dnti"]) & (deti > u["sum_deti"]) & finite & roi
        # razon al umbral del primer pase: min(dNTI / thr_dNTI, dETI / thr_dETI) con el umbral del ROI del pixel
        thrN = np.where(is_summit, u["sum_dnti"], u["sce_dnti"]); thrE = np.where(is_summit, u["sum_deti"], u["sce_deti"])
        razon = np.where(obj & finite, np.minimum(dnti / thrN, deti / thrE), -np.inf)
        for nombre_g, con_compuerta in (("con_compuerta", True), ("sin_compuerta", False)):
            g = gate_bt if con_compuerta else np.isfinite(bt)
            hot1 = roi & finite & p2 & p3 & g
            # control: la funcion REAL con la misma conectiva y compuerta da la misma mascara
            kw_real = dict(A); kw_real["use_prose_branch"] = (nombre_c == "max"); kw_real["apply_bt_gate"] = con_compuerta
            hot_real, _ = fp_api(**kw_real)
            ident1 = bool(np.array_equal(hot1, hot_real))
            kwsp = dict(sp_kw); kwsp["use_prose_branch"] = (nombre_c == "max")
            if kwsp.get("is_summit") is not None:
                kwsp["is_summit"] = is_summit
            for nombre_p, pz in (("", None), ("|d26", pozo_d26)):
                final, dnti2, deti2, st2, u2 = _segundo_pase_replica(nti, eti, hot1, is_summit, kwsp, combinar, pz)
                ident2 = None
                if sp_kw and pz is None:
                    real2 = sp_api(nti=nti, eti=eti, active_mask=hot1, **kwsp)
                    ident2 = bool(np.array_equal(final, real2))
                n1_nulo = sum(1 for z in nulos if bool((z & p23_sum & g).any()))
                n2_nulo = None
                if u2 is not None:
                    p23_sum2 = (dnti2 > u2["sum_dnti"]) & (deti2 > u2["sum_deti"]) & np.isfinite(dnti2) & np.isfinite(deti2)
                    n2_nulo = sum(1 for z in nulos if bool((z & ((p23_sum & g) | p23_sum2)).any()))
                decis["%s|%s%s" % (nombre_c, nombre_g, nombre_p)] = {
                    "umbrales_1": u, "identidad_hot_1": ident1, "identidad_final": ident2,
                    "n_hot_1_escena": int(hot1.sum()), "n_final_escena": int(final.sum()),
                    "objetivo_1": bool((hot1 & obj).any()), "objetivo_final": bool((final & obj).any()),
                    "objetivo_solo_2": bool((final & obj).any() and not (hot1 & obj).any()),
                    "objetivo_final_sens": {str(r): bool((final & m).any()) for r, m in objs.items()},
                    "cumbre_1": bool((hot1 & roi & is_summit).any()),
                    "cumbre_final": bool((final & roi & is_summit).any()),
                    "nulo_1": n1_nulo, "nulo_final": n2_nulo,
                    "z_obj_max": (float(zmin.max()) if np.isfinite(zmin.max()) else None),
                    "razon_obj_max": (float(razon.max()) if np.isfinite(razon.max()) else None),
                    "segundo_pase": ({k: v for k, v in st2.items() if k != "umbrales"} if st2 else None),
                    "umbrales_2": u2,
                }
                if guardar_pixeles:
                    interes |= final & roi & is_summit
                    clave_a = "%s_%s" % (nombre_c, "cc" if con_compuerta else "sc")
                    a = arrays.setdefault(clave_a, {"dnti2": dnti2, "deti2": deti2, "hot1": hot1})
                    a["final" + ("_d26" if pz is not None else "")] = final
    res["decision"] = decis

    if guardar_pixeles:
        idx = np.flatnonzero(interes.ravel())
        if idx.size > 4000:          # techo de tamano: se guardan los 4000 de mayor dNTI + todo el objetivo
            orden = np.argsort(-np.nan_to_num(dnti.ravel()[idx], nan=-9))
            keep = set(idx[orden[:4000]].tolist()) | set(np.flatnonzero(obj.ravel()).tolist())
            idx = np.array(sorted(keep))
        r, c = np.unravel_index(idx, nti.shape)

        def col(x, nd=6):
            return [None if not np.isfinite(v) else round(float(v), nd) for v in np.asarray(x, dtype=np.float64).ravel()[idx]]

        def flag(x):
            return np.asarray(x).ravel()[idx].astype(int).tolist()
        L4 = bt_a_rad(bt, LAMBDA_I04)
        # Con esto se rehace OFFLINE cualquier decision (min o max, con o sin compuerta, pozo del segundo
        # pase con o sin filtros D26) sin volver a bajar el granulo: bt - t_bg, dNTI y dETI de los dos
        # pases, y mu, sigma, mu2, sigma2 en res["primer_pase"] y en decision[...]["segundo_pase"].
        px = {"fila": r.tolist(), "col": c.tolist(), "lat": col(la, 5), "lon": col(lo, 5),
              "dist_ancla_km": col(A["dist_km"], 3), "cumbre": flag(is_summit), "objetivo": flag(obj),
              "bt_i04": col(bt, 3), "bt_menos_tbg": col(bt - t_bg, 3), "L_i04": col(L4, 6),
              "nti": col(nti, 6), "dnti": col(dnti, 6), "deti": col(deti, 6), "pasa_compuerta": flag(gate_bt)}
        for k, a in arrays.items():
            px["dnti2_" + k] = col(a["dnti2"], 6); px["deti2_" + k] = col(a["deti2"], 6)
            px["activo1_" + k] = flag(a["hot1"]); px["final_" + k] = flag(a["final"])
            px["final_d26_" + k] = flag(a["final_d26"])
        res["pixeles"] = px
    return res


def a_json(x):
    """Convierte numpy y tuplas a tipos JSON (NaN e infinitos a None)."""
    if isinstance(x, dict):
        return {str(k): a_json(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [a_json(v) for v in x]
    if isinstance(x, np.ndarray):
        return a_json(x.tolist())
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        v = float(x)
        return v if math.isfinite(v) else None
    return x


# ---------------------------------------------------------------- validacion contra el GeoTIFF
def _media8(a):
    return dc._nanmean_8neighbors_fast(np.asarray(a, dtype=np.float64))


def validar_contra_tif(L_campo, L_tif):
    """Cuanto se parece la radiancia I04 del campo a la del GeoTIFF de MIROVA, celda a celda.

    Mira dos cosas, porque responden preguntas distintas:
      - el campo en si (r_L, diferencia relativa mediana): ¿es la misma escena, bien georreferenciada?
      - la textura de pixel a pixel, dL = L - media de los 8 vecinos (r_dL y la razon de desviaciones
        s_ratio = sd(dL campo) / sd(dL TIF)): es la cantidad que fija la sigma del Test 2. Un campo
        puede tener r_L = 0,99 por el gradiente de altitud y aun asi tener el doble de ruido de pixel.
    Se excluye el borde de 1 celda (el kernel de 8 vecinos queda cojo ahi).
    """
    a = np.asarray(L_campo, dtype=np.float64); b = np.asarray(L_tif, dtype=np.float64)
    if a.shape != b.shape:
        return {"ok": False, "error": "formas distintas %s %s" % (a.shape, b.shape)}
    borde = dc._edge_unsuitable_mask(a.shape)
    da = a - _media8(a); db = b - _media8(b)
    m = ~borde & np.isfinite(a) & np.isfinite(b) & (b > 0) & (a > 0) & np.isfinite(da) & np.isfinite(db)
    n = int(m.sum())
    if n < 100:
        return {"ok": False, "error": "pocas celdas comunes", "n": n}

    def r(x, y):
        x = x - x.mean(); y = y - y.mean()
        den = math.sqrt(float((x * x).sum() * (y * y).sum()))
        return float((x * y).sum() / den) if den > 0 else None
    rel = (a[m] - b[m]) / b[m]

    def ac1(d):
        # autocorrelacion a una celda (horizontal) de dL: la firma del suavizado (textura_utm_vs_geo.py)
        mm = m[:, :-1] & m[:, 1:]
        x = d[:, :-1][mm]; y = d[:, 1:][mm]
        x = x - x.mean(); y = y - y.mean()
        den = math.sqrt(float((x * x).sum() * (y * y).sum()))
        return float((x * y).sum() / den) if den > 0 else None
    return {"ok": True, "ac1_dL_campo": ac1(da), "ac1_dL_tif": ac1(db), "n": n, "frac_celdas": round(n / a.size, 4),
            "r_L": r(a[m], b[m]), "r_dL": r(da[m], db[m]),
            "s_ratio": float(np.std(da[m]) / np.std(db[m])) if np.std(db[m]) > 0 else None,
            "rel_mediana": float(np.median(rel)), "rel_abs_p90": float(np.percentile(np.abs(rel), 90)),
            "sd_dL_tif": float(np.std(db[m])), "sd_dL_campo": float(np.std(da[m]))}
