# -*- coding: utf-8 -*-
"""V10 (verificador S160 espacial): sensibilidad del pareo record nuestro <-> alerta de MIROVA (afirmacion 2, 876 alertas a
120 s) a la tolerancia. Para cada fila ALERTA nocturna de la referencia en los 3 volcanes (misma regla de noche y ventana
que 03 via banco_paridad.indexar_referencia con regla SN), |dt| al record nuestro mas cercano del mismo volcan y sensor.
Se cuenta cuantas alertas quedan pareadas a 30, 60, 120, 300 y 900 s. P1: a 900 s deben aparecer pareos de OTRA pasada
(hay ~18-50 min entre satelites), o sea que la cuenta debe crecer poco entre 120 y 300 s si 120 s es una buena tolerancia.
"""
import io, json, os, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AUD = Path(__file__).resolve().parents[1]
ROOT = AUD.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as BP  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
COORD = {"Tupungatito": (-33.4, -69.8), "PuyehueCordonCaulle": (-40.59, -72.117), "Isluga": (-19.15, -68.83)}
def bucket(s):
    s = s or ""
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else ("VIIRS375" if s.startswith("VIIRS") else None))
filas = [f for f in cargar_referencia_unificada() if f["volcano"] in COORD]
por_vb, *_ = BP.indexar_referencia(filas, COORD, ("2026-01-10", "2026-10-21"), regla_minimas="SN")
rec = defaultdict(list)
for v in COORD:
    for r in json.load(open(AUD / "data" / f"{v}.json", encoding="utf-8"))["records"]:
        b = bucket(r.get("sensor"))
        if b:
            rec[(v, b)].append(datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc))
tol = [30, 60, 120, 300, 900]
c = Counter(); n = 0; dts = []
for (v, b), L in por_vb.items():
    for dt, f in L:
        if not BP.es_alerta(f["tipo"]):
            continue
        n += 1
        m = min((abs((x - dt).total_seconds()) for x in rec[(v, b)]), default=1e9)
        dts.append(m)
        for t in tol:
            c[t] += m <= t
print(f"filas ALERTA nocturnas indexadas (CONS y OCR por separado, regla SN): {n}")
for t in tol:
    print(f"  pareadas a <= {t:4d} s: {c[t]}")
print("  |dt| de las pareadas a 120 s, histograma por decena de segundos:", sorted(Counter(int(x // 10) * 10 for x in dts if x <= 120).items()))
