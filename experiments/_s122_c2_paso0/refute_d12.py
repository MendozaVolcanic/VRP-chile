# D12 refutación adversarial (S122, A62) — atacar la conclusión "no hay núcleo".
#
# Nicolás (geólogo del volcán) pide refutar antes de cerrar D12. Tres ataques:
#   (1) CROSS-SENSOR: ¿VIIRS375 (375m, resuelve sub-píxel) muestra un núcleo concentrado
#       en Láscar cuando MODIS (1km) ve un blob plano? Si sí → el foco existe pero es
#       sub-píxel para MODIS (confirma C2-no-viable Y valida que la cura es real).
#       Si VIIRS375 también plano → Láscar difuso incluso a 375m.
#   (2) HUECO PROPIO: el cluster tiene n_pixels>anomaly_pixels (148 vs 82 en PCC). ¿Hay un
#       píxel-núcleo caliente FUERA de anomaly_pixels que el Paso 0 no miró?
#   (3) ESPACIAL (A61): ¿el píxel pico está EN el cráter (real) o corrido (topográfico)?
#
# Métrica de concentración: frac del píxel pico sobre el total de radiancia del blob.
# Foco real sub-píxel → 1 píxel domina (>40%). Blob difuso → pico ~2-5%.
import json
import io
import sys
import statistics
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "data" / "mirova_equivalent"
LO, HI = "2025-02-15", "2025-05-15"


def load(p):
    d = json.load(open(p, encoding="utf-8"))
    return d["records"] if isinstance(d, dict) and "records" in d else d


def frac_top1(ap):
    vr = sorted((p.get("vrp_mw") or 0) for p in ap)
    s = sum(vr)
    return (vr[-1] / s * 100 if s else 0), vr[-1], len(ap), s


recs = load(BASE / "Lascar.json")

# --- Ataque 1: concentración por familia de sensor, TODA la historia de Láscar ---
print("=" * 70)
print("ATAQUE 1 — CROSS-SENSOR: concentración del blob por resolución (Láscar)")
print("=" * 70)
fam = {"MODIS (1km)": lambda s: s.startswith("MODIS"),
       "VIIRS375 (I-band)": lambda s: s.startswith("VIIRS") and "750" not in s,
       "VIIRS750 (M-band)": lambda s: "750" in s}
for name, pred in fam.items():
    fts = []
    peaks = []
    for r in recs:
        if not pred(r.get("sensor", "")):
            continue
        ap = r.get("anomaly_pixels") or []
        pc = r.get("primary_cluster") or {}
        if not ap or (pc.get("vrp_mw") or 0) <= 1:
            continue
        ft, pk, n, s = frac_top1(ap)
        fts.append(ft)
        peaks.append(pk)
    if fts:
        print(f"\n{name}: {len(fts)} records con pc.vrp>1")
        print(f"  frac top-1 píxel:  mediana {statistics.median(fts):5.1f}%  "
              f"p90 {sorted(fts)[int(len(fts)*0.9)]:5.1f}%  max {max(fts):5.1f}%")
        print(f"  vrp píxel pico:    mediana {statistics.median(peaks):5.2f}  max {max(peaks):5.2f} MW")
        conc = sum(1 for f in fts if f > 40)
        print(f"  records con núcleo real (top-1 >40%): {conc}/{len(fts)}")

# --- Ataque 2: ¿anomaly_pixels omite un núcleo? comparar con discarded + n_pixels cluster ---
print("\n" + "=" * 70)
print("ATAQUE 2 — HUECO PROPIO: ¿hay núcleo fuera de anomaly_pixels? (blobs MODIS path-D)")
print("=" * 70)
def path_d_only(r):
    d = r.get("diag_n_dnti_ctx_path") or 0
    o = sum(r.get(k) or 0 for k in ("diag_n_bt_path", "diag_n_nti_path", "diag_n_eti_path"))
    return d > 0 and o == 0
checked = 0
for r in recs:
    if not r.get("sensor", "").startswith("MODIS"):
        continue
    if not (LO <= r.get("datetime_utc", "")[:10] <= HI):
        continue
    pc = r.get("primary_cluster") or {}
    if not (path_d_only(r) and (pc.get("vrp_mw") or 0) > 5):
        continue
    ap = r.get("anomaly_pixels") or []
    disc = r.get("discarded_anomaly_pixels") or []
    all_bt = [(p.get("bt_k") or 0) for p in ap] + [(p.get("bt_k") or 0) for p in disc]
    all_vrp = [(p.get("vrp_mw") or 0) for p in ap] + [(p.get("vrp_mw") or 0) for p in disc]
    if checked < 5:
        print(f"  {r['datetime_utc']}: n_ap={len(ap)} n_discarded={len(disc)} "
              f"pc.n_pixels={pc.get('n_pixels')} | max_bt(ap+disc)={max(all_bt):.1f}K "
              f"max_vrp={max(all_vrp):.2f}MW t_max_k(record)={r.get('t_max_k')}")
    checked += 1
print(f"  → t_max_k es el píxel más caliente de la escena; si ~ max_bt del blob, no hay núcleo oculto.")

# --- Ataque 3: ubicación del píxel pico vs cráter ---
print("\n" + "=" * 70)
print("ATAQUE 3 — ESPACIAL (A61): ¿el píxel pico está en el cráter o corrido?")
print("=" * 70)
import yaml
volc = yaml.safe_load(open(REPO / "volcanoes.yaml", encoding="utf-8"))
# buscar vent de Lascar
vlat = vlon = None
vs = volc.get("volcanoes", volc) if isinstance(volc, dict) else volc
for v in (vs.values() if isinstance(vs, dict) else vs):
    nm = (v.get("name") or "") if isinstance(v, dict) else ""
    if "asca" in nm.lower():
        vlat, vlon = v.get("vent_lat") or v.get("lat"), v.get("vent_lon") or v.get("lon")
        break
print(f"  vent Láscar (volcanoes.yaml): {vlat}, {vlon}")
import math
def hav(a, b, c, d):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))
shown = 0
for r in recs:
    if not r.get("sensor", "").startswith("MODIS"):
        continue
    if not (LO <= r.get("datetime_utc", "")[:10] <= HI):
        continue
    pc = r.get("primary_cluster") or {}
    if not (path_d_only(r) and (pc.get("vrp_mw") or 0) > 5):
        continue
    ap = r.get("anomaly_pixels") or []
    if not ap or vlat is None:
        continue
    pk = max(ap, key=lambda p: p.get("vrp_mw") or 0)
    dpk = hav(vlat, vlon, pk["lat"], pk["lon"])
    if shown < 6:
        print(f"  {r['datetime_utc']}: pc.vrp={pc.get('vrp_mw'):.1f} píxel-pico a {dpk:.2f}km del cráter "
              f"(bt={pk.get('bt_k'):.1f}K vrp={pk.get('vrp_mw'):.2f}MW)")
    shown += 1
