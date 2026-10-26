# -*- coding: utf-8 -*-
"""S154, tarea 1.33: razón de magnitud contra MIROVA por pasada en Nevados de Chillán, con el cenit del sensor.

POR QUÉ. Chillán en erupción (2026-10-18): detectamos de noche las mismas pasadas que MIROVA pero con menos magnitud.
Este script deja reproducible la tabla que se mostró a Nicolás (antes vivía sólo en la conversación). La magnitud
nuestra es la que el tablero muestra: el núcleo F5' en VIIRS 375 (f5_core_vrp_mw) y el cúmulo (primary_cluster.vrp_mw)
en MODIS y VIIRS 750 (A10, matiz S132). La de MIROVA sale del consolidado remoto de Mirova-v1 (la tabla latest.php) y,
si la pasada no está ahí, del OCR remoto. La ATRIBUCIÓN de la curva con el cenit (D17 o D25) NO sale de acá: ver
experiments/_s151_presupuesto_magnitud/README.md §3.2, que la deja SIN ATRIBUIR.

Uso: python experiments/_s154_chillan/razon_por_cenit.py [--desde 2026-10-18] [--hasta 2026-10-18]
"""
import argparse
import csv
import io
import json
import subprocess
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
URL = "https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_%s.csv"


def bucket(sensor):
    s = sensor.upper()
    return "MODIS" if "MODIS" in s else ("VIIRS750" if s.endswith("_750") or s == "VIIRS" else "VIIRS375")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2026-10-18")
    ap.add_argument("--hasta", default="2026-10-18")
    a = ap.parse_args()
    ref = {}
    for nombre in ("ocr", "consolidado"):   # el consolidado pisa al OCR
        txt = urllib.request.urlopen(URL % nombre, timeout=60).read().decode("utf-8", "replace")
        for r in csv.DictReader(io.StringIO(txt)):
            if "hill" not in r["Volcan"].lower() or not (a.desde <= r["Fecha_Satelite_UTC"][:10] <= a.hasta):
                continue
            if not r["Tipo_Registro"].startswith("ALERTA"):
                continue
            ref[(r["Fecha_Satelite_UTC"][:16], bucket(r["Sensor"]))] = (float(r["VRP_MW"] or 0), nombre, r["Distancia_km"])
    js = subprocess.run(["git", "show", "origin/main:data/mirova_equivalent/NevadosDeChillan.json"],
                        capture_output=True, encoding="utf-8", check=True).stdout
    print("pasada            sensor    cenit  nuestro  MIROVA  fuente       razon")
    for r in json.loads(js)["records"]:
        t, b = r["datetime_utc"][:16], bucket(r["sensor"])
        if (t, b) not in ref:
            continue
        pc = r.get("primary_cluster") or {}
        nuestro = r.get("f5_core_vrp_mw") if b == "VIIRS375" and r.get("f5_core_vrp_mw") is not None else pc.get("vrp_mw")
        mir, fuente, _ = ref[(t, b)]
        if nuestro is None or not mir:
            continue
        print("%s  %-8s  %5.1f  %7.2f  %6.2f  %-11s  %.2f" % (t, b, r.get("sensor_zenith_deg") or float("nan"),
                                                         nuestro, mir, fuente, nuestro / mir))


if __name__ == "__main__":
    main()
