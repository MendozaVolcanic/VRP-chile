"""01: qué escribió producción (data/mirova_equivalent) en las 6 noches, todos los sensores, con la posición de cada
píxel anómalo medida desde el cráter (vent) y desde el centro del TIF de MIROVA (mirova_center).

Pregunta 1 del instrumento: si producción no hubiera escrito nada esa noche, acá sale «sin record» (SIN DATO), no 0.
Pregunta 2: el control positivo es la propia pasada de Suomi NPP, que el objetivo de S159 dice que existe (granule).
Ventana: ±12 h alrededor de la hora UTC de la pasada protegida. Corpus: data/mirova_equivalent/<vol>.json del commit medido.
"""
import json, math, sys, io, datetime as dt
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
import yaml
V = {v["name"]: v for v in yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}

def hav(a, b, c, d):
    R = 6371.0088
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c - a), math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))

SEIS = [("Tupungatito", "2026-08-01 05:00", 279), ("Lascar", "2026-08-22 05:06", 285), ("Isluga", "2026-09-09 06:06", 288),
        ("Tupungatito", "2026-09-14 06:18", 289), ("Tupungatito", "2026-09-28 05:18", 294), ("Tupungatito", "2026-09-29 04:54", 295)]
salida = {}
for vol, h, i in SEIS:
    v = V[vol]
    vlat, vlon = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])
    clat, clon = v.get("mirova_center_lat", v["lat"]), v.get("mirova_center_lon", v["lon"])
    print(f"\n=== id {i} {vol} {h}  inner {v['inner_radius_km']} km | cráter→centro MIROVA {hav(vlat, vlon, clat, clon):.2f} km")
    recs = json.load(open(RAIZ / f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))
    recs = recs["records"] if isinstance(recs, dict) else recs
    t0 = dt.datetime.fromisoformat(h)
    filas = []
    for r in recs:
        t = dt.datetime.fromisoformat(r["datetime_utc"].replace("Z", "")[:19])
        if abs((t - t0).total_seconds()) > 12 * 3600:
            continue
        pc = r.get("primary_cluster") or {}
        px = r.get("anomaly_pixels") or []
        dets = []
        for p in px:
            la, lo = p.get("lat"), p.get("lon")
            if la is None:
                continue
            dets.append({"lat": la, "lon": lo, "vrp": p.get("vrp_mw"), "d_vent": round(hav(la, lo, vlat, vlon), 2),
                         "d_centro": round(hav(la, lo, clat, clon), 2), "bt": p.get("bt_mir_k") or p.get("t_mir_k"),
                         "src": p.get("source") or p.get("path")})
        fila = {"t": r["datetime_utc"], "sensor": r["sensor"], "vrp_mw": r.get("vrp_mw"), "npx": r.get("n_anomalous_pixels"),
                "pc_vrp": pc.get("vrp_mw"), "pc_n": pc.get("n_pixels"), "pc_dist": pc.get("dist_km"),
                "pc_lat": pc.get("centroid_lat") or pc.get("lat"), "pc_lon": pc.get("centroid_lon") or pc.get("lon"),
                "dc": r.get("distance_class"), "fh_dist": r.get("final_hotspot_dist_km"), "fh_src": r.get("final_hotspot_source"),
                "f5": r.get("f5_core_vrp_mw"), "t_bg": r.get("t_bg_k"), "t_max": r.get("t_max_k"), "nti_max": r.get("diag_nti_max"),
                "granule": r.get("granule"), "pixeles": dets, "marca": "<<< LA PASADA" if abs((t - t0).total_seconds()) < 120 else ""}
        filas.append(fila)
        pcd = fila["pc_dist"]
        print(f"  {fila['t'][:16]} {fila['sensor']:16s} vrp {fila['vrp_mw']!s:7s} npx {fila['npx']!s:3s} pc {fila['pc_vrp']!s:7s} n {fila['pc_n']!s:3s} d {pcd!s:7s} {fila['dc']!s:7s} fh {fila['fh_dist']!s:7s} f5 {fila['f5']!s:7s} tbg {fila['t_bg']} {fila['marca']}")
        for d in dets:
            print(f"      px {d['lat']:.4f},{d['lon']:.4f} vrp {d['vrp']} d_vent {d['d_vent']} d_centro {d['d_centro']} {d['src'] or ''}")
    if not filas:
        print("  SIN RECORD en ±12 h")
    salida[str(i)] = {"volcan": vol, "hora": h, "records": filas}
json.dump(salida, open(Path(__file__).with_name("01_records_produccion.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
