# -*- coding: utf-8 -*-
"""S139 - pareo pasada a pasada del archivo de TIF contra la distancia que publica la web.

EL FENOMENO. Cada vez que MIROVA procesa una pasada sobre un volcan publica una imagen
del campo de radiancia MIR recortado a su grilla (el TIF), y en la pagina un numero de
distancia. La pregunta es que punto del campo mide ese numero: el pixel mas caliente del
cumulo alertado, o el pixel alertado mas lejano de la cumbre.

QUE PUEDE Y QUE NO PUEDE EL TIF. El TIF trae el campo COMPLETO, no el conjunto de pixeles
alertados: la prueba NTI que decide cuales se alertan necesita la banda termica, que no
esta en el archivo. Asi que el TIF no entrega el cumulo. Lo que si entrega es la POSICION
del maximo del campo, que bajo la hipotesis "mas caliente" tiene que coincidir con la
distancia publicada, y bajo la hipotesis "mas lejano" solo puede quedar mas cerca o igual.
Esa asimetria de signo es el instrumento.

CONTROLES. (a) pareo desplazado 6 h: si el numero publicado no tiene nada que ver con la
imagen, el desplazado debe dar lo mismo que el pareo real; si el real no mejora al
desplazado, el instrumento no mide nada. (b) filas RUTINA (sin anomalia): el realce del
maximo local sobre el fondo debe ser bajo, contra las ALERTA donde debe ser alto.

Read-only: lee el archivo hermano y los CSV de referencia, escribe solo su JSON.
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

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(AQUI, "..", "..", ".."))
ARCH = os.path.abspath(os.path.join(ROOT, "..", "mirova-tif-archive"))
WEB = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot",
                   "registro_vrp_consolidado.csv")

ARCH2OURS = {"ChillanNevadosde": "NevadosDeChillan"}
SENS_ARCH2WEB = {"MODIS": "MODIS", "VIIRS750": "VIIRS", "VIIRS375": "VIIRS375"}
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
TOL_MIN = 30
_TS = re.compile(r"(\d{8}_\d{6})")

# Corrimiento del origen de las distancias de MIROVA respecto del centro de su grilla,
# despejado por trilateracion sobre las filas Npix=1 del archivo OSF (sonda 03): el
# ajuste cierra con residuo mediano de 0,3 a 1,8 m en VIIRS 375 m, identico en los 10
# volcanes. Se aplica igual a los tres sensores y se reporta tambien la variante sin
# corrimiento, porque en MODIS el ajuste OSF quedo en ~100 m y no es tan limpio.
OFFSET_KM = (-0.25, -0.25)   # (este, norte) en km


def hav(la1, lo1, la2, lo2):
    R = 6371.0088
    p1, p2 = math.radians(la1), math.radians(la2)
    a = (math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2)
         * math.sin(math.radians(lo2 - lo1) / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(max(0.0, min(1.0, a))))


def cargar_index():
    d = pd.read_csv(os.path.join(ARCH, "index.csv"))
    d["volcano"] = d["volcano"].map(lambda v: ARCH2OURS.get(v, v))
    acq = pd.to_datetime(d["acquisition_utc"], utc=True, errors="coerce")
    fn = d["tif_path"].str.extract(_TS, expand=False)
    fnts = pd.to_datetime(fn, format="%Y%m%d_%H%M%S", utc=True, errors="coerce")
    d["acq_source"] = np.where(acq.notna(), "acquisition_utc", "nombre_archivo")
    d["acq"] = acq.fillna(fnts)
    d = d.dropna(subset=["acq"]).sort_values("captured_at_utc")
    d = d.drop_duplicates(subset=["volcano", "sensor", "md5"], keep="first")
    d = d.drop_duplicates(subset=["volcano", "sensor", "acq"], keep="first")
    return d.reset_index(drop=True)


def cargar_web():
    w = pd.read_csv(WEB)
    w["t"] = pd.to_datetime(w.Fecha_Satelite_UTC, errors="coerce", utc=True)
    w["vol"] = w.Volcan.map(lambda v: WEB2OURS.get(str(v).strip()))
    w["VRP_MW"] = pd.to_numeric(w.VRP_MW, errors="coerce")
    w["Distancia_km"] = pd.to_numeric(w.Distancia_km, errors="coerce")
    return w.dropna(subset=["t", "vol"])


def medir_tif(path, inner_km, vent, offset):
    with rasterio.open(path) as src:
        a = src.read(1).astype(float)
        tr = src.transform
        h, wd = a.shape
        # Centro geometrico de la grilla (esquina entre los pixeles centrales).
        clon, clat = rasterio.transform.xy(tr, h / 2.0 - 0.5, wd / 2.0 - 0.5)
        rows, cols = np.mgrid[0:h, 0:wd]
        xs, ys = rasterio.transform.xy(tr, rows.ravel(), cols.ravel())
        lat = np.array(ys).reshape(h, wd)
        lon = np.array(xs).reshape(h, wd)
    olat = clat + offset[1] / 110.574
    olon = clon + offset[0] / (111.320 * math.cos(math.radians(clat)))
    dy = (lat - olat) * 110.574
    dx = (lon - olon) * 111.320 * math.cos(math.radians(clat))
    dist = np.hypot(dx, dy)
    dy0 = (lat - clat) * 110.574
    dx0 = (lon - clon) * 111.320 * math.cos(math.radians(clat))
    dist0 = np.hypot(dx0, dy0)
    dv = np.hypot((lat - vent[0]) * 110.574,
                  (lon - vent[1]) * 111.320 * math.cos(math.radians(vent[0])))
    fin = np.isfinite(a)
    if fin.sum() < 100:
        return None
    fondo = float(np.nanmedian(a[fin]))
    ruido99 = float(np.nanpercentile(a[fin], 99))
    k = int(np.nanargmax(np.where(fin, a, -np.inf)))
    r, c = np.unravel_index(k, a.shape)
    loc = (dv <= inner_km) & fin
    out = {
        "px_km": round(float(abs(tr.a) * 111.320 * math.cos(math.radians(clat))), 4),
        "centro_lat": round(float(clat), 5), "centro_lon": round(float(clon), 5),
        "fondo": round(fondo, 5), "p99": round(ruido99, 5),
        "max_val": round(float(a[r, c]), 5),
        "d_gmax_km": round(float(dist[r, c]), 3),
        "d_gmax_sin_offset_km": round(float(dist0[r, c]), 3),
        "d_gmax_desde_vent_km": round(float(dv[r, c]), 3),
        "realce_gmax": round(float(a[r, c] / fondo), 3) if fondo > 0 else None,
        "n_finitos": int(fin.sum())}
    if loc.sum() >= 5:
        sub = np.where(loc, a, -np.inf)
        kl = int(np.nanargmax(sub))
        rl, cl = np.unravel_index(kl, a.shape)
        out.update({
            "d_lmax_km": round(float(dist[rl, cl]), 3),
            "lmax_val": round(float(a[rl, cl]), 5),
            "realce_lmax": round(float(a[rl, cl] / fondo), 3) if fondo > 0 else None,
            "lmax_supera_p99": bool(a[rl, cl] > ruido99),
            "n_local": int(loc.sum())})
    return out


def main():
    vols = {v["name"]: v for v in yaml.safe_load(
        open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
    idx = cargar_index()
    web = cargar_web()
    V0, V1 = idx.acq.min(), idx.acq.max()

    filas, sin_tif = [], 0
    for _, r in idx.iterrows():
        vol = r["volcano"]
        if vol not in vols:
            continue
        sweb = SENS_ARCH2WEB.get(r["sensor"])
        cand = web[(web.vol == vol) & (web.Sensor == sweb)]
        if cand.empty:
            sin_tif += 1
            continue
        dt = (cand.t - r["acq"]).abs().dt.total_seconds() / 60.0
        j = dt.idxmin()
        if dt.loc[j] > TOL_MIN:
            filas.append({"volcan": vol, "sensor": sweb, "acq": r["acq"].isoformat(),
                          "pareado": False, "tif": r["tif_path"]})
            continue
        row = cand.loc[j]
        # Control: pareo desplazado 6 h (debe colapsar si el instrumento mide algo).
        dt6 = (cand.t - (r["acq"] + pd.Timedelta(hours=6))).abs().dt.total_seconds() / 60.0
        j6 = dt6.idxmin()
        d6 = float(cand.loc[j6, "Distancia_km"]) if dt6.loc[j6] <= TOL_MIN else None
        vcfg = vols[vol]
        vent = (vcfg.get("vent_lat", vcfg["lat"]), vcfg.get("vent_lon", vcfg["lon"]))
        p = os.path.join(ARCH, r["tif_path"].replace("/", os.sep))
        if not os.path.exists(p):
            sin_tif += 1
            continue
        try:
            m = medir_tif(p, float(vcfg.get("inner_radius_km", 5)), vent, OFFSET_KM)
        except Exception as e:                                    # pragma: no cover
            filas.append({"volcan": vol, "sensor": sweb, "error": str(e)})
            continue
        if m is None:
            continue
        f = {"volcan": vol, "sensor": sweb, "acq": r["acq"].isoformat(),
             "acq_source": r["acq_source"], "pareado": True,
             "delta_min": round(float(dt.loc[j]), 1),
             "tipo": row["Tipo_Registro"], "vrp_mw": float(row["VRP_MW"]),
             "dist_pub_km": float(row["Distancia_km"]),
             "dist_pub_desplazada_6h_km": d6,
             "hora_utc": r["acq"].hour, "tif": r["tif_path"],
             "inner_km": float(vcfg.get("inner_radius_km", 5))}
        f.update(m)
        filas.append(f)

    d = pd.DataFrame([f for f in filas if f.get("pareado") and "d_gmax_km" in f])
    R = {"_meta": {
        "archivo_tif": {"ruta": ARCH, "n_tif_indexados": int(len(idx)),
                        "ventana_adquisicion": [str(V0), str(V1)]},
        "web": {"ruta": os.path.relpath(WEB, ROOT), "n_filas": int(len(web))},
        "tolerancia_pareo_min": TOL_MIN,
        "offset_origen_km_este_norte": list(OFFSET_KM),
        "n_tif_pareados": int(len(d)),
        "n_tif_sin_fila_en_csv": int(sum(1 for f in filas if not f.get("pareado"))),
        "limite": "el TIF NO trae el conjunto de pixeles alertados (falta la banda termica): "
                  "se mide la posicion del maximo del campo, no el cumulo de MIROVA."}}

    def resumen(sel, etiqueta, col="d_gmax_km"):
        if len(sel) == 0:
            return {"etiqueta": etiqueta, "n": 0}
        dd = sel["dist_pub_km"].values - sel[col].values
        return {"etiqueta": etiqueta, "n": int(len(sel)),
                "dist_pub_mediana": round(float(np.median(sel.dist_pub_km)), 2),
                f"{col}_mediana": round(float(np.median(sel[col])), 2),
                "delta_mediana_km": round(float(np.median(dd)), 2),
                "abs_delta_mediana_km": round(float(np.median(np.abs(dd))), 2),
                "coinciden_<=0.5km_pct": round(100.0 * float((np.abs(dd) <= 0.5).mean()), 1),
                "pub_mayor_pct": round(100.0 * float((dd > 0.19).mean()), 1),
                "pub_menor_pct": round(100.0 * float((dd < -0.19).mean()), 1)}

    con_vrp = d[d.vrp_mw > 0]
    R["pareo_por_etiqueta"] = {
        t: resumen(d[d.tipo == t], t) for t in sorted(d.tipo.dropna().unique())}
    R["pareo_por_sensor_con_vrp"] = {
        s: resumen(con_vrp[con_vrp.sensor == s], s) for s in sorted(con_vrp.sensor.unique())}
    R["n_por_sensor_etiqueta"] = (d.groupby(["sensor", "tipo"]).size()
                                  .rename("n").reset_index().to_dict("records"))

    # CONTROL de pareo desplazado 6 h.
    sh = con_vrp.dropna(subset=["dist_pub_desplazada_6h_km"])
    if len(sh):
        real = np.abs(sh.dist_pub_km.values - sh.d_gmax_km.values)
        falso = np.abs(sh.dist_pub_desplazada_6h_km.values - sh.d_gmax_km.values)
        R["control_pareo_desplazado_6h"] = {
            "n": int(len(sh)),
            "abs_delta_mediana_pareo_real_km": round(float(np.median(real)), 2),
            "abs_delta_mediana_pareo_6h_km": round(float(np.median(falso)), 2),
            "coinciden_<=0.5km_real_pct": round(100.0 * float((real <= 0.5).mean()), 1),
            "coinciden_<=0.5km_6h_pct": round(100.0 * float((falso <= 0.5).mean()), 1)}

    # CONTROL de realce: RUTINA vs ALERTA (¿el TIF distingue anomalia de campo plano?)
    if "realce_lmax" in d.columns:
        R["control_realce_local"] = {
            t: {"n": int((d.tipo == t).sum()),
                "realce_lmax_mediano": round(float(np.nanmedian(
                    d.loc[d.tipo == t, "realce_lmax"])), 3),
                "lmax_supera_p99_pct": round(100.0 * float(
                    d.loc[d.tipo == t, "lmax_supera_p99"].mean()), 1)}
            for t in sorted(d.tipo.dropna().unique())}

    # Medida 3 del encargo: ¿hay foco dentro del inner en las filas FALSO_POSITIVO?
    R["crater_con_senal_en_falsos_positivos"] = {
        t: {"n": int((d.tipo == t).sum()),
            "con_max_local_sobre_p99_pct": round(100.0 * float(
                d.loc[d.tipo == t, "lmax_supera_p99"].mean()), 1)}
        for t in sorted(d.tipo.dropna().unique())}

    R["detalle"] = filas
    out = os.path.join(AQUI, "04_pareo_tif_vs_distancia.json")
    json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    print("escrito:", out)
    for k in ("pareo_por_etiqueta", "pareo_por_sensor_con_vrp",
              "control_pareo_desplazado_6h", "control_realce_local"):
        print()
        print(k.upper())
        print(json.dumps(R.get(k), ensure_ascii=False, indent=1))
    print()
    print("meta:", json.dumps(R["_meta"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
