# -*- coding: utf-8 -*-
"""Paso 7: junta s1 (posiciones), s4 (radio e imagen), s5 (pixeles) y s6 (nulo) en tablas markdown para INFORME.md.
No calcula nada nuevo salvo conteos."""
import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
A = {r["k"]: r for r in json.load(open("s4_analisis.json", encoding="utf-8"))["filas"]}
P = {r["k"]: r for r in json.load(open("s5_pixeles.json", encoding="utf-8"))}
N = json.load(open("s6_nulo.json", encoding="utf-8"))
pct = collections.defaultdict(dict)
for k, tipo, n, p in N: pct[k][tipo] = p
ORD = sorted(A, key=lambda k: (A[k]["vol"], A[k]["s"], A[k]["t"]))
L = []
L.append("| # | volcán | sensor | fecha UTC | prot. A | C0: lat, lon | C0: km, rumbo | K: lat, lon | K: km, rumbo | MIROVA Distancia_km (fuente) | radio: compatible | píxeles: K respecto de C0 | imagen MIROVA (tipo, pct nulo) |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for i, k in enumerate(ORD, 1):
    a, p = A[k], P[k]
    c, kk = a["C0"], a["K"]
    rad = {"ambos compatibles": "ambos", "ninguno compatible": "ninguno", "solo C0 compatible": "sólo C0",
           "solo K compatible": "sólo K", "sin distancia": "s/d"}[a["veredicto_radio"]]
    pix = "mismo píxel caliente (C0 n=%s, K n=%s)" % (p["C0"]["n_pc"], p["K"]["n_pc"]) if p["clase"].startswith("mismo") else \
          "otro lugar (a %.1f km del píxel de C0 más cercano)" % p["K_centro_a_px_C0"]
    if a["imagenes"]:
        im = []
        for img in a["imagenes"]:
            pv = pct[k].get(img["tipo"])
            nom = {"propia": "propia, mismo gránulo", "otra": "otra pasada %+d min" % img["dt_min"], "reciclada": "reciclada (md5 anterior)"}[img["tipo"]]
            ver = "sin objeto"
            if "obj" in img:
                dc, dk = img["C0_a_obj"], img["K_a_obj"]
                ver = "K más cerca" if dk < dc - 0.3 else ("K más lejos" if dk > dc + 0.3 else "igual")
            im.append("%s: %s, pct %s" % (nom, ver, "%.2f" % pv if pv is not None else "-"))
        imtxt = "; ".join(im)
    else:
        imtxt = "sin imagen"
    md = "%s (%s)" % (a["mir_dist"], a["mir_fuente"]) if a["mir_dist"] is not None else "s/d"
    if a["mir_fuente"] == "OCR": md += ", sólo OCR"
    L.append("| %d | %s | %s | %s | %s | %.4f, %.4f | %.2f, %s | %.4f, %.4f | %.2f, %s | %s | %s | %s | %s |" % (
        i, a["vol"], a["s"], a["t"], "sí" if a["prot_A"] else "no", c["lat"], c["lon"], c["d_vent"], c["card"],
        kk["lat"], kk["lon"], kk["d_vent"], kk["card"], md, rad, pix, imtxt))
open("tabla_movidas.md", "w", encoding="utf-8").write("\n".join(L) + "\n")

# resumen por volcan y sensor
g = collections.defaultdict(collections.Counter)
for k in ORD:
    a, p = A[k], P[k]; key = (a["vol"], a["s"])
    g[key]["n"] += 1; g[key]["prot"] += a["prot_A"]
    g[key]["mismo" if p["clase"].startswith("mismo") else "otro"] += 1
    g[key]["hacia_crater"] += a["K"]["d_vent"] < a["C0"]["d_vent"]
    g[key]["rad_" + a["veredicto_radio"]] += 1
    g[key]["img_" + a["veredicto_imagen"]] += 1
R = ["| volcán | sensor | movidas | protegidas | mismo píxel caliente | K en otro lugar | K más cerca del cráter | radio: sólo K / sólo C0 / ambos / ninguno | imagen: K cerca / K lejos / igual / sin imagen |",
     "|---|---|---|---|---|---|---|---|---|"]
tot = collections.Counter()
for key in sorted(g):
    x = g[key]; tot.update(x)
    R.append("| %s | %s | %d | %d | %d | %d | %d | %d / %d / %d / %d | %d / %d / %d / %d |" % (
        key[0], key[1], x["n"], x["prot"], x["mismo"], x["otro"], x["hacia_crater"],
        x["rad_solo K compatible"], x["rad_solo C0 compatible"], x["rad_ambos compatibles"], x["rad_ninguno compatible"],
        x["img_K acerca"], x["img_K aleja"], x["img_indistinto"], x["img_sin imagen"]))
x = tot
R.append("| **total** | | %d | %d | %d | %d | %d | %d / %d / %d / %d | %d / %d / %d / %d |" % (
    x["n"], x["prot"], x["mismo"], x["otro"], x["hacia_crater"],
    x["rad_solo K compatible"], x["rad_solo C0 compatible"], x["rad_ambos compatibles"], x["rad_ninguno compatible"],
    x["img_K acerca"], x["img_K aleja"], x["img_indistinto"], x["img_sin imagen"]))
open("tabla_resumen.md", "w", encoding="utf-8").write("\n".join(R) + "\n")
print("\n".join(R))
# radio en los casos de otro lugar
o = collections.Counter(A[k]["veredicto_radio"] for k in ORD if not P[k]["clase"].startswith("mismo"))
m = collections.Counter(A[k]["veredicto_radio"] for k in ORD if P[k]["clase"].startswith("mismo"))
print("radio en 'otro lugar':", dict(o)); print("radio en 'mismo pixel':", dict(m))
# mismo pixel: es el pixel mas caliente de C0?
print("mismo pixel y hot C0 == hot K:", sum(1 for k in ORD if P[k]["clase"].startswith("mismo") and P[k]["hot_C0_K_km"] is not None and P[k]["hot_C0_K_km"] < 0.01),
      "de", sum(1 for k in ORD if P[k]["clase"].startswith("mismo")))
print("K de un solo pixel:", sum(1 for k in ORD if P[k]["K"]["n_pc"] == 1), "| C0 multi-pixel en 'mismo':",
      sum(1 for k in ORD if P[k]["clase"].startswith("mismo") and (P[k]["C0"]["n_pc"] or 0) > 1))
