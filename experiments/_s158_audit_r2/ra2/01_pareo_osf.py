# -*- coding: utf-8 -*-
"""RA2 (S158 r2). Pareo por volcan y pasada entre nuestros records 2025 y el OSF v2.5 de MIROVA.

Pregunta 1 del instrumento: si el pareo estuviera roto (mapa de satelites equivocado, tolerancia mal
puesta), la matriz de coincidencias por (Satellite, Resolution) x sensor nuestro y el histograma de dt lo
mostrarian (una matriz difusa o un dt sin pico en 0).
Pregunta 2: si el OSF o los records no cargaran, el numero de pares seria 0, no un cero disfrazado.
Control positivo: el propio mapa de satelites sale del dato (argmax de la matriz), no se supone.

Salida: pares_osf.csv (un par por fila) y 01_pareo_osf.txt (matriz, histograma de dt, pares por volcan).
"""
from __future__ import annotations
import json, math, sys, io
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np, pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2")
OSF = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv")
OUT = WT / "experiments/_s158_audit_r2/ra2"

# Planck: mismas constantes que pipeline (pipeline/process_viirs.py C1/C2), leidas por import.
sys.path.insert(0, str(WT))
from pipeline.process_viirs import C1, C2  # noqa: E402

LAMBDA = {"V375": 3.740, "V750": 4.050, "MODIS": 3.929}  # I04, M13; MODIS: BAND21_LAMBDA escalar porque ENABLE_MODIS_MIR_LAMBDA_POR_BANDA=False (process_modis.py:364,382)
AREA_M2 = {"V375": 375.0 ** 2, "V750": 750.0 ** 2, "MODIS": 1.0e6}
WOOSTER = {"V375": 18.0, "V750": 19.7, "MODIS": 18.9}

NOMBRES = {"Láscar": "Lascar", "Chaitén": "Chaiten", "Puyehue-Cordón Caulle": "PuyehueCordonCaulle",
           "Lastarria": "Lastarria", "Villarrica": "Villarrica", "Chillán, Nevados de": "NevadosDeChillan",
           "Isluga": "Isluga", "Copahue": "Copahue", "Planchón-Peteroa": "PlanchonPeteroa", "Llaima": "Llaima"}
TOL_MIN = 10.0  # tolerancia de pareo declarada; el histograma de dt justifica el valor


def familia(sensor: str) -> str:
    if sensor.startswith("MODIS"):
        return "MODIS"
    return "V750" if sensor.endswith("_750") else "V375"


def plataforma(sensor: str) -> str:
    return sensor.replace("_750", "")


def planck(bt, lam):
    return C1 / (lam ** 5 * (math.exp(C2 / (lam * bt)) - 1.0))


