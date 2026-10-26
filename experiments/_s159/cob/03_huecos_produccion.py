# -*- coding: utf-8 -*-
"""COB 03 (S159, VB-4). Records por dia UTC y por sensor, ultimos 45 dias, 11 Tier A, desde el REMOTO (main).

Fuente: data/mirova_equivalent/<vol>.json bajado con `gh api` (contents, raw) a _remoto/ el 2026-10-21 (A86: la
copia local del worktree se atrasa; regla 5 del proyecto). Ventana: 2026-09-07 .. 2026-10-20 (44 dias completos)
+ 2026-10-21 parcial (son las ~18 UTC, no entra a la mediana). Dia = fecha UTC del inicio del granulo.

Pregunta 1: si faltara una familia entera de records (p.ej. NOAA-21), la mediana por sensor lo mostraria como
una fila en 0 todos los dias; se imprime la tabla completa. Pregunta 2: si los JSON no hubieran cargado, la
tabla seria vacia y el script aborta (assert).
Control positivo: los dias 2026-10-13, 18, 19 y 20 estan senalados por la segunda ronda; deben aparecer bajo
el umbral. Control de sensibilidad: el umbral 0,5 x mediana se compara con 0,75 x mediana.
"""
from __future__ import annotations
import json, sys, io
from pathlib import Path
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(r"C:\vrp-trabajo\s159-pruebas\experiments\_s159\cob")
VOLS = ["Lascar", "Chaiten", "PuyehueCordonCaulle", "Lastarria", "Villarrica", "NevadosDeChillan", "Isluga", "Copahue",
        "PlanchonPeteroa", "Llaima", "Tupungatito"]
INI, FIN = pd.Timestamp("2026-09-07"), pd.Timestamp("2026-10-21")


def main():
    rows = []
    for v in VOLS:
        for r in json.load(open(HERE / "_remoto" / f"{v}.json", encoding="utf-8"))["records"]:
            t = pd.Timestamp(r["datetime_utc"])
            if t >= INI:
                rows.append((v, t, r["sensor"], r.get("granule"), r.get("product_version"), r.get("first_processed_utc"), r.get("processed_utc")))
    df = pd.DataFrame(rows, columns=["vol", "t", "sensor", "granule", "pv", "first_proc", "proc"])
    assert len(df) > 0
    df["dia"] = df.t.dt.normalize()
    print("records en ventana:", len(df), "| ultimo record:", df.t.max(), "| volcanes:", df.vol.nunique())
    df.to_csv(HERE / "records_45d.csv", index=False)

    tab = df.groupby(["dia", "sensor"]).size().unstack(fill_value=0)
    tab = tab.reindex(pd.date_range(INI, FIN), fill_value=0)
    tab["TOTAL"] = tab.sum(axis=1)
    pd.set_option("display.width", 250)
    print("\nRecords por dia UTC y sensor (11 Tier A):")
    print(tab.to_string())
    comp = tab.loc[INI:FIN - pd.Timedelta(days=1)]
    med = comp.median()
    print("\nmediana por columna (44 dias completos):")
    print(med.to_string())
    for f in (0.5, 0.75):
        print(f"\nDias/sensores bajo {f} x mediana:")
        bajo = []
        for d, row in comp.iterrows():
            for c in comp.columns:
                if row[c] < f * med[c]:
                    bajo.append((d.date(), c, int(row[c]), float(med[c])))
        for b in bajo:
            print("  ", b)
    print("\nDias con TOTAL bajo 0,5 x mediana:", [str(d.date()) for d, r in comp.iterrows() if r.TOTAL < 0.5 * med.TOTAL])
    print("Dias con TOTAL bajo 0,75 x mediana:", [str(d.date()) for d, r in comp.iterrows() if r.TOTAL < 0.75 * med.TOTAL])
    # por volcan en los dias senalados
    sel = [pd.Timestamp(x) for x in ("2026-10-12", "2026-10-13", "2026-10-14", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20", "2026-10-21")]
    print("\nRecords por volcan y dia (dias de interes):")
    print(df[df.dia.isin(sel)].groupby(["dia", "vol"]).size().unstack(fill_value=0).to_string())
    print("\nproduct_version por dia (dias de interes):")
    print(df[df.dia.isin(sel)].groupby(["dia", "pv"]).size().unstack(fill_value=0).to_string())


if __name__ == "__main__":
    main()
