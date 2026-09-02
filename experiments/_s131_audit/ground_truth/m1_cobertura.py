"""M1 — Cobertura del archivo TIF de MIROVA vs nuestras pasadas.

POR QUÉ: antes de comparar posiciones hay que saber CUÁNTAS pasadas admiten
comparación pasada-a-pasada. El universo de la auditoría es la intersección
(existe TIF de MIROVA y existe record nuestro del mismo granule), no el total
de detecciones de ninguno de los dos lados (A90: denominador explícito).

TOLERANCIA: ±5 min. Justificación empírica en el JSON (`tolerancia`): la
distribución de |delta| al vecino más cercano es BIMODAL — o cae en 0-5 min
(mismo granule; mediana exacta 0.0) o salta a >60 min (no hay contraparte).
No hay masa intermedia, así que la elección de tolerancia entre 5 y 60 min
no cambia ningún emparejamiento.
"""
import numpy as np
import pandas as pd

import _lib as L

TOL_MIN = 5.0
W0 = pd.Timestamp("2026-05-07", tz="UTC")
W1 = pd.Timestamp("2026-05-22", tz="UTC")


def build_pairs():
    tif = L.load_tif_index()
    recs = L.load_records(start=W0, end=W1)
    pairs, tif_solo, ours_solo = [], [], []
    for v in L.TIER_A:
        for f in ["MODIS", "VIIRS375", "VIIRS750"]:
            g = tif[(tif.volcano == v) & (tif.sensor == f)].copy()
            o = recs[(recs.volcano == v) & (recs.family == f)].sort_values("dt")
            ov = pd.DatetimeIndex(o["dt"])
            used = set()
            for _, x in g.iterrows():
                if len(ov) == 0:
                    tif_solo.append((v, f, x["acq"], x["acq_source"]))
                    continue
                d = np.abs((ov - x["acq"]).total_seconds() / 60.0)
                i = int(np.argmin(d))
                if d[i] <= TOL_MIN and i not in used:
                    used.add(i)
                    r = o.iloc[i]
                    pairs.append(dict(volcano=v, sensor=f, acq=x["acq"],
                                      acq_source=x["acq_source"],
                                      tif_path=x["tif_path"], kmz_path=x["kmz_path"],
                                      rec_idx=int(o.index[i]), delta_min=float(d[i])))
                else:
                    tif_solo.append((v, f, x["acq"], x["acq_source"]))
            for j in range(len(o)):
                if j not in used:
                    r = o.iloc[j]
                    ours_solo.append((v, f, r["dt"], float(r.get("solar_zenith_deg") or np.nan)))
    return pd.DataFrame(pairs), tif_solo, ours_solo, recs, tif


if __name__ == "__main__":
    pairs, tif_solo, ours_solo, recs, tif = build_pairs()
    pairs.to_csv(L.OUT + "/pares_pasada.csv", index=False)

    ts = pd.DataFrame(tif_solo, columns=["volcano", "sensor", "acq", "src"])
    os_ = pd.DataFrame(ours_solo, columns=["volcano", "sensor", "dt", "sza"])

    tab = {}
    for v in L.TIER_A:
        for f in ["MODIS", "VIIRS375", "VIIRS750"]:
            n_tif = int(((tif.volcano == v) & (tif.sensor == f)).sum())
            n_tif_acq = int(((tif.volcano == v) & (tif.sensor == f) &
                             (tif.acq_source == "acquisition_utc")).sum())
            n_ours = int(((recs.volcano == v) & (recs.family == f)).sum())
            n_par = int(((pairs.volcano == v) & (pairs.sensor == f)).sum())
            tab[f"{v}|{f}"] = dict(
                tif_pasadas=n_tif, tif_con_acq_utc=n_tif_acq, nuestras=n_ours,
                pareadas=n_par,
                pct_tif_acq_pareado=round(100 * n_par / n_tif_acq, 1) if n_tif_acq else None,
                pct_nuestras_pareado=round(100 * n_par / n_ours, 1) if n_ours else None)

    # Los "solo TIF" ¿son diurnos? Hora local aprox = UTC - 4 h en Chile.
    ts["hora_utc"] = ts["acq"].dt.hour
    os_["noche"] = os_["sza"] > 90

    res = dict(
        ventana=[str(W0), str(W1)],
        tolerancia=dict(minutos=TOL_MIN,
                        justificacion="distribución bimodal de |delta| al vecino "
                                      "más cercano: 0-5 min o >60 min, sin masa intermedia"),
        universo=dict(
            tif_pasadas_unicas=int(len(tif)),
            tif_con_acquisition_utc=int((tif.acq_source == "acquisition_utc").sum()),
            tif_solo_filename=int((tif.acq_source == "filename").sum()),
            records_nuestros=int(len(recs)),
            pares=int(len(pairs)),
            pct_tif_acq_pareado=round(100 * len(pairs) / max(1, int((tif.acq_source == "acquisition_utc").sum())), 1),
            pct_nuestros_pareado=round(100 * len(pairs) / max(1, len(recs)), 1)),
        pares_por_sensor=pairs.groupby("sensor").size().to_dict(),
        tif_sin_par_por_sensor_y_src=ts.groupby(["sensor", "src"]).size().to_dict(),
        tif_sin_par_hora_utc=ts[ts.src == "acquisition_utc"].groupby(["sensor", "hora_utc"]).size().to_dict(),
        nuestras_sin_par_por_sensor=os_.groupby("sensor").size().to_dict(),
        nuestras_sin_par_noche=os_.groupby(["sensor", "noche"]).size().to_dict(),
        tabla_volcan_sensor=tab)
    L.dump("m1_cobertura.json", res)
    print(pd.DataFrame(tab).T.to_string())
    print("\npares por sensor:", res["pares_por_sensor"])
    print("universo:", res["universo"])
