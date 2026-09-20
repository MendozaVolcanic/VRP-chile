"""Forma, segunda pasada: una linea eliminada cuenta como conservada si se parte en
prefijo+sufijo y ambos aparecen en el texto agregado (la marca se inserto en medio)."""
import subprocess, re, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
FILES = ["CLAUDE.md", "docs/MISSION.md", "docs/MIROVA_DIVERGENCES.md", "docs/audit_s139/BORRADOR_CORREO_COPPOLA.md"]
norm = lambda s: re.sub(r"\s+", " ", s).strip()
words = collections.Counter()
for f in FILES:
    d = subprocess.run(["git", "diff", "-U0", "--", f], capture_output=True, text=True, encoding="utf-8").stdout
    minus = [l[1:] for l in d.split("\n") if l.startswith("-") and not l.startswith("---")]
    plus = [l[1:] for l in d.split("\n") if l.startswith("+") and not l.startswith("+++")]
    nplus = norm("\n".join(plus))
    for m in minus:
        nm = norm(m); ok = nm in nplus
        if not ok:
            toks = nm.split(" ")
            for i in range(1, len(toks)):
                if " ".join(toks[:i]) in nplus and " ".join(toks[i:]) in nplus:
                    ok = True; break
        print(f"{f}: {'OK  ' if ok else 'PERDIDA'} | {nm[:110]}")
    for p in plus:
        for w in re.findall(r"\b[a-záéíóúñ]+[áéí]\b", p):
            words[w] += 1
print(sorted(words.items()))
