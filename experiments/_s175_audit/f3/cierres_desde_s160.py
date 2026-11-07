# -*- coding: utf-8 -*-
"""F3 S175: de los cierres que el censo S145 encuentra en la base, cuales se escribieron desde S160 (git blame con
fecha de autor >= 2026-10-22, inicio de S160 en la bitacora). CLAUDE.md y CLAUDE_HISTORIA.md los reescribio entero #949
(S173): su fecha de blame no dice cuando nacio el cierre, se informan aparte. Salida: cierres_desde_s160.json"""
import io, json, subprocess, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
C = "752d348bc"
d = json.load(open(f"censo_{C}.json", encoding="utf-8"))
raiz = subprocess.run(["git","rev-parse","--show-toplevel"],capture_output=True,text=True).stdout.strip()
out = []
cache = {}
for f in d["filas"]:
    a = f["archivo"]
    if a not in cache:
        b = subprocess.run(["git","blame","--line-porcelain",C,"--",a],capture_output=True,cwd=raiz).stdout.decode("utf-8","replace")
        lines = {}; cur = None; n = 0; info = {}
        for l in b.split("\n"):
            m = re.match(r"^([0-9a-f]{40}) \d+ (\d+)", l)
            if m: cur = m.group(1); n = int(m.group(2)); info = {"sha": cur[:9]}; continue
            if l.startswith("author-time "): info["t"] = int(l.split()[1])
            if l.startswith("summary "): info["s"] = l[8:90]
            if l.startswith("\t"): lines[n] = dict(info)
        cache[a] = lines
    bi = cache[a].get(f["linea"], {})
    import datetime
    fecha = datetime.datetime.utcfromtimestamp(bi.get("t", 0)).strftime("%Y-%m-%d")
    out.append(dict(f, blame_sha=bi.get("sha"), blame_fecha=fecha, blame_resumen=bi.get("s")))
nuevos = [o for o in out if o["blame_fecha"] >= "2026-10-22" and o["archivo"] not in ("CLAUDE.md","docs/CLAUDE_HISTORIA.md")]
json.dump(dict(n_total=len(out), n_desde_s160_fuera_claude=len(nuevos), filas=out), open("cierres_desde_s160.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("total", len(out), "desde S160 (fuera de CLAUDE/HISTORIA):", len(nuevos))
for o in nuevos:
    print(f"{o['archivo']}:{o['linea']} [{o['blame_fecha']} {o['blame_sha']}] tipos={o['tipos']} resp={o['respaldos']} :: {o['texto'][:230]}")
print("\nCLAUDE.md:")
for o in out:
    if o["archivo"]=="CLAUDE.md": print(f"  {o['linea']} {o['tipos']} resp={o['respaldos']} :: {o['texto'][:200]}")
