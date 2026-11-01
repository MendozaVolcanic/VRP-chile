# -*- coding: utf-8 -*-
"""Verificador S159: ¿MIROVA mira un solo granulo, o procesa los dos y lista el que tiene calor?
Si procesara los dos y listara el caliente, en las partidas con el crater en el granulo NORTE (fm del sur < 0,5)
apareceria alguna alerta listando el norte, a la tasa de alerta de ese volcan y sensor en pasadas enteras.
Pregunta 1: lo veria? Si: el esperado bajo esa hipotesis se calcula y debe ser > 0 para que el 0 observado diga algo.
Control positivo: en las partidas con el crater en el sur, observado y esperado deben parecerse.
Entrada: verif_pareo_salida.json (partidas) + referencia unificada. Tasa de alerta = pasadas con alguna ALERTA /
pasadas listadas, por (volcan, sensor, mes), sobre toda la referencia (incluye diurnas: SOSPECHA de sesgo, se
repite solo con horas 00-11 UTC, que en Chile son de noche)."""
import collections, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(sys.argv[1]); sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
pas = collections.defaultdict(lambda: collections.defaultdict(bool))
for f in filas:
    if not ("00" <= f["fecha_utc"][11:13] <= "11"): continue
    k = (f["volcano"], f["sensor_bucket"], f["fecha_utc"][:7])
    pas[k][f["fecha_utc"][:16]] |= (f["tipo"].startswith("ALERTA") and f["tipo"] != "ALERTA_SIN_GEOMETRIA_OCR")
tasa = {k: sum(v.values()) / len(v) for k, v in pas.items()}
P = json.load(open(Path(__file__).with_name("verif_pareo_salida.json"), encoding="utf-8"))["partidas"]
res = collections.defaultdict(lambda: [0, 0.0, 0])
for p in P:
    if not p["sur"]: continue
    lado = "crater en el sur (fm>=0,5)" if p["fm"] >= 0.5 else "crater en el norte (fm<0,5)"
    t = tasa.get((p["vol"], p["b"], p["t"][:7]), 0.0)
    r = res[(p["b"], lado)]; r[0] += 1; r[1] += t; r[2] += p["cl"] == "alerta"
for k in sorted(res):
    n, e, o = res[k]
    print(k, f"n {n}  alertas esperadas si MIROVA viera el crater igual {e:.1f}  observadas {o}")
tot = collections.defaultdict(lambda: [0, 0.0, 0])
for (b, lado), v in res.items():
    for i in range(3): tot[lado][i] += v[i]
for k, (n, e, o) in tot.items():
    print("TOTAL", k, f"n {n} esperadas {e:.1f} observadas {o}")
