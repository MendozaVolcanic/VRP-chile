# -*- coding: utf-8 -*-
"""COB 01 (S159). Pasadas del OSF v2.5 de MIROVA (2025, 10 volcanes Tier A) sin record nuestro.

Ventana: filas del OSF con timeUTC en 2025-01-01..2025-12-31 (OSF llega al 2025-12-31).
Universo: 2.934 filas = todas las filas OSF de los 10 volcanes; 2.880 con Dayflag=0 (noche para MIROVA).
Definicion de "tenemos la pasada": existe un record en data/mirova_equivalent/<vol>.json cuyo sensor es la
plataforma+resolucion del OSF y cuya hora (datetime_utc = inicio del granulo) difiere en <= 10 min de la hora
del OSF. El mapa Satellite/Resolution -> sensor nuestro sale del dato (argmax de coincidencias) y se contrasta
con el prefijo del nombre del granulo del record (MOD/MYD/VNP/VJ1), no se supone.

Pregunta 1 del instrumento: si el pareo estuviera roto (mapa mal), la cobertura de control (pasadas que SI
tienen record) no seria ~100 % con dt = 0; ademas el chequeo cruzado contra el prefijo del granulo lo delata.
Pregunta 2: si los records no cargaran, "sin par" seria 2934 de 2934 (no un cero disfrazado): el script
imprime el total de records cargados y falla si es 0.
Control positivo: las pasadas pareadas deben dar dt = 0 exacto (OSF usa la hora de inicio del granulo).
"""
from __future__ import annotations
import json, sys, io
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np, pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = Path(r"C:\vrp-trabajo\s159-pruebas")
OSF = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv")
OUT = WT / "experiments/_s159/cob"

NOMBRES = {"Láscar": "Lascar", "Chaitén": "Chaiten", "Puyehue-Cordón Caulle": "PuyehueCordonCaulle",
           "Lastarria": "Lastarria", "Villarrica": "Villarrica", "Chillán, Nevados de": "NevadosDeChillan",
           "Isluga": "Isluga", "Copahue": "Copahue", "Planchón-Peteroa": "PlanchonPeteroa", "Llaima": "Llaima"}
TOL = pd.Timedelta(minutes=10)
PREF = {"MOD": "MODIS_TERRA", "MYD": "MODIS_AQUA", "VNP": "VIIRS_SNPP", "VJ1": "VIIRS_NOAA20", "VJ2": "VIIRS_NOAA21"}


