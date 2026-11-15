# FICHA (SDA, CPLT 372): análisis de solo lectura sobre L1B bajados a un temporal; no es detección de producción, no escribe
# en data/, no cambia flags. Corre la vía «código MIROVA» con variantes de remuestreo y mide dónde se pierde energía.
"""Análisis de las dos sospechas S185 con L1B crudos.

(1) Tupungatito VIIRS 750: `analizar_tup`. Las 6 pasadas que MIROVA alerta y la vía calla, más 4 detectadas de control.
    POR QUÉ: la celda del cráter queda a 7 a 15 % bajo su umbral NTI (informe s185_tupungatito_6); el remuestreo y la
    geolocalización del L1B estándar son los candidatos que solo se ven con el gránulo.
(2) Nevados de Chillán VIIRS 375: `analizar_chi`. 3 pasadas bajas del este (razón 0,65 a 0,68 contra MIROVA) y controles.
    POR QUÉ: la energía de I4 se pierde en un lado del barrido (informe s185_v375f_cola); hay que ver el píxel nativo para
    separar remuestreo, banderas de calidad y paralaje de terreno.

Reglas del veredicto, escritas ANTES de ver datos:
  Tupungatito. La variante `lineal` tiene que reproducir el record publicado (misma celda decisiva y margen a 1e-3) o el resto
    no vale (A112, A116). Una variante «recupera» una callada si su margen pasa de 1. Este experimento no incluye rutinas
    (5 de 621 por sobre el umbral en la historia), así que no puede declarar mejora: solo sensibilidad, SOSPECHA.
  Chillán. Decide la razón de la VENTANA (B2, energía en exceso de I4 a menos de 3 km del cráter, nativa sobre grilla; la
    comparación por celda alertada B es descriptiva y sale >1 por construcción). «Se pierde en el remuestreo» si esa razón pasa de
    1,15 en las bajas y es cerca de 1 en los controles;
    «viene baja del nativo» si es cerca de 1 en las bajas y el VRP que da la ventana nativa (razón por el coeficiente de la vía) queda bajo MIROVA. El terreno es SOLO
    DESCRIPTIVO: el GEO de VIIRS (VJ103IMG/VNP03IMG, «Terrain-Corrected Geolocation») ya viene corregido y MIROVA usa el mismo
    (docs/DISENO_D17_REMUESTREO_UTM.md l. 116-119 y 541-544), así que la celda no debe cambiar por paralaje; lo que se mide es cuánto
    movería un error de la altura de la fuente contra la del DEM. Con 3 bajas, todo SOSPECHA.
"""
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import mirova_v750_codigo as MV  # noqa: E402
import interpoladores as IP  # noqa: E402

VENT_TUP = (-33.389044, -69.826374)   # vent_lat, vent_lon de volcanoes.yaml
INNER_TUP = 7
VENT_CHI = (-36.863, -71.377)
INNER_CHI = 5
AREA_CELDA_V375_M2 = 375.0 ** 2
SENSOR_750 = {"VJ1": "VIIRS_NOAA20_750", "VJ2": "VIIRS_NOAA21_750", "VNP": "VIIRS_SNPP_750"}
SENSOR_375 = {"VJ1": "VIIRS_NOAA20", "VJ2": "VIIRS_NOAA21", "VNP": "VIIRS_SNPP"}


def variantes(g0):
    """{nombre: (grilla, interpolador o None)}: la de producción, dos interpoladores y 4 corrimientos de media celda."""
    paso = g0["paso"]
    v = {"lineal": (g0, None), "vecino": (g0, IP.vecino), "promedio": (g0, IP.promedio)}
    for k, (fx, fy) in IP.DESPLAZAMIENTOS.items():
        v[k] = (IP.grilla_desplazada(g0, fx * paso, fy * paso), None)
    return v


def correr_via(familia, nombre_volcan, vent, inner, sensor, rad, lat, lon, ang, g, interp):
    """calcular_vrp_granulo con el remuestreo de `interp` (None = producción). Restaura siempre el original."""
    original = MV.remuestrear_grilla
    if interp is not None:
        MV.remuestrear_grilla = interp
    try:
        return MV.calcular_vrp_granulo(rad, lat, lon, ang, nombre_volcan, vent[0], vent[1], inner, sensor, grilla=g, familia=familia)
    finally:
        MV.remuestrear_grilla = original


