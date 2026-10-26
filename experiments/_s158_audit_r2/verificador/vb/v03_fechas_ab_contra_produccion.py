"""VB v03: pasadas por dia del brazo control del A/B 39530508296 contra produccion (data/mirova_equivalent).

Solo se leen `sensor` y `datetime_utc` de cada record: ninguna metrica, ningun veredicto.
Camino distinto al del auditor: leo los JSON directo del commit 4b6d7f5f2 con `git show` y comparo
claves (volcan, sensor, datetime) contra el checkout de hoy, dia por dia.
Pregunta 1: si al A/B le faltara un dia entero, el conteo diario del control daria 0 donde produccion
tiene pasadas; si no faltara nada, las dos columnas coinciden. Pregunta 2: si la lectura del commit
fallara, el control daria 0 en TODOS los dias (eso seria SIN DATO, no falta): lo controla la columna total.
Control positivo: los dias de la ventana con pasadas en ambos lados (deben ser la gran mayoria).
Ventana: 2026-08-29 a 2026-10-18 (la de cobertura.json del run). Denominador: pasadas VIIRS (375 y 750)
de los 11 volcanes del A/B. Advertencia: produccion de hoy puede tener pasadas agregadas despues del run.
"""
import subprocess, json, os, sys, io
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
C = "4b6d7f5f2"
base = "experiments/_s146_ab_sin_test1/salidas/39530508296/_s157_ab_d25_k_control"
vols = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima", "NevadosDeChillan",
        "PlanchonPeteroa", "PuyehueCordonCaulle", "Tupungatito", "Villarrica"]
LO, HI = "2026-08-29", "2026-10-18"
def g(s): return "MODIS" if s.startswith("MODIS") else ("V750" if s.endswith("_750") else "V375")
def claves(recs):
    out = set()
    for r in recs:
        d = r["datetime_utc"][:10]
        if LO <= d <= HI:
            out.add((r["sensor"], r["datetime_utc"][:16]))
    return out
ab, prod = {}, {}
for v in vols:
    raw = subprocess.run(["git", "-C", REPO, "show", f"{C}:{base}/{v}.json"], capture_output=True).stdout
    ab[v] = claves(json.loads(raw)["records"])
    prod[v] = claves(json.load(open(os.path.join(REPO, "data/mirova_equivalent", v + ".json")))["records"])
dia = defaultdict(lambda: Counter())
for v in vols:
    for (s, t) in ab[v]: dia[t[:10]][("ab", g(s))] += 1
    for (s, t) in prod[v]: dia[t[:10]][("prod", g(s))] += 1
tot = Counter()
print("dia         | A/B control V375 V750 MODIS | produccion V375 V750 MODIS | faltan VIIRS")
for d in sorted(dia):
    c = dia[d]
    falt = (c[("prod", "V375")] + c[("prod", "V750")]) - (c[("ab", "V375")] + c[("ab", "V750")])
    for k in c: tot[k] += c[k]
    marca = "  <==" if falt else ""
    print(f"{d} | {c[('ab','V375')]:5d} {c[('ab','V750')]:4d} {c[('ab','MODIS')]:5d} | {c[('prod','V375')]:5d} {c[('prod','V750')]:4d} {c[('prod','MODIS')]:5d} | {falt:4d}{marca}")
print("TOTAL", dict(tot))
solo_prod = sum(len(prod[v] - ab[v]) for v in vols); solo_ab = sum(len(ab[v] - prod[v]) for v in vols)
solo_prod_viirs = sum(1 for v in vols for (s, t) in prod[v] - ab[v] if not s.startswith("MODIS"))
print(f"claves solo en produccion: {solo_prod} (VIIRS {solo_prod_viirs}); solo en el A/B: {solo_ab}")
pv = Counter((t[:10], g(s)) for v in vols for (s, t) in prod[v] - ab[v] if not s.startswith("MODIS"))
print("solo produccion, VIIRS, por dia y sensor:", dict(sorted(pv.items())))
sat = Counter((t[:10], s) for v in vols for (s, t) in prod[v] - ab[v] if not s.startswith("MODIS"))
print("solo produccion, VIIRS, por dia y plataforma:", dict(sorted(sat.items())))
