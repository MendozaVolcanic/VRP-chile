# -*- coding: utf-8 -*-
"""P5 (F5b): universo de aciertos (alerta de MIROVA pareada a ±120 s con una pasada nuestra publicada) desde el
2026-09-22, tomado de experiments/_s175_audit/f5/i2_pares.csv (F5, base 752d348bc), por volcán y sensor.
Pregunta 2 del instrumento: el control es la fila total (881 según F5) y el recuento antes del 22-sep."""
import csv, collections, json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
H = os.path.dirname(os.path.abspath(__file__))
F5 = os.path.join(H, "..", "f5", "i2_pares.csv")
rows = list(csv.DictReader(open(F5, encoding="utf-8")))
print("total pares F5:", len(rows))
post = [r for r in rows if r["dt"] >= "2026-09-22"]
pre = [r for r in rows if r["dt"] < "2026-09-22"]
print("pre 2026-09-22:", len(pre), " post (>=):", len(post), " rango post:", min(r["dt"] for r in post), "a", max(r["dt"] for r in post))
c = collections.Counter((r["vol"], r["b"]) for r in post)
cp = collections.Counter((r["vol"], r["b"]) for r in post if r["protegida"] == "True")
cf = collections.Counter((r["vol"], r["b"], r["fuente_dist"]) for r in post)
print("por volcán y sensor (total / protegidas):")
for k in sorted(c): print("  ", k, c[k], "/", cp[k], " fuente_dist:", {f: n for (v, b, f), n in cf.items() if (v, b) == k})
print("clase F5 post:", collections.Counter(r["clase"] for r in post))
print("Lascar MODIS post:", [(r["dt"], r["vrp_mirova"], r["dist_mirova"], r["fuente_dist"], r["clase"]) for r in post if r["vol"] == "Lascar" and r["b"] == "MODIS"])
json.dump(post, open(os.path.join(H, "p5_universo_post.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
