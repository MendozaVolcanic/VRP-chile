"""s5: (a) zona de Fecha_Proceso_GitHub del OCR contra la hora de los commits de registro_vrp_ocr.csv;
(b) filas con Fecha_Proceso/Ultima en la hora ambigua o inexistente de America/Santiago;
(c) filas cuya pasada y proceso caen a distinto lado de un cambio de hora (una resta de dos horas
locales ingenuas se equivoca en 1 h ahi); (d) pasadas con hora local 16 (borde del 'diurno 10-15' de s114).
Uso: python s5_ocr_y_ambiguas.py cons.csv ocr.csv"""
import sys, io, json, subprocess, bisect
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
Z = ZoneInfo("America/Santiago")
cons, ocr = pd.read_csv(sys.argv[1]), pd.read_csv(sys.argv[2])

# (a)
r = subprocess.run(["gh", "api", "repos/MendozaVolcanic/Mirova-v1/commits?path=monitoreo_satelital/registro_vrp_ocr.csv"
                    "&since=2026-09-15T00:00:00Z&per_page=100", "--paginate", "--jq", ".[].commit.committer.date"],
                   capture_output=True, text=True)
C = sorted(datetime.fromisoformat(x.replace("Z", "+00:00")) for x in r.stdout.split())
print("(a) commits OCR desde 2026-09-15:", len(C))
fp = sorted(set(ocr.Fecha_Proceso_GitHub.dropna()))
fp = [f for f in fp if f >= "2026-09-15"]
for hip in ["Santiago", "UTC"]:
    ds = []
    for f in fp:
        t = datetime.strptime(f, "%Y-%m-%d %H:%M:%S").replace(tzinfo=Z if hip == "Santiago" else timezone.utc)
        i = bisect.bisect_left(C, t)
        if i < len(C): ds.append((C[i] - t).total_seconds() / 60)
    ds.sort()
    print(f"   hipotesis {hip}: commit siguiente - Fecha_Proceso (min) n={len(ds)} mediana {ds[len(ds)//2]:.1f} max {ds[-1]:.1f}; <=10 min: {sum(x <= 10 for x in ds)}")

# (b)
def clase(s):
    try:
        t = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return "ilegible"
    a = t.replace(tzinfo=Z, fold=0).utcoffset(); b = t.replace(tzinfo=Z, fold=1).utcoffset()
    if a != b:
        # inexistente si el ida y vuelta no conserva la hora
        rt = t.replace(tzinfo=Z).astimezone(timezone.utc).astimezone(Z).replace(tzinfo=None)
        return "inexistente" if rt != t else "ambigua"
    return "ok"
for nom, df in [("cons", cons), ("ocr", ocr)]:
    for col in ["Fecha_Proceso_GitHub", "Ultima_Actualizacion", "Fecha_Captura_Chile"]:
        c = df[col].astype(str).map(clase).value_counts().to_dict()
        print(f"(b) {nom} {col}: {c}")
        amb = df[df[col].astype(str).map(clase).isin(["ambigua", "inexistente"])]
        if len(amb):
            print("     ejemplos:", amb[[col, "Fecha_Satelite_UTC"]].head(3).values.tolist())

# (c)
for nom, df in [("cons", cons), ("ocr", ocr)]:
    u = pd.to_datetime(df.Fecha_Satelite_UTC).dt.tz_localize("UTC")
    p = pd.to_datetime(df.Fecha_Proceso_GitHub, errors="coerce").dt.tz_localize(Z, ambiguous="NaT", nonexistent="NaT")
    off_u = u.dt.tz_convert(Z).map(lambda t: t.utcoffset())
    off_p = p.map(lambda t: t.utcoffset() if not pd.isna(t) else None)
    cruza = (off_u != off_p) & p.notna()
    print(f"(c) {nom}: filas con pasada y proceso en distinto horario: {int(cruza.sum())}")

# (d)
for nom, df in [("cons", cons), ("ocr", ocr)]:
    h = pd.to_datetime(df.Fecha_Captura_Chile).dt.hour
    u = pd.to_datetime(df.Fecha_Satelite_UTC)
    dia_utc = (u.dt.hour >= 11)
    print(f"(d) {nom}: pasadas diurnas (UTC>=11h) por hora local: {h[dia_utc].value_counts().sort_index().to_dict()}")
    print(f"    {nom}: diurnas con hora local 16 o mas (s114 las trata como nocturnas): {int((dia_utc & (h >= 16)).sum())}; "
          f"por sensor {df[dia_utc & (h >= 16)].Sensor.value_counts().to_dict()}")
