# -*- coding: utf-8 -*-
"""Verificador: misma derivacion que v03 pero sin el 17 al 20 de octubre (exclusion declarada en PREREGISTRO §2).
Debe dar neg_resto 5.093, marco 5.055, pos_prot 50, K 39 de 5.132."""
import json, sys, collections
from pathlib import Path
ARB = Path(sys.argv[1])
pob = json.loads((ARB / "experiments/_s159/portes/poblacion_completa.json").read_text(encoding="utf-8"))
P = [p for p in pob["pasadas"] if p["b"] == "MODIS" and not ("2026-10-17" <= p["hora_utc"][:10] <= "2026-10-20")]
def clase(p):
    alg = any("RUTINA" not in m["tipo"] for m in p["mirova"])
    if alg: return "pos_prot" if p.get("protegida") else "pos_bajo"
    return "neg_pub" if p["pub_prod"] else "neg_resto"
C = collections.Counter(clase(p) for p in P)
print("sin 17-20 oct: pasadas", len(P), "clases", C)
o159 = json.loads((ARB / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8"))
n159 = {(o["volcan"], o["hora_utc"]) for o in o159 if o.get("b") == "MODIS" and o.get("clase") == "neg_resto"}
print("marco = estrato - 38 de S159 =", C["neg_resto"] - len(n159), "| K en negativos limpios", C["neg_pub"], "de", C["neg_pub"] + C["neg_resto"], round(C["neg_pub"]/(C["neg_pub"]+C["neg_resto"]), 4))
