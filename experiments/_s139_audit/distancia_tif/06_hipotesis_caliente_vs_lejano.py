# -*- coding: utf-8 -*-
"""S139 - la prueba: ¿el número de la web es el píxel más caliente o el más lejano?

EL FENÓMENO, PRIMERO. De noche el campo de radiancia MIR de una escena volcánica está
dominado por la topografía: el valle bajo irradia más que la cumbre nevada, y ese gradiente
vale varios kelvin (A69). Por eso el máximo CRUDO del TIF de MIROVA cae casi siempre al borde
de la escena, sobre el terreno más tibio, y no sobre el volcán: medido acá, mediana 23 km del
centro en 1.545 pasadas. Ese máximo crudo no sirve de nada.

Lo que sí es una anomalía térmica es un EXCESO LOCAL: un píxel mucho más brillante que sus
vecinos inmediatos. Restarle al campo su mediana móvil (paso alto de 9 píxeles) borra el
gradiente topográfico, que varía en decenas de kilómetros, y deja el foco, que vive en uno o
dos píxeles. El máximo de ese campo filtrado es dónde MIROVA ve el calor.

EL INSTRUMENTO. Conocida la posición del foco, la distancia publicada se puede poner a prueba
con el mismo método que ya funcionó sobre el archivo OSF (sonda 03): si el número publicado es
la distancia al píxel MÁS CALIENTE, entonces "distancia publicada = distancia de un punto fijo
al foco" es un sistema sobredeterminado que cierra por mínimos cuadrados con residuo de
píxel fino; si el número publicado es la distancia al píxel más LEJANO del cúmulo, el ajuste
NO cierra: sobra siempre lo que mide el cúmulo, y sobra hacia un solo lado.

CONTROL POSITIVO (declarado antes de correr): el mismo ajuste sobre las filas Npix=1 del
archivo OSF cierra con residuo mediano de 0,3 a 1,8 m en VIIRS 375 m (sonda 03). Ése es el
aspecto que tiene un ajuste que cierra.
CONTROL NEGATIVO: el mismo ajuste con las distancias BARAJADAS entre pasadas. Si también
cierra, el método ajusta ruido y no vale nada.
SEGUNDO CONTROL NEGATIVO: pasadas RUTINA, sin anomalía publicada, donde el paso alto no debe
encontrar un foco destacado.

Read-only. Lee la copia local del archivo hermano y los TIF bajados a `_dl_/`.
"""
import io
import json
import math
import os
import re
import sys

import numpy as np
import pandas as pd
import rasterio
import yaml
from scipy.ndimage import median_filter
from scipy.optimize import least_squares

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
ARCH = os.path.abspath(os.path.join(ROOT, "..", "mirova-tif-archive"))
DL = os.path.join(AQUI, "_dl_")
WEB = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot",
                   "registro_vrp_consolidado.csv")

ARCH2OURS = {"ChillanNevadosde": "NevadosDeChillan"}
SENS = {"MODIS": "MODIS", "VIIRS750": "VIIRS", "VIIRS375": "VIIRS375"}
ALIAS = {
    "Villarrica": {"Villarrica"},
    "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchon Peteroa"},
    "Lascar": {"Lascar", "Láscar"},
    "PuyehueCordonCaulle": {"PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
                            "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"},
    "NevadosDeChillan": {"NevadosDeChillan", "Nevados de Chillan", "Nevados de Chillán"},
    "Copahue": {"Copahue"}, "Llaima": {"Llaima"}, "Lastarria": {"Lastarria"},
    "Isluga": {"Isluga"}, "Chaiten": {"Chaiten", "Chaitén"},
    "Tupungatito": {"Tupungatito"},
}
WEB2OURS = {n: k for k, s in ALIAS.items() for n in s}
LON = {"Villarrica": -71.93, "PlanchonPeteroa": -70.57, "Lascar": -67.73,
       "PuyehueCordonCaulle": -72.12, "NevadosDeChillan": -71.38, "Copahue": -71.18,
       "Llaima": -71.73, "Lastarria": -68.51, "Isluga": -68.83, "Chaiten": -72.65,
       "Tupungatito": -69.80}
TOL_MIN = 30
KERNEL = 9          # píxeles; ~3,4 km en VIIRS375 y ~9 km en MODIS
PROM_MIN = 6.0      # sigmas del campo filtrado: umbral de "foco inequívoco"
_TS = re.compile(r"(\d{8}_\d{6})")


