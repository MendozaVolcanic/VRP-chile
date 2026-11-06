# -*- coding: utf-8 -*-
"""Compara los IDs (A, D, S, PR) entre el CLAUDE.md viejo y el nuevo.
Uso: python ids_faltantes.py VIEJO NUEVO
Faltar un A-numero es error (exit 1). D, S y PR se informan.
S173: corrido como `git show 80aafc49e:CLAUDE.md > viejo.md`, `git show <rama>:CLAUDE.md > nuevo.md`,
`python ids_faltantes.py viejo.md nuevo.md > ids_resultado.txt` (exit 0)."""
import io, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
viejo = open(sys.argv[1], encoding="utf-8").read()
nuevo = open(sys.argv[2], encoding="utf-8").read()
PAT = {"A": r"(?<![\w/.-])A(\d{1,3})(?!\d)", "D": r"(?<![\w/.-])D(\d{1,2})(?!\d)",
       "S": r"(?<![\w/.-])S(\d{1,3})(?!\d)", "PR": r"#(\d{2,4})(?!\d)"}
def ids(t, k):
    s = {int(x) for x in re.findall(PAT[k], t)}
    if k == "A":  # rangos escritos como A56-A60 / A49-A118
        for a, b in re.findall(r"A(\d{1,3})-A(\d{1,3})", t):
            s |= set(range(int(a), int(b) + 1))
    return s
err = 0
for k in ("A", "D", "S", "PR"):
    v, n = ids(viejo, k), ids(nuevo, k)
    falt = sorted(v - n)
    print(f"{k}: viejo {len(v)}, nuevo {len(n)}, faltan {len(falt)}: {falt if k in ('A','D') else falt[:60]}")
    if k == "A" and falt:
        err = 1
# A-numeros con vineta propia en el viejo: deben tener vineta propia o estar en una linea del nuevo
vin_v = sorted({int(x) for x in re.findall(r"^\s*-\s+\*\*A(\d+)[.\s*]", viejo, re.M)} |
               {int(x) for x in re.findall(r"^\s*-\s+\*\*A(\d+)-A\d+", viejo, re.M)})
vin_n = {int(x) for x in re.findall(r"^\s*-\s+\*\*A(\d+)", nuevo, re.M)}
print("A con vineta en viejo:", len(vin_v), "sin vineta propia en nuevo:", sorted(set(vin_v) - vin_n))
sys.exit(err)
