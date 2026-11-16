# Q1: si el censo estuviera "roto" (no viera cierres), el control positivo (frase sintetica con CERRADA/no reabrir) daria []; si la linea base roja fuese verde, tipos_de_cierre devolveria algo en las lineas objetivo.
# Q2: instrumento muerto => el control positivo daria [] (se imprime). Uso los detectores de censo.py de 752d348bc (copia en v3/censo_752.py), no la copia del auditor.
# Linea base (1): linea de A85 en CLAUDE.md de 77e54e8e0^ con la nota S153. Linea base (2): linea con "C0 antes del 2026-09-18" en documentos rectores de d516b9d8c. Denominador: lineas con esa cadena.
import importlib.util, subprocess, sys, re
from pathlib import Path
spec = importlib.util.spec_from_file_location("censo", Path(sys.argv[1])); c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
print("control positivo:", c.tipos_de_cierre("Esta divergencia queda CERRADA y no reabrir: el efecto es despreciable."))
def show(commit, rel, pat):
    r = subprocess.run(["git","show",f"{commit}:{rel}"],capture_output=True,cwd=sys.argv[2]); 
    if r.returncode: print(commit,rel,"NO EXISTE"); return
    ls = r.stdout.decode("utf-8","replace").split("\n"); n=0
    for i,l in enumerate(ls):
        if re.search(pat,l):
            n+=1; print(f"{commit[:9]} {rel}:{i+1} tipos={c.tipos_de_cierre(l)} respaldos_ventana={c.respaldos_citados(c.contexto(ls,i,1,3))}\n    {l.strip()[:200]}")
    print(commit[:9],rel,"lineas con patron:",n)
show("77e54e8e0^","CLAUDE.md",r"^- \*\*A85\.")
show("d516b9d8c","CLAUDE.md",r"C0 antes del 2026-09-18")
for rel in c.DOCS+["docs/SINTOMAS.md"]:
    show("d516b9d8c",rel,r"C0 antes del 2026-09-18")
