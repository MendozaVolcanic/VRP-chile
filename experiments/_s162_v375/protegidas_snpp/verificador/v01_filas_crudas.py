# -*- coding: utf-8 -*-
"""VP162 verificador, v01: las 6 filas en el CSV OCR crudo y la tabla (CONS) alrededor, sin pasar por el loader.

Pregunta 1 del instrumento: si la tabla SI trajera la pasada (fila CONS a <=10 min), este script la imprime;
no depende del agrupador de #903 ni del loader. Pregunta 2: si el script estuviera muerto (no leyera las tablas),
no imprimiria las filas CONS de las pasadas vecinas de la misma noche (control positivo: debe ver las 05:24, 06:06...).
Ventana: toda la referencia congelada en la rama medida (snapshot CONS + latest_consolidado + OCR).
"""
import csv, io, sys
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = Path(__file__).resolve().parents[4]
CONS = [R/"data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv", R/"latest_consolidado.csv"]
OCR = R/"data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"
OBJ = [("Tupungatito","2026-08-01 05:00"),("Lascar","2026-08-22 05:06"),("Isluga","2026-09-09 06:06"),
       ("Tupungatito","2026-09-14 06:18"),("Tupungatito","2026-09-28 05:18"),("Tupungatito","2026-09-29 04:54")]
def t(s):
    s=s.strip().replace("T"," ")[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d %H:%M"):
        try: return datetime.strptime(s,fmt)
        except ValueError: pass
    return None
def leer(p):
    with open(p,encoding="utf-8-sig",newline="") as fh: return list(csv.DictReader(fh))
ocr=leer(OCR); cons={str(p.name):leer(p) for p in CONS}
for vol,ts in OBJ:
    t0=datetime.strptime(ts,"%Y-%m-%d %H:%M")
    print(f"\n=== {vol} {ts}")
    for r in ocr:
        if vol.lower() in r["Volcan"].lower().replace(" ","") and r["Sensor"].upper().find("375")>=0:
            tt=t(r["Fecha_Satelite_UTC"])
            if tt and abs(tt-t0)<=timedelta(hours=3):
                print(f"  OCR {r['Fecha_Satelite_UTC']} vrp={r['VRP_MW']} dist={r['Distancia_km']} tipo={r['Tipo_Registro']} conf={r['Confianza_Validacion']} zen={r['Zenith_Sat_deg']} ver={r['Version_OCR']} foto={r['Ruta Foto']} aprox={r['Distancia_aprox_km']} met={r['Distancia_aprox_metodo']}")
    for nom,rows in cons.items():
        cerca=[]
        for r in rows:
            if vol.lower() in r["Volcan"].lower().replace(" ","").replace("-","") and "375" in r["Sensor"]:
                tt=t(r["Fecha_Satelite_UTC"])
                if tt and abs(tt-t0)<=timedelta(hours=3): cerca.append((tt,r))
        for tt,r in sorted(cerca,key=lambda x:x[0]):
            m=(tt-t0).total_seconds()/60
            print(f"  CONS[{nom[:12]}] {r['Fecha_Satelite_UTC']} ({m:+.0f} min) vrp={r['VRP_MW']} dist={r['Distancia_km']} tipo={r['Tipo_Registro']}")
        dentro=[x for x in cerca if abs((x[0]-t0).total_seconds())<=600]
        print(f"  -> CONS[{nom[:12]}] filas a <=10 min de la pasada: {len(dentro)}")
