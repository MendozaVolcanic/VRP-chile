"""v07_choques_ocr.py (punto 3, instrumento propio): para cada corrida de ocr_workflow.yml de la ventana bajada
por v03, toma el sha que pidio el checkout (headSha de la API = sha del despacho), las lineas del rebase y los
rangos empujados ("A..B main -> main"). Como con -X ours git no imprime nada cuando resuelve un choque (verificado
en run_40117161109.log: rebase sobre un commit que tocaba el mismo CSV y solo salio "Rebasing (1/1)"), el registro
NO puede contar choques resueltos. Lo que si se puede medir con git: por cada push rebasado, los archivos que el
remoto cambio entre el sha del despacho y la base del push (X..A) y los que el commit del OCR cambia (A..B). Si se
intersectan, hubo un choque posible que -X ours pudo resolver a ciegas (y que sin -X ours puede dejar la corrida
en rojo). Ademas cuenta las huellas textuales de choque que si se imprimen: CONFLICT, Cannot merge, could not apply,
"Pull fallo", "Push fallo", rebase --abort."""
import json, os, re, subprocess, collections
AQUI = os.path.dirname(os.path.abspath(__file__)); CLON = r"D:\vrp-trabajo\s163-d39\mirova-v1"
runs = json.load(open(os.path.join(AQUI, "ocr_runs_lista.json")))
def git(*a):
    return subprocess.run(["git", "-C", CLON] + list(a), capture_output=True, text=True).stdout
def archivos(a, b):
    return set(git("diff", "--name-only", "--no-renames", a, b).split())
RANGO = re.compile(r"\s([0-9a-f]{7,})\.\.([0-9a-f]{7,})\s+main\s+->\s+main")
HUELLA = re.compile(r"CONFLICT|Cannot merge|could not apply|Pull fall|Push fall|rebase --abort|error: ")
tot = collections.Counter(); detalle = []
for r in sorted(runs, key=lambda r: r["createdAt"]):
    p = os.path.join(AQUI, "ocr_logs", f"{r['databaseId']}.txt")
    if not os.path.exists(p):
        tot["sin registro"] += 1; continue
    txt = open(p, encoding="utf-8").read()
    if txt.startswith("ERROR"):
        tot["registro con error (gh)"] += 1; continue
    tot["corridas con registro"] += 1
    X = r["headSha"]
    rangos = RANGO.findall(txt)
    n_rebase = len(re.findall(r"Rebasing \(", txt))
    # sin las lineas que son el eco del guion (ANSI 36;1m) ni el "::error" del propio echo
    huellas = [h for ln in txt.splitlines() if "[36;1m" not in ln for h in HUELLA.findall(ln)]
    if huellas:
        tot["corridas con huella textual de choque"] += 1
        detalle.append((r["databaseId"], r["createdAt"], "HUELLA", huellas[:5]))
    if not rangos:
        tot["corridas sin push"] += 1; continue
    tot["corridas con push"] += 1
    for A, B in rangos:
        tot["pushes"] += 1
        Afull = git("rev-parse", A).strip(); Bfull = git("rev-parse", B).strip()
        if not Afull or not Bfull:
            tot["push con sha no presente en el clon"] += 1; continue
        padre = git("rev-parse", B + "^").strip()
        if padre != Afull:
            tot["push cuyo padre no es la base del rango"] += 1
            detalle.append((r["databaseId"], r["createdAt"], "PADRE!=BASE", A, B, padre[:10]))
        if Afull.startswith(X) or X.startswith(Afull[:len(X)]):
            tot["push sin rebase (base = sha del despacho)"] += 1; continue
        tot["push rebasado (el remoto se movio desde el despacho)"] += 1
        remoto = archivos(X, Afull); propio = archivos(Afull, Bfull)
        inter = remoto & propio
        if inter:
            tot["push rebasado con archivos tocados por los dos lados"] += 1
            remotos = git("log", "--format=%h %an %s", f"{X}..{Afull}", "--", *sorted(inter)).strip().splitlines()
            st1 = git("diff", "--numstat", "--no-renames", X, Afull, "--", *sorted(inter)).strip().replace("	", " ")
            st2 = git("diff", "--numstat", "--no-renames", Afull, Bfull, "--", *sorted(inter)).strip().replace("	", " ")
            detalle.append((r["databaseId"], r["createdAt"], "INTERSECCION", sorted(inter)[:8], "remoto:", remotos[:4], "numstat X..A:", st1, "numstat A..B:", st2))
        else:
            tot["push rebasado sin archivo en comun"] += 1
        csvs = {f for f in remoto if f.endswith(".csv")} & propio
        if csvs:
            tot["  de ellos, CSV en comun"] += 1
print("ventana:", runs[-1]["createdAt"], "a", runs[0]["createdAt"], "| corridas listadas", len(runs))
for k, v in tot.items():
    print(f"  {k}: {v}")
for d in detalle:
    print("  ", d)
