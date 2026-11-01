"""V2 / F2-H2, medición 1: ¿nuestro segundo pase marca píxeles cuando el primero no marcó nada?

Por qué importa: en el código de MIROVA (MIROVA_VIIRS750_hotspot_detection.m:228-235 y 252-400) el
segundo pase es la MISMA función que el primero con los alertados previos puestos en NaN. Si el primer
pase contextual no marcó nada, el segundo recibe exactamente las mismas entradas y devuelve exactamente
lo mismo: vacío. Un segundo pase que marca con el primero vacío es, por construcción, un detector
distinto del primero, cosa que en MIROVA no puede pasar.

Pregunta 1: si nuestro segundo pase fuera idéntico al primero (como en MIROVA), el conteo de records
con primer pase = 0 y recaptura > 0 sería 0. Si la medición diera 0 por no ver los campos, la
pregunta 2 lo atrapa.
Pregunta 2 (instrumento muerto): se cuentan aparte los records sin el campo (SIN DATO) y los que
tienen primer pase > 0 con recaptura > 0 (control positivo: el segundo pase sí actúa cuando hay
conjunto activo; si ese conteo diera 0 el campo estaría muerto).
Denominador: records de data/mirova_equivalent/*.json de los 11 Tier A (archivos > 2 MB), por
sensor; dos ventanas: todo el corpus y desde la observación del 2026-09-18 (detector K, #850).
"""
import sys, io, json
from pathlib import Path
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]

def fam(s):
    if s.startswith("MODIS"): return "MODIS"
    return "VIIRS750" if s.endswith("_750") else "VIIRS375"

C = defaultdict(Counter)
for f in sorted((ROOT / "data/mirova_equivalent").glob("*.json")):
    if f.stat().st_size < 2_000_000:
        continue
    for r in json.load(open(f, encoding="utf-8"))["records"]:
        for ventana in ("todo", "K"):
            if ventana == "K" and r["datetime_utc"] < "2026-09-18":
                continue
            k = (ventana, fam(r["sensor"]))
            C[k]["n"] += 1
            fp = r.get("diag_n_first_pass_pixels"); sp = r.get("diag_n_second_pass_recapture")
            if fp is None or sp is None:
                C[k]["sin_dato"] += 1; continue
            if fp == 0 and sp > 0:
                C[k]["fp0_sp>0"] += 1
                if r.get("distance_class") == "summit":
                    C[k]["fp0_sp>0_summit"] += 1
            elif fp == 0:
                C[k]["fp0_sp0"] += 1
            elif sp > 0:
                C[k]["fp>0_sp>0 (control +)"] += 1
            else:
                C[k]["fp>0_sp0"] += 1
for k in sorted(C):
    print(k, dict(C[k]))

# Medición 1b: de los records con primer pase vacío y recaptura > 0 (ventana K), cuántos quedan con
# magnitud de cúmulo > 0 en summit (proxy del tablero, NO el predicado del tablero: SOSPECHA hasta
# correr isValidDetection con node, A97).
print("\n1b (ventana K, desde 2026-09-18): fp0_sp>0 con summit y pc.vrp_mw>0, por volcán")
D = defaultdict(Counter)
for f in sorted((ROOT / "data/mirova_equivalent").glob("*.json")):
    if f.stat().st_size < 2_000_000:
        continue
    for r in json.load(open(f, encoding="utf-8"))["records"]:
        if r["datetime_utc"] < "2026-09-18": continue
        if r.get("diag_n_first_pass_pixels") == 0 and (r.get("diag_n_second_pass_recapture") or 0) > 0:
            pc = r.get("primary_cluster") or {}
            ok = r.get("distance_class") == "summit" and (pc.get("vrp_mw") or 0) > 0
            D[fam(r["sensor"])][(f.stem, ok)] += 1
for s in D:
    print(s, dict(D[s]))
