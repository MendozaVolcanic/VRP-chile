"""02: desde cuando es confiable cada archivo. Filas por mes, sensor y tipo;
noches de volcan cubiertas; filas por noche contra la cadencia madura.

La cadencia esperada NO se toma de ningun paper: se mide sobre los meses
maduros (junio a agosto de 2026) del propio consolidado, por sensor, como
mediana de filas por noche de volcan, y cada mes se compara contra eso.
"""
import sys

import pandas as pd

from comun import dir_remoto, encabezado, leer

D = dir_remoto(sys.argv)
cons = leer(f"{D}/registro_vrp_consolidado.csv")
ocr = leer(f"{D}/registro_vrp_ocr.csv")
pos = leer(f"{D}/registro_vrp_positivos.csv")
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 500)

encabezado(
    "COMPLETITUD MENSUAL DEL CONSOLIDADO",
    "un mes con el scraper caido tendria 0 filas o noches sin fila; un mes con OCR roto tendria 0 filas OCR o Version_OCR faltante",
    "las tablas llevan el denominador (noches del mes x 11 volcanes); una celda vacia sale como 0 filas, no como cobertura",
    "se elimina la mitad de las filas de 2026-06 en una copia y la cobertura de ese mes debe bajar",
)
print("ventana consolidado:", cons["dt"].min(), "->", cons["dt"].max(), "| filas:", len(cons))
print("ventana OCR        :", ocr["dt"].min(), "->", ocr["dt"].max(), "| filas:", len(ocr))

print("\n--- filas por mes x sensor (consolidado, todos los tipos)")
print(pd.crosstab(cons["mes"], cons["Sensor"], margins=True))
print("\n--- filas por mes x tipo (consolidado)")
print(pd.crosstab(cons["mes"], cons["Tipo_Registro"], margins=True))
print("\n--- volcanes con filas por mes (consolidado)")
print(cons.groupby("mes")["Volcan"].nunique())
print("\n--- primera fila por volcan (consolidado)")
print(cons.groupby("Volcan")["dt"].min().sort_values())


def cobertura(df, etiqueta):
    """fraccion de (volcan, noche) con >=1 fila nocturna, por mes y sensor."""
    n = df[df["noche"]]
    vols = sorted(df["Volcan"].unique())
    filas = []
    for mes, g in n.groupby("mes"):
        noches = pd.period_range(mes, mes, freq="M")[0]
        dias = noches.days_in_month
        # ventana parcial: primer y ultimo mes se acotan al rango observado
        d0 = max(pd.Timestamp(mes + "-01").date(), df["noche_id"].min())
        d1 = min((pd.Timestamp(mes + "-01") + pd.offsets.MonthEnd(0)).date(), df["noche_id"].max())
        dias = (d1 - d0).days + 1
        for s, gs in g.groupby("Sensor"):
            cub = gs.groupby(["Volcan", "noche_id"]).size()
            filas.append({"mes": mes, "sensor": s, "noches_posibles": dias * len(vols),
                          "noches_con_fila": len(cub), "pct": round(100 * len(cub) / (dias * len(vols)), 1),
                          "filas_por_noche_mediana": float(cub.median()),
                          "filas_por_noche_media": round(float(cub.mean()), 2)})
    t = pd.DataFrame(filas)
    print(f"\n--- {etiqueta}: noches de volcan con >=1 fila NOCTURNA, por mes y sensor "
          f"(denominador = dias observados del mes x {len(vols)} volcanes)")
    print(t.pivot(index="mes", columns="sensor", values="pct"))
    print("\n    filas por noche de volcan (mediana) por mes y sensor")
    print(t.pivot(index="mes", columns="sensor", values="filas_por_noche_mediana"))
    print("\n    filas por noche de volcan (media)")
    print(t.pivot(index="mes", columns="sensor", values="filas_por_noche_media"))
    return t


t = cobertura(cons, "CONSOLIDADO")
madura = t[t["mes"].isin(["2026-06", "2026-07", "2026-08"])].groupby("sensor")["filas_por_noche_media"].mean()
print("\n--- cadencia madura medida (media de filas nocturnas por noche de volcan, jun-ago 2026):")
print(madura.round(2).to_dict())
t["deficit_vs_madura_pct"] = t.apply(lambda r: round(100 * (1 - r["filas_por_noche_media"] / madura[r["sensor"]]), 1), axis=1)
print("\n--- deficit de filas por noche respecto de la cadencia madura (%; negativo = mas que madura)")
print(t.pivot(index="mes", columns="sensor", values="deficit_vs_madura_pct"))

