"""s1: audita Fecha_Captura_Chile y timestamp contra Fecha_Satelite_UTC.
Hora oficial: zoneinfo America/Santiago (tzdata). Uso: python s1_hora_chile.py cons.csv ocr.csv"""
import sys, io, collections
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
Z = ZoneInfo("America/Santiago")
import tzdata
print("tzdata", tzdata.IANA_VERSION)

# transiciones de la zona en el rango de datos
t = datetime(2024, 1, 1, tzinfo=timezone.utc); prev = t.astimezone(Z).utcoffset()
print("Transiciones America/Santiago (UTC del instante del cambio):")
while t < datetime(2027, 1, 1, tzinfo=timezone.utc):
    o = t.astimezone(Z).utcoffset()
    if o != prev:
        print(f"  {t:%Y-%m-%d %H:%M} UTC  {prev.total_seconds()/3600:+.0f} -> {o.total_seconds()/3600:+.0f}")
        prev = o
    t += timedelta(minutes=15)

for path in sys.argv[1:]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    print(f"\n===== {path}: {len(df)} filas")
    utc = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce", format="%Y-%m-%d %H:%M:%S")
    cl = pd.to_datetime(df["Fecha_Captura_Chile"], errors="coerce", format="%Y-%m-%d %H:%M:%S")
    print("  UTC ilegibles:", utc.isna().sum(), " Chile ilegibles:", cl.isna().sum())
    # 3. timestamp
    ts = pd.to_numeric(df["timestamp"], errors="coerce")
    epoch = (utc - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)
    d = ts - epoch
    print("  timestamp == epoch(Fecha_Satelite_UTC):", int((d == 0).sum()), "de", len(df),
          "| distintas:", int((d != 0).sum()), "| valores de diferencia:", dict(collections.Counter(d[d != 0].dropna().astype(int)).most_common(5)))
    # 1. hora de Chile
    oficial = utc.dt.tz_localize("UTC").dt.tz_convert(Z).dt.tz_localize(None)
    off_ofi = ((oficial - utc) / pd.Timedelta(hours=1))
    off_csv = ((cl - utc) / pd.Timedelta(hours=1))
    err = ((cl - oficial) / pd.Timedelta(hours=1))
    df2 = pd.DataFrame({"mes": utc.dt.strftime("%Y-%m"), "off_ofi": off_ofi, "off_csv": off_csv, "err": err,
                        "utc": utc, "Tipo": df["Tipo_Registro"]})
    print("  desfase aplicado por el CSV (h):", dict(collections.Counter(off_csv.dropna())))
    print("  error (CSV - oficial) en h:", dict(collections.Counter(err.dropna())))
    tab = df2.groupby(["mes", "off_ofi", "off_csv"]).size().unstack("off_csv", fill_value=0)
    print("  filas por mes x desfase oficial (fila) x desfase del CSV (columna):")
    print(tab.to_string())
    malas = df2[df2.err != 0]
    if len(malas):
        print("  FILAS MAL por mes y sentido (err>0: CSV adelantado; err<0: atrasado):")
        print(malas.groupby(["mes", "err"]).size().to_string())
        print("  rango UTC de las malas:", malas.utc.min(), "->", malas.utc.max())
    # dias de cambio de horario: filas dentro de +-36 h de cada transición
    for tr in ["2025-04-06 03:00", "2025-09-07 04:00", "2026-04-05 03:00", "2026-09-06 04:00"]:
        T = pd.Timestamp(tr)
        w = df2[(df2.utc > T - pd.Timedelta(hours=36)) & (df2.utc < T + pd.Timedelta(hours=36))]
        if len(w):
            print(f"  ventana +-36 h de {tr} UTC: {len(w)} filas, mal {int((w.err != 0).sum())};"
                  f" antes del cambio offsets {sorted(set(w[w.utc < T].off_csv))}, despues {sorted(set(w[w.utc >= T].off_csv))}")
            x = w.sort_values("utc")
            near = x[(x.utc > T - pd.Timedelta(hours=6)) & (x.utc < T + pd.Timedelta(hours=6))]
            for _, r in near.drop_duplicates("utc").iterrows():
                print(f"     {r.utc}  csv{r.off_csv:+.0f}  oficial{r.off_ofi:+.0f}")