def foco_paso_alto(path):
    """Posición del máximo del campo pasado por alto, y su realce en sigmas."""
    with rasterio.open(path) as src:
        a = src.read(1).astype(float)
        tr = src.transform
        h, w = a.shape
        clon, clat = rasterio.transform.xy(tr, h / 2.0 - 0.5, w / 2.0 - 0.5)
        rows, cols = np.mgrid[0:h, 0:w]
        xs, ys = rasterio.transform.xy(tr, rows.ravel(), cols.ravel())
        lat = np.array(ys).reshape(h, w)
        lon = np.array(xs).reshape(h, w)
    fin = np.isfinite(a)
    if fin.sum() < 200:
        return None
    b = np.where(fin, a, np.nanmedian(a[fin]))
    hp = b - median_filter(b, size=KERNEL)
    hp[~fin] = np.nan
    sig = float(np.nanstd(hp))
    if not np.isfinite(sig) or sig <= 0:
        return None
    k = int(np.nanargmax(np.where(fin, hp, -np.inf)))
    r, c = np.unravel_index(k, a.shape)
    return {"lat": float(lat[r, c]), "lon": float(lon[r, c]),
            "centro_lat": float(clat), "centro_lon": float(clon),
            "prominencia_sigma": round(float(hp[r, c] / sig), 2),
            "hp_max": round(float(hp[r, c]), 5), "sigma_hp": round(sig, 5),
            "px_km": round(float(abs(tr.a) * 111.320 * math.cos(math.radians(clat))), 4)}


def cargar_indices():
    """Índice local + índice remoto restringido a lo que se bajó a `_dl_/`."""
    partes = []
    loc = pd.read_csv(os.path.join(ARCH, "index.csv"))
    loc["raiz"] = ARCH
    partes.append(loc)
    rem = os.path.join(DL, "index_remoto.csv")
    if os.path.exists(rem):
        r = pd.read_csv(rem)
        r["raiz"] = DL
        r = r[[os.path.exists(os.path.join(DL, p.replace("/", os.sep)))
               for p in r.tif_path]]
        partes.append(r)
    d = pd.concat(partes, ignore_index=True)
    d["volcano"] = d.volcano.map(lambda v: ARCH2OURS.get(v, v))
    acq = pd.to_datetime(d.acquisition_utc, utc=True, errors="coerce")
    fn = d.tif_path.str.extract(_TS, expand=False)
    fnts = pd.to_datetime(fn, format="%Y%m%d_%H%M%S", utc=True, errors="coerce")
    d["acq"] = acq.fillna(fnts)
    d = d.dropna(subset=["acq"]).sort_values("captured_at_utc")
    d = d.drop_duplicates(subset=["volcano", "sensor", "md5"], keep="first")
    d = d.drop_duplicates(subset=["volcano", "sensor", "acq"], keep="first")
    return d.reset_index(drop=True)


def ajustar_origen(lat, lon, dist, lat0, lon0):
    x = (lon - lon0) * 111.320 * np.cos(np.radians(lat0))
    y = (lat - lat0) * 110.574

    def res(p):
        return np.hypot(x - p[0], y - p[1]) - dist
    s = least_squares(res, [0.0, 0.0], loss="soft_l1", f_scale=0.3)
    return s.x, res(s.x)


