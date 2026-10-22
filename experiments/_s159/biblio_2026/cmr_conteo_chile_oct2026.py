# -*- coding: utf-8 -*-
"""Conteo de granulos por dia y coleccion sobre Chile (bbox -76,-46,-66,-17) en CMR, 2026-10-08 a 2026-10-21.
Pregunta 1: si CMR no sirviera un dia, el conteo de ese dia da 0 mientras los vecinos dan >0.
Pregunta 2: control positivo = dias previos al hueco con conteos > 0 en todas las colecciones; si el
instrumento estuviera muerto, todas las filas darian 0 o error HTTP (se imprime).
Denominador: granulos que CMR lista para el bbox y el dia; no mide si el archivo se puede bajar."""
import requests, datetime as dt, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
COLS = [("VNP02IMG","2"),("VNP02IMG_NRT","2"),("VJ102IMG","2.1"),("VJ102IMG_NRT","2.1"),("VJ202IMG","2.1"),("VJ202IMG_NRT","2.1"),
        ("MOD021KM","6.1"),("MOD021KM","6.1NRT"),("MYD021KM","6.1"),("MYD021KM","6.1NRT")]
BBOX = "-76,-46,-66,-17"
d0 = dt.date(2026,10,8)
print("dia        " + " ".join(f"{s[:12]:>12}" for s,_ in COLS))
for i in range(14):
    d = d0 + dt.timedelta(days=i)
    fila = []
    for sn, ver in COLS:
        try:
            r = requests.get("https://cmr.earthdata.nasa.gov/search/granules.json",
                params={"short_name": sn, "version": ver, "bounding_box": BBOX,
                        "temporal": f"{d}T00:00:00Z,{d}T23:59:59Z", "page_size": 1}, timeout=40)
            fila.append(r.headers.get("CMR-Hits", f"HTTP{r.status_code}"))
        except Exception as e:
            fila.append("ERR")
    print(f"{d} " + " ".join(f"{x:>12}" for x in fila))