def _celda_decisiva(rec):
    return ((rec or {}).get("diag_codigo_mirova", {}).get("s1") or {}).get("celda_decisiva")


def _recorte(lat, lon, vent, radio_km, **campos):
    """Subventana (en índices del gránulo) a menos de radio_km del cráter; devuelve los arreglos recortados como dict."""
    d = MV._haversine(lat, lon, vent[0], vent[1])
    ok = np.isfinite(d) & (d < radio_km)
    if not ok.any():
        return {}
    ii, jj = np.nonzero(ok)
    i0, i1, j0, j1 = ii.min(), ii.max() + 1, jj.min(), jj.max() + 1
    out = {"lat": lat[i0:i1, j0:j1], "lon": lon[i0:i1, j0:j1], "origen_ij": np.array([i0, j0])}
    for k, v in campos.items():
        if v is not None:
            out[k] = np.asarray(v)[i0:i1, j0:j1]
    return out


# ----------------------------------------------------------------------------------------------------- Tupungatito V750
def nativos_cerca(rad, lat, lon, ang, g, vent, radio_km=3.0, n=5):
    """Los n píxeles nativos de mayor NTI a menos de radio_km del cráter, con su celda de la grilla."""
    d = MV._haversine(lat, lon, vent[0], vent[1])
    ok = np.isfinite(d) & (d < radio_km) & np.isfinite(rad["M13"])
    idx = np.argwhere(ok)
    if len(idx) == 0:
        return []
    cf, cc = IP.celdas_de(g, lat[idx[:, 0], idx[:, 1]], lon[idx[:, 0], idx[:, 1]])
    filas = []
    for (i, j), f, c in zip(idx, cf, cc):
        m13, m15 = float(rad["M13"][i, j]), float(rad["M15"][i, j])
        filas.append({"i": int(i), "j": int(j), "lat": round(float(lat[i, j]), 5), "lon": round(float(lon[i, j]), 5),
                      "dist_km": round(float(d[i, j]), 2), "celda": [int(f), int(c)], "M13": m13, "M15": m15,
                      "nti": (m13 - m15) / (m13 + m15) if np.isfinite(m15) and (m13 + m15) != 0 else None,
                      "cenit": round(float(ang["sensor_zenith"][i, j]), 1)})
    filas.sort(key=lambda r: -(r["nti"] if r["nti"] is not None else -9))
    return filas[:n]


def analizar_tup(nombre_l1b, rad, lat, lon, ang, ref):
    """ref = entrada `ref` del manifiesto (distancia y VRP de MIROVA, celda decisiva y n_pix publicados)."""
    g0 = MV.grilla_del_volcan("Tupungatito")
    sensor = SENSOR_750[nombre_l1b[:3]]
    item = {"gran": nombre_l1b, "variantes": {}}
    for nombre, (g, interp) in variantes(g0).items():
        rec = correr_via("VIIRS750", "Tupungatito", VENT_TUP, INNER_TUP, sensor, rad, lat, lon, ang, g, interp)
        if rec is None:
            item["variantes"][nombre] = {"estado": "sin_record"}
            continue
        # OJO: en las variantes desp_* los índices de `alertadas` y de la celda decisiva son de la grilla corrida (ver `grilla_ul`);
        # no se comparan con las celdas candidatas de MIROVA ni con la celda publicada sin sumar el corrimiento.
        item["variantes"][nombre] = {"grilla_ul": [g["ul_x"], g["ul_y"]], "n_pix": rec["n_anomalous_pixels"], "vrp_mw": rec["vrp_mw"],
                                     "celda_decisiva": _celda_decisiva(rec),
                                     "alertadas": [[p["fila"], p["col"]] for p in rec["anomaly_pixels"]]}
    dm = ref["mirova_dist_km"]
    item["mirova"] = {"dist_km": dm, "vrp_mw": ref["mirova_vrp_mw"],
                      "celdas_candidatas": [[f, c] for f in range(24, 32) for c in range(26, 35)
                                            if abs(math.hypot(f - 33, c - 33) * 0.75 - dm) < 0.006]}
    cdp, cdl = ref.get("publicado_celda_decisiva"), item["variantes"].get("lineal", {}).get("celda_decisiva")
    item["publicado"] = {"celda_decisiva": cdp, "n_pix": ref.get("publicado_n_pix")}
    item["reproduce_publicado"] = bool(cdp and cdl and (cdp["fila"], cdp["col"]) == (cdl["fila"], cdl["col"])
                                       and abs(cdp["margen"] - cdl["margen"]) < 1e-3)
    item["nativos_cerca_del_crater"] = nativos_cerca(rad, lat, lon, ang, g0, VENT_TUP)
    return item


