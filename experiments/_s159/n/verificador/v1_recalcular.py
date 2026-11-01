# -*- coding: utf-8 -*-
"""Verificador S159 frente N, paso 1: recalcula desde los resultados crudos del workflow (no desde la tabla del
agente) la publicacion de cada brazo con el predicado del tablero (node), y la compara con tabla_por_pasada.csv.

P1 (si lo medido estuviera roto, se veria?): si el predicado o la lectura de records estuvieran mal, la publicacion
recalculada no coincidiria con la del agente o con la de produccion (pub_prod de data/). Control positivo: F cambia
el cumulo en pasadas donde K tiene 0,0 MW (Lascar 10-08), asi que una comparacion F contra K tiene que dar distinto.
P2 (instrumento muerto): si node no corriera, correr_node devuelve vacio y el script aborta (assert de largo).
Uso: python v1_recalcular.py
"""
import collections, csv, io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
N = AQUI.parent
ROOT = N.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B, clase_mirova as CM

obj = {o["id"]: o for o in json.loads((N / "objetivos_n.json").read_text(encoding="utf-8"))}
res = {}
for f in sorted((N / "run_39682867040").glob("*resultados_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r.get("estado") == "ok" or r["id"] not in res:
            res[r["id"]] = r
inner = B.inner_desde_html()
BR = ("K", "K2", "C", "F", "FC")
casos, idx = [], []
for i, r in res.items():
    for b in BR:
        rec = ((r.get("brazos") or {}).get(b) or {}).get("record")
        if rec is None:
            continue
        s = {k: rec.get(k) for k in B.CAMPOS_JS if k != "anomaly_pixels"}; s["anomaly_pixels"] = []
        casos.append([s, inner[obj[i]["volcan"]]]); idx.append((i, b))
pred = B.correr_node(casos)
assert len(pred) == len(casos) and len(casos) > 0
P = {k: bool(p[4]) for k, p in zip(idx, pred)}
ok = [i for i, r in res.items() if r.get("estado") == "ok" and r.get("brazos")
      and all("error" not in (r["brazos"].get(b) or {"error": 1}) for b in BR)]
print("pasadas ok con 5 brazos:", len(ok), "| estados no ok:",
      collections.Counter(r.get("estado") for r in res.values() if r.get("estado") != "ok"))
pub = lambda i, b: P.get((i, b), False)
tab = {int(f["id"]): f for f in csv.DictReader(open(N / "tabla_por_pasada.csv", encoding="utf-8"))}
dis = [(i, b) for i in ok for b in BR if str(pub(i, b)) != tab[i][f"{b}_pub"]]
print("publicacion recalculada distinta de la tabla del agente:", len(dis), dis[:5])
# control: K contra produccion (data/)
dk = [i for i in ok if pub(i, "K") != bool(obj[i]["pub_prod"])]
dv = [i for i in ok if (obj[i]["pc_vrp"] is None) != (((res[i]["brazos"]["K"]["record"] or {}).get("primary_cluster") or {}).get("vrp_mw") is None)
      or (obj[i]["pc_vrp"] is not None and abs(obj[i]["pc_vrp"] - res[i]["brazos"]["K"]["record"]["primary_cluster"]["vrp_mw"]) > 0.001)]
print("K publica distinto que produccion:", len(dk), "| pc.vrp_mw distinto:", len(dv))
# nulo K2
print("K2 record distinto de K:", sum(json.dumps(res[i]["brazos"]["K"]["record"], sort_keys=True)
                                       != json.dumps(res[i]["brazos"]["K2"]["record"], sort_keys=True) for i in ok))
# control positivo de la comparacion: F contra K en el record completo
print("F record distinto de K (control positivo, tiene que ser > 0):",
      sum(json.dumps(res[i]["brazos"]["F"]["record"], sort_keys=True) != json.dumps(res[i]["brazos"]["K"]["record"], sort_keys=True) for i in ok))
# protegida y decide recalculadas desde la lista de filas de MIROVA de cada pasada
mal = []
for i in ok:
    o = obj[i]
    if o["lab"] != "pos":
        continue
    prot = any(CM.alerta_protegida({"tipo": m["tipo"], "vrp_mw": m["vrp_mw"]}) for m in o["mirova"])
    if prot != bool(o["protegida"]):
        mal.append((i, o["volcan"], o["hora_utc"], o["protegida"], o["mirova"]))
print("protegida recalculada distinta:", len(mal), mal[:3])
# publicacion por brazo contra K, todas las pasadas ok
for b in ("C", "F", "FC"):
    c = collections.Counter((obj[i]["clase"], pub(i, "K"), pub(i, b)) for i in ok)
    print(b, "contra K (clase, K, X): n", {k: v for k, v in sorted(c.items()) if k[1] != k[2]})
print("F distinto de FC en publicacion:", sum(pub(i, "F") != pub(i, "FC") for i in ok))
json.dump({"P": {f"{i}|{b}": v for (i, b), v in P.items()}, "ok": ok}, open(AQUI / "v1_pub.json", "w"))
