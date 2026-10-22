# -*- coding: utf-8 -*-
"""V08 (verificador S160 espacial): afirmacion 5 (E-04, E-08). Sobre el CSV 02b del auditor (reproducido byte a byte en
rerun/), lista los TIF cuyo foco cae en la celda 0,02 grados de la fuente a 10,7 km al E del vent de PCC, con fecha,
hora, etiqueta, prominencia y posicion exacta; cuenta fechas distintas (A106: imagenes repetidas bajo otra hora) y mira si
nuestros records (VIIRS 375, misma hora +-15 min) tienen algun pixel anomalo a <= 1 km de esa posicion.
Control: la misma cuenta en la celda del crater de PCC. P2: n impreso.
"""
import csv, io, json, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from pyproj import Geod
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
AUD = AQUI.parent
G = Geod(ellps="WGS84")
VENT = (-40.525499, -72.146137)
F = [r for r in csv.DictReader(open(AUD / "02b_tif_v375_focos.csv", encoding="utf-8")) if r["vol"] == "PuyehueCordonCaulle"]
recs = [r for r in json.load(open(AUD / "data" / "PuyehueCordonCaulle.json", encoding="utf-8"))["records"]
        if (r.get("sensor") or "").startswith("VIIRS") and not r["sensor"].endswith("_750")]
def d(a, b):
    return G.inv(a[1], a[0], b[1], b[0])[2] / 1000
for nombre, celda in (("fuente E", (-40.52, -72.02)), ("crater (control)", (-40.52, -72.14))):
    sel = [r for r in F if round(float(r["lat"]) / 0.02) * 0.02 == celda[0] and abs(round(float(r["lon"]) / 0.02) * 0.02 - celda[1]) < 1e-9]
    print(f"\n== {nombre}: celda {celda}: {len(sel)} TIF; etiquetas {dict(Counter(r['mir_tipo'] or 'sin fila' for r in sel))}; "
          f"fechas distintas {len(set(r['t'][:10] for r in sel))}; posiciones exactas distintas {len(set((r['lat'], r['lon']) for r in sel))}")
    if not sel:
        continue
    lat0 = median(float(r["lat"]) for r in sel); lon0 = median(float(r["lon"]) for r in sel)
    print(f"   posicion mediana {lat0:.4f}, {lon0:.4f}: a {d((lat0, lon0), VENT):.2f} km del vent; dispersion (p50 de la distancia a la mediana) "
          f"{median(d((float(r['lat']), float(r['lon'])), (lat0, lon0)) for r in sel):.2f} km")
    con = 0
    for r in sel:
        t = datetime.strptime(r["t"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        rr = [x for x in recs if abs((datetime.strptime(x["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) - t).total_seconds()) <= 900]
        hit = any(d((p["lat"], p["lon"]), (float(r["lat"]), float(r["lon"]))) <= 1 for x in rr for p in (x.get("anomaly_pixels") or []) if p.get("lat") is not None)
        con += hit
        if nombre.startswith("fuente"):
            print(f"   {r['t']} {r['mir_tipo'] or 'sin fila':18s} prom {float(r['res_sigma']):5.1f} sigma, bt_max {float(r['bt_max']):.1f} K, "
                  f"{float(r['lat']):.4f},{float(r['lon']):.4f}; record nuestro a +-15 min: {len(rr)}, con pixel anomalo a <= 1 km: {hit}")
    print(f"   TIF con pixel anomalo nuestro a <= 1 km del foco (misma pasada +-15 min): {con} de {len(sel)}")