def recorte_tup(rad, lat, lon, ang):
    return _recorte(lat, lon, VENT_TUP, 12.0, M13=rad["M13"], M15=rad["M15"],
                    cenit=ang.get("sensor_zenith"), azimut=ang.get("sensor_azimuth"))


# ----------------------------------------------------------------------------------------------------- Chillán V375
def leer_banderas(ruta, bandas=("I04", "I05")):
    """Banderas de calidad de cada banda decodificadas con los atributos del archivo: {banda: (arreglo, [(mascara, nombre)])}."""
    import h5py
    out = {}
    with h5py.File(ruta, "r") as f:
        obs = f["observation_data"]
        for b in bandas:
            k = f"{b}_quality_flags"
            if k not in obs:
                out[b] = None
                continue
            ds = obs[k]
            masks = np.asarray(ds.attrs.get("flag_masks", [])).ravel()
            sig = ds.attrs.get("flag_meanings", b"")
            sig = sig.decode() if isinstance(sig, bytes) else str(sig)
            out[b] = (ds[:], list(zip([int(m) for m in masks], sig.split())))
    return out


def leer_altura(ruta_geo):
    """Altura del terreno (m) del GEO, o None si el archivo no la trae."""
    import h5py
    with h5py.File(ruta_geo, "r") as f:
        g = f["geolocation_data"]
        if "height" not in g:
            return None
        ds = g["height"]
        h = ds[:].astype(np.float64)
        fill = ds.attrs.get("_FillValue")
        if fill is not None:
            h[h == float(np.asarray(fill).ravel()[0])] = np.nan     # el valor de relleno que declara el propio archivo
        h = h * float(np.asarray(ds.attrs.get("scale_factor", 1.0)).ravel()[0])
        h[h < -1000] = np.nan                                       # salvaguarda: nada del terreno está 1 km bajo el mar
        return h


def area_nativa_m2(lat, lon, i, j):
    """Área estimada de un píxel nativo: espaciado a sus vecinos de columna (barrido) por el de fila (órbita), en m2.
    Se toma el MENOR de los dos lados en cada eje: un salto entre barridos o una fila perdida solo puede agrandar el espaciado
    (la mediana de dos valores es su promedio y no lo evita). nan si no hay vecinos."""
    def d(a, b):
        return float(MV._haversine(lat[a], lon[a], lat[b], lon[b]) * 1000.0)
    n0, n1 = lat.shape
    ds = [x for x in (d((i, j), (i, jj)) for jj in (j - 1, j + 1) if 0 <= jj < n1) if np.isfinite(x)]
    dt = [x for x in (d((i, j), (ii, j)) for ii in (i - 1, i + 1) if 0 <= ii < n0) if np.isfinite(x)]
    if not ds or not dt:
        return float("nan")
    return float(min(ds) * min(dt))


