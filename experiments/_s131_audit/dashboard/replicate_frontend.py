#!/usr/bin/env python3
"""Replica VERBATIM los predicados de display de frontend/index.html sobre los
JSON persistidos, para contrastar contra lo que el DOM muestra (tecnica T7).

Puertos 1:1 (file:line de index.html):
  mirovaEqVrp :972 | f5CoreMagnitude :1039 | mirovaEqVrpCore :1071
  mirovaEqVrpDisplay :1096 | isCirrusArtifact :1113 | isValidDetection :1371
  isSummitDetection :1378 | latestDetection :1387 | getLevel :716
Read-only.
"""
import io, json, math, sys, os, argparse
from datetime import datetime, timezone
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DATA = os.path.join(ROOT, "data", "mirova_equivalent")

TIER_A = ["Isluga", "Lascar", "Lastarria", "Tupungatito", "PlanchonPeteroa",
          "NevadosDeChillan", "Copahue", "Llaima", "Villarrica",
          "PuyehueCordonCaulle", "Chaiten"]
INNER = {"Isluga": 5, "Lascar": 5, "Lastarria": 3, "Tupungatito": 7,
         "PlanchonPeteroa": 3, "NevadosDeChillan": 5, "Copahue": 4, "Llaima": 5,
         "Villarrica": 5, "PuyehueCordonCaulle": 20, "Chaiten": 5}

LEVELS = [("nd", "Sin datos", 0), ("vlow", "Muy Bajo", 1), ("low", "Bajo", 10),
          ("mod", "Moderado", 100), ("high", "Alto", 1000),
          ("vhigh", "Muy Alto", math.inf)]
F5_R_CORE_KM, F5_BT_EXT_K = 0.75, 295.0
USE_F5_CORE = True
INCLUDE_FAR = False
SENSOR_VISIBLE = {"MODIS": True, "VIIRS375": True, "VIIRS750": True}


def get_level(vrp):
    if not vrp or vrp <= 0:
        return LEVELS[0]
    for l in LEVELS[1:]:
        if vrp < l[2]:
            return l
    return LEVELS[-1]


def parse_utc_ms(s):
    if s is None:
        return float("nan")
    st = str(s).replace(" ", "T")
    low = st.lower()
    has_off = low.endswith("z")
    if not has_off and len(st) >= 6:
        tail = st[-6:]
        if tail[0] in "+-" and tail[1:3].isdigit():
            has_off = True
    if not has_off:
        st += "Z"
    try:
        return datetime.fromisoformat(st.replace("Z", "+00:00").replace("z", "+00:00")).timestamp() * 1000.0
    except Exception:
        return float("nan")


def hav_km(a1, o1, a2, o2):
    R, rad = 6371.0, math.pi / 180
    p1, p2 = a1 * rad, a2 * rad
    dp, dl = (a2 - a1) * rad, (o2 - o1) * rad
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def mirova_eq_vrp(r, inner_km=10, include_far=False):
    if not r:
        return 0
    pc = r.get("primary_cluster")
    if not pc:
        vfb = r.get("vrp_mw")
        if vfb is None:
            vfb = r.get("vrp_mir_mw")
        if vfb is None:
            vfb = 0
        return 0 if vfb > 50000 else vfb
    dc = r.get("distance_class")
    if dc and dc != "summit" and not include_far:
        return 0
    cd = pc.get("centroid_dist_km")
    if (not include_far) and cd is not None and cd > inner_km:
        return 0
    vmw = pc.get("vrp_mw") or 0
    return 0 if vmw > 50000 else vmw


