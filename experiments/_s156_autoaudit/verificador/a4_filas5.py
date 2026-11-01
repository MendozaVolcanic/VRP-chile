import csv, sys
for p in ("registro_vrp_ocr.csv","registro_vrp_consolidado.csv"):
    for r in csv.DictReader(open(p,encoding="utf-8")):
        f=r["Fecha_Satelite_UTC"]
        if ("Tupungatito" in r["Volcan"] and f[:16] in ("2026-09-28 05:18","2026-09-29 04:54")) or ("Puyehue" in r["Volcan"] and f[:16]=="2026-10-10 05:54") or ("Chillan" in r["Volcan"] and f[:16] in ("2026-10-12 07:20","2026-10-15 01:05")):
            print(p[:16], {k:r.get(k) for k in ("Fecha_Satelite_UTC","Volcan","Sensor","VRP_MW","Distancia_km","Tipo_Registro","Nota_Validacion","Metodo_Validacion","Nivel_Anomalia_MIROVA","Clasificacion Mirova")})