def energia_nativa_vs_grilla(rad, lat, lon, g0, alert, L_bk=None):
    """Bloque B del informe: lo que ve el píxel nativo contra lo que ve la grilla de producción en las celdas alertadas.
    Dos medidas:
      - dL (sin fondo, homogénea con la fórmula de la vía, VRP = (L_hot - L_bk) * coef): por celda alertada, el promedio de I4 de
        los píxeles nativos cuyo centro cae en ella, sumado; contra la suma de la grilla en las MISMAS celdas; a ambos se les resta
        el fondo L_bk de la vía (repartido en proporción al número de celdas con nativo). Es la razón que decide.
      - E (con fondo, ponderada por el área estimada de cada píxel nativo contra el área fija de celda): descriptiva; el fondo
        la diluye y por eso no decide nada.
    Las celdas alertadas sin ningún píxel nativo con centro dentro se cuentan aparte (el nativo es más grueso que la celda)."""
    i4 = rad["I04"]
    d = MV._haversine(lat, lon, VENT_CHI[0], VENT_CHI[1])
    cerca = np.argwhere(np.isfinite(d) & (d < 8.0))
    por_celda, areas, e_nat = {}, [], 0.0
    if len(cerca):
        cf, cc = IP.celdas_de(g0, lat[cerca[:, 0], cerca[:, 1]], lon[cerca[:, 0], cerca[:, 1]])
        for (i, j), f, c in zip(cerca, cf, cc):
            k = (int(f), int(c))
            if k in alert and np.isfinite(i4[i, j]):
                a = area_nativa_m2(lat, lon, int(i), int(j))
                s_, n_ = por_celda.get(k, (0.0, 0))
                por_celda[k] = (s_ + float(i4[i, j]), n_ + 1)
                areas.append(a)
                if np.isfinite(a):
                    e_nat += float(i4[i, j]) * a
    m13g, _ = MV.remuestrear_grilla(lat, lon, rad["I04"], rad["I05"], g0)
    suma_grilla = float(sum(m13g[f, c] for f, c in alert if np.isfinite(m13g[f, c]))) if alert else 0.0
    con = [k for k in alert if k in por_celda]
    L_nat = float(sum(por_celda[k][0] / por_celda[k][1] for k in con))
    L_grid_mismas = float(sum(m13g[k] for k in con if np.isfinite(m13g[k])))
    out = {"n_celdas_alertadas": len(alert), "n_celdas_con_nativo": len(con), "n_celdas_sin_nativo": len(alert) - len(con),
           "n_nativos_en_ellas": int(sum(n for _, n in por_celda.values())),
           "L_hot_nativo_por_celda": L_nat, "L_hot_grilla_mismas_celdas": L_grid_mismas, "suma_I4_grilla_todas": suma_grilla,
           "area_nativa_mediana_m2": float(np.nanmedian(areas)) if areas else None,
           "E_nativa_ponderada": e_nat, "E_grilla": suma_grilla * AREA_CELDA_V375_M2,
           "razon_E_nativa_sobre_grilla": (e_nat / (suma_grilla * AREA_CELDA_V375_M2)) if suma_grilla else None,
           "razon_L_hot_nativo_sobre_grilla": (L_nat / L_grid_mismas) if L_grid_mismas else None,
           "dL_nativo": None, "dL_grilla_mismas_celdas": None, "razon_dL_nativo_sobre_grilla": None}
    if L_bk is not None and alert and con:
        bk = float(L_bk) * len(con) / len(alert)
        out.update({"dL_nativo": L_nat - bk, "dL_grilla_mismas_celdas": L_grid_mismas - bk,
                    "razon_dL_nativo_sobre_grilla": ((L_nat - bk) / (L_grid_mismas - bk)) if (L_grid_mismas - bk) else None})
    return out


