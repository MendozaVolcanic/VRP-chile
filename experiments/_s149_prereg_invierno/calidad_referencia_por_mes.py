# -*- coding: utf-8 -*-
"""S149. Calidad de la referencia por mes y sensor: cuantas pasadas nocturnas unicas con alerta vienen de
la TABLA de MIROVA (latest.php, canal CONS, sin OCR) y cuantas SOLO del OCR de las imagenes. Pregunta de
Nicolas: los primeros meses del scraper tenian problemas de OCR; que ventanas son confiables, y MODIS
esta completo? Tambien cuenta las filas RUTINA de la tabla (los negativos) por mes."""
import sys, io, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev
bp = ev.bp
SNAP = RAIZ / "data" / "mirova_reference" / "mirova_v1_snapshot"
filas = ev.cargar_referencia_unificada(SNAP / "registro_vrp_consolidado.csv", SNAP / "registro_vrp_ocr.csv")
coords = bp._coords_por_volcan()
MESES = [("2026-01", "2026-01-10", "2026-01-31"), ("2026-02", "2026-02-01", "2026-02-28"), ("2026-03", "2026-03-01", "2026-03-31"), ("2026-04", "2026-04-01", "2026-04-30"),
         ("2026-05", "2026-05-01", "2026-05-31"), ("2026-06", "2026-06-01", "2026-06-30"), ("2026-07", "2026-07-01", "2026-07-31"), ("2026-08", "2026-08-01", "2026-08-27"), ("2026-09", "2026-09-01", "2026-09-13")]
print("%-8s | %-34s | %-34s | %-24s | %s" % ("mes", "V375 alertas: total, tabla, solo OCR", "V750 alertas: total, tabla, solo OCR", "MODIS: total, tabla, OCR", "RUTINA VRP 0 de la tabla: V375/V750/MODIS"))
for nom, a, b in MESES:
    por_vb, ns, nv, n = bp.indexar_referencia(filas, coords, (a, b))
    src = collections.defaultdict(set); rut = collections.Counter()
    for (vol, s), lista in por_vb.items():
        for dt, f in lista:
            k = (vol, s, f["fecha_utc"][:16])
            if bp.es_alerta(f["tipo"]): src[k].add(f["source"])
            elif f["tipo"] == "RUTINA" and f["source"] == "CONS": rut[s] += 1
    def r(s):
        ks = [k for k in src if k[1] == s]; t = sum(1 for k in ks if "CONS" in src[k])
        return "%4d, %4d, %4d (%2.0f %% solo OCR)" % (len(ks), t, len(ks) - t, 100 * (len(ks) - t) / len(ks) if ks else 0)
    print("%-8s | %-34s | %-34s | %-24s | %d / %d / %d" % (nom, r("VIIRS375"), r("VIIRS750"), r("MODIS")[:24], rut["VIIRS375"], rut["VIIRS750"], rut["MODIS"]))
