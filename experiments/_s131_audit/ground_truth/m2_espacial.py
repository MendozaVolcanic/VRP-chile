# -*- coding: utf-8 -*-
"""M2 — EJE ESPACIAL (A61/A70): dónde ponemos el punto caliente, y hacia dónde.

Dos partes, porque el instrumento externo sólo sobrevivió en dos celdas (M3b):

  A. **Con respaldo exógeno** — sólo en las celdas que pasaron el control: se compara,
     pasada a pasada, el máximo de realce del GeoTIFF de MIROVA contra nuestro
     `primary_cluster.centroid` y nuestro `final_hotspot`.

  B. **Sin instrumento externo, pero contra un punto que no se discute** — el cráter.
     A70 manda medir el offset DIRECCIONAL con mediana (la distancia mediana esconde
     un sesgo sistemático; la media la arruinan los outliers). Se mide (Δnorte, Δeste)
     medianos y la distribución de rumbos por volcán×sensor, en 2026 completo, para
     ver si el sesgo al norte de A69/S104 sobrevive a los cambios de S102-S104.

Read-only.
"""
import json

import numpy as np
import pandas as pd

import _lib as L

W0 = pd.Timestamp("2026-01-01", tz="UTC")
W1 = pd.Timestamp("2026-12-31", tz="UTC")
A0 = pd.Timestamp("2026-05-08", tz="UTC")
A1 = pd.Timestamp("2026-05-21", tz="UTC")


def parte_A(cfg):
    gate = json.load(open(L.OUT + "/m3b_gate.json", encoding="utf-8"))
    aprob = set(gate["celdas_aprobadas"])
    tif = L.load_tif_index()
    tif = tif[(tif.acq >= A0) & (tif.acq <= A1) & (tif.acq_source == "acquisition_utc")]
    recs = L.load_records(start=A0, end=A1)
    filas = []
    for celda in sorted(aprob):
        v, s = celda.split("|")
        c = cfg[v]
        g = tif[(tif.volcano == v) & (tif.sensor == s)]
        o = recs[(recs.volcano == v) & (recs.family == s)]
        for _, x in g.iterrows():
            dd = (pd.DatetimeIndex(o["dt"]) - x["acq"]).total_seconds() / 60.0
            if len(dd) == 0 or np.min(np.abs(dd)) > 5:
                continue
            r = o.iloc[int(np.argmin(np.abs(dd)))]
            a, lat, lon = L.read_tif(L.ARCHIVE + "/" + x["tif_path"].replace("\\", "/"))
            dg = L.dist_grid_km(lat, lon, c["mirova_center_lat"], c["mirova_center_lon"])
            f = np.where(dg <= float(c["radius_km"]), L.local_excess(a, 3), -np.inf)
            i, j = np.unravel_index(int(np.nanargmax(f)), f.shape)
            tla, tlo = float(lat[i, j]), float(lon[i, j])
            pc = r.get("primary_cluster") or {}
            row = dict(volcano=v, sensor=s, dt=str(r["dt"]),
                       tif_lat=tla, tif_lon=tlo,
                       tif_a_vent_km=L.haversine_km(c["vent_lat"], c["vent_lon"], tla, tlo),
                       vrp_pc=pc.get("vrp_mw"))
            for nom, la, lo in (("pc", pc.get("centroid_lat"), pc.get("centroid_lon")),
                                ("final", r.get("final_hotspot_lat"), r.get("final_hotspot_lon"))):
                if la is None or lo is None:
                    continue
                dn, de, dist, brg = L.offset_m(tla, tlo, la, lo)
                row[f"{nom}_a_tif_m"] = dist
                row[f"{nom}_rumbo_desde_tif"] = L.quadrant(brg)
                row[f"{nom}_a_vent_km"] = L.haversine_km(c["vent_lat"], c["vent_lon"], la, lo)
            filas.append(row)
    d = pd.DataFrame(filas)
    if d.empty:
        return {}, d
    res = {}
    for (v, s), g in d.groupby(["volcano", "sensor"]):
        gg = g[g.vrp_pc.notna() & (g.vrp_pc.astype(float) > 0)]
        res[f"{v}|{s}"] = dict(
            n_pasadas_con_tif=int(len(g)),
            n_con_deteccion_nuestra=int(len(gg)),
            tif_a_vent_km_mediana=round(float(g.tif_a_vent_km.median()), 2),
            pc_a_vent_km_mediana=(round(float(gg.pc_a_vent_km.median()), 2)
                                  if "pc_a_vent_km" in gg and gg.pc_a_vent_km.notna().any() else None),
            pc_a_tif_m_mediana=(round(float(gg.pc_a_tif_m.median()), 0)
                                if "pc_a_tif_m" in gg and gg.pc_a_tif_m.notna().any() else None),
            rumbos_pc_desde_tif=(gg.pc_rumbo_desde_tif.value_counts().to_dict()
                                 if "pc_rumbo_desde_tif" in gg else {}),
            final_a_tif_m_mediana=(round(float(gg.final_a_tif_m.median()), 0)
                                   if "final_a_tif_m" in gg and gg.final_a_tif_m.notna().any() else None))
    return res, d


