# -*- coding: utf-8 -*-
"""Verificador: derivar el estrato neg_resto desde la poblacion congelada de S159 con mis propias manos (lab, tipos de
MIROVA, pub_prod) y comprobar que las 400 del lote estan dentro y que el estrato da 5.093 y el marco 5.055.
Pregunta 1: si una pasada del lote tuviera una alerta de MIROVA o pub_prod=1, aparece listada.
Pregunta 2: imprimo el total del estrato derivado; si el derivador no entendiera el formato daria 0."""
import json, sys, collections
from pathlib import Path
D = Path(sys.argv[1]); ARB = Path(sys.argv[2])
pob = json.loads((ARB / "experiments/_s159/portes/poblacion_completa.json").read_text(encoding="utf-8"))
print("meta:", json.dumps(pob["meta"], ensure_ascii=False)[:1200])
P = [p for p in pob["pasadas"] if p["b"] == "MODIS"]
print("pasadas MODIS:", len(P), "lab:", collections.Counter(p["lab"] for p in P), "decide:", collections.Counter(p["decide"] for p in P))
tipos = collections.Counter(m["tipo"] for p in P for m in p["mirova"])
print("tipos MIROVA:", tipos)
def es_alerta(t): return t not in ("RUTINA", "RUTINA_OCR") and "RUTINA" not in t
def clase(p):
    alg = any(es_alerta(m["tipo"]) for m in p["mirova"])
    if not p["mirova"]:
        return "sin_mirova"
    if alg:
        return "pos_prot" if p.get("protegida") else "pos_bajo"
    return "neg_pub" if p["pub_prod"] else "neg_resto"
C = collections.Counter(clase(p) for p in P)
print("clases derivadas (mi derivacion):", C)
print("lab vs mi clase:", collections.Counter((p["lab"], clase(p)) for p in P))
idx = {(p["volcan"], p["hora_utc"]): p for p in P}
obj = json.loads((D / "objetivos_neg_resto_modis.json").read_text(encoding="utf-8"))
neg = [o for o in obj if o["clase"] == "neg_resto"]
malas = []
for o in neg:
    p = idx[(o["volcan"], o["hora_utc"])]
    if clase(p) != "neg_resto" or p["pub_prod"] != 0 or not p["decide"]:
        malas.append((o["id"], o["volcan"], o["hora_utc"], clase(p), p["pub_prod"], p["decide"], [m["tipo"] for m in p["mirova"]]))
print("neg_resto del lote que mi derivacion NO clasifica neg_resto:", len(malas), malas[:10])
print("fuentes MIROVA en las 400:", collections.Counter(tuple(sorted({m["source"] for m in idx[(o["volcan"], o["hora_utc"])]["mirova"]})) for o in neg))
# las 38 de S159 en neg_resto fuera del marco
o159 = json.loads((ARB / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8"))
n159 = {(o["volcan"], o["hora_utc"]) for o in o159 if o.get("b") == "MODIS" and o.get("clase") == "neg_resto"}
print("neg_resto de S159 (MODIS):", len(n159), "| en el lote nuevo como neg_resto:", sum((o["volcan"], o["hora_utc"]) in n159 for o in neg))
print("marco = estrato - S159:", C["neg_resto"] - len(n159))
# por volcan en el estrato vs en la muestra
ev = collections.Counter(p["volcan"] for p in P if clase(p) == "neg_resto")
em = collections.Counter(o["volcan"] for o in neg)
print("por volcan estrato -> muestra (esperado prop. 400/5055):", {v: f"{ev[v]} -> {em[v]} (esp {400*ev[v]/5055:.1f})" for v in sorted(ev)})
ez = collections.Counter(p["estrato_z"] for p in P if clase(p) == "neg_resto")
print("por cenit estrato:", ez, "muestra:", collections.Counter(o["estrato_z"] for o in neg))
# K en todos los negativos limpios (R3 vara): neg_pub + neg_resto
print("K publica en negativos limpios:", C["neg_pub"], "de", C["neg_pub"] + C["neg_resto"], "=", round(C["neg_pub"] / (C["neg_pub"] + C["neg_resto"]), 4))
