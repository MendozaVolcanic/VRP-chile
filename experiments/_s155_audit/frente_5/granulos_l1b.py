# -*- coding: utf-8 -*-
"""S155 frente 5: granulos y pixeles que habria que leer en el L1B para cerrar lo que el record no contesta
(siguiente paso para quien orquesta; este script no baja nada). Imprime granulo, satelite, cenit y los pixeles
alertados (lat, lon, BT) de las pasadas elegidas: nadir, intermedia y borde, por sensor, mas las de seleccion."""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
recs = json.load(open(os.path.join(WT, "data/mirova_equivalent/NevadosDeChillan.json"), encoding="utf-8"))["records"]
QUIEN = [("2026-10-18 05:42", "VIIRS_NOAA"), ("2026-10-18 05:42", "_750"), ("2026-10-18 05:06", "VIIRS_NOAA21"),
         ("2026-10-18 05:06", "_750"), ("2026-10-18 06:48", "VIIRS_NOAA21"), ("2026-10-18 06:48", "_750"),
         ("2026-10-10 06:30", "_750"), ("2026-10-16 06:18", "VIIRS"), ("2026-10-16 01:40", "MODIS"),
         ("2026-10-15 07:35", "MODIS"), ("2026-10-12 07:20", "MODIS"), ("2026-10-15 01:05", "MODIS")]
for t, s in QUIEN:
    for r in recs:
        if r["datetime_utc"][:16] == t and s in r["sensor"] and (s != "VIIRS_NOAA" or not r["sensor"].endswith("_750")) \
                and (s != "VIIRS_NOAA21" or not r["sensor"].endswith("_750")) and (s != "VIIRS" or not r["sensor"].endswith("_750")):
            px = ["(%.5f,%.5f,%.1fK)" % (p["lat"], p["lon"], p["bt_k"]) for p in r["anomaly_pixels"]]
            print("%s %s zen=%.1f %s\n    pixeles: %s" % (t, r["sensor"], r["sensor_zenith_deg"], r["granule"], " ".join(px) or "(ninguno)"))
