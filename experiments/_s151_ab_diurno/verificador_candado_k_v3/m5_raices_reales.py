# -*- coding: utf-8 -*-
"""Verificador v3, pregunta 2: como se ven de verdad las raices del A/B (las diez medias ventanas sobre C0) desde el
punto de vista de H2a. Por raiz y brazo: records leidos, volcanes con 0 records, shas distintos (con conteo), rango de
fechas de los records frente a la ventana de la raiz, y records con el Test 1.

Las dos preguntas del instrumento:
 1. Si H2a estuviera rota sobre raices reales (por ejemplo, raices que traen historia de produccion con otro sha), esta
    medicion lo veria: cuenta shas y fechas por raiz sin pasar por el evaluador.
 2. Si el script estuviera muerto (raices inexistentes), imprime 0 records y lo dice como SIN DATO, no como OK.
Control positivo: sobre C0 los records TIENEN el Test 1 (C0 lo traia encendido), asi que t1 > 0 tiene que aparecer.
Uso: python m5_raices_reales.py <dir con W2a..W6b>
"""
import collections
import json
import sys
from pathlib import Path

base = Path(sys.argv[1])
brazos = ("_s151_ab_diurno_control", "_s151_ab_diurno_on")
tot = collections.Counter()
for raiz in sorted(base.iterdir()):
    if not raiz.is_dir():
        continue
    for b in brazos:
        d = raiz / b
        if not d.is_dir():
            print("%s %s: SIN DIRECTORIO" % (raiz.name, b))
            continue
        n = 0
        shas = collections.Counter()
        fechas = []
        t1 = 0
        vacios = []
        sin_reg = 0
        for p in sorted(d.glob("*.json")):
            recs = json.loads(p.read_text(encoding="utf-8")).get("records", [])
            if not recs:
                vacios.append(p.stem)
            n += len(recs)
            for r in recs:
                reg = r.get("regimen")
                if not reg:
                    sin_reg += 1
                shas[(reg or {}).get("codigo_sha")] += 1
                fechas.append(r.get("datetime_utc") or "")
                if r.get("triggered_test1") is True or r.get("final_hotspot_source") == "test1_roi":
                    t1 += 1
        tot[b] += n
        f = sorted(x for x in fechas if x)
        print("%s %-24s records %5d | vol sin records %s | sin regimen %d | Test 1 %d | fechas %s .. %s | shas %s"
              % (raiz.name, b, n, vacios or "-", sin_reg, t1, f[0][:16] if f else "-", f[-1][:16] if f else "-",
                 {(k or "NINGUNO")[:12]: v for k, v in shas.most_common()}))
print("TOTAL", dict(tot) if tot else "SIN DATO")
