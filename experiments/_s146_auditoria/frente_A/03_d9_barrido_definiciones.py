# -*- coding: utf-8 -*-
"""S146 frente A, paso 3: el probe de S113 (207 de 214 visibles frios path-D = MIROVA-confirmados) no
quedo persistido. Se barren definiciones plausibles de "frio + path-D" sobre mayo-jun 2026 para ver si
ALGUNA reproduce ~97 %. Solo lectura.
 1. Si el enunciado fuese falso, esto lo mostraria? SI, si ninguna definicion se acerca. Limite: no puedo
    probar que S113 no uso otra definicion ni que la data de mayo-jun sea la misma (hubo reprocesos).
 2. Instrumento muerto? Se imprime la tasa de TODOS los visibles como control (esperado ~35-37 %, A83).
"""
import csv, io, json, sys, collections, bisect
from datetime import datetime
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[3]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ALIAS = {"Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Nevados de Chillan": "NevadosDeChillan"}
vols = {v["name"]: v for v in yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"] if v.get("radius_km") == 25}
def fam(s):
    s = s.upper()
    if s.startswith("MODIS"): return "MODIS"
    return "VIIRS750" if (s.endswith("_750") or s == "VIIRS750") else "VIIRS375"
mir = collections.defaultdict(list); mir_any = collections.defaultdict(list)
for p in [ROOT / "latest_consolidado.csv", ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"]:
    for r in csv.DictReader(open(p, encoding="utf-8")):
        v = ALIAS.get(r["Volcan"], r["Volcan"])
        try: vrp = float(r["VRP_MW"] or 0)
        except ValueError: continue
        if vrp <= 0: continue
        t = datetime.fromisoformat(r["Fecha_Satelite_UTC"][:19])
        mir_any[v].append(t)
        # CORRECCION DE INSTRUMENTO (hallada en la 1a corrida): la referencia no trae filas "VIIRS750" en
        # mayo-jun; trae "VIIRS375", "VIIRS" generico y "MODIS". Un record VIIRS750 nuestro no puede
        # confirmarse "por mismo sensor": se reporta APARTE como SIN DATO y "VIIRS" generico vale para 375.
        if r["Sensor"] == "VIIRS": mir[(v, "VIIRS375")].append(t)
        else: mir[(v, fam(r["Sensor"]))].append(t)
def near(lst, t, s): return any(abs((m - t).total_seconds()) <= s for m in lst)
DEFS = {
 "todos los visibles (control)": lambda r, tb, nb, nn, nd: True,
 "tbg<262, D>0, bt=0 y nti=0": lambda r, tb, nb, nn, nd: tb < 262 and nd > 0 and nb == 0 and nn == 0,
 "tbg<270, D>0, bt=0 y nti=0": lambda r, tb, nb, nn, nd: tb < 270 and nd > 0 and nb == 0 and nn == 0,
 "tbg<262, D>0 (cualquier otro path)": lambda r, tb, nb, nn, nd: tb < 262 and nd > 0,
 "tbg<270, D>0 (cualquier otro path)": lambda r, tb, nb, nn, nd: tb < 270 and nd > 0,
 "tbg<262, cualquier path": lambda r, tb, nb, nn, nd: tb < 262,
}
R = {k: collections.Counter() for k in DEFS}
PV = collections.defaultdict(collections.Counter)
for name, v in vols.items():
    inner = v.get("inner_radius_km", 10)
    for r in json.load(open(ROOT / f"data/mirova_equivalent/{name}.json", encoding="utf-8"))["records"]:
        pc = r.get("primary_cluster")
        if not pc or not (pc.get("vrp_mw") or 0) > 0: continue
        t = datetime.fromisoformat(r["datetime_utc"][:19].replace("T", " "))
        if not (datetime(2026, 5, 1) <= t < datetime(2026, 7, 1)): continue
        if r.get("distance_class") not in (None, "summit"): continue
        if pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] > inner: continue
        tb = r.get("t_bg_k")
        if tb is None: continue
        nb, nn, nd = (r.get("diag_n_bt_path") or 0), (r.get("diag_n_nti_path") or 0), (r.get("diag_n_dnti_ctx_path") or 0)
        for k0, f in DEFS.items():
            k = k0 + " | " + fam(r["sensor"])
            R.setdefault(k, collections.Counter())
            if f(r, tb, nb, nn, nd):
                c = R[k]; c["n"] += 1
                c["60min_mismo_sensor"] += near(mir.get((name, fam(r["sensor"])), []), t, 3600)
                c["noche_12h_mismo_sensor"] += near(mir.get((name, fam(r["sensor"])), []), t, 43200)
                if k0.startswith("tbg<262, cualquier"):
                    PV[name]["n"] += 1; PV[name]["conf60"] += near(mir.get((name, fam(r["sensor"])), []), t, 3600); PV[name][fam(r["sensor"])] += 1
                c["noche_12h_cualquier_sensor"] += near(mir_any.get(name, []), t, 43200)
print("ventana 2026-05-01..2026-06-30, records VISIBLES (predicado mirovaEqVrp), pc.vrp>0")
for k, c in sorted(R.items()):
    if "|" not in k: continue
    n = max(1, c["n"])
    print(f"{k:40} n={c['n']:5} | 60min={100*c['60min_mismo_sensor']/n:5.1f} % | noche mismo sensor={100*c['noche_12h_mismo_sensor']/n:5.1f} % | noche cualquier sensor={100*c['noche_12h_cualquier_sensor']/n:5.1f} %")
print()
print("por volcan, def tbg<262 cualquier path:")
for v, c in sorted(PV.items(), key=lambda kv: -kv[1]["n"]): print(f"  {v:22}", dict(c))
