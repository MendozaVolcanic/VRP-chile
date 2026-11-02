# -*- coding: utf-8 -*-
"""Denominador de las cotas (i) y (ii): cuántas pasadas bajo1 y neg_limpio tiene la población del A/B de MOD-D
(poblacion_f4.json, sha256 e8315ba4..., el mismo insumo que resultado_f4.json declara). Pregunta 1: si la población
tuviera otras clases o conteos, se imprimen. Pregunta 2: control: el total por clase tiene que ser >= los discordantes
de esa clase (12 bajo1, 42 neg_limpio); si no, el campo que cuento no es la clase que decide."""
import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("tipo raíz:", type(d).__name__, "| claves:", list(d.keys())[:20] if isinstance(d, dict) else len(d))
def items_de(o):
    if isinstance(o, list): return o
    for k in ("pasadas", "poblacion", "filas", "items", "C", "E"):
        if isinstance(o, dict) and isinstance(o.get(k), list): return o[k]
    return []
if isinstance(d, dict) and all(isinstance(d.get(k), (list, dict)) for k in ("C", "E") if k in d):
    for parte in ("C", "E"):
        if parte in d:
            it = items_de(d[parte]); print(f"parte {parte}: n {len(it)}; ejemplo {json.dumps(it[0], ensure_ascii=False)[:300] if it else None}")
            for k in ("lab", "lab_union", "clase", "etiqueta", "tipo"):
                c = collections.Counter(str(x.get(k)) for x in it if isinstance(x, dict))
                if c and set(c) != {"None"}: print(f"   {k}: {dict(c)}")
it = items_de(d)
print("items planos:", len(it), "| ejemplo:", json.dumps(it[0], ensure_ascii=False)[:400] if it else None)
for k in ("lab", "lab_union", "clase", "etiqueta", "tipo", "tramo", "ventana"):
    c = collections.Counter(str(x.get(k)) for x in it if isinstance(x, dict))
    if c and set(c) != {"None"}: print(f"  {k}: {dict(c)}")
fechas = sorted(str(x.get("dt") or x.get("fecha_utc") or "") for x in it if isinstance(x, dict))
if fechas: print("ventana dt:", fechas[0], "a", fechas[-1])
