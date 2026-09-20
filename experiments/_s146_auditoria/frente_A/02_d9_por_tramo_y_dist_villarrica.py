# -*- coding: utf-8 -*-
"""S146 frente A, paso 2. Dos remediciones sobre data ya en disco (solo lectura):

(a) Cierre D9 (MIROVA_DIVERGENCES.md:515/534): "0 fuga, 0 con pc.vrp>5MW, 207 de 214 visibles frios
    path-D son MIROVA-confirmados". Se midio en mayo-jun 2026, ANTES de #535 (2026-08-28 23:00 UTC, se
    apago la mascara de nube BT<260K, A104). Se remide por tramo.
(b) H_S61_MIROVA_DIST_FIXED_VILLARRICA (HYPOTHESIS_LOG.md:361-373, "CONFIRMADA"): Distancia_km de
    Villarrica seria constante 0.84.

Las dos preguntas del instrumento:
 1. Si lo medido estuviera roto, esta prueba fallaria? (a) SI para la parte VISIBLE: si records frios
    path-D-only se publicaran con >5 MW o sin confirmacion MIROVA, salen contados. NO para "far no
    fuga": el predicado del dashboard devuelve 0 para todo far por definicion, asi que ese cero es
    tautologico y aca se reporta como tal, no como medicion. (b) SI: si fuese constante, saldria un
    unico valor.
 2. Si el instrumento estuviera muerto, se veria distinto? SI: se imprime n de records leidos, n con
    primary_cluster y n de filas MIROVA por volcan; con 0 en cualquiera el script aborta.
Predicado "publicado" = copia literal de mirovaEqVrp (frontend/index.html:1043-1064), sin F5.
Confirmacion MIROVA = misma familia de sensor, |dt|<=60 min, VRP_MW>0 en CONS u OCR (A11, A27).
"""
import csv, io, json, sys, collections
from datetime import datetime, timedelta
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[3]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ALIAS = {"Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Nevados de Chillan": "NevadosDeChillan"}
vols = {v["name"]: v for v in yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"] if v.get("radius_km") == 25}
assert len(vols) == 11, len(vols)

def fam(s):
    s = s.upper()
    if s.startswith("MODIS"): return "MODIS"
    if s.startswith("VIIRS"): return "VIIRS750" if (s.endswith("_750") or s == "VIIRS750") else "VIIRS375"
    return s

mir = collections.defaultdict(list); dist_vil = collections.Counter(); dist_vil_alerta = collections.Counter()
for p in [ROOT / "latest_consolidado.csv", ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"]:
    for r in csv.DictReader(open(p, encoding="utf-8")):
        v = ALIAS.get(r["Volcan"], r["Volcan"])
        try: vrp = float(r["VRP_MW"] or 0)
        except ValueError: continue
        if p.name.startswith("latest") and v == "Villarrica":
            dist_vil[r["Distancia_km"]] += 1
            if r["Tipo_Registro"] == "ALERTA_TERMICA": dist_vil_alerta[r["Distancia_km"]] += 1
        if vrp > 0 and r["Sensor"] != "VIIRS":
            mir[(v, fam(r["Sensor"]))].append(datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S"))
print("(b) Villarrica Distancia_km, CONS, todas las filas:", dist_vil.most_common(6), "n=", sum(dist_vil.values()))
print("(b) Villarrica Distancia_km, CONS, solo ALERTA_TERMICA:", dist_vil_alerta.most_common(12), "n=", sum(dist_vil_alerta.values()))
assert sum(dist_vil.values()) > 0
for k in mir: mir[k].sort()

CORTE = datetime(2026, 8, 28, 23, 0)
T = collections.defaultdict(lambda: collections.Counter()); mx = collections.defaultdict(float)
nrec = npc = 0
for name, v in vols.items():
    recs = json.load(open(ROOT / f"data/mirova_equivalent/{name}.json", encoding="utf-8"))["records"]
    inner = v.get("inner_radius_km", 10)
    for r in recs:
        nrec += 1
        pc = r.get("primary_cluster")
        if not pc: continue
        npc += 1
        t = datetime.fromisoformat(r["datetime_utc"][:19].replace("T", " "))
        if t < datetime(2026, 5, 1): continue
        tbg = r.get("t_bg_k")
        if tbg is None or r.get("diag_n_bt_path") is None: continue
        vis0 = (r.get("distance_class") in (None, "summit")) and not (pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] > inner) and (pc.get("vrp_mw") or 0) > 0
        tr0 = ("pre535 may-jun" if t < datetime(2026, 7, 1) else "pre535 jul-ago") if t < CORTE else "post535"
        ms = mir.get((name, fam(r["sensor"])), [])
        if vis0:
            T[tr0]["CTRL_visibles_todos"] += 1
            T[tr0]["CTRL_conf_60min"] += any(abs((m - t).total_seconds()) <= 3600 for m in ms)
            T[tr0]["CTRL_conf_3h"] += any(abs((m - t).total_seconds()) <= 10800 for m in ms)
            nd = r.get("diag_n_dnti_ctx_path") or 0
            if nd > 0 and nd >= (r.get("diag_n_bt_path") or 0) + (r.get("diag_n_nti_path") or 0) and tbg is not None and tbg < 262:
                T[tr0]["S113like_visibles"] += 1
                T[tr0]["S113like_conf_3h"] += any(abs((m - t).total_seconds()) <= 10800 for m in ms)
        frio_d = (r.get("diag_n_bt_path") == 0 and r.get("diag_n_nti_path") == 0 and tbg < 262 and (r.get("diag_n_dnti_ctx_path") or 0) > 0)
        if not frio_d: continue
        tramo = ("pre535 may-jun" if t < datetime(2026, 7, 1) else "pre535 jul-ago") if t < CORTE else "post535"
        vis = (r.get("distance_class") in (None, "summit")) and not (pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] > inner) and (pc.get("vrp_mw") or 0) > 0
        c = T[tramo]; c["frio_pathD_only"] += 1
        if r.get("distance_class") == "far": c["far"] += 1
        if vis:
            c["visible"] += 1
            if pc["vrp_mw"] > 5.0: c["visible_gt5MW"] += 1
            mx[tramo] = max(mx[tramo], pc["vrp_mw"])
            ok = any(abs((m - t).total_seconds()) <= 3600 for m in mir.get((name, fam(r["sensor"])), []))
            c["visible_confirmado_mirova"] += ok
            c["visible_" + name] += 1
print("records leidos", nrec, "| con primary_cluster", npc, "| claves mirova", len(mir))
assert nrec > 0 and npc > 0 and len(mir) > 0
for tr in sorted(T):
    c = T[tr]
    print(f"\n[{tr}] frio+pathD-only={c['frio_pathD_only']} far={c['far']} visible={c['visible']} "
          f"visible>5MW={c['visible_gt5MW']} max_vis={mx[tr]:.2f} confirmados={c['visible_confirmado_mirova']} "
          f"({100*c['visible_confirmado_mirova']/max(1,c['visible']):.1f} %)")
    print("   CONTROL:", {k: n for k, n in c.items() if k.startswith(("CTRL", "S113"))})
    print("   por volcan:", {k[8:]: n for k, n in c.items() if k.startswith("visible_") and k[8:] in vols})
