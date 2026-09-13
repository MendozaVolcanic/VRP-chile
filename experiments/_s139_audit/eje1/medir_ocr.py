"""S139 eje 1: que agrega el canal OCR y como se cruza con las RUTINA del consolidado.

Preguntas del instrumento:
1. Si el OCR guardara alertas en noches que el consolidado marca RUTINA, el cruce por
   (volcan, sensor, noche) lo ve; si la reconciliacion no corriera, los ALERTA_OCR con
   par FALSO_POSITIVO en CONS apareceria >0.
2. Control positivo: se inyecta en CONS una RUTINA en la misma noche que una ALERTA_OCR
   conocida y otra fila con mismo timestamp exacto; ambas deben contarse.
Uso: python medir_ocr.py <ocr.csv> <consolidado.csv>
"""
import sys, io, re
import pandas as pd
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
LON = {"Isluga": -68.83, "Lascar": -67.73, "Lastarria": -68.51, "Tupungatito": -69.80,
       "PlanchonPeteroa": -70.57, "Peteroa": -70.57, "Nevados de Chillan": -71.38, "Copahue": -71.18,
       "Llaima": -71.73, "Villarrica": -71.94, "Puyehue-Cordon Caulle": -72.12, "Chaiten": -72.65}


def prep(df):
    df = df.copy()
    df["t"] = pd.to_datetime(df.Fecha_Satelite_UTC, errors="coerce")
    lon = df.Volcan.map(LON)
    hs = (df.t.dt.hour + df.t.dt.minute / 60 + lon / 15) % 24
    df["noche"] = (hs < 6) | (hs >= 18)
    df["noche_id"] = (df.t + pd.to_timedelta(lon / 15 * 3600 + 6 * 3600, unit="s")).dt.date
    return df


def cruce(o, c):
    ca = o[o.Tipo_Registro == "ALERTA_TERMICA_OCR"]
    keys_exact = set(zip(c.timestamp, c.Volcan, c.Sensor))
    n_exact = sum((a, b, s) in keys_exact for a, b, s in zip(ca.timestamp, ca.Volcan, ca.Sensor))
    comp = c.groupby(["Volcan", "Sensor", "noche_id"]).Tipo_Registro.agg(
        lambda s: "ALERTA" if (s == "ALERTA_TERMICA").any() else ("SOLO_FP" if (s == "FALSO_POSITIVO").any() else "SOLO_RUTINA"))
    lab = [comp.get((v, s, n), "SIN_FILA_CONS") for v, s, n in zip(ca.Volcan, ca.Sensor, ca.noche_id)]
    return ca.assign(cons_noche_sensor=lab), n_exact