def energia_ventana(rad, lat, lon, g0, radio_km=3.0, anillo_km=(5.0, 9.0)):
    """Energía en exceso de I4 en una VENTANA fija alrededor del cráter, nativa contra grilla. Es la medida que decide dónde se
    pierde la energía, porque no depende de qué celdas alertó el detector (la comparación por celda alertada sale >1 por
    construcción: el remuestreo reparte un píxel caliente entre sus vecinas y la selección toma las más altas).
      nativo: sum((L - mediana del anillo nativo) * área estimada del píxel) sobre los píxeles a menos de radio_km del cráter.
      grilla: sum((L - mediana del anillo de la grilla) * 375^2) sobre las celdas cuyo centro está a menos de radio_km.
    Con un campo suave y una escena regular la razón da ~1 (prueba con un blob gaussiano). OJO: para un píxel aislado NO da 1 ni en
    una escena regular: la triangulación de Delaunay de una red regular es degenerada (cuatro vecinos cocirculares) y el grado
    de cada vértice, que depende del desempate, decide cuánta energía conserva el lineal (medido en una escena sintética: 0,7 con
    un píxel caliente aislado). Eso es parte de lo que este experimento mide; lejos de 1 en las bajas y cerca de 1 en los
    controles = el remuestreo o la geometría del barrido pierde energía."""
    from pyproj import Transformer
    i4 = rad["I04"]
    d = MV._haversine(lat, lon, VENT_CHI[0], VENT_CHI[1])
    ring = np.isfinite(d) & (d >= anillo_km[0]) & (d < anillo_km[1]) & np.isfinite(i4)
    win = np.isfinite(d) & (d < radio_km) & np.isfinite(i4)
    if not ring.any() or not win.any():
        return {"estado": "sin_pixeles_en_la_ventana"}
    med_nat = float(np.median(i4[ring]))
    e_nat, n_nat = 0.0, 0
    for i, j in np.argwhere(win):
        a = area_nativa_m2(lat, lon, int(i), int(j))
        if np.isfinite(a):
            e_nat += (float(i4[i, j]) - med_nat) * a
            n_nat += 1
    m13g, _ = MV.remuestrear_grilla(lat, lon, rad["I04"], rad["I05"], g0)
    n, paso = int(g0["n"]), float(g0["paso"])
    X, Y = np.meshgrid(g0["ul_x"] + paso * (np.arange(n) + 0.5), g0["ul_y"] - paso * (np.arange(n) + 0.5))
    xv, yv = Transformer.from_crs("EPSG:4326", f"EPSG:{g0['epsg']}", always_xy=True).transform(VENT_CHI[1], VENT_CHI[0])
    dc = np.hypot(X - xv, Y - yv) / 1000.0
    rg = (dc >= anillo_km[0]) & (dc < anillo_km[1]) & np.isfinite(m13g)
    wg = (dc < radio_km) & np.isfinite(m13g)
    if not rg.any() or not wg.any():
        return {"estado": "sin_celdas_en_la_ventana"}
    med_grid = float(np.median(m13g[rg]))
    e_grid = float(np.sum(m13g[wg] - med_grid)) * AREA_CELDA_V375_M2
    return {"radio_km": radio_km, "anillo_km": list(anillo_km), "n_nativos": n_nat, "n_celdas": int(wg.sum()),
            "mediana_anillo_nativo": med_nat, "mediana_anillo_grilla": med_grid,
            "E_ventana_nativa": e_nat, "E_ventana_grilla": e_grid,
            "razon_E_ventana_nativa_sobre_grilla": (e_nat / e_grid) if e_grid else None}


def top_nativos(rad, lat, lon, ang, g0, alert, flags, n=25, radio_km=5.0):
    """Los n píxeles nativos más radiantes en I4 a menos de radio_km del cráter, con celda, I4, I5 y banderas decodificadas."""
    i4 = rad["I04"]
    d = MV._haversine(lat, lon, VENT_CHI[0], VENT_CHI[1])
    ok = np.isfinite(d) & (d < radio_km)
    lista = sorted(np.argwhere(ok & np.isfinite(i4)).tolist(), key=lambda ij: -i4[ij[0], ij[1]])[:n]
    top = []
    if lista:
        tf, tc = IP.celdas_de(g0, [lat[i, j] for i, j in lista], [lon[i, j] for i, j in lista])
        celdas = {tuple(ij): (int(f), int(c)) for ij, f, c in zip(lista, tf, tc)}
        for i, j in lista:
            fl = None
            if flags.get("I04"):
                arr, nombres = flags["I04"]
                v = int(arr[i, j])
                fl = {"valor": v, "bits": [nm for mk, nm in nombres if mk and (v & mk)]}
            top.append({"i": i, "j": j, "dist_km": round(float(d[i, j]), 2), "celda": list(celdas[(i, j)]),
                        "en_alertada": celdas[(i, j)] in alert, "I04": float(i4[i, j]), "I05": float(rad["I05"][i, j]),
                        "cenit": round(float(ang["sensor_zenith"][i, j]), 1), "banderas_I04": fl})
    return top, int((ok & ~np.isfinite(i4)).sum())


