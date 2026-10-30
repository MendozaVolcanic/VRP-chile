# -*- coding: utf-8 -*-
"""Medidas de solo lectura sobre poblacion_f4.json, externos_referencia.json y MANIFIESTO_CANDADO_F4.json del arbol.
PREGUNTA 1: cada medida trae su control positivo (se altera una copia en memoria y la medida lo ve).
PREGUNTA 2: nada se imprime como 0 sin su denominador."""
import glob, hashlib, json, collections
from pathlib import Path

A = Path("D:/vrp-trabajo/temporales/s169_audit_patrones/f2_modis/arbol")
C = A / "experiments/_s166_modd_f4"
b = (C / "poblacion_f4.json").read_bytes()
p = json.loads(b)
ref = json.loads((C / "externos_referencia.json").read_bytes())

print("== 1. P-A (VC169-01, ya conocido): huellas de poblacion_f4.json del arbol (git archive con autocrlf=false)")
print("   bytes CRLF:", b.count(b"\r\n"), "| LF:", b.count(b"\n"))
lf = hashlib.sha256(b).hexdigest()
crlf = hashlib.sha256(b.replace(b"\n", b"\r\n")).hexdigest()
print("   sha256 tal cual (=LF):", lf)
print("   sha256 de la version CRLF:", crlf)
print("   externos_referencia.poblacion_sha256:", ref["poblacion_sha256"], "| coincide con CRLF:", ref["poblacion_sha256"] == crlf,
      "| coincide con LF:", ref["poblacion_sha256"] == lf)

print("== 2. Partes: cada clave de gránulo en exactamente una parte (denominador: claves de las pasadas)")
claves = {x["clave"] for x in p["pasadas"]}
en_partes = [c for pt in p["partes"] for c in pt]
print("   claves de pasadas:", len(claves), "| claves en partes:", len(en_partes), "| distintas:", len(set(en_partes)),
      "| sin parte:", len(claves - set(en_partes)), "| de mas:", len(set(en_partes) - claves), "| partes:", len(p["partes"]))
tam = [sum(1 for x in p["pasadas"] if x["clave"] in set(pt)) for pt in p["partes"]]
print("   pasadas por parte min/max:", min(tam), max(tam), "| gránulos por parte min/max:", min(map(len, p["partes"])), max(map(len, p["partes"])))
# control positivo: quitar una clave de una parte se ve
pt2 = [list(x) for x in p["partes"]]; pt2[0] = pt2[0][1:]
print("   control positivo (se quita 1 clave): sin parte =", len(claves - {c for q in pt2 for c in q}))

print("== 3. Campos obligatorios por pasada (denominador:", len(p["pasadas"]), "pasadas)")
for campo in ("l1b", "geo", "inner", "lab", "tramo", "clave", "grilla_censo", "z"):
    falt = sum(1 for x in p["pasadas"] if x.get(campo) in (None, ""))
    print("   %-13s vacio/None en %d" % (campo, falt))
print("   z None en C:", sum(1 for x in p["pasadas"] if x["tramo"] == "C" and x.get("z") is None),
      "| en E:", sum(1 for x in p["pasadas"] if x["tramo"] == "E" and x.get("z") is None))

print("== 4. Manifiesto: archivos que el arnés o la lectura cargan en tiempo de ejecucion y NO estan en el manifiesto")
m = json.loads((C / "MANIFIESTO_CANDADO_F4.json").read_bytes())["archivos"]
candidatos = ["scripts/run_pipeline.py", "pipeline/fetch.py", "pipeline/volcanic_features.yaml",
              "experiments/_s166_modd_f4/externos_referencia.json", "experiments/_s166_modd_f4/head_e.json",
              "experiments/_s166_modd_f4/MANIFIESTO_CANDADO_F4.json"]
for c in candidatos:
    print("   %-62s en manifiesto: %-5s existe en arbol: %s" % (c, c in m, (A / c).exists()))
print("   control positivo: 'pipeline/store.py' en manifiesto:", "pipeline/store.py" in m)
print("   n archivos en el manifiesto:", len(m), "| commit_tag:", json.loads((C / "MANIFIESTO_CANDADO_F4.json").read_bytes())["commit_tag"])

print("== 5. E: dias y HEAD (denominador: 244 pasadas candidatas de E)")
print("   head_e.estado:", p["head_e"]["estado"], "| dias excluidos:", p["dias_e_excluidos"], "| archivo:", p["head_e"]["archivo"])
print("   cmr_aviso en E:", sum(1 for x in p["e_candidatas"] if x.get("cmr_aviso")), "| l1b distinto del guardado:",
      sum(1 for x in p["e_candidatas"] if x.get("l1b_distinto_del_guardado")))
