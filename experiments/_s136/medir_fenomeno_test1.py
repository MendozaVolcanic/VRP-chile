"""S136 - ¿sigue existiendo el fenómeno que justificó la interseccion contextual?

POR QUE: la interseccion contextual del Test 1 (ctxpeak, S100) se adopto porque sobre el
glaciar de Tupungatito el Test 1 integraba el mosaico invernal nieve/roca entero y la magnitud
se inflaba 8-19x contra MIROVA (D10). Esa medicion es PREVIA a nadir-fijo (S103) y a #535
(S126, que apago la mascara de nube y bajo el fondo global 6-8 K en nevados). A87/A90: un
numero deja de medir lo que media cuando el regimen se mueve debajo.

LIMITE DECLARADO: la data en disco esta producida CON el filtro encendido, asi que NO puede
decir cuanto se inflaria sin el. Lo que si mide, y es el fenomeno fisico de D10, es el TAMANO
DEL FOOTPRINT del Test 1 antes del recorte (`n_test1_pixels` se persiste en la linea 1109 de
process_viirs.py, previo al filtro de la 1779). Si el Test 1 ya no barre el mosaico entero, el
material del inflado se apago solo.

Todo numero sale con denominador y ventana (A90).
"""
import io, json, sys, statistics as st
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[2]
# #535 mergeado 2026-08-28 23:00 UTC: retira la mascara de nube hardcodeada (D14)
CORTE = datetime(2026, 8, 28, 23, 0, tzinfo=timezone.utc)
NEVADOS = ["Tupungatito", "Villarrica", "Llaima", "PlanchonPeteroa", "PuyehueCordonCaulle"]
CONTROL = ["Lascar", "Lastarria"]


def cargar(vol):
    p = RAIZ / "data" / "mirova_equivalent" / f"{vol}.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    return d["records"] if isinstance(d, dict) else d


def ts(r):
    s = r.get("datetime_utc") or r.get("timestamp") or ""
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        t = datetime.fromisoformat(s)
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def es_v375(r):
    s = r.get("sensor", "")
    return s.startswith("VIIRS") and "750" not in s  # convencion del proyecto (A48)


def resumen(vals):
    if not vals:
        return "n=0"
    vals = sorted(vals)
    med = st.median(vals)
    p90 = vals[min(len(vals) - 1, int(0.9 * len(vals)))]
    return f"n={len(vals):4d} mediana={med:7.1f} p90={p90:7.1f} max={vals[-1]:7.1f}"


print("=" * 100)
print("FOOTPRINT DEL TEST 1 ANTES DEL RECORTE (n_test1_pixels), VIIRS 375 m")
print(f"Corte de regimen: {CORTE:%Y-%m-%d %H:%M} UTC (#535, retiro de la mascara de nube)")
print("Solo records donde el Test 1 disparo (triggered_test1) - el filtro solo actua ahi")
print("=" * 100)
print(f"{'volcan':22s} {'regimen':8s} {'n_test1_pixels (footprint pre-filtro)':46s}")

filas = {}
for vol in NEVADOS + CONTROL:
    try:
        recs = cargar(vol)
    except FileNotFoundError:
        print(f"{vol:22s} SIN DATA")
        continue
    v = [r for r in recs if es_v375(r) and ts(r)]
    for etiq, sel in (("previo", [r for r in v if ts(r) < CORTE]),
                      ("actual", [r for r in v if ts(r) >= CORTE])):
        disp = [r for r in sel if r.get("triggered_test1")]
        px = [r.get("n_test1_pixels") or 0 for r in disp]
        filas[(vol, etiq)] = (len(sel), px)
        print(f"{vol:22s} {etiq:8s} {resumen(px):46s}  (de {len(sel)} pasadas V375)")
    print()

print("=" * 100)
print("CUANTO MUERDE EL FILTRO HOY: mascara contextual (n_dnti_ctx_path) en los records")
print("donde el Test 1 gana la seleccion. Si la mascara esta vacia, el filtro recorta todo")
print("menos keep_peak; si es grande, el filtro casi no muerde.")
print("=" * 100)
for vol in NEVADOS + CONTROL:
    try:
        recs = cargar(vol)
    except FileNotFoundError:
        continue
    v = [r for r in recs if es_v375(r) and ts(r) and ts(r) >= CORTE]
    t1 = [r for r in v if r.get("final_hotspot_source") == "test1"]
    if not t1:
        print(f"{vol:22s} 0 records con el Test 1 como fuente (de {len(v)} V375 en el regimen actual)")
        continue
    vacios = sum(1 for r in t1 if (r.get("n_dnti_ctx_path") or 0) == 0)
    ctx = [r.get("n_dnti_ctx_path") or 0 for r in t1]
    print(f"{vol:22s} test1-fuente={len(t1):4d}/{len(v):4d}  mascara vacia={vacios:4d} "
          f"({100*vacios/len(t1):5.1f} %)  ctx {resumen(ctx)}")
