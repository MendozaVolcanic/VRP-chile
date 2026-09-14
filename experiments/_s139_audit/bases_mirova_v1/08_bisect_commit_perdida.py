"""08: encuentra el commit exacto del remoto en que desaparecieron filas del
consolidado, por biseccion sobre la historia del archivo (gh api + raw).

Uso: python 08_bisect_commit_perdida.py --remoto DIR --desde 2026-04-21T20:00:00Z --hasta 2026-04-25T00:00:00Z
Busca las llaves de la copia local del 08-abr ausentes en el remoto de hoy y
bisecta el primer commit del rango en que el conteo de presentes baja.
"""
import io
import json
import os
import subprocess
import sys
import urllib.request

import pandas as pd

from comun import LOCAL_MIROVA, dir_remoto, leer

D = dir_remoto(sys.argv)
desde = sys.argv[sys.argv.index("--desde") + 1]
hasta = sys.argv[sys.argv.index("--hasta") + 1]
PATH = "monitoreo_satelital/registro_vrp_consolidado.csv"


def llaves(df):
    return set(zip(df["timestamp"].astype("int64"), df["Volcan"], df["Sensor"]))


cons = leer(f"{D}/registro_vrp_consolidado.csv")
b = leer(os.path.join(LOCAL_MIROVA, "registro_vrp_consolidado al 08042026.csv"))
b.loc[b["Volcan"] == "Peteroa", "Volcan"] = "PlanchonPeteroa"
kr = llaves(cons)
kp = {k for k in llaves(b) if k not in kr}
print("llaves buscadas:", len(kp), "| rango:", desde, "->", hasta)

# lista de commits del archivo en el rango (orden: mas nuevo primero)
commits = []
page = 1
while True:
    out = subprocess.run(["gh", "api", f"repos/MendozaVolcanic/Mirova-v1/commits?path={PATH}&since={desde}&until={hasta}&per_page=100&page={page}",
                          "--jq", ".[] | [.sha, .commit.committer.date, .commit.author.name, (.commit.message|split(\"\\n\")[0])] | @tsv"],
                         capture_output=True, text=True, encoding="utf-8").stdout.strip()
    if not out:
        break
    commits += [l.split("\t") for l in out.splitlines()]
    page += 1
commits.reverse()  # cronologico
print("commits del archivo en el rango:", len(commits))
cache = {}


def presentes(i):
    sha = commits[i][0]
    if sha in cache:
        return cache[sha]
    url = f"https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/{PATH}"
    data = urllib.request.urlopen(url).read()
    df = pd.read_csv(io.BytesIO(data), dtype=str, keep_default_na=False)
    df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce").astype("Int64")
    df.loc[df["Volcan"] == "Peteroa", "Volcan"] = "PlanchonPeteroa"
    n = len(kp & llaves(df))
    cache[sha] = (n, len(df))
    print(f"   {i:4d} {sha[:10]} {commits[i][1]} filas={len(df)} presentes={n}")
    return cache[sha]


lo, hi = 0, len(commits) - 1
n_lo, _ = presentes(lo); n_hi, _ = presentes(hi)
print("presentes al inicio:", n_lo, "| al final:", n_hi)
while hi - lo > 1:
    mid = (lo + hi) // 2
    n, _ = presentes(mid)
    if n == n_lo:
        lo = mid
    else:
        hi = mid
sha_bad = commits[hi][0]
print("\nPRIMER COMMIT EN QUE BAJA:", commits[hi])
print("commit anterior           :", commits[lo])
info = subprocess.run(["gh", "api", f"repos/MendozaVolcanic/Mirova-v1/commits/{sha_bad}",
                       "--jq", "{autor: .commit.author, msg: .commit.message, parents: [.parents[].sha], files: [.files[] | {f: .filename, a: .additions, d: .deletions, s: .status}]}"],
                      capture_output=True, text=True, encoding="utf-8").stdout
print(json.dumps(json.loads(info), indent=1, ensure_ascii=False)[:3000])
