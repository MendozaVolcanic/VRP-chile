# -*- coding: utf-8 -*-
"""I-05. Muestra manual de 24 pasadas (semilla 146), 2 por sensor y por rotulo del banco.

Para cada una: la fila CRUDA de la referencia (tal como esta en el CSV) y nuestro record.
P1: si el rotulo del banco no correspondiera a la fila, se ve a ojo aqui (la fila cruda va completa).
P2: la seleccion es por semilla fija y sobre las etiquetas recalculadas, no elegida a mano.
"""
import sys, io, json, csv, collections, random
from pathlib import Path
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
A = Path(__file__).parent
ROOT = A.parents[2]
DL = ROOT / "experiments/_s145_paridad/_dl_referencia"
RECS = json.load(open(A / "_cache_recs.json", encoding="utf-8"))
REF = [f for f in json.load(open(A / "_cache_ref.json", encoding="utf-8")) if not f["diurna"]]
ALIAS = {"Nevados de Chillan": "NevadosDeChillan", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle"}
BUCK = {"MODIS": "MODIS", "VIIRS375": "VIIRS375", "VIIRS": "VIIRS750"}
crudo = collections.defaultdict(list)
for nombre, src in (("registro_vrp_consolidado.csv", "TABLA"), ("registro_vrp_ocr.csv", "IMAGEN")):
    for r in csv.DictReader(open(DL / nombre, encoding="utf-8")):
        v = ALIAS.get(r["Volcan"], r["Volcan"])
        crudo[(v, BUCK.get(r["Sensor"]), r["Fecha_Satelite_UTC"][:16])].append((src, r))
ref_idx = collections.defaultdict(list)
ns = collections.defaultdict(lambda: [False, False])
for f in REF:
    ref_idx[(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])].append(f)
    d = ns[(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:10])]
    d[0] |= f["tipo"].startswith("ALERTA")
    d[1] |= f["tipo"].startswith("FALSO")
for r in RECS:
    k = (r["vol"], r["b"], r["dt"][:16].replace("T", " "))
    filas = ref_idx.get(k, [])
    a = ns.get((r["vol"], r["b"], k[2][:10]), [False, False])
    if any(f["tipo"].startswith("ALERTA") for f in filas):
        r["lab"] = "pos"
    elif any(f["tipo"].startswith("FALSO") for f in filas):
        r["lab"] = "far_ref"
    elif any(f["tipo"] == "RUTINA" and f["source"] == "CONS" for f in filas):
        r["lab"] = "neg_limpio" if not a[0] and not a[1] else "sin_info(RUTINA en noche con alerta)"
    else:
        r["lab"] = "sin_info(sin fila)"
    r["k"] = k
print("etiquetas:", dict(collections.Counter(r["lab"] for r in RECS)))
rng = random.Random(146)
extra = {}
for vol in {r["vol"] for r in RECS}:
    for x in json.load(open(ROOT / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]:
        extra[(vol, x.get("sensor"), x.get("datetime_utc"))] = x
n = 0
for b in ("MODIS", "VIIRS375", "VIIRS750"):
    for lab in ("pos", "neg_limpio", "far_ref", "sin_info(RUTINA en noche con alerta)", "sin_info(sin fila)"):
        cand = [r for r in RECS if r["b"] == b and r["lab"] == lab]
        for r in rng.sample(cand, min(2, len(cand))):
            n += 1
            x = extra[(r["vol"], r["sensor"], r["k"][2])]
            pc = x.get("primary_cluster") or {}
            print(f"\n--- M{n:02d} | {r['vol']} | {r['sensor']} | {r['k'][2]} UTC | rotulo del banco: {lab} | publica: {r['pub']} (magnitud mostrada {r['disp']})")
            for src, c in crudo.get(r["k"], []) or [("(ninguna fila de referencia a ese minuto)", {})]:
                print(f"    REF {src}: " + " | ".join(f"{kk}={c[kk]}" for kk in ("Fecha_Satelite_UTC", "Sensor", "VRP_MW", "Distancia_km", "Tipo_Registro", "Clasificacion Mirova", "Fecha_Proceso_GitHub") if kk in c)
                      + (f" | Nota={c.get('Nota_Validacion')}" if src == "IMAGEN" else ""))
            print(f"    NUESTRO: distance_class={x.get('distance_class')} vrp_mw={x.get('vrp_mw')} pc.vrp={pc.get('vrp_mw')} pc.dist_km={pc.get('centroid_dist_km')} pc.n_pix={pc.get('n_pixels')}"
                  f" n_anom={x.get('n_anomalous_pixels')} t_max={x.get('t_max_k')} t_bg={x.get('t_bg_k')} nti_max={x.get('nti_max')} zenit={x.get('sensor_zenith_deg')} test1={x.get('triggered_test1')} f5={x.get('f5_core_vrp_mw')} nube={x.get('cloud_fraction')}")
print("\ntotal en la muestra:", n)
