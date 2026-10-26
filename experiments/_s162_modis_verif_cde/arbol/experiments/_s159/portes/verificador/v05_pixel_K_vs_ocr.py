# -*- coding: utf-8 -*-
"""v05: alternativa a la explicación post hoc. ¿La distancia del OCR de las protegidas «perdidas» coincide con un
píxel que PRODUCCIÓN (K) sí ve y el port no? Si coincide, la fila OCR sería de su propia pasada y el port perdería
un píxel débil de verdad; si no, sigue en pie «distancia de otra pasada».
Distancias de los píxeles de K (anomaly_pixels del record publicado, data_main 533398f8f) medidas al MISMO punto que
usa MIROVA y el port (X0, Y0 de la grilla), no al cráter.
Control: las alertas de la TABLA de las mismas pasadas tipo (Tupungatito, Isluga) deben calzar con algún píxel de K.
Pregunta 2: record sin anomaly_pixels = SIN DATO."""
import json
from pathlib import Path
import numpy as np
from pyproj import Transformer
PORTES = Path(r"C:/vrp-trabajo/s159-n/experiments/_s159/portes")
DATA = Path(r"D:/vrp-trabajo/temporales/s159_n/data_main")
ART = Path(r"D:/vrp-trabajo/temporales/s159_portes/run_39712862945")
obj = {o["id"]: o for o in json.loads((PORTES / "objetivos_portes.json").read_text(encoding="utf-8"))}
res = {}
for f in sorted(ART.rglob("resultados_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r.get("estado") == "ok": res[r["id"]] = r
cache = {}
def recs(v):
    if v not in cache:
        cache[v] = {(r["sensor"], r["datetime_utc"]): r for r in json.loads((DATA / f"{v}.json").read_text(encoding="utf-8"))["records"]}
    return cache[v]
ids_dud = [228, 279, 288, 289, 293, 298, 294, 295, 285, 282, 284]
ids_ctl = [i for i, o in obj.items() if o["b"] == "VIIRS375" and o["lab"] == "pos" and o["volcan"] in ("Tupungatito", "Isluga", "Lascar")
           and any(f["source"] == "CONS" for f in o["mirova"])]
for nombre, ids in (("filas solo OCR (las 6 perdidas + 5 que K no publica)", ids_dud), ("control: alertas de la TABLA, mismos volcanes", ids_ctl)):
    print("==", nombre)
    calza = n = 0
    for i in ids:
        o = obj[i]; g = o["grilla"]
        t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
        r = recs(o["volcan"]).get((o["sensor"], o["hora_utc"]))
        ap = (r or {}).get("anomaly_pixels") or []
        if not ap:
            print("  ", i, o["volcan"], o["hora_utc"], "SIN DATO (sin anomaly_pixels)"); continue
        dK = []
        for q in ap:
            x, y = t.transform(q["lon"], q["lat"])
            dK.append((round(float(np.hypot(x - g["X0"], y - g["Y0"]) / 1000), 2), q["vrp_mw"]))
        dK.sort()
        al = [f for f in o["mirova"] if f["tipo"].startswith("ALERTA")]
        dm = [f["dist_km"] for f in al if (f["source"] == "OCR") == (nombre.startswith("filas"))]
        if not dm: continue
        port = sorted(q[3] for q in res[i]["port"]["sensible"]["pixeles"]) if i in res else []
        hit = any(abs(d - k[0]) <= 1.0 for d in dm for k in dK)
        calza += hit; n += 1
        print(f"   {i} {o['volcan'][:11]} {o['hora_utc']} {o['sensor']}: MIROVA {dm} | K px (dist a X0Y0, MW) {dK[:5]} | port sensible {port[:3]} -> {'CALZA K' if hit else 'no'}")
    print(f"   calza con algún píxel de K (<=1 km): {calza} de {n}")