def main():
    vols = {v["name"]: v for v in yaml.safe_load(
        open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
    idx = cargar_indices()
    w = pd.read_csv(WEB)
    w["t"] = pd.to_datetime(w.Fecha_Satelite_UTC, errors="coerce", utc=True)
    w["vol"] = w.Volcan.map(lambda v: WEB2OURS.get(str(v).strip()))
    w["VRP_MW"] = pd.to_numeric(w.VRP_MW, errors="coerce")
    w["Distancia_km"] = pd.to_numeric(w.Distancia_km, errors="coerce")
    w = w.dropna(subset=["t", "vol"])

    casos = []
    for _, r in idx.iterrows():
        vol = r["volcano"]
        if vol not in vols:
            continue
        sw = SENS.get(r["sensor"])
        c = w[(w.vol == vol) & (w.Sensor == sw)]
        if c.empty:
            continue
        dt = (c.t - r["acq"]).abs().dt.total_seconds() / 60.0
        j = dt.idxmin()
        if dt.loc[j] > TOL_MIN:
            continue
        row = c.loc[j]
        p = os.path.join(r["raiz"], r["tif_path"].replace("/", os.sep))
        if not os.path.exists(p):
            continue
        try:
            f = foco_paso_alto(p)
        except Exception:
            continue
        if f is None:
            continue
        hsol = (r["acq"].hour + r["acq"].minute / 60.0 + LON[vol] / 15.0) % 24
        vcfg = vols[vol]
        casos.append({
            "volcan": vol, "sensor": sw, "acq": r["acq"].isoformat(),
            "noche": bool(hsol >= 19 or hsol < 6), "hora_solar": round(float(hsol), 2),
            "tipo": row["Tipo_Registro"], "vrp_mw": float(row["VRP_MW"]),
            "dist_pub_km": float(row["Distancia_km"]),
            "delta_min": round(float(dt.loc[j]), 1),
            "inner_km": float(vcfg.get("inner_radius_km", 5)),
            "vent_lat": vcfg.get("vent_lat", vcfg["lat"]),
            "vent_lon": vcfg.get("vent_lon", vcfg["lon"]),
            "tif": r["tif_path"], "fuente": ("local" if r["raiz"] == ARCH else "descarga"),
            **f})
    d = pd.DataFrame(casos)
    if d.empty:
        raise SystemExit("sin casos")

    d["d_vent_km"] = [
        2 * 6371.0088 * math.asin(math.sqrt(
            math.sin(math.radians(la - vla) / 2) ** 2
            + math.cos(math.radians(vla)) * math.cos(math.radians(la))
            * math.sin(math.radians(lo - vlo) / 2) ** 2))
        for la, lo, vla, vlo in zip(d.lat, d.lon, d.vent_lat, d.vent_lon)]

    R = {"_meta": {
        "n_pasadas_pareadas": int(len(d)),
        "ventana": [str(d.acq.min()), str(d.acq.max())],
        "fuente_tif": dict(d.fuente.value_counts()),
        "kernel_paso_alto_px": KERNEL,
        "prominencia_minima_sigma": PROM_MIN,
        "tolerancia_pareo_min": TOL_MIN,
        "definiciones": {
            "dist_pub_km": "Distancia_km de la fila de la web pareada con esa pasada",
            "foco": "máximo del campo de radiancia menos su mediana móvil de 9 píxeles",
            "prominencia_sigma": "altura del foco en desvíos estándar del campo filtrado"}}}

    # ── CONTROL: ¿el paso alto separa anomalía de campo plano? ───────────────
    R["control_prominencia_por_etiqueta"] = {
        t: {"n": int((d.tipo == t).sum()),
            "prominencia_mediana_sigma": round(float(np.median(
                d.loc[d.tipo == t, "prominencia_sigma"])), 2),
            "sobre_6sigma_pct": round(100.0 * float(
                (d.loc[d.tipo == t, "prominencia_sigma"] >= PROM_MIN).mean()), 1),
            "foco_dentro_del_inner_pct": round(100.0 * float(
                (d.loc[d.tipo == t, "d_vent_km"] <= d.loc[d.tipo == t, "inner_km"]).mean()), 1)}
        for t in sorted(d.tipo.dropna().unique())}

    # ── LA PRUEBA: ajuste del origen sobre las pasadas con foco inequívoco ──
    base = d[(d.prominencia_sigma >= PROM_MIN) & (d.vrp_mw > 0) & d.noche].copy()
    rng = np.random.default_rng(139)
    pruebas, res_todos, res_baraj = [], [], []
    for (vol, sen), g in base.groupby(["volcan", "sensor"]):
        if len(g) < 10:
            continue
        la0 = float(vols[vol]["lat"])
        lo0 = float(vols[vol]["lon"])
        p, r = ajustar_origen(g.lat.values, g.lon.values, g.dist_pub_km.values, la0, lo0)
        _, rb = ajustar_origen(g.lat.values, g.lon.values,
                               g.dist_pub_km.values[rng.permutation(len(g))], la0, lo0)
        res_todos.extend(r.tolist())
        res_baraj.extend(rb.tolist())
        pruebas.append({
            "volcan": vol, "sensor": sen, "n": int(len(g)),
            "origen_corrimiento_km": round(float(np.hypot(*p)), 3),
            "residuo_mediano_m": round(float(np.median(np.abs(r))) * 1000, 1),
            "residuo_p90_m": round(float(np.percentile(np.abs(r), 90)) * 1000, 1),
            "residuo_firmado_mediano_m": round(float(np.median(r)) * 1000, 1),
            "frac_residuo_positivo_pct": round(100.0 * float((r > 0).mean()), 1),
            "control_barajado_residuo_mediano_m": round(float(np.median(np.abs(rb))) * 1000, 1)})
    R["ajuste_por_volcan_sensor"] = pruebas
    if res_todos:
        rt = np.array(res_todos)
        rb = np.array(res_baraj)
        R["ajuste_agregado"] = {
            "n": int(len(rt)),
            "residuo_mediano_m": round(float(np.median(np.abs(rt))) * 1000, 1),
            "residuo_p90_m": round(float(np.percentile(np.abs(rt), 90)) * 1000, 1),
            "residuo_firmado_mediano_m": round(float(np.median(rt)) * 1000, 1),
            "frac_positivo_pct": round(100.0 * float((rt > 0).mean()), 1),
            "control_barajado_residuo_mediano_m": round(float(np.median(np.abs(rb))) * 1000, 1),
            "referencia_control_positivo_OSF_npix1_m": "0,3 a 1,8 m (sonda 03, VIIRS375)"}

    # ── Comparación directa sin ajuste, usando el origen calibrado en OSF ────
    def dist_origen(row, off=(-0.25, -0.25)):
        olat = row.centro_lat + off[1] / 110.574
        olon = row.centro_lon + off[0] / (111.320 * math.cos(math.radians(row.centro_lat)))
        return math.hypot((row.lat - olat) * 110.574,
                          (row.lon - olon) * 111.320 * math.cos(math.radians(row.centro_lat)))
    base["d_foco_km"] = [dist_origen(r) for r in base.itertuples()]
    base["resid_km"] = base.dist_pub_km - base.d_foco_km

    def res_dir(sel, et):
        if len(sel) == 0:
            return {"etiqueta": et, "n": 0}
        v = sel.resid_km.values
        return {"etiqueta": et, "n": int(len(sel)),
                "mediana_km": round(float(np.median(v)), 3),
                "p10_km": round(float(np.percentile(v, 10)), 3),
                "p90_km": round(float(np.percentile(v, 90)), 3),
                "abs_mediana_km": round(float(np.median(np.abs(v))), 3),
                "dentro_de_1px_pct": round(100.0 * float(
                    (np.abs(v) <= sel.px_km.values).mean()), 1),
                "publicada_mayor_pct": round(100.0 * float((v > 0).mean()), 1)}
    R["sin_ajuste_origen_osf"] = {
        "global": res_dir(base, "todas, noche, foco>=6sigma, VRP>0"),
        "por_sensor": {s: res_dir(base[base.sensor == s], s)
                       for s in sorted(base.sensor.unique())},
        "por_tipo": {t: res_dir(base[base.tipo == t], t)
                     for t in sorted(base.tipo.dropna().unique())},
        "foco_lejano_>10km": res_dir(base[base.d_foco_km > 10], "foco a más de 10 km"),
        "foco_cercano_<=5km": res_dir(base[base.d_foco_km <= 5], "foco a 5 km o menos")}

    R["detalle"] = base.drop(columns=["vent_lat", "vent_lon"]).to_dict("records")
    out = os.path.join(AQUI, "06_hipotesis_caliente_vs_lejano.json")
    json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    print("escrito:", out)
    for k in ("_meta", "control_prominencia_por_etiqueta", "ajuste_agregado",
              "sin_ajuste_origen_osf"):
        print()
        print(k.upper())
        print(json.dumps(R.get(k), ensure_ascii=False, indent=1))
    print()
    for p in pruebas:
        print(f"{p['volcan']:20s} {p['sensor']:9s} n={p['n']:4d} "
              f"resid {p['residuo_mediano_m']:8.1f} m (p90 {p['residuo_p90_m']:8.1f}) "
              f"firmado {p['residuo_firmado_mediano_m']:+8.1f}  "
              f"barajado {p['control_barajado_residuo_mediano_m']:8.1f}")


if __name__ == "__main__":
    main()