def f5_core(r, inner_km):
    px = (r or {}).get("anomaly_pixels")
    if not px:
        return None
    pc = r.get("primary_cluster")
    if not pc or pc.get("centroid_lat") is None or pc.get("centroid_lon") is None:
        return None
    cand = [p for p in px if p.get("lat") is not None and p.get("lon") is not None
            and hav_km(p["lat"], p["lon"], pc["centroid_lat"], pc["centroid_lon"]) <= inner_km]
    if not cand:
        return None
    peak = 0
    for i in range(1, len(cand)):
        if (cand[i].get("vrp_mw") or 0) > (cand[peak].get("vrp_mw") or 0):
            peak = i
    plat, plon = cand[peak].get("lat"), cand[peak].get("lon")
    if plat is None or plon is None:
        return None
    s = 0.0
    for i, p in enumerate(cand):
        keep = (i == peak) or \
               (p.get("lat") is not None and p.get("lon") is not None and
                hav_km(p["lat"], p["lon"], plat, plon) <= F5_R_CORE_KM) or \
               ((p.get("bt_k") or 0) >= F5_BT_EXT_K)
        if keep:
            s += (p.get("vrp_mw") or 0)
    return s


def mirova_eq_vrp_core(r, inner_km=10, include_far=False):
    base = mirova_eq_vrp(r, inner_km, include_far)
    if base <= 0:
        return base
    s = str((r or {}).get("sensor") or "").upper()
    if not (s.startswith("VIIRS") and not s.endswith("_750")):
        return base
    core = f5_core(r, inner_km)
    if core is None or core <= 0:
        return base
    return 0 if core > 50000 else core


def eq_vrp_display(r, inner_km=10, include_far=False):
    return mirova_eq_vrp_core(r, inner_km, include_far) if USE_F5_CORE \
        else mirova_eq_vrp(r, inner_km, include_far)


def is_cirrus(r, inner_km=10):
    if not r or r.get("_mirova_confirmed"):
        return False
    t = r.get("t_max_k")
    if t is None or t >= 273.15:
        return False
    return mirova_eq_vrp(r, inner_km, False) > 10


def is_diffuse(r, inner_km=10):
    if not r or r.get("_mirova_confirmed"):
        return False
    pc = r.get("primary_cluster")
    t = r.get("t_max_k")
    if not pc or t is None or t >= 278.15:
        return False
    npx = pc.get("n_pixels") or 0
    if npx < 100:
        return False
    eq = mirova_eq_vrp(r, inner_km, False)
    return eq >= 50 and (eq / npx) < 1.0


def is_thermal_artifact(r, inner_km=10):
    return is_cirrus(r, inner_km) or is_diffuse(r, inner_km)


def is_valid_detection(r):
    if ((r or {}).get("vrp_mw") or 0) > 0:
        return True
    return (r or {}).get("triggered_test1") is True


def is_summit_detection(r):
    if (r.get("vrp_mw") or 0) == 0 and r.get("discarded_reason") and not r.get("triggered_test1"):
        return False
    if r.get("distance_class") == "summit":
        return True
    if r.get("distance_class") == "far":
        return False
    return (r.get("vrp_vent_mw") or 0) > 0


def sensor_group(s):
    if not s:
        return None
    if s.startswith("MODIS"):
        return "MODIS"
    if "750" in s:
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def is_sensor_visible(r):
    g = sensor_group((r or {}).get("sensor"))
    if not g:
        return True
    return SENSOR_VISIBLE.get(g) is not False


def latest_detection(records, now_ms, include_far=False, inner_km=10):
    cutoff = now_ms - 48 * 3600000
    best = None
    for r in records:
        ts = parse_utc_ms(r.get("datetime_utc"))
        if not (ts >= cutoff):
            continue
        if not include_far and not is_summit_detection(r):
            continue
        if not is_valid_detection(r):
            continue
        if not is_sensor_visible(r):
            continue
        if is_thermal_artifact(r, inner_km):
            continue
        v = eq_vrp_display(r, inner_km, include_far)
        if v <= 0:
            continue
        if (best is None) or ts > best["ts"] or (ts == best["ts"] and v > best["vrp"]):
            # index.html:1418-1428 "ancla honesta" S106
            pc = r.get("primary_cluster") or {}
            honest = r.get("final_hotspot_source") in ("ctx_cluster", "test1_roi", "test1_nti_peak")
            dist = (r.get("final_hotspot_dist_km") if honest else None)
            if dist is None:
                dist = pc.get("centroid_dist_km")
            best = {"vrp": v, "dt": r.get("datetime_utc"), "ts": ts,
                    "sensor": r.get("sensor"), "record": r,
                    "dist": dist, "npx": pc.get("n_pixels"),
                    "summit": is_summit_detection(r),
                    "fh_source": r.get("final_hotspot_source")}
    return best


