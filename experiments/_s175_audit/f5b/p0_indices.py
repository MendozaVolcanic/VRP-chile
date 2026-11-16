# -*- coding: utf-8 -*-
"""P0: para cada caso de validación de F5, buscar en los índices del archivo (copias en insumos) el TIF y las láminas
Latest10NTI del mismo volcán y sensor con last_modified alrededor de la pasada. Salida: p0_indices.out.txt (stdout)."""
import csv, sys, datetime as dt
sys.stdout.reconfigure(encoding="utf-8")
INS = r"C:\Users\nmend\vrp-temporales\s175_audit\insumos"
CASOS = [("Lastarria","VIIRS375","2026-06-12 05:54"),("Lastarria","VIIRS375","2026-08-09 05:48"),
         ("Lascar","VIIRS750","2026-06-21 05:30"),("Isluga","VIIRS375","2026-09-22 05:42")]
tif = list(csv.DictReader(open(INS+r"\tif_index.csv", encoding="utf-8")))
png = [r for r in csv.DictReader(open(INS+r"\png_index.csv", encoding="utf-8")) if r["kind"]=="Latest10NTI"]
P = lambda s: dt.datetime.fromisoformat(s.replace("Z","+00:00")).replace(tzinfo=None)
for vol,sen,hora in CASOS:
    t0 = dt.datetime.strptime(hora,"%Y-%m-%d %H:%M")
    print("=====",vol,sen,hora)
    for r in tif:
        if r["volcano"]==vol and r["sensor"]==sen and abs((P(r["last_modified_utc"])-t0).total_seconds())<12*3600:
            print(" TIF", r["acquisition_utc"], r["last_modified_utc"], r["md5"], r["tif_path"])
    for r in png:
        if r["volcano"]==vol and r["sensor"]==sen and -3*3600 < (P(r["last_modified_utc"])-t0).total_seconds() < 30*3600:
            print(" PNG", r["last_modified_utc"], r["md5"][:8], r["size_bytes"], r["png_path"], r["omitido"])