def main(po, pc):
    o = prep(pd.read_csv(po)); c = prep(pd.read_csv(pc))
    assert len(o) and len(c)
    print(f"== OCR {po}: filas={len(o)} ventana {o.t.min()} a {o.t.max()}")
    print(f"   CONS {pc}: filas={len(c)} ventana {c.t.min()} a {c.t.max()}")

    # control positivo
    ca = o[o.Tipo_Registro == "ALERTA_TERMICA_OCR"].iloc[[0]]
    fake = c.head(2).copy()
    fake.iloc[0, fake.columns.get_loc("timestamp")] = ca.timestamp.iloc[0]
    for col in ["Volcan", "Sensor", "noche_id"]:
        fake.iloc[0, fake.columns.get_loc(col)] = ca[col].iloc[0]
        fake.iloc[1, fake.columns.get_loc(col)] = ca[col].iloc[0]
    fake["Tipo_Registro"] = "RUTINA"
    _, ne = cruce(ca, fake)
    x, _ = cruce(ca, fake)
    print(f"CONTROL POSITIVO: match exacto visto={ne == 1}; noche SOLO_RUTINA vista={x.cons_noche_sensor.iloc[0] == 'SOLO_RUTINA'}")

    print("\n-- Tipo x Confianza x Sensor")
    print(pd.crosstab([o.Tipo_Registro, o.Confianza_Validacion], o.Sensor, margins=True).to_string())
    print("\n-- Version_OCR:", o.Version_OCR.value_counts(dropna=False).to_dict())
    nota = o.Nota_Validacion.astype(str)
    cat = np.select([nota.str.contains("RECONCILIADO"), nota.str.contains("Estrella verde"), nota.str.contains("Estrella gris"),
                     nota.str.contains("Grupo p"), nota.str.contains("estrella", case=False)],
                    ["reconciliado", "estrella_verde", "estrella_gris", "grupo_pixeles", "estrella_otra"], "otro")
    o["metodo_nota"] = cat
    print("\n-- metodo segun Nota x Tipo")
    print(pd.crosstab(o.metodo_nota, o.Tipo_Registro, margins=True).to_string())
    print("   ejemplos 'otro':", nota[cat == "otro"].head(5).tolist())
    print("\n-- Nivel_Anomalia_MIROVA x metodo (solo filas con nivel)")
    if "Nivel_Anomalia_MIROVA" in o:
        oo = o[o.Nivel_Anomalia_MIROVA.notna()]
        print(pd.crosstab(oo.metodo_nota, oo.Nivel_Anomalia_MIROVA).to_string())

    print("\n-- dia/noche x tipo x sensor")
    print(pd.crosstab([o.Sensor, o.noche], o.Tipo_Registro).to_string())
    diurna_alta = o[(o.Tipo_Registro == "ALERTA_TERMICA_OCR") & (~o.noche) & (o.VRP_MW >= 10)]
    print(f"   ALERTA_OCR diurnas >=10 MW: {len(diurna_alta)}; {diurna_alta[['Fecha_Satelite_UTC','Volcan','Sensor','VRP_MW','Confianza_Validacion']].to_string() if len(diurna_alta) else ''}")

    print("\n-- reutilizacion de la misma estrella: grupos (volcan,sensor,Fecha_Proceso) con >1 fila guardada por estrella")
    e = o[o.metodo_nota.isin(["estrella_verde", "estrella_gris"])].copy()
    e["y"] = e.Nota_Validacion.str.extract(r"Y=(\d+)")[0]
    g = e.groupby(["Volcan", "Sensor", "Fecha_Proceso_GitHub"])
    multi = g.filter(lambda d: len(d) > 1)
    print(f"   filas por estrella={len(e)}; en grupos multi-fila={len(multi)}; grupos={multi.groupby(['Volcan','Sensor','Fecha_Proceso_GitHub']).ngroups}")
    same_y = multi.groupby(["Volcan", "Sensor", "Fecha_Proceso_GitHub"]).y.nunique()
    print(f"   de esos grupos, con una sola Y de estrella para todas sus filas: {int((same_y == 1).sum())}")
    if len(multi):
        print(multi[["Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "y", "Fecha_Proceso_GitHub"]].head(8).to_string())

    print("\n-- cruce ALERTA_OCR vs consolidado")
    x, ne = cruce(o, c)
    print(f"   ALERTA_OCR={len(x)}; con fila CONS de mismo (timestamp,volcan,sensor)={ne}")
    print("   composicion CONS en la misma noche y sensor:")
    print(pd.crosstab(x.Sensor, x.cons_noche_sensor, margins=True).to_string())
    xn = x[x.noche]
    print("   solo nocturnas:")
    print(pd.crosstab(xn.Sensor, xn.cons_noche_sensor, margins=True).to_string())
    # misma pasada: fila CONS mismo volcan+sensor a <=15 min
    cs = c.sort_values("t")
    near = []
    for _, r in x.iterrows():
        cc = cs[(cs.Volcan == r.Volcan) & (cs.Sensor == r.Sensor)]
        if len(cc) == 0:
            near.append((np.nan, None)); continue
        d = (cc.t - r.t).abs().dt.total_seconds()
        i = d.idxmin(); near.append((d[i], cc.loc[i, "Tipo_Registro"]))
    x["dmin_s"] = [a for a, _ in near]; x["tipo_cercano"] = [b for _, b in near]
    for lim in (60, 900, 3600):
        sel = x[x.dmin_s <= lim]
        print(f"   ALERTA_OCR con fila CONS mismo volcan+sensor a <= {lim} s: {len(sel)}; tipo de esa fila: {sel.tipo_cercano.value_counts().to_dict()}")

    print("\n-- cobertura temporal OCR por mes y sensor (ALERTA_OCR)")
    print(pd.crosstab(x.t.dt.to_period("M"), x.Sensor).to_string())
    print("\n-- FALSO_POSITIVO_OCR: cuantos son RECONCILIADO")
    f = o[o.Tipo_Registro == "FALSO_POSITIVO_OCR"]
    print(f"   {len(f)} filas; reconciliado={int(f.metodo_nota.eq('reconciliado').sum())}")
    print("\n-- Distancia_km==0 en ALERTA_OCR:", int((x.Distancia_km == 0).sum()), "de", len(x))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
