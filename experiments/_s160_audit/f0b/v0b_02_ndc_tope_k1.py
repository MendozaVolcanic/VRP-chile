# -*- coding: utf-8 -*-
"""F0b S160: los 2 records V750 de Nevados de Chillan donde K1 decide el tope D9 de 5 MW.
Pregunta 1: si el predicado del tablero estuviera roto, el control de identidad de banco_paridad lo diria.
Pregunta 2: si node no corriera, correr_node lanza error (no devuelve vacio).
Simula el tope aplicandolo a mano sobre una COPIA del record (pc.vrp_mw = min(pc, 5.0), vrp_mw idem) para ver
que publicaria el tablero; es una aproximacion: el tope real en el pipeline puede tocar otros campos."""
import sys, io, os, json, copy, csv
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SNAP = Path(r"D:\vrp-trabajo\temporales\s160_audit\main")
sys.path.insert(0, str(SNAP)); sys.path.insert(0, str(SNAP / "scripts"))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp
assert str(bp.HTML).startswith(str(SNAP)), bp.HTML
print("control identidad predicado:", bp.control_identidad_predicado() if hasattr(bp, "control_identidad_predicado") else "no existe")
d = json.load(open(SNAP / "data/mirova_equivalent/NevadosDeChillan.json", encoding="utf-8"))
casos = []
for r in d["records"]:
    if r["datetime_utc"] in ("2026-10-01 06:00", "2026-10-13 05:54") and r["sensor"].endswith("750"):
        casos.append(r)
        c = copy.deepcopy(r)
        c["primary_cluster"]["vrp_mw"] = min(c["primary_cluster"]["vrp_mw"], 5.0)
        c["vrp_mw"] = min(c["vrp_mw"], 5.0)
        c["primary_cluster"]["d9_capped"] = True
        casos.append(c)
INNER = bp.inner_desde_html()["NevadosDeChillan"]
print("inner", INNER)
res = bp.correr_node([[c, INNER] for c in casos])
for c, o in zip(casos, res):
    print(c["datetime_utc"], c["sensor"], "pc", c["primary_cluster"]["vrp_mw"], "->", o)
print("\nMIROVA (tabla sola) misma noche:")
for row in csv.DictReader(open(SNAP / "latest_consolidado.csv", encoding="utf-8")):
    if row["Volcan"].startswith("Nevados") and row["Fecha_Satelite_UTC"][:10] in ("2026-10-01", "2026-10-13") and "VIIRS" in row["Sensor"]:
        print(" ", row["Fecha_Satelite_UTC"], row["Sensor"], row["VRP_MW"], row["Distancia_km"], row["Tipo_Registro"])
print("MIROVA (OCR) misma noche:")
for row in csv.DictReader(open(SNAP / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv", encoding="utf-8")):
    v = row.get("Volcan", "")
    if v.startswith("Nevados") and row.get("Fecha_Satelite_UTC", "")[:10] in ("2026-10-01", "2026-10-13") and "VIIRS" in row.get("Sensor", ""):
        print(" ", row.get("Fecha_Satelite_UTC"), row.get("Sensor"), row.get("VRP_MW"), row.get("Distancia_km"), row.get("Tipo_Registro"))
