# -*- coding: utf-8 -*-
"""S181: paridad por noche K contra vía con dos referencias de MIROVA: la tabla sola (CONS) y la tabla más el OCR.

Corrige la bitácora de S181 (14:41 UTC), que llamó «sólo la tabla» a banco_ab.py: banco_ab.py usa
cargar_referencia_unificada, que une tabla y OCR (lo detectó el agente de los mazos). Regla S159: informar siempre la
tabla sola además del combinado. Antes = data/ de origin/main en fb9b4da06 (copiado a antes_data); después = worktree en
21ea8166b (historia reemplazada). Ventana 2026-03-01 a 2026-11-01, previa a todos los cortes.
"""
import sys
sys.path[:0] = [r"D:\vrp-trabajo\worktrees\s181-verif-994\scripts", r"D:\vrp-trabajo\worktrees\s181-verif-994"]
import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

ventana = ("2026-03-01", "2026-11-01")
coords = bp._coords_por_volcan()
inner = bp.inner_desde_html()
todas = cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
for nombre_ref, filas in (("tabla+OCR", todas), ("solo tabla", [f for f in todas if f["source"] == "CONS"])):
    por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana, regla_minimas=bp.MODO_MINIMAS)
    for nombre, data in (("antes_K", r"D:\vrp-trabajo\temporales\s181_verif994\antes_data"),
                         ("despues_via", r"D:\vrp-trabajo\worktrees\s181-verif-994\data\mirova_equivalent")):
        recs = bp.cargar_nuestros(coords, inner, ventana, data=data)
        bp.etiquetar(recs, por_vb, ns, nv)
        ps, pv = bp.resumen(recs, bp.alertas_sin_record(por_vb, recs))
        for b in ("MODIS", "VIIRS375", "VIIRS750"):
            n = ps[b]["noche_volcan"]
            print(f"{nombre_ref:10s} {nombre:11s} {b:8s} noche pos {n['n_pos']} recall {n['recall_pos']} "
                  f"neg {n['n_neg']} pub_neg {n['tasa_pub_neg']}")
