"""S139 eje 1: que garantiza cada etiqueta del CSV consolidado (latest.php) de Mirova-v1.

Preguntas del instrumento:
1. Si la etiqueta estuviera rota (tipo no derivado de vrp/dist/limite), la recomputacion
   la veria: se compara Tipo_Registro contra la regla de scraper.py:144-154.
2. Si el script estuviera muerto (no lee filas) los denominadores serian 0 y se aborta.
   Control positivo: se inyecta una fila incoherente y un hueco de 3 dias y se exige verlos.

Uso: python medir_consolidado.py <ruta_csv> [<ruta_csv_remoto>]
"""
import sys, io
import pandas as pd
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

LIMITE = {"Isluga": 5, "Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3,
          "Peteroa": 3, "Nevados de Chillan": 5, "Copahue": 4, "Llaima": 5, "Villarrica": 5,
          "Puyehue-Cordon Caulle": 20, "Chaiten": 5}
LON = {"Isluga": -68.83, "Lascar": -67.73, "Lastarria": -68.51, "Tupungatito": -69.80,
       "PlanchonPeteroa": -70.57, "Peteroa": -70.57, "Nevados de Chillan": -71.38, "Copahue": -71.18,
       "Llaima": -71.73, "Villarrica": -71.94, "Puyehue-Cordon Caulle": -72.12, "Chaiten": -72.65}


def tipo_regla(r):
    if r.VRP_MW > 0:
        return "ALERTA_TERMICA" if r.Distancia_km <= LIMITE.get(r.Volcan, np.nan) else "FALSO_POSITIVO"
    return "RUTINA"


def preparar(df):
    df = df.copy()
    df["t"] = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce")
    df["lon"] = df["Volcan"].map(LON)
    df["hora_solar"] = (df["t"].dt.hour + df["t"].dt.minute / 60 + df["lon"] / 15) % 24
    df["noche"] = (df["hora_solar"] < 6) | (df["hora_solar"] >= 18)
    # noche de volcan: la noche local que empieza a las 18 solar se asigna a la fecha del dia siguiente
    df["noche_id"] = (df["t"] + pd.to_timedelta(df["lon"] / 15 * 3600 + 6 * 3600, unit="s")).dt.date
    return df


def huecos_dias(df, min_dias=2):
    dias = pd.Series(sorted(df["t"].dt.normalize().dropna().unique()))
    d = dias.diff().dt.days
    return [(dias[i - 1].date(), dias[i].date(), int(d[i]) - 1) for i in d.index if d[i] and d[i] > min_dias - 0]


def control_positivo(df):
    x = df.head(200).copy()
    i = x.index[x.Tipo_Registro == "RUTINA"][0]
    x.loc[i, "VRP_MW"] = 5.0; x.loc[i, "Distancia_km"] = 1.0  # tipo sigue RUTINA: incoherente
    n_mis = int((x.apply(tipo_regla, axis=1) != x.Tipo_Registro).sum())
    y = df.copy(); y["t"] = pd.to_datetime(y["Fecha_Satelite_UTC"])
    corte = y["t"].quantile(0.5).normalize()
    y = y[(y.t < corte) | (y.t >= corte + pd.Timedelta(days=4))]
    h = [g for g in huecos_dias(y, 2) if g[0] < corte.date() <= g[1]]
    print(f"CONTROL POSITIVO: fila incoherente inyectada detectada={n_mis >= 1} (n_mis={n_mis}); "
          f"hueco inyectado detectado={bool(h)} {h}")