# control positivo
c = cons.copy()
jun = c[c["mes"] == "2026-06"].sample(frac=0.5, random_state=1).index
c2 = c.drop(jun)
n0 = cons[cons["noche"] & (cons["mes"] == "2026-06")].groupby(["Sensor", "Volcan", "noche_id"]).size().groupby("Sensor").size()
n1 = c2[c2["noche"] & (c2["mes"] == "2026-06")].groupby(["Sensor", "Volcan", "noche_id"]).size().groupby("Sensor").size()
print("\nCONTROL: noches con fila en 2026-06 antes/despues de borrar 50 % de las filas:", n0.to_dict(), "->", n1.to_dict())

print("\n=== ALERTAS por mes: consolidado (ALERTA_TERMICA) vs OCR (ALERTA_TERMICA_OCR), por sensor ===")
ca = cons[cons["Tipo_Registro"] == "ALERTA_TERMICA"]
oa = ocr[ocr["Tipo_Registro"] == "ALERTA_TERMICA_OCR"]
x = pd.concat([pd.crosstab(ca["mes"], ca["Sensor"]).add_prefix("CONS_"),
               pd.crosstab(oa["mes"], oa["Sensor"]).add_prefix("OCR_")], axis=1).fillna(0).astype(int)
print(x)
print("\n--- ALERTAS nocturnas (misma tabla, solo noche)")
x = pd.concat([pd.crosstab(ca[ca.noche]["mes"], ca[ca.noche]["Sensor"]).add_prefix("CONS_"),
               pd.crosstab(oa[oa.noche]["mes"], oa[oa.noche]["Sensor"]).add_prefix("OCR_")], axis=1).fillna(0).astype(int)
print(x)

print("\n=== OCR: filas por mes x Version_OCR ===")
print(pd.crosstab(ocr["mes"], ocr["Version_OCR"], margins=True))
print("\n=== OCR: filas por mes x Tipo_Registro ===")
print(pd.crosstab(ocr["mes"], ocr["Tipo_Registro"], margins=True))
print("\n=== OCR: filas por mes x Confianza_Validacion ===")
print(pd.crosstab(ocr["mes"], ocr["Confianza_Validacion"], margins=True))
print("\n=== OCR: Metodo_Validacion x mes ===")
print(pd.crosstab(ocr["Metodo_Validacion"], ocr["mes"]))
print("\n=== OCR: Distancia_km == 0 por mes (0 = 'no medida', F-B2) ===")
print(ocr.groupby("mes").apply(lambda g: f"{(g['Distancia_km']==0).sum()}/{len(g)}"))
print("\n=== OCR: mes de PROCESO (Fecha_Proceso_GitHub) vs mes del satelite: filas escritas retroactivamente ===")
ocr["mes_proc"] = pd.to_datetime(ocr["Fecha_Proceso_GitHub"], errors="coerce").dt.strftime("%Y-%m")
print(pd.crosstab(ocr["mes"], ocr["mes_proc"]))
if "Zenith_Sat_deg" in ocr:
    print("\n=== OCR: columnas V30 pobladas por mes ===")
    print(ocr.groupby("mes").apply(lambda g: {c: int((g[c] != "").sum()) for c in
                                              ("Zenith_Sat_deg", "Nivel_Anomalia_MIROVA")} | {"n": len(g)}))

print("\n=== POSITIVOS: filas por mes x sensor ===")
print(pd.crosstab(pos["mes"], pos["Sensor"], margins=True))

print("\n=== Consolidado: filas con VRP > 0 y Tipo RUTINA (regla vieja, antes del 2026-01-16) ===")
r = cons[(cons["Tipo_Registro"] == "RUTINA") & (cons["VRP_MW"] > 0)]
print(len(r), "filas;", r["dt"].min(), "->", r["dt"].max())
print("\n=== Consolidado: 'Clasificacion Mirova' x Tipo ===")
print(pd.crosstab(cons["Tipo_Registro"], cons["Clasificacion Mirova"]))
print("\n=== Consolidado: max VRP por Tipo ===")
print(cons.groupby("Tipo_Registro")["VRP_MW"].max())
