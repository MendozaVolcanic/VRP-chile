# -*- coding: utf-8 -*-
"""Cuantas pasadas nocturnas protegidas publica MIROVA por noche y por sensor (2026-11-03 a 2026-11-09), para estimar
cuanto dura el plazo de 29 protegidas de cada guardia. Referencia: snapshot del repo en main 438a60a1e (tabla y OCR).
Protegida: clase_mirova.alerta_protegida (1 MW o mas, lectura A). Noche: la misma regla diurna de la vigilancia.
Preguntas del instrumento: (1) un conteo roto se veria contra 02 (MODIS tiene que dar 11). (2) instrumento muerto: 0 en todo.
Limite: cuenta alertas de MIROVA, no records de la guardia; el plazo real cuenta las que tienen record de la guardia."""
import io, sys, os, collections
from datetime import datetime, timezone
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\a\base"
sys.path.insert(0, os.path.join(BASE, "scripts")); sys.path.insert(0, BASE); os.chdir(BASE)
import auto_audit_weekly as aa, clase_mirova as cm, vigilancia_sombra as vs
from referencia_mirova_unificada import cargar_referencia_unificada
filas = cargar_referencia_unificada(aa.CONS, aa.OCR)
diurna = vs._diurna_por_defecto()
c, pv, vistos, diur = collections.Counter(), collections.Counter(), set(), collections.Counter()
for f in filas:
    if not ("2026-11-03" <= f["fecha_utc"][:10] <= "2026-11-09") or not cm.alerta_protegida(f): continue
    k = cm.clave_pasada(f)
    if k in vistos: continue
    vistos.add(k)
    dt = datetime.fromisoformat(f["fecha_utc"][:19]).replace(tzinfo=timezone.utc)
    if diurna(f["sensor_bucket"], f["volcano"], dt):
        diur[f["sensor_bucket"]] += 1; continue
    c[f["sensor_bucket"]] += 1; pv[(f["sensor_bucket"], f["volcano"])] += 1
for s in ("MODIS", "VIIRS375", "VIIRS750"):
    t = c[s]
    print(f"{s}: {t} pasadas nocturnas protegidas en 7 noches ({t/7:.2f} por noche); 29 se juntan en {29/(t/7):.1f} noches; "
          f"por volcan {dict((v, n) for (b, v), n in pv.items() if b == s)}; diurnas protegidas fuera del sistema: {diur[s]}")
