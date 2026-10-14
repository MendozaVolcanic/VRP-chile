# -*- coding: utf-8 -*-
"""F3 R6. A119 y calidad_referencia_mirova.py dicen 'cobertura nocturna de la tabla 86 % en enero'. S149 frente B
(B-03) dijo que eso es Tupungatito ausente en el denominador. Re-medido aca con el consolidado vivo unido al
respaldo del 2026-04-08 (misma union que usa banco_paridad).
P1: si la tabla de enero estuviera de verdad incompleta, la cobertura SIN Tupungatito tambien bajaria. P2: control
positivo: marzo (que A119 da por sano) debe dar 99-100 % con los dos denominadores.
Noche: hora UTC < 10:42 o >= 22:42 (definicion de docs/audit_s139/MAPA_BASES_MIROVA_V1.md §2)."""
import sys, collections, calendar
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ))
from referencia_mirova_unificada import leer_pasadas, RESPALDO_20260408
filas = {}
for f in leer_pasadas(RAIZ / "latest_consolidado.csv", "CONS", "viva") + leer_pasadas(RESPALDO_20260408, "CONS", "resp"):
    filas.setdefault((f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16]), f)
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
def noct(h): return h < "10:42" or h >= "22:42"
cub = collections.defaultdict(set)
for (v, b, t), f in filas.items():
    if v in VOLS and noct(t[11:16]): cub[(t[:7], b)].add((v, t[:10]))
for mes in ("2026-01", "2026-02", "2026-03"):
    dias = calendar.monthrange(2026, int(mes[5:]))[1]
    d0 = 11 if mes == "2026-01" else 1   # la tabla parte el 2026-01-10 19:06: en enero se cuentan noches desde el 11
    nd = dias - d0 + 1
    for b in ("MODIS", "VIIRS375", "VIIRS750"):
        s = {x for x in cub[(mes, b)] if int(x[1][8:]) >= d0}
        con = len(s); sin_t = len({x for x in s if x[0] != "Tupungatito"})
        print("%s %-8s noches %2d desde el dia %2d | 11 volcanes: %3d/%3d = %5.1f %% | sin Tupungatito: %3d/%3d = %5.1f %% | Tupungatito: %d" % (
            mes, b, nd, d0, con, 11 * nd, 100 * con / (11 * nd), sin_t, 10 * nd, 100 * sin_t / (10 * nd), con - sin_t))
