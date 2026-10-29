"""S168: lee el log del job Lascar del run 40945613044 (sombra, medir=true) y lo cruza con las alertas de MIROVA.

POR QUE. El job quedo verde y revisar_sombra.py dijo 77 de 77 records de la via, pero la linea de cada granulo muestra
VRP=0 y anomalous_px=0 en todos. Si MIROVA alerto Lascar esa semana, la via corrio sin detectar nada y eso no es
sano. medir=true no commitea los records, asi que el log es lo unico que queda.
Uso: python contar.py log_job_lascar.txt registro_vrp_consolidado.csv
"""
import csv, re, sys
from collections import Counter
log, ref = sys.argv[1], sys.argv[2]
pat750 = re.compile(r"\s((MODIS|VIIRS)_\S+)(?: \(\S+\))? \| VRP=(\S+) MW .*anomalous_px=(\d+)")
pat375 = re.compile(r"\s(VIIRS_\S+) \(375m\) \| VRP_MIR=(\S+) MW")
c = Counter()
for ln in open(log, encoding="utf-8", errors="replace"):
    m = pat750.search(ln)
    if m:
        c[(m.group(1), "con_pixeles" if int(m.group(4)) > 0 else "vacio")] += 1
        if int(m.group(4)) > 0:
            print("  con pixeles:", ln.strip()[29:])
        continue
    m = pat375.search(ln)
    if m:
        c[(m.group(1) + "_375", "con_pixeles" if m.group(2) not in ("None", "0", "0.0") else "vacio")] += 1
print("granulos procesados por sensor (log):")
for k in sorted(c):
    print(" ", k, c[k])
print("total", sum(c.values()))
a = Counter()
for r in csv.DictReader(open(ref, encoding="utf-8")):
    f = r["Fecha_Satelite_UTC"][:10]
    if r["Volcan"] == "Lascar" and "2026-10-21" <= f <= "2026-10-28" and r["Tipo_Registro"] == "ALERTA_TERMICA":
        h = int(r["Fecha_Satelite_UTC"][11:13])
        a[(r["Sensor"], "noche" if 0 <= h <= 10 else "dia", r["VRP_MW"], r["Fecha_Satelite_UTC"])] += 1
print("alertas MIROVA (tabla) Lascar 2026-10-21 a 28:")
for k in sorted(a, key=lambda x: x[3]):
    print(" ", k)
print("total", len(a))
