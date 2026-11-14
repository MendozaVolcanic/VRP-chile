# -*- coding: utf-8 -*-
"""F3 S175: corre los detectores de experiments/_s145_censo_cierres/censo.py (importados, no copiados) sobre los
documentos rectores de un commit, sin escribir en la carpeta de S145. Agrega SINTOMAS.md y CLAUDE_HISTORIA.md
(el CLAUDE.md corto de S173 mando la historia a ese archivo). Uso: python censo_en_commit.py <commit>"""
import io, json, subprocess, sys, importlib.util
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
C = sys.argv[1]
RAIZ = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("censo", RAIZ / "experiments/_s145_censo_cierres/censo.py")
censo = importlib.util.module_from_spec(spec); spec.loader.exec_module(censo)
DOCS = censo.DOCS + ["docs/SINTOMAS.md", "docs/CLAUDE_HISTORIA.md"]
filas = []
for rel in DOCS:
    r = subprocess.run(["git", "show", f"{C}:{rel}"], capture_output=True, cwd=RAIZ)
    if r.returncode: print("no existe", rel); continue
    ls = r.stdout.decode("utf-8", "replace").split("\n")
    for i, l in enumerate(ls):
        t = censo.tipos_de_cierre(l)
        if not t: continue
        resp = censo.respaldos_citados(censo.contexto(ls, i, 1, 3))
        filas.append(dict(archivo=rel, linea=i + 1, tipos=t, respaldos=resp,
                          sin_respaldo=resp == [] or resp == ["sesion"], texto=l.strip()[:300]))
ctrl = censo.tipos_de_cierre("Esta divergencia queda CERRADA y no reabrir: el efecto es despreciable.")
por = {}
for f in filas: por[f["archivo"]] = por.get(f["archivo"], 0) + 1
out = dict(commit=C, control_positivo=ctrl, n=len(filas), n_sin_respaldo=sum(f["sin_respaldo"] for f in filas),
           por_archivo=por, filas=filas)
json.dump(out, open(f"censo_{C.replace('^','_padre')}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print({k: v for k, v in out.items() if k != "filas"})
