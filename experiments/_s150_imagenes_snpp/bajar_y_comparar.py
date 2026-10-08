# -*- coding: utf-8 -*-
"""S150. Baja de Mirova-v1 las imagenes por volcan que respaldan las cinco "alertas solo OCR" de Suomi NPP
que la conectiva `max` pierde (docs/S150_RESULTADO_MESES.md §3) y compara sus md5.

POR QUE: el OCR del scraper le asigna a cada fila la imagen guardada con la hora de esa pasada. Si esa
imagen es en realidad de OTRA pasada, el valor de la fila no describe la pasada que dice. La cabecera de
cada imagen ("Last Update" y el cenit "Zen") dice de que pasada es; este script no lee la cabecera (eso se
hizo mirando las imagenes, docs/S150_IMAGENES_SNPP.md), pero si detecta el caso extremo: dos nombres de
archivo distintos con el mismo contenido.

Uso: python bajar_y_comparar.py [sha_de_Mirova-v1]   (por defecto el usado en S150)
Escribe en imagenes/ junto a este script.
"""
import hashlib, io, sys, urllib.request
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SHA = sys.argv[1] if len(sys.argv) > 1 else "28668309d4d288d1053c8e74e9af543568485530"
BASE = "https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/%s/monitoreo_satelital/imagenes_satelitales/" % SHA
CASOS = ["Lastarria/2026-05-02/05-06-00_Lastarria", "Isluga/2026-05-29/04-54-00_Isluga",
         "Lascar/2026-06-25/04-54-00_Lascar", "Lascar/2026-08-17/05-00-00_Lascar",
         "Lascar/2026-08-22/05-06-00_Lascar",
         "Lascar/2026-08-22/05-24-01_Lascar"]   # la ultima es NOAA-20 de la misma noche, para comparar
out = Path(__file__).resolve().parent / "imagenes"; out.mkdir(exist_ok=True)
vistos = {}
for c in CASOS:
    nombre = c.split("/")[-1] + "_VIIRS375_VRP.png"
    datos = urllib.request.urlopen(BASE + c + "_VIIRS375_VRP.png", timeout=60).read()
    (out / nombre).write_bytes(datos)
    h = hashlib.md5(datos).hexdigest()
    print("%-36s %8d bytes md5 %s%s" % (nombre, len(datos), h, ("  <- MISMO CONTENIDO que " + vistos[h]) if h in vistos else ""))
    vistos.setdefault(h, nombre)
