# -*- coding: utf-8 -*-
"""F2 M6b. Camino de rechazo (misma regla que experiments/_s150_debiles/clases_rechazo.py:31-38) por fiabilidad de la
etiqueta, perdidas V375 de F. Uso: python m6b_camino_por_etiqueta.py filas_mias.json"""
import json, sys, collections
F = json.load(open(sys.argv[1], encoding="utf-8"))
def camino(r):
    b = r["B"]
    if b["diag_n_first_pass_pixels"]: return "1er pase"
    exc = (b["ap_bt_max"] - b["t_bg_k"]) if b.get("ap_bt_max") is not None and b.get("t_bg_k") else None
    return "2o pase BT<tbg+3 (D22)" if exc is not None and exc < 3 else "2o pase BT>=tbg+3"
def et(r):
    if not r["solo_ocr"]: return "tabla"
    return ("OCR<0613" if r["dt"] < "2026-06-13" else "OCR>=0613") + ("_SNPP" if "SNPP" in r["B"]["sensor"] else "")
c = collections.Counter((et(r), camino(r)) for r in F if r["perdida"] and r["b"] == "VIIRS375")
print("M6b V375 perdidas por etiqueta y camino:", dict(sorted(c.items())))
for nombre, ok in (("todas", lambda e: True), ("doc confiable (tabla u OCR>=0613)", lambda e: e in ("tabla", "OCR>=0613", "OCR>=0613_SNPP")), ("estricto (sin OCR SNPP)", lambda e: e in ("tabla", "OCR>=0613"))):
    print("  %-36s %s" % (nombre, dict(collections.Counter(k[1] for k, v in c.items() for _ in range(v) if ok(k[0])))))