def main():
    osf = pd.read_csv(OSF, encoding="utf-8")  # el archivo es UTF-8 (b"Láscar"); con latin-1 se pierden 5 volcanes
    osf["t"] = pd.to_datetime(osf.timeUTC, format="%d/%m/%Y %H:%M")
    osf = osf[(osf.t.dt.year == 2025) & osf.Volc_Name.isin(NOMBRES)].copy()
    osf["vol"] = osf.Volc_Name.map(NOMBRES)
    print("OSF 2025 filas Chile Tier A:", len(osf), "noche (Dayflag=0):", int((osf.Dayflag == 0).sum()))

    ours = []
    for vol in sorted(set(NOMBRES.values())):
        recs = json.load(open(WT / f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))["records"]
        for r in recs:
            if not r["datetime_utc"].startswith("2025"):
                continue
            ours.append((vol, r))
    print("records nuestros 2025 en los 10 volcanes del OSF:", len(ours))
    print("sensores nuestros:", Counter(r["sensor"] for _, r in ours))
    idx = defaultdict(list)  # (vol, plataforma) -> [(t, rec)]
    for vol, r in ours:
        idx[(vol, r["sensor"])].append((pd.Timestamp(r["datetime_utc"]), r))
    for k in idx:
        idx[k].sort(key=lambda x: x[0])

    # 1) matriz (Satellite, Resolution) x sensor nuestro: coincidencias dentro de TOL_MIN, para deducir el mapa
    mat = Counter()
    for _, row in osf.iterrows():
        for (vol, sens), lst in idx.items():
            if vol != row.vol:
                continue
            ts = np.array([t.value for t, _ in lst])
            j = np.searchsorted(ts, row.t.value)
            for jj in (j - 1, j):
                if 0 <= jj < len(ts) and abs(ts[jj] - row.t.value) <= TOL_MIN * 60e9:
                    mat[(int(row.Satellite), int(row.Resolution), sens)] += 1
                    break
    print("\nMatriz (Satellite, Resolution) -> sensor nuestro, coincidencias con |dt| <=", TOL_MIN, "min")
    tabla = defaultdict(dict)
    for (sat, res, sens), n in sorted(mat.items()):
        tabla[(sat, res)][sens] = n
    mapa = {}
    for k, d in sorted(tabla.items()):
        print(" ", k, dict(sorted(d.items(), key=lambda kv: -kv[1])))
        # la plataforma sale del argmax; la resolucion la fija la columna Resolution del OSF (375 y 750 del
        # mismo satelite comparten hora de granulo, asi que el argmax solo puede decidir la plataforma)
        plat = plataforma(max(d.items(), key=lambda kv: kv[1])[0])
        mapa[k] = plat + ("_750" if k[1] == 750 else "")
    print("mapa elegido (argmax de plataforma + resolucion del OSF):", mapa)

    # 2) pareo con el mapa, vecino mas cercano, dt declarado
    pares, dts = [], []
    sin_par = Counter()
    for _, row in osf.iterrows():
        k = (int(row.Satellite), int(row.Resolution))
        if k not in mapa:
            sin_par["sin mapa"] += 1
            continue
        lst = idx.get((row.vol, mapa[k]), [])
        if not lst:
            sin_par["sin records"] += 1
            continue
        ts = np.array([t.value for t, _ in lst])
        j = np.searchsorted(ts, row.t.value)
        cand = [jj for jj in (j - 1, j) if 0 <= jj < len(ts)]
        jj = min(cand, key=lambda q: abs(ts[q] - row.t.value))
        dt = (ts[jj] - row.t.value) / 60e9
        dts.append(dt)
        if abs(dt) > TOL_MIN:
            sin_par["fuera de tolerancia"] += 1
            continue
        r = lst[jj][1]
        fam = familia(r["sensor"])
        lam = LAMBDA[fam]
        ap = r.get("anomaly_pixels") or []
        l_hot = [planck(p["bt_k"], lam) for p in ap]
        pc = r.get("primary_cluster") or {}
        pares.append(dict(
            vol=row.vol, fam=fam, sensor=r["sensor"], sat_osf=k[0], res_osf=k[1],
            t_osf=row.t, t_ours=lst[jj][0], dt_min=round(dt, 2), dayflag=int(row.Dayflag),
            osf_npix=int(row.Npix), osf_hot=float(row.Tot_Lmir_hot), osf_bk=float(row.Tot_Lmir_bk),
            osf_vrp_w=float(row.VRP), osf_zen=float(row.SatZen), osf_class=int(row["class"]),
            osf_maxdist=float(row.Max_Dist),
            zen=r.get("sensor_zenith_deg"), solzen=r.get("solar_zenith_deg"),
            n_anom=r.get("n_anomalous_pixels"), n_listed=len(ap),
            pc_n=pc.get("n_pixels"), pc_vrp=pc.get("vrp_mw"), pc_geo=pc.get("geo_class"),
            rec_vrp=r.get("vrp_mw"), f5=r.get("f5_core_vrp_mw"),
            dist_class=r.get("distance_class"), fh_dist=r.get("final_hotspot_dist_km"),
            l_bg_ring=r.get("diag_L_bg_w_m2_sr_um"), l_bg_local=r.get("diag_L_bg_local_w_m2_sr_um"),
            t_bg_k=r.get("t_bg_k"),
            sum_l_hot_listed=sum(l_hot) if l_hot else np.nan,
            sum_vrp_listed=sum(p["vrp_mw"] for p in ap) if ap else np.nan,
            max_l_hot=max(l_hot) if l_hot else np.nan,
            n_px_inner=sum(1 for p in ap if p.get("dist_km") is not None),
        ))
    df = pd.DataFrame(pares)
    df.to_csv(OUT / "pares_osf.csv", index=False)
    print("\nsin par:", dict(sin_par))
    print("filas OSF sin par por (vol, Resolution) = filas OSF menos pares:")
    tot = osf.groupby(["vol", "Resolution"]).size().unstack(fill_value=0)
    par = df.groupby(["vol", "res_osf"]).size().unstack(fill_value=0).reindex(index=tot.index, columns=tot.columns, fill_value=0)
    print((tot - par).astype(int).to_string())
    print("total OSF por Resolution:", tot.sum().to_dict(), "| pares:", par.sum().to_dict())
    dts = np.array(dts)
    print("histograma de dt (min, nuestro - OSF), todos los vecinos mas cercanos, n =", len(dts))
    h, e = np.histogram(dts, bins=[-1e9, -30, -10, -6, -3, -1, 0, 1, 3, 6, 10, 30, 1e9])
    for a, b, n in zip(e[:-1], e[1:], h):
        print(f"  [{a:>8.0f}, {b:>8.0f}) {n}")
    print("\nPARES (|dt| <= %.0f min): %d" % (TOL_MIN, len(df)))
    print(df.groupby(["vol", "fam"]).size().unstack(fill_value=0))
    print("\npor familia:", df.fam.value_counts().to_dict())
    print("pares con cluster nuestro (pc_vrp no nulo):", int(df.pc_vrp.notna().sum()),
          "con pc_vrp > 0:", int((df.pc_vrp.fillna(0) > 0).sum()))
    print("dt mediana por familia:", df.groupby("fam").dt_min.median().to_dict())


if __name__ == "__main__":
    main()
