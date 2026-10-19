# -*- coding: utf-8 -*-
"""Cuenta cuantas veces se cita cada ID de cierre (D1-D40, A1-A120) en docs/, tasks/, CLAUDE.md
y experiments/*/README.md. Proxy de 'cuanto dano hace si es falso'.
P1: un cierre citado por su contenido sin el ID no se cuenta (piso). P2: control: 'A113' y 'D21'
son de los mas citados conocidos; si dan 0 el instrumento esta muerto."""
import re, sys, io
from pathlib import Path
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
files = list((ROOT/"docs").rglob("*.md")) + list((ROOT/"tasks").glob("*.md")) + [ROOT/"CLAUDE.md"] + list((ROOT/"experiments").glob("*/README.md"))
c = Counter(); nf = Counter()
for f in files:
    t = f.read_text(encoding="utf-8", errors="replace")
    seen = set()
    for m in re.findall(r"\b([AD]\d{1,3})\b", t):
        n = int(m[1:])
        if (m[0] == "D" and n <= 40) or (m[0] == "A" and n <= 120):
            c[m] += 1; seen.add(m)
    for s in seen: nf[s] += 1
print("archivos barridos", len(files), "| control A113", c["A113"], "D21", c["D21"])
for k, v in c.most_common(45):
    print(f"{k:5} menciones={v:5} archivos={nf[k]}")
