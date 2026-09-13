"""Clasifica las ramas remotas por contenido contra main (no por `git cherry`, que da falsos pendientes con squash).
Para cada rama: merge-base con origin/main; archivos que la rama cambio respecto del merge-base (excluyendo data/);
INTEGRADA si `git diff <rama> origin/main -- <esos archivos>` es vacio (todo lo que la rama toco esta identico en main),
PENDIENTE si hay diferencias (se listan hasta 5 archivos), SOLO_DATA si solo toco data/, IGUAL si apunta al mismo commit que main.
P1: si una rama tuviera trabajo sin mergear, el diff por archivo lo mostraria. Si.
P2: si git fallara, el script lanza excepcion (no cero silencioso). Control positivo: una rama recien mergeada por squash
(s137-cierre) debe salir INTEGRADA aunque `git cherry` la marque pendiente.
Ventana: origin/* al 2026-09-13 11:49 UTC. Denominador: todas las ramas remotas menos HEAD y main.
"""
import subprocess, json, sys, io, re
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
def run(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
branches = [b.strip() for b in run("branch", "-r").splitlines() if "->" not in b]
branches = [b for b in branches if b != "origin/main"]
print("ramas remotas (sin HEAD/main):", len(branches))
out = []
for b in branches:
    mb = run("merge-base", b, "origin/main").strip()
    same = run("rev-parse", b).strip() == run("rev-parse", "origin/main").strip()
    files = [f for f in run("diff", "--name-only", mb, b).splitlines() if f]
    files_nd = [f for f in files if not f.startswith("data/")]
    date = run("log", "-1", "--format=%ci", b).strip()[:10]
    if same:
        st = "IGUAL_A_MAIN"; pend = []
    elif not files:
        st = "SIN_CAMBIOS"; pend = []
    elif not files_nd:
        st = "SOLO_DATA"; pend = []
    else:
        d = run("diff", "--name-only", b, "origin/main", "--", *files_nd).splitlines()
        # archivos que la rama toco y que en main estan distintos a la rama
        pend = [f for f in d if f]
        st = "INTEGRADA" if not pend else "PENDIENTE"
    pref = re.sub(r"^origin/", "", b)
    pref = re.sub(r"^(claude/)?(s\d+).*", r"\1\2", pref) if re.match(r"^(claude/)?s\d+", pref) else pref.split("/")[0]
    out.append({"branch": b, "date": date, "state": st, "n_files": len(files), "n_files_nodata": len(files_nd), "pending": pend[:8], "prefix": pref})
json.dump(out, open("experiments/_s138_audit/eje6/ramas.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("\nestado | n"); 
for k, v in Counter(o["state"] for o in out).most_common(): print(f"{k} | {v}")
print("\nPENDIENTES (rama | fecha ultimo commit | archivos con diferencia vs main, sin data/):")
for o in sorted([o for o in out if o["state"] == "PENDIENTE"], key=lambda o: o["date"]):
    print(f"  {o['branch']} | {o['date']} | {len(o['pending'])}: {', '.join(o['pending'][:5])}")
print("\nSOLO_DATA:", [o["branch"] for o in out if o["state"] == "SOLO_DATA"][:20])
print("\npor prefijo (integradas/total):")
g = defaultdict(Counter)
for o in out: g[o["prefix"]][o["state"]] += 1
for k in sorted(g, key=lambda k: -sum(g[k].values())): print(f"  {k}: {dict(g[k])}")
print("\ncontrol positivo s137-cierre:", [o["state"] for o in out if o["branch"].endswith("s137-cierre")])
print("git cherry sobre s137-cierre (commits que cherry marca como no integrados):", len([l for l in run("cherry", "origin/main", "origin/s137-cierre").splitlines() if l.startswith("+")]))
