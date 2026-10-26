# -*- coding: utf-8 -*-
"""Verificador: (1) errores de K escondidos: probe_portes.py:356-357 guarda una excepcion de K en r['K']['error'] sin
cambiar estado, asi que una pasada 'ok' podria no tener record K; cuento esas. (2) Control de instrumento contra S159
leido directo de los JSON de S159 (npix, vrp a 1e-6, mismo granulo). (3) Granulo del objetivo vs granulo realmente
leido (nativo.l1b) en todas las pasadas. Pregunta 1: un K sin record o un granulo distinto saldria listado.
Pregunta 2: imprimo denominadores."""
import json, sys, collections
from pathlib import Path
D, RUN, S159 = (Path(a) for a in sys.argv[1:4])
obj = {o["id"]: o for o in json.loads((D / "objetivos_neg_resto_modis.json").read_text(encoding="utf-8"))}
def cargar(root):
    out = {}
    for f in sorted(root.rglob("resultados_MODIS_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")): out[r["id"]] = r
    return out
res = cargar(RUN); prev = cargar(S159)
ok = [r for r in res.values() if r.get("estado") == "ok"]
print("estado ok:", len(ok), "| K con 'error':", sum(1 for r in ok if "error" in (r.get("K") or {})), "| K sin record:", sum(1 for r in ok if (r.get("K") or {}).get("record") is None), "| con 'traza':", sum(1 for r in res.values() if "traza" in r))
print("granulo del objetivo != granulo leido (nativo.l1b):", [(i, obj[i]["granule"], r["nativo"]["l1b"]) for i, r in res.items() if r.get("nativo") and r["nativo"]["l1b"] != obj[i]["granule"]])
print("granulo del objetivo != r['granule']:", [(i) for i, r in res.items() if r.get("granule") != obj[i]["granule"]])
print("objetivos con granulo NRT:", sum(".NRT." in o["granule"] for o in obj.values()), "de", len(obj), "| leidos NRT:", sum(".NRT." in (r.get("nativo") or {}).get("l1b", "") for r in res.values()))
print("\ncontrol contra S159 (lectura directa de", S159.name, "):")
ctl = [i for i, o in obj.items() if o["clase"] == "control_s159"]
ig = 0
for i in sorted(ctl):
    a = res[i]["port"]["fisica"]; b = (prev.get(i) or {}).get("port", {}).get("fisica")
    if b is None: print("  ", i, "SIN DATO en S159"); continue
    same = a["npix"] == b["npix"] and ((a["vrp_mw"] is None and b["vrp_mw"] is None) or abs((a["vrp_mw"] or 0) - (b["vrp_mw"] or 0)) < 1e-6)
    samepx = a.get("pixeles") == b.get("pixeles")
    gran = res[i].get("granule") == prev[i].get("granule")
    ig += same
    print(f"   {i} {obj[i]['volcan']} {obj[i]['hora_utc']} {obj[i]['clase_s159']}: npix {a['npix']}/{b['npix']} vrp {a['vrp_mw']}/{b['vrp_mw']} {'IGUAL' if same else 'DISTINTO'} pixeles {'iguales' if samepx else 'DISTINTOS'} granulo {'igual' if gran else 'DISTINTO'} | K pc {((res[i]['K']['record'] or {}).get('primary_cluster') or {}).get('vrp_mw')} / S159 K pc {(((prev[i].get('K') or {}).get('record') or {}).get('primary_cluster') or {}).get('vrp_mw')}")
print("iguales:", ig, "de", len(ctl))
# 38 neg_resto de S159 en el run de S159: evaluables y npix (reproduce el 0 de 36 del prereg)
o159 = {o["id"]: o for o in json.loads((Path(sys.argv[4]) / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8"))}
n159 = [i for i, o in o159.items() if o.get("b") == "MODIS" and o.get("clase") == "neg_resto"]
ev = [i for i in n159 if prev.get(i, {}).get("estado") == "ok" and (prev[i]["port"]["fisica"] or {}).get("motivo_vacio") != "escena_invalida" and prev[i].get("port_estado") != "grilla_incompleta"]
print("S159 neg_resto MODIS:", len(n159), "con resultado", sum(i in prev for i in n159), "evaluables", len(ev), "npix>0 en fisica:", sum(1 for i in ev if (prev[i]["port"]["fisica"] or {}).get("npix")))
