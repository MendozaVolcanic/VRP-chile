"""Inventario de regimen (C0 vs K) por volcan, sensor y fecha de observacion.

Pregunta 1 del instrumento: si el regimen estuviera roto (records C0 dentro de la ventana K o al reves),
esta medicion lo ve, porque clasifica cada record por la ancestria de su codigo_sha respecto del merge de K
(34cea39e) con git, no por la fecha.
Pregunta 2: si el campo regimen faltara, el record cae en 'SIN_MARCA', distinto de C0 y de K.
Control positivo: el ultimo record NRT (2026-10-19) debe salir K; un record de enero de 2026, C0 o SIN_MARCA.
Denominador: todos los records de data/mirova_equivalent/*.json del worktree (cb90031a).
"""
import json, glob, os, subprocess, sys, collections, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
K_SHA = "34cea39e"
shas = collections.Counter()
recs_all = []
for f in sorted(glob.glob(os.path.join(ROOT, "data", "mirova_equivalent", "*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    for r in d.get("records", []):
        sha = (r.get("regimen") or {}).get("codigo_sha")
        shas[sha] += 1
        recs_all.append((d["volcano"] if "volcano" in d else os.path.basename(f), r, sha))
anc = {}
for s in shas:
    if not s:
        anc[s] = "SIN_MARCA"; continue
    rc = subprocess.run(["git", "-C", ROOT, "merge-base", "--is-ancestor", K_SHA, s], capture_output=True)
    if rc.returncode == 0: anc[s] = "K"
    elif rc.returncode == 1: anc[s] = "C0"
    else: anc[s] = "SHA_DESCONOCIDO"
print("shas distintos:", len(shas))
for s, n in shas.most_common():
    print(f"  {str(s)[:10]:12s} {anc[s]:16s} n={n}")
# por volcan x mes x regimen
tab = collections.defaultdict(collections.Counter)
first_k = {}
last_c0 = {}
for vol, r, s in recs_all:
    reg = anc[s]
    day = (r.get("datetime_utc") or "")[:10]
    tab[(vol, day[:7])][reg] += 1
    if reg == "K":
        if vol not in first_k or day < first_k[vol]: first_k[vol] = day
    if reg in ("C0", "SIN_MARCA"):
        if vol not in last_c0 or day > last_c0[vol]: last_c0[vol] = day
print("\nPrimer dia observado K y ultimo dia observado C0/SIN_MARCA por volcan:")
for vol in sorted(set(v for v, _, _ in recs_all)):
    print(f"  {vol:28s} primerK={first_k.get(vol)}  ultimoC0={last_c0.get(vol)}")
# records C0/SIN_MARCA con fecha >= 2026-09-18, y K con fecha < 2026-09-18
mix = collections.Counter()
for vol, r, s in recs_all:
    day = (r.get("datetime_utc") or "")[:10]
    reg = anc[s]
    if day >= "2026-09-18" and reg != "K": mix[(vol, r.get("sensor"), reg, "post")] += 1
    if day < "2026-09-18" and reg == "K": mix[(vol, r.get("sensor"), reg, "pre")] += 1
print("\nRecords fuera de su lado de la frontera 2026-09-18:")
for k, n in sorted(mix.items()): print("  ", k, n)
json.dump({"anc": {str(k): v for k, v in anc.items()}}, open(os.path.join(os.path.dirname(__file__), "regimen_por_sha.json"), "w"))
