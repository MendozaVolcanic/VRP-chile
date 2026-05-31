"""S93 — Verificacion reproducible: ¿hay ALERTAS MIROVA confirmadas en pasadas
DIURNAS (elevacion solar > 0) en algun Tier A, rango 2026-05-09 -> 2026-05-30,
con TIF disponible? (pendiente 2.1 BLOQUE_ARRANQUE_S93)

Reescribe el analisis del subagente B (que tenia el signo de elevacion solar
invertido: marco pasadas de madrugada UTC 04-08 = 00-04 local como '+43 diurnas').

Elevacion solar via formula NOAA (sin dependencias externas). Fuente de verdad;
correr y leer stdout. NO commitear data, es scratch verificable (§0.5 integridad).
"""
import math
import os
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TIF_BASE = os.path.normpath(os.path.join(REPO, "..", "mirova-tif-archive", "data", "tif"))

# lat/lon mirova_center de volcanoes.yaml (mirova_monitored: true)
VOLS = {
    "PuyehueCordonCaulle": (-40.59, -72.117),
    "Puyehue-Cordon Caulle": (-40.59, -72.117),
    "Villarrica": (-39.42, -71.93),
    "Lascar": (-23.369, -67.732),
    "Copahue": (-37.856, -71.183),
    "NevadosDeChillan": (-36.863, -71.377),
    "Nevados de Chillan": (-36.863, -71.377),
    "Llaima": (-38.692, -71.729),
    "Chaiten": (-42.833, -72.646),
    "PlanchonPeteroa": (-35.24, -70.568),
    "Lastarria": (-25.168, -68.507),
    "Isluga": (-19.15, -68.83),
    "Tupungatito": (-33.4, -69.8),
}
# nombre de carpeta TIF por volcan (canonico repo)
TIF_DIR = {
    "PuyehueCordonCaulle": "PuyehueCordonCaulle", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
    "Villarrica": "Villarrica", "Lascar": "Lascar", "Copahue": "Copahue",
    "NevadosDeChillan": "NevadosDeChillan", "Nevados de Chillan": "NevadosDeChillan",
    "Llaima": "Llaima", "Chaiten": "Chaiten", "PlanchonPeteroa": "PlanchonPeteroa",
    "Lastarria": "Lastarria", "Isluga": "Isluga", "Tupungatito": "Tupungatito",
}


def solar_elevation(dt_utc, lat, lon):
    """Elevacion solar (grados) via algoritmo NOAA simplificado. dt_utc naive=UTC."""
    # dia juliano fraccional
    import datetime
    jd = dt_utc.toordinal() + 1721424.5 + (dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600)/24.0
    n = jd - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360          # longitud media (deg)
    g = math.radians((357.528 + 0.9856003 * n) % 360)  # anomalia media
    lam = math.radians(L + 1.915*math.sin(g) + 0.020*math.sin(2*g))  # long ecliptica
    eps = math.radians(23.439 - 0.0000004 * n)   # oblicuidad
    dec = math.asin(math.sin(eps)*math.sin(lam)) # declinacion
    # tiempo sideral / angulo horario
    gmst = (280.46061837 + 360.98564736629 * n) % 360
    lmst = (gmst + lon) % 360
    ra = math.degrees(math.atan2(math.cos(eps)*math.sin(lam), math.cos(lam))) % 360
    H = math.radians((lmst - ra) % 360)
    latr = math.radians(lat)
    elev = math.asin(math.sin(latr)*math.sin(dec) + math.cos(latr)*math.cos(dec)*math.cos(H))
    return math.degrees(elev)


def load(path, tipo):
    df = pd.read_csv(path)
    df = df[df["Tipo_Registro"] == tipo].copy()
    df["utc"] = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce")
    df = df.dropna(subset=["utc"])
    m = (df["utc"] >= "2026-05-09") & (df["utc"] <= "2026-05-30 23:59:59")
    df = df[m & df["Volcan"].isin(VOLS.keys())].copy()
    df["fuente"] = tipo
    return df


cons = load(os.path.join(REPO, "latest_consolidado.csv"), "ALERTA_TERMICA")
ocr = load(os.path.join(REPO, "data/mirova_reference/registro_vrp_ocr.csv"), "ALERTA_TERMICA_OCR")
al = pd.concat([cons, ocr], ignore_index=True)

# VRP > 0 (alerta significativa)
al["VRP_MW"] = pd.to_numeric(al["VRP_MW"], errors="coerce")
al = al[al["VRP_MW"] > 0].copy()

# elevacion solar
elevs = []
for _, r in al.iterrows():
    lat, lon = VOLS[r["Volcan"]]
    elevs.append(solar_elevation(r["utc"].to_pydatetime(), lat, lon))
al["sun_elev"] = elevs
al["diurna"] = al["sun_elev"] > 0

print("=" * 70)
print(f"ALERTAS Tier A (VRP>0) en 2026-05-09 -> 2026-05-30: {len(al)}")
print(f"  CONS: {(al.fuente=='ALERTA_TERMICA').sum()}  OCR: {(al.fuente=='ALERTA_TERMICA_OCR').sum()}")
print(f"  DIURNAS (elev>0): {al.diurna.sum()}   NOCTURNAS: {(~al.diurna).sum()}")
print("=" * 70)

# sanity: rango de elev por hora local para validar el calculo
print("\nSanity check (elev solar por hora UTC, deberia ser <0 en UTC 04-08):")
chk = al.groupby(al.utc.dt.hour)["sun_elev"].agg(["min", "max", "count"])
print(chk)

# corte ventana-con-TIF (archivo MIROVA cubre 2026-05-09 -> 2026-05-20)
tif_win = (al["utc"] >= "2026-05-09") & (al["utc"] <= "2026-05-20 23:59:59")
print("\n=== CORTE VENTANA-CON-TIF (2026-05-09 -> 2026-05-20) ===")
print(f"  Alertas Tier A VRP>0 en ventana TIF: {tif_win.sum()}")
print(f"  de esas, DIURNAS (elev>0): {al[tif_win].diurna.sum()}")

diurnas = al[al.diurna].copy()
if len(diurnas):
    print(f"\n--- {len(diurnas)} ALERTAS DIURNAS ---")
    diurnas = diurnas.sort_values("sun_elev", ascending=False)
    for _, r in diurnas.iterrows():
        tdir = os.path.join(TIF_BASE, TIF_DIR.get(r["Volcan"], r["Volcan"]))
        datestr = r["utc"].strftime("%Y%m%d")
        tif = "NO-DIR"
        if os.path.isdir(tdir):
            hits = [f for f in os.listdir(tdir) if datestr in f]
            tif = f"{len(hits)} TIF" if hits else "sin TIF fecha"
        print(f"  {r['utc']} UTC | {r['Volcan']:24s} | {r['Sensor']:12s} | "
              f"VRP={r['VRP_MW']:7.2f} | elev={r['sun_elev']:+5.1f} | {r['fuente']:18s} | {tif}")
else:
    print("\n>>> 0 ALERTAS DIURNAS — no hay material para validar deteccion diurna.")
