# -*- coding: utf-8 -*-
"""M3 — CONTROL DE INSTRUMENTO: ¿el GeoTIFF de MIROVA reproduce a MIROVA?

POR QUÉ (el fenómeno antes que el código): quiero usar la escena publicada por
MIROVA para decir dónde puso ELLA el punto caliente, y compararlo con dónde lo
ponemos nosotros. Pero la escena trae una sola banda —el infrarrojo medio— y en
un volcán nevado de altura el campo de MIR crudo está dominado por el gradiente
de temperatura con la altitud, no por el foco volcánico (A69). Antes de usar la
escena contra nosotros hay que ver si la escena distingue a MIROVA de sí misma:
en las pasadas donde el CSV de MIROVA declara ALERTA con una `Distancia_km`,
¿el punto que yo extraigo de la escena cae a esa distancia?

Se prueban cuatro estimadores del punto caliente y tres anclas de referencia.
Si NINGUNA combinación reproduce la `Distancia_km` de MIROVA, el instrumento no
sirve para adjudicar posición y el eje espacial de M2 queda sin respaldo
externo (extiende el guard de AUDIT_S128 §3).

Read-only.
"""
import numpy as np
import pandas as pd

import _lib as L

W0 = pd.Timestamp("2026-05-08", tz="UTC")
W1 = pd.Timestamp("2026-05-21", tz="UTC")
TOL = pd.Timedelta(minutes=5)

ESTIMADORES = {
    "max_crudo": lambda a: a,
    "realce_3x3": lambda a: L.local_excess(a, 3),
    "realce_5x5": lambda a: L.local_excess(a, 5),
    "realce_9x9": lambda a: L.local_excess(a, 9),
}


def hotspot(a, lat, lon, mask, fn):
    f = fn(a)
    f = np.where(mask, f, -np.inf)
    k = int(np.nanargmax(f))
    i, j = np.unravel_index(k, f.shape)
    return float(lat[i, j]), float(lon[i, j]), float(a[i, j])


def main():
    cfg = L.load_volcanoes()
    tif = L.load_tif_index()
    tif = tif[(tif.acq >= W0) & (tif.acq <= W1) & (tif.acq_source == "acquisition_utc")]
    mir = L.load_mirova_rows(W0, W1)
    al = mir[mir.tipo.str.contains("ALERTA")].copy()

    filas = []
    for _, r in al.iterrows():
        g = tif[(tif.volcano == r["volcano"]) & (tif.sensor == r["sensor"])]
        if g.empty:
            continue
        dd = (g["acq"] - r["dt"]).abs()
        i = dd.idxmin()
        if dd[i] > TOL:
            continue
        c = cfg[r["volcano"]]
        path = L.ARCHIVE + "/" + g.loc[i, "tif_path"].replace("\\", "/")
        try:
            a, lat, lon = L.read_tif(path)
        except Exception as e:
            continue
        anclas = {"mirova_center": (c["mirova_center_lat"], c["mirova_center_lon"]),
                  "vent": (c["vent_lat"], c["vent_lon"]),
                  "gvp": (c["lat"], c["lon"])}
        row = dict(volcano=r["volcano"], sensor=r["sensor"], dt=r["dt"], tipo=r["tipo"],
                   fuente=r["fuente"], vrp_mirova=r["vrp"], dist_csv=r["dist_km"],
                   tif=g.loc[i, "tif_path"])
        for nom_est, fn in ESTIMADORES.items():
            for nom_anc, (la0, lo0) in anclas.items():
                dg = L.dist_grid_km(lat, lon, la0, lo0)
                mask = dg <= float(c["radius_km"])
                if not mask.any():
                    continue
                hla, hlo, val = hotspot(a, lat, lon, mask, fn)
                row[f"d_{nom_est}_{nom_anc}"] = L.haversine_km(la0, lo0, hla, hlo)
                if nom_anc == "mirova_center":
                    row[f"lat_{nom_est}"] = hla
                    row[f"lon_{nom_est}"] = hlo
        filas.append(row)

    d = pd.DataFrame(filas)
    d.to_csv(L.OUT + "/m3_control_detalle.csv", index=False)

    res = {"ventana": [str(W0), str(W1)],
           "alertas_mirova_en_ventana": int(len(al)),
           "alertas_con_tif_de_la_misma_pasada": int(len(d)),
           "nota_anclas": "distancia del estimador a cada ancla, contra Distancia_km del CSV"}

    comp = {}
    ok = d[d.dist_csv.notna()]
    for est in ESTIMADORES:
        for anc in ["mirova_center", "vent", "gvp"]:
            col = f"d_{est}_{anc}"
            if col not in ok:
                continue
            e = (ok[col] - ok.dist_csv).abs()
            comp[f"{est}|{anc}"] = dict(
                n=int(e.notna().sum()),
                err_mediano_km=round(float(e.median()), 2),
                err_p90_km=round(float(e.quantile(.9)), 2),
                frac_err_le_1km=round(float((e <= 1).mean()), 3),
                frac_err_le_2km=round(float((e <= 2).mean()), 3),
                corr_spearman=round(float(ok[col].corr(ok.dist_csv, method="spearman")), 3))
    res["comparacion_estimador_x_ancla"] = comp

    # Estratificado por sensor para el mejor par global
    mejor = min(comp, key=lambda k: comp[k]["err_mediano_km"])
    res["mejor_par"] = mejor
    est, anc = mejor.split("|")
    por = {}
    for s, g in ok.groupby("sensor"):
        e = (g[f"d_{est}_{anc}"] - g.dist_csv).abs()
        por[s] = dict(n=int(len(g)), err_mediano_km=round(float(e.median()), 2),
                      frac_le_1km=round(float((e <= 1).mean()), 3),
                      dist_csv_mediana=round(float(g.dist_csv.median()), 2),
                      dist_estimada_mediana=round(float(g[f"d_{est}_{anc}"].median()), 2))
    res["mejor_par_por_sensor"] = por

    # Contraste: ¿qué distancia da el estimador en pasadas RUTINA (sin alerta)?
    # Si da lo mismo que en las ALERTAS, el instrumento no separa clases.
    res["nota_rutina"] = "ver m3b"
    L.dump("m3_control.json", res)
    print(pd.DataFrame(comp).T.sort_values("err_mediano_km").to_string())
    print("\nmejor:", mejor)
    print(pd.DataFrame(por).T.to_string())


if __name__ == "__main__":
    main()
