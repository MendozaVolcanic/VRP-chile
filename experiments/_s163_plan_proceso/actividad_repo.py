"""S163: actividad del repositorio por mes (commits humanos, commits de bots, PR, dias con commit humano).

POR QUE: el plan de proceso (docs/PLAN_PROCESO_VRP_CHILE_S163.md) muestra el ritmo de trabajo
con cifras que salgan de un script, no de memoria. Commits "humanos" = autor sin "bot" en el
nombre (incluye los commits que Claude hace a nombre de Nicolas: no separa persona de IA).
PR = prs.json, bajado con:
  gh pr list -R MendozaVolcanic/VRP-chile --state all --limit 2000 --json number,state,createdAt,mergedAt
Uso: python -I actividad_repo.py <ruta del repo con origin/main al dia>
"""
import collections
import io
import json
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
repo = sys.argv[1]
log = subprocess.run(["git", "-C", repo, "log", "origin/main", "--format=%ad|%an", "--date=short"],
                     capture_output=True, text=True, encoding="utf-8", check=True).stdout.split("\n")
hum, bot, dias = collections.Counter(), collections.Counter(), collections.defaultdict(set)
for ln in filter(None, log):
    fecha, autor = ln.split("|", 1)
    mes = fecha[:7]
    if "bot" in autor.lower():
        bot[mes] += 1
    else:
        hum[mes] += 1
        dias[mes].add(fecha)
prs = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "prs.json"), encoding="utf-8"))
pr_mes = collections.Counter(p["createdAt"][:7] for p in prs)
mrg = sum(1 for p in prs if p["state"] == "MERGED")
print(f"commits origin/main: humanos={sum(hum.values())} bots={sum(bot.values())}; "
      f"dias con commit humano={sum(len(v) for v in dias.values())}")
print(f"PR: total={len(prs)} mergeados={mrg} primero={min(p['createdAt'] for p in prs)[:10]}")
print("mes\tcommits_humanos\tcommits_bots\tdias_humanos\tPR_abiertos_en_el_mes")
for mes in sorted(set(hum) | set(bot) | set(pr_mes)):
    print(f"{mes}\t{hum[mes]}\t{bot[mes]}\t{len(dias[mes])}\t{pr_mes[mes]}")