def main(path):
    df = pd.read_csv(path)
    assert len(df) > 0, "SIN DATO: CSV vacio"
    df = preparar(df)
    print(f"== {path}\nfilas={len(df)} ventana Fecha_Satelite_UTC {df.t.min()} a {df.t.max()}")
    print("Fecha_Proceso_GitHub min/max:", df.Fecha_Proceso_GitHub.min(), df.Fecha_Proceso_GitHub.max())
    control_positivo(df)

    print("\n-- Tipo x Clasificacion x Sensor")
    print(pd.crosstab([df.Tipo_Registro, df["Clasificacion Mirova"]], df.Sensor, margins=True).to_string())
    print("\n-- Volcan (nombres crudos)")
    print(df.Volcan.value_counts().to_string())
    print("\n-- Editado:", df.Editado.value_counts(dropna=False).to_dict())

    k = ["timestamp", "Volcan", "Sensor"]
    print(f"\n-- duplicados exactos (timestamp,Volcan,Sensor): {int(df.duplicated(k).sum())}")
    s = df.sort_values(["Volcan", "Sensor", "t"])
    dt = s.groupby(["Volcan", "Sensor"])["t"].diff().dt.total_seconds()
    print(f"   pares consecutivos mismo volcan+sensor separados <=300 s: {int((dt <= 300).sum())}; "
          f"<=1800 s: {int((dt <= 1800).sum())} (de {int(dt.notna().sum())})")
    print("   ejemplos <=300 s:")
    idx = dt[dt <= 300].index[:6]
    for i in idx:
        j = s.index[s.index.get_loc(i) - 1]
        print("     ", s.loc[j, ["Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "Tipo_Registro"]].tolist(),
              "|", s.loc[i, ["Fecha_Satelite_UTC", "VRP_MW", "Distancia_km", "Tipo_Registro"]].tolist())

    print("\n-- coherencia Tipo_Registro vs regla scraper.py (limite_km actual)")
    df["tipo_regla"] = df.apply(tipo_regla, axis=1)
    mis = df[df.tipo_regla != df.Tipo_Registro]
    print(f"   discrepancias: {len(mis)} de {len(df)}")
    if len(mis):
        print(pd.crosstab([mis.Volcan, mis.Tipo_Registro], mis.tipo_regla).to_string())
        print("   rango fechas discrepancias:", mis.t.min(), mis.t.max())
        print(mis[["Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "Distancia_km", "Tipo_Registro", "Clasificacion Mirova"]].head(12).to_string())

    print("\n-- geometria de los ceros")
    print(f"   VRP==0 con Distancia>0: {int(((df.VRP_MW == 0) & (df.Distancia_km > 0)).sum())} de {int((df.VRP_MW == 0).sum())}")
    print(f"   VRP>0 con Distancia==0: {int(((df.VRP_MW > 0) & (df.Distancia_km == 0)).sum())} de {int((df.VRP_MW > 0).sum())}")
    print(f"   VRP NaN: {int(df.VRP_MW.isna().sum())}")

    print("\n-- dia/noche (hora solar local <6 o >=18 = noche) por sensor y tipo")
    print(pd.crosstab([df.Sensor, df.noche], df.Tipo_Registro, margins=True).to_string())
    print("   hora UTC por sensor (conteo):")
    print(pd.crosstab(df.Sensor, df.t.dt.hour).to_string())

    print("\n-- huecos globales (dias calendario sin ninguna fila, >=1 dia)")
    h = huecos_dias(df, 2)
    print(f"   n huecos={len(h)}; dias perdidos total={sum(g[2] for g in h)}")
    for g in sorted(h, key=lambda g: -g[2])[:15]:
        print("     ", g)
    dias_tot = (df.t.max().normalize() - df.t.min().normalize()).days + 1
    print(f"   dias con >=1 fila: {df.t.dt.normalize().nunique()} de {dias_tot}")

    print("\n-- cobertura por volcan x sensor: noches con >=1 fila nocturna / noches en ventana del volcan")
    rows = []
    for (v, se), g in df.groupby(["Volcan", "Sensor"]):
        gn = g[g.noche]
        if len(gn) == 0:
            rows.append((v, se, 0, 0, np.nan, np.nan)); continue
        n_ini, n_fin = gn.noche_id.min(), gn.noche_id.max()
        tot = (pd.Timestamp(n_fin) - pd.Timestamp(n_ini)).days + 1
        ppn = gn.groupby("noche_id").size()
        rows.append((v, se, gn.noche_id.nunique(), tot, round(gn.noche_id.nunique() / tot, 3), float(ppn.median())))
    print(pd.DataFrame(rows, columns=["volcan", "sensor", "noches_con_fila", "noches_ventana", "frac", "pasadas_noche_mediana"]).to_string())

    print("\n-- latencia: primera vez vista (Fecha_Proceso_GitHub, hora Chile) menos adquisicion (Fecha_Captura_Chile), horas")
    lat = (pd.to_datetime(df.Fecha_Proceso_GitHub, errors="coerce") - pd.to_datetime(df.Fecha_Captura_Chile, errors="coerce")).dt.total_seconds() / 3600
    print("   ", lat.describe(percentiles=[.05, .5, .95, .99]).round(2).to_dict())
    print(f"   latencia negativa (<-0.1 h): {int((lat < -0.1).sum())}; > 24 h: {int((lat > 24).sum())}")
    fp = pd.to_datetime(df.Fecha_Proceso_GitHub, errors="coerce")
    print(f"   filas con Fecha_Proceso anterior a 2026-01-09 (creacion scraper): {int((fp < '2026-01-09').sum())}")
    corr = pd.Series(sorted(fp.dropna().unique()))
    gaps = corr.diff().dt.total_seconds() / 3600
    print(f"   instantes distintos de Fecha_Proceso: {len(corr)}; brechas >6 h entre corridas que agregaron filas: {int((gaps > 6).sum())}")
    for i in gaps[gaps > 12].index[:20]:
        print(f"      {corr[i-1]} -> {corr[i]} ({gaps[i]:.1f} h)")

    print("\n-- noche de volcan (todas las pasadas nocturnas, todos los sensores): composicion")
    n = df[df.noche].groupby(["Volcan", "noche_id"]).Tipo_Registro.agg(lambda s: "ALERTA" if (s == "ALERTA_TERMICA").any() else ("SOLO_FP" if (s == "FALSO_POSITIVO").any() else "SOLO_RUTINA"))
    print(pd.crosstab(n.index.get_level_values(0), n).to_string())

    print("\n-- FALSO_POSITIVO: distancia y dia/noche")
    f = df[df.Tipo_Registro == "FALSO_POSITIVO"]
    print("   dist km describe:", f.Distancia_km.describe().round(2).to_dict())
    print("   noche:", f.noche.value_counts().to_dict())
    print("   FP con dist <= limite+1 km (borde):", int((f.Distancia_km <= f.Volcan.map(LIMITE) + 1).sum()))
    df.to_pickle(path + ".s139.pkl") if False else None


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
