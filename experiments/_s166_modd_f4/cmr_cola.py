# -*- coding: utf-8 -*-
"""S166 MOD-D fase 4, §4: ¿CMR sirve hoy MOD021KM/MYD021KM y sus MxD03 del 17 al 26 de octubre (D-29 sacó del 17 al
20 porque no los servía)? Cuenta gránulos de 00 a 12 UTC (la noche de Chile) en la caja de los volcanes chilenos, POR
VERSIÓN: 6.1 (estándar, la que pide pipeline/fetch.py primero), 6.1NRT (LANCE, el respaldo) y 7 (Collection 7 de LAADS,
que el pipeline no pide). Sólo lectura, CMR público, sin credenciales. Uso: python cmr_cola.py > cmr_cola_salida.txt"""
import json
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")
print("consultado:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "| caja -76,-46,-66,-17 | 00 a 12 UTC")
print("columnas: producto versión = gránulos")
d = date(2026, 10, 17)
while d <= date(2026, 10, 26):
    fila = []
    for sn in ("MOD021KM", "MOD03", "MYD021KM", "MYD03"):
        for v in ("6.1", "6.1NRT", "7"):
            u = ("https://cmr.earthdata.nasa.gov/search/granules.json?short_name=%s&version=%s"
                 "&temporal=%sT00:00:00Z,%sT12:00:00Z&bounding_box=-76,-46,-66,-17&page_size=200" % (sn, v, d, d))
            fila.append("%s %s=%d" % (sn, v, len(json.load(urllib.request.urlopen(u, timeout=60))["feed"]["entry"])))
    print(d, " ".join(fila))
    d += timedelta(days=1)
