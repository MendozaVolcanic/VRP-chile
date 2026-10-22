"""V0a (F6-4): filas RUTINA con VRP != 0 en la tabla sola de SHA_MAIN; si MIROVA publicara VRP <= 0 el scraper lo
rotula RUTINA (docs/audit_s139/EJE_1_semantica_etiquetas_referencia.md l. 43: RUTINA es `vrp <= 0`), asi que un
negativo apareceria aqui, no en ALERTA. Pregunta 2: control = debe haber > 0 filas RUTINA con VRP == 0."""
import csv, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
T = r"D:/vrp-trabajo/temporales/s160_audit/main/latest_consolidado.csv"
with open(T, encoding="utf-8", newline="") as fh:
    filas = list(csv.DictReader(fh))
ru = [r for r in filas if r["Tipo_Registro"] == "RUTINA"]
print("RUTINA total", len(ru), "con VRP == 0:", sum(1 for r in ru if float(r["VRP_MW"]) == 0))
for r in ru:
    if float(r["VRP_MW"]) != 0:
        print({k: r[k] for k in ("Fecha_Satelite_UTC", "Volcan", "Sensor", "VRP_MW", "Distancia_km", "Clasificacion Mirova", "Editado")})
