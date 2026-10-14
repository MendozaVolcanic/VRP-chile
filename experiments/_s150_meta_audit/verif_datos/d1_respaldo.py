"""D1: para cada alerta perdida, buscar si existe en otras fuentes (match por volcan, sensor y fecha_satelite +-10 min).
argv: perdidas_ref(antes.csv) despues.csv y luego pares nombre=ruta de fuentes candidatas."""
import sys, pandas as pd
a = pd.read_csv(sys.argv[1], dtype=str); d = pd.read_csv(sys.argv[2], dtype=str)
key = ["Fecha_Satelite_UTC", "Volcan", "Sensor"]
kd = set(map(tuple, d[key].values))
lost = a[[tuple(r) not in kd for r in a[key].values]]
al = lost[lost.Tipo_Registro.str.contains("ALERTA", na=False)].copy()
al["t"] = pd.to_datetime(al.Fecha_Satelite_UTC)
norm = lambda s: s.str.lower().str.replace(r"[^a-z]", "", regex=True)
al["v"] = norm(al.Volcan)
src = {}
for kv in sys.argv[3:]:
    n, p = kv.split("=", 1)
    df = pd.read_csv(p, dtype=str)
    tcol = "Fecha_Satelite_UTC" if "Fecha_Satelite_UTC" in df.columns else df.columns[1]
    df["t"] = pd.to_datetime(df[tcol], errors="coerce"); df["v"] = norm(df["Volcan"]) if "Volcan" in df else ""
    src[n] = df
for _, r in al.iterrows():
    hits = []
    for n, df in src.items():
        m = df[(abs(df.t - r.t) <= pd.Timedelta(minutes=10)) & ((df.v == r.v) | (df.v == ""))]
        if len(m):
            hits.append(f"{n}:{'|'.join(m.get('Sensor', pd.Series(['?']*len(m))).astype(str))}/{'|'.join(m.get('Tipo_Registro', pd.Series(['?']*len(m))).astype(str))}")
    noche = r.t.hour >= 23 or r.t.hour <= 10  # UTC; Chile noche ~ 22-11 UTC aprox
    print(r.Fecha_Satelite_UTC, r.Volcan, r.Sensor, r.VRP_MW, "NOCHE" if noche else "DIA", "->", "; ".join(hits) or "SIN RESPALDO")
