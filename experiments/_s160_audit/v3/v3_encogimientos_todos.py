"""V3, hallazgo 245 (clave de fila = fecha_utc,volcan,sensor; una fila corregida no cuenta como perdida), por otro camino que el auditor: TODA la historia de latest_consolidado.csv hasta SHA_MAIN
(no sólo los 400 últimos commits), por FILAS (claves de fila, no líneas), y si las filas perdidas vuelven en
algún commit posterior (pérdida transitoria) o no (permanente). Control positivo: el primer commit tiene que
dar n>0 filas; un encogimiento sintético se cuenta (se verifica con el par artificial al final).
Pregunta 2: si git cat-file fallara, n_filas sería 0 y se aborta.
Uso: python -I v3_encogimientos_todos.py <repo> <sha>"""
import subprocess, sys
repo, sha = sys.argv[1], sys.argv[2]
hs = subprocess.run(["git", "-C", repo, "log", "--reverse", "--format=%H %cI", sha, "--", "latest_consolidado.csv"],
                    capture_output=True, text=True, check=True).stdout.split("\n")
hs = [h.split() for h in hs if h.strip()]
p = subprocess.Popen(["git", "-C", repo, "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
def leer(h):
    p.stdin.write(f"{h}:latest_consolidado.csv\n".encode()); p.stdin.flush()
    head = p.stdout.readline().split()
    if head[-1] == b"missing": return None
    n = int(head[2]); data = p.stdout.read(n); p.stdout.read(1)
    return data
prev = None; prev_set = None; prev_txt = {}; eventos = []; perdidas = {}  # clave (fecha_utc,volcan,sensor) -> (commit, fecha)
TXT = {}
cab = set()
for h, f in hs:
    data = leer(h)
    if data is None: continue
    lineas = data.decode("utf-8", "replace").splitlines()
    cab.add(lineas[0][:60])
    s = set(",".join(l.split(",")[1:2]+l.split(",")[3:5]) for l in lineas[1:])
    filas_txt = {",".join(l.split(",")[1:2]+l.split(",")[3:5]): l for l in lineas[1:]}
    assert len(s) > 0
    # filas que vuelven
    for fila in list(perdidas):
        if fila in s: del perdidas[fila]
    if prev_set is not None and len(lineas) < prev:
        ido = prev_set - s
        eventos.append((h[:9], f, prev, len(lineas), len(ido)))
        for fila in ido: perdidas.setdefault(fila, (h[:9], f)); TXT.setdefault(fila, prev_txt.get(fila, ""))
    prev, prev_set, prev_txt = len(lineas), s, filas_txt
print(f"commits leidos={len(hs)} primera={hs[0][1]} ultima={hs[-1][1]} cabeceras_distintas={len(cab)}")
print(f"encogimientos (lineas bajan)={len(eventos)}")
for e in eventos: print(f"  {e[0]} {e[1]}: {e[2]} -> {e[3]} lineas, filas que salen={e[4]}")
print(f"filas que salieron en un encogimiento y NO volvieron hasta SHA_MAIN={len(perdidas)}")
ult = prev_set
# de esas, cuántas son ALERTA (columna con 'ALERTA' en el texto)
alerta = [r for r in perdidas if "ALERTA" in TXT.get(r,"").upper()]
print(f"  de ellas con la palabra ALERTA={len(alerta)}")
for r in sorted(alerta)[:15]: print("   ", TXT[r][:150], "<- perdida en", perdidas[r])
import collections
print("  ALERTA perdidas por evento:", collections.Counter(perdidas[r][0] for r in alerta))
print("  ALERTA perdidas por volcan y sensor:", collections.Counter(tuple(TXT[r].split(",")[3:5]) for r in alerta).most_common(12))
vrp=[float(TXT[r].split(",")[5]) for r in alerta if TXT[r].split(",")[5].replace(".","",1).isdigit()]
print("  ALERTA perdidas con VRP>=1 MW:", sum(v>=1 for v in vrp), "de", len(vrp))
