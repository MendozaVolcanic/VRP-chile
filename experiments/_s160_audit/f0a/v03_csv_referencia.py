"""V0a (verificador de F6-3 y F6-4): alertas de MIROVA por sensor en las DOS referencias congeladas de SHA_MAIN
(tabla sola = latest_consolidado.csv; combinado = tabla + registro_vrp_ocr.csv del snapshot): n, minimo, <= 0, < 5 MW.
Camino distinto al de m13 de S158: dos referencias (no una), ventana declarada, y se mira ademas si alguna fila
de cualquier tipo trae VRP negativo, y la RUTINA con VRP != 0.
Pregunta 1: si MIROVA publicara VRP <= 0 y el scraper lo guardara, aparece en '<= 0'. Si el scraper lo filtra, no:
eso NO lo distingue este script (lo dice el informe).
Pregunta 2: control positivo = las RUTINA traen VRP 0 por construccion (debe salir > 0 filas con VRP == 0 en RUTINA);
y el filtro de tipo distingue ALERTA de RUTINA (conteos distintos).
"""
import csv, hashlib, io, sys, statistics, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = r"D:/vrp-trabajo/temporales/s160_audit/main/"
T = ROOT + "latest_consolidado.csv"
O = ROOT + "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"
for p in (T, O):
    print(p.split("/")[-1], "sha256", hashlib.sha256(open(p, "rb").read()).hexdigest()[:16])

def leer(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))
tab = leer(T); ocr = leer(O)
print("filas tabla", len(tab), "filas ocr", len(ocr))
print("tipos tabla:", collections.Counter(r["Tipo_Registro"] for r in tab).most_common())
print("tipos ocr:", collections.Counter(r["Tipo_Registro"] for r in ocr).most_common())

def vrp(r):
    try:
        return float(r["VRP_MW"])
    except (ValueError, KeyError):
        return None

def resumen(filas, nombre):
    fechas = [r["Fecha_Satelite_UTC"] for r in filas if r.get("Fecha_Satelite_UTC")]
    print(f"\n[{nombre}] ventana {min(fechas)} -> {max(fechas)}")
    for sensor in ("VIIRS", "VIIRS375", "MODIS"):
        al = [vrp(r) for r in filas if r["Sensor"] == sensor and r["Tipo_Registro"].startswith("ALERTA")]
        al = [v for v in al if v is not None]
        if not al:
            print(f"  {sensor}: 0 alertas"); continue
        print(f"  {sensor} alertas={len(al)} min={min(al):.3f} <=0: {sum(1 for v in al if v <= 0)} <5: {sum(1 for v in al if v < 5)} mediana={statistics.median(al):.2f}")
        ru = [vrp(r) for r in filas if r["Sensor"] == sensor and r["Tipo_Registro"] == "RUTINA"]
        ru = [v for v in ru if v is not None]
        print(f"     RUTINA n={len(ru)} con VRP==0: {sum(1 for v in ru if v == 0)} con VRP!=0: {sum(1 for v in ru if v != 0)}")
    neg = [(r["Fecha_Satelite_UTC"], r["Volcan"], r["Sensor"], r["Tipo_Registro"], r["VRP_MW"]) for r in filas if (vrp(r) or 0) < 0]
    print("  filas de cualquier tipo con VRP < 0:", len(neg), neg[:5])
    vac = sum(1 for r in filas if vrp(r) is None)
    print("  filas con VRP vacio o no numerico:", vac)

resumen(tab, "tabla sola")
resumen(tab + ocr, "combinado tabla + OCR")
resumen(ocr, "solo OCR")
