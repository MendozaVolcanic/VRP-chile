# -*- coding: utf-8 -*-
"""P12 (F5b): resumen de p8_clases.json para el informe: clases por volcán y sensor (protegidas aparte), motivos de (iv),
distribución de d_png_nuestro, lista de (iii) y de protegidas (iii)/(iv), prominencia del píxel elegido, láminas usadas.
Sólo lee; no baja nada. Salida: p12_resumen.out.txt (stdout)."""
import collections, json, os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
H = os.path.dirname(os.path.abspath(__file__))
o = [x for x in json.load(open(os.path.join(H, "p8_clases.json"), encoding="utf-8")) if x.get("vol") != "_CONTROL_"]
print("total aciertos clasificados:", len(o), " errores:", sum(1 for x in o if str(x.get("motivo_iv", "")).startswith("error:")))
orden = sorted({(x["vol"], x["b"]) for x in o}, key=lambda k: (k[0] != "NevadosDeChillan", k))
print("\n| volcán | sensor | n | (i) | (iii) | (iv) | prot n | prot (i) | prot (iii) | prot (iv) | control con dist. OCR (?) | mediana d_png_nuestro km (i+iii) |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
tot = collections.Counter()
for vol, b in orden:
    g = [x for x in o if (x["vol"], x["b"]) == (vol, b)]
    c = collections.Counter(x["clase"].rstrip("?") for x in g)
    p = [x for x in g if x.get("protegida") == "True"]
    cp = collections.Counter(x["clase"].rstrip("?") for x in p)
    d = [x["d_png_nuestro_km"] for x in g if x["clase"].rstrip("?") in ("i", "iii")]
    print(f"| {vol} | {b} | {len(g)} | {c['i']} | {c['iii']} | {c['iv']} | {len(p)} | {cp['i']} | {cp['iii']} | {cp['iv']} | {sum(1 for x in g if x['clase'].endswith('?'))} | {np.median(d):.2f} |" if d else
          f"| {vol} | {b} | {len(g)} | {c['i']} | {c['iii']} | {c['iv']} | {len(p)} | {cp['i']} | {cp['iii']} | {cp['iv']} | {sum(1 for x in g if x['clase'].endswith('?'))} | sin casos |")
    for k, v in c.items(): tot[(b, k)] += v
print("\ntotales por sensor:", dict(tot))
print("\nmotivos (iv):")
for k, v in collections.Counter((x["b"], str(x.get("motivo_iv", "")).split(" (")[0]) for x in o if x["clase"] == "iv").most_common(): print("  ", k, v)
print("\n(iii) y (iii?) listados (vol, sensor, dt, vrp, prot, dist tabla, fuente, d_png_mc, d_png_nuestro, prominencia, mancha_px, panel, lámina):")
for x in sorted([x for x in o if x["clase"].startswith("iii")], key=lambda x: (x["vol"], x["dt"])):
    print("  ", x["vol"], x["sensor"], x["dt"], x["vrp_mirova"], x["protegida"], x["dist_mirova"], x["fuente_dist"], x.get("d_png_mirova_center_km"), x.get("d_png_nuestro_km"), x.get("prominencia"), x.get("mancha_px"), x.get("panel"), str(x.get("png", "")).split("/")[-1])
print("\nprotegidas (iv) con lámina y panel pero control fallido (vol, sensor, dt, vrp, dist tabla, fuente, d_png_mc, d_png_nuestro, prominencia):")
for x in sorted([x for x in o if x["clase"] == "iv" and x.get("protegida") == "True" and x.get("d_png_mirova_center_km") is not None], key=lambda x: (x["vol"], x["dt"])):
    print("  ", x["vol"], x["sensor"], x["dt"], x["vrp_mirova"], x["dist_mirova"], x["fuente_dist"], x.get("d_png_mirova_center_km"), x.get("d_png_nuestro_km"), x.get("prominencia"))
print("\nprotegidas (iv) sin lámina/panel:")
for x in sorted([x for x in o if x["clase"] == "iv" and x.get("protegida") == "True" and x.get("d_png_mirova_center_km") is None], key=lambda x: (x["vol"], x["dt"])):
    print("  ", x["vol"], x["sensor"], x["dt"], x["vrp_mirova"], x.get("motivo_iv"), x.get("laminas_vistas"))
vi = [x for x in o if x["clase"].rstrip("?") in ("i", "iii") and x["b"] != "MODIS"]
d = np.array([x["d_png_nuestro_km"] for x in vi]); pr = np.array([x["prominencia"] for x in vi])
print("\nVIIRS con clase (i)/(iii): n=%d; d_png_nuestro p50 %.2f p90 %.2f max %.2f km; prominencia (lum max - p99 panel) p10 %.0f p50 %.0f; con prominencia < 0: %d" % (len(vi), np.median(d), np.percentile(d, 90), d.max(), np.percentile(pr, 10), np.median(pr), (pr < 0).sum()))
print("lag lámina (h) p50 %.1f p90 %.1f max %.1f; paneles usados:" % tuple(np.percentile([x["lag_lamina_h"] for x in o if "lag_lamina_h" in x], [50, 90, 100])), collections.Counter(x.get("panel") for x in o if "panel" in x))
print("láminas distintas usadas:", len({x.get("png") for x in o if x.get("png")}), " | por sensor:", collections.Counter(x["b"] for x in o if x.get("png")))
