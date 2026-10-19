#!/usr/bin/env python3
"""F3: el auto-audit semanal recalculado EN MEMORIA (no escribe data/), estratificado.

Replica los pasos 1 a 3 de scripts/auto_audit_weekly.py:main() importando sus funciones
(alertas_mirova, es_pasada_diurna_descartada, our_bucket, INNER, CAP, VOLS) y agrega
estratos: regimen (C0 = record sin marca y fecha < 2026-09-18; K = marca con sha
descendiente de 34cea39e), sensor, y magnitud alternativa (f5_core_vrp_mw, la que el
tablero publica en VIIRS 375).

Pregunta 1: si el audit estuviera roto en su magnitud, esto lo veria? Si: el control
'reproducir' exige que con ventana 2026-08-15..2026-10-14 y sin estratos salga un ratio
para Tupungatito comparable al 0,647 de latest.json (sobre el corpus de HOY, que fue
reprocesado con K en sus ultimos 30 dias, asi que NO tiene por que coincidir: A90).
Pregunta 2: un estrato con n = 0 se imprime como SIN DATO, nunca como 0.
"""
import sys, os, json, statistics
from collections import defaultdict
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, ROOT)
import auto_audit_weekly as aw  # noqa: E402

FRONTERA_K = "2026-09-18"

def regimen(rec):
    sha = (rec.get("regimen") or {}).get("codigo_sha")
    if sha:
        return "K"          # verificado en regimen_por_ventana.py: todo sha presente es K
    return "C0" if (rec.get("datetime_utc") or "")[:10] < FRONTERA_K else "sin_marca_post"

def correr(win, estratos=True):
    def in_win(dt):
        return bool(dt) and win[0] <= dt[:10] <= win[1]
    coords = aw._coords_por_volcan()
    mir = defaultdict(float)
    for a in aw.alertas_mirova():
        dt = a["fecha_utc"] or ""
        if not in_win(dt) or a["sensor_bucket"] not in aw.SENSORS:
            continue
        ll = coords.get(a["volcano"])
        if ll:
            try:
                o = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
            except ValueError:
                o = None
            if o and aw.es_pasada_diurna_descartada(a["sensor_bucket"], ll[0], ll[1], o):
                continue
        k = (a["volcano"], a["sensor_bucket"], dt[:10])
        mir[k] = max(mir[k], a["vrp_mw"] or 0.0)
    ours = defaultdict(lambda: {"dash_pc": [], "dash_core": [], "reg": set()})
    for vol in aw.VOLS:
        d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json"), encoding="utf-8"))
        for rec in d["records"]:
            dt = rec.get("datetime_utc")
            if not in_win(dt):
                continue
            b = aw.our_bucket(rec.get("sensor", ""))
            if b is None:
                continue
            pc = rec.get("primary_cluster") or {}
            vrp = pc.get("vrp_mw") or 0.0
            cd = pc.get("centroid_dist_km")
            if (0 < vrp <= aw.CAP) and cd is not None and cd <= aw.INNER[vol]:
                dc = rec.get("distance_class")
                if not dc or dc == "summit":
                    k = (vol, b, dt[:10])
                    ours[k]["dash_pc"].append(vrp)
                    core = rec.get("f5_core_vrp_mw")
                    ours[k]["dash_core"].append(core if (b == "VIIRS375" and isinstance(core, (int, float)) and core > 0) else vrp)
                    ours[k]["reg"].add(regimen(rec))
    filas = []
    for (vol, s, date), m in mir.items():
        o = ours.get((vol, s, date))
        if not (o and o["dash_pc"]) or m <= 0:
            continue
        reg = "C0" if date < FRONTERA_K else "K"
        filas.append({"vol": vol, "s": s, "date": date, "reg": reg, "reg_records": sorted(o["reg"]),
                      "mir": m, "r_pc": max(o["dash_pc"]) / m, "r_core": max(o["dash_core"]) / m})
    return filas

def med(xs):
    return round(statistics.median(xs), 3) if xs else "SIN DATO"

def resumen(filas, vol=None):
    f = [x for x in filas if vol is None or x["vol"] == vol]
    out = {"todo": (len(f), med([x["r_pc"] for x in f]), med([x["r_core"] for x in f]))}
    for reg in ("C0", "K"):
        g = [x for x in f if x["reg"] == reg]
        out[reg] = (len(g), med([x["r_pc"] for x in g]), med([x["r_core"] for x in g]))
    for s in aw.SENSORS:
        for reg in ("C0", "K"):
            g = [x for x in f if x["s"] == s and x["reg"] == reg]
            out[f"{s}|{reg}"] = (len(g), med([x["r_pc"] for x in g]), med([x["r_core"] for x in g]))
    return out

def main():
    res = {}
    for nom, win in {"ventana_run_1014": ("2026-08-15", "2026-10-14"),
                     "ventana_hoy": ("2026-08-20", "2026-10-19")}.items():
        filas = correr(win)
        res[nom] = {"win": win, "global": resumen(filas),
                    "por_volcan": {v: resumen(filas, v) for v in aw.VOLS}}
        print(f"\n===== {nom} {win}  (n, mediana pc.vrp_mw, mediana con f5_core en V375)")
        for v in aw.VOLS:
            r = res[nom]["por_volcan"][v]
            print(f"  {v:20s} todo={r['todo']}  C0={r['C0']}  K={r['K']}")
        if nom == "ventana_hoy":
            print("\n  Tupungatito por sensor x regimen:")
            for k, x in res[nom]["por_volcan"]["Tupungatito"].items():
                print("   ", k, x)
            tup = sorted([x for x in filas if x["vol"] == "Tupungatito"], key=lambda x: x["date"])
            print("\n  Tupungatito noche a noche:")
            for x in tup:
                print(f"    {x['date']} {x['s']:9s} {x['reg']} rec={x['reg_records']} mir={x['mir']:.3f} r_pc={x['r_pc']:.3f} r_core={x['r_core']:.3f}")
            res[nom]["tupungatito_noches"] = tup
        else:
            tup = sorted([x for x in filas if x["vol"] == "Tupungatito"], key=lambda x: x["date"])
            res[nom]["tupungatito_noches"] = tup
    json.dump(res, open(os.path.join(os.path.dirname(__file__), "auto_audit_estratificado.json"), "w", encoding="utf-8"), indent=1)

main()
