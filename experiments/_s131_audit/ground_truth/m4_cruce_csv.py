# -*- coding: utf-8 -*-
"""M4 - cruce pasada a pasada contra el CSV de MIROVA: las tres celdas.

POR QUE: el GeoTIFF no puede adjudicar posicion (control M3). El CSV si trae un
numero que MIROVA publica y que nadie discute: la `Distancia_km` de la anomalia. El
cruce se hace *solo sobre pasadas comunes* -la pasada existe en el CSV de MIROVA y
existe como record nuestro- porque comparar universos distintos convierte en "falta
de deteccion" lo que es "granule que no procesamos" (reference_s124).

Tres celdas:
  (a) MIROVA alerta y nosotros detectamos: se compara posicion y magnitud;
  (b) MIROVA alerta y nosotros nada: cada uno listado con sus diagnosticos;
  (c) nosotros detectamos y MIROVA nada: clasificados por clase de distancia, path
      del hotspot y ubicacion.

A76: las alertas DIURNAS de MIROVA en VIIRS375 son artefacto de reflexion solar; el
pipeline es night-only, asi que perderlas es hacer las cosas bien. Se cuentan aparte.
Read-only.
"""
import numpy as np
import pandas as pd

import _lib as L

W0 = pd.Timestamp("2026-01-01", tz="UTC")
W1 = pd.Timestamp("2026-09-02", tz="UTC")
TOL = 6.0   # min


def _ours(r, c):
    pc = r.get("primary_cluster") or {}
    o = dict(vrp_pc=float(pc.get("vrp_mw") or 0), nti_max=r.get("nti_max"),
             dclass=r.get("distance_class"), fh_source=r.get("final_hotspot_source"),
             sensor_full=r.get("sensor"), sensor_zenith=r.get("sensor_zenith_deg"),
             solar_zenith=r.get("solar_zenith_deg"),
             n_pix=r.get("n_anomalous_pixels"), test1=r.get("triggered_test1"),
             t_bg_k=r.get("t_bg_k"), t_max_k=r.get("t_max_k"))
    la, lo = pc.get("centroid_lat"), pc.get("centroid_lon")
    if la is not None:
        o["pc_lat"], o["pc_lon"] = la, lo
        o["pc_a_vent_km"] = L.haversine_km(c["vent_lat"], c["vent_lon"], la, lo)
        o["pc_a_mirova_center_km"] = L.haversine_km(
            c["mirova_center_lat"], c["mirova_center_lon"], la, lo)
        o["pc_a_gvp_km"] = L.haversine_km(c["lat"], c["lon"], la, lo)
        o["pc_dentro_inner"] = o["pc_a_vent_km"] <= float(c["inner_radius_km"])
        _, _, _, brg = L.offset_m(c["vent_lat"], c["vent_lon"], la, lo)
        o["pc_cuad"] = L.quadrant(brg)
    if r.get("final_hotspot_lat") is not None:
        o["fh_a_vent_km"] = L.haversine_km(c["vent_lat"], c["vent_lon"],
                                           r["final_hotspot_lat"], r["final_hotspot_lon"])
    return o


