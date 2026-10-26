"""v03_bajar_logs_ocr.py: baja los registros de las corridas de ocr_workflow.yml (solo lectura) y guarda,
por corrida, las lineas del checkout (sha pedido), del paso de push del OCR y del paso de Distancia
aproximada. No guarda el log entero (disco). Salida: ocr_logs/<id>.txt y ocr_runs_lista.json."""
import json, os, subprocess, sys, re
REPO = "MendozaVolcanic/Mirova-v1"
AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(AQUI, "ocr_logs")
LIMITE = int(sys.argv[1]) if len(sys.argv) > 1 else 300
lista = subprocess.run(["gh", "run", "list", "-R", REPO, "-w", "ocr_workflow.yml", "--limit", str(LIMITE),
                        "--json", "databaseId,createdAt,conclusion,headSha,event,status"],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
runs = json.loads(lista.stdout)
json.dump(runs, open(os.path.join(AQUI, "ocr_runs_lista.json"), "w"), indent=1)
print("corridas listadas", len(runs), "ventana", runs[-1]["createdAt"], "a", runs[0]["createdAt"], flush=True)
# Los registros viejos vienen con el paso "UNKNOWN STEP": se filtra solo por el texto.
CLAVE = re.compile(r"fetch .*origin \+|Rebasing|Successfully rebased|Auto-merging|CONFLICT|Cannot merge|could not apply|"
                   r"Pull fall|Push fall|Push exitoso|push OK|Intento \d+ de push|main -> main|main\s+-> origin/main|"
                   r"up to date|Sin cambios en Distancia|Push de la distancia|::error|fatal: |error: |"
                   r"##\[group\]Run git config|No hay eventos|rebase --abort|Run actions/checkout")
for r in runs:
    rid = r["databaseId"]
    dest = os.path.join(OUT, f"{rid}.txt")
    if os.path.exists(dest):
        continue
    p = subprocess.run(["gh", "run", "view", str(rid), "-R", REPO, "--log"], capture_output=True, text=True,
                       stdin=subprocess.DEVNULL, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        open(dest, "w", encoding="utf-8").write(f"ERROR rc={p.returncode}\n{p.stderr[:500]}\n")
        print(rid, "ERROR", p.stderr[:120].replace("\n", " "), flush=True)
        continue
    sel = []
    for ln in p.stdout.splitlines():
        partes = ln.split("\t", 2)
        if len(partes) < 3:
            continue
        job, paso, texto = partes
        if CLAVE.search(texto):
            sel.append(f"{job}\t{paso}\t{texto}")
    open(dest, "w", encoding="utf-8").write("\n".join(sel) + "\n")
    print(rid, r["createdAt"], r["conclusion"], len(sel), "lineas", flush=True)
print("FIN", flush=True)
