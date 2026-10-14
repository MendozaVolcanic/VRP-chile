"""D1: tamano del consolidado remoto cada 12 h (ultimo commit antes de cada corte), para encontrar caidas.
Limite: una caida menor que el crecimiento de 12 h (~10 KB) no se ve. Uso: python d1_tamano_historia.py desde hasta salida"""
import subprocess, datetime as dt, sys
from concurrent.futures import ThreadPoolExecutor
P = "monitoreo_satelital/registro_vrp_consolidado.csv"
def uno(t):
    u = t.strftime("%Y-%m-%dT%H:%M:%SZ")
    sha = subprocess.run(["gh", "api", f"repos/MendozaVolcanic/Mirova-v1/commits?path={P}&until={u}&per_page=1", "--jq", ".[0].sha"], capture_output=True, text=True).stdout.strip()
    size = subprocess.run(["gh", "api", f"repos/MendozaVolcanic/Mirova-v1/contents/{P}?ref={sha}", "--jq", ".size"], capture_output=True, text=True).stdout.strip() if sha else ""
    return u, sha, size
a, b = (dt.datetime.fromisoformat(x) for x in sys.argv[1:3])
ts = []
while a < b: ts.append(a); a += dt.timedelta(hours=12)
with ThreadPoolExecutor(6) as ex: res = list(ex.map(uno, ts))
with open(sys.argv[3], "w") as f:
    for r in res: f.write("\t".join(r) + "\n")
prev = None
for u, sha, s in res:
    if s and prev and int(s) < int(prev[2]): print("CAIDA", prev[0], prev[2], "->", u, s, int(s) - int(prev[2]))
    if s: prev = (u, sha, s)
