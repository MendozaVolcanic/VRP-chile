# -*- coding: utf-8 -*-
"""Alertas MODIS de MIROVA segun el angulo de vista de nuestra pasada, para dimensionar el descarte de borde de la via.

Pregunta fisica: la via no deja record en pasadas de borde de barrido (las dos vistas desde el encendido tienen cenit
65,0 y 65,3 grados y MIROVA las lista como RUTINA). Si MIROVA publica alertas en pasadas tan oblicuas, esas alertas
quedarian sin record nuestro. Aqui se cuenta cuantas alertas MODIS de MIROVA cayeron en pasadas nuestras de cenit alto.

Preguntas del instrumento:
1. Si hubiera alertas de borde, se verian? Si, en pasadas con record (de K o de la via) y cenit guardado. No ve las
   pasadas que nunca tuvieron record: para eso esta 06_alertas_modis_sin_record.py (0 sin record).
2. Instrumento muerto: imprime el total de pasadas MODIS con etiqueta `pos` (debe ser del orden de 100) y el maximo cenit.
Ventana: 2026-02-01 a 2026-11-10 (la tabla de MIROVA es confiable desde marzo; febrero se incluye porque decide F26-M).
Denominador: pasadas MODIS nocturnas nuestras con alerta de MIROVA a +-120 s (etiqueta pos de banco_paridad.etiquetar).
"""
import io, sys, os, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\a\base"
sys.path.insert(0, os.path.join(BASE, "scripts")); sys.path.insert(0, BASE); os.chdir(BASE)
import banco_paridad as bp, auto_audit_weekly as aa
from referencia_mirova_unificada import cargar_referencia_unificada
coords = aa._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(aa.CONS, aa.OCR)
win = ("2026-02-01", "2026-11-10")
recs = [r for r in bp.cargar_nuestros(coords, inner, win) if r["b"] == "MODIS"]
bp.etiquetar(recs, *bp.indexar_referencia(filas, coords, win)[:3])
print("pasadas MODIS nuestras en la ventana:", len(recs), "| max cenit:", max(r["z"] for r in recs if r["z"] is not None))
tr = lambda z: "sin_cenit" if z is None else ("z<30" if z < 30 else "z30-50" if z < 50 else "z50-60" if z < 60 else "z60-63" if z < 63 else "z63-64.5" if z < 64.5 else "z>=64.5")
c = collections.Counter(); cn = collections.Counter()
for r in recs:
    cn[tr(r["z"])] += 1
    if r["lab"] == "pos": c[tr(r["z"])] += 1
orden = ["z<30", "z30-50", "z50-60", "z60-63", "z63-64.5", "z>=64.5", "sin_cenit"]
print("tramo de cenit: pasadas nuestras | con alerta de MIROVA (pos)")
for t in orden: print(f"  {t:10s} {cn[t]:5d} | {c[t]:4d}")
print("total pos:", sum(c.values()))
print("\nPasadas con alerta de MIROVA y cenit >= 60:")
for r in sorted(recs, key=lambda x: x["dt"]):
    if r["lab"] == "pos" and r["z"] is not None and r["z"] >= 60:
        print("  ", r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"), "cenit", r["z"], "publica" if r["pub"] else "no publica")
