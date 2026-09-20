# -*- coding: utf-8 -*-
"""V-17: cruce independiente de data/clasificacion_referencia/ contra la referencia cruda (mi loader, sin banco_paridad).
Preguntas: (a) 'no_reference' es de verdad 'MIROVA no listo la pasada'? (b) 'mirova_silent' despues del corte del OCR (2026-09-14 06:42) es de fiar?
(c) 'mirova_confirmed' tiene siempre una ALERTA a +-2 min? (control positivo del cruce: debe dar ~100 %; si diera 0 mi pareo estaria roto).
(1) roto? (c) lo delata. (2) muerto? se imprimen n por valor y deben sumar 2285."""
import io, sys, json, datetime as dt
from collections import Counter, defaultdict
from vlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REF = defaultdict(list)
for f in referencia():
    REF[(f["vol"], f["b"])].append((dt.datetime.fromisoformat(f["dt"]), f["tipo"], f["fuente"], f["vrp"]))
CORTE_OCR = dt.datetime(2026, 9, 14, 6, 42, 1)
tot = Counter(); det = defaultdict(Counter)
for v in VOLS:
    d = json.load(open(os.path.join(ROOT, "data", "clasificacion_referencia", v + ".json"), encoding="utf-8"))["clasificacion"]
    for clave, e in d.items():
        t, s = clave.split("|"); T = dt.datetime.fromisoformat(t); b = bucket(s); val = e["valor"]; tot[val] += 1
        cerca = [x for x in REF.get((v, b), []) if abs((x[0] - T).total_seconds()) <= 120]
        tipos = {x[1] for x in cerca}
        det[val]["con ALERTA a +-2min" if any(x.startswith("ALERTA") for x in tipos) else "con FALSO_POSITIVO a +-2min" if any(x.startswith("FALSO") for x in tipos) else "solo RUTINA a +-2min" if tipos else "sin ninguna fila a +-2min"] += 1
        if val == "mirova_silent": det["silent por sensor y corte OCR"][(b, "despues del corte OCR" if T > CORTE_OCR else "antes")] += 1
print("total", sum(tot.values()), dict(tot))
for k, c in det.items(): print(k, dict(c))
# tasa de alertas v375 que llegan SOLO por OCR (sin fila ALERTA en CONS a +-2 min), 09-01..09-14: mide cuanto depende v375 del OCR
cons = defaultdict(list)
for f in referencia(incluir_ocr=False):
    if f["tipo"] == "ALERTA_TERMICA": cons[(f["vol"], f["b"])].append(dt.datetime.fromisoformat(f["dt"]))
n = solo = 0
for f in referencia():
    if f["fuente"] == "ocr" and f["tipo"] == "ALERTA_TERMICA_OCR" and "2026-09-01" <= f["fecha"] <= "2026-09-14":
        n += 1; T = dt.datetime.fromisoformat(f["dt"])
        if not any(abs((x - T).total_seconds()) <= 120 for x in cons.get((f["vol"], f["b"]), [])): solo += 1
print("alertas OCR 09-01..09-14:", n, "| sin ALERTA equivalente en CONS a +-2 min:", solo)
