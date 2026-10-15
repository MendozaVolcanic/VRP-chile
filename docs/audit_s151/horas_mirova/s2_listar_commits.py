"""s2: lista los commits que tocaron registro_vrp_consolidado.csv en una ventana (hora UTC del commit).
Uso: python s2_listar_commits.py SINCE UNTIL salida.csv   (ISO UTC, ej 2026-09-07T00:00:00Z)"""
import sys, json, subprocess, csv

since, until, out = sys.argv[1:4]
rows = []
page = 1
while True:
    url = (f"repos/MendozaVolcanic/Mirova-v1/commits?path=monitoreo_satelital/registro_vrp_consolidado.csv"
           f"&since={since}&until={until}&per_page=100&page={page}")
    r = subprocess.run(["gh", "api", url], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        print("ERROR", page, r.stderr[:300]); break
    data = json.loads(r.stdout)
    if not data:
        break
    for c in data:
        rows.append((c["sha"], c["commit"]["committer"]["date"], c["commit"]["author"]["date"],
                     c["commit"]["message"].splitlines()[0]))
    page += 1
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["sha", "committer_utc", "author_utc", "mensaje"]); w.writerows(rows)
print(out, len(rows), "commits; paginas", page - 1)
