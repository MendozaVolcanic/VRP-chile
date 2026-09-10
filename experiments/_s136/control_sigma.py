"""S136 - control de instrumento: el sigma_dNTI de MODIS 5x el de VIIRS, es real o es mi medicion?

La observacion que iba a motivar un run de Actions: MODIS tiene sigma_dNTI 0,00697 contra 0,00137
de VIIRS375, o sea 5 veces mas rugoso teniendo el pixel casi 3 veces mas grande. Contraintuitivo.
PERO que_rama_manda.py NO separo dia de noche, y el sol infla el MIR. Si MODIS trae mas
proporcion de pasadas diurnas que VIIRS, el 5x es artefacto de mi propia medicion.

Tambien controlo el otro sospechoso: la ALTITUD. Los volcanes con MODIS pueden no ser los mismos
que dominan VIIRS, y un fondo de altura frio cambia el NTI (A68).
READ-ONLY.
"""
import os, sys, json, statistics as st
from collections import defaultdict
ROOT = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
from run_pipeline import is_nighttime
import yaml
from datetime import datetime

vc = yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))
coord = {v["name"]: (float(v["lat"]), float(v["lon"])) for v in vc["volcanoes"]}
TIER_A = ["Villarrica","Lascar","Isluga","NevadosDeChillan","Llaima","Chaiten","Copahue",
          "Lastarria","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito"]

def bucket(s):
    if not s: return None
    if s.startswith("MODIS"): return "MODIS"
    if s.startswith("VIIRS"): return "V750" if s.endswith("_750") else "V375"
    return None

d = defaultdict(lambda: {"noche": [], "dia": [], "sin_hora": 0})
porvol = defaultdict(lambda: defaultdict(list))
for vol in TIER_A:
    p = os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json")
    if not os.path.exists(p): continue
    recs = json.load(open(p, encoding="utf-8"))
    recs = recs.get("records", recs)
    la, lo = coord.get(vol, (None, None))
    for r in recs:
        b = bucket(r.get("sensor")); sd = r.get("diag_sd_dnti")
        if b is None or not isinstance(sd, (int, float)): continue
        ts = r.get("datetime_utc")
        if not ts or la is None:
            d[b]["sin_hora"] += 1; continue
        # el schema guarda "2025-02-15 03:15": espacio, sin segundos y sin la T de ISO.
        dt = None
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(ts[:len("2025-02-15 03:15:00")].strip(), fmt); break
            except ValueError:
                continue
        if dt is None:
            d[b]["sin_hora"] += 1; continue
        clave = "noche" if is_nighttime(la, lo, dt) else "dia"
        d[b][clave].append(sd)
        if clave == "noche": porvol[b][vol].append(sd)

print("sigma del dNTI, separando dia de noche (lo que no hice la primera vez)\n")
print(f"{'sensor':8s} {'n noche':>8s} {'sd NOCHE':>10s} {'n dia':>7s} {'sd DIA':>9s} {'sin hora':>9s}")
print("-" * 58)
for b in ("MODIS", "V750", "V375"):
    k = d.get(b)
    if not k: continue
    mn = st.median(k["noche"]) if k["noche"] else float("nan")
    md = st.median(k["dia"]) if k["dia"] else float("nan")
    print(f"{b:8s} {len(k['noche']):8d} {mn:10.5f} {len(k['dia']):7d} {md:9.5f} {k['sin_hora']:9d}")

print("\nel 5x sobrevive al control? (cociente MODIS / V375, solo NOCHE)")
if d["MODIS"]["noche"] and d["V375"]["noche"]:
    r = st.median(d["MODIS"]["noche"]) / st.median(d["V375"]["noche"])
    print(f"  {r:.2f}x")

print("\ny por volcan, de noche: los mismos volcanes dominan cada sensor? (A68, altitud)")
for b in ("MODIS", "V375"):
    tot = sum(len(v) for v in porvol[b].values())
    top = sorted(porvol[b].items(), key=lambda kv: -len(kv[1]))[:4]
    print(f"  {b:6s} n={tot:5d}  " + " · ".join(
        f"{v}({len(s)}, sd {st.median(s):.5f})" for v, s in top))
