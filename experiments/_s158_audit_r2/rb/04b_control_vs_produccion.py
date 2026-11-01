"""Afirmación 4, extensión: pasadas VIIRS (375 y 750) que PRODUCCIÓN (data/mirova_equivalent) tiene en V1
(2026-08-29..2026-10-18) y el brazo control del A/B (rama origin/s146-ab/39530508296) NO tiene, y al revés,
por volcán, sensor y día. Clave de pasada = (volcán, sensor, datetime_utc al minuto). Sólo conteos.
Pregunta 1: si el control trajera todo, la columna 'faltan' daría 0 en todas las filas; el control positivo
son los días 2026-10-13 y 2026-10-18 que 04_fechas_ab_d25.txt ya mostró vacíos en el brazo.
Pregunta 2: si git show fallara, excepción; si producción no tuviera records en V1 se imprimiría n=0."""
import sys, io, json, subprocess, os
from collections import Counter, defaultdict
sys.stdout = io.TextOutputWrapper = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["MSYS_NO_PATHCONV"] = "1"
RAMA = "origin/s146-ab/39530508296"; BASE = "experiments/_s146_ab_sin_test1/salidas/39530508296/_s157_ab_d25_k_control"
PROD = "data/mirova_equivalent"
VOLS = ["Chaiten","Copahue","Isluga","Lascar","Lastarria","Llaima","NevadosDeChillan","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito","Villarrica"]
V_INI, V_FIN = "2026-08-29", "2026-10-18"
def claves(recs):
    return {(r.get("sensor"), r.get("datetime_utc")) for r in recs
            if r.get("sensor", "").startswith("VIIRS") and V_INI <= (r.get("datetime_utc") or "")[:10] <= V_FIN}
tot_f = tot_s = tot_p = 0
faltan_dia = Counter(); sobran_dia = Counter()
print(f"{'volcan':20} {'prod':>6} {'ctrl':>6} {'faltan_en_ctrl':>14} {'sobran_en_ctrl':>14}")
for v in VOLS:
    prod = json.load(open(f"{PROD}/{v}.json", encoding="utf-8")); prod = prod["records"] if isinstance(prod, dict) else prod
    out = subprocess.run(["git", "show", f"{RAMA}:{BASE}/{v}.json"], capture_output=True, check=True).stdout
    ctrl = json.loads(out.decode("utf-8")); ctrl = ctrl["records"] if isinstance(ctrl, dict) else ctrl
    kp, kc = claves(prod), claves(ctrl)
    f, s = kp - kc, kc - kp
    tot_p += len(kp); tot_f += len(f); tot_s += len(s)
    print(f"{v:20} {len(kp):6d} {len(kc):6d} {len(f):14d} {len(s):14d}")
    for sen, dt in f: faltan_dia[(dt[:10], sen.endswith('_750'))] += 1
    for sen, dt in s: sobran_dia[(dt[:10], sen.endswith('_750'))] += 1
print(f"TOTAL pasadas VIIRS de produccion en V1: {tot_p}; faltan en el control: {tot_f} ({100*tot_f/max(1,tot_p):.2f} %); sobran en el control: {tot_s}")
print("\nFaltan en el control, por dia (dia, es_750): n")
for k in sorted(faltan_dia): print("  ", k, faltan_dia[k])
print("\nSobran en el control (estan en el brazo y no en produccion), por dia:")
for k in sorted(sobran_dia): print("  ", k, sobran_dia[k])
