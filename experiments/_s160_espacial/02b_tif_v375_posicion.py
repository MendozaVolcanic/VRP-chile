# -*- coding: utf-8 -*-
"""Pregunta 2 (VIIRS 375): posicion del foco caliente en los GeoTIFF de MIROVA respecto del centro del TIF, del crater y
de nuestro cumulo de la misma pasada. Direccion, no solo distancia (A61, A70, A93, A107).

El TIF es el campo de radiancia MIR de la escena (A24): el maximo crudo es el valle tibio, no la anomalia. Como en S139
(docs/audit_s139/DISTANCIA_MIROVA_VS_TIF.md §6) se le resta la mediana movil de 9 x 9 pixeles (3,4 km) y se busca el
maximo del residuo DENTRO de un radio de busqueda (12 km del centro del TIF: cubre el anillo de MIROVA entero, esquina
10,6 km, y el inner de 7 km de Tupungatito medido desde el vent a 4,8 km). El residuo se expresa en sigmas del residuo de
toda la escena (prominencia).

Advertencias (A106, experiments/_s144_conteo_tif/README.md): los TIF estan en EPSG:4326 (~375 m) salvo 8 adquisiciones
UTM del 14 y 15 de septiembre; la georreferencia se CONTROLA aqui con Lascar y Villarrica (foco conocido en el crater):
en pasadas con alerta de MIROVA el foco debe caer a < 1 km del vent. La hora del nombre puede no ser la de la pasada:
se usa acquisition_utc del indice (experiments/_s147_tif/index_remoto.csv, hasta 2026-09-21) cuando existe, con
tolerancia de 30 min contra la referencia de MIROVA (como S139) y de 15 min contra nuestro record. Una misma imagen
servida bajo dos horas (md5 repetido) se cuenta una sola vez (la primera adquisicion).

A109: nuestro record y el TIF de la misma pasada salen del mismo granulo; la coincidencia de posicion entre el foco del
TIF y nuestro cumulo no es evidencia independiente de que haya calor, solo de DONDE lo pone cada uno.

Las dos preguntas del instrumento:
  P1 (roto): control de georreferencia (Lascar/Villarrica con alerta: foco a < 1 km del vent en la mayoria); control de
     pareo barajando horas (+6 h) debe casi anular los pareos.
  P2 (muerto): n de TIF leidos, n con alerta pareada, n con record nuestro; prominencia mediana en RUTINA vs ALERTA debe
     diferir (si no, el filtro no ve nada).
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median

import numpy as np
import pandas as pd
import rasterio
from scipy.ndimage import median_filter

import comun as C

sys.path.insert(0, str(C.ROOT))
sys.path.insert(0, str(C.ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

VOLS = C.VOLS + ["Lascar", "Villarrica"]
GEO = dict(C.GEO)
GEO["Lascar"] = {"lat": -23.369, "lon": -67.732, "vent": (-23.36293, -67.731416), "tif_centro": (-23.3704, -67.7302), "inner_km": 5.0}
GEO["Villarrica"] = {"lat": -39.42, "lon": -71.93, "vent": (-39.420227, -71.939876), "tif_centro": (-39.4202, -71.9317), "inner_km": 5.0}
PAT = ["../mirova-tif-archive/data/tif/{v}/*VIIRS375*.tif", "experiments/_s147_tif/tif/{v}/*.tif",
       "experiments/_s144_conteo_tif/_dl_tif/*/data/tif/{v}/*.tif",
       "experiments/_s139_audit/distancia_tif/_dl_/data/tif/{v}/*VIIRS375*.tif", "experiments/_s142_ndc/_dl_tif/{v}/*.tif"]
R_BUSQ_KM = 12.0
SAL = C.AQUI / "02b_tif_v375_posicion_salida.txt"
CSV = C.AQUI / "02b_tif_v375_focos.csv"
out = []


def p(*a):
    s = " ".join(str(x) for x in a)
    out.append(s)
    print(s)


def foco(path, tc):
    with rasterio.open(path) as ds:
        A = ds.read(1).astype(float)
        T = ds.transform
        crs = ds.crs
        if crs is None or crs.to_epsg() != 4326:
            return None
        A[~np.isfinite(A)] = np.nan
        A[A <= 0] = np.nan
        if np.isnan(A).mean() > 0.5:
            return {"estado": "mas_de_50pct_nan"}
        fill = np.where(np.isnan(A), np.nanmedian(A), A)
        res = fill - median_filter(fill, size=9, mode="nearest")
        res[np.isnan(A)] = np.nan
        sd = np.nanstd(res)
        rows, cols = np.indices(A.shape)
        lons, lats = rasterio.transform.xy(T, rows.ravel(), cols.ravel())
        lats, lons = np.array(lats).reshape(A.shape), np.array(lons).reshape(A.shape)
        dn = (lats - tc[0]) * 111.195
        de = (lons - tc[1]) * 111.195 * np.cos(np.radians(tc[0]))
        d = np.hypot(dn, de)
        m = (d <= R_BUSQ_KM) & np.isfinite(res)
        if not m.any():
            return {"estado": "sin_pixeles_en_radio"}
        k = np.nanargmax(np.where(m, res, -np.inf))
        i, j = np.unravel_index(k, A.shape)
        # prominencia global y local (celda sobre su anillo de 3 a 6 celdas)
        return {"estado": "ok", "lat": float(lats[i, j]), "lon": float(lons[i, j]), "res_sigma": float(res[i, j] / sd) if sd > 0 else None,
                "bt_max": float(A[i, j]), "res_k": float(res[i, j]), "n_nan_pct": float(100 * np.isnan(A).mean()),
                "p99_res_sigma": float(np.nanpercentile(res, 99) / sd) if sd > 0 else None}


def main():
    ix = pd.read_csv(C.ROOT / "experiments/_s147_tif/index_remoto.csv")
    ix = ix[ix.sensor == "VIIRS375"].copy()
    ix["base"] = ix.tif_path.apply(os.path.basename)
    ix["acq"] = pd.to_datetime(ix.acquisition_utc, errors="coerce", utc=True)
    ix["lm"] = pd.to_datetime(ix.last_modified_utc, errors="coerce", utc=True)
    ref = [f for f in cargar_referencia_unificada() if f["volcano"] in VOLS and f["sensor_bucket"] == "VIIRS375"]
    refi = defaultdict(list)
    for f in ref:
        refi[f["volcano"]].append((datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc), f))
    nuestros = defaultdict(list)
    for v in C.VOLS:
        for r in json.load(open(C.DATA / f"{v}.json", encoding="utf-8"))["records"]:
            if C.bucket(r.get("sensor")) != "VIIRS375":
                continue
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            nuestros[v].append((dt, r))
    filas = []
    for v in VOLS:
        seen = {}
        for pt in PAT:
            for f in glob.glob(str(C.ROOT / pt.format(v=v))):
                seen.setdefault(os.path.basename(f).replace("_lm", ""), f)
        md5s = set()
        tc = GEO[v]["tif_centro"]
        vent = GEO[v]["vent"]
        n_ok = n_md5 = n_nan = n_utm = 0
        for base, path in sorted(seen.items()):
            md5 = hashlib.md5(open(path, "rb").read()).hexdigest()
            if md5 in md5s:
                n_md5 += 1
                continue
            md5s.add(md5)
            row = ix[ix.base == base]
            if len(row) and pd.notna(row.iloc[0].acq):
                t = row.iloc[0].acq.to_pydatetime()
                origen_t = "acquisition_utc"
            else:
                try:
                    t = datetime.strptime(base[:15], "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                origen_t = "nombre"
            fo = foco(path, tc)
            if fo is None:
                n_utm += 1
                continue
            if fo["estado"] != "ok":
                n_nan += 1
                continue
            n_ok += 1
            # pareo con MIROVA (+-30 min; prioridad ALERTA, luego FP, luego RUTINA; CONS antes que OCR)
            cand = [f for (dt, f) in refi[v] if abs((dt - t).total_seconds()) <= 1800]
            cand.sort(key=lambda f: (0 if f["tipo"].startswith("ALERTA") else 1 if f["tipo"].startswith("FALSO") else 2, 0 if f["source"] == "CONS" else 1))
            mr = cand[0] if cand else None
            # nuestro record (+-15 min, el mas cercano)
            nr = min(((abs((dt - t).total_seconds()), r) for (dt, r) in nuestros.get(v, [])), key=lambda x: x[0], default=None)
            nr = nr[1] if nr and nr[0] <= 900 else None
            pc = (nr or {}).get("primary_cluster") or {}
            d_c = C.hav_km(fo["lat"], fo["lon"], *tc)
            r_c = C.rumbo_deg(tc[0], tc[1], fo["lat"], fo["lon"])
            d_v = C.hav_km(fo["lat"], fo["lon"], *vent)
            r_v = C.rumbo_deg(vent[0], vent[1], fo["lat"], fo["lon"])
            d_pc = C.hav_km(fo["lat"], fo["lon"], pc["centroid_lat"], pc["centroid_lon"]) if pc.get("centroid_lat") is not None else None
            filas.append({"vol": v, "base": base, "t": t.strftime("%Y-%m-%d %H:%M"), "origen_t": origen_t, "lat": fo["lat"], "lon": fo["lon"],
                          "res_sigma": fo["res_sigma"], "p99_sigma": fo["p99_res_sigma"], "bt_max": fo["bt_max"], "nan_pct": fo["n_nan_pct"],
                          "d_centro": d_c, "rumbo_centro": r_c, "oct_centro": C.octante(r_c), "d_vent": d_v, "rumbo_vent": r_v, "oct_vent": C.octante(r_v),
                          "mir_tipo": mr["tipo"] if mr else "", "mir_src": mr["source"] if mr else "", "mir_vrp": mr["vrp_mw"] if mr else None,
                          "mir_dist": mr["dist_km"] if mr else None, "mir_dt_min": round((datetime.strptime(mr["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc) - t).total_seconds() / 60, 1) if mr else None,
                          "rec_hora": (nr or {}).get("datetime_utc"), "rec_dc": (nr or {}).get("distance_class"), "pc_vrp": pc.get("vrp_mw"),
                          "pc_lat": pc.get("centroid_lat"), "pc_lon": pc.get("centroid_lon"), "d_pc": d_pc,
                          "pc_dvent": C.hav_km(pc["centroid_lat"], pc["centroid_lon"], *vent) if pc.get("centroid_lat") is not None else None,
                          "rec_n_anom": (nr or {}).get("n_anomalous_pixels"), "solar_zen": (nr or {}).get("solar_zenith_deg")})
        p(f"{v}: TIF unicos {len(seen)}, md5 repetidos {n_md5}, UTM/no 4326 {n_utm}, sin datos {n_nan}, analizados {n_ok}")
    df = pd.DataFrame(filas)
    df.to_csv(CSV, index=False)
    # control de pareo (placebo): horas +6 h
    for v in VOLS:
        dv = df[df.vol == v]
        n_al = (dv.mir_tipo.str.startswith("ALERTA")).sum()
        placebo = 0
        for t in dv.t:
            tt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) + timedelta(hours=6)
            placebo += any(abs((dt - tt).total_seconds()) <= 1800 and f["tipo"].startswith("ALERTA") for (dt, f) in refi[v])
        p(f"  pareo {v}: con ALERTA {n_al} de {len(dv)}; placebo +6 h con ALERTA {placebo}")
    p("\nTIF con alerta de MIROVA (ALERTA_TERMICA o _OCR) pareada: posicion del foco del residuo (maximo a <= 12 km del centro)")
    res = {}
    for v in VOLS:
        dv = df[df.vol == v]
        g = GEO[v]
        p(f"\n== {v}: vent a {C.hav_km(*g['tif_centro'], *g['vent']):.2f} km del centro del TIF ({C.octante(C.rumbo_deg(*g['tif_centro'], *g['vent']))}); inner {g['inner_km']:g}")
        for nombre, sel in (("ALERTA", dv[dv.mir_tipo.str.startswith("ALERTA")]), ("ALERTA tabla (CONS)", dv[(dv.mir_tipo == "ALERTA_TERMICA") & (dv.mir_src == "CONS")]),
                            ("ALERTA protegida >= 1 MW", dv[dv.mir_tipo.str.startswith("ALERTA") & (dv.mir_vrp >= 1.0)]),
                            ("FALSO_POSITIVO", dv[dv.mir_tipo.str.startswith("FALSO")]), ("RUTINA (control)", dv[dv.mir_tipo == "RUTINA"]),
                            ("sin fila a 30 min", dv[dv.mir_tipo == ""])):
            if not len(sel):
                p(f"  {nombre:26s} SIN DATO")
                continue
            noche = sel[(sel.solar_zen.isna()) | (sel.solar_zen > 90)] if "solar_zen" in sel else sel
            r = {"n": int(len(sel)), "prom_p50": float(sel.res_sigma.median()), "d_vent_p50": float(sel.d_vent.median()),
                 "pct_vent_1km": float(100 * (sel.d_vent <= 1.0).mean()), "pct_vent_1_5km": float(100 * (sel.d_vent <= 1.5).mean()),
                 "d_centro_p50": float(sel.d_centro.median()), "oct_centro": dict(Counter(sel.oct_centro).most_common(4)),
                 "oct_vent": dict(Counter(sel.oct_vent).most_common(4)),
                 "pct_caja": float(100 * (sel.d_centro <= C.CAJA_KM).mean()), "pct_anillo": float(100 * (sel.d_centro <= C.ANILLO_KM).mean())}
            p(f"  {nombre:26s} n={r['n']:3d} prominencia p50 {r['prom_p50']:.1f} sigma | foco a vent p50 {r['d_vent_p50']:.2f} km (<=1 km {r['pct_vent_1km']:.0f}%, <=1,5 {r['pct_vent_1_5km']:.0f}%) "
              f"octante desde vent {r['oct_vent']} | foco a centro TIF p50 {r['d_centro_p50']:.2f} km, octante {r['oct_centro']}; en caja {r['pct_caja']:.0f}%, en anillo {r['pct_anillo']:.0f}%")
            con = sel[sel.d_pc.notna()]
            if len(con):
                p(f"     {'':26s} con cumulo nuestro {len(con)}: foco a centroide pc p50 {con.d_pc.median():.2f} km, <=0,6 km {100*(con.d_pc<=0.6).mean():.0f}%, "
                  f"<=1,5 km {100*(con.d_pc<=1.5).mean():.0f}%; pc a vent p50 {con.pc_dvent.median():.2f} km; dc {dict(Counter(con.rec_dc))}")
                r["con_pc"] = {"n": int(len(con)), "d_pc_p50": float(con.d_pc.median()), "pct_06": float(100 * (con.d_pc <= 0.6).mean()), "pct_15": float(100 * (con.d_pc <= 1.5).mean())}
            if nombre.startswith("ALERTA") and sel.mir_dist.notna().any():
                dd = (sel.mir_dist - sel.d_centro)
                p(f"     {'':26s} Distancia_km de MIROVA menos d(foco, centro TIF): mediana {dd.median():+.2f} km, |dif|<=0,8 km {100*(dd.abs()<=0.8).mean():.0f}% (n {dd.notna().sum()})")
            res[(v, nombre)] = r
        # focos lejos del vent en ALERTA: donde estan (fuentes persistentes?)
        al = dv[dv.mir_tipo.str.startswith("ALERTA") & (dv.d_vent > 2.0)]
        if len(al):
            bins = Counter((round(x.lat, 2), round(x.lon, 2)) for x in al.itertuples())
            p(f"  focos de ALERTA a > 2 km del vent: {len(al)} de {int(dv.mir_tipo.str.startswith('ALERTA').sum())}; celdas (lat, lon) mas repetidas {bins.most_common(5)}; "
              f"d_vent p50 {al.d_vent.median():.2f}, octante {dict(Counter(al.oct_vent).most_common(4))}; prominencia p50 {al.res_sigma.median():.1f}")
    json.dump({f"{k[0]}|{k[1]}": v for k, v in res.items()}, open(C.AQUI / "02b_tif_v375_posicion.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    SAL.write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
