# -*- coding: utf-8 -*-
"""M2c — tabla maestra pasada-a-pasada: escena de MIROVA + record nuestro + CSV.

POR QUÉ: el control M3 mostró que el máximo de la escena de MIROVA es BIMODAL — a
veces cae sobre el cráter (donde MIROVA dice que está su anomalía) y a veces se va al
borde del recuadro, 10-29 km afuera, que es el gradiente topográfico de A69 mandando
sobre el infrarrojo medio absoluto. Un instrumento bimodal no se descarta: se le pone
un criterio que separe los dos modos SIN mirar ni nuestro dato ni el cráter.

El criterio candidato es la fuerza del realce en el máximo, medida contra la
dispersión del propio realce en la escena (z robusto con MAD). Si el máximo es una
anomalía de verdad, su realce es un outlier; si es el borde topográfico, no lo es.

Esta tabla junta todo lo necesario para probarlo y para el resto del eje. Read-only.
"""
import numpy as np
import pandas as pd

import _lib as L

A0 = pd.Timestamp("2026-05-08", tz="UTC")
A1 = pd.Timestamp("2026-05-21", tz="UTC")
TOL = 5.0


def main():
    cfg = L.load_volcanoes()
    tif = L.load_tif_index()
    tif = tif[(tif.acq >= A0) & (tif.acq <= A1) & (tif.acq_source == "acquisition_utc")]
    recs = L.load_records(start=A0, end=A1)
    mir = L.load_mirova_rows(A0, A1)

    filas = []
    for v in L.TIER_A:
        c = cfg[v]
        for s in ["MODIS", "VIIRS375", "VIIRS750"]:
            g = tif[(tif.volcano == v) & (tif.sensor == s)]
            o = recs[(recs.volcano == v) & (recs.family == s)]
            mm = mir[(mir.volcano == v) & (mir.sensor == s)]
            ov = pd.DatetimeIndex(o["dt"])
            mv = pd.DatetimeIndex(mm["dt"])
            for _, x in g.iterrows():
                row = dict(volcano=v, sensor=s, acq=x["acq"], tif_path=x["tif_path"])
                try:
                    a, lat, lon = L.read_tif(L.ARCHIVE + "/" + x["tif_path"].replace("\\", "/"))
                except Exception:
                    continue
                dgc = L.dist_grid_km(lat, lon, c["mirova_center_lat"], c["mirova_center_lon"])
                roi = dgc <= float(c["radius_km"])
                ex = L.local_excess(a, 3)
                exr = ex[roi]
                med = float(np.median(exr))
                mad = float(np.median(np.abs(exr - med))) or 1e-12
                f = np.where(roi, ex, -np.inf)
                i, j = np.unravel_index(int(np.nanargmax(f)), f.shape)
                tla, tlo = float(lat[i, j]), float(lon[i, j])
                row.update(
                    tif_lat=tla, tif_lon=tlo,
                    tif_z=(float(ex[i, j]) - med) / (1.4826 * mad),
                    tif_excess=float(ex[i, j]),
                    tif_rad=float(a[i, j]),
                    tif_a_vent_km=L.haversine_km(c["vent_lat"], c["vent_lon"], tla, tlo),
                    tif_a_centro_km=L.haversine_km(c["mirova_center_lat"],
                                                   c["mirova_center_lon"], tla, tlo))
                # record nuestro de la misma pasada
                if len(ov):
                    d = np.abs((ov - x["acq"]).total_seconds() / 60.0)
                    k = int(np.argmin(d))
                    if d[k] <= TOL:
                        r = o.iloc[k]
                        pc = r.get("primary_cluster") or {}
                        row.update(tiene_record=True, dt=str(r["dt"]),
                                   sensor_full=r.get("sensor"),
                                   vrp_pc=float(pc.get("vrp_mw") or 0),
                                   nti_max=r.get("nti_max"),
                                   dclass=r.get("distance_class"),
                                   fh_source=r.get("final_hotspot_source"),
                                   sensor_zenith=r.get("sensor_zenith_deg"),
                                   solar_zenith=r.get("solar_zenith_deg"),
                                   n_pix=r.get("n_anomalous_pixels"))
                        if pc.get("centroid_lat") is not None:
                            row["pc_lat"] = pc["centroid_lat"]; row["pc_lon"] = pc["centroid_lon"]
                            row["pc_a_vent_km"] = L.haversine_km(
                                c["vent_lat"], c["vent_lon"], pc["centroid_lat"], pc["centroid_lon"])
                            row["pc_a_tif_m"] = 1000 * L.haversine_km(
                                tla, tlo, pc["centroid_lat"], pc["centroid_lon"])
                        if r.get("final_hotspot_lat") is not None:
                            row["fh_a_vent_km"] = L.haversine_km(
                                c["vent_lat"], c["vent_lon"],
                                r["final_hotspot_lat"], r["final_hotspot_lon"])
                            row["fh_a_tif_m"] = 1000 * L.haversine_km(
                                tla, tlo, r["final_hotspot_lat"], r["final_hotspot_lon"])
                    else:
                        row["tiene_record"] = False
                else:
                    row["tiene_record"] = False
                # fila del CSV de MIROVA de la misma pasada
                if len(mv):
                    d = np.abs((mv - x["acq"]).total_seconds() / 60.0)
                    k = int(np.argmin(d))
                    if d[k] <= TOL:
                        m = mm.iloc[k]
                        row.update(csv_tipo=m["tipo"], csv_vrp=m["vrp"],
                                   csv_dist=m["dist_km"], csv_fuente=m["fuente"],
                                   csv_clase=m["clase"])
                filas.append(row)
    d = pd.DataFrame(filas)
    d.to_csv(L.OUT + "/m2c_tabla_pasadas.csv", index=False)
    print("filas", len(d), "con record", int(d.tiene_record.sum()),
          "con csv", int(d.csv_tipo.notna().sum()))
    print(d.groupby(["sensor"]).agg(n=("acq", "size"),
                                    con_rec=("tiene_record", "sum")).to_string())


if __name__ == "__main__":
    main()
