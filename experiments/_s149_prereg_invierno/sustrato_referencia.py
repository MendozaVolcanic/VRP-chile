# -*- coding: utf-8 -*-
"""S149. Sustrato ANTES de pre-registrar (leccion S130). Cuenta PASADAS nocturnas unicas con alerta de
MIROVA por volcan, sensor y mes, con su magnitud, en el snapshot del scraper.

v2, tras el verificador con contexto limpio (docs/audit_s149/VERIFICADOR_PREREGISTRO_INVIERNO.md, H1 y
H3): la v1 deduplicaba por (minuto, tipo) y contaba DOBLE cada pasada que tiene fila ALERTA_TERMICA y
fila ALERTA_TERMICA_OCR; y solo miraba junio a agosto, asi que afirmo que junio era el unico sustrato
MODIS del ano cuando marzo tiene el doble. Ahora: dedup por (volcan, sensor, minuto), y todos los meses
con serie continua nuestra (desde 2026-02)."""
import json, sys, io, collections, statistics as st
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev
bp = ev.bp
coords = bp._coords_por_volcan()
SNAP = RAIZ / "data" / "mirova_reference" / "mirova_v1_snapshot"
filas = ev.cargar_referencia_unificada(SNAP / "registro_vrp_consolidado.csv", SNAP / "registro_vrp_ocr.csv")
VENTANAS = [("febrero", "2026-02-01", "2026-02-28"), ("marzo", "2026-03-01", "2026-03-31"), ("abril", "2026-04-01", "2026-04-30"),
            ("mayo", "2026-05-01", "2026-05-31"), ("junio", "2026-06-01", "2026-06-30"), ("julio", "2026-07-01", "2026-07-31"),
            ("agosto 01 a 27", "2026-08-01", "2026-08-27")]
out = {}
def pasadas(ventana):
    por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana)
    d = {}
    for (vol, b), lista in por_vb.items():
        for dt, f in lista:
            if bp.es_alerta(f["tipo"]):
                k = (vol, b, f["fecha_utc"][:16])
                d[k] = max(d.get(k, 0) or 0, f["vrp_mw"] or 0)
    return d
print("PASADAS nocturnas unicas con alerta de MIROVA (dedup por volcan, sensor y minuto)")
print("%-16s | %-28s | %-34s | %-34s | %s" % ("mes", "V375 total / V750 / MODIS", "Villarrica V375: n, <0,5 MW, mediana", "Chillan V375: n, <0,5 MW, mediana", "Lascar MODIS: n, >=0,5 MW"))
for nom, a, b in VENTANAS:
    d = pasadas((a, b))
    def sel(vol, s): return [v for (vv, bb, _), v in d.items() if vv == vol and bb == s]
    def res(x): return "%2d, %2d, %s" % (len(x), sum(v < .5 for v in x), ("%.2f" % st.median(x)) if x else "  - ")
    tot = collections.Counter(bb for (_, bb, _) in d)
    lm = sel("Lascar", "MODIS")
    print("%-16s | %4d / %3d / %3d             | %-34s | %-34s | %2d, %2d" % (nom, tot["VIIRS375"], tot["VIIRS750"], tot["MODIS"], res(sel("Villarrica", "VIIRS375")), res(sel("NevadosDeChillan", "VIIRS375")), len(lm), sum(v >= .5 for v in lm)))
    out[nom] = {"ventana": [a, b], "totales": dict(tot), "villarrica_v375": sorted(sel("Villarrica", "VIIRS375")), "chillan_v375": sorted(sel("NevadosDeChillan", "VIIRS375")), "lascar_modis": sorted(lm),
                "por_volcan_v375": dict(collections.Counter(vv for (vv, bb, _) in d if bb == "VIIRS375"))}
(AQUI / "sustrato_referencia.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nFechas de las alertas V375 de Villarrica por mes:")
for nom, a, b in VENTANAS:
    d = pasadas((a, b)); f = sorted(k[2][:10] for k in d if k[0] == "Villarrica" and k[1] == "VIIRS375")
    if f: print("  %-16s %s a %s (%d)" % (nom, f[0], f[-1], len(f)))