def filter_days(records, days, now_ms):
    if not days:
        return records
    cutoff = now_ms - days * 86400000
    return [r for r in records if parse_utc_ms(r.get("datetime_utc")) >= cutoff]


def load(vol):
    with open(os.path.join(DATA, vol + ".json"), encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--now", default=None)
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--out", default=None)
    ap.add_argument("--data-dir", default=None)
    a = ap.parse_args()
    global DATA
    if a.data_dir: DATA = a.data_dir
    now_ms = (datetime.fromisoformat(a.now).replace(tzinfo=timezone.utc).timestamp() * 1000
              if a.now else datetime.now(timezone.utc).timestamp() * 1000)
    out = {"now_utc": datetime.fromtimestamp(now_ms / 1000, timezone.utc).isoformat(),
           "days": a.days, "use_f5_core": USE_F5_CORE, "include_far": INCLUDE_FAR,
           "volcanoes": {}}
    for vol in TIER_A:
        d = load(vol)
        recs = d.get("records", [])
        inner = INNER[vol]
        det = latest_detection(recs, now_ms, INCLUDE_FAR, inner)
        filt = filter_days(recs, a.days, now_ms)

        def eq(r):
            return 0 if is_thermal_artifact(r, inner) else eq_vrp_display(r, inner, INCLUDE_FAR)

        allv = [x for x in (eq(r) for r in filt) if x > 0]
        vre = 0.0
        for r in filt:
            if not is_valid_detection(r):
                continue
            if not is_sensor_visible(r):
                continue
            vm = eq(r)
            if vm > 0:
                vre += vm * 6 * 3.6
        last_ev = None
        for r in recs:
            dt = r.get("datetime_utc")
            if last_ev is None or (dt or "") > last_ev:
                last_ev = dt
        pcc = (det["record"].get("primary_cluster") or {}) if det else {}
        n48 = 0
        for r in recs:
            if parse_utc_ms(r.get("datetime_utc")) < now_ms - 48 * 3600000:
                continue
            if not (is_valid_detection(r) and is_summit_detection(r)):
                continue
            if is_thermal_artifact(r, inner):
                continue
            if eq_vrp_display(r, inner, INCLUDE_FAR) > 0:
                n48 += 1
        out["volcanoes"][vol] = {
            "n_records_total": len(recs),
            "updated": d.get("updated"),
            "card_vrp": round(det["vrp"], 2) if det else None,
            "card_level": get_level(det["vrp"] if det else 0)[1],
            "card_det_dt": det["dt"] if det else None,
            "card_det_sensor": det["sensor"] if det else None,
            "card_det_dist_km": (round(det["dist"], 1) if det and det["dist"] is not None else None),
            "card_det_dist_raw": (det["dist"] if det else None),
            "card_det_npx": (det["npx"] if det else None),
            "card_det_fh_source": (det["fh_source"] if det else None),
            "card_pc_centroid_dist_km": pcc.get("centroid_dist_km") if det else None,
            "last_event_utc": last_ev,
            "n_48h_detections": n48,
            "n_30d_granules": len(filt),
            "n_30d_detections": len(allv),
            "max_vrp_30d": round(max(allv), 2) if allv else None,
            "mean_vrp_30d": round(sum(allv) / len(allv), 2) if allv else None,
            "vre_gj_30d": round(vre, 1) if vre > 0 else None,
        }
    txt = json.dumps(out, indent=2, ensure_ascii=False)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(txt)
    print(txt)


if __name__ == "__main__":
    main()
