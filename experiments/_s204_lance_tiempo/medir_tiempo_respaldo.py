# -*- coding: utf-8 -*-
"""S204: cuánto tiempo de red gasta el respaldo LANCE por volcán en una NRT real. Para cada búsqueda con respaldo
(línea LANCE_RESPALDO [<producto> <fecha>]) toma la marca diag anterior del mismo job (SEARCH_START o la línea previa)
y la diferencia hasta LANCE_RESPALDO: es una cota superior del tiempo del módulo en esa búsqueda (incluye la consulta a
CMR que la precede). Uso: python medir_tiempo_respaldo.py <log de gh run view --log>"""
import io
import re
import sys
from collections import defaultdict
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RX = re.compile(r"\[diag (\d\d:\d\d:\d\d)Z\] (\S+)(.*)")
por_job = defaultdict(list)
for linea in io.open(sys.argv[1], encoding="utf-8", errors="replace"):
    partes = linea.rstrip("\n").split("\t")
    if len(partes) < 3:
        continue
    m = RX.search(partes[2])
    if m:
        por_job[partes[0]].append((datetime.strptime(m.group(1), "%H:%M:%S"), m.group(2), m.group(3)))
print("%-34s %5s %9s %9s %s" % ("job", "n", "suma_s", "max_s", "fechas"))
for job, ev in sorted(por_job.items()):
    tiempos, fechas = [], set()
    for i, (t, tipo, resto) in enumerate(ev):
        if tipo == "LANCE_RESPALDO" and i > 0:
            tiempos.append((t - ev[i - 1][0]).total_seconds())
            fm = re.search(r"(\d{4}-\d\d-\d\d)\]", resto)
            if fm:
                fechas.add(fm.group(1))
    if tiempos:
        print("%-34s %5d %9.0f %9.0f %s" % (job[:34], len(tiempos), sum(tiempos), max(tiempos), sorted(fechas)))
