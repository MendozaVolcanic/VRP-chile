# -*- coding: utf-8 -*-
"""Recuenta las cotas que la regla §4 (i) y (ii) toma de resultado_f4.json (copia local, sha256 312e2050...4129d).

Pregunta 1 (¿vería algo roto?): si los conteos del JSON no fueran 12/10/2 y 42/39/3, este script imprime otros.
Pregunta 2 (¿instrumento muerto?): control positivo al final: contar con otra clase da otro número, y un filtro
imposible da 0 con la etiqueta CONTROL.
"""
import json
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open(sys.argv[1], encoding="utf-8"))
V = d["brazos"]["V"]
p2 = V["p2"]
disc = p2["discordantes"]
print("p2.estado", p2.get("estado"), "| neto", p2["neto"], "| B", p2["B"], "| p_gana", p2["p_gana"],
      "| p_pierde", p2.get("p_pierde"), "| metodo", p2.get("metodo"))
print("n discordantes:", len(disc))
print("valores de c:", Counter(x["c"] for x in disc))
print("clases (lab):", Counter(x["lab"] for x in disc))
for lab in sorted({x["lab"] for x in disc}):
    sub = [x for x in disc if x["lab"] == lab]
    print(f"  {lab}: {len(sub)} | c=+1 (a favor de la vía): {sum(1 for x in sub if x['c'] == 1)} | "
          f"c=-1 (a favor de K): {sum(1 for x in sub if x['c'] == -1)}")
print("suma de c (neto recontado):", sum(x["c"] for x in disc))
fechas = sorted(x["dt"] for x in disc)
print("ventana de los discordantes (dt mín/máx):", fechas[0], fechas[-1])
print("volcanes:", Counter(x["vol"] for x in disc))
# ¿qué significa c? mirar el campo 'metodo' y las dos primeras entradas
print("ejemplos:", disc[:2])
# Denominador: ¿hay total de pasadas por clase en el JSON?
for k in ("n", "n_pasadas", "denominador", "total", "por_clase", "clases"):
    for sec in (p2, V, d):
        if isinstance(sec, dict) and k in sec:
            print("posible denominador", k, "->", json.dumps(sec[k], ensure_ascii=False)[:400])
print("p1:", json.dumps(V.get("p1"), ensure_ascii=False)[:600])
print("p1b:", json.dumps(V.get("p1b"), ensure_ascii=False)[:600])
print("insumos_lectura:", json.dumps(d.get("insumos_lectura"), ensure_ascii=False)[:1200])
print("por_tramo claves:", list(d.get("por_tramo", {}).keys()) if isinstance(d.get("por_tramo"), dict) else d.get("por_tramo"))
print("chillan:", json.dumps(d.get("chillan"), ensure_ascii=False)[:1500])
print("chillan_por_tramo:", json.dumps(d.get("chillan_por_tramo"), ensure_ascii=False)[:1500])
print("razon_protegidas:", json.dumps(V.get("razon_protegidas"), ensure_ascii=False)[:600])
# CONTROL positivo: otra clase y filtro imposible
print("CONTROL otra clase (todas las no bajo1):", sum(1 for x in disc if x["lab"] != "bajo1"))
print("CONTROL filtro imposible (lab == 'no_existe'):", sum(1 for x in disc if x["lab"] == "no_existe"))
