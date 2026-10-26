# -*- coding: utf-8 -*-
"""Verificador: que cuentan x y n. Objetivos del lote (413), clases, pub_prod, duplicados, ids, pertenencia al estrato
neg_resto de la poblacion congelada de S159, mapeo de los 13 controles al objetivo de S159 (misma pasada), pesos.
Pregunta 1: si los objetivos trajeran pasadas con pub_prod=1 o repetidas o fuera del estrato, esto lo imprime.
Pregunta 2: todos los conteos se imprimen con denominador; un archivo vacio daria 0 de 0 y se veria."""
import json, sys, collections, hashlib
from pathlib import Path
D = Path(sys.argv[1]); ARB = Path(sys.argv[2])
raw = (D / "objetivos_neg_resto_modis.json").read_bytes()
print("blob git del objetivos:", hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()[:8], "sha256", hashlib.sha256(raw).hexdigest()[:12])
obj = json.loads(raw)
print("total", len(obj), "claves:", sorted(obj[0].keys()))
print("por b:", collections.Counter(o["b"] for o in obj))
print("por clase:", collections.Counter(o["clase"] for o in obj))
print("por clase_s159 en control:", collections.Counter(o.get("clase_s159") for o in obj if o["clase"] == "control_s159"))
neg = [o for o in obj if o["clase"] == "neg_resto"]
print("neg_resto:", len(neg), "ids min/max", min(o["id"] for o in neg), max(o["id"] for o in neg))
print("pub_prod en neg_resto:", collections.Counter(o["pub_prod"] for o in neg))
print("pub_prod en control:", collections.Counter((o["clase_s159"], o["pub_prod"]) for o in obj if o["clase"] == "control_s159"))
print("pc_vrp en neg_resto no nulo:", sum(o["pc_vrp"] is not None for o in neg), "de", len(neg))
k = collections.Counter((o["volcan"], o["hora_utc"], o["sensor"]) for o in obj)
print("pasadas (volcan,hora,sensor) repetidas:", [x for x, c in k.items() if c > 1])
print("ids repetidos:", [i for i, c in collections.Counter(o["id"] for o in obj).items() if c > 1])
print("pesos neg_resto min/max/suma:", min(o["peso"] for o in neg), max(o["peso"] for o in neg), round(sum(o["peso"] for o in neg), 2))
print("ventana neg_resto:", min(o["hora_utc"] for o in neg), "a", max(o["hora_utc"] for o in neg))
print("17-20 oct en neg_resto:", [o["hora_utc"] for o in neg if "2026-10-17" <= o["hora_utc"][:10] <= "2026-10-20"])
print("partidas:", sum(bool(o.get("partida")) for o in neg))
print("grilla claves:", sorted(neg[0]["grilla"].keys()), "ej:", neg[0]["grilla"])
# pertenencia al estrato de la poblacion congelada de S159
pob = json.loads((ARB / "experiments/_s159/portes/poblacion_completa.json").read_text(encoding="utf-8"))
print("poblacion_completa tipo:", type(pob).__name__, (list(pob.keys())[:10] if isinstance(pob, dict) else len(pob)))
filas = pob if isinstance(pob, list) else next((v for v in pob.values() if isinstance(v, list)), None)
if filas is None:
    for kk, v in pob.items():
        print("  ", kk, type(v).__name__, (len(v) if hasattr(v, "__len__") else v))
else:
    print("fila ej:", {kk: filas[0][kk] for kk in list(filas[0])[:14]})
    mod = [f for f in filas if f.get("b") == "MODIS" or f.get("sensor", "").startswith("MODIS")]
    print("filas MODIS:", len(mod), "clases:", collections.Counter(f.get("clase") for f in mod))
    idx = {(f["volcan"], f["hora_utc"]): f for f in mod}
    fuera = [(o["id"], o["volcan"], o["hora_utc"]) for o in neg if (o["volcan"], o["hora_utc"]) not in idx]
    clase_pob = collections.Counter(idx[(o["volcan"], o["hora_utc"])].get("clase") for o in neg if (o["volcan"], o["hora_utc"]) in idx)
    print("neg_resto del lote que no estan en la poblacion:", fuera)
    print("clase en la poblacion de los 400:", clase_pob)
    pubk = collections.Counter(idx[(o["volcan"], o["hora_utc"])].get("pub_prod") for o in neg if (o["volcan"], o["hora_utc"]) in idx)
    print("pub_prod en la poblacion de los 400:", pubk)
# controles: misma pasada que en S159
o159 = {o["id"]: o for o in json.loads((ARB / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8"))}
for o in obj:
    if o["clase"] == "control_s159":
        r = o159.get(o["id"])
        same = r and r["volcan"] == o["volcan"] and r["hora_utc"] == o["hora_utc"] and r.get("b") == "MODIS"
        print("  control", o["id"], o["volcan"], o["hora_utc"], o["clase_s159"], "pub_prod", o["pub_prod"], "pc_vrp", o["pc_vrp"],
              "| S159:", (r["volcan"], r["hora_utc"], r.get("clase"), r.get("b")) if r else None, "MISMA" if same else "DISTINTA")