def terreno(top, lat, lon, ang, altura, g0, dh_m=200.0):
    """SOLO DESCRIPTIVO. El GEO de VIIRS ya viene corregido por terreno (y MIROVA usa el mismo), así que NO se simula una posición
    sin corregir. Se reporta la altura del DEM bajo el píxel nativo más radiante, el cenit y el azimut, y cuánto se movería su
    posición si la altura real de la fuente difiriera del DEM en +-dh_m: dh*tan(cenit) en la dirección del azimut, probando los dos
    signos (sensor_azimuth apunta del píxel al satélite en el L1B de VIIRS; SIN VERIFICAR en estos archivos) y la celda resultante."""
    if altura is None:
        return "sin height en el GEO"
    if not top:
        return "sin pixeles"
    from pyproj import Transformer
    i, j = top[0]["i"], top[0]["j"]
    hh = float(altura[i, j])
    z = math.radians(float(ang["sensor_zenith"][i, j]))
    az = math.radians(float(ang["sensor_azimuth"][i, j]))
    d_m = dh_m * math.tan(z)
    tf = Transformer.from_crs("EPSG:4326", f"EPSG:{g0['epsg']}", always_xy=True)
    x, y = tf.transform(float(lon[i, j]), float(lat[i, j]))
    paso = float(g0["paso"])
    out = {"altura_dem_m": round(hh, 1), "cenit": round(math.degrees(z), 1), "azimut": round(math.degrees(az), 1),
           "dh_supuesto_m": dh_m, "desplazamiento_por_dh_m": round(d_m, 0), "celda_con_posicion_del_GEO": top[0]["celda"],
           "celda_crater": list(MV.celda_de(g0, VENT_CHI[0], VENT_CHI[1]))}
    for signo, nom in ((-1, "alejado_del_sensor_menos"), (+1, "hacia_el_sensor_mas")):
        xe, ye = x + signo * d_m * math.sin(az), y + signo * d_m * math.cos(az)
        out[nom] = {"celda": [int((g0["ul_y"] - ye) // paso), int((xe - g0["ul_x"]) // paso)]}
    return out


def analizar_chi(nombre_l1b, rad, lat, lon, ang, flags, altura, ref):
    g0 = MV.grilla_del_volcan("NevadosDeChillan", paso_m=MV.FAMILIAS["VIIRS375"]["paso_m"], clave_roi=MV.FAMILIAS["VIIRS375"]["clave_roi"])
    sensor = SENSOR_375[nombre_l1b[:3]]
    mir = ref.get("mirova_vrp_mw")
    item = {"gran": nombre_l1b, "mirova_vrp": mir, "razon_publicada": ref.get("razon_publicada"),
            "vrp_publicado": ref.get("publicado_vrp_mw"), "variantes": {}}
    for nombre, (g, interp) in variantes(g0).items():
        rec = correr_via("VIIRS375", "NevadosDeChillan", VENT_CHI, INNER_CHI, sensor, rad, lat, lon, ang, g, interp)
        if rec is None:
            item["variantes"][nombre] = {"estado": "sin_record"}
            continue
        item["variantes"][nombre] = {"grilla_ul": [g["ul_x"], g["ul_y"]], "vrp_mw": rec["vrp_mw"], "n_pix": rec["n_anomalous_pixels"],
                                     "razon_mirova": (rec["vrp_mw"] / mir) if mir else None,
                                     "alertadas": [[p["fila"], p["col"]] for p in rec["anomaly_pixels"]],
                                     "L_hot": rec["diag_codigo_mirova"].get("L_hot"), "L_bk": rec["diag_codigo_mirova"].get("L_bk")}
    base = item["variantes"].get("lineal", {})
    item["reproduce_publicado"] = bool(base.get("vrp_mw") is not None and ref.get("publicado_vrp_mw") is not None
                                       and abs(base["vrp_mw"] - ref["publicado_vrp_mw"]) < 0.01)
    alert = set(tuple(x) for x in base.get("alertadas", []))
    item["B_energia"] = energia_nativa_vs_grilla(rad, lat, lon, g0, alert, L_bk=base.get("L_bk"))
    top, perdidos = top_nativos(rad, lat, lon, ang, g0, alert, flags)
    item["B2_energia_ventana"] = energia_ventana(rad, lat, lon, g0)
    item["C_top25_nativos"] = top
    item["C_nativos_con_dato_perdido_a_5km"] = perdidos
    item["D_terreno"] = terreno(top, lat, lon, ang, altura, g0)
    return item


def recorte_chi(rad, lat, lon, ang, flags, altura):
    f4 = flags.get("I04")
    return _recorte(lat, lon, VENT_CHI, 12.0, I04=rad["I04"], I05=rad["I05"], cenit=ang.get("sensor_zenith"),
                    azimut=ang.get("sensor_azimuth"), altura=altura, banderas_I04=None if not f4 else f4[0])
