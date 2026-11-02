# -*- coding: utf-8 -*-
"""Chillán en resultado_f4.json: ¿de dónde salen «0,56 de MIROVA» y «tres alertas protegidas de octubre»?
Pregunta 1: si los números fueran otros, se verían (se imprimen todos). Pregunta 2: control: la mediana de razon_b
tiene que ser distinta de la de razon_k, si no el instrumento no distingue brazos."""
import json, sys, statistics as st
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open(sys.argv[1], encoding="utf-8"))
ch = d["chillan"]
print("estado:", ch.get("estado"), "| brazo:", ch.get("brazo"), "| claves:", list(ch.keys()))
rec = ch.get("recuperadas", [])
print("recuperadas:", len(rec), [r["dt"] for r in rec], "| de octubre:", sum(1 for r in rec if r["dt"].startswith("2026-10")))
pares = ch.get("pares", [])
rk = [p["razon_k"] for p in pares]; rb = [p["razon_b"] for p in pares]
print(f"pares: {len(pares)} | mediana razon_k {st.median(rk):.3f} | mediana razon_b {st.median(rb):.3f} | media razon_k {st.fmean(rk):.3f}")
for k, v in ch.items():
    if k not in ("recuperadas", "pares"):
        print(" ", k, "->", json.dumps(v, ensure_ascii=False)[:300])
tr = d.get("chillan_por_tramo", {})
print("por tramo: protegidas", sum(t["protegidas"] for t in tr.values()), "pub_K", sum(t["pub_K"] for t in tr.values()), "pub_b", sum(t["pub_b"] for t in tr.values()))
print("0,56 aparece como razon_K del tramo:", [t for t, v in tr.items() if abs(v["razon_K"] - 0.56) < 0.005])
print("CONTROL medianas distintas:", st.median(rk) != st.median(rb))