def parte_B(cfg):
    recs = L.load_records(start=W0, end=W1)
    filas = []
    for _, r in recs.iterrows():
        c = cfg[r["volcano"]]
        pc = r.get("primary_cluster") or {}
        for nom, la, lo in (("pc", pc.get("centroid_lat"), pc.get("centroid_lon")),
                            ("final", r.get("final_hotspot_lat"), r.get("final_hotspot_lon"))):
            if la is None or lo is None:
                continue
            dn, de, dist, brg = L.offset_m(c["vent_lat"], c["vent_lon"], la, lo)
            filas.append(dict(volcano=r["volcano"], sensor=r["family"], punto=nom,
                              dn=dn, de=de, dist_m=dist, brg=brg,
                              cuad=L.quadrant(brg), mes=r["dt"].strftime("%Y-%m"),
                              dclass=r.get("distance_class"),
                              vrp=(pc.get("vrp_mw") or 0)))
    d = pd.DataFrame(filas)
    d.to_csv(L.OUT + "/m2b_offsets.csv", index=False)
    out = {}
    for (v, s, p), g in d.groupby(["volcano", "sensor", "punto"]):
        if len(g) < 15:
            continue
        cu = g.cuad.value_counts()
        out[f"{v}|{s}|{p}"] = dict(
            n=int(len(g)),
            dist_mediana_m=round(float(g.dist_m.median()), 0),
            dnorte_mediano_m=round(float(g.dn.median()), 0),
            deste_mediano_m=round(float(g.de.median()), 0),
            offset_mediano_m=round(float(np.hypot(g.dn.median(), g.de.median())), 0),
            rumbo_del_offset_mediano=round(float((np.degrees(np.arctan2(
                g.de.median(), g.dn.median())) + 360) % 360), 0),
            cuadrantes={k: int(cu.get(k, 0)) for k in "NESO"},
            frac_norte=round(float((g.cuad == "N").mean()), 3))
    return out, d


if __name__ == "__main__":
    cfg = L.load_volcanoes()
    ra, da = parte_A(cfg)
    rb, db = parte_B(cfg)
    if not da.empty:
        da.to_csv(L.OUT + "/m2a_tif_vs_nuestro.csv", index=False)
    L.dump("m2_espacial.json", dict(
        parte_A=dict(ventana=[str(A0), str(A1)],
                     nota="sólo celdas que pasaron el control M3b", celdas=ra),
        parte_B=dict(ventana=[str(W0), str(W1)],
                     nota="offset de NUESTRO punto respecto del cráter; mediana (A70); "
                          "sólo celdas con n>=15", celdas=rb)))
    print("PARTE A"); print(pd.DataFrame(ra).T.to_string() if ra else "(vacía)")
    print("\nPARTE B (extracto pc):")
    t = pd.DataFrame({k: v for k, v in rb.items() if k.endswith("|pc")}).T
    print(t.to_string())
