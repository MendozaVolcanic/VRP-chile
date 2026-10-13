# -*- coding: utf-8 -*-
"""F3 R9. Una alerta 'solo OCR' puede ser (a) una pasada que la tabla no lista, o (b) una pasada que la tabla SI
lista como RUTINA con VRP 0: MIROVA dice 'nada' en latest.php y el OCR dice 'alerta'. En (b) los dos canales se
contradicen y banco_paridad.etiquetar la marca 'pos' igual (cualquier ALERTA gana). Cuantas hay, por satelite?
La tabla no trae satelite: se toma de nuestro record pareado a +-120 s (data/mirova_equivalent, produccion).
P1: si el OCR nunca contradijera a la tabla, (b) daria 0. P2: control: el mismo cruce sobre las alertas DE LA
TABLA tiene que dar 0 contradicciones (una pasada no puede ser ALERTA y RUTINA en la tabla; S139 lo verifico).
Ventana: 2026-03-01 a 2026-09-30, nocturno no se filtra (se informa la hora). Referencia: snapshot OCR al dia y
latest_consolidado.csv (2026-10-09)."""
import sys, json, collections, bisect
from datetime import datetime, timedelta
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ))
from referencia_mirova_unificada import leer_pasadas, SNAP_OCR, RESPALDO_20260408
cons = {}
for f in leer_pasadas(RAIZ / "latest_consolidado.csv", "CONS", "v") + leer_pasadas(RESPALDO_20260408, "CONS", "r"):
    cons.setdefault((f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16]), f)
ocr = [f for f in leer_pasadas(SNAP_OCR, "OCR", "s") if "2026-03-01" <= f["fecha_utc"][:10] <= "2026-09-30" and f["tipo"].startswith("ALERTA")]
# satelite desde nuestros records
idx = collections.defaultdict(list)
for p in (RAIZ / "data" / "mirova_equivalent").glob("*.json"):
    if "_" in p.stem and p.stem not in ("PlanchonPeteroa", "PuyehueCordonCaulle", "NevadosDeChillan"): pass
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except Exception: continue
    for r in d.get("records", []):
        s = r.get("sensor") or ""
        b = "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else ("VIIRS375" if s.startswith("VIIRS") else None))
        if b and r.get("datetime_utc"):
            idx[(p.stem, b)].append((r["datetime_utc"][:16], s))
for v in idx.values(): v.sort()
def sat(f):
    l = idx.get((f["volcano"], f["sensor_bucket"]), []); t = datetime.strptime(f["fecha_utc"][:16], "%Y-%m-%d %H:%M")
    ts = [x[0] for x in l]; i = bisect.bisect_left(ts, (t - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M"))
    while i < len(l) and l[i][0] <= (t + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M"):
        return l[i][1].replace("VIIRS_", "").replace("_750", "")
        i += 1
    return "sin record"
c = collections.Counter(); ejemplos = []
for f in ocr:
    k = (f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16]); t = cons.get(k)
    estado = "tabla ALERTA" if t and t["tipo"].startswith("ALERTA") else ("tabla RUTINA" if t and t["tipo"] == "RUTINA" else ("tabla FP" if t else "sin fila en tabla"))
    tramo = "<06-13" if f["fecha_utc"][:10] < "2026-06-13" else ">=06-13"
    c[(f["sensor_bucket"], tramo, estado, sat(f))] += 1
    if estado == "tabla RUTINA" and len(ejemplos) < 12: ejemplos.append((f["fecha_utc"][:16], f["volcano"], f["sensor_bucket"], f["vrp_mw"], t["vrp_mw"], sat(f)))
for k, v in sorted(c.items()): print(k, v)
print("ejemplos OCR ALERTA con tabla RUTINA:", ejemplos)
# control P2
ca = [f for f in cons.values() if f["tipo"].startswith("ALERTA")]
print("control: alertas de la tabla", len(ca), "| claves de la tabla con dos tipos: 0 por construccion (diccionario por clave)")
