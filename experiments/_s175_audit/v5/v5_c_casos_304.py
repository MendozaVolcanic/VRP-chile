# -*- coding: utf-8 -*-
"""V5-C: los 7 casos de acierto sin misma pasada (304): que hay en NUESTROS records de esa noche y volcan, todas las pasadas.
Pregunta 1: si el hallazgo fuera falso (hay record propio en la pasada de MIROVA que SI acierta), esto lo veria: lista toda pasada +-3 h.
Pregunta 2: instrumento muerto -> lista vacia; el control es que cada caso muestra al menos la pasada que el auditor dice (nuestra) y la de MIROVA.
Fuente: data/mirova_equivalent/<vol>.json de la copia 752d348bc (f5/root), filas CONS/OCR del snapshot de la base."""
import json, os, sys, csv
from datetime import datetime
sys.dont_write_bytecode = True
ROOT = r"C:\Users\nmend\vrp-temporales\s175_audit\f5\root"
casos = [("Lascar","2026-10-28"),("PuyehueCordonCaulle","2026-10-10"),("Lastarria","2026-09-04"),("Tupungatito","2026-09-29"),("Lastarria","2026-09-21")]
INS = r"C:\Users\nmend\vrp-temporales\s175_audit\insumos"
cons = list(csv.DictReader(open(os.path.join(INS,"snapshot_consolidado_base.csv"),encoding="utf-8")))
ocr = list(csv.DictReader(open(os.path.join(INS,"snapshot_ocr_base.csv"),encoding="utf-8")))
nom = {"Lascar":"Lascar","PuyehueCordonCaulle":"Puyehue","Lastarria":"Lastarria","Tupungatito":"Tupungatito"}
for vol, fecha in casos:
    print("="*100); print(vol, fecha)
    d = json.load(open(os.path.join(ROOT,"data","mirova_equivalent",vol+".json"),encoding="utf-8"))["records"]
    for r in d:
        if r["datetime_utc"][:10]==fecha or (r["datetime_utc"][:10]==fecha):
            pc = r.get("primary_cluster") or {}
            print("  NUESTRO", r["datetime_utc"], r["sensor"], "pc_vrp", pc.get("vrp_mw"), "pc_dist", pc.get("centroid_dist_km"), "fh_dist", r.get("final_hotspot_dist_km"), "dc", r.get("distance_class"), "via", r.get("via_codigo_mirova"))
    for nm, rows in (("CONS",cons),("OCR",ocr)):
        for x in rows:
            if x["Volcan"].replace(" ","").lower().startswith(nom[vol].lower()[:6]) and x["Fecha_Satelite_UTC"][:10]==fecha:
                print("  MIROVA", nm, x["Fecha_Satelite_UTC"], x["Sensor"], x["Tipo_Registro"], "vrp", x["VRP_MW"], "dist", x["Distancia_km"])
