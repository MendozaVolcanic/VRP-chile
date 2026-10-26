"""v08b_rapido.py (A6): todas las versiones del consolidado entre 2026-10-15 03:00 y 2026-10-17 03:00 UTC, filtrando
por texto las lineas de Nevados de Chillan del 15 y 16 de octubre (parseo por posicion)."""
import subprocess, time, urllib.request, json, os, sys, gzip
CLON = r"D:\vrp-trabajo\s163-d39\mirova-v1"; RUTA = "monitoreo_satelital/registro_vrp_consolidado.csv"; AQUI = os.path.dirname(os.path.abspath(__file__))
log = [l.split() for l in subprocess.run(["git", "-C", CLON, "log", "--first-parent", "--reverse", "--format=%H %cI", "--since=2026-10-15T03:00:00Z", "--until=2026-10-17T03:00:00Z", "main", "--", RUTA], capture_output=True, text=True).stdout.split("\n") if l]
print("versiones:", len(log), flush=True)
def leer(sha):
    for i in range(8):
        try:
            req = urllib.request.Request(f"https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/{RUTA}", headers={"Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = r.read()
                if r.headers.get("Content-Encoding", "") == "gzip": d = gzip.decompress(d)
                return d.decode("utf-8")
        except Exception as e: print("   reintento", sha[:10], i, type(e).__name__, flush=True); time.sleep(5 * (i + 1)); err = e
    raise RuntimeError(err)
OBJ = {"2026-10-15 05:00", "2026-10-15 19:00", "2026-10-16 06:18", "2026-10-16 18:42"}
vistas = {}; cerca = {}
for i, (sha, c) in enumerate(log):
    for ln in leer(sha).split("\n"):
        if ",Nevados de Chillan," not in ln: continue
        p = ln.split(",", 9)
        if len(p) < 9 or p[1][:10] not in ("2026-10-15", "2026-10-16"): continue
        k = (p[0].strip(), p[3], p[4]); vistas.setdefault(k, (c, p[1], p[4], p[5], p[7], p[6]))
        if p[1][:16] in OBJ: cerca.setdefault(k, c)
    if i % 50 == 0: print(f"... {i}/{len(log)} {c} vistas {len(vistas)}", flush=True)
hoy = set()
for ln in subprocess.run(["git", "-C", CLON, "show", f"main:{RUTA}"], capture_output=True, check=True).stdout.decode("utf-8").split("\n"):
    p = ln.split(",", 5)
    if len(p) >= 5: hoy.add((p[0].strip(), p[3], p[4]))
print("llaves de Chillan 15-16 oct vistas en alguna version:", len(vistas), flush=True)
falt = {k: v for k, v in vistas.items() if k not in hoy}
print("ausentes hoy en main:", len(falt), flush=True)
for k, v in sorted(falt.items()): print("   ", v, flush=True)
print("filas a las horas de las alertas solo-OCR:", cerca, flush=True)
for k, v in sorted(vistas.items()): print("  vista:", v, flush=True)
json.dump({"vistas": [[list(k), list(v)] for k, v in vistas.items()], "ausentes": [list(k) for k in falt]}, open(os.path.join(AQUI, "v08b_resultado.json"), "w"), indent=1)
print("FIN", flush=True)
