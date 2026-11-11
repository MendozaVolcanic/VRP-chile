# -*- coding: utf-8 -*-
"""Poblacion del A/B de MOD-D por etiqueta y por volcan. Fuente:
git show origin/claude/s170-modd-f4-procedencia:experiments/_s166_modd_f4/poblacion_f4.json, guardado en
D:/vrp-trabajo/temporales/s179-audit/a/poblacion_f4.json. Control: el sha256 tiene que empezar por e8315ba4ff93,
el prefijo que cita la regla sellada. Denominador: las 5.709 pasadas MODIS nocturnas del A/B (2026-03-01 a 2026-10-26)."""
import io, sys, json, collections, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
raw = open("D:/vrp-trabajo/temporales/s179-audit/a/poblacion_f4.json", "rb").read()
d = json.loads(raw.decode("utf-8"))
print("poblacion_f4.json (rama claude/s170-modd-f4-procedencia) sha256:", hashlib.sha256(raw).hexdigest())
print("ventanas:", json.dumps(d["ventanas"], ensure_ascii=False)[:300])
P = d["pasadas"]
print("pasadas:", len(P), "| por etiqueta:", dict(collections.Counter(x["lab"] for x in P)), "| por tramo:", dict(collections.Counter(x["tramo"] for x in P)))
for lab in ("protegida", "bajo1"):
    print(lab, "por volcan:", dict(collections.Counter(x["vol"] for x in P if x["lab"] == lab)))
print("volcanes sin ninguna alerta (protegida o bajo1):", sorted(set(x["vol"] for x in P) - set(x["vol"] for x in P if x["lab"] in ("protegida", "bajo1"))))
