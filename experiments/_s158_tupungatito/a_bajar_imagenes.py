# -*- coding: utf-8 -*-
"""S158. Baja de Mirova-v1 las imágenes por volcán de Tupungatito (VIIRS 375) de las noches del 2026-09-28 y
2026-09-29 (y de las otras dos protegidas sólo OCR de la serie K, ver CASOS), donde están las dos alertas protegidas que no publicamos en su pasada (05:18 y 04:54), y las de la
otra pasada de cada noche (05:36 y 05:18), y compara sus md5.

POR QUÉ: las dos alertas son «sólo OCR» de Suomi NPP. MIROVA publica UNA imagen viva por volcán y la reemplaza
en cada pasada; el scraper la guarda con la hora de una fila, así que la imagen (y la distancia y la clase que
el OCR lee de ella) pueden ser de otra pasada (memoria reference_ocr_imagen_de_otra_pasada, S150). El VRP de la
fila sí sale de la celda de su hora en Latest10NTI (Mirova-v1#20). La cabecera de cada imagen («Last Update» y
«Zen») dice de qué pasada es; este script no la lee (se lee mirando la imagen, ver README §2), pero detecta el
caso extremo: dos nombres de archivo distintos con el mismo contenido.

Uso: python -I a_bajar_imagenes.py <dir_destino> [sha_de_Mirova-v1]
"""
import hashlib
import io
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
DEST = Path(sys.argv[1])
SHA = sys.argv[2] if len(sys.argv) > 2 else "71ddbffc733b5fb46c0743b3ddc9a6d41f2e96ae"
BASE = ("https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/%s/monitoreo_satelital/"
        "imagenes_satelitales/Tupungatito/" % SHA)
CASOS = ["2026-09-28/05-18-00", "2026-09-28/05-36-01", "2026-09-29/04-54-00", "2026-09-29/05-18-01",
         # g_protegidas.py encontró otras dos protegidas sólo OCR de Suomi NPP en la serie K (2026-08-01 05:00,
         # 1,25 MW; 2026-09-14 06:18, 2,22 MW): sus láminas y las de la pasada siguiente, para leer la serie
         "2026-08-01/05-00-00", "2026-08-01/06-06-02", "2026-09-14/05-00-01", "2026-09-14/05-42-02",
         "2026-09-14/06-18-00", "2026-09-15/05-24-02", "2026-09-15/06-00-00",
         # la lámina del 01-ago 06:06 todavía no trae la pasada de 05:00 (Suomi NPP llega tarde): la siguiente
         # lámina guardada de Tupungatito es del 06-ago
         "2026-08-06/06-48-00"]
TIPOS = ["VRP", "Latest", "Dist", "logVRP"]
DEST.mkdir(parents=True, exist_ok=True)
print(f"Mirova-v1 en {SHA}")
vistos = {}
for c in CASOS:
    for t in TIPOS:
        nombre = c.split("/")[1] + f"_Tupungatito_VIIRS375_{t}.png"
        try:
            datos = urllib.request.urlopen(BASE + c.split("/")[0] + "/" + nombre, timeout=60).read()
        except urllib.error.HTTPError as e:
            print("%-52s no está en Mirova-v1 (%s)" % (nombre, e.code))
            continue
        local = DEST / (c.split("/")[0] + "_" + nombre)
        local.write_bytes(datos)
        h = hashlib.md5(datos).hexdigest()
        igual = vistos.get((t, h))
        print("%-52s %7d bytes md5 %s%s" % (local.name, len(datos), h,
                                             ("  <- MISMO CONTENIDO que " + igual) if igual else ""))
        vistos.setdefault((t, h), local.name)