def main():
    cfg = L.load_volcanoes()
    recs = L.load_records(start=W0, end=W1)
    mir = L.load_mirova_rows(W0, W1)

    filas = []
    for v in L.TIER_A:
        c = cfg[v]
        for s in ["MODIS", "VIIRS375", "VIIRS750"]:
            o = recs[(recs.volcano == v) & (recs.family == s)].sort_values("dt").reset_index(drop=True)
            m = mir[(mir.volcano == v) & (mir.sensor == s)].sort_values("dt").reset_index(drop=True)
            ov, mv = pd.DatetimeIndex(o["dt"]), pd.DatetimeIndex(m["dt"])
            usados = set()
            for k in range(len(m)):
                fila = dict(volcano=v, sensor=s, dt=m.loc[k, "dt"],
                            csv_tipo=m.loc[k, "tipo"], csv_vrp=m.loc[k, "vrp"],
                            csv_dist=m.loc[k, "dist_km"], csv_fuente=m.loc[k, "fuente"],
                            csv_clase=m.loc[k, "clase"], lado="ambos")
                if len(ov):
                    d = np.abs((ov - m.loc[k, "dt"]).total_seconds() / 60.0)
                    i = int(np.argmin(d))
                    if d[i] <= TOL:
                        usados.add(i)
                        fila.update(_ours(o.iloc[i], c))
                    else:
                        fila["lado"] = "solo_mirova"
                else:
                    fila["lado"] = "solo_mirova"
                filas.append(fila)
            for i in range(len(o)):
                if i in usados:
                    continue
                fila = dict(volcano=v, sensor=s, dt=o.loc[i, "dt"], lado="solo_nuestro")
                fila.update(_ours(o.iloc[i], c))
                filas.append(fila)
    d = pd.DataFrame(filas)
    d.to_csv(L.OUT + "/m4_cruce_detalle.csv", index=False)

    d["mir_det"] = d.csv_tipo.fillna("").str.contains("ALERTA")
    d["mir_fp"] = d.csv_tipo.fillna("").str.contains("FALSO")
    d["nos_det"] = d.vrp_pc.fillna(0) > 0
    d["hora"] = pd.DatetimeIndex(d.dt).hour
    d["diurna_mirova"] = ~d.hora.between(3, 9)

    com = d[d.lado == "ambos"].copy()
    res = dict(
        ventana=[str(W0), str(W1)], tolerancia_min=TOL,
        universo=dict(
            filas_csv_mirova=int(d.csv_tipo.notna().sum()),
            records_nuestros=int((d.lado != "solo_mirova").sum()),
            pasadas_comunes=int(len(com)),
            solo_mirova=int((d.lado == "solo_mirova").sum()),
            solo_nuestro=int((d.lado == "solo_nuestro").sum())),
        nota_denominador="todo lo que sigue es sobre PASADAS COMUNES")

    cn = com[~com.diurna_mirova].copy()
    tab = {}
    for (v, s), g in cn.groupby(["volcano", "sensor"]):
        tp = int((g.mir_det & g.nos_det).sum())
        fn = int((g.mir_det & ~g.nos_det).sum())
        fp = int((~g.mir_det & ~g.mir_fp & g.nos_det).sum())
        tn = int((~g.mir_det & ~g.mir_fp & ~g.nos_det).sum())
        tab[f"{v}|{s}"] = dict(pasadas=int(len(g)), TP=tp, FN=fn, nos_sin_alerta=fp,
                               ambos_nada=tn,
                               recall=round(tp / (tp + fn), 3) if tp + fn else None)
    res["celdas_por_volcan_sensor"] = tab
    glob = {}
    for s, g in cn.groupby("sensor"):
        tp = int((g.mir_det & g.nos_det).sum()); fn = int((g.mir_det & ~g.nos_det).sum())
        glob[s] = dict(pasadas=int(len(g)), TP=tp, FN=fn,
                       recall=round(tp / (tp + fn), 3) if tp + fn else None,
                       nos_sin_alerta=int((~g.mir_det & ~g.mir_fp & g.nos_det).sum()),
                       tasa_nos_sin_alerta=round(float(
                           (~g.mir_det & ~g.mir_fp & g.nos_det).sum() /
                           max(1, int((~g.mir_det & ~g.mir_fp).sum()))), 3))
    res["celdas_por_sensor"] = glob
    res["alertas_diurnas_de_mirova_excluidas"] = dict(
        total=int((com.mir_det & com.diurna_mirova).sum()),
        por_sensor=com[com.mir_det & com.diurna_mirova].groupby("sensor").size().to_dict(),
        nota="A76: reflexion solar; el pipeline es night-only")

    tp = cn[cn.mir_det & cn.nos_det & cn.csv_dist.notna()].copy()
    anc = {}
    for a in ["mirova_center", "vent", "gvp"]:
        col = f"pc_a_{a}_km"
        e = (tp[col] - tp.csv_dist).abs()
        anc[a] = dict(n=int(e.notna().sum()), err_mediano_km=round(float(e.median()), 2),
                      frac_le_1km=round(float((e <= 1).mean()), 3),
                      corr_spearman=round(float(tp[col].corr(tp.csv_dist, method="spearman")), 3))
    res["TP_ancla_de_la_distancia_de_mirova"] = anc
    res["TP_ancla_por_volcan"] = {}
    for v, g in tp.groupby("volcano"):
        if len(g) < 15:
            continue
        res["TP_ancla_por_volcan"][v] = {
            a: round(float((g[f"pc_a_{a}_km"] - g.csv_dist).abs().median()), 2)
            for a in ["mirova_center", "vent", "gvp"]} | {"n": int(len(g)),
                                                          "csv_dist_med": round(float(g.csv_dist.median()), 2)}
    res["TP_magnitud"] = {}
    for s, g in tp.groupby("sensor"):
        r = (g.vrp_pc / g.csv_vrp).replace([np.inf, -np.inf], np.nan).dropna()
        res["TP_magnitud"][s] = dict(n=int(len(r)), ratio_mediano=round(float(r.median()), 3),
                                     p25=round(float(r.quantile(.25)), 3),
                                     p75=round(float(r.quantile(.75)), 3))

    fn = cn[cn.mir_det & ~cn.nos_det].copy()
    fn.to_csv(L.OUT + "/m4_FN_detalle.csv", index=False)
    res["FN"] = dict(
        n=int(len(fn)),
        por_sensor=fn.groupby("sensor").size().to_dict(),
        por_volcan=fn.groupby("volcano").size().to_dict(),
        vrp_mirova=dict(mediana=round(float(fn.csv_vrp.median()), 3),
                        p90=round(float(fn.csv_vrp.quantile(.9)), 2),
                        frac_menor_0_5MW=round(float((fn.csv_vrp < 0.5).mean()), 3)),
        nti_max=dict(mediana=round(float(fn.nti_max.median()), 4) if fn.nti_max.notna().any() else None,
                     frac_en_piso_menor_m0_9=round(float((fn.nti_max < -0.9).mean()), 3)),
        sensor_zenith_mediano=round(float(fn.sensor_zenith.median()), 1),
        frac_zenith_mayor_45=round(float((fn.sensor_zenith > 45).mean()), 3),
        fuente=fn.groupby("csv_fuente").size().to_dict())

    fp = cn[~cn.mir_det & ~cn.mir_fp & cn.nos_det].copy()
    res["nos_sin_alerta"] = dict(
        n=int(len(fp)),
        por_sensor=fp.groupby("sensor").size().to_dict(),
        por_clase_distancia=fp.groupby("dclass").size().to_dict(),
        por_fuente_hotspot=fp.groupby("fh_source").size().to_dict(),
        vrp_nuestro=dict(mediana=round(float(fp.vrp_pc.median()), 3),
                         p90=round(float(fp.vrp_pc.quantile(.9)), 2)),
        pc_a_vent_km=dict(mediana=round(float(fp.pc_a_vent_km.median()), 2),
                          frac_dentro_inner=round(float(fp.pc_dentro_inner.mean()), 3),
                          frac_menor_2km=round(float((fp.pc_a_vent_km < 2).mean()), 3),
                          frac_mayor_5km=round(float((fp.pc_a_vent_km > 5).mean()), 3)),
        por_volcan=fp.groupby("volcano").agg(
            n=("vrp_pc", "size"), vrp_med=("vrp_pc", "median"),
            pc_vent_km_med=("pc_a_vent_km", "median")).round(3).to_dict("index"),
        cuadrante_del_pc=fp.groupby(["volcano", "pc_cuad"]).size().to_dict())
    fp.to_csv(L.OUT + "/m4_nos_sin_alerta_detalle.csv", index=False)

    L.dump("m4_cruce.json", res)
    print(pd.DataFrame(glob).T.to_string())
    print("\nancla de la distancia de MIROVA:")
    print(pd.DataFrame(anc).T.to_string())
    print("\nFN:", res["FN"]["n"], res["FN"]["por_sensor"], res["FN"]["por_volcan"])
    print("nos_sin_alerta:", res["nos_sin_alerta"]["n"], res["nos_sin_alerta"]["por_sensor"])
    print("universo:", res["universo"])


if __name__ == "__main__":
    main()
