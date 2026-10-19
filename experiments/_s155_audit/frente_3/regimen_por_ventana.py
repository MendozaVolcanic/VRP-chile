#!/usr/bin/env python3
"""F3: cuanto pesa cada regimen (C0 / K) en las ventanas de los instrumentos.

Pregunta 1 (si lo medido estuviera roto, lo veria?): si todos los records de la ventana
fueran C0, la fraccion K daria 0; si el corte por sha estuviera mal, el control positivo
(records NRT posteriores al merge de #850 a las 09:57:30 UTC del 2026-10-18) no saldria 100 % K.
Pregunta 2 (instrumento muerto?): un sha que git no conoce va a 'sha_desconocido', no a C0;
un record sin marca va a 'sin_marca'. SIN DATO != C0.

Clasificacion: K si el commit 34cea39e (squash de #850) es ancestro de regimen.codigo_sha
(o es el mismo). C0 si no lo es. Fuente: git merge-base --is-ancestor.
"""
import json, os, subprocess, sys
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
K_SHA = "34cea39e"
VOLS = ["Lascar", "Lastarria", "Isluga", "Llaima", "Villarrica", "Chaiten", "Tupungatito",
        "Copahue", "PlanchonPeteroa", "PuyehueCordonCaulle", "NevadosDeChillan"]
_cache = {}
def regimen_de(sha):
    if not sha:
        return "sin_marca"
    if sha in _cache:
        return _cache[sha]
    ok = subprocess.run(["git", "-C", ROOT, "cat-file", "-e", sha + "^{commit}"], capture_output=True).returncode == 0
    if not ok:
        _cache[sha] = "sha_desconocido"; return _cache[sha]
    anc = subprocess.run(["git", "-C", ROOT, "merge-base", "--is-ancestor", K_SHA, sha], capture_output=True).returncode
    _cache[sha] = "K" if anc == 0 else "C0"
    return _cache[sha]

def bucket(s):
    if s.startswith("MODIS"): return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    return "VIIRS375"

def main():
    ventanas = {"audit_60d_hoy": ("2026-08-20", "2026-10-19"),
                "audit_60d_run_1014": ("2026-08-15", "2026-10-14"),
                "falsas_hoy": ("2026-09-01", "2026-10-19")}
    out = {}
    por_dia = defaultdict(Counter)
    procesado_post = Counter()
    for v in VOLS:
        recs = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", v + ".json"), encoding="utf-8"))["records"]
        for r in recs:
            dt = r.get("datetime_utc") or ""
            reg = regimen_de((r.get("regimen") or {}).get("codigo_sha"))
            if dt[:10] >= "2026-08-01":
                por_dia[dt[:10]][reg] += 1
            # control positivo: procesado despues del merge de K
            pu = r.get("processed_utc") or ""
            if pu >= "2026-10-18T10:30":
                procesado_post[reg] += 1
            for nom, (a, b) in ventanas.items():
                if a <= dt[:10] <= b:
                    out.setdefault(nom, {}).setdefault(v, Counter())[(bucket(r.get("sensor", "")), reg)] += 1
    print("SHAs vistos:", {k[:10]: x for k, x in _cache.items()})
    print("CONTROL POSITIVO (processed_utc >= 2026-10-18T10:30):", dict(procesado_post))
    res = {"control_positivo_procesado_post_merge": dict(procesado_post), "shas": _cache, "ventanas": {}}
    for nom, porv in out.items():
        tot = Counter()
        for v, c in porv.items():
            for (b, reg), n in c.items():
                tot[reg] += n
        print(f"\n== {nom} {ventanas[nom]} total por regimen: {dict(tot)}")
        res["ventanas"][nom] = {"total": dict(tot), "por_volcan_sensor": {}}
        for v in VOLS:
            c = porv.get(v, Counter())
            fila = {f"{b}|{reg}": n for (b, reg), n in sorted(c.items())}
            res["ventanas"][nom]["por_volcan_sensor"][v] = fila
            if nom == "audit_60d_hoy":
                print(f"  {v:20s} {fila}")
    # frontera diaria
    print("\nfrontera por dia (C0/K/otros):")
    for d in sorted(por_dia):
        if "2026-09-10" <= d <= "2026-09-25" or d >= "2026-10-15":
            print(" ", d, dict(por_dia[d]))
    res["por_dia"] = {d: dict(c) for d, c in sorted(por_dia.items())}
    json.dump(res, open(os.path.join(os.path.dirname(__file__), "regimen_por_ventana.json"), "w", encoding="utf-8"), indent=1)

main()
