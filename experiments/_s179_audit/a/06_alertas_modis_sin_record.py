# -*- coding: utf-8 -*-
"""Alertas MODIS nocturnas de MIROVA sin record nuestro a +-120 s, por ventana, en main 438a60a1e (referencia: snapshot del repo).

Para que sirve: el campo `alertas_de_la_tabla_sin_pasada_nuestra` de la lectura de la retrospectiva da Lascar|MODIS 52.
Su ventana va del 2026-02-01 al 2026-10-16 e incluye los meses entre tramos, donde la retrospectiva no tiene pasadas.
Aqui se cuenta con el mismo codigo (banco_paridad.alertas_sin_record) dentro de cada tramo, contra produccion.

Preguntas del instrumento:
1. Si faltaran records de alertas, se veria? Si: lista cada alerta sin record con su VRP.
2. Instrumento muerto: imprime cuantas alertas MODIS hay en la ventana (denominador) ademas de las sin record.
"""
import io, sys, os, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\a\base"
sys.path.insert(0, os.path.join(BASE, "scripts")); sys.path.insert(0, BASE); os.chdir(BASE)
import banco_paridad as bp, auto_audit_weekly as aa, clase_mirova as cm
from referencia_mirova_unificada import cargar_referencia_unificada
coords = aa._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(aa.CONS, aa.OCR)
for nombre, win, solo_tabla in (("F26-M (febrero 2026), solo tabla", ("2026-02-01", "2026-02-28"), True),
                                ("F26-M (febrero 2026), tabla y OCR", ("2026-02-01", "2026-02-28"), False),
                                ("2026-02-01 a 2026-10-16, solo tabla (ventana del campo de la lectura)", ("2026-02-01", "2026-10-16"), True),
                                ("desde el encendido, tabla y OCR", ("2026-11-02", "2026-11-10"), False)):
    ref = [f for f in filas if f["source"] == "CONS"] if solo_tabla else filas
    recs = [r for r in bp.cargar_nuestros(coords, inner, win) if r["b"] == "MODIS"]
    por_vb, ns, nv, n = bp.indexar_referencia(ref, coords, win, regla_minimas="SN")
    sinr = bp.alertas_sin_record(por_vb, recs)
    tot = collections.Counter()
    for (vol, b), fs in por_vb.items():
        if b == "MODIS":
            tot[vol] += len({f["fecha_utc"][:16] for _d, f in fs if bp.es_alerta(f["tipo"])})
    print(f"\n== {nombre}: records MODIS nuestros {len(recs)}")
    print("   filas de alerta MODIS de MIROVA por volcan (denominador):", dict(tot))
    print("   alertas MODIS sin record nuestro a +-120 s:", {k: v for k, v in sinr.items() if k[1] == "MODIS"})
