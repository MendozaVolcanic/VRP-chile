"""S94 — Auditoría ESPACIAL de Tupungatito: ¿caen nuestras detecciones en la laguna
cratérica, o se dispersan sobre el glaciar?

Pregunta de Nicolás: "los valores no estaban dando en la laguna cratérica".

Geometría (volcanoes.yaml): el cráter real (vent) está en (-33.389044, -69.826374).
MIROVA mide distancias desde su punto nominal mirova_center (-33.42694, -69.80039),
que está a ~4.86 km del cráter (idiosincrasia A13/A30). Por eso una alerta MIROVA
"a 4.37 km" de su centro está en realidad ≈0.5 km del cráter = EN la laguna.

Nuestros campos miden distancia desde el VENT (cráter real): final_hotspot_dist_km
y primary_cluster.centroid_dist_km. inner_radius Tupungatito = 7 km.

Este script (read-only, §0.5) responde:
  1. Distribución espacial de NUESTRAS detecciones por sensor y banda de distancia.
  2. ¿La señal del cráter (VIIRS375 cerca) coincide con MIROVA?
  3. ¿De dónde sale la magnitud? (foco cráter vs campo difuso glaciar).
  4. Un record campo-difuso: ¿hay pixels calientes en el cráter pero el centroide
     del cluster se va al glaciar?
  python experiments/_s94_audit/tupungatito_spatial.py
"""
import sys, os, io, json, math
from statistics import median

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

VENT = (-33.389044, -69.826374)        # cráter real (laguna)
MIROVA_CENTER = (-33.42694, -69.80039)  # punto nominal MIROVA
INNER = 7.0


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def bucket(s):
    s = str(s or "").upper()
    if "MODIS" in s:
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def band(d):
    if d is None:
        return "n/a"
    if d <= 2:
        return "0-2km (cráter)"
    if d <= 5:
        return "2-5km"
    if d <= INNER:
        return "5-7km (borde inner)"
    return ">7km (far/glaciar)"


BANDS = ["0-2km (cráter)", "2-5km", "5-7km (borde inner)", ">7km (far/glaciar)", "n/a"]

d = json.load(open(os.path.join(REPO, "data/mirova_equivalent/Tupungatito.json"), encoding="utf-8"))
recs = d["records"] if isinstance(d, dict) and "records" in d else d

print("=" * 84)
print("TUPUNGATITO — distancia cráter↔mirova_center:",
      round(haversine(*VENT, *MIROVA_CENTER), 2), "km (confirma offset ~4.86, A13/A30)")
print("=" * 84)

# --- distribución por sensor × banda de distancia (records vrp>0) ---
from collections import defaultdict
grid = defaultdict(lambda: defaultdict(int))
vrp_by_band = defaultdict(list)
for r in recs:
    pc = r.get("primary_cluster") or {}
    vrp = pc.get("vrp_mw") or 0
    if vrp <= 0:
        continue
    b = bucket(r.get("sensor"))
    dist = pc.get("centroid_dist_km")
    if dist is None:
        dist = r.get("final_hotspot_dist_km")
    bd = band(dist)
    grid[b][bd] += 1
    vrp_by_band[bd].append(vrp)

print(f"\n¿Dónde caen los CENTROIDES de cluster (records vrp>0), por sensor?")
print(f"{'Sensor':<10}" + "".join(f"{bd:>20}" for bd in BANDS[:4]))
for b in ["VIIRS375", "VIIRS750", "MODIS"]:
    print(f"{b:<10}" + "".join(f"{grid[b][bd]:>20}" for bd in BANDS[:4]))

print(f"\n¿De dónde sale la MAGNITUD? VRP mediano por banda de distancia:")
for bd in BANDS[:4]:
    vs = vrp_by_band[bd]
    if vs:
        print(f"  {bd:<22} n={len(vs):>4}  vrp_med={median(vs):>7.2f}  vrp_max={max(vs):>8.2f}")

# --- el record de mayor VRP: ¿foco o campo difuso? ¿hay pixel caliente en cráter? ---
top = max((r for r in recs if (r.get("primary_cluster") or {}).get("vrp_mw")),
          key=lambda r: r["primary_cluster"]["vrp_mw"])
pc = top["primary_cluster"]
print("\n" + "=" * 84)
print("RECORD DE MAYOR VRP — anatomía foco vs campo difuso")
print("=" * 84)
print(f"  {top['datetime_utc']}  sensor={top.get('sensor')}  vrp={pc['vrp_mw']:.1f} MW")
print(f"  n_pixels={pc.get('n_pixels')}  vrp/px={pc['vrp_mw']/max(pc.get('n_pixels',1),1):.3f}")
print(f"  t_max={top.get('t_max_k')}K ({(top.get('t_max_k') or 0)-273.15:.1f}°C)  "
      f"t_bg={top.get('t_bg_k')}K ({(top.get('t_bg_k') or 0)-273.15:.1f}°C)")
print(f"  distance_class={top.get('distance_class')}  centroid_dist={pc.get('centroid_dist_km')}km")
print(f"  diag_n_bt_path={top.get('diag_n_bt_path')}  diag_n_nti_path={top.get('diag_n_nti_path')}  "
      f"diag_n_dnti_ctx_path={top.get('diag_n_dnti_ctx_path')}")

# anomaly_pixels: ¿alguno cae en el cráter (<2km del vent)?
aps = top.get("anomaly_pixels") or []
if aps:
    near = [p for p in aps if p.get("lat") is not None and haversine(p["lat"], p["lon"], *VENT) <= 2.0]
    dists = sorted(haversine(p["lat"], p["lon"], *VENT) for p in aps if p.get("lat") is not None)
    print(f"  anomaly_pixels: n={len(aps)}, dist al cráter min/med/max = "
          f"{dists[0]:.2f}/{median(dists):.2f}/{dists[-1]:.2f} km")
    print(f"  pixels DENTRO de 2km del cráter (laguna): {len(near)} de {len(aps)}")

print("\nLECTURA: si la magnitud vive en banda >5km con n_pixels alto y vrp/px<1,")
print("es campo difuso glaciar (path D sobre fondo gélido), NO el foco del cráter.")

# --- dump JSON para verificación de integridad (§0.5) ---
v375_close = grid["VIIRS375"]["0-2km (cráter)"]
v375_total = sum(grid["VIIRS375"][bd] for bd in BANDS[:4])
top_aps = top.get("anomaly_pixels") or []
top_near = sum(1 for p in top_aps if p.get("lat") is not None and haversine(p["lat"], p["lon"], *VENT) <= 2.0)
dump = {
    "crater_to_mirova_center_km": round(haversine(*VENT, *MIROVA_CENTER), 2),
    "v375_centroid_within_2km": v375_close,
    "v375_total": v375_total,
    "vrp_med_crater_0_2km": round(median(vrp_by_band["0-2km (cráter)"]), 2),
    "vrp_med_glacier_gt7km": round(median(vrp_by_band[">7km (far/glaciar)"]), 2),
    "top_record": {"datetime": top["datetime_utc"], "sensor": top.get("sensor"),
                   "vrp_mw": round(pc["vrp_mw"], 1), "n_pixels": pc.get("n_pixels"),
                   "pixels_within_2km": top_near, "n_anomaly_pixels": len(top_aps)},
}
outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tupungatito_spatial.json")
json.dump(dump, open(outp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"\nJSON → {outp}")
