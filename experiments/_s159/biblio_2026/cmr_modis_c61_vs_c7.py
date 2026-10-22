# -*- coding: utf-8 -*-
"""Colecciones MOD021KM/MYD021KM en CMR y ultimo granulo por version sobre Chile.
P1: si C6.1 hubiera dejado de producirse el 2026-09-30 (aviso LAADS 199534), el ultimo granulo 6.1 seria <= esa fecha.
P2: control positivo: la version 6.1NRT y 7 (si existe) devuelven granulos recientes; un HTTP != 200 se imprime."""
import requests, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BBOX = "-76,-46,-66,-17"
for sn in ("MOD021KM", "MYD021KM", "MOD03", "MYD03"):
    r = requests.get("https://cmr.earthdata.nasa.gov/search/collections.json", params={"short_name": sn, "page_size": 20}, timeout=40)
    print(sn, "colecciones:", [(c["version_id"], c.get("data_center")) for c in r.json()["feed"]["entry"]])
for sn, ver in (("MOD021KM","6.1"),("MOD021KM","7"),("MOD021KM","7.0"),("MOD021KM","6.1NRT"),("MYD021KM","6.1"),("MYD021KM","7"),("MYD021KM","6.1NRT")):
    r = requests.get("https://cmr.earthdata.nasa.gov/search/granules.json",
        params={"short_name": sn, "version": ver, "bounding_box": BBOX, "sort_key": "-start_date", "page_size": 1,
                "temporal": "2026-01-01T00:00:00Z,2026-12-31T23:59:59Z"}, timeout=40)
    e = r.json().get("feed", {}).get("entry", [])
    print(sn, ver, "HTTP", r.status_code, "hits", r.headers.get("CMR-Hits"), "ultimo:", e[0]["time_start"] if e else None)
