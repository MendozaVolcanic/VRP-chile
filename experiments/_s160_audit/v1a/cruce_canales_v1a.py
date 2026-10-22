# -*- coding: utf-8 -*-
"""V1a. Implementacion propia (no importa banco_paridad ni clase_mirova): pasadas donde el OCR trae una ALERTA de
1 MW o mas y la TABLA, en la misma pasada (mismo volcan, mismo sensor VIIRS375/VIIRS750/MODIS, +-120 s), trae
FALSO_POSITIVO. Sobre el congelado de V1 y V2 del instrumento de K y sobre la referencia de d516b9d8c.
Preguntas del instrumento: (1) si el cruce existiera lo veria: control positivo sintetico al final;
(2) si el lector estuviera muerto, los conteos de filas leidas serian 0: se imprimen.
Uso: python cruce_canales_v1a.py"""
import csv, sys
from datetime import datetime
from pathlib import Path
R = Path(r"C:\vrp-trabajo\s159-pruebas\experiments\_s151_prereg_fk_11")
M = Path(r"D:\vrp-trabajo\temporales\s160_audit\main")
FUENTES = {"congelado_v1": (R/"_congelado_v1"/"registro_vrp_consolidado.csv", R/"_congelado_v1"/"registro_vrp_ocr.csv", "2026-08-29", "2026-10-08"),
           "congelado_v2": (R/"_congelado_v2"/"registro_vrp_consolidado.csv", R/"_congelado_v2"/"registro_vrp_ocr.csv", "2026-03-01", "2026-06-12"),
           "main_v1": (M/"latest_consolidado.csv", M/"data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv", "2026-08-29", "2026-10-08")}
def leer(p):
    with open(p, encoding="utf-8", errors="replace", newline="") as fh:
        return list(csv.reader(fh))
def filas(p, desde, hasta):
    out = []
    rows = leer(p)
    for r in rows[1:]:
        if len(r) < 9: continue
        t = r[1]
        if not (desde <= t[:10] <= hasta): continue
        try: v = float(r[5])
        except ValueError: v = None
        out.append({"t": datetime.strptime(t[:19], "%Y-%m-%d %H:%M:%S"), "vol": r[3], "sen": r[4], "vrp": v, "tipo": r[7]})
    return out, len(rows) - 1
def main(sint=False):
    for nom, (cons, ocr, d, h) in FUENTES.items():
        C, nc = filas(cons, d, h); O, no = filas(ocr, d, h)
        if sint:
            O = O + [{"t": C[0]["t"], "vol": C[0]["vol"], "sen": C[0]["sen"], "vrp": 2.0, "tipo": "ALERTA_TERMICA_OCR"}]
            C = C + [dict(C[0], tipo="FALSO_POSITIVO")]
        hits = []
        for o in O:
            if not (o["tipo"].startswith("ALERTA") and "SIN_GEOMETRIA" not in o["tipo"] and (o["vrp"] or 0) >= 1.0): continue
            for c in C:
                if c["vol"] == o["vol"] and c["sen"] == o["sen"] and abs((c["t"] - o["t"]).total_seconds()) <= 120 and c["tipo"].startswith("FALSO_POSITIVO"):
                    hits.append((o["vol"], o["sen"], str(o["t"]), o["vrp"], c["tipo"], c["vrp"])); break
        n_alert = sum(1 for o in O if o["tipo"].startswith("ALERTA") and (o["vrp"] or 0) >= 1.0)
        print("%s%s: filas tabla %d (ventana %d), OCR %d (ventana %d); alertas OCR >=1 MW %d; con FALSO_POSITIVO en la tabla %d" % (
            "[SINTETICO] " if sint else "", nom, nc, len(C), no, len(O), n_alert, len(hits)))
        for x in hits: print("   ", x)
main(); main(sint=True)
