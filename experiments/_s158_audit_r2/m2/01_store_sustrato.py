"""M2 (S158 r2): sustrato de store.py medido en los JSON publicados.

Pregunta 1 (si store.py estuviera roto, ¿esto lo ve?): mide duplicados de clave, records diurnos
que el gate debió rechazar, píxeles fuera del geofence que el filtro debió sacar, y el estado del
reemplazo NRT->Standard por edad. Cada una de esas cosas es exactamente lo que store.py promete.
Pregunta 2 (si el instrumento estuviera muerto, ¿se nota?): controles positivos al final: un record
sintético duplicado, uno diurno y uno con píxel lejano pasan por las mismas funciones y deben dar
distinto de cero.

Ventana: todo el corpus data/mirova_equivalent/*.json al día de la corrida (se imprime max datetime).
"""
import glob, json, os, sys, io
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(ROOT, "..", "..", ".."))
sys.path.insert(0, REPO)
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import yaml
from pipeline.store import _solar_elevation, _reject_daytime, _filter_pixels_by_distance, _apply_sanity_cap

vols = {v["name"]: v for v in yaml.safe_load(open(os.path.join(REPO, "volcanoes.yaml")))["volcanoes"]}

dup = Counter(); day_leak = Counter(); far_px = Counter(); far_px_none = Counter()
nrt_age = Counter(); pv = Counter(); disc = Counter(); a46 = Counter(); rescue = Counter()
tmax_missing = Counter(); cap_fields = Counter(); vrp0_pc_pos = Counter(); vrp_vs_pc = Counter()
first_proc = Counter(); maxdt = ""; n = 0; nrt_by_sensor = Counter(); tot_by_sensor = Counter()
sens_tier = Counter()
now = datetime.now(timezone.utc)
for f in sorted(glob.glob(os.path.join(REPO, "data/mirova_equivalent/*.json"))):
    name = os.path.basename(f)[:-5]
    v = vols.get(name)
    recs = json.load(open(f))["records"]
    keys = Counter((r.get("datetime_utc"), r.get("sensor")) for r in recs)
    dup[name] = sum(c - 1 for c in keys.values() if c > 1)
    for r in recs:
        n += 1
        s = r.get("sensor", "")
        tier = "A" if v and v.get("inner_radius_km") else "B"
        sens_tier[(s[:5], tier)] += 1
        tot_by_sensor[s] += 1
        dt = r.get("datetime_utc", "")
        maxdt = max(maxdt, dt)
        pv[r.get("product_version")] += 1
        if r.get("product_version") == "nrt":
            nrt_by_sensor[s] += 1
            try:
                age = (now - datetime.strptime(dt, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)).days
                nrt_age[min(age // 30, 12)] += 1
            except ValueError:
                nrt_age["?"] += 1
        if v:
            try:
                d = datetime.strptime(dt, "%Y-%m-%d %H:%M")
                e = _solar_elevation(v["lat"], v["lon"], d)
                if _reject_daytime(s, e, False, False):
                    day_leak[s] += 1
            except ValueError:
                day_leak["unparseable"] += 1
            rk = v.get("radius_km")
            for p in r.get("anomaly_pixels") or []:
                if p.get("dist_km") is None:
                    far_px_none[name] += 1
                elif rk is not None and p["dist_km"] > rk:
                    far_px[name] += 1
        disc[r.get("discarded_reason")] += 1
        if r.get("diag_a46_relabel"):
            a46[s] += 1
        if r.get("final_hotspot_source") == "cluster_rescue":
            rescue[s] += 1
        if "t_max_k" not in r or r.get("t_max_k") is None:
            tmax_missing[s] += 1
        for k in ("vrp_exceeds_sanity_cap", "diag_rejected_sanity_cap_mw", "diag_pc_rejected_sanity_cap_mw",
                  "diag_vrp_floor_mw"):
            if k in r:
                cap_fields[k] += 1
        pc = r.get("primary_cluster") or {}
        if (r.get("vrp_mw") or 0) == 0 and (pc.get("vrp_mw") or 0) > 0:
            vrp0_pc_pos[(s[:5], r.get("discarded_reason"))] += 1
        if "first_processed_utc" in r:
            first_proc["con"] += 1
        else:
            first_proc["sin"] += 1

print("records:", n, "| max datetime_utc:", maxdt, "| corrida:", now.strftime("%Y-%m-%d %H:%M UTC"))
print("sensor x tier (A = tiene inner_radius_km):", sorted(sens_tier.items()))
print("\n[dedup] duplicados de (datetime_utc, sensor) por volcan (debe ser 0):", {k: c for k, c in dup.items() if c} or "0 en los 45")
print("[dia/noche] records que _reject_daytime rechazaria hoy (flags OFF), por sensor:", dict(day_leak) or "0")
print("[geofence] anomaly_pixels con dist_km > radius_km, por volcan:", dict(far_px) or "0")
print("[geofence] anomaly_pixels con dist_km None (el filtro los trata como 0 km):", dict(far_px_none) or "0")
print("[product_version]", dict(pv))
print("[nrt por sensor]", dict(nrt_by_sensor))
print("[nrt por edad en meses (floor(dias/30), 12 = un anio o mas)]", dict(sorted(nrt_age.items(), key=lambda x: str(x[0]))))
print("[discarded_reason]", dict(disc))
print("[diag_a46_relabel summit->far por sensor]", dict(a46))
print("[final_hotspot_source == cluster_rescue por sensor]", dict(rescue))
print("[t_max_k ausente o None por sensor]", dict(tmax_missing) or "0")
print("[campos del cap/piso]", dict(cap_fields) or "ninguno")
print("[vrp_mw == 0 con pc.vrp_mw > 0, por (sensor, discarded_reason)]", dict(vrp0_pc_pos))
print("[first_processed_utc]", dict(first_proc))

# ---- controles positivos (pregunta 2) ----
print("\n== controles positivos ==")
d = datetime(2026, 3, 1, 18, 0)
e = _solar_elevation(-39.42, -71.94, d)
print("Villarrica 2026-03-01 18:00 UTC (15:00 local) elev =", round(e, 1), "-> rechazar:", _reject_daytime("MODIS_TERRA", e, False))
d2 = datetime(2026, 3, 1, 5, 0)
e2 = _solar_elevation(-39.42, -71.94, d2)
print("Villarrica 2026-03-01 05:00 UTC elev =", round(e2, 1), "-> rechazar:", _reject_daytime("MODIS_TERRA", e2, False))
rec = {"anomaly_pixels": [{"dist_km": 1.0, "vrp_mw": 1.0, "lat": 0, "lon": 0}, {"dist_km": 30.0, "vrp_mw": 5.0, "lat": 0, "lon": 0}]}
print("filtro 25 km sobre [1 km, 30 km]:", _filter_pixels_by_distance(rec, 25.0), "->", rec["discarded_reason"], "quedan", len(rec["anomaly_pixels"]))
rec2 = {"vrp_mw": 60000.0, "t_max_k": None, "primary_cluster": {"vrp_mw": 60000.0}}
_apply_sanity_cap(rec2); print("cap con t_max_k None y 60 GW ->", rec2.get("vrp_mw"), rec2.get("discarded_reason"))
rec3 = {"vrp_mw": 60000.0, "t_max_k": 420.0, "primary_cluster": {"vrp_mw": 60000.0}}
_apply_sanity_cap(rec3); print("cap con t_max_k 420 K y 60 GW ->", rec3.get("vrp_mw"), rec3.get("vrp_exceeds_sanity_cap"))
rec4 = {"vrp_mw": 60000.0, "t_max_i04_k": 420.0, "primary_cluster": {"vrp_mw": 60000.0}}
_apply_sanity_cap(rec4); print("cap con SOLO t_max_i04_k 420 K y 60 GW (orden real de append_record) ->", rec4.get("vrp_mw"), rec4.get("discarded_reason"))
