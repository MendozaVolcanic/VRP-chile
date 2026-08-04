# S122 — ¿el ángulo de visión sesga lo que medimos? (primer análisis exploratorio)
#
# HIPÓTESIS FÍSICA: un píxel observado de forma oblicua cubre más terreno y es más
# elongado; el foco sub-píxel (que es chico y fijo) queda promediado con más
# superficie fría alrededor, y además la señal atraviesa más atmósfera. Si eso pesa,
# esperaríamos que a mayor zenith del satélite: (a) la magnitud medida BAJE para el
# mismo volcán, y (b) detectemos MENOS (más FN en pasadas oblicuas).
#
# CAVEAT (no confundir con el efecto): el pipeline usa área de píxel NADIR-FIJA
# (A66/A67), así que NO hay una corrección geométrica que introduzca por sí sola una
# dependencia con el ángulo. Cualquier tendencia que aparezca es FÍSICA (dilución
# espacial + atmósfera), no un artefacto de nuestro cálculo de área.
#
# Números del script (S91). Read-only.
import json
import io
import sys
import statistics
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
TIER = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten",
        "Tupungatito", "Copahue", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "NevadosDeChillan"]
BINS = [(0, 20), (20, 35), (35, 50), (50, 60), (60, 90)]


def fam(sensor: str) -> str:
    if sensor.startswith("MODIS"):
        return "MODIS"
    return "VIIRS750" if sensor.endswith("750") else "VIIRS375"


rows = []
for v in TIER:
    d = json.load(open(REPO / "data/mirova_equivalent" / f"{v}.json", encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    for r in recs:
        z = r.get("sensor_zenith_deg")
        if z is None:
            continue
        pc = r.get("primary_cluster") or {}
        rows.append({
            "vol": v, "fam": fam(r.get("sensor", "")), "z": z,
            "vrp": pc.get("vrp_mw") or 0.0,
            "summit": r.get("distance_class") == "summit",
            "det": (pc.get("vrp_mw") or 0) > 0,
        })

print(f"records con geometría: {len(rows)}\n")


def binof(z):
    for lo, hi in BINS:
        if lo <= z < hi:
            return f"{lo}-{hi}"
    return None


# --- 1. Tasa de detección summit por ángulo (¿perdemos eventos de reojo?) ---
print("1) ¿Detectamos menos en pasadas oblicuas? (tasa de detección summit)")
print(f'{"zenith":<9}' + "".join(f"{f:>12}" for f in ("MODIS", "VIIRS375", "VIIRS750")))
for lo, hi in BINS:
    line = f"{lo}-{hi}°".ljust(9)
    for f in ("MODIS", "VIIRS375", "VIIRS750"):
        sub = [r for r in rows if r["fam"] == f and lo <= r["z"] < hi]
        if len(sub) < 20:
            line += f"{'—':>12}"
            continue
        rate = sum(1 for r in sub if r["summit"] and r["det"]) / len(sub) * 100
        line += f"{rate:>10.1f}% "
    print(line)

# --- 2. Magnitud mediana por ángulo, DENTRO de cada volcán (evita mezclar volcanes) ---
print("\n2) ¿Baja la magnitud medida cuando miramos de reojo?")
print("   (mediana de pc.vrp_mw en detecciones summit, por volcán)")
print(f'{"volcán":<22}' + "".join(f"{lo}-{hi}°".rjust(10) for lo, hi in BINS))
for v in TIER:
    line = v.ljust(22)
    for lo, hi in BINS:
        sub = [r["vrp"] for r in rows
               if r["vol"] == v and r["summit"] and r["det"] and lo <= r["z"] < hi]
        line += (f"{statistics.median(sub):>10.2f}" if len(sub) >= 10 else f"{'—':>10}")
    print(line)

# --- 3. Test global: ¿la magnitud del bin más oblicuo difiere del bin nadir? ---
print("\n3) Resumen global (todas las detecciones summit, normalizadas por volcán)")
print("   Se divide cada VRP por la mediana de SU volcán → compara forma, no nivel.")
med = {}
for v in TIER:
    s = [r["vrp"] for r in rows if r["vol"] == v and r["summit"] and r["det"]]
    if s:
        med[v] = statistics.median(s)
norm = defaultdict(list)
for r in rows:
    if r["summit"] and r["det"] and med.get(r["vol"]):
        b = binof(r["z"])
        if b:
            norm[b].append(r["vrp"] / med[r["vol"]])
print(f'{"zenith":<10}{"n":>7}{"VRP relativo (mediana)":>26}')
for lo, hi in BINS:
    b = f"{lo}-{hi}"
    if len(norm[b]) >= 20:
        print(f'{b+"°":<10}{len(norm[b]):>7}{statistics.median(norm[b]):>26.2f}')
print("\n(1.00 = igual que la mediana de su volcán. Si bajara sistemáticamente con el")
print(" ángulo, sería la dilución espacial + atmósfera actuando sobre el foco sub-píxel.)")
