# -*- coding: utf-8 -*-
"""F2 M6. Recuenta las perdidas de F (46) con la regla que el propio S150_IMAGENES_SNPP §3.2 propone:
"una alerta de Suomi NPP que llega solo por el OCR no es confiable como etiqueta positiva". Lee filas_mias.json
(identico a experiments/_s150_debiles/filas.json). Pregunta 2: el total debe dar 46 (control)."""
import json, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F = json.load(open(sys.argv[1], encoding="utf-8"))
P = [r for r in F if r["perdida"]]
def cat(r):
    if not r["solo_ocr"]: return "tabla"
    snpp = "SNPP" in (r["B"] or {}).get("sensor", "")
    if r["dt"][:10] < "2026-06-13": return "OCR antes 06-13" + (" SNPP" if snpp else "")
    return "OCR desde 06-13" + (" SNPP" if snpp else "")
c = collections.Counter((r["b"], cat(r)) for r in P)
for k, n in sorted(c.items()): print(k, n)
print("total perdidas", len(P))
conf_doc = [r for r in P if cat(r) in ("tabla", "OCR desde 06-13", "OCR desde 06-13 SNPP")]
conf_est = [r for r in P if cat(r) in ("tabla", "OCR desde 06-13")]
print("confiables segun el doc (tabla u OCR desde 06-13):", len(conf_doc), "(incluye las 3 SNPP de imagen de otra pasada? ",
      sum(1 for r in conf_doc if cat(r).endswith("SNPP")), "SNPP)")
print("confiables estricto (sin ningun OCR de SNPP):", len(conf_est), "| V375", sum(r["b"] == "VIIRS375" for r in conf_est))
# denominadores: alertas que B publica por la misma regla
D = collections.Counter((r["b"], cat(r)) for r in F)
for b in ("VIIRS375", "VIIRS750"):
    n = sum(v for (bb, k), v in D.items() if bb == b and k in ("tabla", "OCR desde 06-13"))
    p = sum(1 for r in conf_est if r["b"] == b)
    print(b, "estricto: B publica", n, "| F pierde", p, "| F conserva %.1f %%" % (100 * (n - p) / n))
