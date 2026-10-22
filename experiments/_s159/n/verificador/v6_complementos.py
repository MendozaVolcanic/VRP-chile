# -*- coding: utf-8 -*-
"""Verificador S159 N, paso 6: censo de los elementos SIN DATO (337, 393, 394), censo de alertas de cumbre en 0,0 MW
en la poblacion (lo que F puede ganar), protegidas que deciden, y cota superior Clopper-Pearson para 0 de 140
negativos muestreados (lo que el oraculo podria encender sin que la muestra lo viera). Ventana: objetivos_n.json."""
import collections, json
from pathlib import Path
from scipy.stats import beta
N = Path(__file__).resolve().parent.parent
o = {x["id"]: x for x in json.load(open(N / "objetivos_n.json", encoding="utf-8"))}
for i in (337, 393, 394):
    print(i, {k: o[i][k] for k in ("clase", "protegida", "decide", "pc_vrp", "dc")})
p = [x for x in json.load(open(N / "poblacion_completa.json", encoding="utf-8"))["pasadas"] if x["hora_utc"][:10] not in ("2026-10-18", "2026-10-19")]
print("pos no publicados por prod (dc, pc==0, decide, protegida):", collections.Counter((x.get("dc"), x.get("pc_vrp") == 0.0 if x.get("pc_vrp") is not None else None, x["decide"], x["protegida"]) for x in p if x["lab"] == "pos" and not x["pub_prod"]))
print("protegidas que deciden en la poblacion:", sum(1 for x in p if x["lab"] == "pos" and x["protegida"] and x["decide"]))
u = beta.ppf(0.975, 1, 140); print("CP sup 0/140:", round(u, 4), "x 5331.5 =", round(u * 5331.5, 1))
