# -*- coding: utf-8 -*-
"""S146 frente B: identifica cierres que citan un script/test/experimento.

Dos preguntas del instrumento:
 1. Si lo que mide estuviera roto (no hubiera cierres con script), fallaria? SI: daria 0 filas y
    el control positivo (D26 -> que_rama_manda.py) no apareceria; se comprueba al final.
 2. Si el instrumento estuviera muerto (regex vacias), se veria distinto? SI: 0 filas y control FALLA.
Limite declarado: busca por palabras clave y rutas; es un piso. Solo LEE; escribe en su carpeta.
"""
import io, re, sys, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOCS = ["docs/MIROVA_DIVERGENCES.md", "CLAUDE.md", "docs/MISSION.md", "docs/HYPOTHESIS_LOG.md", "docs/META_RULES_S80.md"]
CIERRE = re.compile(r"\bCERRAD[AO]S?\b|\bRESUELT[AO]S?\b|\bagotad[oa]s?\b|\b[Nn][Oo] reabrir\b|no se reabre|efecto nulo|nulo hoy|irreducible|es FIEL|es fiel|fidelidad confirmada|despreciable|invisible hoy|ABIERTA, menor|prioridad baja|impacto menor|NO ADOPTAR|refutad[oa]s?|REFUT|descartad[oa]|DESCARTAD|no vale|no aplica|redundante|no es bug|NO es bug|inmune|no separa|no discrimina|0 robos|sin sustrato", re.I)
RUTA = re.compile(r"((?:experiments|scripts|tests|scratchpad|pipeline)/[\w/.\-]+\.(?:py|json|md|csv|yml))|(\b[\w]+\.py\b)")
filas = []
for rel in DOCS:
    L = (ROOT/rel).read_text(encoding="utf-8", errors="replace").split("\n")
    for i, l in enumerate(L):
        if not CIERRE.search(l): continue
        v = "\n".join(L[max(0,i-3):i+7])
        rutas = sorted({(m.group(1) or m.group(2)) for m in RUTA.finditer(v)})
        rutas = [r for r in rutas if r.startswith(("experiments","scripts","tests","scratchpad")) or r.endswith(".py")]
        if rutas:
            filas.append({"archivo": rel, "linea": i+1, "rutas": rutas, "texto": l.strip()[:260]})
json.dump(filas, open(HERE/"b00_cierres_con_script.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("filas:", len(filas))
ctrl = [f for f in filas if any("que_rama_manda" in r for r in f["rutas"])]
print("CONTROL POSITIVO D26 (que_rama_manda.py) aparece:", len(ctrl) > 0, [ (c['archivo'],c['linea']) for c in ctrl][:5])
from collections import Counter
c = Counter(r for f in filas for r in f["rutas"])
for r, n in c.most_common(): print(n, r, "EXISTE" if (ROOT/r).exists() else "")
