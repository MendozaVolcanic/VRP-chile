# S159 M: para los records de 2025 cuya publicacion cambia entre A y B, hay fila en el OSF v2.5 de MIROVA?
# OSF = data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv del checkout principal (no versionado). Ojo A105: el
# OSF es filtrado (clase DBSCAN y umbral de VRP por sensor); la ausencia de fila NO es "MIROVA no vio nada".
import csv
import unicodedata
import sys
from datetime import datetime

OSF = sys.argv[1]
CASOS = [("Llaima", "2025-02-15 03:15"), ("Lascar", "2025-05-23 07:25"), ("Lascar", "2025-06-02 07:20"),
         ("Puyehue", "2025-08-03 06:35"), ("Lascar", "2025-03-27 06:20")]
def sin_tilde(x):
    return unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode().lower()


filas = list(csv.DictReader(open(OSF, encoding="utf-8")))
for r in filas:
    r["Volc_Name"] = sin_tilde(r["Volc_Name"])
for v, t in CASOS:
    t0 = datetime.strptime(t, "%Y-%m-%d %H:%M")
    hits = []
    for r in filas:
        if v.lower() not in r["Volc_Name"].lower():
            continue
        tr = datetime.strptime(r["timeUTC"], "%d/%m/%Y %H:%M")
        if abs((tr - t0).total_seconds()) <= 600:
            hits.append((r["timeUTC"], r["Satellite"], r["Resolution"], r["VRP"], r["Max_Dist"], r["class"], r["Npix"]))
    print(v, t, "filas OSF a +-10 min:", hits)

# Control positivo: el buscador encuentra filas donde las hay (Lascar, MODIS 1 km, 2025).
n = [r for r in filas if "lascar" in r["Volc_Name"].lower() and r["Resolution"] == "1000" and "/2025 " in r["timeUTC"]]
print("control: filas OSF de Lascar MODIS en 2025:", len(n), "ejemplo:", (n[0]["timeUTC"], n[0]["VRP"]) if n else None)
