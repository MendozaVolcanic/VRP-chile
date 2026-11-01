#!/usr/bin/env python3
"""F3: magnitud contra MIROVA del MISMO gránulo bajo K (data/mirova_equivalent) y bajo C0
(sombra data/experimental_v2, perfil `experimental`: ENABLE_TEST1_PATH True, PROSE_BRANCH False,
B22 False, leído de pipeline.profile). Pareo por (volcan, datetime_utc, sensor).

Pregunta 1: si K no cambiara la magnitud, el cociente K/C0 por pasada daría 1 en la mediana;
esta medición lo vería. Pregunta 2: si la sombra no tuviera las pasadas, n = 0 y se reporta
SIN DATO. Control: cuántos pares tienen pc.vrp_mw idéntico en los dos (si fuera el 100 %,
la sombra sería una copia y no mediría nada).
Mismo criterio de 'dash' que scripts/auto_audit_weekly.py (CAP, INNER, distance_class).
"""
import sys, os, json, statistics
from collections import defaultdict
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, ROOT)
import auto_audit_weekly as aw  # noqa: E402

def dash(rec, vol):
    pc = rec.get("primary_cluster") or {}
    v = pc.get("vrp_mw") or 0.0; cd = pc.get("centroid_dist_km")
    dc = rec.get("distance_class")
    if (0 < v <= aw.CAP) and cd is not None and cd <= aw.INNER[vol] and (not dc or dc == "summit"):
        return v
    return 0.0

def main():
    coords = aw._coords_por_volcan()
    mir = defaultdict(float)
    for a in aw.alertas_mirova():
        dt = a["fecha_utc"] or ""
        if not dt or a["sensor_bucket"] not in aw.SENSORS:
            continue
        ll = coords.get(a["volcano"])
        try:
            o = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if ll and aw.es_pasada_diurna_descartada(a["sensor_bucket"], ll[0], ll[1], o):
            continue
        k = (a["volcano"], a["sensor_bucket"], dt[:10]); mir[k] = max(mir[k], a["vrp_mw"] or 0.0)
    res = {}
    tot = {"pares": 0, "identicos": 0}
    for vol in aw.VOLS:
        p = os.path.join(ROOT, "data", "experimental_v2", vol + ".json")
        if not os.path.exists(p):
            res[vol] = "SIN DATO (no hay sombra)"; continue
        som = {(r["datetime_utc"], r["sensor"]): r for r in json.load(open(p, encoding="utf-8"))["records"]}
        prod = {(r["datetime_utc"], r["sensor"]): r for r in json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json"), encoding="utf-8"))["records"]}
        comunes = sorted(set(som) & set(prod))
        noches = defaultdict(lambda: {"K": 0.0, "C0": 0.0})
        for k in comunes:
            if k[0][:10] < "2026-09-18":
                continue
            tot["pares"] += 1
            vk, vc = dash(prod[k], vol), dash(som[k], vol)
            if abs(((prod[k].get("primary_cluster") or {}).get("vrp_mw") or 0) - ((som[k].get("primary_cluster") or {}).get("vrp_mw") or 0)) < 1e-12:
                tot["identicos"] += 1
            nk = (vol, aw.our_bucket(k[1]), k[0][:10])
            noches[nk]["K"] = max(noches[nk]["K"], vk); noches[nk]["C0"] = max(noches[nk]["C0"], vc)
        rk, rc, ambos = [], [], []
        for nk, d in noches.items():
            m = mir.get(nk, 0.0)
            if m <= 0:
                continue
            if d["K"] > 0: rk.append(d["K"] / m)
            if d["C0"] > 0: rc.append(d["C0"] / m)
            if d["K"] > 0 and d["C0"] > 0: ambos.append((nk[1], nk[2], d["K"] / m, d["C0"] / m))
        md = lambda x: round(statistics.median(x), 3) if x else "SIN DATO"
        res[vol] = {"pasadas_comunes_post_0918": sum(1 for k in comunes if k[0][:10] >= "2026-09-18"),
                    "rango_sombra": [min(k[0] for k in som)[:10], max(k[0] for k in som)[:10]] if som else None,
                    "n_noches_K": len(rk), "med_K": md(rk), "n_noches_C0": len(rc), "med_C0": md(rc),
                    "n_ambos": len(ambos), "med_K_ambos": md([a[2] for a in ambos]), "med_C0_ambos": md([a[3] for a in ambos]),
                    "ambos": ambos}
        r = res[vol]
        print(f"{vol:20s} sombra={r['rango_sombra']} comunes={r['pasadas_comunes_post_0918']} K n={r['n_noches_K']} med={r['med_K']} | C0 n={r['n_noches_C0']} med={r['med_C0']} | ambos n={r['n_ambos']} K={r['med_K_ambos']} C0={r['med_C0_ambos']}")
    print("control: pares post 09-18", tot)
    res["_control"] = tot
    json.dump(res, open(os.path.join(os.path.dirname(__file__), "pareado_k_vs_sombra.json"), "w", encoding="utf-8"), indent=1)

if __name__ == "__main__":
    main()