def main():
    osf = pd.read_csv(OSF, encoding="utf-8")
    osf["t"] = pd.to_datetime(osf.timeUTC, format="%d/%m/%Y %H:%M")
    osf = osf[(osf.t.dt.year == 2025) & osf.Volc_Name.isin(NOMBRES)].copy()
    osf["vol"] = osf.Volc_Name.map(NOMBRES)
    osf = osf.reset_index(drop=True)
    print("OSF 2025 filas (10 volcanes):", len(osf), "| Dayflag=0:", int((osf.Dayflag == 0).sum()),
          "| rango:", osf.t.min(), osf.t.max())

    rec = []
    for vol in sorted(set(NOMBRES.values())):
        for r in json.load(open(WT / f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))["records"]:
            rec.append(dict(vol=vol, t=pd.Timestamp(r["datetime_utc"]), sensor=r["sensor"], granule=r.get("granule"),
                            solzen=r.get("solar_zenith_deg"), pv=r.get("product_version")))
    rec = pd.DataFrame(rec)
    assert len(rec) > 0, "records no cargaron"
    print("records totales (todos los anios):", len(rec), "| 2025:", int((rec.t.dt.year == 2025).sum()),
          "| primer record 2025:", rec[rec.t.dt.year == 2025].t.min())
    # chequeo cruzado sensor vs prefijo del granulo
    rec["pref"] = rec.granule.str[:3].map(PREF)
    base = rec.sensor.str.replace("_750", "", regex=False)
    print("records cuyo prefijo de granulo NO coincide con la plataforma del sensor:", int((rec.pref != base).sum()),
          "de", len(rec))

    idx = {k: g.sort_values("t") for k, g in rec.groupby(["vol", "sensor"])}
    idx_vol = {k: g.sort_values("t") for k, g in rec.groupby("vol")}

    # mapa Satellite/Resolution -> sensor nuestro, argmax de coincidencias
    mat = Counter()
    for _, row in osf.iterrows():
        for (vol, sens), g in idx.items():
            if vol != row.vol:
                continue
            if (abs(g.t - row.t) <= TOL).any():
                mat[(int(row.Satellite), int(row.Resolution), sens)] += 1
    tabla = defaultdict(dict)
    for (s, rs, se), n in mat.items():
        tabla[(s, rs)][se] = n
    mapa = {}
    for k, d in sorted(tabla.items()):
        best = max(d.items(), key=lambda kv: kv[1])[0].replace("_750", "")
        mapa[k] = best + ("_750" if k[1] == 750 else "")
        print("  ", k, "->", mapa[k], "| coincidencias por sensor:", dict(sorted(d.items(), key=lambda kv: -kv[1])[:3]))
    # contraste con prefijo del granulo: el sensor del mapa debe ser el del prefijo en los pares
    filas = []
    for _, row in osf.iterrows():
        k = (int(row.Satellite), int(row.Resolution))
        sens = mapa.get(k)
        g = idx.get((row.vol, sens))
        dt_same = np.nan
        gran = None
        if g is not None and len(g):
            d = (g.t - row.t)
            j = d.abs().values.argmin()
            dt_same = d.values[j] / np.timedelta64(1, "m")
            gran = g.granule.values[j]
        gv = idx_vol.get(row.vol)
        d2 = (gv.t - row.t)
        j2 = d2.abs().values.argmin()
        dt_any = d2.values[j2] / np.timedelta64(1, "m")
        filas.append(dict(vol=row.vol, t=row.t, dayflag=int(row.Dayflag), sat=int(row.Satellite), res=int(row.Resolution),
                          sensor_esp=sens, npix=int(row.Npix), cls=int(row["class"]), vrp_w=float(row.VRP),
                          satzen=float(row.SatZen), dt_same=dt_same, gran_cercano=gran, dt_any=dt_any,
                          sensor_any=gv.sensor.values[j2]))
    df = pd.DataFrame(filas)
    df["cubierta"] = df.dt_same.abs() <= 10
    print("\nCOBERTURA (|dt|<=10 min, misma plataforma+resolucion): cubiertas", int(df.cubierta.sum()),
          "| faltan", int((~df.cubierta).sum()), "de", len(df))
    pares = df[df.cubierta]
    print("control positivo: dt de las pareadas -> min", pares.dt_same.min(), "max", pares.dt_same.max(),
          "| n con dt!=0:", int((pares.dt_same != 0).sum()))
    # prefijo del granulo de los pareados vs plataforma esperada
    pares = pares.assign(pref=pares.gran_cercano.str[:3].map(PREF))
    print("pareadas cuyo prefijo de granulo != plataforma esperada:",
          int((pares.pref != pares.sensor_esp.str.replace("_750", "", regex=False)).sum()))
    falt = df[~df.cubierta].copy()
    falt["fecha"] = falt.t.dt.date
    falt["mes"] = falt.t.dt.strftime("%Y-%m")
    falt["antes_inicio_serie"] = falt.t < pd.Timestamp("2025-02-15 00:00")
    falt.to_csv(OUT / "faltantes.csv", index=False)
    df.to_csv(OUT / "osf_pareo.csv", index=False)

    print("\nFALTANTES por Dayflag:", falt.dayflag.value_counts().to_dict())
    print("FALTANTES antes del inicio de la serie nuestra (2025-02-15):", int(falt.antes_inicio_serie.sum()))
    print("FALTANTES en/despues 2025-02-15:", int((~falt.antes_inicio_serie).sum()))
    print("Denominador OSF antes 2025-02-15:", int((df.t < pd.Timestamp("2025-02-15")).sum()),
          "| desde 2025-02-15:", int((df.t >= pd.Timestamp("2025-02-15")).sum()))
    print("\nFALTANTES por volcan (total / desde 2025-02-15 / OSF desde 2025-02-15):")
    tot = df.groupby("vol").size()
    totd = df[df.t >= pd.Timestamp("2025-02-15")].groupby("vol").size()
    f1 = falt.groupby("vol").size()
    f2 = falt[~falt.antes_inicio_serie].groupby("vol").size()
    print(pd.DataFrame({"osf_total": tot, "faltan": f1, "osf_desde_0215": totd, "faltan_desde_0215": f2}).fillna(0).astype(int).to_string())
    print("\nFALTANTES (desde 2025-02-15) por sensor esperado:", falt[~falt.antes_inicio_serie].sensor_esp.value_counts().to_dict())
    print("OSF (desde 2025-02-15) por sensor esperado:", df[df.t >= pd.Timestamp("2025-02-15")].sensor_esp.value_counts().to_dict())
    print("\nFALTANTES (desde 2025-02-15) por mes:")
    print(falt[~falt.antes_inicio_serie].groupby("mes").size().to_string())
    print("\nOSF (desde 2025-02-15) por mes:")
    print(df[df.t >= pd.Timestamp("2025-02-15")].groupby(df.t.dt.strftime("%Y-%m")).size().to_string())
    print("\nFALTANTES: distribucion de dt (misma plataforma) y dt (cualquier sensor del volcan):")
    for nombre, col in (("misma plataforma", "dt_same"), ("cualquier sensor", "dt_any")):
        x = falt[col].abs()
        print(" ", nombre, "mediana |dt| min:", float(x.median()), "| <=30:", int((x <= 30).sum()), "| <=60:", int((x <= 60).sum()),
              "| >120:", int((x > 120).sum()))
    print("\nFALTANTES con algun record de OTRA plataforma a <=10 min (mismo volcan):", int((falt.dt_any.abs() <= 10).sum()))
    print("hora UTC de los faltantes (histograma por hora):")
    print(falt.t.dt.hour.value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
