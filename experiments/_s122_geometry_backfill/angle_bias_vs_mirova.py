# S122 — ¿el sesgo por ángulo de visión es NUESTRO o del MÉTODO? (prueba decisiva)
#
# Hallazgo previo: nuestra magnitud VIIRS cae ~2x del nadir a la visión oblicua.
# Dos explicaciones posibles, con consecuencias muy distintas:
#
#   (a) INHERENTE AL MÉTODO — el foco sub-píxel se diluye en un píxel más grande y la
#       señal atraviesa más atmósfera. MIROVA, que usa el mismo enfoque MIR con área
#       nadir-fija, debería mostrar la MISMA pendiente. Entonces el ratio nuestro/MIROVA
#       sería PLANO en ángulo, y el sesgo es una limitación conocida del VRP satelital.
#
#   (b) NUESTRO — algo de nuestra implementación amplifica la caída. Entonces el ratio
#       nuestro/MIROVA CAERÍA con el ángulo, y sería un bug a corregir.
#
# El test: ratio (nuestro pc.vrp_mw / VRP MIROVA) en las MISMAS noches, binned por zenith.
# Números del script (S91). Read-only.
import io
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from pipeline.mirova_csv_loader import load_mirova_alertas  # noqa: E402

TIER = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten",
        "Tupungatito", "Copahue", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "NevadosDeChillan"]
BINS = [(0, 20), (20, 35), (35, 50), (50, 60), (60, 90)]


def bucket(sensor: str) -> str:
    if sensor.startswith("MODIS"):
        return "MODIS"
    return "VIIRS750" if sensor.endswith("750") else "VIIRS375"


# --- Ground truth MIROVA (universo CONS ∪ OCR, A11) ---
alertas = load_mirova_alertas(
    cons_path=REPO / "latest_consolidado.csv",
    ocr_path=REPO / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv",
)
gt = {}
for a in alertas:
    # OJO: `timestamp` es epoch Unix, no fecha ISO — la fecha va en `fecha_utc`.
    fecha = str(a.get("fecha_utc") or "")
    if not fecha or not a.get("vrp_mw"):
        continue
    # clave: volcán + noche + familia de sensor. Si MIROVA publicó varias pasadas
    # esa noche, nos quedamos con el máximo (lo que su web reporta como el evento).
    k = (a["volcano"], fecha[:10], a["sensor_bucket"])
    gt[k] = max(gt.get(k, 0), a["vrp_mw"])
print(f"ALERTAs MIROVA cargadas (CONS∪OCR): {len(gt)}")

# --- Nuestros records con geometría, emparejados con la misma noche ---
pairs = defaultdict(list)  # (familia, bin) -> [ratio]
n_match = 0
for v in TIER:
    d = json.load(open(REPO / "data/mirova_equivalent" / f"{v}.json", encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) and "records" in d else d
    # mejor detección summit por (noche, familia): lo que el dashboard reporta
    best = {}
    for r in recs:
        z = r.get("sensor_zenith_deg")
        if z is None or r.get("distance_class") != "summit":
            continue
        pc = r.get("primary_cluster") or {}
        vrp = pc.get("vrp_mw") or 0
        if vrp <= 0:
            continue
        k = (v, r["datetime_utc"][:10], bucket(r.get("sensor", "")))
        if k not in best or vrp > best[k][0]:
            best[k] = (vrp, z)
    for k, (vrp, z) in best.items():
        mv = gt.get(k)
        if not mv:
            continue
        n_match += 1
        for lo, hi in BINS:
            if lo <= z < hi:
                pairs[(k[2], f"{lo}-{hi}")].append(vrp / mv)
                break

print(f"noches emparejadas (nuestra detección ∧ ALERTA MIROVA): {n_match}\n")
print("Ratio NUESTRO / MIROVA por ángulo de visión")
print("  plano  → el sesgo es del MÉTODO (MIROVA lo tiene igual)")
print("  cae    → el sesgo es NUESTRO (amplificamos la caída)\n")
print(f'{"zenith":<9}' + "".join(f"{f:>18}" for f in ("MODIS", "VIIRS375", "VIIRS750")))
for lo, hi in BINS:
    line = f"{lo}-{hi}°".ljust(9)
    for f in ("MODIS", "VIIRS375", "VIIRS750"):
        vals = pairs[(f, f"{lo}-{hi}")]
        line += (f'{statistics.median(vals):>11.2f} (n={len(vals)})' if len(vals) >= 10
                 else f'{"—":>18}')
    print(line)
