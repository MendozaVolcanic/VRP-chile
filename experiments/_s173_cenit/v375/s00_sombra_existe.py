# -*- coding: utf-8 -*-
"""s00 (S173): ¿existen records de la sombra V375-E de Chillán? POR QUÉ: la tarea supone que
data/sombra_codigo_mirova/NevadosDeChillan.json está en origin/main con records desde 2026-10-xx; si no hay records,
la razón de V375-E por pasada no se puede leer de la sombra y hay que decirlo (SIN DATO), no rellenarlo.
P1: control positivo, el mismo ls-tree sobre data/mirova_equivalent/NevadosDeChillan.json debe encontrarlo.
P2: se imprime el sha de origin/main sobre el que se miró y la fecha de inicio que el lector sellado fija (DESDE_P).
Uso: python -B s00_sombra_existe.py <repo git>"""
import re, subprocess, sys
G = sys.argv[1]
def git(*a):
    return subprocess.run(["git", "-C", G, *a], capture_output=True, text=True, encoding="utf-8").stdout
sha = git("rev-parse", "origin/main").strip()
print("origin/main", sha)
for p in ("data/sombra_codigo_mirova/", "data/sombra_codigo_mirova/NevadosDeChillan.json",
          "data/mirova_equivalent/NevadosDeChillan.json"):
    out = git("ls-tree", "-l", "origin/main", "--", p).strip()
    print(f"ls-tree {p}: {out or 'NO EXISTE'}")
lec = git("show", "s172-v375e-lector-resellado:experiments/_s168/v375e_sombra/leer_sombra_v375e.py")
print("lector sellado DESDE_P:", re.search(r'DESDE_P = "([^"]+)"', lec).group(1))
wf = git("show", "origin/main:.github/workflows/sombra-codigo-mirova.yml")
print("workflow cron:", re.search(r'cron: "([^"]+)"', wf).group(1))
print("workflow, l. con 2026-11-03:", [l.strip() for l in wf.splitlines() if "2026-11-03" in l])
